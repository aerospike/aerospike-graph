#!/usr/bin/env python3
import time

from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

import sys


def load_graph_data(vertices_path, edges_path):
    try:
        # Connect to the Gremlin Server
        # Default connection to localhost:8182
        connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        g = traversal().with_remote(connection)
        g.inject(0).next()
        print("Connected to Aerospike Graph successfully!")
    except Exception as e:
        print(
            f"Error, failed to connect to Aerospike Graph. Please read the root README.md for help setting up Aerospike Graph locally. Error message: {str(e)}")
        sys.exit(1)

    try:
        print("Clearing server data")
        g.V().drop().iterate()
        print(f"Loading data from:\n\tVertices: {vertices_path}\n\tEdges: {edges_path}")

        # Execute the bulk load command
        (g.with_("evaluationTimeout", 1000000)
         .call("aerospike.graphloader.admin.bulk-load.load")
         .with_("aerospike.graphloader.vertices", vertices_path)
         .with_("aerospike.graphloader.edges", edges_path)
         .next())

        check_interval = 5
        log_interval = 10

        last_log = time.time() - log_interval

        while True:
            status = g.call("aerospike.graphloader.admin.bulk-load.status").next()
            now = time.time()

            if now - last_log >= log_interval:
                print(f"Current Async Bulkload Status: {status}")
                last_log = now

            if status.get("complete"):
                print(f"Current Async Bulkload Status: {status}")
                break

            time.sleep(check_interval)

        print("Data loading completed successfully!")

    except Exception as e:
        print(f"Failed to load data, the following error occurred: {str(e)}")
        sys.exit(1)
    finally:
        connection.close()


def main():
    # Convert relative paths to absolute paths
    vertices_path = "/data/python_example/food_delivery_app/vertices"
    edges_path = "/data/python_example/food_delivery_app/edges"

    # Load data.
    load_graph_data(vertices_path, edges_path)


if __name__ == "__main__":
    main()
