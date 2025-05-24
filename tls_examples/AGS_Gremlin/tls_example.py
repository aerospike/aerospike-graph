import ssl
import sys
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

def main():
    try:
        # Create an SSL context that trusts your CA
        ssl_context = ssl.create_default_context(
            cafile="./security/ca.crt"
        )

        # (Optional) disable hostname check if your cert CN doesn't match:
        ssl_context.check_hostname = False

        # Connect over WSS with ssl context
        connection = DriverRemoteConnection(
            'wss://localhost:8182/gremlin',
            'g',
            ssl_context=ssl_context
        )

        g = traversal().withRemote(connection)

        print("Testing Connection to Graph")
        if g.inject(0).next() != 0:
            print("Failed to connect to graph instance")
            exit()
        print("Successfully Connected to Graph")

        g.add_v('foo'). \
            property('company', 'aerospike'). \
            property('scale', 'unlimited').iterate()

        # Read back the new vertex.
        v = g.V().has('company', 'aerospike').next()

        # Print out it's element map
        print("Values:")
        print(g.V(v).values().to_list())
        print("Connected and Queried Successfully, TLS Between AGS and Gremlin is set!")
    except Exception as e:
        print("Traversal failed:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()

if __name__ == "__main__":
    main()
