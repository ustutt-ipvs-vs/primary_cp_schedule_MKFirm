import json
import math
from dataclasses import dataclass
from typing import List


@dataclass
class Stream:
    id: int
    name: str

    source: int
    destination: int
    cycle_time_ns: int
    frame_size_byte: int
    deadline_ns: int

    def __init__(self, json_stream):
        if json_stream is not None:
            self.id = int(json_stream['id'])
            self.name = json_stream['name']
            self.source = int(json_stream['source'])
            self.destination = int(json_stream['target'])
            self.cycle_time_ns = int(json_stream['cycle_time_ns'])
            self.frame_size_byte = int(json_stream['frame_size_byte'])
            self.deadline_ns = int(json_stream['deadline_ns'])


@dataclass
class Scenario:
    streams: List[Stream]
    hyper_cycle: int

    def __init__(self, scenario_path):
        self.streams = []
        with open(scenario_path) as scenario_file:
            # create stream objects
            for json_stream in json.load(scenario_file):
                self.streams.append(Stream(json_stream))

            periods = set([stream.cycle_time_ns for stream in self.streams])
            self.hyper_cycle = math.lcm(*periods)

    def get_stream_ids(self):
        return [stream.id for stream in self.streams]
