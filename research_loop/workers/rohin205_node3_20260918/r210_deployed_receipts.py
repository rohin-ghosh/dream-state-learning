"""Read-only evidence from actual R210 native records, not staged plans."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket

from r209_filter_resume import POLICY, REPAIR_FILES, ROOT, read, require, sha, write
from r209_node3_audit import metadata, read_record


ARMS = ('conversational', 'peer_math', 'peer_repo', 'p32', 'lr03', 'lr3')


def bound(record, path):
    return dict(index=record['index'], sha256=record['sha256'], path=str(path))


def collect(name):
    arm = ROOT / name
    phase = arm / 'r210_enrichment'
    result = dict(parent_publications=[], parent_rendered=[], peer_deliveries=[],
        committed_rows=[], target_eligibility=[], completed_sleeps=[], environment='NO_EXECUTOR_CONNECTED')
    for path in sorted((arm / 'r210_parent').glob('PUBLICATION_*.json')):
        publication = read(path)
        result['parent_publications'].append(dict(path=str(path), sha256=sha(path),
            publication=publication['publication'], observed_unix=publication['observed_unix'],
            new_object=publication['new_object'], after_act_index=publication['after_act_index']))
    for path in sorted((arm / 'r210_parent').glob('RENDERED_*.json')):
        rendered = read(path)
        request_path = arm / 'raw/stream/records' / f'{rendered["request_index"]:020d}.json'
        request = read_record(request_path)
        publication = next(read(Path(item['path'])) for item in result['parent_publications']
            if item['publication']['id'] == rendered['publication_id'])
        require(request['sha256'] == rendered['request_sha256']
            and request['kind'] == 'REQUEST'
            and any(publication['text'] in message.get('content', '') for message in request['document']['messages'])
            and request['document']['render_receipt']['all_history_tokens_masked'], 'actual_parent_render_binding')
        result['parent_rendered'].append(dict(path=str(path), sha256=sha(path), **rendered))
    active_path = arm / 'ACTIVE_RUNTIME.json'
    if not active_path.exists():
        result['status'] = 'ORIGINAL_NATIVE_R210_BOUNDARY_PENDING'
        return result
    active = read(active_path)
    require(Path(active['control']) == phase / 'control', 'exact_active_R210_control')
    guard = read(phase / 'control/GUARD.json')
    source = Path(active['source'])
    result['deployed_filter_files'] = {}
    for relative, expected in REPAIR_FILES.items():
        actual = sha(source / relative)
        require(actual == expected == guard['source_pins'][relative], 'tested_deployed_filter_hash')
        result['deployed_filter_files'][relative] = actual
    result['preserved_boundary'] = read(phase / 'PRESERVED_COMPLETE.json')
    records = [(path, metadata(path)) for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))]
    loaded_path = next(path for path, kind in reversed(records) if kind == 'LOADED')
    loaded = read_record(loaded_path)
    result['loaded'] = dict(bound(loaded, loaded_path), **loaded['document'])
    try:
        process = Path('/proc', str(loaded['document']['pid']))
        command = (process / 'cmdline').read_bytes().split(b'\0')
        state = (process / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        result['current_native_identity'] = str(phase / 'control/GUARD.json').encode() in command and state not in ('Z', 'X')
    except FileNotFoundError:
        result['current_native_identity'] = False
    if loaded['index'] <= result['preserved_boundary']['complete_index']:
        result['status'] = 'DISPATCHED_NOT_YET_R210_LOADED'
        return result
    result['status'] = 'R210_LOADED_CURRENT' if result['current_native_identity'] else 'R210_LOADED_NOT_CURRENT'
    stages = {}
    for path, kind in records:
        if kind == 'R184_STAGE' and int(path.stem) > loaded['index']:
            document = read_record(path)['document']
            stages[document['segment']] = document['stage']
    response = None
    for path, kind in records:
        if int(path.stem) <= loaded['index'] or kind not in (
                'REQUEST', 'RESPONSE', 'COMMITTED', 'TARGET_ELIGIBILITY', 'R205_PEER_THINK_INPUT', 'SLEEP_COMPLETE'):
            continue
        record = read_record(path)
        document = record['document']
        evidence = bound(record, path)
        if kind == 'REQUEST':
            result.setdefault('first_request', dict(evidence, segment=document['segment'],
                stage=stages.get(document['segment']),
                all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked']))
        elif kind == 'RESPONSE':
            response = record
        elif kind == 'COMMITTED':
            row = document['state']['state']['rows'][-1]
            require(response is not None and row['target'] == response['document']['response']['raw'],
                'unchanged_original_RESPONSE_target')
            require(row.get('prose_target_filter') == POLICY, 'new_R210_English_row_annotation')
            result['committed_rows'].append(dict(evidence, stage=stages.get(row['segment']), segment=row['segment'],
                source_sha256=row['source_sha256'], response_record_sha256=response['sha256'],
                raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                prose_target_filter=row['prose_target_filter'], original_target_unchanged=True))
        elif kind == 'TARGET_ELIGIBILITY':
            result['target_eligibility'].append(dict(evidence, **document))
        elif kind == 'SLEEP_COMPLETE':
            result['completed_sleeps'].append(dict(evidence,
                **{key: value for key, value in document.items() if key != 'resume_state'}))
        elif document.get('phase') == 'R210_PARENTED_COMPLEMENTARY_EXPERIENCE':
            require(document['actual_THINK_render_verified'] and document['imported_training_rows'] == 0,
                'masked_peer_context_no_imported_targets')
            result['peer_deliveries'].append(dict(evidence, **document))
    return result


def main():
    observed = datetime.now(timezone.utc)
    receipt = dict(observed_utc=observed.isoformat(), hostname=socket.gethostname(),
        arms={name: collect(name) for name in ARMS})
    destination = ROOT / ('R210_DEPLOYED_' + observed.strftime('%Y%m%dT%H%M%SZ') + '.json')
    write(destination, receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
