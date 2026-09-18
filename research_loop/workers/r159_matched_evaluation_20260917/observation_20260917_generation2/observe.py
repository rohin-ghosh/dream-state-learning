import base64
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time


ROOT = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
COHORT = 'da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b'
ARMS = ('parented_learning', 'parented_frozen', 'unparented_learning')
END = 1789632000
SCAN_LIMIT = 240 * 1024 * 1024
RETURN_LIMIT = 16 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate_key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def regular_path(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink')


class Reader:
    def __init__(self, root, limit=SCAN_LIMIT, end=END):
        self.root, self.limit, self.end = root, limit, end
        self.bytes = 0
        self.files = 0

    def read(self, path):
        if time.time() >= self.end:
            raise ValueError('authority_expired')
        path.relative_to(self.root)
        regular_path(path)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError('not_regular')
            if before.st_size > 16 * 1024 * 1024 or self.bytes + before.st_size + 1 > self.limit:
                raise ValueError('scan_limit')
            raw = stream.read(before.st_size + 1)
            self.bytes += len(raw)
            self.files += 1
            after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns) or len(raw) != before.st_size:
            raise ValueError('changed_during_read')
        return raw, dict(path=str(path), sha256=digest(raw), bytes=len(raw),
            filesystem_mtime_unix=before.st_mtime, filesystem_time_is_event_time=False)

    def document(self, path):
        raw, reference = self.read(path)
        return decode(raw), reference


def fields(document, names):
    return {name: document[name] for name in names if name in document}


def journal(reader, arm_root):
    directory = arm_root / 'stream/records'
    result = dict(status='UNKNOWN', coverage_complete=False, records=[], counts={})
    start_bytes = reader.bytes
    try:
        regular_path(directory)
        manifest, reference = reader.document(arm_root / 'stream/JOURNAL.json')
        result['manifest'] = reference
        previous = digest(canonical(manifest))
        names = set(os.listdir(directory))
        indices = sorted(int(name[:-5]) for name in names if re.fullmatch(r'\d{20}\.json', name))
        counts = Counter()
        result['snapshot_record_count'] = len(indices)
        for expected, index in enumerate(indices):
            if reader.bytes - start_bytes > 70 * 1024 * 1024:
                raise ValueError('arm_scan_limit')
            if index != expected:
                raise ValueError('noncontiguous_journal')
            document, record_ref = reader.document(directory / f'{index:020d}.json')
            intent, intent_ref = reader.document(directory / f'{index:020d}.intent.json')
            payload = {key: value for key, value in document.items() if key != 'sha256'}
            if (document['index'] != index or document['previous_sha256'] != previous
                    or document['sha256'] != digest(canonical(payload))
                    or document['journal_id'] != manifest['journal_id']
                    or document['schema'] != manifest['schema']
                    or intent != dict(schema=document['schema'], journal_id=document['journal_id'],
                        index=index, previous_sha256=previous, record_sha256=document['sha256'])):
                raise ValueError('chain_or_intent_binding')
            previous = document['sha256']
            kind, body = document['kind'], document['document']
            counts[kind] += 1
            result['counts'] = dict(counts)
            entry = dict(index=index, kind=kind, record=record_ref, intent=intent_ref,
                chain_sha256=previous)
            if kind == 'COMMITTED' and body.get('kind') == 'BIRTH':
                entry['event'] = 'BIRTH'
                result.setdefault('first_birth', entry)
            if kind == 'LOADED':
                entry.update(fields(body, ('loaded_unix', 'optimizer_steps', 'resume', 'cohort_sha256', 'matched_arm')))
                result.setdefault('first_loaded', entry)
            if kind == 'REQUEST':
                entry.update(fields(body, ('started_unix', 'segment', 'split')))
                result.setdefault('first_train_request', entry)
            if kind == 'RESPONSE':
                entry.update(fields(body, ('finished_unix', 'request_sha256')))
                result.setdefault('first_train_response', entry)
            if kind == 'COMMITTED' and body.get('kind') != 'BIRTH':
                entry.update(fields(body, ('segment',)))
                result.setdefault('first_train_commit', entry)
            result['records'].append(entry)
        result['listing_stable'] = names == set(os.listdir(directory))
        result['all_intents_paired'] = names == {
            name for index in indices for name in (f'{index:020d}.json', f'{index:020d}.intent.json')}
        result['status'] = 'VERIFIED_RETAINED_PREFIX'
        result['verified_record_count'] = len(result['records'])
        result['last_chain_sha256'] = previous
    except (ValueError, OSError, KeyError, TypeError) as error:
        result['status'] = 'INCOMPLETE'
        result['error_type'] = type(error).__name__
    result['reason'] = 'Retained prefix is not external complete-history or exact first-event timestamp attestation.'
    return result


