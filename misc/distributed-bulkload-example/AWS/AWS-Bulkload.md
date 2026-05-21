# Distributed AWS bulk load example

This example walks you through running a distributed Aerospike Graph Service (AGS) bulk load on AWS EMR using an Aerolab-managed Aerospike cluster.

1. Configure Aerolab for AWS. Follow the [Aerolab AWS setup guide](https://github.com/aerospike/aerolab/blob/master/docs/aws-setup.md).

   Set your default Aerolab zone to the same zone where you intend to create the cluster (in this example, `us-east-1`). Otherwise, unexpected behavior may occur.

2. Create an S3 bucket for the data:

   ```shell
   aws s3 mb s3://<BUCKET_NAME>/ --region <REGION>
   ```

   Download the bulk-loader JAR from the [Aerospike Graph downloads page](https://aerospike.com/download/graph/loader/). Place the JAR in your bucket directory at `bucket-files/jars/`.

3. Edit `set_variables.sh` and set the following variables:

   ```properties
   name
   username
   BUCKET_PATH
   SUBNET_ID           # set after creating your Aerolab cluster
   SECURITY_GROUP      # set after creating your Aerolab cluster
   ```

4. Start the Aerospike cluster. With the variables (excluding `SUBNET_ID` and `SECURITY_GROUP`) set, run:

   ```shell
   ./create_cluster.sh
   ```

   Capture the subnet ID and security-group ID from the output and set them as the values for:

   ```properties
   SUBNET_ID
   SECURITY_GROUP
   ```

5. Find the cluster private IP with `aerolab cluster list`, then edit `bucket-files/config/bulk-loader.properties` with your bucket name and cluster IP.

   ```shell
   aerolab cluster list
   ```

6. Upload files to the bucket:

   ```shell
   aws s3 cp ./bucket-files s3://<BUCKET_NAME>/ --recursive --region us-east-1
   ```

   ```shell
   aws s3 cp ../../../common/bulkload-data/* s3://<BUCKET_NAME>/ --recursive --region us-east-1
   ```

7. Create an EMR cluster and submit the bulk load:

   ```shell
   ./bulkload.sh
   ```

   Check on the job status:

   ```shell
   aws emr describe-step --cluster-id "<EMR_CLUSTER_ID>" --step-id "<STEP_ID>" --region "<REGION>"
   ```

## Expected output

When the bulk load succeeds, the output looks similar to:

```text
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
