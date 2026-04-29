"""
Unit tests for advanced features modules

Test coverage:
- Filter engine (filtering, sorting)
- Export manager (JSON, Markdown, CSV, PDF, HTML)
- Bookmarks manager (add, remove, search, collections)
- History manager (search history, recent items)
- Batch processor (batch operations)
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from mini_wiki.advanced.batch_processor import (
    BatchOperation,
    BatchOperationType,
    BatchProcessor,
    batch_export,
    batch_search,
)
from mini_wiki.advanced.bookmarks_manager import (
    Bookmark,
    BookmarkCollection,
    BookmarksManager,
)
from mini_wiki.advanced.export_manager import (
    ExportConfig,
    ExportFormat,
    ExportManager,
    export_to_csv,
    export_to_json,
    export_to_markdown,
)
from mini_wiki.advanced.filter_engine import (
    FilterCriteria,
    FilterEngine,
    SortCriteria,
    SortEngine,
    SortField,
    SortOrder,
    FilterSortEngine,
)
from mini_wiki.advanced.history_manager import (
    HistoryEntry,
    HistoryManager,
    RecentItem,
)


# ============================================================================
# Filter Engine Tests
# ============================================================================


class TestFilterCriteria:
    """Test FilterCriteria"""

    def test_filter_criteria_creation(self):
        """Test filter criteria creation"""
        criteria = FilterCriteria(
            min_relevance=0.5,
            max_relevance=1.0,
            sources=["source1", "source2"],
        )
        assert criteria.min_relevance == 0.5
        assert criteria.max_relevance == 1.0
        assert "source1" in criteria.sources


class TestFilterEngine:
    """Test FilterEngine"""

    def test_filter_engine_creation(self):
        """Test filter engine creation"""
        engine = FilterEngine()
        assert len(engine.filters) > 0

    def test_filter_by_relevance(self):
        """Test filter by relevance"""
        engine = FilterEngine()
        items = [
            {"id": 1, "relevance": 0.9},
            {"id": 2, "relevance": 0.5},
            {"id": 3, "relevance": 0.3},
        ]
        criteria = FilterCriteria(min_relevance=0.5, max_relevance=1.0)
        result = engine.filter(items, criteria)
        assert result.filtered_count == 2

    def test_filter_by_source(self):
        """Test filter by source"""
        engine = FilterEngine()
        items = [
            {"id": 1, "source": "source1"},
            {"id": 2, "source": "source2"},
            {"id": 3, "source": "source3"},
        ]
        criteria = FilterCriteria(sources=["source1", "source2"])
        result = engine.filter(items, criteria)
        assert result.filtered_count == 2

    def test_filter_by_tags(self):
        """Test filter by tags"""
        engine = FilterEngine()
        items = [
            {"id": 1, "tags": ["python", "ai"]},
            {"id": 2, "tags": ["javascript"]},
            {"id": 3, "tags": ["python", "web"]},
        ]
        criteria = FilterCriteria(tags=["python"])
        result = engine.filter(items, criteria)
        assert result.filtered_count == 2


class TestSortEngine:
    """Test SortEngine"""

    def test_sort_engine_creation(self):
        """Test sort engine creation"""
        engine = SortEngine()
        assert len(engine.sorters) > 0

    def test_sort_by_relevance(self):
        """Test sort by relevance"""
        engine = SortEngine()
        items = [
            {"id": 1, "relevance": 0.5},
            {"id": 2, "relevance": 0.9},
            {"id": 3, "relevance": 0.3},
        ]
        criteria = SortCriteria(field=SortField.RELEVANCE, order=SortOrder.DESCENDING)
        sorted_items = engine.sort(items, criteria)
        assert sorted_items[0]["relevance"] == 0.9

    def test_sort_by_title(self):
        """Test sort by title"""
        engine = SortEngine()
        items = [
            {"id": 1, "title": "Zebra"},
            {"id": 2, "title": "Apple"},
            {"id": 3, "title": "Banana"},
        ]
        criteria = SortCriteria(field=SortField.TITLE, order=SortOrder.ASCENDING)
        sorted_items = engine.sort(items, criteria)
        assert sorted_items[0]["title"] == "Apple"


class TestFilterSortEngine:
    """Test FilterSortEngine"""

    def test_filter_and_sort(self):
        """Test filter and sort together"""
        engine = FilterSortEngine()
        items = [
            {"id": 1, "relevance": 0.9, "source": "source1"},
            {"id": 2, "relevance": 0.5, "source": "source2"},
            {"id": 3, "relevance": 0.3, "source": "source1"},
        ]
        filter_criteria = FilterCriteria(sources=["source1"])
        sort_criteria = SortCriteria(field=SortField.RELEVANCE)
        result, stats = engine.process(items, filter_criteria, sort_criteria)
        assert stats["filtered_items"] == 2
        assert result[0]["relevance"] == 0.9


# ============================================================================
# Export Manager Tests
# ============================================================================


class TestExportConfig:
    """Test ExportConfig"""

    def test_export_config_creation(self):
        """Test export config creation"""
        config = ExportConfig(
            format=ExportFormat.JSON,
            output_path="/tmp/export.json",
        )
        assert config.format == ExportFormat.JSON


class TestExportManager:
    """Test ExportManager"""

    def test_export_manager_creation(self):
        """Test export manager creation"""
        manager = ExportManager()
        assert len(manager.exporters) > 0

    def test_export_to_json(self):
        """Test export to JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExportManager()
            items = [
                {"id": 1, "title": "Item 1", "content": "Content 1"},
                {"id": 2, "title": "Item 2", "content": "Content 2"},
            ]
            output_path = str(Path(tmpdir) / "export.json")
            config = ExportConfig(
                format=ExportFormat.JSON,
                output_path=output_path,
            )
            result = manager.export(items, config)
            assert result.success
            assert result.items_exported == 2

    def test_export_to_markdown(self):
        """Test export to Markdown"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExportManager()
            items = [
                {"id": 1, "title": "Item 1", "content": "Content 1"},
            ]
            output_path = str(Path(tmpdir) / "export.md")
            config = ExportConfig(
                format=ExportFormat.MARKDOWN,
                output_path=output_path,
            )
            result = manager.export(items, config)
            assert result.success

    def test_export_to_csv(self):
        """Test export to CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExportManager()
            items = [
                {"id": 1, "title": "Item 1", "content": "Content 1"},
            ]
            output_path = str(Path(tmpdir) / "export.csv")
            config = ExportConfig(
                format=ExportFormat.CSV,
                output_path=output_path,
            )
            result = manager.export(items, config)
            assert result.success


