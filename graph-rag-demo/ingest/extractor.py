"""
Phase 5: Entity and Relationship Extractor

Uses Ollama LLM to extract entities and relationships from text chunks.
"""

import sys
import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class Entity:
    """Represents an extracted entity"""
    name: str
    type: str  # CONCEPT, PRODUCT, TECHNOLOGY, ORGANIZATION, PERSON, etc.
    description: str = ""
    
    def __hash__(self):
        return hash((self.name.lower(), self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.name.lower() == other.name.lower() and self.type == other.type


@dataclass 
class Relationship:
    """Represents a relationship between two entities"""
    source: str  # Entity name
    target: str  # Entity name
    relation_type: str  # USES, CONTAINS, ENABLES, IS_A, etc.
    
    def __hash__(self):
        return hash((self.source.lower(), self.target.lower(), self.relation_type))


class EntityExtractor:
    """
    Extracts entities and relationships from text using Ollama LLM.
    
    Supports three modes:
    1. DYNAMIC (default): LLM discovers entity/relationship types from content
    2. FIXED: Use predefined entity/relationship types
    3. CUSTOM: User provides domain-specific types
    """
    
    # Dynamic prompt - LLM discovers types 
    DYNAMIC_PROMPT = """Extract entities and relationships from the following text.

TEXT:
{text}

INSTRUCTIONS:
1. Identify important entities (people, places, concepts, objects, events, etc.)
2. For each entity, create an appropriate TYPE that describes what it is
3. Identify meaningful relationships between entities
4. Create descriptive relationship types that capture how entities relate
5. Return ONLY valid JSON

OUTPUT FORMAT (JSON only, no other text):
{{
  "entities": [
    {{"name": "Entity Name", "type": "YOUR_CHOSEN_TYPE", "description": "Brief description"}}
  ],
  "relationships": [
    {{"source": "Entity1", "target": "Entity2", "relation_type": "YOUR_CHOSEN_RELATION"}}
  ]
}}

Extract entities and relationships:"""

    # Fixed prompt - predefined types (original behavior)
    FIXED_PROMPT = """Extract entities and relationships from the following text.

TEXT:
{text}

INSTRUCTIONS:
1. Identify important entities
2. Identify relationships between entities
3. Return ONLY valid JSON in the exact format below
4. Entity types: CONCEPT, PRODUCT, TECHNOLOGY, ORGANIZATION, PERSON, PROCESS
5. Relationship types: USES, CONTAINS, ENABLES, IS_A, PART_OF, RELATED_TO, DEPENDS_ON

OUTPUT FORMAT (JSON only, no other text):
{{
  "entities": [
    {{"name": "Entity Name", "type": "TYPE", "description": "Brief description"}}
  ],
  "relationships": [
    {{"source": "Entity1", "target": "Entity2", "relation_type": "RELATIONSHIP"}}
  ]
}}

Extract entities and relationships:"""

    # Custom prompt template - user provides types
    CUSTOM_PROMPT = """Extract entities and relationships from the following text.

TEXT:
{text}

INSTRUCTIONS:
1. Identify important entities
2. Identify relationships between entities
3. Return ONLY valid JSON in the exact format below
4. Entity types to use: {entity_types}
5. Relationship types to use: {relationship_types}

OUTPUT FORMAT (JSON only, no other text):
{{
  "entities": [
    {{"name": "Entity Name", "type": "TYPE", "description": "Brief description"}}
  ],
  "relationships": [
    {{"source": "Entity1", "target": "Entity2", "relation_type": "RELATIONSHIP"}}
  ]
}}

Extract entities and relationships:"""

    # Ontology discovery prompt - analyze document to suggest types
    ONTOLOGY_DISCOVERY_PROMPT = """Analyze this text and suggest appropriate entity types and relationship types for knowledge extraction.

TEXT:
{text}

Based on the content, suggest:
1. 5-10 entity types that would capture the important concepts
2. 5-10 relationship types that would capture how entities relate

Return ONLY valid JSON:
{{
  "entity_types": ["TYPE1", "TYPE2", ...],
  "relationship_types": ["REL1", "REL2", ...],
  "domain": "brief description of the document domain"
}}"""

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        timeout: int = 120,
        mode: str = "dynamic",  # "dynamic", "fixed", or "custom"
        entity_types: List[str] = None,
        relationship_types: List[str] = None
    ):
        self.model = model or config.OLLAMA_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.timeout = timeout
        self.mode = mode
        self.entity_types = entity_types
        self.relationship_types = relationship_types
        
        # Select prompt based on mode
        if mode == "dynamic":
            self.prompt_template = self.DYNAMIC_PROMPT
        elif mode == "fixed":
            self.prompt_template = self.FIXED_PROMPT
        elif mode == "custom":
            if not entity_types or not relationship_types:
                raise ValueError("Custom mode requires entity_types and relationship_types")
            self.prompt_template = self.CUSTOM_PROMPT
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'dynamic', 'fixed', or 'custom'")
    
    def discover_ontology(self, sample_text: str) -> Dict[str, Any]:
        """
        Analyze sample text to discover appropriate entity and relationship types.
        
        Args:
            sample_text: Sample text to analyze
            
        Returns:
            Dict with 'entity_types', 'relationship_types', and 'domain'
        """
        prompt = self.ONTOLOGY_DISCOVERY_PROMPT.format(text=sample_text[:3000])
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result_text = response.json()["response"].strip()
            
            # Parse JSON
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > 0:
                data = json.loads(result_text[start_idx:end_idx])
                return {
                    'entity_types': data.get('entity_types', []),
                    'relationship_types': data.get('relationship_types', []),
                    'domain': data.get('domain', 'Unknown')
                }
        except Exception as e:
            print(f"  ⚠️ Ontology discovery error: {e}")
        
        return {'entity_types': [], 'relationship_types': [], 'domain': 'Unknown'}
    
    def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            Tuple of (entities, relationships)
        """
        # Build prompt based on mode
        if self.mode == "custom":
            prompt = self.prompt_template.format(
                text=text[:2000],
                entity_types=", ".join(self.entity_types),
                relationship_types=", ".join(self.relationship_types)
            )
        else:
            prompt = self.prompt_template.format(text=text[:2000])
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for consistent extraction
                        "num_ctx": 4096
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result_text = response.json()["response"].strip()
            
            # Parse JSON from response
            entities, relationships = self._parse_response(result_text)
            return entities, relationships
            
        except Exception as e:
            print(f"  ⚠️ Extraction error: {e}")
            return [], []
    
    def _parse_response(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Parse LLM response into entities and relationships"""
        entities = []
        relationships = []
        
        try:
            # Try to find JSON in the response
            # Sometimes LLM adds extra text before/after JSON
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return [], []
            
            json_str = text[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Parse entities
            for e in data.get("entities", []):
                if "name" in e and "type" in e:
                    entities.append(Entity(
                        name=e["name"],
                        type=e.get("type", "CONCEPT"),
                        description=e.get("description", "")
                    ))
            
            # Parse relationships
            for r in data.get("relationships", []):
                if "source" in r and "target" in r:
                    relationships.append(Relationship(
                        source=r["source"],
                        target=r["target"],
                        relation_type=r.get("relation_type", "RELATED_TO")
                    ))
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️ JSON parse error: {e}")
        
        return entities, relationships
    
    # Batch extraction prompt - handles multiple chunks at once
    BATCH_PROMPT = """Extract entities and relationships from the following text chunks.

CHUNKS:
{chunks_text}

INSTRUCTIONS:
1. For EACH chunk, identify important entities and relationships
2. Return results grouped by chunk_id
3. Create appropriate entity types based on the content
4. Return ONLY valid JSON

OUTPUT FORMAT (JSON only):
{{
  "results": [
    {{
      "chunk_id": "id_of_chunk",
      "entities": [{{"name": "...", "type": "...", "description": "..."}}],
      "relationships": [{{"source": "...", "target": "...", "relation_type": "..."}}]
    }}
  ]
}}

Extract:"""

    def extract_from_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        show_progress: bool = True,
        batch_size: int = 0
    ) -> Tuple[List[Entity], List[Relationship], Dict[str, List[str]]]:
        """
        Extract entities from multiple chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'id' and 'text'
            show_progress: Whether to print progress
            batch_size: If > 0, batch multiple chunks per LLM call (faster!)
            
        Returns:
            Tuple of (all_entities, all_relationships, chunk_entity_map)
            chunk_entity_map: {chunk_id: [entity_names]}
        """
        # Use batch mode for faster extraction
        if batch_size > 0:
            return self._extract_batched(chunks, show_progress, batch_size)
        
        # Default: one-by-one extraction
        all_entities = {}  # name -> Entity (dedup by name)
        all_relationships = set()
        chunk_entity_map = {}  # chunk_id -> [entity_names]
        
        total = len(chunks)
        
        for i, chunk in enumerate(chunks):
            if show_progress:
                print(f"  Extracting from chunk {i+1}/{total}...", end="\r")
            
            chunk_id = chunk.get('id', f'chunk_{i}')
            text = chunk.get('text', '')
            
            entities, relationships = self.extract(text)
            
            # Store entities (dedup by lowercase name)
            entity_names = []
            for entity in entities:
                key = entity.name.lower()
                if key not in all_entities:
                    all_entities[key] = entity
                entity_names.append(entity.name)
            
            # Store relationships
            for rel in relationships:
                all_relationships.add(rel)
            
            # Map chunk to entities
            chunk_entity_map[chunk_id] = entity_names
        
        if show_progress:
            print(f"  Extracted from {total} chunks" + " " * 30)
        
        return list(all_entities.values()), list(all_relationships), chunk_entity_map
    
    def _extract_batched(
        self,
        chunks: List[Dict[str, Any]],
        show_progress: bool,
        batch_size: int
    ) -> Tuple[List[Entity], List[Relationship], Dict[str, List[str]]]:
        """Extract entities using batched LLM calls (much faster!)"""
        all_entities = {}
        all_relationships = set()
        chunk_entity_map = {}
        
        total = len(chunks)
        num_batches = (total + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, total)
            batch = chunks[start:end]
            
            if show_progress:
                print(f"  Extracting batch {batch_idx+1}/{num_batches} (chunks {start+1}-{end})...", end="\r")
            
            # Build batch prompt
            chunks_text = ""
            for chunk in batch:
                chunk_id = chunk.get('id', f'chunk_{start}')
                text = chunk.get('text', '')[:800]  # Truncate for batch
                chunks_text += f"\n--- CHUNK [{chunk_id}] ---\n{text}\n"
            
            prompt = self.BATCH_PROMPT.format(chunks_text=chunks_text)
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_ctx": 8192  # Larger context for batches
                        }
                    },
                    timeout=120  # Longer timeout for batches
                )
                response.raise_for_status()
                
                result_text = response.json()["response"].strip()
                
                # Parse batch results
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > 0:
                    data = json.loads(result_text[start_idx:end_idx])
                    
                    for result in data.get("results", []):
                        chunk_id = result.get("chunk_id", "")
                        
                        # Parse entities
                        entity_names = []
                        for e in result.get("entities", []):
                            if "name" in e:
                                entity = Entity(
                                    name=e["name"],
                                    type=e.get("type", "CONCEPT"),
                                    description=e.get("description", "")
                                )
                                key = entity.name.lower()
                                if key not in all_entities:
                                    all_entities[key] = entity
                                entity_names.append(entity.name)
                        
                        # Parse relationships
                        for r in result.get("relationships", []):
                            if "source" in r and "target" in r:
                                all_relationships.add(Relationship(
                                    source=r["source"],
                                    target=r["target"],
                                    relation_type=r.get("relation_type", "RELATED_TO")
                                ))
                        
                        # Map chunk to entities
                        if chunk_id:
                            chunk_entity_map[chunk_id] = entity_names
                            
            except Exception as e:
                print(f"\n  ⚠️ Batch extraction error: {e}")
                # Fall back to one-by-one for this batch
                for chunk in batch:
                    chunk_id = chunk.get('id', '')
                    entities, relationships = self.extract(chunk.get('text', ''))
                    entity_names = []
                    for entity in entities:
                        key = entity.name.lower()
                        if key not in all_entities:
                            all_entities[key] = entity
                        entity_names.append(entity.name)
                    for rel in relationships:
                        all_relationships.add(rel)
                    chunk_entity_map[chunk_id] = entity_names
        
        if show_progress:
            print(f"  Extracted from {total} chunks in {num_batches} batches" + " " * 20)
        
        return list(all_entities.values()), list(all_relationships), chunk_entity_map


