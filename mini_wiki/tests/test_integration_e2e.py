"""
End-to-End Integration Tests
Test complete workflows across all phases

Test coverage:
- Data loading (Phase 1)
- Search and ranking (Phase 2)
- Context generation (Phase 3)
- TUI interface (Phase 4)
- Advanced features (Phase 5)
- Integrated system (Phase 6)
"""

import tempfile
from pathlib import Path

import pytest

from mini_wiki.integrated_system import (
    MiniWikiIntegratedSystem,
    SystemConfig,
    create_system,
)


class TestIntegratedSystemCreation:
    """Test integrated system creation"""

    def test_create_system_default(self):
        """Test create system with defaults"""
        system = create_system()
        assert system is not None
        assert system.config.theme == "dark"

    def test_create_system_custom_config(self):
        """Test create system with custom config"""
        config = SystemConfig(
            data_path="/tmp/data",
            theme="light",
            max_results=50,
        )
        system = create_system(config)
        assert system.config.theme == "light"
        assert system.config.max_results == 50

    def test_system_initialization(self):
        """Test system initialization"""
        system = create_system()
        assert system.datasets is not None
        assert system.stats is not None
        assert system.cache is not None


class TestDataLoading:
    """Test data loading (Phase 1)"""

    def test_load_data_csv(self):
        """Test load CSV data"""
        system = create_system()
        result = system.load_data("test.csv", "csv")
        assert result is True
        assert "test.csv" in system.datasets

    def test_load_data_json(self):
        """Test load JSON data"""
        system = create_system()
        result = system.load_data("test.json", "json")
        assert result is True

    def test_load_data_multiple(self):
        """Test load multiple data sources"""
        system = create_system()
        system.load_data("data1.csv", "csv")
        system.load_data("data2.json", "json")
        assert len(system.datasets) == 2


class TestSearchAndRanking:
    """Test search and ranking (Phase 2)"""

    def test_basic_search(self):
        """Test basic search"""
        system = create_system()
        results = system.search("machine learning")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_with_limit(self):
        """Test search with result limit"""
        system = create_system()
        results = system.search("python", limit=5)
        assert len(results) <= 5

    def test_search_results_ranked(self):
        """Test search results are ranked"""
        system = create_system()
        results = system.search("test")
        if len(results) > 1:
            # Results should be sorted by relevance
            relevances = [r.get("relevance", 0) for r in results]
            assert relevances == sorted(relevances, reverse=True)

    def test_search_includes_context(self):
        """Test search results include context"""
        system = create_system()
        results = system.search("test")
        if results:
            assert "context" in results[0]


class TestExport:
    """Test export functionality (Phase 5)"""

    def test_export_json(self):
        """Test export to JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = create_system()
            results = system.search("test")
            output_path = str(Path(tmpdir) / "results.json")
            success = system.export_results(results, "json", output_path)
            assert success is True
            assert Path(output_path).exists()

    def test_export_markdown(self):
        """Test export to Markdown"""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = create_system()
            results = system.search("test")
            output_path = str(Path(tmpdir) / "results.md")
            success = system.export_results(results, "markdown", output_path)
            assert success is True
            assert Path(output_path).exists()

    def test_batch_export(self):
        """Test batch export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = create_system()
            items = [{"id": 1, "title": "Item 1"}]
            output_path = str(Path(tmpdir) / "batch.json")
            success = system.batch_export(items, "json", output_path)
            assert success is True


class TestBookmarks:
    """Test bookmarks (Phase 5)"""

    def test_add_bookmark(self):
        """Test add bookmark"""
        system = create_system()
        success = system.add_bookmark(
            title="Test",
            url="http://example.com",
            document_id="doc1",
        )
        assert success is True
        assert system.stats.bookmarks_count == 1

    def test_add_multiple_bookmarks(self):
        """Test add multiple bookmarks"""
        system = create_system()
        system.add_bookmark("Test 1", "http://example.com/1", "doc1")
        system.add_bookmark("Test 2", "http://example.com/2", "doc2")
        assert system.stats.bookmarks_count == 2

    def test_get_bookmarks(self):
        """Test get bookmarks"""
        system = create_system()
        system.add_bookmark("Test", "http://example.com", "doc1")
        bookmarks = system.get_bookmarks()
        assert isinstance(bookmarks, list)


class TestHistory:
    """Test history tracking (Phase 5)"""

    def test_search_history(self):
        """Test search history"""
        system = create_system()
        system.search("query1")
        system.search("query2")
        history = system.get_search_history()
        assert isinstance(history, list)

    def test_recent_items(self):
        """Test recent items"""
        system = create_system()
        system.search("test")
        recent = system.get_recent_items()
        assert isinstance(recent, list)


