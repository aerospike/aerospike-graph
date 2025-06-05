#!/bin/bash
source set_variables.sh

# Execute the dataproc command creating a cluster
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

# Bulkload the data
gcloud dataproc jobs submit spark \
    --class=com.aerospike.firefly.bulkloader.SparkBulkLoader \
    --jars="$bulk_jar_uri" \
    --cluster="$dataproc_name" \
    --region="$region" \
    -- -c "$properties_file_uri"