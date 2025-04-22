import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys

# Initialize Faker instances per region
faker_instances = {
    "asian": Faker(["zh_CN", "ja_JP", "ko_KR", "th_TH"]),
    "indian": Faker(["en_IN"]),
    "european": Faker(["fr_FR", "de_DE", "es_ES", "it_IT", "nl_NL"]),
    "israel": Faker(["he_IL"]),
    "american": Faker(["en_US"]),
}

# Define region-to-country mapping
region_to_country = {
    "asian": "China",
    "indian": "India",
    "european": "France",
    "israel": "Israel",
    "american": "United States"
}

class Address(BaseModel):
    address_id: str = Field(..., description="Unique identifier for the address")
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State/Province name")
    postal_code: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country name")

    @classmethod
    def generate(cls, region: str):
        fake = faker_instances.get(region, Faker())
        if not isinstance(fake, Faker):
            fake = Faker()

        try:
            state_name = fake.state()
        except AttributeError:
        # Use an alternative like province, prefecture, or fallback value
            if region == "asian":
                state_name = fake.prefecture() if hasattr(fake, "prefecture") else ""
            else:
                state_name = ""

        return cls(
            address_id=fake.uuid4(),
            street=fake.street_address().replace("\n", " "),  # Ensure no line breaks
            city=fake.city(),
            state=state_name,
            postal_code=fake.postcode(),
            country=region_to_country[region]  # Ensure country consistency with region
        )

def generate_addresses(region: str):
    # Ensure directories exist
    os.makedirs("./dataset/vertices/addresses", exist_ok=True)
    os.makedirs("./dataset/edges/rel-customer-address", exist_ok=True)

    # Read customer data
    customer_df = pd.read_csv("./dataset/vertices/customers/customer.csv")

    if "~id" not in customer_df.columns or "spouse_name" not in customer_df.columns:
        raise ValueError("customer.csv does not have the expected columns ('~id', 'spouse_name').")

    customers = customer_df.to_dict(orient="records")

    address_map = {}  # Stores assigned addresses for customers
    shared_addresses = []  # Stores addresses to be shared (for 1% irregular cases)
    address_records = []  # Stores unique address records
    rel_records = []  # Stores relationship mappings (~from, ~to, ~label)

    # Determine how many customers will share addresses
    num_shared = int(len(customers) * 0.01)
    customers_to_share = random.sample(customers, num_shared)

    for customer in customers:
        customer_id = customer["~id"]
        spouse_name = customer["spouse_name"]

        # If this customer is in the 1% who should share an address
        if customer in customers_to_share and len(shared_addresses) > 0:
            assigned_address = random.choice(shared_addresses)  # Assign existing shared address
        else:
            # Generate a new address for 90% of customers using the correct region
            new_address = Address.generate(region)
            assigned_address = new_address.model_dump()
            address_records.append(assigned_address)

            # Add to shared pool (max 3 customers per shared address)
            if len(shared_addresses) < num_shared // 5:
                shared_addresses.append(assigned_address)

        # Assign address to customer
        address_map[customer_id] = assigned_address["address_id"]

        # Create relationship entry for customer
        rel_records.append({
            "~from": customer_id,
            "~to": assigned_address["address_id"],
            "~label": "residence"
        })

        # If customer has a spouse, assign the same address
        if pd.notna(spouse_name):
            spouse = next((c for c in customers if c["name"] == spouse_name), None)
            if spouse:
                address_map[spouse["~id"]] = assigned_address["address_id"]
                rel_records.append({
                    "~from": spouse["~id"],
                    "~to": assigned_address["address_id"],
                    "~label": "residence"
                })

    # Convert to DataFrames
    address_df = pd.DataFrame(address_records)
    rel_df = pd.DataFrame(rel_records)

    # Rename only the address_id column in address.csv
    address_df.rename(columns={"address_id": "~id"}, inplace=True)

    # Ensure only one '~label' column with value 'Address'
    address_df["~label"] = "Address"

    # Save to CSV files
    address_df.to_csv("./dataset/vertices/addresses/address.csv", index=False)
    rel_df.to_csv("./dataset/edges/rel-customer-address/rel-customer-address.csv", index=False)

    print("Generated address.csv and rel-customer-address.csv successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GenerateAddresses.py <region>")
        sys.exit(1)

    region = sys.argv[1].lower()
    generate_addresses(region)
