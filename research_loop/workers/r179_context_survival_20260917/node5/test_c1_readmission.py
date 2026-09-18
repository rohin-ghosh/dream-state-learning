import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SPEC = importlib.util.spec_from_file_location('c1_readmit_test', Path(__file__).with_name('c1_readmission.py'))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def inputs():
    return (dict(reason='original_privileged_clear_admission', retired=True, terminated=True),
            dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:1530599']),
            dict(cycle=39, record=dict(sha256=MODULE.BOUNDARY_SHA, kind='SLEEP_COMPLETE')), [], [])


def test_exact_preload_failure_is_eligible():
    MODULE.eligible(*inputs())


@pytest.mark.parametrize('name', ['LAUNCH.json', 'NATIVE.log', 'NATIVE_EXIT.json',
                                 'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json'])
def test_no_retry_after_native_or_service_dispatch(name):
    failure, admission, boundary, names, owners = inputs()
    with pytest.raises(ValueError, match='no_prior_native'):
        MODULE.eligible(failure, admission, boundary, [name], owners)


@pytest.mark.parametrize('field,value', [('cycle', 40), ('record', dict(sha256='changed', kind='SLEEP_COMPLETE'))])
def test_boundary_must_be_exact(field, value):
    failure, admission, boundary, names, owners = inputs()
    boundary[field] = value
    with pytest.raises(ValueError, match='same_sleep39'):
        MODULE.eligible(failure, admission, boundary, names, owners)


def test_live_owner_and_other_blocker_refuse():
    failure, admission, boundary, names, owners = inputs()
    with pytest.raises(ValueError, match='owner_still_present'):
        MODULE.eligible(failure, admission, boundary, names, ['actor'])
    admission['blocking_reasons'].append('foreign_device_owner')
    with pytest.raises(ValueError, match='exact_preserved'):
        MODULE.eligible(failure, admission, boundary, names, owners)


def test_strict_prefix_preserved_and_wrong_entrypoint_rejected():
    prefix = ['sudo', 'systemd-run', '--property=DevicePolicy=strict', '--property=DeviceAllow=/dev/nvidia0 rw']
    suffix = [MODULE.PYTHON, '-B', str(MODULE.ORIGINAL / 'rollout_operator.py'), 'contained',
              '--output', str(MODULE.ORIGINAL)]
    original = SimpleNamespace(strict_command=lambda *args: prefix + suffix)
    command = MODULE.strict_command(original, None, {}, {})
    assert command[:len(prefix)] == prefix
    assert command[len(prefix):] == [MODULE.PYTHON, '-B', str(MODULE.FRESH / 'c1_readmission.py'), 'contained']
    original.strict_command = lambda *args: prefix + ['wrong-entrypoint']
    with pytest.raises(ValueError, match='strict_payload_suffix'):
        MODULE.strict_command(original, None, {}, {})
