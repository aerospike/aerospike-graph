# Python basic example

A command-line application that generates a graph of transactions between users and runs sample queries against Aerospike Graph Service (AGS).

## Prerequisites

- Python 3.9 or later.
- Docker.

> **Note:** AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x are incompatible.

## Usage

1. From the example directory root, start Docker Compose:

   ```shell
   docker compose up -d
   ```

2. Install the Gremlin Python dependency:

   ```shell
   pip install "gremlinpython>=3.7.0,<3.8.0"
   ```

3. Run the example:

   ```shell
   python example.py
   ```
