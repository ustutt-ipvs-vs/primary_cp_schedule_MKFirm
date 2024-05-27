import unittest

import Routing
from network.network_graph import NetworkGraph
from scenario.scenario import Scenario


class TestRouting(unittest.TestCase):

    def test_simple_routing(self):
        network = NetworkGraph("test_data/routing_graph_1.json")

        # 0 -> 9
        route = Routing.get_dijkstra_shortest_path("0", "9", network, 1000)
        self.assertEqual(len(route), 3)

        # 0 -> 4
        route = Routing.get_dijkstra_shortest_path("0", "4", network, 1000)
        self.assertEqual(len(route), 2)

        # 0 -> 8
        route = Routing.get_dijkstra_shortest_path("0", "8", network, 1000)
        self.assertEqual(len(route), 4)

        # 9 -> 5
        route = Routing.get_dijkstra_shortest_path("9", "5", network, 1000)
        self.assertEqual(len(route), 3)

    def test_no_path(self):
        network = NetworkGraph("test_data/routing_graph_2.json")
        existing_route = Routing.get_dijkstra_shortest_path("0", "1", network, 1000)
        self.assertEqual(len(existing_route), 1)

        self.assertRaises(Exception, Routing.get_dijkstra_shortest_path, "0", "2", network, 1000)

    def test_candidate_routes(self):
        network: NetworkGraph = NetworkGraph("test_data/routing_graph_1.json")
        scenario: Scenario = Scenario("test_data/test_scenario.json")

        candidate_routes = Routing.compute_candidate_routes(network=network, scenario=scenario)
        self.assertEqual(len(candidate_routes), 4)
        self.assertEqual(len(candidate_routes["0"]), 2)
