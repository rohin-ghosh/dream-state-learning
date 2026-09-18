"""CPU-only fixtures; no live process, provider, or remote operations."""

import copy
import importlib.util
import json
from pathlib import Path
import signal

import pytest


SPEC = importlib.util.spec_from_file_location('legacy_takeover', Path(__file__).with_name('legacy_takeover.py'))
legacy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(legacy)


def binding():
    return dict(branch='NODE3_4_CREATIVE_FREE_SPARSE2', original_config=dict(path='/config'),
        old_output='/old', parent=dict(pid=101, start_ticks='5', cwd='/source', uid=1000,
            argv=['python3', '-m', 'gpu.orch_r133_programme_parent', '--config', '/config', '--output', '/old']))


class FakeOperations:
    def __init__(self):
        self.observed = dict(binding()['parent'], state='S')
        self.signals = []
        self.busy = False
        self.closed = False

    def identity(self, pid):
        return self.observed.copy()

    def open(self, pid):
        return 42

    def close(self, descriptor):
        assert descriptor == 42
        self.closed = True

    def signal(self, descriptor, sig):
        assert descriptor == 42
        self.signals.append(sig)
        self.observed['state'] = 'T' if sig == signal.SIGSTOP else 'S'

    def childless_stopped(self, pid):
        assert self.observed['state'] == 'T'
        if self.busy:
            raise ValueError('provider_or_publish_child_defer')


@pytest.mark.parametrize('failure', ['busy', 'ledger', 'pin', 'expiry'])
def test_every_pretermination_failure_continues_exact_parent(failure):
    operations = FakeOperations()
    operations.busy = failure == 'busy'
    with pytest.raises(ValueError):
        with legacy.quiesce(binding(), operations):
            raise ValueError(failure)
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
    assert operations.closed


@pytest.mark.parametrize('field,value', [('pid', 102), ('start_ticks', '6'), ('cwd', '/other'),
    ('uid', 0), ('state', 'Z'), ('state', 'T')])
def test_identity_or_unowned_stop_never_signalled(field, value):
    operations = FakeOperations()
    operations.observed[field] = value
    with pytest.raises(ValueError):
        with legacy.quiesce(binding(), operations):
            pytest.fail('not reached')
    assert operations.signals == []


@pytest.mark.parametrize('branch', ['C1', 'R158_MATCHED', 'NODE3_6_SUPPORT_NONE_SPARSE5', 'OTHER'])
def test_excluded_branch_not_signalled(branch):
    expected = binding()
    expected['branch'] = branch
    operations = FakeOperations()
    with pytest.raises(ValueError):
        with legacy.quiesce(expected, operations):
            pytest.fail('not reached')
    assert not operations.signals


def test_native_module_cannot_be_a_parent():
    expected = binding()
    expected['parent']['argv'][2] = 'gpu.orch_r125_continual_guard'
    with pytest.raises(ValueError, match='programme_parent_only'):
        legacy.verify_identity(expected, dict(expected['parent'], state='S'))


def fixture(tmp_path, status='SILENT'):
    config = dict(branch='NODE3_4_CREATIVE_FREE_SPARSE2', programme='creative_writing', root='/life',
        hard_end_unix=9999999999, principles_path='/oldprinciples', principles_sha256='old')
    root = tmp_path / 'old'
    directory = root / 'parent_000000'
    directory.mkdir(parents=True)
    legacy.write(root / 'STARTED.json', dict(branch=config['branch'], programme=config['programme']))
    source = dict(head_sha256='a'*64, response_count=20, request_count=21)
    legacy.write(directory / 'SOURCE.json', source)
    result = dict(branch=config['branch'], programme=config['programme'], source_head_sha256='a'*64,
        source_response_count=20, schedule_count=20, started_unix=1, finished_unix=2, status=status)
    if status == 'PUBLISHED':
        result['inbox_publication'] = dict(id='abc', path='/life/stream/inbox/abc.json', sha256='b'*64)
    legacy.write(directory / 'RESULT.json', result)
    legacy.write(directory / 'DISPATCH_INTENT.json', dict(source_sha256=legacy.ref(directory / 'SOURCE.json')['sha256'],
        schedule_count=20))
    return config, root, directory


def test_preserves_reserved_cursor_and_pending_ids(tmp_path):
    config, root, directory = fixture(tmp_path, 'PUBLISHED')
    before = {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}
    previous = legacy.ledger(root, config)
    assert previous['reserved'] == 20 and previous['pending_inbox_ids'] == ['abc']
    candidate = dict(config, principles_path='/newprinciples', principles_sha256='new')
    new = legacy.successor_config(config, candidate, previous, str(root))
    assert new['start_after_response_count'] == 20
    assert new['predecessor_started_sha256'] == legacy.ref(root / 'STARTED.json')['sha256']
    assert {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()} == before


@pytest.mark.parametrize('damage', ['MISSING', 'missing_result', 'source_changed', 'wrong_root', 'intent_changed', 'symlink'])
def test_uncertain_attempts_fail_closed(tmp_path, damage):
    config, root, directory = fixture(tmp_path, 'PUBLISHED')
    path = directory / 'RESULT.json'
    if damage == 'MISSING':
        document = json.loads(path.read_text())
        document['status'] = 'MISSING'
        path.write_text(json.dumps(document))
    elif damage == 'missing_result':
        path.unlink()
    elif damage == 'source_changed':
        (directory / 'SOURCE.json').write_text('{}')
    elif damage == 'wrong_root':
        config['root'] = '/other'
    elif damage == 'intent_changed':
        (directory / 'DISPATCH_INTENT.json').write_text('{"source_sha256":"wrong"}')
    else:
        (directory / 'linked').symlink_to(path)
    with pytest.raises((ValueError, KeyError, OSError)):
        legacy.ledger(root, config)


