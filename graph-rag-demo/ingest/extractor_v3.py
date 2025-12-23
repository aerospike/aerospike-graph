"""
Entity Extractor v3 - Hindsight-Inspired Architecture

Core Concepts (from Hindsight/TEMPR):
1. CANONICAL ENTITIES: All entity mentions resolve to a single canonical form
2. ENTITY REGISTRY: Central registry of known entities with embeddings
3. UNIFIED EXTRACTION: Extract entities, relationships, facts in one pass
4. CROSS-DOCUMENT LINKING: Same entity across documents → same canonical entity

Architecture:
- EntityRegistry: Persistent store of canonical entities + embeddings
- CanonicalResolver: Resolves mentions to canonical entities using embeddings
- UnifiedExtractor: Single-pass extraction of entities + relationships + facts
"""

import sys
import os
import json
import re
import hashlib
import requests
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# =============================================================================
# PHASE 1: ENTITY REGISTRY & CANONICAL RESOLUTION
# =============================================================================

@dataclass
class CanonicalEntity:
    """
    A canonical entity - the single source of truth for an entity.
    All mentions of this entity across all documents resolve to this.
    """
    id: str                          # Unique canonical ID
    canonical_name: str              # The authoritative name
    entity_type: str                 # e.g., "Person", "Company", "Product"
    description: str                 # Aggregated/summarized description
    embedding: Optional[List[float]] # Embedding vector for similarity matching
    aliases: Set[str] = field(default_factory=set)  # All known aliases
    mention_count: int = 0           # How many times mentioned across docs
    source_docs: Set[str] = field(default_factory=set)  # Which docs mention this
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # NEW: Track all raw descriptions for later summarization
    raw_descriptions: List[str] = field(default_factory=list)
    description_summarized: bool = False  # Whether description has been LLM-summarized
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'canonical_name': self.canonical_name,
            'entity_type': self.entity_type,
            'description': self.description,
            'aliases': list(self.aliases),
            'mention_count': self.mention_count,
            'source_docs': list(self.source_docs),
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'description_summarized': self.description_summarized,
        }


@dataclass 
class EntityMention:
    """
    A mention of an entity in text - before resolution to canonical form.
    """
    text: str                        # The exact text mention
    entity_type: str                 # Detected type
    description: str                 # Context/description from extraction
    source_doc: str                  # Which document
    source_chunk: str                # Which chunk
    context: str = ""                # Surrounding text for disambiguation


@dataclass
class ExtractedFact:
    """
    A fact extracted from text - Hindsight style.
    Facts are the atomic unit, containing entities + relationships inherently.
    """
    subject: str                     # Subject entity
    predicate: str                   # Relationship/action
    object: str                      # Object entity or value
    confidence: float = 1.0
    source_doc: str = ""
    source_chunk: str = ""
    temporal_marker: Optional[str] = None  # e.g., "in 2024", "currently"


