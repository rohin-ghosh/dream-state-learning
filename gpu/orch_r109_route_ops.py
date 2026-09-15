"""Source-only deployment and compact receipts for owned resident route lives."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

from gpu import orch_r109_route_run as run
from gpu.orch_r109_route_broker import Store
from organism_v6 import orch_r109_route as policy


REPOSITORY=Path(__file__).resolve().parents[1]
ANALYSIS=REPOSITORY/'research_notes/analysis/orch_r109_route_20260915_attempt1'
ROOTS={lane:Path(run.ROOT_PREFIX+lane+('_attempt2' if lane in ('node1_7','a100_2') else '_attempt3')) for lane in policy.LANES}
RUN_MODULE='gpu.orch_r109_route_run'
BROKER_MODULE='gpu.orch_r109_route_broker'
SCAN_MODULE='gpu.orch_r109_route_scan'
TEST_MODULE='tests.test_orch_r109_route'


def closure():
    queue=list(REPOSITORY.glob('gpu/orch_r109_route*.py'))+[REPOSITORY/'organism_v6/orch_r109_route.py',
        REPOSITORY/(TEST_MODULE.replace('.','/')+'.py')]
    seen=set()
    while queue:
        path=queue.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        if path.suffix != '.py':
            continue
        for parent in path.relative_to(REPOSITORY).parents:
            candidate=REPOSITORY/parent/'__init__.py'
            if candidate.is_file() and candidate not in seen:
                queue.append(candidate)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.endswith(('.sh','.py')):
                for candidate in (path.parent/node.value,REPOSITORY/node.value):
                    if candidate.is_file() and candidate not in seen:
                        queue.append(candidate)
            names=[]
            if isinstance(node,ast.Import):
                names=[value.name for value in node.names]
            elif isinstance(node,ast.ImportFrom):
                base=node.module or ''
                if node.level:
                    package=path.relative_to(REPOSITORY).parent.parts
                    base='.'.join(package[:len(package)-node.level+1]+tuple(base.split('.') if base else []))
                names=[base]+[base+'.'+value.name for value in node.names]
            for name in names:
                target=REPOSITORY/Path(*name.split('.'))
                for candidate in (target.with_suffix('.py'),target/'__init__.py'):
                    if candidate.is_file() and candidate not in seen:
                        queue.append(candidate)
    seen.add(REPOSITORY/policy.PRINCIPLES_PATH)
    return {str(path.relative_to(REPOSITORY)):run.sha(path) for path in sorted(seen)}


def exclusions():
    from gpu import orch_r107_route_parent_r108_registry as registry
    local=registry.collect([REPOSITORY/'research_notes/analysis'])
    script=(REPOSITORY/'gpu/orch_r107_route_parent_r108_registry.py').read_text()
    def collect(host):
        wrapper={'node2':'gpu/ovx_ssh.sh',**{key:value['wrapper'] for key,value in policy.HOSTS.items()}}[host]
        result=subprocess.run(['bash',str(REPOSITORY/wrapper),'python3 - /localhome/local-rohing /tmp'],
            input=script,capture_output=True,text=True,timeout=180,check=True)
        return host,json.loads(result.stdout)
    with ThreadPoolExecutor(max_workers=4) as pool:
        native=dict(pool.map(collect,['node1','node2','node3','a100']))
    identifiers=set(local['identifiers'])
    sources={'repo':local}
    sources.update(native)
    for value in native.values():
        identifiers.update(value['identifiers'])
    result=dict(identifiers=sorted(identifiers),source_snapshots={key:dict(source_files=value['source_files'],
        observed_unix=value['observed_unix'],identifiers_sha256=policy.digest(value['identifiers'])) for key,value in sources.items()},raw_embedded=False)
    ANALYSIS.mkdir(parents=True,exist_ok=True)
    run.write(ANALYSIS/'EXCLUSIONS.json',result)
    print(json.dumps(dict(excluded_identifiers=len(identifiers),snapshots=list(sources))))


def deploy(lane):
    root=ROOTS[lane]
    store=Store(REPOSITORY,root,lane)
    sources=closure()
    target=ANALYSIS/lane
    target.mkdir(parents=True,exist_ok=True)
    run.write(target/'SOURCE_SHA256.json',sources)
    provider_files={name:digest for name,digest in sources.items() if name in {
        'gpu/orch_r109_route_broker.py','organism_v6/orch_r109_route.py',policy.PRINCIPLES_PATH,
        'gpu/orch_math_feedback_uptake_base_broker.py','gpu/orch_math_pipeline_l2_parent_node.py',
        'gpu/orch_math_pipeline_l2_parent_strong.py','gpu/orch_math_pipeline_l2_parent.py',
        'gpu/orch_r107_route_parent_long_protocol.py',BROKER_MODULE.replace('.','/')+'.py',
        str(Path(policy.__file__).relative_to(REPOSITORY))}}
    run.write(target/'PROVIDER_FILES.json',provider_files)
    run.write(target/'PRIOR_LEDGERS.json',dict(no_quota_reset=True,prior_roots_read_only=[
        '/localhome/local-rohing/orch_r107_route_parent_20260915_attempt1',
        '/localhome/local-rohing/orch_r107_route_parent_20260915_attempt2',
        '/localhome/local-rohing/orch_r107_route_parent_20260915_attempt3_long'],
        new_native_cap=policy.NATIVE_CAP,new_parent_cap=policy.parent_cap(lane),lane=lane))
    store.shell('test ! -e '+shlex.quote(str(root))+' && mkdir -p '+shlex.quote(str(root/'source')))
    groups={}
    for relative in sources:
        groups.setdefault(str(Path(relative).parent),[]).append(REPOSITORY/relative)
    for parent,paths in groups.items():
        destination=root/'source'/parent
        store.shell('mkdir -p '+shlex.quote(str(destination)))
        for offset in range(0,len(paths),80):
            subprocess.run(['bash',str(REPOSITORY/store.host['scp'])]+[str(path) for path in paths[offset:offset+80]]+
                ['NODE:'+str(destination)+'/'],capture_output=True,text=True,timeout=120,check=True)
    for name in ('SOURCE_SHA256.json','PROVIDER_FILES.json','PRIOR_LEDGERS.json'):
        store.copy(target/name,'NODE:'+str(root/name))
    store.copy(ANALYSIS/'EXCLUSIONS.json','NODE:'+str(root/'EXCLUSIONS.json'))
    if policy.LANES[lane]['host']=='node3':
        from gpu import orch_oracle_repair_guard as prior_guard
        run.write(target/'LEASE.json',dict(verified=True,lease_end_unix=prior_guard.LEASE_CUTOFF,
            source_relative='gpu/orch_oracle_repair_guard.py',source_sha256=run.sha(Path(prior_guard.__file__)),
            meaning='Conservative inherited existing node3 guard cutoff, not an extension or new actual expiry claim.'))
        store.copy(target/'LEASE.json','NODE:'+str(root/'LEASE.json'))
    command='cd '+shlex.quote(str(root/'source'))+' && export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH='+shlex.quote(str(root/'source'))
    command+=' && '+run.common.PYTHON+' -B -m unittest '+TEST_MODULE+' -q > '+shlex.quote(str(root/'CPU_TESTS.log'))+' 2>&1'
    command+=' && '+run.common.PYTHON+' -B -c '+shlex.quote("from pathlib import Path; import re; from gpu.orch_r109_route_run import write,sha; log=Path("+repr(str(root/'CPU_TESTS.log'))+"); write(Path("+repr(str(root/'CPU_TESTS.json'))+"),dict(passed=True,test_count=int(re.search(r'Ran (\\d+) tests',log.read_text())[1]),log_sha256=sha(log)))")
    command+=' && '+run.common.PYTHON+' -B -m '+RUN_MODULE+' prepare --root '+str(root)+' --lane '+lane
    launch='nohup bash -c '+shlex.quote(command)+' > '+shlex.quote(str(root/'PREPARE.log'))+' 2>&1 < /dev/null & echo $!'
    pid=int(store.shell(launch).stdout.strip())
    run.write(target/'DEPLOY_COMPACT.json',dict(lane=lane,root=str(root),prepare_pid=pid,source_files=len(sources),
        source_manifest_sha256=run.sha(target/'SOURCE_SHA256.json'),created_utc=datetime.now(timezone.utc).isoformat(),
        native_launched=False,raw_embedded=False))
    print(json.dumps(dict(lane=lane,prepare_pid=pid,source_files=len(sources))))


def status(lane):
    root=ROOTS[lane]
    store=Store(REPOSITORY,root,lane)
    script="""import json,time,hashlib
