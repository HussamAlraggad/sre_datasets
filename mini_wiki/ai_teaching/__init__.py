"""
AI Teaching package for mini_wiki
"""

from mini_wiki.ai_teaching.context_generator import ContextGenerator, ContextConfig
from mini_wiki.ai_teaching.reference_extractor import (
    ReferenceExtractor,
    Reference,
    URLExtractor,
    CitationExtractor,
)
from mini_wiki.ai_teaching.ai_documentation import (
    AIDocumentationGenerator,
    DocumentationEntry,
)
from mini_wiki.ai_teaching.knowledge_base import KnowledgeBase

__all__ = [
    "ContextGenerator",
    "ContextConfig",
    "ReferenceExtractor",
    "Reference",
    "URLExtractor",
    "CitationExtractor",
    "AIDocumentationGenerator",
    "DocumentationEntry",
    "KnowledgeBase",
]
