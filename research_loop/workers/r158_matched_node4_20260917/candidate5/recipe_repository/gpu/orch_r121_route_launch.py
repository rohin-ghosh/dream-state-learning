"""R119 independent route forks: immutable birth, original charges, strict admission."""

import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r111_parent_provider as hook
from gpu import orch_route_parent_campaign_run as campaign

require, read, sha, write = hook.require, hook.load, hook.file_sha, campaign.write
PLAN = 'R121_INDEPENDENT_PLAN_V2.json'
HARD = 1789596240
FINAL = 1789538400
COMMON = Path('/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1')
CHECKPOINT_SHA = '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'
OPTIMIZER_SHA = '2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5'


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def bound(item):
    require(sha(item['path']) == item['sha256'], 'immutable_reference')
    return read(item['path'])


def ledger_prefix(root, plan):
    data = (root/'RESERVATIONS.jsonl').read_bytes()
    birth = plan['inherited_ledger']
    require(hashlib.sha256(data[:birth['bytes']]).hexdigest() == birth['sha256'], 'old_charges_unchanged')
    counts = Counter(json.loads(line)['kind'] for line in data.splitlines() if line.strip())
    require(counts['NATIVE'] <= plan['bounds']['native_calls'] and
            counts['PARENT'] <= plan['bounds']['parent_calls'], 'absolute_original_quotas')
    return dict(counts)


def prepare(root, source):
    from gpu import orch_r118_route_parallel_boundary as prior
    root, source = Path(root).resolve(), Path(source).resolve()
    require(not (root/PLAN).exists(), 'never_overwrite_independent_plan')
    old = read(root/'R118_PARALLEL_PLAN.json')
    state = read(COMMON/'STATE.json')
    committed = read(COMMON/'generation_000000/sleep/COMPLETE.json')
    require(state['generation'] == 1 and committed['state'] == state, 'actual_committed_gen1')
    parent = state['checkpoint']
    require(sha(parent['path']) == parent['path_sha256'] == CHECKPOINT_SHA and
            sha(parent['optimizer_path']) == parent['optimizer_path_sha256'] == OPTIMIZER_SHA,
            'genuine_gen1_checkpoint_optimizer')
    original = read(parent['path'])
    require(original['complete'] and original['optimizer_rng_sha256'] == OPTIMIZER_SHA, 'atomic_checkpoint')
    from organism_v6.orch_guided_bridge import AdapterIdentity
    AdapterIdentity.from_document(original['adapter']).verify()
    birth = root/'R121_BIRTH'
    birth.mkdir(exist_ok=False)
    shutil.copytree(original['adapter']['path'], birth/'adapter')
    shutil.copy2(parent['optimizer_path'], birth/'optimizer_rng.pt')
    fork = dict(original, adapter=dict(original['adapter'], path=str(birth/'adapter')),
                independent_fork_of=parent, fork_created_unix=time.time())
    write(birth/'CHECKPOINT.json', fork)
    reference_checkpoint = dict(path=str(birth/'CHECKPOINT.json'), path_sha256=sha(birth/'CHECKPOINT.json'),
        optimizer_path=str(birth/'optimizer_rng.pt'), optimizer_path_sha256=sha(birth/'optimizer_rng.pt'))
    boundary = bound(bound(old['route_boundary_release'])['boundary'])
    next_cycle = boundary['next_cycle']
    require(not (root/f'cycle_{next_cycle:04d}').exists(), 'settled_cursor_no_replay')
    ledger = (root/'RESERVATIONS.jsonl').read_bytes()
    history, seen = [], set()
    for path in sorted(root.glob('cycle_*/ROWS.json')):
        if not (path.parent/'checkpoint/CHECKPOINT.json').exists():
            continue
        rejected = set()
        encoding = path.parent/'ENCODING.json'
        if encoding.exists():
            rejected = {item['source'] for item in read(encoding).get('rejected', [])}
        for row in read(path):
            if row['source_call_sha256'] not in seen | rejected:
                require(sha(row['source_call_path']) == row['source_call_sha256'], 'actual_rehearsal_capture')
                seen.add(row['source_call_sha256'])
                history.append(row)
    write(root/'R121_HISTORY.json', history)
    plan = {key: value for key, value in old.items() if key not in (
        'shared_learner', 'parallel_control', 'parallel_source', 'parallel_stage', 'lease_continuation')}
    plan.update(schema='R119_INDEPENDENT_ROUTE_GEN1_FORK', branch={0:'F1',4:'A1'}[old['physical']],
        mode='EXPLICIT_INDEPENDENT_FORK_OF_COMMITTED_GEN1', fork_checkpoint=reference_checkpoint,
        parent_checkpoint=parent, inherited_state=reference(COMMON/'STATE.json'), next_cycle=next_cycle,
        inherited_sleeps=max(read(path)['sleeps'] for path in root.glob('cycle_*/checkpoint/CHECKPOINT.json')),
        inherited_metrics={key:state[key] for key in ('optimizer_steps','child_token_exposures','anchor_token_exposures')},
        inherited_ledger=dict(bytes=len(ledger),sha256=hashlib.sha256(ledger).hexdigest()),
        history=reference(root/'R121_HISTORY.json'), parent_nonblocking=True, parent_delivery_seconds=600,
        parent_wait_seconds=0, prior_parent_timing_preserved=True, parent_pending_limit=1,
        parent_effort_requested='low', parent_intervention_output_budget=512,
        final_readouts=['2026-09-16T06:00:00Z'], morning_cut_unix=FINAL,
        new_final_scope=dict(not_before_unix=FINAL, native_calls=48, parent_calls=0, optimizer_steps=0,
            distinct_from='2026-09-15T17:00:00Z', scheduling='FIRST_SAFE_BOUNDARY_AT_OR_AFTER_DUE'),
        source_root=str(source), source_files={str(path):sha(path) for path in sorted(source.rglob('*.py'))},
        no_shared_runtime_dependency=True, authority='DIRECT_ROHIN119_INDEPENDENT_FORK')
    plan['cadence'] = 'episode'
    plan['bounds']['hard_end_unix'] = HARD
    write(root/PLAN, plan)
    write(birth/'PROVENANCE.json', dict(plan=reference(root/PLAN), ancestor=parent,
        inherited_ledger=plan['inherited_ledger'], carry=reference(root/'OWN_CARRY.json'),
        inherited_metrics=plan['inherited_metrics'], next_cycle=next_cycle, explicit_fork=True))
    return dict(root=str(root),plan=reference(root/PLAN),fork=reference_checkpoint,
                next_cycle=next_cycle,counts=ledger_prefix(root,plan))


