"""
Stub for future Aerospike Vector Search retriever.

When implementing:
1. pip install aerospike-vector-search
2. During ingestion, generate embeddings via a configurable provider
   (OpenAI, sentence-transformers, etc.) and store them in AVS
3. Implement the Retriever interface methods using vector similarity search
4. Register this retriever alongside GraphRetriever in the CombinedRetriever
"""

from __future__ import annotations

from src.retrieval.base import Retriever, RetrievalResult


class VectorRetriever(Retriever):
    """Placeholder -- not yet implemented."""

    def __init__(self, **kwargs):
        raise NotImplementedError(
            "Vector retriever is not yet implemented. "
            "Install 'graph-rag-mcp[vector]' and implement this class "
            "to enable semantic search via Aerospike Vector Search."
        )

    def search(self, query, tenant_id, entity_type=None, limit=10):
        raise NotImplementedError

    def get_dependencies(self, entity_name, tenant_id, direction="both", depth=2):
        raise NotImplementedError

    def get_file_context(self, file_path, tenant_id):
        raise NotImplementedError

    def get_architecture(self, tenant_id, module=None):
        raise NotImplementedError

    def get_call_graph(self, function_name, tenant_id, depth=3):
        raise NotImplementedError

    def get_related(self, entity_name, tenant_id, limit=20):
        raise NotImplementedError
