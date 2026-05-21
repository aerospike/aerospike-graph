# Python transactions example

A web application that visualizes transactions between two users in a web browser. Refresh data and query for different users from the UI.

## Prerequisites

- Python 3.9 or later.
- Docker.

> **Note:** Aerospike Graph Service (AGS) requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x are incompatible.

## Usage

1. From the example directory root, start Docker Compose:

   ```shell
   docker compose up -d
   ```

2. Install Python dependencies:

   ```shell
   pip install "gremlinpython>=3.7.0,<3.8.0" dash dash-cytoscape dash-bootstrap-components
   ```

3. Start the web app:

   ```shell
   python transactions_between_users.py
   ```

4. Open a web browser and navigate to `http://localhost:8050/`.
