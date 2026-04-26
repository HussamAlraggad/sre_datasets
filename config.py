"""
config.py
=========
Configuration management for the SRE-RAG tool.

Supports two modes:
  1. LEGACY MODE: Hardcoded Glassdoor settings (backward compatible)
  2. NEW MODE: Load from dataset_config.yaml (recommended for new datasets)

To use a dataset_config.yaml file, pass --config path/to/config.yaml to the pipeline scripts.
Otherwise, the tool falls back to hardcoded defaults below.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent.resolve()
FAISS_DIR       = BASE_DIR / "faiss_index"
SHARD_DIR       = FAISS_DIR / "shards"
MERGED_INDEX    = FAISS_DIR / "merged.index"
MERGED_PKL      = FAISS_DIR / "merged.pkl"
PROGRESS_FILE   = FAISS_DIR / "progress.json"
PROMPTS_DIR     = BASE_DIR / "prompts"
OUTPUTS_DIR     = BASE_DIR / "outputs"

# ─────────────────────────────────────────────
# LEGACY DEFAULTS (Glassdoor)
# ─────────────────────────────────────────────
# These are used if no dataset_config.yaml is provided.
# For new datasets, use the wizard to create a dataset_config.yaml instead.

DATASET_PATH    = BASE_DIR / "all_reviews.csv"
TEXT_COLUMNS    = ["title", "pros", "cons", "advice", "job"]
CSV_CHUNK_SIZE  = 50_000
EMBED_BATCH_SIZE = 256
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cuda"
SHARD_SIZE      = 50_000
FAISS_INDEX_TYPE = "Flat"
OLLAMA_MODEL    = "llama3:8b"
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_TEMPERATURE  = 0.1
LLM_NUM_CTX      = 4096
LLM_NUM_PREDICT  = 8192
RETRIEVER_K     = 20
DEFAULT_QUERY   = (
    "What features, tools, and improvements do employees and users want "
    "in a workplace review and rating web application?"
)
SRS_PROJECT_NAME    = "Glassdoor-Style Workplace Review Web Application"
SRS_VERSION         = "1.0"
SRS_AUTHORS         = ["Auto-generated via RAG pipeline"]
SRS_STANDARD        = "IEEE 830 / IEEE 29148"


# ─────────────────────────────────────────────
# Configuration Loading
# ─────────────────────────────────────────────

def load_dataset_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a dataset_config.yaml file.

    Args:
        config_path: Path to the YAML config file

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    from utils import ConfigValidator

    config_path = Path(config_path)
    is_valid, errors = ConfigValidator.validate_file(config_path)

    if not is_valid:
        raise ValueError(f"Invalid config file:\n" + "\n".join(errors))

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get configuration, either from file or defaults.

    Args:
        config_path: Optional path to dataset_config.yaml

    Returns:
        Configuration dictionary with all settings
    """
    if config_path:
        return load_dataset_config(config_path)
    else:
        # Return legacy defaults
        return {
            "dataset_name": "Glassdoor Reviews",
            "csv_path": str(DATASET_PATH),
            "column_mappings": {
                "text_columns": TEXT_COLUMNS,
                "metadata_columns": [],
            },
            "llm_settings": {
                "model": OLLAMA_MODEL,
                "ollama_url": OLLAMA_BASE_URL,
                "temperature": LLM_TEMPERATURE,
                "num_ctx": LLM_NUM_CTX,
                "num_predict": LLM_NUM_PREDICT,
            },
            "output_formats": ["ieee_830"],
            "srs_metadata": {
                "project_name": SRS_PROJECT_NAME,
                "version": SRS_VERSION,
                "authors": SRS_AUTHORS,
            },
        }
