set -e # force script to fail if any step fails
source set_variables.sh # set variables from other script

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