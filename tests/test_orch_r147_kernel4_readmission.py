import importlib.util
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / 'research_loop/workers/r147_kernel4_recovery_20260916t1836z/READMIT_KERNEL4.py'
SPEC = importlib.util.spec_from_file_location('kernel4_readmission', PATH)
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


def denial():
    return dict(clear=False, scanner_euid=0,
                blocking_reasons=operator.CASES['a40r']['reasons'][:])


def test_exact_preload_denial_only():
    operator.denied_preload('a40r', denial(), False)


@pytest.mark.parametrize('field,value', [
    ('clear', True), ('scanner_euid', 2524),
    ('blocking_reasons', ['open_device_pid:123']),
    ('blocking_reasons', []),
])
def test_other_denials_rejected(field, value):
    report = denial()
    report[field] = value
    with pytest.raises(ValueError):
        operator.denied_preload('a40r', report, False)


def test_possible_native_launch_never_retried():
    with pytest.raises(ValueError, match='never_retry_partially_launched_native'):
        operator.denied_preload('a40r', denial(), True)


def test_only_receipt_path_and_unit_change():
    config = dict(attempt_dir='/old', resume=True, plan_sha256='same',
                  source_pins={'native.py': 'same'},
                  device_containment=dict(unit='old', minor=7, uid=2524, gid=2524))
    result = operator.derived_config(config, Path('/new'))
    assert result['attempt_dir'] == '/new'
    assert result['device_containment']['unit'] != 'old'
    result['attempt_dir'] = config['attempt_dir']
    result['device_containment']['unit'] = 'old'
    assert result == config
    assert config['attempt_dir'] == '/old'


def test_other_node_not_authorized():
    assert set(operator.CASES) == {'a40r'}


def test_wrong_hold_rejected(tmp_path):
    import json
    import os
    (tmp_path / 'NODE_UNRESOLVED.json').write_text(json.dumps(dict(stage='/wrong')))
    descriptor = os.open(tmp_path / 'lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        with pytest.raises(ValueError, match='exact_failed_attempt_hold'):
            operator.acquire_after_observer(descriptor, tmp_path, tmp_path / 'lane4')
    finally:
        os.close(descriptor)
