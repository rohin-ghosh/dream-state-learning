"""Explicit once-only R171 Qwen BT operations; no retired humor launch."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

from gpu import ny_caption_data as data


def operate(operation):
    version = "BT_WIDEGAP_V1"
    data.require(operation in ('receive', 'cpu', 'probe', 'train'), 'exact_BT_operation')
    work = Path(__file__).resolve().parent
    repo = work.parents[3]
    transport_ref = data.file_ref(work/'private/bt_widegap_v1/TRANSPORT.json')
    transport = data.bound(transport_ref)
    root = transport['remote_root']
    data.require(root == '/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_v1', 'exact_fresh_remote_root')
    expected = transport['inventory']['sha256']
    request = data.private_write(work/'evidence'/f'PAIR_V{version}_{operation.upper()}_REQUESTED.json',
        dict(operation=operation, transport=transport_ref, requested_unix=time.time(), automatic_retry=False,
            operator=data.file_ref(Path(__file__).resolve())))
    code = '''import hashlib,json,os,shutil,subprocess,sys,tarfile,time
from pathlib import Path
root=Path(ROOT); expected=EXPECTED; operation=OPERATION
archive_hash=ARCHIVE_HASH; archive_bytes=ARCHIVE_BYTES
if operation=='receive':
 assert shutil.disk_usage(root.parent).free>16*1024**3 and not root.exists()
 root.mkdir(mode=0o700)
 archive=root/'PAYLOAD.tar.gz'; checksum=hashlib.sha256(); total=0
 with archive.open('xb') as output:
  while True:
   block=sys.stdin.buffer.read(1024**2)
   if not block: break
   total+=len(block); assert total<=archive_bytes<=128*1024**2
   checksum.update(block); output.write(block)
 assert total==archive_bytes and checksum.hexdigest()==archive_hash
 with tarfile.open(archive,'r:gz') as stream:
  members=stream.getmembers(); raw=stream.extractfile('INVENTORY.json').read(512*1024)
  assert hashlib.sha256(raw).hexdigest()==expected
  inventory=json.loads(raw); files=inventory['files']
  assert inventory['root']==str(root) and len(members)==len(files)+1
  assert {member.name for member in members}==set(files)|{'INVENTORY.json'}
  assert sum(member.size for member in members)<512*1024**2
  for member in members:
   assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
   target=root/member.name; target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
   checksum=hashlib.sha256(); size=0
   with stream.extractfile(member) as source,target.open('xb') as output:
    os.chmod(target,0o600)
    while True:
     block=source.read(1024**2)
     if not block: break
     checksum.update(block); size+=len(block); output.write(block)
   if member.name!='INVENTORY.json':
    assert checksum.hexdigest()==files[member.name]['sha256'] and size==files[member.name]['bytes']
 record=dict(status='RECEIVED_EXACT_NEW_CPU_CANDIDATE',root=str(root),inventory_sha256=expected,files=len(members),observed_unix=time.time(),GPU_calls=0)
else:
 assert hashlib.sha256((root/'INVENTORY.json').read_bytes()).hexdigest()==expected
 marker=root/(operation.upper()+'_PROCESS_STARTED.json')
 assert not marker.exists()
 environment=dict(PATH='/usr/bin:/bin',HOME=str(root),TMPDIR='/tmp',CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
 python='/localhome/local-rohing/v2/venv/bin/python'
 if operation=='cpu':
  assert not (root/'CPU_ONCE.json').exists()
  command=['/usr/bin/timeout','1200',python,'-B','-m','research_loop.workers.r177_caption_game_stage1_20260917.data_judge.widegap_receiving','cpu','--root',str(root),'--inventory-sha256',expected]
 else:
  gate=json.loads((root/'CPU_GATE.json').read_bytes())
  assert gate['status']=='PASS_WIDEGAP100K_CPU_NOT_GPU' and gate['inventory_sha256']==expected
  command=[python,'-B','-m','research_loop.workers.r177_caption_game_stage1_20260917.data_judge.widegap_receiving','dispatch-'+operation,'--root',str(root),'--inventory-sha256',expected]
  assert not (root/('OUTER_'+operation.upper()+'_COMMAND.json')).exists()
  if operation=='train':
   assert not (root/'ADMISSION.json').exists() and not (root/'training').exists()
   proof=json.loads((root/'CONFINEMENT_CPU_PROOF.json').read_bytes())
   assert proof['inventory_sha256']==expected and proof['checks']['denied_foreign_minors']==[0,2,3,4,5,6,7]
 with (root/(operation.upper()+'_PROCESS.log')).open('xb') as output:
  process=subprocess.Popen(command,cwd=root,env=environment,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 fields=(Path('/proc')/str(process.pid)/'stat').read_text().split(') ')[1].split()
 record=dict(status='ACTUAL_'+operation.upper()+'_WRAPPER_STARTED_NOT_SUCCESS',pid=process.pid,startticks=fields[19],started_unix=time.time(),command=command,inventory_sha256=expected,no_automatic_retry=True)
 raw=json.dumps(record,sort_keys=True).encode()
 with marker.open('xb') as output: output.write(raw)
 record['remote_process_receipt']=dict(path=str(marker),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
print(json.dumps(record,sort_keys=True))
'''
    values = {'ROOT': root, 'EXPECTED': expected, 'OPERATION': operation,
        'ARCHIVE_HASH': transport['archive']['sha256'], 'ARCHIVE_BYTES': transport['archive']['bytes']}
    for name, value in values.items():
        code = code.replace(name, repr(value), 1)
    command = ['bash', str(repo/'gpu/a40r_ssh.sh'), 'python3 -B -c '+shlex.quote(code)]
    if operation == 'receive':
        data.require(data.file_ref(transport['archive']['path']) == transport['archive'], 'unchanged_staged_archive')
        with Path(transport['archive']['path']).open('rb') as source:
            result = subprocess.run(command, stdin=source, capture_output=True, timeout=180, check=True)
    else:
        result = subprocess.run(command, capture_output=True, timeout=30, check=True)
    data.require(len(result.stdout) < 65536, 'bounded_operational_receipt_only')
    observed = json.loads(result.stdout)
    reference = data.private_write(work/'evidence'/f'PAIR_V{version}_{operation.upper()}_OBSERVED.json',
        dict(request=request, **observed))
    print(json.dumps(dict(receipt=reference, **observed)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--operation', choices=('receive', 'cpu', 'probe', 'train'), required=True)
    arguments = parser.parse_args()
    operate(arguments.operation)