def readouts(reader, arm_root):
    directory = arm_root / 'readouts'
    result = dict(status='UNKNOWN', coverage_complete=False, receipts=[])
    try:
        regular_path(directory)
        names = set(os.listdir(directory))
        allowed = sorted(name for name in names if re.fullmatch(
            r'sleep_\d{6}_(?:R150_OPEN|R150_CLOSED|DISPATCH)\.json', name))
        for name in allowed:
            document, reference = reader.document(directory / name)
            entry = dict(reference=reference, metadata=fields(document, (
                'opened_unix', 'closed_unix', 'started_unix', 'cycle', 'checkpoint_sha256',
                'resident_pid', 'resident_start_ticks', 'native_dispatcher_sha256',
                'status', 'open_sha256', 'dispatch_sha256', 'parent_present', 'history_shared',
                'evaluation_completion_marker_present', 'evaluation_failure_marker_present',
                'evaluation_contents_read')))
            if 'binding' in document:
                entry['binding'] = fields(document['binding'], ('schema', 'plan_sha256', 'cycle',
                    'matched_arm', 'cohort_sha256', 'checkpoint_commit_sha256',
                    'parent_present', 'history_shared'))
            result['receipts'].append(entry)
        result['listing_stable'] = names == set(os.listdir(directory))
        result['status'] = 'CUSTODY_METADATA_ONLY'
        result['reason'] = 'Open/dispatch timestamps precede model exposure; closed markers do not timestamp first item.'
    except (ValueError, OSError, KeyError, TypeError) as error:
        result['error_type'] = type(error).__name__
    return result


def observe(root=ROOT, expected_cohort=COHORT):
    reader = Reader(root)
    started = time.time()
    raw, cohort_ref = reader.read(root / 'COHORT.json')
    if digest(raw) != expected_cohort:
        raise ValueError('wrong_cohort')
    result = dict(schema='R159_BOUNDED_SOURCE_OBSERVATION_V1',
        status='OBSERVATION_ONLY_AWAITING_SOURCE_OWNER_ATTESTATION',
        hostname=socket.gethostname(), started_unix=started, cohort=cohort_ref,
        authority_read_end_unix=END, scan_limit_bytes=SCAN_LIMIT,
        return_limit_bytes=RETURN_LIMIT, arms={}, original_commit_bytes_base64={},
        source_written=False, adapter_payload_read=False, optimizer_rng_payload_read=False,
        held_contents_read=False, enrollment=False, gpu_calls=0)
    for arm in ARMS:
        arm_root = root / arm
        arm_result = dict(root=str(arm_root), coverage_complete=False)
        result['arms'][arm] = arm_result
        try:
            raw, reference = reader.read(arm_root / 'checkpoints/initial/COMMIT.json')
            document = decode(raw)
            arm_result['initial_commit'] = reference
            arm_result['initial_metadata'] = fields(document, ('created_unix', 'optimizer_steps',
                'adapter_state_sha256', 'adapter_files', 'checkpoint_sha256', 'base_sha256'))
            result['original_commit_bytes_base64'][arm] = base64.b64encode(raw).decode('ascii')
        except (ValueError, OSError, KeyError, TypeError) as error:
            arm_result['initial_commit_status'] = 'UNKNOWN'
            arm_result['initial_commit_error_type'] = type(error).__name__
        try:
            document, reference = reader.document(arm_root / 'INITIAL_STATE_VERIFIED.json')
            arm_result['initial_state_verified'] = dict(reference=reference,
                metadata=fields(document, ('observed_unix', 'arm', 'cohort_sha256', 'optimizer_steps')))
        except (ValueError, OSError, KeyError, TypeError) as error:
            arm_result['initial_state_error_type'] = type(error).__name__
        arm_result['readouts'] = readouts(reader, arm_root)
        arm_result['journal'] = journal(reader, arm_root)
    result.update(observed_unix=time.time(), bytes_read=reader.bytes, files_read=reader.files)
    return result


def main():
    if socket.gethostname() != '[REDACTED_HOST]':
        raise ValueError('wrong_host')
    result = observe()
    encoded = canonical(result)
    if len(encoded) > RETURN_LIMIT:
        raise ValueError('return_limit')
    print(encoded.decode('utf-8'))


if __name__ == '__main__':
    main()
