"""One-slot approved boundary execution with compact, read-only fleet census."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from gpu.orch_rich_hot_node1_exhaustion_roll import remote
from organism_v6 import orch_rich_hot_node1_premise as policy

OUTPUT = Path('research_notes/analysis/orch_rich_hot_node1_20260915_premise_v1')
OLD = '/localhome/local-rohing/orch_rich_hot_node1_20260915_exhaustion_v1'
QUERY = r'''
import subprocess,json,hashlib,socket,time
from pathlib import Path
gpus=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
minors={}
for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
 fields=dict(line.split(':',1) for line in path.read_text().splitlines() if ':' in line)
 minors[fields['GPU UUID'].strip()]=int(fields['Device Minor'].strip())
rows=[]
for line in apps.splitlines():
 uuid,pid=[part.strip() for part in line.split(',')];directory=Path('/proc')/pid
 try:
  args=(directory/'cmdline').read_bytes().decode().split('\0')
  module=args[args.index('-m')+1] if '-m' in args else next((arg for arg in args if arg.endswith('.py')),'unknown')
  root=args[args.index('--root')+1] if '--root' in args else None
  rows.append(dict(uuid=uuid,pid=int(pid),module=module,root=root,start_ticks=(directory/'stat').read_text().rsplit(')',1)[1].split()[19]))
 except (FileNotFoundError,ProcessLookupError):pass
print(json.dumps(dict(observed_unix=time.time(),host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),gpus=gpus.splitlines(),kernel_minors=minors,apps=rows)))
'''


def write(name, value):
    path = OUTPUT / name
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def census():
    wrappers = dict(node1='gpu/a40r_ssh.sh', node2='gpu/ovx_ssh.sh',
                    node3='gpu/ovx2_ssh.sh', a100='gpu/a100_ssh.sh')
    def query(item):
        name, wrapper = item
        return name, json.loads(remote(wrapper, 'sudo -n python3 -c ' + shlex.quote(QUERY)))
    with ThreadPoolExecutor(4) as executor:
        nodes = dict(executor.map(query, wrappers.items()))
    counts = {name: len({row['uuid'] for row in node['apps']
                        if 'rich_hot_' in row['module']}) for name, node in nodes.items()}
    total = sum(counts.values())
    return dict(observed_unix=min(node['observed_unix'] for node in nodes.values()),
                active_generators=total, minimum_during_one_gpu_roll=total - 1,
                counted_nodes=counts, nodes=nodes, classification='compute-resident rich_hot module; conservative')


def send_floor(receipt):
    code = ('from pathlib import Path;import os;path=Path(' + repr(policy.ROOT + '/FLOOR_3.json')
            + ');temporary=path.with_suffix(".tmp");temporary.write_text('
            + repr(json.dumps(receipt)) + ');os.replace(temporary,path)')
    remote('gpu/a40r_ssh.sh', 'python3 -c ' + shlex.quote(code))


def execute():
    write('EXECUTION_STATUS.json', dict(phase='FRESH_FLEET', controller_pid=os.getpid(), observed_unix=time.time()))
    receipt = census()
    write('FLEET_BEFORE.json', receipt)
    policy.require(receipt['minimum_during_one_gpu_roll'] >= 16, 'generation_floor_below_16')
    node1 = receipt['nodes']['node1']
    policy.require(all(any(row['uuid'] == policy.UUIDS[index] and row['root'] == OLD
                           for row in node1['apps']) for index in (0, 1, 3)), 'unhinted_or_selected_identity_missing')
    send_floor(receipt)
    environment = f'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH={policy.ROOT}/source '
    python = '/localhome/local-rohing/v2/venv/bin/python -B '
    command = (environment + python + '-m gpu.orch_rich_hot_node1_premise_boundary '
               f'--root {OLD} --destination {policy.ROOT} --index 3 --floor-receipt {policy.ROOT}/FLOOR_3.json')
    boundary = subprocess.Popen(['bash', 'gpu/a40r_ssh.sh', command], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
    write('EXECUTION_STATUS.json', dict(phase='WAIT_COMPLETE_TASK', controller_pid=os.getpid(),
          boundary_wrapper_pid=boundary.pid, observed_unix=time.time(), floor=receipt['active_generators']))
    while boundary.poll() is None:
        time.sleep(5)
        receipt = census()
        send_floor(receipt)
        write('FLEET_LATEST.json', receipt)
    stdout, stderr = boundary.communicate()
    if boundary.returncode:
        write('BOUNDARY_ERROR.json', dict(returncode=boundary.returncode, stdout=stdout,
              error_tail=stderr[-2000:], observed_unix=time.time()))
        raise RuntimeError('boundary_failed_no_launch')
    write('BOUNDARY_EXECUTED.json', dict(result=json.loads(stdout), observed_unix=time.time()))
    command = (environment + 'HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false nohup '
               + python + '-m gpu.orch_rich_hot_node1_premise_run supervise '
               f'--root {policy.ROOT} --index 3 > {policy.ROOT}/guard_3.log 2>&1 < /dev/null & echo SUBMITTED')
    result = remote('gpu/a40r_ssh.sh', command)
    write('EXECUTION_STATUS.json', dict(phase='GUARDIAN_SUBMITTED', controller_pid=os.getpid(),
          result=result.strip(), observed_unix=time.time(), no_new_budget=True))


if __name__ == '__main__':
    try:
        execute()
    except BaseException as error:
        write('EXECUTION_FAILURE.json', dict(error_type=type(error).__name__, error=str(error), observed_unix=time.time()))
        raise
