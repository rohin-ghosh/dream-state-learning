"""Lease-bounded continuation of the existing R113 route lineages."""

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace


VERSION = 'lease_r120_v2'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    return dict(path=str(path),sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2)


def directory(root, lane):
    return root / VERSION / ('campaign_' + lane)


def resume_cycle(rows, saved_cycle, limit):
    next_cycle = max([saved_cycle] + [row.get('cycle',0) for row in rows]) + 1
    require(next_cycle <= limit, 'existing_unused_cohort_exhausted')
    return next_cycle


def lease_bounds(ready, now):
    hard = ready['lease_end_unix'] - ready['lease_margin_seconds']
    require(now + 300 < hard, 'actual_lease_margin')
    return dict(hard_deadline_unix=hard,native_deadline_unix=hard-120,
                continuation_started_unix=now,max_gpu_hours=(hard-now)/3600)


def load_runtime(root, lane, broker_source=None):
    prior = root / 'recovery_r113_v1' / ('campaign_' + lane)
    if broker_source:
        source = Path(broker_source) / 'gpu/orch_r111_route_recovery.py'
    else:
        recipe = read(prior / 'RECOVERY.json')
        source = next(Path(path) for path in recipe['source_files'] if path.endswith('/orch_r111_route_recovery.py'))
        require(sha(source) == recipe['source_files'][str(source)], 'frozen_recovery_source')
    sys.path.insert(0,str(source.parents[1]))
    import gpu
    frozen_package = str(source.parent)
    if frozen_package not in gpu.__path__:
        gpu.__path__ = list(gpu.__path__) + [frozen_package]
    spec = importlib.util.spec_from_file_location('frozen_route_recovery',source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    relocation = root / VERSION / 'RELOCATION.json'
    if relocation.exists():
        apply_relocation(module,read(relocation),lane)
    return module


def apply_relocation(runtime, relocation, lane):
    require(relocation['lane'] == lane and relocation['target_physical'] in (0,1,2,3),
            'exact_allocated_a40r_route_slot')
    require(relocation['target_wrapper'] == 'gpu/a40r_ssh.sh' and
            relocation['target_uuid'].startswith('GPU-'),'actual_destination_binding')
    policy=runtime.old.policy
    policy.LANES[lane]=dict(policy.LANES[lane],host='node1',physical=relocation['target_physical'],
                            uuid=relocation['target_uuid'])
    policy.DEVICES[lane]=relocation['target_uuid']


def prepare(root, lane, runtime):
    runtime.old.verify(root,lane)
    prior = root / 'recovery_r113_v1' / ('campaign_' + lane)
    status = read(prior / 'STATUS.json')
    require(not Path('/proc',str(status['pid'])).exists(), 'prior_native_exited')
    checkpoints = sorted(prior.glob('CHECKPOINT_C*.json'),key=lambda path:int(path.stem.split('C')[-1]))
    require(bool(checkpoints),'actual_prior_checkpoint')
    checkpoint_path = checkpoints[-1]
    checkpoint = read(checkpoint_path)
    saved_cycle = int(checkpoint_path.stem.split('C')[-1])
    rows = [json.loads(line) for line in (root / 'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]
    ready = read(prior / 'READY.json')
    relocation_path=root / VERSION / 'RELOCATION.json'
    if relocation_path.exists():
        relocation=read(relocation_path)
        ready['lease_end_unix']=relocation['target_lease_end_unix']
        ready['lease_margin_seconds']=relocation['lease_margin_seconds']
    first_cycle = resume_cycle(rows,saved_cycle,ready['cycles'])
    counters = {key:status[key] for key in ('native_completed','parent_completed','train_segments',
        'train_episodes','held_episodes','sleeps','optimizer_updates','triples','semantic_verified_changes')}
    counters['parent_missing'] = status.get('parent_missing',0)
    old_recipe = read(prior / 'RECOVERY.json')
    old_rows = list(old_recipe['old_rows'])
    pending_rows = []
    if ready['learned']:
        require(checkpoint.get('adapter') is not None,'learned_checkpoint_required')
        runtime.seed.validate(checkpoint['adapter'])
        for path in sorted((prior / 'native').glob('CALL_*.json')):
            call = read(path)
            if call.get('status') != 'COMPLETE' or call.get('purpose','').startswith('held'):
                continue
            row = runtime.old.native_engine.replay_row(call,path,runtime.old.sha(path))
            (old_rows if call.get('cycle',0) <= saved_cycle else pending_rows).append(row)
    output = directory(root,lane)
    output.mkdir(parents=True,exist_ok=False)
    (output / 'parent_queue').mkdir()
    ready.update(lease_bounds(ready,time.time()))
    ready['continuation_authority'] = 'User17:10 report-cut-not-stop; until user stop or verified lease margin'
    write(output / 'READY.json',ready)
    recipe = dict(first_cycle=first_cycle,counters=counters,own_memory=checkpoint['own_memory'],
        document=checkpoint.get('adapter'),old_rows=old_rows,pending_rows=pending_rows,
        uuid=runtime.old.policy.allocation(lane),prior_root=str(prior),checkpoint=reference(checkpoint_path),
        old_reservations=reference(root / 'RESERVATIONS.jsonl'),original_pid=status['pid'],
        source=reference(Path(__file__).resolve()),recovery_source=reference(Path(runtime.__file__)),
        previous_recipe=reference(prior / 'RECOVERY.json'),lease_end_unix=ready['lease_end_unix'],
        partial_cycle_preserved_not_regenerated=True,no_ledger_reset=True)
    if relocation_path.exists():recipe['relocation']=reference(relocation_path)
    write(output / 'RECOVERY.json',recipe)
    return dict(lane=lane,root=str(root),ready=reference(output / 'READY.json'),
        recipe=reference(output / 'RECOVERY.json'),first_cycle=first_cycle,counters=counters,
        checkpoint=recipe['checkpoint'],hard_deadline_unix=ready['hard_deadline_unix'],
        native_cap=ready['native_cap'],parent_cap=ready['parent_cap'],learned=ready['learned'])


def bind(root,lane,runtime):
    prior_sleep = runtime.sleep

    def verify(own_root,own_lane):
        runtime.old.verify(own_root,own_lane)
        recipe = read(directory(own_root,own_lane) / 'RECOVERY.json')
        require(recipe['source'] == reference(Path(__file__).resolve()),'continuation_source')
        require(recipe['recovery_source'] == reference(Path(runtime.__file__)),'recovery_source_unchanged')
        require(sha(recipe['checkpoint']['path']) == recipe['checkpoint']['sha256'],'saved_checkpoint_unchanged')
        if 'relocation' in recipe:
            require(reference(recipe['relocation']['path']) == recipe['relocation'],'relocation_unchanged')
        return recipe

    def restore(own_root,own_lane,counters,state):
        recipe = verify(own_root,own_lane)
        counters.update(recipe['counters'])
        state.update(memory=recipe['own_memory'],old_rows=recipe['old_rows'])

    pending = list(read(directory(root,lane) / 'RECOVERY.json')['pending_rows'])

    def sleep(loaded,document,rows,old_rows,anchors,output,deadline,check,writer,hasher):
        result = prior_sleep(loaded,document,pending+rows,old_rows,anchors,output,deadline,check,writer,hasher)
        old_rows.extend(pending)
        pending.clear()
        return result

    runtime.directory=directory
    runtime.verify=verify
    runtime.state=restore
    runtime.sleep=sleep
    return runtime


def guard(root,lane,runtime):
    source = inspect.getsource(runtime.old.guard)
    source = runtime.replace_once(source,"campaign=root/('campaign_'+lane)","campaign=recovery_directory(root,lane)")
    source = runtime.replace_once(source,"'gpu.orch_r109_route_run'","'gpu.orch_r120_route_life'")
    source = source.replace("root/'source'",'continuation_source')
    def admission(own_lane,service):
        command=['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                 sys.executable,'-B',str(Path(__file__).resolve()),'scan','--root',str(root),'--lane',own_lane]
        result=subprocess.run(command,capture_output=True,text=True,check=True,timeout=100)
        return json.loads(result.stdout)
    namespace = dict(runtime.old.guard.__globals__,verify=runtime.verify,recovery_directory=directory,
        continuation_source=Path(__file__).resolve().parents[1],admission=SimpleNamespace(scan=admission))
    exec(compile(source,__file__+':guard','exec'),namespace)
    return namespace['guard'](root,lane)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('prepare','native','guard','broker','scan'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--lane',required=True)
    parser.add_argument('--broker-source',type=Path)
    parser.add_argument('--repository',type=Path)
    parser.add_argument('--buffer',type=Path)
    parser.add_argument('--receipts',type=Path)
    args=parser.parse_args()
    runtime=load_runtime(args.root,args.lane,args.broker_source)
    if args.phase=='prepare':
        print(json.dumps(prepare(args.root,args.lane,runtime),sort_keys=True))
    elif args.phase=='broker':
        runtime.directory=directory
        runtime.broker(args.repository,args.root,args.lane,args.buffer,args.receipts)
    elif args.phase=='scan':
        require(os.geteuid()==0 and os.environ.get('CUDA_VISIBLE_DEVICES')=='','privileged_admission')
        bind(args.root,args.lane,runtime)
        runtime.verify(args.root,args.lane)
        service=args.root / VERSION / 'SERVICE_IDENTITY.json'
        if not service.exists():runtime.old.admission.node1.service(service)
        print(json.dumps(runtime.old.admission.scan(args.lane,service),sort_keys=True))
    else:
        bind(args.root,args.lane,runtime)
        if args.phase=='native':runtime.native_function()(args.root,args.lane)
        else:guard(args.root,args.lane,runtime)


if __name__=='__main__':
    main()
