# Aerospike Graph OLAP

## Overview

Aerospike Graph OLAP is a graph analytics engine that provides a high-performance,
scalable, and cost-effective solution for analyzing large-scale graph data.

It is designed to handle large-scale graph data and to be used in conjunction with
Aerospike Graph Service, which provides a distributed graph database that can
store and query large-scale graph data.

## Pre-requisites

- An Aerospike DB loaded with data that you want to analyze.
- A spark cluster to run the OLAP queries.
- The Aerospike Graph OLAP jar file provided with these instructions.
- A configuration file for Aerospike Graph OLAP that specifies the Aerospike DB connection details.
- Having a vertex label secondary indexes is required if running questions like: `g.withComputer().V().hasLabel("<label>").<etc>`
- Configuring Aerospike to handle a lot of secondary indexes is required.
    - Example for setting single-query-threads: `aerolab attach shell -n "$name" -l all -- asinfo -v '"set-config:context=namespace;id=test;single-query-threads=4"'`
    - Example for setting query-threads-limit: `aerolab attach shell -n "$name" -l all -- asinfo -v '"set-config:context=service;query-threads-limit=1024"'`
    - **Max secondary indexes that can be run is query-threads-limit / single-query-threads,
      which is also how many spark executors can work in parallel without errors.**

## Setup

A spark cluster is required to run Aerospike Graph OLAP.
Please refer to [AWS EMR](./aws-setup/OLAP_AWS.md), [GCP Dataproc](./gcp-setup/OLAP_GCP.md)
and [on prem Spark](./local-setup/OLAP_ON_PREM.md) examples for help.

Based on initial experimentation, having 1 spark executor per 3 aerospike
db cores seems to yield max performance. The actual
ratio will depend on the number of drives each Aerospike cluster has and
the network speed, but this is a good starting point.