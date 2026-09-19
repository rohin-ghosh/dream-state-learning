"""Copy-only, birth-cued ON/OFF diagnostics; never a training or launch path.

run(plan_path, checkpoint_path, config_path, output_path) requires an admitted
native plan, a saved COMMIT, and three caller-authored open prompts. The caller
owns fresh-process/device-FD admission and resident offload. Results belong in a
fresh private directory under plan.root/behavior_readouts, never a parent inbox.
"""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

from organism_v6 import orch_r107_capability as policy
from gpu.orch_r125_continual_readout import _load_engine, _verify_device, MAX_NEW_TOKENS


SCHEMA = 'R186_BEHAVIOR_READOUT_V1'
PROMPT_IDS = ('continue', 'procedure', 'attention')
CONFIG_BINDING = 'R186_BEHAVIOR_CONFIG_SHA256'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_config(config):
    policy.require(type(config) is dict and set(config) == {'schema', 'prompts'}
        and config['schema'] == SCHEMA, 'behavior_config_schema')
    prompts = config['prompts']
    policy.require(type(prompts) is list and len(prompts) == 3, 'exactly_three_open_prompts')
    for expected, prompt in zip(PROMPT_IDS, prompts):
        policy.require(type(prompt) is dict and set(prompt) == {'id', 'text'}
            and prompt['id'] == expected, 'ordered_unique_prompt_ids')
        policy.require(type(prompt['text']) is str and bool(prompt['text'].strip())
            and len(prompt['text'].encode('utf-8')) <= 16384, 'bounded_nonempty_prompt')
    return deepcopy(config)


def messages(plan, prompt):
    return [dict(role='system', content=plan['system_prompt']),
        dict(role='user', content=plan['birth_prompt']),
        dict(role='user', content=prompt['text'])]


def _torch():
    import torch
    return torch


@contextmanager
def _preserve_rng(torch, *, cuda=False):
    python_state = random.getstate()
    cpu_state = torch.get_rng_state().clone()
    numpy = sys.modules.get('numpy')
    numpy_state = deepcopy(numpy.random.get_state()) if numpy is not None else None
    cuda_states = [state.clone() for state in torch.cuda.get_rng_state_all()] if cuda else None
    receipt = dict(restored=False, cuda=cuda, numpy=numpy is not None)
    try:
        yield receipt
    finally:
        random.setstate(python_state)
        torch.set_rng_state(cpu_state)
        if numpy is not None:
            numpy.random.set_state(numpy_state)
        if cuda:
            torch.cuda.set_rng_state_all(cuda_states)
        policy.require(random.getstate() == python_state
            and torch.equal(torch.get_rng_state(), cpu_state), 'CPU_RNG_restoration')
        if numpy is not None:
            observed = numpy.random.get_state()
            policy.require(observed[0] == numpy_state[0]
                and numpy.array_equal(observed[1], numpy_state[1])
                and observed[2:] == numpy_state[2:], 'numpy_RNG_restoration')
        if cuda:
            observed = torch.cuda.get_rng_state_all()
            policy.require(len(observed) == len(cuda_states)
                and all(torch.equal(actual, expected)
                    for actual, expected in zip(observed, cuda_states)), 'CUDA_RNG_restoration')
        receipt['restored'] = True


