## Java application example

### Prerequisites

- Java 11+
- [Aerospike Graph Service](https://aerospike.com/docs/graph/install/docker/)
- [Aerospike Database](https://aerospike.com/docs/database/install/docker/)

Navigate to the `java-example` directory and run the following
shell commands:

```
mvn clean install -q
java -jar target/ags-java-example-1.0-jar-with-dependencies.jar
```

Example output:

```
Connected to Aerospike Graph Service; Adding Data...
Adding some users, accounts and transactions.
Data written successfully...

QUERY 1: Transactions initiated by Alice:
Transaction Amount: 200, Receiver Account ID: A2
Transaction Amount: 722, Receiver Account ID: A1
Transaction Amount: 282, Receiver Account ID: A5
...
...
...
Dropping Dataset. 
Closing Connection...

```
