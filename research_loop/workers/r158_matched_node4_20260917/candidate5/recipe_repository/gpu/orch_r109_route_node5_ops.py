"""Separate node5 source/bindings; never mutates an existing live source tree."""

import argparse
from pathlib import Path

from gpu import orch_r109_route_ops as operations
from gpu import orch_r109_route_node5_run as run
from gpu.orch_r109_route_node5_broker import Store
from organism_v6 import orch_r109_route_node5 as policy


def configure():
    operations.policy=policy
    operations.run=run
    operations.Store=Store
    operations.ROOTS={lane:Path(run.ROOT_PREFIX+lane+'_attempt1') for lane in policy.LANES}
    operations.RUN_MODULE='gpu.orch_r109_route_node5_run'
    operations.BROKER_MODULE='gpu.orch_r109_route_node5_broker'
    operations.SCAN_MODULE='gpu.orch_r109_route_node5_scan'
    operations.TEST_MODULE='tests.test_orch_r109_route_node5'


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('deploy','launch','status'))
    parser.add_argument('--lane',required=True,choices=policy.LANES)
    args=parser.parse_args()
    configure()
    getattr(operations,args.phase)(args.lane)
