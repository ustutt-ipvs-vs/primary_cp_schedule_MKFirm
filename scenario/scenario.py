import json
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
        self.id = json_stream['id']
        # todo is there a reason for source and target being a list? Do we need to account for multiple sources/targets?
        self.source = json_stream['source'][0]
        self.destination = json_stream['target'][0]
        self.cycle_time_ns = json_stream['cycle_time_ns']
        self.frame_size_B = json_stream['frame_size_b']
        self.max_delay_ns = json_stream['max_delay_ns']


@dataclass
class Scenario:

    streams: List[Stream]

    def __init__(self, scenario_path):
        self.streams = []
        with open(scenario_path) as scenario_file:
            # create stream objects
            for _, json_stream in json.load(scenario_file).items():
                self.streams.append(Stream(json_stream))
