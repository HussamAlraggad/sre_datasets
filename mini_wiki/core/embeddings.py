"""
Embeddings Module
Handles text embedding generation using Sentence Transformers

Features:
- Multiple embedding models (all-MiniLM-L6-v2, all-mpnet-base-v2, etc.)
- Batch processing for efficiency
- GPU support with automatic fallback to CPU
- Caching of embeddings
- Dimension reduction and normalization
- Similarity computation
"""

import hashlib
import logging
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embeddings

    Attributes:
        model_name: Sentence Transformers model name (default: 'all-MiniLM-L6-v2')
        batch_size: Batch size for processing (default: 32)
        normalize: Normalize embeddings to unit length (default: True)
        use_gpu: Use GPU if available (default: True)
        cache_dir: Directory for caching embeddings (default: None)
        cache_embeddings: Cache computed embeddings (default: True)
        max_seq_length: Maximum sequence length (default: 512)
        show_progress_bar: Show progress bar during processing (default: False)
    """

    model_name: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    normalize: bool = True
    use_gpu: bool = True
    cache_dir: Optional[Path] = None
    cache_embeddings: bool = True
    max_seq_length: int = 512
    show_progress_bar: bool = False


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    def __init__(self, config: EmbeddingConfig):
        """Initialize provider

        Args:
            config: Embedding configuration
        """
        self.config = config
        self.cache = {} if config.cache_embeddings else None

    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts

        Args:
            texts: List of text strings

        Returns:
            Array of shape (len(texts), embedding_dim)

        Raises:
            ValueError: If texts are invalid
            RuntimeError: If embedding fails
        """
        pass

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Get embedding dimension

        Returns:
            Dimension of embeddings
        """
        pass

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text

        Args:
            text: Text to cache

        Returns:
            Cache key (MD5 hash)
        """
        return hashlib.md5(text.encode()).hexdigest()

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length

        Args:
            embeddings: Array of embeddings

        Returns:
            Normalized embeddings
        """
        if not self.config.normalize:
            return embeddings

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider using Sentence Transformers"""

    def __init__(self, config: EmbeddingConfig):
        """Initialize Sentence Transformers provider

        Args:
            config: Embedding configuration

        Raises:
            ImportError: If sentence-transformers not installed
        """
        super().__init__(config)

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        # Determine device
        device = "cuda" if config.use_gpu else "cpu"

        try:
            # Try to load model
            self.model = SentenceTransformer(config.model_name)
            self.model.to(device)
            logger.info(
                f"Loaded model '{config.model_name}' on device '{device}'"
            )

        except Exception as e:
            logger.warning(f"Failed to load model on {device}: {e}")
            logger.info("Falling back to CPU")
            self.model = SentenceTransformer(config.model_name)
            self.model.to("cpu")

    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using Sentence Transformers

        Args:
            texts: List of text strings

        Returns:
            Array of shape (len(texts), embedding_dim)

        Raises:
            ValueError: If texts are invalid
        """
        if not texts:
            raise ValueError("No texts provided")

        if not all(isinstance(t, str) for t in texts):
            raise ValueError("All texts must be strings")

        # Check cache
        embeddings_list = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            if self.cache is not None:
                cache_key = self._get_cache_key(text)
                if cache_key in self.cache:
                    embeddings_list.append(self.cache[cache_key])
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Compute uncached embeddings
        if uncached_texts:
            logger.info(
                f"Computing embeddings for {len(uncached_texts)} texts "
                f"(batch_size={self.config.batch_size})"
            )

            uncached_embeddings = self.model.encode(
                uncached_texts,
                batch_size=self.config.batch_size,
                normalize_embeddings=self.config.normalize,
                show_progress_bar=self.config.show_progress_bar,
            )

            # Cache embeddings
            if self.cache is not None:
                for text, embedding in zip(uncached_texts, uncached_embeddings):
                    cache_key = self._get_cache_key(text)
                    self.cache[cache_key] = embedding

            # Insert into result list
            for idx, embedding in zip(uncached_indices, uncached_embeddings):
                embeddings_list.insert(idx, embedding)

        # Ensure correct order
        embeddings = np.array(embeddings_list)

        logger.info(f"Generated embeddings with shape {embeddings.shape}")

        return embeddings

    def get_embedding_dim(self) -> int:
        """Get embedding dimension

        Returns:
            Dimension of embeddings
        """
        return self.model.get_sentence_embedding_dimension()


class EmbeddingManager:
    """Manage embeddings with caching and similarity computation"""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedding manager

        Args:
            config: Embedding configuration
        """
        self.config = config or EmbeddingConfig()
        self.provider = SentenceTransformerProvider(self.config)
        self.embeddings_cache: Dict[str, np.ndarray] = {}

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts

        Args:
            texts: List of text strings

        Returns:
            Array of shape (len(texts), embedding_dim)
        """
        return self.provider.embed(texts)

    def embed_records(
        self, records: List[Dict[str, Any]], text_field: str = "text"
    ) -> Tuple[np.ndarray, List[str]]:
        """Generate embeddings for records

        Args:
            records: List of records (dicts)
            text_field: Field name containing text (default: 'text')

        Returns:
            Tuple of (embeddings array, list of texts)

        Raises:
            ValueError: If text_field not found in records
        """
        texts = []

        for record in records:
            if text_field not in record:
                raise ValueError(
                    f"Field '{text_field}' not found in record: {record}"
                )

            text = record[text_field]

            # Convert to string if needed
            if not isinstance(text, str):
                text = str(text)

            texts.append(text)

        embeddings = self.embed_texts(texts)

        return embeddings, texts

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        # Normalize if not already normalized
        e1 = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
        e2 = embedding2 / (np.linalg.norm(embedding2) + 1e-10)

        similarity = np.dot(e1, e2)

        # Clamp to [0, 1]
        return float(np.clip(similarity, 0, 1))

    def compute_similarities(
        self, query_embedding: np.ndarray, embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarities between query and multiple embeddings

        Args:
            query_embedding: Query embedding vector
            embeddings: Array of embedding vectors (shape: (n, dim))

        Returns:
            Array of similarity scores (shape: (n,))
        """
        # Normalize
        q = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        e = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10)

        # Compute similarities
        similarities = np.dot(e, q)

        # Clamp to [0, 1]
        return np.clip(similarities, 0, 1)

    def find_similar(
        self,
        query_text: str,
        embeddings: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """Find most similar embeddings to query

        Args:
            query_text: Query text
            embeddings: Array of embeddings to search
            top_k: Number of top results to return

        Returns:
            List of (index, similarity) tuples, sorted by similarity descending
        """
        # Embed query
        query_embedding = self.embed_texts([query_text])[0]

        # Compute similarities
        similarities = self.compute_similarities(query_embedding, embeddings)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Return (index, similarity) tuples
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    def get_embedding_dim(self) -> int:
        """Get embedding dimension

        Returns:
            Dimension of embeddings
        """
        return self.provider.get_embedding_dim()

    def save_embeddings(
        self, embeddings: np.ndarray, path: Union[str, Path]
    ) -> None:
        """Save embeddings to file

        Args:
            embeddings: Embeddings array
            path: Path to save file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        np.save(path, embeddings)
        logger.info(f"Saved embeddings to {path}")

    def load_embeddings(self, path: Union[str, Path]) -> np.ndarray:
        """Load embeddings from file

        Args:
            path: Path to embeddings file

        Returns:
            Embeddings array
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {path}")

        embeddings = np.load(path)
        logger.info(f"Loaded embeddings from {path} with shape {embeddings.shape}")

        return embeddings

    def save_cache(self, path: Union[str, Path]) -> None:
        """Save embedding cache to file

        Args:
            path: Path to cache file
        """
        if self.provider.cache is None:
            logger.warning("Caching is disabled")
            return

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            pickle.dump(self.provider.cache, f)

        logger.info(f"Saved embedding cache to {path}")

    def load_cache(self, path: Union[str, Path]) -> None:
        """Load embedding cache from file

        Args:
            path: Path to cache file
        """
        path = Path(path)

        if not path.exists():
            logger.warning(f"Cache file not found: {path}")
            return

        with open(path, "rb") as f:
            self.provider.cache = pickle.load(f)

        logger.info(f"Loaded embedding cache from {path}")

    def clear_cache(self) -> None:
        """Clear embedding cache"""
        if self.provider.cache is not None:
            self.provider.cache.clear()
            logger.info("Cleared embedding cache")
