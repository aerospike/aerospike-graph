"""
    Integration tests for transactions_between_users.py
    Tests data population, Dash app Endpoints, Gremlin queries, and results validation
"""
import pytest
from unittest.mock import patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T

@pytest.fixture
def populated_graph(clean_graph_for_individual_test):
    g = clean_graph_for_individual_test
    
    user1 = g.add_v("User").property("userId", "U1").property("name", "Alice").property("age", 30).next()
    user2 = g.add_v("User").property("userId", "U2").property("name", "Bob").property("age", 25).next()
    user3 = g.add_v("User").property("userId", "U3").property("name", "Charlie").property("age", 35).next()
    
    account1 = g.add_v("Account").property("accountId", "A1").property("balance", 1000).next()
    account2 = g.add_v("Account").property("accountId", "A2").property("balance", 500).next()
    account3 = g.add_v("Account").property("accountId", "A3").property("balance", 750).next()
    
    g.add_e("owns").from_(user1).to(account1).next()
    g.add_e("owns").from_(user2).to(account2).next()
    g.add_e("owns").from_(user3).to(account3).next()

    g.add_e("Transaction").from_(account1).to(account2).property("amount", 100).property("timestamp", 1609459200).next()
    g.add_e("Transaction").from_(account3).to(account1).property("amount", 75).property("timestamp", 1609462800).next()
    
    return {
        'g': g,
        'users': [user1, user2, user3],
        'accounts': [account1, account2, account3]
    }


class TestTransactionsBetweenUsersIntegration:

    def test_gremlin_query_execution(self, populated_graph):
        g = populated_graph['g']
        
        user_count = g.V().has_label("User").count().next()
        assert user_count == 3
        
        alice = g.V().has("User", "name", "Alice").next()
        assert alice is not None
        
        alice_account = g.V().has("User", "name", "Alice").out("owns").next()
        assert alice_account is not None
    
    def test_transaction_queries(self, populated_graph):
        g = populated_graph['g']
        
        transactions = (g.V()
                       .has("User", "name", "Alice")
                       .out("owns")
                       .out_e("Transaction")
                       .where(__.in_v().in_("owns").has("name", "Bob"))
                       .element_map()
                       .to_list())
        
        assert len(transactions) == 1
        assert transactions[0]['amount'] == 100
        
        all_transactions = (g.V()
                           .has("User", "name", "Alice")
                           .out("owns")
                           .both_e("Transaction")
                           .where(__.other_v().in_("owns").has("name", "Bob"))
                           .element_map()
                           .to_list())
        
        assert len(all_transactions) == 1
    
    def test_gremlin_query_user_network(self, populated_graph):
        g = populated_graph['g']
        
        connected_users = (g.V()
                          .has("User", "name", "Alice")
                          .out("owns")
                          .both_e("Transaction")
                          .other_v()
                          .in_("owns")
                          .values("name")
                          .dedup()
                          .to_list())
        
        assert "Bob" in connected_users
        assert "Charlie" in connected_users
        assert len(connected_users) == 2
    
    def test_transaction_amount_aggregation(self, populated_graph):
        g = populated_graph['g']
        
        outgoing_amounts = (g.V()
                           .has("User", "name", "Alice")
                           .out("owns")
                           .out_e("Transaction")
                           .values("amount")
                           .to_list())
        
        total_out = sum(outgoing_amounts) if outgoing_amounts else 0
        assert total_out == 100
        
        incoming_amounts = (g.V()
                           .has("User", "name", "Alice")
                           .out("owns")
                           .in_e("Transaction")
                           .values("amount")
                           .to_list())
        
        total_in = sum(incoming_amounts) if incoming_amounts else 0
        assert total_in == 75
    
    def test_dash_app_data_structure(self, populated_graph):
        g = populated_graph['g']
        
        nodes_query = (g.V()
                      .has_label("User")
                      .project("id", "label", "type")
                      .by(T.id)
                      .by("name")
                      .by(__.constant("user"))
                      .to_list())
        
        assert len(nodes_query) == 3
        
        alice_node = next((n for n in nodes_query if n["label"] == "Alice"), None)
        assert alice_node is not None
        assert alice_node["type"] == "user"
        assert "id" in alice_node


class TestDashAppEndpoints:

    def test_dash_app_imports_and_structure(self):
        try:
            import transactions_between_users as tbu
            
            assert hasattr(tbu, 'populate_graph_data')
            assert hasattr(tbu, 'print_all_elements')
            assert callable(tbu.populate_graph_data)
            assert callable(tbu.print_all_elements)
            
            assert hasattr(tbu, 'Dash')  # Dash class is imported

            
        except ImportError as e:
            pytest.fail(f"Failed to import transactions_between_users module: {e}")
    
    @patch('transactions_between_users.HOST', 'localhost')
    @patch('transactions_between_users.PORT', 8182)
    def test_connection_parameters(self):
        import transactions_between_users as tbu
        
        assert tbu.HOST == 'localhost'
        assert tbu.PORT == 8182
    
    def test_graph_populate_function_with_mock_connection(self, g, clean_graph):
        import transactions_between_users as tbu
        
        tbu.populate_graph_data(g)
        
        user_count = g.V().has_label("User").count().next()
        account_count = g.V().has_label("Account").count().next()
        transaction_count = g.E().has_label("Transaction").count().next()
        
        assert user_count >= 5
        assert account_count >= 5
        assert transaction_count >= 1
        
        alice_exists = g.V().has("User", "name", "Alice").has_next()
        bob_exists = g.V().has("User", "name", "Bob").has_next()
        
        assert alice_exists
        assert bob_exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 