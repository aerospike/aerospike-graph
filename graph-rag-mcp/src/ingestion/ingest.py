"""
CLI entrypoint for ingesting a codebase into the graph.

Usage:
    python -m src.ingestion.ingest \
        --tenant-id firefly \
        --name "Aerospike Graph" \
        --root /home/lyndon/github/aerospike-graph \
        --languages python java javascript
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from src.config import GremlinConfig
from src.graph.connection import GremlinConnection
from src.ingestion.code_parser import parse_directory
from src.ingestion.doc_parser import parse_doc_directory
from src.ingestion.graph_modeler import (
    ingest_parsed_doc,
    ingest_parsed_file,
    upsert_repository,
)

log = logging.getLogger(__name__)


def run_ingestion(
    tenant_id: str,
    name: str,
    root_path: str,
    languages: list[str],
    gremlin_config: GremlinConfig | None = None,
) -> dict:
    root = Path(root_path).resolve()
    if not root.is_dir():
        raise ValueError(f"Root path does not exist: {root}")

    conn = GremlinConnection(gremlin_config)
    stats = {"files": 0, "entities": 0, "docs": 0, "doc_sections": 0}

    try:
        g = conn.connect()

        log.info("Creating repository vertex: %s (%s)", name, tenant_id)
        upsert_repository(g, tenant_id, name, str(root), languages)

        log.info("Parsing code in %s ...", root)
        parsed_files = parse_directory(root, languages)
        stats["files"] = len(parsed_files)

        for i, pf in enumerate(parsed_files, 1):
            entity_count = _count_entities(pf.entities)
            stats["entities"] += entity_count
            log.info(
                "[%d/%d] Ingesting %s (%d entities)",
                i, len(parsed_files), pf.path, entity_count,
            )
            ingest_parsed_file(g, tenant_id, name, pf)

        log.info("Parsing docs in %s ...", root)
        parsed_docs = parse_doc_directory(root)
        stats["docs"] = len(parsed_docs)

        for i, pd in enumerate(parsed_docs, 1):
            stats["doc_sections"] += len(pd.sections)
            log.info(
                "[%d/%d] Ingesting doc %s (%d sections)",
                i, len(parsed_docs), pd.path, len(pd.sections),
            )
            ingest_parsed_doc(g, tenant_id, name, pd)

        log.info("Ingestion complete: %s", stats)
        return stats
    finally:
        conn.close()


def _count_entities(entities) -> int:
    count = len(entities)
    for e in entities:
        count += _count_entities(e.children)
    return count


def main():
    parser = argparse.ArgumentParser(description="Ingest a codebase into Aerospike Graph")
    parser.add_argument("--tenant-id", required=True, help="Tenant identifier")
    parser.add_argument("--name", required=True, help="Repository display name")
    parser.add_argument("--root", required=True, help="Root path of the codebase")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["python"],
        help="Languages to parse (default: python)",
    )
    parser.add_argument("--gremlin-host", default=None)
    parser.add_argument("--gremlin-port", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    )

    config = None
    if args.gremlin_host or args.gremlin_port:
        config = GremlinConfig(
            host=args.gremlin_host or "localhost",
            port=args.gremlin_port or 8182,
        )

    t0 = time.time()
    stats = run_ingestion(args.tenant_id, args.name, args.root, args.languages, config)
    elapsed = time.time() - t0

    print(f"\nIngestion completed in {elapsed:.1f}s")
    print(f"  Files:        {stats['files']}")
    print(f"  Entities:     {stats['entities']}")
    print(f"  Docs:         {stats['docs']}")
    print(f"  Doc sections: {stats['doc_sections']}")


if __name__ == "__main__":
    main()
