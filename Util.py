from scenario.scenario import Stream


def get_frames_per_hc(stream: Stream, hyper_cycle: int) -> int:
    return int(hyper_cycle / stream.cycle_time_ns)


def iterate_frames_per_hc(stream: Stream, hyper_cycle: int) -> range:
    return range(0, get_frames_per_hc(stream, hyper_cycle), 1)
