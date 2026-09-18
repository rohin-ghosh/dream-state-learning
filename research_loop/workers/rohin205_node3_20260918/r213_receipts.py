"""Read-only phase/source receipts, with no score or private-evaluation reads."""

from datetime import datetime, timezone
import json
from pathlib import Path

from r209_filter_resume import ROOT, POLICY, REPAIR_FILES, read, require, sha, write
from r209_node3_audit import metadata, read_record
from r213_policy import ASSIGNMENTS


def bound(path, record):
    return dict(path=str(path), index=record['index'], sha256=record['sha256'])


def collect(name):
    arm = ROOT / name
    active_path = arm / 'ACTIVE_RUNTIME.json'
    active = read(active_path) if active_path.exists() else dict(source=str(arm / 'source'), control=str(arm / 'control'))
    control, source = Path(active['control']), Path(active['source'])
    guard, plan = read(control / 'GUARD.json'), read(control / 'PLAN.json')
    phase = read(arm / 'r213_parent/PHASE_START.json')
    result = dict(assignment=ASSIGNMENTS[name], root=str(arm), phase_start=phase,
        plan_sha256=sha(control / 'PLAN.json'), hard_end_unix=plan['hard_end_unix'],
        presentations=plan['new_presentations'], plasticity=plan.get('plasticity'),
        parent_publications=[], parent_renders=[], peer_receipts=[], own_committed=[],
        environment='CLOSED_TEXT_ONLY_NO_EXECUTOR', fresh_matched_causality_claim=False,
        sealed_evaluation_read=False, new_peer_topology_complete=False)
    result['deployed_filter_files'] = {}
    for relative, expected in REPAIR_FILES.items():
        require(sha(source / relative) == guard['source_pins'][relative] == expected, 'actual_deployed_filter_binding')
        result['deployed_filter_files'][relative] = expected
    publications = {}
    for path in sorted((arm / 'r213_parent').glob('PUBLICATION_*.json')):
        publication = read(path)
        publications[publication['publication']['id']] = publication
        result['parent_publications'].append(dict(path=str(path), file_sha256=sha(path), **publication))
    for path in sorted((arm / 'r213_parent').glob('RENDERED_*.json')):
        rendered = read(path)
        request_path = arm / 'raw/stream/records' / f'{rendered["request_index"]:020d}.json'
        request = read_record(request_path)
        publication = publications[rendered['publication_id']]
        require(request['sha256'] == rendered['request_sha256'] and request['kind'] == 'REQUEST'
            and any(publication['text'] in item.get('content', '') for item in request['document']['messages'])
            and request['document']['render_receipt']['all_history_tokens_masked'], 'actual_masked_parent_render')
        result['parent_renders'].append(dict(path=str(path), **rendered))
    paths = [(path, metadata(path)) for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))]
    result['journal_tail'] = [dict(index=int(path.stem), kind=kind) for path, kind in paths[-12:]]
    complete_path = next((path for path, kind in reversed(paths) if kind == 'SLEEP_COMPLETE'), None)
    if complete_path is not None:
        result['latest_complete_file'] = dict(index=int(complete_path.stem), path=str(complete_path),
            file_sha256=sha(complete_path))
    for filename in ('EXIT.json', 'OUTER_EXIT.json', 'FAILED.json', 'OUTER_FAILED.json'):
        if (control / filename).exists():
            result[filename] = read(control / filename)
    loaded_path = next(path for path, kind in reversed(paths) if kind == 'LOADED')
    loaded = read_record(loaded_path)
    result['loaded'] = dict(bound(loaded_path, loaded), **loaded['document'])
    try:
        process = Path('/proc', str(loaded['document']['pid']))
        command = (process / 'cmdline').read_bytes().split(b'\0')
        status = (process / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        result['current_native'] = str(control / 'GUARD.json').encode() in command and status not in ('Z', 'X')
        result['process_state'] = status
    except FileNotFoundError:
        result['current_native'] = False
    response = None
    for path, kind in paths:
        if int(path.stem) <= loaded['index']:
            continue
        if kind == 'COMPACTION' and name.startswith('r213_'):
            record = read_record(path)
            if record['document'].get('kind', '').startswith('R205_BIRTH'):
                result['birth_compaction'] = dict(bound(path, record), kind=record['document']['kind'])
        if int(path.stem) <= phase['floor']:
            continue
        if kind not in ('RESPONSE', 'R205_PEER_THINK_INPUT', 'COMMITTED', 'TARGET_ELIGIBILITY', 'TERMINAL'):
            continue
        record = read_record(path)
        document = record['document']
        if kind == 'RESPONSE':
            response = record
            output = dict(bound(path, record), raw=document['response']['raw'], finished_unix=document.get('finished_unix'))
            result.setdefault('first_response_after_phase_publication', output)
            result['latest_response_after_phase_publication'] = output
        elif kind == 'R205_PEER_THINK_INPUT':
            result['peer_receipts'].append(dict(bound(path, record), **document))
        elif kind == 'COMMITTED' and response is not None:
            row = document['state']['state']['rows'][-1]
            require(row['target'] == response['document']['response']['raw'], 'own_raw_response_unchanged')
            require(row.get('prose_target_filter') == POLICY, 'initial_COMMITTED_R209_annotation')
            result['own_committed'].append(dict(bound(path, record), prose_target_filter=row['prose_target_filter'],
                response_sha256=response['sha256'], source_sha256=row['source_sha256'], original_target_unchanged=True))
        elif kind == 'TARGET_ELIGIBILITY':
            result['latest_target_eligibility'] = dict(bound(path, record), **document)
        elif kind == 'TERMINAL':
            result['terminal'] = dict(bound(path, record), **document)
    return result


def main():
    observed = datetime.now(timezone.utc)
    receipt = dict(observed_utc=observed.isoformat(), arms={name: collect(name) for name in ASSIGNMENTS},
        data_classification='OPERATIONAL_RECEIPTS_WITH_HOST_PATHS_NOT_PRIVATE_EVALUATION')
    receipt['current_native_count'] = sum(arm['current_native'] for arm in receipt['arms'].values())
    path = ROOT / ('R213_PHASE_RECEIPTS_' + observed.strftime('%Y%m%dT%H%M%SZ') + '.json')
    write(path, receipt)
    print(json.dumps(dict(receipt_path=str(path), observed_utc=receipt['observed_utc'],
        current_native_count=receipt['current_native_count'], arms={name: dict(
            physical=row['assignment'][0], pid=row['loaded']['pid'], loaded=row['loaded']['index'],
            loaded_unix=row['loaded']['loaded_unix'], current=row['current_native'],
            phase_floor=row['phase_start']['floor'], renders=[item['request_index'] for item in row['parent_renders']],
            peers=[dict(sender=item['sender'], phase=item.get('phase'),
                THINK_verified=item['actual_THINK_render_verified']) for item in row['peer_receipts']],
            committed=len(row['own_committed']), birth_compaction=row.get('birth_compaction'),
            latest_response=row.get('latest_response_after_phase_publication', {}).get('index'))
            for name, row in receipt['arms'].items()})))


if __name__ == '__main__':
    main()
