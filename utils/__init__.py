"""
utils/
======
Utility modules for the generalized SRE-RAG tool.

Modules:
  - csv_adapter: Normalize arbitrary CSV to standard schema
  - metadata_extractor: Extract and suggest metadata columns
  - config_validator: Validate dataset_config.yaml schema
  - prompt_loader: Load and render Jinja2 prompt templates
  - output_formatters: Multi-format output handling (IEEE 830, JSON, CSV, Excel, etc.)
"""

from .csv_adapter import CsvAdapter
from .metadata_extractor import MetadataExtractor
from .config_validator import ConfigValidator
from .prompt_loader import PromptLoader
from .output_formatters import (
    OutputFormatter,
    IEEE830Formatter,
    IEEE29148Formatter,
    JSONFormatter,
    CSVFormatter,
    ExcelFormatter,
    get_formatter,
    list_formats,
)

__all__ = [
    "CsvAdapter",
    "MetadataExtractor",
    "ConfigValidator",
    "PromptLoader",
    "OutputFormatter",
    "IEEE830Formatter",
    "IEEE29148Formatter",
    "JSONFormatter",
    "CSVFormatter",
    "ExcelFormatter",
    "get_formatter",
    "list_formats",
]
