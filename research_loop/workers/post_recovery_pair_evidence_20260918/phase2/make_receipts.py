"""Project bounded public provenance from private, immutable TRAIN captures."""

from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[3]
FILES = ('gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    captured = json.loads((OWN / 'private/capture.json').read_text())
    sources = {}
    for label, cut in captured.items():
        files = {}
        for relative, source in cut['files'].items():
            assert cut['guard']['source_pins'][relative] == source['sha256']
            files[relative] = dict(running_disk_sha256=source['sha256'],
                native_guard_source_pin=source['sha256'], guard_match=True)
            if relative in FILES:
                files[relative]['proposed_fork_sha256'] = sha(OWN / 'fork' / relative)
        sources[label] = dict(pid=cut['native']['pid'], start_ticks=cut['native']['start_ticks'],
            process_state=cut['native']['process_state'], guard_sha256=cut['native']['guard_sha256'],
            files=files, binding='verified /proc cwd and native guard; not resident Python heap attestation')
    trace = []
    for label, indices in [('learner', (4056, 4135, 4214, 4293)), ('frozen', (2690, 2699, 2723, 2732, 2756, 2765))]:
        cut = json.loads((OWN.parent / 'private' / (label + '.json')).read_text())
        for row in cut['records']:
            if row['index'] not in indices:
                continue
            parents = [event for event in row.get('external', []) if event['actor'] == 'parent']
            selected = [event for event in parents if event['rendered_message_indices'] or event == parents[-1]]
            trace.append(dict(label=label, record_index=row['index'], kind=row['kind'],
                record_sha256=row['sha256'], request_started_unix=row.get('started_unix'),
                all_history_masked=row.get('masked'), historical_parent_events_checked=len(parents),
                parents=[dict(event_id=event['event_id'],
                    source_sha256=event['source_sha256'], rendered_message_indices=event['rendered_message_indices'])
                    for event in selected]))
    compact = next(record for record in captured['frozen']['records'] if record['index'] == 2764)
    compaction = {key: value for key, value in compact['document'].items() if key != 'state'}
    compaction.update(record_index=2764, record_sha256=compact['sha256'], current_parent_raw_position=1165,
        current_parent_id='parent:inbox:910c908bf27745289ac7155581abedf0',
        current_parent_source_sha256='6738e46b1d1c372022c359e85283e9a1265500e2fb60686c4a7573683c7511f0')
    receipt = dict(schema='PHASE2_PARENT_RETENTION_NON_MATERIAL_CPU_REPAIR_V1',
        prepared_utc=datetime.now(timezone.utc).isoformat(), status='PROPOSED_NOT_DEPLOYED',
        scope='worker-local fork, synthetic tests and immutable TRAIN token-budget replay only',
        native_signals=0, remote_file_writes=0, model_generations=0, GPU_jobs=0, parent_messages=0,
        test_contract_sha256={relative: sha(REPOSITORY / relative) for relative in (
            'tests/test_orch_r124_train_history.py', 'tests/test_orch_r125_continual_stream.py',
            'organism_v6/orch_r125_plain_context.py')},
        sources=sources, source_capture_saved_utc=datetime.fromtimestamp(
            (OWN / 'private/capture.json').stat().st_mtime, timezone.utc).isoformat(),
        verified_requests=trace, exact_lost_parent_compaction=compaction)
    (OWN / 'PROVENANCE.json').write_text(json.dumps(receipt, indent=2) + '\n')
    differences = []
    for relative in FILES:
        original = captured['frozen']['files'][relative]['text']
        proposed = (OWN / 'fork' / relative).read_text()
        differences.extend(difflib.unified_diff(original.splitlines(True), proposed.splitlines(True),
            fromfile='a/' + relative, tofile='b/' + relative))
    (OWN / 'REPAIR.patch').write_text(''.join(differences))
    public = [path for path in OWN.rglob('*') if path.is_file()
        and 'private' not in path.relative_to(OWN).parts and '__pycache__' not in path.relative_to(OWN).parts
        and path.name != 'MANIFEST.json']
    (OWN / 'MANIFEST.json').write_text(json.dumps({str(path.relative_to(OWN)): sha(path)
        for path in sorted(public)}, indent=2) + '\n')


if __name__ == '__main__':
    main()
