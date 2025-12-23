"""
Phase 4: Q&A Chain

Simple question-answering using vector retrieval + Ollama LLM.
"""

import sys
import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from storage.milvus_store import MilvusStore
from retrieval.embeddings import OllamaEmbeddings


@dataclass
class QAResult:
    """Result from a Q&A query"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]  # Retrieved chunks used as context
    

class QAChain:
    """
    Simple Q&A chain using vector retrieval.
    
    Flow:
    1. Embed the question
    2. Search Milvus for similar chunks
    3. Filter by minimum score threshold
    4. Build context from retrieved chunks
    5. Send to Ollama LLM for answer generation
    """
    
    # Improved system prompt
    SYSTEM_PROMPT = """You are a helpful assistant that analyzes documents. Answer questions by synthesizing information from the provided context.

Guidelines:
1. Prioritize information from the context - quote and cite specific passages
2. Synthesize across multiple document sections when relevant
3. Be thorough - extract all relevant details from the context
4. Cite sources: mention which document each point comes from
5. If context is limited, work with what's available and note any gaps"""

    # Improved answer prompt
    ANSWER_PROMPT = """CONTEXT FROM DOCUMENTS:

{context}

---

QUESTION: {question}

Analyze the context above and provide a comprehensive answer. Quote relevant passages and cite which document they come from. Synthesize information across all available sections:"""

    def __init__(
        self,
        milvus_store: MilvusStore = None,
        embedder: OllamaEmbeddings = None,
        llm_model: str = None,
        top_k: int = 5,
        min_score: float = 0.45  # Minimum similarity score (cosine) - lower to include more results
    ):
        self.milvus_store = milvus_store
        self.embedder = embedder or OllamaEmbeddings()
        self.llm_model = llm_model or config.OLLAMA_MODEL
        self.llm_base_url = config.OLLAMA_BASE_URL
        self.top_k = top_k
        self.min_score = min_score
        
        # Track if we own the milvus connection
        self._owns_milvus = milvus_store is None
    
    def connect(self):
        """Connect to Milvus if not provided"""
        if self._owns_milvus:
            self.milvus_store = MilvusStore()
            self.milvus_store.connect()
    
    def close(self):
        """Close Milvus connection if we own it"""
        if self._owns_milvus and self.milvus_store:
            self.milvus_store.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def retrieve(self, question: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a question.
        
        Args:
            question: The user's question
            
        Returns:
            List of relevant chunks with metadata, filtered by min_score
        """
        # Embed the question
        question_embedding = self.embedder.embed(question)
        
        # Search Milvus - get more than we need, then filter
        results = self.milvus_store.search(
            query_embedding=question_embedding,
            top_k=self.top_k * 2  # Get extra for filtering
        )
        
        # Filter by minimum score
        filtered = [r for r in results if r['distance'] >= self.min_score]
        
        # Take top_k after filtering
        return filtered[:self.top_k]
    
    def build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved chunks.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            # Format each chunk with clear separation
            header = f"[Document: {chunk['doc_id']}, Section {chunk['position'] + 1}]"
            context_parts.append(f"{header}\n{chunk['text']}")
        
        return "\n\n" + "="*40 + "\n\n".join(context_parts)
    
    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using Ollama LLM.
        
        Args:
            question: The user's question
            context: Retrieved context
            
        Returns:
            Generated answer
        """
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
                    "temperature": 0,  # 0 = deterministic/reproducible
                    "num_ctx": 4096  # Larger context window
                }
            },
            timeout=120  # LLM can be slow
        )
        response.raise_for_status()
        
        return response.json()["response"].strip()
    
    def ask(self, question: str, verbose: bool = False, show_context: bool = False) -> QAResult:
        """
        Answer a question using RAG.
        
        Args:
            question: The user's question
            verbose: Whether to print progress
            show_context: Whether to print the context sent to LLM
            
        Returns:
            QAResult with answer and sources
        """
        if verbose:
            print(f"Question: {question}")
            print("Retrieving relevant chunks...")
        
        # Step 1: Retrieve relevant chunks
        chunks = self.retrieve(question)
        
        if verbose:
            print(f"Found {len(chunks)} relevant chunks (min_score={self.min_score})")
        
        if not chunks:
            return QAResult(
                question=question,
                answer="I couldn't find any relevant information to answer your question.",
                sources=[]
            )
        
        # Step 2: Build context
        context = self.build_context(chunks)
        
        if show_context:
            print("\n" + "="*60)
            print("CONTEXT SENT TO LLM:")
            print("="*60)
            print(context)
            print("="*60 + "\n")
        
        if verbose:
            print("Generating answer...")
        
        # Step 3: Generate answer
        answer = self.generate_answer(question, context)
        
        return QAResult(
            question=question,
            answer=answer,
            sources=chunks
        )


def ask_question(question: str, verbose: bool = True, show_context: bool = False) -> QAResult:
    """
    Convenience function to ask a single question.
    
    Args:
        question: The question to ask
        verbose: Whether to print progress
        show_context: Whether to print context sent to LLM
        
    Returns:
        QAResult with answer and sources
    """
    with QAChain() as qa:
        return qa.ask(question, verbose=verbose, show_context=show_context)


if __name__ == "__main__":
    # Interactive Q&A test
    print("=" * 60)
    print("   GRAPH RAG Q&A (Phase 4 - Vector Only)")
    print("=" * 60)
    print("Type 'quit' to exit, 'debug' to toggle context display\n")
    
    show_context = False
    
    with QAChain() as qa:
        while True:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if question.lower() == 'debug':
                show_context = not show_context
                print(f"Context display: {'ON' if show_context else 'OFF'}")
                continue
            
            if not question:
                continue
            
            print("\n" + "-" * 40)
            result = qa.ask(question, verbose=True, show_context=show_context)
            
            print(f"\n💬 Answer:\n{result.answer}")
            
            print(f"\n📚 Sources ({len(result.sources)}):")
            for i, source in enumerate(result.sources):
                print(f"  {i+1}. {source['doc_id']} (score: {source['distance']:.3f})")
