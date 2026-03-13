"""
Markdown documentation parser.

Splits markdown files into sections by heading, preserving
hierarchy for graph modelling.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


@dataclass
class DocSection:
    title: str
    content: str
    heading_level: int
    start_line: int
    end_line: int
    source_file: str
    children: list[DocSection] = field(default_factory=list)


@dataclass
class ParsedDoc:
    path: str
    content_hash: str
    size: int
    sections: list[DocSection] = field(default_factory=list)


DOC_EXTENSIONS = {".md", ".markdown", ".rst", ".txt"}


def _parse_markdown_sections(text: str, source_file: str) -> list[DocSection]:
    lines = text.split("\n")
    sections: list[DocSection] = []
    current_title = ""
    current_level = 0
    current_start = 0
    current_lines: list[str] = []

    def _flush():
        nonlocal current_lines
        if current_title or current_lines:
            content = "\n".join(current_lines).strip()
            if content or current_title:
                sections.append(DocSection(
                    title=current_title,
                    content=content,
                    heading_level=current_level,
                    start_line=current_start + 1,
                    end_line=current_start + len(current_lines),
                    source_file=source_file,
                ))
        current_lines = []

    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            _flush()
            current_title = m.group(2).strip()
            current_level = len(m.group(1))
            current_start = i
            current_lines = []
        else:
            current_lines.append(line)

    _flush()
    return sections


def _extract_code_references(content: str) -> list[str]:
    """Pull out backtick-quoted identifiers that might reference code entities."""
    return re.findall(r"`([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)`", content)


def parse_doc_file(path: Path) -> ParsedDoc | None:
    if path.suffix.lower() not in DOC_EXTENSIONS:
        return None

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError) as e:
        log.warning("Cannot read %s: %s", path, e)
        return None

    sections = _parse_markdown_sections(text, str(path))

    return ParsedDoc(
        path=str(path),
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        size=len(text),
        sections=sections,
    )


def parse_doc_directory(
    root: Path,
    exclude_dirs: set[str] | None = None,
) -> list[ParsedDoc]:
    if exclude_dirs is None:
        exclude_dirs = {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "build", "dist", "target",
        }

    results: list[ParsedDoc] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in exclude_dirs for part in path.parts):
            continue
        parsed = parse_doc_file(path)
        if parsed:
            results.append(parsed)

    log.info("Parsed %d doc files from %s", len(results), root)
    return results
