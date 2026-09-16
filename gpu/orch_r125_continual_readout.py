"""Fresh-process, parent-free synthetic32 diagnostics of one native checkpoint.

run(plan_path, checkpoint_path, output_path) returns the COMPLETE receipt.
checkpoint_path accepts a checkpoint directory or its COMMIT.json. output_path
must be a new directory below plan.root/readouts, outside the source tree.
Only policy.messages(task) reaches the engine; no stream or optimizer is loaded.
The caller owns resident-model offload, subprocess creation, and RNG restoration.
"""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
import time
from types import SimpleNamespace

from organism_v6 import orch_r107_capability as policy


SCHEMA = 'R125_CONTINUAL_READOUT_V1'
SUITE_SHA256 = '32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c'
MAX_NEW_TOKENS = 512


def _load_engine(plan, checkpoint, check):
    import torch
    from gpu import astra_experienced_event_microloop as source

    policy.require(not torch.cuda.is_initialized(), 'fresh_process_without_resident_CUDA')
    tokenizer = source.native.load_local_tokenizer(plan['model_dir'])
    options = SimpleNamespace(model_dir=plan['model_dir'], device='cuda:0',
        phase='readout', expected_base_sha256=plan['base_sha256'],
        adapter_dir=checkpoint['adapter_path'], gpu_uuid=plan['gpu_uuid'])
    return source.Engine(options, tokenizer, check=check)


def _verify_device(engine, plan):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'],
        'one_bound_GPU_environment')
    policy.require(engine.torch.cuda.device_count() == 1, 'one_visible_GPU')
    observed = str(engine.torch.cuda.get_device_properties(0).uuid)
    if not observed.startswith('GPU-'):
        observed = 'GPU-' + observed
    policy.require(observed == plan['gpu_uuid'], 'CUDA_UUID_mismatch')
    return observed


