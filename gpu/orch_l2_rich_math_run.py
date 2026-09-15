"""Fresh-process experience, sleep and neutral readouts for four pilot lanes."""

import argparse
from dataclasses import asdict
import os
from pathlib import Path
import time
from types import SimpleNamespace
import json

from gpu import orch_guided_native as native
from gpu import astra_goal_quality_train as old
from gpu.orch_l2_rich_math_bootstrap import read, write, sha, legacy_encode
from gpu.orch_l2_shared_run import spend
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_twopass_run import Engine
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_rich_math as policy
from organism_v6 import orch_l2_shared as existing
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


DEVICES = {
    'GUIDED_SLEEP': (4, 'GPU-d304a15c-516a-16a0-a926-a560304077cc'),
    'GUIDED_FROZEN': (5, 'GPU-0cc84073-37a0-4f7a-e555-11671425bd03'),
    'UNPARENTED_SLEEP': (6, 'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf'),
    'BOOTSTRAP_OFF': (7, 'GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed'),
}
COHORT_SHA = '20ec0c83a00c0b8a9649ec1cc6457ddabfd57d3e25c6d9a0481d32bd18bfad89'
ARM_BRIDGE = dict(GUIDED_SLEEP=bridge.ARMS[0], GUIDED_FROZEN=bridge.ARMS[1],
                  UNPARENTED_SLEEP=bridge.ARMS[2], BOOTSTRAP_OFF=bridge.ARMS[2])


def predecessor(root, arm, cycle, phase):
    if arm == 'BOOTSTRAP_OFF':
        path = root / 'OFF/COMPLETE.json'
    elif cycle == 0 or (cycle == 1 and phase == 'experience'):
        path = root / 'FULL/COMPLETE.json'
    elif phase == 'sleep':
        path = root / arm / f'cycle{cycle}' / 'experience/COMPLETE.json'
    else:
        previous = cycle if phase == 'readout' else cycle - 1
        path = root / arm / f'cycle{previous}' / 'sleep/COMPLETE.json'
    receipt = read(path)
    identity = bridge.AdapterIdentity.from_document(receipt.get('output_adapter', receipt.get('input_adapter')))
    return identity, receipt, bridge.ReceiptRef(str(path), sha(path))


def parent_request(root, arm, cycle, payload, check):
    check('parent_request')
    index = spend(root, 'PARENT_REQUESTS', 96, dict(arm=arm, cycle=cycle, kind=payload['kind']))
    identity = f'{arm}_C{cycle}_{index:04d}'
    request = dict(id=identity, payload=payload)
    write(root / 'parent_queue' / (identity + '.request.json'), request)
    path = root / 'parent_queue' / (identity + '.response.json')
    until = min(time.time() + 900, read(root / 'LIFETIME.json')['deadline_unix'])
    while not path.exists() and time.time() < until:
        check('parent_wait')
        time.sleep(2)
    if not path.exists():
        return dict(speak=False, message='', reviews=[], rationale='parent_timeout_no_substitute', error='timeout')
    response = read(path)
    assert response['id'] == identity and response['request_sha256'] == policy.digest(request)
    return response['result']


