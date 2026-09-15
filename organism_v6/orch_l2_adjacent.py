"""Score-blind checkpoint selection and the unchanged SHORT readout callbacks."""

from copy import deepcopy
import json
import math
from pathlib import Path

from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_l2_shared as shared


require = bridge.require
digest = shared.hop.document_sha256
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
ARCHIVE_SHA = '7ccd3c9aa998b54767a64d52090f9654fee9c24dfd41724459c35924ac1c898d'
MANIFEST_SHA = '99014f4c649a7cb8d8d1fe8f5308688167773bcf53339250672bfa37c716e8a6'
SOURCE_FILE_SHA = '6f5f8811c28bc3ccee94232d628a246f70b604e7ea70be746e3e09536553627d'
SOURCE_SHA = '920deb00f6d0836f2dc9c2d49e22f260dd76e2bc6ee71fd1b077f37f7bbe261f'
COHORT_SHA = 'a1746f1c49339da60e9508d82496a257438614af64657fab261f38283c653844'
CALL_CAP = 512
NATIVE_SECONDS = 3600
SIDES = ('PREVIOUS', 'OUTPUT')
CLAIM = 'REUSED_HELD_ADJACENT_CHECKPOINT_DIAGNOSTIC_NOT_UNTOUCHED_OR_REFLECTION_CAUSAL'


def read(path):
    return json.loads(Path(path).read_text())


def identity_fields(identity):
    require(set(identity) == {'path', 'state_sha256', 'base_sha256', 'files'}, 'exact_identity_fields')
    require(Path(identity['path']).is_absolute(), 'absolute_source_adapter_path')
    require(bridge.valid_hash(identity['state_sha256']) and identity['base_sha256'] == BASE_SHA,
            'source_native_state_and_frozen_base')
    require(bool(identity['files']), 'source_adapter_inventory_required')
    names = []
    for name, file_hash in identity['files']:
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and bridge.valid_hash(file_hash), 'safe_source_adapter_file')
        names.append(name)
    require(len(names) == len(set(names)), 'unique_source_adapter_files')
    return identity


def select_first(shared_root):
    shared_root = Path(shared_root)
    previous = identity_fields(read(shared_root / 'INITIAL.json'))
    require(previous['state_sha256'] == shared.INITIAL_STATE, 'initial_child_changed')
    cohort = read(shared_root / 'COHORT.json')
    checked = []
    for cycle in (1, 2, 3):
        folder = shared_root / 'SHORT' / f'cycle{cycle}' / 'sleep'
        receipt_path = folder / 'COMPLETE.json'
        if not receipt_path.exists():
            return dict(status='WAITING_SHORT_SLEEP', cycle=cycle, checked=checked, native_calls=0)
        receipt = read(receipt_path)
        require(receipt['status'] == 'COMPLETE' and receipt['arm'] == 'SHORT'
                and receipt['cycle'] == cycle and receipt['phase'] == 'sleep', 'completed_SHORT_sleep_required')
        require(receipt['input_adapter'] == previous, 'immediate_previous_child_drift')
        output = identity_fields(receipt['output_adapter'])
        updates = receipt['updates']
        require(type(updates) is int and 0 <= updates <= shared.CAPS['updates_per_sleep'], 'actual_update_count')
        require(type(receipt['unchanged']) is bool
                and receipt['unchanged'] == (output['state_sha256'] == previous['state_sha256']),
                'unchanged_receipt_drift')
        checked.append(dict(cycle=cycle, updates=updates, complete_sha256=bridge.file_sha256(receipt_path)))
        if updates == 0:
            require(output == previous and receipt['fits'] == 0, 'zero_update_must_preserve_child')
            previous = output
            continue
        require(receipt['fits'] == 1, 'actual_fit_required')
        loaded_path, losses_path = folder / 'LOADED.json', folder / 'LOSSES.jsonl'
        loaded = read(loaded_path)
        require(loaded['observed'] == previous and loaded['phase'] == 'sleep'
                and loaded['process'] == receipt['process'], 'actual_mounted_input_drift')
        losses = [json.loads(line) for line in losses_path.read_text().splitlines()]
        require([entry['update'] for entry in losses] == list(range(1, updates + 1))
                and all(math.isfinite(entry['loss']) for entry in losses), 'actual_optimizer_ledger_mismatch')
        worlds = cohort['held'][cycle]
        require(len(worlds) == 8, 'fixed_held_world_denominator')
        return dict(status='SELECTED', policy='FIRST_SHORT_ACTUAL_NONZERO_UPDATE_WITHOUT_HELD_SCORES',
                    cycle=cycle, previous=previous, output=output, actual_updates=updates,
                    cohort_sha256=digest(cohort), held_sha256=digest(worlds), checked=checked,
                    complete_sha256=bridge.file_sha256(receipt_path),
                    loaded_sha256=bridge.file_sha256(loaded_path), losses_sha256=bridge.file_sha256(losses_path),
                    predecessor_process=receipt['process'], claim=CLAIM)
    return dict(status='DEALLOCATED_ALL_THREE_SHORT_SLEEPS_ZERO', checked=checked, native_calls=0)


