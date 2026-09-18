"""Isolated native treatment phases using the existing frozen-base/LoRA seam."""

from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import time
from types import SimpleNamespace

from gpu import orch_math_feedback_uptake as sequence
from gpu import orch_math_feedback_uptake_prepare as preparation
from gpu import orch_math_pipeline_l2_r104_native as seam
from gpu import orch_math_pipeline_l2_run as common
from organism_v6 import orch_math_feedback_uptake as policy


def run(root, cycle, phase):
    prepared = common.validate(root.parent)
    ready = common.read(root / 'READY.json')
    lifetime = common.read(root / 'ACTIVATION.json')
    cohort = common.read(root / 'COHORT.json')
    for name, digest in ready['files'].items():
        policy.require(common.sha(root / name) == digest, 'frozen_sidecar_input')
    for name, digest in ready['source_files'].items():
        policy.require(common.sha(Path(name)) == digest, 'frozen_sidecar_source')
    uuid = ready['device']['uuid']
    policy.require(os.environ['CUDA_VISIBLE_DEVICES'] == uuid, 'uuid_cvd_binding')
    policy.require(('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'native_initial_cvd')
    output = root / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    predecessor_path = root / 'INITIAL.json' if cycle == 1 and phase == 'experience' else root / 'GUIDED_SLEEP' / f'cycle{cycle if phase == "readout" else cycle - 1}' / 'experience' / 'COMPLETE.json'
    predecessor = common.read(predecessor_path)
    identity = seam.bridge.AdapterIdentity.from_document(predecessor['output_adapter'])
    learning = phase == 'experience'
    binding = seam.bridge.StageBinding(root.name, seam.bridge.ARMS[0], cycle,
        'training' if learning else 'sealed_readout', identity, learning, True, common.sha(root / 'READY.json'))
    started = time.time()
    request = dict(cycle=cycle, phase=phase, process=seam.native.process_identity(), started_unix=started,
        input_adapter=identity.document(), predecessor_sha256=common.sha(predecessor_path), uuid=uuid)
    common.write(output / 'REQUEST.json', request)
    common.write(output / 'DENOMINATORS.json', dict(original=2 if learning else 0, checks=2 if learning else 0,
        revisions=2 if learning else 0, parents=2 if learning else 0, held=0 if learning else 8,
        retention=48 if not learning and cycle == policy.CYCLES else 0, missing_and_failed_included=True))
    updates = 0
    loaded = None

    def check(label):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'bounded_lifetime:' + label)

    def interrupted(signum, frame):
        raise TimeoutError('owned_phase_interrupted_checkpoint_if_possible')

    signal.signal(signal.SIGTERM, interrupted)

    def save_state(prefix=''):
        engine.verify_base()
        parameters = {name: parameter for name, parameter in engine.model.named_parameters() if seam.native.is_lora(name)}
        destination = output / (prefix + 'adapter')
        engine.model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
        saved = seam.bridge.AdapterIdentity(str(destination), seam.native.state_hash(parameters), identity.base_sha256,
            tuple((path.name, common.sha(path)) for path in sorted(destination.iterdir()) if path.is_file())).verify()
        policy.require(seam.native.observe_adapter(engine, saved) == saved, 'actual_saved_mounted_join')
        optimizer = output / (prefix + 'optimizer.pt')
        engine.torch.save(loaded.optimizer.state_dict(), optimizer)
        return saved, common.sha(optimizer)

    try:
        seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=seam.BUNDLE_SHA)
        kwargs = dict(model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
            context=seam.native.StageContext(private_guidance=('PRIVATE_PARENT_GUIDANCE',) if learning else ()),
            check=check, engine_factory=seam.Engine, predecessor_processes=(tuple(predecessor['process']),))
        recipe = {key: seam.recipe_source.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
        if learning:
            training = SimpleNamespace(binding=lambda unused: binding,
                contract=SimpleNamespace(manifest=lambda unused: dict(recipe=recipe)), lineage=SimpleNamespace(arm=binding.arm))
            loaded = seam.native.load_training(training, **kwargs)
            seed = common.read(root / 'SEED_PROVENANCE.json')
            optimizer_path = Path(seed['optimizer_path']) if cycle == 1 else predecessor_path.parent / 'optimizer.pt'
            expected_optimizer = seed['optimizer_sha256'] if cycle == 1 else predecessor['optimizer_sha256']
            policy.require(common.sha(optimizer_path) == expected_optimizer, 'optimizer_continuity_hash')
            loaded.optimizer.load_state_dict(loaded.engine.torch.load(optimizer_path, map_location='cpu', weights_only=True))
            common.write(output / 'OPTIMIZER_CONTINUITY.json', dict(source=str(optimizer_path), sha256=expected_optimizer, reset=False))
        else:
            loaded = seam.native.load_stage(binding, **kwargs)
        engine = loaded.engine
        common.write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
            uuid=uuid, actual_mounted_identity_verified=True, loaded_unix=time.time()))

        def generate(messages, task_id, purpose, cap=policy.GENERATION):
            check('native_reserve')
            number = seam.legacy.spend(root, 'NATIVE', policy.NATIVE_CAP, dict(cycle=cycle, phase=phase, purpose=purpose, task_id=task_id))
            path = output / f'CALL_{number:04d}.json'
            call = dict(task_id=task_id, purpose=purpose, messages=messages, relative_path=str(path.relative_to(root)),
                prior_updates=updates, started_unix=time.time(), cap=cap, seed=recipe['seed'])
            common.write(path, call)
            try:
                call['response'] = engine.generate(messages, max_new_tokens=cap)
                call['target_sha256'] = policy.text_sha(call['response']['raw'])
            except BaseException as error:
                call['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                call['finished_unix'] = time.time()
                common.write(path, call)
            return call, common.sha(path)

        if learning:
            prior_rows = common.read(root / 'SEED_ROWS.json')
            for previous_cycle in range(1, cycle):
                prior_rows.extend(common.read(root / 'GUIDED_SLEEP' / f'cycle{previous_cycle}' / 'experience' / 'ROWS.json'))
            previous = [dict(task_id=row['episode_id'], trace=row['target'],
                source_record_sha256=row.get('source_record_sha256', row['source_call_sha256']))
                for row in prior_rows if row['kind'] in ('revision', 'past_reflection')][-2:]
            machine = sequence.Cycle(cohort['train'][cycle - 1], cycle, previous)
            source_calls = {}
            while machine.phase != 'sleep':
                action = machine.reserve()
                common.write(output / 'INTERACTION.json', machine.snapshot())
                if action['kind'] == 'CHILD':
                    messages = action['messages']
                    prompt_tokens = len(engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
                    teacher = messages[0]['content'].partition('PRIVATE PARENT GUIDANCE:\n')[2]
                    teacher_tokens = len(engine.tokenizer.encode(teacher, add_special_tokens=False)) if teacher else 0
                    caps = policy.generation_budget(action['purpose'], prompt_tokens, teacher_tokens)
                    call, digest = generate(messages, action['task_id'], action['purpose'], caps['effective_generation_cap'])
                    record = machine.finish_child(call['response'])
                    source_calls[policy.digest(record)] = dict(path=call['relative_path'], sha256=digest)
                    common.write(output / (action['id'] + '_CAP.json'), caps)
                else:
                    check('parent_reserve')
                    seam.legacy.spend(root, 'PARENT', policy.PARENT_CAP, dict(cycle=cycle, id=action['id']))
                    identifier = 'GUIDED_SLEEP_' + action['id']
                    queue = root / preparation.QUEUE_DIRECTORY
                    request_path = queue / (identifier + '.request.json')
                    policy.require(not request_path.exists(), 'parent_never_retried')
                    common.write(request_path, dict(id=identifier, payload=action['payload'], payload_sha256=policy.digest(action['payload']),
                        action_sha256=policy.digest(action), ready_sha256=common.sha(root / 'READY.json')))
                    response_path = queue / (identifier + '.response.json')
                    until = min(time.time() + 300, lifetime['native_deadline_unix'])
                    while not response_path.exists():
                        check('parent_wait')
                        policy.require(time.time() < until, 'parent_timeout_no_retry')
                        time.sleep(2)
                    result = common.read(response_path)
                    policy.require(result['request_sha256'] == common.sha(request_path) and result['status'] == 'COMPLETE', 'real_bound_parent_response')
                    transcript = result['archive']
                    directory = Path(transcript['remote_root'])
                    policy.require(directory.is_relative_to(root.parent / 'parent_transcripts' / root.name), 'own_parent_transcript_root')
                    for name, digest in transcript['files'].items():
                        policy.require('..' not in Path(name).parts and not Path(name).is_absolute(), 'transcript_relative_path')
                        policy.require(common.sha(directory / name) == digest, 'node_parent_transcript_hash')
                    envelope = common.read(directory / 'RAW_RESPONSE.json')
                    policy.require(envelope['status'] == 'completed' and envelope['usage'], 'actual_provider_completion')
                    machine.finish_parent(result['plan'], envelope['model'], dict(node_only=True, all_verified=True,
                        request_sha256=policy.digest(action), plan_sha256=policy.digest(result['plan']),
                        files=transcript['files'], remote_root=str(directory)))
                    common.write(output / (action['id'] + '_PARENT.json'), result)
                common.write(output / 'INTERACTION.json', machine.snapshot())
            rows = machine.rows()
            for row in rows:
                reference = source_calls[row['source_record_sha256']]
                row.update(source_call_path=reference['path'], source_call_sha256=reference['sha256'])
            common.write(output / 'ROWS.json', rows)
            encoded = []
            for index, row in enumerate(rows):
                seam.source_row(root, row)
                value = seam.encode_row(row, engine.tokenizer)
                encoded.append(value)
                common.write(output / f'MASK_{index:02d}.json', asdict(value))
            parameters = {name: parameter for name, parameter in engine.model.named_parameters() if seam.native.is_lora(name)}
            presentations = {row['source_record_sha256']: 0 for row in rows}
            with (output / 'LOSSES.jsonl').open('x') as log:
                def train(value, label):
                    nonlocal updates
                    check('write')
                    engine.model.train()
                    inputs = engine.torch.tensor([value.input_ids], dtype=engine.torch.long, device=engine.device)
                    labels = engine.torch.tensor([value.labels], dtype=engine.torch.long, device=engine.device)
                    loaded.optimizer.zero_grad(set_to_none=True)
                    with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
                        loss = engine.model(input_ids=inputs, labels=labels, attention_mask=engine.torch.ones_like(inputs), use_cache=False).loss
                    policy.require(bool(engine.torch.isfinite(loss)), 'finite_loss')
                    loss.backward()
                    policy.require(all(parameter.grad is not None and bool(engine.torch.isfinite(parameter.grad).all()) for parameter in parameters.values()), 'finite_lora_gradients')
                    loaded.optimizer.step()
                    updates += 1
                    log.write(json.dumps(dict(update=updates, label=label, loss=loss.item(), finished_unix=time.time())) + '\n')
                    log.flush()
                sleep_start = time.time()
                for task in machine.tasks:
                    selected = [(row, value) for row, value in zip(rows, encoded) if row['episode_id'] == task['id']]
                    until = min(time.time() + 60, lifetime['native_deadline_unix'] - 60)
                    first = True
                    while first or time.time() < until:
                        for row, value in selected:
                            train(value, row['source_record_sha256'])
                            presentations[row['source_record_sha256']] += 1
                        first = False
                for row in prior_rows:
                    seam.source_row(root, row)
                    train(seam.encode_row(row, engine.tokenizer), 'PRIOR:' + row['source_call_sha256'])
                legacy = seam.legacy.legacy_encode(root.parent, engine.tokenizer)
                for index, value in enumerate(legacy):
                    train(value, 'LEGACY:' + str(index))
            machine.sleep_complete(presentations, True, True)
            for row in rows:
                row['actual_presentations'] = presentations[row['source_record_sha256']]
            common.write(output / 'ROWS.json', rows)
            common.write(output / 'INTERACTION.json', machine.snapshot())
            saved, optimizer_sha = save_state()
            result = dict(output_adapter=saved.document(), optimizer_sha256=optimizer_sha, updates=updates,
                sleep_started_unix=sleep_start, sleep_finished_unix=time.time(), old_mix_rows=len(legacy),
                prior_rehearsal_rows=len(prior_rows), rows=len(rows), parent_present=True)
        else:
            results = []
            for task in cohort['held'][cycle - 1]:
                try:
                    call, digest = generate([dict(role='system', content=policy.WAKE), dict(role='user', content=task['question'])], task['id'], 'held')
                    results.append(dict(task_id=task['id'], call_sha256=digest, **policy.source.judge(task, call['response'])))
                except Exception as error:
                    results.append(dict(task_id=task['id'], correct=False, error=str(error)))
                common.write(output / 'HELD.json', dict(rows=results, denominator=8))
            if cycle == policy.CYCLES:
                legacy = common.read(root.parent / 'LEGACY_READOUT.json')
                events = [dict(event=fact['event'], raw=episode['event']['raw']) for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
                seam.recall_retention(events, lambda messages, **metadata: generate(messages, 'SEALED_RETENTION', 'retention', 160)[0]['response'], output, 'OLD')
                audit = seam.collect_retention_audit(legacy['held'], lambda messages: generate(messages, 'SEALED_RETENTION', 'audit', 160)[0]['response'], coached=False)
                common.write(output / 'AUDIT.json', audit)
            loaded.verify_unchanged()
            result = dict(output_adapter=identity.document(), denominator=8, completed_calls=len(results), updates=0, parent_present=False)
        seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=seam.BUNDLE_SHA)
        common.write(output / 'AFTER.json', dict(output_adapter=result['output_adapter'], process=loaded.process,
            frozen_base_verified=True, actual_mounted_identity_verified=True, finished_unix=time.time()))
        common.write(output / 'COMPLETE.json', dict(request, status='COMPLETE', finished_unix=time.time(), **result))
    except BaseException as error:
        partial = None
        if loaded is not None and learning and updates:
            try:
                saved, optimizer_sha = save_state('INTERRUPTED_')
                partial = dict(output_adapter=saved.document(), optimizer_sha256=optimizer_sha, updates=updates)
            except BaseException as saving_error:
                partial = dict(save_error=str(saving_error), updates=updates)
        common.write(output / 'FAILED.json', dict(request, error=str(error), error_type=type(error).__name__,
            partial=partial, finished_unix=time.time(), no_retry=True))
        raise
