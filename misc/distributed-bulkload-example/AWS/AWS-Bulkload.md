# Distributed AWS Bulkload Example

1. Configure Aerolab for AWS
Follow this guide to configure Aerolab for AWS: 
https://github.com/aerospike/aerolab/blob/master/docs/aws-setup.md

Make sure your default zone in Aerolab is the same as the zone you intend to make the cluster in, in this case `us-east-1`.
Otherwise, unexpected behaviour may occur.

2. Make Your S3 Bucket
Make a bucket in AWS S3 for the data:
```shell
   aws s3 mb s3://<bucket-name>/ --region <my-region>
```
Download bulk loader jar from here
https://aerospike.com/download/graph/loader/

and place the bulk loader JAR in your bucket directory
bucket-files/jars`

3. Edit the Variables Script
Now edit the `set_variables.sh` script and change values of the variables
Neccesary variable changes are for:
```properties
   name
   username
   BUCKET_PATH
   SUBNET_ID           # This will be changed after creating your Aerolab Cluster
   SECURITY_GROUP      # This will be changed after creating your Aerolab Cluster
```

4. Start the Aerolab Cluster
Once the variables (not including `SUBNET_ID` or `SECURITY_GROUP`) are set, run
```shell
   ./create_cluster.sh
```
Make sure to grab the subnet ID and security group ID from the output
and put them as the values for
```properties
SUBNET_ID           # This will be changed after creating your Aerolab Cluster
SECURITY_GROUP      # This will be changed after creating your Aerolab Cluster
```

5. Configure Your Properties File
Find the Private IP for your cluster using
```bash
aerolab cluster list 
```
Edit the properties file in `bucket-files/configs/bulk-loader.properties`
editing the values to your bucket names and cluster IP

6. Upload Files to AWS
Now upload the files to the bucket using
 ```shell
   aws s3 cp ./bucket-files s3://<your-bucket-name>/ --recursive --region us-east-1
 ```
7. Create EMR Cluster and Submit the Bulkload
Now to create a EMR cluster and submit the bulkload job run:
 ```shell
    ./bulkload.sh
 ```

You can check on it using:
```bash
aws emr describe-step --cluster-id "<your-emr-cluster-id>" --step-id "<your-step-id>" --region "<your-region>"
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