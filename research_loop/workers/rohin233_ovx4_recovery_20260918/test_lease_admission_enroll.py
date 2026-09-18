from copy import deepcopy
import datetime
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from research_loop.workers.rohin233_kept_age_probe_20260918 import enroll
from research_loop.workers.rohin233_ovx4_recovery_20260918 import lease_admission_enroll as subject
from research_loop.workers.rohin233_ovx4_recovery_20260918 import renew_enrollment_admission as handoff


@pytest.mark.parametrize('wrapper,alias,day', [
    ('ovx_ssh.sh','node2',20), ('ovx3_ssh.sh','node5',20), ('ovx2_ssh.sh','node3',24),
    ('a40r_ssh.sh','node4',25), ('ovx4_ssh.sh','ovx4',30)])
def test_exact_source_cutoffs(wrapper, alias, day):
    decision = subject.admission(dict(wrapper=wrapper),0)
    assert decision['source_host_alias'] == alias
    expected = datetime.datetime(2026,9,day,18,tzinfo=datetime.timezone.utc)
    assert decision['source_cutoff_utc'] == expected.isoformat()
    assert decision['effective_cutoff_unix'] == min(expected.timestamp(),subject.SERVICE_END)


@pytest.mark.parametrize('offset', [-35, -1, 0, 1])
def test_no_ssh_at_or_after_latest_safe_start(offset):
    target = dict(label='synthetic',wrapper='ovx_ssh.sh')
    cutoff = subject.admission(target,0)['effective_cutoff_unix']
    def forbidden(*args, **kwargs):
        pytest.fail('closed_source_must_not_be_contacted')
    with pytest.raises(subject.SourceLeaseClosed):
        subject.guarded_page(target,{},Path('/unused'),'unused',{},lambda:cutoff+offset,forbidden)


def test_unknown_wrapper_fails_closed():
    with pytest.raises(KeyError):
        subject.admission(dict(wrapper='unregistered.sh'),0)


def test_allowed_read_preserves_request_and_receiver_alarm():
    target = dict(label='synthetic',wrapper='ovx_ssh.sh',root='/unchanged',journal_id='same')
    cursor = dict(last_index=11,last_sha256='bound')
    calls = []
    def run(command, **kwargs):
        calls.append((command,kwargs))
        return SimpleNamespace(returncode=0,stdout='{"entries": [], "scanned": 0}')
    result = subject.guarded_page(target,cursor,'/repo','import json\n',{},lambda:1,run)
    command, options = calls[0]
    assert command == ['bash','/repo/gpu/ovx_ssh.sh','python3 -B -']
    assert options['timeout'] == 30 and 'limit=64' in options['input']
    assert repr(target) in options['input'] and repr(cursor) in options['input']
    assert 'signal.setitimer(signal.ITIMER_REAL, _remaining)' in options['input']
    assert result['entries'] == []


def test_dispatch_rechecks_clock_after_building_payload():
    target = dict(label='synthetic',wrapper='ovx_ssh.sh')
    cutoff = subject.admission(target,0)['effective_cutoff_unix']
    times = iter([cutoff-36,cutoff-34])
    with pytest.raises(subject.SourceLeaseClosed):
        subject.guarded_page(target,{},'/unused','',{},lambda:next(times),
                             lambda *args,**kwargs:pytest.fail('late_dispatch'))


def test_expired_receiving_host_refuses_before_read():
    decision = dict(effective_cutoff_unix=1)
    code = subject.remote_program("raise RuntimeError('reader_must_not_execute')",{}, {}, decision)
    result = subprocess.run(['python3','-B','-'],input=code,text=True,capture_output=True,timeout=5)
    assert result.returncode != 0 and 'source_lease_closed_before_read' in result.stderr
    assert 'reader_must_not_execute' not in result.stderr


def test_expired_target_preserves_entries_and_cursor(tmp_path):
    target = dict(label='synthetic',wrapper='ovx_ssh.sh')
    initial = dict(entries={'immutable':dict(life='synthetic',record_index=8,sleep=2)},
                   cursors={'synthetic':dict(last_index=8,last_sha256='original')})
    enroll.put(tmp_path/'private/STATE.json',initial)
    registration = dict(deadline_unix=subject.SERVICE_END,targets=[target])
    cutoff = subject.admission(target,0)['effective_cutoff_unix']
    status = subject.lease_tick(enroll,registration,tmp_path,'/unused','',lambda:cutoff,
                               lambda *args,**kwargs:pytest.fail('expired_ssh'))
    assert json.loads((tmp_path/'private/STATE.json').read_bytes()) == initial
    assert status['rows'][0]['status'] == 'SOURCE_LEASE_CLOSED_NO_REMOTE_READ'
    assert status['rows'][0]['enrolled'] == 1
    assert status['rows'][0]['evaluated_by_this_queue'] == 0


def test_closed_source_does_not_block_other_registered_lives(tmp_path):
    targets = [dict(label='closed',wrapper='ovx_ssh.sh'),dict(label='open',wrapper='ovx4_ssh.sh')]
    initial = dict(entries={},cursors={label:dict(last_index=8,last_sha256='same') for label in ['closed','open']})
    enroll.put(tmp_path/'private/STATE.json',initial)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0,stdout=json.dumps(dict(entries=[],cursor=dict(last_index=9,last_sha256='new'),
            caught_up=True,observed_head=9)))
    cutoff = subject.admission(targets[0],0)['effective_cutoff_unix']
    status = subject.lease_tick(enroll,dict(deadline_unix=subject.SERVICE_END,targets=targets),
                               tmp_path,'/repo','',lambda:cutoff,run)
    assert [row['status'] for row in status['rows']] == ['SOURCE_LEASE_CLOSED_NO_REMOTE_READ','CAUGHT_UP']
    assert len(calls) == 1 and calls[0][1] == '/repo/gpu/ovx4_ssh.sh'
    current = json.loads((tmp_path/'private/STATE.json').read_bytes())
    assert current['cursors']['closed'] == initial['cursors']['closed']
    assert current['cursors']['open']['last_index'] == 9


def test_retained_state_integrity_and_monotone_cursor():
    initial = dict(entries={'key':{'sleep':2}},cursors={'life':{'last_index':8}})
    current = deepcopy(initial)
    current['entries']['new'] = {'sleep':3}
    current['cursors']['life']['last_index'] = 9
    subject.verify_preserved(current,initial)
    current['entries']['key']['sleep'] = 7
    with pytest.raises(ValueError,match='historical_enrollment_changed'):
        subject.verify_preserved(current,initial)
    with pytest.raises(ValueError,match='enrollment_cursor_regressed'):
        subject.verify_preserved(dict(entries=initial['entries'],cursors={'life':{'last_index':7}}),initial)


def test_handoff_can_only_target_exact_previous_cpu_enrollment():
    original = dict(pid=handoff.OLD_PID,start_ticks=handoff.OLD_START,args=handoff.OLD_ARGS)
    handoff.verify_old(original)
    for changes in [dict(pid=1),dict(start_ticks=0),dict(args=['python3','native_life.py'])]:
        with pytest.raises(ValueError,match='only_exact_previous_cpu_enrollment'):
            handoff.verify_old(dict(original,**changes))
