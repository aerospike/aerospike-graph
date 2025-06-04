import aerospike, sys
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

# Create GraphTraversalSource to your ags instance, change 00.00.00.00 to the external IP address
remote_conn = DriverRemoteConnection('ws://00.00.00.00:8182/gremlin', 'g')
g = traversal().with_remote(remote_conn)
if g.inject(0).next() != 0:
    print("Failed to connect to graph instance")
    exit()
print("Successfully connected to Aerospike Graph Instance!")
print("Vertice count: " + str(g.V().count().next()))
print("Properties of vertice 100752818: ")
print(g.V(100752818).value_map().to_list())
remote_conn.close()