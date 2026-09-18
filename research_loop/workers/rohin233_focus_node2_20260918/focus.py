"""R233 exact ended-root preservation and one identity-bound orphan-bridge retirement."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time


BASE = Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
STORE = Path('/localhome/local-rohing/orch_rohin233_focus_node2_20260918')
TARGETS = {
    'creative_d1': (BASE/'creative_d1/raw', 2333605, 93403624),
    'math_d1': (BASE/'math_d1/raw', 2308366, 93335010),
    'math_transfer_c1': (BASE/'math_transfer_c1/raw', 2370147, 93528026),
    'repo_c1': (BASE/'repo_c1/raw', 2366411, 93516514),
    'orch_r183_birth1': (Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1/life'), 2263935, None),
}
KEEP = {
    'C0': (2561156, 94173182, '/localhome/local-rohing/orch_r216_C0_20260918_attempt2/control/GUARD_PUBLISHED.json'),
    'C0_math_parent': (2561001, 94172764, '/localhome/local-rohing/orch_r216_C0_20260918_attempt2/parent.py'),
    'C0_curriculum': (2929240, 95395597, '/localhome/local-rohing/orch_r230_c0_operator_20260918/curriculum_current'),
    'Astra7': (2863450, 95248943, '/localhome/local-rohing/orch_r229_Astra7_20260918/control/GUARD_PUBLISHED.json'),
    'GAME_UNPARENTED_N2': (2884345, 95317660, '/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork/control/GUARD.json'),
}
BRIDGE_PID = 2321469
BRIDGE_START = 93363849
BRIDGE_SHA = '371149fff0540732ad08da1cefa189f93cadede944c8d429d77733d56e783a78'
BRIDGE_ROOT = BASE/'math_transfer_c1/r206_phase2_withdrawn_20260918'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def file_sha(path):
    require(path.is_file() and not path.is_symlink(), 'regular_file_only')
    before = path.stat()
    with path.open('rb') as stream:
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
        (after.st_ino, after.st_size, after.st_mtime_ns), 'stable_during_hash')
    return result


def metadata(path):
    require(path.is_file() and not path.is_symlink(), 'regular_record')
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        tail = stream.read()
    marker = tail.rfind(b',"index":')
    require(marker >= 0, 'existing_journal_layout')
    result = json.loads(b'{' + tail[marker + 1:])
    require(result['index'] == int(path.stem), 'record_index_filename_binding')
    return result


def checked_record(path):
    require(path.stat().st_size <= 32 * 1024**2 and not path.is_symlink(), 'bounded_record')
    value = read(path)
    require(value['sha256'] == sha(canonical({key: item for key, item in value.items() if key != 'sha256'})), 'record_hash')
    return value


def process(pid):
    root = Path('/proc')/str(pid)
    if not root.exists():
        return None
    try:
        fields = (root/'stat').read_text().rsplit(')', 1)[1].split()
        command = (root/'cmdline').read_bytes()
        return dict(pid=pid, start_ticks=int(fields[19]), state=fields[0], uid=root.stat().st_uid,
            cmdline_sha256=sha(command), argv=[part.decode() for part in command.split(b'\0') if part])
    except FileNotFoundError:
        return None


def kept_identities():
    result = {}
    for name, (pid, start, argument) in KEEP.items():
        actual = process(pid)
        require(actual and actual['start_ticks'] == start and argument in actual['argv']
            and actual['state'] not in ('T', 'Z', 'X'), 'kept_identity_' + name)
        result[name] = {key: value for key, value in actual.items() if key != 'argv'}
    return result


def check_target(name, raw):
    require(name in TARGETS and raw == TARGETS[name][0], 'exact_target_only')
    require(raw.resolve() == raw and not raw.is_symlink(), 'physical_unaliased_root')
    require('orch_r216_C0' not in str(raw) and 'orch_r229' not in str(raw)
        and raw.name in ('raw', 'life'), 'protected_or_unlisted_root')


def preserve(name):
    raw, pid, start = TARGETS[name]
    check_target(name, raw)
    require(process(pid) is None, 'ended_native_PID_must_be_absent_no_signal')
    destination = STORE/'preserved'/name
    destination.mkdir(parents=True, mode=0o700)
    records = sorted((raw/'stream/records').glob('[0-9]'*20+'.json'))
    headers = [metadata(path) for path in records]
    require(records and [item['index'] for item in headers] == list(range(headers[0]['index'], headers[-1]['index'] + 1)), 'contiguous_record_inventory')
    require(all(current['previous_sha256'] == previous['sha256'] for previous, current in zip(headers, headers[1:])), 'stored_record_hash_chain')
    selected = {}
    for kind in ('LOADED', 'SLEEP_COMPLETE'):
        header = next(item for item in reversed(headers) if item['kind'] == kind)
        selected[kind] = checked_record(raw/'stream/records'/f"{header['index']:020d}.json")
    require(selected['LOADED']['document']['pid'] == pid, 'latest_loaded_exact_ended_native')
    complete = selected['SLEEP_COMPLETE']
    document = complete['document']
    require(document['status'] == 'COMPLETE', 'completed_checkpoint_required')
    checkpoint = raw/'checkpoints'/f"sleep_{document['cycle']:06d}"
    commit = read(checkpoint/'COMMIT.json')
    require(commit['checkpoint_sha256'] == document['checkpoint_sha256']
        and commit['optimizer_steps'] == document['total_optimizer_steps'], 'commit_completion_binding')
    require(sha(canonical(document['resume_state']['state'])) == document['resume_state']['sha256'], 'working_state_hash')
    files = {'COMMIT.json': file_sha(checkpoint/'COMMIT.json')}
    for filename, expected in commit['adapter_files'].items():
        require(Path(filename).name == filename, 'adapter_component_only')
        actual = file_sha(checkpoint/'adapter'/filename)
        require(actual == expected, 'adapter_file_hash')
        files['adapter/' + filename] = actual
    optimizer = file_sha(checkpoint/'optimizer_rng.pt')
    require(optimizer == commit['checkpoint_sha256']['optimizer'] == commit['checkpoint_sha256']['rng'], 'optimizer_rng_hash')
    files['optimizer_rng.pt'] = optimizer
    for filename, expected in files.items():
        target = destination/'checkpoint'/filename
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(checkpoint/filename, target)
        require(file_sha(target) == expected, 'preserved_checkpoint_copy_hash')
    (destination/'records').mkdir(mode=0o700)
    for path in sorted((raw/'stream/records').iterdir()):
        require(path.is_file() and not path.is_symlink(), 'regular_record_directory_entries')
        os.link(path, destination/'records'/path.name)
        require(path.samefile(destination/'records'/path.name), 'preserved_record_same_inode')
    manifest = destination/'RECORD_INVENTORY.jsonl'
    with manifest.open('x') as stream:
        for path, header in zip(records, headers):
            stream.write(json.dumps(dict(filename=path.name, bytes=path.stat().st_size,
                index=header['index'], sha256=header['sha256'], previous_sha256=header['previous_sha256'],
                kind=header['kind'], journal_id=header['journal_id']), sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    require(sorted((raw/'stream/records').glob('[0-9]'*20+'.json')) == records
        and metadata(records[-1]) == headers[-1] and process(pid) is None, 'ended_root_unchanged_during_preservation')
    receipt = dict(complete_utc=utc(), arm=name, physical_raw_root=str(raw), preservation_root=str(destination),
        disposition='ALREADY_ENDED_PRESERVED_NO_NATIVE_SIGNAL', latest_native_pid=pid, historical_start_ticks=start,
        historical_start_ticks_status='recorded_R210_identity' if start else 'not_recovered_PID_absent_no_signal',
        loaded_index=selected['LOADED']['index'], loaded_sha256=selected['LOADED']['sha256'],
        completed_index=complete['index'], completed_sha256=complete['sha256'],
        cycle=document['cycle'], optimizer_steps=commit['optimizer_steps'], checkpoint_file_hashes=files,
        resume_state_sha256=document['resume_state']['sha256'], adapter_state_sha256=commit['adapter_state_sha256'],
        journal_records=len(records), journal_head=headers[-1], record_inventory_sha256=file_sha(manifest),
        all_record_files_preserved=len(list((destination/'records').iterdir())),
        custody='Checkpoint bytes copied and independently hashed; immutable journal files retained as hardlinks, including auxiliary entries. Source bytes and permissions unchanged.',
        verification='All stored record footer hashes linked and chain-checked; LOADED/SLEEP_COMPLETE bodies fully rehashed. Other record bodies not rehashed.',
        native_signals=0, source_deletes=0, checkpoint_binaries_published=False)
    write(destination/'PRESERVED.public.json', receipt)
    return receipt


def bridge_identity(actual, config):
    expected_argv = ['/localhome/local-rohing/v2/venv/bin/python', '-B',
        str(BRIDGE_ROOT/'source/gpu/r184_cpu_bridge.py'), '--config', str(BRIDGE_ROOT/'BRIDGE.json')]
    require(actual and actual['pid'] == BRIDGE_PID and actual['start_ticks'] == BRIDGE_START
        and actual['uid'] == 2524 and actual['cmdline_sha256'] == BRIDGE_SHA
        and actual['argv'] == expected_argv, 'exact_orphan_bridge_identity')
    require(config['raw_root'] == str(TARGETS['math_transfer_c1'][0]), 'bridge_only_retired_root')


def retire_bridge():
    preservation = read(STORE/'PRESERVATION.public.json')
    require(set(preservation['arms']) == set(TARGETS), 'all_named_found_roots_preserved_first')
    before = kept_identities()
    config_path = BRIDGE_ROOT/'BRIDGE.json'
    config = read(config_path)
    config_sha = file_sha(config_path)
    actual = process(BRIDGE_PID)
    bridge_identity(actual, config)
    require(process(TARGETS['math_transfer_c1'][1]) is None, 'bridge_native_already_ended')
    descriptor = os.pidfd_open(BRIDGE_PID)
    try:
        bridge_identity(process(BRIDGE_PID), read(config_path))
        require(file_sha(config_path) == config_sha, 'same_bridge_config_before_signal')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    finally:
        os.close(descriptor)
    for attempt in range(50):
        current = process(BRIDGE_PID)
        if current is None or current['start_ticks'] != BRIDGE_START or current['state'] == 'Z':
            break
        time.sleep(0.1)
    else:
        raise ValueError('SIGTERM_sent_exact_bridge_exit_unverified_no_escalation')
    result = dict(completed_utc=utc(), target='math_transfer_c1 orphan CPU bridge',
        identity={key: value for key, value in actual.items() if key != 'argv'}, config_sha256=config_sha,
        source_sha256=file_sha(BRIDGE_ROOT/'source/gpu/r184_cpu_bridge.py'),
        signal='SIGTERM via pidfd', signals=1, native_signals=0, broad_signals=0,
        kept_before=before, kept_after=kept_identities(), exit_verified=True)
    write(STORE/'BRIDGE_RETIRED.public.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preserve', 'retire-bridge'))
    arguments = parser.parse_args()
    os.umask(0o077)
    STORE.mkdir(mode=0o700, exist_ok=True)
    lock = (STORE/'OPERATOR.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if arguments.mode == 'preserve':
        before = kept_identities()
        results = {name: preserve(name) for name in TARGETS}
        report = dict(complete_utc=utc(), arms=results, kept_before=before, kept_after=kept_identities(), native_signals=0)
        write(STORE/'PRESERVATION.public.json', report)
        print(json.dumps(dict(complete_utc=report['complete_utc'], preserved=list(results), native_signals=0)))
    else:
        result = retire_bridge()
        print(json.dumps(dict(completed_utc=result['completed_utc'], stopped_pid=BRIDGE_PID, signals=1, native_signals=0)))
