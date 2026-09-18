import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
authority_path = BASE / 'ACTIVATION5_CONDITIONAL_MAIN_AUTHORITY.json'
authority_bytes = authority_path.read_bytes()
authority_sha = hashlib.sha256(authority_bytes).hexdigest()
authority = json.loads(authority_bytes)
observer = BASE / 'ACTIVATION5_PASSIVE_BOUNDARY.py'
assert hashlib.sha256(observer.read_bytes()).hexdigest() == authority['observer_sha256']
executor = BASE / 'ACTIVATION5_EVENT_EXECUTE.py'
done = set()
with (BASE / 'ACTIVATION5_EVENT_DISPATCHER_ONCE').open('x') as once:
    once.write(json.dumps(dict(pid=os.getpid(), started_unix=time.time(), authority_sha256=authority_sha)) + '\n')
    once.flush()
    os.fsync(once.fileno())
with (BASE / 'ACTIVATION5_PASSIVE_EVENTS.jsonl').open() as events:
    while time.time() < authority['event_deadline_unix'] and len(done) < len(authority['ready_sha256']):
        position = events.tell()
        line = events.readline()
        if not line or not line.endswith('\n'):
            events.seek(position)
            time.sleep(0.2)
            continue
        event = json.loads(line)
        agent = event.get('agent')
        if agent not in authority['ready_sha256'] or agent in done or event.get('status') != authority['event_status']:
            continue
        if not 0 <= time.time() - event['observed_unix'] <= authority['event_max_age_seconds']:
            continue
        assert event['ready_sha256'] == authority['ready_sha256'][agent]
        assert event['deadline_unix'] == authority['event_deadline_unix']
        done.add(agent)
        with (BASE / ('ACTIVATION5_' + agent + '_EVENT_DISPATCH_INTENT.json')).open('x') as stream:
            stream.write(json.dumps(dict(event=event, authority_sha256=authority_sha,
                observed_unix=time.time(), no_retry=True), sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        command = 'python3 -B - ' + shlex.quote(authority_sha) + ' ' + shlex.quote(json.dumps(event))
        try:
            with executor.open('rb') as script, (BASE / ('ACTIVATION5_' + agent + '_EVENT_DISPATCH.jsonl')).open('xb') as output, (BASE / ('ACTIVATION5_' + agent + '_EVENT_DISPATCH.stderr')).open('xb') as errors:
                result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], cwd=REPO,
                    stdin=script, stdout=output, stderr=errors, timeout=90)
            print(json.dumps(dict(agent=agent, returncode=result.returncode, observed_unix=time.time(),
                status='REMOTE_EVENT_COMMAND_FINISHED_NO_RETRY', no_retry=True)), flush=True)
        except Exception as error:
            print(json.dumps(dict(agent=agent, error_type=type(error).__name__, reason=str(error),
                observed_unix=time.time(), status='UNCERTAIN_DO_NOT_RETRY')), flush=True)
print(json.dumps(dict(status='EVENT_DISPATCHER_FINISHED', attempted=sorted(done),
    no_event=[agent for agent in authority['ready_sha256'] if agent not in done], observed_unix=time.time())), flush=True)
