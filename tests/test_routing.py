import unittest

import Routing
from network.network_graph import NetworkGraph


class TestRouting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.network = NetworkGraph("test_data/routing_graph_1.json")

    def test_simple_routing(self):
        # 0 -> 9
        route = Routing.get_dijkstra_shortest_path("0", "9", self.network, 1000)
        self.assertEqual(len(route), 3)

        # 0 -> 4
        route = Routing.get_dijkstra_shortest_path("0", "4", self.network, 1000)
        self.assertEqual(len(route), 2)

        # 0 -> 8
        route = Routing.get_dijkstra_shortest_path("0", "8", self.network, 1000)
        self.assertEqual(len(route), 4)

        # 9 -> 5
        route = Routing.get_dijkstra_shortest_path("9", "5", self.network, 1000)
        self.assertEqual(len(route), 3)
