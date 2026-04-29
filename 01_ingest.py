"""
01_ingest.py
============
Pipeline Stage 1 — Data Ingestion & FAISS Index Building

What this script does
---------------------
1. Reads dataset CSV in configurable-sized chunks (default 50,000 rows).
   - Supports ANY CSV structure (not just Glassdoor)
   - Uses dataset_config.yaml for column mapping
   - Falls back to hardcoded defaults if no config found
2. Combines the relevant text columns into a single document string per row
   - This becomes the document stored in FAISS
   - Uses CsvAdapter for flexible column handling
3. Embeds each chunk on the GPU using HuggingFaceEmbeddings.
4. Writes one FAISS shard file per chunk to faiss_index/shards/.
5. Tracks progress in faiss_index/progress.json so the run can be RESUMED if
   interrupted (just re-run the script — already-done shards are skipped).
6. After all shards are built, merges them into a single faiss_index/merged.index
   plus the companion faiss_index/merged.pkl (docstore) that LangChain needs.

Usage
-----
    python 01_ingest.py                  # full run / resume
    python 01_ingest.py --merge-only     # skip embedding, just re-merge shards
    python 01_ingest.py --reset          # delete progress + shards, start fresh
    python 01_ingest.py --config dataset_config.yaml  # use custom config

Configuration
--------------
    Place dataset_config.yaml in the project root with:
      - csv_path: Path to your CSV file
      - column_mappings.text_columns: List of columns to combine
      - ingestion.chunk_size: CSV chunk size (default 50000)
    
    Or run: python 00_init_wizard.py

Dependencies (install before running)
--------------------------------------
    pip install langchain langchain-community langchain-huggingface faiss-cpu tqdm
    # faiss-gpu can be used instead of faiss-cpu if your build supports it
"""

import argparse
import json
import os
import pickle
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

# ── project config ────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DATASET_PATH,
    SHARD_DIR,
    MERGED_INDEX,
    MERGED_PKL,
    PROGRESS_FILE,
    TEXT_COLUMNS,
    CSV_CHUNK_SIZE,
    EMBED_BATCH_SIZE,
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    SHARD_SIZE,
)
from utils import CsvAdapter, ConfigValidator

# ── lazy imports (installed by user) ─────────────────────────────────────────
def _import_faiss():
    try:
        import faiss
        return faiss
    except ImportError:
        print("[ERROR] faiss is not installed.")
        print("  Run:  pip install faiss-cpu   (or faiss-gpu if your CUDA build supports it)")
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
            print("[ERROR] langchain-huggingface / langchain-community is not installed.")
            print("  Run:  pip install langchain-huggingface langchain-community")
            sys.exit(1)


# ── configuration loading ──────────────────────────────────────────────────────

