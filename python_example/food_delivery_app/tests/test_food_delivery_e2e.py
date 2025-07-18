"""
End-to-end tests for food delivery application.
Tests Gremlin query functionality and data operations.
"""
import pytest
import sys
import os
from gremlin_queries import GremlinClient
import food_delivery_datasetgen

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@pytest.fixture(scope="session")
def populated_food_delivery_graph(g):
    g.V().drop().iterate()
    
    food_delivery_datasetgen.generate_dataset(
        n_customers=5,
        n_restaurants=3, 
        n_drivers=3,
        min_orders_per_customer=1,
        max_orders_per_customer=2
    )
    
    test_data = {
        'customers': [],
        'restaurants': [], 
        'drivers': [],
        'menu_items': [],
        'orders': [],
        'delivery_addresses': []
    }
    
    for i in range(1, 6):
        customer_id = f"customer_{i:06d}"
        g.add_v("CustomerProfile").property("customer_id", customer_id)\
            .property("name", f"Customer {i}").property("email", f"customer{i}@example.com").iterate()
        test_data['customers'].append({'customer_id': customer_id})
    
    for i in range(1, 4):
        restaurant_id = f"restaurant_{i:06d}"
        g.add_v("Restaurant").property("restaurant_id", restaurant_id)\
            .property("name", f"Restaurant {i}").property("location", f"Location {i}").iterate()
        test_data['restaurants'].append({'restaurant_id': restaurant_id})
        
        for j in range(1, 4):
            menu_item_id = f"menuItem_{restaurant_id}_{j:02d}"
            g.add_v("MenuItem").property("menu_item_id", menu_item_id)\
                .property("name", f"Menu Item {j}").property("price", 10.99).iterate()
            test_data['menu_items'].append({'menu_item_id': menu_item_id})
    
    for i in range(1, 6):
        order_id = f"order_{i:08d}"
        g.add_v("FoodOrder").property("order_id", order_id)\
            .property("order_date", 1600000000).property("status", "DELIVERED").iterate()
        test_data['orders'].append({'order_id': order_id})
    
    return test_data


class TestFoodDeliveryGremlinQueries:
    def test_gremlin_client_connection(self, clean_graph_for_individual_test):
        client = GremlinClient()
        
        try:
            result = client.g.inject(0).next()
            assert result == 0
            
            count = client.g.V().count().next()
            assert isinstance(count, int)
            
        finally:
            client.close()
    
    def test_check_order_query(self, g, populated_food_delivery_graph):
        test_orders = populated_food_delivery_graph['orders']
        assert len(test_orders) > 0, "No test orders available"
        
        test_order_id = test_orders[0]['order_id']
        
        order_vertices = g.V().has("FoodOrder", "order_id", test_order_id).value_map().to_list()
        
        assert len(order_vertices) == 1
        order = order_vertices[0]
        assert order['order_id'][0] == test_order_id
        assert order['status'][0] == "DELIVERED"
    
    def test_restaurant_data_queries(self, g, populated_food_delivery_graph):
        restaurants = g.V().has_label("Restaurant").value_map().to_list()
        assert len(restaurants) == 3
        
        for restaurant in restaurants:
            assert 'restaurant_id' in restaurant
            assert 'name' in restaurant
            assert 'location' in restaurant
    
    def test_customer_orders_query(self, g, populated_food_delivery_graph):
        test_customers = populated_food_delivery_graph['customers']
        assert len(test_customers) > 0, "No test customers available"
        
        test_customer_id = test_customers[0]['customer_id']
        
        customer_vertices = g.V().has("CustomerProfile", "customer_id", test_customer_id).value_map().to_list()
        
        assert len(customer_vertices) == 1
        customer = customer_vertices[0]
        assert customer['customer_id'][0] == test_customer_id
        assert 'name' in customer
        assert 'email' in customer
    
    def test_graph_data_structure(self, g, populated_food_delivery_graph):
        customer_count = g.V().has_label("CustomerProfile").count().next()
        restaurant_count = g.V().has_label("Restaurant").count().next()
        order_count = g.V().has_label("FoodOrder").count().next()
        menu_item_count = g.V().has_label("MenuItem").count().next()
        
        assert customer_count == 5
        assert restaurant_count == 3  
        assert order_count == 5
        assert menu_item_count == 9
        
        test_data = populated_food_delivery_graph
        assert len(test_data['customers']) == customer_count
        assert len(test_data['restaurants']) == restaurant_count
        assert len(test_data['orders']) == order_count
        assert len(test_data['menu_items']) == menu_item_count

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 