import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r157_community_service_keepalive as shared
from gpu import orch_r157_repo_reader_wall as reader


repository = Path('/data/home/rohing/dream-state-orch')
evidence = repository / 'research_loop/workers/r157_repo_reader_wall_20260917/PARENT'
intent = reader.read(evidence / 'STOP_INTENT.json')
owner, before = intent['owner'], intent['before']
assert owner['pid'] == 1554590 and owner['start_ticks'] == '170917389'
assert not Path('/proc/1554590').exists()
assert not (evidence / 'START_INTENT.json').exists()
config_path = Path(owner['config']['path'])
config = reader.read(config_path)
assert reader.ref(config_path) == owner['config']
assert config['root'] == str(reader.HOST_ROOT)
output = config_path.parent / 'parent'
assert shared.programme_state(output, config) == before
reader.write(evidence / 'STOPPED.json', dict(owner=owner, saved=before, observed_unix=time.time(),
    note='Prior pidfd signalled exit before procfs removal; now absence verified. No additional signal.'))
authority = repository / 'research_loop/workers/r157_keepalive_20260917/AUTHORIZATION.json'
provenance = repository / 'research_loop/workers/r157_community_wall_20260917/PROVENANCE.json'
original = repository / 'gpu/orch_r133_programme_parent.py'
spec = dict(schema='R157_PROTECTED_PARENT_RESUME_V1', approved_by='Main', graceful_owner_release=True,
    authority=reader.ref(authority), provenance=reader.ref(provenance), previous_config=reader.ref(config_path),
    successor_config=reader.ref(evidence / 'CONFIG.json'), output=str(output), previous_owner=owner,
    original_source=reader.ref(original), before=before, receipt_directory=str(evidence),
    release=reader.ref(evidence / 'STOPPED.json'))
reader.write(evidence / 'RESUME_SPEC.json', spec)
generated = reader.reader_parent_resume_source(original.read_bytes(), reader.ref(evidence / 'RESUME_SPEC.json'))
with (evidence / 'READER_PARENT.py').open('x') as stream:
    stream.write(generated)
command = ['/usr/bin/python3', '-B', str(evidence / 'READER_PARENT.py'), '--config', str(evidence / 'CONFIG.json'),
           '--repository', str(repository), '--output', str(output)]
environment = dict(os.environ, PYTHONPATH=str(repository), PYTHONDONTWRITEBYTECODE='1')
reader.write(evidence / 'START_INTENT.json', dict(command=command, source=reader.ref(evidence / 'READER_PARENT.py'),
    environment='Current authorized operator environment; prior observed cwd/PYTHONPATH retained; secrets not captured.',
    observed_unix=time.time()))
with (evidence / 'PARENT.log').open('xb') as log:
    process = subprocess.Popen(command, cwd=owner['cwd'], env=environment, stdin=subprocess.DEVNULL,
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
reader.write(evidence / 'STARTED.json', dict(pid=process.pid, command=command, observed_unix=time.time()))
for attempt in range(90):
    resumed = evidence / ('RESUMED_' + str(process.pid) + '.json')
    if resumed.exists():
        assert process.poll() is None
        print(json.dumps(reader.read(resumed), sort_keys=True))
        break
    assert process.poll() is None, 'reader_parent_successor_failed_see_local_log'
    time.sleep(1)
else:
    raise ValueError('reader_parent_startup_receipt_not_yet_observed')
