"""
Advanced Features Package
Advanced filtering, sorting, export, bookmarks, history, and batch operations

Modules:
- filter_engine: Advanced filtering and sorting
- export_manager: Export to multiple formats
- bookmarks_manager: Manage bookmarks and favorites
- history_manager: Search history and recent items
- batch_processor: Batch operations
"""

from mini_wiki.advanced.batch_processor import (
    BatchOperation,
    BatchOperationType,
    BatchProcessor,
    BatchResult,
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
    ExportResult,
    export_to_csv,
    export_to_json,
    export_to_markdown,
)
from mini_wiki.advanced.filter_engine import (
    FilterCriteria,
    FilterEngine,
    FilterResult,
    FilterSortEngine,
    SortCriteria,
    SortEngine,
    SortField,
    SortOrder,
)
from mini_wiki.advanced.history_manager import (
    HistoryEntry,
    HistoryManager,
    RecentItem,
)

__all__ = [
    # Filter Engine
    "FilterCriteria",
    "FilterEngine",
    "FilterResult",
    "SortCriteria",
    "SortEngine",
    "SortField",
    "SortOrder",
    "FilterSortEngine",
    # Export Manager
    "ExportConfig",
    "ExportFormat",
    "ExportManager",
    "ExportResult",
    "export_to_json",
    "export_to_markdown",
    "export_to_csv",
    # Bookmarks Manager
    "Bookmark",
    "BookmarkCollection",
    "BookmarksManager",
    # History Manager
    "HistoryEntry",
    "HistoryManager",
    "RecentItem",
    # Batch Processor
    "BatchOperation",
    "BatchOperationType",
    "BatchProcessor",
    "BatchResult",
    "batch_search",
    "batch_export",
]
