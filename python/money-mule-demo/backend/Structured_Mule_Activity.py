import csv
from gremlin_python.structure.graph import Graph
from gremlin_python.process.traversal import P, T, Order
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from datetime import datetime, timedelta
from gremlin_python.statics import long  # Java long
from gremlin_python.statics import timestamp
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import atexit

# Import existing detection functions from FraudScenarioDetector
from FraudScenarioDetector import (
    detect_scenario_a, detect_scenario_b, detect_scenario_c, detect_scenario_d,
    detect_scenario_e, detect_scenario_f, detect_scenario_g, detect_scenario_h
)

# Input CSV file
INPUT_CSV_FILE = "../dataset/vertices/bank_accounts/bank_account.csv"

# Global connection pool to manage connections properly
connection_pool = {}
pool_lock = threading.Lock()

def get_thread_connection():
    """Get a connection for the current thread with proper lifecycle management."""
    thread_id = threading.get_ident()
    
    with pool_lock:
        if thread_id not in connection_pool:
            try:
                connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
                g = traversal().with_remote(connection)
                connection_pool[thread_id] = {
                    'connection': connection,
                    'traversal': g,
                    'active': True
                }
            except Exception as e:
                print(f"Failed to create connection for thread {thread_id}: {e}")
                return None
        
        return connection_pool[thread_id]['traversal']

def cleanup_thread_connection():
    """Clean up connection for the current thread."""
    thread_id = threading.get_ident()
    
    with pool_lock:
        if thread_id in connection_pool:
            try:
                conn_info = connection_pool[thread_id]
                if conn_info['active']:
                    conn_info['connection'].close()
                    conn_info['active'] = False
                del connection_pool[thread_id]
            except Exception as e:
                # Ignore cleanup errors to prevent the aiohttp issues
                pass

def cleanup_all_connections():
    """Clean up all connections in the pool."""
    with pool_lock:
        for thread_id, conn_info in list(connection_pool.items()):
            try:
                if conn_info['active']:
                    conn_info['connection'].close()
                    conn_info['active'] = False
            except:
                # Ignore cleanup errors
                pass
        connection_pool.clear()

# Register cleanup function to run on exit
atexit.register(cleanup_all_connections)

def process_account(bank_account):
    """
    Process a single bank account through all fraud detection scenarios.
    This function will be executed in parallel for each account.
    
    Args:
        bank_account: The bank account ID to analyze
        
    Returns:
        tuple: (account_id, list_of_detected_scenarios)
    """
    detected_scenarios = []
    
    try:
        # Get thread-specific connection
        g = get_thread_connection()
        if g is None:
            return bank_account, []
        
        # List of all detection scenarios to run
        detection_scenarios = [
            ('Scenario A - Funnel Pattern', detect_scenario_a),
            ('Scenario B - Structured Equal Debits', detect_scenario_b),
            ('Scenario C - Rapid Movement', detect_scenario_c),
            ('Scenario D - Circular Transfers', detect_scenario_d),
            ('Scenario E - Cash-Heavy Activity', detect_scenario_e),
            ('Scenario F - Geographic Anomaly', detect_scenario_f),
            ('Scenario G - High-Risk Hour Activity', detect_scenario_g),
            ('Scenario H - Regional Compliance', detect_scenario_h),
        ]

        # Run all detection scenarios for this account
        for scenario_name, detection_function in detection_scenarios:
            try:
                # Handle scenario_h which has different signature
                if detection_function == detect_scenario_h:
                    is_suspicious = detection_function(g, bank_account, region="indian")
                else:
                    is_suspicious = detection_function(g, bank_account)
                
                if is_suspicious:
                    detected_scenarios.append(scenario_name)
                    
            except Exception as e:
                print(f"Error running {scenario_name} for account {bank_account}: {e}")
                continue
                
    except Exception as e:
        print(f"Error processing account {bank_account}: {e}")
    
    return bank_account, detected_scenarios

def detect_structured_mule_activity(max_workers=8):
    """
    Main function to detect suspicious structured money mule activity using parallel processing.
    Uses all available fraud detection scenarios from FraudScenarioDetector.py
    
    Args:
        max_workers: Maximum number of threads to use for parallel processing
    """
    start_time = time.time()
    
    try:
        # Load bank accounts from CSV
        with open(INPUT_CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            bank_accounts = [row[0] for row in list(reader)[1:]]  # Skip header
        
        print(f" Starting parallel analysis of {len(bank_accounts)} accounts using {max_workers} threads...")
        
        suspect_mule_accounts = []
        processed_count = 0
        
        # Process accounts in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all accounts for processing
            future_to_account = {
                executor.submit(process_account, account): account 
                for account in bank_accounts
            }
            
            # Process completed futures as they finish
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                processed_count += 1
                
                try:
                    account_id, detected_scenarios = future.result()
                    
                    if detected_scenarios:
                        suspect_mule_accounts.append(account_id)
                        print(f"⚠️  {account_id} - Detected: {', '.join(detected_scenarios)}")
                    
                    # Progress indicator
                    if processed_count % 100 == 0:
                        print(f"📊 Progress: {processed_count}/{len(bank_accounts)} accounts processed")
                        
                except Exception as e:
                    print(f"Error processing account {account}: {e}")
        
        # Clean up all remaining connections after ThreadPoolExecutor completes
        cleanup_all_connections()
        print("All threads completed, connections cleaned up properly")
        
        # Calculate performance metrics
        end_time = time.time()
        processing_time = end_time - start_time
        accounts_per_second = len(bank_accounts) / processing_time
        
        print(f"\n🔍 Analysis Complete!")
        print(f"Performance: {len(bank_accounts)} accounts in {processing_time:.2f}s ({accounts_per_second:.1f} accounts/sec)")
        print(f"Results: {len(suspect_mule_accounts)} suspicious accounts found")
        
        return suspect_mule_accounts
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    # You can adjust max_workers based on your system capabilities
    # Good starting point: 2-4x number of CPU cores
    detect_structured_mule_activity(max_workers=8)
