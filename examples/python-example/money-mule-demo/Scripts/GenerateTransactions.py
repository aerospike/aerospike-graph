import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys
import time
from datetime import datetime, timedelta
import GenerateFraudTransactions

# Initialize Faker instance
fake = Faker()

transaction_types = ["credit", "debit"]
transaction_statuses = ["active", "dormant", "closed"]
fraud_prob = 0.05  # 5% fraud transactions

channel_options = {
    "indian": ["NEFT", "RTGS", "IMPS", "ECS", "ATM", "ONLINE", "MOBILE", "UPI", "BRANCH", "SWIFT"],
    "default": ["ATM", "ONLINE", "MOBILE", "BRANCH", "SWIFT", "FAST"]
}

receiver_account_types = {
    "asian": ["current", "savings"],
    "default": ["current", "deposit"]
}

region_city_map = {
    "asian": ["Tokyo", "Seoul", "Shanghai", "Bangkok"],
    "indian": ["Mumbai", "Delhi", "Bangalore", "Hyderabad"],
    "european": ["Paris", "Berlin", "Madrid", "Rome"],
    "israel": ["Tel Aviv", "Jerusalem", "Haifa", "Eilat"],
    "american": ["New York", "Los Angeles", "Chicago", "Houston"]
}

region_banks = {
    "indian": {"SBI": "SBI001", "HDFC": "HDFC002", "ICICI": "ICICI003", "Axis Bank": "AXIS004"},
    "american": {"Chase": "CHS987", "Bank of America": "BOA123", "Wells Fargo": "WF456"},
    "european": {"Deutsche Bank": "DB987", "BNP Paribas": "BNP456", "Santander": "SAN123"},
    "asian": {"Mizuho Bank": "MIZ987", "ICBC": "ICB123", "Bank of China": "BOC456"},
    "israel": {"Leumi": "LEU987", "Hapoalim": "HAP456", "Mizrahi": "MIZ123"}
}

# Get timestamp range for last 3 months
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

def random_timestamp():
    return int(fake.date_time_between(start_date=start_date, end_date=end_date).timestamp() * 1000)

def identify_client_and_fraud_accounts(bank_account_df):
    bank_code_counts = bank_account_df['bank_code'].value_counts()
    client_bank = bank_code_counts.idxmax()
    fraud_accounts = bank_account_df[bank_account_df['bank_code'] != client_bank]
    if fraud_accounts.empty:
        fraud_accounts = bank_account_df.sample(frac=0.02, random_state=42)
    fraud_accounts = fraud_accounts['~id'].tolist()
    return client_bank, fraud_accounts

def identify_mule_accounts(bank_account_df, customer_address_df, customer_bank_account_df, client_bank):
    shared_addresses = customer_address_df.groupby('~to')['~from'].apply(list)
    shared_customers = shared_addresses[shared_addresses.apply(len) > 3].explode().tolist()
    
    if not shared_customers:
        shared_customers = customer_address_df['~from'].sample(n=min(2, len(customer_address_df)), random_state=42).tolist()
    
    mule_accounts = customer_bank_account_df[
    customer_bank_account_df['~from'].isin(shared_customers) &
    customer_bank_account_df['~to'].isin(bank_account_df[~bank_account_df['status'].isin(['dormant', 'closed'])]['~id'])
]['~to'].tolist()
    #additional_mule_accounts = bank_account_df[(bank_account_df['bank_code'] == client_bank) & (bank_account_df['status'].isin(['active', 'reactivated']))].sample(frac=0.01, random_state=42)['~id'].tolist()
    #mule_accounts.extend(additional_mule_accounts)
    return mule_accounts

def identify_dormant_accounts(bank_account_df):
    dormant_accounts = bank_account_df[bank_account_df['status'] == 'dormant']
    dormant_accounts = dormant_accounts['~id'].tolist()
    return dormant_accounts
                       
salary_channel_options = {
    "indian": ["NEFT", "RTGS", "IMPS"],
    "default": ["FAST", "ONLINE"]
}

