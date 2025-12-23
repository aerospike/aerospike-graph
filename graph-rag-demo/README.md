# Graph RAG Demo with Aerospike Graph

A **Hybrid RAG** implementation that compares Vector-Only, Graph-Only, and Hybrid retrieval approaches.

## 🏗️ Architecture

```
Documents → Chunking → Entity Extraction → Dual Storage
                              ↓
                    ┌─────────┴─────────┐
                    ▼                   ▼
               Milvus Lite      Aerospike Graph
               (Vectors)         (Knowledge Graph)
                    │                   │
                    └─────────┬─────────┘
                              ▼
                      3-Way Comparison
                (Vector vs Graph vs Hybrid)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed flow diagrams.

## 🔧 Prerequisites

### 1. Aerospike Graph
Running on `localhost:8182`. Start with Docker:
```bash
# From the parent aerospike-graph directory
docker-compose up -d
```

### 2. Ollama (for embeddings)
```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull required model for embeddings
ollama pull nomic-embed-text

# Optional: Pull local LLM (if not using Claude)
ollama pull llama3.2
```

### 3. Claude API Key (recommended for better extraction)
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd graph-rag-demo
pip install -r requirements.txt

# Additional dependencies
pip install anthropic numpy
```

### 2. Test Connections
```bash
python test_connections.py
```

Expected output:
```
Testing Aerospike Graph connection...
✅ Connected to Aerospike Graph
Testing Ollama connection...
✅ Ollama is running
```

### 3. Ingest Documents
```bash
# Ingest FDA 2024 drug approval documents
python ingest_v3.py ./docs/fda_2024 --clear

# Or ingest synthetic company docs
python ingest_v3.py ./docs/acme_corp --clear
```

### 4. Run 3-Way Comparison
```bash
# Single question
python compare.py "What drugs has Eli Lilly approved?"

# Interactive mode
python compare.py
```

## 📊 Example Output

```
============================================================
COMPARING: What drugs has Eli Lilly approved?
============================================================

[1] VECTOR-ONLY RAG
  🔍 Vector search only...

[2] GRAPH-ONLY RAG
  🏷️  Extracting entities from question...
     Found: ['Eli Lilly']
  🕸️  Graph traversal...
     Found 4 entities, 8 chunks

[3] HYBRID RAG (Vector + Graph)
  🔍 Vector search...
  🕸️  Graph traversal...

======================================================================
📊 COMPARISON: Vector RAG vs Graph RAG vs Hybrid RAG
======================================================================
...
🏆 OVERALL WINNER: 🔀 Hybrid RAG
```

## 📁 Project Structure

```
graph-rag-demo/
├── ingest_v3.py          # Main ingestion script
├── compare.py            # 3-way RAG comparison
├── ask.py                # Simple Q&A interface
├── config.py             # Configuration (LLM, thresholds)
│
├── ingest/
│   ├── parser.py         # Document parsing (PDF/MD/TXT)
│   ├── chunker.py        # Text chunking
│   └── extractor_v3.py   # Entity extraction + resolution
│
├── storage/
│   ├── graph_store.py    # Aerospike Graph (Gremlin)
│   └── milvus_store.py   # Milvus Lite (vectors)
│
├── chat/
│   └── graph_qa_chain.py # 3-way RAG implementation
│
└── docs/                 # Test corpora
    ├── fda_2024/         # FDA drug approvals
    ├── acme_corp/        # Synthetic company docs
    └── shakespeare/      # Shakespeare plays
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# LLM Provider: "claude" (default) or "ollama"
LLM_PROVIDER = "claude"

# Chunking
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 150

# Entity resolution thresholds
ENTITY_SIMILARITY_THRESHOLD = 0.85
```

## 🧪 Test Corpora

| Corpus | Documents | Best For |
|--------|-----------|----------|
| `fda_2024/` | 10 | Cross-document entity queries |
| `acme_corp/` | 10 | Company/team/incident relationships |
| `shakespeare/` | 13 | Character analysis across plays |
| `papers/` | 10 | Academic citation networks |

## 📈 When Each Approach Wins

| Question Type | Best Approach |
|---------------|---------------|
| Abstract concepts | Vector/Hybrid |
| Specific named entities | Graph/Hybrid |
| Entity confusion risk | Graph (prevents hallucination) |
| Cross-document synthesis | Hybrid |

## 🔗 Related

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture diagrams
- [Aerospike Graph Documentation](https://docs.aerospike.com/graph)
- [Microsoft GraphRAG Paper](https://arxiv.org/abs/2404.16130)
