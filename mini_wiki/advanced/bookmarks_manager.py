"""
Bookmarks Manager Module
Manage bookmarks and favorites

Features:
- Add/remove bookmarks
- List bookmarks
- Search bookmarks
- Bookmark collections
- Export/import bookmarks
- Bookmark statistics
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Bookmark:
    """Bookmark entry

    Attributes:
        id: Unique bookmark ID
        title: Bookmark title
        url: Bookmark URL
        document_id: Associated document ID
        tags: Bookmark tags
        notes: User notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str
    title: str
    url: str
    document_id: str
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "document_id": self.document_id,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bookmark":
        """Create from dictionary

        Args:
            data: Dictionary data

        Returns:
            Bookmark instance
        """
        return cls(**data)


@dataclass
class BookmarkCollection:
    """Bookmark collection

    Attributes:
        name: Collection name
        description: Collection description
        bookmarks: List of bookmarks
        created_at: Creation timestamp
    """

    name: str
    description: str = ""
    bookmarks: List[Bookmark] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_bookmark(self, bookmark: Bookmark) -> None:
        """Add bookmark to collection

        Args:
            bookmark: Bookmark to add
        """
        if not any(b.id == bookmark.id for b in self.bookmarks):
            self.bookmarks.append(bookmark)

    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove bookmark from collection

        Args:
            bookmark_id: Bookmark ID

        Returns:
            True if removed, False if not found
        """
        original_count = len(self.bookmarks)
        self.bookmarks = [b for b in self.bookmarks if b.id != bookmark_id]
        return len(self.bookmarks) < original_count

    def get_bookmark(self, bookmark_id: str) -> Optional[Bookmark]:
        """Get bookmark by ID

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Bookmark or None
        """
        for bookmark in self.bookmarks:
            if bookmark.id == bookmark_id:
                return bookmark
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "bookmarks": [b.to_dict() for b in self.bookmarks],
            "created_at": self.created_at,
        }


class BookmarksManager:
    """Manage bookmarks"""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize bookmarks manager

        Args:
            storage_path: Path to store bookmarks
        """
        self.storage_path = Path(storage_path) if storage_path else Path.home() / ".mini_wiki" / "bookmarks.json"
        self.bookmarks: Dict[str, Bookmark] = {}
        self.collections: Dict[str, BookmarkCollection] = {}
        self._load()

    def add_bookmark(
        self,
        title: str,
        url: str,
        document_id: str,
        tags: Optional[List[str]] = None,
        notes: str = "",
    ) -> Bookmark:
        """Add bookmark

        Args:
            title: Bookmark title
            url: Bookmark URL
            document_id: Associated document ID
            tags: Bookmark tags
            notes: User notes

        Returns:
            Created bookmark
        """
        bookmark_id = self._generate_id()
        bookmark = Bookmark(
            id=bookmark_id,
            title=title,
            url=url,
            document_id=document_id,
            tags=tags or [],
            notes=notes,
        )
        self.bookmarks[bookmark_id] = bookmark
        self._save()
        logger.info(f"Added bookmark: {title}")
        return bookmark

    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove bookmark

        Args:
            bookmark_id: Bookmark ID

        Returns:
            True if removed, False if not found
        """
        if bookmark_id in self.bookmarks:
            del self.bookmarks[bookmark_id]
            self._save()
            logger.info(f"Removed bookmark: {bookmark_id}")
            return True
        return False

    def get_bookmark(self, bookmark_id: str) -> Optional[Bookmark]:
        """Get bookmark by ID

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Bookmark or None
        """
        return self.bookmarks.get(bookmark_id)

    def list_bookmarks(self) -> List[Bookmark]:
        """List all bookmarks

        Returns:
            List of bookmarks
        """
        return list(self.bookmarks.values())

    def search_bookmarks(self, query: str) -> List[Bookmark]:
        """Search bookmarks

        Args:
            query: Search query

        Returns:
            List of matching bookmarks
        """
        query_lower = query.lower()
        return [
            b
            for b in self.bookmarks.values()
            if query_lower in b.title.lower()
            or query_lower in b.notes.lower()
            or any(query_lower in tag.lower() for tag in b.tags)
        ]

    def get_bookmarks_by_tag(self, tag: str) -> List[Bookmark]:
        """Get bookmarks by tag

        Args:
            tag: Tag name

        Returns:
            List of bookmarks with tag
        """
        return [b for b in self.bookmarks.values() if tag in b.tags]

    def get_bookmarks_by_document(self, document_id: str) -> List[Bookmark]:
        """Get bookmarks by document

        Args:
            document_id: Document ID

        Returns:
            List of bookmarks for document
        """
        return [b for b in self.bookmarks.values() if b.document_id == document_id]

    def update_bookmark(
        self,
        bookmark_id: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Bookmark]:
        """Update bookmark

        Args:
            bookmark_id: Bookmark ID
            title: New title
            notes: New notes
            tags: New tags

        Returns:
            Updated bookmark or None
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if not bookmark:
            return None

        if title:
            bookmark.title = title
        if notes is not None:
            bookmark.notes = notes
        if tags is not None:
            bookmark.tags = tags

        bookmark.updated_at = datetime.now().isoformat()
        self._save()
        logger.info(f"Updated bookmark: {bookmark_id}")
        return bookmark

    def create_collection(self, name: str, description: str = "") -> BookmarkCollection:
        """Create bookmark collection

        Args:
            name: Collection name
            description: Collection description

        Returns:
            Created collection
        """
        collection = BookmarkCollection(name=name, description=description)
        self.collections[name] = collection
        self._save()
        logger.info(f"Created collection: {name}")
        return collection

    def add_to_collection(self, collection_name: str, bookmark_id: str) -> bool:
        """Add bookmark to collection

        Args:
            collection_name: Collection name
            bookmark_id: Bookmark ID

        Returns:
            True if added, False if not found
        """
        collection = self.collections.get(collection_name)
        bookmark = self.bookmarks.get(bookmark_id)

        if not collection or not bookmark:
            return False

        collection.add_bookmark(bookmark)
        self._save()
        logger.info(f"Added bookmark to collection: {collection_name}")
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get bookmark statistics

        Returns:
            Statistics dictionary
        """
        all_tags = set()
        for bookmark in self.bookmarks.values():
            all_tags.update(bookmark.tags)

        return {
            "total_bookmarks": len(self.bookmarks),
            "total_collections": len(self.collections),
            "unique_tags": len(all_tags),
            "tags": list(all_tags),
        }

    def export(self, output_path: str) -> bool:
        """Export bookmarks to JSON

        Args:
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            data = {
                "bookmarks": [b.to_dict() for b in self.bookmarks.values()],
                "collections": [c.to_dict() for c in self.collections.values()],
                "exported_at": datetime.now().isoformat(),
            }
            Path(output_path).write_text(json.dumps(data, indent=2))
            logger.info(f"Exported bookmarks to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def import_bookmarks(self, input_path: str) -> bool:
        """Import bookmarks from JSON

        Args:
            input_path: Input file path

        Returns:
            True if successful
        """
        try:
            data = json.loads(Path(input_path).read_text())
            for bookmark_data in data.get("bookmarks", []):
                bookmark = Bookmark.from_dict(bookmark_data)
                self.bookmarks[bookmark.id] = bookmark
            self._save()
            logger.info(f"Imported bookmarks from: {input_path}")
            return True
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False

    def _generate_id(self) -> str:
        """Generate unique bookmark ID

        Returns:
            Unique ID
        """
        import uuid

        return str(uuid.uuid4())[:8]

    def _load(self) -> None:
        """Load bookmarks from storage"""
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                for bookmark_data in data.get("bookmarks", []):
                    bookmark = Bookmark.from_dict(bookmark_data)
                    self.bookmarks[bookmark.id] = bookmark
                logger.info(f"Loaded {len(self.bookmarks)} bookmarks")
        except Exception as e:
            logger.warning(f"Failed to load bookmarks: {e}")

    def _save(self) -> None:
        """Save bookmarks to storage"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "bookmarks": [b.to_dict() for b in self.bookmarks.values()],
                "collections": [c.to_dict() for c in self.collections.values()],
                "saved_at": datetime.now().isoformat(),
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save bookmarks: {e}")
