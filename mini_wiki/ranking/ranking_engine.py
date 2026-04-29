"""
Ranking Engine Module
Combines relevance and importance scores for hybrid ranking

Features:
- Hybrid ranking combining relevance and importance
- Configurable weights
- Result aggregation and sorting
- Ranking statistics
- Batch processing
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from mini_wiki.ranking.importance_scorer import ImportanceScorer, ImportanceConfig
from mini_wiki.ranking.relevance_scorer import RelevanceScorer, RelevanceConfig

logger = logging.getLogger(__name__)


@dataclass
class RankingConfig:
    """Configuration for ranking engine

    Attributes:
        relevance_weight: Weight for relevance score (default: 0.6)
        importance_weight: Weight for importance score (default: 0.4)
        normalize: Normalize final scores to [0, 1] (default: True)
        min_score: Minimum score threshold (default: 0.0)
        max_score: Maximum score threshold (default: 1.0)
        relevance_config: Configuration for relevance scorer
        importance_config: Configuration for importance scorer
    """

    relevance_weight: float = 0.6
    importance_weight: float = 0.4
    normalize: bool = True
    min_score: float = 0.0
    max_score: float = 1.0
    relevance_config: Optional[RelevanceConfig] = None
    importance_config: Optional[ImportanceConfig] = None

    def __post_init__(self):
        """Validate configuration"""
        if not (0 <= self.relevance_weight <= 1):
            raise ValueError("relevance_weight must be in [0, 1]")

        if not (0 <= self.importance_weight <= 1):
            raise ValueError("importance_weight must be in [0, 1]")

        # Weights should sum to 1 (or close to it)
        total = self.relevance_weight + self.importance_weight
        if not (0.9 <= total <= 1.1):
            logger.warning(
                f"Weights sum to {total}, expected ~1.0. "
                f"Scores will be normalized."
            )

        # Create default configs if not provided
        if self.relevance_config is None:
            self.relevance_config = RelevanceConfig()

        if self.importance_config is None:
            self.importance_config = ImportanceConfig()


@dataclass
class RankingResult:
    """Result of ranking operation

    Attributes:
        record_id: ID of ranked record
        relevance_score: Relevance score (0-1)
        importance_score: Importance score (0-1)
        final_score: Final combined score (0-1)
        rank: Rank position (1-indexed)
        metadata: Additional metadata
    """

    record_id: int
    relevance_score: float
    importance_score: float
    final_score: float
    rank: int
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "record_id": self.record_id,
            "relevance_score": round(self.relevance_score, 4),
            "importance_score": round(self.importance_score, 4),
            "final_score": round(self.final_score, 4),
            "rank": self.rank,
            "metadata": self.metadata,
        }


class RankingEngine:
    """Hybrid ranking engine combining relevance and importance"""

    def __init__(self, config: Optional[RankingConfig] = None):
        """Initialize ranking engine

        Args:
            config: Ranking configuration
        """
        self.config = config or RankingConfig()
        self.relevance_scorer = RelevanceScorer(self.config.relevance_config)
        self.importance_scorer = ImportanceScorer(self.config.importance_config)

    def fit(
        self,
        documents: List[str],
        dates: Optional[List[datetime]] = None,
        citation_counts: Optional[List[int]] = None,
    ) -> None:
        """Fit ranking engine on documents

        Args:
            documents: List of document texts
            dates: List of document dates (optional)
            citation_counts: List of citation counts (optional)
        """
        logger.info(f"Fitting ranking engine on {len(documents)} documents")

        # Fit TF-IDF on documents
        self.relevance_scorer.fit_tfidf(documents)

        # Fit importance scorers
        self.importance_scorer.fit(documents, dates, citation_counts)

        logger.info("Ranking engine fitted successfully")

    def rank(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        document_texts: List[str],
        document_embeddings: np.ndarray,
        document_ids: Optional[List[int]] = None,
        document_dates: Optional[List[Optional[datetime]]] = None,
        citation_counts: Optional[List[int]] = None,
        top_k: Optional[int] = None,
    ) -> List[RankingResult]:
        """Rank documents

        Args:
            query_text: Query text
            query_embedding: Query embedding
            document_texts: List of document texts
            document_embeddings: Array of document embeddings
            document_ids: List of document IDs (default: sequential)
            document_dates: List of document dates (optional)
            citation_counts: List of citation counts (optional)
            top_k: Return top-k results (default: all)

        Returns:
            List of RankingResult objects sorted by final_score descending
        """
        if not document_texts:
            return []

        if len(document_texts) != len(document_embeddings):
            raise ValueError("Number of texts and embeddings mismatch")

        # Generate document IDs if not provided
        if document_ids is None:
            document_ids = list(range(len(document_texts)))

        # Extract query terms
        query_terms = query_text.lower().split()

        # Compute relevance scores
        relevance_scores = self.relevance_scorer.score_batch(
            query_text,
            query_embedding,
            document_texts,
            document_embeddings,
            document_indices=list(range(len(document_texts))),
        )

        # Compute importance scores
        if document_dates is None:
            document_dates = [None] * len(document_texts)

        if citation_counts is None:
            citation_counts = [0] * len(document_texts)

        importance_scores = self.importance_scorer.score_batch(
            query_terms,
            document_texts,
            document_dates,
            citation_counts,
        )

        # Combine scores
        final_scores = (
            self.config.relevance_weight * relevance_scores
            + self.config.importance_weight * importance_scores
        )

        # Normalize if needed
        if self.config.normalize:
            total_weight = self.config.relevance_weight + self.config.importance_weight
            final_scores = final_scores / total_weight if total_weight > 0 else final_scores

        # Clamp to configured range
        final_scores = np.clip(final_scores, self.config.min_score, self.config.max_score)

        # Create ranking results
        results = []
        for idx, (doc_id, rel_score, imp_score, final_score) in enumerate(
            zip(document_ids, relevance_scores, importance_scores, final_scores)
        ):
            result = RankingResult(
                record_id=doc_id,
                relevance_score=float(rel_score),
                importance_score=float(imp_score),
                final_score=float(final_score),
                rank=0,  # Will be set after sorting
            )
            results.append(result)

        # Sort by final score descending
        results.sort(key=lambda r: r.final_score, reverse=True)

        # Set ranks
        for rank, result in enumerate(results, start=1):
            result.rank = rank

        # Return top-k if specified
        if top_k is not None:
            results = results[:top_k]

        logger.info(f"Ranked {len(results)} documents")

        return results

    def get_config(self) -> Dict:
        """Get current configuration

        Returns:
            Configuration dictionary
        """
        return {
            "relevance_weight": self.config.relevance_weight,
            "importance_weight": self.config.importance_weight,
            "normalize": self.config.normalize,
            "min_score": self.config.min_score,
            "max_score": self.config.max_score,
            "relevance_config": self.relevance_scorer.get_config(),
            "importance_config": self.importance_scorer.get_config(),
        }

    def set_weights(self, relevance_weight: float, importance_weight: float) -> None:
        """Set ranking weights

        Args:
            relevance_weight: Weight for relevance (0-1)
            importance_weight: Weight for importance (0-1)

        Raises:
            ValueError: If weights invalid
        """
        if not (0 <= relevance_weight <= 1):
            raise ValueError("relevance_weight must be in [0, 1]")

        if not (0 <= importance_weight <= 1):
            raise ValueError("importance_weight must be in [0, 1]")

        self.config.relevance_weight = relevance_weight
        self.config.importance_weight = importance_weight

        logger.info(
            f"Updated ranking weights: relevance={relevance_weight}, "
            f"importance={importance_weight}"
        )

    def get_score_breakdown(self, result: RankingResult) -> Dict:
        """Get detailed score breakdown for a result

        Args:
            result: RankingResult object

        Returns:
            Dictionary with score breakdown
        """
        return {
            "record_id": result.record_id,
            "rank": result.rank,
            "relevance_score": round(result.relevance_score, 4),
            "relevance_contribution": round(
                result.relevance_score * self.config.relevance_weight, 4
            ),
            "importance_score": round(result.importance_score, 4),
            "importance_contribution": round(
                result.importance_score * self.config.importance_weight, 4
            ),
            "final_score": round(result.final_score, 4),
        }

    def get_stats(self, results: List[RankingResult]) -> Dict:
        """Get statistics about ranking results

        Args:
            results: List of RankingResult objects

        Returns:
            Dictionary with statistics
        """
        if not results:
            return {
                "count": 0,
                "avg_relevance": 0.0,
                "avg_importance": 0.0,
                "avg_final": 0.0,
                "max_final": 0.0,
                "min_final": 0.0,
            }

        relevance_scores = [r.relevance_score for r in results]
        importance_scores = [r.importance_score for r in results]
        final_scores = [r.final_score for r in results]

        return {
            "count": len(results),
            "avg_relevance": round(np.mean(relevance_scores), 4),
            "avg_importance": round(np.mean(importance_scores), 4),
            "avg_final": round(np.mean(final_scores), 4),
            "max_final": round(np.max(final_scores), 4),
            "min_final": round(np.min(final_scores), 4),
            "std_final": round(np.std(final_scores), 4),
        }
