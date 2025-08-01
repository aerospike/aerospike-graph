import csv
from gremlin_python.structure.graph import Graph
from gremlin_python.process.traversal import P, T, Order
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from datetime import datetime, timedelta
from gremlin_python.statics import long, timestamp
from gremlin_python.process.anonymous_traversal import traversal

# Input CSV file
INPUT_CSV_FILE = "../dataset/vertices/bank_accounts/bank_account.csv"

def get_debit_transactions(account, g):
    """Fetches debit transactions (outgoing) for a given account."""
    return g.V(account).outE("transaction").order().by("datetime", Order.desc).valueMap(True).toList()

def get_credit_transactions(account, g):
    """Fetches credit transactions (incoming) for a given account."""
    return g.V(account).inE("transaction").order().by("datetime").valueMap(True).toList()

def detect_scenario_a(g, account):
    """
    Detects pattern: Multiple small credits followed by single large debit
    - Multiple credits within 24 hours before debit
    - Total credits approximately equal to debit amount (90-100%)
    - At least 2 credit transactions
    """
    debit_transactions = get_debit_transactions(account, g)
    credit_transactions = get_credit_transactions(account, g)

    for debit in debit_transactions:
        debit_amount = debit['amount']
        relevant_credits = {}  # Changed to dict to match original logic
        
        time_window_start = debit['datetime'] - (24*60*60*1000)  # 24 hours before, not 4
        credit_total = 0

        for t in credit_transactions:
            if time_window_start <= t['datetime'] < debit['datetime']:
                credit_total += t['amount']
                relevant_credits[t['datetime']] = t  # Store in dict with timestamp key
                
                # Moved check inside the loop to match original logic
                if (len(relevant_credits) > 2 and 
                    0.9 * debit_amount <= credit_total <= debit_amount):
                    return True
    return False

def detect_scenario_b(g, account):
    """
    Detects pattern: Single large credit followed by structured equal debits
    - One large credit ($10,000-$50,000)
    - Followed by exactly 4 equal-sized debits within 4 hours
    - Each debit should be approximately 1/4 of the credit amount
    - All debits go to the same fraud account
    """
    credit_transactions = get_credit_transactions(account, g)
    debit_transactions = get_debit_transactions(account, g)

    for credit in credit_transactions:
        credit_amount = credit['amount']
        if not (10000 <= credit_amount <= 50000):
            continue

        expected_split = credit_amount / 4  # Each debit should be ~this amount
        time_window_end = credit['datetime'] + (240 * 60 * 1000)  # 4 hours (240 minutes)
        relevant_debits = []
        
        # Get all debits within the time window
        for debit in debit_transactions:
            if credit['datetime'] < debit['datetime'] <= time_window_end:
                # Check if debit is approximately 1/4 of credit amount
                if 0.9 * expected_split <= debit['amount'] <= 1.1 * expected_split:
                    relevant_debits.append(debit)

        # Check if we have exactly 4 equal-sized debits to same destination
        if len(relevant_debits) == 4:
            # Check if all debits go to the same account
            destination = relevant_debits[0]['~to']
            if all(debit['~to'] == destination for debit in relevant_debits):
                return True
    
    return False

def detect_scenario_c(g, account):
    """
    Detects pattern: Multiple large ATM withdrawals
    - 3+ withdrawals $5,000-$10,000 each
    - Self-directed transactions
    """
    withdrawals = g.V(account).outE("suspicious_atm_withdrawal").valueMap(True).toList()
    large_withdrawals = [w for w in withdrawals 
                        if 5000 <= w['amount'] <= 10000]
    return len(large_withdrawals) >= 3

def detect_scenario_d(g, account):
    """
    Detects pattern: High-frequency transfers between mule accounts
    - 10+ transactions $500-$5,000 each
    - Mix of credits/debits within 1 hour
    """
    all_transactions = (g.V(account).bothE("suspicious_transaction")
                       .has('amount', P.between(500, 5000))
                       .valueMap(True).toList())
    
    if len(all_transactions) < 10:
        return False

    # Check for transactions within 1-hour windows
    all_transactions.sort(key=lambda x: x['datetime'])
    for i in range(len(all_transactions) - 9):
        window_start = all_transactions[i]['datetime']
        window_end = window_start + (60 * 60 * 1000)  # 1 hour
        window_transactions = [t for t in all_transactions[i:i+10]
                             if window_start <= t['datetime'] <= window_end]
        if len(window_transactions) >= 10:
            return True
    return False

def detect_scenario_e(g, account):
    """
    Detects pattern: Salary-like deposits followed by suspicious transfers
    - Initial credit $5,000-$10,000
    - Followed by 3+ transfers $5,000-$7,000 each
    """
    credit_transactions = get_credit_transactions(account, g)
    debit_transactions = get_debit_transactions(account, g)

    for credit in credit_transactions:
        if not (5000 <= credit['amount'] <= 10000):
            continue

        suspicious_transfers = [d for d in debit_transactions
                              if d['datetime'] > credit['datetime'] and
                              5000 <= d['amount'] <= 7000]
        
        if len(suspicious_transfers) >= 3:
            return True
    return False

