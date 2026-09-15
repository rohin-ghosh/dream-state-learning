"""Read-only lifecycle/behavior monitor, with durable parent-transcript quarantine."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOTS = ['/tmp/orch_route_parent_campaign_20260915_attempt1'] + [
    f'/tmp/orch_route_parent_campaign_20260915_segment{index}' for index in (2, 3, 4)]
ARMS = ('GUIDED', 'UNPARENTED', 'FROZEN')


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    events = []
    if not root.exists():
        return events
    for arm in ARMS:
        for cycle in (0, 1, 2):
            for phase in ('experience', 'sleep', 'readout'):
                folder = root / arm / f'cycle{cycle}' / phase
                complete = folder / 'COMPLETE.json'
                if not complete.exists():
                    continue
                value = read(complete)
                event = dict(key=f'{root.name}/{arm}/C{cycle}/{phase}', root=str(root), arm=arm,
                    cycle=cycle, phase=phase, receipt_sha256=digest(complete), finished_unix=value['finished_unix'],
                    input_child=value['input_adapter']['state_sha256'], process=value['process'],
                    updates=value.get('updates', 0), parent_free=value.get('parent_free'),
                    episodes=value.get('episodes'), output_child=value.get('output_adapter', {}).get('state_sha256'))
                if phase == 'readout' and cycle:
                    taught = root / arm / f'cycle{cycle}/experience/COMPLETE.json'
                    sleep = root / arm / f'cycle{cycle}/sleep/COMPLETE.json'
                    behavior = folder / 'LEARNER_BEHAVIOR.json'
                    previous = read(sleep)
                    if previous['output_adapter'] != value['input_adapter'] or value.get('parent_free') is not True:
                        raise ValueError('required_parent_free_post_sleep_child_binding')
                    event['taught_to_parent_free_next_episodes'] = dict(
                        taught_receipt_sha256=digest(taught), sleep_receipt_sha256=digest(sleep),
                        next_behavior_sha256=digest(behavior), same_saved_child_verified=True,
                        behavioral_measures=read(behavior)['measures'], reward_only=False,
                        scope='FRESH_PARENT_FREE_POST_SLEEP_EPISODES_NOT_A_CAUSAL_IMPROVEMENT_CLAIM')
                if phase == 'experience' and cycle == 2:
                    bridge = folder / 'TAUGHT_TO_NEXT_CYCLE.json'
                    event['actual_next_training_cycle_bridge'] = read(bridge)
                events.append(event)
    return events


def watch(host, local, deadline):
    local.mkdir(parents=True, exist_ok=True)
    remote_script = '/tmp/orch_route_parent_campaign_20260915_monitor.py'
    subprocess.run(['scp', '-q', str(Path(__file__).resolve()), host + ':' + remote_script], check=True)
    seen_path = local / 'SEEN.json'
    seen = set(read(seen_path)) if seen_path.exists() else set()
    while time.time() < deadline:
        result = subprocess.check_output(['ssh', '-o', 'BatchMode=yes', host,
                                          f'python3 {remote_script} --snapshot'], text=True, timeout=30)
        events = json.loads(result)
        for event in events:
            if event['key'] in seen:
                continue
            name = event['key'].replace('/', '__') + '.json'
            (local / name).write_text(json.dumps(event, indent=2, sort_keys=True) + '\n')
            statement = (f'{datetime.now(timezone.utc).isoformat()} — MONITORED {event["key"]}: '
                f'COMPLETE receipt{event["receipt_sha256"]}, updates{event["updates"]}, '
                f'parent_free={event["parent_free"]}, input{event["input_child"]}, output{event["output_child"]}. '
                'Actual behavior/sleep lineage references retained; no launch-only learning claim.')
            with Path('research_loop/workers/ROUTE_PARENT_CAMPAIGN.md').open('a') as journal:
                journal.write('\n' + statement + '\n')
            seen.add(event['key'])
        seen_path.write_text(json.dumps(sorted(seen)) + '\n')
        (local / 'STATUS.json').write_text(json.dumps(dict(observed_unix=time.time(), completed_events=len(seen),
            deadline_unix=deadline, provider_calls=0, model_calls=0)) + '\n')
        time.sleep(20)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true')
    parser.add_argument('--host')
    parser.add_argument('--local-root')
    parser.add_argument('--deadline', type=float)
    args = parser.parse_args()
    if args.snapshot:
        print(json.dumps([event for root in ROOTS for event in snapshot(Path(root))], sort_keys=True))
    else:
        watch(args.host, Path(args.local_root), args.deadline)


if __name__ == '__main__':
    main()
