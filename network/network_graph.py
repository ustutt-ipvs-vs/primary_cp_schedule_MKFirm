import json
from typing import List, Dict
from network.network_elements import NetworkNode, EgressPort


class NetworkGraph:
    nodes: Dict[str, NetworkNode]

    def __init__(self, network_file_path: str):
        self.nodes = {}

        with open(network_file_path) as network_file:
            topology_json = json.load(network_file)

            # load nodes
            for node_json in topology_json['nodes']:
                node = NetworkNode(node_json['id'])
                # TODO should we use ns here or us?
                node.processing_delay_ns = int(node_json['processing_delay_ns'])
                node.queues_per_port = int(node_json['queues_per_port'])
                node.is_switch = bool(node_json['is_switch'])
                node.ports = []
                self.nodes[node.id] = node

            # load links and create egress ports
            for link in topology_json['links']:
                egress_port = EgressPort(link)
                self.nodes[egress_port.host_node].ports.append(egress_port)

    def get_node_ids(self):
        return list(self.nodes.keys())

    def get_node(self, node_id: str) -> NetworkNode:
        return self.nodes[node_id]
