# Java basic example

A minimal Java application that connects to Aerospike Graph Service (AGS), inserts sample data, and runs a few Gremlin queries.

## Prerequisites

- Java 11 or later.
- [Aerospike Graph Service](https://aerospike.com/docs/graph/deploy/docker).
- [Aerospike Database](https://aerospike.com/docs/database/install/docker/).

> **Note:** AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x are incompatible.

## Build

Build the project with Maven:

```shell
mvn clean install
```

## Run

Run the resulting JAR file:

```shell
java -jar target/ags-java-example-1.0-jar-with-dependencies.jar
```

## Expected output

```text
Connected to Aerospike Graph Service; Adding Data...
Adding some users, accounts and transactions.
Data written successfully...

QUERY 1: Transactions initiated by Alice:
Transaction Amount: 200, Receiver Account ID: A2
Transaction Amount: 722, Receiver Account ID: A1
Transaction Amount: 282, Receiver Account ID: A5
...
Dropping Dataset.
Closing Connection...
```
