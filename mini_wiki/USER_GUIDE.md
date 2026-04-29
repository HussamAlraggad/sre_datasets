"""
mini_wiki User Guide
Complete guide for using mini_wiki - Universal Research Assistant

Contents:
- Getting Started
- Basic Usage
- Advanced Features
- TUI Interface
- Configuration
- Tips and Tricks
- FAQ
"""

# ============================================================================
# MINI_WIKI USER GUIDE
# ============================================================================

## Getting Started

### What is mini_wiki?

mini_wiki is a universal research assistant that helps you:
- **Load** data from multiple formats (CSV, JSON, JSONL, PDF, TXT, URLs)
- **Search** across your data using semantic search
- **Rank** results by relevance and importance
- **Generate** AI-readable documentation
- **Export** results in multiple formats (JSON, Markdown, CSV, PDF, HTML)
- **Manage** bookmarks and search history

### Quick Start

```python
from mini_wiki.integrated_system import create_system

# 1. Create system
system = create_system()

# 2. Load data
system.load_data("documents.csv", "csv")

# 3. Search
results = system.search("machine learning")

# 4. View results
for result in results:
    print(f"{result['title']}: {result['relevance']:.2f}")

# 5. Export
system.export_results(results, "markdown", "results.md")
```

### Installation

```bash
# Quick install
git clone https://github.com/user/mini_wiki.git
cd mini_wiki
python3 bootstrap.py

# Or manual install
python3 -m venv .mini_wiki_venv
source .mini_wiki_venv/bin/activate
pip install -r requirements.txt
```

## Basic Usage

### Loading Data

#### CSV Files

```python
system.load_data("documents.csv", "csv")
```

#### JSON Files

```python
system.load_data("documents.json", "json")
```

#### JSONL Files

```python
system.load_data("documents.jsonl", "jsonl")
```

#### PDF Files

```python
system.load_data("paper.pdf", "pdf")
```

#### Text Files

```python
system.load_data("notes.txt", "txt")
```

#### URLs

```python
system.load_data("https://example.com/article", "url")
```

#### Auto-Detection

```python
# mini_wiki can auto-detect the format
system.load_data("documents.csv", "auto")
```

### Searching

#### Basic Search

```python
results = system.search("machine learning")
```

#### Search with Limit

```python
results = system.search("python tutorial", limit=5)
```

#### Search with Filters

```python
results = system.search(
    query="deep learning",
    filter_criteria={
        "min_relevance": 0.7,
        "sources": ["arxiv", "github"],
        "tags": ["neural-networks"]
    }
)
```

#### Search with Sorting

```python
results = system.search(
    query="python",
    sort_criteria={
        "field": "relevance",
        "order": "descending"
    }
)
```

### Understanding Results

Each search result contains:

```python
{
    "id": "doc_1",
    "title": "Machine Learning Basics",
    "content": "Content of the document...",
    "relevance": 0.95,      # Relevance score (0-1)
    "importance": 0.87,     # Importance score (0-1)
    "context": "Generated context...",  # AI-generated context
    "source": "arxiv",
    "date": "2024-01-15",
    "tags": ["machine-learning", "ai"]
}
```

### Exporting Results

#### Export to JSON

```python
system.export_results(results, "json", "results.json")
```

#### Export to Markdown

```python
system.export_results(results, "markdown", "results.md")
```

#### Export to CSV

```python
system.export_results(results, "csv", "results.csv")
```

#### Export to HTML

```python
system.export_results(results, "html", "results.html")
```

## Advanced Features

### Bookmarks

#### Add Bookmark

```python
bookmark = system.add_bookmark(
    title="Important Paper",
    url="http://example.com/paper",
    document_id="doc_123",
    tags=["important", "research"],
    notes="Great paper on deep learning"
)
```

#### Get Bookmarks

```python
bookmarks = system.get_bookmarks()
for bookmark in bookmarks:
    print(f"{bookmark['title']}: {bookmark['url']}")
```

