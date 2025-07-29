# Aerolab Settings
name="<cluster-name>" # cluster name

# If you are loading your own data, adjust these settings to the size of your loaded data
aerospike_count=1 # number of nodes
aerospike_instance=n2d-standard-16
aerospike_version=8.0.0.7

# Dataproc settings
# Edit all these variable to match your GCP environment.
bucket_path="<bucket-name>"
dataproc_name="<dp-cluster-name>" # change to what you want your dataproc name to be
region=us-central1
zone=us-central1-a
instance_type=n2d-standard-4
master_instance_type=n2d-standard-4
num_workers=2
bulk_jar_uri="gs://${bucket_path}/jars/aerospike-graph-bulk-loader-3.0.0.jar" # rename with your bucket name
properties_file_uri="gs://${bucket_path}/configs/bulk-loader.properties" # rename with your bucket name
project=<gcp-project-name> # rename with your gcp project name

