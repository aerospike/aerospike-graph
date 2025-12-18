set -e #force script to fail if any step fails
source ./set_variables.sh

aerolab cluster create \
    --name "$name" \
    --count "$aerospike_count" \
    --instance "$aerospike_instance" \
    --aerospike-version "$aerospike_version" \
    --featurefile "$features_file" \
    --customconf "$custom_conf" \
    --disk pd-ssd:20 \
    --disk local-ssd@"$aerospike_ssd_count" \
    --start n

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

#aerolab conf adjust -n "$name" set "namespace test.single-query-threads" 2

################For All Flash #############
#aerolab cluster partition create --name="$name" --filter-type=nvme -p 10,10,39,39
## Create a filesystem on partitions 1-2
#aerolab cluster partition mkfs --name="$name" --filter-type=nvme --filter-partitions=1,2 --fs-type=xfs --mount-options=noatime
### Update configuration to use all-flash for 1,2 partitions for pi and si
#aerolab cluster partition conf --name="$name" --namespace=test --filter-type=nvme --filter-partitions=1 --configure=pi-flash
#aerolab cluster partition conf --name="$name" --namespace=test --filter-type=nvme --filter-partitions=2 --configure=si-flash
### Update configuration to use devices for 2 partitions
#aerolab cluster partition conf --name="$name" --namespace=test --filter-type=nvme --filter-partitions=3,4 --configure=device

aerolab aerospike start --name="$name"