class TestExportConvenience:
    """Test export convenience functions"""

    def test_export_to_json_function(self):
        """Test export to JSON function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            items = [{"id": 1, "title": "Item 1"}]
            output_path = str(Path(tmpdir) / "export.json")
            result = export_to_json(items, output_path)
            assert result.success

    def test_export_to_markdown_function(self):
        """Test export to Markdown function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            items = [{"id": 1, "title": "Item 1"}]
            output_path = str(Path(tmpdir) / "export.md")
            result = export_to_markdown(items, output_path)
            assert result.success

    def test_export_to_csv_function(self):
        """Test export to CSV function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            items = [{"id": 1, "title": "Item 1"}]
            output_path = str(Path(tmpdir) / "export.csv")
            result = export_to_csv(items, output_path)
            assert result.success


# ============================================================================
# Bookmarks Manager Tests
# ============================================================================


class TestBookmark:
    """Test Bookmark"""

    def test_bookmark_creation(self):
        """Test bookmark creation"""
        bookmark = Bookmark(
            id="1",
            title="Test Bookmark",
            url="http://example.com",
            document_id="doc1",
        )
        assert bookmark.title == "Test Bookmark"

    def test_bookmark_to_dict(self):
        """Test bookmark to dict"""
        bookmark = Bookmark(
            id="1",
            title="Test",
            url="http://example.com",
            document_id="doc1",
        )
        data = bookmark.to_dict()
        assert data["title"] == "Test"

    def test_bookmark_from_dict(self):
        """Test bookmark from dict"""
        data = {
            "id": "1",
            "title": "Test",
            "url": "http://example.com",
            "document_id": "doc1",
            "tags": [],
            "notes": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        bookmark = Bookmark.from_dict(data)
        assert bookmark.title == "Test"


class TestBookmarksManager:
    """Test BookmarksManager"""

    def test_bookmarks_manager_creation(self):
        """Test bookmarks manager creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BookmarksManager(str(Path(tmpdir) / "bookmarks.json"))
            assert len(manager.bookmarks) == 0

    def test_add_bookmark(self):
        """Test add bookmark"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BookmarksManager(str(Path(tmpdir) / "bookmarks.json"))
            bookmark = manager.add_bookmark(
                title="Test",
                url="http://example.com",
                document_id="doc1",
            )
            assert bookmark.title == "Test"
            assert len(manager.bookmarks) == 1

    def test_remove_bookmark(self):
        """Test remove bookmark"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BookmarksManager(str(Path(tmpdir) / "bookmarks.json"))
            bookmark = manager.add_bookmark(
                title="Test",
                url="http://example.com",
                document_id="doc1",
            )
            removed = manager.remove_bookmark(bookmark.id)
            assert removed is True
            assert len(manager.bookmarks) == 0

    def test_search_bookmarks(self):
        """Test search bookmarks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BookmarksManager(str(Path(tmpdir) / "bookmarks.json"))
            manager.add_bookmark(
                title="Python Tutorial",
                url="http://example.com",
                document_id="doc1",
            )
            manager.add_bookmark(
                title="JavaScript Guide",
                url="http://example.com",
                document_id="doc2",
            )
            results = manager.search_bookmarks("python")
            assert len(results) == 1

    def test_bookmark_statistics(self):
        """Test bookmark statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BookmarksManager(str(Path(tmpdir) / "bookmarks.json"))
            manager.add_bookmark(
                title="Test",
                url="http://example.com",
                document_id="doc1",
                tags=["python", "ai"],
            )
            stats = manager.get_statistics()
            assert stats["total_bookmarks"] == 1
            assert stats["unique_tags"] == 2


