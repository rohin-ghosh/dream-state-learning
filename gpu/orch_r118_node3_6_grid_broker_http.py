"""Prospective direct-HTTP Astra slots for the three owned grid parent lanes."""

import argparse
import inspect
from pathlib import Path
from types import FunctionType

from gpu import orch_r115_grid_astra as astra
from gpu import orch_r118_astra_slots as slots
from gpu import orch_r118_a1004_grid_broker as a100
from gpu import orch_r118_node3_6_grid_broker as node3


LANES = {
    'A4': ('/localhome/local-rohing/orch_r115_grid_pair_20260915/A4', 'F4_ASTRA', astra.transport.Store),
    'A1004': (str(a100.run.ROOT), a100.run.LIFE_ID, a100.Store),
    'NODE3_6': (str(node3.run.ROOT), node3.run.LIFE_ID, node3.Store),
}


def evaluator():
    source = inspect.getsource(astra.evaluate)
    before = "with Path(lock_path).open('a') as lock:\n            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)"
    astra.transport.require(source.count(before) == 1, 'exact_original_parent_lock_statement')
    after = "with slots.acquire(cutoff) as slot_receipt:\n            transport.write(directory/'HTTP_SLOT.json', slot_receipt)"
    namespace = dict(astra.evaluate.__globals__, slots=slots)
    exec(compile(source.replace(before, after, 1), __file__ + ':http_slot_evaluator', 'exec'), namespace)
    return namespace['evaluate']


evaluate = evaluator()


def serve(lane, config_path, launch_path, prompt_root, principles_path):
    astra.transport.require(lane in LANES, 'owned_grid_http_lane')
    root, life_id, store = LANES[lane]
    config = astra.transport.loads(Path(config_path).read_text())
    astra.transport.require(config['remote_root'] == root and config['life_id'] == life_id,
                            'exact_existing_grid_parent_lane')
    namespace = dict(astra.transport.serve.__globals__, Store=store, evaluate=evaluate,
                     validate_launch=astra.authorize)
    namespace['process_request'] = FunctionType(astra.transport.process_request.__code__, namespace,
        'process_request', astra.transport.process_request.__defaults__)
    return FunctionType(astra.transport.serve.__code__, namespace, 'serve',
                        astra.transport.serve.__defaults__)(config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', choices=tuple(LANES), required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.lane, args.config, args.launch_receipt, args.prompt_root, args.principles)
