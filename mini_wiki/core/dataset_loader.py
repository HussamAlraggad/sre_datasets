"""
Dataset Loader Module
Handles loading data from multiple formats: CSV, JSON, JSONL, PDF, TXT, URLs

Supports:
- CSV files with configurable delimiters and encoding
- JSON files (single object or array of objects)
- JSONL files (one JSON object per line)
- PDF files with text extraction
- TXT files with line-by-line parsing
- URLs (fetches and parses content)
- Auto-detection of format based on file extension or content
"""

import csv
import json
import logging
import mimetypes
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
from urllib.request import urlopen

import requests

logger = logging.getLogger(__name__)


@dataclass
class LoaderConfig:
    """Configuration for dataset loader

    Attributes:
        csv_delimiter: Delimiter for CSV files (default: ',')
        csv_encoding: Encoding for CSV files (default: 'utf-8')
        json_nested_key: Key to extract from nested JSON (default: None)
        pdf_extract_method: Method for PDF extraction ('pdfplumber' or 'pypdf')
        txt_delimiter: Delimiter for TXT files (default: '\n')
        url_timeout: Timeout for URL requests in seconds (default: 30)
        url_headers: Custom headers for URL requests (default: None)
        max_file_size: Maximum file size in MB (default: 100)
        auto_detect: Auto-detect format from file extension (default: True)
        preserve_metadata: Preserve original metadata (default: True)
    """

    csv_delimiter: str = ","
    csv_encoding: str = "utf-8"
    json_nested_key: Optional[str] = None
    pdf_extract_method: str = "pdfplumber"
    txt_delimiter: str = "\n"
    url_timeout: int = 30
    url_headers: Optional[Dict[str, str]] = None
    max_file_size: int = 100  # MB
    auto_detect: bool = True
    preserve_metadata: bool = True


class DataLoader(ABC):
    """Abstract base class for data loaders"""

    def __init__(self, config: LoaderConfig):
        """Initialize loader

        Args:
            config: Loader configuration
        """
        self.config = config

    @abstractmethod
    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load data from source

        Args:
            source: Path or URL to data source

        Returns:
            List of dictionaries representing records

        Raises:
            ValueError: If source is invalid or cannot be parsed
            IOError: If file cannot be read
        """
        pass

    def _validate_source(self, source: Union[str, Path]) -> Path:
        """Validate source file exists and is readable

        Args:
            source: Path to source file

        Returns:
            Validated Path object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large
        """
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")

        if not path.is_file():
            raise ValueError(f"Not a file: {source}")

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB "
                f"(max: {self.config.max_file_size}MB)"
            )

        return path

    def _add_metadata(
        self, records: List[Dict[str, Any]], source: Union[str, Path]
    ) -> List[Dict[str, Any]]:
        """Add metadata to records

        Args:
            records: List of records
            source: Source file or URL

        Returns:
            Records with metadata added
        """
        if not self.config.preserve_metadata:
            return records

        metadata = {
            "_source": str(source),
            "_loaded_at": datetime.now().isoformat(),
            "_format": self.__class__.__name__,
            "_record_count": len(records),
        }

        for record in records:
            record["_metadata"] = metadata

        return records


class CSVLoader(DataLoader):
    """Load data from CSV files"""

    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load CSV file

        Args:
            source: Path to CSV file

        Returns:
            List of dictionaries (one per row)

        Raises:
            ValueError: If CSV is invalid
            IOError: If file cannot be read
        """
        path = self._validate_source(source)
        records = []

        try:
            with open(
                path, "r", encoding=self.config.csv_encoding, newline=""
            ) as f:
                reader = csv.DictReader(f, delimiter=self.config.csv_delimiter)

                if reader.fieldnames is None:
                    raise ValueError("CSV file has no headers")

                for row_num, row in enumerate(reader, start=2):
                    # Convert empty strings to None
                    record = {k: v if v else None for k, v in row.items()}
                    records.append(record)

            logger.info(f"Loaded {len(records)} records from CSV: {source}")

            return self._add_metadata(records, source)

        except csv.Error as e:
            raise ValueError(f"CSV parsing error: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Encoding error (try --csv-encoding): {e}"
            )