def _write_once(path, document):
    payload = (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _validate_response(response, expected, tokenizer):
    policy.require(type(response) is dict and response['messages'] == expected,
        'exact_birth_only_context')
    token_ids = response['token_ids']
    policy.require(type(token_ids) is list and 0 < len(token_ids) <= MAX_NEW_TOKENS
        and all(type(token) is int and token >= 0 for token in token_ids), 'actual_bounded_token_ids')
    policy.require(type(response['prompt_tokens']) is int and response['prompt_tokens'] > 0,
        'actual_prompt_token_count')
    policy.require(type(response['terminal']) is bool and type(response['truncated']) is bool
        and response['terminal'] == (token_ids[-1] == tokenizer.eos_token_id)
        and response['truncated'] == (not response['terminal'] and len(token_ids) == MAX_NEW_TOKENS),
        'exact_terminal_metadata')
    visible = token_ids[:-1] if response['terminal'] else token_ids
    policy.require(type(response['raw']) is str and response['raw'] == tokenizer.decode(
        visible, skip_special_tokens=False, clean_up_tokenization_spaces=False), 'exact_raw_decoder')
    policy.require(response.get('max_new_tokens', MAX_NEW_TOKENS) == MAX_NEW_TOKENS, 'fixed_cap512')
    return dict(generated_tokens=len(token_ids), content_tokens=len(visible),
        prefix_labels=[-100] * response['prompt_tokens'], generated_labels=[-100] * len(token_ids),
        target_tokens=0, train_ingestion=False)


def run(plan_path, checkpoint_path, config_path, output_path):
    from gpu import orch_guided_native as weights
    from gpu import orch_r125_continual_native as native
    from gpu import orch_r107_capability_run as switching

    plan_path = Path(plan_path).resolve(strict=True)
    config_path = Path(config_path).resolve(strict=True)
    plan_sha256, config_sha256 = _sha(plan_path), _sha(config_path)
    policy.require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == plan_sha256,
        'admission_plan_SHA256_binding')
    policy.require(os.environ.get(CONFIG_BINDING) == config_sha256, 'behavior_config_SHA256_binding')
    plan = native.validate_plan(json.loads(plan_path.read_bytes()))
    config = validate_config(json.loads(config_path.read_bytes()))
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_bound_GPU_environment')
    root = Path(plan['root']).resolve()
    checkpoint_path = Path(checkpoint_path).resolve(strict=True)
    if checkpoint_path.is_dir():
        checkpoint_path = (checkpoint_path / 'COMMIT.json').resolve(strict=True)
    policy.require(checkpoint_path.name == 'COMMIT.json'
        and checkpoint_path.is_relative_to(root / 'checkpoints'), 'native_checkpoint_COMMIT_path')
    checkpoint_sha256 = _sha(checkpoint_path)
    checkpoint = json.loads(checkpoint_path.read_bytes())
    policy.require(checkpoint['schema'] == native.SCHEMA, 'native_checkpoint_schema')
    policy.require(Path(checkpoint['adapter_path']).resolve() == checkpoint_path.parent / 'adapter'
        and Path(checkpoint['optimizer_rng_path']).resolve() == checkpoint_path.parent / 'optimizer_rng.pt',
        'checkpoint_local_artifacts')
    native.NativeChild.verify_checkpoint(checkpoint)
    output = Path(output_path).resolve()
    readouts = root / 'behavior_readouts'
    policy.require(output.parent == readouts
        and not output.is_relative_to(Path(plan['source_root']).resolve()), 'separate_private_behavior_readouts')
    source_root = Path(__file__).resolve().parents[1]
    source_names = (Path(__file__).name, 'orch_r125_continual_readout.py',
        'astra_experienced_event_microloop.py', 'orch_r107_capability_run.py',
        'orch_r125_continual_native.py', 'orch_guided_native.py')
    sources = {str(source_root / 'gpu' / name): _sha(source_root / 'gpu' / name) for name in source_names}
    sources[str(Path(policy.__file__).resolve())] = _sha(policy.__file__)

    def check(label):
        policy.require(time.time() < plan['hard_end_unix'], 'readout_wall:' + label)

    def verify_inputs():
        policy.require(_sha(plan_path) == plan_sha256 == os.environ.get('R125_ADMISSION_PLAN_SHA256'),
            'admission_plan_SHA256_binding')
        policy.require(_sha(config_path) == config_sha256 == os.environ.get(CONFIG_BINDING),
            'behavior_config_SHA256_binding')
        policy.require(_sha(checkpoint_path) == checkpoint_sha256, 'checkpoint_COMMIT_changed')
        policy.require(all(_sha(path) == expected for path, expected in sources.items()), 'readout_source_changed')
        native.NativeChild.verify_checkpoint(checkpoint)

    def snapshot(engine):
        switching.assert_readonly(engine.model)
        switching.assert_condition(engine.model, 'LORA_ON')
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
            readonly=True, eval_mode=True)

    check('start')
    readouts.mkdir(mode=0o700, exist_ok=True)
    output.mkdir(mode=0o700, exist_ok=False)
    (output / 'reservations').mkdir(mode=0o700)
    provenance = dict(schema=SCHEMA, pid=os.getpid(), process=list(weights.process_identity()),
        plan_path=str(plan_path), plan_sha256=plan_sha256, config_path=str(config_path),
        config_sha256=config_sha256, checkpoint_path=str(checkpoint_path),
        checkpoint_commit_sha256=checkpoint_sha256, adapter_state_sha256=checkpoint['adapter_state_sha256'],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], optimizer_steps=checkpoint['optimizer_steps'],
        base_sha256=plan['base_sha256'], sources=sources, output_path=str(output), gpu_uuid=plan['gpu_uuid'],
        max_new_tokens=MAX_NEW_TOKENS,
        decoder=dict(do_sample=False, num_beams=1, use_cache=True, repetition_penalty=1.0),
        context='pinned_system_birth_plus_one_supplied_prompt', history_present=False,
        parent_present=False, train_ingestion=False, training_updates=0, target_tokens=0,
        automatic_scoring=False, diagnostic_only=True, strict_FD_admission='caller_responsibility',
        started_unix=time.time())
    _write_once(output / 'REQUEST.json', provenance)
    call_files, before_after_verified, outer_rng = {}, False, {}
    try:
        torch = _torch()
        policy.require(not torch.cuda.is_initialized(), 'fresh_process_without_resident_CUDA')
        with _preserve_rng(torch) as outer_rng:
            engine = _load_engine(plan, checkpoint, check)
            before = None
            try:
                before = snapshot(engine)
                _write_once(output / 'BEFORE.json', dict(before, status='PASS', observed_unix=time.time()))
                for position, prompt in enumerate(config['prompts']):
                    for condition in switching.ordered_conditions(position):
                        check('reserve')
                        verify_inputs()
                        expected = messages(plan, prompt)
                        supplied = deepcopy(expected)
                        name = f'CALL_{len(call_files):03d}.json'
                        record = dict(schema=SCHEMA, prompt_id=prompt['id'], position=position,
                            condition=condition, messages=expected, status='RESERVED', started_unix=time.time())
                        _write_once(output / 'reservations' / name, record)
                        call_rng = {}
                        try:
                            with _preserve_rng(torch, cuda=True) as call_rng:
                                with switching.readonly_condition(engine.model, condition):
                                    torch.cuda.synchronize()
                                    started = time.monotonic()
                                    response = engine.generate(supplied, max_new_tokens=MAX_NEW_TOKENS)
                                    record['response'] = deepcopy(response)
                                    torch.cuda.synchronize()
                                    record['generation_wall_seconds'] = time.monotonic() - started
                                    switching.assert_readonly(engine.model)
                                    switching.assert_condition(engine.model, condition)
                                    policy.require(not engine.model.training, 'readout_eval_mode')
                            policy.require(supplied == expected, 'birth_only_messages_mutated')
                            record['mask_receipt'] = _validate_response(response, expected, engine.tokenizer)
                            snapshot(engine)
                            check('generated')
                            record.update(status='COMPLETE', actual_adapter_enabled=condition == 'LORA_ON')
                        except BaseException as error:
                            record.update(status='FAILED', error_type=type(error).__name__, error=str(error))
                            raise
                        finally:
                            record.update(rng=call_rng, finished_unix=time.time())
                            _write_once(output / name, record)
                            call_files[name] = _sha(output / name)
            finally:
                try:
                    after = snapshot(engine)
                    policy.require(before is not None and after == before, 'before_after_identity_changed')
                    before_after_verified = True
                    _write_once(output / 'AFTER.json', dict(after, status='PASS', unchanged=True))
                except BaseException as error:
                    _write_once(output / 'AFTER.json', dict(status='FAILED', unchanged=False,
                        error_type=type(error).__name__, error=str(error)))
                    raise
        check('complete')
        policy.require(len(call_files) == 6, 'all_six_calls_required')
        complete = dict(provenance, status='COMPLETE', calls=6, call_files=call_files,
            before_after_verified=before_after_verified, rng=outer_rng, finished_unix=time.time())
        _write_once(output / 'COMPLETE.json', complete)
        return complete
    except BaseException as error:
        _write_once(output / 'FAILED.json', dict(provenance, status='FAILED', calls=len(call_files),
            call_files=call_files, before_after_verified=before_after_verified, rng=outer_rng,
            error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('plan', 'checkpoint', 'config', 'output'):
        parser.add_argument('--' + option, type=Path, required=True)
    options = parser.parse_args(argv)
    run(options.plan, options.checkpoint, options.config, options.output)


if __name__ == '__main__':
    main()
