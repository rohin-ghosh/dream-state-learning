"""Fresh-process collection, inherited-optimizer sleep, and clean held readouts."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import time

from gpu import orch_guided_native as native
from gpu import orch_math_feedback_uptake_stopped as guarded
from gpu import orch_math_pipeline_l2_r104_native as seam
from gpu import orch_math_pipeline_l2_run as common
from gpu import orch_r107_capability_run as capability_runtime
from gpu import orch_r107_base_anchors_inventory as verified_anchors
from gpu import orch_r110_guided_native as science
from gpu import orch_r108_guided_seed as seed
from organism_v6 import orch_r107_capability as capability
from organism_v6 import orch_r107_parented_replay as replay
from organism_v6 import orch_r110_guided as policy


ROOT = Path('/localhome/local-rohing/orch_r110_guided_20260915_attempt1')
SOURCE_ROOT = Path(__file__).resolve().parents[1]
UUID = 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037'
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
NATIVE_CAP = 5120
PARENT_CAP = 192
read, write, sha = common.read, common.write, common.sha


def validate(root):
    policy.require(root == ROOT and root.resolve() == root and common.host_identity() == HOST_SHA,
        'exact_root_and_hashed_host')
    plan = read(root / 'PLAN.json')
    ready = read(root / 'READY.json')
    policy.require(ready['plan_sha256'] == sha(root / 'PLAN.json')
        and ready['own_cpu_tests_passed'] is True and ready['provenance_passed'] is True,
        'bound_cpu_and_provenance_required')
    policy.require(plan['schema'] == policy.SCHEMA and plan['uuid'] == UUID
        and plan['physical'] == 7 and plan['native_cap'] == NATIVE_CAP
        and plan['parent_cap'] == PARENT_CAP, 'fixed_new_segment_scope')
    policy.require(plan['started_unix'] <= time.time() < plan['native_deadline_unix']
        < plan['hard_deadline_unix'] <= plan['lease_end_unix'] - 21600
        and plan['hard_deadline_unix'] - plan['started_unix'] <= 28800, 'absolute_bounded_lifetime')
    policy.require(plan['sleep_seconds_per_cycle'] == 240 and plan['cycles'] == policy.CYCLES
        and plan['episodes_per_cycle'] == 2 and plan['no_L2_into_original_L1'] is True,
        'declared_schedule_and_lineage')
    source_files = ready['source_files']
    repair_path = SOURCE_ROOT / 'REPAIR.json'
    if repair_path.exists():
        repair = read(repair_path)
        policy.require(repair['schema'] == 'R110_COMPLETION_REPAIR_V2'
            and repair['original_ready_sha256'] == sha(root / 'READY.json'), 'bound_completion_repair')
        for name, expected in source_files.items():
            relative = Path(name)
            policy.require(not relative.is_absolute() and '..' not in relative.parts
                and sha(root / 'source_v1' / relative) == expected, 'original_source_preserved')
        source_files = repair['source_files']
        policy.require(set(ready['source_files']) <= set(source_files)
            and source_files['gpu/orch_r110_guided_run.py'] == sha(Path(__file__)), 'complete_repaired_source')
    for name, expected in source_files.items():
        relative = Path(name)
        policy.require(not relative.is_absolute() and '..' not in relative.parts
            and sha(SOURCE_ROOT / relative) == expected, 'immutable_source_binding')
    for name, expected in ready['input_files'].items():
        relative = Path(name)
        policy.require(not relative.is_absolute() and '..' not in relative.parts
            and sha(root / relative) == expected, 'immutable_input_binding')
    policy.require((root / 'PUBLICATION.json').is_file(), 'published_allocation_required')
    return plan


def spend(root, kind, detail):
    policy.require(kind in ('NATIVE', 'PARENT'), 'known_reservation')
    with (root / 'RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        previous = [json.loads(line) for line in stream if line.strip()]
        count = sum(row['kind'] == kind for row in previous)
        policy.require(count < (NATIVE_CAP if kind == 'NATIVE' else PARENT_CAP), 'lifetime_call_cap')
        number = count + 1
        stream.write(json.dumps(dict(kind=kind, number=number, reserved_unix=time.time(), **detail)) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return number


def input_seed(root, cycle, phase):
    policy.require(cycle in range(1, policy.CYCLES + 1) and phase in ('collection', 'sleep', 'readout'), 'fixed_phase')
    source = root / 'INITIAL.json' if cycle == 1 and phase != 'readout' else (
        root / f'cycle{cycle if phase == "readout" else cycle - 1}' / 'sleep' / 'carry' / 'CARRY.json')
    document = read(source)
    seed.validate(document)
    expected = cycle if phase == 'readout' else cycle - 1
    policy.require(document['generation'] == expected, 'exact_sleep_generation')
    return document


def source_row(root, row):
    relative = Path(row['source_call_path'])
    policy.require(not relative.is_absolute() and '..' not in relative.parts, 'source_call_relative')
    path = root / relative
    policy.require(path.resolve() == path and sha(path) == row['source_call_sha256'], 'source_call_hash')
    call = read(path)
    policy.require(call['task_id'] == row['episode_id'], 'source_task_binding')
    replay.verify_source(row, call)
    return row


def anchor_inventory(root, tokenizer):
    binding = read(root / 'ANCHORS.json')
    path = Path(binding['manifest_path'])
    policy.require(path.is_absolute() and path.resolve() == path and sha(path) == binding['manifest_sha256'],
        'explicit_anchor_manifest')
    inventory = verified_anchors.load_inventory(path.parent, tokenizer, policy.CONTEXT,
        expected_manifest_sha256=binding['manifest_sha256'])
    science.validate_anchor_inventory(inventory)
    return inventory


def parent_call(root, payload, task, check):
    policy.validate_parent_payload(payload)
    identifier = (f"cycle{payload['cycle']}_presleep" if payload['episode'] == 'presleep'
        else f"cycle{payload['cycle']}_episode{payload['episode']}")
    directory = root / 'parent_queue'
    directory.mkdir(exist_ok=True)
    request_path = directory / (identifier + '.request.json')
    policy.require(not request_path.exists(), 'parent_request_never_repeated')
    spend(root, 'PARENT', dict(id=identifier))
    request = dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload), task=payload['task'])
    write(request_path, request)
    response_path = directory / (identifier + '.response.json')
    until = time.time() + 600
    while not response_path.exists():
        check('parent_wait')
        policy.require(time.time() < until, 'bounded_parent_wait')
        time.sleep(1)
    result = read(response_path)
    policy.require(result['status'] == 'COMPLETE' and result['id'] == identifier, 'completed_parent_request')
    policy.validate_plan(result['plan'], [task])
    receipt = result['transcript_receipt']
    archive = Path(receipt['remote_root'])
    policy.require(archive.is_absolute() and archive.resolve() == archive
        and archive.is_relative_to(root / 'parent_transcripts'), 'own_node_only_parent_archive')
    for name, expected in receipt['files'].items():
        relative = Path(name)
        policy.require(not relative.is_absolute() and '..' not in relative.parts
            and sha(archive / relative) == expected, 'actual_parent_archive_hash')
    policy.require({'RAW_RESPONSE.json', 'PLAN.json'} <= set(receipt['files']), 'provider_and_plan_receipts')
    envelope = read(archive / 'RAW_RESPONSE.json')
    policy.require(envelope['status'] == 'completed' and envelope['model'] == policy.STRONG
        and envelope['usage'] and read(archive / 'PLAN.json') == result['plan'], 'actual_strong_parent_response')
    return dict(result, actual_model=envelope['model'])


def capability_capture(task, condition, response, adapter_sha256):
    policy.require(condition in ('LORA_ON', 'LORA_OFF'), 'known_capability_condition')
    policy.require(response['requested_generation_cap'] == response['effective_generation_cap'] == 512,
        'fixed_uncropped_capability_cap')
    normalized = dict(response, max_new_tokens=512, context=response['context_limit'])
    return capability.capture(task, 'ON' if condition == 'LORA_ON' else 'OFF', normalized,
        checkpoint_sha256=adapter_sha256, base_sha256=seed.BASE_SHA,
        lora_enabled=condition == 'LORA_ON')


def completion_record(cycle, phase, process, started, finished, adapter, result):
    details = dict(result)
    for field in ('started_unix', 'finished_unix'):
        if field in details:
            details['training_' + field] = details.pop(field)
    policy.require(not set(details).intersection(('status', 'cycle', 'phase', 'process', 'output_adapter')),
        'completion_metadata_collision')
    return dict(status='COMPLETE', cycle=cycle, phase=phase, process=process,
        started_unix=started, finished_unix=finished, output_adapter=adapter, **details)


def run(root, cycle, phase):
    plan = validate(root)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == UUID
        and ('CUDA_VISIBLE_DEVICES=' + UUID).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'),
        'native_initial_uuid')
    document = input_seed(root, cycle, phase)
    identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
    output = root / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()

    def check(label):
        policy.require(time.time() < plan['native_deadline_unix'], 'native_deadline:' + label)

    def interrupted(signum, frame):
        raise TimeoutError('owned_native_phase_interrupted')

    signal.signal(signal.SIGTERM, interrupted)
    binding_phase = {'collection': 'collection', 'sleep': 'training', 'readout': 'sealed_readout'}[phase]
    parent_present = phase != 'readout'
    binding = native.bridge.StageBinding(root.name, native.bridge.ARMS[0], cycle, binding_phase,
        identity, parent_present, True, sha(root / 'PLAN.json'))
    predecessor_processes = [tuple(document['source_process'])]
    for previous_path in root.glob('cycle*/**/LOADED.json'):
        predecessor_processes.append(tuple(read(previous_path)['process']))
    write(output / 'REQUEST.json', dict(cycle=cycle, phase=phase, started_unix=started,
        process=native.process_identity(), input_adapter=identity.document(),
        seed_binding_sha256=document['binding_sha256'], plan_sha256=sha(root / 'PLAN.json')))
    loaded = None
    try:
        loaded = native.load_stage(binding, model_dir=document['model_dir'], device='cuda:0', gpu_uuid=UUID,
            context=native.StageContext(private_guidance=('R110_PRIVATE_PARENT',) if parent_present else ()),
            check=check, predecessor_processes=tuple(predecessor_processes),
            engine_factory=guarded.engine_class(seam.Engine))
        engine = loaded.engine
        write(output / 'LOADED.json', dict(process=loaded.process, input_adapter=identity.document(),
            parent_present=parent_present, loaded_unix=time.time(), clean_readout=phase == 'readout'))
        cohort = read(root / 'COHORT.json')

        def generate(task, purpose, messages, cap=None, condition='LORA_ON'):
            check('native_reserve')
            cap = (8192 if purpose in ('presleep_initial', 'presleep', 'revision') else 2048) if cap is None else cap
            number = spend(root, 'NATIVE', dict(cycle=cycle, phase=phase, task_id=task['id'], purpose=purpose,
                condition=condition))
            path = output / f'CALL_{number:03d}.json'
            call = dict(task_id=task['id'], purpose=purpose, condition=condition, started_unix=time.time(),
                process=loaded.process, input_adapter=identity.document())
            write(path, call)
            try:
                tagged_purpose = 'revision' if purpose in ('presleep_initial', 'presleep') else purpose
                call['response'] = engine.generate(guarded.TaggedMessages(messages, tagged_purpose), max_new_tokens=cap)
                if purpose == 'revision' and 'reflection_guard' in call['response']:
                    call['response']['reflection_guard']['fit_eligibility'] = 'R110_RAW_CHILD_TOKENS_UNCHANGED'
            except BaseException as error:
                call['error_type'] = type(error).__name__
                raise
            finally:
                call['finished_unix'] = time.time()
                write(path, call)
            return dict(call, path=str(path.relative_to(root)), sha256=sha(path))

        result = dict(optimizer_updates=0)
        if phase == 'collection':
            previous = [] if cycle == 1 else read(root / f'cycle{cycle - 1}' / 'collection' / 'CARRY.json')
            collected = science.collect_cycle(cohort['train'][cycle - 1], cycle, identity.state_sha256,
                previous, generate, lambda payload, task: parent_call(root, payload, task, check),
                lambda name, value: write(output / name, value))
            loaded.verify_unchanged()
            result.update(native_calls=collected['native_experience_calls'], parent_calls=collected['parent_calls'],
                rows_sha256=sha(output / 'ROWS.json'), carry_sha256=sha(output / 'CARRY.json'))
        elif phase == 'sleep':
            collection = root / f'cycle{cycle}' / 'collection'
            complete = read(collection / 'COMPLETE.json')
            policy.require(complete['status'] == 'COMPLETE'
                and complete['rows_sha256'] == sha(collection / 'ROWS.json'), 'complete_two_episodes_before_sleep')
            rows = [source_row(root, row) for row in read(collection / 'ROWS.json')]
            anchors = anchor_inventory(root, engine.tokenizer)
            old_l1 = [seed.encoded(row, engine.tokenizer) for row in seed.rehearsal_rows(document)]
            old_l2 = []
            for previous_cycle in range(1, cycle):
                old_l2.extend(replay.encode_row(source_row(root, row), engine.tokenizer, policy.CONTEXT)
                    for row in read(root / f'cycle{previous_cycle}' / 'collection' / 'ROWS.json'))
            write(output / 'OPTIMIZER_CONTINUITY.json', seed.restore(loaded, document))
            result.update(science.sleep_cycle(engine, loaded.optimizer, rows, old_l1, old_l2, anchors,
                min(time.time() + plan['sleep_seconds_per_cycle'], plan['native_deadline_unix'] - 60), check,
                lambda name, value: write(output / name, value)))
            engine.verify_base()
            destination = output / 'adapter'
            engine.model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
            parameters = {name: parameter for name, parameter in engine.model.named_parameters() if native.is_lora(name)}
            identity = native.bridge.AdapterIdentity(str(destination), native.state_hash(parameters), seed.BASE_SHA,
                tuple((path.name, sha(path)) for path in sorted(destination.iterdir()) if path.is_file())).verify()
            seed.save_carry(loaded, document, identity, output / 'carry')
            result.update(carry_sha256=sha(output / 'carry' / 'CARRY.json'))
        else:
            held = []
            for task in cohort['held'][cycle - 1]:
                call = generate(task, 'held', [dict(role='system', content='Solve the problem. Finish with FINAL: numeric answer.'),
                    dict(role='user', content=task['question'])], cap=8192)
                held.append(dict(task_id=task['id'], call_sha256=call['sha256'],
                    generated_tokens=len(call['response']['token_ids']), semantic_behavior='UNASSESSED',
                    accuracy_secondary=history_judge(task, call['response'])))
                write(output / 'HELD.json', held)
            panel = []
            for position, task in enumerate(capability.tasks()):
                for condition in capability_runtime.ordered_conditions(position):
                    with capability_runtime.readonly_condition(engine.model, condition):
                        call = generate(task, 'held', capability.messages(task), cap=512, condition=condition)
                    panel.append(capability_capture(task, condition, call['response'], identity.state_sha256))
                    write(output / 'CAPABILITY_CELLS.json', panel)
            loaded.verify_unchanged()
            result.update(held_calls=len(held), capability_calls=len(panel), parent_calls=0,
                fresh_process=True, own_context_carry=False, semantic_success_not_inferred=True)
        engine.verify_base()
        write(output / 'COMPLETE.json', completion_record(cycle, phase, loaded.process,
            started, time.time(), identity.document(), result))
    except BaseException as error:
        partial = None
        if loaded is not None and phase == 'sleep' and loaded.optimizer is not None:
            try:
                loaded.engine.verify_base()
                destination = output / 'INTERRUPTED_adapter'
                loaded.engine.model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
                parameters = {name: parameter for name, parameter in loaded.engine.model.named_parameters()
                    if native.is_lora(name)}
                partial_identity = native.bridge.AdapterIdentity(str(destination), native.state_hash(parameters),
                    seed.BASE_SHA, tuple((path.name, sha(path)) for path in sorted(destination.iterdir())
                        if path.is_file())).verify()
                partial = seed.save_carry(loaded, document, partial_identity, output / 'INTERRUPTED_carry')
            except BaseException as preservation_error:
                partial = dict(preservation_error_type=type(preservation_error).__name__)
        write(output / 'FAILED.json', dict(status='FAILED', cycle=cycle, phase=phase,
            error_type=type(error).__name__, error=str(error), started_unix=started,
            finished_unix=time.time(), partial_state=partial, partial_evidence_preserved=True, retry_allowed=False))
        raise


def history_judge(task, response):
    return policy.history.source.judge(task, response)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--cycle', type=int, choices=range(1, policy.CYCLES + 1), required=True)
    parser.add_argument('--phase', choices=('collection', 'sleep', 'readout'), required=True)
    options = parser.parse_args()
    run(options.root, options.cycle, options.phase)
