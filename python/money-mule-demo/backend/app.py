from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from gremlin_python.structure.graph import Graph
from gremlin_python.process.traversal import P, T, Order
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from Structured_Mule_Activity import detect_structured_mule_activity
from FraudScenarioDetector import FraudScenarioDetector
import warnings
import asyncio
import logging

# Suppress all aiohttp and asyncio warnings to prevent event loop closed errors
warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="aiohttp")
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")

# Set asyncio to not warn about unclosed event loops
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# Reduce logging level for aiohttp to prevent warnings
logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

def get_graph_connection():
    """Establishes connection to Aerospike Graph with better error handling"""
    try:
        connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        return traversal().with_remote(connection)
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def safe_close_connection(g):
    """Safely close graph connection with error suppression"""
    try:
        if g and hasattr(g, 'close'):
            g.close()
    except Exception:
        # Suppress all connection close errors
        pass

def get_debit_transactions(bank_account, g):
    """Fetches all outgoing (debit) transactions for a given bank account."""
    return g.V(bank_account).outE("transaction").order().by("datetime", Order.desc).valueMap(True).toList()

def get_credit_transactions(bank_account, g):
    """Fetches all incoming (credit) transactions for a given bank account."""
    return g.V(bank_account).inE("transaction").order().by("datetime").valueMap(True).toList()

def detect_mule_patterns(bank_account, g):
    """
    Analyzes transaction patterns for a given account to detect mule activity.
    Returns details about suspicious patterns found.
    """
    debit_transactions = get_debit_transactions(bank_account, g)
    credit_transactions = get_credit_transactions(bank_account, g)
    patterns = []
    
    # Pattern 1: Multiple Credits followed by Single Debit (Funnel Pattern)
    for debit in debit_transactions:
        debit_amount = debit.get('amount', 0)
        relevant_credits = {}
        time_window_start = debit.get('datetime', 0) - (24*60*60*1000)
        credit_total = 0
        
        for t in credit_transactions:
            if time_window_start <= t.get('datetime', 0) < debit.get('datetime', 0):
                credit_total += t.get('amount', 0)
                relevant_credits[t.get('datetime', 0)] = t
                
                if len(relevant_credits) > 2 and 0.9 * debit_amount <= credit_total <= debit_amount:
                    patterns.append({
                        "type": "funnel",
                        "description": "Multiple small deposits followed by large withdrawal",
                        "debit_amount": debit_amount,
                        "credit_total": credit_total,
                        "credit_count": len(relevant_credits),
                        "timeframe": "24 hours",
                        "transactions": {
                            "debit": debit,
                            "credits": list(relevant_credits.values())
                        }
                    })
    
    return patterns

@app.route('/api/cases', methods=['GET'])
def get_cases():
    g = None
    try:
        g = get_graph_connection()
        if not g:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Get all bank accounts
        bank_accounts = g.V().hasLabel("bank_account").valueMap(True).toList()
        
        cases = []
        case_id = 1
        
        for account in bank_accounts:
            patterns = detect_mule_patterns(account.get('id'), g)
            
            if patterns:
                for pattern in patterns:
                    case = {
                        "id": f"CASE-2025-{case_id:03d}",
                        "title": f"Suspicious {pattern['type'].title()} Pattern",
                        "description": f"{pattern['description']} in account {account.get('account_number', 'Unknown')}. "
                                     f"Total credits: ${pattern['credit_total']:,.2f}, "
                                     f"Debit amount: ${pattern['debit_amount']:,.2f}",
                        "priority": 4 if pattern['credit_total'] > 10000 else 3,
                        "assignedTo": "Fraud Team",
                        "created": datetime.now().strftime("%b %d, %Y"),
                        "status": "open",
                        "severity": "high" if pattern['credit_total'] > 10000 else "medium",
                        "relatedTransactions": [
                            tx.get('transaction_id', 'Unknown')
                            for tx in pattern['transactions']['credits'] + [pattern['transactions']['debit']]
                        ],
                        "accountDetails": {
                            "id": account.get('id'),
                            "number": account.get('account_number'),
                            "bank": account.get('bank_name'),
                            "type": account.get('account_type')
                        }
                    }
                    cases.append(case)
                    case_id += 1
        
        return jsonify(cases)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        safe_close_connection(g)

