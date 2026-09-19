"""CPU-only verified 37ec DEV actor capsule, not full ancestry or a clean lineage.

Keep the export's manifest SHA separately. read_bundle authenticates the capsule,
not the local base bytes; call verify_base_files explicitly before native use.
The unchanged Engine additionally verifies the loaded base state and runtime.
"""

import argparse
from pathlib import Path
import shutil

from gpu import astra_goal_breadth_collection as collector


source = collector.source
require = collector.require
transfer = collector.memory.transfer
PARENT_STATE = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
SCHEMA = 'DEV_PORTABLE_37EC_ACTOR_V1'
TOKENIZER_FILES = ('tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json',
                   'chat_template.jinja', 'vocab.json', 'merges.txt')


def contract():
    return dict(exporter_sha256=source.file_hash(__file__), helpers=collector.helpers(),
        engine_sha256=source.file_hash(source.__file__), native_sha256=source.file_hash(source.native.__file__),
        state_hasher_sha256=source.file_hash(Path(__file__).resolve().parents[1] / 'organism_v6/pcfl_vertical_train.py'),
        runtime=source.native.NUMERICAL_BINDING['runtime'], engine='gpu.astra_experienced_event_microloop.Engine')


def verify_inventory(directory, files):
    directory = Path(directory)
    require(bool(files) and all(Path(name).name == name and name not in ('.', '..') for name in files),
            'safe_nonempty_inventory_required')
    require({path.name for path in directory.iterdir()} == set(files), 'adapter_inventory_drift')
    require(all(not (directory / name).is_symlink() and (directory / name).is_file() for name in files),
            'regular_adapter_files_required')
    transfer.verify_files(directory, files)


def export_bundle(options):
    output = Path(options.output)
    require(not output.exists() and not output.is_symlink(), 'new_bundle_output_required')
    inputs = collector.load_inputs(options)
    parent, arguments = inputs['parent'], inputs['arguments']
    for location in [value for key, value in vars(options).items() if key != 'output'] + [arguments['model_dir'], parent['trained_adapter_dir']]:
        require(Path(location).resolve() not in output.resolve().parents, 'ancestor_output_overlap_forbidden')
    require(inputs['binding']['state'] == parent['trained_state'] == PARENT_STATE
            and parent['source_commit'] == transfer.SOURCE_COMMIT, 'verified_37ec_source_required')
    require(arguments['expected_base_sha256'] == parent['parent']['expected_base_sha256'], 'base_state_join_required')
    adapter, files = Path(parent['trained_adapter_dir']), parent['trained_adapter_files']
    verify_inventory(adapter, files)
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(files)
            and source.read(adapter / 'adapter_config.json')['r'] == 8, 'rank_eight_adapter_required')
    old_ids = inputs['old_ids']
    require(old_ids == inputs['binding']['old_ids'] == sorted(set(old_ids)) and bool(old_ids), 'old_id_join_required')
    lesson = Path(options.lesson_root)
    locators = {}
    for name, path, digest in (
        ('training', lesson / 'train/RESULT.json', parent['training_result_sha256']),
        ('after', lesson / 'after/RESULT.json', parent['after_result_sha256']),
        ('lessons', lesson / 'collect/RESULT.json', parent['lessons_result_sha256']),
        ('prior_exposure', Path(options.prior_collection_root) / 'expose/RESULT.json',
         inputs['binding']['prior_exposure_result_sha256'])):
        require(source.file_hash(path) == digest, 'receipt_locator_drift:' + name)
        locators[name] = dict(path=str(path.resolve()), sha256=digest)
    source_marker = lesson / 'launch/source_commit.txt'
    require(source_marker.read_text().strip() == transfer.SOURCE_COMMIT, 'source_marker_drift')
    locators['source_commit'] = dict(path=str(source_marker.resolve()), sha256=source.file_hash(source_marker))
    for field, filename in (('lesson_helper_sha256', 'experienced_event_two_hop_lesson.py'),
                            ('actor_helper_sha256', 'experienced_event_two_hop.py')):
        path = lesson / 'source/organism_v6' / filename
        digest = parent['recorded_training_binding'][field]
        require(source.file_hash(path) == digest, 'captured_source_locator_drift')
        locators[field] = dict(path=str(path.resolve()), sha256=digest)
    model = Path(arguments['model_dir'])
    tokenizer_files = {name: source.file_hash(model / name) for name in TOKENIZER_FILES if (model / name).is_file()}
    require({'tokenizer.json', 'tokenizer_config.json'} <= set(tokenizer_files), 'local_tokenizer_files_required')
    manifest = dict(schema=SCHEMA, parent_state=PARENT_STATE, source_commit=transfer.SOURCE_COMMIT,
        expected_base_sha256=arguments['expected_base_sha256'], base_files=parent['base_files'],
        tokenizer_files=tokenizer_files, adapter_files=files, old_ids=old_ids, receipt_locators=locators,
        engine_arguments={key: arguments[key] for key in ('model_dir', 'expected_base_sha256')},
        source_contract=contract(), claim='PORTABLE_DEV_ACTOR_NOT_ENTIRE_ANCESTRY_OR_CLEAN_LINEAGE',
        base_verification='EXPLICIT_LOCAL_FILE_CHECK_AND_NATIVE_ENGINE_STATE_CHECK_REQUIRED')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'adapter').mkdir()
    for name in files:
        shutil.copyfile(adapter / name, output / 'adapter' / name)
    verify_inventory(output / 'adapter', files)
    verify_inventory(adapter, files)
    require(contract() == manifest['source_contract'], 'export_source_drift')
    source.write(output / 'MANIFEST.json', manifest)
    return dict(bundle=str(output.resolve()), manifest_sha256=source.file_hash(output / 'MANIFEST.json'), parent_state=PARENT_STATE)


