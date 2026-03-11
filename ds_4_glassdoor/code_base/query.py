"""
query.py — Glassdoor Reviews RAG Query Interface
=================================================
Loads the ChromaDB collection built by ingest.py, embeds your query with the
same all-MiniLM-L6-v2 model, retrieves the top-k most semantically similar
reviews, and feeds them to a local Ollama llama3 model to generate an answer.

Usage:
    python query.py [--db PATH] [--model OLLAMA_MODEL] [--top-k N]
                    [--filter-rating N] [--filter-job TEXT]
                    [--query "your question here"]

Examples:
    # Interactive mode (prompts for input in a loop)
    python query.py

    # Single one-shot query
    python query.py --query "What do software engineers say about work-life balance?"

    # Filter to only 5-star reviews from engineers
    python query.py --filter-rating 5 --filter-job "Software Engineer"

    # Use a different Ollama model
    python query.py --model mistral

Prerequisites:
    1. Ollama installed and running:   ollama serve
    2. llama3 model pulled:            ollama pull llama3
    3. ChromaDB populated:             python ingest.py
"""

import argparse
import logging
import os
import sys
import textwrap
from typing import Optional

import chromadb
import ollama
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COLLECTION_NAME    = "glassdoor_reviews"
DEFAULT_DB_PATH    = "./chroma_db"
DEFAULT_MODEL      = "llama3.2:3b"
DEFAULT_TOP_K      = 10
MAX_CONTEXT_CHARS  = 12_000  # hard cap on context sent to the LLM

# System prompt that anchors the LLM to the retrieved reviews
SYSTEM_PROMPT = """You are an expert analyst of employee reviews from Glassdoor.
You will be given a set of real employee reviews as context, followed by a user question.

Your task:
- Answer the question using ONLY the information in the provided reviews.
- Be specific and cite concrete details (job titles, ratings, pros/cons) when relevant.
- If the reviews do not contain enough information to answer the question, say so clearly.
- Do not hallucinate facts that are not in the reviews.
- Structure your answer clearly, using bullet points where appropriate.
"""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ChromaDB where-filter helpers
# ---------------------------------------------------------------------------

