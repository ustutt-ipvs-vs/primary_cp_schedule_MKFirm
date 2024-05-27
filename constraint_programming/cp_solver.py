from docplex.cp.model import *

import Util
from constraint_programming.cp_structs import CpParameters, CpVariables
from network.network_elements import EgressPort, NetworkNode
from scenario.scenario import Stream


def solve_scheduling(parameters: CpParameters) -> CpoSolveResult:
    # create variables
    var = CpVariables(parameters.network, parameters.scenario, parameters.routes)

    mdl = CpoModel()
    # create constraints
    create_single_stream_constraints(mdl, var, parameters)
    create_transmission_isolation_constraints(mdl, var, parameters)
    create_queuing_isolation_constraints(mdl, var, parameters)
    create_constraints_linking_queuing_to_transmission(mdl, var, parameters)
    create_constraints_linking_pcp_to_queuing(mdl, var, parameters)

    optimization_goal(mdl, var, parameters)

    # call the actual planning
    result = planning(mdl, parameters)

    return result


def create_single_stream_constraints(mdl: CpoModel, var: CpVariables, param: CpParameters):
    """
    Create constraints concerning single streams:
    - link precedence constraints
    - zero jitter constraints
    """

    stream: Stream
    for stream in param.scenario.streams:

        # link precedence constraint
        for frame in Util.iterate_frames_per_hc(stream, param.scenario.hyper_cycle):
            # iterate over all hops of the stream
            for hop in range(1, len(param.routes[stream.id])):
                last_hop: EgressPort = param.routes[stream.id][hop - 1]
                current_hop: EgressPort = param.routes[stream.id][hop]
                processing_delay: int = param.network.get_node(last_hop.host_node).processing_delay_ns
                last_hop_var = var.get_transmission_var(last_hop, stream, frame)
                current_hop_var = var.get_transmission_var(current_hop, stream, frame)
                mdl.add_constraint(end_before_start(last_hop_var, current_hop_var,
                                                    delay=processing_delay + last_hop.propagation_delay_ns))

        # zero jitter constraint
        last_egress_port = param.routes[stream.id][-1]
        for frame in range(1, Util.get_frames_per_hc(stream, param.scenario.hyper_cycle)):
            last_frame_var = var.get_transmission_var(last_egress_port, stream, frame - 1)
            current_frame_var = var.get_transmission_var(last_egress_port, stream, frame)
            mdl.add_constraint(end_at_end(last_frame_var, current_frame_var, delay=stream.cycle_time_ns))


def create_transmission_isolation_constraints(mdl: CpoModel, var: CpVariables, param: CpParameters):
    """
    Create no overlap constraints for transmissions.
    """
    node: NetworkNode
    port: EgressPort
    for node in param.network.nodes.values():
        for egress_port in node.ports:

            # transmissions and inter-frame gaps cannot overlap
            variables = var.transmission_windows[egress_port.id] + list(var.inter_frame_gaps[egress_port.id].values())
            if len(variables) > 1:
                mdl.add_constraint(no_overlap(variables))

            # connect transmission and inter-frame gap, i.e., after each transmission directly follows the according ifg
            for transmission in var.transmission_windows[egress_port.id]:
                if transmission.name in var.inter_frame_gaps[egress_port.id]:
                    mdl.add_constraint(
                        end_at_start(transmission, var.inter_frame_gaps[egress_port.id][transmission.name]))


def create_queuing_isolation_constraints(mdl: CpoModel, var: CpVariables, param: CpParameters):
    node: NetworkNode
    for node in param.network.nodes.values():
        egress_port: EgressPort
        for egress_port in node.ports:
            for queue in range(0, len(var.queuing[egress_port.id])):
                if len(var.queuing[egress_port.id][queue]) > 1:
                    mdl.add_constraint(no_overlap(var.queuing[egress_port.id][queue]))


