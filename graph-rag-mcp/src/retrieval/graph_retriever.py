"""
Gremlin-based graph retriever.

Implements all 6 retrieval strategies using graph traversals
against the code knowledge graph in Aerospike Graph.
"""

from __future__ import annotations

import logging
from typing import Any

from gremlin_python.process.graph_traversal import GraphTraversalSource, __
from gremlin_python.process.traversal import P, T, TextP, Column

from src.graph.schema import VertexLabel, EdgeLabel, Property
from src.retrieval.base import Retriever, RetrievalResult

log = logging.getLogger(__name__)

LABEL_MAP = {
    "class": VertexLabel.CLASS,
    "function": VertexLabel.FUNCTION,
    "file": VertexLabel.FILE,
    "module": VertexLabel.MODULE,
    "doc": VertexLabel.DOC_SECTION,
    "repository": VertexLabel.REPOSITORY,
}


def _get_id(v: dict) -> str:
    """element_map() keys the ID under T.id and label under T.label."""
    return str(v.get(T.id, v.get("id", "")))


def _get_label(v: dict) -> str:
    return str(v.get(T.label, v.get("label", "")))


def _vertex_to_result(v: dict[str, Any]) -> RetrievalResult:
    skip = {T.id, T.label, "id", "label"}
    props = {k: val for k, val in v.items() if k not in skip}
    return RetrievalResult(
        entity_id=_get_id(v),
        label=_get_label(v),
        name=str(props.get(Property.NAME, "")),
        qualified_name=str(props.get(Property.QUALIFIED_NAME, "")),
        path=str(props.get(Property.PATH, "")),
        properties=props,
    )


