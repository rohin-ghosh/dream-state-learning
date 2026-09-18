"""Source-only rolling capture, bounded by existing per-life read authorities."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import prep_common as common


ROOT = common.REMOTE_ROOT


def capture_once(queue, queue_path, sleep):
    protocol = queue.protocol
    plan, root, source, authority = queue.initialized(queue_path, True)
    common.require(sleep in queue.milestones(plan), 'fixed_registered_checkpoint')
    with protocol.lock(root/'queue.lock'):
        boundary = protocol.read(root/'boundaries'/f'{sleep:06d}.json')
        source_commit = queue.checkpoint_path(source,sleep)
        paths = [source_commit,Path(boundary['record']['path']),Path(boundary['intent']['path']),Path(plan['birth_plan']['path'])]
        metadata = queue.Reader(plan,root,source,paths,'metadata')
        commit,commit_ref = metadata.document(source_commit)
        queue.checkpoint(commit,source,sleep)
        record,record_ref = metadata.document(boundary['record']['path'])
        unused,intent_ref = metadata.document(boundary['intent']['path'])
        birth,birth_ref = metadata.document(plan['birth_plan']['path'])
        common.require(commit_ref==boundary['commit'] and record_ref==boundary['record']
            and intent_ref==boundary['intent'] and birth_ref==boundary['birth_plan'],'exact_capture_source_binding')
        context={field:birth[field] for field in ('system_prompt','birth_prompt')}
        queue.validate_boundary(record,commit,sleep,context)
        common.require(protocol.digest(context)==boundary['context_sha256'],'original_birth_hash')
        destination=root/'captures'/f'{sleep:06d}'
        destination.mkdir(mode=0o700,exist_ok=False)
        try:
            adapter_paths=[source_commit.parent/'adapter'/name for name in commit['adapter_files']]
            reader=queue.Reader(plan,root,source,adapter_paths,'adapter')
            (destination/'adapter').mkdir(mode=0o700)
            for path in adapter_paths:
                raw=reader.raw(path)
                common.require(hashlib.sha256(raw).hexdigest()==commit['adapter_files'][path.name],'immutable_source_adapter_hash')
                common.write(destination/'adapter'/path.name,raw)
            commit_copy=common.write(destination/'COMMIT.original.json',metadata.raw(source_commit))
            birth_copy=common.write(destination/'BIRTH.private.json',context)
            manifest=common.write(destination/'MANIFEST.json',dict(schema='R130_CHECKPOINT_MANIFEST_V1',
                adapter_path='adapter',commit_path='COMMIT.original.json',commit_sha256=commit_copy['sha256']))
            boundary_copy=common.write(destination/'BOUNDARY.json',boundary)
            common.write(destination/'COMPLETE.json',dict(status='IMMUTABLE_ADAPTER_BIRTH_CUSTODY',
                manifest=manifest,birth=birth_copy,boundary=boundary_copy,observed_unix=time.time(),
                model_calls=0,optimizer_rng_read=False,adapter_write_hash_reread=False))
        except BaseException as error:
            common.write(destination/'FAILED.json',dict(status='FAILED_CAPTURE_PRESERVED_NO_RETRY',error_type=type(error).__name__))
            raise


def observe_job(queue,queue_path,max_records=32):
    plan,root,source,authority=queue.initialized(queue_path,True)
    discovery=queue.discover(queue_path,max_records=max_records)
    captured=[]
    for sleep in queue.milestones(plan):
        if (root/'boundaries'/f'{sleep:06d}.json').exists() and not (root/'captures'/f'{sleep:06d}').exists():
            capture_once(queue,queue_path,sleep)
            captured.append(sleep)
    return dict(life_id=plan['life_id'],cursor=discovery['verified_through_index'],new_captures=captured,
        captures=[sleep for sleep in queue.milestones(plan) if (root/'captures'/f'{sleep:06d}'/'COMPLETE.json').exists()],
        reads=queue.read_totals(root),model_calls=0)


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',required=True)
    arguments=parser.parse_args()
    request=common.read(arguments.request)
    common.scope(ROOT/'control/PREPARATION_SCOPE.json',ROOT/'control/PROPOSAL.json')
    common.require(common.ref(__file__)['sha256']==request['source_sha256'],'frozen_capture_controller')
    from gpu import orch_r167_object_probe_queue as queue
    operation=ROOT/'capture_operation1'/request['node']
    operation.mkdir(parents=True,mode=0o700,exist_ok=False)
    identity=dict(pid=os.getpid(),start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    common.write(operation/'ONCE.json',dict(request=request,identity=identity,started_unix=time.time(),model_calls=0))
    active={name:ROOT/'source_controls'/name/'QUEUE_PLAN.json' for name in request['lives']}
    cursors={name:-1 for name in active}
    targets={name:common.read(ROOT/'source_controls'/name/'FRESH_CUSTODY.json')['tail_index_at_listing'] for name in active}
    polls={name:1 for name in active}
    next_poll={name:time.time()+60 for name in active}
    sweep=0
    while time.time()<common.END and active:
        worked=False
        for name,path in list(active.items()):
            try:
                if cursors[name]>=targets[name]:
                    if time.time()<next_poll[name]:
                        continue
                    if polls[name]>=241:
                        del active[name]
                        continue
                    plan=queue.protocol.read(path)
                    source=Path(plan['source_root'])/'stream/records'
                    files=list(source.glob('[0-9]'*20+'.json'))
                    targets[name]=max([cursors[name],*[int(entry.stem) for entry in files]])
                    polls[name]+=1
                    next_poll[name]=time.time()+60
                    if targets[name]<=cursors[name]:
                        continue
                report=observe_job(queue,path,min(32,targets[name]-cursors[name]))
                common.write(operation/name/f'{sweep:04d}.json',report)
                cursors[name]=report['cursor']
                worked=True
                if len(report['captures'])==4:
                    del active[name]
            except Exception as error:
                common.write(operation/name/'HELD.json',dict(status='SOURCE_PIPELINE_HELD_NO_RETRY',
                    error_type=type(error).__name__,reason=str(error) if isinstance(error,ValueError) else 'SOURCE_CAPTURE_FAILED',
                    observed_unix=time.time(),model_calls=0))
                del active[name]
        common.require(common.ref(__file__)['sha256']==request['source_sha256'],'capture_source_changed_stop')
        sweep+=1
        if active:
            time.sleep(min(1 if worked else 5,max(0,common.END-time.time())))
    common.write(operation/'TERMINAL.json',dict(status='CAPTURE_WINDOW_OR_SWEEP_BUDGET_ENDED',
        observed_unix=time.time(),unfinished_lives=sorted(active),poll_counts=polls,model_calls=0,provider_calls=0))


if __name__=='__main__':
    main()
