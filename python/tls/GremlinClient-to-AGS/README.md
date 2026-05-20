# Transport Layer Security (TLS) between Gremlin client and Aerospike Graph Service

This example shows how to configure and use TLS between a Gremlin client and Aerospike Graph Service (AGS). It creates new Docker containers for AGS and Aerospike Database.

## Relevant files

The following files contain inline comments explaining how to configure TLS between AGS and a Gremlin client:

```text
docker-compose.yaml
make-certs.sh
tls_example.py
```

Running `make-certs.sh` also generates certificates and keys in two new directories:

```text
.
├── security/
│   ├── ca.crt
│   └── ca.key
└── g-tls/
    ├── server.crt
    └── server.key
```

## Run it

### Install dependencies

```shell
python3 -m pip install "gremlinpython>=3.7.0,<3.8.0" async_timeout
```

### Create certificates and keys

`make-certs.sh` creates the certificates and keys needed for TLS. From the `AGS_Gremlin` directory, run:

```shell
./make-certs.sh
```

This creates `ca.crt` and `ca.key` in `security/`, and `server.crt` and `server.key` in `g-tls/`.

### Start Docker containers

Start the Docker containers:

```shell
docker compose up -d
```

AGS and Aerospike Database start.

### Execute a query

Run the Python example to verify the connection to AGS over TLS:

```shell
python3 ./tls_example.py
```

## Expected output

```text
Values:
['aerospike', 'unlimited']
Connected and Queried Successfully, TLS Between AGS and Gremlin is set!
```