def read_manifest(bundle, *, expected_manifest_sha256):
    root = Path(bundle)
    require(not root.is_symlink() and {path.name for path in root.iterdir()} == {'MANIFEST.json', 'adapter'}
            and not (root / 'MANIFEST.json').is_symlink() and not (root / 'adapter').is_symlink(), 'bundle_inventory_drift')
    require(source.file_hash(root / 'MANIFEST.json') == expected_manifest_sha256, 'manifest_hash_drift')
    manifest = source.read(root / 'MANIFEST.json')
    require(manifest['schema'] == SCHEMA and manifest['parent_state'] == PARENT_STATE
            and manifest['source_commit'] == transfer.SOURCE_COMMIT, 'verified_37ec_source_required')
    require(manifest['source_contract'] == contract(), 'import_source_contract_drift')
    require(set(manifest['engine_arguments']) == {'model_dir', 'expected_base_sha256'}
            and manifest['engine_arguments']['expected_base_sha256'] == manifest['expected_base_sha256'], 'base_state_join_required')
    verify_inventory(root / 'adapter', manifest['adapter_files'])
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(manifest['adapter_files'])
            and source.read(root / 'adapter/adapter_config.json')['r'] == 8, 'rank_eight_adapter_required')
    return manifest


def read_bundle(bundle, *, expected_manifest_sha256, model_dir, device, gpu_uuid):
    manifest = read_manifest(bundle, expected_manifest_sha256=expected_manifest_sha256)
    require(bool(device) and bool(gpu_uuid) and Path(model_dir).is_dir(), 'explicit_local_runtime_paths_required')
    return argparse.Namespace(model_dir=str(Path(model_dir).resolve()), adapter_dir=str(Path(bundle).resolve() / 'adapter'),
        phase='readout', device=device, gpu_uuid=gpu_uuid, expected_base_sha256=manifest['expected_base_sha256'])


def verify_base_files(bundle, model_dir, *, expected_manifest_sha256):
    manifest = read_manifest(bundle, expected_manifest_sha256=expected_manifest_sha256)
    require(transfer.base_files(model_dir) == manifest['base_files'], 'local_base_file_inventory_drift')
    actual = {name: source.file_hash(Path(model_dir) / name) for name in TOKENIZER_FILES if (Path(model_dir) / name).is_file()}
    require(actual == manifest['tokenizer_files'], 'local_tokenizer_file_inventory_drift')
    return dict(verified=True, model_dir=str(Path(model_dir).resolve()), expected_base_sha256=manifest['expected_base_sha256'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default=collector.memory.TRANSFER_ROOT)
    parser.add_argument('--prior-collection-root', default=collector.PRIOR_COLLECTION_ROOT)
    result = export_bundle(parser.parse_args(argv))
    print(source.json.dumps(result, sort_keys=True))
    return result


if __name__ == '__main__':
    main()
