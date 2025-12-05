# GCP Spark Cluster Setup

To create a spark cluster in GCP, the following can be used from command line.

```bash
dataproc_name="example-spark-cluster-gcp"
region=us-central1
zone=us-central1-a
instance_type=n2d-highmem-8
num_workers=20
num_cores_per_instance=$(echo "$instance_type" | grep -o '[0-9]\+$')
spark_executor_cores=$((num_workers * num_cores_per_instance))
project=example-project
olap_jar="gs://<path>/aerospike-graph-olap-<version>.jar"
properties_file_uri="gs://<path>/aerospike-graph-olap.properties"

# Recommend using 75% of memory per core, which for an 8g/core machine, is 6g
memory=6g 

# This command creates the cluster. If there is a cluster already running, it does not need to be run twice.
gcloud dataproc clusters create "$dataproc_name" \
    --enable-component-gateway \
    --region $region \
    --zone $zone \
    --master-machine-type "$instance_type" \
    --master-boot-disk-type pd-ssd \
    --master-boot-disk-size 500 \
    --num-workers "$num_workers" \
    --worker-machine-type "$instance_type" \
    --worker-boot-disk-type pd-ssd \
    --worker-boot-disk-size 500 \
    --image-version 2.1-debian11 \
    --properties spark:spark.history.fs.gs.outputstream.type=FLUSHABLE_COMPOSITE \
    --project $project

# This command submits the jar file to the spark cluster.
# The configurations set below seems to optimize the performance of the spark cluster well.
gcloud dataproc jobs submit spark \
    --class=com.aerospike.firefly.olap.DistributedGraphComputerMain \
    --jars="$olap_jar" \
    --cluster="$dataproc_name" \
    --region="$region" \
    --properties=\
spark.executor.memory=$memory,\
spark.executor.cores=1,\
spark.task.cpus=1,\
spark.executor.instances=$spark_executor_cores,\
spark.speculation=false,\
spark.dynamicAllocation.enabled=true,\
spark.dynamicAllocation.minExecutors=$spark_executor_cores,\
spark.dynamicAllocation.maxExecutors=$spark_executor_cores,\
spark.dynamicAllocation.initialExecutors=$spark_executor_cores,\
spark.scheduler.minRegisteredResourcesRatio=1.0,\
    -- -c "$properties_file_uri"
```