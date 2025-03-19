# Aerospike Graph Build Docker with Bulk Loader

This folder contains a docker compose file that builds the Aerospike Graph docker image and with the Aerospike Bulk Loader.

# Build command
```shell
./build.sh <version>
```
Please note that the minimum version support is 2.6.0.

Prior to version 2.6.0, the bulk loader was automatically bundled in the image, with the exception of the `-slim` image.

# Example output
```shell
./build.sh 2.6.0
```
TODO.
