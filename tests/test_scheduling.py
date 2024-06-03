import unittest
import json

from docplex.cp.solution import CpoSolveResult

import Routing
from Util import get_frames_per_hc
from constraint_programming import cp_structs, cp_solver
from constraint_programming.cp_output_writer import write_result_to_json
from network.network_graph import NetworkGraph
from scenario.scenario import Scenario


class TestScheduling(unittest.TestCase):

    def test_scheduling_result(self):
        network: NetworkGraph = NetworkGraph("test_data/routing_graph_1.json")
        scenario: Scenario = Scenario("test_data/test_scenario.json")
        candidate_routes = Routing.compute_candidate_routes(network=network, scenario=scenario)

        parameters = cp_structs.CpParameters(network=network, scenario=scenario, routes=candidate_routes, timeout=120,
                                             threads=4, verbose=False, raw_output=True)
        result: CpoSolveResult = cp_solver.solve_scheduling(parameters)
        output_path: str = 'test_transmission_output.json'
        write_result_to_json(result, parameters, output_path)

        with open(output_path) as result_file:
            result_json = json.load(result_file)
            # stream count
            self.assertEqual(len(result_json), len(scenario.streams))

            # frame count
            for stream in scenario.streams:
                self.assertEqual(len(result_json[int(stream.id)]['frames']),
                                 get_frames_per_hc(stream, scenario.hyper_cycle))

    def test_scheduling_result_infeasible(self):
        network: NetworkGraph = NetworkGraph("test_data/routing_graph_1.json")
        scenario: Scenario = Scenario("test_data/test_scenario_infeasible.json")
        candidate_routes = Routing.compute_candidate_routes(network=network, scenario=scenario)

        parameters = cp_structs.CpParameters(network=network, scenario=scenario, routes=candidate_routes, timeout=120,
                                             threads=4, verbose=False, raw_output=True)
        result: CpoSolveResult = cp_solver.solve_scheduling(parameters)

        self.assertEqual(result.is_solution(), False)