@app.route('/api/cases/<case_id>', methods=['GET'])
def get_case(case_id):
    try:
        g = get_graph_connection()
        # Implement specific case lookup logic here
        return jsonify({"error": "Not implemented"}), 501
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            g.close()
        except:
            pass

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    # Temporarily disabled to prevent connection errors
    # This endpoint is not currently used by the network analysis
    return jsonify([])
    
    # Original code commented out to prevent connection issues
    # try:
    #     g = get_graph_connection()
    #     
    #     # Get all transactions with their properties and vertex IDs
    #     transactions = g.E().hasLabel("transaction").limit(10).elementMap().toList()
    #     
    #     # Format transactions for the frontend
    #     formatted_transactions = []
    #     for tx in transactions:
    #         try:
    #             print(f"Transaction data: {tx}")
    #             
    #             # Extract inVertexId and outVertexId from elementMap
    #             out_v = None
    #             in_v = None
    #             
    #             # Look for direction keys in the transaction data
    #             for key, value in tx.items():
    #                 key_str = str(key)
    #                 if "Direction.OUT" in key_str or "~outV" in key_str:
    #                     out_v = value
    #                 elif "Direction.IN" in key_str or "~inV" in key_str:
    #                     in_v = value
    #             
    #             # If we can't find the vertices, skip this transaction
    #             if not out_v or not in_v:
    #                 print(f"Could not find vertices for transaction, skipping")
    #                 continue
    # 
    #             from_account = g.V(out_v).values('account_number').next()
    #             to_account = g.V(in_v).values('account_number').next()
    #             amount = tx.get('amount', 0)
    #             datetime_val = tx.get('datetime', 0)
    #             tx_type = tx.get('type', 'unknown')
    #             is_suspicious = tx.get('fraud_flag', False)
    # 
    #             formatted_tx = {
    #                 "id": tx.get('transaction_id'),
    #                 "from_account": from_account,
    #                 "to_account": to_account,
    #                 "amount": amount,
    #                 "datetime": datetime_val,
    #                 "type": tx_type,
    #                 "is_suspicious": is_suspicious
    #             }
    #             print(f"Formatted transaction: {formatted_tx}")
    #             formatted_transactions.append(formatted_tx)
    #         except Exception as e:
    #             print(f"Error processing transaction {tx.get('transaction_id')}: {e}")
    #             continue
    #     
    #     return jsonify(formatted_transactions)
    #     
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500
    # finally:
    #     try:
    #         g.close()
    #     except:
    #         pass

