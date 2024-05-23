from typing import List


class EgressPort:
    port_key: str
    host_node: str
    destination_node: str

    # link properties
    link_speed_mbps: int
    propagation_delay_ns: int

    def __init__(self, key):
        self.port_key = key


class NetworkNode:

    id: str
    processing_delay_ns: int
    queues_per_port: int
    is_switch: bool
    ports: List[EgressPort]

    def __init__(self, name):
        self.id = name

    def get_neighbors(self):
        return [port.destination_node for port in self.ports]




