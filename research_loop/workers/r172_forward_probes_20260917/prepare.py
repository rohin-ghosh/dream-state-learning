"""Local coordinator: pre-reserved wrapper I/O, CPU-only source preparation."""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import prep_common as common


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREP = HERE / 'preparation1'
MIB = 1024 ** 2
WRAPPERS = dict(a100='gpu/a100_ssh.sh', a40r='gpu/a40r_ssh.sh', ovx2='gpu/ovx2_ssh.sh', ovx3='gpu/ovx3_ssh.sh', ovx='gpu/ovx_ssh.sh')
SOURCE_INPUTS = dict(
    native_custody='research_loop/workers/r167_object_survival/fleet_generation2/source/native_custody.py',
    protocol='research_loop/workers/r167_object_survival/fleet_generation2/source/gpu/orch_r167_object_survival_eval.py',
    queue='research_loop/workers/r167_object_survival/fleet_generation2/source/gpu/orch_r167_object_probe_queue.py')


def setup():
    scope, proposal = common.scope(HERE / 'PREPARATION_SCOPE.json', HERE / 'PROPOSAL.json')
    ledger = common.Ledger(PREP / 'global_ledger', dict(metadata=32*common.GIB, adapter=16*common.GIB,
        per_life=2*common.GIB, discovery=64*MIB), [life['life_id'] for life in proposal['lives']])
    return scope, proposal, ledger


