"""
Knowledge Base Module
Build and manage knowledge base from AI documentation

Features:
- Store and retrieve documentation entries
- Search knowledge base
- Tag-based organization
- Difficulty levels
- Version management
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from mini_wiki.ai_teaching.ai_documentation import DocumentationEntry

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Knowledge base for storing and managing documentation"""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize knowledge base

        Args:
            base_path: Base path for knowledge base storage
        """
        self.base_path = Path(base_path) if base_path else Path("knowledge_base")
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.entries_dir = self.base_path / "entries"
        self.index_file = self.base_path / "index.yaml"

        self.entries_dir.mkdir(exist_ok=True)

        # Load or create index
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Load knowledge base index

        Returns:
            Index dictionary
        """
        if self.index_file.exists():
            with open(self.index_file, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _save_index(self) -> None:
        """Save knowledge base index"""
        with open(self.index_file, "w") as f:
            yaml.dump(self.index, f, default_flow_style=False)

    def add_entry(
        self,
        topic: str,
        entry: DocumentationEntry,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> str:
        """Add entry to knowledge base

        Args:
            topic: Topic name
            entry: DocumentationEntry object
            tags: List of tags (optional)
            difficulty: Difficulty level (optional)

        Returns:
            Entry ID
        """
        # Generate entry ID
        entry_id = self._generate_entry_id(topic)

        # Save entry
        entry_path = self.entries_dir / f"{entry_id}.yaml"
        with open(entry_path, "w") as f:
            yaml.dump(entry.to_dict(), f, default_flow_style=False)

        # Update index
        self.index[entry_id] = {
            "topic": topic,
            "tags": tags or [],
            "difficulty": difficulty or "intermediate",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "path": str(entry_path),
        }

        self._save_index()

        logger.info(f"Added entry to knowledge base: {entry_id}")

        return entry_id

    def get_entry(self, entry_id: str) -> Optional[DocumentationEntry]:
        """Get entry from knowledge base

        Args:
            entry_id: Entry ID

        Returns:
            DocumentationEntry or None if not found
        """
        if entry_id not in self.index:
            return None

        entry_path = Path(self.index[entry_id]["path"])

        if not entry_path.exists():
            logger.warning(f"Entry file not found: {entry_path}")
            return None

        with open(entry_path, "r") as f:
            data = yaml.safe_load(f)

        return DocumentationEntry(
            topic=data.get("topic", ""),
            context=data.get("context", ""),
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            references=data.get("references", []),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
        )

    def search_by_topic(self, query: str) -> List[str]:
        """Search entries by topic

        Args:
            query: Search query

        Returns:
            List of matching entry IDs
        """
        query_lower = query.lower()
        results = []

        for entry_id, entry_info in self.index.items():
            topic = entry_info.get("topic", "").lower()
            if query_lower in topic:
                results.append(entry_id)

        return results

    def search_by_tag(self, tag: str) -> List[str]:
        """Search entries by tag

        Args:
            tag: Tag to search for

        Returns:
            List of matching entry IDs
        """
        results = []

        for entry_id, entry_info in self.index.items():
            tags = entry_info.get("tags", [])
            if tag in tags:
                results.append(entry_id)

        return results

    def search_by_difficulty(self, difficulty: str) -> List[str]:
        """Search entries by difficulty level

        Args:
            difficulty: Difficulty level

        Returns:
            List of matching entry IDs
        """
        results = []

        for entry_id, entry_info in self.index.items():
            if entry_info.get("difficulty") == difficulty:
                results.append(entry_id)

        return results

    def list_entries(
        self,
        tag: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """List knowledge base entries

        Args:
            tag: Filter by tag (optional)
            difficulty: Filter by difficulty (optional)
            limit: Maximum number of entries (optional)

        Returns:
            List of entry information dictionaries
        """
        entries = []

        for entry_id, entry_info in self.index.items():
            # Filter by tag
            if tag and tag not in entry_info.get("tags", []):
                continue

            # Filter by difficulty
            if difficulty and entry_info.get("difficulty") != difficulty:
                continue

            entries.append({
                "entry_id": entry_id,
                "topic": entry_info.get("topic"),
                "tags": entry_info.get("tags", []),
                "difficulty": entry_info.get("difficulty"),
                "created_at": entry_info.get("created_at"),
            })

        # Sort by creation date (newest first)
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Limit results
        if limit:
            entries = entries[:limit]

        return entries

    def update_entry(
        self,
        entry_id: str,
        entry: DocumentationEntry,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> bool:
        """Update entry in knowledge base

        Args:
            entry_id: Entry ID
            entry: Updated DocumentationEntry object
            tags: Updated tags (optional)
            difficulty: Updated difficulty (optional)

        Returns:
            True if successful, False if entry not found
        """
        if entry_id not in self.index:
            return False

        # Update entry file
        entry_path = Path(self.index[entry_id]["path"])
        with open(entry_path, "w") as f:
            yaml.dump(entry.to_dict(), f, default_flow_style=False)

        # Update index
        if tags is not None:
            self.index[entry_id]["tags"] = tags

        if difficulty is not None:
            self.index[entry_id]["difficulty"] = difficulty

        self.index[entry_id]["updated_at"] = datetime.now().isoformat()

        self._save_index()

        logger.info(f"Updated entry in knowledge base: {entry_id}")

        return True

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry from knowledge base

        Args:
            entry_id: Entry ID

        Returns:
            True if successful, False if entry not found
        """
        if entry_id not in self.index:
            return False

        # Delete entry file
        entry_path = Path(self.index[entry_id]["path"])
        if entry_path.exists():
            entry_path.unlink()

        # Remove from index
        del self.index[entry_id]

        self._save_index()

        logger.info(f"Deleted entry from knowledge base: {entry_id}")

        return True

    def get_stats(self) -> Dict:
        """Get knowledge base statistics

        Returns:
            Statistics dictionary
        """
        total_entries = len(self.index)

        # Count by difficulty
        difficulty_counts = {}
        for entry_info in self.index.values():
            difficulty = entry_info.get("difficulty", "unknown")
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

        # Count by tag
        tag_counts = {}
        for entry_info in self.index.values():
            for tag in entry_info.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_entries": total_entries,
            "difficulty_counts": difficulty_counts,
            "tag_counts": tag_counts,
            "base_path": str(self.base_path),
        }

    def export_to_json(self, filepath: str) -> None:
        """Export knowledge base to JSON

        Args:
            filepath: Path to export file
        """
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "entries": [],
        }

        for entry_id in self.index.keys():
            entry = self.get_entry(entry_id)
            if entry:
                export_data["entries"].append({
                    "entry_id": entry_id,
                    "data": entry.to_dict(),
                })

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported knowledge base to {filepath}")

    def import_from_json(self, filepath: str) -> int:
        """Import knowledge base from JSON

        Args:
            filepath: Path to import file

        Returns:
            Number of entries imported
        """
        with open(filepath, "r") as f:
            import_data = json.load(f)

        count = 0
        for item in import_data.get("entries", []):
            entry_id = item.get("entry_id")
            data = item.get("data", {})

            entry = DocumentationEntry(
                topic=data.get("topic", ""),
                context=data.get("context", ""),
                summary=data.get("summary", ""),
                key_points=data.get("key_points", []),
                references=data.get("references", []),
                metadata=data.get("metadata"),
                created_at=data.get("created_at"),
            )

            # Save entry
            entry_path = self.entries_dir / f"{entry_id}.yaml"
            with open(entry_path, "w") as f:
                yaml.dump(entry.to_dict(), f, default_flow_style=False)

            # Add to index
            self.index[entry_id] = {
                "topic": data.get("topic", ""),
                "tags": data.get("metadata", {}).get("tags", []),
                "difficulty": data.get("metadata", {}).get("difficulty", "intermediate"),
                "created_at": data.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "path": str(entry_path),
            }

            count += 1

        self._save_index()

        logger.info(f"Imported {count} entries from {filepath}")

        return count

    def _generate_entry_id(self, topic: str) -> str:
        """Generate unique entry ID from topic

        Args:
            topic: Topic name

        Returns:
            Entry ID
        """
        # Convert topic to ID format
        entry_id = topic.lower().replace(" ", "_")
        entry_id = "".join(c for c in entry_id if c.isalnum() or c == "_")

        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        entry_id = f"{entry_id}_{timestamp}"

        return entry_id
