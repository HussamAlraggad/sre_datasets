# Setup Guide

Step-by-step instructions to get the Glassdoor RAG system running on a new machine.

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- The dataset file `all_reviews.csv` placed at `ds_4_glassdoor/all_reviews.csv`
  (not committed to git — obtain it separately)

---

## 1. Clone the repository

```bash
git clone https://github.com/EngHussam23/sre_datasets.git
cd sre_datasets/ds_4_glassdoor
```

---

## 2. Place the dataset

Copy `all_reviews.csv` into the `ds_4_glassdoor/` directory so the path is:

```
ds_4_glassdoor/all_reviews.csv
```

---

## 3. Create and activate the virtual environment

```bash
python3 -m venv code_base/.venv
source code_base/.venv/bin/activate
```

On Windows:

```bat
python -m venv code_base\.venv
code_base\.venv\Scripts\activate
```

---

## 4. Install Python dependencies

```bash
pip install -r code_base/requirements.txt
```

> **Note:** If you have an NVIDIA GPU with CUDA drivers installed, PyTorch will use it
> automatically for embeddings, significantly speeding up ingestion.

---

## 5. Pull the Ollama model

```bash
ollama pull llama3.2:3b
```

Make sure Ollama is running in the background before querying:

```bash
ollama serve   # runs on http://localhost:11434 by default
```

---

## 6. Ingest the dataset

This builds the local ChromaDB vector store. It is **resumable** — safe to stop and
restart at any time.

```bash
# Ingest everything (takes several hours on CPU):
python3 code_base/ingest.py

# Or ingest a small sample first to verify the setup:
python3 code_base/ingest.py --limit 5000
```

The vector store is saved to `code_base/chroma_db/` (created automatically).

---

## 7. Query the system

**Interactive REPL:**

```bash
python3 code_base/query.py
```

**One-shot query:**

```bash
python3 code_base/query.py --query "What do employees say about work-life balance at Google?"
```

### REPL commands

| Command | Description |
|---------|-------------|
| `:top-k N` | Change number of retrieved reviews (default: 10) |
| `:rating N` | Filter results to a specific star rating (1–5) |
| `:job TEXT` | Filter results by job title keyword |
| `:context` | Show the raw context sent to the LLM for the last query |
| `exit` / `quit` | Exit the REPL |

### Additional CLI flags

```bash
python3 code_base/query.py --help
```

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `llama3.2:3b` | Ollama model to use |
| `--db-path` | `./chroma_db` | Path to ChromaDB store |
| `--top-k` | `10` | Number of reviews to retrieve |
| `--query` | — | Run a single query and exit |

---

## Directory layout

```
ds_4_glassdoor/
├── all_reviews.csv          # dataset — NOT in git
└── code_base/
    ├── .venv/               # virtual environment — NOT in git
    ├── chroma_db/           # vector store (built by ingest.py) — NOT in git
    ├── requirements.txt
    ├── ingest.py
    ├── query.py
    ├── SETUP.md             # this file
    └── WHILE_YOU_WAIT.md
```
