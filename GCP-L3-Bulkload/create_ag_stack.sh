set -e # force script to fail if any step fails
source set_variables.sh # set variables from other script

# create your aerolab cluster
aerolab cluster create \
    --name "$name" \
    --count "$aerospike_count" \
    --instance "$aerospike_instance" \
    --aerospike-version "$aerospike_version" \
    --featurefile "$features_file" \
    --disk pd-ssd:20 \
    --disk local-ssd@"$aerospike_ssd_count" \
    --start n

# partition the cluster
aerolab cluster partition create \
      --name "$name" \
      --filter-type nvme \
      --partitions 24,24,24,24
aerolab cluster partition conf \
      --name "$name" \
      --namespace test \
      --filter-type nvme \
      --filter-partitions 1,2,3,4 \
      --configure device

# start aerospike on the cluster
aerolab aerospike start --name="$name"

# attach graph instance to the cluster
aerolab client create graph \
        --cluster-name "$name" \
        --group-name "$graph_name" \
        --count "$graph_count" \
        --instance "$graph_instance_type" \
        --graph-image "$graph_graph_image" \
        --disk pd-ssd:"$graph_disk_size"

# start exporter on all aerospike nodes and launch vm groups
aerolab cluster add exporter -n $name
aerolab client create ams --group-name $ams_name --clusters $name --clients $graph_name --instance 'n2d-standard-2'