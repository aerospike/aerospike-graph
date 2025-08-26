# ==== Aerolab Settings ====
name="<cluster-name>" # cluster name
aerospike_version=8.0.0.7

# If you are loading your own data, adjust these settings to the size of your loaded data
aerospike_count=1 # number of nodes
aerospike_instance="e2‑medium"

# ==== Global ====
region="us-central1"
zone="us-central1-a"

# ==== Dataproc ====
dataproc_name="<dp-cluster-name>" # change to what you want your dataproc name to be
project="<gcp-project-name>" # rename with your gcp project name
num_workers=1
instance_type="n2d-standard-4"
master_instance="n2d-standard-4"

# ==== GS Bucket Locations ====
bucket_path="gs://<bucket-name>" # rename with your bucket name
bulk_jar_uri="${bucket_path}/jars/aerospike-graph-bulk-loader-3.0.0.jar"
properties_file_uri="${bucket_path}/config/bulk-loader.properties"


