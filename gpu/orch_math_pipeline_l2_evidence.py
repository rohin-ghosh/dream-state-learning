"""Author-only failure-aware receipts and taught-to-next-cycle source joins."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def reference(path, root):
    return dict(path=str(path.relative_to(root)), sha256=digest(path.read_bytes()))


def join_transition(campaign, arm, cycle):
    previous = campaign / arm / f'cycle{cycle - 1}/experience'
    current = campaign / arm / f'cycle{cycle}/experience'
    prior = [read(path) for path in sorted(previous.glob('EPISODE_*.json'))]
    actual = [read(path) for path in sorted(current.glob('EPISODE_*.json'))]
    parent_plan = previous / 'PARENT_PLAN.json'
    request_path = campaign / 'parent_queue' / f'{arm}_C{cycle}.request.json'
    parent_request_time = request_path.stat().st_mtime if request_path.exists() else None
    rows = []
    for episode in actual:
        assert episode['task']['split'] == 'TRAIN'
        call = episode.get('trace_call')
        if call is None:
            rows.append(dict(task_id=episode['task']['id'], outcome=episode['outcome'], response_available=False))
            continue
        assert call['purpose'] == 'experience' and call['prior_updates'] == 0
        assert [item['role'] for item in call['messages']] == ['system', 'user']
        assert call['messages'][1]['content'] == episode['task']['question']
        if parent_request_time is not None:
            assert call['finished_unix'] <= parent_request_time
        sources = []
        for earlier in prior:
            assert earlier['task']['split'] == 'TRAIN'
            if earlier['task']['family'] == episode['task']['family'] and earlier.get('reflection_call'):
                reflection = earlier['reflection_call']
                path = campaign / reflection['relative_path']
                assert digest(path.read_bytes()) == earlier['reflection_call_sha256']
                sources.append(dict(task_id=earlier['task']['id'], reflection=reference(path, campaign),
                    outcome=earlier['outcome']))
        path = campaign / call['relative_path']
        assert digest(path.read_bytes()) == episode['trace_call_sha256']
        rows.append(dict(task_id=episode['task']['id'], family=episode['task']['family'],
            response_available='response' in call, outcome=episode['outcome'], original_call=reference(path, campaign),
            parent_free_before_next_guidance=True, preceding_same_family_reflections=sources,
            semantic_guidance_uptake='AUTHOR_REVIEW_PENDING_NOT_AUTO_ADMISSION'))
    return dict(campaign=campaign.name, arm=arm, from_cycle=cycle - 1, to_cycle=cycle,
        planned_denominator=8, captured=len(rows), missing=8 - len(rows),
        correct=sum(row['outcome'].get('correct', False) for row in rows),
        previous_plan=reference(parent_plan, campaign) if parent_plan.exists() else None,
        inherited_learning_claim=arm != 'FROZEN', new_native_calls=0, rows=rows,
        parents_may_read_this_file=False, prior_learning_complete=(previous / 'COMPLETE.json').exists())


def phase_summary(path, root):
    request = path / 'REQUEST.json'
    if not request.exists():
        return None
    calls = [read(item) for item in sorted(path.glob('CALL_*.json'))]
    complete = path / 'COMPLETE.json'
    after = path / 'AFTER.json'
    return dict(path=str(path.relative_to(root)), request=reference(request, root),
        denominators=read(path / 'DENOMINATORS.json'), reservations=len(calls),
        responses=sum('response' in call for call in calls),
        failed_or_unresolved=sum('response' not in call for call in calls),
        output_tokens=sum(len(call.get('response', {}).get('token_ids', [])) for call in calls),
        actual_updates=len((path / 'LOSSES.jsonl').read_text().splitlines()) if (path / 'LOSSES.jsonl').exists() else 0,
        loaded=reference(path / 'LOADED.json', root) if (path / 'LOADED.json').exists() else None,
        complete=reference(complete, root) if complete.exists() else None,
        after=reference(after, root) if after.exists() else None,
        actual_mounted_after_verified=read(after).get('actual_mounted_identity_verified', False) if after.exists() else False)


def snapshot(root, archive):
    assert not archive.exists()
    phases = []
    transitions = []
    paths = [path for path in root.iterdir() if path.is_file() and path.suffix in ('.json', '.log', '.md')]
    for campaign in sorted(root.glob('campaign_*')):
        paths.extend(path for path in campaign.rglob('*') if path.is_file() and path.suffix in ('.json', '.jsonl', '.log', '.txt'))
        for arm in ('GUIDED_SLEEP', 'UNPARENTED_SLEEP', 'FROZEN'):
            for cycle in range(4):
                for phase in ('experience', 'readout'):
                    result = phase_summary(campaign / arm / f'cycle{cycle}' / phase, root)
                    if result:
                        phases.append(result)
            for cycle in (2, 3):
                transitions.append(join_transition(campaign, arm, cycle))
    for folder in ('RECOVERY_GUIDED_SLEEP', 'RECOVERY_UNPARENTED_SLEEP'):
        paths.extend(path for path in (root / folder).glob('*') if path.is_file() and path.suffix in ('.json', '.jsonl'))
    manifest = dict(observed_unix=time.time(), live_snapshot_not_terminal=True, files={},
        phases=phases, taught_next=transitions, checkpoints_not_copied=True, parents_may_read=False)
    with tarfile.open(archive, 'x:gz') as bundle:
        for path in sorted(set(paths)):
            data = path.read_bytes()
            name = str(path.relative_to(root))
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            bundle.addfile(entry, io.BytesIO(data))
            manifest['files'][name] = dict(sha256=digest(data), bytes=len(data),
                stable_during_copy=digest(path.read_bytes()) == digest(data))
        data = json.dumps(manifest, indent=2, sort_keys=True).encode() + b'\n'
        entry = tarfile.TarInfo('EVIDENCE_MANIFEST.json')
        entry.size = len(data)
        bundle.addfile(entry, io.BytesIO(data))
    print(json.dumps(dict(path=str(archive), sha256=digest(archive.read_bytes()), bytes=archive.stat().st_size,
        phases=len(phases), taught_next_captured=sum(item['captured'] for item in transitions))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    options = parser.parse_args()
    snapshot(options.root, options.archive)
