# Graph RAG MCP Server

Multi-tenant Graph RAG system backed by Aerospike Graph, exposed as an MCP server for Cursor IDE.

## Architecture

- **Ingestion**: tree-sitter parses code (Python, Java, JS), markdown parser handles docs
- **Storage**: Aerospike Graph via Gremlin -- vertices for code entities, edges for relationships
- **Retrieval**: Gremlin traversals for keyword search, dependency analysis, call graphs
- **MCP Server**: FastMCP exposes 6 tools that Cursor can call during tasks

## Quick Start

### Prerequisites

- Python 3.10+
- Aerospike Graph Service running locally (port 8182)

### Install

```bash
cd /home/lyndon/github/aerospike-graph/graph-rag-mcp
pip install -e .
```

### Ingest a codebase

```bash
python -m src.ingestion.ingest \
    --tenant-id aerospike-graph-examples \
    --name "Aerospike Graph Examples" \
    --root /home/lyndon/github/aerospike-graph \
    --languages python java javascript \
    -v
```

### Run the MCP server

```bash
# stdio mode (for Cursor)
python -m src.server

# HTTP mode (for testing)
python -m src.server --http 8000
```

### Configure Cursor

Copy `.cursor/mcp.json` to any project where you want Graph RAG context,
or use the global config at `~/.cursor/mcp.json`.

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_code` | Keyword search across code entity names, signatures, docstrings |
| `get_dependencies` | Traverse imports/calls/inheritance to find dependency chains |
| `get_file_context` | Get all entities in a file and their relationships |
| `get_architecture` | Module/file structure and cross-module dependencies |
| `get_call_graph` | Trace call chains from a function |
| `get_related` | Find entities related by any edge type |

## Multi-Tenancy

Each codebase is a "tenant" with a unique ID. All graph queries are scoped
to a tenant, so multiple codebases coexist in one Aerospike Graph instance.

## Future: Vector Search

The retriever interface is designed for hybrid retrieval. To add semantic search:

1. Install: `pip install -e ".[vector]"`
2. Implement `src/retrieval/vector_retriever.py` with Aerospike Vector Search
3. Register it alongside the graph retriever in the combiner
