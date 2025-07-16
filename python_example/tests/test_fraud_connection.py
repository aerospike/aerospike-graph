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

@pytest.fixture(autouse=True)
def clean_graph(g):
    g.V().drop().iterate()
    yield

def test_inserts(g):
    v1 = g.add_v("User").property("name", "Durial321").property("address", "falador").next()
    v2 = g.add_v("User").property("name", "ModMurdoch").property("role", "admin").next()
    e1 = g.add_e("Banned").to(v1).from_(v2).next()

    assert g.V(v2).out_e().next() == e1
    assert g.V(v1).in_().next() == v2