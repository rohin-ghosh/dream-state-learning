"""Read-only, bounded observation of C5's existing pending parent publication."""

import hashlib
import json
from pathlib import Path
import time

from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as files
from gpu import orch_r168_manual_parent_turn as manual


STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
OLD = ROOT/'research_loop/workers/r167_parent_policy_candidates_20260917/R154_ATTENTION_V2/ROLLOUT/C5'
OUTPUT = STAGE/'C5_RECOVERED_PARENT_HANDOFF'
DEADLINE = 1789636920


def reference(path):
    return dict(path=str(path), sha256=files.sha(path))


def observe():
    started = json.loads(files.read_file(OLD/'STARTED.json'))
    current = files.identity(started['successor']['pid'])
    assert current['start_ticks'] == started['successor']['start_ticks']
    assert current['argv'] == started['command']
    assert current['state'] not in ('T', 't', 'Z', 'X')
    attempt = OLD/'parent/parent_000000000087'
    result = json.loads(files.read_file(attempt/'RESULT.json'))
    assert result['status'] == 'PUBLISHED'
    assert result['publication']['id'] == '9319497bcd0e47bb877ede90c133127b'
    report = dict(observed_unix=time.time(), parent=current,
        status='DEFERRED_PENDING_RENDER_ORIGINAL_PARENT_LIVE',
        result=reference(attempt/'RESULT.json'), publication=result['publication'],
        migration_started=(STAGE/'ROLLOUT/C5/STARTED.json').exists(),
        no_signals=True, no_publications=True, no_native_changes=True)
    if (attempt/'DELIVERED.json').exists():
        delivered = json.loads(files.read_file(attempt/'DELIVERED.json'))
        assert delivered['status'] == 'RENDERED'
        assert delivered['publication'] == result['publication']
        assert delivered['result_sha256'] == files.sha(attempt/'RESULT.json')
        assert delivered['rendered']['inbox_sha256'] == result['publication']['sha256']
        assert delivered['rendered']['speaker'] == 'Astra'
        assert delivered['rendered']['text_sha256'] == hashlib.sha256(result['message'].encode()).hexdigest()
        report['delivered'] = dict(reference=reference(attempt/'DELIVERED.json'), receipt=delivered)
        try:
            manual.settled_and_rendered(OLD/'parent')
            report['status'] = 'RENDERED_REQUIRES_FRESH_CUSTODY_PREFLIGHT_NO_AUTOMATIC_RETRY'
        except Exception as error:
            report['status'] = 'RENDERED_OTHER_ATTEMPTS_NOT_SETTLED'
            report['settled_error'] = dict(type=type(error).__name__, message=str(error)[:1000])
    return report


def main():
    for poll in range(45):
        if time.time() >= DEADLINE:
            break
        try:
            report = observe()
        except Exception as error:
            report = dict(observed_unix=time.time(), status='OBSERVER_STOPPED_NO_MUTATION',
                error_type=type(error).__name__, error=str(error)[:1000])
        community.write(OUTPUT/('PENDING_OBSERVATION_'+str(time.time_ns())+'.json'), report)
        print(json.dumps(report), flush=True)
        if report['status'] != 'DEFERRED_PENDING_RENDER_ORIGINAL_PARENT_LIVE':
            break
        time.sleep(min(30, max(0, DEADLINE-time.time())))
    community.write(OUTPUT/'PENDING_OBSERVER_TERMINAL.json',
        dict(observed_unix=time.time(), deadline=DEADLINE, no_mutations=True))


if __name__ == '__main__':
    main()
