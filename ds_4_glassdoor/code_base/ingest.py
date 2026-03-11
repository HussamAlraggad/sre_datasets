"""
ingest.py — Glassdoor Reviews RAG Ingestion Pipeline
=====================================================
Streams all_reviews.csv in chunks, filters low-quality rows, builds one
document per review from all text fields, embeds with all-MiniLM-L6-v2,
and stores in a persistent local ChromaDB collection.

Usage (run from any directory):
    python code_base/ingest.py [--csv PATH] [--db PATH] [--chunk-size N]
                                [--batch-size N] [--min-len N] [--limit N]

Defaults:
    --csv        <script_dir>/../all_reviews.csv   (sibling of code_base/)
    --db         <script_dir>/chroma_db
    --chunk-size 10000   (rows read from CSV at a time)
    --batch-size 512     (rows embedded and upserted at a time)
    --min-len    50      (minimum combined pros+cons character length)
    --limit      0       (0 = no limit, index everything that passes filter)

Resumability:
    Already-indexed document IDs are fetched from ChromaDB at startup.
    Any row whose ID already exists is skipped, so the script is safe to
    interrupt and restart without duplicating work.
"""

import argparse
import hashlib
import logging
import os
import sys
import time
from typing import Iterator

import chromadb
import pandas as pd
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Resolve paths relative to this script file, so the script works regardless
# of which directory it is invoked from.
SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV     = os.path.join(SCRIPT_DIR, "..", "all_reviews.csv")
DEFAULT_DB      = os.path.join(SCRIPT_DIR, "chroma_db")

COLLECTION_NAME = "glassdoor_reviews"

# Columns stored as metadata (must be scalar / JSON-serialisable)
METADATA_COLUMNS = [
    "rating", "status", "Recommend", "CEO Approval", "Business Outlook",
    "Career Opportunities", "Compensation and Benefits", "Senior Management",
    "Work/Life Balance", "Culture & Values", "Diversity & Inclusion",
    "firm_link", "date", "job",
]

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
# Helpers
# ---------------------------------------------------------------------------

def make_doc_id(row_index: int, firm_link: str) -> str:
    """Deterministic, collision-resistant document ID for a review row."""
    raw = f"{row_index}|{firm_link}"
    return hashlib.sha1(raw.encode()).hexdigest()


def csv_chunk_iter(csv_path: str, chunk_size: int) -> Iterator[pd.DataFrame]:
    """Yield successive DataFrame chunks from a CSV file."""
    return pd.read_csv(
        csv_path,
        chunksize=chunk_size,
        dtype=str,           # read everything as str to avoid mixed-type issues
        on_bad_lines="skip",
        low_memory=False,
    )


