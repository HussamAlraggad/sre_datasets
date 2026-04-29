"""
History Manager Module
Manage search history and recent items

Features:
- Record search queries
- Track recent documents
- Search history with timestamps
- Clear history
- Export/import history
- History statistics
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """History entry

    Attributes:
        id: Unique entry ID
        query: Search query
        results_count: Number of results
        timestamp: Search timestamp
        duration_ms: Search duration in milliseconds
    """

    id: str
    query: str
    results_count: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "query": self.query,
            "results_count": self.results_count,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create from dictionary

        Args:
            data: Dictionary data

        Returns:
            HistoryEntry instance
        """
        return cls(**data)


@dataclass
class RecentItem:
    """Recent item entry

    Attributes:
        id: Unique item ID
        title: Item title
        document_id: Document ID
        accessed_at: Last access timestamp
        access_count: Number of accesses
    """

    id: str
    title: str
    document_id: str
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "title": self.title,
            "document_id": self.document_id,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecentItem":
        """Create from dictionary

        Args:
            data: Dictionary data

        Returns:
            RecentItem instance
        """
        return cls(**data)


class HistoryManager:
    """Manage search history"""

    def __init__(self, storage_path: Optional[str] = None, max_history: int = 1000):
        """Initialize history manager

        Args:
            storage_path: Path to store history
            max_history: Maximum history entries to keep
        """
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else Path.home() / ".mini_wiki" / "history.json"
        )
        self.max_history = max_history
        self.history: List[HistoryEntry] = []
        self.recent_items: Dict[str, RecentItem] = {}
        self._load()

    def add_search(
        self, query: str, results_count: int, duration_ms: float = 0.0
    ) -> HistoryEntry:
        """Add search to history

        Args:
            query: Search query
            results_count: Number of results
            duration_ms: Search duration

        Returns:
            Created history entry
        """
        entry_id = self._generate_id()
        entry = HistoryEntry(
            id=entry_id,
            query=query,
            results_count=results_count,
            duration_ms=duration_ms,
        )
        self.history.insert(0, entry)

        # Keep only max_history entries
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]

        self._save()
        logger.info(f"Added search to history: {query}")
        return entry

    def get_history(self, limit: int = 50) -> List[HistoryEntry]:
        """Get search history

        Args:
            limit: Maximum entries to return

        Returns:
            List of history entries
        """
        return self.history[:limit]

    def search_history(self, query: str) -> List[HistoryEntry]:
        """Search history

        Args:
            query: Search query

        Returns:
            List of matching history entries
        """
        query_lower = query.lower()
        return [h for h in self.history if query_lower in h.query.lower()]

    def clear_history(self) -> None:
        """Clear all history"""
        self.history = []
        self._save()
        logger.info("Cleared search history")

    def remove_entry(self, entry_id: str) -> bool:
        """Remove history entry

        Args:
            entry_id: Entry ID

        Returns:
            True if removed, False if not found
        """
        original_count = len(self.history)
        self.history = [h for h in self.history if h.id != entry_id]
        if len(self.history) < original_count:
            self._save()
            return True
        return False

    def add_recent_item(self, title: str, document_id: str) -> RecentItem:
        """Add recent item

        Args:
            title: Item title
            document_id: Document ID

        Returns:
            Created or updated recent item
        """
        # Check if already exists
        for item in self.recent_items.values():
            if item.document_id == document_id:
                item.accessed_at = datetime.now().isoformat()
                item.access_count += 1
                self._save()
                return item

        # Create new
        item_id = self._generate_id()
        item = RecentItem(
            id=item_id,
            title=title,
            document_id=document_id,
        )
        self.recent_items[item_id] = item
        self._save()
        logger.info(f"Added recent item: {title}")
        return item

    def get_recent_items(self, limit: int = 20) -> List[RecentItem]:
        """Get recent items

        Args:
            limit: Maximum items to return

        Returns:
            List of recent items sorted by access time
        """
        sorted_items = sorted(
            self.recent_items.values(),
            key=lambda x: x.accessed_at,
            reverse=True,
        )
        return sorted_items[:limit]

    def clear_recent_items(self) -> None:
        """Clear recent items"""
        self.recent_items = {}
        self._save()
        logger.info("Cleared recent items")

    def get_statistics(self) -> Dict[str, Any]:
        """Get history statistics

        Returns:
            Statistics dictionary
        """
        if not self.history:
            return {
                "total_searches": 0,
                "unique_queries": 0,
                "total_results": 0,
                "average_results": 0.0,
                "total_recent_items": len(self.recent_items),
            }

        unique_queries = len(set(h.query for h in self.history))
        total_results = sum(h.results_count for h in self.history)
        average_results = total_results / len(self.history) if self.history else 0.0

        return {
            "total_searches": len(self.history),
            "unique_queries": unique_queries,
            "total_results": total_results,
            "average_results": average_results,
            "total_recent_items": len(self.recent_items),
        }

    def export(self, output_path: str) -> bool:
        """Export history to JSON

        Args:
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            data = {
                "history": [h.to_dict() for h in self.history],
                "recent_items": [i.to_dict() for i in self.recent_items.values()],
                "exported_at": datetime.now().isoformat(),
            }
            Path(output_path).write_text(json.dumps(data, indent=2))
            logger.info(f"Exported history to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def import_history(self, input_path: str) -> bool:
        """Import history from JSON

        Args:
            input_path: Input file path

        Returns:
            True if successful
        """
        try:
            data = json.loads(Path(input_path).read_text())
            for entry_data in data.get("history", []):
                entry = HistoryEntry.from_dict(entry_data)
                self.history.append(entry)
            for item_data in data.get("recent_items", []):
                item = RecentItem.from_dict(item_data)
                self.recent_items[item.id] = item
            self._save()
            logger.info(f"Imported history from: {input_path}")
            return True
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False

    def _generate_id(self) -> str:
        """Generate unique ID

        Returns:
            Unique ID
        """
        import uuid

        return str(uuid.uuid4())[:8]

    def _load(self) -> None:
        """Load history from storage"""
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                for entry_data in data.get("history", []):
                    entry = HistoryEntry.from_dict(entry_data)
                    self.history.append(entry)
                for item_data in data.get("recent_items", []):
                    item = RecentItem.from_dict(item_data)
                    self.recent_items[item.id] = item
                logger.info(
                    f"Loaded {len(self.history)} history entries and "
                    f"{len(self.recent_items)} recent items"
                )
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")

    def _save(self) -> None:
        """Save history to storage"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "history": [h.to_dict() for h in self.history],
                "recent_items": [i.to_dict() for i in self.recent_items.values()],
                "saved_at": datetime.now().isoformat(),
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
