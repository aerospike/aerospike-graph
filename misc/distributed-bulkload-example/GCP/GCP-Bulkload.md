# GCP Distributed Bulkload Example
    
1. Configure Aerolab for GCP
    Follow this guide to configure Aerolab for GCP: 
    https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md
    Make sure your default zone in Aerolab is the same as the zone you intend to make the cluster in, in this case us-central1-a.
    Otherwise, unexpected behaviour may occur.
    
2. Create Your Cluster
    Now create your Aerospike cluster using this script:
    ```bash
    ./create_cluster.sh
    ```
    
3. Find the Cluster IP
    Now that your cluster is running, find its Private IP using
    ```shell
    aerolab cluster list
    ```
    
4. Make Your GCP Bucket
    Make a bucket in gcp for the data: 
    ```shell
    gsutil mb gs://<name-of-bucket>
    ```
    
    Download bulk loader jar from here
    https://aerospike.com/download/graph/loader/
    
    and place the bulk loader JAR in your bucket directory
    bucket-files/jars`
    
5. Configure Your Properties File
    Edit the properties file in `bucket-files/config/bulk-loader.properties` 
    editing the values to your bucket names and cluster IP
    
6. Upload Files to GCP
    Now upload the files to the bucket using
    ```shell
    gsutil cp -r ./bucket-files/* gs://<name-of-bucket>
    ```
    
7. Edit the Variables Script
    Now edit the `set_variables.sh` script and change values of the variables
    There are explanatory comments in it to help.
    
8. Create Dataproc Cluster and Submit the Bulkload
    Now to create a dataproc cluster and submit the bulkload job run
    ```shell
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
