import argparse
import json

import Routing
from constraint_programming import cp_solver, cp_structs
from network.network_graph import NetworkGraph
from scenario.scenario import Scenario

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--network", type=str, help="Path to the network graph file")
parser.add_argument("-s", "--scenario", type=str, help="Path to the flow scenario file")
parser.add_argument("-t", "--timelimit", type=int,
                    help="solver time limit in seconds. Use negative values for unlimited.", default=120)
parser.add_argument("--threads", type=int, help="Number of threads to be used at most", default=4)
parser.add_argument("-v", "--verbose", help="print a lot of debug outputs. Is overwritten by the raw flag.",
                    action='store_true')
parser.add_argument("--raw-output", help="If set, the output will be in a raw format. Overwrites the verbose flag.",
                    action='store_true')

args = parser.parse_args()
raw_output = args.raw_output
verbose = args.verbose if not raw_output else False

network = NetworkGraph(args.network)
scenario = Scenario(args.scenario)

candidate_routes = Routing.compute_candidate_routes(network=network, scenario=scenario)

timelimit = args.timelimit if args.timelimit > 0 else None
parameters = cp_structs.CpParameters(scenario=scenario, routes=candidate_routes, timeout=timelimit,
                                     threads=args.threads, verbose=verbose, raw_output=raw_output,
                                     hyper_cycle_deadline=args.hyper_cycle_deadline)
results = cp_solver.solve_scheduling(parameters)

# TODO store/print results
