# GCP L3 Bulkload Example

Configure Aerolab for GCP following this guide: https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md

Now create your cluster
```bash
aerolab cluster create -n aerolab-cluster-name -c 3 --instance e2-medium --zone us-central1-a --disk pd-balanced:20 --disk pd-ssd:40 --disk pd-ssd:40 --start n
```

You now have a cluster called aerolab-cluster-name
Find its IP using
```bash
aerolab cluster list
```
Make a buckit in gcp for the data: gsutil mb gs://name-of-bucket

Download bulk loader jar from here:
https://aerospike.com/download/graph/loader/

To ```bucket-files/jars```

Edit the properties file in ```bucket-files/jars``` and edit the following variables:
```
aerospike.client.host=<cluster-host> #Set to the IP found earlier 
aerospike.graphloader.vertices=gs://name-of-bucket/vertices/ #Set <name-of-bucket> to the name of your created bucket
aerospike.graphloader.edges=   gs://name-of-bucket/edges/
aerospike.graphloader.temp-directory=gs://name-of-bucket/temp/
aerospike.graphloader.remote-user=<private_key_id> # Change these to your GCP Credentials
aerospike.graphloader.remote-passkey=<private_key>
aerospike.graphloader.gcs-email=<client_email>
```

Now upload the files to the bucket
```bash
gsutil cp -r ./bucket-files/* gs://name-of-bucket
```

Now edit the ```set_variables.sh``` script and change values of the variables
There are explanatory comments in it to help.

Once the variables are set, run 
```bash
./create_ag_stack.sh
```

Now to create a dataproc cluster and submit the bulkload job run
```bash
./bulkload.sh
```

When it has succeeded, you should see output similar to this:
```
INFO EdgeOperations: Execution time in seconds for Edge write task: 2
INFO ProgressBar:
        Bulk Loader Progress:
                Preflight check complete
                Temp data writing complete
                Supernode extraction complete
                Vertex writing complete
                        Total of 10 vertices have been successfully written
                Vertex validation complete
                Edge writing complete
                        Total of 5 edges have been successfully written
                Edge validation complete

```