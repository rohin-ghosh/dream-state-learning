"""Complete an interrupted CPU custody commit after exact old PID disappearance."""

from pathlib import Path
import time

from gpu import orch_r118_code_final_failed_release as final


def complete(root, *, clock=time.time, proc=Path('/proc')):
    root = Path(root)
    final.require(clock() < final.TRANSFER_END, 'completion_before1650')
    final.functions()['validate_plan'](root)
    record = final.facts(root)
    intent = final.io.read(root / 'TRANSFER_INTENT.json')
    armed = final.handoff.checked(intent['replacement'])
    final.require(intent['old_timer'] == record['old_timer']
        and armed['plan'] == final.handoff.ref(root / 'PLAN.json')
        and armed['facts'] == final.handoff.ref(root / 'FAILED_RELEASE_FACTS.json'),
        'same_interrupted_transaction')
    final.require(final.handoff.alive(armed['identity']), 'replacement_still_alive')
    final.require(not (proc / str(record['old_timer']['pid'])).exists(),
        'old_pid_fully_absent_not_identity_drift')
    final.require(not (root / 'TRANSFER_COMMITTED.json').exists(), 'commit_not_repeated')
    final.io.write(root / 'TRANSFER_COMMITTED.json', dict(plan=armed['plan'], facts=armed['facts'],
        stopped=dict(identity=record['old_timer'], verified_proc_absent_unix=clock(),
            completion_source=final.handoff.ref(__file__), additional_signals=0),
        observed_unix=clock(), native_cap_added=0, interrupted_commit_completed=True))
