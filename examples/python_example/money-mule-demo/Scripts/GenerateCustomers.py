import os
import pandas as pd
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import random
import string
import gender_guesser.detector as gender
from faker import Faker

# Initialize Faker instances per region
faker_instances = {
    "asian": Faker(["en_AU", "en_PH"]),
    "indian": Faker(["en_IN"]),
    "european": Faker(["en_GB"]),
    "israel": Faker(["he_IL"]),
    "american": Faker(["en_US"]),
}

# Country codes by region
country_codes = {
    "asian": "+65",
    "indian": "+91",
    "european": "+33",
    "israel": "+972",
    "american": "+1"
}

# Email domains
email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com", "fakemail.com", "tempmail.net"]

class Customer(BaseModel):
    customer_id: str
    name: str
    gender: str
    marital_status: str
    spouse_name: Optional[str]
    phone_number: str
    email: EmailStr
    annual_income: Optional[int]
    type: str
    revenue: Optional[int]
    occupation: str
    blacklisted: bool
    created_at: int
    last_active: int
    label: str

    @classmethod
    def generate_sample(cls, region: str, fake, name: Optional[str] = None, marital_status: Optional[str] = None, spouse_name: Optional[str] = None):
        def random_customer_id():
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        def clean_email(email):
            """Ensure no consecutive dots in email addresses and no dot before '@'."""
            local_part, domain = email.split("@")
            local_part = local_part.replace("..", ".")  # Replace consecutive dots
            local_part = local_part.rstrip(".")  # Remove trailing dot before '@'
            return f"{local_part}@{domain}"

        def generate_email(name):
            name_part = name.lower().replace(" ", ".")
            return clean_email(f"{name_part}@{random.choice(email_domains)}")

        def clean_phone_number(phone_number, region):
            """Ensure phone numbers do not have repeating country codes."""
            country_code = country_codes[region]
            phone_number = phone_number.strip()

            # Remove duplicate occurrences of the country code at the start
            while phone_number.startswith(country_code):
                phone_number = phone_number[len(country_code):].strip()

            # Ensure only one instance of the country code is added
            return f"{country_code} {phone_number}"

        full_name = name if name else fake.name()
        first_name = full_name.split()[0]

        # Predict gender using name
        detected_gender = gender.Detector().get_gender(first_name)
        if detected_gender in ["male", "mostly_male"]:
            gender_value = "Male"
        elif detected_gender in ["female", "mostly_female"]:
            gender_value = "Female"
        else:
            gender_value = random.choice(["Male", "Female"])  # Default fallback

        # Ensure marital_status is set before assigning spouse
        if marital_status is None:
            marital_status = random.choices(["Single", "Married", "Divorced", "Widowed"], weights=[50, 30, 10, 10])[0]

        is_business = fake.boolean(chance_of_getting_true=20)  # 20% chance of being a business
        is_blacklisted = fake.boolean(chance_of_getting_true=5)  # 5% chance of being blacklisted
        revenue = round(random.uniform(1000000, 50000000)) if is_business else 0
        annual_income = round(random.uniform(35000, 1000000)) if not is_business else 0

        # Generate and clean phone number
        raw_phone = fake.phone_number()
        phone_number = clean_phone_number(f"{country_codes[region]} {raw_phone}", region)

        return cls(
            customer_id=random_customer_id(),
            name=full_name,
            gender=gender_value,
            marital_status=marital_status,
            spouse_name=spouse_name if marital_status == "Married" else None,
            phone_number=phone_number,
            email=generate_email(full_name),
            annual_income=annual_income,
            type="business" if is_business else "individual",
            revenue=revenue,
            occupation=fake.job(),
            blacklisted=is_blacklisted,
            created_at=int(fake.date_time_this_decade().timestamp() * 1000),
            last_active=int(fake.date_time_this_year().timestamp() * 1000),
            label="Customer"
        )

def generate_customer_data(num_records: int, region: str):
    """
    Generates customer data for a specified number of records and region.
    Ensures that every married individual has a spouse record with a proper reference.
    """

    # Ensure directories exist
    os.makedirs("./dataset/vertices/customers", exist_ok=True)
    os.makedirs("./dataset/edges/rel-customer-address", exist_ok=True)

    if region not in faker_instances:
        raise ValueError("Invalid region. Choose from: asian, indian, european, israel, american")
    
    fake = faker_instances[region]
    customers = []
    married_pairs = {}

    while len(customers) < num_records:
        # Generate a primary customer
        customer = Customer.generate_sample(region, fake)

        # If married, ensure the spouse exists
        if customer.marital_status == "Married":
            if customer.name in married_pairs:  
                # If a spouse already exists, assign their name
                customer.spouse_name = married_pairs[customer.name]
            else:
                # Generate a spouse record
                spouse_name = fake.name()
                spouse = Customer.generate_sample(region, fake, name=spouse_name, marital_status="Married", spouse_name=customer.name)
                
                # Store correct spouse mapping
                married_pairs[customer.name] = spouse_name
                married_pairs[spouse_name] = customer.name

                # Add spouse to records
                customers.append(spouse.model_dump())

                # Assign spouse name to primary customer
                customer.spouse_name = spouse_name

        customers.append(customer.model_dump())

    df = pd.DataFrame(customers)

    # Rename only required columns
    df.rename(columns={
        "customer_id": "~id",
        "created_at": "created_at:Long",
        "last_active": "last_active:Long",
        "annual_income": "annual_income:Int",
        "revenue": "revenue:Int",
        "blacklisted": "blacklisted:Boolean",
        "label": "~label"
    }, inplace=True)

    # Save to the correct directory
    csv_filename = "./dataset/vertices/customers/customer.csv"
    df.to_csv(csv_filename, index=False)
    
    print(f"CSV file '{csv_filename}' has been created successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python GenerateCustomers.py <num_records> <region>")
        sys.exit(1)
    
    num_records = int(sys.argv[1])
    region = sys.argv[2]

    generate_customer_data(num_records, region)
