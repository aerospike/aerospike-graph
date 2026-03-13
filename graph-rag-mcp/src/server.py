"""
FastMCP server exposing the Graph RAG retrieval tools for Cursor.

Run with:
    python -m src.server              # stdio (for Cursor)
    python -m src.server --http 8000  # HTTP (for testing)
"""

from __future__ import annotations

import argparse
import logging
import sys

from fastmcp import FastMCP

from src.config import GremlinConfig, ServerConfig
from src.graph.connection import GremlinConnection
from src.retrieval.graph_retriever import GraphRetriever

log = logging.getLogger(__name__)

mcp = FastMCP(
    "Graph RAG",
    instructions=(
        "Code knowledge graph backed by Aerospike Graph. "
        "Use these tools to search code, explore dependencies, "
        "understand architecture, and trace call graphs across "
        "ingested codebases."
    ),
)

_conn: GremlinConnection | None = None
_retriever: GraphRetriever | None = None


def _get_retriever() -> GraphRetriever:
    global _conn, _retriever
    if _retriever is None:
        config = GremlinConfig.from_env()
        _conn = GremlinConnection(config)
        _retriever = GraphRetriever(_conn.connect())
    return _retriever


@mcp.tool
def search_code(
    query: str,
    tenant: str,
    entity_type: str | None = None,
    limit: int = 10,
) -> str:
    """Search code entities by keyword across names, signatures, docstrings.

    Args:
        query: Search term (class name, function name, keyword, etc.)
        tenant: Tenant/codebase identifier (e.g. "aerospike-graph-examples")
        entity_type: Filter by type: "class", "function", "file", "doc" (optional)
        limit: Max results to return
    """
    retriever = _get_retriever()
    results = retriever.search(query, tenant, entity_type, limit)
    if not results:
        return f"No results found for '{query}' in tenant '{tenant}'"
    return _format_results(results)


@mcp.tool
def get_dependencies(
    entity_name: str,
    tenant: str,
    direction: str = "both",
    depth: int = 2,
) -> str:
    """Find what an entity depends on or what depends on it.

    Traverses import, call, and inheritance edges in the code graph.

    Args:
        entity_name: Name or qualified name of the entity
        tenant: Tenant/codebase identifier
        direction: "out" (what it depends on), "in" (what depends on it), or "both"
        depth: How many hops to traverse (default 2)
    """
    retriever = _get_retriever()
    results = retriever.get_dependencies(entity_name, tenant, direction, depth)
    if not results:
        return f"No entity named '{entity_name}' found in tenant '{tenant}'"
    return _format_results(results)


@mcp.tool
def get_file_context(
    file_path: str,
    tenant: str,
) -> str:
    """Get all entities in a file and their relationships.

    Args:
        file_path: Full or partial file path to look up
        tenant: Tenant/codebase identifier
    """
    retriever = _get_retriever()
    results = retriever.get_file_context(file_path, tenant)
    if not results:
        return f"No file matching '{file_path}' found in tenant '{tenant}'"
    return _format_results(results)


@mcp.tool
def get_architecture(
    tenant: str,
    module: str | None = None,
) -> str:
    """Return module/file structure and cross-module dependencies.

    Args:
        tenant: Tenant/codebase identifier
        module: Filter to a specific module/directory path (optional)
    """
    retriever = _get_retriever()
    results = retriever.get_architecture(tenant, module)
    if not results:
        return f"No architecture data found for tenant '{tenant}'"
    return _format_results(results)


@mcp.tool
def get_call_graph(
    function_name: str,
    tenant: str,
    depth: int = 3,
) -> str:
    """Trace call chains starting from a function.

    Args:
        function_name: Name or qualified name of the function
        tenant: Tenant/codebase identifier
        depth: How many levels of calls to trace (default 3)
    """
    retriever = _get_retriever()
    results = retriever.get_call_graph(function_name, tenant, depth)
    if not results:
        return f"No function named '{function_name}' found in tenant '{tenant}'"
    return _format_results(results)


@mcp.tool
def get_related(
    entity_name: str,
    tenant: str,
    limit: int = 20,
) -> str:
    """Find entities related to a given entity by any relationship type.

    Includes imports, calls, inheritance, containment, etc.

    Args:
        entity_name: Name or qualified name of the entity
        tenant: Tenant/codebase identifier
        limit: Max related entities to return
    """
    retriever = _get_retriever()
    results = retriever.get_related(entity_name, tenant, limit)
    if not results:
        return f"No entity named '{entity_name}' found in tenant '{tenant}'"
    return _format_results(results)


def _format_results(results: list) -> str:
    parts = []
    for r in results:
        parts.append(r.to_context_string())
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Graph RAG MCP Server")
    parser.add_argument("--http", type=int, default=None, help="Run as HTTP server on this port")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    )

    if args.http:
        mcp.run(transport="http", port=args.http)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
