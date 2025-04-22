import subprocess
from pathlib import Path
import shutil

def delete_subdirs(parent_dir):
    if Path(parent_dir).is_dir(): 
        for subdir in Path(parent_dir).iterdir():
            if subdir.is_dir():
                shutil.rmtree(subdir)

def region_map(number):
    case_mapping = {1: "asian", 2: "indian", 3: "european", 4: "israel", 5: "american"}
    return case_mapping.get(number, "Unknown")

def main():
    print("Starting dataset generation...")

    num_records = input("Enter the number of customer records to generate: ")
    region_num = input("Enter the choice(#) of region/locale (1: Asian, 2: Indian, 3: European, 4: Israel, 5: American): ").lower()

    valid_regions = ["1", "2", "3", "4", "5"]
    if region_num not in valid_regions:
        print("Invalid region selected. Please choose from:", ", ".join(valid_regions))
        return
    else:
        region = region_map(int(region_num))
        print('Main: ',region) 
    
    try:
        num_records = int(num_records)
    except ValueError:
        print("Invalid number of records. Please enter a valid integer.")
        return

    print(f"Generating {num_records} customer records for the {region} region...")
    delete_subdirs("./dataset/vertices/")
    delete_subdirs("./dataset/edges/")
    # Generate Customers
    subprocess.run(["python3", "./Scripts/GenerateCustomers.py", str(num_records), region], check=True)

    # Generate Addresses
    print(f"Generating address records for the {region} region...")
    subprocess.run(["python3", "./Scripts/GenerateAddresses.py", region], check=True)

    # Generate Mobiles
    print(f"Generating mobile records for the {region} region...")
    subprocess.run(["python3", "./Scripts/GenerateMobiles.py", region], check=True)

    # Generate Bank Accounts
    print(f"Generating bank account records for the {region} region...")
    subprocess.run(["python3", "./Scripts/GenerateBankAccounts.py", region], check=True)

     # Generate National_Ids
    print(f"Generating National_Id records for the {region} region...")
    subprocess.run(["python3", "./Scripts/GenerateNationalIds.py", region], check=True)

     # Generate Tax_Ids
    print(f"Generating Tax_Id records for the {region} region...")
    subprocess.run(["python3", "./Scripts/GeneratePANs.py", region], check=True)

    print(f"Generating Device records...")
    subprocess.run(["python3", "./Scripts/GenerateDevices.py"], check=True)

    print(f"Generating Transactions...")
    subprocess.run(["python3", "./Scripts/GenerateTransactions.py", region], check=True)

    print("Dataset generation completed successfully.")

if __name__ == "__main__":
    main()