class EmbeddingService:
    """
    Wrapper for embedding generation - used for entity similarity matching.
    """
    
    def __init__(self):
        self.model = config.OLLAMA_EMBED_MODEL
        self.base_url = config.OLLAMA_BASE_URL
        self.cache: Dict[str, List[float]] = {}
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text, with caching."""
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": text},
                timeout=30
            )
            if response.status_code == 200:
                embedding = response.json().get('embeddings', [[]])[0]
                self.cache[cache_key] = embedding
                return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
        
        return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(t) for t in texts]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    
    a_np = np.array(a)
    b_np = np.array(b)
    
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(a_np, b_np) / (norm_a * norm_b))


class EntityRegistry:
    """
    Central registry of all canonical entities.
    
    This is the core of the Hindsight-inspired approach:
    - Maintains a single source of truth for all entities
    - Uses embeddings for similarity-based matching
    - Supports cross-document entity resolution
    """
    
    # Similarity thresholds for entity matching
    # VERY CONSERVATIVE to avoid over-merging different entities
    SAME_TYPE_THRESHOLD = 0.98      # Same type entities - extremely high
    DIFF_TYPE_THRESHOLD = 0.995     # Different type - almost never match cross-type
    MIN_NAME_OVERLAP = 0.7          # Require significant name overlap before considering embedding
    
    # Entity types that should NEVER use embedding fallback (require exact/alias match)
    EXACT_MATCH_TYPES = {'person', 'team', 'product', 'company', 'project'}
    
    def __init__(self, debug: bool = False):
        self.entities: Dict[str, CanonicalEntity] = {}  # id -> entity
        self.name_index: Dict[str, str] = {}  # lowercase name -> canonical id
        self.type_index: Dict[str, Set[str]] = {}  # type -> set of canonical ids
        self.embedding_service = EmbeddingService()
        self._embedding_cache: Dict[str, List[float]] = {}  # entity_id -> embedding
        self.debug = debug
    
    def _generate_canonical_id(self, name: str, entity_type: str) -> str:
        """Generate a unique canonical ID for an entity."""
        # Use hash of normalized name + type for stability
        normalized = f"{name.lower().strip()}:{entity_type.lower()}"
        return f"canonical:{hashlib.md5(normalized.encode()).hexdigest()[:12]}"
    
    def _get_entity_embedding(self, entity_id: str) -> List[float]:
        """Get or compute embedding for an entity."""
        if entity_id in self._embedding_cache:
            return self._embedding_cache[entity_id]
        
        entity = self.entities.get(entity_id)
        if entity and entity.embedding:
            self._embedding_cache[entity_id] = entity.embedding
            return entity.embedding
        
        return []
    
    def _name_similarity_score(self, name1: str, name2: str) -> float:
        """
        Compute name-based similarity heuristics.
        Catches patterns like "A. Chen" matching "Alex Chen".
        """
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        if n1 == n2:
            return 1.0
        
        # Check if one is abbreviation of the other
        # "A. Chen" vs "Alex Chen"
        parts1 = n1.replace('.', ' ').split()
        parts2 = n2.replace('.', ' ').split()
        
        # Same last name/word?
        if parts1 and parts2 and parts1[-1] == parts2[-1]:
            # Check if first part is initial
            if len(parts1) > 1 and len(parts2) > 1:
                # "A" matches "Alex" (initial match)
                if len(parts1[0]) == 1 and parts2[0].startswith(parts1[0]):
                    return 0.9
                if len(parts2[0]) == 1 and parts1[0].startswith(parts2[0]):
                    return 0.9
                # "Alex" vs "Alexander" (prefix match)
                if parts1[0].startswith(parts2[0]) or parts2[0].startswith(parts1[0]):
                    return 0.85
        
        # Check containment (one name contained in the other)
        if n1 in n2 or n2 in n1:
            return 0.7
        
        # Word overlap
        words1 = set(parts1)
        words2 = set(parts2)
        if words1 and words2:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap > 0.5:
                return 0.5 + overlap * 0.3
        
        return 0.0
    
    def find_matching_entity(
        self, 
        mention: EntityMention
    ) -> Optional[CanonicalEntity]:
        """
        Find a canonical entity that matches this mention.
        
        Uses multi-signal matching:
        1. Exact name match (fastest)
        2. Alias match
        3. Name heuristics (abbreviations, initials)
        4. Embedding similarity (most robust)
        """
        mention_lower = mention.text.lower().strip()
        
        # 1. Exact name match
        if mention_lower in self.name_index:
            entity_id = self.name_index[mention_lower]
            if self.debug:
                print(f"      [Match] Exact: '{mention.text}' → '{self.entities[entity_id].canonical_name}'")
            return self.entities.get(entity_id)
        
        # 2. Check all aliases
        for entity_id, entity in self.entities.items():
            if mention_lower in {a.lower() for a in entity.aliases}:
                if self.debug:
                    print(f"      [Match] Alias: '{mention.text}' → '{entity.canonical_name}'")
                return entity
        
        # 3. Name heuristics (for same-type entities)
        for entity_id, entity in self.entities.items():
            if mention.entity_type.lower() == entity.entity_type.lower():
                name_sim = self._name_similarity_score(mention.text, entity.canonical_name)
                if name_sim >= 0.85:
                    if self.debug:
                        print(f"      [Match] Name heuristic ({name_sim:.2f}): '{mention.text}' → '{entity.canonical_name}'")
                    return entity
        
        # 4. Embedding-based similarity matching
        # SKIP for entity types that are prone to false merges (people, teams, products)
        if mention.entity_type.lower() in self.EXACT_MATCH_TYPES:
            if self.debug:
                print(f"      [New] '{mention.text}' ({mention.entity_type}) - no embedding match for this type")
            return None
        
        # Use ONLY the name for embedding - description causes false matches
        embed_text = f"{mention.text} ({mention.entity_type})"
        mention_embedding = self.embedding_service.embed(embed_text)
        
        if not mention_embedding:
            return None
        
        best_match: Optional[CanonicalEntity] = None
        best_score = 0.0
        
        for entity_id, entity in self.entities.items():
            # CRITICAL: Require minimum name similarity before considering embedding
            name_sim = self._name_similarity_score(mention.text, entity.canonical_name)
            if name_sim < self.MIN_NAME_OVERLAP:
                continue  # Skip if names are completely different
            
            entity_embedding = self._get_entity_embedding(entity_id)
            if not entity_embedding:
                continue
            
            # Compute embedding similarity
            emb_similarity = cosine_similarity(mention_embedding, entity_embedding)
            
            # Adjust threshold based on type match
            threshold = (
                self.SAME_TYPE_THRESHOLD 
                if mention.entity_type.lower() == entity.entity_type.lower()
                else self.DIFF_TYPE_THRESHOLD
            )
            
            if emb_similarity > threshold and emb_similarity > best_score:
                best_score = emb_similarity
                best_match = entity
                if self.debug:
                    print(f"      [Match] Embedding ({emb_similarity:.2f}, name={name_sim:.2f}): '{mention.text}' → '{entity.canonical_name}'")
        
        if self.debug and not best_match:
            print(f"      [New] No match for '{mention.text}' ({mention.entity_type})")
        
        return best_match
    
    def register_entity(
        self, 
        mention: EntityMention,
        force_new: bool = False
    ) -> CanonicalEntity:
        """
        Register a mention and resolve to canonical entity.
        
        Either finds existing canonical entity or creates new one.
        Returns the canonical entity.
        """
        # Try to find existing match
        if not force_new:
            existing = self.find_matching_entity(mention)
            if existing:
                # Update existing entity with new info
                existing.aliases.add(mention.text)
                existing.mention_count += 1
                existing.source_docs.add(mention.source_doc)
                existing.last_seen = datetime.now()
                
                # Track raw descriptions for later LLM summarization
                if mention.description and mention.description.strip():
                    existing.raw_descriptions.append(mention.description.strip())
                    # For now, just concatenate (will be summarized later)
                    if mention.description not in existing.description:
                        existing.description = f"{existing.description} | {mention.description}".strip(' |')
                
                # Update name index with new alias
                self.name_index[mention.text.lower().strip()] = existing.id
                
                return existing
        
        # Create new canonical entity
        canonical_id = self._generate_canonical_id(mention.text, mention.entity_type)
        
        # Generate embedding for new entity - use only name+type for consistency
        embed_text = f"{mention.text} ({mention.entity_type})"
        embedding = self.embedding_service.embed(embed_text)
        
        new_entity = CanonicalEntity(
            id=canonical_id,
            canonical_name=mention.text,
            entity_type=mention.entity_type,
            description=mention.description,
            embedding=embedding,
            aliases={mention.text},
            mention_count=1,
            source_docs={mention.source_doc},
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            raw_descriptions=[mention.description] if mention.description else []
        )
        
        # Register in all indexes
        self.entities[canonical_id] = new_entity
        self.name_index[mention.text.lower().strip()] = canonical_id
        self._embedding_cache[canonical_id] = embedding
        
        # Type index
        type_lower = mention.entity_type.lower()
        if type_lower not in self.type_index:
            self.type_index[type_lower] = set()
        self.type_index[type_lower].add(canonical_id)
        
        return new_entity
    
    def get_entities_by_type(self, entity_type: str) -> List[CanonicalEntity]:
        """Get all canonical entities of a given type."""
        type_lower = entity_type.lower()
        if type_lower not in self.type_index:
            return []
        return [self.entities[eid] for eid in self.type_index[type_lower]]
    
    def get_all_entities(self) -> List[CanonicalEntity]:
        """Get all canonical entities."""
        return list(self.entities.values())
    
    def get_cross_doc_entities(self) -> List[CanonicalEntity]:
        """Get entities that appear in multiple documents."""
        return [e for e in self.entities.values() if len(e.source_docs) > 1]
    
    def stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        type_counts = {}
        for entity in self.entities.values():
            t = entity.entity_type
            type_counts[t] = type_counts.get(t, 0) + 1
        
        cross_doc = len(self.get_cross_doc_entities())
        
        return {
            'total_entities': len(self.entities),
            'type_distribution': type_counts,
            'cross_document_entities': cross_doc,
            'total_aliases': sum(len(e.aliases) for e in self.entities.values()),
        }


# =============================================================================
# PHASE 2: UNIFIED EXTRACTION (Hindsight-style single-pass)
# =============================================================================

class UnifiedExtractor:
    """
    Single-pass extractor that extracts entities, relationships, and facts together.
    
    Key difference from v2:
    - Extracts FACTS (subject-predicate-object) not just entities
    - Facts inherently capture relationships
    - Immediate resolution to canonical entities via EntityRegistry
    """
    
    # Unified extraction prompt - focused on proper entity extraction
    EXTRACTION_PROMPT = """Extract entities and relationships from this text. Output ONLY valid JSON.

