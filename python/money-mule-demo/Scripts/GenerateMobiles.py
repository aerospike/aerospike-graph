import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys

# Define country code mappings for different regions
region_country_codes = {
    "asian": ["+86", "+81", "+82", "+66"],
    "indian": ["+91"],
    "european": ["+33", "+49", "+34", "+39", "+31"],
    "israel": ["+972"],
    "american": ["+1"]
}

# Initialize Faker instances for different regions
faker_instances = {
    "asian": Faker(["zh_CN", "ja_JP", "ko_KR", "th_TH"]),
    "indian": Faker(["en_IN"]),
    "european": Faker(["fr_FR", "de_DE", "es_ES", "it_IT", "nl_NL"]),
    "israel": Faker(["he_IL"]),
    "american": Faker(["en_US"]),
}

class Mobile(BaseModel):
    mobile_number: str = Field(..., description="Mobile number assigned to a customer")

    @classmethod
    def generate(cls, region: str):
        """Generate a new mobile number based on the region"""
        fake = faker_instances.get(region, Faker())
        country_code = random.choice(region_country_codes[region])
        mobile_number = f"{country_code} {fake.msisdn()}"  # Generate a valid mobile number
        return cls(mobile_number=mobile_number)

def clean_mobile_number(mobile_number: str, region: str):
    """Ensure the country code appears only once in the mobile number."""
    if not isinstance(mobile_number, str):
        return None

    country_code = random.choice(region_country_codes[region])
    mobile_number = mobile_number.strip()

    while mobile_number.startswith(country_code):
        mobile_number = mobile_number[len(country_code):].strip()

    return f"{country_code} {mobile_number}"

def generate_mobiles(region: str):
    os.makedirs("./dataset/vertices/mobiles", exist_ok=True)
    os.makedirs("./dataset/edges/rel-customer-mobile", exist_ok=True)

    customer_df = pd.read_csv("./dataset/vertices/customers/customer.csv")
    rel_customer_address_df = pd.read_csv("./dataset/edges/rel-customer-address/rel-customer-address.csv")

    if "~id" not in customer_df.columns or "phone_number" not in customer_df.columns:
        raise ValueError("customer.csv does not have the expected columns ('~id', 'phone_number').")

    customers = customer_df.to_dict(orient="records")
    rel_customer_address = rel_customer_address_df.groupby("~to")["~from"].apply(list).to_dict()

    mobile_records = []
    rel_records = []
    assigned_mobiles = {}
    fake = faker_instances.get(region, Faker())

    # Assign mobiles to customers
    for customer in customers:
        customer_id = customer["~id"]
        phone_number = customer["phone_number"]
        spouse_name = customer.get("spouse_name")

        mobile_number = Mobile.generate(region).mobile_number
        mobile_number = clean_mobile_number(mobile_number, region)
        assigned_mobiles[customer_id] = mobile_number

        rel_records.append({"~from": customer_id, "~to": mobile_number, "~label": "has_mobile"})

        if mobile_number not in mobile_records:
            mobile_records.append({"~id": mobile_number, "~label": "Mobile"})

    # Handle shared address cases (more than 2 residents)
    for address, residents in rel_customer_address.items():
        if len(residents) > 2:
            shared_count = int(len(residents) * 0.5)  # 50% of them should share a mobile
            shared_residents = random.sample(residents, shared_count)
            shared_mobile = Mobile.generate(region).mobile_number
            shared_mobile = clean_mobile_number(shared_mobile, region)

            if shared_mobile not in mobile_records:
                mobile_records.append({"~id": shared_mobile, "~label": "Mobile"})

            for resident in shared_residents:
                rel_records.append({"~from": resident, "~to": shared_mobile, "~label": "has_mobile"})

    # Convert lists to DataFrames
    mobile_df = pd.DataFrame(mobile_records)
    rel_df = pd.DataFrame(rel_records)

    # Save to CSV files
    mobile_df.to_csv("./dataset/vertices/mobiles/mobile.csv", index=False)
    rel_df.to_csv("./dataset/edges/rel-customer-mobile/rel-customer-mobile.csv", index=False)

    print("Generated mobile.csv and rel-customer-mobile.csv successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GenerateMobiles.py <region>")
        sys.exit(1)
    region = sys.argv[1].lower()
    generate_mobiles(region)
