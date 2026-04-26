"""
utils/metadata_extractor.py
===========================
Extract and suggest metadata columns from CSV files.

The MetadataExtractor helps users identify which columns should be:
  1. Text columns (combined for analysis)
  2. Metadata columns (preserved for reference/filtering)
"""

from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd


class MetadataExtractor:
    """Analyzes CSV structure to suggest metadata columns."""

    def __init__(self, csv_path: Path):
        """
        Initialize the extractor with a CSV file.

        Args:
            csv_path: Path to the CSV file
        """
        self.csv_path = Path(csv_path)
        self.df = pd.read_csv(self.csv_path, nrows=1000)  # Sample for analysis

    def suggest_text_columns(self) -> List[str]:
        """
        Suggest which columns are likely text content (long strings).

        Returns:
            List of column names that appear to be text content
        """
        text_cols = []
        for col in self.df.columns:
            # Check if column contains mostly strings with decent length
            sample = self.df[col].dropna().astype(str).head(10)
            avg_length = sample.str.len().mean()

            # If average length > 50 chars, likely text content
            if avg_length > 50:
                text_cols.append(col)

        return text_cols

    def suggest_metadata_columns(self) -> List[str]:
        """
        Suggest which columns are likely metadata (IDs, dates, ratings, etc).

        Returns:
            List of column names that appear to be metadata
        """
        metadata_cols = []
        for col in self.df.columns:
            # Skip very long text columns
            sample = self.df[col].dropna().astype(str).head(10)
            avg_length = sample.str.len().mean()

            if avg_length <= 50:
                # Check if it looks like ID, date, rating, category, etc.
                if any(
                    keyword in col.lower()
                    for keyword in [
                        "id",
                        "date",
                        "time",
                        "rating",
                        "score",
                        "category",
                        "type",
                        "status",
                        "author",
                        "user",
                    ]
                ):
                    metadata_cols.append(col)
                # Or if it has very few unique values (categorical)
                elif self.df[col].nunique() < 50:
                    metadata_cols.append(col)

        return metadata_cols

    def analyze_columns(self) -> Dict[str, Dict]:
        """
        Comprehensive analysis of all columns.

        Returns:
            Dict mapping column name to analysis (type, uniqueness, length stats)
        """
        analysis = {}
        for col in self.df.columns:
            non_null = self.df[col].notna().sum()
            unique = self.df[col].nunique()
            sample = self.df[col].dropna().astype(str).head(5).tolist()

            analysis[col] = {
                "dtype": str(self.df[col].dtype),
                "non_null": non_null,
                "unique_values": unique,
                "sample": sample,
                "suggested_type": self._infer_type(col, unique, sample),
            }

        return analysis

    def _infer_type(self, col: str, unique: int, sample: List[str]) -> str:
        """Infer the likely type of a column."""
        # Check column name hints
        col_lower = col.lower()
        if any(k in col_lower for k in ["id", "code"]):
            return "identifier"
        if any(k in col_lower for k in ["date", "time"]):
            return "temporal"
        if any(k in col_lower for k in ["rating", "score", "rank"]):
            return "numeric_metric"

        # Check content
        if unique < 20:
            return "categorical"

        avg_len = sum(len(s) for s in sample) / len(sample) if sample else 0
        if avg_len > 100:
            return "text_content"
        elif avg_len > 20:
            return "short_text"
        else:
            return "identifier_or_code"
