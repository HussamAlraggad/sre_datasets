"""
Ranking Presets Module
Pre-configured ranking strategies for different use cases

Features:
- Research-focused preset (high relevance weight)
- Balanced preset (equal weights)
- Importance-focused preset (high importance weight)
- Custom preset creation
- Preset management
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from mini_wiki.ranking.ranking_engine import RankingConfig, RankingEngine
from mini_wiki.ranking.relevance_scorer import RelevanceConfig
from mini_wiki.ranking.importance_scorer import ImportanceConfig

logger = logging.getLogger(__name__)


@dataclass
class RankingPreset:
    """Ranking preset configuration

    Attributes:
        name: Preset name
        description: Preset description
        ranking_config: RankingConfig for this preset
    """

    name: str
    description: str
    ranking_config: RankingConfig

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "config": {
                "relevance_weight": self.ranking_config.relevance_weight,
                "importance_weight": self.ranking_config.importance_weight,
                "relevance_config": self.ranking_config.relevance_config.__dict__,
                "importance_config": self.ranking_config.importance_config.__dict__,
            },
        }


class RankingPresets:
    """Manage ranking presets"""

    # Research-focused preset: prioritize relevance
    RESEARCH_FOCUSED = RankingPreset(
        name="research_focused",
        description="Prioritize relevance for research and academic use cases",
        ranking_config=RankingConfig(
            relevance_weight=0.8,
            importance_weight=0.2,
            relevance_config=RelevanceConfig(
                similarity_weight=0.8,
                tfidf_weight=0.2,
            ),
            importance_config=ImportanceConfig(
                frequency_weight=0.4,
                length_weight=0.2,
                recency_weight=0.2,
                citation_weight=0.2,
            ),
        ),
    )

    # Balanced preset: equal weights
    BALANCED = RankingPreset(
        name="balanced",
        description="Balance relevance and importance for general use",
        ranking_config=RankingConfig(
            relevance_weight=0.6,
            importance_weight=0.4,
            relevance_config=RelevanceConfig(
                similarity_weight=0.7,
                tfidf_weight=0.3,
            ),
            importance_config=ImportanceConfig(
                frequency_weight=0.3,
                length_weight=0.2,
                recency_weight=0.3,
                citation_weight=0.2,
            ),
        ),
    )

    # Importance-focused preset: prioritize importance
    IMPORTANCE_FOCUSED = RankingPreset(
        name="importance_focused",
        description="Prioritize importance for trending and popular content",
        ranking_config=RankingConfig(
            relevance_weight=0.4,
            importance_weight=0.6,
            relevance_config=RelevanceConfig(
                similarity_weight=0.6,
                tfidf_weight=0.4,
            ),
            importance_config=ImportanceConfig(
                frequency_weight=0.2,
                length_weight=0.2,
                recency_weight=0.4,
                citation_weight=0.2,
            ),
        ),
    )

    # Recency-focused preset: prioritize recent documents
    RECENCY_FOCUSED = RankingPreset(
        name="recency_focused",
        description="Prioritize recent documents for news and trending topics",
        ranking_config=RankingConfig(
            relevance_weight=0.5,
            importance_weight=0.5,
            relevance_config=RelevanceConfig(
                similarity_weight=0.7,
                tfidf_weight=0.3,
            ),
            importance_config=ImportanceConfig(
                frequency_weight=0.1,
                length_weight=0.1,
                recency_weight=0.7,
                citation_weight=0.1,
            ),
        ),
    )

    # Citation-focused preset: prioritize highly cited documents
    CITATION_FOCUSED = RankingPreset(
        name="citation_focused",
        description="Prioritize highly cited documents for authoritative sources",
        ranking_config=RankingConfig(
            relevance_weight=0.5,
            importance_weight=0.5,
            relevance_config=RelevanceConfig(
                similarity_weight=0.7,
                tfidf_weight=0.3,
            ),
            importance_config=ImportanceConfig(
                frequency_weight=0.1,
                length_weight=0.1,
                recency_weight=0.2,
                citation_weight=0.6,
            ),
        ),
    )

    # Strict relevance preset: only use relevance
    STRICT_RELEVANCE = RankingPreset(
        name="strict_relevance",
        description="Use only relevance scoring, ignore importance",
        ranking_config=RankingConfig(
            relevance_weight=1.0,
            importance_weight=0.0,
            relevance_config=RelevanceConfig(
                similarity_weight=0.7,
                tfidf_weight=0.3,
            ),
            importance_config=ImportanceConfig(),
        ),
    )

    # Strict importance preset: only use importance
    STRICT_IMPORTANCE = RankingPreset(
        name="strict_importance",
        description="Use only importance scoring, ignore relevance",
        ranking_config=RankingConfig(
            relevance_weight=0.0,
            importance_weight=1.0,
            relevance_config=RelevanceConfig(),
            importance_config=ImportanceConfig(
                frequency_weight=0.3,
                length_weight=0.2,
                recency_weight=0.3,
                citation_weight=0.2,
            ),
        ),
    )

    # Built-in presets
    PRESETS = {
        "research_focused": RESEARCH_FOCUSED,
        "balanced": BALANCED,
        "importance_focused": IMPORTANCE_FOCUSED,
        "recency_focused": RECENCY_FOCUSED,
        "citation_focused": CITATION_FOCUSED,
        "strict_relevance": STRICT_RELEVANCE,
        "strict_importance": STRICT_IMPORTANCE,
    }

    @classmethod
    def get_preset(cls, name: str) -> Optional[RankingPreset]:
        """Get preset by name

        Args:
            name: Preset name

        Returns:
            RankingPreset or None if not found
        """
        return cls.PRESETS.get(name.lower())

    @classmethod
    def list_presets(cls) -> Dict[str, str]:
        """List all available presets

        Returns:
            Dictionary of preset names and descriptions
        """
        return {
            name: preset.description
            for name, preset in cls.PRESETS.items()
        }

    @classmethod
    def create_custom(
        cls,
        name: str,
        description: str,
        relevance_weight: float,
        importance_weight: float,
        relevance_config: Optional[RelevanceConfig] = None,
        importance_config: Optional[ImportanceConfig] = None,
    ) -> RankingPreset:
        """Create custom preset

        Args:
            name: Preset name
            description: Preset description
            relevance_weight: Weight for relevance (0-1)
            importance_weight: Weight for importance (0-1)
            relevance_config: Custom relevance config (optional)
            importance_config: Custom importance config (optional)

        Returns:
            Custom RankingPreset

        Raises:
            ValueError: If weights invalid
        """
        if not (0 <= relevance_weight <= 1):
            raise ValueError("relevance_weight must be in [0, 1]")

        if not (0 <= importance_weight <= 1):
            raise ValueError("importance_weight must be in [0, 1]")

        config = RankingConfig(
            relevance_weight=relevance_weight,
            importance_weight=importance_weight,
            relevance_config=relevance_config or RelevanceConfig(),
            importance_config=importance_config or ImportanceConfig(),
        )

        preset = RankingPreset(
            name=name,
            description=description,
            ranking_config=config,
        )

        logger.info(f"Created custom preset: {name}")

        return preset

    @classmethod
    def get_engine(cls, preset_name: str) -> RankingEngine:
        """Get ranking engine for preset

        Args:
            preset_name: Preset name

        Returns:
            RankingEngine configured with preset

        Raises:
            ValueError: If preset not found
        """
        preset = cls.get_preset(preset_name)

        if preset is None:
            raise ValueError(
                f"Unknown preset: {preset_name}. "
                f"Available: {', '.join(cls.list_presets().keys())}"
            )

        logger.info(f"Creating ranking engine with preset: {preset_name}")

        return RankingEngine(preset.ranking_config)

    @classmethod
    def print_presets(cls) -> str:
        """Get formatted string of all presets

        Returns:
            Formatted preset information
        """
        lines = ["Available Ranking Presets:\n"]

        for name, description in cls.list_presets().items():
            preset = cls.get_preset(name)
            config = preset.ranking_config

            lines.append(f"  {name}:")
            lines.append(f"    Description: {description}")
            lines.append(
                f"    Weights: relevance={config.relevance_weight}, "
                f"importance={config.importance_weight}"
            )
            lines.append("")

        return "\n".join(lines)


# Convenience functions for quick access
def get_research_focused_engine() -> RankingEngine:
    """Get research-focused ranking engine"""
    return RankingPresets.get_engine("research_focused")


def get_balanced_engine() -> RankingEngine:
    """Get balanced ranking engine"""
    return RankingPresets.get_engine("balanced")


def get_importance_focused_engine() -> RankingEngine:
    """Get importance-focused ranking engine"""
    return RankingPresets.get_engine("importance_focused")


def get_recency_focused_engine() -> RankingEngine:
    """Get recency-focused ranking engine"""
    return RankingPresets.get_engine("recency_focused")


def get_citation_focused_engine() -> RankingEngine:
    """Get citation-focused ranking engine"""
    return RankingPresets.get_engine("citation_focused")
