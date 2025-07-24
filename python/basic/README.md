# Overview

The fraud-mimic.py example is a command line application
that generates a graph of transactions between users, and runs sample queries.

# Usage
1. Start Docker Image:
   From the root of the example directory, run the following command to start the Docker image:
```bash
docker compose up -d
```
2. Install Python Dependencies:
```bash
pip install gremlinpython
```
3. Run the CLI Example:
```bash
python fraud_mimic.py
```