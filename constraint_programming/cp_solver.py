from typing import List
from parse import parse
import numpy as np
from docplex.cp.model import *

import Util
from ResultStruct import ResultStruct
from constraint_programming.cp_structs import CpParameters, CpVariables


def solve_scheduling(parameters: CpParameters) -> List[ResultStruct]:

    # create variables
    var = CpVariables()



def plain_planning(parameters: CpParameters, state: CpState, time_step, start_model_building_time,
                   flow_attributes, cluster_mapping, offensive: bool) -> ResultStruct:
    ###############
    # flow binaries
    ###############
    mdl = CpoModel()

    # remove flows
    to_remove = time_step["removeFlows"] if "removeFlows" in time_step else time_step["removeClusters"]
    for remove_sublist in to_remove:
        for remove_stream in cluster_mapping[remove_sublist]:
            state.flow_ids.remove(remove_stream)
            if remove_stream in state.admitted:
                state.admitted.remove(remove_stream)

            if remove_stream in state.var_admit_flows:
                del state.var_admit_flows[remove_stream]
            if remove_stream in state.var_candidate_routes:
                del state.var_candidate_routes[remove_stream]
            # remove entries of the removed stream from the link binary variables
            for link in state.var_bin_link:
                if remove_stream in state.var_bin_link[link]:
                    del state.var_bin_link[link][remove_stream]
            if remove_stream in state.var_time_per_link:
                del state.var_time_per_link[remove_stream]

    # add new flows
    new_flows = time_step["addFlows"] if "addFlows" in time_step else \
        [c for cluster in time_step["addClusters"] for c in cluster["streams"]]
    new_flow_ids = [flow["flowID"] for flow in new_flows]
    for new_flow_id in new_flow_ids:
        state.var_admit_flows[new_flow_id] = expression.binary_var(name="admit_flow_{}_".format(new_flow_id))
    state.flow_ids += new_flow_ids

    if offensive:
        # ensure all old streams are scheduled
        for stream_id in state.admitted:
            state.var_admit_flows[stream_id].domain = (1, 1)

    ################
    # route binaries
    ################
    for flow_id in state.flow_ids:
        state.var_candidate_routes[flow_id] = expression.binary_var_list(len(parameters.routes[flow_id]),
                                                                         name="flow{}_use_route_".format(flow_id))
        mdl.add_constraint(sum_of(state.var_candidate_routes[flow_id]) == state.var_admit_flows[flow_id])

    # network link usages

    for flow_id in state.flow_ids:
        current_route_number = 0
        for current_route in parameters.routes[flow_id]:
            for current_link in current_route:
                if current_link not in state.var_bin_link:
                    state.var_bin_link[current_link] = {}
                if flow_id not in state.var_bin_link[current_link]:
                    state.var_bin_link[current_link][flow_id] = expression.binary_var(
                        name="flow_{}_link_{}".format(flow_id, current_link))
                # var_bin_link[link][flow] is 1, if the link is part of a selected candidate route
                mdl.add_constraint(
                    state.var_bin_link[current_link][flow_id] >= state.var_candidate_routes[flow_id][
                        current_route_number])

                if flow_id not in state.var_time_per_link:
                    state.var_time_per_link[flow_id] = {}
                if current_link not in state.var_time_per_link[flow_id]:
                    state.var_time_per_link[flow_id][current_link] = []

                    # iterate through frames per hyper-cycle
                    frame_number = 0
                    current_period = flow_attributes[flow_id]["period"]
                    transmission_delay = flow_attributes[flow_id]["transmission delay"]

                    while frame_number * current_period < parameters.hyper_cycle:
                        release_time = frame_number * current_period
                        deadline = parameters.hyper_cycle if parameters.hyper_cycle_deadline else release_time + current_period

                        state.var_time_per_link[flow_id][current_link].append(
                            expression.interval_var(
                                start=(release_time, (deadline - Util.PROPAGATION_DELAY - transmission_delay)),
                                end=(release_time + transmission_delay, deadline - Util.PROPAGATION_DELAY),
                                length=transmission_delay,
                                optional=True,
                                name="flow_{}_frame_{}_on_{}".format(flow_id, frame_number, current_link)))
                        frame_number += 1

                # make sure the added frame is present if the link is te be used
                mdl.add_constraint(
                    state.var_bin_link[current_link][flow_id] <= modeler.presence_of(
                        state.var_time_per_link[flow_id][current_link][-1]))

            current_route_number += 1

    ##########################
    # zero-queuing constraints
    ##########################
    delay = Util.PROCESSING_DELAY + Util.PROPAGATION_DELAY
    for flow, candidate_routes in parameters.routes.items():
        if flow not in state.flow_ids:
            continue
        route_number = 0
        for route in candidate_routes:
            last_hop = route[0]

            for hop in route[1:]:
                # frames
                for frame_number in range(0, int(parameters.hyper_cycle / flow_attributes[flow]["period"])):
                    if parameters.zero_queuing:
                        # end_at_start enforces zero queuing
                        mdl.add_constraint(end_at_start(state.var_time_per_link[flow][last_hop][frame_number],
                                                        state.var_time_per_link[flow][hop][frame_number], delay=delay))
                    else:
                        # end_before_start enforces only the ordering -> allows for queuing
                        mdl.add_constraint(end_before_start(state.var_time_per_link[flow][last_hop][frame_number],
                                                            state.var_time_per_link[flow][hop][frame_number],
                                                            delay=delay))

                last_hop = hop
            route_number += 1

    # iterate all network links optimized for CP
    for joint_link in state.var_bin_link:
        intervals = []
        for flow_id in state.var_bin_link[joint_link]:
            intervals += state.var_time_per_link[flow_id][joint_link]

        mdl.add_constraint(no_overlap(intervals))

    ###########
    # objective
    ###########
    nr_new_flows = len(new_flow_ids)
    if parameters.optimize_traffic:
        # traffic values
        traffic_bounds = [
            int(flow_attributes[flow_id]["package size"] * 8. * (1000. / flow_attributes[flow_id]["period"])) for
            flow_id in state.flow_ids]
        # if state.mdl_sol is None:
        # first iteration
        mdl.maximize(np.sum(np.multiply(traffic_bounds, state.var_admit_flows)))
        # else:
        # maximize new flows
        #   mdl.maximize(np.sum(np.multiply(traffic_bounds[len(traffic_bounds) - nr_new_flows:],
        #                                   state.var_admit_flows[len(state.var_admit_flows) - nr_new_flows:])))
    else:
        # if state.mdl_sol is None:
        # maximize number of admitted streams
        mdl.maximize(modeler.sum_of(state.var_admit_flows.values()))

    start_solving_time = time.time()
    if parameters.verbose:
        print("Solving model....")
    log_verbosity = 'Quiet' if parameters.raw_output else 'Terse'
    warning_level = 0 if parameters.raw_output else 2
    mdl_sol = mdl.solve(TimeLimit=parameters.timeout, Workers=parameters.threads, WarningLevel=warning_level,
                        LogVerbosity=log_verbosity) if platform.system() == 'Windows' else mdl.solve(
        TimeLimit=parameters.timeout, Workers=parameters.threads, LogVerbosity=log_verbosity,
        WarningLevel=warning_level, execfile='/home/gepperho/CPLEX_Studio221/cpoptimizer/bin/x86-64_linux/cpoptimizer')
    end_solving_time = time.time()

    state.mdl_sol = mdl_sol

    if parameters.verbose:
        mdl_sol.print_solution()

    #################
    # extract results
    #################
    admitted_flows_var = [var for var in state.var_admit_flows.values() if mdl_sol[var] == 1]
    result_struct = ResultStruct()
    result_struct.time_step = int(time_step['time'])
    result_struct.solver = 'CP'
    result_struct.optimize_traffic = parameters.optimize_traffic
    result_struct.zero_queuing = parameters.zero_queuing
    result_struct.building_time = start_solving_time - start_model_building_time
    result_struct.solving_time = end_solving_time - start_solving_time
    result_struct.total_time = end_solving_time - start_model_building_time
    result_struct.flows_admitted = len(admitted_flows_var)
    result_struct.flows_total = len(state.flow_ids)
    result_struct.mode = 'offensive' if offensive else 'defensive'
    result_struct.admitted_streams = []

    # traffic computation
    traffic_sum = 0.0
    traffic_bounds = {
        flow_id: int(flow_attributes[flow_id]["package size"] * 8. * (1000. / flow_attributes[flow_id]["period"]))
        for flow_id in state.flow_ids}
    for admitted_flow in admitted_flows_var:
        flow_id = int(parse("admit_flow_{:d}_", admitted_flow.name).fixed[0])
        result_struct.admitted_streams.append(flow_id)
        traffic_sum += traffic_bounds[flow_id]
    result_struct.traffic_admitted = traffic_sum / 1000
    if parameters.verbose:
        result_struct.print()
    return result_struct