def detect_scenario_f(g, account):
    """
    Detects pattern: Dormant account sudden activity
    - Account dormant (no transactions for extended period)
    - Sudden large credit $10,000-$50,000
    - Followed by 4 equal debits
    """
    all_transactions = (g.V(account).bothE("suspicious_transaction")
                       .order().by('datetime')
                       .valueMap(True).toList())
    
    if len(all_transactions) < 5:  # Need at least 5 transactions
        return False

    # Check for dormancy followed by sudden activity
    for i in range(len(all_transactions) - 5):
        time_gap = (all_transactions[i+1]['datetime'] - 
                   all_transactions[i]['datetime'])
        if time_gap >= (30 * 24 * 60 * 60 * 1000):  # 30 days dormancy
            credit = all_transactions[i+1]
            if not (10000 <= credit['amount'] <= 50000 and 
                   credit['type'] == 'credit'):
                continue
            
            subsequent_debits = [t for t in all_transactions[i+2:i+6]
                               if t['type'] == 'debit']
            if len(subsequent_debits) >= 4:
                debit_total = sum(d['amount'] for d in subsequent_debits)
                if 0.9 * credit['amount'] <= debit_total <= credit['amount']:
                    return True
    return False

def detect_scenario_g(g, account):
    """
    Detects pattern: International transfers to high-risk jurisdictions
    - 5+ transfers $500-$5,000 each
    - To specific locations (Dubai, Bahrain, Thailand)
    """
    high_risk_locations = ['Dubai', 'Bahrain', 'Thailand']
    suspicious_transfers = (g.V(account).outE("suspicious_transaction")
                          .has('location', P.within(high_risk_locations))
                          .has('amount', P.between(500, 5000))
                          .valueMap(True).toList())
    return len(suspicious_transfers) >= 5

def detect_scenario_h(g, account, region="indian"):
    """
    Detects pattern: Region-specific fraud (Indian context)
    - 3+ large transfers $10,000-$50,000
    - From specific locations (Jamtara, Bharatpur, Alwar)
    """
    if region != "indian":
        return False

    fraud_locations = ['Jamtara', 'Bharatpur', 'Alwar']
    suspicious_transfers = (g.V(account).outE("suspicious_transaction")
                          .has('location', P.within(fraud_locations))
                          .has('amount', P.between(10000, 50000))
                          .has('fraud_flag', True)
                          .valueMap(True).toList())
    return len(suspicious_transfers) >= 3

def FraudScenarioDetector(account_number):
    """
    Main function to analyze a single account for all fraud scenarios.
    This function is called by the backend API.
    
    Args:
        account_number: The account number to analyze
        
    Returns:
        dict: Analysis results with scenario detection results and summary
    """
    try:
        # Establish connection to Aerospike Graph
        connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        g = traversal().with_remote(connection)

        # Check if account exists
        if not g.V(account_number).hasNext():
            connection.close()
            return {
                "error": f"Account {account_number} not found",
                "account_number": account_number
            }

        # Run all scenario detections
        results = {
            'account_number': account_number,
            'scenarios': {
                'scenario_a': {
                    'detected': detect_scenario_a(g, account_number),
                    'description': 'Multiple small credits followed by single large debit'
                },
                'scenario_b': {
                    'detected': detect_scenario_b(g, account_number),
                    'description': 'Single large credit followed by structured equal debits'
                },
                'scenario_c': {
                    'detected': detect_scenario_c(g, account_number),
                    'description': 'Multiple large ATM withdrawals'
                },
                'scenario_d': {
                    'detected': detect_scenario_d(g, account_number),
                    'description': 'High-frequency transfers between mule accounts'
                },
                'scenario_e': {
                    'detected': detect_scenario_e(g, account_number),
                    'description': 'Salary-like deposits followed by suspicious transfers'
                },
                'scenario_f': {
                    'detected': detect_scenario_f(g, account_number),
                    'description': 'Dormant account sudden activity'
                },
                'scenario_g': {
                    'detected': detect_scenario_g(g, account_number),
                    'description': 'International transfers to high-risk jurisdictions'
                },
                'scenario_h': {
                    'detected': detect_scenario_h(g, account_number),
                    'description': 'Region-specific fraud (Indian context)'
                }
            }
        }

        # Add summary
        suspicious_scenarios = [k for k, v in results['scenarios'].items() if v['detected']]
        results['summary'] = {
            'total_scenarios_detected': len(suspicious_scenarios),
            'suspicious_scenarios': suspicious_scenarios,
            'is_suspicious': len(suspicious_scenarios) > 0
        }

        connection.close()
        return results

    except Exception as e:
        try:
            connection.close()
        except:
            pass
        return {
            "error": str(e),
            "account_number": account_number
        }

# Keep the original analyze_account function for backwards compatibility
def analyze_account(account_number):
    """Analyzes a single account for all fraud scenarios (original function)."""
    result = FraudScenarioDetector(account_number)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return None
    
    # Print results in original format
    print(f"\nAnalysis results for account {account_number}:")
    print("----------------------------------------")
    
    if result['summary']['is_suspicious']:
        print("⚠️  Suspicious patterns detected in scenarios:")
        for scenario in result['summary']['suspicious_scenarios']:
            description = result['scenarios'][scenario]['description']
            print(f"  - {scenario}: {description}")
    else:
        print("✅ No suspicious patterns detected")
    
    # Return results in original format for backwards compatibility
    return {k: v['detected'] for k, v in result['scenarios'].items()}

if __name__ == "__main__":
    print("\n🔍 Fraud Scenario Detector")
    print("Enter 'quit' or 'exit' to stop the program")
    print("----------------------------------------")

    while True:
        # Get account number
        account_number = input("\nEnter account number to analyze: ").strip()
        
        # Check for exit commands
        if account_number.lower() in ['quit', 'exit', 'q']:
            print("\nExiting Fraud Scenario Detector. Goodbye! 👋")
            break
        
        # Skip empty input
        if not account_number:
            print("Please enter a valid account number")
            continue
        
        # Analyze account
        results = analyze_account(account_number)
        
        print("\n----------------------------------------")
        print("Ready for next account analysis...")