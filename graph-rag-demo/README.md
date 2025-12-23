# Graph RAG Demo with Aerospike Graph

A step-by-step Graph RAG implementation using:
- **Aerospike Graph** - Knowledge graph storage (Gremlin)
- **Milvus Lite** - Vector similarity search
- **Ollama** - Local LLM for extraction and Q&A

## Prerequisites

1. **Aerospike Graph** running on `localhost:8182`
2. **Ollama** running with required models:
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test connectivity (Phase 1)
python test_connections.py
```

## Build Phases

| Phase | Script | Description |
|-------|--------|-------------|
| 1 | `test_connections.py` | Verify Aerospike Graph + Ollama |
| 2 | TBD | Document chunking + graph storage |
| 3 | TBD | Milvus + embeddings |
| 4 | TBD | Basic Q&A |
| 5+ | TBD | Entity extraction, resolution, UI |

## Current Status

**Phase 1** - Testing connectivity

