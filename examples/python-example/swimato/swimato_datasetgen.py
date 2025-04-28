import os
import random
import time

# Parameters
n_customers = 100000
n_restaurants = 1000
n_drivers = 500
min_orders_per_customer = 1
max_orders_per_customer = 5

# Base timestamp (in milliseconds) and variation for order dates.
base_timestamp = int(time.time() * 1000)
order_time_variation = 10000000  # ~2.8 hours variation

# Define output folder structure mappings for vertex and edge types.
# The value is the subfolder (and file name) to be used.
vertex_types = {
    "CustomerProfile": "customer",
    "DeliveryAddress": "deliveryaddress",
    "Restaurant": "restaurant",
    "MenuItem": "menuitem",
    "Driver": "driver",
    "FoodOrder": "foodorder",
}

edge_types = {
    "HAS_ADDRESS": "has_address",
    "PLACED": "placed",
    "ORDERED_FROM": "ordered_from",
    "DELIVERED_TO": "delivered_to",
    "DELIVERED_BY": "delivered_by",
    "CONTAINS": "contains",
    "RATED": "rated",
}

# Define CSV headers for vertices and edges.
# The header order defines the order of the values to be output.
vertex_headers = {
    "CustomerProfile": "~id,~label,customer_id,name,email",
    "DeliveryAddress": "~id,~label,address_id,street,city,zip",
    "Restaurant": "~id,~label,restaurant_id,name,location",
    "MenuItem": "~id,~label,menu_item_id,name,price,description",
    "Driver": "~id,~label,driver_id,name,rating",
    "FoodOrder": "~id,~label,order_id,order_date,status",
}

edge_headers = {
    "HAS_ADDRESS": "~from,~to,~label",
    "PLACED": "~from,~to,~label,order_date",
    "ORDERED_FROM": "~from,~to,~label",
    "DELIVERED_TO": "~from,~to,~label",
    "DELIVERED_BY": "~from,~to,~label",
    "CONTAINS": "~from,~to,~label,qty",
    "RATED": "~from,~to,~label,rating,comment",
}

# Function to create directories and open file handles with header rows.
def open_file_handles(base_folder, mapping, header_mapping):
    handles = {}
    for label, subfolder in mapping.items():
        dir_path = os.path.join(base_folder, subfolder)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{subfolder}.csv")
        file_handle = open(file_path, "w", encoding="utf-8")
        # Write the header row for this file.
        file_handle.write(header_mapping[label] + "\n")
        handles[label] = file_handle
    return handles

# Open file handles for vertices and edges.
vertex_files = open_file_handles("vertices", vertex_types, vertex_headers)
edge_files = open_file_handles("edges", edge_types, edge_headers)

# Dictionary to hold restaurant -> menu items mapping.
restaurant_menu_items = {}

# --- 1. Create CustomerProfile and DeliveryAddress vertices & HAS_ADDRESS edges ---
for i in range(1, n_customers + 1):
    customer_id = f"customer_{i:06d}"
    # CustomerProfile vertex row: ~id,~label,customer_id,name,email
    customer_vertex = f"{customer_id},CustomerProfile,{customer_id},Customer {i},customer{i}@example.com"
    vertex_files["CustomerProfile"].write(customer_vertex + "\n")
    
    # DeliveryAddress vertex row: ~id,~label,address_id,street,city,zip
    address_id = f"address_{i:06d}"
    street = f"{i} Main St"
    city = f"City{(i % 100) + 1}"
    zip_code = f"{10000 + (i % 90000)}"
    address_vertex = f"{address_id},DeliveryAddress,{address_id},{street},{city},{zip_code}"
    vertex_files["DeliveryAddress"].write(address_vertex + "\n")
    
    # Edge: HAS_ADDRESS row: ~from,~to,~label
    edge_has_address = f"{customer_id},{address_id},HAS_ADDRESS"
    edge_files["HAS_ADDRESS"].write(edge_has_address + "\n")

