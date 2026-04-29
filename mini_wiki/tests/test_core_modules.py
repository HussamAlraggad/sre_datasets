"""
Unit Tests for Core Modules
Tests for dataset_loader, embeddings, indexing, and database modules
"""

import json
import tempfile
from pathlib import Path
from typing import List

import numpy as np
import pytest

from mini_wiki.core.dataset_loader import (
    CSVLoader,
    DatasetLoader,
    JSONLoader,
    JSONLLoader,
    LoaderConfig,
    TXTLoader,
)
from mini_wiki.core.embeddings import EmbeddingConfig, EmbeddingManager
from mini_wiki.core.indexing import IndexConfig, IndexManager
from mini_wiki.storage.database import Database, DatabaseConfig


# ============================================================================
# Dataset Loader Tests
# ============================================================================


class TestCSVLoader:
    """Tests for CSV loader"""

    def test_load_valid_csv(self, tmp_path):
        """Test loading valid CSV file"""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n")

        config = LoaderConfig()
        loader = CSVLoader(config)

        records = loader.load(csv_file)

        assert len(records) == 2
        assert records[0]["name"] == "Alice"
        assert records[0]["age"] == "30"
        assert records[1]["name"] == "Bob"

    def test_load_csv_with_custom_delimiter(self, tmp_path):
        """Test loading CSV with custom delimiter"""
        # Create test CSV with semicolon delimiter
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name;age;city\nAlice;30;NYC\nBob;25;LA\n")

        config = LoaderConfig(csv_delimiter=";")
        loader = CSVLoader(config)

        records = loader.load(csv_file)

        assert len(records) == 2
        assert records[0]["name"] == "Alice"

    def test_load_csv_missing_file(self):
        """Test loading non-existent CSV file"""
        config = LoaderConfig()
        loader = CSVLoader(config)

        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.csv")

    def test_load_csv_with_metadata(self, tmp_path):
        """Test that metadata is preserved"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        config = LoaderConfig(preserve_metadata=True)
        loader = CSVLoader(config)

        records = loader.load(csv_file)

        assert "_metadata" in records[0]
        assert records[0]["_metadata"]["_format"] == "CSVLoader"


class TestJSONLoader:
    """Tests for JSON loader"""

    def test_load_json_array(self, tmp_path):
        """Test loading JSON array"""
        json_file = tmp_path / "test.json"
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        json_file.write_text(json.dumps(data))

        config = LoaderConfig()
        loader = JSONLoader(config)

        records = loader.load(json_file)

        assert len(records) == 2
        assert records[0]["name"] == "Alice"

    def test_load_json_object(self, tmp_path):
        """Test loading single JSON object"""
        json_file = tmp_path / "test.json"
        data = {"name": "Alice", "age": 30}
        json_file.write_text(json.dumps(data))

        config = LoaderConfig()
        loader = JSONLoader(config)

        records = loader.load(json_file)

        assert len(records) == 1
        assert records[0]["name"] == "Alice"

    def test_load_json_nested(self, tmp_path):
        """Test loading nested JSON with key extraction"""
        json_file = tmp_path / "test.json"
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        json_file.write_text(json.dumps(data))

        config = LoaderConfig(json_nested_key="users")
        loader = JSONLoader(config)

        records = loader.load(json_file)

        assert len(records) == 2
        assert records[0]["name"] == "Alice"


class TestJSONLLoader:
    """Tests for JSONL loader"""

    def test_load_jsonl(self, tmp_path):
        """Test loading JSONL file"""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "Alice", "age": 30}\n{"name": "Bob", "age": 25}\n')

        config = LoaderConfig()
        loader = JSONLLoader(config)

        records = loader.load(jsonl_file)

        assert len(records) == 2
        assert records[0]["name"] == "Alice"

    def test_load_jsonl_with_empty_lines(self, tmp_path):
        """Test loading JSONL with empty lines"""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "Alice"}\n\n{"name": "Bob"}\n')

        config = LoaderConfig()
        loader = JSONLLoader(config)

        records = loader.load(jsonl_file)

        assert len(records) == 2


class TestTXTLoader:
    """Tests for TXT loader"""

    def test_load_txt(self, tmp_path):
        """Test loading TXT file"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Line 1\nLine 2\nLine 3\n")

        config = LoaderConfig()
        loader = TXTLoader(config)

        records = loader.load(txt_file)

        assert len(records) == 3
        assert records[0]["text"] == "Line 1"

    def test_load_txt_with_empty_lines(self, tmp_path):
        """Test loading TXT with empty lines"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Line 1\n\nLine 3\n")

        config = LoaderConfig()
        loader = TXTLoader(config)

        records = loader.load(txt_file)

        assert len(records) == 2


class TestDatasetLoader:
    """Tests for main dataset loader"""

    def test_auto_detect_csv(self, tmp_path):
        """Test auto-detection of CSV format"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        loader = DatasetLoader()
        records = loader.load(csv_file)

        assert len(records) == 1

    def test_auto_detect_json(self, tmp_path):
        """Test auto-detection of JSON format"""
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"name": "Alice"}]))

        loader = DatasetLoader()
        records = loader.load(json_file)

        assert len(records) == 1

    def test_load_multiple_sources(self, tmp_path):
        """Test loading from multiple sources"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name\nAlice\n")

        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps([{"name": "Bob"}]))

        loader = DatasetLoader()
        records, errors = loader.load_multiple([csv_file, json_file])

        assert len(records) == 2
        assert len(errors) == 0

    def test_detect_format(self):
        """Test format detection"""
        assert DatasetLoader.detect_format("test.csv") == "csv"
        assert DatasetLoader.detect_format("test.json") == "json"
        assert DatasetLoader.detect_format("test.jsonl") == "jsonl"
        assert DatasetLoader.detect_format("test.txt") == "txt"


# ============================================================================
# Embeddings Tests
# ============================================================================


class TestEmbeddingManager:
    """Tests for embedding manager"""

    @pytest.fixture
    def embedding_manager(self):
        """Create embedding manager"""
        config = EmbeddingConfig(
            model_name="all-MiniLM-L6-v2",
            batch_size=2,
            cache_embeddings=True,
        )
        return EmbeddingManager(config)

    def test_embed_texts(self, embedding_manager):
        """Test embedding texts"""
        texts = ["Hello world", "This is a test"]
        embeddings = embedding_manager.embed_texts(texts)

        assert embeddings.shape[0] == 2
        assert embeddings.shape[1] == embedding_manager.get_embedding_dim()

    def test_embed_texts_caching(self, embedding_manager):
        """Test that embeddings are cached"""
        texts = ["Hello world"]

        # First call
        embeddings1 = embedding_manager.embed_texts(texts)

        # Second call (should use cache)
        embeddings2 = embedding_manager.embed_texts(texts)

        np.testing.assert_array_equal(embeddings1, embeddings2)

    def test_embed_records(self, embedding_manager):
        """Test embedding records"""
        records = [
            {"text": "Hello world", "id": 1},
            {"text": "This is a test", "id": 2},
        ]

        embeddings, texts = embedding_manager.embed_records(records)

        assert embeddings.shape[0] == 2
        assert len(texts) == 2

    def test_compute_similarity(self, embedding_manager):
        """Test similarity computation"""
        texts = ["Hello world", "Hello world"]
        embeddings = embedding_manager.embed_texts(texts)

        similarity = embedding_manager.compute_similarity(embeddings[0], embeddings[1])

        assert 0.99 <= similarity <= 1.01  # Should be very similar

    def test_find_similar(self, embedding_manager):
        """Test finding similar embeddings"""
        texts = ["Hello world", "This is a test", "Another test"]
        embeddings = embedding_manager.embed_texts(texts)

        results = embedding_manager.find_similar("Hello world", embeddings, top_k=2)

        assert len(results) == 2
        assert results[0][0] == 0  # Most similar should be itself

    def test_save_load_embeddings(self, embedding_manager, tmp_path):
        """Test saving and loading embeddings"""
        texts = ["Hello world", "This is a test"]
        embeddings = embedding_manager.embed_texts(texts)

        # Save
        save_path = tmp_path / "embeddings.npy"
        embedding_manager.save_embeddings(embeddings, save_path)

        # Load
        loaded = embedding_manager.load_embeddings(save_path)

        np.testing.assert_array_equal(embeddings, loaded)


# ============================================================================
# Indexing Tests
# ============================================================================


class TestIndexManager:
    """Tests for index manager"""

    @pytest.fixture
    def index_manager(self):
        """Create index manager"""
        config = IndexConfig(index_type="flat", metric="l2")
        return IndexManager(config)

    def test_create_index(self, index_manager):
        """Test index creation"""
        index_manager.create(dimension=384)

        assert index_manager.index.dimension == 384
        assert index_manager.index.size == 0

    def test_add_embeddings(self, index_manager):
        """Test adding embeddings"""
        index_manager.create(dimension=384)

        embeddings = np.random.randn(10, 384).astype(np.float32)
        index_manager.add_embeddings(embeddings)

        assert index_manager.index.size == 10

    def test_search(self, index_manager):
        """Test searching index"""
        index_manager.create(dimension=384)

        embeddings = np.random.randn(10, 384).astype(np.float32)
        index_manager.add_embeddings(embeddings)

        query = embeddings[0]
        results = index_manager.search(query, k=3)

        assert len(results) == 3
        assert results[0][0] == 0  # First result should be itself

    def test_search_batch(self, index_manager):
        """Test batch search"""
        index_manager.create(dimension=384)

        embeddings = np.random.randn(10, 384).astype(np.float32)
        index_manager.add_embeddings(embeddings)

        queries = embeddings[:2]
        results = index_manager.search_batch(queries, k=3)

        assert len(results) == 2
        assert len(results[0]) == 3

    def test_save_load_index(self, index_manager, tmp_path):
        """Test saving and loading index"""
        index_manager.create(dimension=384)

        embeddings = np.random.randn(10, 384).astype(np.float32)
        index_manager.add_embeddings(embeddings, record_ids=list(range(10)))

        # Save
        index_path = tmp_path / "index.faiss"
        id_map_path = tmp_path / "id_map.pkl"
        index_manager.save(index_path, id_map_path)

        # Load
        new_manager = IndexManager()
        new_manager.load(index_path, id_map_path)

        assert new_manager.index.size == 10
        assert len(new_manager.id_map) == 10


# ============================================================================
# Database Tests
# ============================================================================


class TestDatabase:
    """Tests for database"""

    @pytest.fixture
    def database(self, tmp_path):
        """Create database"""
        config = DatabaseConfig(db_path=tmp_path / "test.db")
        db = Database(config)
        db.connect()
        db.create_schema()
        yield db
        db.disconnect()

    def test_insert_dataset(self, database):
        """Test inserting dataset"""
        dataset_id = database.insert_dataset(
            name="test_dataset",
            description="Test dataset",
            source="test.csv",
            format="csv",
        )

        assert dataset_id > 0

    def test_get_dataset(self, database):
        """Test getting dataset"""
        dataset_id = database.insert_dataset(name="test_dataset")

        dataset = database.get_dataset(dataset_id)

        assert dataset is not None
        assert dataset["name"] == "test_dataset"

    def test_get_dataset_by_name(self, database):
        """Test getting dataset by name"""
        database.insert_dataset(name="test_dataset")

        dataset = database.get_dataset_by_name("test_dataset")

        assert dataset is not None
        assert dataset["name"] == "test_dataset"

    def test_list_datasets(self, database):
        """Test listing datasets"""
        database.insert_dataset(name="dataset1")
        database.insert_dataset(name="dataset2")

        datasets = database.list_datasets()

        assert len(datasets) == 2

    def test_insert_records(self, database):
        """Test inserting records"""
        dataset_id = database.insert_dataset(name="test_dataset")

        records = [
            {"text": "Record 1", "id": 1},
            {"text": "Record 2", "id": 2},
        ]

        record_ids = database.insert_records(dataset_id, records)

        assert len(record_ids) == 2

    def test_get_records(self, database):
        """Test getting records"""
        dataset_id = database.insert_dataset(name="test_dataset")

        records = [
            {"text": "Record 1"},
            {"text": "Record 2"},
        ]

        database.insert_records(dataset_id, records)

        retrieved = database.get_records(dataset_id)

        assert len(retrieved) == 2
        assert retrieved[0]["text"] == "Record 1"

    def test_get_record(self, database):
        """Test getting single record"""
        dataset_id = database.insert_dataset(name="test_dataset")

        records = [{"text": "Record 1"}]
        record_ids = database.insert_records(dataset_id, records)

        record = database.get_record(record_ids[0])

        assert record is not None
        assert record["text"] == "Record 1"

    def test_insert_embedding(self, database):
        """Test inserting embedding"""
        dataset_id = database.insert_dataset(name="test_dataset")
        records = [{"text": "Record 1"}]
        record_ids = database.insert_records(dataset_id, records)

        embedding_id = database.insert_embedding(
            record_id=record_ids[0],
            embedding_model="all-MiniLM-L6-v2",
            embedding_dim=384,
            embedding_file="embeddings.npy",
        )

        assert embedding_id > 0

    def test_get_embedding(self, database):
        """Test getting embedding"""
        dataset_id = database.insert_dataset(name="test_dataset")
        records = [{"text": "Record 1"}]
        record_ids = database.insert_records(dataset_id, records)

        database.insert_embedding(
            record_id=record_ids[0],
            embedding_model="all-MiniLM-L6-v2",
            embedding_dim=384,
            embedding_file="embeddings.npy",
        )

        embedding = database.get_embedding(record_ids[0])

        assert embedding is not None
        assert embedding["embedding_model"] == "all-MiniLM-L6-v2"

    def test_delete_dataset(self, database):
        """Test deleting dataset"""
        dataset_id = database.insert_dataset(name="test_dataset")

        database.delete_dataset(dataset_id)

        dataset = database.get_dataset(dataset_id)

        assert dataset is None

    def test_get_stats(self, database):
        """Test getting database stats"""
        database.insert_dataset(name="dataset1")
        dataset_id = database.insert_dataset(name="dataset2")

        records = [{"text": "Record 1"}, {"text": "Record 2"}]
        database.insert_records(dataset_id, records)

        stats = database.get_stats()

        assert stats["datasets"] == 2
        assert stats["records"] == 2

    def test_context_manager(self, tmp_path):
        """Test using database as context manager"""
        config = DatabaseConfig(db_path=tmp_path / "test.db")

        with Database(config) as db:
            db.create_schema()
            db.insert_dataset(name="test_dataset")

        # Verify database was closed
        assert config.db_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
