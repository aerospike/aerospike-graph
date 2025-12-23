"""
Phase 5: Graph-Enhanced Q&A Chain

Combines vector search with graph traversal for better answers.
Also provides comparison mode to show difference between vector-only and graph-enhanced.
"""

import sys
import os
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from gremlin_python.process.traversal import T

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from storage.milvus_store import MilvusStore
from storage.graph_store import GraphStore
from retrieval.embeddings import OllamaEmbeddings


@dataclass
class GraphQAResult:
    """Result from a Graph RAG query"""
    question: str
    answer: str
    vector_chunks: List[Dict[str, Any]]  # Chunks from vector search
    graph_entities: List[Dict[str, Any]]  # Entities found via graph
    graph_chunks: List[Dict[str, Any]]  # Additional chunks from graph traversal
    method: str  # "vector_only" or "graph_enhanced"


class GraphQAChain:
    """
    Graph-enhanced Q&A chain.
    
    Combines:
    1. Vector search for similar chunks (like Phase 4)
    2. Entity extraction from query
    3. Graph traversal to find related entities and chunks
    """
    
    SYSTEM_PROMPT = """You are a helpful assistant that analyzes documents. Answer questions by synthesizing information from the provided context.

Guidelines:
1. Prioritize information from the context - quote and cite specific passages
2. Synthesize across multiple document sections when relevant
3. Be thorough - extract all relevant details from the context
4. Cite sources: mention which document each point comes from
5. If context is limited, work with what's available and note any gaps"""

    ANSWER_PROMPT = """CONTEXT FROM DOCUMENTS:

{context}

---

QUESTION: {question}

Analyze the context above and provide a comprehensive answer. Quote relevant passages and cite which document they come from. Synthesize information across all available sections:"""

    # Prompt to extract entities from a question
    ENTITY_EXTRACT_PROMPT = """Extract the key nouns and concepts from this question that could be used to search a knowledge graph.

Question: {question}

Extract:
- Important nouns (people, places, things, concepts)
- Technical terms
- Subjects being asked about

Return ONLY a JSON array of strings, like: ["parents", "children", "AI"]

Key entities:"""

    def __init__(
        self,
        milvus_store: MilvusStore = None,
        graph_store: GraphStore = None,
        embedder: OllamaEmbeddings = None,
        llm_model: str = None,
        top_k: int = 5,
        min_score: float = 0.45
    ):
        self.milvus_store = milvus_store
        self.graph_store = graph_store
        self.embedder = embedder or OllamaEmbeddings()
        self.llm_model = llm_model or config.OLLAMA_MODEL
        self.llm_base_url = config.OLLAMA_BASE_URL
        self.top_k = top_k
        self.min_score = min_score
        
        self._owns_milvus = milvus_store is None
        self._owns_graph = graph_store is None
    
    def connect(self):
        """Connect to stores if not provided"""
        if self._owns_milvus:
            self.milvus_store = MilvusStore()
            self.milvus_store.connect()
        if self._owns_graph:
            self.graph_store = GraphStore()
            self.graph_store.connect()
    
    def close(self):
        """Close connections if we own them"""
        if self._owns_milvus and self.milvus_store:
            self.milvus_store.close()
        if self._owns_graph and self.graph_store:
            self.graph_store.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _vector_search(self, question: str) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        question_embedding = self.embedder.embed(question)
        
        results = self.milvus_store.search(
            query_embedding=question_embedding,
            top_k=self.top_k * 2
        )
        
        # Filter by minimum score
        filtered = [r for r in results if r['distance'] >= self.min_score]
        return filtered[:self.top_k]
    
    def _extract_query_entities(self, question: str) -> List[str]:
        """Extract entity names from the question using LLM"""
        try:
            response = requests.post(
                f"{self.llm_base_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": self.ENTITY_EXTRACT_PROMPT.format(question=question),
                    "stream": False,
                    "options": {"temperature": 0}
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()["response"].strip()
            
            # Parse JSON array
            import json
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > 0:
                entities = json.loads(result[start:end])
                return [e for e in entities if isinstance(e, str)]
            return []
            
        except Exception as e:
            print(f"  ⚠️ Entity extraction error: {e}")
            return []
    
    def _graph_search(self, entity_names: List[str], question: str = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Search graph for entities and related chunks.
        
        Args:
            entity_names: List of entity names to search for
            question: Optional question for future relevance filtering
        
        Returns:
            Tuple of (entities_found, chunks_from_graph)
        """
        entities_found = []
        chunks_from_graph = []
        seen_chunk_ids = set()
        seen_entity_names = set()
        
        # Allocate chunks per query entity to ensure all get represented
        MAX_ENTITIES = 15
        CHUNKS_PER_QUERY_ENTITY = 5  # Ensure each query entity gets some chunks
        MAX_TOTAL_CHUNKS = 20
        
        # Filter out generic terms
        valid_names = [name for name in entity_names 
                       if name.lower() not in ['shakespeare', 'play', 'act', 'scene', 'character', 'the']]
        
        # PASS 1: Get chunks for each query entity (ensure all are represented)
        for name in valid_names:
            search_results = self.graph_store.search_entities(name)
            
            chunks_for_this_entity = 0
            for entity in search_results[:2]:  # Top 2 matches per query
                entity_name = entity.get('name', [''])[0] if isinstance(entity.get('name'), list) else entity.get('name', '')
                
                if entity_name.lower() in seen_entity_names:
                    continue
                seen_entity_names.add(entity_name.lower())
                entities_found.append(entity)
                
                # Get chunks for this entity
                chunks = self.graph_store.get_chunks_mentioning_entity(entity_name)
                for chunk in chunks[:CHUNKS_PER_QUERY_ENTITY]:
                    if chunks_for_this_entity >= CHUNKS_PER_QUERY_ENTITY:
                        break
                    chunk_id = chunk.get(T.id, chunk.get('id', ''))
                    if chunk_id and chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(chunk_id)
                        chunks_from_graph.append(chunk)
                        chunks_for_this_entity += 1
        
        # PASS 2: Get related entities and their chunks (if space remains)
        for name in valid_names[:2]:  # Only first 2 query entities
            if len(entities_found) >= MAX_ENTITIES:
                break
            if len(chunks_from_graph) >= MAX_TOTAL_CHUNKS:
                break
                
            search_results = self.graph_store.search_entities(name)
            for entity in search_results[:1]:  # Top match only
                entity_name = entity.get('name', [''])[0] if isinstance(entity.get('name'), list) else entity.get('name', '')
                
                related = self.graph_store.get_related_entities(entity_name, max_hops=1)
                for rel_entity in related[:2]:
                    if len(entities_found) >= MAX_ENTITIES:
                        break
                        
                    rel_name = rel_entity.get('name', [''])[0] if isinstance(rel_entity.get('name'), list) else rel_entity.get('name', '')
                    
                    if rel_name.lower() in seen_entity_names:
                        continue
                    seen_entity_names.add(rel_name.lower())
                    entities_found.append(rel_entity)
                    
                    # Get a couple chunks for related entities
                    if len(chunks_from_graph) < MAX_TOTAL_CHUNKS:
                        rel_chunks = self.graph_store.get_chunks_mentioning_entity(rel_name)
                        for chunk in rel_chunks[:2]:
                            if len(chunks_from_graph) >= MAX_TOTAL_CHUNKS:
                                break
                            chunk_id = chunk.get(T.id, chunk.get('id', ''))
                            if chunk_id and chunk_id not in seen_chunk_ids:
                                seen_chunk_ids.add(chunk_id)
                                chunks_from_graph.append(chunk)
        
        return entities_found, chunks_from_graph
    
    def _build_context(
        self, 
        vector_chunks: List[Dict], 
        graph_entities: List[Dict] = None,
        graph_chunks: List[Dict] = None
    ) -> str:
        """Build context string from chunks and entities"""
        context_parts = []
        
        # Add vector search chunks
        if vector_chunks:
            context_parts.append("=== RELEVANT TEXT CHUNKS ===")
            for i, chunk in enumerate(vector_chunks):
                header = f"[Document: {chunk['doc_id']}, Section {chunk.get('position', i) + 1}]"
                context_parts.append(f"{header}\n{chunk['text']}")
        
        # Add graph entities (if any)
        if graph_entities:
            context_parts.append("\n=== RELATED ENTITIES FROM KNOWLEDGE GRAPH ===")
            for entity in graph_entities:
                name = entity.get('name', ['Unknown'])[0] if isinstance(entity.get('name'), list) else entity.get('name', 'Unknown')
                etype = entity.get('entity_type', [''])[0] if isinstance(entity.get('entity_type'), list) else entity.get('entity_type', '')
                desc = entity.get('description', [''])[0] if isinstance(entity.get('description'), list) else entity.get('description', '')
                context_parts.append(f"- {name} ({etype}): {desc}")
        
        # Add graph chunks (additional context) - these provide cross-document insights
        if graph_chunks:
            context_parts.append("\n=== ADDITIONAL CONTEXT FROM KNOWLEDGE GRAPH ===")
            # Use more chunks but summarize them better
            for i, chunk in enumerate(graph_chunks[:8]):  # Increased from 3 to 8
                text = chunk.get('text', [''])[0] if isinstance(chunk.get('text'), list) else chunk.get('text', '')
                doc_id = chunk.get('doc_id', [''])[0] if isinstance(chunk.get('doc_id'), list) else chunk.get('doc_id', 'Unknown')
                if text:
                    # Truncate but keep more text for better context
                    context_parts.append(f"[From {doc_id}]\n{text[:800]}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Ollama LLM"""
        prompt = self.ANSWER_PROMPT.format(
            context=context,
            question=question
        )
        
        response = requests.post(
            f"{self.llm_base_url}/api/generate",
            json={
                "model": self.llm_model,
                "prompt": prompt,
                "system": self.SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_ctx": 4096
                }
            },
            timeout=120
        )
        response.raise_for_status()
        
        return response.json()["response"].strip()
    
    def ask_vector_only(self, question: str, verbose: bool = False) -> GraphQAResult:
        """Answer using ONLY vector search (no graph)"""
        if verbose:
            print("  🔍 Vector search only...")
        
        vector_chunks = self._vector_search(question)
        
        if not vector_chunks:
            return GraphQAResult(
                question=question,
                answer="I couldn't find any relevant information.",
                vector_chunks=[],
                graph_entities=[],
                graph_chunks=[],
                method="vector_only"
            )
        
        context = self._build_context(vector_chunks)
        answer = self._generate_answer(question, context)
        
        return GraphQAResult(
            question=question,
            answer=answer,
            vector_chunks=vector_chunks,
            graph_entities=[],
            graph_chunks=[],
            method="vector_only"
        )
    
    def ask_graph_enhanced(self, question: str, verbose: bool = False) -> GraphQAResult:
        """Answer using ONLY graph traversal (no vector search) for pure comparison"""
        # Intentionally skip vector search for pure Graph RAG comparison
        vector_chunks = []
        
        if verbose:
            print("  🏷️  Extracting entities from question...")
        query_entities = self._extract_query_entities(question)
        if verbose and query_entities:
            print(f"     Found: {query_entities}")
        
        if verbose:
            print("  🕸️  Graph traversal...")
        graph_entities, graph_chunks = self._graph_search(query_entities)
        if verbose:
            print(f"     Found {len(graph_entities)} entities, {len(graph_chunks)} additional chunks")
        
        if not vector_chunks and not graph_chunks:
            return GraphQAResult(
                question=question,
                answer="I couldn't find any relevant information.",
                vector_chunks=[],
                graph_entities=[],
                graph_chunks=[],
                method="graph_enhanced"
            )
        
        context = self._build_context(vector_chunks, graph_entities, graph_chunks)
        
        if verbose:
            print("  💬 Generating answer...")
        answer = self._generate_answer(question, context)
        
        return GraphQAResult(
            question=question,
            answer=answer,
            vector_chunks=vector_chunks,
            graph_entities=graph_entities,
            graph_chunks=graph_chunks,
            method="graph_enhanced"
        )
    
    def ask_hybrid(self, question: str, verbose: bool = False) -> GraphQAResult:
        """
        Answer using BOTH vector search AND graph traversal (hybrid approach).
        
        This combines:
        1. Vector search for semantically similar chunks (high precision)
        2. Graph traversal for entity-connected chunks (cross-document context)
        3. Deduplication to avoid repetition
        """
        if verbose:
            print("  🔍 Vector search...")
        vector_chunks = self._vector_search(question)
        if verbose:
            print(f"     Found {len(vector_chunks)} vector chunks")
        
        if verbose:
            print("  🏷️  Extracting entities from question...")
        query_entities = self._extract_query_entities(question)
        if verbose:
            if query_entities:
                print(f"     Found: {query_entities}")
            else:
                print(f"     No specific named entities (using vector search only)")
        
        if verbose:
            print("  🕸️  Graph traversal...")
        
        if not query_entities:
            graph_entities, graph_chunks = [], []
            if verbose:
                print(f"     Skipping graph traversal (no entities)")
        else:
            graph_entities, graph_chunks = self._graph_search(query_entities, question=question)
            if verbose:
                print(f"     Found {len(graph_entities)} entities, {len(graph_chunks)} graph chunks")
        
        # Deduplicate: remove graph chunks that are already in vector chunks
        vector_chunk_texts = set()
        for vc in vector_chunks:
            text = vc.get('text', '')[:200]  # First 200 chars for matching
            vector_chunk_texts.add(text)
        
        unique_graph_chunks = []
        for gc in graph_chunks:
            text = gc.get('text', [''])[0] if isinstance(gc.get('text'), list) else gc.get('text', '')
            if text[:200] not in vector_chunk_texts:
                unique_graph_chunks.append(gc)
        
        if verbose:
            print(f"     After dedup: {len(unique_graph_chunks)} unique graph chunks")
        
        if not vector_chunks and not unique_graph_chunks:
            return GraphQAResult(
                question=question,
                answer="I couldn't find any relevant information.",
                vector_chunks=[],
                graph_entities=[],
                graph_chunks=[],
                method="hybrid"
            )
        
        # Build context with vector chunks as primary, graph chunks as additional
        context = self._build_context(vector_chunks, graph_entities, unique_graph_chunks)
        
        if verbose:
            print("  💬 Generating answer...")
        answer = self._generate_answer(question, context)
        
        return GraphQAResult(
            question=question,
            answer=answer,
            vector_chunks=vector_chunks,
            graph_entities=graph_entities,
            graph_chunks=unique_graph_chunks,
            method="hybrid"
        )
    
    def compare(self, question: str, verbose: bool = True) -> Tuple[GraphQAResult, GraphQAResult, GraphQAResult]:
        """
        Answer the same question using all three methods and return all results.
        
        Returns:
            Tuple of (vector_only_result, graph_only_result, hybrid_result)
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"COMPARING: {question}")
            print(f"{'='*60}")
        
        if verbose:
            print("\n[1] VECTOR-ONLY RAG")
        vector_result = self.ask_vector_only(question, verbose=verbose)
        
        if verbose:
            print("\n[2] GRAPH-ONLY RAG")
        graph_result = self.ask_graph_enhanced(question, verbose=verbose)
        
        if verbose:
            print("\n[3] HYBRID RAG (Vector + Graph)")
        hybrid_result = self.ask_hybrid(question, verbose=verbose)
        
        return vector_result, graph_result, hybrid_result


def compare_answers(question: str) -> Tuple[GraphQAResult, GraphQAResult, GraphQAResult]:
    """Convenience function to compare all three methods"""
    with GraphQAChain() as qa:
        return qa.compare(question, verbose=True)


if __name__ == "__main__":
    # Interactive comparison mode
    print("=" * 60)
    print("   GRAPH RAG 3-WAY COMPARISON")
    print("   Compares Vector vs Graph vs Hybrid RAG")
    print("=" * 60)
    print("Type 'quit' to exit\n")
    
    with GraphQAChain() as qa:
        while True:
            try:
                question = input("\n❓ Question: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            vector_result, graph_result, hybrid_result = qa.compare(question, verbose=True)
            
            print("\n" + "=" * 60)
            print("📊 COMPARISON RESULTS")
            print("=" * 60)
            
            print("\n" + "-" * 60)
            print("🔢 VECTOR-ONLY ANSWER:")
            print("-" * 60)
            print(vector_result.answer)
            print(f"\n   Sources: {len(vector_result.vector_chunks)} chunks")
            
            print("\n" + "-" * 60)
            print("🕸️  GRAPH-ENHANCED ANSWER:")
            print("-" * 60)
            print(graph_result.answer)
            print(f"\n   Sources: {len(graph_result.vector_chunks)} vector chunks")
            print(f"            {len(graph_result.graph_entities)} entities")
            print(f"            {len(graph_result.graph_chunks)} graph chunks")

