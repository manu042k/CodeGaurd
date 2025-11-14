"""Vector store using HNSWlib for fast similarity search."""
import hnswlib
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger

from config import settings


class VectorStore:
    """Manages vector storage and similarity search using HNSWlib."""
    
    def __init__(self, dimension: int = None, index_path: str = None):
        self.dimension = dimension or settings.embedding_dimension
        self.index_path = index_path or settings.vector_index_path
        self.index = None
        self.current_id = 0
        self.max_elements = 1_000_000  # Can store up to 1M vectors
        
    def initialize(self, force_new: bool = False):
        """Initialize or load the HNSW index."""
        index_file = Path(self.index_path)
        
        if index_file.exists() and not force_new:
            logger.info(f"Loading existing vector index from {self.index_path}")
            self.load()
        else:
            logger.info(f"Creating new vector index with dimension {self.dimension}")
            self.index = hnswlib.Index(space='cosine', dim=self.dimension)
            self.index.init_index(
                max_elements=self.max_elements,
                ef_construction=200,  # Higher = better quality
                M=16  # Number of connections
            )
            self.index.set_ef(50)  # Higher = better search quality
            self.current_id = 0
    
    def add_vectors(self, vectors: np.ndarray, ids: Optional[List[int]] = None) -> List[int]:
        """Add vectors to the index."""
        if self.index is None:
            self.initialize()
        
        # Ensure vectors are 2D
        if len(vectors.shape) == 1:
            vectors = vectors.reshape(1, -1)
        
        num_vectors = vectors.shape[0]
        
        # Generate IDs if not provided
        if ids is None:
            ids = list(range(self.current_id, self.current_id + num_vectors))
            self.current_id += num_vectors
        
        # Add to index
        self.index.add_items(vectors, ids)
        logger.info(f"Added {num_vectors} vectors to index (IDs: {ids[0]}-{ids[-1]})")
        
        return ids
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for k nearest neighbors."""
        if self.index is None:
            raise ValueError("Index not initialized. Call initialize() first.")
        
        # Ensure query is 2D
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Search
        labels, distances = self.index.knn_query(query_vector, k=k)
        
        # Convert to lists
        ids = labels[0].tolist()
        scores = (1 - distances[0]).tolist()  # Convert distance to similarity
        
        return ids, scores
    
    def batch_search(self, query_vectors: np.ndarray, k: int = 10) -> Tuple[List[List[int]], List[List[float]]]:
        """Search for multiple queries."""
        if self.index is None:
            raise ValueError("Index not initialized. Call initialize() first.")
        
        labels, distances = self.index.knn_query(query_vectors, k=k)
        
        ids = labels.tolist()
        scores = (1 - distances).tolist()
        
        return ids, scores
    
    def save(self):
        """Save the index to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        # Ensure directory exists
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.index.save_index(self.index_path)
        logger.info(f"Vector index saved to {self.index_path}")
        
        # Save metadata
        metadata_path = str(self.index_path) + ".meta"
        with open(metadata_path, 'w') as f:
            f.write(f"{self.current_id}\n")
            f.write(f"{self.dimension}\n")
        logger.info(f"Saved {self.current_id} vectors")
    
    def load(self):
        """Load the index from disk."""
        if not Path(self.index_path).exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        
        # Load metadata
        metadata_path = str(self.index_path) + ".meta"
        if Path(metadata_path).exists():
            with open(metadata_path, 'r') as f:
                self.current_id = int(f.readline().strip())
                saved_dim = int(f.readline().strip())
                if saved_dim != self.dimension:
                    logger.warning(f"Dimension mismatch: expected {self.dimension}, got {saved_dim}")
                    self.dimension = saved_dim
        
        # Load index
        self.index = hnswlib.Index(space='cosine', dim=self.dimension)
        self.index.load_index(self.index_path, max_elements=self.max_elements)
        self.index.set_ef(50)
        
        logger.info(f"Loaded vector index with {self.current_id} vectors")
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        if self.index is None:
            return {"initialized": False}
        
        return {
            "initialized": True,
            "dimension": self.dimension,
            "total_vectors": self.current_id,
            "max_elements": self.max_elements,
        }
