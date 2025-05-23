# Bulk Loading with TLS

To bulk load a TLS enabled Aerospike cluster the 
following steps are required:
1. The x509 ca cert file (generally a .pem file) must be in a location that is available to all workers
2. A tls setup script must be in a location that is available to all workers
3. The script must be run on all workers to configure the JVM and spark.

## Example TLS Setup Script

Note you need to uncomment one of the line below (or add your own) 
to transfer the file from the remote to the local worker.

```bash
CA_CERT_REMOTE="<path>/cacert.pem"
DEST_DIR="/etc/aerospike-graph-tls"
CA_CERT=${DEST_DIR}/cacert.pem
TRUSTSTORE=${DEST_DIR}/truststore.jks

# Create directory.
mkdir -p $DEST_DIR

# Download CA certificate. Use one of the following commands.

# For local file system
# cp $CA_CERT_REMOTE $CA_CERT

# For HDFS
# hdfs dfs -copyToLocal $CA_CERT_REMOTE $CA_CERT

# For GCP
# gsutil cp $CA_CERT_REMOTE $CA_CERT

# For AWS
# aws s3 cp $CA_CERT_REMOTE $CA_CERT

# Create truststore from CA cert.
keytool -import -trustcacerts \
  -alias aerospike-ca \
  -file $CA_CERT \
  -keystore $TRUSTSTORE \
  -storepass changeit \
  -noprompt

# Secure the truststore. Note, master node can run with 400, but workers require 444.
chmod 444 $TRUSTSTORE

# Configure Spark to use the truststore.
echo "spark.driver.extraJavaOptions=-Djavax.net.ssl.trustStore=$TRUSTSTORE -Djavax.net.ssl.trustStorePassword=changeit" >> /etc/spark/conf/spark-defaults.conf
echo "spark.executor.extraJavaOptions=-Djavax.net.ssl.trustStore=$TRUSTSTORE -Djavax.net.ssl.trustStorePassword=changeit" >> /etc/spark/conf/spark-defaults.conf
```

## Bulk Loader Config Adjustments For TLS

The properties file provided to the bulk loader requires some minor 
adjustments to allow loading a tls enabled Aerospike cluster.

```
aerospike.client.host=<ip_of_aerospike_node>:<tls_name_of_cluster>:<port_for_tls_name>
aerospike.client.tls=true
```

The important piece here is that `aerospike.client.tls=true` is set to `true`, 
and the `aerospike.client.host` is set accordingly.

## Run Initialization Script on Spark Cluster

### GCP Dataproc

In GCP you must add this command:
--initialization-actions=gs://<path_to_script>

Example:
```
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
    --initialization-actions=gs://<path_to_script> \
    --project $project
```

### AWS EMR

In AWS EMR you must add this command:
--bootstrap-actions Path="s3://<path_to_script>

and this json file must be created and added to the local filesystem for each worker using the script above.
```
[
  {
    "Classification": "spark-defaults",
    "Properties": {
      "spark.driver.extraJavaOptions": "-Djavax.net.ssl.trustStore=/etc/aerospike-graph-tls/truststore.jks -Djavax.net.ssl.trustStorePassword=changeit",
      "spark.executor.extraJavaOptions": "-Djavax.net.ssl.trustStore=/etc/aerospike-graph-tls/truststore.jks -Djavax.net.ssl.trustStorePassword=changeit"
    }
  }
]
```

```
aws emr create-cluster \
    --name "My Spark TLS Cluster" \
    --release-label emr-6.13.0 \
    --applications Name=Spark \
    --instance-type m5.xlarge \
    --instance-count 3 \
    --use-default-roles \
    --ec2-attributes KeyName=your-key \
    --bootstrap-actions Path="s3://<path_to_script>" \
    --configurations file://spark-tls-config.json <--- json from above that needs to be generated via tls script above.
```

You may also require 

### On Premises

In an on prem cluster, the script may be needed to be run by hand before introducing the node to the spark cluster.

Spark does not provide a native way to do this.

In this case you may need to add the following:
```
spark-submit \
  ....
  --conf "spark.driver.extraJavaOptions=-Djavax.net.ssl.trustStore=/etc/aerospike-graph-tls/truststore.jks -Djavax.net.ssl.trustStorePassword=changeit" \
  --conf "spark.executor.extraJavaOptions=-Djavax.net.ssl.trustStore=/etc/aerospike-graph-tls/truststore.jks -Djavax.net.ssl.trustStorePassword=changeit" \
  ...
```