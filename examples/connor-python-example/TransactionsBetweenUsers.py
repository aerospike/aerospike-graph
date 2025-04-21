import random
import datetime
import traceback
import asyncio

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, Direction
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.traversal import P
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from dash import Dash, html
import dash_cytoscape as cyto
from dash import dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc



HOST = "localhost"
PORT = 8182


def create_cluster():
    return DriverRemoteConnection("ws://localhost:8182/gremlin", "g")


def print_all_elements(g):
    print("=== Vertices ===")
    for v in g.V().limit(10).element_map().toList():
        # v is a dict: {'id': ..., 'label': ..., 'prop1': [...], ...}
        print(v)

    print("\n=== Edges ===")
    for e in g.E().limit(10).element_map().toList():
        # same shape for edges: includes 'inV', 'outV', 'label', etc.
        print(e)


def populate_graph_data(g):
    """Populate the Aerospike Graph with sample data."""
    try:
        print("Connecting to Aerospike Graph Service to populate data...")

        # Check if graph is connected
        if g.inject(0).next() != 0:
            print("Failed to connect to graph instance")
            exit()
        print("Connected to Aerospike Graph Service; Adding Data...")

        print("Adding some users, accounts and transactions")

        # Add Users
        user1 = g.add_v("User").property("userId", "U1").property("name", "Alice").property("age", 30).next()
        user2 = g.add_v("User").property("userId", "U2").property("name", "Bob").property("age", 35).next()
        user3 = g.add_v("User").property("userId", "U3").property("name", "Charlie").property("age", 25).next()
        user4 = g.add_v("User").property("userId", "U4").property("name", "Diana").property("age", 28).next()
        user5 = g.add_v("User").property("userId", "U5").property("name", "Eve").property("age", 32).next()

        # Add Accounts
        account1 = g.add_v("Account").property("accountId", "A1").property("balance", 5000).next()
        account2 = g.add_v("Account").property("accountId", "A2").property("balance", 3000).next()
        account3 = g.add_v("Account").property("accountId", "A3").property("balance", 4000).next()
        account4 = g.add_v("Account").property("accountId", "A4").property("balance", 2000).next()
        account5 = g.add_v("Account").property("accountId", "A5").property("balance", 6000).next()

        # Link Users to Accounts
        g.add_e("owns").from_(user1).to(account1).property("since", "2020").iterate()
        g.add_e("owns").from_(user2).to(account2).property("since", "2021").iterate()
        g.add_e("owns").from_(user3).to(account3).property("since", "2022").iterate()
        g.add_e("owns").from_(user4).to(account4).property("since", "2023").iterate()
        g.add_e("owns").from_(user5).to(account5).property("since", "2024").iterate()

        # Add Transactions
        g.add_e("Transaction") \
            .from_(account1).to(account2) \
            .property("transactionId", "T1") \
            .property("amount", 200) \
            .property("type", "debit") \
            .property("timestamp", convert_timestamp_to_long("2023-01-15")) \
            .iterate()

        g.add_e("Transaction") \
            .from_(account2).to(account1) \
            .property("transactionId", "T2") \
            .property("amount", 150) \
            .property("type", "credit") \
            .property("timestamp", convert_timestamp_to_long("2023-01-16")) \
            .iterate()

        # Add Transactions
        random.seed()
        for i in range(1, 51):
            # Randomly select two accounts to create a transaction
            from_account = g.V().has_label("Account").sample(1).next()
            to_account = g.V().has_label("Account").sample(1).next()
            if not from_account or not to_account:
                print("Error: Not enough Account vertices to create edges")
                continue
            amount = random.randint(1, 1000)

            # Generate a random transaction ID
            transaction_id = f"T{i}"
            type_ = "debit" if random.choice([True, False]) else "credit"
            timestamp = f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            #print(f"Transaction ID: {transaction_id}, Amount: {amount}, Type: {type_}, Timestamp: {timestamp}")

            # Create the transaction edge
            g.add_e("Transaction") \
                .from_(from_account).to(to_account) \
                .property("transactionId", transaction_id) \
                .property("amount", amount) \
                .property("type", type_) \
                .property("timestamp", convert_timestamp_to_long(timestamp)) \
                .iterate()

        print("Data written successfully...")
        #print_all_elements(g)
        print("Data population complete.")
    except Exception as e:
        print("Error populating graph data:", e)
        traceback.print_exc()

