import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


SOURCE = Path('/tmp/astra_prediction_transfer_source_20260913_attempt1')
BATCH = Path('/tmp/astra_prediction_transfer_batch_20260913_attempt1')
RETRY = Path('/tmp/astra_prediction_transfer_retry_20260913_attempt2')


def pin(path):
    path = Path(path)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def prepare(api):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    RETRY.mkdir(exist_ok=False)
    roster = api.read(BATCH / 'roster.json')
    entries = []
    for seed in (0,1):
        original = roster['entries'][seed]
        root = Path(original['root'])
        failure = api.read(root / 'run/post/stage_failure.json')
        cvd = api.read(root / 'run/post/post_cvd.json')['value']
        assert failure == [{'error':'resource not clear: cvd','type':'ActorError'}]
        assert cvd['owners'] == cvd['unexpected'] == []
        assert len(cvd['unresolved']) == 1 and cvd['unresolved'][0]['pid'] == 2960286
        assert cvd['unresolved'][0]['error_type'] == 'PermissionError'
        for state in ('OFF','post'):
            assert api.read(root / 'run' / state / 'closed.json')['calls'] == 48
            assert api.read(root / 'run' / state / 'exit.json')['returncode'] == 0
            assert api.read(root / 'run' / state / 'released.json')['owned_group_released'] is True
        assert not Path('/proc/2960286').exists()
        new_root = root.with_name(f'prediction_transfer_seed{seed}_20260913_attempt2')
        result = api.prepare(str(new_root), original['spec']['path'], original['spec']['sha256'], allow_native=True)
        entry = {'seed':seed,'root':str(new_root),'plan_sha256':result['plan_sha256'],
            'original_failed_root':str(root),'original_failure':pin(root / 'run/post/stage_failure.json'),
            'spec':original['spec'],'runner':original['runner']}
        api.write(RETRY / f'prepared_seed{seed}.json',entry)
        entries.append(entry)
        print(json.dumps(entry),flush=True)
    api.write(RETRY / 'roster.json',{'entries':entries,'helper':pin(__file__),
        'reason':'INFRASTRUCTURE_RETRY_BEFORE_OUTCOME_INSPECTION; completed peer unreaped by ordered batch waits',
        'scientific_inputs_changed':False,'fits':0,'additional_calls':192,'execution':'serial; reap each controller before starting next'})


def launch(api):
    roster = api.read(RETRY / 'roster.json')
    api.write(RETRY / 'started.json',{'helper':pin(__file__),'identity':api.lifecycle.identity(os.getpid()),'at':time.time()})
    time.sleep(8)
    for entry in roster['entries']:
        assert pin(entry['runner']['path']) == entry['runner']
        argv = [sys.executable,'-B',entry['runner']['path'],'controller','--root',entry['root'],
            '--plan-sha256',entry['plan_sha256'],'--allow-gpu']
        with (RETRY / f"seed{entry['seed']}.stdout.log").open('xb') as stdout, (RETRY / f"seed{entry['seed']}.stderr.log").open('xb') as stderr:
            process = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True,
                env={**os.environ,'CUDA_VISIBLE_DEVICES':'','PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'})
        api.write(RETRY / f"seed{entry['seed']}.launch.json",{'identity':api.lifecycle.identity(process.pid),'argv':argv,'root':entry['root'],'at':time.time()})
        returncode = process.wait(timeout=api.TOTAL_SECONDS + 120)
        result = {'seed':entry['seed'],'returncode':returncode,'root':entry['root'],'at':time.time()}
        if returncode == 0:
            complete = pin(Path(entry['root']) / 'capture_complete.json')
            try:
                result['collection'] = api.collect(entry['root'],entry['plan_sha256'],complete['sha256'],entry['root'] + '_collected')
            except Exception as error:
                result['collection_error'] = {'type':type(error).__name__,'message':str(error)}
        api.write(RETRY / f"seed{entry['seed']}.terminal.json",result)
        if returncode != 0 or 'collection_error' in result:
            api.write(RETRY / 'stopped.json',{'reason':'retry failed; no further retry or next seed','terminal':result})
            return
    api.write(RETRY / 'complete.json',{'at':time.time(),'seeds':[0,1]})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=('prepare','launch'))
    arguments = parser.parse_args()
    sys.path.insert(0,str(SOURCE))
    runner = importlib.import_module('gpu.astra_level1_prediction_transfer_readout')
    globals()[arguments.mode](runner)
