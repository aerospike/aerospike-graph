# GCP L3 Bulkload Example

1.Configure Aerolab for GCP
Use this guide: https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md

2. Create your cluster
```bash
aerolab cluster create /name:cluster-name /count:3 /aerospike-version:8.0.0.7 /instance:e2-medium /zone:us-central1-a
```

3. Find the cluster IP
You now have a cluster called aerolab-cluster-name
Find its IP using
```bash
aerolab cluster list
```

4. Make GCP bucket
Make a bucket in gcp for the data: 
```bash
gsutil mb gs://name-of-bucket
```

Download bulk loader jar from here
https://aerospike.com/download/graph/loader/

and place the bulk loader JAR in your bucket directory
```bucket-files/jars```

5. Configure properties file
Edit the properties file in ```bucket-files/configs/bulk-loader.properties``` 
editing the values to your bucket names and cluster IP

6. Upload files to GCP
Now upload the files to the bucket using
```bash
gsutil cp -r ./bucket-files/* gs://name-of-bucket
```

7. Edit the variables script
Now edit the ```set_variables.sh``` script and change values of the variables
There are explanatory comments in it to help.

8. Attach the graph stack
Once the variables are set, run 
```bash
./create_ag_stack.sh
```

9. Create dataproc cluster and submit the bulkload
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
                Edge cache generation complete
                Vertex writing complete
                        Total of 10 vertices have been successfully written
                Vertex validation complete
                Edge writing complete
                        Total of 5 edges have been successfully written
                Edge validation complete


```