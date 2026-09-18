"""One new bounded observation; never replays the interrupted candidate creation."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
WORKER = HERE.parents[1]
sys.path.insert(0, str(WORKER))
import preparation_io as common


REMOTE = '''import hashlib,json,os,pathlib,sys,time
os.umask(0o077)
request=json.loads(sys.stdin.buffer.read(131072))
root=pathlib.Path(request['observation_root'])
root.mkdir(mode=0o700,exist_ok=False)
def write(name,document):
 raw=json.dumps(document,sort_keys=True,separators=(',',':')).encode()
 with (root/name).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
write('REQUEST.json',request)
path=pathlib.Path(request['candidate_public_path'])
result={'status':'CANDIDATE_PUBLIC_RECEIPT_ABSENT','observed_unix':time.time(),'actual_metadata_bytes':0,
 'model_calls':0,'provider_calls':0,'execution_authorized':False}
if path.is_file():
 with path.open('rb',buffering=0) as stream:
  size=os.fstat(stream.fileno()).st_size
  assert path==path.resolve() and size<=request['allowance']['document']['bytes']
  write('READ_CHARGE.json',{'bytes':size,'authority':request['allowance']['reference'],
   'status':'CHARGED_BEFORE_READ_NO_REFUND','path':str(path)})
  raw=stream.read(size)
  assert len(raw)==size
 receipt=json.loads(raw)
 result.update(status='EXISTING_CANDIDATE_RECOVERED_WITHOUT_REPLAY',actual_metadata_bytes=size,
  remote_receipt={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()},candidate=receipt)
write('PUBLIC_METADATA.json',result)
print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    root = HERE / 'recovery_observation1'
    root.mkdir(mode=0o700, exist_ok=False)
    ledger = common.Ledger(WORKER / 'preparation1/global_ledger')
    allowance = ledger.reserve('C2_metadata_repair1_recovery_observation1', 'C2',
        'metadata', 128 * 1024, discovery=True)
    request = dict(allowance=allowance,
        observation_root=str(common.REMOTE / 'runner_candidate2_recovery_observation1'),
        candidate_public_path=str(common.REMOTE / 'runner_candidate2_metadata_repair1/PUBLIC_METADATA.json'),
        recorded_unix=time.time(), source_attempt_not_replayed=True)
    common.write(root / 'REQUEST.json', request)
    try:
        result = subprocess.run(['bash', str(WORKER.parents[2] / 'gpu/ovx_ssh.sh'),
            'python3 -c ' + shlex.quote(REMOTE)], input=common.canonical(request),
            capture_output=True, timeout=90)
        receipt = json.loads(result.stdout) if result.returncode == 0 else dict(
            status='RECOVERY_OBSERVATION_FAILED_NO_RETRY', returncode=result.returncode,
            stderr_bytes=len(result.stderr), stderr_sha256=common.sha(result.stderr))
    except subprocess.TimeoutExpired:
        receipt = dict(status='RECOVERY_OBSERVATION_TIMED_OUT_NO_RETRY')
    common.write(root / 'PUBLIC_METADATA.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
