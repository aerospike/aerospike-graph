# Distributed GCP bulk load example

This example walks you through running a distributed Aerospike Graph Service (AGS) bulk load on GCP Dataproc using an Aerolab-managed Aerospike cluster.

1. Configure Aerolab for GCP. Follow the [Aerolab GCP setup guide](https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md).

   Set your default Aerolab zone to the same zone where you intend to create the cluster (in this example, `us-central1-a`). Otherwise, unexpected behavior may occur.

2. Create your Aerospike cluster:

   ```bash
   ./create_cluster.sh
   ```

3. Find the cluster private IP:

   ```shell
   aerolab cluster list
   ```

4. Create a GCP bucket for the data:

   ```shell
   gsutil mb gs://<BUCKET_NAME>
   ```

   Download the bulk-loader JAR from the [Aerospike Graph downloads page](https://aerospike.com/download/graph/loader/). Place the JAR in your bucket directory at `bucket-files/jars/`.

5. Edit `bucket-files/config/bulk-loader.properties`, setting the bucket name and cluster IP.

6. Upload files to the bucket:

   ```shell
   gsutil cp -r ./bucket-files/* gs://<BUCKET_NAME>
   ```

   ```shell
   gsutil cp -r ../../../common/bulkload-data/* gs://<BUCKET_NAME>
   ```

7. Edit `set_variables.sh` and update the variables. Inline comments explain each value.

8. Create the Dataproc cluster and submit the bulk load:

   ```shell
   ./bulkload.sh
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
