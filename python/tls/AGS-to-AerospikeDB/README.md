# Transport Layer Security (TLS) between Aerospike Graph Service and Aerospike Database

This example shows how to configure and use TLS between Aerospike Graph Service (AGS) and Aerospike Database. It creates new Docker containers for AGS and Aerospike Database.

## Relevant files

The following files contain inline comments explaining how to configure TLS between AGS and Aerospike Database:

```text
docker-compose.yaml
aerospike.conf
make-certs.sh
```

Running `make-certs.sh` also generates certificates and keys in a new `security/` directory:

```text
.
└── security/
    ├── ca.crt
    ├── ca.key
    ├── server.crt
    └── server.key
```

## Run it

### Install dependencies

```shell
python3 -m pip install "gremlinpython>=3.7.0,<3.8.0" async_timeout
```

### Create certificates and keys

```shell
./make-certs.sh
```

The script writes `ca.crt`, `ca.key`, `server.crt`, and `server.key` to `security/`.

### Start Docker containers

```shell
docker compose up -d
```

### Execute a query

```shell
python3 ./tls_example.py
```

## Expected output

```text
Connected and Queried Successfully, TLS between AGS and Aerospike DB is set up!
```
