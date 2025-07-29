# TLS Between AGS and Gremlin

This example will cover how to configure and use TLS between
Aerospike Graph Service and Gremlin.
This includes creating a new docker container for Aerospike Graph
Service (AGS) and Aerospike Server.

## Relevant Files

The files
```
docker-compose.yaml
make-certs.sh
tls_example.py
```
are all important to use TLS between AGS and Gremlin and
include explanitive comments.
Certificates and keys will also be generated in a new dir when
running the make-certs.sh

```dir
.
├── security/
│   ├── ca.crt
│   └── ca.key
└── g-tls/
    ├── server.crt
    └── server.key
```

## Run it

### Install Dependencies
Dependencies to install:
```shell
python3 -m pip install gremlinpython async_timeout
```
### Create Certificates and Keys
make-certs.sh creates the certificates and keys needed for TLS

Navigate to the AGS_Gremlin directory, and run the command:
```shell
./make-certs.sh
```

This should create the necessary files in the security folder: ca.crt, ca.key, 
and in the g-tls folder: server.crt, and server.key.

### Start Docker Containers
Next start the docker containers with:
```shell
docker-compose up -d
```

AGS and Aerospike Server should start up.

### Execute a query
Now execute the python example to make sure you can connect to AGS and query gremlin with TLS
```shell
python3 ./tls_example.py
```
If it works you should see output like
```
Values:
['aerospike', 'unlimited']
Connected and Queried Successfully, TLS Between AGS and Gremlin is set!
```
