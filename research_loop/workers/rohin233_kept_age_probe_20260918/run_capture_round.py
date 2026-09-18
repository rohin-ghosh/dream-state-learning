"""One finite prospective source-copy round; historical work is opt-in, no GPU work."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import time

from research_loop.workers.rohin233_kept_age_probe_20260918 import capture_priority, capture_retained, enroll


WORKER = Path(__file__).resolve().parent
REPO = WORKER.parents[2]
BASELINE_SHA = '548aa3b6e60675dc402fdba560aa06dddfc94f1c2969311896ade6955afa8f55'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    lock = (WORKER / 'PROSPECTIVE_CAPTURE.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    policy_path = WORKER / 'PROSPECTIVE_POLICY.json'
    coverage_bytes = (WORKER / 'QUEUE_COVERAGE.json').read_bytes()
    if hashlib.sha256(coverage_bytes).hexdigest() != BASELINE_SHA:
        raise ValueError('frozen_published_policy_baseline')
    coverage = json.loads(coverage_bytes)
    if not policy_path.exists():
        policy = dict(schema='R233_PROSPECTIVE_FAIR_CAPTURE_V1', adopted_unix=time.time(),
            baseline_cut_utc=coverage['observed_utc'], baseline_sha256=BASELINE_SHA,
            baseline_commit='23265a60f1944452d4ac0fd1c667100cc3afa406',
            prospective_definition='COMPLETE record index strictly after each bound source frontier; not a guessed wall-clock timestamp',
            sources=[{key: row[key] for key in ('life', 'journal_id', 'source_frontier')}
                for row in coverage['rows']],
            selection='Oldest available prospective COMPLETE per life; one per life per finite round; least recently attempted life first',
            optional_historical_enabled=False, metadata_never_removed=True,
            enrollment_is_not_testing=True, gpu_dispatch=False, deadline_unix=1789739970)
        enroll.put(policy_path, policy)
    policy = json.loads(policy_path.read_bytes())
    if policy['baseline_sha256'] != BASELINE_SHA or policy['optional_historical_enabled']:
        raise ValueError('fixed_prospective_policy')
    entries, source_cuts, targets = {}, [], {}
    for directory, registry in [('enrollment', 'REGISTRATION.json'), ('extra_enrollment', 'EXTRA_REGISTRATION.json')]:
        state_bytes = (WORKER / directory / 'private/STATE.json').read_bytes()
        state = json.loads(state_bytes)
        source_cuts.append(dict(ledger=directory, sha256=hashlib.sha256(state_bytes).hexdigest(),
            enrolled=len(state['entries'])))
        for key, entry in state['entries'].items():
            if key in entries:
                raise ValueError('duplicate_entry_across_ledgers')
            entries[key] = entry
        for target in json.loads((WORKER / 'private' / registry).read_bytes())['targets']:
            if target['label'] in targets or target['wrapper'] not in enroll.WRAPPERS:
                raise ValueError('unique_current_registered_source')
            targets[target['label']] = target
    if len(targets) != 16:
        raise ValueError('sixteen_pinned_roots')
    known_ages = {row['life']: set(row['coherent_captured_ages']) for row in coverage['rows']}
    captured = {key for key, entry in entries.items() if entry['sleep'] in known_ages[entry['life']]}
    attempts = {}
    directory = WORKER / 'capture_rounds'
    directory.mkdir(exist_ok=True)
    for path in sorted(directory.glob('*.json')):
        receipt = json.loads(path.read_bytes())
        for row in receipt['results']:
            attempts[row['life']] = max(attempts.get(row['life'], 0), receipt['finished_unix'])
            if row['status'] == 'CAPTURED':
                captured.add(row['key'])
    plan = capture_priority.plan_round(list(entries.values()), policy['sources'], captured, attempts)
    receipt = dict(schema='R233_PROSPECTIVE_CAPTURE_ROUND_V1', started_unix=time.time(),
        policy_sha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        ledger_cuts=source_cuts, plan=plan, execution_requested=args.execute, results=[],
        no_gpu_dispatch=True, no_learner_signals=True)
    source = Path(capture_retained.__file__).read_text()
    for entry in plan['selected'] if args.execute else []:
        if time.time() >= policy['deadline_unix']:
            break
        target = targets[entry['life']]
        result = dict(life=entry['life'], key=entry['key'], sleep=entry['sleep'],
            record_sha256=entry['record_sha256'], status='PENDING')
        output = '/localhome/local-rohing/orch_r233_retained_source_queue_20260918/' + entry['life']
        code = source + '\nprint(json.dumps(capture(' + repr(target) + ',' + repr(entry) + ',Path(' + repr(output) + '))))\n'
        try:
            process = subprocess.run(['bash', str(REPO / 'gpu' / target['wrapper']), 'python3 -B -'],
                input=code, text=True, capture_output=True, timeout=35)
            if process.returncode or len(process.stdout) > 65536:
                raise RuntimeError('source_capture_failed')
            result['source'] = json.loads(process.stdout)
            if result['source']['sleep_complete_sha256'] != entry['record_sha256']:
                raise ValueError('returned_source_join')
            result['status'] = 'CAPTURED'
        except Exception as error:
            result.update(status='UNAVAILABLE_PENDING_RETRY', error_type=type(error).__name__)
        receipt['results'].append(result)
    receipt['finished_unix'] = time.time()
    receipt['captured_this_round'] = sum(row['status'] == 'CAPTURED' for row in receipt['results'])
    if args.execute:
        enroll.put(directory / (str(time.time_ns()) + '.json'), receipt)
    enroll.put(WORKER / 'CAPTURE_ROUND_LATEST.json', receipt)
    print(json.dumps(dict(selected=plan['selected_count'], enrolled_retained=plan['enrolled_retained'],
        classes=plan['classes'], captured_this_round=receipt['captured_this_round'],
        results=[{key: row[key] for key in ('life', 'sleep', 'status')} for row in receipt['results']],
        no_gpu_dispatch=True)))


if __name__ == '__main__':
    main()
