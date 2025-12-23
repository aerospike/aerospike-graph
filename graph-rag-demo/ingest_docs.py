#!/usr/bin/env python3
"""
Document Ingestion Script with Unified Ontology Discovery

TWO-PASS APPROACH:
1. First pass: Parse all documents, chunk them, discover unified ontology
2. Second pass: Extract entities using unified schema, store everything

This ensures consistent entity types across ALL documents.

Usage:
    python ingest_docs.py                    # Ingest all docs in ./docs folder
    python ingest_docs.py path/to/file.md   # Ingest a single file
    python ingest_docs.py --clear           # Clear existing demo data first
    python ingest_docs.py --no-entities     # Skip entity extraction (faster)
"""

import sys
import os
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingest.parser import parse_file, parse_directory, Document
from ingest.chunker import chunk_document, Chunk
from ingest.extractor_v2 import EntityExtractorV2, Entity, Relationship
from storage.graph_store import GraphStore
from storage.milvus_store import MilvusStore
from retrieval.embeddings import OllamaEmbeddings


def normalize_ontology(entity_types: list, extractor: EntityExtractorV2) -> list:
    """
    Normalize discovered entity types by merging semantically equivalent ones.
    
    Uses LLM to identify and merge types like:
    - Person ≈ Team Member ≈ Employee → Person
    - Technology ≈ System ≈ Infrastructure → Technology
    """
    import requests
    
    if len(entity_types) <= 5:
        return entity_types
    
    # First, basic deduplication (case-insensitive)
    seen = {}
    for t in entity_types:
        key = t.lower().replace(' ', '').replace('_', '')
        if key not in seen:
            seen[key] = t
    
    deduplicated = list(seen.values())
    
    # If we have many types, use LLM to identify semantic equivalents
    if len(deduplicated) > 8:
        print(f"     🔄 Merging {len(deduplicated)} types using LLM...")
        
        types_str = ", ".join(deduplicated)
        prompt = f"""Merge these entity types by grouping semantically equivalent ones.

TYPES: {types_str}

MERGE RULES:
- "Person", "Team Member", "Employee", "Staff" → Person
- "Technology", "System", "Service", "Infrastructure" → Technology  
- "Company", "Organization", "Firm" → Organization
- Keep distinct types separate

OUTPUT only the MERGED list (8-12 types, one per line):"""

        try:
            response = requests.post(
                f"{extractor.base_url}/api/generate",
                json={
                    "model": extractor.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 2048}
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()["response"].strip()
            
            # Parse the canonical types
            canonical_types = []
            for line in result.split('\n'):
                line = line.strip()
                # Skip empty lines and explanatory text
                if not line or line.startswith('#') or ':' in line or len(line) > 30:
                    continue
                # Remove numbering like "1." or "- "
                line = line.lstrip('0123456789.-) ').strip()
                if line and len(line) > 1:
                    canonical_types.append(line)
            
            if canonical_types and len(canonical_types) >= 4:
                # Build mapping from original types to canonical
                # Keep only types that are in the canonical list or very close
                merged = []
                canonical_lower = {t.lower(): t for t in canonical_types}
                
                for orig_type in deduplicated:
                    orig_lower = orig_type.lower()
                    # Check if this type is canonical or similar to a canonical type
                    if orig_lower in canonical_lower:
                        if canonical_lower[orig_lower] not in merged:
                            merged.append(canonical_lower[orig_lower])
                    else:
                        # Check for partial match
                        matched = False
                        for can_lower, can_type in canonical_lower.items():
                            if can_lower in orig_lower or orig_lower in can_lower:
                                if can_type not in merged:
                                    merged.append(can_type)
                                matched = True
                                break
                        # If no match, keep original if we have room
                        if not matched and len(merged) < 12:
                            merged.append(orig_type)
                
                if merged:
                    print(f"     ✅ Merged to {len(merged)} canonical types")
                    return merged[:15]
                    
        except Exception as e:
            print(f"     ⚠️ LLM merge failed: {e}, using basic dedup")
    
    # Fallback: limit to 15 types
    return deduplicated[:15]


def ingest_documents(
    documents: list[Document], 
    clear_first: bool = False,
    extract_entities: bool = True,
    batch_size: int = 8
):
    """
    Ingest documents with UNIFIED ontology discovery across all docs.
    
    TWO-PASS APPROACH:
    Pass 1: Parse all docs, collect chunks, discover unified ontology
    Pass 2: Extract entities with unified schema, store in graph/milvus
    """
    if not documents:
        print("❌ No documents to ingest")
        return
    
    print(f"\n{'='*60}")
    print(f"   INGESTING {len(documents)} DOCUMENT(S)")
    if extract_entities:
        print(f"   (with UNIFIED ontology discovery)")
    print(f"{'='*60}")
    
    # Initialize components
    print("\nInitializing components...")
    embedder = OllamaEmbeddings()
    print(f"  ✅ Embeddings: {embedder.model}")
    
    extractor = None
    if extract_entities:
        extractor = EntityExtractorV2()
        print(f"  ✅ Entity extractor v2: {extractor.model}")
    
    # =========================================================================
    # PASS 1: Parse all documents and discover UNIFIED ontology
    # =========================================================================
    print(f"\n{'='*60}")
    print("   PASS 1: PARSING & ONTOLOGY DISCOVERY")
    print(f"{'='*60}")
    
    all_doc_chunks = []  # List of (doc, chunks) tuples
    
    # Parse and chunk all documents
    for doc in documents:
        print(f"\n📄 Parsing: {doc.title}")
        chunks = chunk_document(doc)
        print(f"   📝 {len(chunks)} chunks")
        all_doc_chunks.append((doc, chunks))
    
    # Unified ontology discovery (if extracting entities)
    if extract_entities and extractor:
        print(f"\n🔬 UNIFIED ONTOLOGY DISCOVERY (across {len(documents)} documents)")
        print("-" * 50)
        
        # Collect samples from ALL documents
        all_samples = []
        for doc, chunks in all_doc_chunks:
            # Take first 2 chunks from each document
            for chunk in chunks[:2]:
                all_samples.append(chunk.text[:800])
        
        # Discover ontology from first document
        if all_samples:
            sample_text = "\n\n---\n\n".join(all_samples[:3])
            extractor.discover_ontology(sample_text)
            print(f"   Initial types from Doc 1: {len(extractor.discovered_entity_types)}")
            
            # Add types from remaining documents (ADDITIVE)
            for i in range(3, len(all_samples), 2):
                sample_text = "\n\n".join(all_samples[i:i+2])
                extractor.add_to_ontology(sample_text)
            
            print(f"   Total accumulated types: {len(extractor.discovered_entity_types)}")
        
        # Normalize the ontology
        original_count = len(extractor.discovered_entity_types)
        extractor.discovered_entity_types = normalize_ontology(
            extractor.discovered_entity_types, 
            extractor
        )
        
        print(f"\n✅ UNIFIED ONTOLOGY:")
        print(f"   Domain: {extractor.domain}")
        print(f"   Entity Types: {extractor.discovered_entity_types}")
        print(f"   Relationship Types: {extractor.discovered_relationship_types}")
        if original_count != len(extractor.discovered_entity_types):
            print(f"   (normalized from {original_count} to {len(extractor.discovered_entity_types)} types)")
    
    # =========================================================================
    # PASS 2: Extract entities and store everything
    # =========================================================================
    print(f"\n{'='*60}")
    print("   PASS 2: EXTRACTION & STORAGE")
    print(f"{'='*60}")
    
    with GraphStore() as graph_store, MilvusStore() as milvus_store:
        if clear_first:
            graph_store.clear_demo_data()
            milvus_store.clear_collection()
        
        all_entities = {}
        total_relationships_created = 0
        total_relationships_skipped = 0
        
        for doc, chunks in all_doc_chunks:
            print(f"\n📄 Ingesting: {doc.title}")
            
            # Store document and chunks in graph
            graph_store.ingest_document_with_chunks(doc, chunks)
            
            # Generate and store embeddings
            print(f"   🧠 Generating embeddings...")
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = embedder.embed_batch(chunk_texts, show_progress=False)
            
            milvus_store.insert_chunks_batch(
                chunk_ids=[chunk.id for chunk in chunks],
                embeddings=embeddings,
                texts=chunk_texts,
                doc_ids=[chunk.doc_id for chunk in chunks],
                positions=[chunk.position for chunk in chunks]
            )
            print(f"   ✅ Stored {len(embeddings)} embeddings")
            
            # Extract entities and relationships (using UNIFIED ontology)
            if extract_entities and extractor:
                print(f"   🔍 Extracting entities & relationships...")
                
                chunk_dicts = [{'id': c.id, 'text': c.text} for c in chunks]
                doc_entities = 0
                doc_relationships = []
                
                # Extract from each chunk
                chunk_entity_map = {}
                for chunk_dict in chunk_dicts:
                    entities, relationships = extractor.extract(chunk_dict['text'])
                    
                    entity_names = []
                    for entity in entities:
                        key = entity.name.lower()
                        if key not in all_entities:
                            all_entities[key] = entity
                            # Store entity in graph IMMEDIATELY
                            graph_store.store_entity(
                                name=entity.name,
                                entity_type=entity.type,
                                description=entity.description
                            )
                            doc_entities += 1
                        entity_names.append(entity.name)
                    
                    doc_relationships.extend(relationships)
                    chunk_entity_map[chunk_dict['id']] = entity_names
                
                # Link chunks to entities
                for chunk_id, entity_names in chunk_entity_map.items():
                    for entity_name in entity_names:
                        graph_store.link_chunk_to_entity(chunk_id, entity_name)
                
                # Store relationships IMMEDIATELY for this document
                doc_created = 0
                doc_skipped = 0
                skipped_info = []
                ontology_types = extractor.discovered_entity_types
                
                for rel in doc_relationships:
                    # Check entity existence before attempting
                    source_id = rel.source.lower().replace(' ', '_').replace('-', '_')
                    target_id = rel.target.lower().replace(' ', '_').replace('-', '_')
                    source_vertex_id = f"entity:{source_id}"
                    target_vertex_id = f"entity:{target_id}"
                    
                    source_exists = graph_store.vertex_exists(source_vertex_id)
                    target_exists = graph_store.vertex_exists(target_vertex_id)
                    
                    success = graph_store.create_entity_relationship(
                        source_name=rel.source,
                        target_name=rel.target,
                        relation_type=rel.relation_type,
                        ontology_types=ontology_types
                    )
                    
                    if success:
                        doc_created += 1
                    else:
                        doc_skipped += 1
                        # Record why it was skipped
                        missing = []
                        if not source_exists:
                            inferred = graph_store._infer_entity_type(rel.source, rel.relation_type, ontology_types, True) if ontology_types else None
                            missing.append(f"src:'{rel.source}'" + (f"→{inferred}" if inferred else "→?"))
                        if not target_exists:
                            inferred = graph_store._infer_entity_type(rel.target, rel.relation_type, ontology_types, False) if ontology_types else None
                            missing.append(f"tgt:'{rel.target}'" + (f"→{inferred}" if inferred else "→?"))
                        
                        skip_reason = f"[{rel.relation_type}] " + ", ".join(missing) if missing else "unknown"
                        skipped_info.append(skip_reason)
                
                total_relationships_created += doc_created
                total_relationships_skipped += doc_skipped
                
                print(f"   ✅ Entities: {doc_entities} new, Relationships: {doc_created} created, {doc_skipped} skipped")
                
                # Show skipped reasons (limit to 3 per document)
                if skipped_info:
                    for info in skipped_info[:3]:
                        print(f"      ⚠️ Skipped: {info}")
                    if len(skipped_info) > 3:
                        print(f"      ... and {len(skipped_info) - 3} more skipped")
        
        print(f"\n📊 TOTALS: {len(all_entities)} entities, {total_relationships_created} relationships created, {total_relationships_skipped} skipped")
        
        # Wait for AGS summary to update (async)
        import time
        time.sleep(1)
        
        # Print final stats
        graph_stats = graph_store.get_stats()
        entity_stats = graph_store.get_entity_stats()
        milvus_stats = milvus_store.get_stats()
        
        print(f"\n{'='*60}")
        print(f"   INGESTION COMPLETE")
        print(f"{'='*60}")
        print(f"\nAerospike Graph:")
        print(f"  📄 Documents: {graph_stats['documents']}")
        print(f"  📝 Chunks: {graph_stats['chunks']}")
        print(f"  🔗 CONTAINS edges: {graph_stats['contains_edges']}")
        print(f"  ➡️  NEXT edges: {graph_stats['next_edges']}")
        
        if extract_entities:
            print(f"\n  🏷️  Entities: {entity_stats['entities']}")
            if 'entities_by_type' in entity_stats:
                for etype, count in sorted(entity_stats['entities_by_type'].items(), key=lambda x: -x[1])[:10]:
                    print(f"      • {etype}: {count}")
            print(f"  📌 MENTIONS edges: {entity_stats['mentions_edges']}")
            print(f"  🔀 Relationship edges: {entity_stats['relationship_edges']}")
        
        print(f"\nMilvus Vector Store:")
        print(f"  🔢 Chunk embeddings: {milvus_stats['chunks']}")
        
        if extract_entities:
            print(f"\n📊 UNIFIED SCHEMA USED:")
            print(f"   Domain: {extractor.domain}")
            print(f"   Entity types: {extractor.discovered_entity_types}")
            print(f"   Relationship types: {extractor.discovered_relationship_types}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_docs_path = os.path.join(script_dir, 'docs')
    
    parser = argparse.ArgumentParser(
        description="Ingest documents with UNIFIED ontology discovery"
    )
    parser.add_argument(
        'path',
        nargs='?',
        default=default_docs_path,
        help=f'File or directory to ingest (default: {default_docs_path})'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing demo data before ingesting'
    )
    parser.add_argument(
        '--no-entities',
        action='store_true',
        help='Skip entity extraction (faster ingestion)'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=8,
        help='Batch size for entity extraction (default: 8)'
    )
    
    args = parser.parse_args()
    
    # Resolve path
    target_path = args.path
    if not os.path.isabs(target_path):
        target_path = os.path.join(script_dir, target_path)
    
    print(f"Target path: {target_path}")
    
    # Parse documents
    if os.path.isfile(target_path):
        doc = parse_file(target_path)
        documents = [doc] if doc else []
    elif os.path.isdir(target_path):
        documents = parse_directory(target_path)
    else:
        print(f"❌ Path not found: {target_path}")
        sys.exit(1)
    
    ingest_documents(
        documents, 
        clear_first=args.clear,
        extract_entities=not args.no_entities,
        batch_size=args.batch
    )


if __name__ == "__main__":
    main()
