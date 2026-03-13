"""
Combines results from multiple retrievers, deduplicating by entity ID
and merging scores.
"""

from __future__ import annotations

from src.retrieval.base import Retriever, RetrievalResult


class CombinedRetriever(Retriever):
    """Delegates to multiple retrievers and merges results."""

    def __init__(self, retrievers: list[Retriever]):
        self._retrievers = retrievers

    def _merge(self, result_lists: list[list[RetrievalResult]], limit: int) -> list[RetrievalResult]:
        seen: dict[str, RetrievalResult] = {}
        for results in result_lists:
            for r in results:
                if r.entity_id in seen:
                    existing = seen[r.entity_id]
                    existing.score = max(existing.score, r.score)
                    for rel in r.relationships:
                        if rel not in existing.relationships:
                            existing.relationships.append(rel)
                else:
                    seen[r.entity_id] = r
        merged = sorted(seen.values(), key=lambda r: r.score, reverse=True)
        return merged[:limit]

    def search(self, query, tenant_id, entity_type=None, limit=10):
        return self._merge(
            [r.search(query, tenant_id, entity_type, limit) for r in self._retrievers],
            limit,
        )

    def get_dependencies(self, entity_name, tenant_id, direction="both", depth=2):
        return self._merge(
            [r.get_dependencies(entity_name, tenant_id, direction, depth) for r in self._retrievers],
            limit=50,
        )

    def get_file_context(self, file_path, tenant_id):
        return self._merge(
            [r.get_file_context(file_path, tenant_id) for r in self._retrievers],
            limit=100,
        )

    def get_architecture(self, tenant_id, module=None):
        return self._merge(
            [r.get_architecture(tenant_id, module) for r in self._retrievers],
            limit=100,
        )

    def get_call_graph(self, function_name, tenant_id, depth=3):
        return self._merge(
            [r.get_call_graph(function_name, tenant_id, depth) for r in self._retrievers],
            limit=50,
        )

    def get_related(self, entity_name, tenant_id, limit=20):
        return self._merge(
            [r.get_related(entity_name, tenant_id, limit) for r in self._retrievers],
            limit,
        )
