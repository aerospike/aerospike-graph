# Graph RAG Learnings & Gotchas

Key insights discovered while building the Graph RAG demo.

---

## 1. LLM Temperature Matters for Output Determinism

**Problem:** Running the same query multiple times produced different results, making it hard to compare RAG approaches fairly.

**Solution:** Set `temperature=0` for deterministic, reproducible outputs.

```python
response = requests.post(
    f"{base_url}/api/generate",
    json={
        "model": model,
        "prompt": prompt,
        "options": {"temperature": 0}  # Deterministic output
    }
)
```

**Why it matters:**
- Temperature controls randomness in token selection
- `temperature=0` → always picks the most probable token (deterministic)
- `temperature>0` → introduces randomness (creative but inconsistent)
- For RAG evaluation/comparison, determinism is essential

---

## 2. Prompt Complexity Must Match Model Capability

**Problem:** The Microsoft GraphRAG prompt with tuple delimiters (`<|>`, `##`, `<|COMPLETE|>`) caused llama3.2 to generate Python code instead of the expected output format.

**Solution:** Simplify prompts for smaller/local models like Ollama's llama3.2.

### ❌ Too Complex for Small Models (MS GraphRAG Original)
```
Format each entity as ("entity"<|>NAME<|>TYPE<|>DESCRIPTION)
Use **##** as the list delimiter.
When finished, output <|COMPLETE|>
```

### ✅ Works with Ollama/Small Models
```
For each entity, output: ENTITY: Name | Type | Description
For each relationship, output: RELATIONSHIP: Source | Target | How related | Strength
```

**Key insight:** 
- **OpenAI GPT-4/Claude** → Can handle complex structured prompts with custom delimiters
- **Ollama/llama3.2** → Needs simpler, more direct instructions
- The "intelligence" of the model determines how sophisticated your prompts can be

---

## 3. Avoid Example Bias in Discovery Prompts

**Problem:** Providing domain-specific examples in ontology discovery prompts caused the LLM to copy those examples instead of analyzing the actual document.

### ❌ Biased Prompt (LLM copies examples)
```
Identify entity types. Examples by domain:
- Finance: FeeType, AccountStatus, InterestRate
- Research: Researcher, Institution, Algorithm
- Corporate: Employee, Department, Product
```

### ✅ Open-Ended Prompt (LLM discovers from content)
```
Read this text and identify what TYPES of things are mentioned.
Think about:
- What kinds of people, roles, or actors appear?
- What kinds of objects, items, or artifacts are discussed?
- What processes, events, or actions occur?
- What concepts, rules, or conditions are described?
```

**Key insight:**
- Examples anchor the LLM's thinking to those specific patterns
- For true ontology discovery, ask "what's IN the text" not "what SHOULD be there"
- Guide the LLM's analysis process, not its output vocabulary

---

## 4. Multi-Document Ontology Must Be Additive

**Problem:** When processing multiple documents, discovering ontology from only the first document misses entity types unique to other documents.

**Solution:** Accumulate entity types across ALL documents, then reconcile related types.

### Process:
```
Doc A: Product, Person, Team         → 3 types
Doc B: ProductSpec, Architecture     → 5 types (additive)
Doc C: Customer, Contract            → 7 types (additive)
```

### Type Reconciliation:
After accumulating types, use LLM to identify relationships:
- **SAME_AS**: Product ↔ Artifact (equivalent concepts)
- **IS_TYPE_OF**: ProductSpec → Product (specialization)

### Cross-Type Relationships:
Entities of related types should be connected:
```
If Product.SAME_AS.Artifact:
  Connect all Product entities to related Artifact entities
```

**Key insight:**
- Single-document ontology discovery misses cross-document concepts
- Type reconciliation enables connecting related entities across documents
- This is critical for Graph RAG to find multi-hop relationships

---

*Add more learnings as we discover them...*

