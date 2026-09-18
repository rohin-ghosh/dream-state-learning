"""Explicit retention-seam repair without modifying the original native archive."""

import argparse
from pathlib import Path
import signal

from gpu import astra_event_two_hop_memory as retention
from gpu import orch_full_rich
from gpu import orch_math_pipeline_l2_native as frozen_native


def bind_retention():
    assert callable(retention.recall) and callable(retention.audit.collect_cases)
    orch_full_rich.memory = retention


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=frozen_native.policy.ARMS, required=True)
    parser.add_argument('--cycle', type=int, required=True)
    parser.add_argument('--phase', choices=('experience', 'readout'), required=True)
    options = parser.parse_args()
    assert options.cycle in (1, 2, 3), 'failed_baseline_never_retried'
    bind_retention()
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    frozen_native.run(options.root, options.arm, options.cycle, options.phase)
