#!/bin/bash

if [ $# -lt 1 ]; then
  echo "Usage: $0 <input>"
  exit 1
fi

# Ensure that the bulk loader .jar file is correctly named and
# accessible by your CLI profile.
dataproc_name="$1"
region=us-central1
zone=us-central1-a
instance_type=n2d-highmem-8
master_instance_type=n2d-highmem-8
num_workers=64
project=firefly-aerospike
bulk_jar_uri="gs://gcp-bl-test/jars/aerospike-graph-bulk-loader-2.6.0.jar"
properties_file_uri="gs://gcp-bl-test/configs/bulk-loader.properties"

# Execute the dataproc command
gcloud dataproc clusters create "$dataproc_name" \
    --enable-component-gateway \
    --region $region \
    --zone $zone \
    --master-machine-type "$master_instance_type" \
    --master-boot-disk-type pd-ssd \
    --master-boot-disk-size 500 \
    --num-workers "$num_workers" \
    --worker-machine-type "$instance_type" \
    --worker-boot-disk-type pd-ssd \
    --worker-boot-disk-size 500 \
    --image-version 2.1-debian11 \
    --properties spark:spark.history.fs.gs.outputstream.type=FLUSHABLE_COMPOSITE \
    --project $project

echo "Starting Spark Worker Job"
gcloud dataproc jobs submit spark \
    --class=com.aerospike.firefly.bulkloader.SparkBulkLoader \
    --jars="$bulk_jar_uri" \
    --cluster="$dataproc_name" \
    --region="$region" \
    -- -c "$properties_file_uri"