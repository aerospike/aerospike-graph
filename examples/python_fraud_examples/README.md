# Overview

The fraud-mimic.py example is a command line application
that generates a graph of transactions between users, and runs sample queries.
The transactions-between-users.py example is a web application that
visualizes transactions between two users in a web browser where you can
refresh data and query for different users.

# Usage

1. Start Docker Image:
   From the root of the example directory, run the following command to start the Docker image:
   ```bash
   docker compose up -d
   ```
2. Install Python Dependencies:
   ```bash
   pip install gremlinpython dash dash-cytoscape dash-bootstrap-components
   ```
3. Run the Example:
   ```bash
   python fraud_mimic.py
   ```
   OR
   ```bash
   python transctions_between_users.py
   ```
4. Open the Web Application:
   Open your web browser and navigate to `http://localhost:8050/` to view the web application.
   There is only a web application for the `transctions_between_users.py` example.
   The  `fraud_mimic.py` example is a command line application.