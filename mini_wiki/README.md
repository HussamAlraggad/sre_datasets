# mini_wiki - Universal Research Assistant

A powerful tool that learns your dataset, teaches AI models about it, and helps you analyze it with intelligent hybrid ranking.

## Features

- **Multi-Format Support**: Load data from CSV, JSON, PDF, URLs, and more
- **Intelligent Embeddings**: Generate semantic embeddings using state-of-the-art models
- **Hybrid Ranking**: Combine relevance and importance scores for better results
- **AI Teaching**: Generate explicit documentation for AI model reference
- **Advanced Filtering**: Apply custom filters to refine results
- **Multiple Export Formats**: Export to CSV, JSON, YAML, Markdown, Excel
- **Interactive TUI**: User-friendly terminal interface
- **Customizable Configuration**: Full control over ranking weights and parameters
- **Performance Optimized**: Fast search with FAISS indexing

## Installation

### From Source

```bash
git clone <repository-url>
cd mini_wiki
pip install -e .
```

### From PyPI (Coming Soon)

```bash
pip install mini_wiki
```

## Quick Start

### 1. Load Your Dataset

```bash
mini_wiki load path/to/data.csv --format csv
```

### 2. Set Your Research Topic

```bash
mini_wiki topic "Machine Learning Ethics"
```

### 3. Rank Content

```bash
mini_wiki rank --limit 20
```

### 4. Export Results

```bash
mini_wiki export csv output.csv --include-reference
```

### 5. Interactive TUI

```bash
mini_wiki tui
```

## Python API

```python
from mini_wiki import MiniWiki

# Initialize
wiki = MiniWiki(config_path="mini_wiki_config.yaml")

# Load dataset
dataset = wiki.load_dataset("path/to/data.csv", format="csv")

# Set topic
wiki.set_topic("Machine Learning Ethics")

# Rank content
results = wiki.rank(limit=20)

# Export with AI reference
wiki.export(format="yaml", path="output.yaml", include_reference=True)
```

## Configuration

mini_wiki uses YAML configuration files. The default configuration is located at:

- `./mini_wiki_config.yaml` (project-specific)
- `~/.mini_wiki/config.yaml` (user-specific)
- `/etc/mini_wiki/config.yaml` (system-wide)

### Key Configuration Options

```yaml
# Ranking weights
ranking:
  weights:
    relevance: 0.6      # 60% relevance score
    importance: 0.4     # 40% importance score

# Embeddings model
embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  device: "cpu"         # or "cuda" for GPU

# UI settings
ui:
  theme: "dark"
  table_width: 120
  results_per_page: 20
```

See `config/mini_wiki_config.yaml` for complete configuration options.

## Architecture

mini_wiki follows a layered architecture:

```
┌─────────────────────────────────────────┐
│         TUI Interface Layer             │
├─────────────────────────────────────────┤
│         API/Command Layer               │
├─────────────────────────────────────────┤
│      Business Logic Layer               │
│  ├─ Dataset Manager                    │
│  ├─ Ranking Engine                     │
│  ├─ AI Teaching System                 │
│  ├─ Filter Engine                      │
│  └─ Export Manager                     │
├─────────────────────────────────────────┤
│      Data Access Layer                  │
│  ├─ Dataset Loader                     │
│  ├─ Index Manager                      │
│  └─ Cache Manager                      │
├─────────────────────────────────────────┤
│      Storage Layer                      │
│  ├─ SQLite Database                    │
│  ├─ FAISS Indexes                      │
│  └─ File System                        │
└─────────────────────────────────────────┘
```

See `ARCHITECTURE.md` for detailed architecture documentation.

## Module Structure

```
mini_wiki/
├── core/                    # Core learning system
│   ├── dataset_loader.py   # Multi-format data loading
│   ├── embeddings.py       # Embedding generation
│   ├── indexing.py         # FAISS index management
│   └── data_models.py      # Data structures
├── ranking/                 # Hybrid ranking system
│   ├── relevance_scorer.py # Relevance scoring
│   ├── importance_scorer.py# Importance scoring
│   └── hybrid_ranker.py    # Hybrid ranking
├── ai_teaching/             # AI teaching system
│   ├── context_generator.py# Dataset context
│   ├── reference_builder.py# AI reference docs
│   └── quality_metrics.py  # Quality metrics
├── filtering/               # Filtering engine
├── export/                  # Export system
├── analysis/                # Analysis engine
├── ui/                      # User interface
├── storage/                 # Storage layer
├── utils/                   # Utilities
└── tests/                   # Test suite
```

