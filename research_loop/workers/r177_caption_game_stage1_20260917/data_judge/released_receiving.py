"""Rohin167 immutable receiving CPU gate and physical2-only development dispatch."""

import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import resource
import shutil
import signal
import subprocess
import sys
import time

from gpu import ny_caption_data as data
from gpu import ny_caption_judge as judge


DEVICE = 'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8'


def cpu_test_environment(root, inventory):
    data.require(inventory.get('test_support_directory') == 'support'
        and 'support/pytest/__init__.py' in inventory['files'], 'explicit_pinned_pytest_support')
    environment = dict(os.environ)
    environment.update(PYTHONPATH=str(root)+os.pathsep+str(root/'support'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    return environment


def verified(root, expected):
    reference = data.file_ref(root/'INVENTORY.json')
    data.require(reference['sha256'] == expected, 'exact_receiving_inventory')
    inventory = data.bound(reference)
    data.require(inventory['schema'] == 'NY_R167_RELEASED_RECEIVING_V1'
        and inventory['root'] == str(root)
        and inventory['hostname_sha256'] == hashlib.sha256(platform.node().encode()).hexdigest(), 'exact_receiving_host_root')
    data.require(time.time() < inventory['lease_safe_end_unix'], 'existing_lease_not_expired')
    lease = data.bound(inventory['lease'])
    data.require(lease['hard_end_unix'] == inventory['lease_safe_end_unix'], 'unchanged_machine_hardwall')
    data.require(sum(entry['bytes'] for entry in inventory['files'].values()) <= 512*1024**2,
        'bounded_authorized_receiving_data')
    for name, entry in inventory['files'].items():
        data.require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative_inventory_path')
        actual = data.file_ref(root/name)
        data.require(actual['sha256'] == entry['sha256'] and actual['bytes'] == entry['bytes'], 'receiving_file_pin')
    data.require(shutil.disk_usage(root).free >= 16*1024**3, 'receiving_checkpoint_disk_admission')
    return inventory


def cpu(root, expected):
    inventory = verified(root, expected)
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.environ.get('HF_HUB_OFFLINE') == '1'
        and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'CPU_only_offline_gate')
    data.private_write(root/'CPU_ONCE.json', dict(started_unix=time.time(), inventory_sha256=expected))
    result = subprocess.run([sys.executable, '-B', '-m', 'pytest', 'tests/test_ny_caption_data.py',
        'tests/test_ny_caption_judge.py', '-q', '-p', 'no:cacheprovider'], cwd=root,
        capture_output=True, text=True, timeout=120, check=False, env=cpu_test_environment(root, inventory))
    data.require(len(result.stdout)+len(result.stderr) <= 1024**2, 'bounded_CPU_test_output')
    test_ref = data.private_write(root/'CPU_TESTS.json', dict(returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr))
    data.require(result.returncode == 0, 'receiving_CPU_tests_pass')
    import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    data.require(not torch.cuda.is_initialized(), 'CPU_gate_no_CUDA')
    config = data.bound(inventory['config'])
    judge.validate_config(config)
    training, held, audit = judge.prepare_training_data(config)
    full_fitting_proof = None
    if config.get('fitting_policy') == judge.FULL_FITTING_POLICY:
        sampler = judge.FullContestPairSampler(training, config['seed'])
        schedule_hash, seen, ranked_pairs = hashlib.sha256(), set(), 0
        for unused in range(config['max_steps']):
            batch, pairs = sampler.sample(config['batch_size'])
            for row in batch:
                identity = row['contest_id']+':'+row['caption_family_sha256']
                data.require(identity not in seen, 'actual_fitting_schedule_without_duplicate_rows')
                seen.add(identity)
                schedule_hash.update((identity+'\n').encode())
            ranked_pairs += len(judge.ranking_terms(batch, pairs, config['smoothing'], config['vote_weight_cap']))
        logits = torch.zeros((2, 3), dtype=torch.float64, requires_grad=True)
        loss = judge.ranking_tensor_loss(logits, [(0, 1, 0.25, 0.5)], torch)
        loss.backward()
        data.require(abs(loss.item()-0.0625) < 1e-12 and logits.grad[0, 0] > 0 and logits.grad[1, 0] < 0,
            'actual_CPU_q_difference_gradient')
        full_fitting_proof = dict(eligible_fitting_rows=len(training), distinct_scheduled_rows=len(seen),
            scheduled_fraction=len(seen)/len(training), paired_rows=2*ranked_pairs,
            schedule_sha256=schedule_hash.hexdigest(), actual_CPU_gradient_pass=True,
            auxiliary_weight=config['ranking_auxiliary_weight'], no_replacement=True, full_epoch_claim=False)
    model = data.bound(config['local_model_manifest'])
    for name, checksum in model['files'].items():
        data.require(data.file_ref(Path(model['root'])/name)['sha256'] == checksum, 'actual_pretrained_file_pin')
    tokenizer = AutoTokenizer.from_pretrained(model['root'], local_files_only=True, trust_remote_code=False)
    maximum, total = 0, 0
    for rows in [training, audit, *held.values()]:
        for start in range(0, len(rows), 128):
            encoded = tokenizer([judge.canonical_input(row['scene'], row['caption']) for row in rows[start:start+128]],
                truncation=False, padding=False)['input_ids']
            maximum = max(maximum, max(map(len, encoded)))
            total += len(encoded)
    data.require(maximum <= config['max_length'], 'actual_data_no_model_truncation')
    sampler, generator = judge.SceneFitSampler(training), random.Random(config['seed']+1)
    positive_scenes, negative_scenes = Counter(), Counter()
    maximum_negative = 0
    for unused in range(100):
        positives, negatives = sampler.sample(config['batch_size'], generator)
        data.require(all(judge.distinct_scene(positive, negative) and positive['caption'] == negative['caption']
            for positive, negative in zip(positives, negatives)), 'actual_negative_scene_disjointness')
        positive_scenes.update(row['scene'] for row in positives)
        negative_scenes.update(row['scene'] for row in negatives)
        encoded = tokenizer([judge.canonical_input(row['scene'], row['caption']) for row in negatives],
            truncation=False, padding=False)['input_ids']
        maximum_negative = max(maximum_negative, max(map(len, encoded)))
    data.require(positive_scenes == negative_scenes and maximum_negative <= config['max_length'],
        'actual_fit_marginal_balance_and_no_truncation')
    threshold_rows = held['threshold_selection']
    threshold_negatives = judge.swapped_rows(threshold_rows, config['seed']+5)
    data.require(Counter(row['scene'] for row in threshold_rows) == Counter(row['scene'] for row in threshold_negatives),
        'actual_threshold_scene_marginal_balance')
    stress_rows = judge.balanced_scene_rows(audit, config['stress_examples'], config['seed']+6)
    challenges = judge.stress_cases(stress_rows, len(stress_rows), config['seed']+7)
    swaps = [case for case in challenges if case['kind'] == 'scene_swap']
    data.require(Counter(row['original']['scene'] for row in swaps) == Counter(row['scene'] for row in swaps),
        'actual_stress_scene_marginal_balance')
    challenge_tokens = tokenizer([judge.canonical_input(row['scene'], row['caption']) for row in challenges],
        truncation=False, padding=False)['input_ids']
    max_challenge_tokens = max(map(len, challenge_tokens))
    data.require(max_challenge_tokens <= config['max_length'], 'actual_stress_no_input_truncation')
    data.require(not torch.cuda.is_initialized(), 'CPU_gate_no_CUDA')
    counts = dict(judge_train=len(training), development_audit=len(audit), **{name: len(rows) for name, rows in held.items()})
    reference = data.private_write(root/'CPU_GATE.json', dict(schema='NY_R167_ACTUAL_RECEIVING_CPU_GATE_V1',
        status='PASS_CPU_NOT_TRAINING', config=inventory['config'], inventory_sha256=expected,
        tests=test_ref, counts=counts, max_input_tokens=maximum, tokenized_rows=total, CUDA_initialized=False,
        scene_fit_sampling_policy=judge.SCENE_FIT_SAMPLING_POLICY, actual_sampler_batches=100,
        positive_negative_scene_marginals_equal=True, negative_unique_scenes=len(negative_scenes), max_negative_tokens=maximum_negative,
        threshold_scene_marginals_equal=True, threshold_negative_unique_scenes=len({row['scene'] for row in threshold_negatives}),
        stress_scene_marginals_equal=True, stress_negative_unique_scenes=len({row['scene'] for row in swaps}),
        max_challenge_tokens=max_challenge_tokens, calibration_stress_scene_swap_policy=judge.SCENE_SWAP_POLICY,
        full_fitting_proof=full_fitting_proof,
        source_sha256={name: inventory['files']['gpu/'+name]['sha256'] for name in ('ny_caption_data.py', 'ny_caption_judge.py')},
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, completed_unix=time.time()))
    print(json.dumps(dict(status='PASS_CPU_NOT_TRAINING', receipt=reference, counts=counts, max_input_tokens=maximum)), flush=True)


def capacity(root, inventory):
    result = subprocess.run(['/usr/bin/nvidia-smi', '-i', DEVICE,
        '--query-gpu=index,uuid,memory.free,utilization.gpu', '--format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=15, check=True)
    values = [part.strip() for part in result.stdout.strip().split(',')]
    apps = subprocess.run(['/usr/bin/nvidia-smi', '-i', DEVICE,
        '--query-compute-apps=gpu_uuid,pid,used_memory', '--format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=15, check=True)
    data.require(len(values) == 4 and values[0] in ('0', '2') and values[1] == DEVICE
        and int(values[2])*1024**2 >= 32*1024**3 and int(values[3]) == 0 and not apps.stdout.strip(),
        'fresh_physical2_idle_admission')
    return dict(device_uuid=DEVICE, physical=2, nvml_visible_index=int(values[0]), free_mib=int(values[2]), utilization=int(values[3]),
        compute_processes=[], observed_unix=time.time(), lease=inventory['lease'],
        disk_free_bytes=shutil.disk_usage(root).free)


def run(root, expected):
    inventory = verified(root, expected)
    gate_ref = data.file_ref(root/'CPU_GATE.json')
    gate = data.bound(gate_ref)
    data.require(gate['status'] == 'PASS_CPU_NOT_TRAINING' and gate['inventory_sha256'] == expected
        and gate['config'] == inventory['config'], 'bound_receiving_CPU_gate_before_GPU')
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == DEVICE, 'only_assigned_physical2')
    config = data.bound(inventory['config'])
    lock = open('/tmp/orch_r177_node4_physical2.lock', 'a+b')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    probe = capacity(root, inventory)
    now = time.time()
    allocation_end = min(inventory['lease_safe_end_unix'], inventory.get('allocation_end_unix', inventory['lease_safe_end_unix']))
    data.require(now + config['max_seconds'] + 60 < allocation_end, 'finite_run_inside_existing_hardwall')
    admission = dict(schema='NY_JUDGE_CAPACITY_ADMISSION_V1', issuer='Main/Astra builder',
        scope='R177_STAGE1_JUDGE_TRAINING_ONLY', authority='Ampere delegated Builder under Rohin167 and standing directives; not new human ratification',
        config=inventory['config'], source_sha256=gate['source_sha256'], issued_unix=now,
        end_unix=now+config['max_seconds'], lease_safe_end_unix=inventory['lease_safe_end_unix'],
        max_gpu_seconds=config['max_seconds'], max_steps=config['max_steps'], device='cuda:0', device_uuid=DEVICE,
        output_root=str(root/'training'), min_free_bytes=32*1024**3, max_reserved_bytes=20*1024**3,
        max_model_examples=600000, max_model_tokens=300000000, CPU_gate=gate_ref, actual_capacity=probe)
    admission_ref = data.private_write(root/'ADMISSION.json', admission)
    data.private_write(root/'DISPATCH_STARTED.json', dict(status='DISPATCHED_NOT_YET_TRAINING', pid=os.getpid(),
        process_startticks=Path('/proc/self/stat').read_text().split(') ')[1].split()[19],
        started_unix=time.time(), config=inventory['config'], admission=admission_ref, counts=gate['counts']))
    def wall_expired(signum, frame):
        raise TimeoutError('fixed_admitted_development_wall')
    signal.signal(signal.SIGALRM, wall_expired)
    signal.alarm(config['max_seconds'])
    try:
        result = judge.train(inventory['config'], admission_ref, root/'training')
        data.private_write(root/'COMPLETED.json', dict(status='DEVELOPMENT_TRAINED_PROVISIONAL', judge_config=result,
            completed_unix=time.time(), no_final_claim=True))
        print(json.dumps(dict(status='DEVELOPMENT_TRAINED_PROVISIONAL', judge_config=result)), flush=True)
    finally:
        signal.alarm(0)
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'train'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--inventory-sha256', required=True)
    arguments = parser.parse_args()
    target = Path(arguments.root).resolve()
    try:
        (cpu if arguments.mode == 'cpu' else run)(target, arguments.inventory_sha256)
    except BaseException as error:
        data.private_write(target/(arguments.mode.upper()+'_FAILURE.json'), dict(status='FAILED_PRESERVED_NO_AUTOMATIC_RETRY',
            error_type=type(error).__name__, observed_unix=time.time()))
        print(json.dumps(dict(status='FAILED_PRESERVED_NO_AUTOMATIC_RETRY', error_type=type(error).__name__)), flush=True)
        raise
