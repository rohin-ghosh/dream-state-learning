import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from gpu import orch_r157_community_service_keepalive as shared
from gpu import orch_r157_repo_reader_wall as reader


repository = Path('/data/home/rohing/dream-state-orch')
evidence = repository / 'research_loop/workers/r157_repo_reader_wall_20260917/PARENT'
previous = repository / 'research_loop/workers/r153_measurement_parent_node5_staging_20260916/repo_reader_rebind_20260916T2341Z'
config_path = previous / 'PARENT_CONFIG.json'
output = previous / 'parent'
pid = 1554590
ticks = '170917389'
authority = repository / 'research_loop/workers/r157_keepalive_20260917/AUTHORIZATION.json'
provenance = repository / 'research_loop/workers/r157_community_wall_20260917/PROVENANCE.json'
reader.authority(authority)
assert reader.sha(provenance) == '23832f7011f78cdcfbe1d4e29bbc23fcb44d540792e17992a9b983911b8ed269'
assert reader.read(provenance)['conflicting_real_reservation_found'] is False
config = reader.read(config_path)
assert config['root'] == str(reader.HOST_ROOT) and config['programme'] == 'repo_reader'
assert config['hard_end_unix'] == reader.OLD_WALL
proc = Path('/proc') / str(pid)
expected = ['/usr/bin/python3', '-B', '-m', 'gpu.orch_r133_programme_parent', '--config', str(config_path),
            '--repository', str(repository), '--output', str(output)]


def identity():
    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert fields[19] == ticks
    assert (proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0') == expected
    return fields


def children():
    return [child for task in (proc / 'task').iterdir() for child in (task / 'children').read_text().split()]


identity()
environment = dict(part.split(b'=', 1) for part in (proc / 'environ').read_bytes().split(b'\0') if b'=' in part)
environment = {key.decode(): value.decode() for key, value in environment.items()}
cwd = os.readlink(proc / 'cwd')
original = repository / 'gpu/orch_r133_programme_parent.py'
original_raw = original.read_bytes()
assert reader.sha(original) == shared.PROGRAMME_SOURCE_SHA
reader.reader_parent_resume_source(original_raw, {'path': '/tmp/preflight-unused', 'sha256': 'a' * 64})
evidence.mkdir(mode=0o700)
reader.write(evidence / 'CPU_GATE.json', dict(local_reader_tests=48, parent_tests=35, status='PASS',
    source=reader.ref(Path(reader.__file__).resolve()), tests=reader.ref(repository / 'tests/test_orch_r157_repo_reader_wall.py'),
    shared=reader.ref(Path(shared.__file__).resolve()), observed_unix=time.time()))
successor = dict(config, hard_end_unix=reader.NEW_WALL)
reader.write(evidence / 'CONFIG.json', successor)
descriptor = os.pidfd_open(pid)
paused = False
retired = False
try:
    end = time.monotonic() + 100
    while time.monotonic() < end:
        identity()
        if (proc / 'wchan').read_text().strip() != 'hrtimer_nanosleep' or children():
            time.sleep(0.1)
            continue
        before = shared.programme_state(output, config)
        identity()
        if children() or (proc / 'wchan').read_text().strip() != 'hrtimer_nanosleep':
            continue
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        paused = True
        for attempt in range(100):
            if identity()[0] == 'T':
                break
            time.sleep(0.01)
        assert identity()[0] == 'T'
        if children() or shared.programme_state(output, config) != before:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            paused = False
            continue
        owner = dict(pid=pid, start_ticks=ticks, command=expected, cwd=cwd, config=reader.ref(config_path))
        reader.write(evidence / 'STOP_INTENT.json', dict(owner=owner, idle=True, children=[],
            before=before, observed_unix=time.time(), signal='SIGINT'))
        signal.pidfd_send_signal(descriptor, signal.SIGINT)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        paused = False
        assert select.select([descriptor], [], [], 30)[0], 'old_reader_parent_did_not_exit'
        assert not proc.exists(), 'old_reader_parent_still_present'
        retired = True
        reader.write(evidence / 'STOPPED.json', dict(owner=owner, saved=before, observed_unix=time.time()))
        break
    assert retired, 'no_settled_reader_parent_boundary_in_100_seconds'
finally:
    if paused:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    os.close(descriptor)

spec = dict(schema='R157_PROTECTED_PARENT_RESUME_V1', approved_by='Main', graceful_owner_release=True,
    authority=reader.ref(authority), provenance=reader.ref(provenance), previous_config=reader.ref(config_path),
    successor_config=reader.ref(evidence / 'CONFIG.json'), output=str(output), previous_owner=owner,
    original_source=reader.ref(original), before=before, receipt_directory=str(evidence),
    release=reader.ref(evidence / 'STOPPED.json'))
reader.write(evidence / 'RESUME_SPEC.json', spec)
generated = reader.reader_parent_resume_source(original_raw, reader.ref(evidence / 'RESUME_SPEC.json'))
with (evidence / 'READER_PARENT.py').open('x') as stream:
    stream.write(generated)
command = ['/usr/bin/python3', '-B', str(evidence / 'READER_PARENT.py'), '--config', str(evidence / 'CONFIG.json'),
           '--repository', str(repository), '--output', str(output)]
reader.write(evidence / 'START_INTENT.json', dict(command=command, source=reader.ref(evidence / 'READER_PARENT.py'),
    observed_unix=time.time()))
with (evidence / 'PARENT.log').open('xb') as log:
    process = subprocess.Popen(command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
reader.write(evidence / 'STARTED.json', dict(pid=process.pid, command=command, observed_unix=time.time()))
for attempt in range(90):
    resumed = evidence / ('RESUMED_' + str(process.pid) + '.json')
    if resumed.exists():
        assert process.poll() is None
        print(json.dumps(reader.read(resumed), sort_keys=True))
        sys.exit(0)
    assert process.poll() is None, 'reader_parent_successor_failed_see_local_log'
    time.sleep(1)
raise ValueError('reader_parent_startup_receipt_not_yet_observed')
