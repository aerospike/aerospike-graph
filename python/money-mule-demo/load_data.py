#!/usr/bin/env python3
"""
Aerospike Graph Data Loader
Loads vertices and edges from dataset files into Aerospike Graph database.
"""

import time
import sys
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal


def get_graph_connection():
    """Establishes connection to Aerospike Graph"""
    try:
        connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        return traversal().with_remote(connection)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None


def start_bulk_load(g, vertices_path, edges_path):
    """Initiates the bulk load process"""
    try:
        print("  Starting bulk load process...")
        print(f"   Vertices path: {vertices_path}")
        print(f"   Edges path: {edges_path}")
        
        result = (g.with_("evaluationTimeout", 2000000)
                  .call("aerospike.graphloader.admin.bulk-load.load")
                  .with_("aerospike.graphloader.vertices", vertices_path)
                  .with_("aerospike.graphloader.edges", edges_path)
                  .next())
        
        print(f"✅ Bulk load initiated successfully: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error starting bulk load: {e}")
        return False


def check_load_status(g):
    """Checks the current status of the bulk load process"""
    try:
        status = g.call("aerospike.graphloader.admin.bulk-load.status").next()
        return status
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None


def poll_for_completion(g, poll_interval=5, max_wait_time=1800):
    """
    Polls the bulk load status until completion or timeout
    
    Args:
        g: Graph traversal object
        poll_interval: Seconds between status checks (default: 5)
        max_wait_time: Maximum time to wait in seconds (default: 30 minutes)
    """
    print(f"🔍 Polling for completion (checking every {poll_interval}s, max wait: {max_wait_time}s)...")
    
    start_time = time.time()
    
    while True:
        # Check if we've exceeded max wait time
        elapsed_time = time.time() - start_time
        if elapsed_time > max_wait_time:
            print(f"⏰ Timeout reached after {elapsed_time:.1f} seconds")
            return False
        
        # Check status
        status = check_load_status(g)
        if status is None:
            print("❌ Failed to get status, retrying...")
            time.sleep(poll_interval)
            continue
        
        # Print current status
        step = status.get('step', 'unknown')
        complete = status.get('complete', False)
        status_result = status.get('status', 'unknown')
        
        print(f"📊 Status: {step} | Complete: {complete} | Result: {status_result}")
        
        # Print detailed stats if available
        if 'duplicate-vertex-ids' in status:
            duplicate_vertices = status.get('duplicate-vertex-ids', 0)
            bad_edges = status.get('bad-edges', 0)
            bad_entries = status.get('bad-entries', 0)
            print(f"   Stats: {duplicate_vertices} duplicate vertices, {bad_edges} bad edges, {bad_entries} bad entries")
        
        # Check if load is complete
        if complete and step == "done":
            if status_result == "success":
                print("🎉 Bulk load completed successfully!")
                return True
            else:
                print(f"❌ Bulk load completed with status: {status_result}")
                return False
        
        # Wait before next check
        print(f"   ⏳ Waiting {poll_interval}s before next check... (elapsed: {elapsed_time:.1f}s)")
        time.sleep(poll_interval)


def print_final_stats(g):
    """Prints final statistics after load completion"""
    try:
        print("\n📈 Final Load Statistics:")
        status = check_load_status(g)
        if status:
            for key, value in status.items():
                print(f"   {key}: {value}")
        else:
            print("   Unable to retrieve final statistics")
    except Exception as e:
        print(f"   Error retrieving final statistics: {e}")


def main():
    """Main execution function"""
    # Default paths (can be modified as needed)
    vertices_path = "/data/python/money-mule-demo/dataset/vertices"
    edges_path = "/data/python/money-mule-demo/dataset/edges"
    
    # Allow command line arguments for custom paths
    if len(sys.argv) == 3:
        vertices_path = sys.argv[1]
        edges_path = sys.argv[2]
        print(f"📁 Using custom paths:")
        print(f"   Vertices: {vertices_path}")
        print(f"   Edges: {edges_path}")
    elif len(sys.argv) > 1:
        print("Usage: python load_data.py [vertices_path] [edges_path]")
        print("If no paths provided, will use default paths:")
        print(f"  Vertices: {vertices_path}")
        print(f"  Edges: {edges_path}")
        return
    
    print("🛡️  FraudGuard Data Loader")
    print("=" * 50)
    
    # Connect to graph database
    print("🔌 Connecting to Aerospike Graph...")
    g = get_graph_connection()
    if not g:
        print("❌ Failed to connect to database. Ensure Aerospike Graph is running on localhost:8182")
        return
    
    print("✅ Connected successfully!")
    
    try:
        # Start bulk load
        if not start_bulk_load(g, vertices_path, edges_path):
            print("❌ Failed to start bulk load process")
            return
        
        # Poll for completion
        success = poll_for_completion(g, poll_interval=5, max_wait_time=1800)
        
        # Print final results
        print("\n" + "=" * 50)
        if success:
            print("🎉 Data loading completed successfully!")
            print_final_stats(g)
        else:
            print("❌ Data loading failed or timed out")
            print("🔍 Final status check:")
            print_final_stats(g)
            
    except KeyboardInterrupt:
        print("\n⏹️  Loading interrupted by user")
        print("🔍 Current status:")
        print_final_stats(g)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up connection
        try:
            if g:
                g.close()
                print("🔌 Connection closed")
        except:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    main() 