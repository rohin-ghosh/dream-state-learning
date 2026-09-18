"""Bounded read-only phase observer; no provider calls, parent writes, or signals."""

import hashlib
import json
from pathlib import Path
import time

from gpu import orch_r133_programme_parent as parent
from research_loop.workers.r167_parent_policy_candidates_20260917.R154_ATTENTION_V2 import OBSERVE


DEADLINE = 1789634854
ROOT = OBSERVE.ROOT/'MONITOR'


def main():
    ROOT.mkdir(mode=0o700)
    parent.write(ROOT/'STARTED.json',dict(pid=__import__('os').getpid(),started_unix=time.time(),
        deadline_unix=DEADLINE,interval_seconds=30,tail_interval_seconds=120,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),no_parent_signals=True,
        no_publication=True,no_provider_calls=True))
    last_tail=0
    status='MONITOR_BOUND_COMPLETE_NO_DELIVERY_INFERRED'
    latest=None
    for index in range(128):
        if time.time()>=DEADLINE or (ROOT/'STOP_OBSERVER').exists():
            break
        report=dict(observed_unix=time.time())
        try:
            report['parents']=OBSERVE.phases()
            if time.time()-last_tail>=120:
                try:
                    report['tail_counts']=OBSERVE.tail_counts()
                except Exception as error:
                    report['tail_error']=dict(type=type(error).__name__,message=str(error))
                last_tail=time.time()
        except Exception as error:
            report['error']=dict(type=type(error).__name__,message=str(error))
        path=ROOT/f'OBSERVATION_{index:04d}.json'
        parent.write(path,report)
        latest=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        parents=report.get('parents',[])
        rendered=[entry['branch'] for entry in parents if any(attempt.get('rendered') for attempt in entry['fresh_attempts'])]
        print(json.dumps(dict(observed_unix=report['observed_unix'],receipt=latest,rendered=rendered,
            phases={entry['branch']:[dict(attempt=attempt['attempt'],marker=attempt.get('marker_present'),
                status=attempt.get('status'),rendered=bool(attempt.get('rendered'))) for attempt in entry['fresh_attempts']]
                    for entry in parents})),flush=True)
        if len(rendered)==5:
            status='ALL_FIVE_HAVE_NEW_RENDERED_PARENT_TURN'
            break
        time.sleep(max(0,min(30,DEADLINE-time.time())))
    parent.write(ROOT/'TERMINAL.json',dict(status=status,finished_unix=time.time(),latest=latest,
        no_parent_state_change=True,parents_continue_under_original_walls=True))


if __name__ == '__main__':
    main()