# ============================================================================
# History Manager Tests
# ============================================================================


class TestHistoryEntry:
    """Test HistoryEntry"""

    def test_history_entry_creation(self):
        """Test history entry creation"""
        entry = HistoryEntry(
            id="1",
            query="test query",
            results_count=10,
        )
        assert entry.query == "test query"

    def test_history_entry_to_dict(self):
        """Test history entry to dict"""
        entry = HistoryEntry(
            id="1",
            query="test",
            results_count=5,
        )
        data = entry.to_dict()
        assert data["query"] == "test"


class TestHistoryManager:
    """Test HistoryManager"""

    def test_history_manager_creation(self):
        """Test history manager creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(str(Path(tmpdir) / "history.json"))
            assert len(manager.history) == 0

    def test_add_search(self):
        """Test add search"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(str(Path(tmpdir) / "history.json"))
            entry = manager.add_search("test query", 10)
            assert entry.query == "test query"
            assert len(manager.history) == 1

    def test_get_history(self):
        """Test get history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(str(Path(tmpdir) / "history.json"))
            manager.add_search("query1", 5)
            manager.add_search("query2", 10)
            history = manager.get_history()
            assert len(history) == 2

    def test_search_history(self):
        """Test search history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(str(Path(tmpdir) / "history.json"))
            manager.add_search("python tutorial", 5)
            manager.add_search("javascript guide", 10)
            results = manager.search_history("python")
            assert len(results) == 1

    def test_add_recent_item(self):
        """Test add recent item"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(str(Path(tmpdir) / "history.json"))
            item = manager.add_recent_item("Test Item", "doc1")
            assert item.title == "Test Item"
            assert len(manager.recent_items) == 1

    def test_history_statistics(self):
        """Test history statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager(str(Path(tmpdir) / "history.json"))
            manager.add_search("query1", 5)
            manager.add_search("query2", 10)
            stats = manager.get_statistics()
            assert stats["total_searches"] == 2
            assert stats["total_results"] == 15


# ============================================================================
# Batch Processor Tests
# ============================================================================


class TestBatchOperation:
    """Test BatchOperation"""

    def test_batch_operation_creation(self):
        """Test batch operation creation"""
        items = [{"id": 1, "query": "test"}]
        operation = BatchOperation(
            id="op1",
            type=BatchOperationType.SEARCH,
            items=items,
            parameters={},
        )
        assert operation.type == BatchOperationType.SEARCH


