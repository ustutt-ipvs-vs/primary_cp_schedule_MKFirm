from docplex.cp.model import *

from Util import iterate_frames_per_hc
from constraint_programming.cp_structs import CpParameters


def write_result_to_json(cp_result: CpoSolveResult, parameters: CpParameters, output_file: str):
    def get_transmission_var(_stream, _frame, _egress_port):
        name: str = 'transmission_port_{}_stream_{}_frame_{}'.format(_egress_port.id, _stream.id, _frame)
        return cp_result[name]

    output = []
    for stream in parameters.scenario.streams:
        stream_dict = {'stream_id': stream.id,
                       'pcp': int(cp_result[f"pcp_{stream.id}"])}
        frame_list = []
        for frame in iterate_frames_per_hc(stream, parameters.scenario.hyper_cycle):
            frame_dict = {'frame_number': frame,
                          'transmissions': []}
            transmissions = []
            for egress_port in parameters.routes[stream.id]:
                transmission = get_transmission_var(stream, frame, egress_port)
                transmission_dict = {'egress_port': egress_port.id,
                                     'start': transmission.start,
                                     'end': transmission.end}
                transmissions.append(transmission_dict)
            # end of egress_port loop
            frame_dict['transmissions'] = transmissions
            frame_list.append(frame_dict)
        # end of frame loop
        stream_dict['frames'] = frame_list
        output.append(stream_dict)
    # end of stream loop

    with open(output_file, 'w') as file:
        json.dump(output, file, indent=4)
