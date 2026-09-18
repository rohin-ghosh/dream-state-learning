"""Narrow old-grid crash continuation: replay saved calls, never regenerate them."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r109_grid_20260915_attempt1')
OLD_RUN_SHA = '1199d9a6a68755c40225c55b4221e5e897016e3a6630ed0c5ce6c55076cc6c11'
READY_SHA = '20e88eff72cb6e84f1709f0781c51996a20cb09bfbd30b3b2767fc527b7f588d'
UUID = 'GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed'
RECEIPTS = 'recovery_v3/receipts'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2)
        stream.flush();os.fsync(stream.fileno())


class Replay:
    def __init__(self,root,old,cadence,cycle):
        self.root,self.old=root,old
        self.original_spend,self.original_write=old.spend,old.write
        rows=[json.loads(line) for line in (root/'LEDGER.jsonl').read_text().splitlines() if line.strip()]
        start=next(index for index,row in enumerate(rows) if row['kind']=='NATIVE'
            and row['cadence']==cadence and row['cycle']==cycle and row['phase']=='train')
        self.cached=rows[start:]
        self.cursor=0
        self.pending=None
        self.initial_native=sum(row['kind']=='NATIVE' for row in rows)
        self.initial_parent=sum(row['kind']=='PARENT' for row in rows)
        self.original_calls={root/'calls'/f'N{row["number"]:05d}.json' for row in rows if row['kind']=='NATIVE'}
        self.output=root/RECEIPTS

    def spend(self,root,kind,detail):
        require(root==self.root,'same_evolving_root')
        if self.cursor<len(self.cached):
            row=self.cached[self.cursor]
            require(row['kind']==kind and all(row.get(key)==value for key,value in detail.items()),
                'cached_reservation_sequence_mismatch')
            self.cursor+=1
            if kind=='NATIVE':
                path=root/'calls'/f'N{row["number"]:05d}.json'
                call=read(path)
                require(call['status']=='COMPLETE','cannot_retry_unknown_native_call')
                self.pending=call
            return row['number']
        require(self.pending is None,'cached_native_not_consumed')
        return self.original_spend(root,kind,detail)

    def generate(self,engine,messages,**kwargs):
        if self.pending is not None:
            call,self.pending=self.pending,None
            require(call['messages']==messages,'exact_saved_prompt_reconstruction')
            require(call['response']['requested_generation_cap']==kwargs['max_new_tokens'],
                'same_saved_generation_cap')
            return deepcopy(call['response'])
        require(self.cursor==len(self.cached),'unconsumed_cached_parent')
        return engine.generate(messages,**kwargs)

    def write(self,path,value):
        path=Path(path)
        if path.exists() and not (path.parent==self.root/'calls' and path not in self.original_calls):
            existing=read(path)
            if path.name=='FAILED.json':
                write_new(self.output/'NEW_FAILURE.json',dict(legacy_failure=ref(path),new_failure=value))
                return
            if path.name in ('STARTED.json','LOADED.json'):
                for key in ('lane','cadence','phase','base_sha256','no_adapter'):
                    if key in value and key in existing:
                        require(value[key]==existing[key],'same_existing_phase')
                return
            if path.parent==self.root/'calls':
                require(existing['status']=='COMPLETE','no_incomplete_call_replay')
                for key in ('task_id','split','purpose','messages','base_sha256','adapter'):
                    require(existing[key]==value[key],'same_saved_call_identity')
                if value['status']=='COMPLETE':
                    require(existing['response']==value['response'],'same_saved_response')
                else:
                    require(value['status']=='STARTED','saved_call_status')
                return
            require(existing==value,'immutable_reconstructed_evidence_mismatch')
            return
        self.original_write(path,value)
        if path.parent==self.root/'calls' and value.get('status')=='COMPLETE':
            first=self.output/'FIRST_NEW_NATIVE.json'
            if not first.exists():
                write_new(first,dict(call=ref(path),finished_unix=value['finished_unix'],
                    original_native_charged=self.initial_native,original_parent_charged=self.initial_parent,
                    cached_records_reused=self.cursor,new_model_call=True,old_calls_retried=0))


class EngineProxy:
    def __init__(self,engine,replay):
        self.engine,self.replay=engine,replay

    def __getattr__(self,name):
        return getattr(self.engine,name)

    def generate(self,messages,**kwargs):
        return self.replay.generate(self.engine,messages,**kwargs)


def install(old,replay):
    path=Path(old.__file__)
    require(ref(path)['sha256']==OLD_RUN_SHA,'exact_old_run_source')
    text=path.read_text()
    node=next(node for node in ast.parse(text).body if isinstance(node,ast.FunctionDef) and node.name=='run')
    fragment='\n'.join(text.splitlines()[node.lineno-1:node.end_lineno])
    needle='output.mkdir(parents=True, exist_ok=False)'
    require(fragment.count(needle)==1,'single_resume_directory_delta')
    fragment=fragment.replace(needle,'output.mkdir(parents=True, exist_ok=True)')
    exec(compile(fragment,str(path)+'[R113_RECOVERY_V1]','exec'),old.__dict__)
    old.spend,old.write=replay.spend,replay.write


def native():
    from gpu import orch_r109_grid_run as old
    require(ref(ROOT/'READY.json')['sha256']==READY_SHA,'same_old_ready')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')==UUID,'assigned_uuid')
    ready=old.validate(ROOT,'ovx')
    failure=ROOT/'segment/cycle02/train/FAILED.json'
    require(read(failure)['error_type']=='JSONDecodeError','specific_preserved_publication_crash')
    replay=Replay(ROOT,old,'segment',2)
    install(old,replay)
    def check(label):require(time.time()<old.policy.NATIVE_END,'original_deadline:'+label)
    tokenizer=old.portable.source.native.load_local_tokenizer(ready['model_dir'])
    engine=EngineProxy(old.Engine(ready['model_dir'],tokenizer,device='cuda:0',check=check),replay)
    write_new(ROOT/RECEIPTS/'LOADED.json',dict(pid=os.getpid(),base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter,loaded_unix=time.time(),original_failure=ref(failure),
        original_native_charged=replay.initial_native,original_parent_charged=replay.initial_parent))
    for cadence in old.policy.LANES['ovx']['order']:
        for cycle in range(1,old.policy.CYCLES+1):
            for phase in ('train','held'):
                if (ROOT/cadence/f'cycle{cycle:02d}'/phase/'COMPLETE.json').exists():
                    continue
                old.run(ROOT,'ovx',cadence,cycle,phase,shared_engine=engine)
    engine.verify_base()


def scoped_scan():
    from gpu import orch_r109_grid_run as old
    if os.geteuid()!=0:
        command=['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+str(ROOT/'source_v1'),'python3','-B',str(Path(__file__).resolve()),'scan']
        return json.loads(subprocess.check_output(command,text=True,timeout=100))
    import orch_r110_admission as repaired
    require(ref(Path(repaired.__file__))['sha256']=='91027037bf98aa391afe5d89da9814502da57d6b15ad16574b2a7cdef9976c3f',
        'tested_scoped_scanner_source')
    old.bind('ovx')
    return repaired.scan(7,ROOT/'SERVICE_IDENTITY.json')


def guard():
    from gpu import orch_r109_grid_run as old
    output=ROOT/RECEIPTS
    (output/'GUARD_ONCE').mkdir()
    try:
        old.validate(ROOT,'ovx')
        old_pid=read(ROOT/'RESIDENT_LOADED.json')['pid']
        require(not Path(f'/proc/{old_pid}').exists(),'old_native_gone_no_signal')
        for attempt in range(90):
            report=scoped_scan()
            write_new(output/f'ADMISSION_{attempt:03d}.json',report)
            if report['clear']:
                require(report['scanner_euid']==0 and not report['blocking_reasons']
                    and report['gpu']['uuid']==UUID,'exact_fresh_clear')
                break
            time.sleep(2)
        else:
            raise ValueError('fresh_admission_not_clear_no_waiver')
        environment=dict(os.environ,CUDA_VISIBLE_DEVICES=UUID,PYTHONPATH=str(ROOT/'source_v1'),
            PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        seconds=int(old.policy.HARD_END-time.time()-5)
        require(seconds>0,'same_deadline')
        command=['timeout','--signal=TERM','--kill-after=5s',str(seconds)+'s',old.PYTHON,'-B',
            str(Path(__file__).resolve()),'native']
        with (output/'NATIVE.log').open('x') as stream:
            child=subprocess.Popen(command,cwd=ROOT/'source_v1',env=environment,stdout=stream,
                stderr=subprocess.STDOUT,start_new_session=True)
        write_new(output/'LAUNCH.json',dict(pid=child.pid,launched_unix=time.time(),command=command))
        require(child.wait()==0,'recovery_native_failure_preserved')
        write_new(ROOT/'RECOVERY_V3_TERMINAL.json',dict(status='COMPLETE',finished_unix=time.time()))
    except BaseException as error:
        write_new(ROOT/'RECOVERY_V3_TERMINAL.json',dict(status='FAILED',error_type=type(error).__name__,
            error=str(error),finished_unix=time.time()))
        raise
    finally:
        write_new(output/'FINAL_RELEASE.json',scoped_scan())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('native','guard','scan'))
    args=parser.parse_args()
    if args.mode=='scan':
        print(json.dumps(scoped_scan(),sort_keys=True))
    else:
        native() if args.mode=='native' else guard()
