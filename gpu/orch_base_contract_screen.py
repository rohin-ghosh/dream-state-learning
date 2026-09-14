"""Bounded paired same-base/installed-adapter diagnostic using the pinned Engine."""

import argparse
import dataclasses
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import time

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_base_contract as policy


def write(path, document):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mounted(model):
    assert not any(parameter.requires_grad for parameter in model.parameters())
    parameters = {name: parameter for name, parameter in model.named_parameters()
                  if '.lora_A.' in name or '.lora_B.' in name}
    assert parameters
    return parameters


def condition(model, state):
    layers = [module for module in model.modules() if hasattr(module, 'lora_A')]
    disabled = state == 'BASE'
    assert layers and all(module.disable_adapters is disabled for module in layers)
    assert all(not module.merged_adapters for module in layers)
    assert all(module.active_adapters == ['default'] for module in layers)
    assert not model.training and not any(module.training for module in layers)
    status = dataclasses.asdict(model.get_model_status())
    assert status['enabled'] is (not disabled)
    return dict(state=state, disabled_layers=sum(module.disable_adapters for module in layers),
                total_layers=len(layers), model_status=status, unmerged=True)


def serialization(tokenizer, messages):
    tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, return_dict=False)
    assert tokens == tokenizer.encode(text, add_special_tokens=False)
    return dict(messages=messages, serialized_prompt=text, serialized_prompt_sha256=policy.sha(text),
                input_token_ids=tokens, prompt_tokens=len(tokens))


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'freeze', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'screen'), required=True)
    parser.add_argument('--shard', choices=range(4), type=int, default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--resume-from')
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    entries = json.loads(Path(options.freeze).read_text())['entries']
    assert len(entries) == 8
    assert os.environ['HF_HUB_OFFLINE'] == os.environ['TRANSFORMERS_OFFLINE'] == '1'
    binding = dict(arguments=vars(options), started_unix=started, pid=os.getpid(),
                   freeze_sha256=digest(options.freeze), driver_sha256=digest(__file__),
                   policy_sha256=digest(policy.__file__), trainingAllowed=False, fits=0, updates=0)
    write(output / 'REQUEST.json', binding)
    rows = []
    imports = []

    def deadline(label):
        if time.time() >= started + 1500:
            raise TimeoutError(label)

    try:
        binding['base_verification'] = portable.verify_base_files(options.bundle, options.model_dir,
                                                                 expected_manifest_sha256=policy.MANIFEST)
        tokenizer = portable.source.native.load_local_tokenizer(options.model_dir)
        import peft
        api = dict(version=peft.__version__, source=inspect.getsource(peft.PeftModel.disable_adapter),
                   file_sha256=digest(inspect.getfile(peft.PeftModel.disable_adapter)))
        write(output / 'LOCAL_DISABLE_API.json', api)
        template = dict(chat_template=tokenizer.chat_template, eos_token_id=tokenizer.eos_token_id,
                        pad_token_id=tokenizer.pad_token_id,
                        generation=dict(do_sample=False, num_beams=1, max_new_tokens=512,
                                        repetition_penalty=1.0, use_cache=True, min_new_tokens=0),
                        engine_generate_source=inspect.getsource(portable.source.Engine.generate),
                        entries=[dict(task_id=entry['task']['id'], **serialization(tokenizer, entry['initial_messages']))
                                 for entry in entries])
        assert all(item['prompt_tokens'] <= 2048 for item in template['entries'])
        write(output / 'SERIALIZATION_AUDIT.json', template)
        if options.phase == 'prepare':
            write(output / 'RESULT.json', dict(binding, status='PREPARED_NO_MODEL', model_calls=0))
            return
        if options.resume_from:
            previous_root = Path(options.resume_from)
            previous_failure = json.loads((previous_root / 'FAILED.json').read_text())
            assert previous_failure['freeze_sha256'] == binding['freeze_sha256']
            for previous_path in sorted(previous_root.glob('CALL_*.json')):
                previous_row = json.loads(previous_path.read_text())
                assert policy.sha(previous_row['target']) == previous_row['target_sha256']
                rows.append(previous_row)
                shutil.copyfile(previous_path, output / previous_path.name)
                imports.append(dict(path=str(previous_path), sha256=digest(previous_path)))
            assert len(rows) == previous_failure['model_calls']
            write(output / 'RESUME_IMPORTS.json', dict(imports=imports, new_model_calls=0,
                  historical_post_mounted_hash_missing=True))
        completed = policy.completed_states(rows)
        assert os.environ['CUDA_VISIBLE_DEVICES'] == options.gpu_uuid
        assert ('CUDA_VISIBLE_DEVICES=' + options.gpu_uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=policy.MANIFEST,
                                         model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = portable.source.Engine(arguments, tokenizer, check=deadline)
        from organism_v6.pcfl_vertical_train import _state_hash
        assert _state_hash(mounted(engine.model)) == portable.PARENT_STATE
        engine.verify_base()
        write(output / 'ACTOR_READY.json', dict(binding, runtime=engine.runtime,
              adapter_sha256=portable.PARENT_STATE, condition=condition(engine.model, 'ORIGINAL')))

        for position, entry in enumerate(entries):
            if position % 4 != options.shard:
                continue
            order = policy.STATES if position % 2 == 0 else tuple(reversed(policy.STATES))
            for state in order:
                if (position, state) in completed:
                    continue
                previous = None
                with policy.readonly_condition(engine.model, state):
                    active = condition(engine.model, state)
                    for turn in range(2):
                        deadline('call')
                        assert len(rows) < 8
                        messages, student = policy.prompt(entry, previous)
                        if turn == 0:
                            assert messages == entry['initial_messages']
                        serialized = serialization(tokenizer, messages)
                        if serialized['prompt_tokens'] > 2048:
                            write(output / f'CONTEXT_STOP_{position}_{state}_{turn}.json', serialized)
                            break
                        condition(engine.model, state)
                        result = engine.generate(messages, max_new_tokens=512)
                        assert result['prompt_tokens'] == serialized['prompt_tokens']
                        row = policy.capture(entry, result, student, previous)
                        row.update(state=state, position=position, turn=turn, condition=active,
                                   serialization=serialized, rationale_tokens=len(tokenizer.encode(row['rationale'], add_special_tokens=False)))
                        rows.append(row)
                        write(output / f'CALL_{len(rows):03d}.json', row)
                        if not row['outcome_pass'] or turn == 1:
                            break
                        previous = row
                    engine.verify_base()
                    assert _state_hash(mounted(engine.model)) == portable.PARENT_STATE
                    write(output / f'STATE_VERIFIED_{position}_{state}.json', dict(
                          base_sha256=engine.expected_base, adapter_sha256=portable.PARENT_STATE,
                          condition=condition(engine.model, state), finished_unix=time.time()))
                condition(engine.model, 'ORIGINAL')
                assert _state_hash(mounted(engine.model)) == portable.PARENT_STATE
        engine.verify_base()
        assert _state_hash(mounted(engine.model)) == portable.PARENT_STATE
        portable.read_manifest(options.bundle, expected_manifest_sha256=policy.MANIFEST)
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', model_calls=len(rows),
              new_model_calls=len(rows) - len(imports), imported_model_calls=len(imports),
              historical_post_mounted_hash_missing=bool(imports),
              finished_unix=time.time(), adapter_sha256=portable.PARENT_STATE,
              base_sha256=engine.expected_base, base_and_adapter_unchanged=True,
              final_condition=condition(engine.model, 'ORIGINAL')))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, status='FAILED', model_calls=len(rows),
              error=repr(error), finished_unix=time.time()))
        raise


if __name__ == '__main__':
    main()
