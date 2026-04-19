# Execution Guide
## Glassdoor RAG — Software Requirements Engineering Pipeline

> **Keep this document open while running the project from the repository root.**
> Every step is listed in order. Do not skip steps.
> Key root-level files: `01_ingest.py`, `02_retriever.py`, `03_chains.py`, `04_generate_srs.py`, `config.py`, `prompts/`, `faiss_index/`, `outputs/`, `STUDY_GUIDE.md`.
> Place `all_reviews.csv` in the repository root before running Stage 1.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Install Dependencies](#2-install-dependencies)
3. [Pull the LLM Model](#3-pull-the-llm-model)
4. [Verify the Setup](#4-verify-the-setup)
5. [Stage 1 — Build the FAISS Index](#5-stage-1--build-the-faiss-index)
6. [Stage 2 — Test the Retriever](#6-stage-2--test-the-retriever)
7. [Stage 3 — Generate the SRS](#7-stage-3--generate-the-srs)
8. [Output Files Reference](#8-output-files-reference)
9. [Configuration Cheat-Sheet](#9-configuration-cheat-sheet)
10. [Troubleshooting](#10-troubleshooting)
11. [Changelog](#11-changelog)

---

## 1. System Requirements

| Component | Required | My Setup |
|---|---|---|
| Python | 3.10+ | 3.13.7 |
| CUDA | 11.7+ | 13.0 |
| GPU VRAM | 6 GB+ | 8 GB (RTX 5060 Laptop) |
| RAM | 16 GB+ recommended | — |
| Disk space (index) | ~30–80 GB (full dataset) | — |
| Ollama | installed & running | installed |

---

## 2. Install Dependencies

This project runs on a Debian/Ubuntu system with an externally managed Python
environment (PEP 668). The `--break-system-packages` flag is required and is
safe on a personal dev machine where AI/ML libraries are already installed
outside apt.

```bash
pip install --break-system-packages \
    langchain \
    langchain-community \
    langchain-ollama \
    langchain-huggingface \
    faiss-cpu \
    tqdm \
    numpy \
    pandas
```

> **Note on `faiss-cpu` vs `faiss-gpu`:**
> `faiss-cpu` is used here. The GPU handles the **embedding model**
> (sentence-transformers), not the FAISS index itself. `faiss-gpu` on PyPI
> is broken for CUDA 12+. `faiss-cpu` gives identical retrieval quality.

Verify the install:

```bash
python3 -c "
import faiss; print('faiss:', faiss.__version__)
import langchain; print('langchain:', langchain.__version__)
from langchain_ollama import ChatOllama; print('langchain-ollama: OK')
from langchain_huggingface import HuggingFaceEmbeddings; print('langchain-huggingface: OK')
import torch; print('torch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
"
```

**Confirmed working versions (installed 2026-03-13):**

| Package | Version |
|---|---|
| faiss-cpu | 1.13.2 |
| langchain | 1.2.12 |
| langchain-ollama | latest |
| langchain-huggingface | latest |
| torch | 2.10.0+cu128 |
| numpy | 2.2.4 |
| pandas | 3.0.1 |
| tqdm | 4.67.1 |

---

## 3. Pull the LLM Model

> **Already done** as of 2026-03-13 — `llama3:8b` (4.7 GB) is present.
> Skip this step unless you reset Ollama or switch machines.

```bash
ollama pull llama3:8b
```

Verify:

```bash
ollama list
# Should show: llama3:8b   365c0bd3c000   4.7 GB
```

Make sure Ollama is running in the background before any generation step:

```bash
ollama serve &   # or run in a separate terminal
```

> Ollama on this system starts automatically — check with `curl http://localhost:11434/api/tags`

---

## 4. Verify the Setup

Quick sanity check — run from the repository root:

```bash
python -c "
import torch
print('CUDA:', torch.cuda.is_available())
print('GPU:', torch.cuda.get_device_name(0))
import faiss
print('FAISS:', faiss.__version__)
import langchain
print('LangChain:', langchain.__version__)
"
```

Expected output:

```
CUDA: True
GPU: NVIDIA GeForce RTX 5060 Laptop GPU
FAISS: 1.x.x
LangChain: 1.x.x
```

---

## 5. Stage 1 — Build the FAISS Index

This is the long step. It reads all ~9.9 million rows, embeds them on the GPU,
and writes the FAISS index to `faiss_index/`.

```bash
python 01_ingest.py
```

### What to expect

| Metric | Estimate |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` (default) |
| Chunk size | 50 000 rows per shard |
| Total shards | 199 |
| Time per shard | ~20–60 seconds (GPU) |
| **Total time** | **2–6 hours** |
| Disk usage | ~32 GB (18 GB shards + 11 GB merged.index + 3.6 GB merged.pkl) |

> **Current status (2026-03-14):** Ingestion is complete — 199/199 shards, 9,901,889 rows fully embedded.
> Note: `wc -l` previously reported ~16.9M lines, which was misleading — review text fields contain embedded newlines. The true row count confirmed via pandas is ~9.9M.

Progress is saved to `faiss_index/progress.json` after every shard.
**If the process is interrupted, just re-run the same command** — it will
resume from where it left off.

### Optional flags

```bash
# Just re-merge existing shards without re-embedding
python 01_ingest.py --merge-only

# Wipe everything and start fresh
python 01_ingest.py --reset
```

### When it's done you will see

```
[MERGE] Done. Total vectors: 9,901,889
        Index  → faiss_index/merged.index
        Docstore → faiss_index/merged.pkl

[DONE] FAISS index is ready. You can now run 04_generate_srs.py.
```

---

## 6. Stage 2 — Test the Retriever

Optional but recommended — verify the index works before running the full
generation pipeline:

```bash
python 02_retriever.py "What features do users want in a workplace review app?"
```

You should see 5 real Glassdoor review excerpts printed to the terminal.

Try different queries:

```bash
python 02_retriever.py --k 10 "salary transparency and pay equity"
python 02_retriever.py "management feedback tools"
python 02_retriever.py "mobile app usability"
```

---

## 7. Stage 3 — Generate the SRS

Make sure Ollama is running (`ollama serve`) then:

```bash
python 04_generate_srs.py
```

This runs all 5 LangChain chains sequentially:

| Chain | Task | Est. time |
|---|---|---|
| 1/5 | FR/NFR Extraction | 1–3 min |
| 2/5 | MoSCoW Prioritization | 1–2 min |
| 3/5 | DFD Component Identification | 1–2 min |
| 4/5 | CSPEC Logic (Activation + Decision Tables) | 2–4 min |
| 5/5 | IEEE 830 SRS Document Formatting | 3–6 min |

**Total: ~10–20 minutes** depending on your hardware.

### Optional flags

```bash
# Custom retrieval query
python 04_generate_srs.py --query "salary and compensation transparency features"

# Retrieve more reviews for richer context
python 04_generate_srs.py --k 30

# Skip retrieval and reuse the cached retrieved_reviews.json
# (useful for re-running chains without hitting FAISS again)
python 04_generate_srs.py --skip-retrieval
```

---

## 8. Output Files Reference

All outputs are written to `outputs/` in the repository root:

| File | Contents |
|---|---|
| `retrieved_reviews.json` | Raw review texts retrieved from FAISS |
| `requirements.json` | Structured FR + NFR list with IDs, categories, statements, sources |
| `moscow.json` | MoSCoW priority assignment for every requirement |
| `dfd_components.json` | DFD Level-1: entities, processes, data stores, data flows (raw JSON) |
| `dfd_components.md` | DFD components as Markdown tables (ready to paste into a report) |
| `cspec_tables.json` | Activation + Decision tables (raw JSON) |
| `cspec_tables.md` | CSPEC tables as formatted Markdown |
| `SRS.md` | **Full IEEE 830 Software Requirements Specification document** |

### Recommended reading order

1. `SRS.md` — the main deliverable
2. `requirements.json` + `moscow.json` — for detailed requirement analysis
3. `dfd_components.md` — use this to draw your DFD diagram manually
4. `cspec_tables.md` — use this to fill in your CSPEC tables in the report

---

## 9. Configuration Cheat-Sheet

All knobs are in `config.py`. Key ones:

| Parameter | Default | What it controls |
|---|---|---|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding quality vs. speed |
| `EMBED_BATCH_SIZE` | `256` | GPU VRAM per batch (lower if OOM) |
| `CSV_CHUNK_SIZE` | `50_000` | Rows per shard (lower = less RAM) |
| `RETRIEVER_K` | `20` | Reviews retrieved per query |
| `OLLAMA_MODEL` | `llama3:8b` | LLM used for all chains |
| `LLM_TEMPERATURE` | `0.1` | Lower = more deterministic output |
| `LLM_NUM_CTX` | `4096` | Context window in tokens (conservative; raise to 8192 if needed) |
| `LLM_NUM_PREDICT` | `8192` | Max tokens the LLM generates per chain call |
| `DEFAULT_QUERY` | (long string) | Default retrieval query |

**To switch embedding models** (better quality, uses more VRAM):

```python
# In config.py:
EMBEDDING_MODEL  = "sentence-transformers/all-mpnet-base-v2"
EMBED_BATCH_SIZE = 128  # reduce from 256 to be safe
```

Note: changing the embedding model requires re-running `01_ingest.py --reset`
because the vector dimensions change (384 → 768).

---

## 10. Troubleshooting

### `faiss` not found
```bash
pip install faiss-cpu
```

### `langchain_ollama` not found
```bash
pip install langchain-ollama
```

### `langchain_huggingface` not found
```bash
pip install langchain-huggingface
```

### CUDA out of memory during ingestion
Lower `EMBED_BATCH_SIZE` in `config.py` (try `128` or `64`), then resume:
```bash
python 01_ingest.py   # resumes automatically
```

### Ollama connection refused
```bash
ollama serve   # start Ollama in another terminal
```

### LLM wraps JSON in conversational preamble (e.g. "Here is the output: {...}")
This was the actual failure mode encountered on the first run (2026-03-14).
`llama3:8b` prefixes its JSON response with a natural-language sentence like
`"Here is the extracted requirements in JSON format:"`, which caused
`json.loads()` to fail immediately.

**This is now fixed in `03_chains.py`** — `_safe_json()` finds the first `{`
or `[` in the response and slices off any preamble before parsing. No action
needed; re-running `04_generate_srs.py` will produce correct output.

If you still see `{"error": ..., "raw_output": ...}` in a JSON file after the
fix, inspect the `raw_output` field to diagnose the new failure mode, then
lower `LLM_TEMPERATURE` to `0.0` in `config.py` and re-run.

### Ingest interrupted mid-shard
Just re-run `python 01_ingest.py`. The completed shards are saved and the
script will skip them automatically.

### `merged.index` already exists but you want a clean re-merge
```bash
python 01_ingest.py --merge-only
```

---

## 11. Changelog

| Date | Version | Changes |
|---|---|---|
| 2026-03-13 | v1.0 | Initial project build. All five pipeline stages implemented. |
| 2026-03-13 | v1.1 | Dependencies installed (`--break-system-packages`). `llama3:8b` pulled. GPU + Ollama smoke tests passed. Ready for Stage 1 ingest. |
| 2026-03-14 | v1.2 | Stage 1 ingestion confirmed complete — 199/199 shards, 9,901,889 rows (100%). Note: `wc -l` incorrectly reported ~16.9M lines due to embedded newlines in review text fields; true row count confirmed via pandas. Stage 3 first run: all 5 chains executed but chains 1–4 produced `{"error": ...}` JSON due to LLM wrapping output in natural-language preamble. `dfd_components.md` and `cspec_tables.md` empty as a result. `SRS.md` truncated mid-table (hit `LLM_NUM_PREDICT = 2048` token limit). |
| 2026-03-14 | v1.3 | Fixed `_safe_json()` in `03_chains.py` to strip natural-language preamble before JSON parsing. Raised `LLM_NUM_PREDICT` from 2048 → 8192 in `config.py` to fix SRS truncation. Re-ran `04_generate_srs.py --skip-retrieval`; all outputs successfully regenerated. |
| 2026-03-14 | v1.4 | Improved SRS quality: rewrote `prompts/srs_formatter.txt` with strict formatting rules (IEEE IDs, "shall" language, MUST/SHOULD/COULD labels, full DFD/CSPEC tables, proper section headings, references). Fixed `_safe_json()` to use `json.JSONDecoder.raw_decode()` so trailing LLM text after first JSON object no longer causes parse failures. Added SRS post-processor in `04_generate_srs.py` to deterministically append the Traceability Matrix and fix Section 1.3 when the LLM omits them. Re-ran pipeline — SRS.md now passes all IEEE 830 structural checks. |

---

*This document is automatically kept up to date as the project evolves.*
