"""
mini_wiki - Universal Research Assistant

A tool that learns your dataset, teaches AI models about it,
and helps you analyze it with intelligent hybrid ranking.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

# Lazy imports to handle missing dependencies gracefully
__all__ = [
    "MiniWiki",
    "DataRecord",
    "Dataset",
    "RankingResult",
    "AIReference",
]


def __getattr__(name):
    """Lazy import to handle missing dependencies"""
    if name == "MiniWiki":
        from .main import MiniWiki
        return MiniWiki
    elif name in ("DataRecord", "Dataset", "RankingResult", "AIReference"):
        from .core.data_models import DataRecord, Dataset, RankingResult, AIReference
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
