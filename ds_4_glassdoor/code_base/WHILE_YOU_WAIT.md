# While the Ingestion Runs

## 1. Ollama model is already ready

`llama3.2:3b` is already pulled and available. If you want better answer quality at the cost of a larger download, you can pull a bigger model in a separate terminal:

```bash
ollama pull llama3.2     # 8B version, ~5 GB
```

Then pass `--model llama3.2` when querying.

---

## 2. Think about what queries you want to run

Some examples to get you started:

- *"What do software engineers say about work-life balance at Google?"*
- *"What are the most common complaints about management?"*
- *"What do 1-star reviews say that 5-star reviews don't?"*
- *"What industries have the best compensation reviews?"*

If your queries are always **company-specific** or **job-specific**, use the
`--filter-job` and `--filter-rating` flags heavily. If they are broad thematic
queries, the current setup works well as-is.

---

## 3. Decide how much to index

The full run indexes ~12-13 million rows and takes many hours on CPU.

| Option | Rows | Est. time (CPU) | Est. disk |
|---|---|---|---|
| Sample 500K rows | ~500K | ~30-60 min | ~2-3 GB |
| Sample 1M rows | ~1M | ~1-2 hours | ~5-6 GB |
| Index everything | ~13M | ~8-15 hours | ~30+ GB |

You can stop the current run at any point with `Ctrl+C` (progress is saved),
and already have a very usable system for most queries from as few as 500K docs.

To stop cleanly and resume later:
```
Ctrl+C
```

To resume from where you left off:
```bash
python3 code_base/ingest.py
```

---

## 4. Check your available disk space

ChromaDB will grow large. Check your headroom:

```bash
df -h ~
```

Make sure you have at least **5 GB free** for a partial index, or **35+ GB**
for a full index.

---

## 5. Silence the HuggingFace warning (optional)

During ingestion you see:
```
WARNING: You are sending unauthenticated requests to the HF Hub...
```

This is harmless. It disappears on subsequent runs once the model is cached
locally. To silence it permanently, create a free account at huggingface.co,
generate a read token, and add this to your `~/.bashrc`:

```bash
export HF_TOKEN=your_token_here
```

---

## 6. How to query once ingestion is done

Make sure Ollama is running, then:

```bash
# Interactive mode
python3 code_base/query.py --model llama3.2:3b

# One-shot query
python3 code_base/query.py --model llama3.2:3b --query "What do engineers say about work-life balance?"

# With filters
python3 code_base/query.py --model llama3.2:3b --filter-rating 1 --query "What are the biggest complaints?"
```

### In-REPL commands

| Command | Effect |
|---|---|
| `:context` | Toggle showing the raw retrieved reviews |
| `:top-k 20` | Retrieve more reviews per query |
| `:rating 5` | Filter to 5-star reviews only |
| `:job "Data Scientist"` | Filter by job title keyword |
| `:job` | Clear the job filter |
| `:rating 0` | Clear the rating filter |
| `exit` | Quit |
