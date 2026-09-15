"""Prospective parent slots after P0040; unchanged HTTP source and charged ledger."""

import argparse
import inspect
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r118_node3_6_grid_broker_http as previous


ROOT = Path('/localhome/local-rohing/orch_r118_node3_6_grid_20260915_attempt1')
TERMINAL = 'R118_NODE3_6_RECOVERY_TERMINAL.json'
OLD_SHA = '7f68c9cf541fa2d3d10c78f8ebfa48ebfbc78afd436d2272b387aaa783444b7c'
TRANSPORT_SHA = '6d2dc623cf1e7000175de78160d6f791ac040ad3679bbd6ae852529b8db1cb99'
transport = previous.astra.transport


def historical(name):
    return name in {f'P{number:04d}.request.json' for number in range(1, 41)}


def terminal_source(source):
    old = "store.exists(root / 'TERMINAL.json')"
    transport.require(source.count(old) == 1, 'one_frozen_terminal_site')
    return source.replace(old, "store.exists(root / '" + TERMINAL + "')", 1)


def serve(config_path, launch_path, prompt_root, principles_path):
    transport.require(transport.sha(Path(transport.__file__)) == TRANSPORT_SHA, 'same_HTTP_source')
    config = transport.loads(Path(config_path).read_text())
    transport.require(config['remote_root'] == str(ROOT) and config['life_id'] == 'R118_NODE3_6_ASTRA',
                      'only_owned_node3_6')
    store = previous.node3.Store(transport.ROOT)
    transport.require(store.hash(ROOT / 'TERMINAL.json') == OLD_SHA, 'failed_original_terminal_unchanged')
    ready = transport.loads(store.shell('cat ' + shlex.quote(str(ROOT / 'recovery_1336_v1/CPU_READY.json'))).stdout)
    transport.require(ready['status'] == 'PASS' and ready['terminal_filename'] == TERMINAL
        and ready['state']['next_cycle'] == 9 and ready['state']['inherited_parent_charges'] == 40,
        'same_life_recovery_era')
    namespace = dict(transport.serve.__globals__, Store=previous.node3.Store, evaluate=previous.evaluate,
                     validate_launch=previous.astra.authorize)
    original = FunctionType(transport.process_request.__code__, namespace, 'process_request',
                            transport.process_request.__defaults__)

    def prospective(store, config, launch, name, buffer, prompt_root, principles_path):
        if historical(name) or store.exists(ROOT / 'parent_received' / name.replace('.request.json', '.json')):
            return 'HISTORICAL_NO_REDISPATCH'
        return original(store, config, launch, name, buffer, prompt_root, principles_path)

    namespace['process_request'] = prospective
    exec(compile(terminal_source(inspect.getsource(transport.serve)), __file__ + ':recovery_terminal', 'exec'), namespace)
    return namespace['serve'](config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles)
