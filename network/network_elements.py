from dataclasses import dataclass
from typing import List, overload

from scenario.scenario import Stream


@dataclass
class EgressPort:
    id: str
    host_node: str
    destination_node: str

    # link properties
    link_speed_mbps: int
    propagation_delay_ns: int

    inter_frame_gap: int

    def __init__(self, json_link):

        self.id = json_link['key']
        self.host_node = json_link['source']
        self.destination_node = json_link['target']
        self.link_speed_mbps = int(json_link['link_speed_mbps'])
        self.propagation_delay_ns = int(json_link['propagation_delay_ns'])

        self.inter_frame_gap = self.calculate_transmission_delay_in_ns_of(12)

    @overload
    def calculate_transmission_delay_in_ns_of(self, stream: Stream) -> int:
        ...

    @overload
    def calculate_transmission_delay_in_ns_of(self, frame_size: int) -> int:
        ...

    def calculate_transmission_delay_in_ns_of(self, arg) -> int:
        def computation(frame_size: int) -> int:
            return int(frame_size * 8 / self.link_speed_mbps * 10 ** 3)

        if isinstance(arg, Stream):
            return computation(arg.frame_size_B)
        elif isinstance(arg, int):
            return computation(arg)
        else:
            raise ValueError("Invalid argument type")

    def get_inter_frame_gap(self):
        return self.inter_frame_gap


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
