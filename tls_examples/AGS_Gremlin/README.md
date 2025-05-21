# Transport Layer Security Between AGS and Gremlin

This directory is an example on how to setup and use the Transport Layer Security feature
with Aerospike Graph. Including creating new docker containers for Aerospike Graph Service (AGS) and Aerospike.

In this example, we will setup TLS between AGS and Gremlin.

## How it Works

### Setting The Option
To use TLS between AGS and Gremlin, your AGS instance needs to
be started with the option
```aerospike.graph-service.ssl.enabled=true```

In this example it is done through the ```docker-compose.yaml``` here
```YAML
environment:
  aerospike.client.host: gremlin-tls-aerospike-db
  aerospike.client.port: 3000
  aerospike.client.namespace: test
  aerospike.graph-service.ssl.enabled: true
```

### Certificates / Keys
For TLS, a certificate and private key are needed, and optionally a certificate
authority.
The shell script ```make-certs.sh``` generates these files and stores them
in directories for mounting.
```dir
.
├── security/
│   ├── ca.crt
│   └── ca.key
└── g-tls/
    ├── server.crt
    └── server.key
```

To use TLS, you will need to mount the certificate and private key
to ```/opt/aerospike-graph/gremlin-server-tls```, and if you are wanting
certificate authority, the certificate should be mounted to ```/opt/aerospike-graph/gremlin-server-ca```.
These should be the only files mounted in the respective directories.

In this example they are mounted through the ```docker-compose.yaml```
from sub-directories made in the shell script.
```YAML
volumes:
- ./g-tls:/opt/aerospike-graph/gremlin-server-tls:ro
- ./security/ca.crt:/opt/aerospike-graph/gremlin-server-ca/ca.crt:ro
```

### Querying / Gremlin
When querying gremlin, you will now have to use the secure websocket scheme,
and supply a SSL/TLS context that trusts your CA if using one.
You can also optionally check hostname/clustername.
```python
ssl_context = ssl.create_default_context(
    cafile="./security/ca.crt"
)
connection = DriverRemoteConnection(
    'wss://localhost:8182/gremlin',
    'g',
    ssl_context=ssl_context
)
```

## Run it

### Install Dependencies
Dependencies to install:
``` bash
python3 -m pip install gremlinpython async_timeout
```
### Create Certificates and Keys
make-certs.sh creates the certificates and keys needed for TLS

Navigate to the AGS_Gremlin directory, and run the command:
```bash
./make-certs.sh
```

This should create the necessary files in the security folder: ca.crt, ca.key, 
and in the g-tls folder: server.crt, and server.key.

### Start Docker Containers
Next start the docker containers with:
```bash
docker-compose up -d
```

AGS and Aerospike Server should start up.

### Execute a query
Now execute the python example to make sure you can connect to AGS and query gremlin with TLS
```
python3 ./tls_example.py
```
If it works you should see output like
```
Values:
['aerospike', 'unlimited']
Connected and Queried Successfully, TLS Between AGS and Gremlin is set!
```