import json

import pytest

from gpu import orch_r111_grid_release as release


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def finished(tmp_path):
    path=tmp_path/'episode/cycle01/held/COMPLETE.json'
    write(path, dict(status='COMPLETE',held_parent_free=True,finished_unix=10))
    write(path.parent.parent/'train/COMPLETE.json',dict(status='COMPLETE',held_parent_free=False))
    rows=[dict(kind='NATIVE',number=1,reserved_unix=1),dict(kind='PARENT',number=1,reserved_unix=2)]
    (tmp_path/'LEDGER.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    write(tmp_path/'calls/N00001.json',dict(status='COMPLETE',finished_unix=3))
    write(tmp_path/'parent_queue/P0001.response.json',dict(status='COMPLETE'))
    return tmp_path,path


def test_complete_cycle_preserves_charges(finished):
    root,path=finished
    value=release.boundary(root,path)
    assert value['charged_native']==value['charged_parent']==1
    assert value['no_pending_calls'] and not value['outcome_selection'] and not value['next_cycle_charged']


def test_next_reserved_call_blocks_even_if_not_written(finished):
    root,path=finished
    with (root/'LEDGER.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='NATIVE',number=2,reserved_unix=11))+'\n')
    assert release.boundary(root,path) is None


@pytest.mark.parametrize('status',['STARTED','FAILED'])
def test_pending_or_failed_call_never_selected_for_handoff(finished,status):
    root,path=finished
    write(root/'calls/N00001.json',dict(status=status,finished_unix=3))
    assert release.boundary(root,path) is None


def test_pending_parent_blocks(finished):
    root,path=finished
    (root/'parent_queue/P0001.response.json').unlink()
    assert release.boundary(root,path) is None


def test_train_only_not_a_full_cycle(finished):
    root,path=finished
    with pytest.raises(ValueError,match='full_cycle_only'):
        release.boundary(root,path.parent.parent/'train/COMPLETE.json')


def test_game_outcomes_do_not_select_boundary(finished):
    root,path=finished
    for success in (False,True):
        value=json.loads(path.read_text());value['success']=success;write(path,value)
        assert release.boundary(root,path)['no_pending_calls']
