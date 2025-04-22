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

def fraud_scenario_a(transactions, mule_accounts, fraud_accounts, client_accounts):
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

def fraud_scenario_b(transactions, mule_accounts, fraud_accounts, client_accounts):
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

def fraud_scenario_c(transactions, mule_accounts):
    for a in range(5):
        mule = random.choice(mule_accounts)
        transactions.extend([
            {"~from": mule, "~to": mule, "~label": "suspicious_atm_withdrawal", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(5000, 10000), "type": "debit", "description": "fraud_scenario_c"}
            for _ in range(3)
        ])
    return transactions

def fraud_scenario_d(transactions, mule_accounts):
    for a in range(5):
        mule = random.choice(mule_accounts)
        start_time = random_timestamp()
        transactions.extend([
            {"~from": mule, "~to": random.choice(mule_accounts), "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": start_time + 60000 * random.randint(1,60), "amount": random.uniform(500, 5000), "type": random.choice(["credit", "debit"]), "description": "fraud_scenario_d"}
            for i in range(10)
        ])
    return transactions

def fraud_scenario_e(transactions, mule_accounts, client_accounts):
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

def fraud_scenario_f(transactions, dormant_accounts, fraud_accounts, client_accounts):
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

def fraud_scenario_g(transactions, mule_accounts):
    for mule in mule_accounts:
        transactions.extend([
            {"~from": mule, "~to": "unknown", "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(500, 5000), "type": "debit", "location": random.choice(["Dubai", "Bahrain", "Thailand"]), "fraud_flag": True, "description": "fraud_scenario_g"}
            for _ in range(5)
        ])
    return transactions

def fraud_scenario_h(transactions, mule_accounts, fraud_accounts, region):
    if region == "indian":
        for a in range(5):
            mule = random.choice(mule_accounts)
            fraud_account = random.choice(fraud_accounts)
            transactions.extend([
                {"~from": mule, "~to": fraud_account, "~label": "suspicious_transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(10000, 50000), "type": "debit", "location": random.choice(["Jamtara", "Bharatpur", "Alwar"]), "fraud_flag": True, "description": "fraud_scenario_h"}
                for _ in range(3)
            ])
    return transactions
