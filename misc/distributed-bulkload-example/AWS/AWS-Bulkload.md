# Distributed AWS Bulkload Example

1. Configure Aerolab for AWS
   Use this guide: https://github.com/aerospike/aerolab/blob/master/docs/aws-setup.md
   Make sure your default zone in Aerolab is the same as the zone you intend to make the cluster in, in this case us-central1-a.
   Otherwise, unexpected behaviour may occur.

2. Make S3 bucket
   Make a bucket in AWS S3 for the data:
    ```shell
    aws s3 mb s3://<bucket-name>/ --region <my-region>
    ```
   Download bulk loader jar from here
   https://aerospike.com/download/graph/loader/

   and place the bulk loader JAR in your bucket directory
   bucket-files/jars`

3. Edit the variables script
   Now edit the `set_variables.sh` script and change values of the variables
   There are explanatory comments in it to help.

8. Attach the graph stack
   Once the variables are set, run
    ```shell
    ./create_ag_stack.sh
Make sure to grab the subnet ID and security group ID from the output

5. Configure properties file
   Edit the properties file in `bucket-files/configs/bulk-loader.properties`
   editing the values to your bucket names and cluster IP

6. Upload files to AWS
   Now upload the files to the bucket using
    ```shell
   aws s3 cp ./bucket-files s3://<bucket-name>/ --recursive --region <my-region>
    ```

9. Create EMR cluster and submit the bulkload
   Now to create a EMR cluster and submit the bulkload job run
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
