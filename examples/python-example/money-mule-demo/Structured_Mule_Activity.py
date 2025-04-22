import csv
from gremlin_python.structure.graph import Graph
from gremlin_python.process.traversal import P, T, Order
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from datetime import datetime, timedelta
from gremlin_python.statics import long  # Java long
from gremlin_python.statics import timestamp

# Aerospike Graph Server connection details
AEROSPIKE_GRAPH_URL = "ws://localhost:8182/gremlin"

# Input CSV file
INPUT_CSV_FILE = "./dataset/vertices/bank_accounts/bank_account.csv"

def get_debit_transactions(bank_account, g):
    """Fetches debit transactions (outgoing) for a given bank_account."""
    return g.V(bank_account).outE("transaction").order().by("datetime", Order.desc).valueMap(True).toList()

def get_credit_transactions(bank_account, g):
    """Fetches credit transactions (incoming) for a given VPA ID."""
    return g.V(bank_account).inE("transaction").order().by("datetime").valueMap(True).toList()

def detect_structured_mule_activity():
    """Detects structured mule activity based on transaction patterns."""
    try:
        # Establish connection to Aerospike Graph
        graph = Graph()
        connection = DriverRemoteConnection(AEROSPIKE_GRAPH_URL, 'gmuleGraph')
        g = graph.traversal().withRemote(connection)

        # Read the input CSV file
        with open(INPUT_CSV_FILE, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            bank_accounts = [row[0] for row in list(reader)[1:]]  # Skip header
            suspect_mule_accounts = []

        for bank_account in bank_accounts:
            debit_transactions = get_debit_transactions(bank_account, g)
            credit_transactions = get_credit_transactions(bank_account, g)

            for debit in debit_transactions:
                debit_amount = debit['amount']
                relevant_credits={}
                
                time_window_start = debit['datetime'] - (24*60*60*1000) #Check upto 24 hrs ago 
                credit_total=0

                for t in credit_transactions:
                    if time_window_start <= t['datetime'] < debit['datetime']:
                        credit_total += t['amount']
                        relevant_credits[t['datetime']] = t 
                        if len(relevant_credits) > 2 and 0.9 * debit_amount <= credit_total <= debit_amount:
                            if bank_account not in suspect_mule_accounts:
                                suspect_mule_accounts.append(bank_account)
                                print(bank_account)

            for credit in credit_transactions:
                credit_amount = credit['amount']
                relevant_debits={}
                
                time_window_end = credit['datetime'] + (24*60*60*1000) #Check upto 24 hrs later 
                debit_total=0

                for t in debit_transactions:
                    if credit['datetime'] < t['datetime'] <= time_window_end:
                        debit_total += t['amount']
                        relevant_debits[t['datetime']] = t 
                        if len(relevant_debits) > 2 and 0.9 * credit_amount <= debit_total <= credit_amount:
                            if bank_account not in suspect_mule_accounts:
                                suspect_mule_accounts.append(bank_account)
                                print(bank_account)
        # Close connection
        connection.close()
    except Exception as e:
        print(f"Error: {e}")
        try:
            connection.close()
        except:
            pass

if __name__ == "__main__":
    detect_structured_mule_activity()
