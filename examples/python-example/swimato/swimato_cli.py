import cmd
import time
from datetime import datetime
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, Order

class SwimatoCLI(cmd.Cmd):
    intro = 'Welcome to Swimato CLI. Type help or ? to list commands.\n'
    prompt = 'swimato> '

    def __init__(self):
        super().__init__()
        self.connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
        self.g = traversal().with_remote(self.connection)

    def do_check_order(self, arg):
        """
        Check order status. Usage:
        check_order order <order_id>
        check_order customer <customer_id>
        """
        args = arg.split()
        if len(args) != 2:
            print("Invalid arguments. Use 'help check_order' for usage.")
            return

        type_, id_ = args
        if type_ == 'order':
            order = self.g.V(id_).valueMap().toList()
            # Get menu items and their quantities
            items = self.g.V(id_)\
                    .outE("CONTAINS")\
                    .project("item", "qty", "price")\
                    .by(__.inV().values("name"))\
                    .by(__.values("qty"))\
                    .by(__.inV().values("price"))\
                    .toList()
            
            if order:
                print(f"Order Status: {order[0].get('status', ['Unknown'])[0]}")
                print("\nOrder Items:")
                for item in items:
                    print(f"- {item['item']}: {item['qty']} x ${item['price']}")         
            else:
                print("Order not found")
        
        elif type_ == 'customer':
            # Get most recent order for customer
            # .order().by("order_date", "desc")\
            order = self.g.V(id_)\
                    .out("PLACED")\
                    .order()\
                    .by("order_date", Order.desc)\
                    .valueMap()\
                    .toList()
            if order:
                # Convert string to long integer
                timestamp = int(str(order[0].get('order_date', [0])[0]), 10)  # base 10, handles large numbers
                date_str = datetime.fromtimestamp(timestamp/1000)  # divide by 1000 if timestamp is in milliseconds
                
                print(f"Most Recent Order Status: {order[0].get('status', ['Unknown'])[0]}")
                print(f"Order ID: {order[0].get('order_id', ['Unknown'])[0]}")
                print(f"Order Date: {date_str}")
            else:
                print("No orders found for customer")

    def do_assign_driver(self, arg):
        """
        Assign driver to an order. Usage:
        assign_driver <order_id> <driver_id>
        """
        args = arg.split()
        if len(args) != 2:
            print("Invalid arguments. Use 'help assign_driver' for usage.")
            return

        order_id, driver_id = args
        try:
            # Create DELIVERED_BY edge
            self.g.V(order_id)\
                .as_('order')\
                .V(driver_id)\
                .addE("DELIVERED_BY")\
                .from_('order')\
                .property("assigned_date", int(time.time()))\
                .iterate()
            
            # Update order status
            self.g.V(order_id)\
                .property("status", "ASSIGNED_TO_DRIVER")\
                .iterate()
                
            print(f"Driver {driver_id} assigned to order {order_id}")
        except Exception as e:
            print(f"Error assigning driver: {str(e)}")

    def do_restaurant_ratings(self, arg):
        """
        List ratings for a restaurant. Usage:
        restaurant_ratings <restaurant_id>
        """
        if not arg:
            print("Please provide restaurant_id")
            return

        ratings = self.g.V(arg).hasLabel("Restaurant")\
                .inE("RATED")\
                .limit(10)\
                .valueMap("rating", "comment")\
                .toList()
        
        if ratings:
            print("\nRatings:")
            for rating in ratings:
                print(f"Rating: {rating.get('rating', ['N/A'])[0]}")
                print(f"Comment: {rating.get('comment', ['No comment'])}")
                print("-" * 30)
        else:
            print("No ratings found for this restaurant")

    def do_customer_orders(self, arg):
        """
        Get 5 most recent orders for a customer. Usage:
        customer_orders <customer_id>
        """
        if not arg:
            print("Please provide customer_id")
            return
        
        orders = self.g.V(arg).hasLabel("CustomerProfile")\
                .out("PLACED")\
                .order()\
                .by("order_date", Order.desc)\
                .limit(5)\
                .valueMap()\
                .toList()

        if orders:
            print("\n5 Most Recent Orders:")
            for order in orders:
                # Convert string to long integer
                timestamp = int(str(order.get('order_date', [0])[0]), 10)  # base 10, handles large numbers
                date_str = datetime.fromtimestamp(timestamp/1000)  # divide by 1000 if timestamp is in milliseconds
                
                print(f"Order ID: {order.get('order_id', ['Unknown'])[0]}")
                print(f"Status: {order.get('status', ['Unknown'])[0]}")
                print(f"Date: {date_str}")
                print("-" * 30)
        else:
            print("No orders found for this customer")

    def do_quit(self, arg):
        """Exit the CLI"""
        self.connection.close()
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        """Exit on Ctrl-D"""
        return self.do_quit(arg)

if __name__ == '__main__':
    try:
        SwimatoCLI().cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")