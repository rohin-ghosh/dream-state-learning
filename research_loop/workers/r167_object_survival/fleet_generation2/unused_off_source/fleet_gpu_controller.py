"""Consume fixed copied cells under exact Main conditional authority."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r167_fleet_eval as evaluator


protocol=evaluator.protocol
ROOT=evaluator.ROOT
OPERATION_NAME="gpu_operation2"


def candidates(pipeline, physical):
    condition=evaluator.queue.CONDITIONS[physical]
    result=[]
    for ordinal in range(4):
        for life in pipeline['lives']:
            if life['status']!='SOURCE_CANDIDATE':continue
            registered=ROOT/'lives'/life['life_id']/'REGISTERED.json'
            if not registered.exists():continue
            life_plan=protocol.bound(protocol.read(registered)['plan'])
            sleep=evaluator.queue.milestones(life_plan)[ordinal]
            key=evaluator.queue.key(life['life_id'],sleep,condition)
            transfer=ROOT/'receiving_transfers'/f"{life['life_id']}_{sleep:06d}"/'COMPLETE.json'
            if transfer.exists() and not any(ROOT.glob('gpu_operation*/'+key+'.ONCE.json')) and not (ROOT/'jobs'/(key+'.CONFIG.json')).exists() and not (ROOT/'launches'/key).exists() and not (ROOT/'ledger'/(key+'.RESERVED.json')).exists():
                result.append(dict(life_id=life['life_id'],sleep=sleep,condition=condition,key=key,transfer=protocol.ref(transfer)))
    return result


def gone(sidecar, identity):
    try:return sidecar.gone(identity)
    except ProcessLookupError:return not (Path('/proc')/str(identity['pid'])).exists()


def slot(runtime, physical):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    pipeline=protocol.bound(runtime['common']['pipeline'])
    operation=ROOT/OPERATION_NAME
    while time.time()+915<pipeline['hard_end_unix']:
        ready=candidates(pipeline,physical)
        if not ready:
            time.sleep(5)
            continue
        cell=ready[0];key=cell['key']
        protocol.write(operation/(key+'.ONCE.json'),dict(cell=cell,entered_unix=time.time(),authority=runtime['common']['authority']))
        try:
            life=ROOT/'lives'/cell['life_id']
            config=dict(runtime['common'],life_id=cell['life_id'],sleep=cell['sleep'],condition=cell['condition'],
                capture=protocol.ref(life/'captures'/f"{cell['sleep']:06d}"/'COMPLETE.json'),
                registration=protocol.ref(life/'REGISTERED.json'),TRAIN_freeze=protocol.ref(life/'TRAIN_FREEZE.json'),
                transfer=cell['transfer'],physical=physical,gpu_uuid=sidecar.DEVICES[physical])
            config_path=ROOT/'jobs'/(key+'.CONFIG.json')
            protocol.write(config_path,config)
            evaluator.validate(config_path)
            go_path=ROOT/'jobs'/(key+'.MAIN_GO.json')
            go_ref=protocol.write(go_path,evaluator.expected_go(config_path,config['authority']))
            protocol.write(operation/(key+'.GO_METADATA.json'),dict(execution=protocol.ref(config_path),go=go_ref,
                authority=config['authority'],physical=physical,created_unix=time.time()))
            directory=ROOT/'launches'/key
            command=[config['python'],'-B','-m','gpu.orch_r167_fleet_eval','start','--config',str(config_path),
                '--go',str(go_path),'--directory',str(directory)]
            with (operation/(key+'.start.private.log')).open('xb') as log:
                process=subprocess.run(command,cwd=config['source_root'],env=dict(os.environ,PYTHONPATH=config['source_root'],
                    R167_FLEET_GO_SHA256=go_ref['sha256']),stdin=subprocess.DEVNULL,stdout=log,stderr=log,timeout=120)
            protocol.require(process.returncode==0,'exact_start_failed_no_retry')
            started=time.monotonic()
            while time.monotonic()-started<1100:
                disposition=directory/'DISPOSITION.json'
                if (directory/'DISPATCH_ERROR.json').exists():raise RuntimeError('DISPATCH_ERROR_NO_RETRY')
                if disposition.exists():
                    document=protocol.read(disposition)
                    protocol.require(document['status']=='METADATA_ONLY','DEVICE_BUSY_NO_RETRY')
                    attempt=ROOT/'attempts'/key
                    paths=[attempt/'sealed/PROCESS.json',attempt/'LAUNCH.json',directory/'WRAPPER.json']
                    if (ROOT/'ledger'/(key+'.COMPLETE.json')).exists() and all(
                        gone(sidecar,protocol.read(path)['identity']) for path in paths):
                        protocol.write(operation/(key+'.RELEASED.json'),dict(status='COMPLETE_AND_EXACT_IDENTITIES_RELEASED',
                            observed_unix=time.time(),calls=3,physical=physical))
                        break
                time.sleep(1)
            else:raise RuntimeError('UNKNOWN_TERMINAL_NO_RETRY')
        except BaseException as error:
            protocol.write(operation/f'PHYSICAL{physical}.BLOCKED.json',dict(status='STOP_NEW_ADMISSIONS_FOR_SLOT',
                key=key,error_type=type(error).__name__,error_class=str(error) if type(error) in (ValueError,RuntimeError) else type(error).__name__,
                observed_unix=time.time(),no_consumed_retry=True))
            return
    protocol.write(operation/f'PHYSICAL{physical}.WINDOW_END.json',dict(status='FIXED_WINDOW_ENDED_MISSING_NOT_NEGATIVE',observed_unix=time.time()))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True);args=parser.parse_args()
    runtime=protocol.read(args.runtime)
    for name,checksum in runtime['common']['sources'].items():
        protocol.require(protocol.sha(Path(runtime['common']['source_root'])/name)==checksum,'immutable_controller_runtime')
    protocol.require(protocol.sha(__file__)==runtime['common']['sources']['fleet_gpu_controller.py'],'actual_controller_source')
    protocol.require(runtime['physical_slots']==[1], 'only_unconsumed_OFF_physical1_scope')
    root=ROOT/OPERATION_NAME;root.mkdir(mode=0o700,exist_ok=False)
    (ROOT/'jobs').mkdir(mode=0o700,exist_ok=True)
    protocol.write(root/'ONCE.json',dict(runtime=protocol.ref(args.runtime),authority=runtime['common']['authority'],started_unix=time.time()))
    slot(runtime,1)


if __name__=='__main__':main()
