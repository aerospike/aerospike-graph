"""
Phase 2: Simple text chunker

Splits documents into overlapping chunks for processing.
"""

from dataclasses import dataclass
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ingest.parser import Document


@dataclass
class Chunk:
    """Represents a chunk of text from a document"""
    id: str
    doc_id: str
    text: str
    position: int  # chunk index within document
    start_char: int  # character offset in original document
    
    def __repr__(self):
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Chunk(id={self.id}, pos={self.position}, len={len(self.text)})"


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[tuple[str, int]]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum characters per chunk (default from config)
        chunk_overlap: Overlap between chunks (default from config)
        
    Returns:
        List of (chunk_text, start_char) tuples
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
    
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Get chunk end position
        end = start + chunk_size
        
        # If not at the end, try to break at a sentence or word boundary
        if end < len(text):
            # Try to find a good break point (sentence end, newline, or space)
            # Look backwards from end to find a break point
            break_chars = ['. ', '.\n', '\n\n', '\n', ' ']
            
            best_break = end
            for break_char in break_chars:
                # Search in the last 20% of the chunk for a break
                search_start = max(start, end - int(chunk_size * 0.2))
                pos = text.rfind(break_char, search_start, end)
                if pos != -1:
                    best_break = pos + len(break_char)
                    break
            
            end = best_break
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, start))
        
        # Move start forward, accounting for overlap
        start = end - chunk_overlap
        
        # Prevent infinite loop
        if start >= len(text) - 1:
            break
        if end == start + chunk_overlap:
            start = end  # Force progress if we're stuck
    
    return chunks


def chunk_document(document: Document) -> List[Chunk]:
    """
    Chunk a document into smaller pieces.
    
    Args:
        document: The Document to chunk
        
    Returns:
        List of Chunk objects
    """
    raw_chunks = chunk_text(document.content)
    
    chunks = []
    for position, (text, start_char) in enumerate(raw_chunks):
        chunk_id = f"{document.id}_chunk_{position:04d}"
        
        chunks.append(Chunk(
            id=chunk_id,
            doc_id=document.id,
            text=text,
            position=position,
            start_char=start_char
        ))
    
    return chunks


def chunk_documents(documents: List[Document]) -> List[Chunk]:
    """
    Chunk multiple documents.
    
    Args:
        documents: List of Documents to chunk
        
    Returns:
        List of all Chunks
    """
    all_chunks = []
    
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"📝 {doc.title}: {len(chunks)} chunks")
    
    print(f"\n📦 Total chunks: {len(all_chunks)}")
    return all_chunks


if __name__ == "__main__":
    # Quick test with sample text
    sample_text = """
    Graph RAG is an evolution of traditional RAG that uses knowledge graphs 
    to provide better context and relationships for LLM-based Q&A systems.
    
    Instead of just chunking documents and doing vector similarity search, 
    Graph RAG extracts entities and relationships from documents, builds a 
    knowledge graph, and uses graph traversal combined with vector similarity 
    for retrieval.
    
    This provides more contextual and connected information to the LLM, 
    resulting in better answers that understand the relationships between 
    concepts in your documents.
    """
    
    print("Testing chunker with sample text...")
    print(f"Original length: {len(sample_text)} chars")
    print(f"Chunk size: {config.CHUNK_SIZE}, Overlap: {config.CHUNK_OVERLAP}")
    print("-" * 50)
    
    chunks = chunk_text(sample_text)
    for i, (text, start) in enumerate(chunks):
        print(f"\nChunk {i} (start={start}, len={len(text)}):")
        print(f"  '{text[:80]}...'")

