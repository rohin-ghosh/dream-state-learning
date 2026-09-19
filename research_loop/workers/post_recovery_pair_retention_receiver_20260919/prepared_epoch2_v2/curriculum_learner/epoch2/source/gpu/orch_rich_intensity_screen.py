"""Finite read-only collection: two GPU shards per frozen condition."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_math_rich_screen import mounted_adapter_parameters, write
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_rich_intensity as policy


class Engine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens):
        if type(max_new_tokens) is not int or max_new_tokens not in (512, 1536):
            raise ValueError('raw85_fixed_generation_caps_required')
        self.check('generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        if not 0 < len(tokens) <= policy.CONTEXT_LIMIT:
            raise ValueError('context_bound_exceeded_no_truncation')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1,
            use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=config)
        assert generated[0, :len(tokens)].tolist() == tokens
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        text = self.tokenizer.decode(tail[:-1] if terminal else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
            raw=text, terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)


def main():
    parser = argparse.ArgumentParser()
    for name in ('bundle', 'model-dir', 'tasks', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'screen'), required=True)
    parser.add_argument('--index', type=int, choices=range(6), default=0)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--deadline', type=float, required=True)
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    condition, shard = policy.allocation(options.index)
    document = json.loads(Path(options.tasks).read_text())
    policy.validate(document)
    assert hashlib.sha256(Path(options.tasks).read_bytes()).hexdigest() == policy.TASKS_SHA
    assert os.environ['HF_HUB_OFFLINE'] == os.environ['TRANSFORMERS_OFFLINE'] == '1'
    binding = dict(arguments=vars(options), started_unix=time.time(), pid=os.getpid(),
        cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'), condition=condition,
        tasks_sha256=policy.TASKS_SHA, driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        policy_sha256=hashlib.sha256(Path(policy.__file__).read_bytes()).hexdigest(),
        trainingAllowed=False, fits=0, updates=0, fit_ready=False)
    write(output / 'REQUEST.json', binding)
    rows = []

    def check(label):
        if time.time() >= options.deadline:
            raise TimeoutError('common_batch_deadline:' + label)

    try:
        check('prepare')
        manifest = portable.read_manifest(options.bundle, expected_manifest_sha256=policy.BUNDLE_SHA)
        assert manifest['parent_state'] == portable.PARENT_STATE
        binding['base_verification'] = portable.verify_base_files(options.bundle, options.model_dir,
            expected_manifest_sha256=policy.BUNDLE_SHA)
        if options.phase == 'prepare':
            write(output / 'RESULT.json', dict(binding, status='PREPARED_NO_MODEL', model_calls=0))
            return
        assert os.environ['CUDA_VISIBLE_DEVICES'] == options.gpu_uuid
        assert ('CUDA_VISIBLE_DEVICES=' + options.gpu_uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=policy.BUNDLE_SHA,
            model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = Engine(arguments, portable.source.native.load_local_tokenizer(options.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_adapter_parameters(engine.model)
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'ACTOR_READY.json', dict(binding, ready_unix=time.time(),
            runtime=engine.runtime, adapter_state=portable.PARENT_STATE))

        def generate(task, kind, previous=None):
            check('call')
            assert len(rows) < 256
            messages, student = policy.prompt(task, condition, kind, previous)
            encoded = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=True, return_dict=False)
            assert len(encoded) <= policy.CONTEXT_LIMIT
            cap = policy.generation_cap(condition, kind)
            write(output / f'INTENT_{len(rows) + 1:04d}.json', dict(task_id=task['id'],
                kind=kind, condition=condition, max_new_tokens=cap, started_unix=time.time()))
            result = engine.generate(messages, max_new_tokens=cap)
            row = policy.capture(task, kind, result, student)
            row.update(condition=condition, physical_index=options.index,
                generation_messages=messages, student_prefix_sha256=original.digest(student),
                max_new_tokens=cap)
            rows.append(row)
            write(output / f'CALL_{len(rows):04d}.json', row)
            return row

        for position, task in enumerate(document['tasks']):
            if position % 2 != shard:
                continue
            rich = generate(task, 'rich')
            if rich['outcome_pass']:
                generate(task, 'new_record', rich['target'])
            else:
                write(output / (task['id'] + '_SKIPPED.json'), dict(task_id=task['id'],
                    reason='initial_failed_exact_oracle', skipped=['new_record'], denominator=256))
        engine.verify_base()
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', model_calls=len(rows),
            finished_unix=time.time(), adapter_state=portable.PARENT_STATE))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, status='FAILED', model_calls=len(rows),
            error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


if __name__ == '__main__':
    main()
