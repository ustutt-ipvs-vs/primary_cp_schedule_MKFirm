from dataclasses import dataclass
from typing import Dict, List, Any

from docplex.cp.model import *

from Util import iterate_frames_per_hc
from network.network_elements import EgressPort, NetworkNode
from network.network_graph import NetworkGraph
from scenario.scenario import Scenario, Stream


@dataclass
class CpParameters:
    """Parameters for the constraint programming model."""
    network: NetworkGraph
    scenario: Scenario
    routes: Dict[str, List[EgressPort]]

    timeout: int
    threads: int
    verbose: bool
    raw_output: bool


@dataclass
class CpVariables:
    """Variables for the constraint programming model."""
    pcp: Dict[str, Any]  # int variable for the streams pcp value
    transmission_windows: Dict[str, List[Any]]  # key: egress_port, value: interval variables
    queuing: Dict[
        str, List[List[Any]]]  # key: egress_port, value: list for each queue (pcp), in list: list of interval variables

    def __init__(self, network: NetworkGraph, scenario: Scenario, routes: Dict[str, List[EgressPort]]):

        self.transmission_windows = {}
        self.queuing = {}
        self.pcp = {}

        # prepare transmission_windows and queuing structures
        node: NetworkNode
        egress_port: EgressPort
        for node in network.nodes.values():
            for egress_port in node.ports:
                self.transmission_windows[egress_port.id] = []
                self.queuing[egress_port.id] = [[] for _ in range(node.queues_per_port)]

        stream: Stream
        for stream in scenario.streams:
            # create pcp variable
            # TODO pcp ranges from 0 to 7, however, we have a specific field for the number of queues in each network device. Can wi simply assume that we always have 8 queues? -> if yes, we can use the cplex integer_var_dict
            # queues_available - 1, because highest queue for ET traffic
            self.pcp[stream.id] = expression.integer_var(0, network.min_queues_available - 1, name=f"pcp_{stream.id}")

            # create transmission_window and queuing variables
            for egress_port in routes[stream.id]:
                for frame in iterate_frames_per_hc(stream, scenario.hyper_cycle):
                    release_time = frame * stream.cycle_time_ns
                    deadline = release_time + stream.max_delay_ns

                    self.transmission_windows[egress_port.id].append(
                        expression.interval_var(
                            start=(release_time, deadline),  # todo make the bound tighter
                            end=(release_time, deadline),  # todo make the bound tighter
                            size=egress_port.calculate_transmission_delay_in_ns_of(stream),
                            optional=False,
                            name='transmission_port_{}_stream_{}_frame_{}'.format(egress_port.id, stream.id, frame)
                        ))
                    for queue in range(0, network.min_queues_available):
                        self.queuing[egress_port.id][queue].append(
                            expression.interval_var(
                                start=(release_time, deadline),  # todo make the bound tighter
                                end=(release_time, deadline),  # todo make the bound tighter
                                optional=True,
                                name='queuing_port_{}_stream_{}_frame_{}_queue_{}'.format(egress_port.id, stream.id,
                                                                                          frame, queue)
                            ))

    def get_transmission_var(self, hop: EgressPort, stream: Stream, frame: int):
        return next((v for v in self.transmission_windows[hop.id] if
                     v.name == 'transmission_port_{}_stream_{}_frame_{}'.format(hop.id, stream.id, frame)), None)

    def get_queuing_var(self, hop: EgressPort, stream: Stream, frame: int, queue: int):
        return next((v for v in self.queuing[hop.id][queue] if
                     v.name == 'queuing_port_{}_stream_{}_frame_{}_queue_{}'.format(hop.id, stream.id, frame, queue)),
                    None)

    def get_pcp_var(self, stream: Stream):
        return self.pcp[stream.id]
