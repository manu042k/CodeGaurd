"""Embedding generation using BGE models."""
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Union
from loguru import logger
import numpy as np

from config import settings


class CodeEmbedder:
    """Handles code embedding generation using BGE models."""
    
    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or settings.embedding_model
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.dimension = settings.embedding_dimension
        
        logger.info(f"Initializing embedder with model: {self.model_name}")
        logger.info(f"Using device: {self.device}")
    
    def load_model(self):
        """Load the embedding model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=settings.models_path
            )
            logger.info(f"Model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")
            self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if self.model is None:
            self.load_model()
        
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = None) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        if self.model is None:
            self.load_model()
        
        batch_size = batch_size or settings.batch_size
        
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        if self.model is None:
            self.load_model()
        return self.dimension


# Global embedder instance
_embedder = None


def get_embedder() -> CodeEmbedder:
    """Get or create global embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = CodeEmbedder()
    return _embedder
