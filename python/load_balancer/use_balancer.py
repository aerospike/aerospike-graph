import logging
import sys
from time import sleep
from gremlin_python.process.anonymous_traversal import traversal
from load_balancer import RoundRobinClientRemoteConnection

# Logging Configurations
root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
)
root.addHandler(handler)
lb_logger = logging.getLogger("RoundRobinClientRemoteConnection")
lb_logger.setLevel(logging.DEBUG) # Change this if you want less verbose output
logging.getLogger("gremlin_python").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

endpoints = [
    "localhost:8181",
    "localhost:8182",
    "localhost:8183"
]

rr_conn = RoundRobinClientRemoteConnection(endpoints, traversal_source="g",
                                           log_level=logging.DEBUG, logger=lb_logger )
g = traversal().withRemote(rr_conn)
results = []

user1 = g.add_v("User").property("userId", "U1").property("name", "Alice").property("age", 30).next()
user2 = g.add_v("User").property("userId", "U2").property("name", "Bob").property("age", 25).next()
user3 = g.add_v("User").property("userId", "U3").property("name", "Charlie").property("age", 35).next()

account1 = g.add_v("Account").property("accountId", "A1").property("balance", 1000).next()
account2 = g.add_v("Account").property("accountId", "A2").property("balance", 500).next()
account3 = g.add_v("Account").property("accountId", "A3").property("balance", 750).next()

g.add_e("owns").from_(user1).to(account1).next()
g.add_e("owns").from_(user2).to(account2).next()
g.add_e("owns").from_(user3).to(account3).next()

try:
    i = 1
    while True:
        try:
            results = g.V().limit(i).to_list()
            sleep(3)
            i += 1
        except Exception as e:
            logging.warning("Traversal failed: %s", e)
except KeyboardInterrupt:
    print("\nReceived interrupt, shutting down load balancer loop.")
finally:
    rr_conn.close()
    print("Load balancer closed. Goodbye!")