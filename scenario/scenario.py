import json
import math
from dataclasses import dataclass
from typing import List


@dataclass
class Stream:
    id: str

    source: str
    destination: str
    cycle_time_ns: int
    frame_size_B: int
    max_delay_ns: int

    def __init__(self, json_stream):
        self.id: str = json_stream['id']
        # todo is there a reason for source and target being a list? Do we need to account for multiple sources/targets?
        self.source: str = json_stream['source'][0]
        self.destination: str = json_stream['target'][0]
        self.cycle_time_ns: int = int(json_stream['cycle_time_ns'])
        self.frame_size_B: int = int(json_stream['frame_size_b'])
        self.max_delay_ns: int = int(json_stream['max_delay_ns'])


@dataclass
class Scenario:
    streams: List[Stream]
    hyper_cycle: int

    def __init__(self, scenario_path):
        self.streams = []
        with open(scenario_path) as scenario_file:
            # create stream objects
            for _, json_stream in json.load(scenario_file).items():
                self.streams.append(Stream(json_stream))

            periods = set([stream.cycle_time_ns for stream in self.streams])
            self.hyper_cycle = math.lcm(*periods)

    def get_stream_ids(self):
        return [stream.id for stream in self.streams]
