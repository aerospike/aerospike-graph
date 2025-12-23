"""
Entity and Relationship Extractor v2

FULLY DYNAMIC ONTOLOGY using Microsoft GraphRAG methodology.
1. Two-phase extraction: Discover ontology first from documents, then extract with it
2. Entity types and relationship types are derived entirely from document content
3. No predefined vertex or edge types - everything comes from LLM analysis
4. Uses MS GraphRAG tuple-based output format for reliable parsing
"""

import sys
import os
import json
import re
import requests
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def repair_json(text: str) -> str:
    """
    Attempt to repair common JSON errors from LLM output.
    """
    # Find JSON boundaries
    start = text.find('{')
    end = text.rfind('}') + 1
    if start == -1 or end == 0:
        return text
    
    json_str = text[start:end]
    
    # Fix common issues
    # 1. Remove trailing commas before ] or }
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    # 2. Replace single quotes with double quotes (careful with apostrophes)
    json_str = re.sub(r"'(\w+)':", r'"\1":', json_str)  # Keys
    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # String values
    
    # 3. Fix unescaped newlines in strings
    json_str = re.sub(r'(?<!\\)\n', ' ', json_str)
    
    # 4. Remove control characters
    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
    
    return json_str


def safe_json_parse(text: str) -> Optional[Dict]:
    """
    Safely parse JSON with repair attempts.
    Also handles conversational responses that contain entity/relationship info.
    """
    # First try direct parse
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > 0:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    
    # Try with repairs
    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass
    
    # Try to extract arrays directly if JSON object fails
    try:
        entity_match = re.search(r'"entity_types"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        rel_match = re.search(r'"relationship_types"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        domain_match = re.search(r'"domain"\s*:\s*"([^"]*)"', text)
        
        if entity_match or rel_match:
            result = {"domain": "Unknown", "entity_types": [], "relationship_types": []}
            
            if domain_match:
                result["domain"] = domain_match.group(1)
            
            if entity_match:
                items = re.findall(r'"([^"]+)"', entity_match.group(1))
                result["entity_types"] = items
            
            if rel_match:
                items = re.findall(r'"([^"]+)"', rel_match.group(1))
                result["relationship_types"] = items
            
            return result
    except Exception:
        pass
    
    # Fallback: Parse conversational response with bullet points or headers
    try:
        result = {"domain": "Unknown", "entity_types": [], "relationship_types": []}
        
        domain_patterns = [
            r'\*\*Domain[:\*]*\s*([A-Za-z/\s]+)',
            r'Domain[:\s]+([A-Za-z/\s]+)',
        ]
        for pattern in domain_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["domain"] = match.group(1).strip().strip('*').strip()
                break
        
        entity_section_patterns = [
            r'\*\*Entity\s*Types?\*?\*?:?\s*(.*?)(?:\*\*Relationship|\*\*Key|$)',
            r'Entity\s*Types?:\s*(.*?)(?:Relationship|Key|$)',
        ]
        for pattern in entity_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1)
                items = re.findall(r'[-•*]\s*([A-Za-z][A-Za-z\s]+?)(?:\n|$)', section)
                if not items:
                    items = re.findall(r'\d+\.\s*([A-Za-z][A-Za-z\s]+?)(?:\n|$)', section)
                if not items:
                    items = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', section)
                if items:
                    result["entity_types"] = [i.strip() for i in items if len(i.strip()) > 2]
                    break
        
        rel_section_patterns = [
            r'\*\*Relationship\s*Types?\*?\*?:?\s*(.*?)(?:\*\*Key|\*\*Entity|$)',
            r'Relationship\s*Types?:\s*(.*?)(?:Key|Entity|$)',
        ]
        for pattern in rel_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1)
                items = re.findall(r'[-•*]\s*"?([a-z_\s]+)"?(?:\n|$)', section, re.IGNORECASE)
                if not items:
                    items = re.findall(r'\d+\.\s*"?([a-z_\s]+)"?(?:\n|$)', section, re.IGNORECASE)
                if items:
                    result["relationship_types"] = [i.strip().lower().replace(' ', '_') for i in items if len(i.strip()) > 2]
                    break
        
        if result["entity_types"]:
            return result
            
    except Exception:
        pass
    
    return None


def clean_type_label(raw_type: str) -> str:
    """
    Clean a type string to be a valid graph label.
    Does NOT map to predefined types - just cleans the string.
    
    Examples:
        "fee type" -> "FeeType"
        "PERSON" -> "Person"
        "account_status" -> "AccountStatus"
    """
    if not raw_type:
        return "Unknown"
    
    # Remove special characters except spaces and underscores
    cleaned = re.sub(r'[^a-zA-Z0-9\s_]', '', raw_type)
    
    # Split by spaces or underscores
    parts = re.split(r'[\s_]+', cleaned)
    
    # Title case each part and join (PascalCase)
    result = ''.join(part.capitalize() for part in parts if part)
    
    return result if result else "Unknown"


def clean_relationship_label(raw_type: str) -> str:
    """
    Clean a relationship description to be a valid edge label.
    Does NOT map to predefined types - derives from the actual description.
    
    Examples:
        "works at" -> "WORKS_AT"
        "triggers when" -> "TRIGGERS_WHEN"
        "is part of" -> "IS_PART_OF"
    """
    if not raw_type:
        return "RELATED_TO"
    
    # Remove special characters except spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', raw_type)
    
    # Split by spaces, uppercase, join with underscores
    parts = cleaned.split()
    result = '_'.join(part.upper() for part in parts if part)
    
    return result if result else "RELATED_TO"