def verify_plan(root, gpu=False):
    from gpu import orch_r121_route_independent as run
    root = Path(root)
    plan = read(root/PLAN)
    require(plan['schema']=='R119_INDEPENDENT_ROUTE_GEN1_FORK' and not plan.get('shared_learner'), 'independent_only')
    require(plan['physical'] in (0,4) and plan['uuid']==run.UUIDS[plan['physical']], 'own_UUID')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest()==run.HOST_SHA, 'hashed_host_binding')
    require(time.time()<plan['bounds']['hard_end_unix']<=HARD and
        HARD<=plan['bounds']['lease_end_unix']-21600, 'original_lease_margin')
    require(plan['anchor_lambda']==.25 and plan['anchor_count']==42 and plan['episodes_per_sleep']==2,
            'sleep_invariants')
    require(plan['parent_nonblocking'] and plan['parent_wait_seconds']==0, 'no_parent_wait')
    require(sha(plan['fork_checkpoint']['path'])==plan['fork_checkpoint']['path_sha256'] and
        sha(plan['fork_checkpoint']['optimizer_path'])==OPTIMIZER_SHA, 'local_exact_fork')
    require(sha(plan['history']['path'])==plan['history']['sha256'], 'historical_rows_frozen')
    for path, expected in plan['source_files'].items():
        require(sha(path)==expected, 'immutable_source:'+str(Path(path).name))
    ledger_prefix(root,plan)
    if gpu:
        require(os.environ.get('CUDA_VISIBLE_DEVICES')==plan['uuid'], 'native_exact_UUID')
    return plan


