import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


HERE = Path(__file__).resolve().parent


@pytest.fixture
def freeze():
    specification = importlib.util.spec_from_file_location('freeze_under_test', HERE / 'BOUNDARY_FREEZE.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.mark.parametrize('boundary,started,moved,expected', [
    (None, False, False, False),
    ({'cycle': 43}, False, False, False),
    ({'cycle': 43}, True, True, False),
    ({'cycle': 43}, True, False, True),
])
def test_opportunity_needs_current_boundary_revision_and_timer(freeze, boundary, started, moved, expected):
    reads = []
    observations = []

    def current(root):
        reads.append(root)
        return None if moved and len(reads) > 1 else boundary

    def readout(*arguments):
        observations.append(arguments)
        return started

    original = SimpleNamespace(saved=SimpleNamespace(sleep_boundary=current, readout_started=readout))
    result = freeze.opportunity(original, dict(root='/fixture/life', readout_revision=2),
                                dict(actor=dict(pid=10), timer=dict(pid=11)))
    assert (result is not None) is expected
    if boundary is not None:
        assert observations == [('/fixture/life', 43, 2, 11)]


def test_references_hash_file_bytes_not_internal_digest(freeze, tmp_path):
    path = tmp_path / 'record.json'
    path.write_bytes(b'{"sha256":"internal-record-digest"}\n')
    assert freeze.reference(path)['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('seconds', [False, 0, 5401])
def test_unbounded_watch_refuses_before_loading(freeze, seconds):
    with pytest.raises(ValueError, match='bounded_observation_seconds'):
        freeze.watch(seconds)


@pytest.mark.parametrize('cycle', [True, 0, -1])
def test_non_cycle_refuses_before_reading(freeze, cycle):
    with pytest.raises(ValueError, match='observed_positive_cycle'):
        freeze.freeze({}, {}, cycle)


def test_other_life_refuses_before_reading(freeze):
    with pytest.raises(ValueError, match='one_life_record'):
        freeze.freeze(dict(path='/other/stream/records/00000000000000000001.json'), {}, 43)


def test_other_cycle_commit_refuses_before_reading(freeze):
    with pytest.raises(ValueError, match='same_cycle_commit'):
        freeze.freeze(dict(path=str(freeze.LIFE / 'stream/records/00000000000000000001.json')),
                      dict(path=str(freeze.LIFE / 'checkpoints/sleep_000042/COMMIT.json')), 43)
