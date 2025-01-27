# Aerospike Graph Fraud Detection Scenarios

This guide helps you set up Aerospike Graph, bulk load data, and run various scenarios for real-time fraud detection using Gremlin queries.

---

## 1. Setting Up Aerospike Graph

Follow these steps to set up Aerospike Graph:

1. **Run Docker Compose**:
   - Navigate to the root level of the repository and start the Aerospike Graph services using Docker Compose:
     ```bash
     docker compose up -d
     ```
   - This will start the Aerospike Database and Aerospike Graph Service in detached mode.

2. **Verify Services**:
   - Check if the services are running:
     ```bash
     docker ps
     ```
   - Confirm that both the Aerospike Database and Aerospike Graph Service containers are running without errors.

3. **Connect to Aerospike Graph using GdotV**:
   (Optional) Import the customized Graph stylesheet in Gdotv `UPIGraphGdotvStylesheet.json`
   
---

## 2. Bulk Load Data

To load data into Aerospike Graph, use the following Gremlin query:

```groovy
g.with("evaluationTimeout", 100000)
 .call("aerospike.graphloader.admin.bulk-load.load")
 .with("aerospike.graphloader.vertices", "/data/upi_demo/dataset/vertices")
 .with("aerospike.graphloader.edges", "/data/upi_demo/dataset/edges")
```

## 3. Run sample Queries

Run the sample queries in `queries.md`  