def budget(cohort, legacy):
    require(len(cohort['held']) == 4 and all(len(worlds) == 8 for worlds in cohort['held']), 'fixed_held_cohorts')
    require(all(len(shared.tasks(world)) == 2 for worlds in cohort['held'] for world in worlds), 'fixed_opposite_goals')
    require(len(legacy['old_bank']) == len(legacy['old_episodes']) == 16, 'fixed_W0_W8_denominators')
    audit_calls = len(legacy['held']['cases'])
    require(audit_calls == legacy['held']['expected_calls'] == 16, 'fixed_audit_denominator')
    per_side = 16 * shared.CAPS['child_turns_per_episode'] + 2 * len(legacy['old_bank']) + audit_calls
    require(2 * per_side <= CALL_CAP, 'exact_evaluator_exceeds_lifetime_cap_before_calls')
    return dict(routing_episodes_per_side=16, routing_worlds_per_side=8, old_W0_per_side=16,
                old_W8_per_side=16, audit_per_side=audit_calls, worst_case_per_side=per_side,
                worst_case_total=2 * per_side, lifetime_cap=CALL_CAP)


def verify_inputs(shared_root, runtime_root):
    from gpu import astra_goal_quality_train as old

    shared_root, runtime_root = Path(shared_root), Path(runtime_root)
    archive_hash = bridge.file_sha256(runtime_root.parent / 'source_runtime_v2.tar')
    require(archive_hash == ARCHIVE_SHA, 'exact_SHORT_V2_archive')
    require(bridge.file_sha256(shared_root / 'PREPARE_RUNTIME_V2.json') == MANIFEST_SHA, 'exact_SHORT_V2_manifest')
    manifest = read(shared_root / 'PREPARE_RUNTIME_V2.json')
    cohort, source = read(shared_root / 'COHORT.json'), read(shared_root / 'SOURCE.json')
    require(digest(cohort) == COHORT_SHA == manifest['cohort_sha256'], 'exact_SHORT_cohort')
    require(bridge.file_sha256(shared_root / 'SOURCE.json') == SOURCE_FILE_SHA
            and digest(source) == SOURCE_SHA, 'exact_stored_SOURCE_bytes')
    shared.verify_source(cohort, source)
    require(bridge.file_sha256(shared_root / 'LEGACY_READOUT.json') == manifest['legacy_files']['LEGACY_READOUT.json'],
            'legacy_file_changed')
    legacy = read(shared_root / 'LEGACY_READOUT.json')
    require(legacy['held'] == old.memory.audit.build_cases(legacy['held']['events'], legacy['held']['split']),
            'existing_audit_case_integrity')
    require(legacy['held']['split'] == old.memory.audit.HELD, 'held_audit_required')
    for relative, expected in manifest['source_files'].items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'safe_runtime_inventory')
        require(bridge.file_sha256(runtime_root / relative) == expected, 'SHORT_V2_runtime_drift:' + relative)
    return dict(cohort_sha256=digest(cohort), source_sha256=digest(source), source_file_sha256=SOURCE_FILE_SHA,
                legacy_file_sha256=bridge.file_sha256(shared_root / 'LEGACY_READOUT.json'),
                runtime_manifest_sha256=bridge.file_sha256(shared_root / 'PREPARE_RUNTIME_V2.json'),
                runtime_archive_sha256=archive_hash,
                budget=budget(cohort, legacy), native_calls=0)


def routing(cohort, source, cycle, generate, emit):
    store = shared.verify_source(cohort, source)
    episodes, worlds = [], []
    for world in cohort['held'][cycle]:
        local_store = {edge['event']: store[edge['event']] for edge in world['edges'] if edge['event'] in store}
        records = []
        for task in shared.tasks(world):
            record = guided.episode(world, task, generate, local_store, parent=None,
                                    telemetry=guided.learner_telemetry(episodes, cycle, 0), rich_contract=False)
            episodes.append(record)
            records.append(record)
            emit(f'EPISODE_{len(episodes):02d}.json', record)
        worlds.append(dict(master=world['master'], successes=sum(record['correct'] for record in records),
                           denominator=2, both_goals_correct=all(record['correct'] for record in records)))
    return dict(episodes=len(episodes), successes=sum(record['correct'] for record in episodes),
                episode_denominator=16, world_denominator=8, worlds=worlds)


def evaluate(cohort, source, legacy, cycle, generate, output, emit):
    from gpu import astra_goal_quality_train as old

    result = routing(cohort, source, cycle, generate, emit)
    events = [dict(event=fact['event'], raw=episode['event']['raw'])
              for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
    result['retention'] = old.memory.recall(events, generate, output, 'OLD')
    audit = old.memory.audit.collect_cases(legacy['held'], generate, coached=False)
    emit('AUDIT.json', audit)
    result['audit'] = audit['summary']
    return result


def original_counts(path, selection):
    require(selection['status'] == 'SELECTED', 'bind_selection_before_original_outcomes')
    original = read(path)
    require(original['status'] == 'COMPLETE' and original['arm'] == 'SHORT'
            and original['phase'] == 'readout' and original['cycle'] == selection['cycle'], 'matching_original_readout')
    require(original['input_adapter'] == selection['output'], 'original_output_child_mismatch')
    return dict(status='AVAILABLE', contextual_only=True, file_sha256=bridge.file_sha256(path),
                counts={key: deepcopy(original[key]) for key in
                        ('episodes', 'successes', 'episode_denominator', 'world_denominator', 'retention', 'audit')})
