"""
Phase 3: Milvus Lite Vector Store

Stores and searches vector embeddings using Milvus Lite (in-process).
"""

import sys
import os
from typing import List, Optional, Dict, Any

from pymilvus import MilvusClient, DataType

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class MilvusStore:
    """
    Vector store using Milvus Lite.
    
    Stores chunk embeddings for similarity search.
    Milvus Lite runs in-process - no server needed.
    """
    
    # Collection name for chunk embeddings
    CHUNKS_COLLECTION = "chunks"
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.MILVUS_DB_PATH
        self.client = None
        self.dimension = config.EMBEDDING_DIMENSION
    
    def connect(self):
        """Initialize Milvus Lite client"""
        # Ensure data directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        print(f"Connecting to Milvus Lite: {self.db_path}")
        self.client = MilvusClient(self.db_path)
        print("✅ Connected to Milvus Lite")
        
        # Ensure collection exists
        self._ensure_collection()
    
    def close(self):
        """Close the client"""
        if self.client:
            self.client.close()
            print("Milvus connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _ensure_collection(self):
        """Create chunks collection if it doesn't exist"""
        if not self.client.has_collection(self.CHUNKS_COLLECTION):
            print(f"Creating collection: {self.CHUNKS_COLLECTION}")
            
            # Create schema with VARCHAR primary key (string IDs)
            schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)
            
            # Add fields
            schema.add_field(
                field_name="id",
                datatype=DataType.VARCHAR,
                is_primary=True,
                max_length=256
            )
            schema.add_field(
                field_name="vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=self.dimension
            )
            schema.add_field(
                field_name="text",
                datatype=DataType.VARCHAR,
                max_length=65535  # Max text length
            )
            schema.add_field(
                field_name="doc_id",
                datatype=DataType.VARCHAR,
                max_length=256
            )
            schema.add_field(
                field_name="position",
                datatype=DataType.INT32
            )
            
            # Create index params
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="FLAT",  # Simple flat index for small datasets
                metric_type="COSINE"
            )
            
            # Create collection
            self.client.create_collection(
                collection_name=self.CHUNKS_COLLECTION,
                schema=schema,
                index_params=index_params
            )
            print(f"✅ Collection '{self.CHUNKS_COLLECTION}' created")
        else:
            print(f"Collection '{self.CHUNKS_COLLECTION}' already exists")
    
    def clear_collection(self):
        """Delete and recreate the chunks collection"""
        print(f"Clearing collection: {self.CHUNKS_COLLECTION}")
        if self.client.has_collection(self.CHUNKS_COLLECTION):
            self.client.drop_collection(self.CHUNKS_COLLECTION)
        self._ensure_collection()
        print("✅ Collection cleared")
    
    def insert_chunk(
        self, 
        chunk_id: str, 
        embedding: List[float], 
        text: str,
        doc_id: str,
        position: int
    ):
        """
        Insert a single chunk embedding.
        
        Args:
            chunk_id: Unique identifier for the chunk
            embedding: Vector embedding
            text: Original text (stored for retrieval)
            doc_id: Parent document ID
            position: Position in document
        """
        self.client.insert(
            collection_name=self.CHUNKS_COLLECTION,
            data=[{
                "id": chunk_id,
                "vector": embedding,
                "text": text,
                "doc_id": doc_id,
                "position": position
            }]
        )
    
    def insert_chunks_batch(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        doc_ids: List[str],
        positions: List[int]
    ):
        """
        Insert multiple chunk embeddings in batch.
        
        Args:
            chunk_ids: List of chunk IDs
            embeddings: List of embedding vectors
            texts: List of original texts
            doc_ids: List of parent document IDs
            positions: List of positions
        """
        data = [
            {
                "id": chunk_id,
                "vector": embedding,
                "text": text,
                "doc_id": doc_id,
                "position": position
            }
            for chunk_id, embedding, text, doc_id, position 
            in zip(chunk_ids, embeddings, texts, doc_ids, positions)
        ]
        
        self.client.insert(
            collection_name=self.CHUNKS_COLLECTION,
            data=data
        )
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filter_expr: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_expr: Optional filter expression (e.g., "doc_id == 'doc1'")
            
        Returns:
            List of results with id, distance, and metadata
        """
        results = self.client.search(
            collection_name=self.CHUNKS_COLLECTION,
            data=[query_embedding],
            limit=top_k,
            output_fields=["text", "doc_id", "position"],
            filter=filter_expr
        )
        
        # Flatten results (search returns list of lists)
        if results and len(results) > 0:
            return [
                {
                    "id": hit["id"],
                    "distance": hit["distance"],
                    "text": hit["entity"]["text"],
                    "doc_id": hit["entity"]["doc_id"],
                    "position": hit["entity"]["position"]
                }
                for hit in results[0]
            ]
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.client.has_collection(self.CHUNKS_COLLECTION):
            return {"chunks": 0}
        
        # Get collection info
        stats = self.client.get_collection_stats(self.CHUNKS_COLLECTION)
        return {
            "chunks": stats.get("row_count", 0)
        }


if __name__ == "__main__":
    # Quick test
    print("Testing Milvus Store...")
    
    with MilvusStore() as store:
        stats = store.get_stats()
        print(f"\nCurrent stats:")
        print(f"  Chunks in Milvus: {stats['chunks']}")
