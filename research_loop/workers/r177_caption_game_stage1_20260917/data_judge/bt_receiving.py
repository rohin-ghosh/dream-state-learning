"""R171 CPU provenance and strict physical2-only scalar-ranker execution."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_ranker as ranker
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import physical2_confinement as confinement
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import released_receiving as receiving


MODULE = 'research_loop.workers.r177_caption_game_stage1_20260917.data_judge.bt_receiving'


def validate_config(config):
    data.require(config['schema'] == 'NY_R171_BT_TRAIN_CONFIG_V1'
        and config['objective'] == 'BRADLEY_TERRY_WEIGHTED_LOGISTIC'
        and config['label_policy'] == ranker.LABEL_POLICY and config['pair_policy'] == ranker.PAIR_POLICY
        and config['reliability_policy'] == ranker.RELIABILITY_POLICY, 'registered_R171_BT_contract')
    data.require(0 < config['max_updates'] <= 1000 and 0 < config['batch_pairs'] <= 2
        and 0 < config['gradient_accumulation'] <= 4 and 600 < config['max_seconds'] <= 2400
        and config['calibration_reserve_seconds'] == 600 and config['max_length'] == 512
        and config['heldout_per_contest'] == 64 and config['learning_rate'] == 0.0001, 'bounded_R171_recipe')
    data.require(config['humor_soft_CE_used'] is False and config['image_judge_training'] is False
        and config['development_reuse_provisional'] is True, 'retired_objectives_and_sealed_boundaries')


def verify_models(config):
    manifest = data.bound(config['base_model'])
    data.require(manifest['model_id'] == ranker.MODEL_ID and manifest['revision'] == ranker.MODEL_REVISION,
        'pinned_pretrained_Qwen_only')
    root = Path(manifest['root'])
    data.require({path.name for path in root.iterdir()} == set(manifest['files'])|{'BASE_MANIFEST.json'}, 'exact_Qwen_runtime_closure')
    for name, expected in manifest['files'].items():
        data.require(Path(name).name == name and name.endswith(('.json', '.txt', '.safetensors'))
            and data.file_ref(root/name) == expected, 'Qwen_runtime_file_hash')
    fit = data.bound(config['frozen_scene_fit'])
    data.require(fit['locked_judge_validation_consumed'] is False and fit['scene_fit_sampling_policy'] ==
        'UNIFORM_DISTINCT_SCENE_RECIPROCAL_PAIRS_V1', 'frozen_corrected_scene_fit_only_not_humor')
    for name, reference in fit['checkpoint'].items():
        if name.startswith(('scene_fit/', 'tokenizer/')):
            data.require(data.file_ref(reference['path']) == reference, 'frozen_scene_fit_hash')


def cpu(root, expected):
    inventory = receiving.verified(root, expected)
    config = data.bound(inventory['config'])
    validate_config(config)
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.environ.get('HF_HUB_OFFLINE') == '1', 'offline_CPU_gate')
    data.private_write(root/'CPU_ONCE.json', dict(started_unix=time.time(), inventory_sha256=expected, no_retry=True))
    tests = subprocess.run([sys.executable, '-B', '-m', 'pytest',
        'research_loop/workers/r177_caption_game_stage1_20260917/data_judge/test_bt_ranker.py', '-q', '-p', 'no:cacheprovider'],
        cwd=root, env=receiving.cpu_test_environment(root, inventory), capture_output=True, text=True, timeout=120)
    test_ref = data.private_write(root/'CPU_TESTS.json', dict(returncode=tests.returncode, stdout=tests.stdout, stderr=tests.stderr))
    data.require(tests.returncode == 0 and 'skipped' not in tests.stdout, 'actual_BT_and_Qwen_CPU_tests_no_skips')
    verify_models(config)
    import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    data.require(not torch.cuda.is_initialized(), 'CPU_gate_never_initializes_CUDA')
    base = data.bound(config['base_model'])
    tokenizer = AutoTokenizer.from_pretrained(base['root'], local_files_only=True, trust_remote_code=False)
    prepared = ranker.prepare(config, tokenizer)
    from gpu import ny_caption_judge as helpers
    stress_rows = helpers.balanced_scene_rows(prepared['held']['development_audit'], 40, config['seed']+6)
    cases = helpers.stress_cases(stress_rows, len(stress_rows), config['seed']+7)
    data.require(all(len(tokenizer(helpers.canonical_input(case['scene'], case['caption']), truncation=False)['input_ids'])
        <= config['max_length'] for case in cases), 'CPU_bound_actual_BT_stress_inputs')
    pair_ref = data.private_write(root/'PAIR_PLAN.private.json', prepared)
    data.require(not torch.cuda.is_initialized(), 'CPU_gate_never_initializes_CUDA')
    reference = data.private_write(root/'CPU_GATE.json', dict(status='PASS_R171_CPU_NOT_GPU', inventory_sha256=expected,
        config=inventory['config'], tests=test_ref, pair_plan=pair_ref, metadata=prepared['metadata'],
        CPU_tiny_Qwen_scalar_LoRA_gradient_and_reload_pass=True, real_7B_CPU_model_loaded=False,
        CUDA_initialized=False, completed_unix=time.time()))
    print(json.dumps(dict(status='PASS_R171_CPU_NOT_GPU', receipt=reference, metadata=prepared['metadata'])), flush=True)


def run(root, expected):
    inventory = receiving.verified(root, expected)
    config = data.bound(inventory['config'])
    validate_config(config)
    gate_ref = data.file_ref(root/'CPU_GATE.json')
    gate = data.bound(gate_ref)
    data.require(gate['status'] == 'PASS_R171_CPU_NOT_GPU' and gate['inventory_sha256'] == expected
        and gate['config'] == inventory['config'], 'actual_bound_R171_CPU_gate')
    verify_models(config)
    data.require(os.environ.get('CUDA_VISIBLE_DEVICES') == confinement.DEVICE, 'physical2_only')
    lock = open('/tmp/orch_r177_node4_physical2.lock', 'a+b')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    capacity = receiving.capacity(root, inventory)
    now = time.time()
    data.require(now+config['max_seconds']+60 < min(inventory['allocation_end_unix'], inventory['lease_safe_end_unix']),
        'unchanged_existing_allocation_must_fit')
    admission = dict(schema='NY_R171_BT_CAPACITY_ADMISSION_V1', issuer='Main/Astra delegated Builder',
        authority='Explicit Rohin170/171 relay and standing directives; not new inferred human ratification',
        config=inventory['config'], issued_unix=now, end_unix=now+config['max_seconds'],
        allocation_end_unix=inventory['allocation_end_unix'], lease_safe_end_unix=inventory['lease_safe_end_unix'],
        device_uuid=confinement.DEVICE, max_model_examples=100000, max_model_tokens=30000000,
        max_reserved_bytes=32*1024**3, max_gpu_seconds=config['max_seconds'], CPU_gate=gate_ref,
        source_sha256={name: reference['sha256'] for name, reference in inventory['files'].items() if name.endswith('.py') and not name.startswith('support/')},
        actual_capacity=capacity)
    admission_ref = data.private_write(root/'ADMISSION.json', admission)
    data.private_write(root/'DISPATCH_STARTED.json', dict(pid=os.getpid(),
        process_startticks=Path('/proc/self/stat').read_text().split(') ')[1].split()[19],
        started_unix=time.time(), admission=admission_ref, objective=config['objective']))
    result = ranker.train(config, admission, data.bound(gate['pair_plan']), root/'training')
    data.private_write(root/'COMPLETED.json', dict(status='PROVISIONAL_R171_BT_TRAINED_NOT_ACCEPTANCE_CLAIM', judge_config=result,
        completed_unix=time.time(), no_final_claim=True))
    lock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'dispatch-probe', 'dispatch-train', 'probe', 'train'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--unit')
    args = parser.parse_args()
    root, expected = Path(args.root).resolve(), args.inventory_sha256
    if args.mode.startswith('dispatch-'):
        mode = args.mode.removeprefix('dispatch-')
        inventory = receiving.verified(root, expected)
        config = data.bound(inventory['config'])
        gate = data.bound(data.file_ref(root/'CPU_GATE.json'))
        data.require(gate['status'] == 'PASS_R171_CPU_NOT_GPU' and gate['inventory_sha256'] == expected, 'gate_before_strict_dispatch')
        if mode == 'train':
            proof = data.bound(data.file_ref(root/'CONFINEMENT_CPU_PROOF.json'))
            data.require(proof['inventory_sha256'] == expected and proof['checks']['denied_foreign_minors'] == [0,2,3,4,5,6,7], 'actual_prior_foreign_device_denial')
        command = confinement.command(root, expected, mode, config['max_seconds'])
        command[command.index(confinement.MODULE)] = MODULE
        data.private_write(root/('OUTER_'+mode.upper()+'_COMMAND.json'), dict(command=command, command_sha256=data.digest(command), issued_unix=time.time()))
        raise SystemExit(subprocess.run(command).returncode)
    if args.mode == 'cpu':
        cpu(root, expected)
        return
    proof = confinement.verify(root, expected, args.unit)
    reference = data.private_write(root/('CONFINEMENT_CPU_PROOF.json' if args.mode == 'probe' else 'TRAIN_CONFINEMENT_PROOF.json'), proof)
    print(json.dumps(dict(status=proof['status'], receipt=reference, foreign_minors_denied=7)), flush=True)
    if args.mode == 'train':
        run(root, expected)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if isinstance(error, SystemExit):
            raise
        if '--root' in sys.argv:
            root = Path(sys.argv[sys.argv.index('--root')+1]).resolve()
            data.private_write(root/('FAILURE_'+str(time.time_ns())+'.json'),
                dict(status='FAILED_PRESERVED_NO_RETRY', error_type=type(error).__name__, reason=str(error)[:500], observed_unix=time.time()))
        raise
