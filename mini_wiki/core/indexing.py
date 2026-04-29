"""
Indexing Module
Handles vector indexing and similarity search using FAISS

Features:
- Multiple index types (Flat, IVF, HNSW)
- Efficient similarity search
- Index persistence (save/load)
- Batch operations
- Index statistics and monitoring
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IndexConfig:
    """Configuration for vector index

    Attributes:
        index_type: Type of index ('flat', 'ivf', 'hnsw')
        metric: Distance metric ('l2', 'cosine')
        nprobe: Number of probes for IVF (default: 10)
        nlist: Number of clusters for IVF (default: 100)
        m: Number of connections for HNSW (default: 16)
        ef_construction: Construction parameter for HNSW (default: 200)
        ef_search: Search parameter for HNSW (default: 200)
    """

    index_type: str = "flat"
    metric: str = "l2"
    nprobe: int = 10
    nlist: int = 100
    m: int = 16
    ef_construction: int = 200
    ef_search: int = 200


class VectorIndex:
    """Vector index for similarity search"""

    def __init__(self, config: Optional[IndexConfig] = None):
        """Initialize vector index

        Args:
            config: Index configuration
        """
        self.config = config or IndexConfig()
        self.index = None
        self.dimension = None
        self.size = 0

    def _get_faiss(self):
        """Get FAISS module

        Returns:
            FAISS module

        Raises:
            ImportError: If FAISS not installed
        """
        try:
            import faiss
            return faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu not installed. "
                "Install with: pip install faiss-cpu"
            )

    def create(self, dimension: int) -> None:
        """Create index with given dimension

        Args:
            dimension: Embedding dimension

        Raises:
            ValueError: If dimension is invalid
        """
        if dimension <= 0:
            raise ValueError(f"Invalid dimension: {dimension}")

        self.dimension = dimension
        faiss = self._get_faiss()

        logger.info(
            f"Creating {self.config.index_type} index "
            f"with dimension {dimension}"
        )

        if self.config.index_type == "flat":
            self.index = self._create_flat_index(faiss, dimension)

        elif self.config.index_type == "ivf":
            self.index = self._create_ivf_index(faiss, dimension)

        elif self.config.index_type == "hnsw":
            self.index = self._create_hnsw_index(faiss, dimension)

        else:
            raise ValueError(
                f"Unknown index type: {self.config.index_type}. "
                f"Supported: flat, ivf, hnsw"
            )

        self.size = 0
        logger.info(f"Index created successfully")

    def _create_flat_index(self, faiss, dimension: int):
        """Create flat (brute-force) index

        Args:
            faiss: FAISS module
            dimension: Embedding dimension

        Returns:
            FAISS index
        """
        if self.config.metric == "cosine":
            # For cosine similarity, use inner product on normalized vectors
            return faiss.IndexFlatIP(dimension)
        else:
            # L2 distance
            return faiss.IndexFlatL2(dimension)

    def _create_ivf_index(self, faiss, dimension: int):
        """Create IVF (Inverted File) index

        Args:
            faiss: FAISS module
            dimension: Embedding dimension

        Returns:
            FAISS index
        """
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(
            quantizer, dimension, self.config.nlist
        )
        index.nprobe = self.config.nprobe

        return index

    def _create_hnsw_index(self, faiss, dimension: int):
        """Create HNSW (Hierarchical Navigable Small World) index

        Args:
            faiss: FAISS module
            dimension: Embedding dimension

        Returns:
            FAISS index
        """
        index = faiss.IndexHNSWFlat(dimension, self.config.m)
        index.hnsw.efConstruction = self.config.ef_construction
        index.hnsw.efSearch = self.config.ef_search

        return index

    def add(self, embeddings: np.ndarray) -> None:
        """Add embeddings to index

        Args:
            embeddings: Array of embeddings (shape: (n, dimension))

        Raises:
            ValueError: If embeddings have wrong dimension
            RuntimeError: If index not created
        """
        if self.index is None:
            raise RuntimeError("Index not created. Call create() first.")

        if embeddings.ndim != 2:
            raise ValueError(
                f"Embeddings must be 2D array, got {embeddings.ndim}D"
            )

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: "
                f"expected {self.dimension}, got {embeddings.shape[1]}"
            )

        # Ensure float32
        embeddings = embeddings.astype(np.float32)

        logger.info(f"Adding {len(embeddings)} embeddings to index")

        # For IVF, need to train first
        if self.config.index_type == "ivf" and self.size == 0:
            logger.info("Training IVF index...")
            self.index.train(embeddings)

        self.index.add(embeddings)
        self.size += len(embeddings)

        logger.info(f"Index now contains {self.size} vectors")

    def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar embeddings

        Args:
            query_embedding: Query embedding (shape: (dimension,))
            k: Number of results to return

        Returns:
            Tuple of (distances, indices) arrays

        Raises:
            ValueError: If query has wrong dimension
            RuntimeError: If index is empty
        """
        if self.index is None:
            raise RuntimeError("Index not created. Call create() first.")

        if self.size == 0:
            raise RuntimeError("Index is empty. Add embeddings first.")

        if query_embedding.ndim != 1:
            raise ValueError(
                f"Query must be 1D array, got {query_embedding.ndim}D"
            )

        if query_embedding.shape[0] != self.dimension:
            raise ValueError(
                f"Query dimension mismatch: "
                f"expected {self.dimension}, got {query_embedding.shape[0]}"
            )

        # Ensure float32 and reshape for FAISS
        query = query_embedding.astype(np.float32).reshape(1, -1)

        # Clamp k to index size
        k = min(k, self.size)

        distances, indices = self.index.search(query, k)

        return distances[0], indices[0]

    def search_batch(
        self, query_embeddings: np.ndarray, k: int = 5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar embeddings (batch)

        Args:
            query_embeddings: Query embeddings (shape: (n, dimension))
            k: Number of results per query

        Returns:
            Tuple of (distances, indices) arrays

        Raises:
            ValueError: If queries have wrong dimension
            RuntimeError: If index is empty
        """
        if self.index is None:
            raise RuntimeError("Index not created. Call create() first.")

        if self.size == 0:
            raise RuntimeError("Index is empty. Add embeddings first.")

        if query_embeddings.ndim != 2:
            raise ValueError(
                f"Queries must be 2D array, got {query_embeddings.ndim}D"
            )

        if query_embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension mismatch: "
                f"expected {self.dimension}, got {query_embeddings.shape[1]}"
            )

        # Ensure float32
        queries = query_embeddings.astype(np.float32)

        # Clamp k to index size
        k = min(k, self.size)

        distances, indices = self.index.search(queries, k)

        return distances, indices

    def save(self, path: Union[str, Path]) -> None:
        """Save index to file

        Args:
            path: Path to save file
        """
        if self.index is None:
            raise RuntimeError("Index not created")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        faiss = self._get_faiss()
        faiss.write_index(self.index, str(path))

        logger.info(f"Saved index to {path}")

    def load(self, path: Union[str, Path]) -> None:
        """Load index from file

        Args:
            path: Path to index file
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}")

        faiss = self._get_faiss()
        self.index = faiss.read_index(str(path))
        self.dimension = self.index.d
        self.size = self.index.ntotal

        logger.info(
            f"Loaded index from {path} "
            f"(dimension={self.dimension}, size={self.size})"
        )

    def reset(self) -> None:
        """Reset index"""
        if self.index is not None:
            self.index.reset()
            self.size = 0
            logger.info("Index reset")

    def get_stats(self) -> dict:
        """Get index statistics

        Returns:
            Dictionary with index stats
        """
        return {
            "type": self.config.index_type,
            "metric": self.config.metric,
            "dimension": self.dimension,
            "size": self.size,
            "is_trained": self.index.is_trained if self.index else False,
        }


