"""Fixed registered capture forwarding; outputs are never decoded on the VM."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = HERE/'fleet_generation2'
ROOT = '/localhome/local-rohing/orch_r167_fleet_20260917_generation2'
NODES = ('ovx3','ovx2','a100','a40r')


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document,output,sort_keys=True)


def available(node, plan):
    ids=[life['life_id'] for life in plan['lives'] if life['node']==node and life['status']=='SOURCE_CANDIDATE']
    script='''import json
from pathlib import Path
root=Path(ROOT_VALUE);ids=IDS_VALUE
rows=[]
for life_id in ids:
    for receipt in sorted((root/'lives'/life_id/'captures').glob('*/COMPLETE.json')):
        if not (receipt.parent/'FAILED.json').exists():rows.append({'life_id':life_id,'sleep':int(receipt.parent.name)})
print(json.dumps(rows))
'''.replace('ROOT_VALUE',repr(ROOT)).replace('IDS_VALUE',repr(ids))
    result=subprocess.run(['bash',str(REPO/'gpu'/(node+'_ssh.sh')),'python3 -c '+shlex.quote(script)],
        capture_output=True,timeout=30,check=True)
    return [(node,row['life_id'],row['sleep']) for row in json.loads(result.stdout)]


def copy_cell(row, operation, pins):
    node,life_id,sleep=row
    key=f'{life_id}_{sleep:06d}'
    once=operation/(key+'.ONCE.json')
    if time.time()+330>=1789659000:
        return dict(status='MISSING_INSUFFICIENT_TRANSFER_WINDOW',life_id=life_id,sleep=sleep,model_calls=0)
    write(once,dict(node=node,life_id=life_id,sleep=sleep,started_unix=time.time(),no_retry=True))
    source_helper=ROOT+'/transfer_runtime1/fleet_transfer.py'
    receiver=ROOT+'/receiving_generation1/source/fleet_transfer.py'
    source_command=f"echo '{pins['helper_sha256']}  {source_helper}' | sha256sum -c - >&2 && PYTHONPATH={ROOT}/source timeout 240s python3 -B {source_helper} export --plan {ROOT}/control2/PLAN.json --life {life_id} --sleep {sleep}"
    receiving_command=f"echo '{pins['helper_sha256']}  {receiver}' | sha256sum -c - >&2 && PYTHONPATH={ROOT}/receiving_generation1/source timeout 240s /localhome/local-rohing/v2/venv/bin/python -B {receiver} receive"
    private=Path('/tmp/orch_r167_fleet_copy_generation2_private');private.mkdir(mode=0o700,exist_ok=True)
    with (private/(key+'.source.log')).open('xb') as source_log, (private/(key+'.receiving.log')).open('xb') as receiver_log:
        exporter=subprocess.Popen(['bash',str(REPO/'gpu'/(node+'_ssh.sh')),source_command],stdout=subprocess.PIPE,stderr=source_log)
        importer=subprocess.Popen(['bash',str(REPO/'gpu/ovx_ssh.sh'),receiving_command],stdin=exporter.stdout,stdout=subprocess.PIPE,stderr=receiver_log)
        exporter.stdout.close()
        result=importer.communicate(timeout=300)[0]
        source_status=exporter.wait(timeout=30)
    status=dict(node=node,life_id=life_id,sleep=sleep,source_returncode=source_status,receiving_returncode=importer.returncode,
        observed_unix=time.time(),model_calls=0)
    if source_status==0 and importer.returncode==0:
        status.update(status='EXACT_RECEIVING_COPY_VERIFIED',receiving=json.loads(result))
        write(operation/(key+'.COMPLETE.json'),status)
    else:
        status['status']='COPY_FAILED_OR_UNCERTAIN_NO_RETRY'
        write(operation/(key+'.FAILED.json'),status)
    return status


def run():
    os.umask(0o077)
    plan=json.loads((BASE/'control2/PLAN.json').read_bytes())
    pins=json.loads((BASE/'TRANSFER_CPU_GATE.json').read_bytes())
    assert pins['status']=='PASS' and pins['helper_sha256']==hashlib.sha256((HERE/'fleet_transfer.py').read_bytes()).hexdigest()
    operation=BASE/'copy_operation1';operation.mkdir(mode=0o700,exist_ok=False)
    write(operation/'ONCE.json',dict(started_unix=time.time(),plan_sha256=hashlib.sha256((BASE/'control2/PLAN.json').read_bytes()).hexdigest(),model_calls=0))
    while time.time()<1789659000:
        rows=[]
        for node in NODES:
            try:rows.extend(available(node,plan))
            except Exception as error:
                write(operation/(node+'.OBSERVATION_FAILURE.'+str(time.time_ns())+'.json'),dict(error_type=type(error).__name__))
        order={life['life_id']:index for index,life in enumerate(plan['lives'])}
        rows=sorted(rows,key=lambda item:(item[2]!=0,order[item[1]],item[2]))
        pending=[row for row in rows if not (operation/(f'{row[1]}_{row[2]:06d}.ONCE.json')).exists()]
        with ThreadPoolExecutor(max_workers=2) as workers:
            for result in workers.map(lambda row:copy_cell(row,operation,pins),pending):
                print(json.dumps(result),flush=True)
        time.sleep(20)


if __name__=='__main__':run()
