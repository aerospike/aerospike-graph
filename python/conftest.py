import pytest
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal


HOST = "localhost"
PORT = 8182


@pytest.fixture(scope="session")
def gremlin_connection():
    conn = DriverRemoteConnection(f"ws://{HOST}:{PORT}/gremlin", "g")
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def g(gremlin_connection):
    return traversal().with_remote(gremlin_connection)


@pytest.fixture
def clean_graph_for_individual_test(g):
    g.V().drop().iterate()
    yield g
    g.V().drop().iterate()
