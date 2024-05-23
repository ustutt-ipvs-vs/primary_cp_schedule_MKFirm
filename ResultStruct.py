import time
from dataclasses import dataclass
from typing import List


@dataclass
class GlobalConfigs:
    network: str
    scenario: str
    threads: int
    routing: str
    candidate_paths: int
    unique_time_stamp: int

    def __init__(self):
        self.unique_time_stamp = int(time.time())


@dataclass
class ResultStruct:
    time_step: int
    solver: str
    mode: str
    optimize_traffic: bool
    zero_queuing: bool
    building_time: float
    solving_time: float
    total_time: float
    flows_admitted: int
    flows_total: int
    traffic_admitted: float

    admitted_streams: List[int]

    def __init__(self):
        pass

    def print(self):
        print("Time step: {}".format(self.time_step))
        print("Solver: {}-{}-{}".format(self.solver, 't' if self.optimize_traffic else 'f',
                                        'zq' if self.zero_queuing else 'q'))
        print("Mode: {}".format(self.mode))
        print("Model building time [s]: {}".format(self.building_time))
        print("Solving time [s]: {}".format(self.solving_time))
        print("Total time [s]: {}".format(self.total_time))
        print("Admitted flows: {}".format(self.flows_admitted))
        print("Total flows: {}".format(self.flows_total))
        print("Ingress traffic [Mbit/s]: {}".format(self.traffic_admitted))

    def print_raw(self, global_configs: GlobalConfigs):
        log_string = ("{time_step:}\t{network:}\t{scenario:}\t{routing:}\t{candidate_paths:}\t{builder:}\t{cps:}\t"
                      "{expansion:}\t{threads:}\t{unique_time_stamp:}").format(
            time_step=self.time_step,
            network=global_configs.network,
            scenario=global_configs.scenario,
            routing=global_configs.routing,
            candidate_paths=global_configs.candidate_paths,
            builder="none",
            cps=-1,
            expansion=-1,
            threads=global_configs.threads,
            unique_time_stamp=global_configs.unique_time_stamp
        )

        log_string += ("\t{strategy:}\t{mode:}\t{cluster_acc:}\t{cluster_rej:}\t{cluster_total:}\t"
                       "{streams_acc:}\t{streams_rej:}\t{streams_total:}\t{traffic:}\t{frames:}\t").format(
            strategy=self.solver,
            mode=self.mode,
            cluster_acc=-1,
            cluster_rej=-1,
            cluster_total=-1,
            streams_acc=self.flows_admitted,
            streams_rej=self.flows_total - self.flows_admitted,
            streams_total=self.flows_total,
            traffic=self.traffic_admitted,
            frames=-1  # todo
        )
        log_string += "-1\t-1\t-1\t-1\t"  # cg metrics
        log_string += "{solving_time:}\t{add_time:}\t0\t0\t0\t".format(  # time metrics
            solving_time=self.solving_time,
            add_time=self.building_time
        )
        log_string += "-0.0\t-0.0\t-0.0\t-0.0\t-0.0"  # cg prob metrics

        print(log_string)
