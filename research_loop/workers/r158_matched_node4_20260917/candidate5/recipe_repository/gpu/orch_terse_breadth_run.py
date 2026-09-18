"""Bounded native stages using portable37ec and the existing266 lab primitives."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
import time
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from gpu import orch_terse_breadth_fit as fit
from organism_v6 import orch_terse_breadth as design


original = fit.original
portable = original.collector.portable
source = original.source
require = source.require
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
PROTOCOL = 'research_notes/analysis/orch_terse_breadth_20260914_protocol.md'
ALLOCATION = (
    ('a100', 4, 'GPU-31583768-d90f-520c-51ed-5dac761526d0', 7801, design.ARMS[0], 4),
    ('a100', 5, 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9', 7801, design.ARMS[1], 4),
    ('a100', 6, 'GPU-6de3930d-104a-f969-7d36-009271368dd1', 7802, design.ARMS[0], 4),
    ('a100', 7, 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037', 7802, design.ARMS[1], 4),
    ('node3', 6, 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8', 7801, design.ARMS[0], 16),
    ('node3', 7, 'GPU-319224de-e668-1822-d80b-4b24d15968ae', 7801, design.ARMS[1], 16),
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def helpers():
    return dict(driver=source.file_hash(__file__), fit=source.file_hash(fit.__file__),
                design=source.file_hash(design.__file__), original=original.helpers(),
                layout=source.file_hash(Path(design.__file__).with_name('experienced_event_goal_replay_layout.py')),
                guard=source.file_hash(Path(__file__).with_name('orch_terse_breadth_guard.sh')),
                protocol=source.file_hash(Path(__file__).resolve().parents[1] / PROTOCOL))


def prepare(options, output):
    manifest = portable.read_manifest(BUNDLE, expected_manifest_sha256=BUNDLE_SHA)
    verified = portable.verify_base_files(BUNDLE, options.model_dir, expected_manifest_sha256=BUNDLE_SHA)
    historical = Path(options.legacy_root) / 'prepare/RESULT.json'
    arguments = source.read(historical)['arguments']
    arguments['model_dir'] = options.model_dir
    legacy = original.load_inputs(SimpleNamespace(**arguments))
    old_material = {key: legacy['material'][key] for key in original.GROUPS[:-1]}
    require([len(old_material[key]) for key in original.GROUPS[:-1]] == [128, 20, 62, 12],
            'exact_legacy_material_required')
    require(source.file_hash(options.source_archive) == options.source_sha, 'source_archive_drift')
    worlds = design.registry(manifest['old_ids'])
    frozen = dict(schema='ORCH_TERSE_BREADTH_V1', created_utc=utc(), helpers=helpers(),
        source_sha256=options.source_sha, bundle_sha256=BUNDLE_SHA, initial_state=portable.PARENT_STATE,
        old_ids=manifest['old_ids'], registry=worlds, registry_sha256=design.digest(worlds),
        seeds=list(design.SEEDS), seed_doses=design.SEED_DOSES, allocation=ALLOCATION, train_worlds=128, held_worlds=32,
        source_calls=1280, teaching_calls=3072, readout_calls_per_state=1728,
        max_updates=24672, train_wall_seconds=86400, collection_wall_seconds=7200,
        readout_wall_seconds=7200, allocation_wall_seconds=100800,
        projection='PAIR_QUALITY_NATIVE_TARGET_PARENT_FREE_FULL_REFERENCE',
        protocol_sha256=helpers()['protocol'], legacy_prepare_sha256=source.file_hash(historical),
        legacy_binding=legacy['binding']['legacy'], verified_base=verified)
    source.write(output / 'LEGACY_MATERIAL.json', old_material)
    source.write(output / 'OLD_MASKS.json', legacy['old_masks'])
    source.write(output / 'LEGACY_READOUT.json', legacy['original'])
    frozen['legacy_files'] = {name: source.file_hash(output / name) for name in
                            ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json')}
    source.write(output / 'MANIFEST.json', frozen)
    return dict(status='PREPARED_NO_MODEL', model_calls=0, fits=0, manifest_sha256=source.file_hash(output / 'MANIFEST.json'))


def read_manifest(root):
    manifest = source.read(root / 'prepare/MANIFEST.json')
    original.same(manifest['helpers'], helpers(), 'published_source_protocol_drift')
    require(source.file_hash(root / 'source.tar.gz') == manifest['source_sha256'], 'frozen_archive_drift')
    require(design.digest(manifest['registry']) == manifest['registry_sha256'], 'registry_drift')
    original.same(manifest['registry'], design.registry(manifest['old_ids']), 'generated_registry_drift')
    for name, expected in manifest['legacy_files'].items():
        require(source.file_hash(root / 'prepare' / name) == expected, 'legacy_input_drift:' + name)
    return manifest


def collect(manifest, lane, generate, output):
    documents = []
    for shard in design.SHARDS:
        if shard % 6 != lane:
            continue
        runtime = design.runtime(shard)
        worlds = manifest['registry'][shard]
        shard_output = output / f'shard{shard}'
        shard_output.mkdir()
        collections = []
        for index, world in enumerate(worlds['TRAIN'] + worlds['PROBE']):
            document = runtime.collect_world(world,
                lambda messages: generate(messages, role='exposure', master=world['master']), old_ids=manifest['old_ids'])
            runtime.replay_collection(document, old_ids=manifest['old_ids'])
            source.write(shard_output / f'COLLECTION_{index:02d}.json', document)
            collections.append(document)
        source.write(shard_output / 'EXPOSURE.json', dict(collections=collections))
        teaching = []
        for index, collection in enumerate(collections[:8]):
            if not collection['ready']:
                source.write(shard_output / f'SOURCE_FAILED_{index}.json', collection)
                continue
            document = design.collect_quality(shard, collection,
                lambda messages, metadata: original.quality.hop._invoke(
                    lambda prompt: generate(prompt, role='coached_actor', **metadata), messages))
            design.replay_quality(shard, document)
            source.write(shard_output / f'TEACH_{index:02d}.json', document)
            teaching.append(document)
        documents.append(dict(shard=shard, collection_hashes=[entry['collection_sha256'] for entry in collections],
            qualified_rows=sum(len(entry['quality']['rows']) for entry in teaching),
            missing_sources=[index for index, entry in enumerate(collections[:8]) if not entry['ready']]))
    return dict(status='COMPLETE', shards=documents)


def assemble(root, manifest, output):
    documents, exposures, receipts = [], [], []
    for lane in range(6):
        lane_root = root / f'collection{lane}'
        result = source.read(lane_root / 'RESULT.json')
        require(result['status'] == 'COMPLETE' and not (lane_root / 'FAILED.json').exists(), 'all_six_collection_lanes_required')
        require(result['loaded_adapter_state_sha256'] == result['adapter_state_after'] == portable.PARENT_STATE
                and result['frozen_base_unchanged'] and result['source_sha256'] == manifest['source_sha256'],
                'native_source_state_binding_required')
        native_files = sorted(lane_root.glob('CALL_*.json'))
        require(len(native_files) == result['model_calls'], 'native_capture_count_required')
        captures = iter(source.read(path) for path in native_files)

        def replay(messages, **metadata):
            capture = next(captures, None)
            require(capture is not None and capture['error'] is None, 'native_capture_error_or_missing')
            original.same(capture['messages'], messages, 'actual_native_prompt_drift')
            original.same({key: capture[key] for key in metadata}, metadata, 'actual_native_metadata_drift')
            return deepcopy(capture['response'])

        with TemporaryDirectory() as temporary:
            replay_root = Path(temporary)
            replayed = collect(manifest, lane, replay, replay_root)
            original.same(replayed['shards'], result['shards'], 'actual_native_source_summary_drift')
            for replay_file in replay_root.rglob('*.json'):
                require(source.file_hash(replay_file) == source.file_hash(lane_root / replay_file.relative_to(replay_root)),
                        'actual_native_source_artifact_drift')
        require(next(captures, None) is None, 'extra_native_capture')
        receipts.append(source.file_hash(lane_root / 'RESULT.json'))
    for shard in design.SHARDS:
        directory = root / f'collection{shard % 6}' / f'shard{shard}'
        collections = source.read(directory / 'EXPOSURE.json')['collections']
        require(tuple(entry['master'] for entry in collections) == design.runtime(shard).MASTERS,
                'complete_fixed_world_roster_required')
        for collection in collections:
            design.runtime(shard).replay_collection(collection, old_ids=manifest['old_ids'])
        exposures.append(collections)
        for index, collection in enumerate(collections[:8]):
            if collection['ready']:
                documents.append((shard, source.read(directory / f'TEACH_{index:02d}.json')))
            else:
                original.same(source.read(directory / f'SOURCE_FAILED_{index}.json'), collection, 'missing_source_preservation_required')
    held = [world for shard in manifest['registry'] for world in shard['PROBE']]
    rows = design.qualified_rows(documents, held)
    material = dict(source.read(root / 'prepare/LEGACY_MATERIAL.json'), new_trajectory_rows=rows)
    source.write(output / 'TRAINING_ROWS.json', material)
    source.write(output / 'READOUT_SOURCES.json', exposures)
    recipes = [fit.recipe(len(rows), arm, seed, manifest['protocol_sha256'], presentations)
               for unused_host, unused_index, unused_uuid, seed, arm, presentations in ALLOCATION]
    source.write(output / 'RECIPES.json', recipes)
    batch = dict(status='BATCH_ADMITTED_NO_FIT', model_calls=0, fits=0, created_utc=utc(),
        manifest_sha256=source.file_hash(root / 'prepare/MANIFEST.json'), collection_result_sha256=receipts,
        qualified_targets=len(rows), updates=[recipe['updates'] for recipe in recipes],
        estimated_training_hours_per_fit=[recipe['updates'] * (5600.709 / 2928) / 3600 for recipe in recipes],
        files={name: source.file_hash(output / name) for name in ('TRAINING_ROWS.json', 'READOUT_SOURCES.json', 'RECIPES.json')})
    require(max(batch['estimated_training_hours_per_fit']) < 24, 'training_wall_projection_exceeds_cap')
    source.write(output / 'BATCH.json', batch)
    return batch


def read_batch(root):
    batch = source.read(root / 'assembly/BATCH.json')
    require(batch['status'] == 'BATCH_ADMITTED_NO_FIT'
            and batch['manifest_sha256'] == source.file_hash(root / 'prepare/MANIFEST.json'), 'same_frozen_batch_required')
    for name, expected in batch['files'].items():
        require(source.file_hash(root / 'assembly' / name) == expected, 'batch_file_drift:' + name)
    return batch


def evaluate(root, generate, output):
    exposures = source.read(root / 'assembly/READOUT_SOURCES.json')
    panels, references = [], []
    for shard, collections in enumerate(exposures):
        runtime = design.runtime(shard)
        for index, collection in enumerate(collections):
            if index < 8:
                if (shard, index) in original.TRAIN_SELECTION:
                    panels.append(dict(split='TRAIN', **original.evaluate_goal_world(collection, 'OWN_TEXT', generate,
                        output, 'TRAIN', shard, runtime)))
                continue
            world_index = 2 * shard + index - 8
            for condition in ('OWN_TEXT', 'UNAVAILABLE'):
                panel = original.evaluate_goal_world(collection, condition, generate, output, 'PROBE', world_index, runtime)
                panels.append(dict(split='PROBE', **panel))
            reference = original.first_port_reference(collection, runtime)
            source.write(output / f'PROBE_{world_index}_FIRST_PORT_REFERENCE.json', reference)
            references.append(reference)
    legacy = source.read(root / 'prepare/LEGACY_READOUT.json')
    events = [dict(event=fact['event'], raw=episode['event']['raw'])
              for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
    retention = original.memory.recall(events, generate, output, 'OLD')
    audited = original.memory.audit.collect_cases(legacy['held'],
        lambda messages: generate(messages, role='held_audit', graph='HELD'), coached=False)
    source.write(output / 'HELD_AUDIT.json', audited)
    taught = original.memory.evaluate_graph(legacy['original_collection']['world'], legacy['original_collection'],
        generate, output, ('OWN_TEXT',), 'TAUGHT')
    fresh = original.memory.evaluate_graph(legacy['world'], legacy['collection'], generate, output, ('OWN_TEXT',), 'PREVIOUS_FRESH')
    held_panels = [entry for entry in panels if entry['split'] == 'PROBE' and entry['condition'] == 'OWN_TEXT']
    require(len(held_panels) == 32, 'all_thirty_two_held_worlds_required')
    primary = dict(correct=sum(entry['summary']['paired']['correct'] for entry in held_panels), denominator=64,
        goals=sum(entry['summary']['individual']['correct'] for entry in held_panels), goal_denominator=128)
    checks = dict(old_w0=retention['0']['correct'] >= 15, old_w8=retention['8']['correct'] >= 15,
        audit=audited['summary']['overall']['correct'] >= 15, taught=taught['OWN_TEXT']['correct'] >= 3,
        previous_fresh=fresh['OWN_TEXT']['correct'] >= 3, pairs=primary['correct'] >= 48,
        every_world=all(entry['summary']['paired']['correct'] >= 1 for entry in held_panels))
    summary = dict(primary=primary, checks=checks, engineering_target_met=all(checks.values()),
        panels=panels, deterministic_first_port=references, old_recall=retention, held_audit=audited['summary'],
        taught_graph=taught, previous_fresh_graph=fresh, efficacy='REQUIRES_ALL_MATCHED_COMPARATORS',
        claim='FINITE_TERSE_BREADTH_SEED_REPLICATION_NOT_PROMOTION_OR_LEARNING_LOOP')
    source.write(output / 'SUMMARY.json', summary)
    return dict(status='COMPLETE', summary=summary)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True, choices=('prepare', 'collect', 'assemble', 'baseline', 'train', 'after'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model-dir')
    parser.add_argument('--source-archive')
    parser.add_argument('--source-sha')
    parser.add_argument('--legacy-root', default='/tmp/astra_goal_quality_train_20260914_attempt2')
    parser.add_argument('--lane', type=int, choices=range(6))
    parser.add_argument('--deadline', type=float)
    options = parser.parse_args(argv)
    root, output = Path(options.root), Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(phase=options.phase, started_utc=utc(), pid=os.getpid(), model_calls=0, fits=0, updates=0)
    source.write(output / 'REQUEST.json', dict(result, arguments=vars(options)))
    engine, captures = None, []
    try:
        if options.phase == 'prepare':
            result.update(prepare(options, output))
        else:
            manifest = read_manifest(root)
            result['source_sha256'] = manifest['source_sha256']
            result['manifest_sha256'] = source.file_hash(root / 'prepare/MANIFEST.json')
            if options.phase == 'assemble':
                result.update(assemble(root, manifest, output))
            else:
                require(options.lane is not None and options.deadline is not None, 'bounded_physical_lane_required')
                host, physical, uuid, seed, arm, presentations = ALLOCATION[options.lane]
                require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'exact_uuid_visibility_required')
                require(options.phase != 'baseline' or options.lane == 0, 'one_fixed_baseline_only')
                cap = sum(shard % 6 == options.lane for shard in design.SHARDS) * 272 if options.phase == 'collect' else 1728

                def check(label):
                    require(time.time() < options.deadline, 'native_deadline:' + label)

                check('before_model')
                portable.verify_base_files(BUNDLE, options.model_dir, expected_manifest_sha256=BUNDLE_SHA)
                arguments = portable.read_bundle(BUNDLE, expected_manifest_sha256=BUNDLE_SHA,
                    model_dir=options.model_dir, device='cuda:0', gpu_uuid=uuid)
                state = portable.PARENT_STATE
                if options.phase != 'collect':
                    batch = read_batch(root)
                    result['batch_sha256'] = source.file_hash(root / 'assembly/BATCH.json')
                    result.update(seed=seed, arm=arm, trajectory_presentations=presentations)
                if options.phase == 'after':
                    trained_root = root / f'train{options.lane}'
                    trained = source.read(trained_root / 'RESULT.json')
                    require(trained['status'] == 'COMPLETE' and trained['batch_sha256'] == result['batch_sha256']
                            and trained['seed'] == seed and trained['arm'] == arm and trained['fits'] == 1
                            and trained['updates'] == batch['updates'][options.lane]
                            and trained['trajectory_presentations'] == presentations, 'complete_own_training_required')
                    for name, expected in trained['training_files'].items():
                        require(source.file_hash(trained_root / name) == expected, 'training_evidence_drift')
                    for name, expected in trained['adapter_files'].items():
                        require(source.file_hash(trained_root / 'adapter' / name) == expected, 'trained_adapter_file_drift')
                    arguments.adapter_dir = str(trained_root / 'adapter')
                    state = trained['adapter_state_after']
                    result['training_result_sha256'] = source.file_hash(trained_root / 'RESULT.json')
                engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
                from organism_v6.pcfl_vertical_train import _state_hash

                parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                              if '.lora_A.' in name or '.lora_B.' in name}
                require(parameters and _state_hash(parameters) == state, 'exact_mounted_named_parameter_state_required')
                require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
                        'initial_readonly_actor_required')
                result.update(loaded_adapter_state_sha256=state, runtime=engine.runtime, gpu_uuid=uuid,
                              physical_index=physical, host_alias=host)

                def generate(messages, **metadata):
                    check('call')
                    require(options.phase != 'train' and len(captures) < cap, 'finite_native_call_cap')
                    capture = dict(call_index=len(captures), messages=deepcopy(messages), response=None, error=None, **metadata)
                    captures.append(capture)
                    try:
                        capture['response'] = deepcopy(engine.generate(deepcopy(messages), max_new_tokens=160))
                        return deepcopy(capture['response'])
                    except BaseException as error:
                        capture['error'] = repr(error)
                        raise
                    finally:
                        source.write(output / f"CALL_{capture['call_index']:04d}.json", capture)

                if options.phase == 'collect':
                    result.update(collect(manifest, options.lane, generate, output))
                elif options.phase == 'train':
                    inputs = dict(material=source.read(root / 'assembly/TRAINING_ROWS.json'),
                        old_masks=source.read(root / 'prepare/OLD_MASKS.json'), protocol_sha256=manifest['protocol_sha256'],
                        trajectory_presentations=presentations)
                    result.update(fit.train(engine, inputs, output, arm, seed), status='COMPLETE')
                    state = result['adapter_state_after']
                else:
                    result.update(evaluate(root, generate, output))
                check('complete')
                engine.verify_base()
                require(_state_hash(parameters) == state, 'final_named_parameter_state_drift')
                result.update(adapter_state_after=state, frozen_base_unchanged=True, model_calls=len(captures))
                source.write(output / 'STATES.json', dict(before=result['loaded_adapter_state_sha256'], after=state))
        result.update(finished_utc=utc(), wall_seconds=time.time() - started)
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), finished_utc=utc())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
