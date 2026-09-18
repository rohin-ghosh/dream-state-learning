"""Resume the released gen7 task cursor and unfinished segment allowance."""

import argparse
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace


def worker(root):
    spec = importlib.util.spec_from_file_location('frozen_generator',root/'orch_r119_l1_generation_resume.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resumed_source(source):
    original = "    start_calls = count = inherited['calls']"
    assert source.count(original) == 1
    source = source.replace(original,"    start_calls = inherited.get('original_segment_start_calls', inherited['calls'])\n    count = inherited['calls']")
    original = '    directory.mkdir(exist_ok=False)'
    assert source.count(original) == 1
    return source.replace(original,original+'\n    restore_carry(directory)')


def configuration(root):
    module = worker(root)
    config = module.config(root)
    receipt = module.trainer.read(root/'CURSOR_RESUME.json')
    assert module.trainer.sha(__file__) == receipt['source_sha256']
    assert receipt['physical'] == 7 and config['node'] == 'ovx'
    assert receipt['progress']['calls'] == 20286 and receipt['progress']['inherited_calls'] == 15842
    assert module.trainer.sha(receipt['release_path']) == receipt['release_sha256']
    assert module.trainer.sha(receipt['assay_terminal_path']) == receipt['assay_terminal_sha256']
    return module,config,receipt


def generate(root,segment):
    module,config,receipt = configuration(root)
    stage = root/('segment%04d'%segment)
    plan = module.trainer.read(stage/'PLAN.json')
    assert os.environ['CUDA_VISIBLE_DEVICES'] == config['uuid_by_index'][7]
    def restore_carry(directory):
        if segment != 0:
            return
        manifest = module.trainer.read(receipt['capture_manifest'])
        assert module.trainer.sha(receipt['capture_manifest']) == receipt['capture_manifest_sha256']
        for relative,expected in manifest['files'].items():
            source = Path(receipt['prior_root'])/relative
            if source.name.startswith(('CALL_','INTENT_','EPISODE_')):
                assert module.trainer.sha(source) == expected
                shutil.copyfile(source,directory/source.name)
    prior = module.trainer.policy
    def allocation(node,index):
        assert node == 'ovx' and index == 7
        return config['condition_positions']['7']
    module.trainer.policy = SimpleNamespace(**dict(prior.__dict__,allocation=allocation))
    context = dict(module.generation.__dict__,ROOT=stage,ORIGIN=Path(config['origin_view']),
                   END=config['hard_deadline_unix'],CUTOFF=config['hard_deadline_unix'],
                   verify=lambda:plan,restore_carry=restore_carry)
    source = resumed_source(inspect.getsource(module.generation.generate))
    exec(compile(source,__file__,'exec'),context)
    try:
        context['generate'](7)
    finally:
        module.trainer.policy = prior


def supervise(root):
    module,config,receipt = configuration(root)
    ready = module.trainer.read(root/'PRE_GPU.json')
    assert ready['cpu_passed'] and ready['cursor_resume_sha256'] == module.trainer.sha(root/'CURSOR_RESUME.json')
    assert ready['builder_line'].startswith('[Builder]')
    assert not (root/'START.json').exists()
    module.trainer.write(root/'START.json',dict(identity=module.identity(os.getpid()),physical=7,
                         prior_cursor=receipt['progress'],new_lineage=False,observed_unix=time.time()))
    progress = dict(receipt['progress'],original_segment_start_calls=receipt['progress']['inherited_calls'])
    segment = 0
    while time.time() < config['hard_deadline_unix']:
        stage = root/('segment%04d'%segment);stage.mkdir()
        plan = module.trainer.read(Path(receipt['prior_stage'])/'PLAN.json')
        module.trainer.write(stage/'PLAN.json',dict(plan,cursor_resume_sha256=module.trainer.sha(root/'CURSOR_RESUME.json')))
        module.trainer.write(stage/'RELEASE_7.json',dict(progress=progress,same_lineage=True,no_replay=True))
        while time.time() < config['hard_deadline_unix']:
            snapshot = module.scan(root,7)
            snapshot.pop('host',None)
            module.trainer.write(stage/('ADMISSION_%d.json'%time.time_ns()),snapshot)
            if snapshot['clear']:
                assert snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == config['uuid_by_index'][7]
                break
            time.sleep(2)
        else:
            return
        with (stage/'NATIVE.log').open('x') as log:
            child = subprocess.Popen([sys.executable,'-B','-u',str(Path(__file__).resolve()),'generate','--root',str(root),'--segment',str(segment)],
                    cwd=config['source_cwd'],env=dict(os.environ,CUDA_VISIBLE_DEVICES=config['uuid_by_index'][7],
                    PYTHONPATH=config['pythonpath'],HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),
                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        expected = module.identity(child.pid)
        module.trainer.write(stage/'LAUNCH.json',dict(identity=expected,physical=7,first_new_call=progress['calls']+1,observed_unix=time.time()))
        while child.poll() is None:
            module.trainer.write(root/'HEARTBEAT.json',dict(identity=expected,segment=segment,phase='generation',observed_unix=time.time()))
            if time.time() >= config['hard_deadline_unix']:
                module.original.stop(child,expected,'ORIGINAL_LEASE_WALL');return
            time.sleep(3)
        module.trainer.write(stage/'EXIT.json',dict(returncode=child.returncode,observed_unix=time.time()))
        assert child.returncode == 0,'failed_stage_preserved_no_replay'
        progress = module.trainer.read(stage/'gpu7/PROGRESS.json')
        segment += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('check','supervise','generate'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--segment',type=int,default=0)
    options=parser.parse_args()
    if options.action == 'check':
        module,config,receipt=configuration(options.root)
        compile(resumed_source(inspect.getsource(module.generation.generate)),__file__,'exec')
        print(json.dumps(dict(status='CPU_PROVENANCE_PASS',physical=7,next_call=20287,remaining_original_segment_allowance=11940)))
    elif options.action == 'generate':
        generate(options.root,options.segment)
    else:
        supervise(options.root)
