from dataclasses import dataclass
from typing import Dict, List, Any

from network.network_elements import EgressPort
from network.network_graph import NetworkGraph
from scenario.scenario import Scenario


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
    queuing: Dict[str, List[List[Any]]]  # key: egress_port, value: list for each queue (pcp), in list: list of interval variables

    def __init__(self, network: NetworkGraph, scenario: Scenario, routes: Dict[str, List[EgressPort]]):
        pass
