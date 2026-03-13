"""
Maps parsed code and doc entities to Gremlin graph mutations.

Uses mergeV/mergeE for idempotent upserts so re-ingestion
is safe and incremental.
"""

from __future__ import annotations

import logging
from pathlib import Path

from gremlin_python.process.graph_traversal import GraphTraversalSource, __
from gremlin_python.process.traversal import T, Merge, Direction

from src.graph.schema import VertexLabel, EdgeLabel, Property
from src.ingestion.code_parser import CodeEntity, ParsedFile
from src.ingestion.doc_parser import DocSection, ParsedDoc

log = logging.getLogger(__name__)


def _vid(tenant_id: str, label: str, qualified_name: str) -> str:
    return Property.vertex_id(tenant_id, label, qualified_name)


def upsert_repository(
    g: GraphTraversalSource,
    tenant_id: str,
    name: str,
    root_path: str,
    languages: list[str],
) -> None:
    vid = _vid(tenant_id, VertexLabel.REPOSITORY, name)
    g.merge_v({T.id: vid, T.label: VertexLabel.REPOSITORY}).option(
        Merge.on_create,
        {
            Property.TENANT_ID: tenant_id,
            Property.NAME: name,
            Property.PATH: root_path,
            Property.LANGUAGE: ",".join(languages),
        },
    ).option(
        Merge.on_match,
        {
            Property.PATH: root_path,
            Property.LANGUAGE: ",".join(languages),
        },
    ).next()


def upsert_file(
    g: GraphTraversalSource,
    tenant_id: str,
    repo_name: str,
    parsed: ParsedFile,
) -> None:
    rel_path = parsed.path
    vid = _vid(tenant_id, VertexLabel.FILE, rel_path)
    repo_vid = _vid(tenant_id, VertexLabel.REPOSITORY, repo_name)

    g.merge_v({T.id: vid, T.label: VertexLabel.FILE}).option(
        Merge.on_create,
        {
            Property.TENANT_ID: tenant_id,
            Property.PATH: rel_path,
            Property.LANGUAGE: parsed.language,
            Property.CONTENT_HASH: parsed.content_hash,
            Property.SIZE: parsed.size,
            Property.NAME: Path(rel_path).name,
        },
    ).option(
        Merge.on_match,
        {
            Property.CONTENT_HASH: parsed.content_hash,
            Property.SIZE: parsed.size,
        },
    ).next()

    _upsert_edge(g, vid, repo_vid, EdgeLabel.BELONGS_TO)


def _upsert_entity(
    g: GraphTraversalSource,
    tenant_id: str,
    entity: CodeEntity,
    parent_vid: str,
    parent_edge_label: str,
    repo_vid: str,
) -> str:
    label = VertexLabel.CLASS if entity.kind == "class" else VertexLabel.FUNCTION
    vid = _vid(tenant_id, label, entity.qualified_name)

    props_create = {
        Property.TENANT_ID: tenant_id,
        Property.NAME: entity.name,
        Property.QUALIFIED_NAME: entity.qualified_name,
        Property.START_LINE: entity.start_line,
        Property.END_LINE: entity.end_line,
    }
    props_update = {
        Property.START_LINE: entity.start_line,
        Property.END_LINE: entity.end_line,
    }

    if entity.signature:
        props_create[Property.SIGNATURE] = entity.signature
        props_update[Property.SIGNATURE] = entity.signature
    if entity.docstring:
        props_create[Property.DOCSTRING] = entity.docstring
        props_update[Property.DOCSTRING] = entity.docstring

    g.merge_v({T.id: vid, T.label: label}).option(
        Merge.on_create, props_create,
    ).option(
        Merge.on_match, props_update,
    ).next()

    _upsert_edge(g, vid, parent_vid, parent_edge_label)
    _upsert_edge(g, vid, repo_vid, EdgeLabel.BELONGS_TO)

    for child in entity.children:
        _upsert_entity(g, tenant_id, child, vid, EdgeLabel.CONTAINS, repo_vid)

    return vid


def _upsert_edge(
    g: GraphTraversalSource,
    from_vid: str,
    to_vid: str,
    label: str,
) -> None:
    g.merge_e(
        {T.label: label, Direction.OUT: from_vid, Direction.IN: to_vid}
    ).next()


def ingest_parsed_file(
    g: GraphTraversalSource,
    tenant_id: str,
    repo_name: str,
    parsed: ParsedFile,
) -> None:
    repo_vid = _vid(tenant_id, VertexLabel.REPOSITORY, repo_name)
    file_vid = _vid(tenant_id, VertexLabel.FILE, parsed.path)

    upsert_file(g, tenant_id, repo_name, parsed)

    for entity in parsed.entities:
        _upsert_entity(
            g, tenant_id, entity, file_vid, EdgeLabel.CONTAINS, repo_vid,
        )

    log.debug("Ingested %s (%d entities)", parsed.path, len(parsed.entities))


def ingest_parsed_doc(
    g: GraphTraversalSource,
    tenant_id: str,
    repo_name: str,
    parsed_doc: ParsedDoc,
) -> None:
    repo_vid = _vid(tenant_id, VertexLabel.REPOSITORY, repo_name)

    file_vid = _vid(tenant_id, VertexLabel.FILE, parsed_doc.path)
    g.merge_v({T.id: file_vid, T.label: VertexLabel.FILE}).option(
        Merge.on_create,
        {
            Property.TENANT_ID: tenant_id,
            Property.PATH: parsed_doc.path,
            Property.LANGUAGE: "markdown",
            Property.CONTENT_HASH: parsed_doc.content_hash,
            Property.SIZE: parsed_doc.size,
            Property.NAME: Path(parsed_doc.path).name,
        },
    ).next()
    _upsert_edge(g, file_vid, repo_vid, EdgeLabel.BELONGS_TO)

    for section in parsed_doc.sections:
        _ingest_doc_section(g, tenant_id, section, file_vid, repo_vid)


def _ingest_doc_section(
    g: GraphTraversalSource,
    tenant_id: str,
    section: DocSection,
    parent_vid: str,
    repo_vid: str,
) -> None:
    qn = f"{section.source_file}::{section.title}::{section.start_line}"
    vid = _vid(tenant_id, VertexLabel.DOC_SECTION, qn)

    content_truncated = section.content[:4000] if section.content else ""

    g.merge_v({T.id: vid, T.label: VertexLabel.DOC_SECTION}).option(
        Merge.on_create,
        {
            Property.TENANT_ID: tenant_id,
            Property.TITLE: section.title,
            Property.CONTENT: content_truncated,
            Property.SOURCE_FILE: section.source_file,
            Property.HEADING_LEVEL: section.heading_level,
            Property.START_LINE: section.start_line,
            Property.END_LINE: section.end_line,
        },
    ).option(
        Merge.on_match,
        {
            Property.CONTENT: content_truncated,
        },
    ).next()

    _upsert_edge(g, vid, parent_vid, EdgeLabel.CONTAINS)
    _upsert_edge(g, vid, repo_vid, EdgeLabel.BELONGS_TO)

    for child in section.children:
        _ingest_doc_section(g, tenant_id, child, vid, repo_vid)
