"""Fresh native phases for the explicitly new interrupted-life replicate."""

import argparse
import importlib.util
from pathlib import Path
import signal

from gpu import orch_math_pipeline_l2_run as common


def bind_driver(path):
    specification = importlib.util.spec_from_file_location('math_replicate_driver', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    module.bind_retention()
    return module.frozen_native


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=('GUIDED_SLEEP', 'UNPARENTED_SLEEP'), required=True)
    parser.add_argument('--cycle', type=int, required=True)
    parser.add_argument('--phase', choices=('experience', 'readout'), required=True)
    options = parser.parse_args()
    assert options.root.name == 'campaign_02_recovery_paired'
    ready = common.read(options.root / 'REPLICATE_READY.json')
    assert common.sha(Path(__file__)) == ready['native_driver_sha256']
    continuation = Path(__file__).with_name('orch_math_pipeline_l2_native_continue.py')
    assert common.sha(continuation) == ready['retention_driver_sha256']
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    bind_driver(continuation).run(options.root, options.arm, options.cycle, options.phase)
