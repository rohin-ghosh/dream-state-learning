"""Focused CPU regression tests; no model loading or external calls."""

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from gpu import orch_guided_native as native
from gpu import orch_rich_breadth_bootstrap_run as run
from gpu.orch_l2_rich_math_bootstrap import read, sha
from organism_v6 import orch_rich_breadth_bootstrap as policy
from tests.test_experienced_event_two_hop_lesson import Tokenizer


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / 'research_notes/analysis/orch_rich_breadth_bootstrap_20260915_attempt1'


def encoded_row(target=(12, 13, 99)):
    return native.source.native.EncodedRow((1, 2) + target + (3,),
        (-100, -100) + target + (-100,), target)


def test_original_schedule_is_exact_all_224_updates():
    layout = policy.BreadthLayout(16)
    assert layout.updates == policy.BASELINE.updates == 224
    for update in range(1, 225):
        assert layout.training_indexes(update) == policy.BASELINE.training_indexes(update)
    assert layout.presentation_counts() == policy.BASELINE.presentation_counts()


def test_all256_new_slots_only_are_remapped_to_frozen_cycle():
    layout = policy.BreadthLayout(26)
    ordinal = 0
    for update in range(1, 225):
        old = policy.BASELINE.training_indexes(update)
        new = layout.training_indexes(update)
        for original, mapped in zip(old, new):
            if original < 222:
                assert original == mapped
            else:
                assert mapped == 222 + ordinal % 26
                ordinal += 1
    assert ordinal == 256


def test_legacy_selection_exposure_and_per_row_counts_exact():
    baseline = policy.BASELINE.presentation_counts()
    for size in (16, 26):
        counts = policy.BreadthLayout(size).presentation_counts()
        assert counts[:222] == baseline[:222]
        assert sum(counts[:128]) == 224
        assert sum(counts[128:210]) == 224
        assert counts[210:222] == (16,) * 12
        assert sum(counts[222:]) == 256
        assert sum(counts) == 896
    assert policy.BreadthLayout(26).presentation_counts()[222:] == (10,) * 22 + (9,) * 4


@pytest.mark.parametrize('size', [16, 26])
def test_full_off_pair_exact_inputs_and_legacy_labels_for_every_update(size):
    rows = tuple(encoded_row((12,) * (index % 4 + 1) + (99,)) for index in range(222 + size))
    layout = policy.BreadthLayout(size)
    audit = run.token_audit(rows, layout, 0)
    assert audit['full_supervised_tokens'] > audit['off_supervised_tokens'] > 0
    assert audit['full_supervised_tokens'] == audit['new_supervised_tokens'] + audit['legacy_supervised_tokens']
    assert layout.masked_row_indexes('NEW_TRAJECTORY_LOSS_OFF') == tuple(range(222, 222 + size))
    assert layout.masked_row_indexes('FULL_TARGET') == ()


def test_native_layout_boundary_accepts_custom_subclass_and_rejects_legacy_drift():
    legacy = (encoded_row(),) * 222
    new = (encoded_row(),) * 26
    result = native.assemble_replay(legacy, new, policy.BreadthLayout(26), legacy_reference=legacy, eos_token_id=99)
    assert result == legacy + new
    with pytest.raises(ValueError):
        native.assemble_replay(legacy, new, policy.BreadthLayout(26), legacy_reference=legacy[:-1], eos_token_id=99)


def test_native_eos_context_suffix_masks_remain_strict():
    row = encoded_row()
    arguments = dict(prefix_ids=(1, 2), target_ids=(12, 13), suffix_ids=(3,), eos_token_id=99,
        validate_masks=native.masks.validate_masks)
    native.bridge.validate_encoding_boundary(row, **arguments)
    for labels in ((1,) + row.labels[1:], row.labels[:-1] + (3,), row.labels[:4] + (-100, -100)):
        with pytest.raises(ValueError):
            native.bridge.validate_encoding_boundary(replace(row, labels=labels), **arguments)
    with pytest.raises(ValueError):
        native.bridge.validate_encoding_boundary(replace(row, target_ids=(12, 13)), **arguments)


def test_encode_rows_not_fixed16_validator_and_no_target_rewrite():
    tokenizer = Tokenizer()
    row = dict(student_prefix=[dict(role='user', content='Question')], target='.' * 180)
    with patch.object(run.encoding, 'validate_packet', side_effect=AssertionError('fixed16_not_called')):
        encoded = run.encoding.encode_rows([row] * 26, tokenizer)
    assert len(encoded) == 26 and row['target'] == '.' * 180
    assert all(item.target_ids[-1] == tokenizer.eos_token_id for item in encoded)
    with pytest.raises(AssertionError):
        run.encoding.encode_rows([dict(row, target='.' * 401)], tokenizer)


@pytest.mark.parametrize('size,presentations', [(10, 16), (27, 16), (26, 4), (True, 16)])
def test_no_corpus_or_epoch_extension(size, presentations):
    with pytest.raises(ValueError):
        policy.BreadthLayout(size, presentations)


