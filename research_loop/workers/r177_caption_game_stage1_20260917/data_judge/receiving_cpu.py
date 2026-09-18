"""One immutable node4 CPU staging/test attempt; never a GPU training admission."""

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checksum(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for raw in iter(lambda: stream.read(1024**2), b''):
            result.update(raw)
    return result.hexdigest()


def write_once(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def verify_inventory(root, inventory, expected_host, now):
    require(root == root.resolve() and root.is_absolute(), 'canonical_receiving_root')
    require(inventory['schema'] == 'NY_RECEIVING_CPU_STAGE_INVENTORY_V1'
        and inventory['root'] == str(root) and inventory['host_sha256'] == expected_host,
        'exact_receiving_host_and_root')
    require(now < inventory['cpu_end_unix'] <= inventory['lease_safe_end_unix'], 'unchanged_lease_and_CPU_wall')
    require(type(inventory['cpu_seconds']) is int and 0 < inventory['cpu_seconds'] <= 180 and inventory['cpu_threads'] == 2
        and inventory['max_address_space_bytes'] == 16*1024**3, 'finite_CPU_only_bounds')
    lease_path = Path(inventory['lease']['path'])
    require(lease_path == lease_path.resolve() and lease_path.stat().st_size <= 65536
        and checksum(lease_path) == inventory['lease']['sha256'], 'unchanged_actual_machine_lease')
    require(json.loads(lease_path.read_bytes())['hard_end_unix'] == inventory['lease_safe_end_unix'], 'existing_lease_hardwall_only')
    total = 0
    for name, reference in inventory['files'].items():
        path = root/name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and path == path.resolve() and path.is_file(), 'regular_receiving_whitelist_path')
        require(path.stat().st_size == reference['bytes'] and checksum(path) == reference['sha256'], 'receiving_file_hash')
        total += reference['bytes']
    require(total <= 384*1024**2, 'bounded_receiving_payload')
    require(not inventory['historical_captions_included'] and not inventory['FINAL_included'], 'no_real_caption_or_FINAL_payload')
    return total


def run(root, expected_inventory_sha256):
    root = Path(root).resolve()
    inventory_path = root/'INVENTORY.json'
    require(checksum(inventory_path) == expected_inventory_sha256, 'bound_receiving_inventory')
    inventory = json.loads(inventory_path.read_bytes())
    host = hashlib.sha256(platform.node().encode()).hexdigest()
    verify_inventory(root, inventory, host, time.time())
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.environ.get('HF_HUB_OFFLINE') == '1'
        and os.environ.get('TRANSFORMERS_OFFLINE') == '1' and os.environ.get('PYTHONDONTWRITEBYTECODE') == '1',
        'CPU_only_offline_no_cache_mutation')
    gate = json.loads((root/'BUILDER_CPU_GATE.json').read_bytes())
    require(gate['schema'] == 'NY_BUILDER_CPU_STAGING_GATE_V1' and gate['local_tests_passed'] >= 115
        and gate['scope'] == 'NODE4_OWN_SCRATCH_CPU_TESTS_ONLY_NOT_GPU_GO', 'prior_Builder_local_CPU_gate')
    for name in ('gpu/ny_caption_data.py', 'gpu/ny_caption_judge.py'):
        require(gate['source_sha256'][name] == inventory['files'][name]['sha256'], 'source_pinned_to_prior_CPU_gate')
    write_once(root/'ATTEMPT_STARTED.json', dict(inventory_sha256=expected_inventory_sha256,
        started_unix=time.time(), CPU_only=True, no_automatic_retry=True))
    started = time.time()
    try:
        result = subprocess.run([sys.executable, '-B', '-m', 'pytest', 'tests/test_ny_caption_data.py',
            'tests/test_ny_caption_judge.py', '-q', '-p', 'no:cacheprovider'], cwd=root,
            capture_output=True, text=True, timeout=60, check=False)
        require(len(result.stdout)+len(result.stderr) <= 1024**2, 'bounded_receiving_test_output')
        write_once(root/'CPU_TESTS.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
        require(result.returncode == 0, 'actual_receiving_CPU_suite_failed')
        resource.setrlimit(resource.RLIMIT_AS, (inventory['max_address_space_bytes'], inventory['max_address_space_bytes']))
        def block_network(event, arguments):
            if event in ('socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.sendto'):
                raise PermissionError('CPU_receiving_model_proof_network_forbidden')
        sys.addaudithook(block_network)
        import torch
        import transformers
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from gpu import ny_caption_data as data
        from gpu import ny_caption_judge as judge
        torch.set_num_threads(2)
        torch.set_num_interop_threads(2)
        torch.manual_seed(177)
        require(not torch.cuda.is_initialized(), 'CUDA_not_initialized')
        model_root = root/'model'
        tokenizer = AutoTokenizer.from_pretrained(str(model_root), local_files_only=True, trust_remote_code=False)
        texts = [judge.canonical_input('A synthetic room contains a desk and two standing figures.', 'A synthetic test sentence.'),
            judge.canonical_input('A synthetic garden contains a chair beside a small tree.', 'Another synthetic test sentence.')]
        inputs = tokenizer(texts, padding=True, truncation=False, return_tensors='pt')
        require(inputs['input_ids'].shape[-1] <= 128, 'bounded_synthetic_model_input')
        humor = judge.load_pretrained_classifier(AutoModelForSequenceClassification, model_root, 3, 'cpu')
        fit = judge.load_pretrained_classifier(AutoModelForSequenceClassification, model_root, 2, 'cpu')
        require(all(parameter.device.type == 'cpu' for model in (humor, fit) for parameter in model.parameters()), 'all_parameters_CPU_only')
        logits = humor(**inputs).logits
        target = torch.tensor([judge.soft_target([7, 2, 1], 0.5), judge.soft_target([2, 4, 4], 0.5)], dtype=logits.dtype)
        weights = torch.tensor([judge.vote_weight(10, 100)]*2, dtype=logits.dtype)
        loss = (-(target*torch.log_softmax(logits, dim=-1)).sum(dim=-1)*weights).sum()/weights.sum()
        require(bool(torch.isfinite(loss)), 'finite_synthetic_soft_loss')
        optimizer = torch.optim.AdamW(humor.parameters(), lr=0.00002)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        require(any(parameter.grad is not None for parameter in humor.parameters()), 'actual_CPU_backward')
        optimizer.step()
        with torch.no_grad():
            fit_logits = fit(**inputs).logits
        require(tuple(logits.shape) == (2, 3) and tuple(fit_logits.shape) == (2, 2)
            and bool(torch.isfinite(fit_logits).all()) and not torch.cuda.is_initialized(), 'two_separate_CPU_heads_no_CUDA')
        require(time.time() < inventory['cpu_end_unix'] and time.time()-started < inventory['cpu_seconds'], 'CPU_proof_wall')
        verify_inventory(root, inventory, host, time.time())
        receipt = dict(schema='NY_ACTUAL_NODE4_RECEIVING_CPU_PROOF_V1', status='PASS_CPU_ONLY_NOT_JUDGE_TRAINED',
            inventory_sha256=expected_inventory_sha256, model_files={name: reference for name, reference in inventory['files'].items() if name.startswith('model/')},
            source_files={name: reference for name, reference in inventory['files'].items() if name.startswith('gpu/')},
            runtime_versions={name: version(name) for name in ('torch', 'transformers', 'safetensors')},
            runtime_python=sys.executable, hostname_sha256=host, elapsed_seconds=time.time()-started,
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            actual_CPU_model_loads=2, synthetic_optimizer_steps=1, actual_training_caption_rows=0,
            GPU_calls=0, CUDA_initialized=False, provider_calls=0, trained_checkpoint=None,
            human_validated=False, FINAL_consumed=False, completed_unix=time.time())
        import inspect
        receipt['loaded_runtime_files'] = {name: dict(path=str(Path(path).resolve()), sha256=checksum(Path(path).resolve()))
            for name, path in [('torch', torch.__file__), ('transformers', transformers.__file__),
                ('humor_classifier', inspect.getfile(type(humor))), ('scene_fit_classifier', inspect.getfile(type(fit))),
                ('tokenizer', inspect.getfile(type(tokenizer)))]}
        write_once(root/'RECEIVING_CPU_PROOF.json', receipt)
        print(json.dumps(dict(status=receipt['status'],receipt_path=str(root/'RECEIVING_CPU_PROOF.json'),
            receipt_sha256=checksum(root/'RECEIVING_CPU_PROOF.json'))))
    except BaseException as error:
        write_once(root/'FAILED.json', dict(status='FAILED_PRESERVED_NO_AUTOMATIC_RETRY', error_type=type(error).__name__,
            error=str(error)[:4000], observed_unix=time.time(), elapsed_seconds=time.time()-started))
        print(json.dumps(dict(status='FAILED_PRESERVED_NO_AUTOMATIC_RETRY', error_type=type(error).__name__)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--inventory-sha256', required=True)
    arguments = parser.parse_args()
    run(arguments.root, arguments.inventory_sha256)