def scan(root):
    from gpu import orch_r118_route_concurrent_admission as proof
    root = Path(root)
    plan = verify_plan(root)
    source = Path(__file__).resolve().parents[1]
    dependencies = {key:reference(source/'gpu'/name) for key,name in dict(
        argv='orch_math_feedback_uptake_r118_argv_admission.py',
        math='orch_math_feedback_uptake_r118_preinfer.py',
        transient='orch_admission_transient_exit.py').items()}
    directory = root/'R121_ADMISSION'
    directory.mkdir(exist_ok=True)
    request = dict(root=str(root), attempt_directory=str(directory), dependencies=dependencies)
    def own_window(unused):
        require(time.time()<plan['bounds']['hard_end_unix'], 'lease_admission_window')
    function = FunctionType(proof.scan.__code__,dict(proof.scan.__globals__,validate_window=own_window),
        'independent_same_combined_proof',proof.scan.__defaults__)
    return function(request, SimpleNamespace(verify_plan=verify_plan))


def launch(root, python):
    root=Path(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'CPU_launcher_empty_CVD')
    plan=verify_plan(root)
    with (root/'R121_LAUNCH.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(not (root/'R121_LAUNCH_ATTEMPT_V2.json').exists(), 'one_attempt_preserve_failures')
        write(root/'R121_LAUNCH_ATTEMPT_V2.json',dict(started_unix=time.time(),plan=reference(root/PLAN),counts=ledger_prefix(root,plan)))
        command=['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+plan['source_root'],'python3','-B','-m','gpu.orch_r121_route_launch','scan','--root',str(root)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=120)
        if result.returncode:
            write(root/'R121_ADMISSION_FAILED_V2.json',dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
            raise ValueError('privileged_scan_failed_preserved')
        report=json.loads(result.stdout)
        write(root/'R121_ADMISSION_RESULT.json',report)
        require(report['clear'] and time.time()-report['scanned_unix']<30,'strict_fresh_clear')
        environment={key:value for key,value in os.environ.items() if not key.startswith(('ORCH_R119_LEASE_CLOCK','R118_PARALLEL'))}
        environment.update(CUDA_VISIBLE_DEVICES=plan['uuid'],PYTHONPATH=plan['source_root'],
            HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false')
        command=['timeout','--signal=TERM','--kill-after=30',str(int(plan['bounds']['hard_end_unix']-time.time())),
                 python,'-B','-m','gpu.orch_r121_route_independent','run','--root',str(root)]
        with (root/'R121_NATIVE.log').open('x') as stream:
            process=subprocess.Popen(command,env=environment,cwd=plan['source_root'],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        receipt=dict(pid=process.pid,started_unix=time.time(),command=command,physical=plan['physical'],uuid=plan['uuid'],
            plan=reference(root/PLAN),admission=reference(root/'R121_ADMISSION_RESULT.json'),mode=plan['mode'],native_actor_pending=True)
        write(root/'R121_LAUNCH.json',receipt)
        return receipt


def final_status(root,plan):
    root=Path(root)
    if time.time()<FINAL or (root/'R121_NEW_FINAL_ATTEMPT.json').exists():
        return
    from gpu import orch_r121_route_independent as run
    checkpoints=sorted(root.glob('cycle_*/checkpoint/CHECKPOINT.json'))
    selected=checkpoints[-1]
    directory=root/'R121_FINAL_20260916_0600'
    directory.mkdir(exist_ok=False)
    for name in ('COHORT.json','SEALED_FINAL.json',PLAN):
        shutil.copy2(root/name,directory/name)
    write(root/'R121_NEW_FINAL_ATTEMPT.json',dict(scheduled_unix=FINAL,started_unix=time.time(),
        checkpoint=reference(selected),new_distinct_scope=True,original_final_untouched=True))
    run.run_readout(root, read(selected)['sleeps'], selected, plan,scope='final')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('prepare','verify','scan','launch'))
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    if args.phase=='prepare': result=prepare(args.root,args.source)
    elif args.phase=='scan': result=scan(args.root)
    elif args.phase=='launch': result=launch(args.root,sys.executable)
    else:
        plan=verify_plan(args.root)
        result=dict(verified=True,physical=plan['physical'],counts=ledger_prefix(args.root,plan))
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
