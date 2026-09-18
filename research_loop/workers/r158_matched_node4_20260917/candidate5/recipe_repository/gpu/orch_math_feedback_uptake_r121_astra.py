"""A2 low-effort asynchronous HTTP custody over its preserved original queue."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import tempfile
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_math_feedback_uptake_r118_broker as delivery
from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life


base, require = delivery.shared, delivery.shared.require


def low_settings(document):
    settings = delivery.tomllib.loads(document)
    require(settings['model'] == delivery.STRONG, 'existing_strong_model_only')
    result = deepcopy(settings)
    result['model_reasoning_effort'] = 'low'
    return result


def evaluate(*args, **kwargs):
    namespace = dict(delivery.astra_evaluate.__globals__, tomllib=SimpleNamespace(loads=low_settings))
    function = FunctionType(delivery.astra_evaluate.__code__, namespace, 'astra_low_once',
        delivery.astra_evaluate.__defaults__)
    function.__kwdefaults__ = delivery.astra_evaluate.__kwdefaults__
    return function(*args, **kwargs)


def validate_delta(config, original, plan):
    expected = dict(original, deadline_unix=plan['bounds']['train_end_unix'],
        max_parent_calls=plan['prospective_capacity']['parent'], max_output_tokens=1024)
    require(config == expected, 'only_prospective_deadline_capacity_short_budget_changes')
    require(plan['branch'] == 'A2' and plan['index'] == 5 and plan['contract']['parent_wait_seconds'] == 0,
        'owned_nonblocking_A2_only')
    require(config['remote_root'] == plan['original_root'], 'original_queue_custody')


def namespace(config_path, binding_path):
    config = base.loads(Path(config_path).read_text())
    binding = base.loads(Path(binding_path).read_text())
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_broker_only')
    base.validate_config(config)
    store = base.Store(base.ROOT)
    def remote(reference):
        require(store.hash(reference['path']) == reference['sha256'], 'exact_native_broker_binding')
        return base.loads(store.shell('cat '+shlex.quote(reference['path'])).stdout)
    original = remote(binding['original_config'])
    plan = remote(binding['plan'])
    validate_delta(config, original, plan)
    require(base.sha(config_path) == binding['config_sha256'], 'bound_prospective_config')
    root, fork = Path(plan['original_root']), Path(plan['root'])
    terminal = fork/'TERMINAL.json'
    def mapped(path):
        path = Path(path)
        if path == root/'parent_claude/CONFIG.json':
            return fork/'BROKER_LEDGER_CONFIG.json'
        if path in (root/'TERMINAL.json', root/'SHARED_TERMINAL.json'):
            return terminal
        return path
    class Store(base.Store):
        def exists(self, path):
            return super().exists(mapped(path))

        def hash(self, path):
            return super().hash(mapped(path))

        def copy(self, source, destination):
            if str(destination).startswith('NODE:'):
                destination = 'NODE:'+str(mapped(str(destination)[5:]))
            return super().copy(source, destination)

        def shell(self, script, check=True):
            result = super().shell(script, check=check)
            if script == 'mkdir '+shlex.quote(str(root/'parent_claude/RUNNER.lock')) and result.returncode == 0:
                with tempfile.TemporaryDirectory(prefix='orch_math_r121_broker_') as directory:
                    path = Path(directory)/'BROKER_READY.json'
                    base.write(path, dict(plan=binding['plan'], terminal_path=str(terminal),
                        identity=life.identity(os.getpid()), identity_location='VM',
                        config_sha256=base.sha(config_path), original_config=binding['original_config'],
                        actual_single_lane_lock_acquired=True, configured_reasoning_effort='low',
                        configured_max_output_tokens=1024, provider_calls_observed=0,
                        source=dict(path=str(Path(__file__).resolve()), sha256=base.sha(__file__)),
                        nonblocking_child=True, observed_unix=time.time()))
                    require(not self.exists(fork/'BROKER_READY.json'), 'new_actual_broker_receipt_only')
                    self.copy(path, 'NODE:'+str(fork/'BROKER_READY.json'))
                    require(self.hash(fork/'BROKER_READY.json') == base.sha(path), 'actual_native_receipt_hash')
            return result
    values = dict(vars(base))
    for name, value in vars(base).items():
        if isinstance(value, FunctionType) and value.__module__ == base.__name__:
            values[name] = FunctionType(value.__code__, values, name, value.__defaults__, value.__closure__)
            values[name].__kwdefaults__ = value.__kwdefaults__
    values.update(Store=Store, evaluate=evaluate, terminal_path=lambda config: terminal)
    return values


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('config', 'launch-receipt', 'binding', 'prompt-root', 'principles'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    namespace(args.config, args.binding)['serve'](args.config, args.launch_receipt, args.prompt_root, args.principles)
