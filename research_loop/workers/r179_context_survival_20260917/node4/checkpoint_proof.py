"""Read-only CPU proof of a latest committed checkpoint, never a cutover choice."""

import argparse
import json
from pathlib import Path
import sys
import time


def prove(bundle, physical):
    sys.path.insert(0, str(bundle))
    import node4_rollout as operator
    helpers = operator.helper_module(bundle)
    config_path, config, plan, original, pair = operator.selected(physical, helpers)
    deadline = time.monotonic() + 120
    saved = None
    for index, path in enumerate(reversed(helpers.records(plan['root']))):
        operator.require(index < 500 and time.monotonic() < deadline, 'bounded_latest_committed_boundary_lookup')
        record = helpers.read(path)
        if record['kind'] != 'SLEEP_COMPLETE':
            continue
        operator.require(record['sha256'] == helpers.digest({key: value for key, value in record.items() if key != 'sha256'}),
                         'complete_record_integrity')
        document = record['document']
        envelope = document['resume_state']
        state = envelope['state']
        operator.require(document['status'] == 'COMPLETE' and envelope['sha256'] == helpers.digest(state)
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows']), 'complete_saved_boundary')
        saved = dict(path=str(path), record_sha256=record['sha256'], state_sha256=envelope['sha256'],
            state=state, cycle=document['cycle'])
        break
    operator.require(saved is not None, 'latest_committed_sleep_exists')
    evidence = operator.saved_evidence(plan, saved, original, helpers)
    operator.require(all(helpers.identity(process['pid']) == process for process in pair.values()), 'original_lives_unchanged')
    return dict(status='LATEST_COMMITTED_STATE_CPU_VERIFIED_NOT_CUTOVER', physical=physical, evidence=evidence,
        operator_sha256=helpers.sha(bundle / 'node4_rollout.py'), proof_script_sha256=helpers.sha(Path(__file__)),
        source_sha256=helpers.sha(Path(plan['source_root']) / operator.NATIVE),
        current_saved_boundary_required_again=True, signals_sent=0, journal_writes=0, model_calls=0,
        sealed_output_reads=0, observed_unix=time.time())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--physical', type=int, choices=(0, 1, 3, 4), required=True)
    args = parser.parse_args()
    print(json.dumps(prove(args.bundle, args.physical), sort_keys=True))