TEXT:
{text}

ENTITY RULES:
1. Person = human names (e.g., "Emily Watson"), NOT job titles
2. Team = teams/departments (e.g., "Platform Team")
3. Product = software/systems (e.g., "NexusDB", "GraphSync")
4. Project = project codes (e.g., "NEXUS-1542")
5. Company = organizations (e.g., "Acme Corp")

RELATIONSHIP RULES:
- Extract who leads/manages which team
- Extract who reports to whom
- Extract who works on which product/project

OUTPUT FORMAT:
{{"entities":[{{"name":"...","type":"Person|Team|Product|Project|Company","description":"..."}}],"facts":[{{"subject":"Emily Watson","predicate":"leads","object":"Platform Team"}}]}}

OUTPUT JSON ONLY:"""

    # Gleaning prompt - MS GraphRAG inspired multi-pass extraction
    GLEANING_PROMPT = """The previous extraction may have missed some entities or relationships.

ORIGINAL TEXT:
{text}

ALREADY EXTRACTED:
Entities: {existing_entities}
Facts: {existing_facts}

TASK: Find any ADDITIONAL entities or relationships that were missed.
Focus on:
- People mentioned but not extracted
- Teams, products, or projects referenced indirectly
- Relationships between already-extracted entities

If you find more, output them in the same JSON format. If nothing was missed, output: {{"entities":[],"facts":[]}}

