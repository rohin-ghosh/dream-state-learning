"""Read existing observer receipts and private immutable tails; no transport."""

import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path


OWN = Path(__file__).resolve().parent
PREVIOUS = OWN.parent / 'rohin227_intention_audit_20260918'


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def load_prior_audit():
    path = PREVIOUS / 'audit.py'
    specification = importlib.util.spec_from_file_location('r228_bound_r227_audit', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module, sha(path.read_bytes())


def merge(evidence, batch):
    if (batch['journal_id'] != evidence['journal_id']
            or batch['anchor']['index'] != evidence['head']['index']
            or batch['anchor']['sha256'] != evidence['head']['sha256']):
        raise ValueError('source_tail_anchor_mismatch')
    previous = batch['anchor']
    chain = {}
    for meta in batch['continuity']:
        if (meta['index'] != previous['index'] + 1 or meta['previous_sha256'] != previous['sha256']
                or meta['journal_id'] != batch['journal_id']):
            raise ValueError('source_tail_chain_mismatch')
        chain[meta['index']] = meta
        previous = meta
    if previous != batch['through']:
        raise ValueError('source_tail_through_mismatch')
    for event in batch['events']:
        meta = chain.get(event['record_index'])
        if not meta or meta['sha256'] != event['record_sha256'] or meta['kind'] != event['kind']:
            raise ValueError('source_tail_event_mismatch')
    result = copy.deepcopy(evidence)
    result['events'].extend(batch['events'])
    result['continuity'].extend(batch['continuity'])
    result['head'] = batch['through']
    result['observed_unix'] = batch['observed_unix']
    return result


def from_observer(label):
    if label not in ('C2', 'P7'):
        raise ValueError('known_observer_label_required')
    latest_bytes = (PREVIOUS / f'operator/{label}_LATEST.json').read_bytes()
    latest = json.loads(latest_bytes)
    parts = latest['observation']['input_part_sha256']
    if not 1 <= len(parts) <= 256:
        raise ValueError('bounded_source_parts_required')
    wanted = set(parts)
    by_hash = {}
    for path in (PREVIOUS / 'private').glob(f'{label}_*.json'):
        if path.stat().st_size > 128 * 1024 * 1024:
            raise ValueError('private_input_size_bound')
        payload = path.read_bytes()
        identifier = sha(payload)
        if identifier in wanted:
            by_hash[identifier] = payload
    if set(by_hash) != wanted:
        raise ValueError('bound_private_source_unavailable')
    evidence = json.loads(by_hash[parts[0]])
    for identifier in parts[1:]:
        evidence = merge(evidence, json.loads(by_hash[identifier]))
    if (evidence['head']['index'] != latest['head']['index']
            or evidence['head']['sha256'] != latest['head']['sha256']):
        raise ValueError('observer_projection_cut_mismatch')
    provenance = dict(observer_projection_sha256=sha(latest_bytes), input_part_sha256=parts,
                      observed_utc=latest['observed_utc'], remote_calls=0,
                      source_observer_identity=latest['observation']['observer_identity'])
    return evidence, provenance


def prior_watcher_receipt():
    payload = (PREVIOUS / 'operator/PROCESS.json').read_bytes()
    source = json.loads(payload)
    matching = False
    state = None
    try:
        fields = Path(f"/proc/{source['pid']}/stat").read_text().rsplit(')', 1)[1].split()
        matching = int(fields[19]) == source['start_ticks']
        state = fields[0] if matching else None
    except (FileNotFoundError, ProcessLookupError):
        pass
    return dict(schema='R228_PRIOR_OBSERVER_STATE_RECEIPT_V1',
                observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source_receipt_sha256=sha(payload), pid=source['pid'], start_ticks=source['start_ticks'],
                proc_identity_matches=matching, proc_state=state, status=source['status'],
                expires_utc=source['expires_utc'], interval_seconds=source['interval_seconds'],
                successful_polls=source['successful_polls'], last_success_utc=source.get('last_success_utc'),
                errors=source.get('errors', []), signals_sent=0, observer_restarted=False,
                observer_expiry_extended=False)
