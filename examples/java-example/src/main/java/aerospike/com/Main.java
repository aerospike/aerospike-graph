package aerospike.com;
import org.apache.tinkerpop.gremlin.structure.Vertex;
import org.apache.tinkerpop.gremlin.structure.Edge;
import org.apache.tinkerpop.gremlin.driver.Cluster;
import org.apache.tinkerpop.gremlin.driver.remote.DriverRemoteConnection;
import org.apache.tinkerpop.gremlin.process.traversal.dsl.graph.GraphTraversalSource;
import org.apache.tinkerpop.gremlin.process.traversal.dsl.graph.__;

import static org.apache.tinkerpop.gremlin.process.traversal.AnonymousTraversalSource.traversal;
import org.apache.tinkerpop.gremlin.process.traversal.P;


import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Random;


public class Main {
    // Define the host and port for connecting to the Aerospike Graph service
    private static final String HOST = "localhost";
    private static final int PORT = 8182;

    // Build the Cluster object with connection details
    private static final Cluster.Builder BUILDER = Cluster.build()
            .addContactPoint(HOST)  // Add the contact point (host)
            .port(PORT)             // Specify the port
            .enableSsl(false);      // Disable SSL for this example (use true in production if needed)

    public static void main(String[] args) {
        // Create a Cluster object for connecting to the graph database
        final Cluster cluster = BUILDER.create();
        // Initialize a GraphTraversalSource to interact with the graph
        final GraphTraversalSource g = traversal().withRemote(DriverRemoteConnection.using(cluster));
        
        System.out.println("Connected to Aerospike Graph Service; Adding Data...");

        // Add users, accounts, and transactions
        System.out.println("Adding some users, accounts and transactions");

        // Add Users
        Vertex user1 = g.addV("User").property("userId", "U1").property("name", "Alice").property("age", 30).next();
        Vertex user2 = g.addV("User").property("userId", "U2").property("name", "Bob").property("age", 35).next();
        Vertex user3 = g.addV("User").property("userId", "U3").property("name", "Charlie").property("age", 25).next();
        Vertex user4 = g.addV("User").property("userId", "U4").property("name", "Diana").property("age", 28).next();
        Vertex user5 = g.addV("User").property("userId", "U5").property("name", "Eve").property("age", 32).next();

        // Add Accounts
        Vertex account1 = g.addV("Account").property("accountId", "A1").property("balance", 5000).next();
        Vertex account2 = g.addV("Account").property("accountId", "A2").property("balance", 3000).next();
        Vertex account3 = g.addV("Account").property("accountId", "A3").property("balance", 4000).next();
        Vertex account4 = g.addV("Account").property("accountId", "A4").property("balance", 2000).next();
        Vertex account5 = g.addV("Account").property("accountId", "A5").property("balance", 6000).next();

        // Link Users to Accounts
        g.addE("owns").from(user1).to(account1).property("since", "2020").iterate();
        g.addE("owns").from(user2).to(account2).property("since", "2021").iterate();
        g.addE("owns").from(user3).to(account3).property("since", "2022").iterate();
        g.addE("owns").from(user4).to(account4).property("since", "2023").iterate();
        g.addE("owns").from(user5).to(account5).property("since", "2024").iterate();

        // Add Transactions
        g.addE("Transaction")
                .from(account1).to(account2)
                .property("transactionId", "T1")
                .property("amount", 200)
                .property("type", "debit")
                .property("timestamp", convertTimestampToLong("2023-01-15"))
                .iterate();

        g.addE("Transaction")
                .from(account2).to(account1)
                .property("transactionId", "T2")
                .property("amount", 150)
                .property("type", "credit")
                .property("timestamp", convertTimestampToLong("2023-01-16"))
                .iterate();

        // Add Transactions
        Random random = new Random();
        for (int i = 1; i <= 50; i++) {
            Vertex fromAccount = g.V().hasLabel("Account").sample(1).next();
            Vertex toAccount = g.V().hasLabel("Account").sample(1).next();
            int amount = random.nextInt(1000) + 1; // Random amount between 1 and 1000
            String transactionId = "T" + i;
            String type = random.nextBoolean() ? "debit" : "credit";
            String timestamp = String.format("2025-%02d-%02d", random.nextInt(11) + 1,random.nextInt(28) + 1); // Random date in January 2025

            g.addE("Transaction")
                    .from(fromAccount).to(toAccount)
                    .property("transactionId", transactionId)
                    .property("amount", amount)
                    .property("type", type)
                    .property("timestamp", convertTimestampToLong(timestamp))
                    .iterate();
        }
        System.out.println("Data written successfully...");

        // Query Example 1: Find all transactions initiated by a specific user
        System.out.println("\nQUERY 1: Transactions initiated by Alice:");
        g.V().has("User", "name", "Alice")
                .out("owns")
                .outE("Transaction")
                .as("transaction")
                .inV()
                .values("accountId")
                .as("receiver")
                .select("transaction", "receiver")
                .by("amount")
                .by()
                .forEachRemaining(result -> {
                    System.out.println("Transaction Amount: " + result.get("transaction") + ", Receiver Account ID: " + result.get("receiver"));
                });
        // Query Example 2: Aggregate total transaction amounts for each user
        System.out.println("\nQUERY 2: Total transaction amounts initiated by users:");
        g.V().hasLabel("Account")
                .group()
                .by("accountId")
                .by(
                        __.outE("Transaction")
                                .values("amount")
                                .sum()
                )
                .forEachRemaining(System.out::println);
        System.out.println("\nQUERY 3: Users who transferred greater than 100 to Alice:");
        g.V().has("User", "name", "Alice")
                .out("owns")
                .inE("Transaction")
                .has("amount", P.gte(100))
                .outV()
                .in("owns")
                .valueMap("name")
                .forEachRemaining(result -> {
                    System.out.println("User: " + result);
                });

        // Query Example 4: List all properties of a specific user
        System.out.println("\nQUERY 4: Properties of Bob:");
        Vertex bob = g.V().has("User", "name", "Bob").next();
        bob.properties().forEachRemaining(property -> {
            System.out.println(property.key() + " : " + property.value());
        });


        // Clean up
        g.V().drop().iterate();
        System.out.print("Dropping Dataset.");
        try {
            System.out.println("Closing Connection...");
            cluster.close();
        } catch (Exception e) {
            System.err.println("Failed to Close Connection: " + e);
        }
    }

    /**
     * Converts a date string (e.g., "2023-01-15") into a long representing epoch milliseconds.
     * @param date The date string in "yyyy-MM-dd" format.
     * @return The epoch timestamp in milliseconds as a long.
     */
    private static long convertTimestampToLong(String date) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        // Parse the date string to LocalDate
        LocalDate localDate = LocalDate.parse(date, formatter);
        // Convert LocalDate to epoch milliseconds
        return localDate.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
    }
}
