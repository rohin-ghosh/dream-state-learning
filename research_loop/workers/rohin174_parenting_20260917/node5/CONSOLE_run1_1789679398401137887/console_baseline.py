"""Main-delegated grounded console baseline with exact automatic-parent custody."""

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import sys
import time


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def load_runtime(manifest):
    source = Path(manifest['source'])
    for name, digest in manifest['source_pins'].items():
        require(sha(source / name) == digest, 'immutable_source_pin')
    sys.path.insert(0, str(source))
    specification = importlib.util.spec_from_file_location('bound_activation', source / 'activate_parent.py')
    runtime = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runtime)
    from gpu import orch_r166_parent_policy as policy
    require(Path(policy.tick.__code__.co_filename).resolve() == source / 'gpu/orch_r166_parent_policy.py',
            'actual_bound_r166_tick')
    runtime.install_private_errata(policy, source / 'PARENT_METADATA_ERRATA_V1.md')
    provenance = runtime.install_response_compatibility(policy, source)
    return runtime, policy, provenance


def merge_seed(policy, old_output, state):
    original = read(old_output / 'SEED.json')
    require(original['schema'] == policy.SCHEMA, 'existing_R175_seed')
    successor = copy.deepcopy(original)
    successor['attempts'].extend(policy.export_predecessor(old_output, state)['attempts'])
    require(not policy.memory(successor, [], state)['awaiting_render'], 'no_pending_publication')
    return successor


def lock_owner(path, pid):
    actual = path.stat(follow_symlinks=False)
    wanted = (os.major(actual.st_dev), os.minor(actual.st_dev), actual.st_ino)
    matches = []
    for line in Path('/proc/locks').read_text().splitlines():
        fields = line.split()
        if len(fields) < 6 or fields[1] != 'FLOCK' or fields[3] != 'WRITE':
            continue
        major, minor, inode = fields[5].split(':')
        if (int(major, 16), int(minor, 16), int(inode)) == wanted:
            matches.append(int(fields[4]))
    require(matches == [pid], 'genuine_existing_parent_flock_exact_owner')
    return dict(device=actual.st_dev, inode=actual.st_ino, owner_pid=pid)


def parent_census(root, own_pid):
    owners = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == own_pid:
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            arguments = (entry / 'cmdline').read_bytes().decode().split('\0')
            if not any('parent' in value.lower() or value.endswith('refresh.py') for value in arguments[:5]):
                continue
            config_path = None
            if '--manifest' in arguments:
                manifest = read(arguments[arguments.index('--manifest') + 1])
                config_path = manifest['predecessor']['config']['path']
            elif '--config' in arguments:
                config_path = arguments[arguments.index('--config') + 1]
            elif '--binding' in arguments:
                binding = read(arguments[arguments.index('--binding') + 1])
                config_path = binding.get('config')
            if config_path and read(config_path).get('root') == root:
                owners.append(int(entry.name))
        except (FileNotFoundError, PermissionError, ValueError, KeyError, IndexError, TypeError):
            continue
    return sorted(owners)