OUTPUT JSON ONLY:"""

    # Description summarization prompt
    SUMMARIZE_PROMPT = """You are summarizing multiple descriptions of the same entity into one coherent description.

ENTITY: {entity_name} ({entity_type})

DESCRIPTIONS FROM DIFFERENT SOURCES:
{descriptions}

Create a single, comprehensive description that:
1. Includes all unique information from the descriptions
2. Resolves any contradictions by preferring more specific information
3. Is written in third person
4. Is no longer than 100 words

OUTPUT (description only, no quotes or formatting):"""

    def __init__(self, registry: EntityRegistry, max_gleanings: int = 1):
        self.registry = registry
        self.provider = getattr(config, 'LLM_PROVIDER', 'ollama')
        self.max_gleanings = max_gleanings  # Number of gleaning passes (MS GraphRAG style)
        
        # Ollama config
        self.llm_url = config.OLLAMA_BASE_URL
        self.llm_model = config.OLLAMA_MODEL
        
        # Claude config
        self.claude_model = getattr(config, 'CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        self.anthropic_client = None
        
        if self.provider == 'claude':
            try:
                import anthropic
                api_key = getattr(config, 'ANTHROPIC_API_KEY', '')
                if api_key:
                    self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                    print(f"Using Claude ({self.claude_model}) for extraction")
                else:
                    print("Warning: ANTHROPIC_API_KEY not set, falling back to Ollama")
                    self.provider = 'ollama'
            except ImportError:
                print("Warning: anthropic package not installed, falling back to Ollama")
                self.provider = 'ollama'
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for extraction (supports Ollama and Claude)."""
        if self.provider == 'claude' and self.anthropic_client:
            return self._call_claude(prompt)
        else:
            return self._call_ollama(prompt)
    
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API for extraction."""
        try:
            message = self.anthropic_client.messages.create(
                model=self.claude_model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude error: {e}")
            return ""
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama for extraction."""
        try:
            response = requests.post(
                f"{self.llm_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 4096}
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            print(f"Ollama error: {e}")
        return ""
    
    def _parse_extraction(self, llm_output: str) -> Tuple[List[Dict], List[Dict]]:
        """Parse LLM output into entities and facts."""
        entities = []
        facts = []
        
        # Remove markdown code blocks if present
        cleaned = llm_output
        if '```json' in cleaned:
            cleaned = re.sub(r'```json\s*', '', cleaned)
            cleaned = re.sub(r'```\s*$', '', cleaned)
        elif '```' in cleaned:
            # Remove generic code blocks
            cleaned = re.sub(r'```\s*', '', cleaned)
        
        # Find JSON in output
        try:
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            if start >= 0 and end > 0:
                json_str = cleaned[start:end]
                # Clean common issues
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                data = json.loads(json_str)
                
                entities = data.get('entities', [])
                facts = data.get('facts', [])
        except json.JSONDecodeError as e:
            # Fallback: try to extract entities from text patterns
            entity_pattern = r'"name":\s*"([^"]+)".*?"type":\s*"([^"]+)".*?"description":\s*"([^"]*)"'
            for match in re.finditer(entity_pattern, llm_output, re.DOTALL):
                entities.append({
                    'name': match.group(1),
                    'type': match.group(2),
                    'description': match.group(3)
                })
        
        return entities, facts
    
    def summarize_descriptions(
        self, 
        entity_name: str, 
        entity_type: str, 
        descriptions: List[str]
    ) -> str:
        """
        Use LLM to summarize multiple descriptions into one coherent description.
        
        MS GraphRAG-inspired feature: When same entity has different descriptions
        from different chunks/documents, use LLM to resolve conflicts and create
        a comprehensive summary.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of the entity  
            descriptions: List of descriptions from different sources
            
        Returns:
            A single summarized description
        """
        # If only one description, return it as-is
        if len(descriptions) <= 1:
            return descriptions[0] if descriptions else ""
        
        # Filter out empty/duplicate descriptions
        unique_descriptions = list(set([d.strip() for d in descriptions if d.strip()]))
        if len(unique_descriptions) <= 1:
            return unique_descriptions[0] if unique_descriptions else ""
        
        # Format descriptions for prompt
        numbered_descriptions = "\n".join([
            f"{i+1}. {desc}" for i, desc in enumerate(unique_descriptions)
        ])
        
        prompt = self.SUMMARIZE_PROMPT.format(
            entity_name=entity_name,
            entity_type=entity_type,
            descriptions=numbered_descriptions
        )
        
        summarized = self._call_llm(prompt)
        
        # Clean up the summary (remove quotes, extra whitespace)
        summarized = summarized.strip().strip('"\'')
        
        # If LLM failed, fall back to concatenation
        if not summarized or len(summarized) < 10:
            return " | ".join(unique_descriptions[:3])  # Limit to 3 descriptions
        
        return summarized
    
    def extract_and_resolve(
        self, 
        text: str, 
        source_doc: str,
        source_chunk: str
    ) -> Tuple[List[CanonicalEntity], List[ExtractedFact]]:
        """
        Extract entities and facts from text, resolving to canonical entities.
        
        Uses MS GraphRAG-style gleaning loop to catch missed entities.
        
        Returns:
        - List of canonical entities (new or existing)
        - List of extracted facts
        """
        text_truncated = text[:3000]  # Limit text size
        
        # Initial extraction
        prompt = self.EXTRACTION_PROMPT.format(text=text_truncated)
        llm_output = self._call_llm(prompt)
        raw_entities, raw_facts = self._parse_extraction(llm_output)
        
        # Gleaning loop - MS GraphRAG style multi-pass extraction
        if self.max_gleanings > 0 and (raw_entities or raw_facts):
            for gleaning_round in range(self.max_gleanings):
                # Format existing entities and facts for context
                existing_entities = ", ".join([e.get('name', '') for e in raw_entities])
                existing_facts = ", ".join([
                    f"{f.get('subject', '')} {f.get('predicate', '')} {f.get('object', '')}" 
                    for f in raw_facts
                ])
                
                # Ask for additional extractions
                gleaning_prompt = self.GLEANING_PROMPT.format(
                    text=text_truncated,
                    existing_entities=existing_entities or "None",
                    existing_facts=existing_facts or "None"
                )
                
                gleaning_output = self._call_llm(gleaning_prompt)
                new_entities, new_facts = self._parse_extraction(gleaning_output)
                
                # If no new entities/facts found, stop gleaning
                if not new_entities and not new_facts:
                    break
                
                # Add new extractions (avoiding duplicates by name)
                existing_names = {
                    (e.get('name', '') if isinstance(e, dict) else str(e)).lower() 
                    for e in raw_entities
                }
                for ent in new_entities:
                    # Handle case where entity might be string or dict
                    if isinstance(ent, dict):
                        ent_name = ent.get('name', '').lower()
                        if ent_name and ent_name not in existing_names:
                            raw_entities.append(ent)
                            existing_names.add(ent_name)
                
                raw_facts.extend(new_facts)
        
        canonical_entities = []
        entity_name_to_canonical: Dict[str, CanonicalEntity] = {}
        
        # Resolve each entity mention to canonical form
        for ent in raw_entities:
            # Skip if entity is not a dict (malformed output)
            if not isinstance(ent, dict):
                continue
                
            mention = EntityMention(
                text=ent.get('name', ''),
                entity_type=ent.get('type', 'Unknown'),
                description=ent.get('description', ''),
                source_doc=source_doc,
                source_chunk=source_chunk,
                context=text[:200]
            )
            
            if not mention.text:
                continue
            
            # Resolve to canonical entity
            canonical = self.registry.register_entity(mention)
            canonical_entities.append(canonical)
            entity_name_to_canonical[mention.text.lower()] = canonical
        
        # Process facts AND create entities from subjects/objects that don't exist
        extracted_facts = []
        for fact in raw_facts:
            # Skip if fact is not a dict (malformed output)
            if not isinstance(fact, dict):
                continue
                
            subject = fact.get('subject', '')
            predicate = fact.get('predicate', '')
            obj = fact.get('object', '')
            
            if not subject or not predicate or not obj:
                continue
            
            # Create entity for subject if it doesn't exist
            if subject.lower() not in entity_name_to_canonical:
                subject_type = self._infer_entity_type(subject, predicate, is_subject=True)
                mention = EntityMention(
                    text=subject,
                    entity_type=subject_type,
                    description=f"Referenced in: {predicate} {obj}",
                    source_doc=source_doc,
                    source_chunk=source_chunk,
                    context=text[:200]
                )
                canonical = self.registry.register_entity(mention)
                canonical_entities.append(canonical)
                entity_name_to_canonical[subject.lower()] = canonical
            
            # Create entity for object if it looks like an entity (not a value)
            if obj.lower() not in entity_name_to_canonical and self._looks_like_entity(obj):
                obj_type = self._infer_entity_type(obj, predicate, is_subject=False)
                mention = EntityMention(
                    text=obj,
                    entity_type=obj_type,
                    description=f"Referenced by: {subject} {predicate}",
                    source_doc=source_doc,
                    source_chunk=source_chunk,
                    context=text[:200]
                )
                canonical = self.registry.register_entity(mention)
                canonical_entities.append(canonical)
                entity_name_to_canonical[obj.lower()] = canonical
            
            extracted_facts.append(ExtractedFact(
                subject=subject,
                predicate=predicate,
                object=obj,
                source_doc=source_doc,
                source_chunk=source_chunk,
                temporal_marker=fact.get('temporal')
            ))
        
        return canonical_entities, extracted_facts
    
    def _looks_like_entity(self, text: str) -> bool:
        """Check if text looks like an entity name vs a value."""
        text = text.strip()
        
        # Skip pure numbers
        if text.replace('.', '').replace(',', '').isdigit():
            return False
        
        # Skip very short strings
        if len(text) < 2:
            return False
        
        # Skip common non-entity patterns
        non_entity_patterns = [
            'true', 'false', 'yes', 'no', 'none', 'null',
            'etc', 'and', 'or', 'the', 'a', 'an'
        ]
        if text.lower() in non_entity_patterns:
            return False
        
        # Entities typically start with capital letter or are proper nouns
        if text[0].isupper() or ' ' in text:
            return True
        
        # Check for entity-like patterns (contains Team, Project, etc.)
        entity_keywords = ['team', 'project', 'system', 'department', 'group', 'committee']
        if any(kw in text.lower() for kw in entity_keywords):
            return True
        
        return len(text) > 3  # Short strings less likely to be entities
    
    def _infer_entity_type(self, name: str, predicate: str, is_subject: bool) -> str:
        """
        Infer entity type using configurable domain rules.
        
        Rules are defined in domain_config/domain_rules.py and can be customized
        for different domains without modifying extraction code.
        """
        try:
            from domain_config.domain_rules import infer_entity_type
            return infer_entity_type(name, predicate, is_subject)
        except ImportError:
            # Fallback if config not available - use generic type
            return 'Entity'


# =============================================================================
# PHASE 3: CROSS-DOCUMENT ENTITY LINKER
# =============================================================================

class CrossDocumentLinker:
    """
    Links entities across documents and maintains relationship graph.
    
    After extraction from multiple documents, this class:
    1. Identifies entities that appear across documents
    2. Merges similar entities that weren't caught during extraction
    3. Builds a relationship graph from extracted facts
    """
    
    def __init__(self, registry: EntityRegistry):
        self.registry = registry
        self.relationships: List[Tuple[str, str, str]] = []  # (source_id, predicate, target_id)
    
    def post_process_merge(self, similarity_threshold: float = 0.97) -> int:
        """
        Post-processing pass to merge entities that should be the same.
        
        Sometimes during extraction, the same entity gets registered twice
        if the mentions are different enough. This pass catches those.
        
        Returns number of merges performed.
        
        NOTE: Very conservative threshold (0.97) to avoid over-merging.
        """
        merge_count = 0
        entities = list(self.registry.entities.values())
        merged_ids: Set[str] = set()
        
        # Entity types that should NEVER be merged via embedding
        SKIP_MERGE_TYPES = {'person', 'team', 'product', 'company', 'project'}
        
        for i, entity_a in enumerate(entities):
            if entity_a.id in merged_ids:
                continue
                
            for entity_b in entities[i+1:]:
                if entity_b.id in merged_ids:
                    continue
                
                # Skip if different types (usually)
                if entity_a.entity_type.lower() != entity_b.entity_type.lower():
                    continue
                
                # SKIP embedding-based merge for entity types prone to false merges
                if entity_a.entity_type.lower() in SKIP_MERGE_TYPES:
                    # Only merge if names are exact match (already handled by alias matching)
                    continue
                
                # Check embedding similarity
                emb_a = self.registry._get_entity_embedding(entity_a.id)
                emb_b = self.registry._get_entity_embedding(entity_b.id)
                
                if not emb_a or not emb_b:
                    continue
                
                similarity = cosine_similarity(emb_a, emb_b)
                
                if similarity >= similarity_threshold:
                    # Merge B into A
                    self._merge_entities(entity_a, entity_b)
                    merged_ids.add(entity_b.id)
                    merge_count += 1
        
        # Clean up merged entities
        for merged_id in merged_ids:
            if merged_id in self.registry.entities:
                del self.registry.entities[merged_id]
        
        return merge_count
    
    def _merge_entities(
        self, 
        primary: CanonicalEntity, 
        secondary: CanonicalEntity
    ) -> None:
        """Merge secondary entity into primary."""
        # Merge aliases
        primary.aliases.update(secondary.aliases)
        primary.aliases.add(secondary.canonical_name)
        
        # Merge source docs
        primary.source_docs.update(secondary.source_docs)
        
        # Merge counts
        primary.mention_count += secondary.mention_count
        
        # Merge descriptions
        if secondary.description and secondary.description not in primary.description:
            primary.description = f"{primary.description} {secondary.description}".strip()
        
        # Update timestamps
        if secondary.first_seen and (not primary.first_seen or secondary.first_seen < primary.first_seen):
            primary.first_seen = secondary.first_seen
        if secondary.last_seen and (not primary.last_seen or secondary.last_seen > primary.last_seen):
            primary.last_seen = secondary.last_seen
        
        # Update name index to point to primary
        for alias in secondary.aliases:
            self.registry.name_index[alias.lower().strip()] = primary.id
        self.registry.name_index[secondary.canonical_name.lower().strip()] = primary.id
    
    def build_relationships_from_facts(
        self, 
        facts: List[ExtractedFact]
    ) -> List[Tuple[CanonicalEntity, str, CanonicalEntity]]:
        """
        Build relationships between canonical entities from extracted facts.
        
        Returns list of (source_entity, predicate, target_entity) tuples.
        """
        relationships = []
        
        for fact in facts:
            # Try to resolve subject and object to canonical entities
            subject_lower = fact.subject.lower().strip()
            object_lower = fact.object.lower().strip()
            
            source_entity = None
            target_entity = None
            
            # Check name index
            if subject_lower in self.registry.name_index:
                source_id = self.registry.name_index[subject_lower]
                source_entity = self.registry.entities.get(source_id)
            
            if object_lower in self.registry.name_index:
                target_id = self.registry.name_index[object_lower]
                target_entity = self.registry.entities.get(target_id)
            
            if source_entity and target_entity:
                relationships.append((source_entity, fact.predicate, target_entity))
                self.relationships.append((source_entity.id, fact.predicate, target_entity.id))
        
        return relationships
    
    def get_entity_graph(self) -> Dict[str, Any]:
        """
        Get the entity relationship graph.
        
        Returns dict with:
        - nodes: List of canonical entities
        - edges: List of relationships
        """
        return {
            'nodes': [e.to_dict() for e in self.registry.get_all_entities()],
            'edges': [
                {
                    'source': self.registry.entities[s].canonical_name if s in self.registry.entities else s,
                    'predicate': p,
                    'target': self.registry.entities[t].canonical_name if t in self.registry.entities else t
                }
                for s, p, t in self.relationships
            ]
        }


# =============================================================================
# MAIN EXTRACTOR CLASS - Combines all phases
# =============================================================================

class EntityExtractorV3:
    """
    Main extractor class that orchestrates all phases.
    
    Usage:
        extractor = EntityExtractorV3()
        
        # Process documents
        for doc in documents:
            for chunk in doc.chunks:
                extractor.process_chunk(chunk.text, doc.id, chunk.id)
        
        # Finalize (merge similar entities, build relationships)
        extractor.finalize()
        
        # Get results
        entities = extractor.get_canonical_entities()
        relationships = extractor.get_relationships()
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.registry = EntityRegistry(debug=debug)
        self.unified_extractor = UnifiedExtractor(self.registry)
        self.linker = CrossDocumentLinker(self.registry)
        self.all_facts: List[ExtractedFact] = []
        self._finalized = False
    
    def process_chunk(
        self, 
        text: str, 
        doc_id: str, 
        chunk_id: str
    ) -> Tuple[List[CanonicalEntity], List[ExtractedFact]]:
        """
        Process a single chunk of text.
        
        Extracts entities and facts, resolving to canonical forms.
        """
        entities, facts = self.unified_extractor.extract_and_resolve(
            text=text,
            source_doc=doc_id,
            source_chunk=chunk_id
        )
        
        self.all_facts.extend(facts)
        
        return entities, facts
    
    def finalize(self, summarize_descriptions: bool = True) -> Dict[str, Any]:
        """
        Finalize extraction after all documents processed.
        
        1. Summarize descriptions using LLM (MS GraphRAG feature)
        2. Post-process merge similar entities
        3. Build relationship graph from facts
        
        Args:
            summarize_descriptions: Whether to use LLM to summarize conflicting descriptions
        
        Returns summary statistics.
        """
        if self._finalized:
            return self.get_stats()
        
        descriptions_summarized = 0
        
        # Phase 0: Summarize descriptions for entities with multiple descriptions
        if summarize_descriptions:
            for entity in self.registry.get_all_entities():
                if len(entity.raw_descriptions) > 1 and not entity.description_summarized:
                    # Use LLM to create coherent summary
                    summarized = self.unified_extractor.summarize_descriptions(
                        entity_name=entity.canonical_name,
                        entity_type=entity.entity_type,
                        descriptions=entity.raw_descriptions
                    )
                    if summarized:
                        entity.description = summarized
                        entity.description_summarized = True
                        descriptions_summarized += 1
        
        # Phase 1: Merge similar entities
        merge_count = self.linker.post_process_merge()
        
        # Phase 2: Build relationships from facts
        relationships = self.linker.build_relationships_from_facts(self.all_facts)
        
        self._finalized = True
        
        return {
            'descriptions_summarized': descriptions_summarized,
            'entities_merged': merge_count,
            'relationships_created': len(relationships),
            **self.get_stats()
        }
    
    def get_canonical_entities(self) -> List[CanonicalEntity]:
        """Get all canonical entities."""
        return self.registry.get_all_entities()
    
    def get_cross_document_entities(self) -> List[CanonicalEntity]:
        """Get entities that appear in multiple documents."""
        return self.registry.get_cross_doc_entities()
    
    def get_relationships(self) -> List[Tuple[str, str, str]]:
        """Get all relationships as (source_id, predicate, target_id) tuples."""
        return self.linker.relationships
    
    def get_entity_graph(self) -> Dict[str, Any]:
        """Get full entity graph with nodes and edges."""
        return self.linker.get_entity_graph()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        registry_stats = self.registry.stats()
        return {
            **registry_stats,
            'total_facts': len(self.all_facts),
            'relationships': len(self.linker.relationships),
            'finalized': self._finalized
        }


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EntityExtractor V3 - Hindsight-Inspired")
    print("=" * 60)
    
    # Test with sample text
    test_texts = [
        {
            'doc_id': 'doc1',
            'chunk_id': 'chunk1',
            'text': """
            Acme Corp was founded by Sarah Chen in 2020. The company develops 
            NexusDB, a high-performance graph database. Alex Chen leads the 
            engineering team and reports to Sarah Chen. The platform team, 
            managed by Emily Watson, maintains the core infrastructure.
            """
        },
        {
            'doc_id': 'doc2', 
            'chunk_id': 'chunk2',
            'text': """
            Sarah Chen, CEO of Acme Corp, announced the Q4 roadmap. The roadmap
            includes GraphSync 2.0, led by Alex Chen's team. Emily Watson will
            handle the security review. A. Chen presented the technical specs.
            """
        }
    ]
    
    extractor = EntityExtractorV3()
    
    print("\n📄 Processing documents...")
    for item in test_texts:
        print(f"\n  Processing {item['doc_id']}/{item['chunk_id']}...")
        entities, facts = extractor.process_chunk(
            item['text'], 
            item['doc_id'], 
            item['chunk_id']
        )
        print(f"    Entities: {len(entities)}")
        print(f"    Facts: {len(facts)}")
    
    print("\n🔗 Finalizing (merging similar entities, building relationships)...")
    summary = extractor.finalize()
    
    print(f"\n📊 Results:")
    print(f"   Total canonical entities: {summary['total_entities']}")
    print(f"   Entities merged: {summary['entities_merged']}")
    print(f"   Cross-document entities: {summary['cross_document_entities']}")
    print(f"   Total facts: {summary['total_facts']}")
    print(f"   Relationships created: {summary['relationships_created']}")
    
    print(f"\n🏷️ Canonical Entities:")
    for entity in extractor.get_canonical_entities():
        cross_doc = "📚" if len(entity.source_docs) > 1 else ""
        aliases = f" (aliases: {', '.join(entity.aliases - {entity.canonical_name})})" if len(entity.aliases) > 1 else ""
        print(f"   • {entity.canonical_name} [{entity.entity_type}] {cross_doc}{aliases}")
    
    print(f"\n🔀 Relationships:")
    graph = extractor.get_entity_graph()
    for edge in graph['edges'][:10]:
        print(f"   • {edge['source']} --[{edge['predicate']}]--> {edge['target']}")