@dataclass
class Entity:
    """
    Represents an extracted entity with dynamically discovered type.
    No normalization to predefined types - type comes directly from LLM.
    """
    name: str
    type: str  # Dynamically discovered type, cleaned for graph labels
    description: str = ""
    raw_type: str = ""  # Original type string from LLM before cleaning
    
    def __post_init__(self):
        # Store original type
        self.raw_type = self.type
        # Clean for valid graph label (PascalCase, no special chars)
        self.type = clean_type_label(self.type)
    
    def __hash__(self):
        return hash((self.name.lower(), self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.name.lower() == other.name.lower()


@dataclass
class Relationship:
    """
    Represents a relationship with dynamically discovered type.
    No normalization to predefined types - type is derived from description.
    """
    source: str
    target: str
    relation_type: str
    strength: int = 5  # Relationship strength (1-10) from MS GraphRAG
    raw_type: str = ""  # Original type string from LLM before cleaning
    
    def __post_init__(self):
        # Store original type
        self.raw_type = self.relation_type
        # Clean for valid graph label (UPPER_SNAKE_CASE)
        self.relation_type = clean_relationship_label(self.relation_type)
    
    def __hash__(self):
        return hash((self.source.lower(), self.target.lower(), self.relation_type))


class EntityExtractorV2:
    """
    Fully dynamic entity extractor using Microsoft GraphRAG methodology.
    
    Based on: https://github.com/microsoft/graphrag
    
    1. Two-phase extraction:
       - Phase 1: Discover entity types from document content
       - Phase 2: Extract using MS GraphRAG tuple format with discovered types
    
    2. NO HARDCODED SCHEMA:
       - All entity types come from LLM analysis of the documents
       - No predefined vertex labels or edge labels
    
    3. MS GraphRAG tuple format:
       - Entities: ("entity"<|>NAME<|>TYPE<|>DESCRIPTION)
       - Relationships: ("relationship"<|>SOURCE<|>TARGET<|>DESCRIPTION<|>STRENGTH)
       - Record delimiter: ##
       - Completion: <|COMPLETE|>
    """
    
    # Microsoft GraphRAG delimiters
    TUPLE_DELIMITER = "<|>"
    RECORD_DELIMITER = "##"
    COMPLETION_DELIMITER = "<|COMPLETE|>"
    
    # Phase 1: Ontology discovery prompt (discovers BOTH entity types AND relationship types)
    ONTOLOGY_DISCOVERY_PROMPT = """You must output ONLY valid JSON. No explanations, no markdown, no text before or after.

Read this text carefully and identify what TYPES of things are mentioned AND how they relate.

TEXT:
{text}

TASK:
1. What domain/subject is this text about? (2-3 words)
2. What CATEGORIES of things are mentioned? (6-12 types)
   - People, roles, actors
   - Objects, items, artifacts
   - Processes, events, actions
   - Concepts, rules, conditions
3. What kinds of RELATIONSHIPS exist between things? (4-8 types)
   - How do people relate to things? (owns, manages, created, uses)
   - How do things relate to each other? (contains, depends_on, triggers)
   - How do events connect? (causes, follows, requires)

OUTPUT ONLY THIS JSON:
{{"domain": "the domain", "entity_types": ["Type1", "Type2", "Type3"], "relationship_types": ["MANAGES", "CONTAINS", "DEPENDS_ON", "TRIGGERS"]}}"""

    # Phase 2: Extraction prompt with BOTH entity and relationship types
    EXTRACTION_PROMPT = """Extract entities and relationships from this text.

ENTITY TYPES: {entity_types}
RELATIONSHIP TYPES: {relationship_types}

TEXT:
{input_text}

RULES:
1. Extract ALL named items as entities with their type
2. Extract ALL connections between entities as relationships
3. Use the relationship types provided, or create descriptive ones

OUTPUT FORMAT:
ENTITY: Name | Type | Description
RELATIONSHIP: SourceEntity | TargetEntity | RelationType | Strength(1-10)

EXTRACT NOW:"""

    # Continue prompt for missed entities
    CONTINUE_PROMPT = "MANY entities and relationships were missed in the last extraction. Remember to ONLY emit entities that match any of the previously extracted types. Add them below using the same format:\n"
    
    # Loop check prompt
    LOOP_PROMPT = "It appears some entities and relationships may have still been missed. Answer Y if there are still entities or relationships that need to be added, or N if there are none. Please answer with a single letter Y or N.\n"

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        timeout: int = 90
    ):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL
        self.timeout = timeout
        
        # Discovered ontology (populated during extraction)
        self.domain = "Unknown"
        self.discovered_entity_types: List[str] = []
        self.discovered_relationship_types: List[str] = []  # NEW: relationship types
        
        # Mapping cache for type normalization (populated lazily)
        self._type_mapping_cache: Dict[str, str] = {}
    
    def _normalize_type_to_ontology(self, extracted_type: str) -> str:
        """
        Normalize an extracted entity type to match one of the discovered ontology types.
        
        Uses matching in order:
        1. Exact match (case-insensitive)
        2. Substring match (ontology type in extracted type)
        3. Word overlap matching
        4. LLM classification (cached for speed)
        
        Args:
            extracted_type: The raw type from LLM extraction
            
        Returns:
            The best matching type from discovered_entity_types
        """
        if not self.discovered_entity_types:
            return extracted_type
        
        # Check cache first
        cache_key = extracted_type.lower().strip()
        if cache_key in self._type_mapping_cache:
            return self._type_mapping_cache[cache_key]
        
        extracted_lower = extracted_type.lower().strip()
        extracted_words = set(re.split(r'[\s_]+', extracted_lower))
        
        # 1. Exact match (case-insensitive)
        for ont_type in self.discovered_entity_types:
            if ont_type.lower() == extracted_lower:
                self._type_mapping_cache[cache_key] = ont_type
                return ont_type
        
        # 2. Direct substring match - ontology type is in extracted type
        for ont_type in self.discovered_entity_types:
            if ont_type.lower() in extracted_lower:
                self._type_mapping_cache[cache_key] = ont_type
                return ont_type
        
        # 3. Reverse substring - extracted type is in ontology type
        for ont_type in self.discovered_entity_types:
            if extracted_lower in ont_type.lower():
                self._type_mapping_cache[cache_key] = ont_type
                return ont_type
        
        # 4. Word overlap - find best match by shared words
        best_match = None
        best_overlap = 0
        for ont_type in self.discovered_entity_types:
            ont_words = set(re.split(r'[\s_]+', ont_type.lower()))
            overlap = len(extracted_words & ont_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = ont_type
        
        if best_match and best_overlap > 0:
            self._type_mapping_cache[cache_key] = best_match
            return best_match
        
        # 5. Use LLM to classify (only for truly unknown types)
        llm_match = self._llm_classify_type(extracted_type)
        if llm_match:
            self._type_mapping_cache[cache_key] = llm_match
            return llm_match
        
        # 6. Fallback to first ontology type
        fallback = self.discovered_entity_types[0]
        self._type_mapping_cache[cache_key] = fallback
        return fallback
    
    def _llm_classify_type(self, extracted_type: str) -> Optional[str]:
        """
        Use LLM to classify an unknown type to one of the discovered ontology types.
        
        This is called only when heuristic matching fails.
        """
        if not self.discovered_entity_types:
            return None
        
        types_list = ", ".join(self.discovered_entity_types)
        prompt = f"""Which category does "{extracted_type}" belong to?

CATEGORIES: {types_list}

Reply with ONLY the category name, nothing else."""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 512}
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()["response"].strip()
            
            # Find best match in ontology
            result_lower = result.lower()
            for ont_type in self.discovered_entity_types:
                if ont_type.lower() in result_lower or result_lower in ont_type.lower():
                    return ont_type
            
            # Exact match
            for ont_type in self.discovered_entity_types:
                if ont_type.lower() == result_lower:
                    return ont_type
                    
        except Exception:
            pass
        
        return None
    
    def discover_ontology(self, sample_text: str) -> Dict[str, Any]:
        """
        Phase 1: Discover domain-specific ontology from sample text.
        
        This is the key to dynamic schema - the LLM analyzes the document
        and identifies what types of entities exist.
        
        NO HARDCODED TYPES - everything comes from this analysis.
        
        Args:
            sample_text: Sample text from the documents to analyze
            
        Returns:
            Dict with 'domain', 'entity_types'
            
        Raises:
            ValueError: If ontology discovery fails or returns invalid data
        """
        prompt = self.ONTOLOGY_DISCOVERY_PROMPT.format(text=sample_text[:3000])
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 4096}
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()["response"].strip()
        
        # Parse JSON with repair attempts
        data = safe_json_parse(result)
        if not data:
            raise ValueError(f"Failed to parse ontology discovery response. Raw output:\n{result[:500]}")
        
        # Validate we got useful data
        entity_types = data.get('entity_types', [])
        if not entity_types:
            raise ValueError(f"Ontology discovery returned no entity types. Raw output:\n{result[:500]}")
        
        # Get relationship types (with sensible defaults if not provided)
        relationship_types = data.get('relationship_types', [])
        if not relationship_types:
            # LLM didn't provide relationship types - use generic ones
            relationship_types = ['MANAGES', 'CONTAINS', 'USES', 'RELATES_TO', 'DEPENDS_ON', 'CREATED_BY']
        
        # Store discovered ontology
        self.domain = data.get('domain', 'Unknown')
        self.discovered_entity_types = entity_types
        self.discovered_relationship_types = relationship_types
        
        return data
    
    def add_to_ontology(self, sample_text: str) -> Dict[str, Any]:
        """
        Add newly discovered entity types to existing ontology (ADDITIVE).
        
        Use this when processing multiple documents to accumulate entity types
        across all documents rather than replacing.
        
        Args:
            sample_text: Sample text from a new document to analyze
            
        Returns:
            Dict with newly discovered types (before merging)
        """
        prompt = self.ONTOLOGY_DISCOVERY_PROMPT.format(text=sample_text[:3000])
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 4096}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()["response"].strip()
            data = safe_json_parse(result)
            
            if data and data.get('entity_types'):
                new_types = data.get('entity_types', [])
                # Add new types that aren't already present (case-insensitive check)
                existing_lower = {t.lower() for t in self.discovered_entity_types}
                for t in new_types:
                    if t.lower() not in existing_lower:
                        self.discovered_entity_types.append(t)
                        existing_lower.add(t.lower())
                
                # Also accumulate relationship types
                new_rel_types = data.get('relationship_types', [])
                existing_rel_lower = {t.lower() for t in self.discovered_relationship_types}
                for t in new_rel_types:
                    if t.lower() not in existing_rel_lower:
                        self.discovered_relationship_types.append(t)
                        existing_rel_lower.add(t.lower())
                
                # Update domain if we don't have one
                if self.domain == "Unknown" and data.get('domain'):
                    self.domain = data.get('domain')
                
                return data
        except Exception as e:
            print(f"  ⚠️ Add to ontology error: {e}")
        
        return {"entity_types": []}
    
    # Prompt for reconciling related entity types across documents
    TYPE_RECONCILIATION_PROMPT = """Given these entity types discovered from multiple documents, identify which types are related or represent similar concepts.

ENTITY TYPES: {entity_types}

TASK:
1. Find pairs of types that represent the SAME or SIMILAR concepts
2. Find pairs where one type is a SUBTYPE or SPECIALIZATION of another
3. Only include pairs that are CLEARLY related

OUTPUT FORMAT (one per line):
SAME: Type1 | Type2 | explanation
SUBTYPE: ParentType | ChildType | explanation

Examples:
SAME: Employee | TeamMember | both represent people who work at the company
SUBTYPE: Product | ProductSpec | ProductSpec is a detailed specification of a Product

Now analyze the types above:"""

    def reconcile_entity_types(self) -> List[Tuple[str, str, str, str]]:
        """
        Use LLM to identify relationships between discovered entity types.
        
        This helps connect entities across documents where types may be named
        differently but represent related concepts (e.g., Product and ProductSpec).
        
        Returns:
            List of (relationship, type1, type2, explanation) tuples
        """
        if len(self.discovered_entity_types) < 2:
            return []
        
        prompt = self.TYPE_RECONCILIATION_PROMPT.format(
            entity_types=", ".join(self.discovered_entity_types)
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 4096}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()["response"].strip()
            return self._parse_type_reconciliation(result)
            
        except Exception as e:
            print(f"  ⚠️ Type reconciliation error: {e}")
            return []
    
    def _parse_type_reconciliation(self, text: str) -> List[Tuple[str, str, str, str]]:
        """Parse type reconciliation output."""
        relationships = []
        current_section = None  # 'SAME' or 'SUBTYPE'
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if line.upper().startswith('SAME:') or line.upper() == 'SAME':
                current_section = 'SAME'
                # Check if there's content on same line
                content = line[5:].strip() if ':' in line else ''
                if content and '|' in content:
                    parts = [p.strip() for p in content.split('|')]
                    if len(parts) >= 2:
                        explanation = parts[2] if len(parts) > 2 else "equivalent types"
                        relationships.append(('SAME_AS', parts[0], parts[1], explanation))
                continue
            
            if line.upper().startswith('SUBTYPE:') or line.upper() == 'SUBTYPE':
                current_section = 'SUBTYPE'
                content = line[8:].strip() if ':' in line else ''
                if content and '|' in content:
                    parts = [p.strip() for p in content.split('|')]
                    if len(parts) >= 2:
                        explanation = parts[2] if len(parts) > 2 else "subtype relationship"
                        relationships.append(('IS_TYPE_OF', parts[1], parts[0], explanation))
                continue
            
            # Parse bullet points under current section
            if current_section and '|' in line:
                # Remove bullet point markers
                content = re.sub(r'^[-*•]\s*', '', line)
                parts = [p.strip() for p in content.split('|')]
                
                if len(parts) >= 2:
                    explanation = parts[2] if len(parts) > 2 else "related types"
                    
                    if current_section == 'SAME':
                        relationships.append(('SAME_AS', parts[0], parts[1], explanation))
                    elif current_section == 'SUBTYPE':
                        # For subtype: first is parent, second is child
                        relationships.append(('IS_TYPE_OF', parts[1], parts[0], explanation))
        
        return relationships
    
    def create_cross_type_relationships(
        self, 
        entities: List[Entity],
        type_relationships: List[Tuple[str, str, str, str]]
    ) -> List[Relationship]:
        """
        Create relationships between entities whose types are related.
        
        For example, if "Product" and "ProductSpec" are related types,
        create relationships between Product entities and ProductSpec entities.
        
        Args:
            entities: List of extracted entities
            type_relationships: Output from reconcile_entity_types()
            
        Returns:
            List of new cross-type relationships
        """
        new_relationships = []
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            type_key = entity.type.lower()
            if type_key not in entities_by_type:
                entities_by_type[type_key] = []
            entities_by_type[type_key].append(entity)
        
        # Create relationships based on type relationships
        for rel_type, type1, type2, explanation in type_relationships:
            type1_lower = clean_type_label(type1).lower()
            type2_lower = clean_type_label(type2).lower()
            
            entities1 = entities_by_type.get(type1_lower, [])
            entities2 = entities_by_type.get(type2_lower, [])
            
            # Create relationships between entities of related types
            for e1 in entities1:
                for e2 in entities2:
                    if e1.name.lower() != e2.name.lower():
                        new_relationships.append(Relationship(
                            source=e1.name,
                            target=e2.name,
                            relation_type=rel_type,
                            strength=7
                        ))
        
        return new_relationships
    
    def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships from text.
        
        Uses the entity types discovered in Phase 1.
        NO HARDCODED TYPES.
        
        Args:
            text: Text to extract from
            
        Returns:
            Tuple of (entities, relationships)
            
        Raises:
            ValueError: If ontology has not been discovered yet
        """
        if not self.discovered_entity_types:
            raise ValueError(
                "Ontology must be discovered before extraction. "
                "Call discover_ontology() first or use extract_from_chunks()"
            )
        
        # Build entity types string (comma-separated, uppercase)
        entity_types_str = ", ".join(t.upper() for t in self.discovered_entity_types[:12])
        
        # Build relationship types string
        rel_types = self.discovered_relationship_types or ['MANAGES', 'CONTAINS', 'USES', 'RELATES_TO']
        relationship_types_str = ", ".join(t.upper() for t in rel_types[:8])
        
        # Build prompt
        prompt = self.EXTRACTION_PROMPT.format(
            entity_types=entity_types_str,
            relationship_types=relationship_types_str,
            input_text=text[:2500]
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 4096}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()["response"].strip()
            entities, relationships = self._parse_extraction_output(result)
            
            # Debug: show if we got relationships
            if relationships:
                print(f"      📎 Found {len(relationships)} relationships in chunk")
            
            return entities, relationships
            
        except Exception as e:
            print(f"  ⚠️ Extraction error: {e}")
            return [], []
    
    def _parse_extraction_output(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """
        Parse extraction output in various formats:
        - ENTITY: Name | Type | Description
        - RELATIONSHIP: Source | Target | RelType | Strength
        - Numbered lists with markdown headers
        - MS GraphRAG tuple format
        """
        entities = []
        relationships = []
        
        # Track which section we're in (for markdown formatted output)
        current_section = None  # 'entities' or 'relationships'
        
        # Process line by line
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that look like code or non-extraction content
            if line.startswith('import ') or line.startswith('def ') or line.startswith('#'):
                continue
            if '=' in line and '|' not in line:
                continue
            
            # Detect section headers (markdown format)
            line_lower = line.lower()
            if 'entit' in line_lower and ('**' in line or ':' in line):
                current_section = 'entities'
                continue
            if 'relationship' in line_lower and ('**' in line or ':' in line):
                current_section = 'relationships'
                continue
            
            # Parse ENTITY: format
            if line.upper().startswith('ENTITY:') or line.startswith('- ENTITY:'):
                entity = self._parse_entity_line(line)
                if entity:
                    entities.append(entity)
                continue
            
            # Parse RELATIONSHIP: format
            if line.upper().startswith('RELATIONSHIP:') or line.startswith('- RELATIONSHIP:'):
                relationship = self._parse_relationship_line(line)
                if relationship:
                    relationships.append(relationship)
                continue
            
            # Also try MS GraphRAG tuple format as fallback
            if '"entity"' in line_lower or "'entity'" in line_lower:
                entity = self._parse_entity_tuple(line)
                if entity:
                    entities.append(entity)
                continue
            
            if '"relationship"' in line_lower or "'relationship'" in line_lower:
                relationship = self._parse_relationship_tuple(line)
                if relationship:
                    relationships.append(relationship)
                continue
            
            # Try numbered list format - use section context to decide
            # Check for pipe OR hyphen delimiters
            if re.match(r'^\d+\.?\s*', line) and ('|' in line or ' - ' in line):
                # Determine delimiter
                if '|' in line:
                    parts = line.split('|')
                else:
                    parts = line.split(' - ')
                
                # Use section context to decide parsing
                if current_section == 'relationships':
                    relationship = self._parse_numbered_relationship(line)
                    if relationship:
                        relationships.append(relationship)
                        continue
                
                if current_section == 'entities':
                    entity = self._parse_numbered_pipe_entity(line)
                    if entity:
                        entities.append(entity)
                        continue
                
                # No section context - guess from part count
                # 4+ parts likely a relationship: Source | Target | RelType | Strength
                if len(parts) >= 4:
                    relationship = self._parse_numbered_relationship(line)
                    if relationship:
                        relationships.append(relationship)
                        continue
                
                # 2-3 parts likely an entity: Name | Type | Description
                if len(parts) <= 3:
                    entity = self._parse_numbered_pipe_entity(line)
                    if entity:
                        entities.append(entity)
        
        # NORMALIZE entity types to match the unified ontology
        if self.discovered_entity_types:
            normalized_entities = []
            for entity in entities:
                # Get the normalized type from the unified ontology
                normalized_type = self._normalize_type_to_ontology(entity.raw_type or entity.type)
                # Create new entity with normalized type
                normalized_entities.append(Entity(
                    name=entity.name,
                    type=normalized_type,
                    description=entity.description
                ))
            entities = normalized_entities
        
        return entities, relationships
    
    def _parse_numbered_pipe_entity(self, line: str) -> Optional[Entity]:
        """
        Parse entity from numbered list formats:
        - Pipe: 1. Name | Type | Desc
        - Hyphen: 1. Name - Type
        """
        try:
            # Remove number prefix
            content = re.sub(r'^\d+\.?\s*', '', line)
            
            # Try pipe delimiter first
            if '|' in content:
                parts = [p.strip() for p in content.split('|')]
            # Try hyphen delimiter
            elif ' - ' in content:
                parts = [p.strip() for p in content.split(' - ')]
            else:
                return None
            
            if len(parts) >= 2:
                name = parts[0].strip()
                entity_type = parts[1].strip()
                # Handle compound types like "PERSON, ROLE (CEO)" - take first type
                if ',' in entity_type:
                    entity_type = entity_type.split(',')[0].strip()
                # Remove parenthetical info from type
                if '(' in entity_type:
                    entity_type = entity_type.split('(')[0].strip()
                
                description = parts[2].strip() if len(parts) > 2 else ""
                
                if name and len(name) > 1:
                    return Entity(name=name, type=entity_type, description=description)
        except Exception:
            pass
        return None
    
    def _parse_numbered_relationship(self, line: str) -> Optional[Relationship]:
        """
        Parse relationship from various numbered list formats:
        
        Format 1: Source | Target | RelType | Strength
        Format 2: Source - RelType - Target
        Format 3: Source (TYPE) RELTYPE Target (TYPE) | Strength
        Format 4: Source - Target (RelType, Strength)
        Format 5: Source RELTYPE Target (Strength: N) - Description
        """
        try:
            # Remove number prefix
            content = re.sub(r'^\d+\.?\s*', '', line)
            
            # PRIORITY 1: Handle pipe-delimited format first (most common LLM output)
            # Format: "Source | RelType | Target | Strength" OR "Source | Target | RelType | Strength"
            if '|' in content:
                parts = [p.strip() for p in content.split('|')]
                if len(parts) >= 3:
                    # Determine which part is the relationship type by checking our known types
                    rel_idx = -1
                    matched_rel = None
                    if self.discovered_relationship_types:
                        for i, part in enumerate(parts):
                            part_upper = part.upper().replace(' ', '_')
                            for rel_type in self.discovered_relationship_types:
                                rel_upper = rel_type.upper().replace(' ', '_')
                                if part_upper == rel_upper:
                                    rel_idx = i
                                    matched_rel = rel_upper
                                    break
                            if rel_idx >= 0:
                                break
                    
                    if rel_idx >= 0 and matched_rel:
                        # Determine source and target based on relationship position
                        if rel_idx == 1:  # Format: Source | RelType | Target [| Strength]
                            source = parts[0]
                            target = parts[2] if len(parts) > 2 else ""
                            strength = 5
                            if len(parts) > 3:
                                strength_match = re.match(r'(\d+)', parts[3])
                                if strength_match:
                                    strength = int(strength_match.group(1))
                        elif rel_idx == 2:  # Format: Source | Target | RelType [| Strength]
                            source = parts[0]
                            target = parts[1]
                            strength = 5
                            if len(parts) > 3:
                                strength_match = re.match(r'(\d+)', parts[3])
                                if strength_match:
                                    strength = int(strength_match.group(1))
                        else:
                            source = parts[0]
                            target = parts[1] if len(parts) > 1 else ""
                            strength = 5
                        
                        if source and target:
                            return Relationship(source=source, target=target, relation_type=matched_rel, strength=strength)
            
            # PRIORITY 2: Match known relationship types in space-separated format
            # This prevents misidentifying entity names as relationship types
            if self.discovered_relationship_types:
                for rel_type in self.discovered_relationship_types:
                    rel_upper = rel_type.upper().replace(' ', '_')
                    
                    # Pattern with strength: "Source RELTYPE Target (Strength: N)"
                    pattern_with_strength = rf'^(.+?)\s+{re.escape(rel_upper)}\s+(.+?)\s*\(Strength:\s*(\d+)\)'
                    match = re.match(pattern_with_strength, content, re.IGNORECASE)
                    if match:
                        source = match.group(1).strip()
                        target = match.group(2).strip()
                        strength = int(match.group(3))
                        if ' - ' in target:
                            target = target.split(' - ')[0].strip()
                        if source and target:
                            return Relationship(source=source, target=target, relation_type=rel_upper, strength=strength)
                    
                    # Pattern without strength: "Source RELTYPE Target"
                    pattern_no_strength = rf'^(.+?)\s+{re.escape(rel_upper)}\s+(.+?)$'
                    match = re.match(pattern_no_strength, content, re.IGNORECASE)
                    if match:
                        source = match.group(1).strip()
                        target = match.group(2).strip()
                        if ' - ' in target:
                            target = target.split(' - ')[0].strip()
                        # Remove trailing parenthetical info
                        if '(' in target:
                            target = target.split('(')[0].strip()
                        if source and target:
                            return Relationship(source=source, target=target, relation_type=rel_upper, strength=5)
            
            # FALLBACK: Generic pattern for unknown relationship types
            # "Acme Corp LEADS DataFlow Inc (Strength: 8) - Description"
            # Only use if relationship type is ALL_UPPERCASE and looks like a verb
            strength5_pattern = r'^(.+?)\s+([A-Z][A-Z_]+)\s+(.+?)\s*\(Strength:\s*(\d+)\)'
            match = re.match(strength5_pattern, content)
            if match:
                source = match.group(1).strip()
                rel_type = match.group(2).strip()
                target = match.group(3).strip()
                strength = int(match.group(4))
                
                # Validate: relationship should be ALL UPPERCASE and not look like a name
                # Names are typically TitleCase (e.g., "Michael_Brown"), not ALL_CAPS verbs
                if rel_type.isupper() and not any(c.islower() for c in rel_type):
                    # Additional check: don't treat obvious names as relationships
                    name_indicators = ['_JR', '_SR', '_DR', '_MR', '_MS', '_INC', '_LLC', '_CORP']
                    is_likely_name = any(indicator in rel_type for indicator in name_indicators)
                    
                    if not is_likely_name:
                        if ' - ' in target:
                            target = target.split(' - ')[0].strip()
                        if source and target:
                            return Relationship(source=source, target=target, relation_type=rel_type, strength=strength)
            
            # Format 4: "Acme Corp - Engineering Team (CONTAINS, 10)"
            # Pattern: Source - Target (RelType, Strength)
            paren_pattern = r'^(.+?)\s*-\s*(.+?)\s*\(([A-Z_]+),?\s*(\d+)?\)'
            match = re.match(paren_pattern, content)
            if match:
                source = match.group(1).strip()
                target = match.group(2).strip()
                rel_type = match.group(3).strip()
                strength = int(match.group(4)) if match.group(4) else 5
                
                if source and target and rel_type:
                    return Relationship(
                        source=source,
                        target=target,
                        relation_type=rel_type,
                        strength=strength
                    )
            
            # Format 3: "Emily Watson (PERSON) LEADS Platform Team (TEAM) | 10"
            # Pattern: Source (Type) RELATION Target (Type) [| Strength]
            inline_pattern = r'^(.+?)\s*\([A-Z]+\)\s+([A-Z_]+)\s+(.+?)\s*\([A-Z]+\)'
            match = re.match(inline_pattern, content)
            if match:
                source = match.group(1).strip()
                rel_type = match.group(2).strip()
                target = match.group(3).strip()
                
                # Extract strength if present after pipe
                strength = 5
                if '|' in content:
                    strength_part = content.split('|')[-1].strip()
                    strength_match = re.match(r'(\d+)', strength_part)
                    if strength_match:
                        strength = int(strength_match.group(1))
                
                if source and target and rel_type:
                    return Relationship(
                        source=source,
                        target=target,
                        relation_type=rel_type,
                        strength=strength
                    )
            
            # Format 1: Pipe delimiter "Source | Target | RelType | Strength"
            if '|' in content:
                parts = [p.strip() for p in content.split('|')]
                if len(parts) >= 3:
                    source = parts[0].strip()
                    target = parts[1].strip()
                    rel_type = parts[2].strip()
                    
                    strength = 5
                    if len(parts) > 3:
                        strength_match = re.match(r'(\d+)', parts[3].strip())
                        if strength_match:
                            strength = int(strength_match.group(1))
                    
                    if source and target and rel_type:
                        return Relationship(source=source, target=target, relation_type=rel_type, strength=strength)
            
            # Format 2: Hyphen delimiter "Source - RelType - Target"
            if ' - ' in content:
                parts = [p.strip() for p in content.split(' - ')]
                if len(parts) >= 2:
                    # Check if second part looks like a relationship type (UPPERCASE)
                    if len(parts) >= 3 and (parts[1].isupper() or '_' in parts[1]):
                        source = parts[0]
                        rel_type = parts[1]
                        target = parts[2]
                        # Remove parenthetical info from target
                        if '(' in target:
                            target = target.split('(')[0].strip()
                        return Relationship(source=source, target=target, relation_type=rel_type, strength=5)
                    
        except Exception:
            pass
        return None
    
    def _parse_entity_tuple(self, record: str) -> Optional[Entity]:
        """
        Parse a single entity tuple in MS GraphRAG format.
        
        Format: ("entity"<|>NAME<|>TYPE<|>DESCRIPTION)
        """
        try:
            record = record.strip()
            
            # Check if this looks like an entity tuple
            if '"entity"' not in record.lower() and "'entity'" not in record.lower():
                return None
            
            # Remove outer parentheses
            if record.startswith('('):
                record = record[1:]
            if record.endswith(')'):
                record = record[:-1]
            
            # Split by tuple delimiter
            parts = record.split(self.TUPLE_DELIMITER)
            
            if len(parts) >= 4:
                # parts[0] should be "entity"
                name = parts[1].strip().strip('"\'')
                entity_type = parts[2].strip().strip('"\'')
                description = parts[3].strip().strip('"\'') if len(parts) > 3 else ""
                
                if name and len(name) > 1:
                    return Entity(name=name, type=entity_type, description=description)
                    
        except Exception:
            pass
        return None
    
    def _parse_relationship_tuple(self, record: str) -> Optional[Relationship]:
        """
        Parse a single relationship tuple in MS GraphRAG format.
        
        Format: ("relationship"<|>SOURCE<|>TARGET<|>DESCRIPTION<|>STRENGTH)
        """
        try:
            record = record.strip()
            
            # Check if this looks like a relationship tuple
            if '"relationship"' not in record.lower() and "'relationship'" not in record.lower():
                return None
            
            # Remove outer parentheses
            if record.startswith('('):
                record = record[1:]
            if record.endswith(')'):
                record = record[:-1]
            
            # Split by tuple delimiter
            parts = record.split(self.TUPLE_DELIMITER)
            
            if len(parts) >= 4:
                # parts[0] should be "relationship"
                source = parts[1].strip().strip('"\'')
                target = parts[2].strip().strip('"\'')
                description = parts[3].strip().strip('"\'') if len(parts) > 3 else ""
                
                # Parse strength if present
                strength = 5  # Default
                if len(parts) > 4:
                    try:
                        strength = int(parts[4].strip().strip('"\''))
                    except (ValueError, IndexError):
                        pass
                
                if source and target:
                    return Relationship(
                        source=source, 
                        target=target, 
                        relation_type=description,
                        strength=strength
                    )
                    
        except Exception:
            pass
        return None
    
    def _parse_entity_line(self, line: str) -> Optional[Entity]:
        """Parse an entity from 'ENTITY: name | type | description' format."""
        try:
            # Remove ENTITY: prefix and any leading markers
            content = re.sub(r'^[-*•\d\.]*\s*ENTITY:\s*', '', line, flags=re.IGNORECASE)
            content = content.strip()
            
            if not content:
                return None
            
            parts = [p.strip() for p in content.split('|')]
            
            if len(parts) >= 3:
                name = parts[0].strip()
                entity_type = parts[1].strip()
                description = parts[2].strip()
                
                # Clean name - remove any remaining ENTITY: prefix
                name = re.sub(r'^ENTITY:\s*', '', name, flags=re.IGNORECASE).strip()
                
                if name and len(name) > 1:
                    return Entity(name=name, type=entity_type, description=description)
            elif len(parts) == 2:
                name = parts[0].strip()
                entity_type = parts[1].strip()
                name = re.sub(r'^ENTITY:\s*', '', name, flags=re.IGNORECASE).strip()
                if name and len(name) > 1:
                    return Entity(name=name, type=entity_type, description="")
                    
        except Exception:
            pass
        return None
    
    def _parse_relationship_line(self, line: str) -> Optional[Relationship]:
        """Parse a relationship from 'RELATIONSHIP: source | target | description | strength' format."""
        try:
            content = re.sub(r'^[-*•\d\.]*\s*RELATIONSHIP:\s*', '', line, flags=re.IGNORECASE)
            content = content.strip()
            
            if not content:
                return None
            
            parts = [p.strip() for p in content.split('|')]
            
            if len(parts) >= 3:
                source = parts[0].strip()
                target = parts[1].strip()
                description = parts[2].strip()
                
                # Parse strength if present
                strength = 5  # Default
                if len(parts) > 3:
                    try:
                        strength = int(parts[3].strip())
                    except (ValueError, IndexError):
                        pass
                
                if source and target:
                    return Relationship(
                        source=source, 
                        target=target, 
                        relation_type=description,
                        strength=strength
                    )
            elif len(parts) == 2:
                source = parts[0].strip()
                target = parts[1].strip()
                if source and target:
                    return Relationship(source=source, target=target, relation_type="related_to")
                    
        except Exception:
            pass
        return None
    
    def extract_from_documents(
        self,
        documents_chunks: List[List[Dict[str, Any]]],
        show_progress: bool = True,
        batch_size: int = 0,
        reconcile_types: bool = True
    ) -> Tuple[List[Entity], List[Relationship], Dict[str, List[str]]]:
        """
        Extract from MULTIPLE documents with ADDITIVE ontology discovery.
        
        This method:
        1. Discovers entity types from EACH document and ACCUMULATES them
        2. Reconciles related types across documents (e.g., Product ↔ ProductSpec)
        3. Creates cross-type relationships for related entity types
        
        Args:
            documents_chunks: List of chunk lists, one per document
            show_progress: Print progress
            batch_size: Chunks per batch (0 = one-by-one)
            reconcile_types: Whether to reconcile and relate entity types
            
        Returns:
            Tuple of (entities, relationships, chunk_entity_map)
        """
        all_entities = {}
        all_relationships = set()
        chunk_entity_map = {}
        
        if not documents_chunks:
            raise ValueError("No documents provided")
        
        # Phase 1: ADDITIVE ontology discovery from all documents
        if show_progress:
            print("  📊 Phase 1: Discovering ontology from ALL documents (additive)...")
        
        for doc_idx, chunks in enumerate(documents_chunks):
            if not chunks:
                continue
            
            # Sample from this document
            sample_text = "\n\n".join([c.get('text', '')[:800] for c in chunks[:2]])
            
            if doc_idx == 0:
                # First document: full discovery
                self.discover_ontology(sample_text)
            else:
                # Subsequent documents: add to existing ontology
                self.add_to_ontology(sample_text)
            
            if show_progress:
                print(f"     Doc {doc_idx + 1}: {len(self.discovered_entity_types)} types accumulated")
        
        if show_progress:
            print(f"     Final ontology: {self.discovered_entity_types}")
        
        # Phase 2: Reconcile entity types if requested
        type_relationships = []
        if reconcile_types and len(self.discovered_entity_types) > 3:
            if show_progress:
                print("  🔗 Phase 2: Reconciling entity types across documents...")
            type_relationships = self.reconcile_entity_types()
            if show_progress and type_relationships:
                for rel_type, t1, t2, expl in type_relationships:
                    print(f"     {t1} --[{rel_type}]--> {t2}: {expl[:50]}...")
        
        # Phase 3: Extract from all documents
        if show_progress:
            print("  🔍 Phase 3: Extracting entities and relationships...")
        
        for doc_idx, chunks in enumerate(documents_chunks):
            for chunk in chunks:
                chunk_id = chunk.get('id', '')
                text = chunk.get('text', '')
                
                entities, relationships = self.extract(text)
                
                entity_names = []
                for entity in entities:
                    key = entity.name.lower()
                    if key not in all_entities:
                        all_entities[key] = entity
                    entity_names.append(entity.name)
                
                for rel in relationships:
                    all_relationships.add(rel)
                
                chunk_entity_map[chunk_id] = entity_names
        
        # Phase 4: Create cross-type relationships
        if type_relationships:
            if show_progress:
                print("  🌐 Phase 4: Creating cross-type relationships...")
            cross_rels = self.create_cross_type_relationships(
                list(all_entities.values()), 
                type_relationships
            )
            for rel in cross_rels:
                all_relationships.add(rel)
            if show_progress:
                print(f"     Created {len(cross_rels)} cross-type relationships")
        
        if show_progress:
            print(f"  ✅ Total: {len(all_entities)} entities, {len(all_relationships)} relationships")
        
        return list(all_entities.values()), list(all_relationships), chunk_entity_map
    
    def extract_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
        show_progress: bool = True,
        batch_size: int = 0,
        discover_ontology_first: bool = True
    ) -> Tuple[List[Entity], List[Relationship], Dict[str, List[str]]]:
        """
        Extract from multiple chunks with mandatory ontology discovery.
        
        For multi-document extraction with additive ontology, use extract_from_documents().
        
        The ontology (entity types) is DISCOVERED from the document content,
        not predefined. 
        
        Args:
            chunks: List of chunk dicts with 'id' and 'text'
            show_progress: Print progress
            batch_size: Chunks per batch (0 = one-by-one)
            discover_ontology_first: Must be True - ontology discovery is required
            
        Returns:
            Tuple of (entities, relationships, chunk_entity_map)
            
        Raises:
            ValueError: If ontology discovery fails or is disabled
        """
        if not discover_ontology_first:
            raise ValueError("Ontology discovery is required. Set discover_ontology_first=True")
        
        all_entities = {}  # name_lower -> Entity
        all_relationships = set()
        chunk_entity_map = {}
        
        total = len(chunks)
        if total == 0:
            raise ValueError("No chunks provided for extraction")
        
        # Phase 1: Ontology discovery from sample chunks (REQUIRED)
        if show_progress:
            print("  📊 Phase 1: Discovering domain ontology from documents...")
        
        # Use first 3 chunks for ontology discovery
        sample_text = "\n\n".join([c.get('text', '')[:1000] for c in chunks[:3]])
        self.discover_ontology(sample_text)  # Will raise ValueError if it fails
        
        if show_progress:
            print(f"     Domain: {self.domain}")
            print(f"     Discovered entity types: {self.discovered_entity_types}")
        
        # Phase 2: Extract entities and relationships
        if show_progress:
            print("  🔍 Phase 2: Extracting entities and relationships...")
        
        if batch_size > 0:
            # Batch extraction
            entities_list, rels_list, chunk_map = self._extract_batched(
                chunks, show_progress, batch_size
            )
            for e in entities_list:
                all_entities[e.name.lower()] = e
            all_relationships.update(rels_list)
            chunk_entity_map = chunk_map
        else:
            # One-by-one extraction
            for i, chunk in enumerate(chunks):
                if show_progress:
                    print(f"     Chunk {i+1}/{total}...", end="\r")
                
                chunk_id = chunk.get('id', f'chunk_{i}')
                text = chunk.get('text', '')
                
                entities, relationships = self.extract(text)
                
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
            print(f"  ✅ Extracted {len(all_entities)} entities, {len(all_relationships)} relationships")
            
            # Show type distribution
            type_counts = {}
            for e in all_entities.values():
                type_counts[e.type] = type_counts.get(e.type, 0) + 1
            print(f"     Type distribution: {dict(sorted(type_counts.items(), key=lambda x: -x[1])[:8])}")
        
        return list(all_entities.values()), list(all_relationships), chunk_entity_map
    
    def _extract_batched(
        self,
        chunks: List[Dict[str, Any]],
        show_progress: bool,
        batch_size: int
    ) -> Tuple[List[Entity], List[Relationship], Dict[str, List[str]]]:
        """Batch extraction with better chunk handling."""
        all_entities = []
        all_relationships = []
        chunk_entity_map = {}
        
        total = len(chunks)
        num_batches = (total + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, total)
            batch = chunks[start:end]
            
            if show_progress:
                print(f"     Batch {batch_idx+1}/{num_batches} (chunks {start+1}-{end})...", end="\r")
            
            for chunk in batch:
                chunk_id = chunk.get('id', '')
                text = chunk.get('text', '')
                
                entities, relationships = self.extract(text)
                
                entity_names = []
                for e in entities:
                    all_entities.append(e)
                    entity_names.append(e.name)
                
                all_relationships.extend(relationships)
                chunk_entity_map[chunk_id] = entity_names
        
        return all_entities, all_relationships, chunk_entity_map
    
    def get_discovered_schema(self) -> Dict[str, Any]:
        """
        Return the discovered ontology/schema.
        Useful for inspecting what types were discovered from the documents.
        """
        return {
            "domain": self.domain,
            "entity_types": self.discovered_entity_types
        }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing EntityExtractorV2 (Dynamic Ontology)")
    print("=" * 60)
    print("NOTE: No hardcoded schema - all types discovered from documents!")
    print()
    
    # Test type cleaning
    print("1. Testing type label cleaning:")
    test_types = ["fee type", "PERSON", "account_status", "Interest Rate"]
    for t in test_types:
        cleaned = clean_type_label(t)
        print(f"   '{t}' → '{cleaned}'")
    
    print("\n2. Testing relationship label cleaning:")
    test_rels = ["works at", "triggers when", "is part of"]
    for r in test_rels:
        cleaned = clean_relationship_label(r)
        print(f"   '{r}' → '{cleaned}'")
    
    # Test line parsing
    print("\n3. Testing line format parsing:")
    extractor = EntityExtractorV2()
    
    test_output = '''ENTITY: JOINING FEE | FEETYPE | One-time fee of Rs. 500 charged when card is issued
ENTITY: ANNUAL FEE | FEETYPE | Yearly membership fee of Rs. 1000
ENTITY: NPA | ACCOUNTSTATUS | Non-performing asset classification after 90 days
RELATIONSHIP: JOINING FEE | CARD ISSUANCE | triggered by | 8
RELATIONSHIP: NPA | 90 DPD THRESHOLD | occurs after | 9'''
    
    entities, relationships = extractor._parse_extraction_output(test_output)
    print(f"   Parsed {len(entities)} entities:")
    for e in entities:
        print(f"     - {e.name} ({e.type}): {e.description[:50]}...")
    print(f"   Parsed {len(relationships)} relationships:")
    for r in relationships:
        print(f"     - {r.source} --[{r.relation_type}]--> {r.target} (strength: {r.strength})")
    
    # Test full extraction with LLM
    print("\n4. Testing full extraction with LLM...")
    test_text = """
    The credit card policy defines several fees:
    1. Joining Fee: Rs. 500, charged at card issuance
    2. Annual Membership Fee: Rs. 1000, charged yearly
    3. Cash Advance Fee: 2.5% of amount, charged per transaction
    4. Late Payment Charge: Rs. 750, triggered when payment is overdue
    
    If the cardholder fails to pay within 90 days (>90 DPD), the account 
    is classified as NPA and collection proceedings begin.
    """
    
    try:
        # Discover ontology
        print("\n   Discovering ontology from text...")
        ontology = extractor.discover_ontology(test_text)
        print(f"   Domain: {ontology.get('domain')}")
        print(f"   Discovered entity types: {ontology.get('entity_types')}")
        
        # Extract
        print("\n   Extracting entities and relationships...")
        entities, relationships = extractor.extract(test_text)
        
        print(f"\n   Extracted {len(entities)} entities:")
        for e in entities[:10]:
            print(f"     - {e.name} ({e.type})")
            if e.description:
                print(f"       Desc: {e.description[:60]}...")
        
        print(f"\n   Extracted {len(relationships)} relationships:")
        for r in relationships[:10]:
            print(f"     - {r.source} --[{r.relation_type}]--> {r.target} (strength: {r.strength})")
            
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
