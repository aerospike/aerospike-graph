# Swimato - Food Delivery Graph Demo Application

A demo application showcasing graph database capabilities using Aerospike Graph, featuring a food delivery system with
customers, restaurants, orders, and drivers.

## Overview

Swimato consists of two main components:

1. Data Generator (`swimato_datasetgen.py`) - Creates the dataset
2. GUI Interface (`frontend_streamlit.py`) - Runs the webpage

## Prerequisites

- Python 3.8+
- Aerospike Graph database
- Python virtual environment (recommended)
- Set up Aerospike Graph (see the root directory [README.md](../../../README.md) for more information)


1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install gremlinpython streamlit_agraph streamlit
```

## Data Generation

The `swimato_datasetgen.py` script generates sample food delivery orders with the following entities:

- Customers
- Restaurants
- Menu Items
- Orders
- Drivers
- Delivery Addresses

To generate sample data

```bash
python swimato_datasetgen.py
```

The data will now be created and mounted to the Aerospike Graph container.

Run the following command to load the data into Aerospike Graph:

```bash
python swimato_load.py
```

## GUI

`gremlin_queries.py` and `frontend_streamlit.py` create an interactive web page
to run graph queries, as well as visualize subgraphs of swimato.

start the webpage with

```bash
streamlit run frontend_streamlit.py
```

you may now test out the features navigated by the dropdown 'Select Action'

## Graph Schema

### Vertices

- CustomerProfile
- Restaurant
- MenuItem
- FoodOrder
- Driver
- DeliveryAddress

### Edges

- PLACED (CustomerProfile → FoodOrder)
- ORDERED_FROM (FoodOrder → Restaurant)
- CONTAINS (FoodOrder → MenuItem)
- DELIVERED_BY (FoodOrder → Driver)
- DELIVERED_TO (FoodOrder → DeliveryAddress)
- RATED (CustomerProfile → Restaurant)


