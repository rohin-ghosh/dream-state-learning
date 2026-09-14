"""Bounded paired native collection; no shared outcome reducer or fitting."""

import argparse
import json
import os
from pathlib import Path
import time

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_math_replication as policy


def mounted_parameters(model):
    parameters = {name: parameter for name, parameter in model.named_parameters()
                  if '.lora_A.' in name or '.lora_B.' in name}
    if not parameters or any(parameter.requires_grad for _, parameter in model.named_parameters()):
        raise ValueError('frozen_named_parameters_required')
    return parameters


def run_task(task, position, generate):
    calls = {kind: generate(task, kind) for kind in policy.initial_order(position)}
    solved = calls['rich']
    if not solved['outcome_pass'] and not solved['call'].get('error'):
        solved = generate(task, 'correction', solved['target'])
    if solved['outcome_pass']:
        generate(task, 'record', solved['target'])


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'tasks', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--phase', choices=('prepare', 'native'), required=True)
    parser.add_argument('--shard', type=int, choices=range(3), default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--seconds', type=int, default=2670)
    options = parser.parse_args()
    if not 0 < options.seconds <= 2670:
        raise ValueError('finite_bound_required')
    if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
        raise ValueError('offline_required')
    if options.phase == 'prepare' and os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('cpu_preparation_requires_empty_cvd')
    options.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    document = json.loads(options.tasks.read_text())
    tasks = policy.validate_cohort(document)
    binding = dict(arguments={key: str(value) if isinstance(value, Path) else value
                              for key, value in vars(options).items()},
                   started_unix=time.time(), pid=os.getpid(),
                   cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                   tasks_sha256=policy.sha256(options.tasks),
                   driver_sha256=policy.sha256(Path(__file__)),
                   policy_sha256=policy.sha256(Path(policy.__file__)),
                   manifest_sha256=policy.MANIFEST_SHA256, fits=0, updates=0)
    policy.write(options.output / 'REQUEST.json', binding)
    rows = []

    def check(label):
        if time.monotonic() - started >= options.seconds:
            raise TimeoutError('finite_native_deadline:' + label)

    try:
        binding['base_verification'] = portable.verify_base_files(
            options.bundle, options.model_dir, expected_manifest_sha256=policy.MANIFEST_SHA256)
        if options.phase == 'prepare':
            policy.write(options.output / 'PREPARED.json', dict(binding, status='PREPARED_CPU_ONLY',
                                                               model_calls=0))
            return
        if not options.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != options.gpu_uuid:
            raise ValueError('exact_uuid_required')
        if ('CUDA_VISIBLE_DEVICES=' + options.gpu_uuid).encode() not in Path('/proc/self/environ').read_bytes().split(b'\0'):
            raise ValueError('physical_cvd_environ_required')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=policy.MANIFEST_SHA256,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, portable.source.native.load_local_tokenizer(options.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_parameters(engine.model)
        if _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('mounted_adapter_hash_mismatch')
        policy.write(options.output / 'ACTOR_READY.json', dict(binding, runtime=engine.runtime,
                                                              adapter_state=portable.PARENT_STATE))
        max_calls = 4 * sum(position % 3 == options.shard for position in range(32))

        def generate(task, kind, previous=None):
            check('call')
            if len(rows) >= max_calls:
                raise ValueError('shard_call_cap')
            messages, student = policy.prompt(task, kind, previous)
            encoded = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                        add_generation_prompt=True, return_dict=False)
            if not 0 < len(encoded) <= 2048 or len(messages) > 6:
                result = dict(messages=messages, prompt_tokens=len(encoded), token_ids=[],
                              raw='', terminal=False, truncated=False, error='PROMPT_CONTRACT_FAILURE')
            else:
                result = engine.generate(messages, max_new_tokens=64 if kind == 'terse' else 512)
            row = policy.capture(task, kind, result, student)
            rows.append(row)
            policy.write(options.output / f'CALL_{len(rows):04d}.json', row)
            return row

        for position, task in enumerate(tasks):
            if position % 3 == options.shard:
                run_task(task, position, generate)
        engine.verify_base()
        if _state_hash(parameters) != portable.PARENT_STATE:
            raise ValueError('mounted_adapter_changed')
        policy.write(options.output / 'COMPLETE.json', dict(binding, status='COMPLETE',
                     model_calls=len(rows), finished_unix=time.time(), runtime=engine.runtime,
                     adapter_state=portable.PARENT_STATE, frozen_base_unchanged=True))
    except BaseException as error:
        policy.write(options.output / 'FAILED.json', dict(binding, status='FAILED', model_calls=len(rows),
                     error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


if __name__ == '__main__':
    main()