def estimate_total_rows(csv_path: str) -> int:
    """Fast row-count estimate by counting newlines."""
    log.info("Estimating row count (scanning newlines)…")
    count = 0
    with open(csv_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            count += chunk.count(b"\n")
    return max(count - 1, 0)  # subtract header


def process_chunk(
    chunk_df: pd.DataFrame,
    chunk_start_row: int,
    min_len: int,
    existing_ids: set,
) -> tuple[list[str], list[str], list[dict]]:
    """
    Vectorised processing of a whole DataFrame chunk at once.

    Returns three parallel lists: ids, documents, metadatas.
    Uses pandas vectorised operations instead of iterrows() for speed.
    """
    df = chunk_df.copy()

    # --- Fill NaN with empty string for all columns ---
    df = df.fillna("")

    # --- Filter: combined pros+cons length >= min_len ---
    pros_len = df["pros"].str.strip().str.len() if "pros" in df.columns else pd.Series(0, index=df.index)
    cons_len = df["cons"].str.strip().str.len() if "cons" in df.columns else pd.Series(0, index=df.index)
    mask = (pros_len + cons_len) >= min_len
    df = df[mask]

    if df.empty:
        return [], [], []

    # --- Build document strings vectorised ---
    def col(name: str) -> pd.Series:
        return df[name].str.strip() if name in df.columns else pd.Series("", index=df.index)

    docs = (
        "Title: "  + col("title")    + "\n" +
        "Status: " + col("status")   + "\n" +
        "Job: "    + col("job")      + "\n" +
        "Rating: " + col("rating")   + "\n" +
        "Date: "   + col("date")     + "\n" +
        "Pros: "   + col("pros")     + "\n" +
        "Cons: "   + col("cons")     + "\n" +
        "Advice: " + col("advice")   + "\n" +
        "Firm: "   + col("firm_link")
    )
    # Strip trailing newlines/whitespace on empty fields
    docs = docs.str.strip()

    # --- Build IDs using the original CSV row numbers ---
    # chunk_start_row is the 1-based index of the first row of this chunk
    row_numbers = range(chunk_start_row, chunk_start_row + len(chunk_df))
    # We need row numbers only for the rows that passed the filter
    filtered_row_numbers = [
        chunk_start_row + i
        for i, passed in enumerate(mask)
        if passed
    ]
    firm_links = col("firm_link").tolist()
    ids = [
        make_doc_id(rn, fl)
        for rn, fl in zip(filtered_row_numbers, firm_links)
    ]

    # --- Dedup against already-indexed IDs ---
    keep = [doc_id not in existing_ids for doc_id in ids]
    ids   = [v for v, k in zip(ids,          keep) if k]
    docs  = [v for v, k in zip(docs.tolist(), keep) if k]
    df_keep = df[keep]

    if not ids:
        return [], [], []

    # --- Build metadata dicts vectorised ---
    metadatas = []
    for _, row in df_keep.iterrows():
        meta = {}
        for col_name in METADATA_COLUMNS:
            val = row.get(col_name, "")
            meta[col_name] = str(val).strip() if val else ""
        metadatas.append(meta)

    return ids, docs, metadatas


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Glassdoor reviews into ChromaDB")
    parser.add_argument("--csv",        default=DEFAULT_CSV,       help="Path to all_reviews.csv")
    parser.add_argument("--db",         default=DEFAULT_DB,        help="ChromaDB persistence directory")
    parser.add_argument("--chunk-size", type=int, default=10_000,  help="Rows read from CSV per iteration")
    parser.add_argument("--batch-size", type=int, default=512,     help="Rows embedded/upserted per batch")
    parser.add_argument("--min-len",    type=int, default=50,      help="Min combined pros+cons char length")
    parser.add_argument("--limit",      type=int, default=0,       help="Max rows to index (0 = unlimited)")
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv)
    db_path  = os.path.abspath(args.db)

    if not os.path.exists(csv_path):
        log.error("CSV not found: %s", csv_path)
        sys.exit(1)

    log.info("CSV path : %s", csv_path)
    log.info("DB path  : %s", db_path)
    log.info("Min len  : %d chars (pros+cons combined)", args.min_len)
    log.info("Limit    : %s", args.limit if args.limit else "unlimited")

    # ------------------------------------------------------------------
    # 1. Load embedding model
    # ------------------------------------------------------------------
    log.info("Loading embedding model: all-MiniLM-L6-v2 …")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    log.info("Model loaded. Embedding dimension: %d", model.get_sentence_embedding_dimension())

    # ------------------------------------------------------------------
    # 2. Connect to / create ChromaDB collection
    # ------------------------------------------------------------------
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Fetch all existing IDs for resumability
    log.info("Fetching existing IDs from ChromaDB (for resumability)…")
    existing_ids: set[str] = set()
    offset, page_size = 0, 100_000
    while True:
        result = collection.get(limit=page_size, offset=offset, include=[])
        ids = result.get("ids", [])
        if not ids:
            break
        existing_ids.update(ids)
        offset += len(ids)
        if len(ids) < page_size:
            break
    log.info("Already indexed: %d documents", len(existing_ids))

    # ------------------------------------------------------------------
    # 3. Stream CSV, filter, embed, upsert — fully vectorised per chunk
    # ------------------------------------------------------------------
    total_rows_estimate = estimate_total_rows(csv_path)
    log.info("Estimated total rows (excl. header): ~%s", f"{total_rows_estimate:,}")

    indexed_this_run = 0
    total_rows_seen  = 0
    skipped_filter   = 0
    skipped_existing = 0
    start_time       = time.time()

    # Pending buffer across chunks (for the final partial batch)
    buf_ids:   list[str]  = []
    buf_docs:  list[str]  = []
    buf_metas: list[dict] = []

    def flush_buffer() -> None:
        nonlocal indexed_this_run
        if not buf_docs:
            return
        embeddings = model.encode(
            buf_docs,
            batch_size=args.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()
        collection.upsert(
            ids=buf_ids,
            documents=buf_docs,
            embeddings=embeddings,
            metadatas=buf_metas,
        )
        indexed_this_run += len(buf_ids)
        buf_ids.clear()
        buf_docs.clear()
        buf_metas.clear()

    pbar = tqdm(
        total=total_rows_estimate,
        unit="rows",
        desc="Ingesting",
        dynamic_ncols=True,
    )

    done = False
    try:
        for chunk_df in csv_chunk_iter(csv_path, args.chunk_size):
            chunk_size_actual = len(chunk_df)
            chunk_start = total_rows_seen + 1
            total_rows_seen += chunk_size_actual
            pbar.update(chunk_size_actual)

            # Count rows that failed the filter in this chunk
            if "pros" in chunk_df.columns and "cons" in chunk_df.columns:
                pros_len = chunk_df["pros"].fillna("").str.strip().str.len()
                cons_len = chunk_df["cons"].fillna("").str.strip().str.len()
                skipped_filter += int(((pros_len + cons_len) < args.min_len).sum())

            # Vectorised processing
            ids, docs, metas = process_chunk(
                chunk_df, chunk_start, args.min_len, existing_ids
            )

            # Count skipped-existing
            # (ids returned already had existing ones removed)
            raw_passed = chunk_size_actual - int(
                ((chunk_df["pros"].fillna("").str.strip().str.len() +
                  chunk_df["cons"].fillna("").str.strip().str.len()) < args.min_len).sum()
            ) if "pros" in chunk_df.columns else chunk_size_actual
            skipped_existing += raw_passed - len(ids)

            # Trim to --limit if needed (before buffering)
            if args.limit:
                remaining = args.limit - indexed_this_run - len(buf_ids)
                if remaining <= 0:
                    ids, docs, metas = [], [], []
                elif len(ids) > remaining:
                    ids   = ids[:remaining]
                    docs  = docs[:remaining]
                    metas = metas[:remaining]

            buf_ids.extend(ids)
            buf_docs.extend(docs)
            buf_metas.extend(metas)

            # Flush whenever buffer reaches batch_size
            while len(buf_ids) >= args.batch_size:
                batch_ids   = buf_ids[:args.batch_size]
                batch_docs  = buf_docs[:args.batch_size]
                batch_metas = buf_metas[:args.batch_size]
                del buf_ids[:args.batch_size]
                del buf_docs[:args.batch_size]
                del buf_metas[:args.batch_size]

                embeddings = model.encode(
                    batch_docs,
                    batch_size=args.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                ).tolist()
                collection.upsert(
                    ids=batch_ids,
                    documents=batch_docs,
                    embeddings=embeddings,
                    metadatas=batch_metas,
                )
                indexed_this_run += len(batch_ids)
                existing_ids.update(batch_ids)

            if args.limit and (indexed_this_run + len(buf_ids)) >= args.limit:
                log.info("Reached --limit %d, stopping early.", args.limit)
                done = True
                break

        # Flush remaining
        flush_buffer()

    except KeyboardInterrupt:
        log.warning("Interrupted! Flushing remaining buffer before exit…")
        flush_buffer()
        log.info("Progress saved. Re-run to continue from where you left off.")

    finally:
        pbar.close()

    # ------------------------------------------------------------------
    # 4. Summary
    # ------------------------------------------------------------------
    elapsed     = time.time() - start_time
    total_in_db = collection.count()
    throughput  = indexed_this_run / elapsed if elapsed > 0 else 0

    log.info("=" * 60)
    log.info("Ingestion complete")
    log.info("  Total CSV rows seen    : %s", f"{total_rows_seen:,}")
    log.info("  Skipped (filter)       : %s", f"{skipped_filter:,}")
    log.info("  Skipped (already in DB): %s", f"{skipped_existing:,}")
    log.info("  Indexed this run       : %s", f"{indexed_this_run:,}")
    log.info("  Total documents in DB  : %s", f"{total_in_db:,}")
    log.info("  Elapsed time           : %.1f s (%.1f min)", elapsed, elapsed / 60)
    log.info("  Throughput             : %.0f docs/sec", throughput)
    log.info("  ChromaDB path          : %s", db_path)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