def get_graph_elements(g):
    try:
        elements = []
        # Check if graph is connected
        if g.inject(0).next() != 0:
            print("Failed to connect to graph instance")
            exit()
        print("Connected to Aerospike Graph Cluster; Retrieving data...")
        #print elements to check they are here
        #print_all_elements(g)

        # Retrieve vertices
        vertices = g.V().value_map(True).dedup().toList()
        for vertex in vertices:
            # Use T.id to extract the vertex id from the map
            v_id = vertex[T.id]
            # Choose a display label—modify based on your properties:
            display_label = vertex.get('name', vertex.get('userId', vertex.get('accountId', '')))[0]
            node = {
                'data': {
                    'id': str(v_id),
                    'label': display_label
                }
            }
            elements.append(node)

        # Retrieve edges with an explicit projection for source and target IDs
        edges = g.E().project('id', 'source', 'target', 'label') \
            .by(__.id_()) \
            .by(__.out_v().id_()) \
            .by(__.in_v().id_()) \
            .by(__.label()) \
            .dedup() \
            .to_list()

        for edge in edges:
            edge_element = {
                'data': {
                    'id': str(edge['id']),
                    'source': str(edge['source']),
                    'target': str(edge['target']),
                    'label': edge.get('label', '')
                }
            }
            elements.append(edge_element)

        #cluster.close()
        return elements
    except Exception as e:
        print(f"Something went wrong {e}")
        traceback.print_exc()

def all_transactions_by_user(g, user_name):
    #Find all transactions initiated by a specific user
    print("\nQUERY 1: Transactions initiated by " + user_name + ":")
    results =  g.V().has("User", "name", user_name) \
        .out("owns") \
        .outE("Transaction") \
        .as_("transaction") \
        .inV() \
        .values("accountId") \
        .as_("receiver") \
        .select("transaction", "receiver") \
        .by("amount") \
        .by() \
        .toList()
    for result in results:
        print(f"Transaction Amount: {result['transaction']}, Receiver Account ID: {result['receiver']}")

def aggregate_transaction_amounts(g):
    # Query Example 2: Aggregate total transaction amounts for each user
    print("\nQUERY 2: Total transaction amounts initiated by users:")
    results = g.V().hasLabel("Account") \
        .group() \
        .by("accountId") \
        .by(__.outE("Transaction").values("amount").sum_()) \
        .toList()

    for result in results:
        print(result)

def transfers_to_user(g, user_name):
    print("\nQUERY 3: Users who transferred greater than 100 to " + user_name + ":")
    results = g.V().has("User", "name", user_name) \
        .out("owns") \
        .inE("Transaction") \
        .has("amount", P.gte(100)) \
        .outV() \
        .in_("owns") \
        .valueMap("name") \
        .toList()

    for result in results:
        print(f"User: {result}")

def list_user_properties(g, user_name):
    # Query Example 4: List all properties of a specific user
    print("\nQUERY 4: Properties of " + user_name + ":")
    user_properties = g.V().has("User", "name", user_name).valueMap().next()

    # Iterate and print properties
    for key, value in user_properties.items():
        print(f"{key}: {value[0]}")


def transactions_between_users(g, user1, user2):
    person_1_id = g.V() \
        .has('User','name',user1) \
        .id_() \
        .next()
    person_2_id = g.V() \
        .has('User','name', user2) \
        .id_() \
        .next()
    results = g.V(person_1_id).outE().otherV().bothE().otherV().inE().otherV().hasId(person_2_id).path().by(T.id).toList()

    vertex_ids = set()
    edge_ids   = set()
    for path in results:
        elems = list(path)
        vertex_ids.update(elems[::2])
        edge_ids.update(elems[1::2])
    vertex_ids = list(vertex_ids)
    edge_ids   = list(edge_ids)

    # Retrieve vertices and edges using the collected IDs
    vertex_data = g.V(vertex_ids).valueMap(True).toList()
    edge_data   = g.E(edge_ids).elementMap().toList()

    elements = []
    for vertex in vertex_data:
        # 1) extract the id from the dict
        v_id = vertex[T.id]
        v_label = vertex[T.label]
        if v_label == 'Account':
            # accountId was stored as a single‑element list
            disp = vertex['accountId'][0]
        elif v_label == 'User':
            # users have both 'userId' and 'name' properties
            # choose whichever you prefer—here we'll show the name
            disp = vertex['name'][0]
        else:
            # fallback to the raw id
            disp = str(v_id)

        node = {
                    'data': {
                        'id':    str(v_id),
                        'type': v_label,
                        'label': disp,
                    }
                }
        elements.append(node)

    for edge in edge_data:
        e_id = edge[T.id]
        e_label = edge[T.label]
        out_dict = edge[Direction.OUT]
        src_id   = out_dict[T.id]
        in_dict  = edge[Direction.IN]
        tgt_id   = in_dict[T.id]
        label = ""
        if(e_label == "Transaction"):
            label = "T->$" + str(edge['amount'])
        else:
            label = e_label
        edge_element = {
            'data': {
                'id': str(e_id),
                'source': str(src_id),
                'target': str(tgt_id),
                'type': e_label,
                'label': label,
            }
        }
        elements.append(edge_element)
    return elements


