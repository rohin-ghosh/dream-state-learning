"""CPU-only prospective scheduling, recovery and intake invariants."""

from copy import deepcopy
import hashlib
import random
from types import SimpleNamespace

import pytest

from organism_v6 import orch_combined_l1_fifo_v1 as fifo
from organism_v6.orch_combined_l1_continual import ContinualLayout, rank_positions


def target(number):
    return hashlib.sha256(str(number).encode()).hexdigest()


def start(rows=20, update=30):
    counts = [0] * (222 + rows)
    layout = ContinualLayout(rows, 2)
    for step in range(1, update + 1):
        for row in layout.training_indexes(step):
            counts[row] += 1
    return fifo.start(update=update, corpus_targets=[target(number) for number in range(rows)],
        corpus_version=13, exposure_counts=counts, paired_anchor=dict(FULL=target(-1), OFF=target(-2)))


def intake(state, number=0, count=8):
    return dict(batch_id=f'future_{number}', manifest_sha256=target(100000 + number),
        native_receipt_sha256=target(200000 + number),
        corpus_targets=state['corpus_targets'] + [target(300000 + number * 100 + offset) for offset in range(count)],
        corpus_version=state['corpus_version'] + 1, origin='L1_EXTERNAL_GENERATION',
        parenting_experience=False, teacher_source=False)


def advance(state):
    proposed = fifo.plan(state)
    return fifo.commit_after_optimizer(state, proposed, actual_update=proposed['update']), proposed


def test_no_intake_exact_original_batches_and_counts():
    state = start()
    layout = ContinualLayout(20, 2)
    for unused in range(100):
        state, proposed = advance(state)
        assert proposed['rows'] == list(layout.training_indexes(state['update']))


def test_future_only_no_reclassifying_existing375_or_other_history():
    state = start(rows=3635, update=40)
    original = deepcopy(state)
    updated = fifo.ingest(state, **intake(state))
    assert state == original
    assert updated['fifo'] == list(range(3857, 3865))
    assert updated['exposure_counts'][:3857] == original['exposure_counts']
    assert updated['paired_anchor'] == original['paired_anchor']
    assert updated['rehearsal_cursor'] == original['rehearsal_cursor']


def test_every_future_row_once_first_with_frozen_legacy_facts():
    state = start()
    state = fifo.ingest(state, **intake(state, count=12))
    first_rows = list(state['fifo'])
    for index in range(12):
        state, proposed = advance(state)
        assert proposed['fifo_first_row'] == first_rows[index]
        offset = state['update'] - 1
        assert proposed['rows'][:2] == [offset % 128, 128 + offset % 82]
        assert state['exposure_counts'][first_rows[index]] == 1
    assert not state['fifo'] and len(state['first_future_presentations']) == 12


def test_later_arrivals_never_overtake_or_starve_initial_rehearsal():
    state = start(update=0)
    old_rows = set(state['rehearsal_ring'])
    first_batch = intake(state, count=8)
    state = fifo.ingest(state, **first_batch)
    original_fifo = list(state['fifo'])
    seen_rehearsal, first = set(), []
    for number in range(40):
        state = fifo.ingest(state, **intake(state, number=number + 1, count=2))
        state, proposed = advance(state)
        seen_rehearsal.add(proposed['rows'][2])
        first.append(proposed['fifo_first_row'])
    assert first[:8] == original_fifo
    assert old_rows <= seen_rehearsal
    assert len(set(first)) == len(first)
    assert state['batches'][0]['final_first_exposure_update_bound'] == 8


def test_exactly_once_after_later_intakes_and_rebound_rejection():
    initial = start()
    batch = intake(initial)
    state = fifo.ingest(initial, **batch)
    state = fifo.ingest(state, **intake(state, number=1))
    assert fifo.ingest(state, **batch) is state
    with pytest.raises(ValueError, match='rebound'):
        fifo.ingest(state, **dict(batch, manifest_sha256=target(99)))


@pytest.mark.parametrize('key,value,reason', [('origin', 'PARENT', 'external_qualified'),
    ('parenting_experience', True, 'external_qualified'), ('teacher_source', True, 'external_qualified'),
    ('native_receipt_sha256', '', 'native_admission'), ('corpus_version', 13, 'advancing_corpus')])
def test_intake_rejections_preserve_state(key, value, reason):
    state = start()
    before = deepcopy(state)
    with pytest.raises(ValueError, match=reason):
        fifo.ingest(state, **dict(intake(state), **{key: value}))
    assert state == before


def test_prefix_edits_duplicates_and_empty_deduplicated_batch():
    state = start()
    batch = intake(state)
    for targets, reason in [([target(-3)] + batch['corpus_targets'][1:], 'unchanged_corpus'),
                            (state['corpus_targets'] + [state['corpus_targets'][0]], 'dedup')]:
        with pytest.raises(ValueError, match=reason):
            fifo.ingest(state, **dict(batch, corpus_targets=targets))
    updated = fifo.ingest(state, **dict(batch, corpus_targets=state['corpus_targets']))
    assert not updated['fifo'] and updated['batches'][0]['added_rows'] == []