from pathlib import Path
root=Path(ROOT)
campaign=root/('campaign_'+LANE)
result=dict(lane=LANE,observed_unix=time.time(),raw_embedded=False)
for name in ('READY.json','LAUNCH.json','ACTOR_READY.json','STATUS.json','FAILED.json','GUARDIAN_FAILED.json','COMPLETE.json','TERMINAL.json'):
 path=campaign/name
 if path.exists():
  value=json.loads(path.read_text())
  result[name]={key:value[key] for key in ('pid','lane','uuid','started_unix','loaded_unix','phase','native_completed','parent_completed','train_segments','train_episodes','held_episodes','sleeps','optimizer_updates','triples','semantic_verified_changes','error','reason','hard_deadline_unix','native_cap','parent_cap','base_sha256','principles_sha256') if key in value}
  result[name]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
for pattern,key in (('native/CALL_*.json','first_native'),('PARENT_*.json','first_parent')):
 for path in sorted(campaign.glob(pattern)):
  value=json.loads(path.read_text())
  if key=='first_native' and value.get('status')!='COMPLETE': continue
  result[key]={name:value[name] for name in ('started_unix','finished_unix','observed_unix','response_sha256','principles_sha256') if name in value}
  result[key].update(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  if 'response' in value: result[key].update(tokens=len(value['response']['token_ids']),input_truncated=value['response']['input_truncated'])
  break
print(json.dumps(result))
""".replace('ROOT',repr(str(root))).replace('LANE',repr(lane))
    value=json.loads(store.shell('python3 -c '+shlex.quote(script)).stdout)
    stamp=datetime.now(timezone.utc).strftime('%H%M%S')
    run.write(ANALYSIS/lane/('STATUS_'+stamp+'.json'),value)
    print(json.dumps(value))


def launch(lane):
    policy.require(bool(os.environ.get('NVIDIA_API_KEY')),'existing_private_parent_environment_required')
    root=ROOTS[lane]
    store=Store(REPOSITORY,root,lane)
    campaign=root/('campaign_'+lane)
    attempt=root.name.rsplit('_',1)[1]
    target=ANALYSIS/lane/attempt
    target.mkdir(parents=True,exist_ok=True)
    if lane in ('a100_3','a100_6') and attempt=='attempt3':
        predecessor=Path(str(root).replace('_attempt3','_attempt2'))
        prior_campaign=predecessor/('campaign_'+lane)
        policy.require(not store.exists(prior_campaign/'LAUNCH.json'),'prior_no_native_launch_required')
        terminal=json.loads(store.shell('cat '+shlex.quote(str(prior_campaign/'TERMINAL.json'))).stdout)
        policy.require(terminal['status']=='FAILED','failed_initial_admission_only')
        policy.require(not store.exists(predecessor/'RESERVATIONS.jsonl'),'zero_consumed_prior_segment')
        run.write(target/'PREDECESSOR_COMPACT.json',dict(root=str(predecessor),terminal=terminal,
            terminal_sha256=store.shell('sha256sum '+shlex.quote(str(prior_campaign/'TERMINAL.json'))).stdout.split()[0],
            native_calls=0,parent_calls=0,unused_same_segment_replaced=True))
    if lane in ('a100_1','a100_5'):
        predecessor=Path('/localhome/local-rohing/orch_r107_route_parent_20260915_attempt3_long')
        prior_campaign=predecessor/('campaign_route_parent_'+lane[-1])
        terminal=json.loads(store.shell('cat '+shlex.quote(str(prior_campaign/'TERMINAL.json'))).stdout)
        policy.require(terminal['status']=='COMPLETE' and store.exists(prior_campaign/'RELEASE.json'),'natural_complete_release_required')
        previous=json.loads(store.shell('cat '+shlex.quote(str(prior_campaign/'LAUNCH.json'))).stdout)
        policy.require(previous['uuid']==policy.LANES[lane]['uuid'],'prior_exact_uuid')
        policy.require(store.shell('test ! -d /proc/'+str(previous['pid']),check=False).returncode==0,'prior_native_absent')
        run.write(target/'PREDECESSOR_COMPACT.json',dict(root=str(predecessor),terminal=terminal,
            terminal_sha256=store.shell('sha256sum '+shlex.quote(str(prior_campaign/'TERMINAL.json'))).stdout.split()[0],
            prior_launch=previous,old_ledger_unchanged=True,natural_completion_only=True))
    ready=json.loads(store.shell('cat '+shlex.quote(str(campaign/'READY.json'))).stdout)
    ready_sha=store.shell('sha256sum '+shlex.quote(str(campaign/'READY.json'))).stdout.split()[0]
    policy.require(ready['principles_sha256']==policy.PRINCIPLES_SHA and ready['lane']==lane,'exact_ready')
    board=(REPOSITORY/'research_loop/BOARD.md').read_text()
    policy.require('R109 overnight allocation' in board and 'Poincare' in board,'published_r109_board')
    entry=policy.LANES[lane]
    tests=json.loads(store.shell('cat '+shlex.quote(str(root/'CPU_TESTS.json'))).stdout)
    dated=datetime.now(timezone.utc).isoformat()
    allocation=(f'[Builder / Poincare] {dated} R110_ROUTE own preGPU: existing published R109 BOARD09:02 allocation; '
        f'lane={lane}; wrapper={store.host["wrapper"]}; physical={entry["physical"]}; UUID={entry["uuid"]}; '
        f'root={root}; nativeCPU{tests["test_count"]}testsPASS+frozenBASEtensor/config/noPEFT checked; '
        f'principles={policy.PRINCIPLES_SHA}; READY={ready_sha}; '
        f'NEW segment explicit +{ready["native_cap"]}native/+{ready["parent_cap"]}Astra maximum; '
        f'for A100attempt3 this replaces zero-call failedadmissionattempt2, not another quota addition; '
        f'256cycles/512sequentialTRAINepisodes/8GPUh maximum; absolute2026-09-15T17:02:00UTC '
        f'and earlier verified lease6hmargin; dispatchend16:60-equivalent17:00UTC; '
        f'cadence={entry["cadence"]}, unit=completedTRAINnative response not hidden thought; '
        f'preEVERYsleep {ready["reflection_turns"]}turn parent-child puremetacognition conversation, no padding; '
        f'outcomesbackground/no failuregate; all triples retained UNKNOWNpendingaudit; '
        f'learned={entry["learned"]}, real inheritedFULL8932LoRA/AdamW updates only wherelearned, BASE noadapter; '
        f'initialfreshprivileged fullUUID/proc/CVD/kernelminor admission required; residentcycles no repeatedadmission; '
        f'oldledgers/raw/activeA1001and5 preserved; noforeignsignals/noL2toL1feed; allrawnodeonly.\n')
    allocation=allocation.replace('dispatchend16:60-equivalent17:00UTC','dispatchend17:00UTC')
    patch_text='*** Begin Patch\n*** Add File: '+str((target/'ALLOCATION.md').relative_to(REPOSITORY))+'\n+'+allocation.rstrip()+'\n*** End Patch\n'
    subprocess.run(['apply_patch',patch_text],cwd=REPOSITORY,check=True,capture_output=True,text=True)
    for relative in ('research_loop/COORDINATION.md','research_loop/workers/R109_ROUTE.md'):
        path=REPOSITORY/relative
        with path.open('a') as stream:
            fcntl_module=__import__('fcntl')
            fcntl_module.flock(stream,fcntl_module.LOCK_EX)
            stream.write('\n'+allocation)
    store.copy(target/'ALLOCATION.md','NODE:'+str(root/'ALLOCATION.md'))
    publication=dict(ready_sha256=ready_sha,allocation_sha256=run.sha(target/'ALLOCATION.md'),
        dated_builder_publication=dated,board_sha256=run.sha(REPOSITORY/'research_loop/BOARD.md'))
    run.write(target/'PUBLICATION.json',publication)
    store.copy(target/'PUBLICATION.json','NODE:'+str(campaign/'PUBLICATION.json'))
    store.shell('cd '+shlex.quote(str(root/'source'))+' && sudo -n env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH='+
        shlex.quote(str(root/'source'))+' python3 -B -m '+SCAN_MODULE+' service --lane '+lane+' --service '+str(root/'SERVICE_IDENTITY.json'))
    command='cd '+shlex.quote(str(root/'source'))+' && exec env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH='+shlex.quote(str(root/'source'))+' '+run.common.PYTHON+' -B -m '+RUN_MODULE+' guard --root '+str(root)+' --lane '+lane
    guard_pid=int(store.shell('nohup bash -c '+shlex.quote(command)+' > '+shlex.quote(str(campaign/'guardian.log'))+' 2>&1 < /dev/null & echo $!').stdout.strip())
    buffer=Path('/tmp/orch_r109_route_'+lane+'_broker_'+root.name.rsplit('_',1)[1])
    receipts=target/'BROKER_COMPACT'
    with Path(str(buffer)+'.log').open('x') as log:
        broker_process=subprocess.Popen(['python3','-B','-m',BROKER_MODULE,'--repository',str(REPOSITORY),
            '--root',str(root),'--lane',lane,'--buffer',str(buffer),'--receipts',str(receipts)],cwd=REPOSITORY,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True,
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    run.write(target/'DISPATCH_COMPACT.json',dict(guardian_pid=guard_pid,broker_pid=broker_process.pid,lane=lane,
        dispatched_utc=datetime.now(timezone.utc).isoformat(),ready_sha256=ready_sha,actual_gpu_launch_unverified=True))
    print(json.dumps(dict(lane=lane,guardian_pid=guard_pid,broker_pid=broker_process.pid,phase='STRICT_ADMISSION_PENDING')))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('exclusions','deploy','status','launch'))
    parser.add_argument('--lane',choices=policy.LANES)
    args=parser.parse_args()
    exclusions() if args.phase=='exclusions' else globals()[args.phase](args.lane)
