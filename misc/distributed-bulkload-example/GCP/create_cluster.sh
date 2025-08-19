source set_variables.sh # set variables from other script

echo
echo "Creating Cluster"
aerolab cluster create --name "$name" \
    --count "$aerospike_count" \
    --aerospike-version "$aerospike_version" \
    --instance "$aerospike_instance" \
    --zone "$zone" \
    --start n \

echo
echo "Starting Cluster"
aerolab aerospike start --name="$name"
