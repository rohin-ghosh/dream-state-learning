"""Hourly bounded review triage, not semantic judgment or a life controller."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORIGINAL = HERE.parent / 'rohin232_correction_audit_20260918'
CONTRACT = HERE / 'contract'


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


audit = load('hourly_original_audit', CONTRACT / 'audit.py')
epochs = load('hourly_source_epochs', HERE / 'epochs.py')
previous_audit = sys.modules.get('audit')
sys.modules['audit'] = audit
try:
    queue = load('hourly_original_review_queue', CONTRACT / 'review_queue.py')
finally:
    if previous_audit is None:
        del sys.modules['audit']
    else:
        sys.modules['audit'] = previous_audit


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.next')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def process(pid):
    path = Path('/proc') / str(pid)
    try:
        fields = path.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
        return dict(pid=pid, start_ticks=fields[19], state=fields[0],
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    except (FileNotFoundError, ProcessLookupError):
        return None


def same_process(actual, expected):
    return bool(actual and actual['state'] != 'Z' and actual['start_ticks'] == str(expected['start_ticks'])
        and actual['pid'] == expected['pid'] and actual['boot_id'] == expected.get('boot_id', actual['boot_id']))


def acquire_locks(config):
    descriptors = []
    try:
        for path, expected, flags in (
            (ORIGINAL / 'operator/SINGLE_READER.lock', config['old_lock_identity'], os.O_RDONLY),
            (HERE / 'operator/SINGLE_READER.lock', config.get('own_lock_identity'), os.O_RDWR | os.O_CREAT),
        ):
            descriptor = os.open(path, flags | os.O_NOFOLLOW, 0o600)
            descriptors.append(descriptor)
            information = os.fstat(descriptor)
            if expected and [information.st_dev, information.st_ino] != expected:
                raise ValueError('singleton_lock_inode_changed')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return descriptors
    except BaseException:
        for descriptor in descriptors:
            os.close(descriptor)
        raise


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def next_hour(value):
    return (int(value) // 3600 + 1) * 3600


def references(value):
    found = {}
    def walk(item):
        if isinstance(item, dict):
            if all(key in item for key in ('index', 'sha256', 'kind')):
                found[item['index']] = {key: item[key] for key in ('index', 'sha256', 'kind')}
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    walk(value)
    return [found[index] for index in sorted(found)]


def history(label):
    directory = HERE / 'private/history' / label
    if not (directory / 'ANNOTATIONS.json').exists():
        return dict(highest_verified_level=None, traces=[], provenance='NO_IMPORTED_MANUAL_ANNOTATION'), []
    pins = json.loads((directory / 'PINS.json').read_text())
    for name, expected in pins.items():
        if sha(directory / name) != expected:
            raise ValueError('immutable_imported_adjudication')
    evidence = json.loads((directory / 'EVIDENCE.json').read_text())
    annotations = json.loads((directory / 'ANNOTATIONS.json').read_text())
    result = audit.report(evidence, label, annotations)
    refs = references(result['traces'])
    records = {row['index']: row for row in evidence['records']}
    for reference in refs:
        if reference['kind'] == 'RESPONSE':
            reference['response_text_sha256'] = audit.text_sha(records[reference['index']]['text'])
    for trace in result['traces']:
        trace['observer_assessment_sha256'] = audit.text_sha(trace.pop('observer_assessment'))
    result.update(provenance='REVALIDATED_ORIGINAL_MANUAL_LEDGER_NOT_NEW_SEMANTICS',
        imported_pins=pins, historical_cut_index=evidence['through']['index'])
    return result, refs


def remote(target, refs, probe=False):
    if target['wrapper'] not in ('ovx_ssh.sh', 'ovx2_ssh.sh', 'ovx3_ssh.sh', 'a40r_ssh.sh', 'ovx4_ssh.sh'):
        raise ValueError('registered_transport_only')
    code = (CONTRACT / 'reader.py').read_text() + '\n' + (HERE / 'remote.py').read_text()
    code += '\nprint(json.dumps(inspect(' + repr(target) + ',' + repr(refs) + ',probe=' + repr(probe) + ')))\n'
    result = subprocess.run(['bash', str(REPO / 'gpu' / target['wrapper']),
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        input=code, text=True, capture_output=True, timeout=240, check=True)
    return json.loads(result.stdout)


def one(entry):
    label = entry['label']
    row = dict(label=label, highest_verified_level=None, new_semantic_judgments=0)
    try:
        previous, refs = history(label)
        row.update(highest_verified_level=previous['highest_verified_level'], historical=previous,
            level_scope='IMPORTED_ORIGINAL_LEDGER_ONLY_NOT_LIFETIME_OR_NEW_WINDOW_JUDGMENT',
            historical_reference_scope='LOCAL_FROZEN_CACHE_ONLY')
        if not entry.get('binding'):
            row.update(status='CURRENT_BINDING_UNRESOLVED_NOT_COLLECTED', native_identity_verified=False,
                original_registry_status=entry.get('registry_status'), historical_reference_scope='LOCAL_FROZEN_CACHE_ONLY')
            return row
        target = entry['binding']
        if time.time() >= target['until_unix']:
            row.update(status='SOURCE_HORIZON_ELAPSED_NO_REMOTE_READ', native_identity_verified=False)
            return row
        captured = remote(target, refs)
        evidence = captured.pop('evidence')
        epoch_id = epochs.source_epoch(label, target)
        private = HERE / 'private/epochs' / label / epoch_id
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        snapshot = private / 'cuts' / stamp / 'EVIDENCE.json'
        save(snapshot, evidence)
        prior_path = private / 'REVIEW_QUEUE_CURSOR.json'
        prior = json.loads(prior_path.read_text()) if prior_path.exists() else dict(
            journal_id=evidence['journal_id'], source_epoch_id=epoch_id, through_index=evidence['coverage_start'] - 1)
        epochs.validate_cursor(prior, epoch_id)
        review, cursor = queue.build_queue(evidence, label, previous['traces'], prior, limit=4)
        review['source_epoch_id'] = cursor['source_epoch_id'] = epoch_id
        for item in review['items']:
            item['source_epoch_id'] = epoch_id
        save(snapshot.with_name('REVIEW_QUEUE_CURSOR.json'), cursor)
        save(prior_path, cursor)
        frames = audit.frames(evidence)
        gap = [prior['through_index'] + 1, evidence['coverage_start'] - 1]
        previous_cut_path = HERE / 'public/CURRENT.json'
        previous_cut = json.loads(previous_cut_path.read_text()) if previous_cut_path.exists() else {}
        earlier = next((item for item in previous_cut.get('rows', []) if item['label'] == label), {})
        same_prior = earlier.get('binding_receipt_sha256') == target['owner_receipt_sha256'] and all(
            earlier.get('current_identity', {}).get(key) == captured['identity'].get(key) for key in ('pid', 'start_ticks', 'guard_sha256'))
        if same_prior and earlier.get('current_window'):
            gap = [earlier['current_window']['through']['index'] + 1, evidence['coverage_start'] - 1]
        row.update(status='ACTUAL_BOUNDED_COLLECTION_COMPLETE', native_identity_verified=True,
            source_epoch_id=epoch_id, ACT_parent_exposure=epochs.act_exposure(evidence, audit, queue, epoch_id),
            prior_completed_cut_utc=previous_cut.get('observed_utc') if same_prior else None,
            prior_epoch_id=earlier.get('source_epoch_id') if same_prior else None,
            legacy_unversioned_reviews_preserved_not_carried_to_new_epoch=True,
            current_identity=captured['identity'], binding_receipt_sha256=target['owner_receipt_sha256'],
            source_horizon_utc=utc(target['until_unix']), historical_reference_scope='CANONICAL_SOURCE_RECORDS_RECHECKED_NOW',
            revalidated_historical_record_count=len(refs), historical_reference_manifest_sha256=audit.text_sha(json.dumps(refs, sort_keys=True)),
            current_window=dict(first=evidence['coverage_start'], through=evidence['through'], head=evidence['head'],
                caught_up=evidence['caught_up'], raw_bytes_read=evidence['bytes_read'],
                snapshot_sha256=sha(snapshot), snapshot_relative=str(snapshot.relative_to(HERE)),
                source_epoch_id=epoch_id, actual_committed_ACTs=sum(frame['stage'] == 'ACT' for frame in frames),
                newest_ACT=next((queue.output_ref(frame) for frame in reversed(frames) if frame['stage'] == 'ACT'), None)),
            between_hour_gap=gap if gap[0] <= gap[1] else None,
            earlier_unsampled_interval=[previous.get('historical_cut_index', 0) + 1, evidence['coverage_start'] - 1],
            review_queue=review, current_window_semantic_level=None,
            original_correction_context_may_remain_visible=True)
    except Exception as error:
        save(HERE / 'private/errors' / (label + '.json'), dict(time_unix=time.time(), type=type(error).__name__, error=str(error)[-1800:]))
        row.update(status='COLLECTION_ERROR_NO_CURRENT_PROOF', error_type=type(error).__name__, native_identity_verified=False)
    return row


def run_once(config):
    for name, expected in config['source_pins'].items():
        if sha(HERE / name) != expected:
            raise ValueError('frozen_observer_source_changed')
    with ThreadPoolExecutor(max_workers=2) as workers:
        rows = list(workers.map(one, config['entries']))
    result = dict(observed_utc=utc(time.time()), rows=rows, collector_process=process(os.getpid()),
        actual_current_bound_sources=sum(row.get('native_identity_verified') is True for row in rows),
        registered_rows=len(rows), unique_kept_sources=17, native_kept_sources=16, alias_rows=1,
        partial_fleet=True, automatic_semantic_review=False, new_semantic_judgments=0,
        model_calls=0, parent_messages=0, remote_writes=0, native_signals=0, git_publication=False,
        interpretation='Historical levels are manual-ledger revalidations; fresh inputs/ACTs are unjudged. Unknown is not level0. Bounded windows and unsampled gaps are explicit.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    save(HERE / 'public/cuts' / (stamp + '.json'), result)
    save(HERE / 'public/CURRENT.json', result)
    save(HERE / 'public/SOURCE_EPOCHS.json', dict(observed_utc=result['observed_utc'], rows=epochs.publish_rows(rows),
        rule='Every ACT window and queue cursor is keyed by per-life source epoch. Changed source fails closed. Future before/after comparison requires an exact deployment receipt and separately bound windows; retention is not uptake.'))
    queues = [row['review_queue'] for row in rows if 'review_queue' in row]
    save(HERE / 'public/REVIEW_QUEUE.json', dict(observed_utc=result['observed_utc'], owner=queue.OWNER,
        automatic_semantic_review=False, new_semantic_judgments=0, rows=queues,
        pending_total=sum(item['pending_total'] for item in queues),
        displayed=sum(item['displayed'] for item in queues), raw_text_published=False))
    lines = ['# Hourly correction evidence — partial coverage', '', 'Cut: ' + result['observed_utc'], '',
        'Historical best levels are revalidated manual annotations, not new semantic judgments. Current windows remain pending review.',
        'Four initially bound native sources; all unresolved rows remain explicitly unresolved. Unknown is not failure.', '',
        '| Life | Prior revalidated level | Actual current collection | New-window ACTs | Pending review |',
        '|---|---:|---|---:|---:|']
    for row in rows:
        level = row.get('highest_verified_level')
        lines.append('| ' + ' | '.join(str(value) for value in (row['label'], level if level is not None else 'unknown',
            row['status'], row.get('current_window', {}).get('actual_committed_ACTs', 'unresolved'),
            row.get('review_queue', {}).get('pending_total', 'unresolved'))) + ' |')
    (HERE / 'public/STATUS_LATEST.md').write_text('\n'.join(lines) + '\n')
    return result


def serve():
    os.umask(0o077)
    config_path = HERE / 'private/CONFIG.json'
    config_sha = sha(config_path)
    config = json.loads(config_path.read_text())
    old_pid = config['old_process']
    actual = process(old_pid['pid'])
    if same_process(actual, old_pid):
        raise ValueError('original_auditor_still_alive')
    old_state_path = HERE / 'operator/PROCESS.json'
    if old_state_path.exists():
        old_state = json.loads(old_state_path.read_text())
        if same_process(process(old_state['pid']), old_state):
            raise ValueError('previous_observer_still_alive')
    descriptors = acquire_locks(config)
    current = process(os.getpid())
    state = dict(**current, started_utc=utc(time.time()), source_sha256=config['source_pins'], config_sha256=config_sha,
        old_lock_held_read_only=True, old_lock_identity=config['old_lock_identity'],
        expires_utc=utc(max(config['horizons'].values())), interval_seconds=3600,
        completed_collections=0, next_cut_utc=utc(time.time()), phase='COLLECTING', publishing=False,
        lock_descriptors=descriptors, model_calls=0, native_signals=0,
        caption_observation=dict(expected=config['caption_collector'], observed=process(config['caption_collector']['pid']), actions=0))
    save(HERE / 'operator/PROCESS.json', state)
    while time.time() < max(config['horizons'].values()):
        state.update(phase='COLLECTING', last_attempt_utc=utc(time.time()))
        save(HERE / 'operator/PROCESS.json', state)
        save(HERE / 'public/SERVICE.json', state)
        if sha(config_path) != config_sha:
            raise ValueError('immutable_observer_config_changed')
        try:
            cut = run_once(config)
            state.update(completed_collections=state['completed_collections'] + 1, last_cut_utc=cut['observed_utc'],
                actual_current_bound_sources=cut['actual_current_bound_sources'], phase='SCHEDULED')
        except Exception as error:
            save(HERE / 'private/SERVICE_ERROR.json', dict(error=str(error), time_unix=time.time()))
            state.update(phase='SCHEDULED_AFTER_ERROR')
        due = min(next_hour(time.time()), max(config['horizons'].values()))
        state['next_cut_utc'] = utc(due)
        save(HERE / 'operator/PROCESS.json', state)
        save(HERE / 'public/SERVICE.json', state)
        while time.time() < due:
            time.sleep(max(0, min(5, due - time.time())))
    state.update(phase='EXITED_SOURCE_HORIZONS', next_cut_utc=None)
    save(HERE / 'operator/PROCESS.json', state)
    save(HERE / 'public/SERVICE.json', state)
    save(HERE / 'operator/EXIT.json', dict(reason='all_conservative_source_horizons_elapsed', time_unix=time.time(), native_signals=0))


if __name__ == '__main__':
    serve()
