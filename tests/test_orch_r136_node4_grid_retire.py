import ctypes
import json
import os
import select
import struct

import pytest

from gpu import orch_r136_node4_grid_retire as grid


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def boundary(tmp_path):
    root=tmp_path/'grid'
    carry=[{'split':'TRAIN','trace':'exact carry'}]
    put(root/'CARRY.json',carry)
    rows=[dict(cycle=10,kind='NATIVE',number=3,split='TRAIN',attached_readout=False,reserved_unix=10),
          dict(cycle=10,kind='PARENT',number=2,reserved_unix=11)]
    (root/'LEDGER.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    put(root/'calls/N00003.json',dict(cycle=10,number=3,status='COMPLETE',finished_unix=20))
    put(root/'parent_received/P0002.json',dict(observed_unix=19))
    put(root/'cycles/0010/TRAIN_COMPLETE.json',dict(optimizer_steps=0,outcomes=[{},{}],carry=carry,finished_unix=21))
    put(root/grid.ERA/'LOADED.json',dict(pid=123,optimizer_steps=0,
        no_adapter={'adapter_parameter_count':0,'trainable_parameter_count':0}))
    put(root/grid.ERA/'C0010_CONTINUED.json',dict(cycle=10,optimizer_steps=0,
        carry=grid.ref(root/'CARRY.json'),ledger=grid.ref(root/'LEDGER.jsonl'),observed_unix=22))
    return root


def test_complete_saved_grid_carry_and_ledger(boundary):
    result=grid.frontier(boundary,'C0010_CONTINUED.json',{'pid':123})
    assert result['cycle']==10 and result['optimizer']=='ABSENT_FROZEN_BASE'


@pytest.mark.parametrize('physical',[0,1,2,3,4,5,6,True,'7'])
def test_every_other_physical_rejected_before_process_access(physical):
    with pytest.raises(ValueError,match='physical7_only'):
        grid.check_chain({'physical':physical})


@pytest.mark.parametrize('filename,value',[('CARRY.json',[]),('LEDGER.jsonl',{})])
def test_changed_live_state_invalidates_saved_marker(boundary,filename,value):
    put(boundary/filename,value)
    with pytest.raises(ValueError,match='no_work_after'):
        grid.frontier(boundary,'C0010_CONTINUED.json',{'pid':123})


@pytest.mark.parametrize('patch',[{'status':'STARTED'},{'finished_unix':23},{'cycle':11}])
def test_grid_inflight_or_later_native_rejected(boundary,patch):
    path=boundary/'calls/N00003.json'
    put(path,dict(grid.read(path),**patch))
    with pytest.raises(ValueError,match='no_inflight'):
        grid.frontier(boundary,'C0010_CONTINUED.json',{'pid':123})


def test_grid_does_not_infer_base_from_name(boundary):
    path=boundary/grid.ERA/'LOADED.json'
    put(path,dict(grid.read(path),no_adapter={'adapter_parameter_count':12,'trainable_parameter_count':12}))
    with pytest.raises(ValueError,match='not_active_optimizer'):
        grid.frontier(boundary,'C0010_CONTINUED.json',{'pid':123})


def test_grid_missing_parent_disposition_blocks(boundary):
    (boundary/'parent_received/P0002.json').unlink()
    with pytest.raises(FileNotFoundError):
        grid.frontier(boundary,'C0010_CONTINUED.json',{'pid':123})


def test_grid_incomplete_two_episode_state_rejected(boundary):
    path=boundary/'cycles/0010/TRAIN_COMPLETE.json'
    put(path,dict(grid.read(path),outcomes=[{}]))
    with pytest.raises(ValueError,match='two_episode'):
        grid.frontier(boundary,'C0010_CONTINUED.json',{'pid':123})


@pytest.mark.parametrize('publication', ['hardlink', 'rename', 'direct'])
def test_boundary_watch_detects_actual_atomic_publications(tmp_path, publication):
    library = ctypes.CDLL(None, use_errno=True)
    descriptor = library.inotify_init1(os.O_CLOEXEC | os.O_NONBLOCK)
    assert descriptor >= 0
    try:
        assert library.inotify_add_watch(descriptor, os.fsencode(tmp_path), grid.BOUNDARY_EVENTS) >= 0
        target = tmp_path / 'C0010_CONTINUED.json'
        temporary = tmp_path / 'C0010_CONTINUED.json.123.tmp'
        if publication == 'direct':
            target.write_text('{}')
        else:
            temporary.write_text('{}')
            if publication == 'hardlink':
                os.link(temporary, target)
                temporary.unlink()
            else:
                os.replace(temporary, target)
        assert select.select([descriptor], [], [], 1)[0]
        payload = os.read(descriptor, 65536)
        assert grid.boundary_markers(payload) == ['C0010_CONTINUED.json']
    finally:
        os.close(descriptor)


def test_boundary_events_ignore_temporary_and_nonpublication_names():
    def event(name, mask):
        encoded = name.encode() + b'\0'
        return struct.pack('iIII', 1, mask, 0, len(encoded)) + encoded
    payload = event('C0010_CONTINUED.json.123.tmp', 0x100)
    payload += event('OTHER.json', 0x100)
    payload += event('C0011_CONTINUED.json', 0x200)
    payload += event('C0012_CONTINUED.json', 0x100)
    assert grid.boundary_markers(payload) == ['C0012_CONTINUED.json']


def test_old_watch_mask_misses_hardlink_publication(tmp_path):
    library = ctypes.CDLL(None, use_errno=True)
    descriptor = library.inotify_init1(os.O_CLOEXEC | os.O_NONBLOCK)
    assert descriptor >= 0
    try:
        assert library.inotify_add_watch(descriptor, os.fsencode(tmp_path), 0x8 | 0x80) >= 0
        temporary = tmp_path / 'C0010_CONTINUED.json.123.tmp'
        temporary.write_text('{}')
        os.link(temporary, tmp_path / 'C0010_CONTINUED.json')
        temporary.unlink()
        assert select.select([descriptor], [], [], 1)[0]
        assert grid.boundary_markers(os.read(descriptor, 65536)) == []
    finally:
        os.close(descriptor)


@pytest.mark.parametrize('seconds', [1, 1200, 3600])
def test_bounded_observation_can_cover_a_full_grid_cycle(seconds):
    grid.check_wait(seconds, {'hard_end_unix': 5000, 'lease_end_unix': 26600}, 100)


@pytest.mark.parametrize('seconds', [0, -1, 3601, True, 3.5, '3600'])
def test_observation_rejects_invalid_or_unbounded_windows(seconds):
    with pytest.raises(ValueError, match='bounded_existing_lease'):
        grid.check_wait(seconds, {'hard_end_unix': 5000, 'lease_end_unix': 26600}, 100)


@pytest.mark.parametrize('lease,now', [({'hard_end_unix': 4000, 'lease_end_unix': 25600}, 100),
                                      ({'hard_end_unix': 5000, 'lease_end_unix': 26599}, 100)])
def test_long_observation_preserves_existing_lease_margin(lease, now):
    with pytest.raises(ValueError, match='bounded_existing_lease'):
        grid.check_wait(3600, lease, now)
