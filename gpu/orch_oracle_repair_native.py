"""Bounded native oracle-repair collection using the frozen portable Engine."""

import argparse
import json
import os
from pathlib import Path
import sys
import time

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_math_replication_native import mounted_parameters
from organism_v6 import orch_oracle_repair as policy


def run_task(task, generate):
    for branch in task['branch_order']:
        repair = generate(task, branch, 'repair')
        if repair['outcome_pass']:
            generate(task, branch, 'record', repair['target'])


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'roster', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--phase', choices=('prepare', 'native'), required=True)
    parser.add_argument('--shard', type=int, choices=range(4), default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline', type=float)
    options = parser.parse_args()
    if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
        raise ValueError('offline_required')
    if options.phase == 'prepare' and os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('cpu_prepare_requires_empty_cvd')
    if sys.executable != '/localhome/local-rohing/v2/venv/bin/python':
        raise ValueError('exact_verified_native_interpreter_required')
    options.output.mkdir(exist_ok=False)
    document = json.loads(options.roster.read_text())
    tasks = policy.validate_roster(document)
    rows = []
    binding = dict(started_unix=time.time(), pid=os.getpid(), shard=options.shard,
                   python=sys.executable, cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                   roster_sha256=policy.sha256(options.roster),
                   driver_sha256=policy.sha256(Path(__file__)),
                   policy_sha256=policy.sha256(Path(policy.__file__)), fits=0, updates=0)
    policy.write(options.output / 'REQUEST.json', binding)

    def check(label):
        if options.phase == 'native' and (options.deadline is None or time.time() >= options.deadline):
            raise TimeoutError('native_deadline:' + label)

    try:
        check('begin')
        binding['base_verification'] = portable.verify_base_files(
            options.bundle, options.model_dir, expected_manifest_sha256=policy.MANIFEST_SHA256)
        if options.phase == 'prepare':
            tokenizer = portable.source.native.load_local_tokenizer(options.model_dir)
            prompt_lengths = []
            for task in tasks:
                for branch in policy.BRANCHES:
                    messages, student = policy.prompt(task, branch, 'repair')
                    prompt_lengths.append(len(tokenizer.apply_chat_template(
                        messages, tokenize=True, add_generation_prompt=True, return_dict=False)))
            if max(prompt_lengths) > 2048:
                raise ValueError('prospective_prompt_budget_failure')
            policy.write(options.output / 'PREPARED.json', dict(binding, status='CPU_PREPARED',
                         native_calls=0, manifest_sha256=policy.MANIFEST_SHA256,
                         repair_prompt_lengths=prompt_lengths))
            return
        if (not options.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES') != options.gpu_uuid
                or ('CUDA_VISIBLE_DEVICES=' + options.gpu_uuid).encode() not in
                Path('/proc/self/environ').read_bytes().split(b'\0')):
            raise ValueError('physical_uuid_environ_required')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=policy.MANIFEST_SHA256,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, portable.source.native.load_local_tokenizer(options.model_dir),
                                        check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_parameters(engine.model)
        actual = _state_hash(parameters)
        if actual != portable.PARENT_STATE:
            raise ValueError('actual_mounted_named_parameters_not_37ec')
        hashes = {name: _state_hash({name: parameter}) for name, parameter in parameters.items()}
        policy.write(options.output / 'MOUNTED.json', dict(binding, actual_adapter_state=actual,
                     per_named_parameter_hashes=hashes, runtime=engine.runtime,
                     source='actual_model_named_parameters_not_peft_export'))
        shard_tasks = [task for task in tasks if task['shard'] == options.shard]

        def generate(task, branch, kind, repair_raw=None):
            check('call')
            if len(rows) >= 4 * len(shard_tasks):
                raise ValueError('native_shard_call_cap')
            messages, student = policy.prompt(task, branch, kind, repair_raw)
            encoded = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                        add_generation_prompt=True, return_dict=False)
            prefix_ids = engine.tokenizer.apply_chat_template(student, tokenize=True,
                        add_generation_prompt=True, return_dict=False)
            if not 0 < len(encoded) <= 2048 or len(messages) > 6:
                result = dict(messages=messages, prompt_tokens=len(encoded), token_ids=[],
                              raw='', terminal=False, truncated=False, error='PROMPT_CONTRACT_FAILURE')
            else:
                result = engine.generate(messages, max_new_tokens=512)
            row = policy.capture(task, branch, kind, result, student, prefix_ids)
            rows.append(row)
            policy.write(options.output / f'CALL_{len(rows):04d}.json', row)
            return row

        for task in shard_tasks:
            run_task(task, generate)
        engine.verify_base()
        final = _state_hash(mounted_parameters(engine.model))
        if final != actual:
            raise ValueError('mounted_state_changed')
        policy.write(options.output / 'COMPLETE.json', dict(binding, status='COMPLETE',
                     native_calls=len(rows), finished_unix=time.time(), adapter_state=final,
                     frozen_base_unchanged=True, runtime=engine.runtime))
    except BaseException as error:
        policy.write(options.output / 'FAILED.json', dict(binding, status='FAILED',
                     native_calls=len(rows), finished_unix=time.time(),
                     error_type=type(error).__name__, error=str(error)))
        raise


if __name__ == '__main__':
    main()
