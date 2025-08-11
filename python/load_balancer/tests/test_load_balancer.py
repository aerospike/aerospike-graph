from time import sleep

import docker
import pytest
from load_balancer.load_balancer import RoundRobinClientRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENDPOINTS = ["localhost:8181", "localhost:8182", "localhost:8183"]
@pytest.fixture
def populated_graph():

    load_balancer = RoundRobinClientRemoteConnection(ENDPOINTS, traversal_source="g", health_check_interval=2,
                                                     log_level=logging.DEBUG)
    g = traversal().withRemote(load_balancer)
    g.V().drop().iterate()

    user1 = g.add_v("User").property("userId", "U1").property("name", "Alice").property("age", 30).next()
    user2 = g.add_v("User").property("userId", "U2").property("name", "Bob").property("age", 25).next()
    user3 = g.add_v("User").property("userId", "U3").property("name", "Charlie").property("age", 35).next()

    account1 = g.add_v("Account").property("accountId", "A1").property("balance", 1000).next()
    account2 = g.add_v("Account").property("accountId", "A2").property("balance", 500).next()
    account3 = g.add_v("Account").property("accountId", "A3").property("balance", 750).next()

    g.add_e("owns").from_(user1).to(account1).next()
    g.add_e("owns").from_(user2).to(account2).next()
    g.add_e("owns").from_(user3).to(account3).next()

    yield {
        'g': g,
        'load_balancer': load_balancer,
        'users': [user1, user2, user3],
        'accounts': [account1, account2, account3],
    }

    load_balancer.close()


class TestPythonLoadBalancer:

    def test_host_add_and_removal(self, populated_graph):
        rr_conn = populated_graph["load_balancer"]
        initial_hosts = rr_conn.get_clients()
        initial_available = rr_conn.get_available()
        endpoint_to_remove = ENDPOINTS[1]
        rr_conn.remove_host(endpoint_to_remove)
        post_remove_hosts = rr_conn.get_clients()
        post_remove_available = rr_conn.get_available()
        removed = True
        for host in post_remove_hosts:
            if endpoint_to_remove in host.url:
                removed = False
        assert removed
        assert len(initial_hosts) == len(post_remove_hosts) + 1
        assert len(initial_available) == len(post_remove_available) + 1

        rr_conn.add_host(endpoint_to_remove)
        added = False
        post_add_hosts = rr_conn.get_clients()
        post_add_available = rr_conn.get_available()
        for host in post_add_hosts:
            if endpoint_to_remove in host.url:
                added = True
        assert added
        assert len(post_remove_hosts) == len(post_add_hosts) - 1
        assert len(post_remove_available) == len(post_add_available) - 1

    def test_rotation(self, populated_graph, caplog):
        caplog.set_level(logging.DEBUG, logger="RoundRobinClientRemoteConnection")

        g = populated_graph["g"]
        for _ in range(5):
            g.V().has("name", "Alice").limit(_).to_list()

        msgs = [rec.getMessage() for rec in caplog.records]
        assert msgs.count("Traversal submitted via connection #0") == 1
        assert msgs.count("Traversal submitted via connection #1") == 2
        assert msgs.count("Traversal submitted via connection #2") == 2

    def test_health_check(self, populated_graph):
        rr_conn = populated_graph["load_balancer"]
        g = populated_graph["g"]

        host_to_close = ENDPOINTS[1]
        host_ip, port = host_to_close.split(":")
        initial_avaiable = rr_conn.get_available()
        unhealthy_found = any(False for health in initial_avaiable)
        assert not unhealthy_found

        container_id = self.stop_container_by_host_port(host_ip, int(port))
        for _ in range(3):
            g.V().has("name", "Alice").limit(_).to_list()
        post_container_down_available = rr_conn.get_available()
        unhealthy_found = any(health == False for health in post_container_down_available)
        assert unhealthy_found

        self.start_container_by_host_port(container_id)
        sleep(7) # wait for healthcheck ping
        unhealthy_found = any(health == False for health in rr_conn.get_available())
        assert not unhealthy_found

    def stop_container_by_host_port(self, host_ip: str, host_port: int, timeout: int = 10) -> str:
        client = docker.from_env()

        for container in client.containers.list():
            ports = container.attrs['NetworkSettings']['Ports'] or {}
            for container_port, mappings in ports.items():
                if not mappings:
                    continue
                for m in mappings:
                    if (m['HostIp'] in ('0.0.0.0', host_ip) and
                            int(m['HostPort']) == host_port):
                        # found it—stop and return
                        container.stop(timeout=timeout)
                        return container.id
        return ""

    def start_container_by_host_port(self, container_id: str):
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.start()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])