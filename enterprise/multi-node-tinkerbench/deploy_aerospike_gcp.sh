#!/bin/bash
set -a  # Export all variables automatically

# ==== Naming ====
name="my-cluster" # cluster name
graph_name="my-cluster-g"
bench_group="my-cluster-bench"
namespace="test"

# ==== Graph ====
graph_instance=n2d-standard-16
graph_graph_image="aerospike/aerospike-graph-service:latest"
graph_disk_size=50

# ==== Bench VM ====
bench_instance=n2d-standard-16
bench_disk_size=50

# ==== Aerospike DB ====
aerospike_instance=n2d-standard-16
aerospike_version=8.0.*
aerospike_ssd_count=4
features_file="./features.conf"
custom_conf="./aerospike.conf"

# ==== AEROLAB CLUSTER CREATE ====
aerolab cluster create \
    --name "$name" \
    --count 3 \
    --instance "$aerospike_instance" \
    --aerospike-version "$aerospike_version" \
    --featurefile "$features_file" \
    --customconf "$custom_conf" \
    --disk pd-ssd:20 \
    --disk local-ssd@"$aerospike_ssd_count" \
    --start n

# ==== PARTITION CONFIGURATION ====
aerolab cluster partition create \
    --name "$name" \
    --filter-type nvme \
    --partitions 24,24,24,24

aerolab cluster partition conf \
    --name "$name" \
    --namespace "$namespace" \
    --filter-type nvme \
    --filter-partitions 1,2,3,4 \
    --configure device

# ==== CONFIGURATION TWEAK ====
aerolab conf adjust -n "$name" set "namespace test.single-query-threads" 2

# ==== START AEROSPIKE ====
aerolab aerospike start --name="$name"
echo "Aerospike cluster '$name' setup complete."

# ==== Attach and Start AGS Instances ====
echo "Creating Aerospike Graph Instances"
aerolab client create graph \
        --cluster-name "$name" \
        --group-name "$graph_name" \
        --count 3 \
        --namespace "$namespace" \
        --instance "$graph_instance" \
        --graph-image "$graph_graph_image" \
        --disk pd-ssd:"$graph_disk_size"
echo "Graph Instances Created"

# Create dedicated VM for benchmarking ====
echo "Creating Benchmark VM"
aerolab client create base \
    --group-name "$bench_group" \
    --count 1 \
    --instance "$bench_instance" \
    --disk pd-ssd:"$bench_disk_size"
echo "→ Benchmark VM group '$bench_group' created."

echo
echo "Hosts for AGS Instances: "
aerolab client list   | grep -A1 connor-multi   | grep -o 'gremlin[^ ]*' | sed 's|gremlin://||'

echo
echo "Benchmark VM IP:"
aerolab client list /owner:"$name" | grep "$bench_group" | awk '{print $1}'