def retire_exact(runtime, row, lock_path, output, revalidate):
    descriptor = os.pidfd_open(row['pid'])
    paused, retired, watcher, cancel_end = False, False, None, None
    lock_descriptor = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        runtime.validate_owner(row, runtime.identity(row['pid']))
        require(not runtime.children(row['pid']), 'no_inflight_parent_transport')
        bound_lock = lock_owner(lock_path, row['pid'])
        read_end, cancel_end = os.pipe()
        watcher = os.fork()
        if watcher == 0:
            os.close(cancel_end)
            runtime.watchdog(descriptor, read_end, output)
        os.close(read_end)
        write(output / 'PARENT_PAUSE_INTENT.json', dict(owner=row, lock=bound_lock, child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        paused = True
        deadline = time.monotonic() + 2
        while runtime.identity(row['pid'])['state'] not in ('T', 't') and time.monotonic() < deadline:
            time.sleep(.01)
        runtime.validate_owner(row, runtime.identity(row['pid']), paused=True)
        require(runtime.identity(row['pid'])['state'] in ('T', 't') and not runtime.children(row['pid']),
                'exact_parent_paused_no_children')
        require(lock_owner(lock_path, row['pid']) == bound_lock, 'lock_unchanged_while_paused')
        revalidate()
        write(output / 'PARENT_RETIRE_INTENT.json', dict(owner=row, lock=bound_lock, child_signals=0))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        retired = True
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        paused = False
        require(bool(select.select([descriptor], [], [], 20)[0]), 'exact_parent_exit')
        write(output / 'PARENT_EXITED.json', dict(owner=row, child_signals=0, observed_unix=time.time()))
        current, opened = lock_path.stat(follow_symlinks=False), os.fstat(lock_descriptor)
        require((current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino) ==
                (bound_lock['device'], bound_lock['inode']), 'same_existing_lock_inode')
        fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(output / 'GENUINE_PARENT_LOCK_ACQUIRED.json', dict(lock=bound_lock,
            new_owner_pid=os.getpid(), old_owner_exited=True, observed_unix=time.time(), no_lock_replacement=True))
        result, lock_descriptor = lock_descriptor, None
        return result
    finally:
        if paused and not retired:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        if cancel_end is not None:
            os.write(cancel_end, b'C')
            os.close(cancel_end)
        if watcher:
            os.waitpid(watcher, 0)
        if lock_descriptor is not None:
            os.close(lock_descriptor)
        os.close(descriptor)


def publish_baseline(policy, source, config, output, seed, state, baseline, baseline_ref):
    require(baseline['authorship'] == 'NODE5_CODEX_AUTHORED_UNDER_MAIN_CONSOLE_DELEGATION', 'honest_authorship')
    memory_state = policy.memory(seed, [], state)
    require(not memory_state['awaiting_render'], 'no_duplicate_pending_publication')
    response = baseline['response']
    details = policy.decision(response, state, memory_state)
    require(details is not None, 'grounded_strict_baseline')
    require(len(response['message'].split()) <= config['r175_word_limit'] and
            len(response['message'].encode()) <= 4096, 'actual_arm_message_cap')
    directory = output / ('parent_' + str(state['request_count']).zfill(12) + '_main_console_baseline1')
    directory.mkdir(mode=0o700)
    write(directory / 'SOURCE.json', state)
    write(directory / 'DISPATCH_ONCE.json', dict(baseline=baseline_ref, API_calls=0,
        source='Main-authorized operator-authored console baseline; NOT provider output'))
    write(directory / 'AUTHORED_RESPONSE.json', baseline)
    write(directory / 'PUBLISH_INTENT.json', dict(speaker='Astra', message=response['message']))
    result = dict(details, status='PUBLICATION_UNKNOWN', source_sha256=sha(directory / 'SOURCE.json'),
        message=response['message'], grammar_lesson=False, authorship=baseline['authorship'],
        model=None, API_calls=0, delegated_authority='Main explicit grounded console fallback')
    try:
        require(time.time() < config['hard_end_unix'], 'unchanged_wall')
        result['publication'] = policy.parent.publish(source, config, response['message'])
        result['status'] = 'PUBLISHED'
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error)[:240])
    write(directory / 'RESULT.json', result)
    require(result['status'] == 'PUBLISHED', 'uncertain_publication_NO_RETRY')
    write(output / 'FIRST_PUBLICATION.json', dict(result=ref(directory / 'RESULT.json'),
        publication=result['publication'], observed_unix=time.time(), rendered=False,
        authorship=baseline['authorship'], API_calls=0))
    return result


