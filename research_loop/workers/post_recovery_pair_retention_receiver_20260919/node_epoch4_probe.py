"""Pair CPU diagnostics on exact staged source; never admission, signals or locks."""

import argparse
import contextlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import types

from remote_epoch4_stage import ROOT, checksum, exact_native, inventory, read, require


PAIR = 'research_loop/workers/post_recovery_pair_retention_receiver_20260919'


def write_once(path, value):
    path = Path(path)
    content = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == content, 'existing_probe_artifact_mismatch_stop')
        return checksum(content)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    return checksum(content)


def sidecars(root):
    return ([dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
        if (Path(root) / 'correction_ledger.json').exists() else [])


def family(plan):
    native = importlib.import_module('gpu.orch_r125_continual_native')
    recovery = importlib.import_module('gpu.r232_recovery')
    initial = recovery.ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json'
    recovery.frozen.INITIAL = native.read(initial)
    base = recovery.FrozenJournal if plan['physical'] == 1 else recovery.LearnerJournal
    require(base.__module__ == 'gpu.r232_recovery'
        and base.__qualname__ == ('FrozenJournal' if plan['physical'] == 1 else 'LearnerJournal'),
        'actual_pair_journal_family_not_plain_journal')
    return base, dict(path=str(initial), sha256=checksum(initial.read_bytes()),
        frozen_INITIAL_explicitly_initialized=True, journal_type=base.__module__ + ':' + base.__qualname__)


def header(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 2048))
        raw = handle.read()
    match = re.search(rb',"index":([0-9]+),"journal_id":"([0-9a-f]{32})","kind":"([A-Z0-9_]+)",'
        rb'"previous_sha256":"([0-9a-f]{64})","schema":"R125_STREAM_JOURNAL_V1","sha256":"([0-9a-f]{64})"}\n\Z', raw)
    require(match is not None, 'canonical_record_suffix_required')
    return dict(index=int(match.group(1)), journal_id=match.group(2).decode(), kind=match.group(3).decode(),
        previous_sha256=match.group(4).decode(), sha256=match.group(5).decode())


def load_boundary(path):
    specification = importlib.util.spec_from_file_location('_pair_epoch4_readonly_boundary', path)
    boundary = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(boundary)
    return boundary


def select_candidate(observation, plan):
    path = ROOT / 'pair_operator_bundle_v4/research_loop/workers/post_recovery_retention_boundary_20260918/boundary.py'
    manifest = read(ROOT / 'pair_operator_bundle_v4/MANIFEST.json')
    require(checksum(path.read_bytes()) == manifest['source_files'][str(path.relative_to(ROOT / 'pair_operator_bundle_v4'))],
        'exact_operator_boundary_bytes')
    boundary = load_boundary(path)
    directory = Path(observation['journal_root']) / 'records'
    paths = sorted(directory.glob('[0-9]' * 20 + '.json'))[-512:]
    metadata = [header(path) for path in paths]
    for position in reversed(range(len(metadata))):
        item = metadata[position]
        if item['kind'] != 'SLEEP_COMPLETE':
            continue
        entry = paths[position].stat()
        if max(entry.st_mtime_ns, entry.st_ctime_ns) > time.time_ns() - 10_000_000_000:
            continue
        selected = [item]
        for following in metadata[position + 1:]:
            if following['kind'] not in ('INBOX', 'R184_LEARN_COMPLETE'):
                break
            selected.append(following)
            if following['kind'] == 'R184_LEARN_COMPLETE':
                records = [boundary.read(directory / f'{record["index"]:020d}.json') for record in selected]
                intents = {record['index']: boundary.read(directory / f'{record["index"]:020d}.intent.json')
                    for record in selected}
                candidate = boundary.validate_records(records, dict(journal_id=observation['journal_id'],
                    hard_end_unix=plan['hard_end_unix']), intents=intents)
                require(candidate is not None, 'actual_historical_COMPLETE_LEARN')
                return candidate, metadata[-1]['index']
    raise ValueError('no_aged_COMPLETE_LEARN_in_bounded_suffix')