# --- 2. Create Restaurant and MenuItem vertices ---
for i in range(1, n_restaurants + 1):
    restaurant_id = f"restaurant_{i:06d}"
    # Restaurant vertex row: ~id,~label,restaurant_id,name,location
    restaurant_vertex = f"{restaurant_id},Restaurant,{restaurant_id},Restaurant {i},Location {i}"
    vertex_files["Restaurant"].write(restaurant_vertex + "\n")
    
    # Each restaurant gets between 5 and 10 menu items.
    n_menu_items = random.randint(5, 10)
    menu_item_ids = []
    for j in range(1, n_menu_items + 1):
        menu_item_id = f"menuItem_{restaurant_id}_{j:02d}"
        menu_item_ids.append(menu_item_id)
        price = round(random.uniform(5, 30), 2)
        # MenuItem vertex row: ~id,~label,menu_item_id,name,price,description
        menu_item_vertex = f"{menu_item_id},MenuItem,{menu_item_id},Menu Item {j} at {restaurant_id},{price},Delicious food"
        vertex_files["MenuItem"].write(menu_item_vertex + "\n")
    restaurant_menu_items[restaurant_id] = menu_item_ids

# --- 3. Create Driver vertices ---
for i in range(1, n_drivers + 1):
    driver_id = f"driver_{i:06d}"
    rating = round(random.uniform(3, 5), 2)
    # Driver vertex row: ~id,~label,driver_id,name,rating
    driver_vertex = f"{driver_id},Driver,{driver_id},Driver {i},{rating}"
    vertex_files["Driver"].write(driver_vertex + "\n")

# --- 4. Create FoodOrder vertices and related edges ---
order_counter = 1

for i in range(1, n_customers + 1):
    customer_id = f"customer_{i:06d}"
    # Number of orders for this customer (random between min and max).
    n_orders = random.randint(min_orders_per_customer, max_orders_per_customer)
    for _ in range(n_orders):
        order_id = f"order_{order_counter:08d}"
        order_date = base_timestamp + random.randint(0, order_time_variation)
        status = random.choice(["DELIVERED", "IN_PROGRESS", "CANCELED"])
        # FoodOrder vertex row: ~id,~label,order_id,order_date,status
        order_vertex = f"{order_id},FoodOrder,{order_id},{order_date},{status}"
        vertex_files["FoodOrder"].write(order_vertex + "\n")
        
        # Edge: PLACED row: ~from,~to,~label,order_date
        edge_placed = f"{customer_id},{order_id},PLACED,{order_date}"
        edge_files["PLACED"].write(edge_placed + "\n")

        # Randomly assign a restaurant for this order.
        restaurant_index = random.randint(1, n_restaurants)
        restaurant_id = f"restaurant_{restaurant_index:06d}"
        # Edge: ORDERED_FROM row: ~from,~to,~label
        edge_ordered_from = f"{order_id},{restaurant_id},ORDERED_FROM"
        edge_files["ORDERED_FROM"].write(edge_ordered_from + "\n")

        # Edge: DELIVERED_TO row: ~from,~to,~label, using customer's delivery address.
        address_id = f"address_{i:06d}"
        edge_delivered_to = f"{order_id},{address_id},DELIVERED_TO"
        edge_files["DELIVERED_TO"].write(edge_delivered_to + "\n")

        # Randomly assign a driver.
        driver_index = random.randint(1, n_drivers)
        driver_id = f"driver_{driver_index:06d}"
        # Edge: DELIVERED_BY row: ~from,~to,~label
        edge_delivered_by = f"{order_id},{driver_id},DELIVERED_BY"
        edge_files["DELIVERED_BY"].write(edge_delivered_by + "\n")

        # For each order, randomly select 1 to 3 menu items from the chosen restaurant.
        n_order_items = random.randint(1, 3)
        menu_items = restaurant_menu_items[restaurant_id]
        for _ in range(n_order_items):
            menu_item_id = random.choice(menu_items)
            qty = random.randint(1, 5)
            # Edge: CONTAINS row: ~from,~to,~label,qty
            edge_contains = f"{order_id},{menu_item_id},CONTAINS,{qty}"
            edge_files["CONTAINS"].write(edge_contains + "\n")

        # With a probability, create a RATED edge from customer to restaurant.
        if random.random() < 0.3:
            rating_value = random.randint(1, 5)
            comment = f"Review for {restaurant_id}"
            # Edge: RATED row: ~from,~to,~label,rating,comment
            edge_rated = f"{customer_id},{restaurant_id},RATED,{rating_value},{comment}"
            edge_files["RATED"].write(edge_rated + "\n")

        order_counter += 1

# Close all open files.
for f in vertex_files.values():
    f.close()
for f in edge_files.values():
    f.close()

print("Dataset generation complete.")
print("Vertex files are in the 'vertices' folder and edge files are in the 'edges' folder.")