## Ranking System

### Hybrid Ranking Formula

```
final_score = (0.6 × relevance_score) + (0.4 × importance_score)
```

### Relevance Scoring

- **Method**: Cosine similarity + TF-IDF
- **Calculation**: 0.7 × cosine_similarity + 0.3 × tfidf_score
- **Range**: 0.0 - 1.0

### Importance Scoring

- **Frequency**: How often content appears (30%)
- **Length**: Document length (20%)
- **Recency**: How recent the content is (30%)
- **Citations**: How many times referenced (20%)
- **Range**: 0.0 - 1.0

### Customizable Weights

```yaml
ranking:
  presets:
    research_focused:
      relevance: 0.7
      importance: 0.3
    balanced:
      relevance: 0.6
      importance: 0.4
    importance_focused:
      relevance: 0.4
      importance: 0.6
```

## AI Teaching System

mini_wiki generates explicit documentation for AI models:

```yaml
dataset_context:
  name: "Machine Learning Ethics Research"
  size: 1000
  key_topics: ["Ethics", "Fairness", "Bias"]

ranking_methodology:
  formula: "final_score = (0.6 × relevance) + (0.4 × importance)"
  relevance:
    method: "Cosine similarity + TF-IDF"
  importance:
    method: "Multi-factor scoring"

top_ranked_content:
  - rank: 1
    title: "Ethics Framework for AI"
    relevance_score: 0.98
    importance_score: 0.91
    final_score: 0.95

quality_metrics:
  completeness: 0.94
  average_relevance: 0.72
  coverage: 0.89
```

## Supported Data Formats

- **CSV**: Comma-separated values with configurable delimiters
- **JSON**: Flat or nested JSON structures
- **JSONL**: Line-delimited JSON
- **PDF**: Text extraction from PDF files
- **TXT**: Plain text files
- **URLs**: Web scraping and content extraction

## Export Formats

- **CSV**: Spreadsheet format with rankings
- **JSON**: Structured JSON with full metadata
- **YAML**: Human-readable format with AI reference
- **Markdown**: Formatted markdown tables
- **Excel**: Excel workbooks with formatting

## Performance

### Benchmarks

- Load 1000 records: < 5 seconds
- Generate embeddings for 1000 records: < 30 seconds
- Rank 1000 records: < 2 seconds
- Export 1000 records: < 5 seconds
- Search top 20 results: < 100ms

### Optimization Tips

1. Use GPU for embeddings: `device: "cuda"`
2. Increase batch size for faster processing
3. Use FAISS indexing for large datasets
4. Enable caching for repeated queries

## Development

### Setup Development Environment

```bash
pip install -e ".[dev]"
pre-commit install
```

### Run Tests

```bash
pytest tests/
pytest tests/ --cov=mini_wiki  # With coverage
```

### Code Quality

```bash
black mini_wiki/
flake8 mini_wiki/
isort mini_wiki/
mypy mini_wiki/
```

## Documentation

- [Architecture Guide](ARCHITECTURE.md) - Detailed system architecture
- [API Reference](docs/API.md) - Complete API documentation
- [User Guide](docs/USER_GUIDE.md) - User guide and tutorials
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Development guidelines
- [Examples](docs/EXAMPLES.md) - Usage examples

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for similarity search
- [Textual](https://textual.textualize.io/) for TUI framework
- [Click](https://click.palletsprojects.com/) for CLI framework

## Support

For issues, questions, or suggestions, please:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/your-repo/issues)
3. Create a new issue with detailed information

## Roadmap

- [ ] Phase 1: Core Learning System (in progress)
- [ ] Phase 2: Hybrid Ranking System
- [ ] Phase 3: AI Teaching System
- [ ] Phase 4: TUI Interface
- [ ] Phase 5: Advanced Features
- [ ] Phase 6: Deployment & Integration

See [plan.md](plan.md) for detailed implementation plan.

---

**mini_wiki** - Learn. Teach. Analyze. 🚀
