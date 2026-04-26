# Phase 1 Quick Start Guide

## What You Can Do Now

Phase 1 provides a **configuration layer** that lets you:

1. ✅ **Use the interactive wizard** to set up any dataset without editing code
2. ✅ **Auto-detect CSV columns** and suggest which are text vs. metadata
3. ✅ **Validate configuration files** before running the pipeline
4. ✅ **Load configs from YAML** instead of hardcoding values
5. ✅ **Keep backward compatibility** with existing Glassdoor pipeline

---

## Quick Start: 3 Steps

### Step 1: Prepare Your CSV
Place your CSV file in the project directory (or anywhere accessible).

**Example CSV structure:**
```
title,description,feedback,date,author,rating
"Great culture","Positive workplace","Recommended","2026-01-15","Alice",5
"Need balance","Long hours","Improve","2026-02-20","Bob",2
```

### Step 2: Run the Wizard
```bash
python 00_init_wizard.py
```

The wizard will:
- Ask for your CSV file path
- Show available columns
- Suggest which columns are text vs. metadata
- Let you choose requirement categories (optional)
- Ask for output formats (IEEE 830, JSON, Excel, etc.)
- Configure LLM settings (model, temperature, etc.)
- Generate `dataset_config.yaml`

### Step 3: Use the Config
Once you have `dataset_config.yaml`, you can:

```bash
# In Phase 2+, you'll be able to do:
python 01_ingest.py --config dataset_config.yaml
python 04_generate_srs.py --config dataset_config.yaml
```

---

## Manual Configuration (Advanced)

If you prefer to edit YAML directly instead of using the wizard:

1. Copy the template:
   ```bash
   cp dataset_config.yaml my_dataset.yaml
   ```

2. Edit `my_dataset.yaml`:
   ```yaml
   dataset_name: "My Research"
   csv_path: "./my_data.csv"
   column_mappings:
     text_columns: ["title", "description"]
     metadata_columns: ["date", "author"]
   llm_settings:
     model: "llama3.1:8b"
     ollama_url: "http://localhost:11434"
     temperature: 0.1
   output_formats: ["ieee_830", "json"]
   ```

3. Validate it:
   ```bash
   python -c "from utils import ConfigValidator; from pathlib import Path; is_valid, errors = ConfigValidator.validate_file(Path('my_dataset.yaml')); print('✓ Valid' if is_valid else f'✗ Errors: {errors}')"
   ```

---

## Understanding the Configuration

### `column_mappings`
- **text_columns**: Which CSV columns to combine for analysis (will be embedded)
- **metadata_columns**: Which columns to preserve for reference (won't be embedded)

**Example:**
```yaml
column_mappings:
  text_columns: ["title", "description", "feedback"]  # These get analyzed
  metadata_columns: ["date", "author", "rating"]      # These stay for reference
```

### `llm_settings`
- **model**: Which Ollama model to use
  - `llama3.1:8b` (recommended, 4.9 GB)
  - `deepseek-r1:8b` (5.2 GB, good for reasoning)
  - `codellama:13b` (7.4 GB, for code)
- **temperature**: Randomness (0.1 = structured, 0.7 = creative)
- **num_ctx**: Context window size (how much text the model sees)
- **num_predict**: Max tokens to generate

### `output_formats`
Choose which formats to generate:
- `ieee_830` — IEEE 830 SRS (recommended)
- `ieee_29148` — IEEE 29148 alternative
- `json` — Structured JSON
- `csv` — Spreadsheet format
- `excel` — Excel workbook

### `categories` (Optional)
Define requirement categories for your domain:
```yaml
categories:
  enabled: true
  functional_requirements:
    - "Authentication"
    - "Data Management"
    - "Reporting"
  non_functional_requirements:
    - "Performance"
    - "Security"
    - "Scalability"
```

---

## Available Utilities

### `CsvAdapter`
Normalize any CSV to a standard schema.

```python
from utils import CsvAdapter
from pathlib import Path

adapter = CsvAdapter(Path('data.csv'))
columns = adapter.get_columns()  # List all columns
sample = adapter.get_sample_data(nrows=5)  # Preview data
result = adapter.combine_text_columns(
    text_columns=['title', 'description'],
    metadata_columns=['date', 'author']
)
```

### `MetadataExtractor`
Analyze CSV structure and suggest columns.

```python
from utils import MetadataExtractor

extractor = MetadataExtractor(Path('data.csv'))
text_cols = extractor.suggest_text_columns()      # Long text
meta_cols = extractor.suggest_metadata_columns()  # IDs, dates, etc.
analysis = extractor.analyze_columns()            # Full analysis
```

### `ConfigValidator`
Validate and load configuration files.

```python
from utils import ConfigValidator
from pathlib import Path

# Validate
is_valid, errors = ConfigValidator.validate_file(Path('config.yaml'))

# Load (with validation)
config = ConfigValidator.load_config(Path('config.yaml'))
```

---

## Backward Compatibility

**Existing Glassdoor pipeline still works:**

```bash
# These still work without any config file
python 01_ingest.py
python 04_generate_srs.py
```

The tool falls back to hardcoded Glassdoor defaults if no config is provided.

---

## What's Coming in Phase 2+

- **Phase 2**: Prompt templates (Jinja2) for customizable analysis
- **Phase 3**: Pipeline refactoring to use configs
- **Phase 4**: Data filtering and cleaning
- **Phase 5**: Testing and documentation

---

## Troubleshooting

### "CSV file not found"
Make sure the `csv_path` in your config is correct (relative or absolute path).

### "Invalid output format"
Valid formats are: `ieee_830`, `ieee_29148`, `json`, `csv`, `excel`

### "Missing required field"
Check that your YAML has all required sections:
- `dataset_name`
- `csv_path`
- `column_mappings` (with `text_columns`)
- `llm_settings` (with `model` and `ollama_url`)
- `output_formats`

### "Ollama model not found"
Make sure you've pulled the model:
```bash
ollama pull llama3.1:8b
```

---

## Next Steps

1. **Try the wizard**: `python 00_init_wizard.py`
2. **Create a config**: Answer the prompts
3. **Validate it**: The wizard validates automatically
4. **Wait for Phase 2**: Prompt templates and pipeline integration coming soon

---

**Questions?** Check `PHASE_1_SUMMARY.md` for detailed technical documentation.
