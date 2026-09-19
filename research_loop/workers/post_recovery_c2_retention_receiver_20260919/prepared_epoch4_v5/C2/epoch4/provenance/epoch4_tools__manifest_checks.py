"""Exact candidate source verification; never grants prefix or native authority."""

import hashlib
from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def delta(before, after):
    return {name: dict(before=before.get(name), after=after.get(name))
        for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)}


def verify(source, manifest):
    require(manifest['schema'] == 'C2_EPOCH4_OFFLINE_CANDIDATE_V1', 'exact_epoch4_candidate_schema')
    changes = {'gpu/checkpoint_tail_runtime.py', 'gpu/immutable_prefix_proof.py', 'gpu/c2_prefix_authority.py',
        'gpu/c2_retention_runtime.py', 'gpu/orch_r125_continual_guard.py'}
    require(delta(manifest['epoch3_source_pins'], manifest['new_source_pins']) == manifest['epoch3_to_epoch4_delta']
        and set(manifest['epoch3_to_epoch4_delta']) == changes, 'five_explicit_epoch3_epoch4_deltas')
    require(delta(manifest['old_source_pins'], manifest['new_source_pins']) == manifest['changed']
        and len(manifest['changed']) == 9 and len(manifest['new_source_pins']) == 186, 'nine_old_live_deltas_186_files')
    for name in ('gpu/r188_node5_confinement.py', 'gpu/orch_r125_continual_native.py',
            'gpu/r184_cpu_bridge.py', 'gpu/orch_r125_stream_journal.py', 'organism_v6/orch_r124_train_history.py'):
        require(manifest['new_source_pins'][name] == manifest['epoch3_source_pins'][name], 'preserved_source:' + name)
    require(manifest['deadline_unix'] == 1789927200 and manifest['lease_end_unix'] == 1789948800,
        'unchanged_C2_bounds')
    require(manifest['trust_review_required'] is True and manifest['same_namespace_native_admission_proven'] is False
        and manifest['actual_30_second_budget_proven'] is False, 'candidate_not_operational_approval')
    source = Path(source).absolute()
    require(source.resolve() == source, 'literal_source')
    actual = {}
    for path in source.rglob('*'):
        require(not path.is_symlink(), 'no_symlink_source')
        if path.is_file():
            actual[str(path.relative_to(source))] = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = dict(manifest['new_source_pins'])
    expected.update({name: value['sha256'] for name, value in manifest['additional_assets'].items()})
    require(actual == expected, 'entire_exact_epoch4_source_no_extra_files')
    return manifest['new_source_pins']
