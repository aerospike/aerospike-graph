"""
Tree-sitter based code parser that extracts structural entities
(classes, functions, imports) from source files.

Supports Python and Java initially; designed to add more languages
by registering new grammars and node-type mappings.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import tree_sitter_python as ts_python
import tree_sitter_java as ts_java
import tree_sitter_javascript as ts_js
from tree_sitter import Language, Parser, Node

log = logging.getLogger(__name__)


@dataclass
class CodeEntity:
    kind: str  # "class", "function", "import"
    name: str
    qualified_name: str
    start_line: int
    end_line: int
    signature: str = ""
    docstring: str = ""
    children: list[CodeEntity] = field(default_factory=list)


@dataclass
class ParsedFile:
    path: str
    language: str
    content_hash: str
    size: int
    entities: list[CodeEntity] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


LANGUAGE_REGISTRY: dict[str, Language] = {}


def _ensure_languages():
    if LANGUAGE_REGISTRY:
        return
    LANGUAGE_REGISTRY["python"] = Language(ts_python.language())
    LANGUAGE_REGISTRY["java"] = Language(ts_java.language())
    LANGUAGE_REGISTRY["javascript"] = Language(ts_js.language())


LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".mjs": "javascript",
    ".jsx": "javascript",
}


def detect_language(path: Path) -> str | None:
    return LANGUAGE_EXTENSIONS.get(path.suffix.lower())


# ---------------------------------------------------------------------------
# Python extractor
# ---------------------------------------------------------------------------

def _python_extract_docstring(node: Node, source: bytes) -> str:
    body = node.child_by_field_name("body")
    if body and body.child_count > 0:
        first = body.children[0]
        if first.type == "expression_statement" and first.child_count > 0:
            expr = first.children[0]
            if expr.type == "string":
                raw = source[expr.start_byte:expr.end_byte].decode("utf-8", errors="replace")
                return raw.strip("\"'").strip()
    return ""


def _python_extract_signature(node: Node, source: bytes) -> str:
    params = node.child_by_field_name("parameters")
    name = node.child_by_field_name("name")
    if name and params:
        return_ann = node.child_by_field_name("return_type")
        sig = f"{source[name.start_byte:name.end_byte].decode()}({source[params.start_byte:params.end_byte].decode()})"
        if return_ann:
            sig += f" -> {source[return_ann.start_byte:return_ann.end_byte].decode()}"
        return sig
    return ""


def _python_extract_imports(root: Node, source: bytes) -> list[str]:
    imports: list[str] = []
    for child in root.children:
        if child.type == "import_statement":
            imports.append(source[child.start_byte:child.end_byte].decode("utf-8", errors="replace"))
        elif child.type == "import_from_statement":
            imports.append(source[child.start_byte:child.end_byte].decode("utf-8", errors="replace"))
    return imports


def _python_walk(node: Node, source: bytes, prefix: str) -> list[CodeEntity]:
    entities: list[CodeEntity] = []
    for child in node.children:
        if child.type == "class_definition":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            entity = CodeEntity(
                kind="class",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                docstring=_python_extract_docstring(child, source),
            )
            body = child.child_by_field_name("body")
            if body:
                entity.children = _python_walk(body, source, qn)
            entities.append(entity)

        elif child.type == "function_definition":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            entity = CodeEntity(
                kind="function",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                signature=_python_extract_signature(child, source),
                docstring=_python_extract_docstring(child, source),
            )
            entities.append(entity)
    return entities


# ---------------------------------------------------------------------------
# Java extractor
# ---------------------------------------------------------------------------

def _java_extract_docstring(node: Node, source: bytes) -> str:
    prev = node.prev_sibling
    if prev and prev.type == "block_comment":
        raw = source[prev.start_byte:prev.end_byte].decode("utf-8", errors="replace")
        return raw
    return ""


def _java_extract_imports(root: Node, source: bytes) -> list[str]:
    imports: list[str] = []
    for child in root.children:
        if child.type == "import_declaration":
            imports.append(source[child.start_byte:child.end_byte].decode("utf-8", errors="replace").strip().rstrip(";"))
    return imports


def _java_walk(node: Node, source: bytes, prefix: str) -> list[CodeEntity]:
    entities: list[CodeEntity] = []
    for child in node.children:
        if child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            entity = CodeEntity(
                kind="class",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                docstring=_java_extract_docstring(child, source),
            )
            body = child.child_by_field_name("body")
            if body:
                entity.children = _java_walk(body, source, qn)
            entities.append(entity)

        elif child.type == "method_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            params = child.child_by_field_name("parameters")
            sig = ""
            if params:
                sig = f"{name}({source[params.start_byte:params.end_byte].decode()})"
            entity = CodeEntity(
                kind="function",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                signature=sig,
                docstring=_java_extract_docstring(child, source),
            )
            entities.append(entity)

        elif child.type in ("interface_declaration", "enum_declaration"):
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            entity = CodeEntity(
                kind="class",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                docstring=_java_extract_docstring(child, source),
            )
            body = child.child_by_field_name("body")
            if body:
                entity.children = _java_walk(body, source, qn)
            entities.append(entity)
    return entities


# ---------------------------------------------------------------------------
# JavaScript extractor
# ---------------------------------------------------------------------------

def _js_extract_imports(root: Node, source: bytes) -> list[str]:
    imports: list[str] = []
    for child in root.children:
        if child.type == "import_statement":
            imports.append(source[child.start_byte:child.end_byte].decode("utf-8", errors="replace"))
    return imports


def _js_walk(node: Node, source: bytes, prefix: str) -> list[CodeEntity]:
    entities: list[CodeEntity] = []
    for child in node.children:
        if child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            entity = CodeEntity(
                kind="class",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
            )
            body = child.child_by_field_name("body")
            if body:
                entity.children = _js_walk(body, source, qn)
            entities.append(entity)

        elif child.type == "function_declaration":
            name_node = child.child_by_field_name("name")
            if not name_node:
                continue
            name = source[name_node.start_byte:name_node.end_byte].decode()
            qn = f"{prefix}.{name}" if prefix else name
            params = child.child_by_field_name("parameters")
            sig = ""
            if params:
                sig = f"{name}({source[params.start_byte:params.end_byte].decode()})"
            entities.append(CodeEntity(
                kind="function",
                name=name,
                qualified_name=qn,
                start_line=child.start_point[0] + 1,
                end_line=child.end_point[0] + 1,
                signature=sig,
            ))

        elif child.type == "export_statement":
            entities.extend(_js_walk(child, source, prefix))

        elif child.type == "lexical_declaration":
            for decl in child.children:
                if decl.type == "variable_declarator":
                    name_node = decl.child_by_field_name("name")
                    value = decl.child_by_field_name("value")
                    if name_node and value and value.type in ("arrow_function", "function"):
                        name = source[name_node.start_byte:name_node.end_byte].decode()
                        qn = f"{prefix}.{name}" if prefix else name
                        entities.append(CodeEntity(
                            kind="function",
                            name=name,
                            qualified_name=qn,
                            start_line=child.start_point[0] + 1,
                            end_line=child.end_point[0] + 1,
                        ))
    return entities


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_EXTRACTORS = {
    "python": (_python_walk, _python_extract_imports),
    "java": (_java_walk, _java_extract_imports),
    "javascript": (_js_walk, _js_extract_imports),
}


def parse_file(path: Path, language: str | None = None) -> ParsedFile | None:
    _ensure_languages()
    lang = language or detect_language(path)
    if lang is None or lang not in LANGUAGE_REGISTRY:
        return None

    try:
        source = path.read_bytes()
    except (OSError, PermissionError) as e:
        log.warning("Cannot read %s: %s", path, e)
        return None

    parser = Parser(LANGUAGE_REGISTRY[lang])
    tree = parser.parse(source)
    root = tree.root_node

    walk_fn, import_fn = _EXTRACTORS[lang]
    module_name = path.stem

    entities = walk_fn(root, source, module_name)
    imports = import_fn(root, source)

    return ParsedFile(
        path=str(path),
        language=lang,
        content_hash=hashlib.sha256(source).hexdigest(),
        size=len(source),
        entities=entities,
        imports=imports,
    )


def parse_directory(
    root: Path,
    languages: list[str] | None = None,
    exclude_dirs: set[str] | None = None,
) -> list[ParsedFile]:
    if exclude_dirs is None:
        exclude_dirs = {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "build", "dist", "target", ".tox", ".mypy_cache",
        }

    results: list[ParsedFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in exclude_dirs for part in path.parts):
            continue
        lang = detect_language(path)
        if lang is None:
            continue
        if languages and lang not in languages:
            continue
        parsed = parse_file(path, lang)
        if parsed:
            results.append(parsed)

    log.info("Parsed %d files from %s", len(results), root)
    return results
