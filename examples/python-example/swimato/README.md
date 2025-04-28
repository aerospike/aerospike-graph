# Swimato - Food Delivery Graph Demo Application

A demo application showcasing graph database capabilities using Aerospike Graph, featuring a food delivery system with
customers, restaurants, orders, and drivers.

## Overview

Swimato consists of two main components:

1. Data Generator (`swimato-datasetgen.py`) - Creates the dataset
2. CLI Interface (`swimato_cli.py`) - Provides commands to interact with the graph database

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
pip install gremlinpython
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

to run

```bash
pip install streamlit_agraph streamlit
```

then start the webpage with

```bash
streamlit run frontend_streamlit.py
```

you may now test out the features navigated by the dropdown 'Select Action'

## CLI Interface

The `swimato_cli.py` provides an interactive interface to query the graph database.

To start the CLI:

```bash
python swimato_cli.py
```

### Available Commands

1. Check Order Status:

```bash
swimato> check_order order <order_id>
# Shows order status and items

swimato> check_order customer <customer_id>
# Shows most recent order for customer
```

2. Assign Driver:

```bash
swimato> assign_driver <order_id> <driver_id>
# Assigns a driver to an order and updates status
```

3. View Restaurant Ratings:

```bash
swimato> restaurant_ratings <restaurant_id>
# Shows recent ratings and comments for restaurant
```

4. View Customer Orders:

```bash
swimato> customer_orders <customer_id>
# Shows 5 most recent orders for customer
```

5. Exit CLI:

```bash
swimato> quit
# or press Ctrl+D
```

### Sample Usage

```bash
swimato> check_order order order_123456
Order Status: PLACED
Order Items:
- Burger: 2 x $9.99
- Fries: 1 x $4.99

swimato> customer_orders customer_004670
5 Most Recent Orders:
Order ID: order_789012
Status: DELIVERED
Date: 2024-03-14 15:45:23
------------------------------
Order ID: order_789013
Status: PLACED
Date: 2024-03-14 14:30:12
------------------------------
```

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