def set_frontend(graph_elements):
    # Set up the Dash application
    app = Dash(__name__)
    @app.callback(
        Output('cytoscape-graph', 'elements'),
        Input('refresh-btn', 'n_clicks'),
        State('user1-dropdown', 'value'),
        State('user2-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_graph(n_clicks, user1, user2):
        # Get the graph elements based on the selected users
        elements = transactions_between_users(g, user1, user2)
        return elements

    USER_OPTIONS = [
        {"label": "Alice",   "value": "Alice"},
        {"label": "Bob",     "value": "Bob"},
        {"label": "Charlie", "value": "Charlie"},
        {"label": "Diana",   "value": "Diana"},
        {"label": "Eve",     "value": "Eve"},
    ]
    app.layout = html.Div([
        # ── HEADER BAR ─────────────────────────────────────────────────────────
        html.Div([
            html.H2("Aerospike Graph", style={'margin': '0 20px 0 20px',
                                              'fontFamily': '"Roboto", sans-serif',
                                              'fontWeight': 'bold'}),
            html.H4("Transactions Between Users", style={'margin': '0 20px 0 20px',
                                              'fontFamily': '"Roboto", sans-serif'}),

            # select first user
            dcc.Dropdown(
                id="user1-dropdown",
                options=USER_OPTIONS,
                value="Alice",
                clearable=False,
                style={'width': '150px', 'marginRight': '10px'}
            ),

            # select second user
            dcc.Dropdown(
                id="user2-dropdown",
                options=USER_OPTIONS,
                value="Bob",
                clearable=False,
                style={'width': '150px', 'marginRight': '20px'}
            ),

            # refresh button
            dbc.Button("Refresh Graph", id="refresh-btn", color="primary")
        ],
            style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '10px 20px',
                'backgroundColor': '#f8f9fa',
                'borderBottom': '1px solid #ddd'
            }),

        # ── GRAPH ──────────────────────────────────────────────────────────────
        cyto.Cytoscape(
            id='cytoscape-graph',
            elements=graph_elements,
            style={'width': '100%', 'height': '80vh'},
            layout={'name': 'cose'},
            stylesheet=[
                {
                    'selector': 'node',
                    'style': {
                        'label': 'data(label)',
                        'width': '40px',
                        'height': '40px',
                        'background-color': '#0074D9',
                        'color': '#ffffff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px'
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        'label': 'data(label)',
                        'font-size': '8px',
                        'line-color': '#7FDBFF',
                        'target-arrow-color': '#7FDBFF',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'text-rotation': 'autorotate',
                        'text-margin-y': '-4px'
                    }
                }
            ]
        )
    ])

    return app
    
    
def convert_timestamp_to_long(date):
    formatter = "%Y-%m-%d"
    local_date = datetime.datetime.strptime(date, formatter)
    return int(local_date.replace(tzinfo=datetime.timezone.utc).timestamp())


if __name__ == '__main__':
    try:
        print("Closing Connection...")
        cluster = create_cluster()
        g = traversal().with_remote(cluster)
        populate_graph_data(g)
        # Then, start the Dash web server

        #all_transactions_by_user(g, "Alice")
        #aggregate_transaction_amounts(g)
        #transfers_to_user(g, "Alice")
        #list_user_properties(g, "Bob")

        #get graph elements, then if its not empty render the graph
        #elements = get_graph_elements(g)
        elements = transactions_between_users(g, "Alice", "Bob")
        if not elements:
            print("No graph elements found. Exiting.")
            exit()
        print("Starting Dash web server...")
        app = set_frontend(elements)
        app.run(debug=True)

        #Clean up
        print("Dropping Dataset.")
        g.V().drop().iterate()
        if cluster:
            try:
                print("Closing Connection...")
                cluster.close()
            except Exception as e:
                print(f"Failed to Close Connection: {e}")

    except Exception as e:
        print(f"Something went wrong {e}")
        traceback.print_exc()

