# Tinker Bench Multi-Node Aerospike Cluster with AGS Instances in Aerolab

# Configure Aerolab
https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md#prerequisites

# Create Clusters
The following script will:
1. Set environment variables for Aerospike cluster configuration
2. Create a 3-Node Aerospike cluster on GCP using Aerolab
3. Configure NVMe device partitions for the cluster
4. Adjust a namespace parameter for tuning
5. Start the Aerospike cluster
6. Create and attach Graph Instances
7. Print the URLs of the Graph Instances

```bash
./deploy_aerospike_gcp.sh
```

# Connect TinkerBench to Run Benchmarks
Setup hosts in the `benchmark.yaml` file
The hosts will be in the last 3 lines output from the last steps command

```bash
git clone https://github.com/aerospike-community/tinkerbench.git
cd tinkerbench
mvn clean install
```

Edit ./conf/simple.properties to add in the host you want to test
Run the tinkerbench simple via:
```bash
./scripts/run_simple.sh
```