# Overview

The example.py example is a command line application
that generates a graph of transactions between users, and runs sample queries.

# Usage
1. Start Docker Image:
   From the root of the example directory, run the following command to start the Docker image:
   ```shell
   docker compose up -d
   ```

2. Install Gremlin Python dependency. AGS requires TinkerPop 3.7.x client drivers; 3.8.x and 4.0.x are not compatible:
   ```shell
   pip install "gremlinpython>=3.7.0,<3.8.0"
   ```

3. Run the basic Python example:
   ```shell
   python example.py
   ```