def inbox_snapshot(root):
    snapshots = {}
    for path in sorted((Path(root) / 'inbox').glob('*.json')):
        require(not path.is_symlink(), 'no_INBOX_symlinks')
        before = path.stat()
        require(before.st_size <= 16 * 1024**2 and len(snapshots) < 100000, 'bounded_INBOX_snapshot')
        content = path.read_bytes()
        after = path.stat()
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        require(identity(before) == identity(after), 'INBOX_changed_during_observation')
        snapshots[path.name] = dict(identity=identity(after), sha256=checksum(content))
    return snapshots


def probe(request, mode):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicit_CPU_only_environment')
    observation = request['observation']
    source = ROOT / observation['life'] / 'epoch4/source'
    manifest = read(source.parent / 'EPOCH4_SOURCE.json')
    require(str(source) == manifest['new_source'] and inventory(source) == manifest['new_source_pins'],
        'exact_production_epoch4_source_required')
    before = exact_native(observation)
    directory = Path(request['life_root'])
    require(directory.is_relative_to(ROOT) and directory.resolve() == directory, 'literal_own_probe_root')
    sys.path.insert(0, str(ROOT / 'pair_operator_bundle_v4'))
    sys.path.insert(0, str(ROOT / 'pair_operator_bundle_v4' / PAIR))
    sys.path.insert(0, str(ROOT / 'pair_prefix_producer_v4'))
    sys.path.insert(0, str(source))
    plan = read(source.parent / 'control/PLAN.template.json')
    require(plan['source_root'] == str(source) and plan['hard_end_unix'] == observation['plan']['hard_end_unix'],
        'same_deadline_exact_plan_template')
    base, initial = family(plan)
    started = time.monotonic()
    if mode == 'select':
        candidate, observed_head = select_candidate(observation, plan)
        request_path = directory / 'CHECKPOINT_REQUEST.json'
        request_sha = write_once(request_path, dict(source=str(source), candidate=candidate, plan=plan))
        epoch = read(source.parent / 'control/SOURCE_EPOCH.template.json')
        epoch_path = source.parent / 'control/SOURCE_EPOCH.json'
        epoch_sha = write_once(epoch_path, epoch)
        epoch_path.chmod(0o444)
        selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=observation['journal_root'],
            journal_id=observation['journal_id'], complete_index=candidate['complete_index'],
            complete_sha256=candidate['complete_sha256'], life_id=plan['think_act_learn']['trial_id'],
            max_tail_records=2048, max_tail_bytes=1024**3, sidecars=sidecars(observation['journal_root']),
            persist_complete_anchors=False)
        producer = dict(schema='R233_PREFIX_PRODUCER_REQUEST_V1', selection=selection,
            source=dict(root=str(source), pins=manifest['new_source_pins'], epoch=dict(path=str(epoch_path), sha256=epoch_sha)),
            journal_type=initial['journal_type'])
        producer_path = directory / 'PRODUCER.json'
        producer_sha = write_once(producer_path, producer)
        result = dict(status='HISTORICAL_COMPLETE_SELECTED_NOT_HANDOFF', complete_index=candidate['complete_index'],
            complete_sha256=candidate['complete_sha256'], learn_index=candidate['learn_index'], observed_head=observed_head,
            optimizer_steps=candidate['checkpoint']['optimizer_steps'], checkpoint_request=str(request_path),
            checkpoint_request_sha256=request_sha, producer_request=str(producer_path), producer_request_sha256=producer_sha)
    elif mode == 'checkpoint':
        import cpu_probe
        saved = read(directory / 'CHECKPOINT_REQUEST.json')
        result = dict(status='ACTUAL_SAVED_CHECKPOINT_CPU_NOT_HANDOFF',
            evidence=cpu_probe.probe(str(source), saved['candidate'], saved['plan'], 'checkpoint'),
            complete_index=saved['candidate']['complete_index'])
    elif mode == 'produce':
        import prefix_cli
        path = directory / 'PRODUCER.json'
        producer_request = read(path)
        epoch_metadata = Path(producer_request['source']['epoch']['path']).stat()
        remaining = (max(epoch_metadata.st_mtime_ns, epoch_metadata.st_ctime_ns) + 3_000_000_000 - time.time_ns()) / 10**9
        require(remaining <= 5, 'no_future_epoch_metadata_or_clock_repair')
        if remaining > 0:
            time.sleep(remaining + 0.05)
        result = prefix_cli.execute(types.SimpleNamespace(command='produce', request=str(path),
            request_sha256=checksum(path.read_bytes()), proof_output=str(directory / 'PROOF.json'),
            guard_candidate_output=str(directory / 'GUARD_A.json')))
    elif mode == 'read':
        import prefix_cli
        from gpu.checkpoint_tail_runtime import scan
        from gpu.immutable_prefix_proof import read_pinned
        guard_path = directory / 'GUARD_A.json'
        authority = dict(guard_path=str(guard_path), guard_sha256=checksum(guard_path.read_bytes()))
        guard, snapshot = read_pinned(str(guard_path), authority['guard_sha256'])
        selection = guard['resume']['selection']
        require(selection['sidecars'] == sidecars(observation['journal_root']), 'current_sidecars_must_match_selection')
        inbox_before = inbox_snapshot(observation['journal_root'])
        scan_started = time.monotonic()
        with prefix_cli.readonly_journal(base, selection['root']) as journal:
            state = scan(journal, selection, prefix_proof=authority)
            scan_seconds = time.monotonic() - scan_started
            result = dict(status='PRODUCTION_SOURCE_DIAGNOSTIC_READ_NOT_HANDOFF', scan_seconds=scan_seconds,
                receipt=journal.checkpoint_tail_receipt, inbox_registered_count=len(state['inbox']),
                pending={key: state[key] is not None for key in ('request', 'response', 'sleep_request')})
        inbox_after = inbox_snapshot(observation['journal_root'])
        preserved = all(inbox_after.get(name) == value for name, value in inbox_before.items())
        require(preserved, 'original_INBOX_snapshot_moved_or_changed')
        result.update(inbox_files_before=len(inbox_before), inbox_files_after=len(inbox_after),
            new_INBOX_file_count=len(set(inbox_after) - set(inbox_before)), original_INBOX_files_unchanged=preserved,
            observed_INBOX_file_names_sha256=checksum(json.dumps(sorted(inbox_after)).encode()))
        write_once(directory / ('INBOX_SNAPSHOT_' + str(time.time_ns()) + '.json'),
            dict(before=inbox_before, after=inbox_after))
    else:
        raise ValueError('known_CPU_diagnostic_mode_only')
    result['operation_seconds'] = time.monotonic() - started
    require(checksum(Path(initial['path']).read_bytes()) == initial['sha256'], 'frozen_initial_commit_unchanged')
    require(inventory(source) == manifest['new_source_pins'], 'production_source_untouched')
    after = exact_native(observation)
    result.update(life=observation['life'], source=str(source), source_file_count=len(manifest['new_source_pins']),
        native_before=before, native_after=after, original_native_source_guard_unchanged=True, family=initial,
        native_signals=[], parent_actions=[], reservations=[], GPU_calls=0, journal_writes=0,
        writer_lock_acquired=False, authorizes_native_handoff=False, actual_confined_admission_proven=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('select', 'checkpoint', 'produce', 'read'))
    parser.add_argument('--request', required=True, type=Path)
    args = parser.parse_args()
    request = read(args.request)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            result = probe(request, args.mode)
    except Exception as error:
        result = dict(status='CPU_DIAGNOSTIC_REFUSED_NO_NATIVE_ACTION', mode=args.mode,
            error_type=type(error).__name__, error=str(error),
            native_after=exact_native(request['observation']), native_signals=[], parent_actions=[],
            reservations=[], GPU_calls=0, journal_writes=0, authorizes_native_handoff=False)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
