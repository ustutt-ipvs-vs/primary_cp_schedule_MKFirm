import argparse
import os
import Routing
from constraint_programming import cp_solver, cp_structs
from constraint_programming.cp_output_writer import write_result_to_json
from network.network_graph import NetworkGraph
from scenario.scenario import Scenario

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--network", type=str, help="Path to the network graph file", required=True)
parser.add_argument("-s", "--scenario", type=str, help="Path to the flow scenario file", required=True)
parser.add_argument("-t", "--timelimit", type=int,
                    help="solver time limit in seconds. Use negative values for unlimited.", default=120)
parser.add_argument("--threads", type=int, help="Number of threads to be used at most", default=4)
parser.add_argument("-v", "--verbose", help="print a lot of debug outputs on the console. Can be overwritten by the raw flag.",
                    action='store_true')
parser.add_argument("--raw-output", help="If set, the console output will be in a raw format. Overwrites the verbose flag.",
                    action='store_true')
parser.add_argument("-o", "--output", type=str, help="Filename and path to store the output in.", default='transmission_output.json')
parser.add_argument("--cplex", type=str, help="Path to cplex executable. Provide if it is not in the path variable.", default=None)

args = parser.parse_args()
raw_output = args.raw_output
verbose = args.verbose if not raw_output else False

network = NetworkGraph(args.network)
scenario = Scenario(args.scenario)

candidate_routes = Routing.compute_candidate_routes(network=network, scenario=scenario)

timelimit = args.timelimit if args.timelimit > 0 else None
parameters = cp_structs.CpParameters(network=network, scenario=scenario, routes=candidate_routes, timeout=timelimit,
                                     threads=args.threads, verbose=verbose, raw_output=raw_output,
                                     cplex_executable=args.cplex)
result = cp_solver.solve_scheduling(parameters)

if '/' in str(args.output):
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.isdir(output_dir):
        print(f"Creating directory {output_dir} for output file.")
        os.makedirs(output_dir, exist_ok=True)

if result.is_solution():
    write_result_to_json(result, parameters, args.output)
