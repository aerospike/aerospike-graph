# Aerospike Graph fraud-detection scenarios

This guide helps you set up Aerospike Graph Service (AGS), bulk-load data, and run various scenarios for real-time fraud detection using Gremlin queries.

## 1. Set up AGS

1. Run Docker Compose. Navigate to the root of the repository and start AGS using Docker Compose:

   ```shell
   docker compose up -d
   ```

   This starts Aerospike Database and AGS in detached mode.

2. Verify the services. Check that the services are running:

   ```shell
   docker ps
   ```

   Confirm that both the Aerospike Database and AGS containers are running without errors.

3. (Optional) Connect to AGS using GdotV. Import the customized graph stylesheet `UPIGraphGdotvStylesheet.json` into GdotV.

## 2. Bulk-load the data

To load data into AGS, set the graph traversal source using the [Gremlin Console](https://aerospike.com/docs/graph/quick-start#install-the-gremlin-console) (see the [official Quickstart](https://aerospike.com/docs/graph/quick-start) for setup steps):

```groovy
g = traversal().withRemote(DriverRemoteConnection.using("localhost", 8182, "g"))
```

Run the following Gremlin query:

```groovy
g.with("evaluationTimeout", 100000)
 .call("aerospike.graphloader.admin.bulk-load.load")
 .with("aerospike.graphloader.vertices", "/data/upi-demo/dataset/vertices")
 .with("aerospike.graphloader.edges", "/data/upi-demo/dataset/edges")
```

To check the status of the bulk loader:

```groovy
g.call("aerospike.graphloader.admin.bulk-load.status")
```

## 3. Run sample queries

Run the sample queries in [`queries.md`](queries.md).