class GraphRetriever(Retriever):
    def __init__(self, g: GraphTraversalSource):
        self._g = g

    def search(
        self,
        query: str,
        tenant_id: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        """Keyword search across vertex names, qualified names, docstrings, and content."""
        t = self._g.V().has(Property.TENANT_ID, tenant_id)

        if entity_type and entity_type.lower() in LABEL_MAP:
            t = t.has_label(LABEL_MAP[entity_type.lower()])

        query_lower = query.lower()
        t = t.or_(
            __.has(Property.NAME, TextP.containing(query)),
            __.has(Property.QUALIFIED_NAME, TextP.containing(query)),
            __.has(Property.DOCSTRING, TextP.containing(query_lower)),
            __.has(Property.TITLE, TextP.containing(query)),
            __.has(Property.CONTENT, TextP.containing(query_lower)),
            __.has(Property.SIGNATURE, TextP.containing(query)),
        )

        vertices = t.limit(limit).element_map().to_list()
        results = [_vertex_to_result(v) for v in vertices]

        for r in results:
            r.relationships = self._get_direct_relationships(r.entity_id)

        return results

    def get_dependencies(
        self,
        entity_name: str,
        tenant_id: str,
        direction: str = "both",
        depth: int = 2,
    ) -> list[RetrievalResult]:
        """Traverse imports/calls/inherits edges to find dependencies."""
        start = self._find_entity(entity_name, tenant_id)
        if not start:
            return []

        dep_edges = [EdgeLabel.IMPORTS, EdgeLabel.CALLS, EdgeLabel.INHERITS]
        results: list[RetrievalResult] = [start]

        if direction in ("out", "both"):
            t = self._g.V(start.entity_id)
            for _ in range(depth):
                t = t.out(*dep_edges)
            t = t.has(Property.TENANT_ID, tenant_id).dedup()
            for v in t.element_map().to_list():
                results.append(_vertex_to_result(v))

        if direction in ("in", "both"):
            t = self._g.V(start.entity_id)
            for _ in range(depth):
                t = t.in_(*dep_edges)
            t = t.has(Property.TENANT_ID, tenant_id).dedup()
            for v in t.element_map().to_list():
                results.append(_vertex_to_result(v))

        return results

    def get_file_context(
        self,
        file_path: str,
        tenant_id: str,
    ) -> list[RetrievalResult]:
        """Get all entities contained in a file and their relationships."""
        files = (
            self._g.V()
            .has(Property.TENANT_ID, tenant_id)
            .has_label(VertexLabel.FILE)
            .has(Property.PATH, TextP.containing(file_path))
            .element_map()
            .to_list()
        )

        if not files:
            return []

        results: list[RetrievalResult] = []
        for f in files:
            file_result = _vertex_to_result(f)
            results.append(file_result)

            children = (
                self._g.V(_get_id(f))
                .in_(EdgeLabel.CONTAINS)
                .has(Property.TENANT_ID, tenant_id)
                .element_map()
                .to_list()
            )
            for child in children:
                r = _vertex_to_result(child)
                r.relationships = self._get_direct_relationships(r.entity_id)
                results.append(r)

        return results

    def get_architecture(
        self,
        tenant_id: str,
        module: str | None = None,
    ) -> list[RetrievalResult]:
        """Return the file/module structure and cross-module dependencies."""
        t = (
            self._g.V()
            .has(Property.TENANT_ID, tenant_id)
            .has_label(VertexLabel.FILE)
        )

        if module:
            t = t.has(Property.PATH, TextP.containing(module))

        files = t.element_map().to_list()
        results: list[RetrievalResult] = []
        for f in files:
            r = _vertex_to_result(f)
            imports = (
                self._g.V(_get_id(f))
                .out(EdgeLabel.IMPORTS)
                .has(Property.TENANT_ID, tenant_id)
                .element_map()
                .to_list()
            )
            r.relationships = [
                {
                    "edge": EdgeLabel.IMPORTS,
                    "target": str(imp.get(Property.QUALIFIED_NAME, imp.get(Property.PATH, _get_id(imp)))),
                }
                for imp in imports
            ]
            results.append(r)

        return results

    def get_call_graph(
        self,
        function_name: str,
        tenant_id: str,
        depth: int = 3,
    ) -> list[RetrievalResult]:
        """Trace call chains from a function."""
        start = self._find_entity(function_name, tenant_id)
        if not start:
            return []

        results: list[RetrievalResult] = [start]
        visited = {start.entity_id}

        frontier = [start.entity_id]
        for _ in range(depth):
            if not frontier:
                break
            next_frontier = []
            for vid in frontier:
                callees = (
                    self._g.V(vid)
                    .out(EdgeLabel.CALLS)
                    .has(Property.TENANT_ID, tenant_id)
                    .dedup()
                    .element_map()
                    .to_list()
                )
                for v in callees:
                    r = _vertex_to_result(v)
                    if r.entity_id not in visited:
                        visited.add(r.entity_id)
                        results.append(r)
                        next_frontier.append(r.entity_id)
            frontier = next_frontier

        return results

    def get_related(
        self,
        entity_name: str,
        tenant_id: str,
        limit: int = 20,
    ) -> list[RetrievalResult]:
        """Find entities related by any edge type."""
        start = self._find_entity(entity_name, tenant_id)
        if not start:
            return []

        results: list[RetrievalResult] = [start]

        neighbors = (
            self._g.V(start.entity_id)
            .both_e()
            .where(__.other_v().has(Property.TENANT_ID, tenant_id))
            .project("edge_label", "other")
            .by(__.label())
            .by(__.other_v().element_map())
            .to_list()
        )

        seen = {start.entity_id}
        for n in neighbors[:limit]:
            v = n["other"]
            r = _vertex_to_result(v)
            if r.entity_id not in seen:
                seen.add(r.entity_id)
                r.relationships = [{"edge": n["edge_label"], "target": start.name}]
                results.append(r)

        return results

    def _find_entity(self, name: str, tenant_id: str) -> RetrievalResult | None:
        candidates = (
            self._g.V()
            .has(Property.TENANT_ID, tenant_id)
            .or_(
                __.has(Property.NAME, name),
                __.has(Property.QUALIFIED_NAME, name),
                __.has(Property.QUALIFIED_NAME, TextP.containing(name)),
            )
            .limit(1)
            .element_map()
            .to_list()
        )
        if candidates:
            return _vertex_to_result(candidates[0])
        return None

    def _get_direct_relationships(self, vid: str) -> list[dict[str, str]]:
        edges = (
            self._g.V(vid)
            .both_e()
            .project("edge_label", "direction", "other_name")
            .by(__.label())
            .by(
                __.choose(
                    __.out_v().has_id(vid),
                    __.constant("out"),
                    __.constant("in"),
                )
            )
            .by(
                __.other_v().coalesce(
                    __.values(Property.QUALIFIED_NAME),
                    __.values(Property.NAME),
                    __.values(Property.PATH),
                    __.id_(),
                )
            )
            .to_list()
        )
        return [
            {
                "edge": f"{e['direction']}:{e['edge_label']}",
                "target": str(e["other_name"]),
            }
            for e in edges[:10]
        ]
