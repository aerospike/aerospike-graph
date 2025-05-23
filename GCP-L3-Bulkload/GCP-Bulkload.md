Follow all the way through here: https://github.com/aerospike/aerolab/blob/master/docs/gcp-setup.md

aerolab cluster create -n testcluster -c 3 --instance e2-medium --zone us-central1-a --region  us-central1 --disk pd-balanced:20 --disk pd-ssd:40 --disk pd-ssd:40

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
Make a service account and add the info to the properties file:

Upload the config
```bash
gsutil cp bulk-loader.properties gs://gcp-bl-test/configs/
```

Now run the shell script:
```bash
run-spark.sh
```


gcloud dataproc jobs list --region us-central1
gcloud dataproc jobs wait <JOB_ID> --region us-central1