"""Preserve failed P3 continuation and reconcile its exact saved auxiliary frontier."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

import p3_native_renew as recovery


OLD = recovery.ROOT / 'r233_lease_continuation'
TARGET = recovery.ROOT / 'r233_lease_continuation_retry1'


def learning_plan(previous):
    from r227_plan import proposed_plan
    proposed, unused = proposed_plan(previous, str(recovery.SOURCE))
    if previous.get('startup_context') is not None:
        proposed['startup_context'] = deepcopy(previous['startup_context'])
    return proposed


def reconcile_corrections(complete):
    from p3_auxiliary_cache import select_cache
    from p3_auxiliary_reader import metadata
    cache = recovery.ROOT / 'life/stream/correction_ledger.json'
    before = recovery.read(cache)
    candidates = []
    for path in reversed(recovery.records()):
        if int(path.stem) >= complete['index']:
            continue
        if metadata(path)['kind'] == 'R197_CORRECTION_CYCLE':
            candidates.append(recovery.read(path))
            break
    selected = select_cache(candidates, complete)
    recovery.write(recovery.CONTROL / 'CORRECTION_CACHE_RECOVERY.json', dict(before=before, after=selected,
        complete_index=complete['index'], complete_sha256=complete['sha256'],
        future_cycles_not_reused=True, old_journal_records_retained=True))
    temporary = cache.with_name('correction_ledger.r233_retry1.tmp')
    recovery.write(temporary, selected)
    temporary.replace(cache)
    recovery.write(recovery.CONTROL / 'CORRECTION_CACHE_RECONCILED.json', dict(
        cache_sha256=recovery.sha(cache), observed_unix=time.time(), native_absent=True))


def configure():
    recovery.OLD = OLD
    recovery.TARGET = TARGET
    recovery.SOURCE = TARGET / 'source'
    recovery.CONTROL = TARGET / 'control'
    recovery.PID = 598987
    recovery.TICKS = '32509102'


def stage():
    recovery.require(not Path('/proc/598987').exists(), 'failed_native_must_be_absent')
    guard = recovery.read(OLD / 'control/GUARD.json')
    recovery.require(recovery.sha(guard['plan_path']) == guard['plan_sha256'], 'preserve_failed_original_plan')
    for name, expected in guard['source_pins'].items():
        recovery.require(recovery.sha(OLD / 'source' / name) == expected, 'original_source_preserved')
    failure = recovery.read(OLD / 'control/EXIT.json')
    recovery.require(failure['exit_code'] == 1 and failure['no_retry'] is True, 'explicit_failed_attempt_preserved')
    tests = recovery.read(recovery.CONTROL / 'RECEIVING_TESTS.json')
    recovery.require(tests['passed'] is True and tests['GPU_science_run'] is False, 'receiving_CPU_tests_required')
    pins = {str(path.relative_to(recovery.SOURCE)): recovery.sha(path)
        for path in recovery.SOURCE.rglob('*.py')}
    recovery.write(recovery.CONTROL / 'STAGED.json', dict(status='SOURCE_READY_EXPLICIT_REPAIRED_RETRY',
        old_guard_sha256=recovery.sha(OLD / 'control/GUARD.json'), source_pins=pins,
        source_compiled=True, receiving_tests_sha256=recovery.sha(recovery.CONTROL / 'RECEIVING_TESTS.json'),
        old_exit=failure, old_native_stderr_sha256=recovery.sha(OLD / 'control/NATIVE.log'),
        native_signals=[], authorized_bound_unix=recovery.END_UNIX,
        reason='correction cache must match COMPLETE, never the discarded tail; R227 prospective policy'))
    print(json.dumps(dict(status='REPAIRED_RETRY_STAGED_NOT_DISPATCHED', source_pins=len(pins))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'continue'))
    arguments = parser.parse_args()
    configure()
    if arguments.action == 'stage':
        stage()
    else:
        recovery.continue_life(plan_transform=learning_plan, correction_recovery=reconcile_corrections)


if __name__ == '__main__':
    main()