def run(plan_path, checkpoint_path, output_path):
    from gpu import orch_guided_native as weights
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_capability_run import assert_condition, assert_readonly, readonly_condition

    plan_path = Path(plan_path).resolve(strict=True)
    plan_bytes = plan_path.read_bytes()
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
    policy.require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == plan_sha256,
        'admission_plan_SHA256_binding')
    plan = native.validate_plan(json.loads(plan_bytes))
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'],
        'one_bound_GPU_environment')
    checkpoint_path = Path(checkpoint_path).resolve(strict=True)
    if checkpoint_path.is_dir():
        checkpoint_path = (checkpoint_path / 'COMMIT.json').resolve(strict=True)
    root = Path(plan['root']).resolve()
    policy.require(checkpoint_path.name == 'COMMIT.json'
        and checkpoint_path.is_relative_to(root / 'checkpoints'), 'native_checkpoint_COMMIT_path')
    checkpoint_bytes = checkpoint_path.read_bytes()
    checkpoint_sha256 = hashlib.sha256(checkpoint_bytes).hexdigest()
    checkpoint = json.loads(checkpoint_bytes)
    policy.require(checkpoint['schema'] == native.SCHEMA, 'native_checkpoint_schema')
    policy.require(Path(checkpoint['adapter_path']).resolve() == checkpoint_path.parent / 'adapter'
        and Path(checkpoint['optimizer_rng_path']).resolve() == checkpoint_path.parent / 'optimizer_rng.pt',
        'checkpoint_local_artifacts')
    native.NativeChild.verify_checkpoint(checkpoint)
    output = Path(output_path).resolve()
    readouts = root / 'readouts'
    policy.require(output != readouts and output.is_relative_to(readouts)
        and not output.is_relative_to(Path(plan['source_root']).resolve()), 'separate_node_local_readouts')
    tasks = policy.tasks()
    policy.require(len(tasks) == 32 and policy.digest(tasks) == SUITE_SHA256, 'fixed_synthetic32_suite')

    def check(label):
        policy.require(time.time() < plan['hard_end_unix'], 'readout_wall:' + label)

    def verify_inputs():
        policy.require(native.sha(plan_path) == plan_sha256
            == os.environ.get('R125_ADMISSION_PLAN_SHA256'), 'admission_plan_SHA256_binding')
        policy.require(native.sha(checkpoint_path) == checkpoint_sha256, 'checkpoint_COMMIT_changed')
        native.NativeChild.verify_checkpoint(checkpoint)

    def snapshot(engine):
        assert_readonly(engine.model)
        assert_condition(engine.model, 'LORA_ON')
        policy.require(not engine.model.training, 'readout_eval_mode')
        device_uuid = _verify_device(engine, plan)
        engine.verify_base()
        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
            if weights.is_lora(name)}
        policy.require(bool(parameters), 'mounted_LoRA_required')
        adapter_sha256 = weights.state_hash(parameters)
        policy.require(adapter_sha256 == checkpoint['adapter_state_sha256'], 'immutable_checkpoint_adapter')
        verify_inputs()
        return dict(adapter_state_sha256=adapter_sha256, base_sha256=plan['base_sha256'],
            frozen_base_verified=True, checkpoint_files_verified=True, gpu_uuid=device_uuid,
            readonly=True)

    check('start')
    output.mkdir(parents=True, exist_ok=False)
    provenance = dict(schema=SCHEMA, pid=os.getpid(), ppid=os.getppid(),
        process=list(weights.process_identity()), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        plan_path=str(plan_path), plan_sha256=plan_sha256,
        checkpoint_path=str(checkpoint_path), checkpoint_commit_sha256=checkpoint_sha256,
        checkpoint_sha256=checkpoint['checkpoint_sha256'],
        adapter_state_sha256=checkpoint['adapter_state_sha256'],
        optimizer_steps=checkpoint['optimizer_steps'], base_sha256=plan['base_sha256'],
        suite_sha256=SUITE_SHA256, source=policy.SOURCE, output_path=str(output),
        gpu_uuid=plan['gpu_uuid'], max_new_tokens=MAX_NEW_TOKENS,
        decoder=dict(do_sample=False, num_beams=1, repetition_penalty=1.0),
        parent_present=False, history_present=False, train_ingestion=False, training_updates=0,
        raw_reasoning_preserved=True, started_unix=time.time())
    native.write_once(output / 'REQUEST.json', provenance)
    captures, call_files = [], {}
    before_after_verified = False

    def paired_scores():
        return policy.reduce_paired(captures, checkpoint_sha256=checkpoint['adapter_state_sha256'],
            base_sha256=plan['base_sha256'], max_new_tokens=MAX_NEW_TOKENS)

    try:
        engine = _load_engine(plan, checkpoint, check)
        before = None
        try:
            before = snapshot(engine)
            native.write_once(output / 'BEFORE.json', dict(before, status='PASS',
                pid=os.getpid(), observed_unix=time.time()))
            for position, task in enumerate(tasks):
                arms = ('ON', 'OFF') if position % 2 == 0 else ('OFF', 'ON')
                for arm in arms:
                    check('reserve')
                    messages = policy.messages(task)
                    condition = 'LORA_' + arm
                    name = f'CALL_{len(call_files):03d}.json'
                    record = dict(provenance, position=position, task_id=task['id'],
                        family=task['family'], arm=arm, condition=condition,
                        messages=deepcopy(messages), status='RESERVED', started_unix=time.time())
                    native.write_once(output / 'reservations' / name, record)
                    try:
                        with readonly_condition(engine.model, condition):
                            response = engine.generate(messages, max_new_tokens=MAX_NEW_TOKENS)
                        record['response'] = deepcopy(response)
                        policy.require(messages == policy.messages(task), 'public_messages_mutated')
                        policy.require('max_new_tokens' not in response
                            or response['max_new_tokens'] == MAX_NEW_TOKENS, 'fixed_cap512')
                        response = dict(response, max_new_tokens=MAX_NEW_TOKENS,
                            eos_token_id=engine.tokenizer.eos_token_id)
                        capture = policy.capture(task, arm, response,
                            checkpoint_sha256=checkpoint['adapter_state_sha256'],
                            base_sha256=plan['base_sha256'], lora_enabled=arm == 'ON')
                        captures.append(capture)
                        record.update(status='COMPLETE', response=response, capture=capture)
                    except BaseException as error:
                        capture = policy.capture(task, arm, dict(error=type(error).__name__),
                            checkpoint_sha256=checkpoint['adapter_state_sha256'],
                            base_sha256=plan['base_sha256'], lora_enabled=arm == 'ON')
                        captures.append(capture)
                        record.update(status='FAILED', error_type=type(error).__name__,
                            error=str(error), capture=capture)
                        raise
                    finally:
                        record['finished_unix'] = time.time()
                        native.write_once(output / name, record)
                        call_files[name] = native.sha(output / name)
        finally:
            try:
                after = snapshot(engine)
                policy.require(before is not None and after == before, 'before_after_identity_changed')
                before_after_verified = True
                native.write_once(output / 'AFTER.json', dict(after, status='PASS', unchanged=True,
                    pid=os.getpid(), observed_unix=time.time()))
            except BaseException as error:
                native.write_once(output / 'AFTER.json', dict(status='FAILED', unchanged=False,
                    error_type=type(error).__name__, error=str(error), pid=os.getpid(),
                    observed_unix=time.time()))
                raise
        check('complete')
        scores = paired_scores()
        policy.require(scores['recorded_cells'] == 64 and scores['all_cells_recorded'], 'all64_cells_required')
        complete = dict(provenance, status='COMPLETE', calls=len(call_files), call_files=call_files,
            task_count=32, before_after_verified=before_after_verified, paired_scores=scores,
            finished_unix=time.time())
        native.write_once(output / 'COMPLETE.json', complete)
        return complete
    except BaseException as error:
        failed = dict(provenance, status='FAILED',
            error_type=type(error).__name__, error=str(error), calls=len(call_files), call_files=call_files,
            before_after_verified=before_after_verified, finished_unix=time.time())
        try:
            failed['paired_scores'] = paired_scores()
        except Exception as reduction_error:
            failed['reduction_error'] = dict(error_type=type(reduction_error).__name__, error=str(reduction_error))
        native.write_once(output / 'FAILED.json', failed)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args(argv)
    run(options.plan, options.checkpoint, options.output)


if __name__ == '__main__':
    main()
