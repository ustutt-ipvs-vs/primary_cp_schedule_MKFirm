import unittest

from network.network_graph import NetworkGraph


class TestNetwork(unittest.TestCase):

    def check_network_Devices(self, network, devices, is_switch):
        for device_id, connected_nodes in devices.items():
            switch = network.get_node(str(device_id))
            self.assertEqual(switch.is_switch, is_switch)
            self.assertEqual(switch.processing_delay_ns, 4000 if is_switch else 0)
            self.assertEqual(switch.queues_per_port, 8)

            self.assertEqual(len(switch.ports), len(connected_nodes))
            self.assertEqual(len(switch.get_neighbors()), len(connected_nodes))

            for port in switch.ports:
                self.assertTrue(int(port.destination_node) in connected_nodes)

    def test_network_loading(self):
        network: NetworkGraph = NetworkGraph("test_data/routing_graph_1.json")

        self.assertEqual(len(network.nodes), 11)
        self.assertEqual(network.get_node_ids(), ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])

        switches = {1: [0, 2, 3, 4, 10],
                    2: [1, 6, 9],
                    3: [1, 6],
                    4: [1, 5],
                    5: [4, 6],
                    6: [2, 3, 5, 7, 8],
                    }

        self.check_network_Devices(network, switches, True)

        end_devices = {
            0: [1],
            7: [6],
            8: [6],
            9: [2],
            10: [1],
        }

        self.check_network_Devices(network, end_devices, False)
