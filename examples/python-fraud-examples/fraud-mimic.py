import random
import datetime
import traceback

from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import P


HOST = "localhost"
PORT = 8182


def main():
    try:
        # Create a GraphTraversalSource to remote server
        print("Connecting to Aerospike Graph Service...")
        cluster = DriverRemoteConnection("ws://{host}:{port}/gremlin".format(host=HOST, port=PORT), "g")
        g = traversal().with_remote(cluster)

        # Check if graph is connected
        if g.inject(0).next() != 0:
            print("Failed to connect to graph instance")
            exit()
        print("Connected to Aerospike Graph Service; Adding Data...")

        print("Adding some users, accounts and transactions")

        # Add Users
        user1 = g.add_v("User").property("userId", "U1").property("name", "Alice").property("age", 30).next()
        user2 = g.add_v("User").property("userId", "U2").property("name", "Bob").property("age", 35).next()
        user3 = g.add_v("User").property("userId", "U3").property("name", "Charlie").property("age", 25).next()
        user4 = g.add_v("User").property("userId", "U4").property("name", "Diana").property("age", 28).next()
        user5 = g.add_v("User").property("userId", "U5").property("name", "Eve").property("age", 32).next()

        # Add Accounts
        account1 = g.add_v("Account").property("accountId", "A1").property("balance", 5000).next()
        account2 = g.add_v("Account").property("accountId", "A2").property("balance", 3000).next()
        account3 = g.add_v("Account").property("accountId", "A3").property("balance", 4000).next()
        account4 = g.add_v("Account").property("accountId", "A4").property("balance", 2000).next()
        account5 = g.add_v("Account").property("accountId", "A5").property("balance", 6000).next()

        # Link Users to Accounts
        g.add_e("owns").from_(user1).to(account1).property("since", "2020").iterate()
        g.add_e("owns").from_(user2).to(account2).property("since", "2021").iterate()
        g.add_e("owns").from_(user3).to(account3).property("since", "2022").iterate()
        g.add_e("owns").from_(user4).to(account4).property("since", "2023").iterate()
        g.add_e("owns").from_(user5).to(account5).property("since", "2024").iterate()

        # Add Transactions
        g.add_e("Transaction") \
            .from_(account1).to(account2) \
            .property("transactionId", "T1") \
            .property("amount", 200) \
            .property("type", "debit") \
            .property("timestamp", convert_timestamp_to_long("2023-01-15")) \
            .iterate()

        g.add_e("Transaction") \
            .from_(account2).to(account1) \
            .property("transactionId", "T2") \
            .property("amount", 150) \
            .property("type", "credit") \
            .property("timestamp", convert_timestamp_to_long("2023-01-16")) \
            .iterate()

        # Add Transactions
        random.seed()
        for i in range(1, 51):
            #fix the python deprecated api calls
            #Creates list of 2 random unique accounts to create a transaction
            accounts = g.V().has_label("Account").sample(2).to_list()

            if len(accounts) < 2:
                print("Error: Not enough Account vertices to create edges")
                continue
            amount = random.randint(1, 1000)

            # Generate a random transaction ID
            transaction_id = f"T{i}"
            type_ = "debit" if random.choice([True, False]) else "credit"
            timestamp = f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            #print(f"Transaction ID: {transaction_id}, Amount: {amount}, Type: {type_}, Timestamp: {timestamp}")

            # Create the transaction edge
            g.add_e("Transaction") \
                .from_(accounts[0]).to(accounts[1]) \
                .property("transactionId", transaction_id) \
                .property("amount", amount) \
                .property("type", type_) \
                .property("timestamp", convert_timestamp_to_long(timestamp)) \
                .iterate()

        print("Data written successfully...")

        # Query Example 1: Find all transactions initiated by a specific user

        print("\nQUERY 1: Transactions initiated by Alice:")
        results =  g.V().has("User", "name", "Alice") \
            .out("owns") \
            .out_e("Transaction") \
            .as_("transaction") \
            .in_v() \
            .values("accountId") \
            .as_("receiver") \
            .select("transaction", "receiver") \
            .by("amount") \
            .by() \
            .to_list()
        for result in results:
            print(f"Transaction Amount: {result['transaction']}, Receiver Account ID: {result['receiver']}")

        # Query Example 2: Aggregate total transaction amounts for each user
        print("\nQUERY 2: Total transaction amounts initiated by users:")
        results = g.V().has_label("Account") \
            .group() \
            .by("accountId") \
            .by(__.out_e("Transaction").values("amount").sum_()) \
            .to_list()

        for result in results:
            print(result)


        print("\nQUERY 3: Users who transferred greater than 100 to Alice:")
        results = g.V().has("User", "name", "Alice") \
            .out("owns") \
            .in_e("Transaction") \
            .has("amount", P.gte(100)) \
            .out_v() \
            .in_("owns") \
            .value_map("name") \
            .to_list()

        for result in results:
            print(f"User: {result}")

        # Query Example 4: List all properties of a specific user
        print("\nQUERY 4: Properties of Bob:")

        bob_properties = g.V().has("User", "name", "Bob").value_map().next()

        # Iterate and print properties
        for key, value in bob_properties.items():
            print(f"{key}: {value[0]}")

        # Clean up
        g.V().drop().iterate()
        print("Dropping Dataset.")
        if cluster:
            try:
                print("Closing Connection...")
                cluster.close()
            except Exception as e:
                print(f"Failed to Close Connection: {e}")

    except Exception as e:
        print(f"Something went wrong {e}")
        traceback.print_exc()


def convert_timestamp_to_long(date):
    timestamp = datetime.datetime.now().timestamp()
    long_timestamp = int(timestamp)
    return long_timestamp


if __name__ == "__main__":
    main()

