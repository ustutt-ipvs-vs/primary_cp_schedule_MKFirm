from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


@dataclass
class CpParameters:
    """Parameters for the constraint programming model."""
    scenario: Any
    routes: Dict[int, List[List[Tuple[int, int]]]]
    timeout: int
    threads: int
    verbose: bool
    raw_output: bool
    optimize_traffic: bool
    zero_queuing: bool
    hyper_cycle_deadline: bool
    hyper_cycle: int = 0

    def __post_init__(self):
        self.hyper_cycle = self.scenario['config_info']['hyper_cycle']


@dataclass
class CpState:
    # solution object
    mdl_sol: Any = None

    # scenario content
    time_step: int = 0
    flow_ids: List[int] = None

    admitted: List[int] = None

    # cp variables
    # =========
    var_admit_flows: Dict[int, Any] = None
    var_candidate_routes: Dict[int, Any] = None
    # network link usages
    var_bin_link: Dict[Any, Dict[int, Any]] = None
    var_time_per_link: Dict[int, Dict[Any, Any]] = None

    def __post_init__(self):
        if self.flow_ids is None:
            self.flow_ids = []
        if self.admitted is None:
            self.admitted = []
        if self.var_admit_flows is None:
            self.var_admit_flows = {}
        if self.var_candidate_routes is None:
            self.var_candidate_routes = {}
        if self.var_bin_link is None:
            self.var_bin_link = {}
        if self.var_time_per_link is None:
            self.var_time_per_link = {}
