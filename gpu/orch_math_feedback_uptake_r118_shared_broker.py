"""Prospective A2 terminal-path handoff; unchanged HTTP slots, config and ledger."""

import argparse
from pathlib import Path
import shlex

from gpu import orch_math_feedback_uptake_r118_broker as delivery


shared = delivery.shared
LANE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane5')


def terminal_path(path):
    path = Path(path)
    return LANE/'SHARED_TERMINAL.json' if path == LANE/'TERMINAL.json' else path


def validate_binding(store, config_path, binding):
    config = shared.loads(Path(config_path).read_text())
    shared.validate_config(config)
    shared.require(config['remote_root'] == str(LANE) and binding['root'] == str(LANE), 'A2_only_shared_terminal')
    shared.require(shared.sha(config_path) == binding['config_sha256'], 'unchanged_A2_broker_config')
    shared.require(not (Path('/proc')/str(binding['prior_broker_identity']['pid'])).exists(), 'old_A2_broker_exited')
    for name, digest in binding['source_files'].items():
        shared.require(shared.sha(shared.ROOT/name) == digest, 'exact_successor_broker_source')
    required = {'gpu/orch_math_feedback_uptake_r118_shared_broker.py',
        'gpu/orch_math_feedback_uptake_r118_broker.py', 'gpu/orch_r118_astra_slots.py'}
    shared.require(required.issubset(binding['source_files']), 'HTTP_slot_wrapper_source_binding')
    documents = {}
    for key, expected_path in (('release', LANE/'shared_handoff_r118/release/RELEASED.json'),
            ('activation', LANE/'SHARED_ACTIVATION.json'), ('ready', LANE/'SHARED_CLIENT_READY.json')):
        reference = binding[key]
        shared.require(reference['path'] == str(expected_path) and store.hash(expected_path) == reference['sha256'],
            'exact_native_shared_'+key)
        documents[key] = shared.loads(store.shell('cat '+shlex.quote(str(expected_path))).stdout)
    activation, release, ready = (documents[key] for key in ('activation', 'release', 'ready'))
    shared.require(release['status'] == 'RELEASED' and release['root'] == str(LANE), 'actual_A2_native_release')
    shared.require(activation['release'] == binding['release'] and activation['ready_sha256'] == binding['ready']['sha256']
        and activation['shared_learner']['branch'] == 'A2', 'same_native_activation')
    shared.require(activation['inherited_bounds']['native_end_unix'] == config['deadline_unix']
        and activation['inherited_bounds']['parent_calls'] == config['max_parent_calls']
        and ready['command_module'] == 'gpu.orch_math_feedback_uptake_r118_shared_run', 'original_bounds_runnable_successor')
    shared.require(store.hash(LANE/'parent_claude/CONFIG.json') == binding['config_sha256'], 'original_ledger_config')
    shared.require(binding['drain_verified'] is True and binding['charged_retries'] == 0, 'all_prior_claims_verified_no_retry')
    return config


def serve(config_path, launch_path, prompt_root, principles_path, binding_path):
    binding = shared.loads(Path(binding_path).read_text())
    base_store, old_evaluate = shared.Store, shared.evaluate
    validate_binding(base_store(shared.ROOT), config_path, binding)
    class SharedTerminalStore(base_store):
        def exists(self, path):
            return super().exists(terminal_path(path))
    try:
        shared.Store = SharedTerminalStore
        shared.evaluate = delivery.astra_evaluate
        return shared.serve(config_path, launch_path, prompt_root, principles_path)
    finally:
        shared.Store, shared.evaluate = base_store, old_evaluate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles, args.binding)
