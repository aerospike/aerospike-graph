# frontend_streamlit.py
import streamlit as st
import graphviz
from gremlin_python.process.traversal import T
from gremlin_queries import GremlinClient

client = GremlinClient()

st.set_page_config(page_title="Swimato Frontend")
st.title("Swimato Local App")

st.markdown(
    """
    <style>
      .stAppDeployButton { visibility: hidden !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
# Sidebar navigation
command = st.sidebar.selectbox("Select Action", [
    "Check Order by ID", "Check Order by Customer", "Assign Driver",
    "Restaurant Ratings", "Get Random", "Customer Orders", "Graph Visualization"
])
if command == "Check Order by ID":
    order_id = st.text_input("Order ID")
    if st.button("Run"):
        res = client.check_order('order', order_id)
        if res:
            st.write(f"**Status:** {res['status']}")
            st.subheader("Items:")
            for item in res['items']:
                st.write(f"- {item['item']}: {item['qty']} x ${item['price']}")
        else:
            st.error("Order not found.")

elif command == "Check Order by Customer":
    cust_id = st.text_input("Customer ID")
    if st.button("Run"):
        res = client.check_order('customer', cust_id)
        if res:
            st.write(f"**Order ID:** {res['order_id']}")
            st.write(f"**Status:** {res['status']}")
            st.write(f"**Date:** {res['order_date']}")
        else:
            st.error("No orders found for this customer.")

elif command == "Assign Driver":
    order_id = st.text_input("Order ID")
    driver_id = st.text_input("Driver ID")
    if st.button("Assign"):
        try:
            client.assign_driver(order_id, driver_id)
            st.success(f"Driver {driver_id} assigned to order {order_id}.")
        except Exception as e:
            st.error(f"Error: {e}")

elif command == "Restaurant Ratings":
    rest_id = st.text_input("Restaurant ID")
    limit = st.number_input("Max Ratings", min_value=1, max_value=50, value=10)
    if st.button("Fetch"):
        ratings = client.get_restaurant_ratings(rest_id, limit)
        if ratings:
            for r in ratings:
                st.write(f"**Rating:** {r.get('rating', [None])[0]}")
                st.write(f"Comment: {r.get('comment', [''])[0]}")
                st.write("---")
        else:
            st.info("No ratings found.")

elif command == "Get Random":
    type_ = st.selectbox("Type", ['customers', 'orders', 'restaurants', 'drivers'])
    count = st.number_input("Count", min_value=1, max_value=100, value=5)
    if st.button("Fetch"):
        data = client.get_random(type_, count)
        st.write(data)

elif command == "Customer Orders":
    cust_id = st.text_input("Customer ID")
    limit = st.number_input("Limit", min_value=1, max_value=20, value=5)
    if st.button("Fetch"):
        orders = client.get_customer_orders(cust_id, limit)
        if orders:
            st.subheader("Recent Orders")
            for o in orders:
                st.write(f"- ID: {o['order_id']}, Status: {o['status']}, Date: {o['order_date']}")
        else:
            st.info("No orders found.")

elif command == "Graph Visualization":
    entity_type = st.selectbox("Type", ['customer', 'order', 'restaurant', 'driver'])
    depth = st.selectbox("Depth", [1, 2, 3, 4, 5])
    object_id = st.text_input("ID")
    if st.button("Run"):
        data = client.get_subgraph(object_id, entity_type, depth)
        if data:
            dot = graphviz.Digraph()
            for v in data["vertices"]:
                dot.node(str(v[T.id]), v[T.label])
            for e in data["edges"]:
                dot.edge(str(e.get("out")), str(e.get("in")), label=e.get("label"))
            st.graphviz_chart(dot, use_container_width=True)
        else:
            st.error("vertex cannot be found")

# To run:
# pip install streamlit gremlinpython
# streamlit run frontend_streamlit.py
