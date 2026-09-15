"""A3 canonical-lease broker custody without rewriting the original queue ledger."""

import argparse
import json
from pathlib import Path
import shlex
from types import FunctionType

from gpu import orch_r108_code_parent_r118_astra_shared as shared


def mapped(path, root, service):
    path, root, service = Path(path), Path(root), Path(service)
    if path in (root / 'TERMINAL.json', root / 'SHARED_TERMINAL.json'):
        return service / 'GUARD_TERMINAL.json'
    if path == root / 'parent_claude/CONFIG.json':
        return service / 'BROKER_LEDGER_CONFIG.json'
    return path


def validate_binding(config, original, runtime, policy, campaign):
    require = shared.astra.transport.require
    require(config == dict(original, deadline_unix=runtime['train_end_unix']),
        'only_canonical_deadline_changes_original_broker')
    require(runtime['schema'] == 'R119_CODE_LEASE_RUNTIME_V1'
        and runtime['root'] == config['remote_root'] == str(shared.ROOT), 'own_A3_lease_runtime')
    require(policy['train_end_unix'] == runtime['train_end_unix'] == campaign['deadline_unix']
        and policy['hard_end_unix'] == runtime['hard_end_unix']
        and campaign['root'] == runtime['common_root'], 'one_Main_clock_campaign')


def serve(config_path, launch_path, prompt_root, principles_path, custody_path):
    astra = shared.astra
    transport = astra.transport
    config = transport.loads(Path(config_path).read_text())
    launch = transport.loads(Path(launch_path).read_text())
    custody = transport.loads(Path(custody_path).read_text())
    root, service = Path(config['remote_root']), Path(custody['service'])
    store = transport.Store(transport.ROOT)
    shared.verify_gate(store, config, launch)
    def remote(reference):
        transport.require(store.hash(reference['path']) == reference['sha256'], 'exact_remote_custody_pin')
        return transport.loads(store.shell('cat ' + shlex.quote(reference['path'])).stdout)
    runtime = remote(custody['runtime'])
    pointers = remote(runtime['pointers'])
    historical = remote(pointers['original_broker_config'])
    original = remote(custody['actual_predecessor_config'])
    transport.require({key: value for key, value in original.items() if key not in ('source_files', 'deadline_unix')}
        == {key: value for key, value in historical.items() if key not in ('source_files', 'deadline_unix')},
        'same_original_queue_scope_caps_and_prompt_settings')
    transport.require(store.hash(root / 'parent_claude/CONFIG.json') == custody['actual_predecessor_config']['sha256'],
        'actual_predecessor_ledger_config_preserved')
    policy = remote(runtime['lease_policy'])
    campaign = remote(runtime['campaign'])
    validate_binding(config, original, runtime, policy, campaign)
    transport.require(service == Path(runtime['service']) and custody['root'] == str(root), 'same_A3_service')

    class Store(transport.Store):
        def exists(self, path):
            return super().exists(mapped(path, root, service))

        def hash(self, path):
            return super().hash(mapped(path, root, service))

        def copy(self, source, destination):
            if str(destination).startswith('NODE:'):
                destination = 'NODE:' + str(mapped(str(destination)[5:], root, service))
            return super().copy(source, destination)

    namespace = dict(transport.serve.__globals__, evaluate=astra.evaluate,
        validate_launch=astra.authorize, Store=Store)
    namespace['process_request'] = FunctionType(transport.process_request.__code__, namespace,
        'process_request', transport.process_request.__defaults__)
    FunctionType(transport.serve.__code__, namespace, 'serve', transport.serve.__defaults__)(
        config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'launch-receipt', 'prompt-root', 'principles', 'custody'):
        parser.add_argument('--' + name, type=Path, required=True)
    arguments = parser.parse_args()
    serve(arguments.config, arguments.launch_receipt, arguments.prompt_root,
        arguments.principles, arguments.custody)
