"""Fresh admission after an evidence-preserved, pre-native F2 scan rejection."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


RUNNER = Path('/localhome/local-rohing/orch_r149_f2_recovery_source_20260916t1920z/orch_r149_math_resume_candidate2.py')
RUNNER_SHA = 'eaa0591db2bfdd3957b602549ddb44c30173cf047d3f5cf703690423e1b51692'
GUARD_RECEIPTS = {'GUARD_STARTED.json', 'ADMISSION.json', 'LAUNCH.json', 'GUARD_TERMINAL.json', 'GUARD_FAILURE.json'}


def validate_failure(service, reader, proc=Path('/proc')):
    failure = reader(service/'GUARD_FAILURE.json')
    if failure['native_started'] is not False or failure['error'] != 'fresh_strict_F2_admission_no_waiver':
        raise ValueError('only_failed_pre_native_admission')
    report = reader(service/'ADMISSION.json')
    if report['clear'] is not False or report['scanner_euid'] != 0 or not report['blocking_reasons']:
        raise ValueError('original_privileged_denial_required')
    if not all(reason.startswith('process_identity_drift:') for reason in report['blocking_reasons']):
        raise ValueError('other_admission_failure_not_in_scope')
    started = reader(service/'GUARD_STARTED.json')
    if (proc/str(started['pid'])).exists():
        raise ValueError('prior_guard_still_present_or_PID_reused')
    if any((service/name).exists() for name in ('LAUNCH.json', 'LOADED.json', 'native.log')):
        raise ValueError('native_attempt_not_replayable')


def receipt_writer(original, service, attempt):
    def emit(path, value):
        path = Path(path)
        if path.parent == service and path.name in GUARD_RECEIPTS:
            path = attempt/path.name
        return original(path, value)
    return emit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if hashlib.sha256(RUNNER.read_bytes()).hexdigest() != RUNNER_SHA:
        raise ValueError('exact_tested_native_runner')
    spec = importlib.util.spec_from_file_location('r149_pinned_native', RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    validate_failure(runner.SERVICE, runner.read)
    runner.require(not (runner.ROOT/'cycle000097').exists(), 'no_new_cycle_before_readmission')
    attempt = runner.SERVICE/'readmission1'
    authorization = runner.read(runner.SERVICE/'READMIT_GO.json')
    runner.require(authorization['authorized'] is True and authorization['source_sha256'] == runner.sha(__file__)
                   and authorization['tests_passed'] is True and bool(authorization['publication']),
                   'tested_bound_readmission_publication')
    attempt.mkdir(exist_ok=False)
    preserved = {str(runner.SERVICE/name): runner.sha(runner.SERVICE/name) for name in
                 ('GUARD_STARTED.json', 'ADMISSION.json', 'GUARD_FAILURE.json', 'GUARD.log')}
    runner.write(attempt/'ORIGINAL_FAILURE.json', dict(preserved=preserved, source=runner.ref(__file__),
                                                      runner=runner.ref(RUNNER), authorization=authorization))
    original = runner.write
    runner.write = receipt_writer(original, runner.SERVICE, attempt)
    runner.guard()


if __name__ == '__main__':
    main()
