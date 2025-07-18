# frontend_streamlit.py
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from gremlin_python.process.traversal import T
from gremlin_queries import GremlinClient

client = GremlinClient()
def pick_random(key: str, type_: str):
    data = client.get_random(type_, 1)
    if not data:
        st.error(f"No {type_} returned")
        return
    first = data[0]
    if isinstance(first, str):
        st.session_state[key] = first


st.set_page_config(page_title="Food Delivery App")
st.title("Food Delivery App")

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
    col1, col2 = st.columns([3, 1])

    with col1:
        order_id = st.text_input("Order ID", key="order_id")
    with col2:
        st.button("🔀 Fetch Random Order", on_click=pick_random, args=("order_id","orders"))
    if st.button("Run"):
        res = client.check_order('order', st.session_state.order_id)
        if res:
            st.write(f"**Status:** {res['status']}")
            st.subheader("Items:")
            for item in res['items']:
                st.write(f"- {item['item']}: {item['qty']} x ${item['price']}")
        else:
            st.error("Order not found.")

elif command == "Check Order by Customer":
    col1, col2 = st.columns([3, 1])

    with col1:
        cust_id = st.text_input("Customer ID", key="customer_id")
    with col2:
        st.button("🔀 Fetch Random Customer", on_click=pick_random, args=("customer_id","customers"))
    if st.button("Run"):
        res = client.check_order('customer', st.session_state.customer_id)
        if res:
            st.write(f"**Order ID:** {res['order_id']}")
            st.write(f"**Status:** {res['status']}")
            st.write(f"**Date:** {res['order_date']}")
        else:
            st.error("No orders found for this customer.")

elif command == "Assign Driver":
    col1, col2 = st.columns([3, 1])
    col3, col4 = st.columns([3, 1])
    with col1:
        order_id = st.text_input("Order ID", key="order_id")
    with col2:
        st.button("🔀 Fetch Random Order", on_click=pick_random, args=("order_id","orders"))

    with col3:
        driver_id = st.text_input("Driver ID", key="driver_id")
    with col4:
        st.button("🔀 Fetch Random Driver", on_click=pick_random, args=("driver_id","drivers"))

    if st.button("Assign"):
        try:
            client.assign_driver(order_id, st.session_state.driver_id)
            st.success(f"Driver {driver_id} assigned to order {order_id}.")
        except Exception as e:
            st.error(f"Error: {e}")

elif command == "Restaurant Ratings":
    col1, col2 = st.columns([3, 1])

    with col1:
        rest_id = st.text_input("Restaurant ID", key="restaurant_id")
    with col2:
        st.button("🔀 Fetch Random Restaurant", on_click=pick_random, args=("restaurant_id","restaurants"))
    limit = st.number_input("Max Ratings", min_value=1, max_value=50, value=10, key="max_ratings")
    if st.button("Fetch"):
        ratings = client.get_restaurant_ratings(st.session_state.restaurant_id, st.session_state.max_ratings)
        if ratings:
            for r in ratings:
                st.write(f"**Rating:** {r.get('rating', [None])[0]}")
                st.write(f"Comment: {r.get('comment')}")
                st.write("---")
        else:
            st.info("No ratings found.")

elif command == "Get Random":
    type_ = st.selectbox("Type", ['customers', 'orders', 'restaurants', 'drivers'])
    count = st.number_input("Count", min_value=1, max_value=100, value=5, key="count")
    if st.button("Fetch"):
        data = client.get_random(type_, st.session_state.count)
        st.write(data)

elif command == "Customer Orders":
    col1, col2 = st.columns([3, 1])

    with col1:
        cust_id = st.text_input("Customer ID", key="customer_id")
    with col2:
        st.button("🔀 Fetch Random Customer", on_click=pick_random, args=("customer_id","customers"))
    limit = st.number_input("Limit", min_value=1, max_value=20, value=5, key="limit")
    if st.button("Fetch"):
        orders = client.get_customer_orders(st.session_state.customer_id, st.session_state.limit)
        if orders:
            st.subheader("Recent Orders")
            for o in orders:
                st.write(f"- ID: {o['order_id']}, Status: {o['status']}, Date: {o['order_date']}")
        else:
            st.info("No orders found.")

elif command == "Graph Visualization":
    if 'graph_data' not in st.session_state:
        st.session_state['graph_data'] = []

    entity_type = st.selectbox("Type", ['customers', 'orders', 'restaurants', 'drivers'], key="entity_type", index=0)
    depth = st.selectbox("Depth", [1, 2, 3, 4, 5], key="depth", index=2)

    col1, col2 = st.columns([3, 1])
    with col1:
        object_id = st.text_input("ID", key="object_id")
    with col2:
        st.button("🔀 Fetch Random", on_click=pick_random, args=("object_id", entity_type))

    if st.button("Run"):
        st.session_state.graph_data = client.get_subgraph(st.session_state.object_id, entity_type, st.session_state.depth)
    if st.session_state['graph_data']  and len(st.session_state['graph_data']['vertices']) > 0:
        data = st.session_state['graph_data']
        nodes = [
            Node(id=str(v[T.id]), label=v[T.label], tooltip=str(v))
            for v in data["vertices"]
        ]
        edges = [
            Edge(source=str(e.get("out")), target=str(e.get("in")), label=e.get("label"))
            for e in data["edges"]
        ]
        config = Config(
            width="100%",
            height=600,
            directed=True,
            groups={ #This will be used to add icons for nodes based on label
                "CustomerProfile": {
                    "shape": "icon",
                    "icon": {
                        "face": "FontAwesome",
                        "code": "\f007",
                        "size": 50
                    }
                },
                "Restaurant": {
                    "shape": "icon",
                    "icon": {
                        "face": "FontAwesome",
                        "code": "\f2e7",
                        "size": 50
                    }
                },
                "FoodOrder": {
                    "shape": "icon",
                    "icon": {
                        "face": "FontAwesome",
                        "code": "\e4c6",
                        "size": 50
                    }
                },
                "Driver": {
                    "shape": "icon",
                    "icon": {
                        "face": "FontAwesome",
                        "code": "\ff5e4",
                        "size": 50
                    }
                },
            },
            interaction={
                "hover": True,
                "hoverConnectedEdges": True,
                "tooltipDelay": 200
            },
            nodes={
                "shape": "dot",
                "size": 16,
                "font":
                    { "size": 14 }
            },
            edges={ "smooth": False },
            physics=True,
        )

        agraph(nodes=nodes, edges=edges, config=config)
    elif st.session_state['graph_data'] and len(st.session_state['graph_data']['vertices']) == 0:
        st.error("vertex cannot be found")
    else:
        st.session_state['graph_data'] = []
