"""Fair per-completed-sleep scheduling; separate Main GO mandatory to run."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import time

import prep_common as common
import r172_runner as runner


ROOT=common.REMOTE_ROOT


def candidates(root,condition,ready=None):
    root=Path(root)
    served={}
    for path in (root/'ledger').glob('*.RESERVED.json'):
        row=common.read(path)
        if row['condition']==condition:
            served[row['life_id']]=served.get(row['life_id'],0)+1
    result=[]
    for path in (root/'receiving_transfers').glob('*/COMPLETE.json'):
        transfer=common.read(path)
        name,sleep=transfer['life_id'],transfer['sleep']
        key=runner.prior.queue.key(name,sleep,condition)
        if (root/'attempts'/key).exists() or (root/'scheduler_once'/(key+'.json')).exists():
            continue
        baseline_path=root/'baseline_authorities'/f'{name}_{condition}.json'
        if sleep==0 and (not baseline_path.exists() or common.read(baseline_path).get('status')!='NEW_BASELINE_AUTHORIZED'):
            continue
        result.append(dict(life_id=name,sleep=sleep,condition=condition,key=key,transfer=common.ref(path),
            capture=transfer['capture'],ready_unix=transfer['observed_unix'],baseline_authority=common.ref(baseline_path) if sleep==0 else None))
    first_by_life={}
    for row in result:
        if ready is not None and not ready(row):
            continue
        order=(row['sleep']==0,row['sleep'])
        current=first_by_life.get(row['life_id'])
        if current is None or order<(current['sleep']==0,current['sleep']):
            first_by_life[row['life_id']]=row
    return sorted(first_by_life.values(),key=lambda row:(served.get(row['life_id'],0),row['sleep']==0,row['ready_unix'],row['life_id']))


def preparation_ready(root,cell):
    root=Path(root)
    life=root/'lives'/cell['life_id']
    required=[life/'REGISTERED.json',life/'TRAIN_FREEZE.json',
        root/'receiving_allowances'/f"{cell['life_id']}_{cell['sleep']:06d}.json"]
    return all(path.is_file() and path==path.resolve() for path in required)


def configuration(runtime,cell,physical,root=ROOT):
    root=Path(root)
    life=root/'lives'/cell['life_id']
    return dict(runtime,life_id=cell['life_id'],sleep=cell['sleep'],condition=cell['condition'],physical=physical,
        gpu_uuid=runner.device_uuid(common.bound(runtime['lease']),physical),capture=cell['capture'],transfer=cell['transfer'],
        registration=common.ref(life/'REGISTERED.json'),TRAIN_freeze=common.ref(life/'TRAIN_FREEZE.json'),
        receiving_read_allowance=common.ref(root/'receiving_allowances'/f"{cell['life_id']}_{cell['sleep']:06d}.json"),
        baseline_authority=cell['baseline_authority'])


def run_slot(runtime,go_path,physical):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    condition=runner.prior.queue.CONDITIONS[physical]
    while time.time()+915<common.END:
        available=candidates(ROOT,condition,ready=lambda cell:preparation_ready(ROOT,cell))
        if not available:
            time.sleep(10)
            continue
        cell=available[0]
        key=cell['key']
        common.write(ROOT/'scheduler_once'/(key+'.json'),dict(cell=cell,go=common.ref(go_path),entered_unix=time.time()))
        try:
            config=configuration(runtime,cell,physical,ROOT)
            config_path=ROOT/'jobs'/(key+'.CONFIG.json')
            common.write(config_path,config)
            runner.start(config_path,go_path)
            attempt=ROOT/'attempts'/key
            common.require((ROOT/'ledger'/(key+'.COMPLETE.json')).exists(),'failed_refused_or_unknown_no_retry')
            for path in (attempt/'TIMEOUT.json',attempt/'sealed/PROCESS.json'):
                identity=common.read(path)['identity']
                common.require(sidecar.gone(identity),'prior_native_timeout_not_released')
            common.write(ROOT/'scheduler_released'/(key+'.json'),dict(status='EXACT_NATIVE_TIMEOUT_RELEASED',observed_unix=time.time()))
        except Exception as error:
            common.write(ROOT/'scheduler_holds'/f'PHYSICAL{physical}.json',dict(status='STOP_NEW_SLOT_ADMISSION_NO_RETRY',
                key=key,error_type=type(error).__name__,reason=str(error) if isinstance(error,ValueError) else 'UNRESOLVED_JOB',observed_unix=time.time()))
            return


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',required=True)
    parser.add_argument('--go',required=True)
    arguments=parser.parse_args()
    runtime=common.read(arguments.runtime)
    runner.validate_go(arguments.go,runtime['pipeline'],runtime['source_freeze'],runtime['cpu_gate'])
    operation=ROOT/'scheduler_operation1'
    operation.mkdir(mode=0o700,exist_ok=False)
    common.write(operation/'ONCE.json',dict(runtime=common.ref(arguments.runtime),go=common.ref(arguments.go),started_unix=time.time()))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_slot,runtime,Path(arguments.go),physical) for physical in (0,1)]
        for future in futures:
            future.result()


if __name__=='__main__':
    main()
