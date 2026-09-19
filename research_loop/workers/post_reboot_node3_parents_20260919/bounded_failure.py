"""Diagnose unchanged byte bounds; publish attributed operational errors only."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time

MAX_RECORD_BYTES = 33554432
MAX_TOTAL_BYTES = 67108864
POLICY = 'R233_UNSCORED_TRANSPORT_ERROR_FEEDBACK_V1'


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def record(root, index, journal_id):
    from gpu.orch_r125_stream_journal import _decode, _digest
    path = Path(root) / 'stream/records' / f'{index:020d}.json'
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_RECORD_BYTES:
        raise ValueError('bounded_regular_original_record_required')
    raw = path.read_bytes()
    value = _decode(raw)
    if (value['index'] != index or value['journal_id'] != journal_id or value['sha256'] !=
            _digest({key:item for key,item in value.items() if key != 'sha256'})):
        raise ValueError('exact_original_index_journal_hash_required')
    return value, dict(index=index, kind=value['kind'], bytes=len(raw),
        sha256=value['sha256'], file_sha256=digest_bytes(raw), path=str(path))


def minimal_window(root, origin, journal_id):
    from gpu.ny_caption_life import child_act, latest_own_think
    child_act(root, origin)
    think = latest_own_think(root, origin)
    first = think['origin']['record_index'] if think else origin['record_index']
    final = None
    for index in range(origin['record_index'] + 1, origin['record_index'] + 33):
        value, unused = record(root, index, journal_id)
        if value['kind'] == 'R184_STAGE':
            final = index
            break
    if final is None or final - first > 288:
        raise ValueError('original_stage_window_bound_required')
    rows, previous = [], None
    for index in range(first, final + 1):
        value, reference = record(root, index, journal_id)
        if previous is not None and value['previous_sha256'] != previous:
            raise ValueError('unchanged_contiguous_THINK_ACT_ancestry_required')
        previous = value['sha256']
        rows.append(reference)
    total = sum(row['bytes'] for row in rows)
    return dict(first=first, final=final, total_bytes=total, bound_bytes=MAX_TOTAL_BYTES,
        exceeds_bound=total > MAX_TOTAL_BYTES, excess_bytes=max(0,total-MAX_TOTAL_BYTES),
        THINK=think['origin'] if think else None, ACT=origin, records=rows,
        original_bytes_only=True, all_ancestry_preserved=True,
        repairable_by_smaller_contiguous_window=not (total > MAX_TOTAL_BYTES),
        no_export_or_scoring_performed=True)


def validate_failure(transport, act, journal_id):
    origin = transport['origin']
    environment = act['document'].get('outcome', {}).get('environment', {})
    report = environment.get('report', {})
    if (transport.get('dispatched') is not False or transport.get('receipt_sha256') is not None
            or transport.get('error') != 'ORIGIN_TRANSPORT_NOT_DISPATCHED'
            or act['kind'] != 'R184_ACT' or act['journal_id'] != journal_id
            or act['document']['origin'] != origin or environment.get('origin') != origin
            or environment.get('receipt_sha256') or report.get('feedback')
            or report.get('error') != 'ORIGIN_TRANSPORT_NOT_DISPATCHED'
            or report.get('error_type') != transport.get('error_type')):
        raise ValueError('source_bound_confirmed_not_dispatched_failure_required')


def message(origin, window):
    if not window['exceeds_bound']:
        raise ValueError('do_not_mislabel_non_bound_failure')
    return (f"No judgment: operational transport failure for your ACT response {origin['record_index']} "
        f"({origin['record_sha256'][:12]}). Its complete authenticated ACT/THINK record window "
        f"requires {window['total_bytes']} bytes, exceeding the unchanged 64MiB "
        f"({MAX_TOTAL_BYTES}-byte) transport limit. The scorer was not contacted for this attempt. "
        "No rank, acceptance decision, or zero score exists; this is not a rejection of your caption. "
        "No ACT was replayed, and no evidence or THINK attribution was dropped.")


def immutable(path, value):
    raw = json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode() + b'\n'
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable_operational_evidence_changed')
        return
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.name+'.pending-',delete=False) as stream:
        temporary=Path(stream.name)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        try:
            os.link(temporary,path)
        except FileExistsError:
            if path.read_bytes()!=raw:
                raise ValueError('immutable_operational_evidence_changed')
    finally:
        temporary.unlink()


def publish_once(root, destination, projection):
    from gpu.orch_r127_pilot_console import _inbox
    from organism_v6.orch_r124_train_history import TrainEvent
    from organism_v6.orch_r125_plain_context import event_message, has_scaffolding
    text = projection['text']
    event = TrainEvent(event_id='environment:inbox:operationalcheck',actor='environment',
        text='Tool: ' + text,split='TRAIN',phase='feedback',episode_id='continual_stream',
        source_id=projection['ACT_record']['path'],source_sha256=projection['ACT_record']['sha256'],
        origin='TRAIN_COLLECTION')
    if has_scaffolding('Tool: ' + text) or event_message(event)['content'] != 'Tool: ' + text:
        raise ValueError('existing_plain_Tool_renderer_required')
    destination.mkdir(mode=0o700,parents=True,exist_ok=True)
    key = digest_bytes(json.dumps(projection,sort_keys=True,separators=(',',':')).encode())
    projection_path = destination / (key + '.projection.json')
    receipt_path = destination / (key + '.published.json')
    with (destination/'WRITER.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        immutable(projection_path,projection)
        source = dict(path=str(projection_path),sha256=digest_bytes(projection_path.read_bytes()))
        if receipt_path.exists():
            saved = json.loads(receipt_path.read_bytes())
            if saved['source_receipt'] != source:
                raise ValueError('existing_projection_source_changed')
            return saved
        existing = None
        for path in (Path(root)/'stream/inbox').glob('*.json'):
            value = json.loads(path.read_bytes())
            if value.get('source_receipt') == source:
                if (value.get('text') != text or value.get('speaker') != 'Tool'
                        or value.get('actor') != 'environment'):
                    raise ValueError('existing_operational_inbox_conflict')
                existing = dict(id=value['id'],path=str(path),sha256=digest_bytes(path.read_bytes()))
                break
        publication = existing or _inbox(root,'Tool',text,source)
        saved = dict(schema=POLICY,origin=projection['origin'],ACT_record=projection['ACT_record'],
            publication=publication,source_receipt=source,published_unix=time.time(),
            recovered_existing_inbox=existing is not None,scoring_calls=0,scorer_receipt=False,
            no_judgment=True,native_signals=[],target_rows_written=0)
        immutable(receipt_path,saved)
        return saved


def receipt(root, saved, journal_id):
    publication = saved['publication']
    inbox_path = Path(publication['path'])
    if (digest_bytes(inbox_path.read_bytes()) != publication['sha256']
            or digest_bytes(Path(saved['source_receipt']['path']).read_bytes()) != saved['source_receipt']['sha256']):
        raise ValueError('unchanged_operational_publication_required')
    inbox = None
    for path in sorted((Path(root)/'stream/records').glob('[0-9]'*20+'.json')):
        if int(path.stem) <= saved['ACT_record']['index']:
            continue
        with path.open('rb') as stream:
            stream.seek(max(0,path.stat().st_size-8192))
            found=re.findall(rb',"index":(\d+),"journal_id":"[^"]+","kind":"([^"]+)"',stream.read())
        if not found or int(found[-1][0])!=int(path.stem):
            raise ValueError('exact_journal_metadata_required')
        if found[-1][1]!=b'INBOX':
            continue
        value, reference = record(root,int(path.stem),journal_id)
        if value['kind']=='INBOX' and value['document']['message']['id']==publication['id']:
            if value['document']['source_sha256'] != publication['sha256']:
                raise ValueError('exact_operational_INBOX_required')
            inbox = reference
            break
    return dict(saved,INBOX=inbox,status='OPERATIONAL_ERROR_INBOX_VERIFIED' if inbox else 'OPERATIONAL_ERROR_PUBLISHED_INBOX_PENDING')
