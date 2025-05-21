# Transport Layer Security Between AGS and Aerospike Server

This directory is an example on how to setup and use the Transport Layer Security feature
with Aerospike Graph. Including creating new docker containers for Aerospike Graph Service (AGS) and Aerospike Server.

In this example, we will setup TLS between AGS and Aerospike Server.

## How it Works

### Cluster Name Match Setup
All of your Aerospike server nodes must use the same certificate.
The certificate must include the cluster name defined in CN field such as:
```
Subject: C=US, ST=California, L=San Jose, O=Acme, Inc., OU=Aerospike Cluster, CN=as-cluster-west
```

All Aerospike server nodes must use the same aerospike.conf file, with 
the same cluster name specified in the aerospike.conf file.

A tls sub-stanza for ```<cluster-name>``` has to be defined in the aerospike.conf 
file and the tls-name in the service sub-stanza must be specified and have 
the value ```<cluster-name>``` in order for the node’s configured cluster name to 
be used as the TLS name.
Using the cluster name (cluster-name) requires using Aerospike’s heartbeat-v3 protocol.

On client applications, for each seed host passed into the ```cluster_create()```
call, pass in the same ```<cluster-name>``` for the tls-name as the TLS name.

### AGS Setup
In your AGS Properties file or wherever you set config options you need
```YAML
aerospike.client.tls=true
aerospike.client.host=<host>:<tls-name>:<port>
```
Replace <host> and <port> with your Aerospike DB host name and port.
Replace <tls-name> with the "tls-name" value from your Aerospike Database TLS configuration setup
in which you set up TLS on the Aerospike DB instance.

Then you want to add the certificates as volumes to AGS
```
volumes:
  - ./security/ca.crt:/opt/aerospike-graph/aerospike-client-tls/ca.crt
  - ./security/server.crt:/opt/aerospike-graph/aerospike-client-tls/server.crt
```
### Certificates and Keys
The shell script ```make-certs.sh``` generates these files and stores them
in the security directory for mounting.
```dir
.
├── security/
    ├── ca.crt
    └── ca.key
    └── server.crt
    └── server.key
```

## Run it

Dependencies to install:
``` bash
python3 -m pip install gremlinpython async_timeout
```

make-certs.sh creates the certificates and keys needed for TLS

Navigate to the AGS_AeroDB directory, and run the command:
```bash
./make-certs.sh
```

This should create the necessary files in the security folder, ca.crt, ca.key, server.crt, and server.key.

Next create the necessary docker containers by using
```bash
docker-compose up -d
```

Execute the python example to make sure you can connect to AGS and Query
```
python3 ./tls_example.py
```

If you see the output
```Connected and Queried Successfully, TLS between AGS and Aerospike DB is set up!```
it worked correctly!