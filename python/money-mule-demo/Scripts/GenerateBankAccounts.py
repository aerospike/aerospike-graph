import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys
import time

# Initialize Faker instance
fake = Faker()

# Define region-specific bank names, codes, and currencies
region_bank_data = {
    "asian": [("Bank of China", "BOC987"), ("Mizuho Bank", "MIZ456"), ("ICBC", "ICB123")],
    "indian": [("State Bank of India", "SBI001"), ("HDFC Bank", "HDFC002"), ("ICICI Bank", "ICICI003")],
    "european": [("Deutsche Bank", "DB987"), ("BNP Paribas", "BNP456"), ("Santander", "SAN123")],
    "israel": [("Bank Hapoalim", "HAP987"), ("Leumi Bank", "LEU456"), ("Mizrahi-Tefahot", "MIZ123")],
    "american": [("Chase Bank", "CHS987"), ("Wells Fargo", "WF456"), ("Bank of America", "BOA123")]
}

region_currency = {
    "asian": "CNY",
    "indian": "INR",
    "european": "EUR",
    "israel": "ILS",
    "american": "USD"
}

class BankAccount(BaseModel):
    account_id: str = Field(..., description="15-digit numeric account ID")
    bank_name: str = Field(..., description="Name of the bank")
    bank_code: str = Field(..., description="Bank's unique identification code")
    account_type: str = Field(..., description="Type of bank account (e.g., 'Checking', 'Savings')")
    balance: float = Field(..., description="Current balance in the account (Double)")
    currency: str = Field(..., description="Currency type (e.g., 'USD', 'EUR', 'INR')")
    fraud_block: bool = Field(..., description="Indicates if the account is blocked due to fraud (5% chance)")
    status: str = Field(..., description="Status of the account (e.g., 'dormant', 'active', 'closed', 'reactivated')")
    open_date: int = Field(..., description="Epoch time in milliseconds when the account was opened (Long)")

    @classmethod
    def generate(cls, region: str):
        """Generates a bank account with region-specific data."""
        bank_name, bank_code = random.choice(region_bank_data[region])
        return cls(
            account_id=str(random.randint(10**14, 10**15 - 1)),
            bank_name=bank_name,
            bank_code=bank_code,
            account_type=random.choices(["Savings", "Checking"], weights=[70, 30])[0],
            balance=round(random.uniform(1000.00, 1000000.00), 2),
            currency=region_currency[region],
            fraud_block=random.random() < 0.05,
            status=random.choices(["active", "dormant", "closed", "reactivated"], weights=[80, 7, 7, 6])[0],
            open_date=int(fake.date_time_this_decade().timestamp() * 1000)
        )

def generate_bank_accounts(region: str):
    os.makedirs("./dataset/vertices/bank_accounts", exist_ok=True)
    os.makedirs("./dataset/edges/rel-customer-bank_account", exist_ok=True)
    os.makedirs("./dataset/edges/rel-mobile-bank_account", exist_ok=True)

    customer_df = pd.read_csv("./dataset/vertices/customers/customer.csv")
    rel_customer_mobile_df = pd.read_csv("./dataset/edges/rel-customer-mobile/rel-customer-mobile.csv")

    if "~id" not in customer_df.columns:
        raise ValueError("customer.csv does not have the expected columns ('~id').")

    customers = customer_df.to_dict(orient="records")
    customer_mobiles = rel_customer_mobile_df.groupby("~from")["~to"].apply(list).to_dict()

    mobile_shared = rel_customer_mobile_df.groupby("~to")["~from"].apply(list).to_dict()
    
    bank_records = []
    customer_bank_relations = []
    mobile_bank_relations = {}
    
    for customer in customers:
        customer_id = customer["~id"]
        bank_account = BankAccount.generate(region)
        bank_records.append(bank_account.model_dump())
        customer_bank_relations.append({"~from": customer_id, "~to": bank_account.account_id, "~label": "has_account"})
        
        if customer_id in customer_mobiles:
            primary_mobile = random.choice(customer_mobiles[customer_id])
            mobile_bank_relations[bank_account.account_id] = primary_mobile
        
    for mobile, users in mobile_shared.items():
        if len(users) > 2:
            shared_users = random.sample(users, len(users) // 2)
            for user in shared_users:
                bank_accounts = [acc["account_id"] for acc in bank_records if acc["account_id"] in [rel["~to"] for rel in customer_bank_relations if rel["~from"] == user]]
                for acc in bank_accounts:
                    mobile_bank_relations[acc] = mobile
    
    bank_df = pd.DataFrame(bank_records)
    customer_bank_df = pd.DataFrame(customer_bank_relations)
    mobile_bank_df = pd.DataFrame([{"~from": mobile, "~to": acc, "~label": "primary_mobile"} for acc, mobile in mobile_bank_relations.items()])
    
    bank_df.rename(columns={"account_id": "~id", "balance": "balance:Double", "fraud_block": "fraud_block:Boolean", "open_date": "open_date:Long"}, inplace=True)
    bank_df["~label"] = "Bank Account"
    
    bank_df.to_csv("./dataset/vertices/bank_accounts/bank_account.csv", index=False)
    customer_bank_df.to_csv("./dataset/edges/rel-customer-bank_account/rel-customer-bank_account.csv", index=False)
    mobile_bank_df.to_csv("./dataset/edges/rel-mobile-bank_account/rel-mobile-bank_account.csv", index=False)
    
    print("Generated bank_account.csv, rel-customer-bank_account.csv, and rel-mobile-bank_account.csv successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GenerateBankAccounts.py <region>")
        sys.exit(1)
    region = sys.argv[1].lower()
    generate_bank_accounts(region)
