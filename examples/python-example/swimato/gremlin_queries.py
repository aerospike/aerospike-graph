# gremlin_queries.py
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, Order
import time
from datetime import datetime


class GremlinClient:
    def __init__(self, url: str = 'ws://localhost:8182/gremlin', traversal_source: str = 'g'):
        self.connection = DriverRemoteConnection(url, traversal_source)
        self.g = traversal().with_remote(self.connection)

    def close(self):
        self.connection.close()

    def check_order(self, type_: str, id_: str):
        if type_ == 'order':
            order = self.g.V(id_).value_map().to_list()
            items = (
                self.g.V(id_)
                .out_e("CONTAINS")
                .project("item", "qty", "price")
                .by(__.in_v().values("name"))
                .by(__.values("qty"))
                .by(__.in_v().values("price"))
                .to_list()
            )
            if order:
                status = order[0].get('status', ['Unknown'])[0]
                return {'status': status, 'items': items}
            return None
        elif type_ == 'customer':
            order = (
                self.g.V(id_)
                .out("PLACED")
                .order()
                .by("order_date", Order.desc)
                .value_map()
                .to_list()
            )
            if order:
                ts = int(str(order[0].get('order_date', [0])[0]), 10)
                date = datetime.fromtimestamp(ts / 1000)
                return {
                    'status': order[0].get('status', ['Unknown'])[0],
                    'order_id': order[0].get('order_id', ['Unknown'])[0],
                    'order_date': date
                }
            return None
        else:
            raise ValueError("Type must be 'order' or 'customer'")

    def assign_driver(self, order_id: str, driver_id: str) -> bool:
        self.g.V(order_id).as_('order') \
            .V(driver_id) \
            .add_e("DELIVERED_BY") \
            .from_('order') \
            .property("assigned_date", int(time.time())) \
            .iterate()
        self.g.V(order_id).property("status", "ASSIGNED_TO_DRIVER").iterate()
        return True

    def get_restaurant_ratings(self, restaurant_id: str, limit: int = 10):
        ratings = (
            self.g.V(restaurant_id)
            .has_label("Restaurant")
            .in_e("RATED")
            .limit(limit)
            .value_map("rating", "comment")
            .to_list()
        )
        return ratings

    def get_random(self, type_: str, count: int):
        label_map = {
            'customers': 'CustomerProfile',
            'orders': 'FoodOrder',
            'restaurants': 'Restaurant',
            'drivers': 'Driver'
        }
        label = label_map.get(type_)
        if not label:
            raise ValueError("in_valid type")
        return self.g.V().has_label(label).sample(count).id_().to_list()

    def get_customer_orders(self, customer_id: str, limit: int = 5):
        orders = (
            self.g.V(customer_id)
            .has_label("CustomerProfile")
            .out("PLACED")
            .order()
            .by("order_date", Order.desc)
            .limit(limit)
            .value_map()
            .to_list()
        )
        result = []
        for o in orders:
            ts = int(str(o.get('order_date', [0])[0]), 10)
            date = datetime.fromtimestamp(ts / 1000)
            result.append({
                'order_id': o.get('order_id', ['Unknown'])[0],
                'status': o.get('status', ['Unknown'])[0],
                'order_date': date
            })
        return result

    def get_subgraph(self, object_id, entity_type, depth):
        # customer_078124
        # restaurant_000417
        # driver_000242
        # order_00217003

        max_per_hop: int = 5
        max_paths: int = 150
        label = ""
        if entity_type == "customer":
            label = "CustomerProfile"
        elif entity_type == "restaurant":
            label = "Restaurant"
        elif entity_type == "order":
            label = "FoodOrder"
        else:
            label = "Driver"

        raw_paths = (
            self.g.V(object_id)
            .has_label(label)
            .repeat(
                __.local(__.both_e().other_v().limit(max_per_hop))  # cap per-vertex
                .simplePath()
            )
            .times(depth)
            .path()
            .by(T.id)
            .limit(max_paths)  # global cap
            .to_list()
        )

        vertex_ids = set()
        edge_ids = set()
        for p in raw_paths:
            for idx, elem_id in enumerate(p):
                if idx % 2 == 0:
                    vertex_ids.add(elem_id)
                else:
                    edge_ids.add(elem_id)

        vertices = []
        if vertex_ids:
            vertices = (
                self.g.V(*vertex_ids)
                .element_map()
                .to_list()
            )

        edges = []
        if edge_ids:
            edges = (
                self.g.E(*edge_ids)
                .project('id', 'label', 'out', 'in', 'properties')
                .by(T.id)
                .by(T.label)
                .by(__.out_v().id_())
                .by(__.in_v().id_())
                .by(__.value_map())
                .to_list()
            )
        return {'vertices': vertices, 'edges': edges}
