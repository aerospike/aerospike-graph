# ==== Aerolab ====
name="<cluster-name>" # cluster name
instance_count=1 # number of nodes
aws_instance_type="t3.medium" # same for core nodes
username="<your-username>" # the owner of the Aerolab cluster

# ==== Bulkload ====
AWS_REGION="us-east-1"

# ==== S3 Locations ====
BUCKET_PATH="s3://<bucket-name>"
LOG_URI="${BUCKET_PATH}/logs/"
SPARK_JAR="${BUCKET_PATH}/jars/aerospike-graph-bulk-loader-3.0.0.jar"
#User may add more params supported by bulkloader
SPARK_ARGS="-c,${BUCKET_PATH}/configs/bulk-loader.properties"

# ==== SPARK Job ====
SPARK_JOB_NAME="Aerospike Graph AWS Spark Job"
SPARK_CLASS="com.aerospike.firefly.bulkloader.SparkBulkLoaderMain"

# ==== EMR Cluster ====
CLUSTER_NAME="Aerospike AWS Graph Cluster"
EMR_RELEASE="emr-6.15.0"

#Switch from java8 to java 11, the minimum java version needed for Aerospike Firefly Graph.
CONFIGURATIONS='[{"Classification":"hadoop-env","Configurations":[{"Classification":"export","Configurations":[],"Properties":{"JAVA_HOME":"/usr/lib/jvm/java-11-amazon-corretto.x86_64"}}],"Properties":{}},{"Classification":"spark-env","Configurations":[{"Classification":"export","Configurations":[],"Properties":{"JAVA_HOME":"/usr/lib/jvm/java-11-amazon-corretto.x86_64"}}],"Properties":{}},{"Classification":"spark-defaults","Properties":{"spark.executorEnv.JAVA_HOME":"/usr/lib/jvm/java-11-amazon-corretto.x86_64"}}]'

#Recommend to keep the subnetid (and AWS region) same as of Aerospike cluster
#(assuming they're in the AWS as well), to have a hassle free communication between DB and Spark cluster
# When DB is created using Aerolab, it prints its subnetid
SUBNET_ID="<your-subnet>" # This will be changed after creating your Aerolab Cluster

#Aerolab also prints out the security-group associated with the server nodes. The Aerolab log looks like following
#Using security group ID sg-098adnad21 name AeroLabServer-9abh0918awe
SECURITY_GROUP="<your-security-group>" # This will be changed after creating your Aerolab Cluster

