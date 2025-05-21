# AWS Spark Cluster Setup

To create a spark cluster in AWS, the following can be used from command line.

```bash
emr_name="olap-spark-cluster-aws"
region=us-east-1
instance_type="m7a.2xlarge"
num_workers=20
num_cores_per_instance=$(aws ec2 describe-instance-types --instance-types "$instance_type" --query "InstanceTypes[0].VCpuInfo.DefaultVCpus" --output text --region $region)
spark_executor_cores=$((num_workers * num_cores_per_instance))
olap_jar="s3://<path>/aerospike-graph-olap-<version>.jar"
properties_file_uri="s3://<path>/aerospike-graph-olap.properties"
step_name="olap-step"
log_uri="s3://<path>/logs/"

# Recommend using 75% of memory per core, which for an 8g/core machine, is 6g
memory=6g 

# Recommend to keep the subnetid (and AWS reigon) same as of Aerospike cluster
# (assuming they're in the AWS as well), to have a hassle free communication between DB and Spark cluster
# If DB is created using aerolab, the subnetid will be printed during cluster create
subnet_id="subnet-04bc1bfb6c6ebc05b"

# Aerolab also prints out the security-group associated with the server nodes.
#   The aerolab log looks like following
#   Using security group ID sg-030a778997ce044eb name AeroLabServer-0eb2d9ae66bac4b47
security_group="sg-028ccc8c880bd48cd"

#Switch from java8 to java 11, the minimum java version needed for Aerospike Firefly Graph.
CONFIGURATIONS='[{"Classification":"hadoop-env","Configurations":[{"Classification":"export","Configurations":[],"Properties":{"JAVA_HOME":"/usr/lib/jvm/java-11-amazon-corretto.x86_64"}}],"Properties":{}},{"Classification":"spark-env","Configurations":[{"Classification":"export","Configurations":[],"Properties":{"JAVA_HOME":"/usr/lib/jvm/java-11-amazon-corretto.x86_64"}}],"Properties":{}},{"Classification":"spark-defaults","Properties":{"spark.executorEnv.JAVA_HOME":"/usr/lib/jvm/java-11-amazon-corretto.x86_64"}}]'
EMR_RELEASE="emr-6.15.0"

# Create EMR Cluster
echo "Creating EMR Cluster..."

# This command creates the cluster. If there is a cluster already running, it does not need to be run twice.

CLUSTER_ID=$(aws emr create-cluster \
    --name "$emr_name" \
    --release-label "$EMR_RELEASE" \
    --applications Name=Spark \
    --log-uri "$log_uri" \
    --use-default-roles \
    --instance-type "$instance_type" \
    --instance-count "$num_workers" \
    --ec2-attributes SubnetId="$subnet_id",EmrManagedSlaveSecurityGroup="$security_group",EmrManagedMasterSecurityGroup="$security_group" \
    --configurations "$CONFIGURATIONS" \
    --query 'ClusterId' \
    --region "$region" \
    --output text)


# This command submits the jar file to the spark cluster.
# The configurations set below seems to optimize the performance of the spark cluster well.

# Add Step to run Spark job
aws emr add-steps --cluster-id "$CLUSTER_ID" --steps '[
  {
    "Name": "'"$step_name"'",
    "ActionOnFailure": "CONTINUE",
    "Type": "Spark",
    "Args": [
        "--class", "com.aerospike.firefly.olap.DistributedGraphComputerMain", 
        "--conf", "spark.executor.memory=$memory",
        "--conf", "spark.executor.cores=1",
        "--conf", "spark.task.cpus=1",
        "--conf", "spark.executor.instances='"$spark_executor_cores"'",
        "--conf", "spark.speculation=false",
        "--conf", "spark.dynamicAllocation.enabled=true",
        "--conf", "spark.dynamicAllocation.minExecutors='"$spark_executor_cores"'",
        "--conf", "spark.dynamicAllocation.maxExecutors='"$spark_executor_cores"'",
        "--conf", "spark.dynamicAllocation.initialExecutors='"$spark_executor_cores"'",
        "--conf", "spark.scheduler.minRegisteredResourcesRatio=1.0",
        "'$olap_jar'",
        "-c", "'"$properties_file_uri"'"
      ]
    }
]' \
    --query 'StepIds[0]' \
    --output text \
    --region "$region"
```