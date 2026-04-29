"""
Relevance Scorer Module
Computes relevance scores using cosine similarity and TF-IDF

Features:
- Cosine similarity from embeddings
- TF-IDF scoring from text
- Hybrid relevance combining both metrics
- Configurable weights
- Batch processing
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


@dataclass
class RelevanceConfig:
    """Configuration for relevance scoring

    Attributes:
        similarity_weight: Weight for cosine similarity (default: 0.7)
        tfidf_weight: Weight for TF-IDF score (default: 0.3)
        normalize: Normalize scores to [0, 1] (default: True)
        min_score: Minimum score threshold (default: 0.0)
        max_score: Maximum score threshold (default: 1.0)
    """

    similarity_weight: float = 0.7
    tfidf_weight: float = 0.3
    normalize: bool = True
    min_score: float = 0.0
    max_score: float = 1.0

    def __post_init__(self):
        """Validate configuration"""
        if not (0 <= self.similarity_weight <= 1):
            raise ValueError("similarity_weight must be in [0, 1]")

        if not (0 <= self.tfidf_weight <= 1):
            raise ValueError("tfidf_weight must be in [0, 1]")

        # Weights should sum to 1 (or close to it)
        total = self.similarity_weight + self.tfidf_weight
        if not (0.9 <= total <= 1.1):
            logger.warning(
                f"Weights sum to {total}, expected ~1.0. "
                f"Scores will be normalized."
            )


class SimilarityScorer:
    """Compute relevance using cosine similarity"""

    def __init__(self, config: RelevanceConfig):
        """Initialize similarity scorer

        Args:
            config: Relevance configuration
        """
        self.config = config

    def score(
        self, query_embedding: np.ndarray, document_embedding: np.ndarray
    ) -> float:
        """Compute cosine similarity score

        Args:
            query_embedding: Query embedding vector
            document_embedding: Document embedding vector

        Returns:
            Similarity score in [0, 1]
        """
        # Normalize vectors
        q = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        d = document_embedding / (np.linalg.norm(document_embedding) + 1e-10)

        # Compute cosine similarity
        similarity = np.dot(q, d)

        # Clamp to [0, 1]
        return float(np.clip(similarity, 0, 1))

    def score_batch(
        self, query_embedding: np.ndarray, document_embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity scores (batch)

        Args:
            query_embedding: Query embedding vector
            document_embeddings: Array of document embeddings (shape: (n, dim))

        Returns:
            Array of similarity scores (shape: (n,))
        """
        # Normalize query
        q = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)

        # Normalize documents
        d = document_embeddings / (
            np.linalg.norm(document_embeddings, axis=1, keepdims=True) + 1e-10
        )

        # Compute cosine similarities
        similarities = np.dot(d, q)

        # Clamp to [0, 1]
        return np.clip(similarities, 0, 1)


class TFIDFScorer:
    """Compute relevance using TF-IDF"""

    def __init__(self, config: RelevanceConfig):
        """Initialize TF-IDF scorer

        Args:
            config: Relevance configuration
        """
        self.config = config
        self.vectorizer = None
        self.tfidf_matrix = None
        self.documents = None

    def fit(self, documents: List[str]) -> None:
        """Fit TF-IDF vectorizer on documents

        Args:
            documents: List of document texts
        """
        if not documents:
            raise ValueError("No documents provided")

        logger.info(f"Fitting TF-IDF vectorizer on {len(documents)} documents")

        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words="english",
            lowercase=True,
            min_df=1,
            max_df=0.95,
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        self.documents = documents

        logger.info(f"TF-IDF vectorizer fitted with {self.tfidf_matrix.shape[1]} features")

    def score(self, query: str, document_index: int) -> float:
        """Compute TF-IDF score for query against document

        Args:
            query: Query text
            document_index: Index of document in fitted documents

        Returns:
            TF-IDF score in [0, 1]

        Raises:
            RuntimeError: If vectorizer not fitted
            IndexError: If document_index out of range
        """
        if self.vectorizer is None:
            raise RuntimeError("Vectorizer not fitted. Call fit() first.")

        if document_index < 0 or document_index >= len(self.documents):
            raise IndexError(f"Document index {document_index} out of range")

        # Transform query
        query_vector = self.vectorizer.transform([query])

        # Compute similarity with document
        document_vector = self.tfidf_matrix[document_index]

        # Cosine similarity
        similarity = query_vector.dot(document_vector.T).toarray()[0, 0]

        return float(np.clip(similarity, 0, 1))

    def score_batch(self, query: str, document_indices: List[int]) -> np.ndarray:
        """Compute TF-IDF scores (batch)

        Args:
            query: Query text
            document_indices: List of document indices

        Returns:
            Array of TF-IDF scores

        Raises:
            RuntimeError: If vectorizer not fitted
        """
        if self.vectorizer is None:
            raise RuntimeError("Vectorizer not fitted. Call fit() first.")

        # Transform query
        query_vector = self.vectorizer.transform([query])

        scores = []
        for idx in document_indices:
            if idx < 0 or idx >= len(self.documents):
                scores.append(0.0)
            else:
                document_vector = self.tfidf_matrix[idx]
                similarity = query_vector.dot(document_vector.T).toarray()[0, 0]
                scores.append(float(np.clip(similarity, 0, 1)))

        return np.array(scores)


