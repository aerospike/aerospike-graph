import sys
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver import client, serializer

remote_conn = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
g = traversal().with_remote(remote_conn)

def main():
    try:
        print("Testing Connection to Graph")
        if g.inject(0).next() != 0:
            print("Failed to connect to graph instance")
            exit()
        g.add_v('foo'). \
            property('company', 'aerospike'). \
            property('scale', 'unlimited').iterate()

        # Read back the new vertex.
        v = g.V().has('company', 'aerospike').next()

        # Print out it's element map
        print("Values:")
        print(g.V(v).values().to_list())
        print("Connected and Queried Successfully, TLS between AGS and Aerospike DB is set up!")
    except Exception as e:
        print("Traversal failed:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        remote_conn.close()

if __name__ == "__main__":
    main()
