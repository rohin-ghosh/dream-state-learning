"""CPU-only source coverage and timestamp reduction; never dispatches native work."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import time


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(campaign, row):
    relative = Path(row['source_call_path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    source = campaign / relative
    assert source.resolve().is_relative_to(campaign.resolve())
    call = read(source)
    assert sha(source) == row['source_call_sha256']
    assert call['response']['raw'] == row['target']
    assert call['task_id'] == row['episode_id']
    assert hashlib.sha256(row['target'].encode()).hexdigest() == row['target_sha256']
    return source


def coverage(campaign, output):
    rows = read(output / 'ROWS.json')
    episodes = [read(path) for path in sorted(output.glob('EPISODE_*.json'))]
    losses = [json.loads(line) for line in (output / 'LOSSES.jsonl').read_text().splitlines() if line]
    verified = []
    for position, episode in enumerate(episodes):
        matching = [row for row in rows if row['episode_id'] == episode['task']['id']]
        assert sum(row['kind'] == 'past_attempt' for row in matching) == bool(episode.get('trace'))
        assert sum(row['kind'] == 'past_reflection' for row in matching) == 1
        for row in matching:
            source = verify_source(campaign, row)
            assert row['outcome'] == episode['outcome']['status']
            assert not row['teacher_in_prefix'] and not row['observed_fact_endorsement']
            prefix = '\n'.join(message['content'] for message in row['student_prefix'])
            assert 'NOT as an endorsed solution' in prefix
            assert f'Actual recorded attempt outcome: {row["outcome"]}' in prefix
            mask_path = output / f'MASK_{position:02d}_{row["kind"]}.json'
            mask = read(mask_path)
            active = [index for index, label in enumerate(mask['labels']) if label != -100]
            assert active and active[0] > 0
            assert [mask['labels'][index] for index in active] == mask['target_ids']
            assert all(mask['input_ids'][index] == mask['labels'][index] for index in active)
            writes = sum(loss['source'].get('episode_id') == row['episode_id'] and
                loss['source']['kind'] == row['kind'] for loss in losses)
            assert writes == row['actual_presentations'] and writes > 0
            verified.append(dict(episode_id=row['episode_id'], kind=row['kind'], outcome=row['outcome'],
                presentations=writes, source_sha256=sha(source), mask_sha256=sha(mask_path)))
    return dict(phase=str(output), complete_sha256=sha(output / 'COMPLETE.json'),
        rows_sha256=sha(output / 'ROWS.json'), episodes=len(episodes),
        negative_episodes=sum(episode['outcome']['status'] != 'CORRECT' for episode in episodes),
        verified_rows=verified, update_kinds=dict(Counter(loss['source']['kind'] for loss in losses)),
        all_present_rows_verified=True)


def timing(campaign, output, now):
    request = read(output / 'REQUEST.json')
    terminal = next((read(output / name) for name in ('COMPLETE.json', 'FAILED.json')
        if (output / name).exists()), {})
    calls = [read(path) for path in sorted(output.glob('CALL_*.json'))]
    generation = defaultdict(float)
    for call in calls:
        if 'response' in call and 'finished_unix' in call:
            generation[call['purpose']] += call['finished_unix'] - call['started_unix']
    finish = terminal.get('finished_unix', now)
    cycle = output.parent.name.removeprefix('cycle')
    arm = output.parent.parent.name
    transcript = campaign.parent / 'parent_transcripts' / campaign.name / f'{arm}_C{cycle}'
    parent_done = transcript / 'COMPLETE.json'
    invocation = transcript / 'INVOCATION.json'
    queue = campaign / 'parent_queue' / f'{arm}_C{cycle}.request.json'
    response = queue.with_name(f'{arm}_C{cycle}.response.json')
    reflections = [call for call in calls if call['purpose'] == 'reflection']
    return dict(phase=str(output), status='COMPLETE' if (output / 'COMPLETE.json').exists()
        else 'FAILED' if (output / 'FAILED.json').exists() else 'PARTIAL',
        started_unix=request['started_unix'], finished_unix=terminal.get('finished_unix'),
        elapsed_seconds=finish - request['started_unix'], updates=terminal.get('updates'),
        responses=sum('response' in call for call in calls), reservations=len(calls),
        generation_seconds_by_purpose=dict(generation),
        load_to_first_call_seconds=min(call['started_unix'] for call in calls) - request['started_unix'] if calls else None,
        parent_http_wall_seconds=read(parent_done)['finished_unix'] - read(invocation)['started_unix']
        if parent_done.exists() and invocation.exists() and output.name == 'experience'
        and read(invocation).get('provider') == 'EXISTING_VERIFIED_PRIMARY_RESPONSES' else None,
        parent_queue_seconds=response.stat().st_mtime - queue.stat().st_mtime
        if response.exists() and output.name == 'experience' else None,
        sleep_envelope_seconds=finish - min(call['started_unix'] for call in reflections) if reflections else None,
        optimizer_only_seconds=None, failure_message=terminal.get('message'),
        complete_sha256=sha(output / 'COMPLETE.json') if (output / 'COMPLETE.json').exists() else None,
        after_sha256=sha(output / 'AFTER.json') if (output / 'AFTER.json').exists() else None)


def audit(root):
    now = time.time()
    result = dict(observed_unix=now, raw_local=False, parent_may_read=False, timings=[], coverage=[])
    for name, arm in (
        ('campaign_03_r102_micro5', 'GUIDED_SLEEP'), ('campaign_04_r102_creative7', 'GUIDED_SLEEP'),
        ('campaign_02_recovery_paired', 'GUIDED_SLEEP'), ('campaign_02_recovery_paired', 'UNPARENTED_SLEEP')):
        campaign = root / name
        for output in sorted((campaign / arm).glob('cycle*/*')):
            if not output.is_dir() or not (output / 'REQUEST.json').exists():
                continue
            result['timings'].append(timing(campaign, output, now))
            if output.name == 'experience' and (output / 'COMPLETE.json').exists():
                result['coverage'].append(coverage(campaign, output))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(audit(options.root), indent=2))
