"""
Graph schema constants for the code knowledge graph.

Vertex labels, edge labels, and property keys used across
ingestion and retrieval.
"""


class VertexLabel:
    REPOSITORY = "Repository"
    FILE = "File"
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    DOC_SECTION = "DocSection"

    ALL = {REPOSITORY, FILE, MODULE, CLASS, FUNCTION, DOC_SECTION}


class EdgeLabel:
    BELONGS_TO = "belongs_to"
    CONTAINS = "contains"
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    REFERENCES = "references"

    ALL = {BELONGS_TO, CONTAINS, IMPORTS, CALLS, INHERITS, REFERENCES}


class Property:
    """Shared property keys. Not every vertex type uses every key."""

    TENANT_ID = "tenant_id"
    NAME = "name"
    QUALIFIED_NAME = "qualified_name"
    PATH = "path"
    LANGUAGE = "language"
    CONTENT_HASH = "content_hash"
    SIZE = "size"
    DOCSTRING = "docstring"
    SIGNATURE = "signature"
    START_LINE = "start_line"
    END_LINE = "end_line"
    TITLE = "title"
    CONTENT = "content"
    SOURCE_FILE = "source_file"
    HEADING_LEVEL = "heading_level"

    # Vertex-id helper: deterministic IDs avoid duplicates on re-ingestion.
    @staticmethod
    def vertex_id(tenant_id: str, label: str, qualified_name: str) -> str:
        return f"{tenant_id}::{label}::{qualified_name}"
