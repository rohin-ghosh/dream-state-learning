from copy import deepcopy
from pathlib import Path
import time

import pytest

from gpu import orch_r146_benchmark_enrollment_phase as phase
from tests.test_orch_r130_checkpoint_scheduler import copied_checkpoint, dump


@pytest.fixture
def prepared(tmp_path):
    now = time.time()
    registry = dict(schema=phase.scheduler.LINEAGES_SCHEMA,
                    lineages=[dict(lineage_id=name, cohort='original', initial_commit_sha256=character * 64)
                              for name, character in [('legacy', 'a'), ('pilot', 'b'), ('kernel', 'c')]])
    copies = tmp_path / 'copies'
    copies.mkdir()
    checkpoints = {role: copied_checkpoint(copies, role, steps=steps, created=now - age)
                   for role, steps, age in [('initial', 0, 100), ('firstsleep', 32, 60), ('latest', 70, 10)]}
    custody = tmp_path / 'CUSTODY.json'
    dump(custody, dict(synthetic=True, never_loaded=True))
    document = dict(schema=phase.SCHEMA,
                    entry=dict(lineage_id='r137_raw_fixture', cohort='R137',
                               initial_commit_sha256=checkpoints['initial']['commit_sha256'],
                               first_sleep_commit_sha256=checkpoints['firstsleep']['commit_sha256'],
                               programme_start_unix=now - 110), checkpoints=checkpoints,
                    custody=dict(receipt_path=str(custody), receipt_sha256=phase.sha(custody)))
    return dict(document=document, previous_registry=registry, copy_roots=[str(copies)],
                custody_roots=[str(tmp_path)], now=now)


def test_real_native_file_inventory_required_without_loading_model(prepared):
    before = deepcopy(prepared)
    checked = phase.proposal(**prepared)
    assert checked['checkpoints']['initial']['optimizer_steps'] == 0
    assert checked['source_custody_content_independently_reviewed'] is False
    extended = phase.extend_registry(prepared['previous_registry'], [checked])
    assert extended['lineages'][:3] == prepared['previous_registry']['lineages']
    assert len(phase.ready_candidates([checked])) == 3
    assert prepared == before


@pytest.mark.parametrize('change', ['unknown_field', 'old_lineage', 'cohort', 'missing_initial',
                                   'initial_hash', 'first_hash', 'custody_hash', 'future_start',
                                   'extra_checkpoint_field', 'adapter_changed', 'symlink'])
def test_reject_unbound_or_unsupported_proposals(prepared, change):
    document = prepared['document']
    if change == 'unknown_field':
        document['messages'] = []
    elif change == 'old_lineage':
        document['entry']['lineage_id'] = 'legacy'
    elif change == 'cohort':
        document['entry']['cohort'] = 'original'
    elif change == 'missing_initial':
        del document['checkpoints']['initial']
    elif change in ('initial_hash', 'first_hash'):
        document['entry']['initial_commit_sha256' if change == 'initial_hash' else 'first_sleep_commit_sha256'] = 'd' * 64
    elif change == 'custody_hash':
        document['custody']['receipt_sha256'] = 'e' * 64
    elif change == 'future_start':
        document['entry']['programme_start_unix'] = prepared['now'] + 100
    elif change == 'extra_checkpoint_field':
        document['checkpoints']['initial']['score'] = 1
    else:
        directory = Path(document['checkpoints']['initial']['manifest_path']).parent
        target = directory / 'adapter/adapter_model.safetensors'
        if change == 'adapter_changed':
            target.write_bytes(b'changed synthetic adapter')
        else:
            replacement = directory / 'replacement'
            target.rename(replacement)
            target.symlink_to(replacement)
    with pytest.raises(ValueError):
        phase.proposal(**prepared)


def test_reject_nonzero_initial_and_time_reversal(prepared):
    document = prepared['document']
    document['checkpoints']['initial'] = document['checkpoints']['firstsleep']
    document['entry']['initial_commit_sha256'] = document['entry']['first_sleep_commit_sha256']
    with pytest.raises(ValueError):
        phase.proposal(**prepared)


def test_reject_reversed_checkpoint_order(prepared):
    prepared['document']['checkpoints']['latest'] = prepared['document']['checkpoints']['initial']
    with pytest.raises(ValueError, match='chronological_checkpoint_roles'):
        phase.proposal(**prepared)


