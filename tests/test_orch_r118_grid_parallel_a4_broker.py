from copy import deepcopy
from pathlib import Path

import pytest

from gpu import orch_r118_grid_parallel_a4_broker as broker


def documents():
    bounds = dict(parent_used=47, parent_cap=298, native_cap=1858,
                  hard_end_unix=1789491720, train_end_unix=1789491300)
    envelope = dict(status='RELEASED', root='/node/A4', bounds=bounds)
    release = dict(envelope, original_FAILED_preserved=True, calls_replayed=0, parent_claims_discarded=0)
    return envelope, release


def test_actual_counter_cutoff_no_replay():
    envelope, release = documents()
    cutoff = broker.validate_handoff(envelope, release, Path('/node/A4'))
    assert all(broker.historical(f'P{number:04d}.request.json', cutoff) for number in range(1, 48))
    assert not broker.historical('P0048.request.json', cutoff)
    assert broker.TERMINAL == 'R118_GRID_PARALLEL_TERMINAL.json'
    assert broker.prior.TERMINAL == 'R118_SHARED_REPAIR_TERMINAL.json'


@pytest.mark.parametrize('field,value', [('status','PLANNED'), ('calls_replayed',1),
    ('parent_claims_discarded',1), ('original_FAILED_preserved',False), ('root','/foreign')])
def test_no_planned_release_or_replay_waiver(field, value):
    envelope, release = documents()
    release[field] = value
    with pytest.raises(ValueError):
        broker.validate_handoff(envelope, release, Path('/node/A4'))


def test_no_quota_extension():
    envelope, release = documents()
    release['bounds'] = dict(release['bounds'], hard_end_unix=1789492800)
    with pytest.raises(ValueError):
        broker.validate_handoff(envelope, release, Path('/node/A4'))
