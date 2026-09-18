import copy
import json
from pathlib import Path
import signal
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refresh_node4 as refresh


def expected():
    return json.loads((refresh.PREVIOUS / 'RUNNING.json').read_text())['parent']


@pytest.mark.parametrize('pid', [716608, 601954, 447695, 448014, 508091, 508573, 1])
def test_other_parents_excluded(pid):
    identity = expected()
    identity['pid'] = pid
    with pytest.raises(ValueError, match='only_explicit_raw3'):
        refresh.verify(identity, identity)


@pytest.mark.parametrize('key,value', [('start_ticks', '0'), ('cwd', '/tmp'), ('uid', -1), ('argv', [])])
def test_pid_reuse_and_identity_changes(key, value):
    identity = expected()
    observed = copy.deepcopy(identity)
    observed[key] = value
    with pytest.raises(ValueError):
        refresh.verify(identity, observed)


def test_config_changes_only_fresh_predecessor_and_cursor():
    old = json.loads((refresh.PREVIOUS / 'CONFIG.json').read_text())
    ledger = dict(clock='response_count', reserved=12345, started_sha256='a' * 64)
    updated = refresh.successor_config(old, ledger)
    changes = {key for key in updated if updated[key] != old.get(key)}
    assert changes == {'predecessor_output', 'predecessor_started_sha256', 'start_after_response_count'}
    assert updated['hard_end_unix'] == old['hard_end_unix']
    assert updated['cadence_responses'] == old['cadence_responses']


def test_expired_wall_cannot_restart():
    config = json.loads((refresh.PREVIOUS / 'CONFIG.json').read_text())
    config['hard_end_unix'] = 0
    with pytest.raises(ValueError, match='existing_wall_only'):
        refresh.successor_config(config, {})


class FakeOperations:
    def __init__(self, children=False, race=False):
        self.signals = []
        self.children = children
        self.race = race
        self.closed = False

    def identity(self, pid):
        result = expected()
        result['state'] = 'T' if self.signals else 'S'
        return result

    def children_absent(self, pid):
        return not self.children

    def open(self, pid):
        assert pid == 601818
        return 123

    def signal(self, descriptor, number):
        assert descriptor == 123
        self.signals.append(number)

    def childless_stopped(self, pid):
        if self.race:
            raise ValueError('provider_or_publish_child_defer')

    def close(self, descriptor):
        self.closed = True


def test_children_mean_zero_signals():
    operations = FakeOperations(children=True)
    with pytest.raises(ValueError, match='child_present_no_signal'):
        with refresh.paused(expected(), operations):
            pytest.fail('must not enter')
    assert operations.signals == []


def test_child_race_resumes_without_termination():
    operations = FakeOperations(race=True)
    with pytest.raises(ValueError, match='provider_or_publish_child_defer'):
        with refresh.paused(expected(), operations):
            pytest.fail('must not enter')
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
    assert operations.closed


def test_ledger_failure_resumes_without_termination():
    operations = FakeOperations()
    with pytest.raises(ValueError, match='unsettled'):
        with refresh.paused(expected(), operations):
            raise ValueError('unsettled')
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
    assert operations.closed


def test_exact_frozen_sources_and_model():
    source = Path(expected()['cwd'])
    assert refresh.custody.ref(source / 'gpu/orch_r133_programme_parent.py')['sha256'] == refresh.PARENT_SHA
    assert refresh.custody.ref(source / 'gpu/orch_r136_node4_parent.py')['sha256'] == refresh.ADAPTER_SHA
    assert "STRONG = 'openai/openai/gpt-6-astra'" in (source / 'gpu/orch_route_parent_campaign_providers.py').read_text()
