import os
import pandas as pd
from pydantic import BaseModel, Field
from faker import Faker
import random
import sys

# Initialize Faker instance
fake = Faker()

device_types = ["desktop", "mobile"]
device_os_mapping = {
    "desktop": ["windows"],
    "mobile": ["ios", "android"]
}

class Device(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    type: str = Field(..., description="Type of device (desktop, mobile)")
    os: str = Field(..., description="Operating system of the device")

    @classmethod
    def generate(cls):
        device_type = random.choice(device_types)
        os_type = random.choice(device_os_mapping[device_type])
        return cls(
            device_id=fake.uuid4(),
            type=device_type,
            os=os_type
        )

def generate_devices():
    os.makedirs("./dataset/vertices/devices", exist_ok=True)
    os.makedirs("./dataset/edges/rel-customer-device", exist_ok=True)
    
    # Read customer and address data
    customer_df = pd.read_csv("./dataset/vertices/customers/customer.csv")
    rel_customer_address_df = pd.read_csv("./dataset/edges/rel-customer-address/rel-customer-address.csv")
    rel_customer_mobile_df = pd.read_csv("./dataset/edges/rel-customer-mobile/rel-customer-mobile.csv")
    
    # Group customers by address
    rel_customer_address = rel_customer_address_df.groupby("~to")["~from"].apply(list).to_dict()
    irregular_addresses = {addr: customers for addr, customers in rel_customer_address.items() if len(customers) > 2}
    
    customer_device_relations = []
    device_records = []
    
    # Assign devices for irregular addresses
    for addr, customers in irregular_addresses.items():
        num_devices = max(1, len(customers) // 2)
        assigned_devices = [Device.generate().model_dump() for _ in range(num_devices)]
        device_records.extend(assigned_devices)
        for customer in customers:
            for device in assigned_devices:
                customer_device_relations.append({"~from": customer, "~to": device["device_id"], "~label": "known_device"})
    
    # Assign up to 3 customers to the same device for 5% of total customers
    total_customers = len(customer_df)
    shared_device_customers = random.sample(customer_df["~id"].tolist(), int(0.05 * total_customers))
    for i in range(0, len(shared_device_customers), 3):
        shared_device = Device.generate().model_dump()
        device_records.append(shared_device)
        for customer in shared_device_customers[i:i+3]:
            customer_device_relations.append({"~from": customer, "~to": shared_device["device_id"], "~label": "known_device"})
    
    # Assign devices based on mobile ownership
    customer_mobile_counts = rel_customer_mobile_df["~from"].value_counts().to_dict()
    for customer, count in customer_mobile_counts.items():
        num_devices = count if count > 1 else 1
        if count == 1 and random.random() < 0.1:
            num_devices = 2
        assigned_devices = [Device.generate().model_dump() for _ in range(num_devices)]
        device_records.extend(assigned_devices)
        for device in assigned_devices:
            customer_device_relations.append({"~from": customer, "~to": device["device_id"], "~label": "known_device"})
    
    df = pd.DataFrame(device_records)
    df.rename(columns={
        "device_id": "~id",
        "type": "type",
        "os": "os",
    }, inplace=True)
    df["~label"] = "Device"
    df.to_csv("./dataset/vertices/devices/device.csv", index=False)
    
    rel_df = pd.DataFrame(customer_device_relations)
    rel_df.to_csv("./dataset/edges/rel-customer-device/rel-customer-device.csv", index=False)
    
    print("Generated device.csv and rel-customer-device.csv successfully.")

if __name__ == "__main__":
    generate_devices()
