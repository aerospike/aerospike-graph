from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

if __name__ == '__main__':
    # Create GraphTraversalSource to remote server.
    g = traversal().with_remote(DriverRemoteConnection(
        'ws://localhost:8182/gremlin', 'g'))

    # Add a new vertex.
    g.add_v('foo').\
        property('company', 'aerospike').\
        property('scale', 'unlimited').iterate()

    # Read back the new vertex.
    v = g.V().has('company', 'aerospike').next()

    # Print out it's element map
    print("Element map:")
    print(g.V().element_map().to_list())

    # Update a property
    g.V(v).property('scale', 'infinite').iterate()

    # Print out the new property
    print("\nProperty map, updated:")
    print(g.V(v).property_map().to_list())

    # Delete the vertex
    g.V(v).drop().iterate()
