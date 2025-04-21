#!/usr/bin/env python3

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.structure.graph import Graph
import sys
import os
import argparse

def load_graph_data(vertices_path, edges_path):
    try:
        # Create a Graph instance
        graph = Graph()

        # Connect to the Gremlin Server
        # Default connection to localhost:8182
        connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        g = graph.traversal().withRemote(connection)

        print("Connected to Aerospike Graph successfully!")

        # Verify if the paths exist
        if not os.path.exists(vertices_path):
            raise FileNotFoundError(f"Vertices directory not found: {vertices_path}")
        if not os.path.exists(edges_path):
            raise FileNotFoundError(f"Edges directory not found: {edges_path}")

        print(f"Loading data from:\nVertices: {vertices_path}\nEdges: {edges_path}")

        # Execute the bulk load command
        result = (g.with_("evaluationTimeout", 1000000)
                 .call("aerospike.graphloader.admin.bulk-load.load")
                 .with_("aerospike.graphloader.vertices", vertices_path)
                 .with_("aerospike.graphloader.edges", edges_path)
                 .next())

        print("Data loading completed successfully!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"Error occurred while loading data: {str(e)}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    parser = argparse.ArgumentParser(description='Load data into Aerospike Graph')
    parser.add_argument('--vertices', 
                      default='vertices',
                      help='Path to vertices directory (default: ./vertices)')
    parser.add_argument('--edges', 
                      default='edges',
                      help='Path to edges directory (default: ./edges)')

    args = parser.parse_args()
    
    # Convert relative paths to absolute paths
    vertices_path = os.path.abspath(args.vertices)
    edges_path = os.path.abspath(args.edges)

    load_graph_data(vertices_path, edges_path)

if __name__ == "__main__":
    main() 