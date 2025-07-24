# Food Delivery Graph Demo Application

A demo application showcasing graph database capabilities using Aerospike Graph, featuring a food delivery system with
customers, restaurants, orders, and drivers.

## Overview

Food Delivery App consists of two main components:

1. Data Generator (`food_delivery_datasetgen.py`) - creates the dataset.
2. GUI Interface (`frontend_streamlit.py`) - runs the webpage.

## Prerequisites

- Python 3.8+
- Aerospike Graph database
- Python virtual environment (recommended)
- Set up Aerospike Graph (see the root directory [README.md](../README.md) for more information)


1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install gremlinpython streamlit_agraph streamlit
   ```

## Data Generation

The `food_delivery_datasetgen.py` script generates sample food delivery orders with the following entities:

- Customers
- Restaurants
- Menu items
- Orders
- Drivers
- Delivery addresses

To generate sample data, use the following script with or without any of 
the following options to customize the size of the dataset:
```
--n-customers x                #default is 100000
--n-restaurants x              #default is 1000
--n-drivers x                  #default is 500
--min-orders-per-customer x    #default is 1
--max-orders-per-customer x    #default is 5
```

```bash
python food_delivery_datasetgen.py
```

The data is created and mounted to the Aerospike Graph container.

Run the following command to load the data into Aerospike Graph:

```bash
python food_delivery_load.py
```

## GUI

`gremlin_queries.py` and `frontend_streamlit.py` create an interactive web page
to run graph queries, as well as visualize subgraphs of the food delivery data.

Start the webpage with the following command:

```bash
streamlit run frontend_streamlit.py
```

You can now test out the features navigated by the dropdown 'Select Action'.

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