def test_planning_is_not_actual_exposure_and_commit_is_exactly_once():
    state = start()
    before = deepcopy(state)
    proposed = fifo.plan(state)
    assert state == before
    updated = fifo.commit_after_optimizer(state, proposed, actual_update=31)
    with pytest.raises(ValueError, match='stale_or_duplicate'):
        fifo.commit_after_optimizer(updated, proposed, actual_update=31)
    broken = deepcopy(proposed)
    broken['rows'][-1] += 1
    with pytest.raises(ValueError, match='bound_plan'):
        fifo.commit_after_optimizer(state, broken, actual_update=31)


def test_no_rng_use_and_paired_unequal_ranks_select_exact_same_rows():
    random.seed(64)
    before = random.getstate()
    full = fifo.ingest(start(), **intake(start()))
    off = deepcopy(full)
    for unused in range(15):
        full, full_plan = advance(full)
        off, off_plan = advance(off)
        assert full_plan == off_plan and full == off
        for world in (1, 2, 3):
            positions = [position for rank in range(world) for position in rank_positions(rank, world)]
            assert sorted(positions) == [0, 1, 2, 3]
    assert random.getstate() == before


def test_checkpoint_restores_pending_fifo_counters_and_optimizer_rng_hashes():
    state = fifo.ingest(start(), **intake(start()))
    state, unused = advance(state)
    files = {'adapter/adapter_model.safetensors': target(1), 'adapter/adapter_config.json': target(5),
             'optimizer.pt': target(2), 'rank0.pt': target(3), 'rank1.pt': target(4)}
    args = dict(native_update=state['update'], native_exposure_counts=state['exposure_counts'],
                native_file_hashes=files, native_world_size=2)
    saved = fifo.checkpoint(state, **args)
    restored = fifo.restore(saved, expected_sha256=saved['sha256'], **args)
    assert fifo.plan(restored) == fifo.plan(state)
    for number in range(50):
        state, unused = advance(state)
        restored, unused = advance(restored)
    assert state == restored
    with pytest.raises(ValueError, match='binding_drift'):
        fifo.restore(saved, expected_sha256=saved['sha256'], **dict(args, native_file_hashes=dict(files, **{'optimizer.pt': target(9)})))
    with pytest.raises(ValueError, match='adapter_optimizer_rng'):
        fifo.checkpoint(saved['body']['state'], **dict(args, native_world_size=3))


@pytest.mark.parametrize('field', ['fifo', 'exposure_counts', 'rehearsal_ring'])
def test_corrupted_state_fails_closed(field):
    state = fifo.ingest(start(), **intake(start()))
    state[field].pop()
    with pytest.raises(ValueError):
        fifo.validate(state)


def test_old_trajectory_dose_is_not_claimed_fixed_under_queue():
    initial = start(update=0)
    updated = fifo.ingest(initial, **intake(initial, count=8))
    old = deepcopy(initial)
    for unused in range(8):
        updated, unused = advance(updated)
        old, unused = advance(old)
    assert updated['exposure_counts'][:210] == old['exposure_counts'][:210]
    assert sum(updated['exposure_counts'][210:242]) == 8
    assert sum(old['exposure_counts'][210:242]) == 16


def test_existing_native_collator_masks_eos_and_global_reference_unchanged():
    from gpu import orch_guided_native as native
    state = fifo.ingest(start(), **intake(start()))
    proposed = fifo.plan(state)
    rows = []
    for index in range(len(state['exposure_counts'])):
        target_ids = tuple(range(10, 12 + index % 4)) + (99,)
        rows.append(native.source.native.EncodedRow((1, 2) + target_ids + (3,),
            (-100, -100) + target_ids + (-100,), target_ids))
    native.masks.validate_masks(rows, 99)
    layout = SimpleNamespace(row_count=len(rows), training_indexes=lambda update: tuple(proposed['rows']),
        masked_row_indexes=lambda arm: tuple(range(222, len(rows))) if arm == 'NEW_TRAJECTORY_LOSS_OFF' else ())
    full = native.training_batch(rows, layout, proposed['update'], pad_id=0)
    off = native.training_batch(rows, layout, proposed['update'], pad_id=0, replay_arm='NEW_TRAJECTORY_LOSS_OFF')
    assert full[0] == off[0] == tuple(proposed['rows'])
    assert full[1]['input_ids'] == off[1]['input_ids']
    assert full[1]['attention_mask'] == off[1]['attention_mask']
    assert full[2] == off[2] == sum(len(rows[index].target_ids) for index in proposed['rows'])
    for position, index in enumerate(proposed['rows']):
        if index >= 222:
            assert all(label == -100 for label in off[1]['labels'][position])
        else:
            assert full[1]['labels'][position] == off[1]['labels'][position]


def test_native_module_does_not_import_prospective_sampler():
    from pathlib import Path
    for path in ('gpu/orch_combined_l1_continual_run.py', 'gpu/orch_combined_l1_continual_guard.py'):
        assert 'orch_combined_l1_fifo_v1' not in Path(path).read_text()
