Follow all the way through here: https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md

You now have a cluster called testcluster
Find its IP using
```bash
aerolab cluster list
```
Make a buckit: gsutil mb gs://gcp-bl-test

load the vertices and edges to the bucket
```bash
gsutil cp ./vertices.csv gs://gcp-bl-test/vertices/
```
```bash
gsutil cp ./edges.csv gs://gcp-bl-test/edges/
```
Download bulk loader jar to this directory:
https://aerospike.com/download/graph/loader/

```bash
gsutil cp C:\Users\chengstler_aerospike\Downloads gs://gcp-bl-test/jars/
```

Upload the config
```bash
gsutil cp bulk-loader.properties gs://gcp-bl-test/configs/
```

gcloud dataproc clusters create testcluster \
--enable-component-gateway \
--region us-central1 \
--zone us-central1-a \
--master-machine-type n2d-highmem-8 \
--master-boot-disk-type pd-ssd \
--master-boot-disk-size 500 \
--num-workers 8 \
--worker-machine-type n2d-highmem-8 \
--worker-boot-disk-type pd-ssd \
--worker-boot-disk-size 500 \
--image-version 2.1-debian11 \
--project my-project

gcloud dataproc jobs submit spark \
--cluster testcluster \
--region us-central1 \
--class com.aerospike.firefly.bulkloader.SparkBulkLoader \
--jars gs://my-bucket/jars/aerospike-graph-bulk-loader-2.6.0.jar \
-- \
-c gs://my-bucket/configs/bulk-loader.properties

gcloud dataproc jobs list --region us-central1
gcloud dataproc jobs wait <JOB_ID> --region us-central1