def activate(binding_path, digest):
    require(sha(binding_path) == digest, 'exact_new_binding')
    binding = read(binding_path)
    require(sha(__file__) == binding['helper_sha256'] and sha(binding['cpu']['path']) == binding['cpu']['sha256'],
            'helper_CPU_pins')
    cpu = read(binding['cpu']['path'])
    require(cpu['status'] == 'PASS' and cpu['helper_sha256'] == binding['helper_sha256'], 'actual_CPU_PASS')
    require(binding['label'] in ('run1', 'pilot'), 'only_bound_active_R175_lanes_C2_excluded')
    for pin in (binding['manifest'], binding['baseline'], binding['active_parent']):
        require(sha(pin['path']) == pin['sha256'], 'input_pin')
    manifest = read(binding['manifest']['path'])
    runtime, policy, provenance = load_runtime(manifest)
    source, old_output, output = Path(manifest['source']), Path(manifest['output']), Path(binding['output'])
    require(output.is_relative_to(HERE) and not output.exists(), 'fresh_owned_output_no_retry')
    output.mkdir(mode=0o700)
    row = dict(read(binding['active_parent']['path'])['identity'], label=binding['label'])
    config = read(old_output / 'CONFIG.json')
    require(sha(old_output / 'CONFIG.json') == read(binding['active_parent']['path'])['config']['sha256'], 'config_pin')
    policy.validate(config)
    require(parent_census(config['root'], os.getpid()) == [row['pid']], 'one_exact_automatic_parent')
    baseline = read(binding['baseline']['path'])
    latest = sorted(old_output.glob('POLL_*.json'))[-1]
    cursor = read(latest)['reference']
    observed = runtime.snapshot_poll(policy, source, config, cursor, bootstrap=True)
    state, cursor = observed['snapshot'], observed['reference']
    require(state['caught_up'], 'fresh_verified_TRAIN_frontier')
    seed = merge_seed(policy, old_output, state)
    require(policy.decision(baseline['response'], state, policy.memory(seed, [], state)) is not None,
            'strict_nonempty_grounded_baseline_before_signals')
    write(output / 'PREFLIGHT.json', dict(snapshot=observed, seed_sha256=policy._digest(seed),
        binding=ref(binding_path), parser_provenance=provenance, owner=row, child_signals=0,
        no_new_API_call=True, helper_CPU=binding['cpu']))
    deadline = time.monotonic() + 90
    while runtime.children(row['pid']):
        require(time.monotonic() < deadline, 'inflight_parent_left_running')
        time.sleep(.2)

    def revalidate():
        require(merge_seed(policy, old_output, state) == seed, 'same_reserved_history_at_pause')
        require(parent_census(config['root'], os.getpid()) == [row['pid']], 'exclusive_parent_custody')

    lock_descriptor = retire_exact(runtime, row, old_output / 'PARENT.lock', output, revalidate)
    try:
        require(parent_census(config['root'], os.getpid()) == [], 'old_parent_gone_no_competitor')
        write(output / 'SEED.json', seed)
        config = dict(config, predecessor_seed=ref(output / 'SEED.json'))
        write(output / 'CONFIG.json', config)
        with policy.community.parent_lock(output):
            write(output / 'ACTIVE_PARENT.json', dict(pid=os.getpid(), identity=runtime.identity(os.getpid()),
                label=binding['label'], arm=config['r175_arm'], config=ref(output / 'CONFIG.json'),
                old_active=binding['active_parent'], binding=ref(binding_path), parser_provenance=provenance,
                tick_file=policy.tick.__code__.co_filename, child_signals=0, observed_unix=time.time()))
            published = publish_baseline(policy, source, config, output, seed, state, baseline, binding['baseline'])
            sequence, first = 0, None
            while time.time() < config['hard_end_unix']:
                observed = runtime.snapshot_poll(policy, source, config, cursor, bootstrap=True)
                state, cursor = observed['snapshot'], observed['reference']
                path = output / ('POLL_' + str(sequence).zfill(8) + '.json')
                write(path, observed)
                if first is None:
                    first = runtime.exposure(published['publication'], published['message'], state)
                    if first is not None:
                        write(output / 'FIRST_RENDERED_REQUEST.json', dict(first, snapshot=ref(path),
                            observed_unix=time.time(), authorship=baseline['authorship'], peer_channel_active=False))
                if first is not None and state['sleep_count'] >= first['three_sleep_check_at']:
                    status = dict(status='WITHDRAWAL_NO_NEW_PARENT_OR_PEER', sleep_count=state['sleep_count'])
                    if state['sleep_count'] >= first['withdrawal_complete_at']:
                        write(output / 'WITHDRAWAL_COMPLETE.json', status)
                        return
                else:
                    status = policy.tick(source, config, output, seed, state)
                write(output / ('STATUS_' + str(sequence).zfill(8) + '.json'), status)
                sequence += 1
                time.sleep(5)
    finally:
        os.close(lock_descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    arguments = parser.parse_args()
    try:
        activate(arguments.binding, arguments.sha256)
    except BaseException as error:
        if sha(arguments.binding) == arguments.sha256:
            output = Path(read(arguments.binding)['output'])
            if output.is_dir() and not (output / 'FAILED_CLOSED.json').exists():
                write(output / 'FAILED_CLOSED.json', dict(status='OPERATOR_FAILURE_NOT_CHILD_FAILURE',
                    error_type=type(error).__name__, error=str(error)[:240], child_signals=0,
                    retired=(output / 'PARENT_EXITED.json').exists(), no_implicit_retry=True))
        raise