def defensive_planning(parameters: CpParameters, state: CpState, time_step, flow_attributes,
                       cluster_mapping) -> ResultStruct:
    """
    Calls the plain planning function with the previous solution as fixed input.
    :return:
    """
    start_model_building_time = time.time()
    fix_previous_solution(solution=state.mdl_sol,
                          state=state)

    result = plain_planning(parameters, state, time_step, start_model_building_time, flow_attributes, cluster_mapping,
                            offensive=False)
    return result


def offensive_planning(parameters: CpParameters, state: CpState, time_step, flow_attributes,
                       cluster_mapping) -> ResultStruct:
    """
    This function is a placeholder for the actual planning function.
    :return:
    """

    start_model_building_time = time.time()
    result = plain_planning(parameters, state, time_step, start_model_building_time, flow_attributes, cluster_mapping,
                            offensive=True)
    return result


def fix_previous_solution(solution, state):
    """
    fix the old variable values -> makes them basically immutable
    :param solution:
    :param state:
    :return:
    """
    if solution is None:
        return

    # Note, also the rejected streams need to be fixed. Otherwise, they could be scheduled in a later step, after being rejected.
    for admit_flow_var in state.var_admit_flows.values():
        former_result = solution[admit_flow_var.name]
        admit_flow_var.domain = (former_result, former_result)

    for key, flow_route_vars in state.var_candidate_routes.items():
        for candidate_route_var in flow_route_vars:
            former_result = solution[candidate_route_var.name]
            candidate_route_var.domain = (former_result, former_result)

    for key, bin_link_vars in state.var_bin_link.items():
        for key2, bin_link_var in bin_link_vars.items():
            former_result = solution[bin_link_var.name]
            bin_link_var.domain = (former_result, former_result)

    for key, time_per_link_vars in state.var_time_per_link.items():
        for key2, time_per_link_var_list in time_per_link_vars.items():
            for time_per_link_var in time_per_link_var_list:
                former_result = solution[time_per_link_var.name]
                if len(former_result) > 0:
                    time_per_link_var.presence = 'present'
                    time_per_link_var.start = (former_result.start, former_result.start)
                    time_per_link_var.end = (former_result.end, former_result.end)
