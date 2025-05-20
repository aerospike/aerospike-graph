from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

if __name__ == '__main__':
    # Create GraphTraversalSource to remote server.
    remote_conn = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
    g = traversal().with_remote(remote_conn)

    # Check if graph is connected
    if g.inject(0).next() != 0:
        print("Failed to connect to graph instance")
        exit()

    # Add a new vertex.
    g.add_v('foo').\
        property('company', 'aerospike').\
        property('scale', 'unlimited').iterate()

    # Read back the new vertex.
    v = g.V().has('company', 'aerospike').next()

    # Print out it's element map
    print("Values:")
    print(g.V(v).values().to_list())

    # Update a property
    g.V(v).property('scale', 'infinite').iterate()

    # Print out the new property
    print("\nUpdated:")
    print(g.V(v).values().to_list())

    # Delete the vertex
    g.V(v).drop().iterate()

    remote_conn.close()
    