def create_constraints_linking_queuing_to_transmission(mdl: CpoModel, var: CpVariables, param: CpParameters):
    """
    Create constraints linking queuing to transmission.
    """
    stream: Stream
    for stream in param.scenario.streams:
        previous_hop: EgressPort = param.routes[stream.id][0]
        current_hop: EgressPort
        for current_hop in param.routes[stream.id][1:]:
            frame: int
            for frame in Util.iterate_frames_per_hc(stream, param.scenario.hyper_cycle):
                previous_transmission = var.get_transmission_var(previous_hop, stream, frame)
                current_transmission = var.get_transmission_var(current_hop, stream, frame)

                queue: int
                for queue in range(0, len(var.queuing[current_hop.id])):
                    queuing_var = var.get_queuing_var(current_hop, stream, frame, queue)
                    if queuing_var is not None:
                        # queuing starts after the previous transmission ends
                        mdl.add_constraint(start_at_end(queuing_var, previous_transmission))
                        # queuing ends with the end of the current transmission
                        mdl.add_constraint(end_at_end(queuing_var, current_transmission))

                # end of queue loop
            previous_hop = current_hop
            # end of frame loop
        # end of hop loop
    # end of stream loop


def create_constraints_linking_pcp_to_queuing(mdl: CpoModel, var: CpVariables, param: CpParameters):
    stream: Stream
    for stream in param.scenario.streams:
        pcp_var = var.get_pcp_var(stream)

        for hop in param.routes[stream.id]:
            for frame in Util.iterate_frames_per_hc(stream, param.scenario.hyper_cycle):
                for queue in range(0, len(var.queuing[hop.id])):
                    queuing_var = var.get_queuing_var(hop, stream, frame, queue)

                    if queuing_var is not None:
                        # if the pcp is equal to the queue, the queuing must be present
                        mdl.add_constraint(if_then(pcp_var == queue, presence_of(queuing_var)))


def optimization_goal(mdl: CpoModel, var: CpVariables, param: CpParameters):
    """
    Minimize the maximum end-to-end delay.
    Note that it is fine to minmax the e2e delay for the first frame of each stream, since we have a zero-jitter constraint.
    """
    end_to_end_delays = []
    for stream in param.scenario.streams:
        first_hop = param.routes[stream.id][0]
        last_hop = param.routes[stream.id][-1]
        first_transmission = var.get_transmission_var(hop=first_hop, stream=stream, frame=0)
        last_transmission = var.get_transmission_var(hop=last_hop, stream=stream, frame=0)
        end_to_end = interval_var(start=first_transmission.start, end=last_transmission.end, optional=False,
                                  name="end_to_end_delay_stream_{}".format(stream.id))
        mdl.add_constraint(span(end_to_end, [first_transmission, last_transmission]))
        end_to_end_delays.append(end_to_end)

    mdl.minimize(max([length_of(v) for v in end_to_end_delays]))


def planning(mdl: CpoModel, param: CpParameters) -> CpoSolveResult:
    start_solving_time = time.time()

    if param.verbose:
        print("Solving model....")
    log_verbosity = 'Quiet' if param.raw_output else 'Terse'
    warning_level = 0 if param.raw_output else 2
    mdl_sol: CpoSolveResult
    if platform.system() == 'Windows':
        mdl_sol = mdl.solve(TimeLimit=param.timeout, Workers=param.threads, WarningLevel=warning_level,
                            LogVerbosity=log_verbosity)
    else:
        mdl_sol = mdl.solve(TimeLimit=param.timeout, Workers=param.threads, LogVerbosity=log_verbosity,
                            WarningLevel=warning_level,
                            execfile='/home/gepperho/CPLEX_Studio221/cpoptimizer/bin/x86-64_linux/cpoptimizer')
    end_solving_time = time.time()

    if param.verbose:
        mdl_sol.print_solution()
        print("Solving time: ", end_solving_time - start_solving_time)

    return mdl_sol
