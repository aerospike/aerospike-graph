import random
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

# Initialize Faker instance
fake = Faker()

def random_timestamp():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    return int(fake.date_time_between(start_date=start_date, end_date=end_date).timestamp() * 1000)

"""
Scenario A simulates a classic money mule pattern where:
1. Multiple small deposits (credits) from different client accounts:
   - 5 transactions between $1,000-$3,000 each
   - Spread across a 4-hour window
   - Coming from random legitimate client accounts

2. Followed by a single large withdrawal (debit):
   - Occurs 3-6 hours after the last deposit
   - Amount is 90-100% of total deposits (simulating fees)
   - Money is sent to fraudster's account

This pattern is typical of money mule operations where fraudsters:
- Break up large amounts into smaller transactions to avoid detection
- Use multiple sources to make deposits look less suspicious
- Use mule account as intermediary to obscure money trail
- Move accumulated money to their account after a short delay
"""
def fraud_scenario_a(transactions, mule_accounts, fraud_accounts, client_accounts):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_a. Consider increasing the number of Customer Records")
        return transactions
    if not fraud_accounts:
        print("⚠️ No fraud accounts available; skipping fraud_scenario_a. Consider increasing the number of Customer Records")
        return transactions
    if not client_accounts:
        print("⚠️ No client accounts available; skipping fraud_scenario_a. Consider increasing the number of Customer Records")
        return transactions

    for a in range(5):
        mule = random.choice(mule_accounts)
        base_time = random_timestamp()
        credit_times = [base_time + 60000 * random.randint(1, 240) for _ in range(5)]
        credits = [random.uniform(1000, 3000) for _ in range(5)]
        fraud_account = random.choice(fraud_accounts)
        transactions.extend([
            {"~from": random.choice(client_accounts), "~to": mule, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": credit_times[i], "amount": credits[i], "type": "credit", "description": "fraud_scenario_a"}
            for i in range(5)
        ])
        last_credit_time = max(credit_times)
        debit_time = last_credit_time + 60000 * random.randint(180, 360)
        transactions.append(
            {"~from": mule, "~to": fraud_account, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": debit_time, "amount": sum(credits) * random.uniform(0.9, 1.0), "type": "debit", "description": "fraud_scenario_a"}
        )
    return transactions

"""
Scenario B simulates a money mule pattern that's the reverse of Scenario A:
1. Single large deposit (credit):
   - One transaction of $10,000-$50,000
   - From a single client account
   - Occurs 3-6 hours before withdrawals

2. Followed by multiple smaller withdrawals (debits):
   - 4 equal-sized withdrawals (large amount split evenly)
   - Spread across a 4-hour window
   - All going to fraudster's account

This pattern demonstrates "structuring" or "smurfing" where:
- Large suspicious deposit is broken into smaller withdrawals
- Multiple smaller transactions may avoid detection systems
- Mule account used to obscure the money trail
"""
def fraud_scenario_b(transactions, mule_accounts, fraud_accounts, client_accounts):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_b. Consider increasing the number of Customer Records")
        return transactions
    if not fraud_accounts:
        print("⚠️ No fraud accounts available; skipping fraud_scenario_b. Consider increasing the number of Customer Records")
        return transactions
    if not client_accounts:
        print("⚠️ No client accounts available; skipping fraud_scenario_b. Consider increasing the number of Customer Records")
        return transactions

    for a in range(5):
        mule = random.choice(mule_accounts)
        base_time = random_timestamp()
        credit_time = base_time - 60000 * random.randint(180, 360) 
        debit_times = [base_time + 60000 * random.randint(0, 240) for _ in range(4)]
        large_credit = random.uniform(10000, 50000)
        fraud_account = random.choice(fraud_accounts)
        debit_splits = [large_credit / 4 for _ in range(4)]
        transactions.append(
            {"~from": random.choice(client_accounts), "~to": mule, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": credit_time, "amount": large_credit, "type": "credit", "description": "fraud_scenario_b"}
        )
        transactions.extend([
            {"~from": mule, "~to": fraud_account, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": debit_times[i], "amount": debit_splits[i], "type": "debit", "description": "fraud_scenario_b"}
            for i in range(4)
        ])
    return transactions

"""
Scenario C simulates suspicious ATM withdrawal patterns:
1. Multiple large ATM withdrawals:
   - 3 withdrawals per mule account
   - Each withdrawal between $5,000-$10,000
   - Self-directed transactions (mule to same mule)
   - Random timestamps

This pattern demonstrates potential structuring of cash withdrawals where:
- Multiple large cash withdrawals just under suspicious activity reporting thresholds
- Same account making repeated large withdrawals
- Common in money laundering where criminals need to convert electronic funds to cash
- Self-directed transactions indicate ATM or cash withdrawal activity
"""
def fraud_scenario_c(transactions, mule_accounts):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_c. Consider increasing the number of Customer Records")
        return transactions

    for a in range(5):
        mule = random.choice(mule_accounts)
        transactions.extend([
            {"~from": mule, "~to": mule, "~label": "suspicious_atm_withdrawal", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(5000, 10000), "type": "debit", "description": "fraud_scenario_c"}
            for _ in range(3)
        ])
    return transactions

"""
Scenario D simulates a network of mule accounts transferring money between themselves:
1. High-frequency random transfers:
   - 10 transactions per mule account
   - Random amounts between $500-$5,000
   - Spread across a 1-hour window
   - Mix of credits and debits
   - Transfers between different mule accounts

This pattern demonstrates "layering" in money laundering where:
- Money moves rapidly between multiple mule accounts
- Random transaction types and amounts to appear chaotic
- Creates complex transaction paths to obscure money trail
- Makes it difficult to track the original source/destination of funds
- Typical of sophisticated money laundering networks using multiple mules
"""
def fraud_scenario_d(transactions, mule_accounts):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_d. Consider increasing the number of Customer Records")
        return transactions

    for a in range(5):
        mule = random.choice(mule_accounts)
        start_time = random_timestamp()
        transactions.extend([
            {"~from": mule, "~to": random.choice(mule_accounts), "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": start_time + 60000 * random.randint(1,60), "amount": random.uniform(500, 5000), "type": random.choice(["credit", "debit"]), "description": "fraud_scenario_d"}
            for i in range(10)
        ])
    return transactions

"""
Scenario E simulates a salary/income-based money laundering pattern:
1. Initial "salary-like" deposit:
   - Single credit between $5,000-$10,000
   - Coming from a client account
   - Mimics legitimate income/salary deposit

2. Followed by multiple suspicious transfers:
   - 3 outgoing transfers per mule
   - Each transfer between $5,000-$7,000
   - Sent to other mule accounts
   - Random timestamps

This pattern demonstrates:
- Attempt to legitimize funds by mimicking regular salary deposits
- Immediate distribution of funds to other mules
- Transfers slightly lower than incoming amount to appear as normal spending
- Common in employment-based money laundering schemes where:
  * Mules are given fake employment
  * Receive seemingly legitimate payments
  * Then distribute funds through the mule network
"""
def fraud_scenario_e(transactions, mule_accounts, client_accounts):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_e. Consider increasing the number of Customer Records")
        return transactions
    if not client_accounts:
        print("⚠️ No client accounts available; skipping fraud_scenario_e. Consider increasing the number of Customer Records")
        return transactions

    for mule in mule_accounts:
        income = random.uniform(5000, 10000)
        transactions.append(
            {"~from": random.choice(client_accounts), "~to": mule, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": income, "type": "credit", "description": "fraud_scenario_e"}
        )
        transactions.extend([
            {"~from": mule, "~to": random.choice(mule_accounts), "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(5000, 7000), "type": "debit", "description": "fraud_scenario_e"}
            for _ in range(3)
        ])
    return transactions

"""
Scenario F simulates dormant account takeover fraud:
1. Large deposit into previously dormant account:
   - Single credit between $10,000-$50,000
   - From a client account
   - Occurs 3-6 hours before withdrawals begin
   - Targets specifically dormant accounts

2. Followed by structured withdrawals:
   - 4 equal-sized withdrawals (large amount split evenly)
   - Spread across a 4-hour window
   - All going to fraudster's account

This pattern demonstrates account takeover fraud where:
- Criminals target inactive/dormant accounts
- Sudden activity after period of dormancy is a red flag
- Similar structuring pattern to Scenario B, but using compromised accounts
- Common in cybercrime where:
  * Hackers gain access to dormant accounts
  * Use them as temporary money laundering vehicles
  * Quick in-and-out transactions before detection
  * Account owner may not notice activity due to inactivity
"""
def fraud_scenario_f(transactions, dormant_accounts, fraud_accounts, client_accounts):
    if not dormant_accounts:
        print("⚠️ No dormant accounts available; skipping fraud_scenario_f. Consider increasing the number of Customer Records")
        return transactions
    if not fraud_accounts:
        print("⚠️ No fraud accounts available; skipping fraud_scenario_f. Consider increasing the number of Customer Records")
        return transactions
    if not client_accounts:
        print("⚠️ No client accounts available; skipping fraud_scenario_f. Consider increasing the number of Customer Records")
        return transactions
    for a in range(5):
        dormant_account = random.choice(dormant_accounts)
        base_time = random_timestamp()
        credit_time = base_time - 60000 * random.randint(180, 360) 
        debit_times = [base_time + 60000 * random.randint(0, 240) for _ in range(4)]
        large_credit = random.uniform(10000, 50000)
        fraud_account = random.choice(fraud_accounts)
        debit_splits = [large_credit / 4 for _ in range(4)]
        transactions.append(
            {"~from": random.choice(client_accounts), "~to": dormant_account, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": credit_time, "amount": large_credit, "type": "credit", "description": "fraud_scenario_f"}
        )
        transactions.extend([
            {"~from": dormant_account, "~to": fraud_account, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": debit_times[i], "amount": debit_splits[i], "type": "debit", "description": "fraud_scenario_f"}
            for i in range(4)
        ])
    return transactions

"""
Scenario G simulates international money laundering:
1. Multiple small-to-medium transfers to high-risk jurisdictions:
   - 5 transactions per mule account
   - Amounts between $500-$5,000
   - All debits (money leaving)
   - Destinations in known high-risk locations (Dubai, Bahrain, Thailand)
   - Recipients marked as "unknown"

This pattern demonstrates:
- International money movement to high-risk jurisdictions
- Multiple smaller transfers to avoid scrutiny
- Typical of international money laundering or terrorist financing
- Transactions to regions known for financial opacity
"""
def fraud_scenario_g(transactions, mule_accounts):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_g. Consider increasing the number of Customer Records")
        return transactions
    for mule in mule_accounts:
        transactions.extend([
            {"~from": mule, "~to": "unknown", "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(500, 5000), "type": "debit", "location": random.choice(["Dubai", "Bahrain", "Thailand"]), "fraud_flag": True, "description": "fraud_scenario_g"}
            for _ in range(5)
        ])
    return transactions

"""
Scenario H simulates region-specific fraud patterns (Indian context):
1. Large suspicious transfers from specific fraud hotspots:
   - 3 transactions per mule account
   - Large amounts between ₹10,000-₹50,000
   - All debits to fraud accounts
   - Originating from known fraud hotspots (Jamtara, Bharatpur, Alwar)
   - Explicitly flagged as fraudulent

This pattern demonstrates:
- Region-specific fraud patterns (Indian cybercrime hotspots)
- Known high-risk geographical areas for financial fraud
- Larger transaction amounts typical of phone/cyber fraud
- Direct transfers to fraudster accounts
- Common in phone scams and cyber fraud originating from these regions
"""
def fraud_scenario_h(transactions, mule_accounts, fraud_accounts, region):
    if not mule_accounts:
        print("⚠️ No mule accounts available; skipping fraud_scenario_h. Consider increasing the number of Customer Records")
        return transactions
    if not fraud_accounts:
        print("⚠️ No fraud accounts available; skipping fraud_scenario_h. Consider increasing the number of Customer Records")
        return transactions

    if region == "indian":
        for a in range(5):
            mule = random.choice(mule_accounts)
            fraud_account = random.choice(fraud_accounts)
            transactions.extend([
                {"~from": mule, "~to": fraud_account, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(10000, 50000), "type": "debit", "location": random.choice(["Jamtara", "Bharatpur", "Alwar"]), "fraud_flag": True, "description": "fraud_scenario_h"}
                for _ in range(3)
            ])
    return transactions
