#!/bin/bash
cd /home/lyndon/github/aerospike-graph/graph-rag-mcp
export GREMLIN_HOST="${GREMLIN_HOST:-localhost}"
export GREMLIN_PORT="${GREMLIN_PORT:-8182}"
export PYTHONPATH="/home/lyndon/github/aerospike-graph/graph-rag-mcp:$PYTHONPATH"
exec python3 -m src.server