### Search History

#### View History

```python
history = system.get_search_history(limit=20)
for entry in history:
    print(f"{entry['query']}: {entry['results_count']} results")
```

#### Recent Items

```python
recent = system.get_recent_items(limit=10)
for item in recent:
    print(f"{item['title']}: accessed {item['access_count']} times")
```

### Batch Operations

#### Batch Export

```python
items = [
    {"id": 1, "title": "Item 1"},
    {"id": 2, "title": "Item 2"},
    {"id": 3, "title": "Item 3"},
]
system.batch_export(items, "json", "batch_export.json")
```

### Statistics

#### System Statistics

```python
stats = system.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Total searches: {stats['total_searches']}")
print(f"Bookmarks: {stats['bookmarks_count']}")
```

#### Health Check

```python
health = system.health_check()
print(f"System status: {health['status']}")
for component, status in health['components'].items():
    print(f"  {component}: {status}")
```

## TUI Interface

### Launching TUI

```bash
# Launch with default settings
mini_wiki tui

# Launch with custom theme
mini_wiki tui --theme light

# Launch with custom dimensions
mini_wiki tui --width 120 --height 40
```

### TUI Navigation

```
┌──────────────────────────────────────────────────┐
│              mini_wiki Main Menu                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  → 1. Search Documents                           │
│    2. View Knowledge Base                         │
│    3. Recent Searches                             │
│    4. Settings                                    │
│    5. Help                                        │
│    6. Exit                                        │
│                                                  │
│  Use ↑/↓ to navigate, Enter to select, Q to quit │
└──────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate menu items |
| Enter | Select menu item |
| Q | Go back to previous screen |
| Ctrl+C | Exit application |
| Backspace | Delete character (in input) |

### Search Screen

1. Enter your search query
2. Press Enter to search
3. View results in the results screen
4. Select a result to view the full document

### Results Screen

- Results are displayed in a table format
- Columns: Document, Score, Relevance
- Use ↑/↓ to navigate
- Press Enter to view a document
- Press Q to go back

### Knowledge Base Screen

- Browse topics organized by category
- Each topic contains curated information
- Use ↑/↓ to navigate
- Press Enter to view a topic
- Press Q to go back

### Settings Screen

- Theme: Change color theme (dark/light/monokai)
- Language: Select interface language
- Results per page: Adjust pagination
- Auto-save: Enable/disable auto-saving

## Configuration

### Configuration File

Create `~/.mini_wiki/config.yaml`:

```yaml
# Data paths
data_path: ./data
index_path: ./index
storage_path: ./storage

# Display settings
theme: dark
max_results: 100

# Performance settings
enable_caching: true
cache_size_mb: 100
batch_size: 32

# Embedding settings
embedding_model: all-MiniLM-L6-v2
embedding_device: cpu

# Ranking settings
relevance_weight: 0.6
importance_weight: 0.4

# Search settings
default_limit: 10
min_relevance: 0.3

# Export settings
default_export_format: markdown
export_include_metadata: true
export_include_scores: true
export_include_references: true

# Logging settings
log_level: INFO
log_file: ~/.mini_wiki/mini_wiki.log
```

### Ranking Presets

| Preset | Relevance | Importance | Use Case |
|--------|-----------|------------|----------|
| research_focused | 80% | 20% | Academic research |
| balanced | 60% | 40% | General use |
| importance_focused | 40% | 60% | Finding key documents |
| recency_focused | 30% | 70%* | Recent information |
| citation_focused | 40% | 60%* | Highly cited works |
| strict_relevance | 100% | 0% | Exact matches only |
| strict_importance | 0% | 100% | Key documents only |

*Note: Recency and citation are components of importance score

### Score Interpretation

| Score Range | Interpretation |
|-------------|---------------|
| 0.9 - 1.0 | Highly relevant/important |
| 0.7 - 0.9 | Relevant/important |
| 0.5 - 0.7 | Moderately relevant |
| 0.3 - 0.5 | Weakly relevant |
| 0.0 - 0.3 | Not relevant |

## Tips and Tricks

### 1. Use Specific Queries

```python
# Bad: Too broad
results = system.search("ai")