class RelevanceScorer:
    """Compute hybrid relevance scores"""

    def __init__(self, config: Optional[RelevanceConfig] = None):
        """Initialize relevance scorer

        Args:
            config: Relevance configuration
        """
        self.config = config or RelevanceConfig()
        self.similarity_scorer = SimilarityScorer(self.config)
        self.tfidf_scorer = TFIDFScorer(self.config)

    def fit_tfidf(self, documents: List[str]) -> None:
        """Fit TF-IDF on documents

        Args:
            documents: List of document texts
        """
        self.tfidf_scorer.fit(documents)

    def score(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        document_text: str,
        document_embedding: np.ndarray,
        document_index: Optional[int] = None,
    ) -> float:
        """Compute hybrid relevance score

        Args:
            query_text: Query text
            query_embedding: Query embedding
            document_text: Document text
            document_embedding: Document embedding
            document_index: Index in TF-IDF matrix (optional)

        Returns:
            Relevance score in [0, 1]
        """
        # Compute similarity score
        similarity = self.similarity_scorer.score(query_embedding, document_embedding)

        # Compute TF-IDF score
        tfidf = 0.0
        if self.tfidf_scorer.vectorizer is not None and document_index is not None:
            tfidf = self.tfidf_scorer.score(query_text, document_index)

        # Combine scores
        score = (
            self.config.similarity_weight * similarity
            + self.config.tfidf_weight * tfidf
        )

        # Normalize if needed
        if self.config.normalize:
            total_weight = self.config.similarity_weight + self.config.tfidf_weight
            score = score / total_weight if total_weight > 0 else score

        # Clamp to configured range
        return float(np.clip(score, self.config.min_score, self.config.max_score))

    def score_batch(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        document_texts: List[str],
        document_embeddings: np.ndarray,
        document_indices: Optional[List[int]] = None,
    ) -> np.ndarray:
        """Compute hybrid relevance scores (batch)

        Args:
            query_text: Query text
            query_embedding: Query embedding
            document_texts: List of document texts
            document_embeddings: Array of document embeddings
            document_indices: List of indices in TF-IDF matrix (optional)

        Returns:
            Array of relevance scores
        """
        # Compute similarity scores
        similarities = self.similarity_scorer.score_batch(
            query_embedding, document_embeddings
        )

        # Compute TF-IDF scores
        tfidf_scores = np.zeros(len(document_texts))
        if self.tfidf_scorer.vectorizer is not None and document_indices is not None:
            tfidf_scores = self.tfidf_scorer.score_batch(query_text, document_indices)

        # Combine scores
        scores = (
            self.config.similarity_weight * similarities
            + self.config.tfidf_weight * tfidf_scores
        )

        # Normalize if needed
        if self.config.normalize:
            total_weight = self.config.similarity_weight + self.config.tfidf_weight
            scores = scores / total_weight if total_weight > 0 else scores

        # Clamp to configured range
        return np.clip(scores, self.config.min_score, self.config.max_score)

    def get_config(self) -> Dict:
        """Get current configuration

        Returns:
            Configuration dictionary
        """
        return {
            "similarity_weight": self.config.similarity_weight,
            "tfidf_weight": self.config.tfidf_weight,
            "normalize": self.config.normalize,
            "min_score": self.config.min_score,
            "max_score": self.config.max_score,
        }

    def set_weights(self, similarity_weight: float, tfidf_weight: float) -> None:
        """Set scoring weights

        Args:
            similarity_weight: Weight for similarity (0-1)
            tfidf_weight: Weight for TF-IDF (0-1)

        Raises:
            ValueError: If weights invalid
        """
        if not (0 <= similarity_weight <= 1):
            raise ValueError("similarity_weight must be in [0, 1]")

        if not (0 <= tfidf_weight <= 1):
            raise ValueError("tfidf_weight must be in [0, 1]")

        self.config.similarity_weight = similarity_weight
        self.config.tfidf_weight = tfidf_weight

        logger.info(
            f"Updated weights: similarity={similarity_weight}, tfidf={tfidf_weight}"
        )
