"""
Phase 3: Ollama Embeddings

Generates vector embeddings using Ollama's embedding models.
"""

import sys
import os
import requests
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class OllamaEmbeddings:
    """
    Wrapper for Ollama embedding API.
    
    Uses nomic-embed-text by default (768 dimensions).
    """
    
    def __init__(
        self, 
        base_url: str = None, 
        model: str = None,
        timeout: int = 60
    ):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_EMBED_MODEL
        self.timeout = timeout
        self._dimension = None
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension (cached after first call)"""
        if self._dimension is None:
            # Get dimension by embedding a test string
            test_embedding = self.embed("test")
            self._dimension = len(test_embedding)
        return self._dimension
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["embedding"]
    
    def embed_batch(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            show_progress: Whether to print progress
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(texts)
        
        for i, text in enumerate(texts):
            if show_progress and (i + 1) % 10 == 0:
                print(f"  Embedding {i + 1}/{total}...")
            
            embedding = self.embed(text)
            embeddings.append(embedding)
        
        if show_progress:
            print(f"  ✅ Generated {total} embeddings")
        
        return embeddings


# Singleton instance for convenience
_embeddings_instance: Optional[OllamaEmbeddings] = None


def get_embeddings() -> OllamaEmbeddings:
    """Get or create the embeddings instance"""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = OllamaEmbeddings()
    return _embeddings_instance


def embed_text(text: str) -> List[float]:
    """Convenience function to embed a single text"""
    return get_embeddings().embed(text)


def embed_texts(texts: List[str], show_progress: bool = True) -> List[List[float]]:
    """Convenience function to embed multiple texts"""
    return get_embeddings().embed_batch(texts, show_progress)


if __name__ == "__main__":
    # Quick test
    print("Testing Ollama Embeddings...")
    print(f"Model: {config.OLLAMA_EMBED_MODEL}")
    print(f"Expected dimension: {config.EMBEDDING_DIMENSION}")
    
    embedder = OllamaEmbeddings()
    
    # Test single embedding
    test_text = "Aerospike Graph is a high-performance graph database."
    embedding = embedder.embed(test_text)
    
    print(f"\nTest text: '{test_text}'")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
    # Test batch embedding
    print("\nTesting batch embedding...")
    texts = [
        "Graph databases store nodes and edges.",
        "Vector search finds similar items.",
        "Knowledge graphs connect entities."
    ]
    embeddings = embedder.embed_batch(texts)
    print(f"Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")

