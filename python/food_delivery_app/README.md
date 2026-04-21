# Food-delivery graph demo application

A demo application that uses Aerospike Graph Service (AGS) to model a food-delivery system with customers, restaurants, orders, and drivers.

## Overview

The food-delivery app has two main components:

1. **Data generator** (`food_delivery_datasetgen.py`) — creates the dataset.
2. **GUI** (`frontend_streamlit.py`) — runs the web page.

## Prerequisites

- Python 3.9 or later.
- Aerospike Graph Service. Set up AGS using the [root README](../../README.md).
- A Python virtual environment (recommended).

> **Note:** AGS requires Apache TinkerPop 3.7.x Gremlin client drivers. TinkerPop 3.8.x and 4.0.x are incompatible.

## Setup

1. Create and activate a virtual environment:

   ```shell
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```shell
   pip install "gremlinpython>=3.7.0,<3.8.0" streamlit_agraph streamlit
   ```

## Data generation

The `food_delivery_datasetgen.py` script generates sample food-delivery orders for the following entities:

- Customers
- Restaurants
- Menu items
- Orders
- Drivers
- Delivery addresses

To generate sample data, run the script with or without these options to control dataset size:

```text
--n-customers x                # default: 100000
--n-restaurants x              # default: 1000
--n-drivers x                  # default: 500
--min-orders-per-customer x    # default: 1
--max-orders-per-customer x    # default: 5
```

```shell
python food_delivery_datasetgen.py
```

The generated data is written to a directory mounted into the AGS container.

Load the generated data into AGS:

```shell
python food_delivery_load.py
```

## GUI

`gremlin_queries.py` and `frontend_streamlit.py` together provide an interactive web page for running graph queries and visualizing subgraphs of the food-delivery data.

Start the web page:

```shell
streamlit run frontend_streamlit.py
```

Use the **Select Action** dropdown to navigate between features.

## Graph schema

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
