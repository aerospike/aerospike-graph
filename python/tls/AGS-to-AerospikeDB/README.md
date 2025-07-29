# TLS Between AGS and Aerospike Server

This example will cover how to configure and use TLS between 
Aerospike Graph Service and Aerospike Server. 
This includes creating a new docker container for Aerospike Graph 
Service (AGS) and Aerospike Server.

## Relevant Files

The files 
```
docker-compose.yaml
aerospike.conf
make-certs.sh
```
are all important to use TLS between AGS and Aerospike Server and 
include explanitive comments.
Certificates and keys will also be generated in a new dir when
running the make-certs.sh
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
```shell
python3 -m pip install gremlinpython async_timeout
```

make-certs.sh creates the certificates and keys needed for TLS

```shell
./make-certs.sh
```

This should create the necessary files in the security folder, ca.crt, ca.key, server.crt, and server.key.

Next create the necessary docker containers by using
```shell
docker-compose up -d
```

Execute the python example to make sure you can connect to AGS and Query
```shell
python3 ./tls_example.py
```

If you see the output
```
Connected and Queried Successfully, TLS between AGS and Aerospike DB is set up!
```
it worked correctly!