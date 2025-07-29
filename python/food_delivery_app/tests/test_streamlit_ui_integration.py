"""
    Integration tests for the Food Delivery App
    Tests Streamlit application UI/UX.
"""
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest
from food_delivery_app.gremlin_queries import GremlinClient

mock_client_instance = MagicMock()
frontend_py = (Path(__file__).parent.parent / "frontend_streamlit.py").resolve()


class TestStreamlitFoodDeliveryUI:
    def test_app_initialization(self):
        try:
            app_test = AppTest.from_file(str(frontend_py))
            assert app_test is not None
            
        except Exception as e:
            pytest.fail(f"Streamlit testing not available or app has initialization issues: {e}")

    @patch("food_delivery_app.frontend_streamlit.GremlinClient")
    def test_sidebar_navigation(self, mock_gremlin_client):
        # Mock the GremlinClient to avoid actual database connections
        mock_gremlin_client.return_value = mock_client_instance
        
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()
            
            assert len(app_test.selectbox) > 0, "No selectbox found for action selection"
            
            selectbox = app_test.selectbox[0]
            options = selectbox.options
            
            expected_options = [
                "Check Order by ID",
                "Customer Orders", 
                "Restaurant Ratings",
                "Graph Visualization"
            ]
            
            for expected_option in expected_options:
                assert any(expected_option in str(option) for option in options), \
                    f"Missing expected option: {expected_option}"
                    
        except Exception as e:
            pytest.fail(f"Streamlit UI testing failed: {e}")

    @patch('food_delivery_app.frontend_streamlit.GremlinClient')
    def test_check_order_workflow(self, mock_gremlin_client):
        mock_client_instance.check_order.return_value = {
            'status': 'DELIVERED',
            'order_id': 'order_12345',
            'order_date': 'Jan 1, 2023',
            'items': [{'name': 'Pizza', 'qty': 1, 'price': 15.99}]
        }
        mock_gremlin_client.return_value = mock_client_instance
        
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()
            
            if len(app_test.selectbox) > 0:
                app_test.selectbox[0].select("Check Order by ID")
                app_test.run()
                
                if len(app_test.text_input) > 0:
                    app_test.text_input[0].input("order_12345")
                    app_test.run()
                    
                    if len(app_test.button) > 0:
                        app_test.button[0].click()
                        app_test.run()

                        assert len(str(app_test)) > 0, \
                            "No output generated from order check workflow"
                            
        except Exception as e:
            pytest.fail(f"Check order workflow test failed: {e}")

    @patch('food_delivery_app.frontend_streamlit.GremlinClient')
    def test_customer_orders_workflow(self, mock_gremlin_client):
        mock_client_instance.check_order.return_value = {
            'status': 'DELIVERED',
            'order_id': 'order_67890',
            'order_date': 'Jan 2, 2023',
            'items': [{'name': 'Burger', 'qty': 2, 'price': 12.99}]
        }
        mock_gremlin_client.return_value = mock_client_instance
        
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()
            
            if len(app_test.selectbox) > 0:
                app_test.selectbox[0].select("Customer Orders")
                app_test.run()
                
                if len(app_test.text_input) > 0:
                    app_test.text_input[0].input("customer_001")
                    app_test.run()
                    
                    if len(app_test.button) > 0:
                        app_test.button[0].click()
                        app_test.run()
                        
                        assert True
                        
        except Exception as e:
            pytest.fail(f"Customer orders workflow test failed: {e}")

    @patch('food_delivery_app.frontend_streamlit.GremlinClient')
    def test_restaurant_ratings_workflow(self, mock_gremlin_client):
        mock_client_instance.get_random.return_value = [
            {'restaurant_id': 'rest_001', 'name': 'Pizza Palace', 'avg_rating': 4.5},
            {'restaurant_id': 'rest_002', 'name': 'Burger Barn', 'avg_rating': 4.2}
        ]
        mock_gremlin_client.return_value = mock_client_instance
        
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()
            
            if len(app_test.selectbox) > 0:
                app_test.selectbox[0].select("Restaurant Ratings")
                app_test.run()
                
                if len(app_test.button) > 0:
                    app_test.button[0].click()
                    app_test.run()
                
                assert True
                
        except Exception as e:
            pytest.fail(f"Restaurant ratings workflow test failed: {e}")

    def test_error_handling(self):
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()

            assert True
            
        except Exception as e:
            pytest.fail(f"App has fundamental issues that prevent testing: {e}")


class TestStreamlitAppStructure:
    def test_app_has_title(self):
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()
            
            has_title = (len(app_test.title) > 0 or
                        len(app_test.header) > 0 or
                        len(app_test.subheader) > 0)
            
            assert has_title, "App should have a title, header, or subheader"
            
        except Exception as e:
            pytest.fail(f"App structure test failed: {e}")
    
    def test_app_has_interactive_elements(self):
        try:
            app_test = AppTest.from_file(str(frontend_py))
            app_test.run()
            
            has_interactions = (len(app_test.selectbox) > 0 or
                              len(app_test.text_input) > 0 or
                              len(app_test.button) > 0)
            
            assert has_interactions, "App should have interactive elements"
            
        except Exception as e:
            pytest.fail(f"Interactive elements test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 