source set_variables.sh # set variables from other script

echo
echo "Creating Cluster"
aerolab cluster create --name "$name" \
    --count "$instance_count" \
    --instance-type "$aws_instance_type" \
    --owner "$username" \
    --start n \

echo
echo "Starting Cluster"
aerolab aerospike start --name="$name"
