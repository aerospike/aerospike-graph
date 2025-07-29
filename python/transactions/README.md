# Overview

The transactions-between-users.py example is a web application that
visualizes transactions between two users in a web browser where you can
refresh data and query for different users.

# Usage

1. Start Docker Image:
   From the root of the example directory, run the following command to start the Docker image:
   ```shell
   docker compose up -d
   ```

2. Install Python Dependencies:
   ```shell
   pip install gremlinpython dash dash-cytoscape dash-bootstrap-components
   ```

3. Start the Web Example:
   ```shell
   python transactions_between_users.py
   ```

4. Open the Web Application:
   Open your web browser and navigate to `http://localhost:8050/` to view the web application.