def generate_non_fraud_transactions(transactions, client_accounts, bank_account_df, region):
    recurring_recipients = {}
    current_accounts = bank_account_df[bank_account_df['account_type'] == 'Checking']['~id'].tolist()
        
    for account in client_accounts:
        account_type = bank_account_df.loc[bank_account_df['~id'] == account, 'account_type'].values[0]
        bank_code = bank_account_df.loc[bank_account_df['~id'] == account, 'bank_code'].values[0]
        bank_name = bank_account_df.loc[bank_account_df['~id'] == account, 'bank_name'].values[0]
        account_status = bank_account_df.loc[bank_account_df['~id'] == account, 'status'].values[0]
        if account_status in ('dormant', 'closed'): continue
        
        for month in range(3):
            num_transactions = random.randint(5, 20)
            transaction_dates = sorted([random_timestamp() for _ in range(num_transactions)])
            
            if account_type in ["Savings", "Deposit"] and random.random() <= 0.7:
                salary_amount = random.uniform(2000, 5000)
                salary_sender = random.choice(current_accounts)
                transactions.append({
                    "~from": salary_sender, "~to": account, "~label": "transaction", "transaction_id": fake.uuid4(), "datetime": transaction_dates[0], "amount": salary_amount, "type": "credit", "fraud_flag": False,
                    "channel": random.choice(salary_channel_options.get(region, salary_channel_options["default"])), "receiver_bank": bank_name, "receiver_bank_code": bank_code, "receiver_account_type": account_type,
                    "description": "SALARY"
                })
            
            for i in range(1, num_transactions):
                receiver = random.choice(client_accounts) if random.random() <= 0.5 else random.choice(bank_account_df['~id'].tolist())
                amount = random.uniform(10, 2000)
                transactions.append({
                    "~from": account, "~to": receiver, "~label": "transaction", "transaction_id": fake.uuid4(), "datetime": transaction_dates[i], "amount": amount, "type": "debit", "fraud_flag": False,
                    "channel": random.choice(channel_options.get(region, channel_options["default"])), "receiver_bank": bank_name, "receiver_bank_code": bank_code, "receiver_account_type": account_type,
                    "description": "General Transaction"
                })
                
                if account not in recurring_recipients:
                    recurring_recipients[account] = [receiver]
                elif receiver not in recurring_recipients[account] and len(recurring_recipients[account]) < 3:
                    recurring_recipients[account].append(receiver)
                
            for receiver in recurring_recipients.get(account, []):
                transactions.append({
                    "~from": account, "~to": receiver, "~label": "transaction", "transaction_id": fake.uuid4(), "datetime": random_timestamp(), "amount": random.uniform(50, 500), "type": "debit", "fraud_flag": False,
                    "channel": random.choice(channel_options.get(region, channel_options["default"])), "receiver_bank": bank_name, "receiver_bank_code": bank_code, "receiver_account_type": account_type,
                    "description": "Recurring Payment"
                })
    
    return transactions

def generate_transactions(region):
    os.makedirs("./dataset/edges/transactions", exist_ok=True)
    
    bank_account_df = pd.read_csv("./dataset/vertices/bank_accounts/bank_account.csv")
    customer_address_df = pd.read_csv("./dataset/edges/rel-customer-address/rel-customer-address.csv")
    customer_bank_account_df = pd.read_csv("./dataset/edges/rel-customer-bank_account/rel-customer-bank_account.csv")
    
    account_ids = bank_account_df['~id'].tolist()
    client_bank, fraud_accounts = identify_client_and_fraud_accounts(bank_account_df)
    mule_accounts = identify_mule_accounts(bank_account_df, customer_address_df, customer_bank_account_df, client_bank)
    dormant_accounts = identify_dormant_accounts(bank_account_df)
    client_accounts = bank_account_df[bank_account_df['bank_code'] == client_bank]['~id'].tolist()
    
    transactions = []
    transactions = GenerateFraudTransactions.fraud_scenario_a(transactions, mule_accounts, fraud_accounts, client_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_b(transactions, mule_accounts, fraud_accounts, client_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_c(transactions, mule_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_d(transactions, mule_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_e(transactions, mule_accounts, fraud_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_f(transactions, dormant_accounts, fraud_accounts, client_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_g(transactions, mule_accounts)
    transactions = GenerateFraudTransactions.fraud_scenario_h(transactions, mule_accounts, fraud_accounts, region)
    transactions = generate_non_fraud_transactions(transactions, client_accounts, bank_account_df, region)
    df = pd.DataFrame(transactions)
    df["amount"] = df["amount"].round(2)
    df.rename(columns={"datetime": "datetime:Long",
                       "amount": "amount:Double",
                       "fraud_flag": "fraud_flag:Boolean",}, inplace=True)
    df.to_csv("./dataset/edges/transactions/transaction.csv", index=False)
    
    print("Generated transaction.csv successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GenerateTransaction.py <region>")
        sys.exit(1)
    region = sys.argv[1].lower()
    generate_transactions(region)
