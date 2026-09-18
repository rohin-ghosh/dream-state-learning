"""Prospective lease-clock continuation of immutable C2; original optimizer/RNG."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

try:
    import orch_r109_l1_experience as experience
except ImportError:
    from gpu import orch_r109_l1_experience as experience
from gpu import orch_r109_l1_train as trainer
from gpu import orch_r109_l1_run as original


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def namespace(root):
    config = trainer.read(root / 'CONTINUATION.json')
    prior = Path(config['prior_version'])
    assert trainer.sha(prior / 'PLAN.json') == config['prior_plan_sha256']
    plan = trainer.read(prior / 'PLAN.json')
    prepared = trainer.read(prior / 'PREPARED.json')
    assert trainer.sha(prior / 'ENCODED.json') == prepared['encoded_sha256']
    assert trainer.sha(prior / 'ELIGIBLE.json') == plan['eligible_sha256']
    assert trainer.sha(__file__) == config['source_sha256']
    assert trainer.sha(experience.__file__) == config['experience_source_sha256']
    assert config['hard_deadline_unix'] == config['lease_end_unix'] - 21600
    assert plan['train_slots'] == {'FULL': 5, 'CONTROL': 6}
    assert config['slots'] == {'FULL': 0, 'CONTROL': 1}
    plan = dict(plan, prior_lifetime=plan['lifetime'], continuation_authorization='USER_20260915_1710_AND_1715',
                uuid_by_index=config['uuid_by_index'], model_dir=config['model_dir'],
                train_slots=config['slots'], lifetime=dict(started_unix=plan['lifetime']['started_unix'],
                              hard_deadline_unix=config['hard_deadline_unix'],
                              native_deadline_unix=config['hard_deadline_unix'],
                              lease_end_unix=config['lease_end_unix'], max_gpus=14))
    assert time.time() < config['hard_deadline_unix']

    def load_plan(arm, checkpoint, training):
        commit = trainer.storage.verify_checkpoint(checkpoint)['metadata']
        adapter = trainer.native.bridge.AdapterIdentity.from_document(dict(commit['adapter'], path=str(checkpoint / 'adapter')))
        binding = trainer.native.bridge.StageBinding(plan['cohort_id'] + '_' + arm, trainer.native.bridge.ARMS[2],
            0, 'training' if training else 'sealed_readout', adapter, False, not training, trainer.sha(root / 'CONTINUATION.json'))
        proxy = SimpleNamespace(binding=lambda unused: binding,
            contract=SimpleNamespace(manifest=lambda unused: dict(recipe=trainer.previous.common.RECIPE)),
            lineage=SimpleNamespace(arm=trainer.native.bridge.ARMS[2]))
        return plan, prepared, commit, adapter, binding, proxy

    context = dict(experience.__dict__, ROOT=root, SLOTS=config['slots'], load_plan=load_plan)
    for name in ('train', 'readout'):
        function = getattr(experience, name)
        context[name] = FunctionType(function.__code__, context, 'continued_' + name, function.__defaults__)
    return config, plan, context


def supervise(root, arm):
    import fcntl
    config, plan, context = namespace(root)
    ready = trainer.read(root / 'PRE_GPU.json')
    assert ready['cpu_passed'] is True and ready['continuation_sha256'] == trainer.sha(root / 'CONTINUATION.json')
    assert ready['builder_line'].startswith('[Builder]')
    lock = (root / (arm + '.lock')).open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    start = root / ('START_' + arm + '.json')
    assert not start.exists(), 'single_own_supervisor_no_retry'
    trainer.write(start, dict(identity=identity(os.getpid()), original_checkpoint=config['arms'][arm],
                             hard_deadline_unix=config['hard_deadline_unix'], observed_unix=time.time()))
    resume = Path(config['arms'][arm]['checkpoint'])
    assert trainer.sha(resume / 'COMMIT.json') == config['arms'][arm]['commit_sha256']
    segment = config['next_segment']
    while time.time() < config['hard_deadline_unix']:
        for phase, condition in (('train', None), ('readout', 'ON'), ('readout', 'OFF')):
            while time.time() < config['hard_deadline_unix']:
                from gpu.orch_combined_l1_continual_run import scan
                snapshot = scan(config['slots'][arm], Path(config['service_identity']))
                snapshot.pop('host', None)
                trainer.write(root / 'admissions' / f'{arm}_{segment}_{phase}_{condition}_{time.time_ns()}.json', snapshot)
                if snapshot['clear']:
                    assert snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == plan['uuid_by_index'][config['slots'][arm]]
                    break
                trainer.write(root / ('HEARTBEAT_' + arm + '.json'), dict(phase='WAIT_OWNERSHIP', index=config['slots'][arm],
                              resume=str(resume), segment=segment, observed_unix=time.time()))
                time.sleep(2)
            else:
                return
            command = [sys.executable, '-B', '-u', str(Path(__file__).resolve()), phase, '--root', str(root),
                       '--arm', arm, '--segment', str(segment), '--resume', str(resume)]
            if condition:
                command += ['--condition', condition]
            with (root / f'{arm}_{segment}_{phase}_{condition}.log').open('x') as log:
                child = subprocess.Popen(command, cwd=os.getcwd(), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid_by_index'][config['slots'][arm]],
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
            expected = identity(child.pid)
            trainer.write(root / f'{arm}_{segment}_{phase}_{condition}_LAUNCH.json', dict(identity=expected,
                          index=config['slots'][arm], resume=str(resume), phase=phase, observed_unix=time.time()))
            while child.poll() is None:
                trainer.write(root / ('HEARTBEAT_' + arm + '.json'), dict(phase=phase, condition=condition,
                    identity=expected, index=config['slots'][arm], resume=str(resume), segment=segment,
                    hard_deadline_unix=config['hard_deadline_unix'], observed_unix=time.time()))
                if time.time() >= config['hard_deadline_unix']:
                    original.stop(child, expected, 'ACTUAL_LEASE_MINUS_ORIGINAL_6H_MARGIN')
                    return
                time.sleep(2)
            assert child.returncode == 0, 'preserve_failed_stage_no_replay'
            if phase == 'train':
                complete = trainer.read(root / 'fit' / arm / f'segment{segment:03d}' / 'COMPLETE.json')
                resume = Path(complete['checkpoint'])
        trainer.write(root / f'{arm}_{segment}_PAIRED_COMPLETE.json', dict(checkpoint=str(resume),
                      conditions=['ON', 'OFF'], score_gate=False, observed_unix=time.time()))
        segment += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('supervise', 'train', 'readout', 'check'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=('FULL', 'CONTROL'))
    parser.add_argument('--segment', type=int)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--condition', choices=('ON', 'OFF'))
    options = parser.parse_args()
    if options.action == 'supervise':
        supervise(options.root, options.arm)
    else:
        config, plan, context = namespace(options.root)
        if options.action == 'check':
            assert context['train'].__code__ is experience.train.__code__
            assert context['readout'].__code__ is experience.readout.__code__
            for arm, record in config['arms'].items():
                commit = trainer.storage.verify_checkpoint(Path(record['checkpoint']))['metadata']
                assert commit['update'] == record['update'] and commit['world_size'] == 1
                assert trainer.sha(Path(record['checkpoint']) / 'COMMIT.json') == record['commit_sha256']
            print(json.dumps(dict(status='CPU_PROVENANCE_PASS', slots=config['slots'], arms=config['arms'],
                                  hard_deadline_unix=config['hard_deadline_unix'], optimizer_reset=False)))
        elif options.action == 'train':
            context['train'](options.arm, options.segment, options.resume)
        else:
            context['readout'](options.arm, options.condition, options.segment, options.resume)
