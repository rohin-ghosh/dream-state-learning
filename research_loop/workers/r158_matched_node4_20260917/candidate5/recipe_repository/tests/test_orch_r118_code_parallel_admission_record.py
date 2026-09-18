from copy import deepcopy

import pytest

from gpu import orch_r118_code_parallel_admission_record as admission


PLAN = dict(gpu_uuid='GPU-test', hard_deadline_unix=1000)
CLEAR = dict(clear=True, scanner_euid=0, gpu=dict(uuid='GPU-test'),
    device_minor=6, blocking_reasons=[])


def test_rejected_snapshot_saved_before_failure_no_retry_default(tmp_path):
    report = dict(CLEAR, clear=False, blocking_reasons=['open_device_pid:42'])
    calls = []
    def scan(root):
        calls.append(root)
        return report
    with pytest.raises(ValueError, match='recorded_rejection'):
        admission.acquire(tmp_path / 'service', tmp_path, PLAN, deadline=500, scan=scan, clock=lambda: 100)
    assert len(calls) == 1
    assert admission.io.read(tmp_path / 'service/ADMISSION_ATTEMPTS/SCAN_000.json') == report
    assert admission.io.read(tmp_path / 'service/ADMISSION_ATTEMPTS/DECISION_000.json')['accepted'] is False


@pytest.mark.parametrize('change', [dict(scanner_euid=1000), dict(gpu=dict(uuid='GPU-foreign')),
    dict(clear=False), dict(blocking_reasons=['reserved_cvd_pid:7'])])
def test_no_waiver_of_original_privileged_predicate(tmp_path, change):
    report = dict(CLEAR, **change)
    with pytest.raises(ValueError, match='recorded_rejection'):
        admission.acquire(tmp_path / 'service', tmp_path, PLAN, deadline=500,
            scan=lambda root: report, clock=lambda: 100)


def test_explicit_future_bounded_wait_requires_new_genuinely_clear_scan(tmp_path):
    denied = dict(CLEAR, clear=False, blocking_reasons=['unknown_process_visibility:7'])
    reports = iter([denied, deepcopy(CLEAR)])
    waits = []
    result = admission.acquire(tmp_path / 'service', tmp_path, PLAN, deadline=500,
        scan=lambda root: next(reports), attempts=2, pause=waits.append, clock=lambda: 100)
    assert result == CLEAR and waits == [5]
    assert admission.io.read(tmp_path / 'service/ADMISSION_ATTEMPTS/SCAN_000.json') == denied
    assert admission.io.read(tmp_path / 'service/ADMISSION_ATTEMPTS/SCAN_001.json') == CLEAR


def test_late_clear_never_admitted(tmp_path):
    times = iter([100, 100, 100, 501, 501, 501])
    with pytest.raises(ValueError, match='late_clear'):
        admission.acquire(tmp_path / 'service', tmp_path, PLAN, deadline=500,
            scan=lambda root: CLEAR, clock=lambda: next(times))


def test_existing_attempt_and_foreign_root_never_reused(tmp_path):
    service = tmp_path / 'service'
    admission.acquire(service, tmp_path, PLAN, deadline=500, scan=lambda root: CLEAR, clock=lambda: 100)
    with pytest.raises(FileExistsError):
        admission.acquire(service, tmp_path, PLAN, deadline=500, scan=lambda root: CLEAR, clock=lambda: 100)
    with pytest.raises(ValueError, match='owned_service'):
        admission.acquire(tmp_path.parent / 'foreign', tmp_path, PLAN, deadline=500,
            scan=lambda root: CLEAR, clock=lambda: 100)


def test_scanner_exception_preserved_no_retry(tmp_path):
    def scan(root):
        raise PermissionError('synthetic')
    with pytest.raises(PermissionError):
        admission.acquire(tmp_path / 'service', tmp_path, PLAN, deadline=500,
            scan=scan, attempts=3, clock=lambda: 100)
    assert admission.io.read(tmp_path / 'service/ADMISSION_ATTEMPTS/ERROR_000.json')['error_type'] == 'PermissionError'
