"""Node-local, terminal-only custody of an unchanged frozen Claude broker."""

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shlex
import sys
import time


SCHEMA = 'R118_CLAUDE_TERMINAL_CUSTODY_V1'
TERMINALS = {'F1': 'R118_PARALLEL_TERMINAL.json', 'F2': 'GUARD_TERMINAL.json',
    'F3': 'GUARD_TERMINAL.json', 'F4': 'R118_GRID_PARALLEL_TERMINAL.json'}
ROOTS = {'F1': '/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1',
    'F2': '/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane1',
    'F3': '/localhome/local-rohing/orch_r108_code_parent_r115_node5_2_20260915_attempt1',
    'F4': '/localhome/local-rohing/orch_r115_grid_pair_20260915/F4'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def bound(item):
    path = Path(item['path'])
    require(path.is_absolute() and not path.is_symlink() and sha(path) == item['sha256'], 'exact_bound_file')
    return read(path)


def claim_inventory(root):
    ledger = Path(root) / 'parent_claude'
    claims = sorted(ledger.glob('*.claim'))
    require(all((path / 'PUBLISHED.json').is_file() for path in claims), 'no_inflight_or_unpublished_claim_handoff')
    return {str(path.relative_to(ledger)): sha(path) for claim in claims
        for path in sorted(claim.rglob('*')) if path.is_file()}


def identity():
    directory = Path('/proc') / str(os.getpid())
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=os.getpid(), uid=os.getuid(), start_ticks=fields[19], ppid=int(fields[1]),
        command_sha256=sha(directory / 'cmdline'), cwd=str((directory / 'cwd').resolve()),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def write_once(path, value):
    path = Path(path)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def validate(binding, now):
    require(binding['schema'] == SCHEMA and binding['branch'] in ROOTS, 'owned_Claude_branch')
    branch = binding['branch']
    require(binding['root'] == ROOTS[branch], 'original_queue_root_only')
    require(binding['not_before_unix'] <= now < binding['migration_end_unix'], 'explicit_migration_window')
    require(binding['wrapper_sha256'] == sha(__file__), 'wrapper_source_pin')
    config = bound(binding['config'])
    require(config['branch'] == branch and config['remote_root'] == binding['root']
        and config.get('queue_transport') == 'node_local', 'same_node_local_original_configuration')
    require(sha(Path(binding['root']) / 'parent_claude/CONFIG.json') == binding['config']['sha256'],
        'actual_active_ledger_config')
    require(config['max_parent_calls'] == binding['parent_cap']
        and config['deadline_unix'] == binding['deadline_unix'], 'no_cap_or_deadline_reset')
    release = bound(binding['release'])
    require(release['status'] == 'RELEASED' and release['root'] == binding['root'], 'actual_owner_release')
    runtime = bound(binding['runtime'])
    campaign = bound(binding['campaign'])
    require(campaign['schema'] == 'R118_PARALLEL_CAMPAIGN_V1', 'actual_common_campaign')
    bound(binding['authorization'])
    terminal = Path(binding['terminal_path'])
    require(terminal.is_absolute() and terminal.name == TERMINALS[branch]
        and terminal.is_relative_to('/localhome/local-rohing'), 'real_family_terminal_only')
    require(not terminal.exists(), 'successor_already_terminal_no_restart')
    writer = Path(binding['terminal_writer']['path'])
    require(sha(writer) == binding['terminal_writer']['sha256']
        and TERMINALS[branch] in writer.read_text(), 'bound_actual_terminal_writer')
    require(claim_inventory(binding['root']) == binding['prior_claim_files'], 'old_claims_and_publications_unchanged')
    if branch == 'F1':
        require(terminal.parent == Path(binding['root']) and runtime['parent_wait_seconds'] == 120,
            'route_real_terminal_and_wait')
    elif branch == 'F2':
        require(runtime['release'] == binding['release'] and runtime['campaign'] == binding['campaign']
            and runtime['inherited_bounds']['parent_calls'] == config['max_parent_calls']
            and runtime['inherited_bounds']['native_end_unix'] == config['deadline_unix'], 'math_runtime_custody')
        require(terminal.parent == Path(binding['runtime']['path']).parent, 'math_service_terminal')
    elif branch == 'F3':
        require(runtime['root'] == binding['root'] and runtime['schema'] == 'R118_CODE_PARALLEL_RUNTIME_V1'
            and terminal.parent == Path(binding['runtime']['path']).parent, 'code_runtime_custody')
    else:
        require(terminal.parent == Path(binding['root']), 'grid_real_root_terminal')
    return config, runtime


def ready_record(binding, runtime):
    record = dict(runtime=binding['runtime'], terminal_path=binding['terminal_path'], identity=identity(),
        actual_single_lane_lock_acquired=True, config_sha256=binding['config']['sha256'],
        source=reference(Path(__file__).resolve()), observed_unix=time.time(), provider='EXISTING_CLAUDE_FABLE',
        claims_preserved=True, provider_retries=0, campaign=binding['campaign'])
    if binding['branch'] == 'F1':
        record.update(root=binding['root'], plan=binding['runtime'], terminal=TERMINALS['F1'],
            parent_wait_seconds=120, provider=runtime['provider'])
    return record


def install(base, binding, config, runtime):
    original_store = base.NodeLocalStore
    lock_command = 'mkdir ' + shlex.quote(str(Path(binding['root']) / 'parent_claude/RUNNER.lock'))

    class BoundStore(original_store):
        def shell(self, script, check=True):
            result = super().shell(script, check=check)
            if script == lock_command and result.returncode == 0:
                try:
                    require(claim_inventory(binding['root']) == binding['prior_claim_files'], 'claims_stable_at_lock')
                    write_once(binding['ready_path'], ready_record(binding, runtime))
                except BaseException:
                    super().shell('rmdir ' + shlex.quote(str(Path(binding['root']) / 'parent_claude/RUNNER.lock')))
                    raise
            return result

    def terminal_path(actual):
        require(actual == config, 'broker_config_unchanged')
        return Path(binding['terminal_path'])

    base.NodeLocalStore = BoundStore
    base.terminal_path = terminal_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not any((path / '.git').exists()
        for path in Path(__file__).resolve().parents), 'CPU_frozen_runtime_only')
    binding = read(args.binding)
    config, runtime = validate(binding, time.time())
    sys.path.insert(0, binding['legacy_source_root'])
    base = importlib.import_module('gpu.orch_r110_claude_broker')
    require(sha(base.__file__) == config['source_files']['gpu/orch_r110_claude_broker.py'], 'exact_legacy_broker_bytes')
    base.validate_config(config)
    require(sha(binding['launch_path']) == binding['launch_sha256'], 'unchanged_original_launch_receipt')
    base.validate_launch(config, read(binding['launch_path']), time.time())
    if args.check:
        print(json.dumps(dict(status='BOUND_NOT_LAUNCHED', branch=binding['branch'], terminal=binding['terminal_path'])))
        return
    install(base, binding, config, runtime)
    base.serve(binding['config']['path'], binding['launch_path'], binding['prompt_root'], binding['principles_path'])


if __name__ == '__main__':
    main()
