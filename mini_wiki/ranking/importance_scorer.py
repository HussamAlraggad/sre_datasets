"""
Importance Scorer Module
Computes importance scores based on multiple factors

Features:
- Frequency scoring (how often term appears)
- Length scoring (document length)
- Recency scoring (how recent the document is)
- Citation scoring (how many times referenced)
- Configurable weights for each factor
- Batch processing
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ImportanceConfig:
    """Configuration for importance scoring

    Attributes:
        frequency_weight: Weight for term frequency (default: 0.3)
        length_weight: Weight for document length (default: 0.2)
        recency_weight: Weight for recency (default: 0.3)
        citation_weight: Weight for citations (default: 0.2)
        normalize: Normalize scores to [0, 1] (default: True)
        min_score: Minimum score threshold (default: 0.0)
        max_score: Maximum score threshold (default: 1.0)
    """

    frequency_weight: float = 0.3
    length_weight: float = 0.2
    recency_weight: float = 0.3
    citation_weight: float = 0.2
    normalize: bool = True
    min_score: float = 0.0
    max_score: float = 1.0

    def __post_init__(self):
        """Validate configuration"""
        weights = [
            self.frequency_weight,
            self.length_weight,
            self.recency_weight,
            self.citation_weight,
        ]

        for weight in weights:
            if not (0 <= weight <= 1):
                raise ValueError(f"Weight must be in [0, 1], got {weight}")

        # Weights should sum to 1 (or close to it)
        total = sum(weights)
        if not (0.9 <= total <= 1.1):
            logger.warning(
                f"Weights sum to {total}, expected ~1.0. "
                f"Scores will be normalized."
            )


class FrequencyScorer:
    """Compute importance based on term frequency"""

    def __init__(self, config: ImportanceConfig):
        """Initialize frequency scorer

        Args:
            config: Importance configuration
        """
        self.config = config

    def score(self, query_terms: List[str], document_text: str) -> float:
        """Compute frequency score

        Args:
            query_terms: List of query terms
            document_text: Document text

        Returns:
            Frequency score in [0, 1]
        """
        if not query_terms or not document_text:
            return 0.0

        # Convert to lowercase for matching
        doc_lower = document_text.lower()

        # Count term occurrences
        total_occurrences = 0
        for term in query_terms:
            term_lower = term.lower()
            # Count non-overlapping occurrences
            count = doc_lower.count(term_lower)
            total_occurrences += count

        # Normalize by document length and number of terms
        doc_length = len(document_text.split())
        max_possible = doc_length * len(query_terms)

        if max_possible == 0:
            return 0.0

        score = min(total_occurrences / max_possible, 1.0)

        return float(score)

    def score_batch(
        self, query_terms: List[str], document_texts: List[str]
    ) -> np.ndarray:
        """Compute frequency scores (batch)

        Args:
            query_terms: List of query terms
            document_texts: List of document texts

        Returns:
            Array of frequency scores
        """
        scores = [self.score(query_terms, doc) for doc in document_texts]
        return np.array(scores)


class LengthScorer:
    """Compute importance based on document length"""

    def __init__(self, config: ImportanceConfig):
        """Initialize length scorer

        Args:
            config: Importance configuration
        """
        self.config = config
        self.avg_length = None
        self.max_length = None

    def fit(self, documents: List[str]) -> None:
        """Fit length statistics on documents

        Args:
            documents: List of document texts
        """
        if not documents:
            raise ValueError("No documents provided")

        lengths = [len(doc.split()) for doc in documents]

        self.avg_length = np.mean(lengths)
        self.max_length = np.max(lengths)

        logger.info(
            f"Length statistics: avg={self.avg_length:.1f}, max={self.max_length}"
        )

    def score(self, document_text: str) -> float:
        """Compute length score

        Args:
            document_text: Document text

        Returns:
            Length score in [0, 1]
        """
        if not document_text:
            return 0.0

        doc_length = len(document_text.split())

        # If not fitted, use simple normalization
        if self.avg_length is None:
            # Assume optimal length is 200-500 words
            optimal_length = 350
            score = 1.0 - abs(doc_length - optimal_length) / (optimal_length * 2)
            return float(np.clip(score, 0, 1))

        # Score based on distance from average
        # Longer documents get higher scores (up to a point)
        if doc_length < self.avg_length:
            score = doc_length / self.avg_length
        else:
            # Penalize very long documents
            score = 1.0 - (doc_length - self.avg_length) / (self.max_length - self.avg_length) * 0.5

        return float(np.clip(score, 0, 1))

    def score_batch(self, document_texts: List[str]) -> np.ndarray:
        """Compute length scores (batch)

        Args:
            document_texts: List of document texts

        Returns:
            Array of length scores
        """
        scores = [self.score(doc) for doc in document_texts]
        return np.array(scores)


class RecencyScorer:
    """Compute importance based on recency"""

    def __init__(self, config: ImportanceConfig):
        """Initialize recency scorer

        Args:
            config: Importance configuration
        """
        self.config = config
        self.reference_date = None

    def fit(self, dates: List[datetime]) -> None:
        """Fit recency statistics on dates

        Args:
            dates: List of document dates
        """
        if not dates:
            raise ValueError("No dates provided")

        # Use most recent date as reference
        self.reference_date = max(dates)

        logger.info(f"Recency reference date: {self.reference_date}")

    def score(self, document_date: Optional[datetime] = None) -> float:
        """Compute recency score

        Args:
            document_date: Document date (default: now)

        Returns:
            Recency score in [0, 1]
        """
        if document_date is None:
            document_date = datetime.now()

        # If not fitted, use current date as reference
        if self.reference_date is None:
            reference = datetime.now()
        else:
            reference = self.reference_date

        # Calculate days since document
        days_old = (reference - document_date).days

        # Score: newer documents get higher scores
        # Half-life of 365 days (1 year)
        half_life = 365
        score = np.exp(-days_old / half_life)

        return float(np.clip(score, 0, 1))

    def score_batch(self, document_dates: List[Optional[datetime]]) -> np.ndarray:
        """Compute recency scores (batch)

        Args:
            document_dates: List of document dates

        Returns:
            Array of recency scores
        """
        scores = [self.score(date) for date in document_dates]
        return np.array(scores)


class CitationScorer:
    """Compute importance based on citations"""

    def __init__(self, config: ImportanceConfig):
        """Initialize citation scorer

        Args:
            config: Importance configuration
        """
        self.config = config
        self.max_citations = None

    def fit(self, citation_counts: List[int]) -> None:
        """Fit citation statistics

        Args:
            citation_counts: List of citation counts
        """
        if not citation_counts:
            raise ValueError("No citation counts provided")

        self.max_citations = max(citation_counts)

        logger.info(f"Citation statistics: max={self.max_citations}")

    def score(self, citation_count: int) -> float:
        """Compute citation score

        Args:
            citation_count: Number of citations

        Returns:
            Citation score in [0, 1]
        """
        if citation_count < 0:
            return 0.0

        # If not fitted, use logarithmic scaling
        if self.max_citations is None:
            # Log scale: 1 citation = 0.3, 10 = 0.6, 100 = 0.9
            score = np.log1p(citation_count) / np.log1p(100)
            return float(np.clip(score, 0, 1))

        # Normalize by max citations
        score = citation_count / self.max_citations if self.max_citations > 0 else 0.0

        return float(np.clip(score, 0, 1))

    def score_batch(self, citation_counts: List[int]) -> np.ndarray:
        """Compute citation scores (batch)

        Args:
            citation_counts: List of citation counts

        Returns:
            Array of citation scores
        """
        scores = [self.score(count) for count in citation_counts]
        return np.array(scores)


class ImportanceScorer:
    """Compute hybrid importance scores"""

    def __init__(self, config: Optional[ImportanceConfig] = None):
        """Initialize importance scorer

        Args:
            config: Importance configuration
        """
        self.config = config or ImportanceConfig()
        self.frequency_scorer = FrequencyScorer(self.config)
        self.length_scorer = LengthScorer(self.config)
        self.recency_scorer = RecencyScorer(self.config)
        self.citation_scorer = CitationScorer(self.config)

    def fit(
        self,
        documents: List[str],
        dates: Optional[List[datetime]] = None,
        citation_counts: Optional[List[int]] = None,
    ) -> None:
        """Fit importance scorers on documents

        Args:
            documents: List of document texts
            dates: List of document dates (optional)
            citation_counts: List of citation counts (optional)
        """
        self.length_scorer.fit(documents)

        if dates:
            self.recency_scorer.fit(dates)

        if citation_counts:
            self.citation_scorer.fit(citation_counts)

    def score(
        self,
        query_terms: List[str],
        document_text: str,
        document_date: Optional[datetime] = None,
        citation_count: int = 0,
    ) -> float:
        """Compute hybrid importance score

        Args:
            query_terms: List of query terms
            document_text: Document text
            document_date: Document date (optional)
            citation_count: Number of citations (default: 0)

        Returns:
            Importance score in [0, 1]
        """
        # Compute individual scores
        frequency = self.frequency_scorer.score(query_terms, document_text)
        length = self.length_scorer.score(document_text)
        recency = self.recency_scorer.score(document_date)
        citations = self.citation_scorer.score(citation_count)

        # Combine scores
        score = (
            self.config.frequency_weight * frequency
            + self.config.length_weight * length
            + self.config.recency_weight * recency
            + self.config.citation_weight * citations
        )

        # Normalize if needed
        if self.config.normalize:
            total_weight = (
                self.config.frequency_weight
                + self.config.length_weight
                + self.config.recency_weight
                + self.config.citation_weight
            )
            score = score / total_weight if total_weight > 0 else score

        # Clamp to configured range
        return float(np.clip(score, self.config.min_score, self.config.max_score))

    def score_batch(
        self,
        query_terms: List[str],
        document_texts: List[str],
        document_dates: Optional[List[Optional[datetime]]] = None,
        citation_counts: Optional[List[int]] = None,
    ) -> np.ndarray:
        """Compute hybrid importance scores (batch)

        Args:
            query_terms: List of query terms
            document_texts: List of document texts
            document_dates: List of document dates (optional)
            citation_counts: List of citation counts (optional)

        Returns:
            Array of importance scores
        """
        # Compute individual scores
        frequencies = self.frequency_scorer.score_batch(query_terms, document_texts)
        lengths = self.length_scorer.score_batch(document_texts)

        if document_dates is None:
            document_dates = [None] * len(document_texts)
        recencies = self.recency_scorer.score_batch(document_dates)

        if citation_counts is None:
            citation_counts = [0] * len(document_texts)
        citations = self.citation_scorer.score_batch(citation_counts)

        # Combine scores
        scores = (
            self.config.frequency_weight * frequencies
            + self.config.length_weight * lengths
            + self.config.recency_weight * recencies
            + self.config.citation_weight * citations
        )

        # Normalize if needed
        if self.config.normalize:
            total_weight = (
                self.config.frequency_weight
                + self.config.length_weight
                + self.config.recency_weight
                + self.config.citation_weight
            )
            scores = scores / total_weight if total_weight > 0 else scores

        # Clamp to configured range
        return np.clip(scores, self.config.min_score, self.config.max_score)

    def get_config(self) -> Dict:
        """Get current configuration

        Returns:
            Configuration dictionary
        """
        return {
            "frequency_weight": self.config.frequency_weight,
            "length_weight": self.config.length_weight,
            "recency_weight": self.config.recency_weight,
            "citation_weight": self.config.citation_weight,
            "normalize": self.config.normalize,
            "min_score": self.config.min_score,
            "max_score": self.config.max_score,
        }

    def set_weights(
        self,
        frequency_weight: float,
        length_weight: float,
        recency_weight: float,
        citation_weight: float,
    ) -> None:
        """Set scoring weights

        Args:
            frequency_weight: Weight for frequency (0-1)
            length_weight: Weight for length (0-1)
            recency_weight: Weight for recency (0-1)
            citation_weight: Weight for citations (0-1)

        Raises:
            ValueError: If weights invalid
        """
        weights = [frequency_weight, length_weight, recency_weight, citation_weight]

        for weight in weights:
            if not (0 <= weight <= 1):
                raise ValueError(f"Weight must be in [0, 1], got {weight}")

        self.config.frequency_weight = frequency_weight
        self.config.length_weight = length_weight
        self.config.recency_weight = recency_weight
        self.config.citation_weight = citation_weight

        logger.info(
            f"Updated weights: frequency={frequency_weight}, length={length_weight}, "
            f"recency={recency_weight}, citation={citation_weight}"
        )