# Good: More specific
results = system.search("transformer architecture for natural language processing")
```

### 2. Use Filters to Narrow Results

```python
# Filter by minimum relevance
results = system.search(
    "machine learning",
    filter_criteria={"min_relevance": 0.7}
)
```

### 3. Export Results for Later Use

```python
# Export to Markdown for reading
system.export_results(results, "markdown", "research_notes.md")

# Export to JSON for processing
system.export_results(results, "json", "results.json")

# Export to CSV for spreadsheets
system.export_results(results, "csv", "results.csv")
```

### 4. Use Bookmarks for Important Documents

```python
# Bookmark important findings
system.add_bookmark(
    title="Key Paper",
    url="http://example.com/paper",
    document_id="doc_123",
    tags=["important", "research"]
)
```

### 5. Check Search History

```python
# Review past searches
history = system.get_search_history(limit=10)
for entry in history:
    print(f"Query: {entry['query']}, Results: {entry['results_count']}")
```

### 6. Optimize Performance

```python
# Clear cache and optimize
system.optimize_performance()

# Check system health
health = system.health_check()
print(f"System status: {health['status']}")
```

## FAQ

### Q: How do I install mini_wiki?

A: Run `python3 bootstrap.py` in the project directory. This will automatically create a virtual environment, install dependencies, and launch the application.

### Q: What data formats are supported?

A: mini_wiki supports CSV, JSON, JSONL, PDF, TXT, and URL formats. The format is auto-detected based on the file extension.

### Q: How do I change the ranking algorithm?

A: Use ranking presets or custom weights:
```python
# Use preset
system.search("query", preset="research_focused")

# Custom weights
system.search("query", relevance_weight=0.8, importance_weight=0.2)
```

### Q: How do I export results?

A: Use the export_results method:
```python
system.export_results(results, "markdown", "output.md")
```
Supported formats: JSON, Markdown, CSV, PDF, HTML

### Q: How do I use the TUI?

A: Run `mini_wiki tui` to launch the interactive terminal interface. Use arrow keys to navigate and Enter to select.

### Q: How do I backup my data?

A: Copy the data, index, and storage directories:
```bash
cp -r ./data ./data_backup
cp -r ./index ./index_backup
cp -r ./storage ./storage_backup
```

### Q: How do I get help?

A: 
- Documentation: https://mini_wiki.readthedocs.io
- GitHub Issues: https://github.com/user/mini_wiki/issues
- Email: support@mini_wiki.dev

## Keyboard Shortcuts Reference

### TUI Shortcuts

| Key | Action |
|-----|--------|
| ↑/↓ or W/S | Navigate menu items |
| ←/→ or A/D | Navigate options |
| Enter | Select/Confirm |
| Q | Go back |
| Ctrl+C | Exit application |
| Backspace | Delete character |

### CLI Commands

| Command | Description |
|---------|-------------|
| `mini_wiki load` | Load data |
| `mini_wiki search` | Search documents |
| `mini_wiki rank` | Rank results |
| `mini_wiki export` | Export results |
| `mini_wiki show` | Show configuration |
| `mini_wiki tui` | Launch TUI |

## Glossary

| Term | Definition |
|------|-----------|
| **Relevance** | How closely a document matches the search query (0-1) |
| **Importance** | How significant a document is overall (0-1) |
| **Embedding** | Vector representation of text for semantic search |
| **Index** | Data structure for fast similarity search |
| **Context** | AI-generated summary of document content |
| **Knowledge Base** | Organized collection of documented knowledge |
| **Bookmark** | Saved reference to an important document |
| **Preset** | Pre-configured ranking weights |
| **TUI** | Terminal User Interface |
| **Batch** | Processing multiple items at once |