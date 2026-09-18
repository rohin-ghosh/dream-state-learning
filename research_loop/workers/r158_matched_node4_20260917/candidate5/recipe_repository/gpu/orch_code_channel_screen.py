"""Single immutable-lifetime native arm using the original portable actor."""

import argparse
import json
import os
from pathlib import Path
import time

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_freeze import digest, write


def generate(engine, messages, maximum):
    if maximum not in (1536, 512):
        raise ValueError('prospective_source_or_new_ceiling_required')
    engine.check('generation')
    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                  return_dict=False)
    if not 0 < len(tokens) or len(tokens) + maximum > 4096:
        raise ValueError('context_bound_no_truncation')
    inputs = engine.torch.tensor([tokens], dtype=engine.torch.long, device=engine.device)
    config = engine.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
        max_new_tokens=maximum, repetition_penalty=1.0, eos_token_id=engine.tokenizer.eos_token_id,
        pad_token_id=engine.tokenizer.pad_token_id)
    with engine.torch.inference_mode():
        generated = engine.model.generate(input_ids=inputs, attention_mask=engine.torch.ones_like(inputs),
                                           generation_config=config)
    if generated[0, :len(tokens)].tolist() != tokens:
        raise ValueError('generated_prefix_changed')
    tail = generated[0, len(tokens):].tolist()
    terminal = bool(tail) and tail[-1] == engine.tokenizer.eos_token_id
    text = engine.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                                    clean_up_tokenization_spaces=False)
    return dict(messages=messages, prompt_tokens=len(tokens), input_token_ids=tokens, token_ids=tail,
                raw=text, terminal=terminal, truncated=not terminal and len(tail) == maximum,
                generation_ceiling=maximum)


def proof(engine):
    from organism_v6.pcfl_vertical_train import _state_hash

    engine.verify_base()
    if engine.expected_base != policy.BASE or any(parameter.requires_grad for parameter in engine.model.parameters()):
        raise ValueError('frozen_native_base_required')
    parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                  if '.lora_A.' in name or '.lora_B.' in name}
    state = _state_hash(parameters)
    if not parameters or state != policy.MOUNTED:
        raise ValueError('actual_mounted37ec_required')
    layers = [module for module in engine.model.modules() if hasattr(module, 'lora_A')]
    if not layers or any(module.disable_adapters or module.merged_adapters or module.training
                         or module.active_adapters != ['default'] for module in layers):
        raise ValueError('original_enabled_unmerged_adapter_required')
    return dict(actual_native_base_sha256=engine.expected_base, actual_mounted_sha256=state,
                runtime=engine.runtime, adapter_layers=len(layers), frozen=True, fits=0)


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'freeze', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'screen'), required=True)
    parser.add_argument('--arm', choices=policy.ARMS)
    parser.add_argument('--deadline', type=float)
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    freeze = json.loads(Path(options.freeze).read_text())
    tasks = freeze['tasks']
    assert len(tasks) == 64 and len({task['id'] for task in tasks}) == 64
    assert freeze['manifest_sha256'] == policy.MANIFEST
    assert freeze['mounted_sha256'] == policy.MOUNTED and freeze['base_sha256'] == policy.BASE
    assert os.environ['HF_HUB_OFFLINE'] == os.environ['TRANSFORMERS_OFFLINE'] == '1'
    started = time.time()
    binding = dict(arguments=vars(options), started_unix=started, pid=os.getpid(),
                   freeze_sha256=digest(options.freeze), driver_sha256=digest(__file__),
                   policy_sha256=digest(policy.__file__), fits=0)
    write(output / 'START.json', binding)
    rows = []
    engine = None

    def deadline(label):
        if options.phase == 'screen' and time.time() >= options.deadline - 90:
            raise TimeoutError(label)

    try:
        from gpu import astra_portable_actor_bundle as portable

        verification = portable.verify_base_files(options.bundle, options.model_dir,
                                                   expected_manifest_sha256=policy.MANIFEST)
        tokenizer = portable.source.native.load_local_tokenizer(options.model_dir)
        if options.phase == 'prepare':
            counts = []
            for arm in policy.ARMS:
                for position, task in enumerate(tasks):
                    messages, student = policy.prompt(task, arm)
                    assert messages == freeze['initial_templates'][arm][position]
                    assert student == freeze['neutral_prefixes'][position]
                    tokens = tokenizer.apply_chat_template(messages, tokenize=True,
                        add_generation_prompt=True, return_dict=False)
                    assert 0 < len(tokens) and len(tokens) + 1536 <= 4096
                    counts.append(dict(arm=arm, position=position, prompt_tokens=len(tokens)))
            write(output / 'RESULT.json', dict(binding, status='PREPARED_NO_MODEL', model_calls=0,
                base_verification=verification, token_counts=counts,
                tokenizer=dict(eos=tokenizer.eos_token_id, pad=tokenizer.pad_token_id,
                               chat_template_sha256=policy.sha(tokenizer.chat_template))))
            return
        index, uuid = policy.DEVICES[options.arm]
        assert options.deadline and 0 < options.deadline - started <= 5400
        assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
        assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=policy.MANIFEST,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=uuid)
        engine = portable.source.Engine(arguments, tokenizer, check=deadline)
        write(output / 'PRECALL_PROOF.json', dict(binding, **proof(engine), gpu_index=index,
                                                gpu_uuid=uuid, cvd=os.environ['CUDA_VISIBLE_DEVICES']))
        for position, task in enumerate(tasks):
            previous = None
            for kind in ('SOURCE', 'NEW'):
                if kind == 'NEW' and not previous['outcome_pass']:
                    break
                deadline('call')
                if len(rows) >= 128:
                    raise ValueError('arm_call_cap')
                messages, student = policy.prompt(task, options.arm, previous)
                call_start = time.time()
                result = generate(engine, messages, 1536 if kind == 'SOURCE' else 512)
                row = policy.capture(task, options.arm, result, previous)
                assert row['student_prefix'] == student
                row.update(position=position, call_start_unix=call_start, call_end_unix=time.time())
                write(output / f'CALL_{len(rows):03d}.json', row)
                rows.append(row)
                previous = row
            write(output / f'TASK_{position:03d}.json', dict(task_id=task['id'], position=position,
                calls=len(rows), completed_unix=time.time()))
        final = proof(engine)
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', model_calls=len(rows),
            completed_tasks=64, elapsed_seconds=time.time() - started, final_proof=final))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, error_type=type(error).__name__, error=str(error),
                                          preserved_calls=len(rows), elapsed_seconds=time.time() - started))
        raise
    finally:
        if engine is not None:
            engine.hook.remove()
            del engine.model
            engine.torch.cuda.empty_cache()


if __name__ == '__main__':
    main()