class JSONLoader(DataLoader):
    """Load data from JSON files"""

    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load JSON file

        Args:
            source: Path to JSON file

        Returns:
            List of dictionaries

        Raises:
            ValueError: If JSON is invalid
            IOError: If file cannot be read
        """
        path = self._validate_source(source)

        try:
            with open(path, "r", encoding=self.config.csv_encoding) as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # If nested key specified, extract from that key
                if self.config.json_nested_key:
                    if self.config.json_nested_key not in data:
                        raise ValueError(
                            f"Key '{self.config.json_nested_key}' not found in JSON"
                        )
                    records = data[self.config.json_nested_key]
                    if not isinstance(records, list):
                        raise ValueError(
                            f"Value at '{self.config.json_nested_key}' is not a list"
                        )
                else:
                    # Treat single object as single-item list
                    records = [data]
            else:
                raise ValueError(f"Unexpected JSON type: {type(data)}")

            # Ensure all records are dictionaries
            if not all(isinstance(r, dict) for r in records):
                raise ValueError("Not all JSON records are objects")

            logger.info(f"Loaded {len(records)} records from JSON: {source}")

            return self._add_metadata(records, source)

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parsing error: {e}")


class JSONLLoader(DataLoader):
    """Load data from JSONL files (one JSON object per line)"""

    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load JSONL file

        Args:
            source: Path to JSONL file

        Returns:
            List of dictionaries

        Raises:
            ValueError: If JSONL is invalid
            IOError: If file cannot be read
        """
        path = self._validate_source(source)
        records = []

        try:
            with open(path, "r", encoding=self.config.csv_encoding) as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()

                    # Skip empty lines
                    if not line:
                        continue

                    try:
                        record = json.loads(line)

                        if not isinstance(record, dict):
                            raise ValueError(
                                f"Line {line_num}: not a JSON object"
                            )

                        records.append(record)

                    except json.JSONDecodeError as e:
                        raise ValueError(f"Line {line_num}: {e}")

            logger.info(f"Loaded {len(records)} records from JSONL: {source}")

            return self._add_metadata(records, source)

        except UnicodeDecodeError as e:
            raise ValueError(f"Encoding error: {e}")


class PDFLoader(DataLoader):
    """Load data from PDF files"""

    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load PDF file

        Args:
            source: Path to PDF file

        Returns:
            List of dictionaries (one per page)

        Raises:
            ValueError: If PDF cannot be read
            ImportError: If required PDF library not installed
        """
        path = self._validate_source(source)

        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber not installed. Install with: pip install pdfplumber"
            )

        records = []

        try:
            with pdfplumber.open(path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()

                    if text:
                        record = {
                            "page": page_num,
                            "text": text,
                            "width": page.width,
                            "height": page.height,
                        }
                        records.append(record)

            logger.info(f"Loaded {len(records)} pages from PDF: {source}")

            return self._add_metadata(records, source)

        except Exception as e:
            raise ValueError(f"PDF extraction error: {e}")


class TXTLoader(DataLoader):
    """Load data from TXT files"""

    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load TXT file

        Args:
            source: Path to TXT file

        Returns:
            List of dictionaries (one per line or paragraph)

        Raises:
            ValueError: If TXT cannot be read
            IOError: If file cannot be read
        """
        path = self._validate_source(source)
        records = []

        try:
            with open(path, "r", encoding=self.config.csv_encoding) as f:
                content = f.read()

            # Split by delimiter (default: newline)
            lines = content.split(self.config.txt_delimiter)

            for line_num, line in enumerate(lines, start=1):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                record = {
                    "line": line_num,
                    "text": line,
                    "length": len(line),
                }
                records.append(record)

            logger.info(f"Loaded {len(records)} lines from TXT: {source}")

            return self._add_metadata(records, source)

        except UnicodeDecodeError as e:
            raise ValueError(f"Encoding error: {e}")