def environment():
    return dict(PATH=os.environ.get('PATH', '/usr/bin:/bin'), HOME=os.environ['HOME'],
        PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')


def wrapper(node, operation, command, raw=b'', seconds=120):
    directory = PREP / 'wrapper_operations' / operation
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    common.write(directory / 'ONCE.json', dict(node=node, command_sha256=hashlib.sha256(command.encode()).hexdigest(),
        input_bytes=len(raw), started_unix=time.time(), no_retry=True))
    try:
        result = subprocess.run(['bash', str(REPO / WRAPPERS[node]), command], input=raw,
            capture_output=True, cwd=REPO, env=environment(), timeout=seconds)
        common.write(directory / 'stdout.private.bin', result.stdout)
        common.write(directory / 'stderr.private.bin', result.stderr)
        common.write(directory / 'RESULT.json', dict(returncode=result.returncode, observed_unix=time.time()))
        common.require(result.returncode == 0, 'wrapper_operation_failed_preserved_no_retry')
        return result.stdout
    except subprocess.TimeoutExpired as error:
        common.write(directory / 'UNCERTAIN.json', dict(status='WRAPPER_TIMEOUT_PRESERVED_NO_RETRY', observed_unix=time.time()))
        if error.stdout:
            common.write(directory / 'partial_stdout.private.bin', error.stdout)
        raise


def freeze():
    scope, proposal, ledger = setup()
    destination = PREP / 'source'
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    files = {'prep_common.py': HERE/'prep_common.py', 'source_prepare.py':HERE/'source_prepare.py',
        'native_custody.py':REPO/SOURCE_INPUTS['native_custody'],
        'gpu/orch_r167_object_survival_eval.py':REPO/SOURCE_INPUTS['protocol'],
        'gpu/orch_r167_object_probe_queue.py':REPO/SOURCE_INPUTS['queue']}
    old = common.bound(proposal['old_campaign_ref'])
    for target, path in files.items():
        if target in old['sources']:
            common.require(common.ref(path)['sha256'] == old['sources'][target], 'reuse_exact_frozen_CPU_primitive')
        common.write(destination/target, path.read_bytes())
    common.write(destination/'gpu/__init__.py', b'')
    common.write(PREP/'SOURCE_FREEZE.json', dict(status='PREPARATION_ONLY_SOURCE_FROZEN',
        files={str(path.relative_to(destination)):common.ref(path)['sha256'] for path in destination.rglob('*.py')},
        scope=common.ref(HERE/'PREPARATION_SCOPE.json'), proposal=common.ref(HERE/'PROPOSAL.json'),
        model_calls=0, frozen_unix=time.time()))
    print(json.dumps(dict(status='CPU_SOURCE_FROZEN_NO_REMOTE_ACTION', source_files=len(files)+1)))


def stage():
    scope, proposal, ledger = setup()
    frozen = common.read(PREP/'SOURCE_FREEZE.json')
    payload = {}
    for name, checksum in frozen['files'].items():
        path = PREP/'source'/name
        raw = path.read_bytes()
        common.require(hashlib.sha256(raw).hexdigest() == checksum, 'frozen_source_changed')
        payload['source/'+name] = base64.b64encode(raw).decode()
    for name in ('PREPARATION_SCOPE.json','PROPOSAL.json'):
        payload['control/'+name] = base64.b64encode((HERE/name).read_bytes()).decode()
    raw = common.canonical(payload)
    script = '''import base64,json,os,sys
from pathlib import Path
os.umask(0o077)
root=Path("/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1")
root.mkdir(mode=0o700,exist_ok=False)
payload=json.loads(sys.stdin.buffer.read(2097152))
for name,encoded in payload.items():
 target=root/name
 assert target.is_relative_to(root) and '..' not in Path(name).parts
 target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
 with target.open('xb') as stream: stream.write(base64.b64decode(encoded))
print(json.dumps(dict(status='PREPARATION_SOURCE_STAGED_NO_MODELS',files=len(payload))))
'''
    encoded = base64.b64encode(script.encode()).decode()
    command = f"python3 -B -c \"import base64;exec(base64.b64decode('{encoded}'))\""
    for node in ('a100','ovx2','ovx3','a40r'):
        ledger.reserve('stage:'+node, '_campaign','metadata',len(raw)+2*MIB,discovery=True)
        wrapper(node,'stage_'+node,command,raw)
        print(json.dumps(dict(node=node,status='SOURCE_STAGED_NO_MODELS')))


def remote_request(node, operation, action, request, seconds=180):
    raw = common.canonical(request)
    request_path = common.REMOTE_ROOT/'requests'/(operation+'.json')
    encoded = base64.b64encode(raw).decode()
    script = f'''import base64,os,sys
from pathlib import Path
os.umask(0o077)
path=Path({str(request_path)!r})
path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
with path.open('xb') as stream: stream.write(base64.b64decode({encoded!r}))
os.chdir({str(common.REMOTE_ROOT/'source')!r})
os.execve('/usr/bin/python3',['python3','-B','source_prepare.py',{action!r},'--request',str(path)],{{'PATH':'/usr/bin:/bin','HOME':os.environ['HOME'],'PYTHONPATH':{str(common.REMOTE_ROOT/'source')!r},'PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}})
'''
    stdout = wrapper(node,operation,'python3 -B -',script.encode(),seconds)
    return json.loads(stdout)


def discovery():
    scope, proposal, ledger = setup()
    old = common.bound(proposal['old_campaign_ref'])
    births = {life['life_id']:life['birth_plan'] for life in old['lives']}
    source_sha = common.read(PREP/'SOURCE_FREEZE.json')['files']['source_prepare.py']
    requests = []
    for node in ('a100','ovx2','ovx3','a40r'):
        lives = [dict(life,old_birth_plan=births.get(life['life_id'])) for life in proposal['lives'] if life['node']==node]
        ledger.reserve('discovery:'+node,'_campaign','metadata',8*MIB,discovery=True)
        request = dict(node=node,lives=lives,read_cap=7*MIB,source_sha256=source_sha)
        common.write(PREP/'requests'/('discovery_'+node+'.json'), request)
        requests.append((node,request))
    def run(item):
        node,request=item
        result=remote_request(node,'discovery_'+node,'discover',request)
        common.write(PREP/'discovery'/(node+'.json'),result)
        return dict(node=node,candidates=sum(row['status']=='METADATA_CANDIDATE_NOT_ENROLLED' for row in result['rows']),
            held=sum(row['status']!='METADATA_CANDIDATE_NOT_ENROLLED' for row in result['rows']),metadata_charged=result['bytes_charged'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run,requests):
            print(json.dumps(result))


def enrollment():
    scope, proposal, ledger = setup()
    lives={life['life_id']:life for life in proposal['lives']}
    entries=[]
    for node in ('a100','ovx2','ovx3','a40r'):
        for observation in common.read(PREP/'discovery'/(node+'.json'))['rows']:
            if observation['status']=='METADATA_CANDIDATE_NOT_ENROLLED':
                entries.append((node,observation))
    entries.sort(key=lambda entry:(not lives[entry[1]['life_id']]['prior_registered'],entry[1]['life_id']))
    requests={node:[] for node in ('a100','ovx2','ovx3','a40r')}
    for node,observation in entries:
        name=observation['life_id']
        try:
            metadata=ledger.reserve('enrollment_metadata:'+name,name,'metadata',observation['metadata_read_cap'])
            adapter=ledger.reserve('enrollment_adapter:'+name,name,'adapter',observation['adapter_read_cap'])
            allocation=common.write(PREP/'allocations'/(name+'.json'),dict(metadata=metadata,adapter=adapter,
                status='FULL_SOURCE_ENVELOPE_CHARGED_BEFORE_REMOTE_IO_NO_REFUND'))
            request=dict(life=lives[name],discovery=observation,metadata_read_cap=observation['metadata_read_cap'],
                adapter_read_cap=observation['adapter_read_cap'],allocation_ref=allocation,
                scope_ref=dict(path=str(common.REMOTE_ROOT/'control/PREPARATION_SCOPE.json'),sha256=common.ref(HERE/'PREPARATION_SCOPE.json')['sha256']),
                source_sha256=common.read(PREP/'SOURCE_FREEZE.json')['files']['source_prepare.py'])
            common.write(PREP/'requests'/('enroll_'+name+'.json'),request)
            requests[node].append(request)
        except ValueError as error:
            common.write(PREP/'enrollment'/(name+'.json'),dict(life_id=name,status='NEW_ALLOCATION_HELD',reason=str(error),model_calls=0))
    def run_node(item):
        node,node_requests=item
        results=[]
        for request in node_requests:
            name=request['life']['life_id']
            try:
                result=remote_request(node,'enroll_'+name,'enroll',request,seconds=180)
            except Exception as error:
                result=dict(life_id=name,status='ENROLLMENT_WRAPPER_UNCERTAIN_NO_RETRY',error_type=type(error).__name__,model_calls=0)
            common.write(PREP/'enrollment'/(name+'.json'),result)
            results.append(dict(life_id=name,status=result['status'],frontier=result.get('frontier'),reason=result.get('reason')))
        return results
    with ThreadPoolExecutor(max_workers=4) as pool:
        for results in pool.map(run_node,requests.items()):
            for result in results:
                print(json.dumps(result))


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','stage','discover','enroll'))
    action=parser.parse_args().action
    {'freeze':freeze,'stage':stage,'discover':discovery,'enroll':enrollment}[action]()


if __name__=='__main__':
    main()