class IndexManager:
    """Manage vector indices with caching and persistence"""

    def __init__(self, config: Optional[IndexConfig] = None):
        """Initialize index manager

        Args:
            config: Index configuration
        """
        self.config = config or IndexConfig()
        self.index = VectorIndex(self.config)
        self.id_map: List[int] = []  # Map from index position to record ID

    def create(self, dimension: int) -> None:
        """Create index

        Args:
            dimension: Embedding dimension
        """
        self.index.create(dimension)
        self.id_map = []

    def add_embeddings(
        self, embeddings: np.ndarray, record_ids: Optional[List[int]] = None
    ) -> None:
        """Add embeddings to index

        Args:
            embeddings: Array of embeddings
            record_ids: Optional list of record IDs (default: sequential)
        """
        self.index.add(embeddings)

        if record_ids is None:
            record_ids = list(range(len(self.id_map), len(self.id_map) + len(embeddings)))

        self.id_map.extend(record_ids)

    def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> List[Tuple[int, float]]:
        """Search for similar records

        Args:
            query_embedding: Query embedding
            k: Number of results

        Returns:
            List of (record_id, distance) tuples
        """
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for idx, distance in zip(indices, distances):
            if idx >= 0:  # FAISS returns -1 for invalid results
                record_id = self.id_map[idx]
                results.append((record_id, float(distance)))

        return results

    def search_batch(
        self, query_embeddings: np.ndarray, k: int = 5
    ) -> List[List[Tuple[int, float]]]:
        """Search for similar records (batch)

        Args:
            query_embeddings: Query embeddings
            k: Number of results per query

        Returns:
            List of result lists, each containing (record_id, distance) tuples
        """
        distances, indices = self.index.search_batch(query_embeddings, k)

        all_results = []
        for query_distances, query_indices in zip(distances, indices):
            results = []
            for idx, distance in zip(query_indices, query_distances):
                if idx >= 0:
                    record_id = self.id_map[idx]
                    results.append((record_id, float(distance)))
            all_results.append(results)

        return all_results

    def save(self, index_path: Union[str, Path], id_map_path: Union[str, Path]) -> None:
        """Save index and ID map

        Args:
            index_path: Path to save index
            id_map_path: Path to save ID map
        """
        self.index.save(index_path)

        # Save ID map
        id_map_path = Path(id_map_path)
        id_map_path.parent.mkdir(parents=True, exist_ok=True)

        import pickle
        with open(id_map_path, "wb") as f:
            pickle.dump(self.id_map, f)

        logger.info(f"Saved ID map to {id_map_path}")

    def load(self, index_path: Union[str, Path], id_map_path: Union[str, Path]) -> None:
        """Load index and ID map

        Args:
            index_path: Path to index file
            id_map_path: Path to ID map file
        """
        self.index.load(index_path)

        # Load ID map
        id_map_path = Path(id_map_path)

        if not id_map_path.exists():
            raise FileNotFoundError(f"ID map file not found: {id_map_path}")

        import pickle
        with open(id_map_path, "rb") as f:
            self.id_map = pickle.load(f)

        logger.info(f"Loaded ID map from {id_map_path}")

    def get_stats(self) -> dict:
        """Get index statistics

        Returns:
            Dictionary with stats
        """
        stats = self.index.get_stats()
        stats["id_map_size"] = len(self.id_map)
        return stats
