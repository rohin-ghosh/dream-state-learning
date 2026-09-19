"""Validate the single, exact C2 epoch2-to-epoch3 performance delta."""

import hashlib
from pathlib import Path, PurePosixPath


HISTORY = 'organism_v6/orch_r124_train_history.py'
BEFORE = 'ec7ecd7ebf395885606e7b500a47baedd11172a4c46e23b8d05d569dc8fac1d3'
AFTER = '8d44b45941228b229340a1546d3bf984965b0f9d2acfab12967c829d48f16315'
PORT = '551aaf3eabcc1aef13c44830d3790b63a1ad0ce043c7b39b41e051b6d21cea79'
EPOCH2 = '399e47a4be85b62b7b1410a077ec45a80cb27f0425eb85f9f0ad25b7a46b2d7c'
ADOPTION = {'gpu/orch_r125_continual_native.py', 'gpu/c2_retention_runtime.py'}
RETENTION = {HISTORY, 'organism_v6/orch_r125_continual_stream.py', 'gpu/orch_r184_think_act_learn.py'}
UNCHANGED = ('gpu/r188_node5_confinement.py', 'gpu/orch_r125_continual_guard.py',
    'gpu/orch_r125_stream_journal.py', 'gpu/checkpoint_tail_runtime.py', 'gpu/r184_cpu_bridge.py')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def delta(before, after):
    return {name: dict(before=before.get(name), after=after.get(name))
        for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)}


def validate(manifest):
    require(manifest['schema'] == 'C2_EPOCH3_EXACT_LOCAL_SOURCE_V1' and manifest['life'] == 'C2',
        'exact_C2_epoch3_schema')
    require(manifest['epoch2_manifest_sha256'] == EPOCH2 and manifest['frontier_port_sha256'] == PORT,
        'exact_immutable_epoch2_and_Main_port')
    previous, current = manifest['epoch2_source_pins'], manifest['new_source_pins']
    expected = {HISTORY: dict(before=BEFORE, after=AFTER)}
    require(delta(previous, current) == manifest['epoch2_to_epoch3_delta'] == expected,
        'one_exact_history_delta_only')
    require(delta(manifest['old_source_pins'], current) == manifest['changed']
        and set(manifest['changed']) == ADOPTION | RETENTION, 'five_exact_old_live_changed_filenames')
    require(delta(manifest['epoch1_source_pins'], previous) == manifest['epoch1_to_epoch2_delta']
        and set(manifest['epoch1_to_epoch2_delta']) == ADOPTION, 'preserve_historical_epoch1_epoch2_map')
    require(delta(manifest['epoch1_source_pins'], current) == manifest['epoch1_to_epoch3_delta']
        and set(manifest['epoch1_to_epoch3_delta']) == ADOPTION | {HISTORY}, 'three_epoch1_epoch3_deltas')
    require(len(current) == manifest['source_file_count'] == 184, 'same_184_python_file_closure')
    require(all(current[name] == manifest['old_source_pins'][name] for name in UNCHANGED),
        'unchanged_r188_guard_journal_reader_bridge')
    binding = manifest['historical_life_binding']
    require(manifest['deadline_unix'] == binding['hard_end_unix'] == 1789927200
        and manifest['lease_end_unix'] == 1789948800, 'same_hard_end_and_lease')
    require(binding['journal_id'] == manifest['journal_id'] == '260be8b8710a42559b291797c6e14983'
        and binding['source_pins'] == manifest['old_source_pins'], 'same_original_C2_journal_and_source')
    require(all(manifest[key] is False for key in ('admission_granted', 'receiving_plan_ready',
        'remote_staging_performed', 'native_binding_freshly_verified', 'plan_template_candidate_bound')),
        'local_preparation_is_not_live_authority')


def verify(source, manifest):
    validate(manifest)
    source = Path(source).absolute()
    require(source.resolve() == source, 'literal_source_directory')
    expected = dict(manifest['new_source_pins'])
    expected.update({name: value['sha256'] for name, value in manifest['additional_assets'].items()})
    for name in expected:
        path = PurePosixPath(name)
        require(name == str(path) and not path.is_absolute() and '..' not in path.parts,
            'literal_relative_closure_member')
    actual = {}
    for path in source.rglob('*'):
        require(not path.is_symlink(), 'no_symlink_in_source')
        require(path.is_dir() or path.is_file(), 'regular_source_members_only')
        if path.is_file():
            actual[str(path.relative_to(source))] = sha(path)
    require(actual == expected, 'entire_exact_source_including_no_extra_files')
    return manifest['new_source_pins']
