"""CPU handoff to a future separately allocated pair, never a launcher."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import os
from pathlib import Path

from gpu import orch_guided_native as native
from gpu.orch_teacher_branching_pilot_compile import MATH, ROUTE, read, sha, write_once
from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_replication as route_readout
from organism_v6 import orch_teacher_branching_pilot as pilot
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


def paired_batches(encoded, pad_id):
    layout = GoalReplayLayout(16, 4)
    totals = dict(full_reference=0, full_active=0, masked_reference=0, masked_active=0)
    for update in range(1, layout.updates + 1):
        indexes, full, reference, active, scale = native.training_batch(
            encoded, layout, update, pad_id=pad_id, replay_arm=pilot.ARMS[0])
        masked_indexes, masked, masked_reference, masked_active, masked_scale = native.training_batch(
            encoded, layout, update, pad_id=pad_id, replay_arm=pilot.ARMS[1])
        pilot.require(indexes == masked_indexes and full['input_ids'] == masked['input_ids']
            and full['attention_mask'] == masked['attention_mask'], 'identical_pair_inputs_and_padding')
        pilot.require(reference == active == masked_reference and scale == 1
                      and masked_scale == masked_active / reference, 'unchanged_reference_normalization')
        for position, index in enumerate(indexes):
            pilot.require(masked['labels'][position] == full['labels'][position] if index < 222
                          else all(label == -100 for label in masked['labels'][position]), 'only_new_labels_masked')
        totals['full_reference'] += reference
        totals['full_active'] += active
        totals['masked_reference'] += masked_reference
        totals['masked_active'] += masked_active
    return totals


def evaluate_routes(collections, generate, emit):
    pilot.require(len(collections) == 2, 'exact_two_held_route_worlds')
    panels = []
    calls = 0

    def bounded(messages):
        nonlocal calls
        pilot.require(calls < 48, 'paired_arm_route_call_cap')
        calls += 1
        return generate(messages)

    for ordinal, collection in enumerate(collections):
        world = collection['world']
        pilot.require('HELD' in world['master'], 'held_route_readout_only')
        pilot.teacher.route.runtime(world['master'])['replay_collection'](collection)
        store = {record['edge']['event']: record['event']['raw'] for record in collection['records']
                 if record['accepted']}
        records = []
        for task_index, task in enumerate(route_readout.tasks(world)):
            episode = route_readout.episode(world, task, bounded, store)
            emit(f'WORLD_{ordinal:02d}_GOAL_{task_index}.json', episode)
            records.append(episode)
        panels.append(route_readout.summarize(world, records))
    return dict(worlds=panels, actor_calls=calls, goal_denominator=8, pair_denominator=4,
                goals=sum(panel['goals'] for panel in panels), pairs=sum(panel['pairs'] for panel in panels),
                condition='FIXED_PREEXISTING_SOURCE_EVENT_TEXT_NOT_NEW_CHILD_OWN_TEXT')


def prepare_interface(manifest_path, expected_sha256, inputs, output):
    from transformers import AutoTokenizer
    from gpu.orch_l2_shared_run import legacy_encode

    pilot.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_visible_devices_empty')
    pilot.require(str(output.resolve()).startswith('/localhome/local-rohing/orch_teacher_branching_pilot_'),
                  'native_only_interface')
    pilot.require(sha(manifest_path) == expected_sha256, 'compiled_manifest_pin')
    manifest = read(manifest_path)
    pilot.require(manifest['source_label'] == pilot.LABEL and manifest['rows'] == 16
                  and not manifest['training_application_allowed'], 'compiled_teacher_pending_only')
    source_root = Path(manifest['source_root'])
    pilot.require(all(sha(source_root / name) == digest for name, digest in manifest['runtime_source_files'].items()),
                  'immutable_compiler_runtime_files')
    for entry in list(manifest['files'].values()) + list(manifest['legacy_refs'].values()):
        pilot.require(sha(entry['path']) == entry['sha256'], 'native_compile_input_hash')
    output.mkdir(exist_ok=False)
    tokenizer = AutoTokenizer.from_pretrained(manifest['base_verified']['model_dir'], local_files_only=True)
    legacy_root = Path(manifest['legacy_refs']['LEGACY_MATERIAL.json']['path']).parent
    legacy = legacy_encode(legacy_root, tokenizer)
    new = pilot.encode_rows(read(manifest['files']['ROWS.json']['path']), tokenizer)
    pilot.require([asdict(row) for row in new] == [dict((key, tuple(value)) for key, value in row.items())
        for row in read(manifest['files']['ENCODED_TEACHER.json']['path'])], 'exact_saved_teacher_encoding')
    encoded = native.assemble_replay(legacy, new, GoalReplayLayout(16, 4), legacy_reference=legacy,
                                     eos_token_id=tokenizer.eos_token_id)
    totals = paired_batches(encoded, tokenizer.pad_token_id)
    cohort = read(manifest['files']['READOUT_COHORT.json']['path'])
    math_cohort, route_cohort, source = read(inputs / MATH), read(inputs / ROUTE / 'COHORT.json'), read(inputs / ROUTE / 'SOURCE.json')
    pilot.require(pilot.readout_cohort(math_cohort, route_cohort) == cohort, 'fixed_held_readout_cohort')
    roster = read('/localhome/local-rohing/orch_route_parent_campaign_20260915_raw_mirror/teacher_exemplar/ROSTER.json')
    for relative in (MATH, ROUTE + 'COHORT.json', ROUTE + 'SOURCE.json'):
        pilot.require(sha(inputs / relative) == roster['source_files'][relative], 'readout_source_hash')
    collections = {item['master']: item for item in source['collections']}
    selected = [collections[master] for master in cohort['route_world_masters']]
    for collection, expected in zip(selected, cohort['route_world_sha256']):
        pilot.require(pilot.digest(collection['world']) == expected, 'held_world_source_join')
    mock_episodes = []
    mock = evaluate_routes(selected, route_readout.first_port, lambda name, value: mock_episodes.append(value))
    pilot.require(len(mock_episodes) == 8 and mock['actor_calls'] <= 48, 'cpu_route_shape_rehearsal')
    teacher_text = read(manifest['files']['ROWS.json']['path'])
    held_ids = {task['id'] for group in math_cohort['held'] for task in group}
    pilot.require(not {row['task_id'] for row in teacher_text} & held_ids, 'held_tasks_never_teacher_train')
    readout = dict(schema='TEACHER_PAIR_SEALED_READOUT_INPUTS_V1', teacher_or_parent_access=False,
                   training_allowed=False, math_tasks=[task for group in math_cohort['held'][:2] for task in group],
                   route_collections=selected, native_source_sha256=sha(inputs / ROUTE / 'SOURCE.json'),
                   route_condition=mock['condition'], new_source_generation_calls=0)
    write_once(output / 'SEALED_READOUT_INPUTS.json', readout)
    recipe = {key: shared.RECIPE[key] for key in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
    protocol = dict(pilot.protocol(), fits_planned=2, optimizer=recipe,
        route_condition=mock['condition'], route_driver='orch_replication.episode+summarize',
        route_source_caveat='EXISTING_OBSERVED_SOURCE_EVENTS_IDENTICAL_BOTH_ARMS_NOT_CHILD_AUTOBIOGRAPHY',
        route_richness_caveat='STRICT_ACTION_PROTOCOL_MEASURES_ROUTING_TRANSFER_NOT_FREEFORM_METHOD_RICHNESS',
        primary_richness_readout='16_MATH_FULL_OUTPUTS_PER_ARM_DEFAULT_NEUTRAL_PROMPT',
        pair_seed=8203, fresh_optimizer_per_arm=True, all_lora_only=True,
        masks='NEW_ROWS222_TO237_TARGET_AND_EOS_ONLY',
        lifetime='ONE_SHARED_START_NO_RESET_7200S_LEASE_END_MINUS6H_WHICHEVER_EARLIER',
        model_generation_kwargs='DO_SAMPLE_FALSE_NO_MINIMUM_OR_PADDING_KEEP_RAW_TRUNCATION_AND_FAILURES',
        parent_or_teacher_at_readout=False, comparisons='ONE_SEED_FIXED_DEV_PAIRED_FULL_MINUS_MASKED_ONLY')
    write_once(output / 'PAIRED_PROTOCOL.json', protocol)
    ready = dict(schema='ORCH_TEACHER_DOSE4_CPU_INTERFACE_READY_V1',
        utc=datetime.now(timezone.utc).isoformat(), status='CPU_READY_NO_GPU_ALLOCATION_OR_LAUNCH',
        compiled_manifest=dict(path=str(manifest_path), sha256=expected_sha256),
        interface_source=dict(path=str(Path(__file__).resolve()), sha256=sha(__file__)),
        totals=totals, route_cpu_mock=dict(actor_calls=mock['actor_calls'], episodes=len(mock_episodes),
        actual_model_calls=0, not_a_learner_result=True), protocol=protocol,
        files={path.name: dict(path=str(path), sha256=sha(path)) for path in sorted(output.iterdir())})
    write_once(output / 'READY.json', ready)
    return ready


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'inputs', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_interface(args.manifest, args.expected_sha256, args.inputs, args.output), sort_keys=True))
