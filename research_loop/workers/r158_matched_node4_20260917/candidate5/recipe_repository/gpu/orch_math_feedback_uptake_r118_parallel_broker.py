"""A2 custody wrapper: existing HTTP slots/claims, new authentic guard terminal."""

import argparse
import json
import os
from pathlib import Path
import shlex
import tempfile
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r118_broker as delivery
from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life


base, require = delivery.shared, delivery.shared.require


def namespace(config_path, binding_path):
    config = base.loads(Path(config_path).read_text())
    binding = base.loads(Path(binding_path).read_text())
    base.validate_config(config)
    root = life.client.BRANCHES['A2']
    service = life.service_for('A2')
    require(config['remote_root'] == binding['root'] == str(root) and binding['service'] == str(service),
            'A2_only_original_queue_and_new_service')
    require(base.sha(config_path) == binding['config_sha256'], 'unchanged_original_A2_broker_config')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_broker')
    store = base.NodeLocalStore(base.ROOT) if config.get('queue_transport') == 'node_local' else base.Store(base.ROOT)
    require(store.hash(root/'parent_claude/CONFIG.json') == base.sha(config_path), 'actual_active_A2_ledger_config')
    for name in ('runtime', 'release'):
        reference = binding[name]
        require(store.hash(reference['path']) == reference['sha256'], 'actual_node_'+name+'_hash')
    runtime = base.loads(store.shell('cat '+shlex.quote(binding['runtime']['path'])).stdout)
    released = base.loads(store.shell('cat '+shlex.quote(binding['release']['path'])).stdout)
    require(runtime['release'] == binding['release'] and released['status'] == 'RELEASED'
            and released['root'] == str(root), 'authentic_same_life_release_not_NEW_ledger')
    require(runtime['inherited_bounds']['parent_calls'] == config['max_parent_calls']
            and runtime['inherited_bounds']['native_end_unix'] == config['deadline_unix'], 'unchanged_parent_budget_deadline')
    terminal = service/'GUARD_TERMINAL.json'
    def terminal_path(actual_config):
        require(actual_config == config, 'unchanged_broker_configuration')
        return terminal
    def publishing_store(parent):
        class PublishingStore(parent):
            def exists(self, path):
                path = Path(path)
                if path in (root/'TERMINAL.json', root/'SHARED_TERMINAL.json'):
                    path = terminal
                return super().exists(path)

            def shell(self, script, check=True):
                result = super().shell(script, check=check)
                if script == 'mkdir '+shlex.quote(str(root/'parent_claude/RUNNER.lock')) and result.returncode == 0:
                    record = dict(runtime=binding['runtime'], terminal_path=str(terminal),
                        identity=life.identity(os.getpid()), broker_locality=config.get('queue_transport', 'ssh'),
                        actual_single_lane_lock_acquired=True, config_sha256=base.sha(config_path),
                        provider='EXISTING_STRONG_ASTRA_HTTP_SLOTS', observed_unix=time.time())
                    with tempfile.TemporaryDirectory(prefix='orch_math_parallel_broker_') as directory:
                        path = Path(directory)/'BROKER_READY.json'
                        base.write(path, record)
                        require(not self.exists(service/'BROKER_READY.json'), 'single_NEW_broker_receipt')
                        self.copy(path, 'NODE:'+str(service/'BROKER_READY.json'))
                        require(self.hash(service/'BROKER_READY.json') == base.sha(path), 'node_broker_ready_hash')
                return result
        return PublishingStore
    values = dict(vars(base))
    for name, value in vars(base).items():
        if isinstance(value, FunctionType) and value.__module__ == base.__name__:
            values[name] = FunctionType(value.__code__, values, name, value.__defaults__, value.__closure__)
            values[name].__kwdefaults__ = value.__kwdefaults__
    values.update(Store=publishing_store(base.Store), terminal_path=terminal_path, evaluate=delivery.astra_evaluate)
    if hasattr(base, 'NodeLocalStore'):
        values['NodeLocalStore'] = publishing_store(base.NodeLocalStore)
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    args = parser.parse_args()
    namespace(args.config, args.binding)['serve'](args.config, args.launch_receipt, args.prompt_root, args.principles)


if __name__ == '__main__':
    main()
