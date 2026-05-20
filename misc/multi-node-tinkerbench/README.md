# TinkerBench multi-node Aerospike cluster with AGS instances on Aerolab

This example shows how to create a multi-node Aerospike Database cluster on GCP using Aerolab, attach an Aerospike Graph Service (AGS) instance to each Aerospike node, and run TinkerBench on a dedicated benchmark VM.

> **Note:** This example uses Aerolab to create an Aerospike Database Enterprise Edition cluster, which requires an enterprise feature-key file. To get a free 60-day trial feature-key file, see the [Aerospike Enterprise trial page](https://aerospike.com/get-started-aerospike-database/).
>
> As of AGS 3.2.2, AGS itself no longer requires the `graph-service` feature to be enabled in the feature-key file. The feature-key file is still required for Aerospike Database Enterprise Edition.

## Configure Aerolab for GCP

Follow the [Aerolab GCP setup prerequisites](https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md#prerequisites).

## Create clusters

First, configure `deploy_aerospike_gcp.sh` for your environment. To make the benchmark run faster, scale the bench VM to a more powerful machine type.

The deployment script:

1. Sets environment variables for the Aerospike cluster configuration.
2. Creates a 3-node Aerospike cluster on GCP using Aerolab.
3. Configures NVMe device partitions for the cluster.
4. Adjusts a namespace parameter for tuning.
5. Starts the Aerospike cluster.
6. Creates and attaches AGS instances.
7. Creates a separate dedicated VM for running TinkerBench.
8. Prints the URLs of the AGS instances.

Run the script:

```bash
./deploy_aerospike_gcp.sh
```

The script also outputs the `host:port` for your clusters.

## SSH into the dedicated benchmark VM

The benchmark VM is named `${bench_group}-1`. SSH into it:

```bash
aerolab attach client /n <BENCH_GROUP> -- bash
```

## Connect TinkerBench and run the benchmarks

```bash
git clone https://github.com/aerospike-community/tinkerbench.git
```

Edit `./conf/simple.properties` to add the host you want to test. Run the simple TinkerBench benchmark:

```bash
cd tinkerbench
sudo apt update
sudo apt install -y maven
mvn clean install
./scripts/run_simple.sh
```

## Failure modes

This example creates a 3-node Aerospike cluster with one AGS instance per node. If a node fails during the benchmark, the cluster continues to serve traffic at reduced capacity until migrations complete. Replication factor and migration behavior affect benchmark results during a node failure; for steady-state benchmarks, ensure all nodes are healthy and migrations are complete before starting.
