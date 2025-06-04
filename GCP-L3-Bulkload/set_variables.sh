# Aerolab Settings
name="name-of-bucket" # cluster name
graph_name="name-of-bucket-g"
client_name="name-of-bucket-c"

# If you are loading your own data, adjust these settings to the size of your loaded data
aerospike_count=1 # number of nodes
aerospike_instance=n2d-standard-16
aerospike_version=7.0.*
aerospike_ssd_count=1  # number of drives
custom_conf="./aerospike7,rf=1.conf"
graph_count=1
graph_instance_type=n2d-highmem-32
graph_disk_size=50
graph_graph_image="aerospike/aerospike-graph-service"
client_instance_type="n2d-standard-4"
client_test_name="./tests/test"

# Dataproc settings
# Edit all these variable to match your GCP environment.
# Ensure that the bulk loader .jar file is correctly named and
# accessible by your CLI profile.
dataproc_name="cluster-name"
region=us-central1
zone=us-central1-a
instance_type=n2d-standard-4
master_instance_type=n2d-standard-4
num_workers=1
project=firefly-aerospike
bulk_jar_uri="gs://name-of-bucket/aerospike-graph-bulk-loader-2.6.0.jar"
properties_file_uri="gs://name-of-bucket/bulk-loader.properties"