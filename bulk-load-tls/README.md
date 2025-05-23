# Bulk Loading with TLS

To bulk load a TLS enabled Aerospike cluster the 
following steps are required:
1. The x509 ca cert file (generally a .pem file) must be in a location that is available to all workers
2. A tls setup script must be in a location that is available to all workers

## Example TLS Setup Script

```bash
CA_CERT_REMOTE="<path>/cacert.pem"
DEST_DIR="/etc/aerospike-graph-tls"
CA_CERT=${DEST_DIR}/cacert.pem
TRUSTSTORE=${DEST_DIR}/truststore.jks

# Create directory.
mkdir -p $DEST_DIR

# Download CA certificate from remote location to local.
gsutil cp $CA_CERT_REMOTE $CA_CERT

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