class URLLoader(DataLoader):
    """Load data from URLs"""

    def load(self, source: str) -> List[Dict[str, Any]]:
        """Load data from URL

        Args:
            source: URL to fetch

        Returns:
            List of dictionaries

        Raises:
            ValueError: If URL is invalid or cannot be fetched
            IOError: If request fails
        """
        # Validate URL
        try:
            result = urlparse(source)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"Invalid URL: {source}")
        except Exception as e:
            raise ValueError(f"URL parsing error: {e}")

        try:
            # Fetch content
            headers = self.config.url_headers or {
                "User-Agent": "mini_wiki/1.0"
            }

            response = requests.get(
                source,
                timeout=self.config.url_timeout,
                headers=headers,
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()

            # Detect format from content type
            if "application/json" in content_type:
                data = response.json()
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = [data]
                else:
                    raise ValueError("Unexpected JSON structure")

            elif "text/csv" in content_type:
                # Parse CSV from response text
                lines = response.text.split("\n")
                reader = csv.DictReader(lines, delimiter=self.config.csv_delimiter)
                records = list(reader)

            else:
                # Default to plain text
                text = response.text
                lines = text.split("\n")
                records = [
                    {"line": i + 1, "text": line.strip()}
                    for i, line in enumerate(lines)
                    if line.strip()
                ]

            logger.info(f"Loaded {len(records)} records from URL: {source}")

            return self._add_metadata(records, source)

        except requests.RequestException as e:
            raise IOError(f"Failed to fetch URL: {e}")
        except Exception as e:
            raise ValueError(f"URL parsing error: {e}")


class DatasetLoader:
    """Main dataset loader with auto-detection and format routing"""

    def __init__(self, config: Optional[LoaderConfig] = None):
        """Initialize dataset loader

        Args:
            config: Loader configuration (uses defaults if None)
        """
        self.config = config or LoaderConfig()
        self.loaders = {
            ".csv": CSVLoader(self.config),
            ".json": JSONLoader(self.config),
            ".jsonl": JSONLLoader(self.config),
            ".pdf": PDFLoader(self.config),
            ".txt": TXTLoader(self.config),
        }

    def load(self, source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load data from source with auto-detection

        Args:
            source: Path to file or URL

        Returns:
            List of dictionaries

        Raises:
            ValueError: If format cannot be detected or is unsupported
            IOError: If source cannot be read
        """
        source_str = str(source)

        # Check if URL
        if source_str.startswith(("http://", "https://")):
            logger.info(f"Loading from URL: {source_str}")
            loader = URLLoader(self.config)
            return loader.load(source_str)

        # Detect format from file extension
        path = Path(source)
        extension = path.suffix.lower()

        if extension not in self.loaders:
            raise ValueError(
                f"Unsupported format: {extension}. "
                f"Supported: {', '.join(self.loaders.keys())}"
            )

        logger.info(f"Loading {extension} file: {source}")
        loader = self.loaders[extension]

        return loader.load(source)

    def load_multiple(
        self, sources: List[Union[str, Path]]
    ) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
        """Load data from multiple sources

        Args:
            sources: List of paths or URLs

        Returns:
            Tuple of (combined records, list of errors)
        """
        all_records = []
        errors = []

        for source in sources:
            try:
                records = self.load(source)
                all_records.extend(records)
                logger.info(f"Successfully loaded {len(records)} records from {source}")

            except Exception as e:
                error_msg = f"Failed to load {source}: {str(e)}"
                logger.error(error_msg)
                errors.append((str(source), str(e)))

        logger.info(
            f"Loaded {len(all_records)} total records from {len(sources)} sources"
        )

        return all_records, errors

    def get_loader(self, format_name: str) -> Optional[DataLoader]:
        """Get loader for specific format

        Args:
            format_name: Format name (e.g., 'csv', 'json')

        Returns:
            DataLoader instance or None if format not found
        """
        extension = f".{format_name.lower()}"
        return self.loaders.get(extension)

    @staticmethod
    def detect_format(source: Union[str, Path]) -> str:
        """Detect format from source

        Args:
            source: Path or URL

        Returns:
            Format name (e.g., 'csv', 'json')

        Raises:
            ValueError: If format cannot be detected
        """
        source_str = str(source)

        # Check if URL
        if source_str.startswith(("http://", "https://")):
            return "url"

        # Check file extension
        path = Path(source)
        extension = path.suffix.lower()

        if extension.startswith("."):
            return extension[1:]  # Remove leading dot

        raise ValueError(f"Cannot detect format for: {source}")
