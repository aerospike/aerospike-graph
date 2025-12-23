"""
Domain-Specific Entity Type Inference Rules

This file contains configurable rules for inferring entity types
when entities are found in relationships but not explicitly extracted.

CUSTOMIZATION:
- Modify NAME_PATTERNS to add domain-specific entity name patterns
- Modify PREDICATE_RULES to add relationship-based type inference
- Set DEFAULT_TYPE for entities that don't match any rule

These rules are applied when:
1. An entity appears in a fact (subject/object) but wasn't explicitly extracted
2. The extractor needs to create the entity and determine its type
"""

# =============================================================================
# NAME-BASED PATTERNS
# =============================================================================
# If entity name contains any of these keywords, assign the corresponding type
# Format: {"keyword": "EntityType"}

NAME_PATTERNS = {
    # Team/Department indicators
    "team": "Team",
    "department": "Team", 
    "group": "Team",
    "division": "Team",
    "unit": "Team",
    
    # Project indicators (common patterns)
    # Add your project code prefixes here
    # "PROJ-": "Project",
    # "JIRA-": "Project",
    
    # Product indicators
    "system": "Product",
    "platform": "Product",
    "service": "Product",
    
    # Location indicators
    "office": "Location",
    "headquarters": "Location",
    "region": "Location",
}

# =============================================================================
# PROJECT CODE PREFIXES
# =============================================================================
# Entity names starting with these prefixes are classified as Projects
# Add your organization's project code patterns here

PROJECT_PREFIXES = [
    "NEXUS-",    # Example: NEXUS-1542
    "SR-",       # Example: SR-2024-001 (Security Review)
    "INC-",      # Example: INC-2024-003 (Incident)
    "PROJ-",     # Generic project prefix
    # Add more prefixes as needed for your domain
]

# =============================================================================
# PREDICATE-BASED RULES
# =============================================================================
# If the relationship predicate contains certain keywords,
# infer entity type based on position (subject vs object)
# Format: {"predicate_keyword": {"subject": "Type", "object": "Type"}}

PREDICATE_RULES = {
    # Leadership predicates
    "leads": {"subject": "Person", "object": "Team"},
    "manages": {"subject": "Person", "object": "Team"},
    "reports to": {"subject": "Person", "object": "Person"},
    "is lead of": {"subject": "Person", "object": "Team"},
    
    # Team membership
    "has team": {"subject": "Company", "object": "Team"},
    "member of": {"subject": "Person", "object": "Team"},
    "belongs to": {"subject": "Person", "object": "Team"},
    
    # Development predicates
    "develops": {"subject": "Person", "object": "Product"},
    "built": {"subject": "Person", "object": "Product"},
    "created": {"subject": "Person", "object": "Product"},
    "maintains": {"subject": "Person", "object": "Product"},
    
    # Work predicates
    "works on": {"subject": "Person", "object": "Project"},
    "assigned to": {"subject": "Person", "object": "Project"},
    "responsible for": {"subject": "Person", "object": "Project"},
}

# =============================================================================
# CAPITALIZATION HEURISTICS
# =============================================================================
# Enable/disable name-based heuristics

# If True, two-word capitalized names (e.g., "John Smith") are assumed to be Person
TWO_WORD_CAPITALIZED_IS_PERSON = True

# =============================================================================
# DEFAULT TYPE
# =============================================================================
# Type to use when no rules match
# Set to None to skip creating entities that can't be typed

DEFAULT_ENTITY_TYPE = "Entity"  # Generic fallback, or set to None to skip


# =============================================================================
# HELPER FUNCTION (used by extractor)
# =============================================================================

def infer_entity_type(name: str, predicate: str, is_subject: bool) -> str:
    """
    Infer entity type using the configured rules.
    
    Args:
        name: The entity name
        predicate: The relationship predicate (if from a fact)
        is_subject: True if entity is the subject of the fact
        
    Returns:
        Inferred entity type string, or DEFAULT_ENTITY_TYPE
    """
    name_lower = name.lower()
    pred_lower = predicate.lower() if predicate else ""
    
    # 1. Check project prefixes first (most specific)
    for prefix in PROJECT_PREFIXES:
        if name.startswith(prefix):
            return "Project"
    
    # 2. Check name patterns
    for pattern, entity_type in NAME_PATTERNS.items():
        if pattern in name_lower:
            return entity_type
    
    # 3. Check predicate-based rules
    for pred_pattern, types in PREDICATE_RULES.items():
        if pred_pattern in pred_lower:
            return types.get("subject" if is_subject else "object", DEFAULT_ENTITY_TYPE)
    
    # 4. Capitalization heuristics
    if TWO_WORD_CAPITALIZED_IS_PERSON:
        words = name.split()
        if len(words) == 2 and all(w and w[0].isupper() for w in words):
            return "Person"
    
    # 5. Default
    return DEFAULT_ENTITY_TYPE

