#!/usr/bin/env python3
"""
Document Ingestion Script using Extractor V3 (Hindsight-Inspired)

FEATURES:
- Canonical entity resolution (same entity across docs → single node)
- Cross-document entity linking
- Embedding-based entity matching
- Alias tracking

Usage:
    python ingest_v3.py                    # Ingest all docs in ./docs folder
    python ingest_v3.py path/to/folder     # Ingest specific folder
    python ingest_v3.py --clear            # Clear existing demo data first
    python ingest_v3.py --debug            # Show matching decisions
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingest.parser import parse_file, parse_directory, Document
from ingest.chunker import chunk_document, Chunk
from ingest.extractor_v3 import EntityExtractorV3, CanonicalEntity, ExtractedFact
from storage.graph_store import GraphStore
from storage.milvus_store import MilvusStore
from retrieval.embeddings import OllamaEmbeddings


def ingest_documents(
    docs_path: str,
    clear_first: bool = False,
    debug: bool = False
):
    """
    Ingest documents using V3 extractor with canonical entity resolution.
    """
    print("=" * 60)
    print("   DOCUMENT INGESTION (V3 - Hindsight-Inspired)")
    print("=" * 60)
    
    # Parse documents
    print(f"\n📂 Parsing documents from: {docs_path}")
    
    if os.path.isfile(docs_path):
        documents = [parse_file(docs_path)]
    else:
        documents = parse_directory(docs_path)
    
    if not documents:
        print("❌ No documents found!")
        return
    
    print(f"   Found {len(documents)} documents")
    
    # Chunk all documents
    print(f"\n📝 Chunking documents...")
    all_doc_chunks = []
    total_chunks = 0
    
    for doc in documents:
        chunks = chunk_document(doc)
        all_doc_chunks.append((doc, chunks))
        total_chunks += len(chunks)
        print(f"   • {doc.title}: {len(chunks)} chunks")
    
    print(f"   Total: {total_chunks} chunks")
    
    # Initialize V3 extractor
    print(f"\n🧠 Initializing V3 Extractor...")
    extractor = EntityExtractorV3(debug=debug)
    embedder = OllamaEmbeddings()
    
    # Process with graph and milvus
    print(f"\n{'='*60}")
    print("   EXTRACTION & STORAGE")
    print(f"{'='*60}")
    
    with GraphStore() as graph_store, MilvusStore() as milvus_store:
        if clear_first:
            print("\n🗑️  Clearing existing data...")
            graph_store.clear_demo_data()
            milvus_store.clear_collection()
        
        # Process each document
        for doc, chunks in all_doc_chunks:
            print(f"\n📄 Processing: {doc.title}")
            
            # Store document vertex
            graph_store.ingest_document_with_chunks(doc, chunks)
            print(f"   ✅ Document + {len(chunks)} chunks stored")
            
            # Generate embeddings
            print(f"   🧠 Generating embeddings...")
            chunk_texts = [c.text for c in chunks]
            embeddings = embedder.embed_batch(chunk_texts, show_progress=False)
            
            milvus_store.insert_chunks_batch(
                chunk_ids=[c.id for c in chunks],
                embeddings=embeddings,
                texts=chunk_texts,
                doc_ids=[c.doc_id for c in chunks],
                positions=[c.position for c in chunks]
            )
            print(f"   ✅ {len(embeddings)} embeddings stored")
            
            # Extract entities with V3 (canonical resolution happens automatically)
            print(f"   🔍 Extracting entities (V3)...")
            doc_entities = []
            doc_facts = []
            chunk_entity_links = []  # Store for later linking
            
            for chunk in chunks:
                entities, facts = extractor.process_chunk(
                    text=chunk.text,
                    doc_id=doc.id,
                    chunk_id=chunk.id
                )
                doc_entities.extend(entities)
                doc_facts.extend(facts)
                
                # Store links for later (after entities are in graph)
                for entity in entities:
                    chunk_entity_links.append((chunk.id, entity.canonical_name, entity.entity_type))
            
            # Store entities IMMEDIATELY so we can link them
            for entity in doc_entities:
                graph_store.store_entity(
                    name=entity.canonical_name,
                    entity_type=entity.entity_type,
                    description=entity.description
                )
            
            # NOW link chunks to entities (entities exist in graph)
            for chunk_id, entity_name, _ in chunk_entity_links:
                graph_store.link_chunk_to_entity(chunk_id, entity_name)
            
            # Count unique entities for this doc
            unique_entities = len(set(e.id for e in doc_entities))
            print(f"   ✅ {len(doc_entities)} mentions → {unique_entities} canonical entities, {len(doc_facts)} facts")
        
        # Finalize extraction (merge similar entities, build relationships)
        print(f"\n{'='*60}")
        print("   FINALIZING")
        print(f"{'='*60}")
        
        print("\n🔗 Merging similar entities & building relationships...")
        summary = extractor.finalize()
        
        if summary['entities_merged'] > 0:
            print(f"   ✅ Merged {summary['entities_merged']} similar entities")
        
        # Note: Entities are stored during doc processing, not here
        # This avoids the bug where MENTIONS edges were created before entity vertices
        print(f"\n💾 Entities already stored during processing: {summary['total_entities']}")
        
        # Store relationships from facts
        print(f"\n🔀 Storing relationships...")
        relationships_created = 0
        relationships_skipped = 0
        
        # Get entity graph for name lookup
        entity_graph = extractor.get_entity_graph()
        
        for edge in entity_graph['edges']:
            source_name = edge['source']
            target_name = edge['target']
            predicate = edge['predicate']
            
            # Clean the predicate for use as edge label
            clean_predicate = predicate.upper().replace(' ', '_').replace('-', '_')
            
            success = graph_store.create_entity_relationship(
                source_name=source_name,
                target_name=target_name,
                relation_type=clean_predicate,
                ontology_types=None
            )
            
            if success:
                relationships_created += 1
            else:
                relationships_skipped += 1
        
        print(f"   ✅ Created {relationships_created} relationships")
        if relationships_skipped > 0:
            print(f"   ⚠️  Skipped {relationships_skipped} (entities not found)")
        
        # Wait for graph to settle
        time.sleep(1)
        
        # Print final stats
        print(f"\n{'='*60}")
        print("   INGESTION COMPLETE")
        print(f"{'='*60}")
        
        graph_stats = graph_store.get_stats()
        entity_stats = graph_store.get_entity_stats()
        milvus_stats = milvus_store.get_stats()
        
        print(f"\nAerospike Graph:")
        print(f"  📄 Documents: {graph_stats.get('documents', 0)}")
        print(f"  📝 Chunks: {graph_stats.get('chunks', 0)}")
        print(f"  🔗 CONTAINS edges: {graph_stats.get('contains_edges', 0)}")
        print(f"  ➡️  NEXT edges: {graph_stats.get('next_edges', 0)}")
        
        entities_by_type = entity_stats.get('entities_by_type', {})
        print(f"\n  🏷️  Entities: {entity_stats.get('entities', 0)}")
        for entity_type, count in sorted(entities_by_type.items(), key=lambda x: -x[1]):
            print(f"      • {entity_type}: {count}")
        
        print(f"  📌 MENTIONS edges: {graph_stats.get('mentions_edges', 0)}")
        print(f"  🔀 Relationship edges: {graph_stats.get('relationship_edges', 0)}")
        
        print(f"\nMilvus Vector Store:")
        print(f"  🔢 Chunk embeddings: {milvus_stats.get('count', 0)}")
        
        # V3 specific stats
        print(f"\n📊 V3 EXTRACTION STATS:")
        print(f"  Total canonical entities: {summary['total_entities']}")
        print(f"  Cross-document entities: {summary['cross_document_entities']}")
        print(f"  Total aliases tracked: {summary['total_aliases']}")
        print(f"  Facts extracted: {summary['total_facts']}")
        
        # Show cross-document entities
        cross_doc = extractor.get_cross_document_entities()
        if cross_doc:
            print(f"\n🔗 CROSS-DOCUMENT ENTITIES ({len(cross_doc)}):")
            for entity in cross_doc[:10]:
                docs = ', '.join(sorted(entity.source_docs))
                aliases = entity.aliases - {entity.canonical_name}
                alias_str = f" (aliases: {', '.join(sorted(aliases))})" if aliases else ""
                print(f"   • {entity.canonical_name} [{entity.entity_type}]{alias_str}")
                print(f"     appears in: {docs}")


def main():
    parser = argparse.ArgumentParser(description='Ingest documents with V3 extractor')
    parser.add_argument('path', nargs='?', default='./docs',
                       help='Path to document or directory')
    parser.add_argument('--clear', action='store_true',
                       help='Clear existing demo data first')
    parser.add_argument('--debug', action='store_true',
                       help='Show entity matching decisions')
    
    args = parser.parse_args()
    
    ingest_documents(
        docs_path=args.path,
        clear_first=args.clear,
        debug=args.debug
    )


if __name__ == "__main__":
    main()

