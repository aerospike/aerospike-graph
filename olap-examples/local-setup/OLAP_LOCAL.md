# Local Spark Cluster Setup

If you have a local spark cluster running, 
you can use the following command to submit the jar file to spark:

```bash
num_cores_per_instance=<number of cores per instance>
num_instances=<number of instances>
spark_executor_cores=$((num_cores_per_instance * num_instances))
olap_jar=<path>/aerospike-graph-olap-<version>.jar
properties_file=<path>/aerospike-graph-olap.properties

# Recommend using 75% of memory per core, which for an 8g/core machine, is 6g
memory=6g 

# This command submits the jar file to the spark cluster.
spark-submit \
    --conf spark.worker.cleanup.enabled=true \
    --conf spark.executor.memory=$memory \
    --conf spark.executor.cores=1 \
    --conf spark.task.cpus=1 \
    --conf spark.executor.instances='"$spark_executor_cores"' \
    --conf spark.speculation=false \
    --conf spark.dynamicAllocation.enabled=true \
    --conf spark.dynamicAllocation.minExecutors='"$spark_executor_cores"' \
    --conf spark.dynamicAllocation.maxExecutors='"$spark_executor_cores"' \
    --conf spark.dynamicAllocation.initialExecutors='"$spark_executor_cores"' \
    --conf spark.scheduler.minRegisteredResourcesRatio=1.0 \
    --class com.aerospike.firefly.olap.DistributedGraphComputerMain \
    "$olap_jar" \
    -c "$properties_file"
```