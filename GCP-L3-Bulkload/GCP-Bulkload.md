# Aerolab and GCP L3 Bulkload Example
All files have explanatory comments for further details

Setup aerolab by following this tutorial
**https://github.com/aerospike/aerolab/blob/master/docs/GETTING_STARTED.md**

Configure aerolab for gcp
```bash
aerolab config backend -t gcp -o project-name
```
Make sure zones are consistent
```bash
aerolab config defaults -k '*.Zone' -v 'us-central1-a'
gcloud config set compute/zone us-central1-a
```

Download bulkloader jar and put in top level of bucket-files dir
https://aerospike.com/download/graph/loader/

Configure bulk loader properties in bucket files dir, changing the name,
and path to vertices/edges.
Upload the data to a gcp bucket using
```bash
gsutil -m cp -r bucket-files/* gs://name-of-bucket
```
now the bucket should look like this
```
-name-of-bucket
    |
    |--- edges
    |      |--- edges.csv
    |
    |--- vertices
    |      |--- vertices.csv
    |
    |--- bulk-loader.properties
    |--- aerospike-graph-bulk-loader-2.6.0.jar
```
You can use your own data instead, or make your own, formatting like this:
Edges:
```csv
~label,~to,~from,property1,property2
label,1789265,1,value1,value2
```

Vertices:
```csv
~id,~label,property1,property2
1,label,value1,value2
```

Configure set variables script changing names and paths to your gcp bucket

Now create your Aerospike cluster in Aerolab 
```bash
./create_ag_stack.sh
```

After running that successfully, bulkload your data to the server
```bash
./bulkload.sh
```

In cmd run
```bash
aerolab client list
```
find your graph instance i.e. ```name-of-cluster-g```
take the external ip and place it into test-bl.py

install dependencies and run
```bash
pip install gremlin-python
python3 test-bl.py
```

You should see output like
```
Successfully connected to Aerospike Graph Instance!
Vertice count: 10
Properties of vertice 100752818: 
[{'name': [' joe']}]
```