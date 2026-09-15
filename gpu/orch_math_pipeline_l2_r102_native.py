"""Rohin102 future-only version: two sequential episodes and terminal retention."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu import orch_l2_shared_run as legacy
from gpu.astra_event_two_hop_memory import recall as recall_retention
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, read, sha, write
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_shared as recipe_source
from gpu import orch_math_pipeline_l2_r102_policy as policy
from organism_v6.experienced_event_reader_audit_lesson import collect_cases as collect_retention_audit


def retention_due(cycle):
    assert 1 <= cycle <= 8
    return cycle == 8


def generation_budget(prompt_tokens, requested):
    assert 0 < requested <= policy.GENERATION
    assert 0 < prompt_tokens < policy.CONTEXT, 'full_context_does_not_fit_no_silent_truncation'
    return min(requested, policy.CONTEXT - prompt_tokens)


class Engine(native.source.Engine):
    def generate(self, messages, *, max_new_tokens=policy.GENERATION):
        assert 0 < max_new_tokens <= policy.GENERATION
        self.check('generation')
        self.model.eval()
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        actual_cap = generation_budget(len(tokens), max_new_tokens)
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=actual_cap, repetition_penalty=1.0, eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), generation_config=config)
        assert generated[0, :len(tokens)].tolist() == tokens
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
            raw=self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            terminal=terminal, truncated=not terminal and len(tail) == actual_cap,
            requested_generation_cap=max_new_tokens, effective_generation_cap=actual_cap,
            context_limit=policy.CONTEXT, input_truncated=False)


def encode_row(row, tokenizer):
    target = row['target']
    prefix = tokenizer.apply_chat_template(row['student_prefix'], tokenize=False, add_generation_prompt=True, return_dict=False)
    full = tokenizer.apply_chat_template(row['student_prefix'] + [dict(role='assistant', content=target)],
        tokenize=False, add_generation_prompt=False, return_dict=False)
    assert full == prefix + target + tokenizer.eos_token + '\n'
    prefix_ids = native.source.native._encode(tokenizer, prefix)
    target_ids = native.source.native._encode(tokenizer, target)
    suffix = native.source.native._encode(tokenizer, '\n')
    assert target_ids and not set(tokenizer.all_special_ids).intersection(target_ids)
    sequence = native.source.native._encode(tokenizer, full)
    labels = (-100,) * len(prefix_ids) + target_ids + (tokenizer.eos_token_id,) + (-100,) * len(suffix)
    assert len(sequence) == len(labels) <= policy.CONTEXT, 'complete_source_record_exceeds_context'
    assert sequence == prefix_ids + target_ids + (tokenizer.eos_token_id,) + suffix
    return native.source.native.EncodedRow(sequence, labels, target_ids + (tokenizer.eos_token_id,))


def source_row(root, row):
    relative = Path(row['source_call_path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    path = root / relative
    assert path.resolve() == path and path.is_relative_to(root.resolve()) and sha(path) == row['source_call_sha256']
    call = read(path)
    assert call['response']['raw'] == row['target'] and policy.text_sha(row['target']) == row['target_sha256']
    assert call['task_id'] == row['episode_id'] and row['outcome'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE')
    return row


def parent_request(root, arm, cycle, payload, check):
    policy.validate_parent_payload(payload)
    identifier = f'{arm}_C{cycle}'
    request = dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload))
    directory = root / 'parent_queue'
    directory.mkdir(exist_ok=True)
    path = directory / f'{identifier}.request.json'
    assert not path.exists(), 'parent_call_never_retried'
    write(path, request)
    response = directory / f'{identifier}.response.json'
    until = min(time.time() + 900, read(root.parent / 'LIFETIME.json')['native_deadline_unix'])
    while not response.exists():
        check('parent_wait')
        assert time.time() < until, 'parent_transport_timeout_no_substitution'
        time.sleep(2)
    result = read(response)
    assert result['id'] == identifier and result['request_sha256'] == policy.digest(request)
    assert result['status'] == 'COMPLETE', 'parent_backend_failure_no_substitute'
    return result['plan']


def input_state(root, arm, cycle, phase):
    if phase == 'readout' and cycle > 0:
        receipt = read(root / arm / f'cycle{cycle}' / 'experience' / 'COMPLETE.json')
        return bridge.AdapterIdentity.from_document(receipt['output_adapter']), receipt
    if cycle <= 1:
        initial = read(root / 'INITIAL.json')
        return bridge.AdapterIdentity.from_document(initial['output_adapter']), initial
    receipt = read(root / arm / f'cycle{cycle - 1}' / 'experience' / 'COMPLETE.json')
    return bridge.AdapterIdentity.from_document(receipt['output_adapter']), receipt


def run(root, arm, cycle, phase):
    prepared = read(root.parent / 'PREPARE.json')
    lifetime = read(root.parent / 'LIFETIME.json')
    cohort = read(root / 'COHORT.json')
    assert sha(root.parent / 'source.tar') == prepared['source_sha256']
    from gpu.orch_math_rich_source import verify_archive
    assert verify_archive(root.parent / 'source.tar', root.parent / 'source') == prepared['source_files']
    assert sha(root / 'COHORT.json') == read(root / 'INITIAL.json')['cohort_sha256']
    assert all(sha(root.parent / name) == digest for name, digest in prepared['files'].items())
    uuid = policy.DEVICES[arm][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    output = root / arm / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    identity, predecessor = input_state(root, arm, cycle, phase)
    parented = phase == 'experience' and arm != 'UNPARENTED_SLEEP'
    learning = phase == 'experience' and arm != 'FROZEN'
    binding = bridge.StageBinding(root.name, bridge.ARMS[1] if arm == 'FROZEN' else bridge.ARMS[0] if parented else bridge.ARMS[2], cycle,
        'sealed_readout' if phase == 'readout' else 'training' if learning else 'collection',
        identity, parented, True, sha(root.parent / 'PREPARE.json'))

    def check(label):
        assert time.time() < lifetime['native_deadline_unix'], 'original_lifetime:' + label

    request = dict(arm=arm, cycle=cycle, phase=phase, process=native.process_identity(),
        input_adapter=identity.document(), uuid=uuid, started_unix=time.time())
    write(output / 'REQUEST.json', request)
    planned = cohort['held'][cycle] if phase == 'readout' else cohort['train'][cycle - 1]
    write(output / 'DENOMINATORS.json', dict(planned_tasks=[task['id'] for task in planned],
        task_denominator=len(planned), original_attempts=2 if phase == 'experience' else 0,
        reflections=2 if phase == 'experience' else 0, retention_calls=48 if phase == 'readout' and retention_due(cycle) else 0,
        missing_or_unattempted_remain_in_denominator=True))
    try:
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
        kwargs = dict(model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(private_guidance=('PRIVATE_PARENT_REPLAY',) if parented else ()),
            check=check, engine_factory=Engine, predecessor_processes=(tuple(predecessor['process']),))
        recipe = {key: recipe_source.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
        if learning:
            plan = SimpleNamespace(binding=lambda unused: binding,
                contract=SimpleNamespace(manifest=lambda unused: dict(recipe=recipe)), lineage=SimpleNamespace(arm=binding.arm))
            loaded = native.load_training(plan, **kwargs)
            if cycle > 1:
                previous_optimizer = root / arm / f'cycle{cycle - 1}' / 'experience' / 'optimizer.pt'
                assert sha(previous_optimizer) == predecessor['optimizer_sha256']
                loaded.optimizer.load_state_dict(loaded.engine.torch.load(previous_optimizer, map_location='cpu', weights_only=True))
        else:
            loaded = native.load_stage(binding, **kwargs)
        engine = loaded.engine
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process, uuid=uuid))
        updates = 0

        def generate(messages, task_id, purpose, cap=policy.GENERATION):
            check('call_reservation')
            counter = legacy.spend(root, 'NATIVE_' + arm, policy.MAX_CALLS_PER_ARM,
                dict(cycle=cycle, phase=phase, task_id=task_id, purpose=purpose))
            path = output / f'CALL_{counter:04d}.json'
            call = dict(task_id=task_id, purpose=purpose, messages=messages, started_unix=time.time(),
                relative_path=str(path.relative_to(root)), prior_updates=updates)
            write(path, call)
            try:
                call['response'] = engine.generate(messages, max_new_tokens=cap)
                call['target_sha256'] = policy.text_sha(call['response']['raw'])
            except BaseException as error:
                call['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                call['finished_unix'] = time.time()
                write(path, call)
            return call, sha(path)

        if phase == 'readout':
            rows = []
            for task in cohort['held'][cycle]:
                try:
                    call, digest = generate([dict(role='system', content=policy.WAKE), dict(role='user', content=task['question'])], task['id'], 'held')
                    result = dict(task_id=task['id'], call_sha256=digest, **policy.judge(task, call['response']))
                except Exception as error:
                    result = dict(task_id=task['id'], correct=False, error=str(error))
                rows.append(result)
                write(output / 'HELD.json', dict(rows=rows, denominator=8))
            if retention_due(cycle):
                saved_legacy = read(root.parent / 'LEGACY_READOUT.json')
                events = [dict(event=fact['event'], raw=episode['event']['raw'])
                    for fact, episode in zip(saved_legacy['old_bank'], saved_legacy['old_episodes'])]
                retention = recall_retention(events, lambda messages, **metadata:
                    generate(messages, 'SEALED_RETENTION', 'retention', 160)[0]['response'], output, 'OLD')
                audit = collect_retention_audit(saved_legacy['held'], lambda messages:
                    generate(messages, 'SEALED_RETENTION', 'audit', 160)[0]['response'], coached=False)
                write(output / 'AUDIT.json', audit)
            else:
                retention = dict(status='TERMINAL_ONLY_NOT_RUN_THIS_CYCLE', calls=0)
                audit = dict(summary=dict(status='TERMINAL_ONLY_NOT_RUN_THIS_CYCLE', calls=0))
            loaded.verify_unchanged()
            result = dict(output_adapter=identity.document(), denominator=8, successes=sum(row['correct'] for row in rows),
                retention=retention, audit=audit['summary'], updates=0, parent_present=False)
        else:
            episodes, rows = [], []
            for position, task in enumerate(cohort['train'][cycle - 1]):
                episode = dict(task=task, outcome=dict(status='NO_RESPONSE', correct=False), trace='')
                try:
                    call, digest = generate([dict(role='system', content=policy.WAKE), dict(role='user', content=task['question'])], task['id'], 'experience')
                    episode.update(trace=call['response']['raw'], trace_call=call,
                        trace_call_sha256=digest, outcome=policy.judge(task, call['response']))
                except Exception as error:
                    episode['error'] = dict(type=type(error).__name__, message=str(error))
                episodes.append(episode)
                write(output / f'EPISODE_{position:02d}.json', episode)
            prior_rows = []
            for previous in range(1, cycle):
                prior_rows.extend(read(root / arm / f'cycle{previous}' / 'experience' / 'ROWS.json'))
            previous_reflections = [dict(episode_id=row['episode_id'], target=row['target'], source_call_sha256=row['source_call_sha256'])
                for row in prior_rows if row['kind'] == 'past_reflection'][-2:]
            if parented:
                plan = parent_request(root, arm, cycle, policy.parent_payload(episodes, cycle, previous_reflections), check)
                policy.validate_parent_plan(plan, episodes)
            else:
                plan = dict(order=[episode['task']['id'] for episode in episodes], guidance='', rationale='VERIFIER_ONLY',
                    episode_guidance={episode['task']['id']: '' for episode in episodes})
            write(output / 'PARENT_PLAN.json', plan)
            tokenizer = engine.tokenizer
            legacy_encoded = legacy.legacy_encode(root.parent, tokenizer)
            parameters = {name: parameter for name, parameter in engine.model.named_parameters() if native.is_lora(name)}

            with (output / 'LOSSES.jsonl').open('x') as loss_log:
                def train_encoded(encoded, label):
                    nonlocal updates
                    if not learning:
                        return
                    check('write')
                    engine.model.train()
                    tensors = dict(input_ids=engine.torch.tensor([encoded.input_ids], dtype=engine.torch.long, device=engine.device),
                        labels=engine.torch.tensor([encoded.labels], dtype=engine.torch.long, device=engine.device))
                    tensors['attention_mask'] = engine.torch.ones_like(tensors['input_ids'])
                    loaded.optimizer.zero_grad(set_to_none=True)
                    with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
                        loss = engine.model(**tensors, use_cache=False).loss
                    assert bool(engine.torch.isfinite(loss))
                    loss.backward()
                    assert all(parameter.grad is not None and bool(engine.torch.isfinite(parameter.grad).all()) for parameter in parameters.values())
                    loaded.optimizer.step()
                    updates += 1
                    loss_log.write(json.dumps(dict(update=updates, source=label, loss=loss.item(),
                        supervised_tokens=sum(value != -100 for value in encoded.labels[1:]), matched_learning_rate=recipe['learning_rate'])) + '\n')
                    loss_log.flush()

                for task_id in plan['order']:
                    position, episode = next((index, item) for index, item in enumerate(episodes) if item['task']['id'] == task_id)
                    teacher = '\n'.join(value for value in (plan['guidance'], plan['episode_guidance'][task_id]) if value)
                    actual, public = policy.reflection_messages(episode, teacher)
                    record_tokens = tokenizer.apply_chat_template(policy.historical_prefix(episode, 'past_reflection'),
                        tokenize=True, add_generation_prompt=True, return_dict=False)
                    cap = min(policy.GENERATION, policy.CONTEXT - len(record_tokens) - 2)
                    assert cap > 0, 'full_historical_context_cannot_fit_no_cropping'
                    call, digest = generate(actual, task_id, 'reflection', cap)
                    episode.update(reflection_call=call, reflection_call_sha256=digest, reflection_public_context=public)
                    episode_rows = []
                    if episode['trace']:
                        episode_rows.append(policy.recorded_row(episode, 'past_attempt', episode['trace'],
                            episode['trace_call'], episode['trace_call_sha256']))
                    episode_rows.append(policy.recorded_row(episode, 'past_reflection', call['response']['raw'], call, digest, teacher))
                    encoded_rows = []
                    for row in episode_rows:
                        source_row(root, row)
                        encoded = encode_row(row, tokenizer)
                        write(output / f'MASK_{position:02d}_{row["kind"]}.json', asdict(encoded))
                        encoded_rows.append(encoded)
                    window_end = min(time.time() + policy.WRITE_WINDOW_SECONDS, lifetime['native_deadline_unix'] - 60)
                    presentation = 0
                    while learning and (presentation == 0 or time.time() < window_end):
                        for row, encoded in zip(episode_rows, encoded_rows):
                            train_encoded(encoded, dict(kind=row['kind'], episode_id=task_id, source_call_sha256=row['source_call_sha256'], presentation=presentation))
                        presentation += 1
                    for row in episode_rows:
                        row['actual_presentations'] = presentation
                    rows.extend(episode_rows)
                    write(output / 'ROWS.json', rows)
                    write(output / f'EPISODE_{position:02d}.json', episode)
                for row in prior_rows:
                    source_row(root, row)
                    encoded = encode_row(row, tokenizer)
                    train_encoded(encoded, dict(kind='prior_' + row['kind'], episode_id=row['episode_id'], presentation=0))
                for index, encoded in enumerate(legacy_encoded):
                    train_encoded(encoded, dict(kind='canonical_legacy', row=index))
            coverage = policy.validate_coverage(episodes, rows)
            assert updates > 0 if learning else updates == 0
            if learning:
                engine.verify_base()
                engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
                saved = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
                    tuple((path.name, sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
                assert native.observe_adapter(engine, saved) == saved
                engine.torch.save(loaded.optimizer.state_dict(), output / 'optimizer.pt')
            else:
                loaded.verify_unchanged()
                saved = identity
            result = dict(output_adapter=saved.document(), updates=updates, coverage=coverage,
                cumulative_prior_rows=len(prior_rows), new_rows=len(rows), parent_present=parented,
                source_safe_recording=True, semantic_quality_gate=False)
            result.update(optimizer_sha256=sha(output / 'optimizer.pt') if learning else None,
                optimizer_lifecycle='CONTINUED' if learning and cycle > 1 else 'NEW' if learning else 'NONE')
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
        write(output / 'AFTER.json', dict(output_adapter=result['output_adapter'], process=loaded.process,
            frozen_base_verified=True, actual_mounted_identity_verified=True, finished_unix=time.time()))
        write(output / 'COMPLETE.json', dict(request, status='COMPLETE', finished_unix=time.time(), **result))
    except BaseException as error:
        if 'loaded' in locals():
            try:
                engine.verify_base()
                current = native.state_hash({name: parameter for name, parameter in engine.model.named_parameters() if native.is_lora(name)})
                portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
                write(output / 'FAILED_AFTER.json', dict(frozen_base_verified=True,
                    mounted_adapter_state_sha256=current, process=loaded.process))
            except BaseException as verification_error:
                write(output / 'FAILED_AFTER.json', dict(verified=False, error=str(verification_error)))
        write(output / 'FAILED.json', dict(request, type=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=('GUIDED_SLEEP',), required=True)
    parser.add_argument('--cycle', type=int, required=True)
    parser.add_argument('--phase', choices=('experience', 'readout'), required=True)
    options = parser.parse_args()
    run(options.root, options.arm, options.cycle, options.phase)