class TestBatchProcessor:
    """Test BatchProcessor"""

    def test_batch_processor_creation(self):
        """Test batch processor creation"""
        processor = BatchProcessor()
        assert len(processor.handlers) > 0

    def test_create_operation(self):
        """Test create operation"""
        processor = BatchProcessor()
        items = [{"id": 1, "query": "test"}]
        operation = processor.create_operation(
            BatchOperationType.SEARCH,
            items,
        )
        assert operation.type == BatchOperationType.SEARCH

    def test_execute_search_operation(self):
        """Test execute search operation"""
        processor = BatchProcessor()
        items = [{"id": 1, "query": "test"}]
        operation = processor.create_operation(
            BatchOperationType.SEARCH,
            items,
        )
        result = processor.execute(operation.id)
        assert result.success
        assert result.total_items == 1

    def test_execute_export_operation(self):
        """Test execute export operation"""
        processor = BatchProcessor()
        items = [{"id": 1, "title": "Test"}]
        operation = processor.create_operation(
            BatchOperationType.EXPORT,
            items,
            {"format": "json"},
        )
        result = processor.execute(operation.id)
        assert result.success

    def test_list_operations(self):
        """Test list operations"""
        processor = BatchProcessor()
        items = [{"id": 1}]
        processor.create_operation(BatchOperationType.SEARCH, items)
        processor.create_operation(BatchOperationType.EXPORT, items)
        operations = processor.list_operations()
        assert len(operations) == 2

    def test_cancel_operation(self):
        """Test cancel operation"""
        processor = BatchProcessor()
        items = [{"id": 1}]
        operation = processor.create_operation(
            BatchOperationType.SEARCH,
            items,
        )
        operation.status = "running"
        cancelled = processor.cancel_operation(operation.id)
        assert cancelled is True


class TestBatchConvenience:
    """Test batch convenience functions"""

    def test_batch_search_function(self):
        """Test batch search function"""
        queries = ["query1", "query2"]
        result = batch_search(queries, lambda x: x)
        assert result.total_items == 2

    def test_batch_export_function(self):
        """Test batch export function"""
        items = [{"id": 1, "title": "Item 1"}]
        result = batch_export(items, "json")
        assert result.success


# ============================================================================
# Integration Tests
# ============================================================================


class TestAdvancedIntegration:
    """Integration tests for advanced features"""

    def test_filter_sort_export_flow(self):
        """Test filter, sort, and export flow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create items
            items = [
                {"id": 1, "title": "Item 1", "relevance": 0.9, "source": "source1"},
                {"id": 2, "title": "Item 2", "relevance": 0.5, "source": "source2"},
                {"id": 3, "title": "Item 3", "relevance": 0.3, "source": "source1"},
            ]

            # Filter and sort
            filter_engine = FilterSortEngine()
            filter_criteria = FilterCriteria(sources=["source1"])
            sort_criteria = SortCriteria(field=SortField.RELEVANCE)
            filtered_items, stats = filter_engine.process(
                items, filter_criteria, sort_criteria
            )

            # Export
            manager = ExportManager()
            output_path = str(Path(tmpdir) / "export.json")
            config = ExportConfig(
                format=ExportFormat.JSON,
                output_path=output_path,
            )
            result = manager.export(filtered_items, config)
            assert result.success
            assert result.items_exported == 2

    def test_bookmarks_and_history_flow(self):
        """Test bookmarks and history flow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create managers
            bookmarks = BookmarksManager(str(Path(tmpdir) / "bookmarks.json"))
            history = HistoryManager(str(Path(tmpdir) / "history.json"))

            # Add bookmark
            bookmark = bookmarks.add_bookmark(
                title="Test",
                url="http://example.com",
                document_id="doc1",
            )

            # Add search history
            history.add_search("test query", 1)

            # Add recent item
            history.add_recent_item("Test Item", "doc1")

            # Verify
            assert len(bookmarks.bookmarks) == 1
            assert len(history.history) == 1
            assert len(history.recent_items) == 1