@app.route('/api/stats', methods=['GET'])
def get_stats():
    g = None
    try:
        g = get_graph_connection()
        if not g:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Get counts of different transaction patterns
        total_accounts = g.V().hasLabel("bank_account").count().next()
        suspicious_patterns = g.V().hasLabel("bank_account").filter(
            __.outE("transaction").count().is_(P.gte(3))
        ).count().next()
        
        return jsonify({
            "totalAccounts": total_accounts,
            "suspiciousPatterns": suspicious_patterns,
            "highRiskAlerts": suspicious_patterns,
            "monitoringAlerts": int(suspicious_patterns * 1.5),  # Example metric
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        safe_close_connection(g)

@app.route('/api/detect-suspicious-accounts', methods=['GET'])
def detect_suspicious_accounts():
    try:
        print("Detecting suspicious accounts...")
        accounts = detect_structured_mule_activity()
        print(f"Suspicious accounts found: {accounts}")
        return jsonify({"accounts": accounts})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fraud-scenario/<account_id>', methods=['GET'])
def run_fraud_scenario(account_id):
    try:
        print(f"Running fraud scenario analysis for account: {account_id}")
        # Call the FraudScenarioDetector function
        details = FraudScenarioDetector(account_id)
        print(f"Fraud scenario results: {details}")
        return jsonify({"details": details})
    except Exception as e:
        print(f"Error in fraud scenario analysis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/network/<account_id>', methods=['GET'])
def get_network_data(account_id):
    """
    Get network visualization data for a specific account.
    Returns nodes and links showing transaction relationships.
    """
    g = None
    try:
        print(f"Getting network data for account: {account_id}")
        g = get_graph_connection()
        if not g:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Check if account exists
        if not g.V(account_id).hasNext():
            return jsonify({"error": f"Account {account_id} not found"}), 404
        
        # Get account details
        account_data = g.V(account_id).valueMap(True).next()
        print(f"Account data: {account_data}")
        
        # Start simple - just create a basic network structure
        nodes = []
        links = []
        
        # Add the main account as central node
        main_node = {
            "id": str(account_id),
            "name": f"Account {account_data.get('account_number', [account_id])[0] if isinstance(account_data.get('account_number'), list) else account_data.get('account_number', account_id)}",
            "type": "main_account",
            "bank": account_data.get('bank_name', ['Unknown'])[0] if isinstance(account_data.get('bank_name'), list) else account_data.get('bank_name', 'Unknown'),
            "account_type": account_data.get('account_type', ['Unknown'])[0] if isinstance(account_data.get('account_type'), list) else account_data.get('account_type', 'Unknown'),
            "size": 20,
            "color": "#ff4444"
        }
        nodes.append(main_node)
        print(f"Added main node: {main_node}")
        
        # Step 1: Get connected vertices (start simple, add amounts separately)
        try:
            # Get vertices connected via outgoing transactions
            outgoing_vertices = g.V(account_id).out("transaction").toList()
            print(f"Found {len(outgoing_vertices)} outgoing connected vertices")
            
            for vertex in outgoing_vertices:
                vertex_id = str(vertex)
                if vertex_id != str(account_id):
                    # Add the connected node
                    nodes.append({
                        "id": vertex_id,
                        "name": f"Account {vertex_id}",
                        "type": "connected_account",
                        "bank": "Unknown",
                        "account_type": "Unknown", 
                        "size": 10,
                        "color": "#45b7d1"
                    })
                    
                    # Add a link - we'll get amounts in a separate step
                    links.append({
                        "source": str(account_id),
                        "target": vertex_id,
                        "type": "outgoing",
                        "amount": 5000,  # Use a realistic dummy amount for now
                        "datetime": 0,
                        "transaction_id": f"tx_out_{len(links)}",
                        "color": "#ff6b6b"
                    })
                    print(f"Added outgoing connection: {account_id} -> {vertex_id}")
                    
        except Exception as e:
            print(f"Error getting outgoing vertices: {e}")
        
        try:
            # Get vertices connected via incoming transactions  
            incoming_vertices = g.V(account_id).in_("transaction").toList()
            print(f"Found {len(incoming_vertices)} incoming connected vertices")
            
            for vertex in incoming_vertices:
                vertex_id = str(vertex)
                if vertex_id != str(account_id):
                    # Check if we already added this node
                    if not any(node["id"] == vertex_id for node in nodes):
                        nodes.append({
                            "id": vertex_id,
                            "name": f"Account {vertex_id}",
                            "type": "connected_account", 
                            "bank": "Unknown",
                            "account_type": "Unknown",
                            "size": 10,
                            "color": "#45b7d1"
                        })
                    
                    # Add a link
                    links.append({
                        "source": vertex_id,
                        "target": str(account_id),
                        "type": "incoming",
                        "amount": 3000,  # Use a different realistic dummy amount
                        "datetime": 0,
                        "transaction_id": f"tx_in_{len(links)}",
                        "color": "#4ecdc4"
                    })
                    print(f"Added incoming connection: {vertex_id} -> {account_id}")
                    
        except Exception as e:
            print(f"Error getting incoming vertices: {e}")
        
        # Step 2: Try to get real amounts for the edges we created
        try:
            # Get all outgoing edges with amounts
            outgoing_edges = g.V(account_id).outE("transaction").valueMap("amount").toList()
            
            # Update outgoing links with real amounts
            for i, edge_data in enumerate(outgoing_edges):
                if i < len([l for l in links if l['type'] == 'outgoing']):
                    outgoing_links = [l for l in links if l['type'] == 'outgoing']
                    if i < len(outgoing_links):
                        amount = edge_data.get('amount', [5000])
                        if isinstance(amount, list) and len(amount) > 0:
                            outgoing_links[i]['amount'] = amount[0]
                        else:
                            outgoing_links[i]['amount'] = amount
                        
        except Exception as e:
            print(f"Could not get outgoing amounts: {e}")
        
        try:
            # Get all incoming edges with amounts  
            incoming_edges = g.V(account_id).inE("transaction").valueMap("amount").toList()
            
            # Update incoming links with real amounts
            for i, edge_data in enumerate(incoming_edges):
                if i < len([l for l in links if l['type'] == 'incoming']):
                    incoming_links = [l for l in links if l['type'] == 'incoming']
                    if i < len(incoming_links):
                        amount = edge_data.get('amount', [3000])
                        if isinstance(amount, list) and len(amount) > 0:
                            incoming_links[i]['amount'] = amount[0]
                        else:
                            incoming_links[i]['amount'] = amount
                        
        except Exception as e:
            print(f"Could not get incoming amounts: {e}")
        
        network_data = {
            "nodes": nodes,
            "links": links,
            "center_account": account_id,
            "total_transactions": len(links),
            "connected_accounts": len(nodes) - 1  # Subtract 1 for main account
        }
        
        print(f"Final network data: {len(nodes)} nodes, {len(links)} links")
        return jsonify(network_data)
        
    except Exception as e:
        print(f"Error getting network data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        safe_close_connection(g)

@app.route('/api/account-details/<account_id>', methods=['GET'])
def get_account_details(account_id):
    """
    Get detailed properties for a specific account vertex.
    This is called when clicking on connected accounts in the network visualization.
    """
    g = None
    try:
        print(f"Getting detailed properties for account: {account_id}")
        g = get_graph_connection()
        if not g:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Extract the actual vertex ID from string format like "v[555322704748358]"
        actual_vertex_id = account_id
        if account_id.startswith('v[') and account_id.endswith(']'):
            actual_vertex_id = account_id[2:-1]  # Remove "v[" and "]"
            print(f"Extracted vertex ID: {actual_vertex_id}")
        
        # Keep as string - don't convert to int to avoid overflow issues
        print(f"Using string vertex ID: {actual_vertex_id}")
        
        # Use the same simple approach as the network API
        if not g.V(actual_vertex_id).hasNext():
            print(f"Vertex not found with ID: {actual_vertex_id}")
            return jsonify({"error": f"Account {account_id} not found"}), 404
        
        # Get all vertex properties
        vertex_data = g.V(actual_vertex_id).valueMap(True).next()
        
        # Format the vertex data for better display
        formatted_data = {}
        
        for key, value in vertex_data.items():
            key_str = str(key)
            if "T.id" in key_str:
                formatted_data['vertex_id'] = str(value)
            elif "T.label" in key_str:
                formatted_data['vertex_label'] = str(value)
            else:
                # Regular properties - extract from list if needed
                if isinstance(value, list) and len(value) == 1:
                    formatted_data[str(key)] = value[0]
                else:
                    formatted_data[str(key)] = value
        
        # Get transaction statistics using the same approach
        try:
            outgoing_count = g.V(actual_vertex_id).outE("transaction").count().next()
            incoming_count = g.V(actual_vertex_id).inE("transaction").count().next()
            
            # Calculate volume estimates
            try:
                # Get outgoing transaction amounts
                outgoing_amounts = g.V(actual_vertex_id).outE("transaction").valueMap("amount").toList()
                estimated_outgoing_volume = sum(
                    amount[0] if isinstance(amount, list) and len(amount) > 0 else amount
                    for edge in outgoing_amounts
                    for amount in [edge.get('amount', 0)]
                    if amount
                )
                
                # Get incoming transaction amounts  
                incoming_amounts = g.V(actual_vertex_id).inE("transaction").valueMap("amount").toList()
                estimated_incoming_volume = sum(
                    amount[0] if isinstance(amount, list) and len(amount) > 0 else amount
                    for edge in incoming_amounts
                    for amount in [edge.get('amount', 0)]
                    if amount
                )
            except Exception as e:
                print(f"Error calculating volumes: {e}")
                estimated_outgoing_volume = 0
                estimated_incoming_volume = 0
            
            # Get connection statistics
            try:
                unique_outgoing_connections = g.V(actual_vertex_id).out("transaction").dedup().count().next()
                unique_incoming_connections = g.V(actual_vertex_id).in_("transaction").dedup().count().next()
                total_unique_connections = g.V(actual_vertex_id).both("transaction").dedup().count().next()
            except Exception as e:
                print(f"Error calculating connections: {e}")
                unique_outgoing_connections = 0
                unique_incoming_connections = 0
                total_unique_connections = 0
            
            transaction_stats = {
                'outgoing_count': int(outgoing_count),
                'incoming_count': int(incoming_count),
                'total_transactions': int(outgoing_count + incoming_count),
                'estimated_outgoing_volume': float(estimated_outgoing_volume),
                'estimated_incoming_volume': float(estimated_incoming_volume)
            }
            
            connection_stats = {
                'unique_outgoing_connections': int(unique_outgoing_connections),
                'unique_incoming_connections': int(unique_incoming_connections),
                'total_unique_connections': int(total_unique_connections)
            }
            
        except Exception as e:
            print(f"Error getting transaction counts: {e}")
            transaction_stats = {
                'outgoing_count': 0,
                'incoming_count': 0,
                'total_transactions': 0,
                'estimated_outgoing_volume': 0.0,
                'estimated_incoming_volume': 0.0
            }
            connection_stats = {
                'unique_outgoing_connections': 0,
                'unique_incoming_connections': 0,
                'total_unique_connections': 0
            }
        
        result = {
            'account_id': str(account_id),
            'properties': formatted_data,
            'transaction_statistics': transaction_stats,
            'connection_statistics': connection_stats,
            'status': 'success'
        }
        
        print(f"Successfully prepared account details for {account_id}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting account details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        safe_close_connection(g)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 