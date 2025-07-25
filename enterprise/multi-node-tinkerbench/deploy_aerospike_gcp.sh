#!/bin/bash
set -a  # Export all variables automatically

# ==== CONFIGURATION ====
name="connor-multi" # cluster name
graph_name="connor-multi-g"
#client_name="<client-name>"
namespace="test"

graph_instance=n2d-standard-16
graph_graph_image="aerospike/aerospike-graph-service:latest"
graph_disk_size=50

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

echo "Hosts for AGS Instances: "
aerolab client list   | grep -A1 connor-multi   | grep -o 'gremlin[^ ]*' | sed -E 's|.*://([^:/]+):.*|\1|'
