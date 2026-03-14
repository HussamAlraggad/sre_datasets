"""
config.py
=========
Single source of truth for all tunable parameters.
Edit values here — no other file needs to change.
"""

from pathlib import Path

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent.resolve()
DATASET_PATH    = BASE_DIR / "all_reviews.csv"
FAISS_DIR       = BASE_DIR / "faiss_index"
SHARD_DIR       = FAISS_DIR / "shards"
MERGED_INDEX    = FAISS_DIR / "merged.index"
MERGED_PKL      = FAISS_DIR / "merged.pkl"
PROGRESS_FILE   = FAISS_DIR / "progress.json"
PROMPTS_DIR     = BASE_DIR / "prompts"
OUTPUTS_DIR     = BASE_DIR / "outputs"

# ─────────────────────────────────────────────
# Dataset ingestion
# ─────────────────────────────────────────────
# Columns from all_reviews.csv that are combined into the review text
TEXT_COLUMNS = ["title", "pros", "cons", "advice", "job"]

# Number of CSV rows loaded per pandas chunk (memory vs. speed trade-off)
# 50 000 rows ≈ 200–400 MB RAM per chunk; safe for most systems
CSV_CHUNK_SIZE = 50_000

# Number of texts sent to the embedding model per GPU forward pass
# Lower  → less VRAM, more iterations   |   Higher → more VRAM, fewer iterations
# 256 is safe for all-mpnet-base-v2 on 8 GB VRAM; raise to 512 for all-MiniLM-L6-v2
EMBED_BATCH_SIZE = 256

# ─────────────────────────────────────────────
# Embedding model
# ─────────────────────────────────────────────
# Options (HuggingFace sentence-transformers):
#   "sentence-transformers/all-MiniLM-L6-v2"   → fast, 384-dim,  ~80 MB
#   "sentence-transformers/all-mpnet-base-v2"   → best quality, 768-dim, ~420 MB
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cuda"   # "cuda" | "cpu"

# ─────────────────────────────────────────────
# FAISS index
# ─────────────────────────────────────────────
# Each shard file holds this many embedded vectors before flushing to disk.
# 50 000 vectors × 384 dims × 4 bytes ≈ 73 MB per shard (all-MiniLM)
# 50 000 vectors × 768 dims × 4 bytes ≈ 147 MB per shard (all-mpnet)
SHARD_SIZE = 50_000

# FAISS index type used for each shard.
# "Flat"  → exact search, no training needed  (recommended for correctness)
# "IVF"   → approximate, faster at query time (requires training pass)
FAISS_INDEX_TYPE = "Flat"

# ─────────────────────────────────────────────
# LLM (Ollama)
# ─────────────────────────────────────────────
OLLAMA_MODEL    = "llama3:8b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Generation parameters
LLM_TEMPERATURE  = 0.1   # Low temp → deterministic, structured output
LLM_NUM_CTX      = 4096  # Context window (tokens); llama3:8b supports up to 8192
LLM_NUM_PREDICT  = 8192  # Max tokens to generate per chain call

# ─────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────
# Number of reviews to retrieve per query (top-k similarity search)
RETRIEVER_K = 20

# ─────────────────────────────────────────────
# Generation / SRS
# ─────────────────────────────────────────────
# The focal query used to drive retrieval and all chains.
# Can be overridden at runtime via CLI argument in 04_generate_srs.py.
DEFAULT_QUERY = (
    "What features, tools, and improvements do employees and users want "
    "in a workplace review and rating web application?"
)

# Project metadata written into the SRS header
SRS_PROJECT_NAME    = "Glassdoor-Style Workplace Review Web Application"
SRS_VERSION         = "1.0"
SRS_AUTHORS         = ["Auto-generated via RAG pipeline"]
SRS_STANDARD        = "IEEE 830 / IEEE 29148"
