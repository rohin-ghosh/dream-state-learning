from pathlib import Path

import pytest

from gpu import orch_r149_math_readmit as readmit


def fixture(tmp_path):
    service = tmp_path/'service'
    service.mkdir()
    values = {
        'GUARD_FAILURE.json': dict(native_started=False, error='fresh_strict_F2_admission_no_waiver'),
        'ADMISSION.json': dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:42']),
        'GUARD_STARTED.json': dict(pid=18274),
    }
    return service, values


def test_only_pre_native_drift_is_readmitted(tmp_path):
    service, values = fixture(tmp_path)
    readmit.validate_failure(service, lambda path: values[path.name], tmp_path/'proc')


@pytest.mark.parametrize('filename,key,value', [
    ('GUARD_FAILURE.json', 'native_started', True),
    ('GUARD_FAILURE.json', 'error', 'other'),
    ('ADMISSION.json', 'clear', True),
    ('ADMISSION.json', 'scanner_euid', 2524),
    ('ADMISSION.json', 'blocking_reasons', []),
    ('ADMISSION.json', 'blocking_reasons', ['target_device_open:42']),
])
def test_rejects_nonmatching_failure(tmp_path, filename, key, value):
    service, values = fixture(tmp_path)
    values[filename][key] = value
    with pytest.raises(ValueError):
        readmit.validate_failure(service, lambda path: values[path.name], tmp_path/'proc')


@pytest.mark.parametrize('filename', ['LAUNCH.json', 'LOADED.json', 'native.log'])
def test_never_replays_native_attempt(tmp_path, filename):
    service, values = fixture(tmp_path)
    (service/filename).touch()
    with pytest.raises(ValueError, match='native_attempt_not_replayable'):
        readmit.validate_failure(service, lambda path: values[path.name], tmp_path/'proc')


def test_live_or_reused_guard_pid_rejected(tmp_path):
    service, values = fixture(tmp_path)
    (tmp_path/'proc/18274').mkdir(parents=True)
    with pytest.raises(ValueError, match='prior_guard'):
        readmit.validate_failure(service, lambda path: values[path.name], tmp_path/'proc')


@pytest.mark.parametrize('name', sorted(readmit.GUARD_RECEIPTS))
def test_guard_receipts_go_to_new_attempt(name):
    service, attempt = Path('/service'), Path('/service/readmission1')
    observed = []
    writer = readmit.receipt_writer(lambda path, value: observed.append((path, value)), service, attempt)
    writer(service/name, {'new': True})
    assert observed == [(attempt/name, {'new': True})]


def test_other_receipts_stay_in_original_runtime():
    observed = []
    writer = readmit.receipt_writer(lambda path, value: observed.append(path), Path('/service'), Path('/attempt'))
    writer(Path('/service/LOADED.json'), {})
    assert observed == [Path('/service/LOADED.json')]