if __name__ == "__main__":
    import sys
    
    # Test text - can be overridden with command line
    test_text = """
    Graph RAG (Retrieval-Augmented Generation) is an advanced approach that combines 
    large language models with knowledge graphs. It uses vector search to find relevant 
    documents and graph traversal to discover entity relationships. Aerospike Graph 
    provides the graph database backend, while Milvus handles vector similarity search.
    The system uses Gremlin as its query language for graph operations.
    """
    
    # Check for mode argument
    mode = sys.argv[1] if len(sys.argv) > 1 else "dynamic"
    
    print(f"Testing Entity Extractor (mode: {mode})...")
    print("=" * 50)
    
    if mode == "discover":
        # Test ontology discovery
        extractor = EntityExtractor(mode="dynamic")
        print("\nDiscovering ontology from sample text...")
        ontology = extractor.discover_ontology(test_text)
        print(f"\nDomain: {ontology['domain']}")
        print(f"Suggested entity types: {ontology['entity_types']}")
        print(f"Suggested relationship types: {ontology['relationship_types']}")
    else:
        # Test extraction
        extractor = EntityExtractor(mode=mode)
        entities, relationships = extractor.extract(test_text)
        
        print(f"\nExtracted {len(entities)} entities:")
        for e in entities:
            desc = e.description[:50] + "..." if len(e.description) > 50 else e.description
            print(f"  - {e.name} ({e.type}): {desc}")
        
        print(f"\nExtracted {len(relationships)} relationships:")
        for r in relationships:
            print(f"  - {r.source} --[{r.relation_type}]--> {r.target}")

