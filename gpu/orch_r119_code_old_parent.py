"""CPU-only fast Fable transport for explicitly allocated old CODE context forks."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time
from types import FunctionType

from gpu import orch_r110_claude_broker as provider
from gpu import orch_r119_code_fable_parser as parser
from gpu import orch_r119_code_fast_astra as queue


def validate_scope(plan, config, wrapper):
    provider.require(wrapper in ('ovx2', 'a40r') and plan['wrapper'] == wrapper,
        'owned_old_CODE_wrapper')
    provider.require(plan['root'] == config['remote_root'] and plan['parent_cadence'] == 'EPISODE'
        and plan['parent_wait_seconds'] == 0 and plan['parent_ttl_seconds'] == 600,
        'nonblocking_episode_scope')
    provider.require(config['deadline_unix'] == plan['train_end_unix']
        and config['deadline_unix'] < plan['hard_end_unix'] == plan['lease_end_unix']-21600,
        'actual_old_slot_lease')
    provider.require(config['max_parent_calls'] == plan['ancestry']['parent_cap']-plan['ancestry']['parent_used']
        and config['parent_effort'] in ('low', 'medium') and config['max_output_tokens'] == 512,
        'inherited_parent_caps_and_fast_settings')


def serve(config_path, launch_path, plan_path, plan_sha256, wrapper, prompt_root, principles_path):
    config = provider.loads(Path(config_path).read_text())
    root = Path(config['remote_root'])
    class Store(provider.Store):
        def shell(self, script, check=True):
            if script == queue.queue_listing(root):
                script = queue.pending_listing(root)
            return subprocess.run(['bash', str(self.repository/'gpu'/f'{wrapper}_ssh.sh'), script],
                text=True, capture_output=True, timeout=20, check=check)

        def copy(self, source, destination):
            subprocess.run(['bash', str(self.repository/'gpu'/f'{wrapper}_scp.sh'), str(source), str(destination)],
                capture_output=True, timeout=20, check=True)

    store = Store(provider.ROOT)
    provider.require(store.hash(plan_path) == plan_sha256, 'exact_native_fork_plan')
    plan = provider.loads(store.shell('cat '+shlex.quote(str(plan_path))).stdout)
    validate_scope(plan, config, wrapper)
    validation_namespace = dict(provider.validate_config.__globals__, NODE5_HARD_WALL_UNIX=plan['hard_end_unix'])
    validate_config = FunctionType(provider.validate_config.__code__, validation_namespace, 'validate_config',
        provider.validate_config.__defaults__)
    def authorize(actual_config, launch, now):
        provider.require(launch.get('authorized') is True and launch.get('config_sha256') == provider.digest(actual_config)
            and launch.get('native_plan') == dict(path=str(plan_path), sha256=plan_sha256)
            and launch.get('authorization') == 'R119_OWN_OLD_CODE_FAST_PARENT'
            and launch.get('not_before_unix', now+1) <= now < actual_config['deadline_unix'], 'exact_old_CODE_CPU_publication')
    namespace = dict(provider.evaluate.__globals__, validate_config=validate_config,
        validate_launch=authorize, parse_output=parser.parse_output)
    evaluate = FunctionType(provider.evaluate.__code__, namespace, 'evaluate', provider.evaluate.__defaults__)
    evaluate.__kwdefaults__ = dict(provider.evaluate.__kwdefaults__)
    namespace = dict(provider.serve.__globals__, validate_config=validate_config,
        validate_launch=authorize, evaluate=evaluate, Store=Store)
    namespace['process_request'] = FunctionType(provider.process_request.__code__, namespace,
        'process_request', provider.process_request.__defaults__)
    FunctionType(provider.serve.__code__, namespace, 'serve', provider.serve.__defaults__)(
        config_path, launch_path, prompt_root, principles_path)


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    for name in ('config', 'launch-receipt', 'plan', 'prompt-root', 'principles'):
        arguments.add_argument('--'+name, type=Path, required=True)
    arguments.add_argument('--plan-sha256', required=True)
    arguments.add_argument('--wrapper', choices=('ovx2','a40r'), required=True)
    options = arguments.parse_args()
    serve(options.config, options.launch_receipt, options.plan, options.plan_sha256,
        options.wrapper, options.prompt_root, options.principles)
