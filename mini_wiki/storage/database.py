"""
Database Module
Handles data persistence using SQLite

Features:
- Schema creation and migration
- CRUD operations
- Batch operations
- Transaction support
- Query building
"""

import json
import logging
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from mini_wiki.core.data_models import DataRecord, Dataset

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuration for database

    Attributes:
        db_path: Path to SQLite database file
        timeout: Connection timeout in seconds
        check_same_thread: Allow same thread check (default: False for multi-threading)
    """

    def __init__(
        self,
        db_path: Union[str, Path] = "mini_wiki.db",
        timeout: float = 30.0,
        check_same_thread: bool = False,
    ):
        self.db_path = Path(db_path)
        self.timeout = timeout
        self.check_same_thread = check_same_thread


class Database:
    """SQLite database for mini_wiki"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize database

        Args:
            config: Database configuration
        """
        self.config = config or DatabaseConfig()
        self.connection = None
        self.cursor = None

    def connect(self) -> None:
        """Connect to database

        Raises:
            sqlite3.Error: If connection fails
        """
        try:
            # Create parent directory if needed
            self.config.db_path.parent.mkdir(parents=True, exist_ok=True)

            self.connection = sqlite3.connect(
                str(self.config.db_path),
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread,
            )

            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")

            self.cursor = self.connection.cursor()

            logger.info(f"Connected to database: {self.config.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            logger.info("Disconnected from database")

    def create_schema(self) -> None:
        """Create database schema

        Raises:
            sqlite3.Error: If schema creation fails
        """
        if not self.connection:
            raise RuntimeError("Not connected to database")

        try:
            # Create datasets table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    source TEXT,
                    format TEXT,
                    record_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
                """
            )

            # Create records table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    original_id TEXT,
                    text TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                )
                """
            )

            # Create embeddings table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL UNIQUE,
                    embedding_model TEXT,
                    embedding_dim INTEGER,
                    embedding_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
                """
            )

            # Create indices for performance
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_records_dataset_id ON records(dataset_id)"
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_embeddings_record_id ON embeddings(record_id)"
            )

            self.connection.commit()

            logger.info("Database schema created successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to create schema: {e}")
            self.connection.rollback()
            raise

    def insert_dataset(
        self,
        name: str,
        description: Optional[str] = None,
        source: Optional[str] = None,
        format: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Insert dataset

        Args:
            name: Dataset name
            description: Dataset description
            source: Data source
            format: Data format
            metadata: Additional metadata

        Returns:
            Dataset ID

        Raises:
            sqlite3.IntegrityError: If dataset name already exists
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None

            self.cursor.execute(
                """
                INSERT INTO datasets (name, description, source, format, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, description, source, format, metadata_json),
            )

            self.connection.commit()

            dataset_id = self.cursor.lastrowid

            logger.info(f"Inserted dataset '{name}' with ID {dataset_id}")

            return dataset_id

        except sqlite3.IntegrityError as e:
            logger.error(f"Dataset name already exists: {name}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to insert dataset: {e}")
            self.connection.rollback()
            raise

    def insert_records(
        self, dataset_id: int, records: List[Dict[str, Any]]
    ) -> List[int]:
        """Insert records

        Args:
            dataset_id: Dataset ID
            records: List of records

        Returns:
            List of record IDs

        Raises:
            sqlite3.Error: If insertion fails
        """
        try:
            record_ids = []

            for record in records:
                # Extract text field
                text = record.get("text", "")
                if not isinstance(text, str):
                    text = str(text)

                # Store remaining data as JSON
                data = {k: v for k, v in record.items() if k != "text"}
                data_json = json.dumps(data)

                self.cursor.execute(
                    """
                    INSERT INTO records (dataset_id, text, data)
                    VALUES (?, ?, ?)
                    """,
                    (dataset_id, text, data_json),
                )

                record_ids.append(self.cursor.lastrowid)

            self.connection.commit()

            # Update record count
            self.cursor.execute(
                "UPDATE datasets SET record_count = record_count + ? WHERE id = ?",
                (len(records), dataset_id),
            )
            self.connection.commit()

            logger.info(f"Inserted {len(records)} records into dataset {dataset_id}")

            return record_ids

        except sqlite3.Error as e:
            logger.error(f"Failed to insert records: {e}")
            self.connection.rollback()
            raise

    def get_dataset(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """Get dataset by ID

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset dictionary or None if not found
        """
        self.cursor.execute(
            "SELECT * FROM datasets WHERE id = ?",
            (dataset_id,),
        )

        row = self.cursor.fetchone()

        if not row:
            return None

        columns = [desc[0] for desc in self.cursor.description]
        dataset = dict(zip(columns, row))

        # Parse metadata
        if dataset["metadata"]:
            dataset["metadata"] = json.loads(dataset["metadata"])

        return dataset

    def get_dataset_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get dataset by name

        Args:
            name: Dataset name

        Returns:
            Dataset dictionary or None if not found
        """
        self.cursor.execute(
            "SELECT * FROM datasets WHERE name = ?",
            (name,),
        )

        row = self.cursor.fetchone()

        if not row:
            return None

        columns = [desc[0] for desc in self.cursor.description]
        dataset = dict(zip(columns, row))

        # Parse metadata
        if dataset["metadata"]:
            dataset["metadata"] = json.loads(dataset["metadata"])

        return dataset

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets

        Returns:
            List of dataset dictionaries
        """
        self.cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC")

        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]

        datasets = []
        for row in rows:
            dataset = dict(zip(columns, row))
            if dataset["metadata"]:
                dataset["metadata"] = json.loads(dataset["metadata"])
            datasets.append(dataset)

        return datasets

    def get_records(
        self, dataset_id: int, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get records from dataset

        Args:
            dataset_id: Dataset ID
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            List of record dictionaries
        """
        query = "SELECT * FROM records WHERE dataset_id = ? ORDER BY id"

        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        self.cursor.execute(query, (dataset_id,))

        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]

        records = []
        for row in rows:
            record = dict(zip(columns, row))
            if record["data"]:
                record["data"] = json.loads(record["data"])
            records.append(record)

        return records

    def get_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get record by ID

        Args:
            record_id: Record ID

        Returns:
            Record dictionary or None if not found
        """
        self.cursor.execute(
            "SELECT * FROM records WHERE id = ?",
            (record_id,),
        )

        row = self.cursor.fetchone()

        if not row:
            return None

        columns = [desc[0] for desc in self.cursor.description]
        record = dict(zip(columns, row))

        if record["data"]:
            record["data"] = json.loads(record["data"])

        return record

    def insert_embedding(
        self,
        record_id: int,
        embedding_model: str,
        embedding_dim: int,
        embedding_file: str,
    ) -> int:
        """Insert embedding metadata

        Args:
            record_id: Record ID
            embedding_model: Model name
            embedding_dim: Embedding dimension
            embedding_file: Path to embedding file

        Returns:
            Embedding ID
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO embeddings (record_id, embedding_model, embedding_dim, embedding_file)
                VALUES (?, ?, ?, ?)
                """,
                (record_id, embedding_model, embedding_dim, embedding_file),
            )

            self.connection.commit()

            embedding_id = self.cursor.lastrowid

            logger.info(f"Inserted embedding for record {record_id}")

            return embedding_id

        except sqlite3.Error as e:
            logger.error(f"Failed to insert embedding: {e}")
            self.connection.rollback()
            raise

    def get_embedding(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get embedding metadata

        Args:
            record_id: Record ID

        Returns:
            Embedding dictionary or None if not found
        """
        self.cursor.execute(
            "SELECT * FROM embeddings WHERE record_id = ?",
            (record_id,),
        )

        row = self.cursor.fetchone()

        if not row:
            return None

        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def delete_dataset(self, dataset_id: int) -> None:
        """Delete dataset and all associated records

        Args:
            dataset_id: Dataset ID
        """
        try:
            self.cursor.execute(
                "DELETE FROM datasets WHERE id = ?",
                (dataset_id,),
            )

            self.connection.commit()

            logger.info(f"Deleted dataset {dataset_id}")

        except sqlite3.Error as e:
            logger.error(f"Failed to delete dataset: {e}")
            self.connection.rollback()
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics

        Returns:
            Dictionary with stats
        """
        self.cursor.execute("SELECT COUNT(*) FROM datasets")
        dataset_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM records")
        record_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM embeddings")
        embedding_count = self.cursor.fetchone()[0]

        return {
            "datasets": dataset_count,
            "records": record_count,
            "embeddings": embedding_count,
        }

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
