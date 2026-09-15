"""Prospective CPU-only queue recovery for two failed old CODE transports."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from types import FunctionType


ROOTS = {
    'ovx2': '/localhome/local-rohing/orch_r119_code_old_forks_20260915_v3/ovx2_5',
    'a40r': '/localhome/local-rohing/orch_r123_base_code_refill_20260915/a40r_5',
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_name(name):
    require(re.fullmatch(r'[a-zA-Z0-9_-]{1,100}\.request\.json', name), 'queue_filename')
    return name.removesuffix('.request.json')


def eligible(root, name, not_before, now):
    identifier = validate_name(name)
    root = Path(root)
    queue = root / 'parent_queue'
    if (queue / (identifier + '.response.json')).exists() or (root / 'parent_claude' / (identifier + '.claim')).exists():
        return False
    path = queue / name
    if not path.exists() or path.stat().st_mtime < not_before:
        return False
    request = read(path)
    require(request.get('id') == identifier, 'queue_id_join')
    deadline = request.get('lane_deadline_unix')
    require(type(deadline) in (int, float), 'request_deadline')
    return now < deadline


def listing(root, not_before, now):
    names = sorted(path.name for path in (Path(root) / 'parent_queue').glob('*.request.json'))
    return '\n'.join(name for name in names if eligible(root, name, not_before, now))


def guarded_request(delegate, allowed, store, config, launch, name, buffer, prompt_root, principles_path):
    if name == '':
        return 'EMPTY_LISTING'
    validate_name(name)
    if not allowed(name):
        return 'INELIGIBLE_NO_RETRY'
    return delegate(store, config, launch, name, buffer, prompt_root, principles_path)


def validate_recovery(recovery, config, wrapper, now):
    require(wrapper in ROOTS and config['remote_root'] == ROOTS[wrapper], 'exact_two_owned_CODE_roots')
    require(recovery['root'] == config['remote_root'] and recovery['wrapper'] == wrapper,
        'recovery_root_binding')
    require(recovery['authorization'] == 'R128_CODE_ONLY_QUEUE_RECOVERY' and
        recovery['not_before_unix'] <= now < config['deadline_unix'], 'prospective_existing_deadline')
    require(recovery['deadline_unix'] == config['deadline_unix'] and
        recovery['max_parent_calls'] == config['max_parent_calls'], 'no_cap_or_deadline_reset')
    require(not recovery['retry_old_claims'] and not recovery['change_actor'], 'transport_only_no_retry')
    for reference in recovery['local_files']:
        require(sha(reference['path']) == reference['sha256'], 'frozen_recovery_source')
    require(sha(recovery['config']['path']) == recovery['config']['sha256'], 'same_config_bytes')


def serve(recovery_path):
    from gpu import orch_r119_code_old_parent as inherited

    provider, parser = inherited.provider, inherited.parser
    recovery = read(recovery_path)
    config_path = Path(recovery['config']['path'])
    config = read(config_path)
    wrapper = recovery['wrapper']
    validate_recovery(recovery, config, wrapper, time.time())
    root = Path(config['remote_root'])
    plan_path, plan_sha = recovery['plan']['path'], recovery['plan']['sha256']
    require(not Path('/proc', str(recovery['predecessor_pid'])).exists(), 'predecessor_broker_absent')

    def remote_command(name=None):
        command = ['python3', recovery['native_source']['path'], 'list', '--root', str(root),
            '--wrapper', wrapper, '--not-before', str(recovery['not_before_unix']),
            '--source-sha256', recovery['native_source']['sha256'], '--plan-sha256', plan_sha]
        if name is not None:
            command.extend(['--name', name])
        return shlex.join(command)

    class Store(provider.Store):
        def shell(self, script, check=True):
            is_listing = script == inherited.queue.queue_listing(root)
            if is_listing:
                script = remote_command()
            return subprocess.run(['bash', str(self.repository / 'gpu' / (wrapper + '_ssh.sh')), script],
                text=True, capture_output=True, timeout=20, check=check or is_listing)

        def copy(self, source, destination):
            subprocess.run(['bash', str(self.repository / 'gpu' / (wrapper + '_scp.sh')), str(source), str(destination)],
                capture_output=True, timeout=20, check=True)

    store = Store(provider.ROOT)
    require(store.hash(recovery['native_source']['path']) == recovery['native_source']['sha256'],
        'exact_native_adapter')
    require(store.hash(plan_path) == plan_sha, 'exact_native_fork_plan')
    plan = provider.loads(store.shell('cat ' + shlex.quote(plan_path)).stdout)
    inherited.validate_scope(plan, config, wrapper)
    validation_namespace = dict(provider.validate_config.__globals__, NODE5_HARD_WALL_UNIX=plan['hard_end_unix'])
    validate_config = FunctionType(provider.validate_config.__code__, validation_namespace,
        'validate_config', provider.validate_config.__defaults__)

    def authorize(actual_config, launch, now):
        require(launch.get('authorized') is True and launch.get('config_sha256') == provider.digest(actual_config)
            and launch.get('native_plan') == dict(path=plan_path, sha256=plan_sha)
            and launch.get('authorization') == 'R119_OWN_OLD_CODE_FAST_PARENT'
            and recovery['not_before_unix'] <= now < actual_config['deadline_unix'], 'exact_existing_CPU_authorization')

    namespace = dict(provider.evaluate.__globals__, validate_config=validate_config,
        validate_launch=authorize, parse_output=parser.parse_output)
    evaluate = FunctionType(provider.evaluate.__code__, namespace, 'evaluate', provider.evaluate.__defaults__)
    evaluate.__kwdefaults__ = dict(provider.evaluate.__kwdefaults__)
    namespace = dict(provider.serve.__globals__, validate_config=validate_config,
        validate_launch=authorize, evaluate=evaluate, Store=Store)
    delegate = FunctionType(provider.process_request.__code__, namespace,
        'process_request', provider.process_request.__defaults__)

    def process_request(store, config, launch, name, buffer, prompt_root, principles_path):
        def allowed(candidate):
            result = store.shell(remote_command(candidate))
            require(result.stdout in ('', candidate), 'exact_eligibility_output')
            return result.stdout == candidate
        return guarded_request(delegate, allowed, store, config, launch, name, buffer, prompt_root, principles_path)

    namespace['process_request'] = process_request
    FunctionType(provider.serve.__code__, namespace, 'serve', provider.serve.__defaults__)(
        config_path, Path(recovery['launch']['path']), Path(recovery['prompt_root']), Path(recovery['principles']))


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('phase', choices=('list', 'serve'))
    arguments.add_argument('--recovery', type=Path)
    arguments.add_argument('--root', type=Path)
    arguments.add_argument('--wrapper', choices=tuple(ROOTS))
    arguments.add_argument('--not-before', type=float)
    arguments.add_argument('--source-sha256')
    arguments.add_argument('--plan-sha256')
    arguments.add_argument('--name')
    options = arguments.parse_args()
    if options.phase == 'serve':
        serve(options.recovery)
    else:
        require(str(options.root) == ROOTS[options.wrapper], 'exact_native_root')
        require(sha(__file__) == options.source_sha256 and sha(options.root / 'PLAN.json') == options.plan_sha256,
            'native_source_and_plan_pins')
        if options.name is None:
            sys.stdout.write(listing(options.root, options.not_before, time.time()))
        elif eligible(options.root, options.name, options.not_before, time.time()):
            sys.stdout.write(options.name)
