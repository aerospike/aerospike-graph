from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import GraphTraversalSource

from src.config import GremlinConfig

log = logging.getLogger(__name__)


class GremlinConnection:
    """Manages a Gremlin connection to Aerospike Graph Service."""

    def __init__(self, config: GremlinConfig | None = None):
        self._config = config or GremlinConfig.from_env()
        self._connection: DriverRemoteConnection | None = None
        self._g: GraphTraversalSource | None = None

    def connect(self) -> GraphTraversalSource:
        if self._g is not None:
            return self._g
        log.info("Connecting to Gremlin at %s", self._config.url)
        self._connection = DriverRemoteConnection(
            self._config.url,
            self._config.traversal_source,
        )
        self._g = traversal().with_remote(self._connection)
        return self._g

    @property
    def g(self) -> GraphTraversalSource:
        if self._g is None:
            return self.connect()
        return self._g

    def close(self) -> None:
        if self._connection is not None:
            log.info("Closing Gremlin connection")
            self._connection.close()
            self._connection = None
            self._g = None

    def __enter__(self) -> GremlinConnection:
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.close()


@contextmanager
def gremlin_connection(
    config: GremlinConfig | None = None,
) -> Generator[GraphTraversalSource, None, None]:
    conn = GremlinConnection(config)
    try:
        yield conn.connect()
    finally:
        conn.close()
