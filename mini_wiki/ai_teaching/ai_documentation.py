"""
AI Documentation Module
Generates AI-readable documentation from contexts and references

Features:
- Generate structured documentation for AI models
- Create knowledge base entries
- Format documentation in YAML/JSON
- Include context, references, and metadata
- Support multiple documentation formats
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from mini_wiki.ai_teaching.context_generator import ContextGenerator
from mini_wiki.ai_teaching.reference_extractor import Reference, ReferenceExtractor

logger = logging.getLogger(__name__)


@dataclass
class DocumentationEntry:
    """AI documentation entry

    Attributes:
        topic: Topic or query
        context: Main context/content
        summary: Brief summary
        key_points: List of key points
        references: List of references
        metadata: Additional metadata
        created_at: Creation timestamp
    """

    topic: str
    context: str
    summary: str
    key_points: List[str]
    references: List[Dict]
    metadata: Optional[Dict] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "topic": self.topic,
            "context": self.context,
            "summary": self.summary,
            "key_points": self.key_points,
            "references": self.references,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    def to_yaml(self) -> str:
        """Convert to YAML format

        Returns:
            YAML formatted string
        """
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        """Convert to JSON format

        Returns:
            JSON formatted string
        """
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        """Convert to Markdown format

        Returns:
            Markdown formatted string
        """
        lines = [f"# {self.topic}\n"]

        # Summary
        if self.summary:
            lines.append("## Summary\n")
            lines.append(f"{self.summary}\n")

        # Context
        if self.context:
            lines.append("## Context\n")
            lines.append(f"{self.context}\n")

        # Key Points
        if self.key_points:
            lines.append("## Key Points\n")
            for point in self.key_points:
                lines.append(f"- {point}")
            lines.append("")

        # References
        if self.references:
            lines.append("## References\n")
            for i, ref in enumerate(self.references, 1):
                lines.append(f"{i}. {ref.get('title', 'Unknown')}")
                if ref.get('url'):
                    lines.append(f"   URL: {ref['url']}")
            lines.append("")

        # Metadata
        if self.metadata:
            lines.append("## Metadata\n")
            for key, value in self.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        return "\n".join(lines)


class AIDocumentationGenerator:
    """Generate AI-readable documentation"""

    def __init__(self):
        """Initialize documentation generator"""
        self.context_generator = ContextGenerator()
        self.reference_extractor = ReferenceExtractor()

    def generate_documentation(
        self,
        topic: str,
        contexts: List[Dict],
        references: Optional[List[Reference]] = None,
        key_points: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> DocumentationEntry:
        """Generate documentation entry

        Args:
            topic: Topic or query
            contexts: List of context dictionaries
            references: List of Reference objects (optional)
            key_points: List of key points (optional)
            metadata: Additional metadata (optional)

        Returns:
            DocumentationEntry object
        """
        # Combine contexts
        combined = self.context_generator.combine_contexts(contexts)
        context = combined["combined_context"]
        summary = combined["combined_summary"]

        # Format references
        if references is None:
            references = []

        reference_dicts = [ref.to_dict() for ref in references]

        # Extract key points if not provided
        if key_points is None:
            key_points = self._extract_key_points(context)

        # Add metadata
        if metadata is None:
            metadata = {}

        metadata.update({
            "num_source_documents": combined["metadata"].get("num_source_documents", 0),
            "source_documents": combined["metadata"].get("source_documents", []),
            "context_length": combined["metadata"].get("combined_length", 0),
        })

        # Create entry
        entry = DocumentationEntry(
            topic=topic,
            context=context,
            summary=summary,
            key_points=key_points,
            references=reference_dicts,
            metadata=metadata,
            created_at=datetime.now().isoformat(),
        )

        logger.info(f"Generated documentation for topic: {topic}")

        return entry

    def _extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from text

        Args:
            text: Input text
            num_points: Number of key points to extract

        Returns:
            List of key points
        """
        if not text:
            return []

        # Simple extraction: split by sentences and take first few
        sentences = text.split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        # Take first num_points sentences as key points
        key_points = sentences[:num_points]

        return key_points

    def generate_batch_documentation(
        self,
        topics: List[str],
        contexts_list: List[List[Dict]],
        references_list: Optional[List[List[Reference]]] = None,
    ) -> List[DocumentationEntry]:
        """Generate documentation for multiple topics

        Args:
            topics: List of topics
            contexts_list: List of context lists
            references_list: List of reference lists (optional)

        Returns:
            List of DocumentationEntry objects
        """
        if references_list is None:
            references_list = [None] * len(topics)

        entries = []
        for topic, contexts, references in zip(topics, contexts_list, references_list):
            entry = self.generate_documentation(
                topic=topic,
                contexts=contexts,
                references=references,
            )
            entries.append(entry)

        logger.info(f"Generated documentation for {len(entries)} topics")

        return entries

    def save_documentation(
        self,
        entry: DocumentationEntry,
        filepath: str,
        format: str = "yaml",
    ) -> None:
        """Save documentation to file

        Args:
            entry: DocumentationEntry object
            filepath: Path to save file
            format: File format ('yaml', 'json', 'markdown')

        Raises:
            ValueError: If format not supported
        """
        if format.lower() == "yaml":
            content = entry.to_yaml()
        elif format.lower() == "json":
            content = entry.to_json()
        elif format.lower() == "markdown":
            content = entry.to_markdown()
        else:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported: yaml, json, markdown"
            )

        with open(filepath, "w") as f:
            f.write(content)

        logger.info(f"Saved documentation to {filepath}")

    def load_documentation(self, filepath: str) -> DocumentationEntry:
        """Load documentation from file

        Args:
            filepath: Path to documentation file

        Returns:
            DocumentationEntry object

        Raises:
            ValueError: If file format not supported
        """
        with open(filepath, "r") as f:
            content = f.read()

        # Try to parse as YAML first
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            # Try JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("Could not parse documentation file")

        # Create entry from data
        entry = DocumentationEntry(
            topic=data.get("topic", ""),
            context=data.get("context", ""),
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            references=data.get("references", []),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
        )

        logger.info(f"Loaded documentation from {filepath}")

        return entry

    def create_knowledge_base_entry(
        self,
        topic: str,
        context: str,
        summary: str,
        key_points: List[str],
        references: List[Dict],
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> Dict:
        """Create knowledge base entry

        Args:
            topic: Topic name
            context: Main context
            summary: Brief summary
            key_points: List of key points
            references: List of references
            tags: List of tags (optional)
            difficulty: Difficulty level (optional)

        Returns:
            Knowledge base entry dictionary
        """
        entry = {
            "topic": topic,
            "context": context,
            "summary": summary,
            "key_points": key_points,
            "references": references,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "tags": tags or [],
                "difficulty": difficulty or "intermediate",
            },
        }

        return entry

    def format_for_ai_training(
        self, entry: DocumentationEntry, include_references: bool = True
    ) -> str:
        """Format documentation for AI model training

        Args:
            entry: DocumentationEntry object
            include_references: Include references in output

        Returns:
            Formatted string for AI training
        """
        lines = []

        # Topic
        lines.append(f"Topic: {entry.topic}")
        lines.append("")

        # Summary
        lines.append(f"Summary: {entry.summary}")
        lines.append("")

        # Context
        lines.append("Context:")
        lines.append(entry.context)
        lines.append("")

        # Key Points
        if entry.key_points:
            lines.append("Key Points:")
            for point in entry.key_points:
                lines.append(f"- {point}")
            lines.append("")

        # References
        if include_references and entry.references:
            lines.append("References:")
            for ref in entry.references:
                lines.append(f"- {ref.get('title', 'Unknown')}")
                if ref.get('url'):
                    lines.append(f"  URL: {ref['url']}")
            lines.append("")

        return "\n".join(lines)

    def create_prompt_context(
        self, entry: DocumentationEntry, max_length: int = 2000
    ) -> str:
        """Create context for AI prompt

        Args:
            entry: DocumentationEntry object
            max_length: Maximum context length

        Returns:
            Formatted context for prompt
        """
        context_parts = [
            f"Topic: {entry.topic}",
            f"Summary: {entry.summary}",
            f"Context: {entry.context}",
        ]

        if entry.key_points:
            context_parts.append("Key Points:")
            for point in entry.key_points:
                context_parts.append(f"- {point}")

        context = "\n".join(context_parts)

        # Truncate if needed
        if len(context) > max_length:
            context = context[:max_length].rsplit("\n", 1)[0] + "\n..."

        return context
