#!/usr/bin/env python3
"""
00_init_wizard.py
=================
Interactive setup wizard for the SRE-RAG tool.

Guides users through:
  1. CSV file selection and column detection
  2. Mapping columns to text_columns and metadata_columns
  3. Defining requirement categories (optional)
  4. Selecting output formats
  5. Configuring LLM settings

Generates a dataset_config.yaml file that can be used with the pipeline.

Usage:
    python 00_init_wizard.py
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import CsvAdapter, MetadataExtractor, ConfigValidator


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_info(msg: str):
    """Print an info message."""
    print(f"ℹ️  {msg}")


def print_success(msg: str):
    """Print a success message."""
    print(f"✓ {msg}")


def print_error(msg: str):
    """Print an error message."""
    print(f"✗ {msg}")


def prompt_csv_path() -> Path:
    """Prompt user for CSV file path."""
    print_header("Step 1: CSV File Selection")
    print("Enter the path to your CSV file (relative or absolute).")
    print("Example: ./data.csv  or  /home/user/research/data.csv\n")

    while True:
        csv_input = input("CSV file path: ").strip()
        csv_path = Path(csv_input)

        if not csv_path.exists():
            print_error(f"File not found: {csv_path}")
            continue

        if not csv_path.suffix.lower() == ".csv":
            print_error("File must be a CSV file (.csv)")
            continue

        print_success(f"CSV file loaded: {csv_path}")
        return csv_path


def prompt_column_mappings(adapter: CsvAdapter) -> Dict[str, List[str]]:
    """Prompt user to map CSV columns to text and metadata."""
    print_header("Step 2: Column Mapping")

    # Show available columns
    columns = adapter.get_columns()
    print(f"Available columns in your CSV ({len(columns)} total):\n")
    for i, col in enumerate(columns, 1):
        print(f"  {i:2d}. {col}")

    # Show sample data
    print("\nSample data (first 3 rows):\n")
    sample = adapter.get_sample_data(nrows=3)
    print(sample.to_string())

    # Get suggestions
    print("\n" + "=" * 80)
    print("Analyzing columns to suggest text vs. metadata...\n")

    extractor = MetadataExtractor(adapter.csv_path)
    suggested_text = extractor.suggest_text_columns()
    suggested_meta = extractor.suggest_metadata_columns()

    print(f"Suggested TEXT columns (long text content):")
    for col in suggested_text:
        print(f"  • {col}")

    print(f"\nSuggested METADATA columns (IDs, dates, ratings, etc.):")
    for col in suggested_meta:
        print(f"  • {col}")

    # Prompt for text columns
    print("\n" + "=" * 80)
    print("Which columns should be COMBINED for analysis?")
    print("(These will be embedded and searched)")
    print("Enter column numbers separated by commas, or column names separated by commas.")
    print("Example: 1,2,3  or  title,description,feedback\n")

    text_columns = []
    while not text_columns:
        text_input = input("Text columns: ").strip()
        text_columns = _parse_column_input(text_input, columns)
        if not text_columns:
            print_error("Please enter at least one column")

    print_success(f"Selected text columns: {', '.join(text_columns)}")

    # Prompt for metadata columns
    print("\n" + "=" * 80)
    print("Which columns should be PRESERVED as metadata?")
    print("(These won't be embedded but will appear in output)")
    print("Enter column numbers/names, or press Enter to skip.\n")

    metadata_input = input("Metadata columns (optional): ").strip()
    metadata_columns = _parse_column_input(metadata_input, columns) if metadata_input else []

    if metadata_columns:
        print_success(f"Selected metadata columns: {', '.join(metadata_columns)}")
    else:
        print_info("No metadata columns selected")

    return {
        "text_columns": text_columns,
        "metadata_columns": metadata_columns,
    }


def prompt_categories() -> Dict[str, Any]:
    """Prompt user to define requirement categories."""
    print_header("Step 3: Requirement Categories (Optional)")

    print("Do you want to categorize requirements?")
    print("(This helps organize extracted requirements by type)")
    print("Options: yes, no\n")

    while True:
        choice = input("Enable categories? (yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            enabled = True
            break
        elif choice in ["no", "n"]:
            enabled = False
            break
        else:
            print_error("Please enter 'yes' or 'no'")

    if not enabled:
        print_info("Categories disabled")
        return {"enabled": False}

    print("\nEnter your FUNCTIONAL REQUIREMENT categories.")
    print("(Examples: Authentication, Data Management, Reporting)")
    print("Enter one per line, or press Enter twice to finish:\n")

    fr_categories = []
    while True:
        cat = input(f"FR category {len(fr_categories) + 1}: ").strip()
        if not cat:
            if fr_categories:
                break
            else:
                print_error("Please enter at least one category")
                continue
        fr_categories.append(cat)

    print("\nEnter your NON-FUNCTIONAL REQUIREMENT categories.")
    print("(Examples: Performance, Security, Scalability, Usability)")
    print("Enter one per line, or press Enter twice to finish:\n")

    nfr_categories = []
    while True:
        cat = input(f"NFR category {len(nfr_categories) + 1}: ").strip()
        if not cat:
            if nfr_categories:
                break
            else:
                print_error("Please enter at least one category")
                continue
        nfr_categories.append(cat)

    print_success(f"Functional requirements: {', '.join(fr_categories)}")
    print_success(f"Non-functional requirements: {', '.join(nfr_categories)}")

    return {
        "enabled": True,
        "functional_requirements": fr_categories,
        "non_functional_requirements": nfr_categories,
    }


def prompt_output_formats() -> List[str]:
    """Prompt user to select output formats."""
    print_header("Step 4: Output Formats")

    valid_formats = ["ieee_830", "ieee_29148", "json", "csv", "excel"]
    format_descriptions = {
        "ieee_830": "IEEE 830 Software Requirements Specification (recommended)",
        "ieee_29148": "IEEE 29148 Systems & Software Engineering Requirements",
        "json": "Structured JSON for programmatic use",
        "csv": "Comma-separated values for spreadsheets",
        "excel": "Excel workbook with multiple sheets",
    }

    print("Which output formats do you want to generate?\n")
    for i, fmt in enumerate(valid_formats, 1):
        print(f"  {i}. {fmt:15s} - {format_descriptions[fmt]}")

    print("\nEnter format numbers separated by commas.")
    print("Example: 1,3,5  (for IEEE 830, JSON, Excel)\n")

    selected = []
    while not selected:
        fmt_input = input("Output formats: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in fmt_input.split(",")]
            if any(i < 0 or i >= len(valid_formats) for i in indices):
                raise ValueError("Invalid format number")
            selected = [valid_formats[i] for i in indices]
        except (ValueError, IndexError):
            print_error("Please enter valid format numbers (1-5)")

    print_success(f"Selected formats: {', '.join(selected)}")
    return selected


def prompt_llm_settings() -> Dict[str, Any]:
    """Prompt user for LLM settings."""
    print_header("Step 5: LLM Settings (Local Ollama)")

    print("Available local models:")
    print("  • llama3.1:8b (recommended, 4.9 GB)")
    print("  • deepseek-r1:8b (5.2 GB, good for reasoning)")
    print("  • codellama:13b (7.4 GB, for code-related requirements)")
    print("  • codellama:7b (3.8 GB, lightweight)")
    print("\nEnter the model name (or press Enter for llama3.1:8b):\n")

    model = input("Model: ").strip() or "llama3.1:8b"
    print_success(f"Selected model: {model}")

    print("\nOllama URL (default: http://localhost:11434):")
    ollama_url = input("Ollama URL: ").strip() or "http://localhost:11434"
    print_success(f"Ollama URL: {ollama_url}")

    print("\nTemperature (0.0 = deterministic, 1.0 = creative)")
    print("Use 0.1 for structured output (SRS, JSON)")
    print("Use 0.7 for more creative analysis")
    print("(default: 0.1)\n")

    while True:
        temp_input = input("Temperature: ").strip() or "0.1"
        try:
            temperature = float(temp_input)
            if not 0.0 <= temperature <= 1.0:
                raise ValueError
            break
        except ValueError:
            print_error("Please enter a number between 0.0 and 1.0")

    print_success(f"Temperature: {temperature}")

    return {
        "model": model,
        "ollama_url": ollama_url,
        "temperature": temperature,
        "num_ctx": 4096,
        "num_predict": 8192,
    }


def prompt_srs_metadata() -> Dict[str, Any]:
    """Prompt user for SRS metadata."""
    print_header("Step 6: SRS Metadata")

    print("Enter metadata for the SRS header:\n")

    project_name = input("Project name: ").strip() or "My Research Project"
    version = input("Version (default: 1.0): ").strip() or "1.0"
    authors = input("Authors (comma-separated, default: Auto-generated): ").strip()

    if not authors:
        authors = ["Auto-generated via RAG pipeline"]
    else:
        authors = [a.strip() for a in authors.split(",")]

    print_success(f"Project: {project_name} v{version}")
    print_success(f"Authors: {', '.join(authors)}")

    return {
        "project_name": project_name,
        "version": version,
        "authors": authors,
    }


def prompt_config_filename() -> Path:
    """Prompt user for output config filename."""
    print_header("Step 7: Save Configuration")

    default_name = "dataset_config.yaml"
    print(f"Enter filename for the configuration (default: {default_name}):\n")

    filename = input("Config filename: ").strip() or default_name
    config_path = Path(filename)

    if config_path.exists():
        print_error(f"File already exists: {config_path}")
        overwrite = input("Overwrite? (yes/no): ").strip().lower()
        if overwrite not in ["yes", "y"]:
            return prompt_config_filename()

    return config_path


def _parse_column_input(user_input: str, available_columns: List[str]) -> List[str]:
    """
    Parse user input (column numbers or names) into a list of column names.

    Args:
        user_input: User's input (e.g., "1,2,3" or "title,description")
        available_columns: List of available column names

    Returns:
        List of column names, or empty list if invalid
    """
    parts = [p.strip() for p in user_input.split(",")]
    result = []

    for part in parts:
        # Try as column number (1-indexed)
        try:
            idx = int(part) - 1
            if 0 <= idx < len(available_columns):
                result.append(available_columns[idx])
                continue
        except ValueError:
            pass

        # Try as column name
        if part in available_columns:
            result.append(part)
            continue

        # Not found
        print_error(f"Column not found: {part}")
        return []

    return result


def main():
    """Run the interactive wizard."""
    print_header("SRE-RAG Tool Setup Wizard")
    print("This wizard will help you configure the tool for your dataset.")
    print("You'll be asked about your CSV file, columns, categories, and output formats.")
    print("At the end, a dataset_config.yaml file will be created.\n")

    try:
        # Step 1: CSV path
        csv_path = prompt_csv_path()
        adapter = CsvAdapter(csv_path)

        # Step 2: Column mappings
        column_mappings = prompt_column_mappings(adapter)

        # Step 3: Categories
        categories = prompt_categories()

        # Step 4: Output formats
        output_formats = prompt_output_formats()

        # Step 5: LLM settings
        llm_settings = prompt_llm_settings()

        # Step 6: SRS metadata
        srs_metadata = prompt_srs_metadata()

        # Step 7: Config filename
        config_path = prompt_config_filename()

        # Build config
        config = {
            "dataset_name": Path(csv_path).stem,
            "csv_path": str(csv_path),
            "column_mappings": column_mappings,
            "categories": categories,
            "llm_settings": llm_settings,
            "output_formats": output_formats,
            "srs_metadata": srs_metadata,
            "filtering": {
                "remove_empty_records": True,
                "min_text_length": 10,
            },
        }

        # Save config
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print_header("Configuration Saved!")
        print_success(f"Config file created: {config_path}")
        print("\nYou can now use this config with the pipeline:")
        print(f"  python 01_ingest.py --config {config_path}")
        print(f"  python 04_generate_srs.py --config {config_path}")

    except KeyboardInterrupt:
        print("\n\nWizard cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print_error(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
