# Aerolab Settings
name="aerolab-cluster-name" # cluster name
graph_name="${name}-g"
client_name="${name}-c"

# If you are loading your own data, adjust these settings to the size of your loaded data
aerospike_count=1 # number of nodes
aerospike_instance=n2d-standard-16
aerospike_version=8.0.*
aerospike_ssd_count=1  # number of drives
custom_conf="./aerospike8,rf=1.conf"
graph_count=1
graph_instance_type=n2d-highmem-32
graph_disk_size=50
graph_graph_image="aerospike/aerospike-graph-service"
client_instance_type="n2d-standard-4"
client_test_name="./tests/test"

# Dataproc settings
# Edit all these variable to match your GCP environment.
bucket_path=name-of-bucket
dataproc_name="dp-cluster-name" # change to what you want your dataproc name to be
region=us-central1
zone=us-central1-a
instance_type=n2d-standard-4
master_instance_type=n2d-standard-4
num_workers=2
project=your-gcp-project # rename to your GCP project
bulk_jar_uri="gs://${bucket_path}/jars/aerospike-graph-bulk-loader-2.6.0.jar" # rename with your bucket name
properties_file_uri="gs://${bucket_path}/configs/bulk-loader.properties" # rename with your bucket name

