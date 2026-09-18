"""Metadata-only canonical monitoring; raw tasks and replies stay on node3."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path('/tmp/orch_route_parent_campaign_20260915_canonical102')
ARMS = ('GUIDED', 'UNPARENTED', 'NO_LORA')


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root=ROOT):
    observed = time.time()
    result = dict(observed_utc=datetime.fromtimestamp(observed, timezone.utc).isoformat(),
                  root=str(root), phases=[], parent_responses=[], held_text_exported=False)
    for arm in ARMS:
        for cycle in range(9):
            for phase in ('experience', 'sleep', 'readout'):
                folder = root / arm / f'cycle{cycle}' / phase
                request = folder / 'REQUEST.json'
                if not request.exists():
                    continue
                start = read(request)
                complete, failed = folder / 'COMPLETE.json', folder / 'FAILED.json'
                terminal = complete if complete.exists() else failed if failed.exists() else None
                value = read(terminal) if terminal else {}
                row = dict(arm=arm, cycle=cycle, phase=phase,
                    status='COMPLETE' if complete.exists() else 'FAILED' if failed.exists() else 'RUNNING_CENSORED',
                    started_unix=start['started_unix'], finished_unix=value.get('finished_unix'),
                    elapsed_seconds=value.get('finished_unix', observed) - start['started_unix'],
                    request_path=str(request), request_sha256=digest(request),
                    terminal_path=str(terminal) if terminal else None,
                    terminal_sha256=digest(terminal) if terminal else None,
                    input_identity=start['input_adapter'], updates=value.get('updates'),
                    parent_free=value.get('parent_free'), error=value.get('error'))
                metrics = folder / 'THINKING_METRICS.json'
                if metrics.exists():
                    row['thinking_first'] = read(metrics)
                if complete.exists():
                    row['ancillary_outcomes'] = dict(successes=value.get('successes'), episodes=value.get('episodes'),
                        paired_both_correct=value.get('paired_both_correct'), paired_worlds=value.get('world_denominator'))
                    if phase == 'readout' and cycle:
                        prior = read(root / arm / f'cycle{cycle}/sleep/COMPLETE.json')
                        assert prior['output_adapter'] == value['input_adapter']
                        assert prior['process'] != value['process'] and value['parent_free'] is True
                        row['fresh_parent_free_saved_child_verified'] = True
                    if phase == 'experience' and cycle > 1:
                        prior_path = root / arm / f'cycle{cycle - 1}/sleep/COMPLETE.json'
                        prior = read(prior_path)
                        assert prior['output_adapter'] == value['input_adapter']
                        row['taught_to_actual_next_cycle'] = dict(previous_sleep_sha256=digest(prior_path),
                            current_experience_sha256=digest(complete), same_saved_child=True,
                            different_tasks_exploratory_not_causal=True)
                calls = sorted(folder.glob('CALL_*.json'))
                if calls:
                    call = read(calls[0])
                    row['first_call'] = dict(path=str(calls[0]), sha256=digest(calls[0]),
                        started_unix=call['started_unix'], finished_unix=call.get('finished_unix'),
                        response_observed=call.get('response') is not None,
                        prompt_tokens=call.get('response', {}).get('prompt_tokens'),
                        output_tokens=len(call.get('response', {}).get('token_ids', [])))
                result['phases'].append(row)
    for path in sorted((root / 'parent_raw').glob('*/RECEIPT.json')):
        receipt = read(path)
        result['parent_responses'].append(dict(id=path.parent.name, node_path=str(path), sha256=digest(path),
            actual_model=receipt['actual_model'], started_unix=receipt['started_unix'],
            finished_unix=receipt['finished_unix'], usage=receipt['usage']))
    return result


def watch(host, local, deadline):
    script = '/tmp/orch_route_parent_campaign_canonical102_monitor.py'
    subprocess.run(['scp', '-q', str(Path(__file__).resolve()), host + ':' + script], check=True)
    while time.time() < deadline:
        data = json.loads(subprocess.check_output(['ssh', '-o', 'BatchMode=yes', host,
            f'python3 {script} --snapshot'], text=True, timeout=30))
        temporary = local.with_suffix('.partial')
        temporary.write_text(json.dumps(data, indent=2) + '\n')
        temporary.replace(local)
        time.sleep(15)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true')
    parser.add_argument('--host')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--deadline', type=float)
    args = parser.parse_args()
    if args.snapshot:
        print(json.dumps(snapshot()))
    else:
        watch(args.host, args.output, args.deadline)
