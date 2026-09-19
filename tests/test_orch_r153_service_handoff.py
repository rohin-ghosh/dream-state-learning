from copy import deepcopy
import fcntl
import json
import os
import sqlite3

import pytest

from gpu import orch_r153_service_handoff as handoff
from gpu import orch_r153_community_exchange as exchange


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(handoff, 'validate_config', lambda config: config)
    root = tmp_path / 'broker'
    root.mkdir(mode=0o700)
    for name in ('SERVICE_OWNER.lock', 'LOCK'):
        (root / name).touch(mode=0o600)
    previous = dict(profile='ALL5_OVX3', broker_root=str(root), agents={'C5': 'unchanged'},
                    hosts={'ovx3': dict(repository='/localhome/local-rohing/orch_r153_service_source_v2_20260916',
                                       source_sha256={handoff.TRANSPORT: 'a' * 64,
                                                      handoff.EXCHANGE: 'e' * 64, 'other': 'c' * 64})})
    successor = deepcopy(previous)
    successor['hosts']['ovx3']['repository'] = '/localhome/local-rohing/orch_r153_service_source_v3_20260916'
    successor['hosts']['ovx3']['source_sha256'][handoff.TRANSPORT] = 'b' * 64
    successor['hosts']['ovx3']['source_sha256'][handoff.EXCHANGE] = 'f' * 64
    with sqlite3.connect(root / 'state.sqlite3') as database:
        database.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value BLOB)')
        database.execute('INSERT INTO metadata VALUES (?,?)', ('service_config', exchange.encoded(previous)))
        database.execute('CREATE TABLE service_jobs (id TEXT, status TEXT)')
        database.execute("INSERT INTO service_jobs VALUES ('existing','CPU_DONE')")
        database.execute('CREATE TABLE service_cursors (actor TEXT, next_index INTEGER)')
        database.execute("INSERT INTO service_cursors VALUES ('C1',144)")
        database.execute('CREATE TABLE artifacts (id TEXT, content BLOB)')
        database.execute("INSERT INTO artifacts VALUES ('shared',?)", (b'preserved',))
    os.chmod(root / 'state.sqlite3', 0o600)
    return previous, successor, tmp_path / 'evidence'


def test_transport_handoff_preserves_all_existing_rows(setup):
    previous, successor, evidence = setup
    handoff.handoff(previous, successor, evidence)
    with sqlite3.connect(previous['broker_root'] + '/state.sqlite3') as database:
        assert database.execute('SELECT * FROM service_jobs').fetchall() == [('existing', 'CPU_DONE')]
        assert database.execute('SELECT * FROM service_cursors').fetchall() == [('C1', 144)]
        assert database.execute('SELECT * FROM artifacts').fetchall() == [('shared', b'preserved')]
        assert json.loads(database.execute('SELECT value FROM metadata').fetchone()[0]) == successor
    with sqlite3.connect(evidence / 'BEFORE.sqlite3') as backup:
        assert json.loads(backup.execute('SELECT value FROM metadata').fetchone()[0]) == previous
    assert (evidence / 'APPLIED.json').is_file()
    with pytest.raises(ValueError, match='exact_previous'):
        handoff.handoff(previous, successor, evidence.parent / 'retry')


@pytest.mark.parametrize('change', ['agent', 'dependency', 'root', 'gate'])
def test_rejects_unrelated_changes(setup, change):
    previous, successor, evidence = setup
    if change == 'agent':
        successor['agents']['C5'] = 'changed'
    elif change == 'dependency':
        successor['hosts']['ovx3']['source_sha256']['other'] = 'd' * 64
    elif change == 'root':
        successor['broker_root'] += 'new'
    else:
        successor['hosts']['ovx3']['gate_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='transport_only'):
        handoff.handoff(previous, successor, evidence)
    assert not evidence.exists()


def test_live_owner_blocks_handoff(setup):
    previous, successor, evidence = setup
    with open(previous['broker_root'] + '/SERVICE_OWNER.lock', 'r+') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            handoff.handoff(previous, successor, evidence)
    assert not evidence.exists()


def test_inflight_cpu_blocks_handoff(setup):
    previous, successor, evidence = setup
    with sqlite3.connect(previous['broker_root'] + '/state.sqlite3') as database:
        database.execute("UPDATE service_jobs SET status='CPU_INTENT'")
    with pytest.raises(ValueError, match='resolve_inflight'):
        handoff.handoff(previous, successor, evidence)
    assert not evidence.exists()