def test_registry_extension_cannot_rebind_original_baselines(prepared):
    checked = phase.proposal(**prepared)
    extended = phase.extend_registry(prepared['previous_registry'], [checked])
    phase.registry_delta(prepared['previous_registry'], extended)
    extended['lineages'][0]['initial_commit_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='every_prior_lineage_binding_preserved'):
        phase.registry_delta(prepared['previous_registry'], extended)
    with pytest.raises(ValueError, match='bounded_new_lineages_only'):
        phase.registry_delta(prepared['previous_registry'], prepared['previous_registry'])


def test_no_duplicate_lineages_or_ambiguous_ready(prepared):
    checked = phase.proposal(**prepared)
    with pytest.raises(ValueError):
        phase.extend_registry(prepared['previous_registry'], [checked, checked])
    checked['checkpoints']['latest'] = deepcopy(checked['checkpoints']['firstsleep'])
    assert len(phase.ready_candidates([checked])) == 2
    checked['checkpoints']['latest']['manifest_sha256'] = 'd' * 64
    with pytest.raises(ValueError):
        phase.ready_candidates([checked])


def test_original_and_ambiguous_reservations_count_against_budget():
    assert phase.remaining_budget(4800, set(range(78)), 20, 58) == 2
    assert phase.remaining_budget(4800, set(range(80)), 20, 58) == 0
    assert phase.remaining_budget(4800, set(range(20)), 57, 58) == 1
    for values in [(4801, set(), 0, 58), (4800, [], 0, 58), (4800, set(), 59, 58)]:
        with pytest.raises(ValueError):
            phase.remaining_budget(*values)


@pytest.mark.parametrize('remaining', [0, 179, 255.069, 254.169, 279.070, 3600, 3615])
def test_short_windows_defer_without_spending_a_reservation(remaining):
    result = phase.dispatch_window(dict(hard_end_unix=1000 + remaining, job_max_seconds=3600), 1000)
    assert result['status'] == 'DEFER_WITHOUT_RESERVATION'
    assert result['reservation_created'] is False
    assert result['failed_checkpoint_replayed'] is False


def test_full_dispatch_window_and_invalid_budget():
    config = dict(hard_end_unix=4616, job_max_seconds=3600)
    assert phase.dispatch_window(config, 1000)['status'] == 'FULL_JOB_WINDOW_AVAILABLE'
    for bad in [dict(config, job_max_seconds=300), dict(config, hard_end_unix=float('nan'))]:
        with pytest.raises(ValueError):
            phase.dispatch_window(bad, 1000)


def test_future_config_preserves_protocol_and_never_publishes(prepared, tmp_path):
    checked = phase.proposal(**prepared)
    registry = tmp_path / 'NEW_REGISTRY.json'
    registry_sha = dump(registry, phase.extend_registry(prepared['previous_registry'], [checked]))
    builder = tmp_path / 'BUILDER.md'
    builder.write_text('## [Builder] 2026-09-16 synthetic CPU admission test\n')
    original_registry = tmp_path / 'OLD_REGISTRY.json'
    original_sha = dump(original_registry, prepared['previous_registry'])
    previous = dict(physical_devices=[0, 1], operator_root=str(tmp_path),
                    lease_end_unix=prepared['now'] + 86400,
                    lineages_path=str(original_registry), lineages_sha256=original_sha,
                    builder_entry_path='previous_builder', builder_entry_sha256='b' * 64,
                    created_unix=1, hard_end_unix=2, first_dispatch_unix=1, output_root='previous_output',
                    max_jobs=8, job_max_seconds=3600, corpus_sha256='c' * 64,
                    ledger_root='same_ledger', sources={'same.py': 'd' * 64})
    before = deepcopy(previous)
    args = dict(previous=previous, registry_path=str(registry), registry_sha256=registry_sha,
                builder_path=str(builder), builder_sha256=phase.sha(builder),
                output_root=str(tmp_path / 'scheduler_run_r146_test'), now=prepared['now'],
                wall=prepared['now'] + 7200, remaining_jobs=4)
    proposed = phase.prospective_config(**args)
    phase.config_delta(previous, proposed)
    assert previous == before
    assert not Path(proposed['output_root']).exists()
    with pytest.raises(ValueError, match='enough_time_for_fixed_dispatch'):
        phase.prospective_config(**dict(args, wall=proposed['first_dispatch_unix'] + 3615))
    assert not Path(proposed['output_root']).exists()
    proposed['corpus_sha256'] = 'e' * 64
    with pytest.raises(ValueError):
        phase.config_delta(previous, proposed)
    with pytest.raises(ValueError):
        phase.prospective_config(**dict(args, wall=previous['lease_end_unix']))
