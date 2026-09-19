"""Node-local V3 generation; inherited lifetime, budgets and immutable raw."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import orch_rich_hot_node2_continue as base
from organism_v6 import orch_rich_hot_node2_exhaustion_v3 as policy


ROOT = Path('/localhome/local-rohing/orch_rich_hot_node2_exhaustion_v3_20260915_attempt1')
FLOOR = Path('/localhome/local-rohing/orch_rich_hot_node2_floor98_20260915_attempt1')
DERIVED = Path('/localhome/local-rohing/orch_rich_hot_node2_checkpoint99_20260915_attempt1')
OLD_CONTROL = Path('/localhome/local-rohing/orch_rich_hot_node2_checkpoint99_control_20260915_attempt1')


class Engine(base.portable.source.Engine):
    def prompt_tokens(self, messages):
        return self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)

    def generate(self, messages, *, max_new_tokens):
        self.check('generation')
        tokens = self.prompt_tokens(messages)
        base.hot.require(0 < max_new_tokens <= policy.effective_budget(len(tokens)), 'bounded_context_no_crop')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, repetition_penalty=1.0, eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), generation_config=config)
        base.hot.require(generated[0, :len(tokens)].tolist() == tokens, 'generation_prefix_changed')
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        raw = self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail, raw=raw, terminal=terminal,
                    truncated=not terminal and len(tail) == max_new_tokens, max_new_tokens=max_new_tokens, context=policy.CONTEXT)


def validate():
    prepared = base.read(ROOT / 'PREPARE.json')
    base.hot.require(base.sha(ROOT / 'source.tar') == prepared['source_sha256'], 'source_archive_drift')
    base.hot.require(base.verify_archive(ROOT / 'source.tar', ROOT / 'source') == prepared['source_files'], 'source_files_drift')
    base.hot.require(all(base.sha(Path(path)) == digest for path, digest in prepared['files'].items()), 'input_drift')
    return prepared


def counts(root):
    result = [0] * 8
    for path in (root / 'reservations').glob('*.json'):
        result[int(path.name.split('_', 1)[0])] += 1
    return result


def reserve(prepared, shard, task, stage, messages, prompt_tokens):
    budget = policy.effective_budget(prompt_tokens)
    if time.time() >= base.read(ROOT / 'LIFETIME.json')['native_deadline_unix']:
        raise base.BudgetEnd('inherited_deadline')
    with (ROOT / 'CALLS.jsonl').open('a+') as ledger:
        fcntl.flock(ledger, fcntl.LOCK_EX)
        historical = [left + right for left, right in zip(counts(FLOOR), counts(DERIVED))]
        current = counts(ROOT)
        if not policy.remaining_cap(historical, current, shard):
            raise base.BudgetEnd('inherited_aggregate_or_slot_cap')
        identity = prepared['identities'][str(shard)]
        row = dict(index=sum(current), shard=shard, task_id=task['id'], stage=stage, family=task['family'],
            source_task_id=task['source_task_id'], repeated_train_source=task['repeated_train_source'],
            prospective_train_source_reuse=True, condition=policy.CONDITIONS[shard // 2], steering_degree=shard // 2,
            prompt_version=policy.VERSION, messages=messages, prompt_sha256=hashlib.sha256(base.exporter.wire(messages)).hexdigest(),
            prompt_tokens=prompt_tokens, max_new_tokens=budget, target_max_new_tokens=policy.TARGET, context=policy.CONTEXT,
            generator_identity=identity, generator_classification='CHECKPOINT_DERIVED_NOT_IMPROVED' if shard == 0 else 'ORIGINAL37EC_CONTROL',
            source_code_sha256=prepared['source_sha256'], source_checkpoint_commit_sha256=prepared['checkpoint_commit_sha256'] if shard == 0 else None,
            source_checkpoint_update=256 if shard == 0 else None, reserved_unix=time.time(), trainingAllowed=False,
            exhaustion_applicable=not stage.startswith('exposure'), historical_reserved_before=sum(historical))
        base.write(ROOT / 'reservations' / f'{shard}_{task["id"]}_{stage}.json', row)
        ledger.write(json.dumps({key: value for key, value in row.items() if key != 'messages'}) + '\n')
        ledger.flush()
        os.fsync(ledger.fileno())
        return row


def run(shard):
    prepared = validate()
    base.hot.require(os.environ.get('CUDA_VISIBLE_DEVICES') == base.hot.UUIDS[shard], 'exact_uuid')
    output = ROOT / f'shard{shard}'
    (output / 'evidence').mkdir(parents=True, exist_ok=False)
    lifetime, tasks = base.read(ROOT / 'LIFETIME.json'), base.read(ROOT / 'TASKS.json')
    loaded, completed, status = None, 0, 'FAILED'

    def check(label):
        if time.time() >= lifetime['native_deadline_unix']:
            raise base.BudgetEnd('inherited_deadline:' + label)

    try:
        identity = base.bridge.AdapterIdentity.from_document(prepared['identities'][str(shard)])
        binding = base.bridge.StageBinding(ROOT.name + f'_{shard}', base.bridge.ARMS[1], 0, 'sealed_readout',
            identity, False, True, base.sha(ROOT / 'PREPARE.json'))
        loaded = base.native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=base.hot.UUIDS[shard],
            context=base.native.StageContext(), check=check, engine_factory=Engine)
        base.write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
            uuid=base.hot.UUIDS[shard], prompt_version=policy.VERSION, condition=policy.CONDITIONS[shard // 2],
            target_max_new_tokens=policy.TARGET, context=policy.CONTEXT))
        for batch in range(policy.prior.MAX_BATCHES):
            for position in range(shard % 2, policy.prior.TASKS_PER_BATCH, 2):
                check('task_boundary')
                if (ROOT / 'STOP_AFTER_TASK.json').exists() or (ROOT / f'STOP_AFTER_TASK_{shard}.json').exists():
                    raise base.BudgetEnd('safe_task_boundary_stop')
                task, stages = policy.task_at(tasks, batch, position, shard), {}

                def generate(stage, prompts):
                    nonlocal completed
                    number = stages.get(stage, 0)
                    stages[stage] = number + 1
                    stage = f'{stage}_{number}'
                    row = reserve(prepared, shard, task, stage, prompts, len(loaded.engine.prompt_tokens(prompts)))
                    try:
                        response = loaded.engine.generate(prompts, max_new_tokens=row['max_new_tokens'])
                        row.update(response=response, outcome=policy.outcome(task, response))
                        completed += 1
                        return response
                    except BaseException as error:
                        row['error'] = dict(type=type(error).__name__, message=str(error))
                        raise
                    finally:
                        row['finished_unix'] = time.time()
                        base.write(output / f'{task["id"]}_{stage}.json', row)

                try:
                    if task['family'] == 'route':
                        evidence = policy.route_task(task, shard, generate)
                    else:
                        first = generate('draft' if shard >= 4 else 'final', policy.messages(task, shard))
                        if shard >= 4:
                            generate('final', policy.messages(task, shard, first['raw']))
                        evidence = dict(status='TASK_CALLS_COMPLETE')
                    base.write(output / 'evidence' / f'{task["id"]}.json', dict(task=task, evidence=evidence))
                except Exception as error:
                    base.write(output / 'evidence' / f'{task["id"]}.json', dict(task=task, error=dict(type=type(error).__name__, message=str(error))))
                observed = loaded.verify_unchanged()
                base.write(output / 'evidence' / f'{task["id"]}_CHECKPOINT.json', dict(unchanged=True, observed=observed.document()))
        status = 'FINITE_POOL_COMPLETE'
    except base.BudgetEnd as error:
        status = 'BOUNDED_STOP'
        base.write(output / 'BOUND.json', dict(reason=str(error), observed_unix=time.time()))
    except BaseException as error:
        base.write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if loaded is not None:
            observed = loaded.verify_unchanged()
            base.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=base.BUNDLE_SHA)
            base.write(output / 'AFTER.json', dict(observed=observed.document(), unchanged=True))
        base.write(output / 'TERMINAL.json', dict(status=status, completed_calls=completed, finished_unix=time.time(),
            fits=0, parent_calls=0, admitted_rows=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--shard', required=True, type=int, choices=range(8))
    run(parser.parse_args().shard)
