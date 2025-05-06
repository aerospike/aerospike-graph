import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys
from datetime import timezone
import calendar

# Initialize Faker instances per region
faker_instances = {
    "asian": Faker(["zh_CN", "ja_JP", "ko_KR", "th_TH"]),
    "indian": Faker(["en_IN"]),
    "european": Faker(["fr_FR", "de_DE", "es_ES", "it_IT", "nl_NL"]),
    "israel": Faker(["he_IL"]),
    "american": Faker(["en_US"]),
}

# Country mapping
region_country_map = {
    "asian": "China",
    "indian": "India",
    "european": "France",
    "israel": "Israel",
    "american": "USA"
}

# National ID format mapping
national_id_formats = {
    "american": lambda fake: fake.ssn(),
    "indian": lambda fake: fake.random_int(min=100000000000, max=999999999999),  # 12-digit Aadhaar
    "european": lambda fake: fake.ssn(),
    "israel": lambda fake: fake.random_int(min=100000000, max=999999999),  # 9-digit Teudat Zehut
    "asian": lambda fake: fake.ssn()
}

def datetime_to_millis(dt):
    # Ensure dt is timezone‐aware in UTC so timestamp() is unambiguous
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    try:
        # This will raise OSError on Windows if dt < 1970-01-01
        return int(dt.timestamp() * 1000)
    except OSError:
        # Fallback: use calendar.timegm on the UTC tuple + microseconds
        return calendar.timegm(dt.utctimetuple()) * 1000 + (dt.microsecond // 1000)

class NationalID(BaseModel):
    national_id: str = Field(..., description="Unique national identifier")
    issued_ctry: str = Field(..., description="Country where ID was issued")
    issued_date: int = Field(..., description="Epoch timestamp (ms) when the ID was issued")
    date_of_birth: int = Field(..., description="Epoch timestamp (ms) of the holder's birth date")
    name: str = Field(..., description="Full name of the ID holder")
    address: str = Field(..., description="Registered address of the ID holder")

    @classmethod
    def generate(cls, customer, address, fake, region):
        issued_date = fake.date_time_between(start_date="-30y", end_date="-5y")
        date_of_birth = fake.date_time_between(start_date="-80y", end_date="-18y")

        #Windows only supports dates on/after UNIX epoch, so we fall back on timegm if we get an os error
        issued_ms = datetime_to_millis(issued_date)
        dob_ms    = datetime_to_millis(date_of_birth)
        return cls(
            national_id=str(national_id_formats[region](fake)),
            issued_ctry=region_country_map[region],
            issued_date=int(issued_ms),
            date_of_birth=int(dob_ms),
            name=customer['name'],
            address=address
        )

def generate_national_ids(region):
    os.makedirs("./dataset/vertices/national_ids", exist_ok=True)
    os.makedirs("./dataset/edges/rel-customer-national_id", exist_ok=True)
    
    if region != "indian":
        print("Skipping National_ID to Bank_Account linking as this is only applicable for the Indian region.")
    else:
      os.makedirs("./dataset/edges/rel-national_id-bank_account", exist_ok=True)
    
    # Read customer and bank account data
    customer_df = pd.read_csv("./dataset/vertices/customers/customer.csv")
    rel_customer_address_df = pd.read_csv("./dataset/edges/rel-customer-address/rel-customer-address.csv")
    address_df = pd.read_csv("./dataset/vertices/addresses/address.csv")
    bank_account_df = pd.read_csv("./dataset/vertices/bank_accounts/bank_account.csv")
    rel_customer_bank_df = pd.read_csv("./dataset/edges/rel-customer-bank_account/rel-customer-bank_account.csv")
    
    if "~id" not in customer_df.columns or "name" not in customer_df.columns:
        raise ValueError("customer.csv does not have the expected columns ('~id', 'name', 'type').")
    
    # Merge customer and address relationship data
    rel_customer_address = rel_customer_address_df.groupby("~from")["~to"].apply(list).to_dict()
    address_map = address_df.set_index("~id")["street"].to_dict()
    customer_bank_map = rel_customer_bank_df.groupby("~from")["~to"].apply(list).to_dict()
    
    customers = customer_df.to_dict(orient="records")
    national_id_records = []
    customer_national_id_relations = []
    national_id_bank_relations = []
    
    fake = faker_instances.get(region, Faker())
    
    for customer in customers:
        addresses = rel_customer_address.get(customer["~id"], [])
        if addresses:
            assigned_address = random.choice(addresses)
            address_str = address_map.get(assigned_address, "Unknown Address")
            national_id = NationalID.generate(customer, address_str, fake, region)
            national_id_records.append(national_id.model_dump())
            customer_national_id_relations.append({"~from": customer["~id"], "~to": national_id.national_id, "~label": "has_national_id"})
            
            # Assign National ID to Bank Account for 30% of Individual customers only for Indian region
            if region == "indian" and customer["type"].lower() == "individual" and random.random() < 0.3:
                bank_accounts = customer_bank_map.get(customer["~id"], [])
                for bank_account in bank_accounts:
                    national_id_bank_relations.append({"~from": national_id.national_id, "~to": bank_account, "~label": "linked_to_bank"})
    
    df = pd.DataFrame(national_id_records)
    df.rename(columns={
        "national_id": "~id",
        "issued_date": "issued_date:Long",
        "date_of_birth": "date_of_birth:Long",
    }, inplace=True)

    df["~label"] = "National_ID"
    df.to_csv("./dataset/vertices/national_ids/national_id.csv", index=False)
    
    rel_df = pd.DataFrame(customer_national_id_relations)
    rel_df.to_csv("./dataset/edges/rel-customer-national_id/rel-customer-national_id.csv", index=False)
    
    if region == "indian": 
      rel_bank_df = pd.DataFrame(national_id_bank_relations)
      rel_bank_df.to_csv("./dataset/edges/rel-national_id-bank_account/rel-national_id-bank_account.csv", index=False)
      print("Generated national_id.csv, rel-customer-national_id.csv, and rel-national_id-bank_account.csv successfully.")
    else:
      print("Generated national_id.csv, rel-customer-national_id.csv successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GenerateNationalId.py <region>")
        sys.exit(1)
    region = sys.argv[1].lower()
    generate_national_ids(region)
