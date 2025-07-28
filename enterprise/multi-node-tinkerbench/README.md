# Tinker Bench Multi-Node Aerospike Cluster with AGS Instances in Aerolab

# Configure Aerolab for GCP
https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md#prerequisites

# Create Clusters
First configure the `deploy_aerospike_gcp.sh` file to your specifications
If you want the benchmark to run faster, scale the beench VM to a more powerful machine

The following script will:
1. Set environment variables for Aerospike cluster configuration
2. Create a 3-Node Aerospike cluster on GCP using Aerolab
3. Configure NVMe device partitions for the cluster
4. Adjust a namespace parameter for tuning
5. Start the Aerospike cluster
6. Create and attach Graph Instances
7. Create a separate dedicated VM for running TinkerBench
8. Print the URLs of the Graph Instances
9. Print the Benchmark VMs IP

```bash
./deploy_aerospike_gcp.sh
```
This will also output the IP `Host:Port` for your clusters

# SSH into the Dedicated Benchmark VM
The VM should be named `bench_group-1`
SSH into it using
```bash
aerolab attach client /n connor-multi-bench -- bash
```

# Connect TinkerBench to Run Benchmarks
```bash
git clone https://github.com/aerospike-community/tinkerbench.git
```

Edit ./conf/simple.properties to add in the host you want to test
Run the tinkerbench simple via:
```bash
cd tinkerbench
sudo apt update
apt install maven
mvn clean install
./scripts/run_simple.sh
```