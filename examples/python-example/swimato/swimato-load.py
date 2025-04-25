#!/usr/bin/env python3

from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

import sys
import os
import argparse


def load_graph_data(vertices_path, edges_path):
    try:
        # Connect to the Gremlin Server
        # Default connection to localhost:8182
        connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        g = traversal().with_remote(connection)
        g.inject(0).next()
        print("Connected to Aerospike Graph successfully!")
    except Exception as e:
        print(f"Error, failed to connect to Aerospike Graph. Please read the root README.md for help setting up Aerospike Graph locally. Error message: {str(e)}")
        sys.exit(1)

    try:
        print(f"Loading data from:\n\tVertices: {vertices_path}\n\tEdges: {edges_path}")

        # Execute the bulk load command
        result = (g.with_("evaluationTimeout", 1000000)
                 .call("aerospike.graphloader.admin.bulk-load.load")
                 .with_("aerospike.graphloader.vertices", vertices_path)
                 .with_("aerospike.graphloader.edges", edges_path)
                 .next())

        print("Data loading completed successfully!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"Failed to load data, the following error occurred: {str(e)}")
        sys.exit(1)
    finally:
        connection.close()


def main():
    # Convert relative paths to absolute paths
    vertices_path = "python_examples/swimato/data/vertices"
    edges_path = "python_examples/swimato/data/edges"

    # Load data.
    load_graph_data(vertices_path, edges_path)


if __name__ == "__main__":
    main() 