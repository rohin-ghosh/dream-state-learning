"""Rebind the existing community service using its offline handoff primitive."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sqlite3
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent / 'R205_SERVICE'
SOURCE = ROOT / 'source'
REPOSITORY = Path('/data/home/rohing/dream-state-orch')
PREVIOUS = REPOSITORY / 'research_loop/workers/r157_community_service_keepalive_20260917/bundle/SERVICE.json'
READY = REPOSITORY / 'research_loop/workers/rohin201_c2_clones_20260917/r205_ready/READY.json'
sys.path.insert(0, str(SOURCE))
from gpu import orch_r153_community_transport as transport
from gpu import orch_r153_service_handoff as handoff
from gpu.orch_r153_community_service import validate_config


def write(name, document):
    with (ROOT / name).open('x') as output:
        json.dump(document, output, indent=2, sort_keys=True)


def validate_transition(previous, successor):
    assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() == '401489f42fb3fba8dea7046e40401c053eceb9d5132de2df98e794d7455cf5ef'
    assert previous == json.loads(PREVIOUS.read_bytes())
    assert previous['profile'] == 'ALL5_OVX3'
    expected = deepcopy(previous)
    expected['hosts']['ovx3']['repository'] = '/localhome/local-rohing/orch_r153_service_source_v5_20260918'
    expected['hosts']['ovx3']['source_sha256'] = transport.source_pins(SOURCE)
    assert successor == expected
    main = json.loads(READY.read_bytes())
    for name in transport.SOURCES:
        if name in main['files']:
            assert successor['hosts']['ovx3']['source_sha256'][name] == main['files'][name]
    validate_config(successor)


def main():
    previous = json.loads(PREVIOUS.read_bytes())
    successor = deepcopy(previous)
    successor['hosts']['ovx3']['repository'] = '/localhome/local-rohing/orch_r153_service_source_v5_20260918'
    successor['hosts']['ovx3']['source_sha256'] = transport.source_pins(SOURCE)
    validate_transition(previous, successor)
    if (ROOT / 'SERVICE.json').exists():
        assert json.loads((ROOT / 'SERVICE.json').read_bytes()) == successor
    else:
        write('SERVICE.json', successor)
    database_path = Path(previous['broker_root']) / 'state.sqlite3'
    with sqlite3.connect(database_path.as_uri() + '?mode=ro', uri=True) as database:
        assert database.execute("SELECT count(*) FROM service_jobs WHERE status IN ('CPU_INTENT','CPU_UNKNOWN')").fetchone()[0] == 0
        before = dict(cursors=database.execute('SELECT * FROM service_cursors ORDER BY actor').fetchall(),
            jobs=database.execute('SELECT actor,status,count(*) FROM service_jobs GROUP BY actor,status').fetchall())
    process = Path('/proc/769286')
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    argv = (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
    assert fields[19] == '178833457' and fields[0] == 'T'
    assert argv[-2:] == [str(PREVIOUS), '--run']
    descriptor = os.pidfd_open(769286)
    write('OLD_STOP_INTENT.json', dict(observed_unix=time.time(), pid=769286,
        start_ticks=fields[19], before=before, other_learners_and_parents_untouched=True))
    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    assert select.select([descriptor], [], [], 10)[0]
    os.close(descriptor)
    handoff.validate_transition = validate_transition
    receipt = handoff.handoff(previous, successor, ROOT / 'handoff')
    with sqlite3.connect(database_path.as_uri() + '?mode=ro', uri=True) as database:
        after = dict(cursors=database.execute('SELECT * FROM service_cursors ORDER BY actor').fetchall(),
            jobs=database.execute('SELECT actor,status,count(*) FROM service_jobs GROUP BY actor,status').fetchall())
    assert before == after
    write('REBIND.json', dict(observed_unix=time.time(), preserved=after,
        service_config_sha256=hashlib.sha256((ROOT / 'SERVICE.json').read_bytes()).hexdigest(),
        source_pins=successor['hosts']['ovx3']['source_sha256'], handoff_schema=receipt['schema'],
        roots_cursors_jobs_gates_and_recipes_unchanged=True))
    with (ROOT / 'service.log').open('x') as log:
        service = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r153_community_service',
            '--config', str(ROOT / 'SERVICE.json'), '--run'], cwd=SOURCE,
            env=dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    fields = (Path('/proc') / str(service.pid) / 'stat').read_text().rsplit(') ', 1)[1].split()
    write('STARTED.json', dict(observed_unix=time.time(), pid=service.pid, start_ticks=fields[19],
        cwd=str(SOURCE), config_path=str(ROOT / 'SERVICE.json'), R205_origin_policy='R205_CONSOLE_REPLY_ACT_V1'))
    print('R205_COMMUNITY_REBOUND', service.pid, flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        write('FAILURE_' + str(time.time_ns()) + '.json',
            dict(observed_unix=time.time(), error_type=type(error).__name__, reason=str(error)))
        raise