@pytest.mark.parametrize('field', ['hard_end_unix', 'cadence_responses', 'root', 'source_root', 'programme', 'schedule_on'])
def test_recipe_drift_rejected(tmp_path, field):
    config, root, directory = fixture(tmp_path)
    previous = legacy.ledger(root, config)
    candidate = dict(config, principles_path='/new', principles_sha256='new')
    candidate[field] = 'changed'
    with pytest.raises(ValueError, match='principles_only'):
        legacy.successor_config(config, candidate, previous, str(root))


@pytest.mark.parametrize('now', [9, 20, 21])
def test_exact_GO_window(now):
    go = dict(approved_by='Main', action='R167_EXACT_PARENT_ONLY_HANDOFF', not_before_unix=10, expires_unix=20)
    with pytest.raises(ValueError):
        legacy.gate_window(go, now)
    legacy.gate_window(go, 19)


def test_wrapper_equivalence_rejects_policy_change():
    original = 'def prompt(): return 1\ndef serve(): return 2\n'
    wrapper = 'def prompt(): return 1\ndef serve(): return 3\n'
    assert legacy.equivalent(original, wrapper)['equal_functions'] == ['prompt']
    with pytest.raises(ValueError):
        legacy.equivalent(original, wrapper.replace('return 1', 'return 4'))


def test_actual_protected_functions_equal_original():
    source = legacy.REPOSITORY / 'gpu/orch_r133_programme_parent.py'
    assert legacy.ref(source)['sha256'] == legacy.SOURCE_HASHES[1]
    for lane in ('RUN1', 'PILOT'):
        wrapper = legacy.REPOSITORY / 'research_loop/workers/r157_protected_parent_keepalive_20260917' / lane / (lane + '_PARENT.py')
        assert legacy.equivalent(legacy.read(source), legacy.read(wrapper))['differing_functions'] == ['serve']


def test_actual_sources_have_supported_predecessor_contract():
    paths = [Path('/tmp/r133-node3-creative-build/parent_source/gpu/orch_r133_programme_parent.py'),
        legacy.REPOSITORY / 'gpu/orch_r133_programme_parent.py']
    for path in paths:
        assert legacy.ref(path)['sha256'] in legacy.SOURCE_HASHES
        text = legacy.read(path).decode()
        assert 'def resume_cursor(' in text and 'predecessor_started_sha256' in text


def test_missing_before_strong_return_preserves_status_cursor_and_bytes(tmp_path):
    config, root, directory = fixture(tmp_path, 'MISSING')
    path = directory / 'RESULT.json'
    result = json.loads(path.read_text())
    result.update(error_code='parent_call_or_delivery_failed', error_type='HTTPError')
    path.write_text(json.dumps(result))
    before = path.read_bytes()
    previous = legacy.ledger(root, config, legacy.SOURCE_HASHES[0])
    assert previous['statuses'] == {'MISSING': 1} and previous['reserved'] == 20
    assert previous['classifications'] == {'SETTLED_PREPUBLICATION_FAILURE_STATUS_UNCHANGED': 1}
    assert path.read_bytes() == before and not previous['pending_inbox_ids']


@pytest.mark.parametrize('field,value', [('sent_unix', 1.5), ('sent_unix', None),
    ('inbox_publication', {}), ('response', {}), ('response', None),
    ('error_code', 'unknown'), ('error_type', ''), ('status', 'UNKNOWN')])
def test_missing_with_possible_publication_or_unknown_controlflow_rejected(field, value):
    result = dict(status='MISSING', error_code='parent_call_or_delivery_failed', error_type='HTTPError')
    result[field] = value
    with pytest.raises(ValueError):
        legacy.classify_result(result, legacy.SOURCE_HASHES[0])


def test_prepublication_proof_requires_exact_inspected_source():
    result = dict(status='MISSING', error_code='parent_call_or_delivery_failed', error_type='HTTPError')
    with pytest.raises(ValueError, match='inspected_controlflow'):
        legacy.classify_result(result, 'other_source')


def test_read_only_quiet_wait_still_requires_stopped_full_check(monkeypatch):
    expected = binding()
    expected['quiet_window_wait_seconds'] = 30
    operations = FakeOperations()
    observations = iter([False, False, True])
    operations.children_absent = lambda pid: next(observations)
    operations.busy = True
    monkeypatch.setattr(legacy.time, 'sleep', lambda seconds: None)
    with pytest.raises(ValueError, match='provider_or_publish_child_defer'):
        with legacy.quiesce(expected, operations):
            pytest.fail('busy after quiet read')
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]


def test_quiet_wait_timeout_has_no_signals(monkeypatch):
    expected = binding()
    expected['quiet_window_wait_seconds'] = 30
    operations = FakeOperations()
    operations.children_absent = lambda pid: False
    clock = iter([0, 31])
    monkeypatch.setattr(legacy.time, 'monotonic', lambda: next(clock))
    with pytest.raises(ValueError, match='quiet_window_not_observed'):
        with legacy.quiesce(expected, operations):
            pytest.fail('never quiet')
    assert operations.signals == []


def test_quiet_wait_cannot_expand_duration():
    expected = binding()
    expected['quiet_window_wait_seconds'] = 300
    operations = FakeOperations()
    with pytest.raises(ValueError, match='bounded_quiet_wait'):
        with legacy.quiesce(expected, operations):
            pytest.fail('unbounded wait')
    assert operations.signals == []
