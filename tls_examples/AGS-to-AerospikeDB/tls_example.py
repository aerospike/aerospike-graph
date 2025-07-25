import sys
import time

from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver import client, serializer

def main():
    max_retries = 5
    initial_backoff = 2

    remote_conn = None
    g = None

    # Retry Loop
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}: Connecting to Graph...")
            remote_conn = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
            g = traversal().with_remote(remote_conn)

            if g.inject(0).next() != 0:
                raise RuntimeError("Health check failed: expected 0 from g.inject(0)")

            print("Connection established and healthy.")
            break
        except Exception as conn_exc:
            print(f"Connection attempt {attempt} failed: {conn_exc}", file=sys.stderr)
            try:
                if remote_conn:
                    remote_conn.close()
            except Exception:
                pass

            if attempt == max_retries:
                print("Reached max retries. Exiting.", file=sys.stderr)
                sys.exit(1)

            backoff = initial_backoff * (2 ** (attempt - 1))
            print(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
    try:

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