def test_no_out_of_budget_updates():
    for update in (0, 225, True, 2.5):
        with pytest.raises(ValueError):
            policy.BreadthLayout(26).training_indexes(update)


def test_exact_packet_bindings_and_new_admission_forbidden():
    assert run.validate_packet_files(ARTIFACT)['author_only_qualification']
    packet = ARTIFACT / 'PACKET'
    first, extra, combined = (read(packet / name) for name in ('FIRST16.json', 'ADDITIONAL10.json', 'COMBINED26.json'))
    altered = deepcopy(combined)
    altered[0]['target'] += ' '
    with pytest.raises(AssertionError):
        policy.validate_packets(first, extra, altered)
    with pytest.raises(AssertionError):
        policy.validate_packets(first, extra[:-1], first + extra[:-1])
    with pytest.raises(AssertionError):
        policy.validate_packets(first, list(reversed(extra)), combined)


def test_cohort_frozen_balanced_anscombe_excluded_and_original_prompts():
    document = read(ARTIFACT / 'COHORT.json')
    assert sha(ARTIFACT / 'COHORT.json') == run.COHORT_SHA
    assert Counter(task['family'] for task in document['tasks']) == policy.QUOTAS
    assert len({task['id'] for task in document['tasks']}) == 32
    prior = read(ROOT / 'research_notes/analysis/orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json')
    assert not {task['id'] for task in prior['tasks']} & {task['id'] for task in document['tasks']}
    assert not {task['question_sha256'] for task in prior['tasks']} & {task['question_sha256'] for task in document['tasks']}
    for task, prompt in zip(document['tasks'], document['prompts']):
        assert prompt == policy.original.prompt(task, 'rich')[0]
    assert read(ARTIFACT / 'DATA_PROVENANCE.json')['anscombe_outcomes_read'] is False


def test_cohort_deterministic_and_normalized_aliases_excluded():
    records = [dict(question=f'Question {index}: 10% of 100?', answer='#### 10') for index in range(40)]
    exclusions = [dict(id='gsm8k-train-0', question=records[1]['question'].upper())]
    with patch.object(policy, 'QUOTAS', dict(percentages=32)):
        first = policy.cohort(records, exclusions)
        assert first == policy.cohort(records, exclusions)
    assert not {'gsm8k-train-0', 'gsm8k-train-1'} & {task['id'] for task in first['tasks']}


def test_call_caps_reserved_before_execution_no_overwrite(tmp_path):
    for index in range(80):
        cap = 1536 if index < 32 else 160
        path, record = run.reserve(tmp_path, index, [], cap, {})
        assert path.exists() and record['status'] == 'RESERVED'
    with pytest.raises(FileExistsError):
        run.reserve(tmp_path, 0, [], 1536, {})
    for index, cap in ((80, 160), (0, 160), (32, 1536)):
        with pytest.raises(AssertionError):
            run.reserve(tmp_path, index, [], cap, {})
    assert policy.CALLS_TOTAL == 4 * policy.CALLS_PER_CELL == 320
    assert policy.SECONDS == 7200 and policy.GPU_HOURS == 4 * policy.SECONDS / 3600 == 8


def test_deadline_includes_load_training_and_readout():
    with patch.object(run.time, 'time', return_value=100):
        for phase in ('load', 'update', 'generation', 'reserve', 'launch_train', 'launch_readout'):
            with pytest.raises(AssertionError):
                run.check_deadline(dict(native_deadline_unix=100), phase)
            run.check_deadline(dict(native_deadline_unix=101), phase)


def test_generation_uses_only_original_legacy_or_math_caps():
    engine = object.__new__(run.ReadoutEngine)
    with patch.object(run.portable.source.Engine, 'generate', return_value='legacy') as legacy:
        assert engine.generate([], max_new_tokens=160) == 'legacy'
        legacy.assert_called_once_with(engine, [], max_new_tokens=160)
    with patch.object(run.RichEngine, 'generate', return_value='math') as math:
        assert engine.generate([], max_new_tokens=1536) == 'math'
        math.assert_called_once_with([], max_new_tokens=1536)
    with pytest.raises(AssertionError):
        engine.generate([], max_new_tokens=512)


def test_fresh_original_initialization_and_same_recipe_for_all_cells():
    assert run.RECIPE == dict(optimizer='AdamW', learning_rate=0.00003, seed=8203,
        optimizer_kwargs=dict(betas=[0.9, 0.999], eps=1e-8, weight_decay=0.01,
            amsgrad=False, foreach=False, fused=False))
    assert set(index for index, uuid in policy.DEVICES.values()) == {0, 1, 2, 3}
    assert {run.layout_for(cell).updates for cell in policy.CELLS} == {224}
    for cell in policy.CELLS:
        manifest = run.layout_for(cell).manifest(run.replay_arm(cell))
        assert manifest['new_target_presentations'] == 256
        assert manifest['old_trajectory_presentations'] == 192
        assert manifest['new_supervised_presentations'] == (256 if cell.endswith('_FULL') else 0)
