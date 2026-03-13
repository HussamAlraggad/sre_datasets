"""
02_retriever.py
===============
Pipeline Stage 2 — FAISS Retriever

Loads the merged FAISS index built by 01_ingest.py and wraps it as a
LangChain-compatible retriever.  This module is imported by 03_chains.py
and 04_generate_srs.py; it can also be run standalone for sanity-checking
the index.

Standalone usage
----------------
    python 02_retriever.py "What features do users want in a review platform?"
    python 02_retriever.py --k 10 "salary transparency tools"
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    EMBED_BATCH_SIZE,
    MERGED_INDEX,
    MERGED_PKL,
    RETRIEVER_K,
)


# ─────────────────────────────────────────────────────────────────────────────
# Lazy imports
# ─────────────────────────────────────────────────────────────────────────────

def _import_faiss():
    try:
        import faiss
        return faiss
    except ImportError:
        print("[ERROR] faiss not installed.  Run: pip install faiss-cpu")
        sys.exit(1)


def _import_embeddings():
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings
    except ImportError:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings
        except ImportError:
            print("[ERROR] langchain-huggingface not installed.")
            print("  Run:  pip install langchain-huggingface langchain-community")
            sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Simple retriever class (no LangChain vector-store dependency)
# ─────────────────────────────────────────────────────────────────────────────

class FAISSRetriever:
    """
    Lightweight retriever that:
    1. Embeds a query on the GPU.
    2. Runs L2 similarity search against the merged FAISS index.
    3. Returns the top-k raw review strings.

    This avoids LangChain's FAISS wrapper quirks with custom indexes while
    still letting 03_chains.py pass retrieved text directly into prompts.
    """

    def __init__(self, k: int = RETRIEVER_K):
        self.k      = k
        self.faiss  = _import_faiss()
        self._load_index()
        self._load_embedder()

    # ── index + docstore ──────────────────────────────────────────────────────

    def _load_index(self):
        if not MERGED_INDEX.exists():
            raise FileNotFoundError(
                f"Merged FAISS index not found at {MERGED_INDEX}.\n"
                "  Please run:  python 01_ingest.py"
            )
        print(f"[RETRIEVER] Loading FAISS index from {MERGED_INDEX} …", end=" ", flush=True)
        self.index = self.faiss.read_index(str(MERGED_INDEX))
        print(f"OK  ({self.index.ntotal:,} vectors, dim={self.index.d})")

        if not MERGED_PKL.exists():
            raise FileNotFoundError(
                f"Docstore not found at {MERGED_PKL}.\n"
                "  Please run:  python 01_ingest.py"
            )
        with open(MERGED_PKL, "rb") as f:
            store = pickle.load(f)
        self.texts    = store["texts"]     # list[str]
        self.metadata = store["metadata"]  # list[dict]
        print(f"[RETRIEVER] Docstore loaded: {len(self.texts):,} documents.")

    # ── embedding model ───────────────────────────────────────────────────────

    def _load_embedder(self):
        HuggingFaceEmb = _import_embeddings()
        print(f"[RETRIEVER] Loading embedding model: {EMBEDDING_MODEL} …", end=" ", flush=True)
        self.embedder = HuggingFaceEmb(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"batch_size": EMBED_BATCH_SIZE, "normalize_embeddings": True},
        )
        print("OK")

    # ── public interface ──────────────────────────────────────────────────────

    def retrieve(self, query: str, k: int | None = None) -> list[dict]:
        """
        Returns a list of dicts:
            {"text": str, "metadata": dict, "score": float}
        sorted by ascending L2 distance (lower = more similar).
        """
        k = k or self.k
        q_vec = np.array(
            self.embedder.embed_query(query), dtype="float32"
        ).reshape(1, -1)

        distances, indices = self.index.search(q_vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:           # FAISS returns -1 for empty slots
                continue
            results.append({
                "text":     self.texts[idx],
                "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                "score":    float(dist),
            })
        return results

    def retrieve_texts(self, query: str, k: int | None = None) -> list[str]:
        """Convenience wrapper — returns only the text strings."""
        return [r["text"] for r in self.retrieve(query, k)]


# ─────────────────────────────────────────────────────────────────────────────
# Standalone sanity-check
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Glassdoor RAG — retriever test")
    parser.add_argument("query", nargs="?", default="What features do users want?")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    retriever = FAISSRetriever(k=args.k)
    results   = retriever.retrieve(args.query)

    print(f"\n[QUERY] {args.query}")
    print(f"[TOP-{args.k} RESULTS]\n{'─' * 80}")
    for i, r in enumerate(results, 1):
        print(f"\n#{i}  (L2 dist: {r['score']:.4f})")
        print(f"    {r['text'][:300]} …")
    print("─" * 80)


if __name__ == "__main__":
    main()
