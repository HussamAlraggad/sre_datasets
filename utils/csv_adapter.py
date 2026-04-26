"""
utils/csv_adapter.py
====================
Normalize arbitrary CSV files to a standard schema.

The CsvAdapter handles:
  1. Auto-detecting CSV columns
  2. Mapping user-specified columns to text_columns and metadata_columns
  3. Combining text columns into a single review document
  4. Handling missing/null values gracefully
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd


class CsvAdapter:
    """Adapts arbitrary CSV files to the standard SRE-RAG schema."""

    def __init__(self, csv_path: Path):
        """
        Initialize the adapter with a CSV file.

        Args:
            csv_path: Path to the CSV file
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Load first few rows to detect schema
        self.df_sample = pd.read_csv(self.csv_path, nrows=100)
        self.all_columns = list(self.df_sample.columns)

    def get_columns(self) -> List[str]:
        """Return list of all columns in the CSV."""
        return self.all_columns

    def get_sample_data(self, nrows: int = 5) -> pd.DataFrame:
        """Return sample rows from the CSV for user inspection."""
        return pd.read_csv(self.csv_path, nrows=nrows)

    def combine_text_columns(
        self,
        text_columns: List[str],
        metadata_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Load CSV and combine specified text columns into a single 'text' column.

        Args:
            text_columns: List of column names to combine into review text
            metadata_columns: Optional list of columns to preserve as metadata

        Returns:
            DataFrame with 'text' column (combined) and metadata columns
        """
        # Validate that all requested columns exist
        missing = set(text_columns) - set(self.all_columns)
        if missing:
            raise ValueError(f"Columns not found in CSV: {missing}")

        if metadata_columns:
            missing_meta = set(metadata_columns) - set(self.all_columns)
            if missing_meta:
                raise ValueError(f"Metadata columns not found in CSV: {missing_meta}")

        # Load full CSV
        df = pd.read_csv(self.csv_path)

        # Combine text columns
        def combine_row(row: pd.Series) -> str:
            """Combine text columns for a single row."""
            parts = []
            for col in text_columns:
                val = row.get(col, "")
                if pd.notna(val) and str(val).strip():
                    parts.append(f"{col.upper()}: {str(val).strip()}")
            return "\n".join(parts) if parts else ""

        df["text"] = df.apply(combine_row, axis=1)

        # Keep only text + metadata columns
        keep_cols = ["text"]
        if metadata_columns:
            keep_cols.extend(metadata_columns)

        result = df[keep_cols].copy()

        # Remove rows where text is empty
        result = result[result["text"].str.strip() != ""]

        return result

    def get_column_stats(self) -> Dict[str, Any]:
        """
        Return statistics about the CSV columns.

        Returns:
            Dict with column names, types, null counts, sample values
        """
        stats = {}
        for col in self.all_columns:
            stats[col] = {
                "dtype": str(self.df_sample[col].dtype),
                "null_count": self.df_sample[col].isnull().sum(),
                "sample_values": self.df_sample[col].dropna().head(2).tolist(),
            }
        return stats