def build_where_filter(rating: Optional[float], job: Optional[str]) -> Optional[dict]:
    """
    Build a ChromaDB metadata filter dict.
    ChromaDB's $and operator requires a list of conditions.
    """
    conditions = []

    if rating is not None:
        # Rating is stored as a string (we cast everything to str during ingest)
        conditions.append({"rating": {"$eq": str(int(rating))}})

    if job is not None:
        conditions.append({"job": {"$contains": job}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def format_context(query_result: dict, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    Format the retrieved documents into a numbered context block for the LLM.
    Truncates gracefully if the total context would exceed max_chars.
    """
    docs      = query_result.get("documents", [[]])[0]
    distances = query_result.get("distances", [[]])[0]
    metas     = query_result.get("metadatas", [[]])[0]

    parts = []
    total_chars = 0

    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metas), start=1):
        similarity = 1.0 - dist  # cosine distance → cosine similarity
        header = (
            f"--- Review {i} "
            f"(similarity={similarity:.3f}, "
            f"rating={meta.get('rating', 'N/A')}, "
            f"job={meta.get('job', 'N/A')}, "
            f"date={meta.get('date', 'N/A')}) ---"
        )
        block = f"{header}\n{doc.strip()}"
        total_chars += len(block)
        if total_chars > max_chars and parts:
            parts.append(f"\n[... {len(docs) - i + 1} more reviews truncated to fit context window ...]")
            break
        parts.append(block)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# RAG pipeline
# ---------------------------------------------------------------------------

class GlassdoorRAG:
    def __init__(self, db_path: str, ollama_model: str, top_k: int) -> None:
        self.ollama_model = ollama_model
        self.top_k        = top_k

        # Load embedding model (same one used during ingestion)
        log.info("Loading embedding model: all-MiniLM-L6-v2 …")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Connect to ChromaDB
        abs_db = os.path.abspath(db_path)
        log.info("Connecting to ChromaDB at: %s", abs_db)
        client = chromadb.PersistentClient(
            path=abs_db,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = client.get_collection(name=COLLECTION_NAME)
        doc_count = self.collection.count()
        log.info("Collection '%s' has %s documents.", COLLECTION_NAME, f"{doc_count:,}")

        if doc_count == 0:
            log.warning(
                "The collection is empty! Run `python ingest.py` first to populate it."
            )

        # Verify Ollama is reachable and the model is available
        self._check_ollama()

    def _check_ollama(self) -> None:
        """Ping Ollama and warn if the chosen model isn't pulled yet."""
        try:
            models = [m.model for m in ollama.list().models]
            # Ollama model names may have ":latest" suffix
            normalised = [m.split(":")[0] for m in models]
            if self.ollama_model not in normalised:
                log.warning(
                    "Model '%s' not found in Ollama. Available: %s\n"
                    "Pull it with:  ollama pull %s",
                    self.ollama_model,
                    normalised,
                    self.ollama_model,
                )
            else:
                log.info("Ollama model '%s' is ready.", self.ollama_model)
        except Exception as exc:
            log.warning(
                "Could not reach Ollama (%s). "
                "Make sure `ollama serve` is running before querying.",
                exc,
            )

    def retrieve(
        self,
        query: str,
        where: Optional[dict] = None,
    ) -> dict:
        """Embed the query and retrieve top-k documents from ChromaDB."""
        query_embedding = self.embedder.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        kwargs = dict(
            query_embeddings=query_embedding,
            n_results=self.top_k,
            include=["documents", "distances", "metadatas"],
        )
        if where:
            kwargs["where"] = where

        return self.collection.query(**kwargs)

    def generate(self, query: str, context: str) -> str:
        """Send the context + query to Ollama and return the generated answer."""
        user_message = (
            f"Here are the relevant Glassdoor reviews:\n\n"
            f"{context}\n\n"
            f"---\n\n"
            f"Question: {query}\n\n"
            f"Please answer based only on the reviews above."
        )

        response = ollama.chat(
            model=self.ollama_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
        )
        return response.message.content

    def ask(
        self,
        query: str,
        filter_rating: Optional[float] = None,
        filter_job: Optional[str]      = None,
    ) -> dict:
        """
        Full RAG pipeline: retrieve → format context → generate → return result.
        Returns a dict with keys: query, context, answer, n_retrieved.
        """
        where = build_where_filter(filter_rating, filter_job)

        log.info("Retrieving top-%d documents …", self.top_k)
        results  = self.retrieve(query, where=where)
        context  = format_context(results)
        n_docs   = len(results.get("documents", [[]])[0])

        log.info("Retrieved %d documents. Generating answer with %s …", n_docs, self.ollama_model)
        answer = self.generate(query, context)

        return {
            "query":       query,
            "context":     context,
            "answer":      answer,
            "n_retrieved": n_docs,
        }


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 70

def print_separator(title: str = "") -> None:
    if title:
        pad = max(0, 70 - len(title) - 4)
        print(f"\n{'=' * 2} {title} {'=' * pad}")
    else:
        print(SEPARATOR)


def print_result(result: dict, show_context: bool = False) -> None:
    print_separator("ANSWER")
    # Word-wrap the answer at 78 chars for readability
    for line in result["answer"].splitlines():
        if line.strip():
            print(textwrap.fill(line, width=78))
        else:
            print()

    if show_context:
        print_separator(f"RETRIEVED CONTEXT ({result['n_retrieved']} reviews)")
        print(result["context"])

    print_separator()
    print(f"  Retrieved {result['n_retrieved']} reviews from ChromaDB.")


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

def interactive_loop(rag: GlassdoorRAG, args: argparse.Namespace) -> None:
    """Run a REPL-style query loop until the user types 'exit' or hits Ctrl-C."""
    print("\n" + SEPARATOR)
    print("  Glassdoor RAG — Interactive Query Mode")
    print("  Commands:  exit | quit  →  quit")
    print("             :context     →  toggle showing raw retrieved reviews")
    print("             :top-k N     →  change number of retrieved results")
    print("             :rating N    →  filter by star rating (1-5, 0=clear)")
    print("             :job TEXT    →  filter by job title keyword (empty=clear)")
    print(SEPARATOR + "\n")

    show_context  = False
    filter_rating: Optional[float] = args.filter_rating
    filter_job:    Optional[str]   = args.filter_job or None

    def print_active_filters() -> None:
        filters = []
        if filter_rating:
            filters.append(f"rating={int(filter_rating)}")
        if filter_job:
            filters.append(f"job contains '{filter_job}'")
        if filters:
            print(f"  [Active filters: {', '.join(filters)}]")

    while True:
        try:
            print_active_filters()
            query = input("Query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not query:
            continue

        # Commands
        lower = query.lower()
        if lower in ("exit", "quit"):
            print("Goodbye.")
            break

        if lower == ":context":
            show_context = not show_context
            print(f"  [Show context: {'ON' if show_context else 'OFF'}]")
            continue

        if lower.startswith(":top-k "):
            try:
                rag.top_k = int(lower.split()[1])
                print(f"  [top-k set to {rag.top_k}]")
            except (IndexError, ValueError):
                print("  Usage: :top-k <number>")
            continue

        if lower.startswith(":rating "):
            try:
                v = float(lower.split()[1])
                filter_rating = None if v == 0 else v
                print(f"  [Rating filter: {filter_rating}]")
            except (IndexError, ValueError):
                print("  Usage: :rating <1-5>  (0 to clear)")
            continue

        if lower.startswith(":job "):
            filter_job = query[5:].strip() or None
            print(f"  [Job filter: {filter_job!r}]")
            continue

        if lower == ":job":
            filter_job = None
            print("  [Job filter cleared]")
            continue

        # Regular query
        try:
            result = rag.ask(
                query,
                filter_rating=filter_rating,
                filter_job=filter_job,
            )
            print_result(result, show_context=show_context)
        except ollama.ResponseError as exc:
            log.error("Ollama error: %s", exc)
        except Exception as exc:
            log.error("Unexpected error: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Query Glassdoor reviews via RAG")
    parser.add_argument("--db",            default=DEFAULT_DB_PATH, help="ChromaDB persistence directory")
    parser.add_argument("--model",         default=DEFAULT_MODEL,   help="Ollama model name (default: llama3.2:3b)")
    parser.add_argument("--top-k",         type=int, default=DEFAULT_TOP_K, help="Number of reviews to retrieve")
    parser.add_argument("--filter-rating", type=float, default=None, help="Filter results to a specific star rating (1-5)")
    parser.add_argument("--filter-job",    default=None,            help="Filter results by job title keyword")
    parser.add_argument("--query",         default=None,            help="Run a single query non-interactively")
    parser.add_argument("--show-context",  action="store_true",     help="Print retrieved reviews alongside the answer")
    args = parser.parse_args()

    rag = GlassdoorRAG(
        db_path=args.db,
        ollama_model=args.model,
        top_k=args.top_k,
    )

    if args.query:
        # One-shot mode
        result = rag.ask(
            args.query,
            filter_rating=args.filter_rating,
            filter_job=args.filter_job,
        )
        print_result(result, show_context=args.show_context)
    else:
        # Interactive REPL
        interactive_loop(rag, args)


if __name__ == "__main__":
    main()