class TestStatistics:
    """Test system statistics"""

    def test_get_statistics(self):
        """Test get statistics"""
        system = create_system()
        system.load_data("test.csv", "csv")
        system.search("test")
        system.add_bookmark("Test", "http://example.com", "doc1")

        stats = system.get_statistics()
        assert stats["total_searches"] >= 1
        assert stats["bookmarks_count"] >= 1

    def test_statistics_structure(self):
        """Test statistics structure"""
        system = create_system()
        stats = system.get_statistics()
        assert "total_documents" in stats
        assert "total_searches" in stats
        assert "bookmarks_count" in stats


class TestPerformance:
    """Test performance optimization"""

    def test_optimize_performance(self):
        """Test optimize performance"""
        system = create_system()
        success = system.optimize_performance()
        assert success is True

    def test_cache_clearing(self):
        """Test cache clearing"""
        system = create_system()
        system.cache["test"] = "value"
        system.optimize_performance()
        assert len(system.cache) == 0


class TestHealthCheck:
    """Test health check"""

    def test_health_check(self):
        """Test health check"""
        system = create_system()
        health = system.health_check()
        assert health["status"] == "healthy"
        assert "components" in health

    def test_health_check_components(self):
        """Test health check components"""
        system = create_system()
        health = system.health_check()
        components = health["components"]
        assert "phase1_core" in components
        assert "phase2_ranking" in components
        assert "phase3_ai_teaching" in components
        assert "phase4_tui" in components
        assert "phase5_advanced" in components


class TestSystemShutdown:
    """Test system shutdown"""

    def test_shutdown(self):
        """Test shutdown"""
        system = create_system()
        system.shutdown()
        # System should be shut down gracefully


class TestCompleteWorkflow:
    """Test complete workflow across all phases"""

    def test_load_search_export_workflow(self):
        """Test load, search, export workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = create_system()

            # Phase 1: Load data
            system.load_data("test.csv", "csv")

            # Phase 2: Search
            results = system.search("machine learning", limit=5)
            assert len(results) > 0

            # Phase 5: Export
            output_path = str(Path(tmpdir) / "results.json")
            success = system.export_results(results, "json", output_path)
            assert success is True

    def test_search_bookmark_history_workflow(self):
        """Test search, bookmark, history workflow"""
        system = create_system()

        # Phase 2: Search
        results = system.search("python")

        # Phase 5: Bookmark
        if results:
            system.add_bookmark(
                title=results[0].get("title"),
                url="http://example.com",
                document_id=results[0].get("id"),
            )

        # Phase 5: Check history
        history = system.get_search_history()
        assert len(history) > 0

        # Check bookmarks
        bookmarks = system.get_bookmarks()
        assert isinstance(bookmarks, list)

    def test_full_system_workflow(self):
        """Test full system workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(
                data_path=str(Path(tmpdir) / "data"),
                storage_path=str(Path(tmpdir) / "storage"),
            )
            system = create_system(config)

            # Load data
            system.load_data("data1.csv", "csv")
            system.load_data("data2.json", "json")

            # Search
            results = system.search("test", limit=10)

            # Bookmark
            if results:
                system.add_bookmark(
                    title="Test",
                    url="http://example.com",
                    document_id="doc1",
                    tags=["test"],
                )

            # Export
            output_path = str(Path(tmpdir) / "export.json")
            system.export_results(results, "json", output_path)

            # Get statistics
            stats = system.get_statistics()
            assert stats["total_searches"] >= 1

            # Health check
            health = system.health_check()
            assert health["status"] == "healthy"

            # Optimize
            system.optimize_performance()

            # Shutdown
            system.shutdown()


class TestErrorHandling:
    """Test error handling"""

    def test_search_error_handling(self):
        """Test search error handling"""
        system = create_system()
        results = system.search("")
        assert isinstance(results, list)

    def test_export_error_handling(self):
        """Test export error handling"""
        system = create_system()
        success = system.export_results([], "json", "/invalid/path/file.json")
        assert success is False

    def test_bookmark_error_handling(self):
        """Test bookmark error handling"""
        system = create_system()
        success = system.add_bookmark("", "", "")
        assert success is True  # Should handle gracefully


class TestSystemConfiguration:
    """Test system configuration"""

    def test_custom_configuration(self):
        """Test custom configuration"""
        config = SystemConfig(
            data_path="/custom/data",
            index_path="/custom/index",
            storage_path="/custom/storage",
            theme="light",
            max_results=50,
            enable_caching=False,
            enable_logging=True,
        )
        system = create_system(config)
        assert system.config.data_path == "/custom/data"
        assert system.config.theme == "light"
        assert system.config.max_results == 50

    def test_system_to_dict(self):
        """Test system to dict"""
        system = create_system()
        system_dict = system.to_dict()
        assert "config" in system_dict
        assert "stats" in system_dict
