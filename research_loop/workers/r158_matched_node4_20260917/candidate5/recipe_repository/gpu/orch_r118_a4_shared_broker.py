"""Terminal-only A4 broker successor over the frozen, charged HTTP transport."""

import argparse
import inspect
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r118_node3_6_grid_broker_http as previous


TRANSPORT_SHA = '6d2dc623cf1e7000175de78160d6f791ac040ad3679bbd6ae852529b8db1cb99'
ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/A4')
transport = previous.astra.transport


def terminal_source(source):
    old = "store.exists(root / 'TERMINAL.json')"
    transport.require(source.count(old) == 1, 'exact_frozen_terminal_check')
    return source.replace(old, "store.exists(root / 'SHARED_TERMINAL.json')", 1)


def validate_release(document):
    transport.require(document.get('root') == str(ROOT) and document.get('branch') == 'A4'
        and document.get('status') == 'RELEASED' and document.get('all_predecessors_exited') is True
        and document.get('all_charged_captures_preserved') is True
        and document.get('no_calls_retried') is True and document.get('next_cycle', 0) > 0,
        'actual_A4_release_required')
    transport.require(document['bounds']['parent_wait_seconds'] == 120
        and document['bounds']['max_parent_calls'] == 298
        and document['bounds']['hard_end_unix'] == 1789491720.0, 'same_A4_bounds')


def serve(config_path, launch_path, prompt_root, principles_path):
    transport.require(transport.sha(Path(transport.__file__)) == TRANSPORT_SHA,
        'unchanged_frozen_HTTP_transport')
    config = transport.loads(Path(config_path).read_text())
    transport.require(config['remote_root'] == str(ROOT) and config['life_id'] == 'F4_ASTRA',
        'owned_A4_only')
    store = transport.Store(transport.ROOT)
    released = transport.loads(store.shell('cat ' + shlex.quote(str(
        ROOT / 'R118_SHARED_RELEASE/RELEASED.json'))).stdout)
    validate_release(released)
    namespace = dict(transport.serve.__globals__, evaluate=previous.evaluate,
        validate_launch=previous.astra.authorize)
    namespace['process_request'] = FunctionType(transport.process_request.__code__, namespace,
        'process_request', transport.process_request.__defaults__)
    exec(compile(terminal_source(inspect.getsource(transport.serve)),
        __file__ + ':shared_terminal', 'exec'), namespace)
    return namespace['serve'](config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles)
