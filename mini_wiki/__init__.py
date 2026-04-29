"""
mini_wiki - Universal Research Assistant

A tool that learns your dataset, teaches AI models about it,
and helps you analyze it with intelligent hybrid ranking.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

from .core.data_models import DataRecord, Dataset, RankingResult, AIReference
from .main import MiniWiki

__all__ = [
    "MiniWiki",
    "DataRecord",
    "Dataset",
    "RankingResult",
    "AIReference",
]
