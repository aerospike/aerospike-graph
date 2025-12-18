set -a
name="ags-aerospike" # cluster name

aerospike_count=2
aerospike_instance=n2d-standard-4
aerospike_version=8.0.*
aerospike_ssd_count=2
features_file="./features.conf"  # Aerospike license file (not included - obtain from Aerospike)
custom_conf="./aerospike-rf2.conf"
