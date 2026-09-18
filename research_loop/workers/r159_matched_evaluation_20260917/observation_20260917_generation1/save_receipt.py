import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


DIRECTORY = Path(__file__).resolve().parent
AUTHORITY = DIRECTORY.parent / 'candidate5_initial3_templates/MAIN_METADATA_READ_AUTHORITY_20260917T0552Z.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc(value):
    return None if value is None else datetime.fromtimestamp(value, timezone.utc).isoformat()


def write_new(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o600)


def save():
    transport_raw = (DIRECTORY / 'TRANSPORT.private.json').read_bytes()
    observation = json.loads(transport_raw)
    originals = observation.pop('original_commit_bytes_base64')
    observation['authority'] = dict(path=str(AUTHORITY), sha256=sha(AUTHORITY.read_bytes()))
    observation['helper_sha256'] = sha((DIRECTORY / 'observe.py').read_bytes())
    observation['transport_sha256'] = sha(transport_raw)
    observation['returned_metadata_bytes'] = len(transport_raw)
    summary = dict(status=observation['status'],
        started_utc=utc(observation['started_unix']), observed_utc=utc(observation['observed_unix']),
        observed_unix=observation['observed_unix'], bytes_read=observation['bytes_read'],
        returned_metadata_bytes=len(transport_raw), files_read=observation['files_read'],
        authority=observation['authority'], helper_sha256=observation['helper_sha256'], arms={})
    for arm, details in observation['arms'].items():
        raw = base64.b64decode(originals[arm], validate=True)
        if sha(raw) != details['initial_commit']['sha256']:
            raise ValueError('transport_commit_hash')
        path = DIRECTORY / f'{arm}.initial.COMMIT.original.json'
        write_new(path, raw)
        details['original_commit_archive'] = dict(path=str(path), sha256=sha(raw))
        journal = details['journal']
        metadata = details.get('initial_state_verified', {}).get('metadata', {})
        birth = journal.get('first_birth', {})
        request = journal.get('first_train_request', {})
        response = journal.get('first_train_response', {})
        committed = journal.get('first_train_commit', {})
        loaded = journal.get('first_loaded', {})
        receipts = details['readouts']['receipts']
        opened = next((entry for entry in receipts if entry['reference']['path'].endswith(
            'sleep_000000_R150_OPEN.json')), None)
        closed = next((entry for entry in receipts if entry['reference']['path'].endswith(
            'sleep_000000_R150_CLOSED.json')), None)
        dispatch = next((entry for entry in receipts if entry['reference']['path'].endswith(
            'sleep_000000_DISPATCH.json')), None)
        readout_binding_verified = bool(opened and closed and dispatch and
            opened.get('binding') == closed.get('binding') and
            closed['metadata'].get('open_sha256') == opened['reference']['sha256'] and
            closed['metadata'].get('dispatch_sha256') == dispatch['reference']['sha256'] and
            opened['binding'].get('checkpoint_commit_sha256') == details['initial_commit']['sha256'] and
            dispatch['metadata'].get('checkpoint_sha256') == details['initial_commit']['sha256'])
        summary['arms'][arm] = dict(initial_commit_sha256=sha(raw),
            original_commit_archive=details['original_commit_archive'],
            optimizer_steps=details['initial_metadata'].get('optimizer_steps'),
            initial_state_verified_sha256=details.get('initial_state_verified', {}).get('reference', {}).get('sha256'),
            birth_record_present=bool(birth), birth_record_sha256=birth.get('record', {}).get('sha256'),
            birth_exact_first_unix=None,
            birth_bracket_utc=[utc(metadata.get('observed_unix')), utc(loaded.get('loaded_unix'))],
            birth_filesystem_mtime_utc=utc(birth.get('record', {}).get('filesystem_mtime_unix')),
            birth_filesystem_time_is_event_time=False,
            first_train_request_utc=utc(request.get('started_unix')),
            first_train_response_utc=utc(response.get('finished_unix')),
            first_train_commit_segment=committed.get('segment'),
            initial_readout_bindings_verified=readout_binding_verified,
            first_readout_open_utc=utc(opened['metadata'].get('opened_unix')) if opened else None,
            first_readout_dispatch_utc=utc(dispatch['metadata'].get('started_unix')) if dispatch else None,
            first_readout_closed_utc=utc(closed['metadata'].get('closed_unix')) if closed else None,
            initial_readout_completion_marker_present=closed['metadata'].get('evaluation_completion_marker_present') if closed else None,
            initial_readout_failure_marker_present=closed['metadata'].get('evaluation_failure_marker_present') if closed else None,
            evaluation_exact_first_unix=None,
            retained_journal_status=journal['status'],
            retained_journal_records=journal.get('verified_record_count', len(journal['records'])),
            snapshot_record_count=journal.get('snapshot_record_count'),
            journal_listing_stable=journal.get('listing_stable'),
            all_intents_paired=journal.get('all_intents_paired'),
            counts=journal['counts'], coverage_complete=False,
            first_exposure_attestation='UNKNOWN_PENDING_SOURCE_OWNER')
    write_new(DIRECTORY / 'OBSERVATION.json', json.dumps(observation, indent=2, sort_keys=True).encode() + b'\n')
    summary['observation_sha256'] = sha((DIRECTORY / 'OBSERVATION.json').read_bytes())
    write_new(DIRECTORY / 'SUMMARY.json', json.dumps(summary, indent=2, sort_keys=True).encode() + b'\n')
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    save()
