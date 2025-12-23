"""
Phase 5: Aerospike Graph storage

Stores documents, chunks, entities, and relationships.

IMPORTANT: 
- Always use T.id for vertex IDs, and g.V(id) for lookups.
- NO HARDCODED SCHEMA - entity types and relationship types are dynamically discovered.
"""

import sys
import os
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.structure.graph import Graph
from gremlin_python.process.traversal import T, Direction, Merge

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ingest.parser import Document
from ingest.chunker import Chunk


class GraphStore:
    """
    Manages storage of documents, chunks, and entities in Aerospike Graph.
    
    DYNAMIC SCHEMA:
    - Entity types (vertex labels) are NOT predefined
    - Entity types come from LLM ontology discovery during ingestion
    - The graph accepts ANY valid label string
    
    Graph Schema:
    - Document vertex: T.id=doc:{id}, label=Document, (title, source, ingested_at)
    - Chunk vertex: T.id=chunk:{id}, label=Chunk, (doc_id, text, position)
    - Entity vertex: T.id=entity:{name}, label={DynamicType}, (name, description)
      DynamicType is discovered from documents, e.g., Researcher, Algorithm, FeeType, etc.
    
    Edges:
    - CONTAINS: Document -> Chunk
    - NEXT: Chunk -> Chunk (preserves order)
    - MENTIONS: Chunk -> Entity
    - [DynamicRelationType]: Entity -> Entity (e.g., WORKS_AT, TRIGGERS, DEFINES)
    
    NOTE: We use T.id for vertex IDs and g.V(id) for direct lookups.
    """
    
    # System labels (not entities) - these are the ONLY fixed labels
    SYSTEM_LABELS = {'Document', 'Chunk'}
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.GRAPH_HOST
        self.port = port or config.GRAPH_PORT
        self.connection = None
        self.g = None
        # Cache of discovered entity labels (populated dynamically)
        self._discovered_entity_labels: Set[str] = set()
    
    def connect(self):
        """Establish connection to Aerospike Graph"""
        connection_string = f"ws://{self.host}:{self.port}/gremlin"
        print(f"Connecting to Aerospike Graph: {connection_string}")
        
        self.connection = DriverRemoteConnection(connection_string, "g")
        self.g = traversal().withRemote(self.connection)
        print("✅ Connected to Aerospike Graph")
    
    def close(self):
        """Close the connection"""
        if self.connection:
            self.connection.close()
            print("Connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _get_all_entity_labels(self) -> Set[str]:
        """
        Dynamically discover all entity labels currently in the graph.
        Entity labels are any vertex labels that are NOT Document or Chunk.
        """
        try:
            all_labels = self.g.V().label().dedup().toList()
            entity_labels = set(all_labels) - self.SYSTEM_LABELS
            # Update cache
            self._discovered_entity_labels.update(entity_labels)
            return entity_labels
        except Exception:
            return self._discovered_entity_labels
    
    def clear_demo_data(self):
        """
        Remove all demo data (Documents, Chunks, and Entities).
        Useful for re-running ingestion.
        """
        print("Clearing existing demo data...")
        
        # Count documents and chunks
        doc_count = self.g.V().hasLabel('Document').count().next()
        chunk_count = self.g.V().hasLabel('Chunk').count().next()
        
        # Dynamically discover entity labels and count them
        entity_labels = self._get_all_entity_labels()
        entity_count = 0
        for label in entity_labels:
            entity_count += self.g.V().hasLabel(label).count().next()
        # Also check for legacy 'Entity' label
        legacy_count = self.g.V().hasLabel('Entity').count().next()
        entity_count += legacy_count
        
        print(f"  Found: {doc_count} Documents, {chunk_count} Chunks, {entity_count} Entities")
        if entity_labels:
            print(f"  Entity labels discovered: {entity_labels}")
        
        # Delete all vertices (edges are deleted automatically)
        self.g.V().hasLabel('Document').drop().toList()
        self.g.V().hasLabel('Chunk').drop().toList()
        
        # Delete entities with dynamically discovered labels
        for label in entity_labels:
            self.g.V().hasLabel(label).drop().toList()
        
        # Delete legacy Entity vertices
        self.g.V().hasLabel('Entity').drop().toList()
        
        # Clear the cache
        self._discovered_entity_labels.clear()
        
        print("✅ Demo data cleared")
    
    def vertex_exists(self, vertex_id: str) -> bool:
        """Check if a vertex with given ID exists using g.V(id)"""
        return self.g.V(vertex_id).hasNext()
    
    # ==================== DOCUMENT METHODS ====================
    
    def store_document(self, document: Document) -> str:
        """
        Store a document as a vertex using mergeV for idempotent operations.
        
        Uses Aerospike Graph's mergeV to create if not exists, or update if exists.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        """
        doc_vertex_id = f"doc:{document.id}"
        
        # Use mergeV for idempotent upsert
        self.g.merge_v({T.id: doc_vertex_id}) \
            .option(Merge.on_create, {
                T.label: 'Document',
                'title': document.title,
                'source': document.source,
                'ingested_at': datetime.now().isoformat()
            }) \
            .option(Merge.on_match, {
                'title': document.title,
                'source': document.source
            }) \
            .iterate()
        
        return doc_vertex_id
    
    # ==================== CHUNK METHODS ====================
    
    def store_chunk(self, chunk: Chunk) -> str:
        """
        Store a chunk as a vertex using mergeV for idempotent operations.
        
        Uses Aerospike Graph's mergeV to create if not exists, or update if exists.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        """
        chunk_vertex_id = f"chunk:{chunk.id}"
        
        # Use mergeV for idempotent upsert
        self.g.merge_v({T.id: chunk_vertex_id}) \
            .option(Merge.on_create, {
                T.label: 'Chunk',
                'doc_id': chunk.doc_id,
                'text': chunk.text,
                'position': chunk.position,
                'start_char': chunk.start_char
            }) \
            .option(Merge.on_match, {
                'text': chunk.text,
                'position': chunk.position
            }) \
            .iterate()
        
        return chunk_vertex_id
    
    def create_contains_edge(self, doc_id: str, chunk_id: str):
        """
        Create CONTAINS edge from Document to Chunk using mergeE.
        
        Uses Aerospike Graph's mergeE for idempotent edge creation.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        """
        doc_vertex_id = f"doc:{doc_id}"
        chunk_vertex_id = f"chunk:{chunk_id}"
        
        # Use mergeE for idempotent edge creation
        self.g.merge_e({
            T.label: 'CONTAINS',
            Direction.OUT: doc_vertex_id,
            Direction.IN: chunk_vertex_id
        }).iterate()
    
    def create_next_edge(self, chunk_id_from: str, chunk_id_to: str):
        """
        Create NEXT edge between consecutive chunks using mergeE.
        
        Uses Aerospike Graph's mergeE for idempotent edge creation.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        """
        from_vertex_id = f"chunk:{chunk_id_from}"
        to_vertex_id = f"chunk:{chunk_id_to}"
        
        # Use mergeE for idempotent edge creation
        self.g.merge_e({
            T.label: 'NEXT',
            Direction.OUT: from_vertex_id,
            Direction.IN: to_vertex_id
        }).iterate()
    
    def ingest_document_with_chunks(self, document: Document, chunks: List[Chunk]):
        """Ingest a document and its chunks, creating all edges."""
        print(f"\n📄 Ingesting: {document.title}")
        
        self.store_document(document)
        print(f"  ✅ Document vertex created")
        
        prev_chunk_id = None
        for chunk in chunks:
            self.store_chunk(chunk)
            self.create_contains_edge(document.id, chunk.id)
            
            if prev_chunk_id:
                self.create_next_edge(prev_chunk_id, chunk.id)
            
            prev_chunk_id = chunk.id
        
        print(f"  ✅ {len(chunks)} chunks stored with edges")
    
    # ==================== ENTITY METHODS ====================
    
    def store_entity(self, name: str, entity_type: str, description: str = "") -> str:
        """
        Store an entity as a vertex using mergeV for idempotent operations.
        
        DYNAMIC SCHEMA: Entity type becomes the vertex LABEL directly.
        NO validation against predefined types - accepts any valid label.
        
        Uses Aerospike Graph's mergeV to create if not exists, or update if exists.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        
        Args:
            name: Entity name
            entity_type: Entity type (will become the vertex label, e.g., Researcher, Algorithm, FeeType)
            description: Brief description
            
        Returns:
            The vertex ID
        """
        # Normalize entity name for ID
        entity_id = name.lower().replace(' ', '_').replace('-', '_')
        entity_vertex_id = f"entity:{entity_id}"
        
        # Clean entity type for valid label (PascalCase, no special chars)
        # The cleaning is done in extractor_v2.py, but we clean again for safety
        clean_type = entity_type.strip()
        if not clean_type:
            clean_type = "Unknown"
        
        # Track this label in our cache
        self._discovered_entity_labels.add(clean_type)
        
        # Use mergeV for idempotent upsert
        self.g.merge_v({T.id: entity_vertex_id}) \
            .option(Merge.on_create, {
                T.label: clean_type,
                'name': name,
                'description': description
            }) \
            .option(Merge.on_match, {
                'description': description  # Update description on match
            }) \
            .iterate()
        
        return entity_vertex_id
    
    def link_chunk_to_entity(self, chunk_id: str, entity_name: str):
        """
        Create MENTIONS edge from Chunk to Entity using mergeE.
        
        Uses Aerospike Graph's mergeE for idempotent edge creation.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        """
        chunk_vertex_id = f"chunk:{chunk_id}"
        entity_id = entity_name.lower().replace(' ', '_').replace('-', '_')
        entity_vertex_id = f"entity:{entity_id}"
        
        # Only create edge if both vertices exist
        if self.vertex_exists(chunk_vertex_id) and self.vertex_exists(entity_vertex_id):
            # Use mergeE for idempotent edge creation
            self.g.merge_e({
                T.label: 'MENTIONS',
                Direction.OUT: chunk_vertex_id,
                Direction.IN: entity_vertex_id
            }).iterate()
    
    def create_entity_relationship(
        self, 
        source_name: str, 
        target_name: str, 
        relation_type: str,
        ontology_types: List[str] = None,
        infer_missing_types: bool = True
    ):
        """
        Create a relationship edge between two entities using mergeE.
        
        DYNAMIC SCHEMA: Relation type becomes the edge label directly.
        NO validation against predefined types - accepts any valid label.
        
        Uses Aerospike Graph's mergeE for idempotent edge creation.
        See: https://aerospike.com/docs/graph/develop/query/basics/
        
        Args:
            source_name: Name of the source entity
            target_name: Name of the target entity
            relation_type: Type of relationship (becomes edge label)
            ontology_types: List of valid entity types from discovered ontology
            infer_missing_types: If True, try to infer type for missing entities
        
        Returns:
            True if relationship was created, False otherwise
        """
        source_id = source_name.lower().replace(' ', '_').replace('-', '_')
        target_id = target_name.lower().replace(' ', '_').replace('-', '_')
        
        source_vertex_id = f"entity:{source_id}"
        target_vertex_id = f"entity:{target_id}"
        
        # Clean relation type for valid edge label
        clean_relation = relation_type.strip() if relation_type else "RELATED_TO"
        # Remove special characters, replace spaces with underscores
        clean_relation = ''.join(c if c.isalnum() or c == '_' else '_' for c in clean_relation)
        clean_relation = clean_relation.upper()
        
        # Check if entities exist
        source_exists = self.vertex_exists(source_vertex_id)
        target_exists = self.vertex_exists(target_vertex_id)
        
        # Try to create missing entities if we have ontology and can infer type
        if infer_missing_types and ontology_types:
            if not source_exists:
                inferred_type = self._infer_entity_type(source_name, relation_type, ontology_types, is_source=True)
                if inferred_type:
                    self.store_entity(name=source_name, entity_type=inferred_type, description="")
                    source_exists = True
            
            if not target_exists:
                inferred_type = self._infer_entity_type(target_name, relation_type, ontology_types, is_source=False)
                if inferred_type:
                    self.store_entity(name=target_name, entity_type=inferred_type, description="")
                    target_exists = True
        
        # Create edge if both vertices exist
        if source_exists and target_exists:
            # Use mergeE for idempotent edge creation
            self.g.merge_e({
                T.label: clean_relation,
                Direction.OUT: source_vertex_id,
                Direction.IN: target_vertex_id
            }).iterate()
            return True
        
        return False
    
    def _infer_entity_type(
        self, 
        entity_name: str, 
        relation_type: str, 
        ontology_types: List[str],
        is_source: bool
    ) -> Optional[str]:
        """
        Infer entity type based on name and relationship context.
        
        Uses heuristics based on:
        1. Relationship type patterns (LEADS/MANAGES -> Person as source)
        2. Name patterns (words like "Team", "System", "Policy" in name)
        3. Common entity type keywords
        
        Returns None if type cannot be confidently inferred.
        """
        if not ontology_types:
            return None
        
        name_lower = entity_name.lower()
        rel_lower = relation_type.lower()
        ontology_lower = {t.lower(): t for t in ontology_types}
        
        # 1. Check if name contains an ontology type directly
        for ont_type in ontology_types:
            if ont_type.lower() in name_lower:
                return ont_type
        
        # 2. Infer from relationship type patterns
        # Person-like sources (who does the action)
        person_source_relations = {'leads', 'manages', 'owns', 'created', 'reported', 'approved', 'authored'}
        # Person-like targets
        person_target_relations = {'reports_to', 'managed_by', 'owned_by'}
        # Team/Org patterns
        team_relations = {'part_of', 'member_of', 'belongs_to'}
        # Product/Tech patterns  
        tech_relations = {'uses', 'depends_on', 'contains', 'triggers'}
        
        if is_source:
            if any(p in rel_lower for p in person_source_relations):
                if 'person' in ontology_lower:
                    return ontology_lower['person']
                if 'team member' in ontology_lower:
                    return ontology_lower['team member']
        else:
            if any(p in rel_lower for p in person_target_relations):
                if 'person' in ontology_lower:
                    return ontology_lower['person']
            if any(p in rel_lower for p in team_relations):
                if 'team' in ontology_lower:
                    return ontology_lower['team']
                if 'organization' in ontology_lower:
                    return ontology_lower['organization']
        
        # 3. Infer from name patterns
        name_type_hints = {
            'team': 'Team',
            'department': 'Team', 
            'group': 'Team',
            'system': 'Technology',
            'service': 'Technology',
            'database': 'Technology',
            'api': 'Technology',
            'policy': 'Policy',
            'process': 'Process',
            'project': 'Project',
            'product': 'Product',
            'company': 'Organization',
            'corp': 'Organization',
            'inc': 'Organization',
        }
        
        for hint, type_name in name_type_hints.items():
            if hint in name_lower:
                if type_name.lower() in ontology_lower:
                    return ontology_lower[type_name.lower()]
        
        # 4. Cannot confidently infer - return None (don't create entity)
        return None
    
    # ==================== RETRIEVAL METHODS ====================
    
    def get_entities_for_chunk(self, chunk_id: str) -> List[Dict[str, Any]]:
        """Get all entities mentioned in a chunk"""
        chunk_vertex_id = f"chunk:{chunk_id}"
        
        entities = self.g.V(chunk_vertex_id).out('MENTIONS').valueMap(True).toList()
        return entities
    
    def get_related_entities(self, entity_name: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        """Get entities related to the given entity via any relationship"""
        entity_id = entity_name.lower().replace(' ', '_').replace('-', '_')
        entity_vertex_id = f"entity:{entity_id}"
        
        if not self.vertex_exists(entity_vertex_id):
            return []
        
        # Get entities within max_hops, excluding the source
        related = self.g.V(entity_vertex_id) \
            .repeat(__.both().simplePath()) \
            .times(max_hops) \
            .dedup() \
            .valueMap(True) \
            .toList()
        
        return related
    
    def get_chunks_mentioning_entity(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all chunks that mention a specific entity"""
        entity_id = entity_name.lower().replace(' ', '_').replace('-', '_')
        entity_vertex_id = f"entity:{entity_id}"
        
        if not self.vertex_exists(entity_vertex_id):
            return []
        
        chunks = self.g.V(entity_vertex_id).in_('MENTIONS').valueMap(True).toList()
        return chunks
    
    def find_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an entity by name (case-insensitive)"""
        entity_id = name.lower().replace(' ', '_').replace('-', '_')
        entity_vertex_id = f"entity:{entity_id}"
        
        results = self.g.V(entity_vertex_id).valueMap(True).toList()
        return results[0] if results else None
    
    def search_entities(self, search_term: str, entity_type: str = None) -> List[Dict[str, Any]]:
        """
        Search for entities by name (case-insensitive contains search).
        
        DYNAMIC SCHEMA: Works with any entity type discovered from documents.
        
        Args:
            search_term: Text to search for in entity names
            entity_type: Optional filter by entity type (label)
        """
        from gremlin_python.process.traversal import TextP
        
        # Get all entity labels dynamically
        entity_labels = self._get_all_entity_labels()
        if not entity_labels:
            # If no labels discovered yet, try to find any vertex that's not Document/Chunk
            entity_labels = {'Entity'}  # Fallback to legacy label
        
        # Try multiple case variants for better matching
        search_variants = []
        if search_term:
            search_variants = [
                search_term,
                search_term.capitalize(),  # "fee" -> "Fee"
                search_term.title(),        # "late payment" -> "Late Payment"
                search_term.upper(),        # "fee" -> "FEE"
            ]
            # Remove duplicates while preserving order
            search_variants = list(dict.fromkeys(search_variants))
        
        all_entities = []
        seen_ids = set()
        
        for variant in search_variants if search_variants else ['']:
            if entity_type:
                # Search specific type
                if variant:
                    entities = self.g.V().hasLabel(entity_type) \
                        .has('name', TextP.containing(variant)) \
                        .valueMap(True) \
                        .limit(10) \
                        .toList()
                else:
                    entities = self.g.V().hasLabel(entity_type) \
                        .valueMap(True) \
                        .limit(10) \
                        .toList()
            else:
                # Search all entity types (dynamically discovered)
                if entity_labels and variant:
                    entities = self.g.V().hasLabel(*entity_labels) \
                        .has('name', TextP.containing(variant)) \
                        .valueMap(True) \
                        .limit(10) \
                        .toList()
                elif entity_labels:
                    entities = self.g.V().hasLabel(*entity_labels) \
                        .valueMap(True) \
                        .limit(10) \
                        .toList()
                else:
                    entities = []
            
            # Add unique entities
            for e in entities:
                e_id = e.get(T.id, str(e.get('name', [''])[0]))
                if e_id not in seen_ids:
                    seen_ids.add(e_id)
                    all_entities.append(e)
        
        return all_entities[:15]  # Limit total results
    
    def get_entities_by_type(self, entity_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all entities of a specific type.
        
        DYNAMIC SCHEMA: Accepts any entity type that exists in the graph.
        """
        return self.g.V().hasLabel(entity_type) \
            .valueMap(True) \
            .limit(limit) \
            .toList()
    
    # ==================== STATS METHODS ====================
    
    def get_graph_summary(self) -> dict:
        """
        Get graph summary using AGS built-in metadata summary.
        
        Uses Aerospike Graph Service's efficient summary collection which runs
        asynchronously and provides approximate statistics without scanning the entire graph.
        See: https://aerospike.com/docs/graph/manage/summary/
        
        Returns:
            dict with vertex counts, edge counts, and property information
        """
        try:
            summary = self.g.call("aerospike.graph.admin.metadata.summary").next()
            return self._parse_summary(summary)
        except Exception as e:
            # Fall back to manual counting if summary not available
            print(f"  ⚠️ AGS summary not available, using manual count: {e}")
            return self._get_stats_manual()
    
    def _parse_summary(self, summary) -> dict:
        """Parse AGS summary output into structured dict."""
        result = {
            'total_vertices': 0,
            'vertex_counts_by_label': {},
            'total_edges': 0,
            'edge_counts_by_label': {},
            'supernodes': {},
            'vertex_properties_by_label': {},
            'edge_properties_by_label': {}
        }
        
        if isinstance(summary, dict):
            # AGS returns dict with keys like 'Total vertex count', 'Vertex count by label', etc.
            result['total_vertices'] = summary.get('Total vertex count', 0)
            result['vertex_counts_by_label'] = summary.get('Vertex count by label', {})
            result['total_edges'] = summary.get('Total edge count', 0)
            result['edge_counts_by_label'] = summary.get('Edge count by label', {})
            result['supernodes'] = summary.get('Supernode count by label', {})
            result['total_supernodes'] = summary.get('Total supernode count', 0)
            result['vertex_properties_by_label'] = summary.get('Vertex properties by label', {})
            result['edge_properties_by_label'] = summary.get('Edge properties by label', {})
            return result
        
        # Parse string output from AGS (legacy format)
        if isinstance(summary, str):
            for line in summary.split('\n'):
                line = line.strip()
                if 'Total vertex count' in line:
                    result['total_vertices'] = int(line.split('=')[-1])
                elif 'Vertex count by label' in line:
                    counts_str = line.split('=', 1)[-1].strip('{}')
                    for item in counts_str.split(','):
                        if '=' in item:
                            label, count = item.strip().split('=')
                            result['vertex_counts_by_label'][label] = int(count)
                elif 'Total edge count' in line:
                    result['total_edges'] = int(line.split('=')[-1])
                elif 'Edge count by label' in line:
                    counts_str = line.split('=', 1)[-1].strip('{}')
                    for item in counts_str.split(','):
                        if '=' in item:
                            label, count = item.strip().split('=')
                            result['edge_counts_by_label'][label] = int(count)
        
        return result
    
    def _get_stats_manual(self) -> dict:
        """Fallback manual stats collection."""
        doc_count = self.g.V().hasLabel('Document').count().next()
        chunk_count = self.g.V().hasLabel('Chunk').count().next()
        
        # Get all vertex labels and counts
        vertex_counts = self.g.V().label().groupCount().next()
        edge_counts = self.g.E().label().groupCount().next()
        
        return {
            'total_vertices': sum(vertex_counts.values()),
            'vertex_counts_by_label': vertex_counts,
            'total_edges': sum(edge_counts.values()),
            'edge_counts_by_label': edge_counts,
            'supernodes': {}
        }
    
    def get_stats(self) -> dict:
        """Get statistics about stored data (legacy interface)."""
        summary = self.get_graph_summary()
        
        vertex_counts = summary.get('vertex_counts_by_label', {})
        edge_counts = summary.get('edge_counts_by_label', {})
        
        return {
            'documents': vertex_counts.get('Document', 0),
            'chunks': vertex_counts.get('Chunk', 0),
            'contains_edges': edge_counts.get('CONTAINS', 0),
            'next_edges': edge_counts.get('NEXT', 0)
        }
    
    def get_entity_stats(self) -> dict:
        """Get entity-specific statistics with breakdown by type (DYNAMIC)."""
        summary = self.get_graph_summary()
        
        vertex_counts = summary.get('vertex_counts_by_label', {})
        edge_counts = summary.get('edge_counts_by_label', {})
        
        # Filter to entity types only (exclude Document, Chunk)
        # This is DYNAMIC - we accept whatever labels exist in the graph
        entity_counts = {
            label: count for label, count in vertex_counts.items() 
            if label not in self.SYSTEM_LABELS
        }
        total_entities = sum(entity_counts.values())
        
        # Count relationship edges (excluding structural edges)
        structural_edges = {'CONTAINS', 'NEXT', 'MENTIONS'}
        relationship_edge_count = sum(
            count for label, count in edge_counts.items() 
            if label not in structural_edges
        )
        
        return {
            'entities': total_entities,
            'entities_by_type': entity_counts,
            'entity_counts_by_label': entity_counts,  # Alias for compatibility
            'mentions_edges': edge_counts.get('MENTIONS', 0),
            'relationship_edges': relationship_edge_count,
            'supernodes': summary.get('supernodes', {})
        }
    
    def get_discovered_schema(self) -> dict:
        """
        Get the dynamically discovered schema from the graph.
        
        Returns:
            dict with entity_labels and relationship_labels found in graph
        """
        vertex_labels = set(self.g.V().label().dedup().toList())
        edge_labels = set(self.g.E().label().dedup().toList())
        
        entity_labels = vertex_labels - self.SYSTEM_LABELS
        relationship_labels = edge_labels - {'CONTAINS', 'NEXT', 'MENTIONS'}
        
        return {
            'entity_labels': sorted(entity_labels),
            'relationship_labels': sorted(relationship_labels),
            'system_labels': sorted(self.SYSTEM_LABELS),
            'structural_edges': ['CONTAINS', 'NEXT', 'MENTIONS']
        }
    
    # ==================== LEGACY METHODS ====================
    
    def get_document(self, doc_id: str) -> Optional[dict]:
        """Get a document by ID"""
        doc_vertex_id = f"doc:{doc_id}"
        results = self.g.V(doc_vertex_id).valueMap(True).toList()
        return results[0] if results else None
    
    def get_chunk(self, chunk_id: str) -> Optional[dict]:
        """Get a chunk by ID"""
        chunk_vertex_id = f"chunk:{chunk_id}"
        results = self.g.V(chunk_vertex_id).valueMap(True).toList()
        return results[0] if results else None
    
    def get_document_chunks(self, doc_id: str) -> List[dict]:
        """Get all chunks for a document, ordered by position"""
        doc_vertex_id = f"doc:{doc_id}"
        chunks = (
            self.g.V(doc_vertex_id)
            .out('CONTAINS')
            .order().by('position')
            .valueMap(True)
            .toList()
        )
        return chunks


if __name__ == "__main__":
    # Quick test
    print("Testing GraphStore connection (DYNAMIC SCHEMA)...")
    print("=" * 60)
    
    with GraphStore() as store:
        stats = store.get_stats()
        entity_stats = store.get_entity_stats()
        schema = store.get_discovered_schema()
        
        print(f"\nCurrent graph stats:")
        print(f"  Documents: {stats['documents']}")
        print(f"  Chunks: {stats['chunks']}")
        print(f"  CONTAINS edges: {stats['contains_edges']}")
        print(f"  NEXT edges: {stats['next_edges']}")
        
        print(f"\nEntity stats:")
        print(f"  Total entities: {entity_stats['entities']}")
        print(f"  MENTIONS edges: {entity_stats['mentions_edges']}")
        print(f"  Relationship edges: {entity_stats['relationship_edges']}")
        
        print(f"\nDiscovered Schema (DYNAMIC):")
        print(f"  Entity labels: {schema['entity_labels']}")
        print(f"  Relationship labels: {schema['relationship_labels']}")
