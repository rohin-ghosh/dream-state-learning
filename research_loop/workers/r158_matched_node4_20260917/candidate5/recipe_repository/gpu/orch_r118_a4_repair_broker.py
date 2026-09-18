"""Prospective A4 repair-terminal binding; old failures and requests stay intact."""

import argparse
import inspect
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r118_a4_shared_broker as prior


READY = prior.ROOT / 'shared_repair_v1/READY.json'
READY_SHA = '5716e34f1303a11052e37aec6bca6114ecb64fb2f0a771bf716c52a1b5f7b43e'
TERMINAL = 'R118_SHARED_REPAIR_TERMINAL.json'
transport = prior.transport


def validate_ready(document):
    transport.require(document['root'] == str(prior.ROOT)
        and document['schema'] == 'R118_GRID_SHARED_NO_REPLAY_REPAIR_V1'
        and document['terminal_filename'] == TERMINAL
        and document['bounds']['parent_wait_seconds'] == 120
        and document['bounds']['max_parent_calls'] == 298
        and document['bounds']['hard_end_unix'] == 1789491720.0
        and document['parent_requests_redispatched'] == 0,
        'exact_A4_repair_era_and_unchanged_bounds')


def historical(name):
    return name in {f'P{number:04d}.request.json' for number in range(1, 33)}


def serve(config_path, launch_path, prompt_root, principles_path):
    transport.require(transport.sha(Path(transport.__file__)) == prior.TRANSPORT_SHA,
        'unchanged_frozen_HTTP_transport')
    config = transport.loads(Path(config_path).read_text())
    transport.require(config['remote_root'] == str(prior.ROOT) and config['life_id'] == 'F4_ASTRA',
        'owned_A4_only')
    store = transport.Store(transport.ROOT)
    transport.require(store.hash(READY) == READY_SHA, 'exact_Herschel_READY')
    ready = transport.loads(store.shell('cat '+shlex.quote(str(READY))).stdout)
    validate_ready(ready)
    transport.require(store.hash(prior.ROOT/'SHARED_TERMINAL.json') ==
        ready['preserved_files']['SHARED_TERMINAL.json'], 'old_FAILED_terminal_preserved')
    namespace = dict(transport.serve.__globals__, evaluate=prior.previous.evaluate,
        validate_launch=prior.previous.astra.authorize)
    original = FunctionType(transport.process_request.__code__, namespace,
        'process_request', transport.process_request.__defaults__)

    def prospective(store, config, launch, name, buffer, prompt_root, principles_path):
        if historical(name) or store.exists(prior.ROOT/'parent_received'/name.replace('.request.json','.json')):
            return 'HISTORICAL_NO_REDISPATCH'
        return original(store, config, launch, name, buffer, prompt_root, principles_path)

    namespace['process_request'] = prospective
    source = prior.terminal_source(inspect.getsource(transport.serve))
    transport.require(source.count("'SHARED_TERMINAL.json'") == 1, 'one_terminal_binding')
    source = source.replace("'SHARED_TERMINAL.json'", repr(TERMINAL), 1)
    exec(compile(source, __file__+':repair_terminal', 'exec'), namespace)
    return namespace['serve'](config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles)
