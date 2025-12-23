"""
Configuration for Graph RAG Demo
"""
import os

# Aerospike Graph connection
GRAPH_HOST = "localhost"
GRAPH_PORT = 8182

# =============================================================================
# LLM Provider Selection
# =============================================================================
# Options: "ollama" or "claude"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")

# Ollama configuration (local LLM)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # For entity extraction and Q&A
OLLAMA_EMBED_MODEL = "nomic-embed-text"  # For embeddings (768 dimensions)

# Claude configuration (Anthropic API)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # claude-sonnet-4-20250514 or claude-3-5-sonnet-20241022

# Chunking configuration
CHUNK_SIZE = 1500  # characters
CHUNK_OVERLAP = 150  # characters

# Entity resolution
ENTITY_SIMILARITY_THRESHOLD = 0.85  # Cosine similarity threshold for matching

# Milvus configuration (Phase 3)
MILVUS_DB_PATH = "./data/milvus_lite.db"
EMBEDDING_DIMENSION = 768  # nomic-embed-text dimension