def prepare(root, model_dir):
    assert sha(root / 'COHORT.json') == COHORT_SHA
    assert read(root / 'COHORT.json') == policy.cohort()
    assert read(root / 'BOOTSTRAP_TERMINAL.json')['a100_device3_released']
    full, off = read(root / 'FULL/COMPLETE.json'), read(root / 'OFF/COMPLETE.json')
    assert full['status'] == off['status'] == 'COMPLETE'
    assert full['input_adapter'] == off['input_adapter'] == read(root / 'INITIAL.json')
    for receipt in (full, off):
        bridge.AdapterIdentity.from_document(receipt['output_adapter'])
        assert receipt['updates'] == 224 and receipt['layout']['new_target_presentations'] == 256
    legacy = read(root / 'LEGACY_READOUT.json')
    assert len(legacy['old_bank']) == len(legacy['old_episodes']) == 16
    assert len(legacy['held']['cases']) == 16
    from gpu import astra_portable_actor_bundle as portable
    verified = portable.verify_base_files('/tmp/astra_portable_37ec_20260914_attempt1', model_dir,
        expected_manifest_sha256='5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469')
    write(root / 'LANE_PREPARE.json', dict(model_dir=str(model_dir), verified_base=verified,
        source_sha256=sha(root / 'source_lanes.tar'),
        files_verified=verify_archive(root / 'source_lanes.tar', root / 'source_lanes'),
        files={name: sha(root / name) for name in ('COHORT.json', 'LIFETIME.json', 'LEGACY_READOUT.json',
            'LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'FULL/COMPLETE.json', 'OFF/COMPLETE.json', 'BOOTSTRAP_TERMINAL.json')},
        learner_call_maximum=1184, provider_envelope_maximum=168, total_caps=dict(learner=1536, parent_provider=192),
        oracle_ceiling_per_stage=8, prepared_unix=time.time()))


def run(root, arm, cycle, phase):
    assert arm in DEVICES and phase in ('experience', 'sleep', 'readout')
    assert phase == 'readout' or (arm != 'BOOTSTRAP_OFF' and cycle in (1, 2, 3))
    assert phase != 'readout' or cycle in (0, 1, 2, 3)
    prepared, lifetime = read(root / 'LANE_PREPARE.json'), read(root / 'LIFETIME.json')
    assert sha(root / 'source_lanes.tar') == prepared['source_sha256']
    assert verify_archive(root / 'source_lanes.tar', root / 'source_lanes') == prepared['files_verified']
    assert all(sha(root / name) == digest for name, digest in prepared['files'].items())
    output = root / arm / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    uuid = DEVICES[arm][1]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    identity, prior, reference = predecessor(root, arm, cycle, phase)
    parent_present = phase == 'experience' and arm.startswith('GUIDED')
    binding = bridge.StageBinding(root.name, ARM_BRIDGE[arm], cycle,
        'sealed_readout' if phase == 'readout' else 'training' if phase == 'sleep' else 'collection',
        identity, parent_present, True, sha(root / 'LANE_PREPARE.json'), (reference,))
    request = dict(arm=arm, cycle=cycle, phase=phase, input_adapter=identity.document(),
                   process=native.process_identity(), uuid=uuid, started_unix=time.time())
    write(output / 'REQUEST.json', request)

    def check(label):
        assert time.time() < lifetime['deadline_unix'], 'global_pilot_deadline:' + label

    try:
        if phase == 'sleep' and (arm == 'GUIDED_FROZEN' or not prior['admitted']):
            write(output / 'COMPLETE.json', dict(request, status='COMPLETE', output_adapter=identity.document(),
                updates=0, fits=0, unchanged=True, reason='FROZEN' if arm == 'GUIDED_FROZEN' else 'ZERO_YIELD', finished_unix=time.time()))
            return
        kwargs = dict(model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
                      context=native.StageContext(private_guidance=(policy.GUIDANCE,) if parent_present else ()),
                      check=check, predecessor_processes=(tuple(prior['process']),), engine_factory=Engine)
        if phase == 'sleep':
            recipe = {key: existing.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
            plan = SimpleNamespace(binding=lambda unused: binding,
                contract=SimpleNamespace(manifest=lambda unused: dict(recipe=recipe)), lineage=SimpleNamespace(arm=ARM_BRIDGE[arm]))
            loaded = native.load_training(plan, **kwargs)
        else:
            loaded = native.load_stage(binding, **kwargs)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process, uuid=uuid))

        def generate(messages, **metadata):
            check('generation')
            index = spend(root, 'LEARNER', policy.LEARNER_CALLS, dict(arm=arm, cycle=cycle, phase=phase, **metadata))
            path = output / f'CALL_{index:04d}.json'
            capture = dict(index=index, metadata=metadata, messages=messages, started_unix=time.time())
            write(path, capture)
            try:
                response = loaded.engine.generate(messages, max_new_tokens=512)
                capture['response'] = response
                return response, index
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                capture['finished_unix'] = time.time()
                write(path, capture)

        if phase == 'readout':
            tasks = read(root / 'COHORT.json')['held'][cycle]
            rows = []
            for task in tasks:
                try:
                    response, index = generate([dict(role='user', content=task['question'])], purpose='held', task_id=task['id'])
                    result = dict(task_id=task['id'], index=index, **policy.judge(task, response['raw']))
                    result['correct'] = result['correct'] and response['terminal'] and not response['truncated']
                except Exception as error:
                    result = dict(task_id=task['id'], correct=False, error=str(error))
                rows.append(result)
                write(output / f'HELD_{len(rows):02d}.json', result)
            legacy = read(root / 'LEGACY_READOUT.json')
            events = [dict(event=fact['event'], raw=episode['event']['raw']) for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
            retention = old.memory.recall(events, lambda messages, **metadata: generate(messages, **metadata)[0], output, 'OLD')
            audit = old.memory.audit.collect_cases(legacy['held'], lambda messages: generate(messages, purpose='audit')[0], coached=False)
            write(output / 'AUDIT.json', audit)
            loaded.verify_unchanged()
            result = dict(successes=sum(row['correct'] for row in rows), denominator=8, oracle_ceiling=8,
                          retention=retention, audit=audit['summary'], updates=0, fits=0)
        elif phase == 'experience':
            tasks = read(root / 'COHORT.json')['train'][cycle - 1]
            episodes, admitted, reviewed = [], [], []
            previous_experience = root / arm / f'cycle{cycle - 1}' / 'experience'
            previous_records = [read(previous_experience / f'EPISODE_{position:02d}.json')
                                for position in (6, 7)] if cycle > 1 else []
            previous_admitted = read(previous_experience / 'COMPLETE.json')['admitted_rows'] if cycle > 1 else 0

            def coach(payload):
                response = parent_request(root, arm, cycle, payload, check)
                if response.get('speak') and len(loaded.engine.tokenizer.encode(response.get('message', ''), add_special_tokens=False)) > 160:
                    return dict(speak=False, message='', rationale='overlength_parent_not_truncated', rejected=response)
                return response

            for position, task in enumerate(tasks):
                telemetry = dict(cycle=cycle, previous_admitted=previous_admitted,
                    recent_actual_records=[episode['captures'][-1]['target'] for episode in episodes[-2:] if episode['captures']],
                    previous_cycle_actual_records=[episode['captures'][-1]['target'] for episode in previous_records if episode['captures']],
                    learning='Only complete successful supported own responses train in LoRA; parent absent at readout.')
                try:
                    episode = policy.experience(task, generate, coach if parent_present else None, telemetry)
                except Exception as error:
                    episode = dict(task_id=task['id'], final_correct=False, captures=[], error=str(error))
                episodes.append(episode)
                write(output / f'EPISODE_{position:02d}.json', episode)
                if position % 2 == 1:
                    rows = [row for episode in episodes[-2:] for row in episode['captures']]
                    payload = policy.review_payload(rows)
                    response = parent_request(root, arm, cycle, payload, check) if payload['candidates'] else dict(reviews=[])
                    write(output / f'REVIEW_{position:02d}.json', response)
                    try:
                        qualified = policy.admit_reviews(rows, response)
                    except Exception as error:
                        write(output / f'REVIEW_{position:02d}_ERROR.json', dict(error=str(error)))
                        qualified = rows
                    reviewed.extend(qualified)
                    for row in qualified:
                        if row.get('admitted'):
                            policy.encode_rows([row], loaded.engine.tokenizer)
                            admitted.append(row)
            loaded.verify_unchanged()
            write(output / 'REVIEWED_ROWS.json', reviewed)
            result = dict(successes=sum(episode['final_correct'] for episode in episodes), denominator=8,
                          admitted=admitted, admitted_rows=len(admitted), updates=0, fits=0)
        else:
            rows = prior['admitted']
            new = policy.encode_rows(rows, loaded.engine.tokenizer)
            legacy = legacy_encode(root, loaded.engine.tokenizer)
            layout = GoalReplayLayout(len(new), 4)
            encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy, eos_token_id=loaded.engine.tokenizer.eos_token_id)
            write(output / 'MASKS.json', [asdict(row) for row in new])
            write(output / 'RECIPE.json', dict(recipe=recipe, layout=layout.manifest('FULL_TARGET')))
            torch = loaded.engine.torch
            parameters = {name: parameter for name, parameter in loaded.engine.model.named_parameters() if native.is_lora(name)}
            with (output / 'LOSSES.jsonl').open('x') as stream:
                for update in range(1, layout.updates + 1):
                    check('sleep')
                    indexes, batch, reference_tokens, active, scale = native.training_batch(encoded, layout, update, pad_id=loaded.engine.tokenizer.pad_token_id)
                    tensors = {name: torch.tensor(value, dtype=torch.long, device=loaded.engine.device) for name, value in batch.items()}
                    loaded.optimizer.zero_grad(set_to_none=True)
                    with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                        loss = loaded.engine.model(**tensors, use_cache=False).loss * scale
                    assert bool(torch.isfinite(loss))
                    loss.backward()
                    assert all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in parameters.values())
                    loaded.optimizer.step()
                    stream.write(json.dumps(dict(update=update, loss=loss.item(), indexes=indexes, reference=reference_tokens, active=active, scale=scale)) + '\n')
                    stream.flush()
            loaded.engine.verify_base()
            loaded.engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
            saved = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
                tuple((path.name, sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
            assert native.observe_adapter(loaded.engine, saved) == saved
            result = dict(output_adapter=saved.document(), updates=layout.updates, fits=1, unchanged=saved.state_sha256 == identity.state_sha256)
        write(output / 'COMPLETE.json', dict(request, status='COMPLETE', finished_unix=time.time(), **result))
    except BaseException as error:
        write(output / 'FAILED.json', dict(request, error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=('prepare', 'experience', 'sleep', 'readout'), required=True)
    parser.add_argument('--arm', choices=policy.ARMS)
    parser.add_argument('--cycle', type=int)
    parser.add_argument('--model-dir', type=Path)
    options = parser.parse_args()
    root = options.root.resolve()
    assert root == Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')
    if options.phase == 'prepare':
        prepare(root, options.model_dir)
    else:
        run(root, options.arm, options.cycle, options.phase)


if __name__ == '__main__':
    main()