def _load_config(config_path: Path = None) -> dict:
    """
    Load configuration from dataset_config.yaml or use defaults.
    
    Args:
        config_path: Path to dataset_config.yaml (default: dataset_config.yaml)
    
    Returns:
        Configuration dictionary with keys: csv_path, text_columns, chunk_size
    """
    if config_path is None:
        config_path = Path("dataset_config.yaml")
    
    if config_path.exists():
        try:
            config = ConfigValidator.load_config(config_path)
            return {
                "csv_path": Path(config.get("csv_path", DATASET_PATH)),
                "text_columns": config.get("column_mappings", {}).get("text_columns", TEXT_COLUMNS),
                "chunk_size": config.get("ingestion", {}).get("chunk_size", CSV_CHUNK_SIZE),
            }
        except Exception as e:
            print(f"[WARN] Failed to load config from {config_path}: {e}")
            print(f"[WARN] Using default configuration")
    
    # Fallback to defaults
    return {
        "csv_path": DATASET_PATH,
        "text_columns": TEXT_COLUMNS,
        "chunk_size": CSV_CHUNK_SIZE,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_text(row: pd.Series, text_columns: list) -> str:
    """
    Combine relevant columns into a single document string.
    
    Uses CsvAdapter for flexible column handling.
    """
    parts = []
    for col in text_columns:
        val = row.get(col, "")
        if pd.notna(val) and str(val).strip():
            parts.append(f"{col.upper()}: {str(val).strip()}")
    # Add rating and date as lightweight metadata so they can appear in retrieval
    rating = row.get("rating", "")
    date   = row.get("date", "")
    if pd.notna(rating):
        parts.append(f"RATING: {rating}")
    if pd.notna(date):
        parts.append(f"DATE: {str(date).strip()}")
    return " | ".join(parts) if parts else ""


def _load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed_shards": [], "total_rows_processed": 0}


def _save_progress(progress: dict):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def _shard_path(shard_idx: int) -> Path:
    return SHARD_DIR / f"shard_{shard_idx:05d}.index"


def _shard_meta_path(shard_idx: int) -> Path:
    return SHARD_DIR / f"shard_{shard_idx:05d}.meta.pkl"


# ─────────────────────────────────────────────────────────────────────────────
# Core: embed one chunk and write a shard
# ─────────────────────────────────────────────────────────────────────────────

def embed_and_save_shard(
    texts: list[str],
    metadata: list[dict],
    shard_idx: int,
    embed_fn,
    faiss,
):
    """
    Embed `texts` on the GPU in sub-batches, build a FAISS FlatL2 index shard,
    and persist the index + metadata to disk.
    """
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    all_vectors = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        vecs  = embed_fn.embed_documents(batch)   # returns list[list[float]]
        all_vectors.extend(vecs)

    vectors_np = np.array(all_vectors, dtype="float32")
    dim        = vectors_np.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(vectors_np)

    faiss.write_index(index, str(_shard_path(shard_idx)))

    with open(_shard_meta_path(shard_idx), "wb") as f:
        pickle.dump({"texts": texts, "metadata": metadata}, f)

    return len(texts)


# ─────────────────────────────────────────────────────────────────────────────
# Merge all shards → single FAISS index + docstore pkl
# ─────────────────────────────────────────────────────────────────────────────

def merge_shards(faiss):
    """
    Merge every shard_NNNNN.index file into a single merged.index.
    Also build the companion merged.pkl that stores the raw texts for LangChain.
    """
    shard_files = sorted(SHARD_DIR.glob("shard_?????.index"))
    if not shard_files:
        print("[ERROR] No shard files found in", SHARD_DIR)
        sys.exit(1)

    print(f"\n[MERGE] Found {len(shard_files)} shards — merging …")

    # Read first shard to get dimension
    first = faiss.read_index(str(shard_files[0]))
    dim   = first.d

    merged_index = faiss.IndexFlatL2(dim)
    all_texts    = []
    all_meta     = []

    for sf in tqdm(shard_files, desc="Merging shards"):
        idx  = faiss.read_index(str(sf))
        vecs = faiss.rev_swig_ptr(idx.get_xb(), idx.ntotal * idx.d)
        vecs = np.frombuffer(vecs, dtype="float32").reshape(idx.ntotal, idx.d).copy()
        merged_index.add(vecs)

        meta_file = sf.with_suffix("").with_suffix(".meta.pkl")
        if meta_file.exists():
            with open(meta_file, "rb") as f:
                meta = pickle.load(f)
            all_texts.extend(meta["texts"])
            all_meta.extend(meta["metadata"])

    MERGED_INDEX.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(merged_index, str(MERGED_INDEX))

    with open(MERGED_PKL, "wb") as f:
        pickle.dump({"texts": all_texts, "metadata": all_meta}, f)

    print(f"[MERGE] Done. Total vectors: {merged_index.ntotal:,}")
    print(f"        Index  → {MERGED_INDEX}")
    print(f"        Docstore → {MERGED_PKL}")


# ─────────────────────────────────────────────────────────────────────────────
# Main ingestion loop
# ─────────────────────────────────────────────────────────────────────────────

def run_ingest(config: dict):
    faiss           = _import_faiss()
    HuggingFaceEmb  = _import_embeddings()

    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL} on {EMBEDDING_DEVICE}")
    embed_fn = HuggingFaceEmb(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": EMBEDDING_DEVICE},
        encode_kwargs={"batch_size": EMBED_BATCH_SIZE, "normalize_embeddings": True},
    )
    print("[INFO] Embedding model loaded.\n")

    progress          = _load_progress()
    completed_shards  = set(progress["completed_shards"])
    total_rows        = progress["total_rows_processed"]

    dataset_path = config["csv_path"]
    text_columns = config["text_columns"]
    chunk_size = config["chunk_size"]

    print(f"[INFO] Dataset: {dataset_path}")
    print(f"[INFO] Text columns: {text_columns}")
    print(f"[INFO] CSV chunk size: {chunk_size:,} rows")
    print(f"[INFO] Already completed shards: {len(completed_shards)}")
    print(f"[INFO] Rows processed so far:    {total_rows:,}\n")

    shard_idx     = max(completed_shards, default=-1) + 1
    chunk_iter    = pd.read_csv(
        dataset_path,
        chunksize=chunk_size,
        low_memory=False,
        on_bad_lines="skip",
    )

    # If resuming, fast-forward the CSV iterator past already-done chunks
    chunks_to_skip = len(completed_shards)
    if chunks_to_skip:
        print(f"[RESUME] Skipping {chunks_to_skip} already-processed CSV chunks …")
        for _ in tqdm(range(chunks_to_skip), desc="Fast-forwarding CSV"):
            try:
                next(chunk_iter)
            except StopIteration:
                break
        print()

    t_start = time.time()

    for chunk_num, chunk_df in enumerate(chunk_iter, start=len(completed_shards)):
        # Build document texts
        texts    = []
        metadata = []
        for _, row in chunk_df.iterrows():
            text = _build_text(row, text_columns)
            if text:
                texts.append(text)
                metadata.append({
                    "rating":    str(row.get("rating", "")),
                    "job":       str(row.get("job", "")),
                    "date":      str(row.get("date", "")),
                    "firm_link": str(row.get("firm_link", "")),
                    "status":    str(row.get("status", "")),
                })

        if not texts:
            print(f"[WARN]  Chunk {chunk_num} produced no text — skipping.")
            completed_shards.add(chunk_num)
            _save_progress({
                "completed_shards": sorted(completed_shards),
                "total_rows_processed": total_rows,
            })
            continue

        n_saved = embed_and_save_shard(texts, metadata, shard_idx, embed_fn, faiss)
        total_rows      += n_saved
        completed_shards.add(chunk_num)

        _save_progress({
            "completed_shards": sorted(completed_shards),
            "total_rows_processed": total_rows,
        })

        elapsed  = time.time() - t_start
        rows_sec = total_rows / elapsed if elapsed > 0 else 0
        print(
            f"  Shard {shard_idx:05d} | chunk {chunk_num:5d} | "
            f"{n_saved:,} docs | "
            f"total {total_rows:,} rows | "
            f"{rows_sec:,.0f} rows/s"
        )

        shard_idx += 1

    print(f"\n[INFO] Embedding complete. Total rows embedded: {total_rows:,}")
    print(f"[INFO] Time elapsed: {(time.time() - t_start) / 60:.1f} minutes\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SRE-RAG — Data Ingestion Pipeline")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("dataset_config.yaml"),
        help="Path to dataset_config.yaml (default: dataset_config.yaml)",
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Skip embedding; just merge existing shards into merged.index",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all shards + progress and start fresh",
    )
    args = parser.parse_args()

    if args.reset:
        if SHARD_DIR.exists():
            shutil.rmtree(SHARD_DIR)
            print(f"[RESET] Deleted {SHARD_DIR}")
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            print(f"[RESET] Deleted {PROGRESS_FILE}")
        if MERGED_INDEX.exists():
            MERGED_INDEX.unlink()
        if MERGED_PKL.exists():
            MERGED_PKL.unlink()
        print("[RESET] Clean slate. Re-run without --reset to start ingestion.\n")
        return

    # Load configuration
    config = _load_config(args.config)
    print(f"[INFO] Configuration loaded: {config}\n")

    faiss = _import_faiss()

    if not args.merge_only:
        run_ingest(config)

    merge_shards(faiss)
    print("\n[DONE] FAISS index is ready. You can now run 04_generate_srs.py.\n")


if __name__ == "__main__":
    main()
