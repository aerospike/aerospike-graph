import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys

# Initialize Faker instance for generating PAN numbers
fake = Faker("en_IN")

class PAN(BaseModel):
    pan: str = Field(..., description="Unique PAN (Tax ID) for India")

    @classmethod
    def generate(cls):
        return cls(pan=fake.bothify(text="?????####?", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

def generate_pan(region):
    if region != "indian":
        print("Skipping Tax Id generation as this is only applicable for the Indian region.")
        return
    
    os.makedirs("./dataset/vertices/pan", exist_ok=True)
    os.makedirs("./dataset/edges/rel-national_id-PAN", exist_ok=True)
    os.makedirs("./dataset/edges/rel-pan-bank_account", exist_ok=True)
    
    # Read necessary data
    national_id_df = pd.read_csv("./dataset/vertices/national_ids/national_id.csv")
    rel_customer_bank_df = pd.read_csv("./dataset/edges/rel-customer-bank_account/rel-customer-bank_account.csv")
    rel_customer_address_df = pd.read_csv("./dataset/edges/rel-customer-address/rel-customer-address.csv")
    rel_customer_national_id_df = pd.read_csv("./dataset/edges/rel-customer-national_id/rel-customer-national_id.csv")
    
    if "~id" not in national_id_df.columns:
        raise ValueError("national_id.csv does not have the expected columns ('~id').")
    
    # Generate PAN records
    pan_records = []
    national_id_pan_relations = []
    pan_bank_relations = []
    
    pan_mapping = {}
    for _, row in national_id_df.iterrows():
        pan = PAN.generate()
        pan_records.append({"~id": pan.pan, "~label": "PAN"})
        national_id_pan_relations.append({"~from": row["~id"], "~to": pan.pan, "~label": "belongs_to"})
        pan_mapping[row["~id"]] = pan.pan
    
    # Map customers to their national_id
    customer_national_id_map = rel_customer_national_id_df.set_index("~from")["~to"].to_dict()
    
    # Process shared addresses to limit PAN assignment
    rel_customer_address = rel_customer_address_df.groupby("~to")["~from"].apply(list).to_dict()
    irregular_addresses = {addr: customers for addr, customers in rel_customer_address.items() if len(customers) > 2}
    
    selected_pan_mapping = {}
    for addr, customers in irregular_addresses.items():
        selected_customers = random.sample(customers, min(3, len(customers)))
        assigned_pans = {cust: pan_mapping.get(customer_national_id_map.get(random.sample(selected_customers,1)[0], None), None) for cust in customers if cust in customer_national_id_map}
        selected_pan_mapping.update(assigned_pans)
    
    # Assign PANs for shared address customers first
    for _, rel in rel_customer_bank_df.iterrows():
        customer_id = rel["~from"]
        bank_account_id = rel["~to"]
        
        if customer_id in selected_pan_mapping and selected_pan_mapping[customer_id]:
            selected_pan = selected_pan_mapping[customer_id]
            pan_bank_relations.append({"~from": selected_pan, "~to": bank_account_id, "~label": "linked_to_bank"})
    
    # Assign PANs to regular bank account owners who were not part of shared addresses
    for _, rel in rel_customer_bank_df.iterrows():
        customer_id = rel["~from"]
        bank_account_id = rel["~to"]
        
        if customer_id not in selected_pan_mapping:
            national_id = customer_national_id_map.get(customer_id, None)
            if national_id and national_id in pan_mapping:
                pan_bank_relations.append({"~from": pan_mapping[national_id], "~to": bank_account_id, "~label": "linked_to_bank"})
    
    # Save to CSV files
    pd.DataFrame(pan_records).to_csv("./dataset/vertices/pan/pan.csv", index=False)
    pd.DataFrame(national_id_pan_relations).to_csv("./dataset/edges/rel-national_id-PAN/rel-national_id-PAN.csv", index=False)
    
    if pan_bank_relations:
        pd.DataFrame(pan_bank_relations).to_csv("./dataset/edges/rel-pan-bank_account/rel-pan-bank_account.csv", index=False)
    else:
        print("No PAN to Bank Account relationships were generated.")
    
    print("Generated pan.csv, rel-national_id-PAN.csv, and rel-pan-bank_account.csv successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GeneratePAN.py <region>")
        sys.exit(1)
    region = sys.argv[1].lower()
    generate_pan(region)
