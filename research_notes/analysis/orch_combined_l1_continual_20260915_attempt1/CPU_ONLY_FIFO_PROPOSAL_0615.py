"""Counterfactual integer-slot analysis only; never imported by the trainer."""

from collections import Counter
import hashlib
import json

from organism_v6.orch_combined_l1_continual import ContinualLayout


def analyze():
    layout = ContinualLayout(3635, 2)
    updates = list(range(2021, 3648))
    original = [list(layout.training_indexes(update)) for update in updates]
    reordered = [list(batch) for batch in original]
    fresh = list(range(3482, 3857))
    original_slots = {row: (offset, position) for offset, batch in enumerate(original)
        for position, row in enumerate(batch) if row in fresh}
    assert len(original_slots) == len(fresh) == 375
    swaps = []
    for offset, row in enumerate(fresh):
        position = 3
        assert original[offset][position] >= 222
        source_offset, source_position = original_slots[row]
        assert source_offset > offset and reordered[source_offset][source_position] == row
        displaced = reordered[offset][position]
        reordered[offset][position], reordered[source_offset][source_position] = row, displaced
        swaps.append(dict(row=row, early_update=updates[offset], position=position,
            repayment_update=updates[source_offset], repayment_position=source_position))
    assert Counter(row for batch in original for row in batch) == Counter(row for batch in reordered for row in batch)
    for before, after in zip(original, reordered):
        assert before[:2] == after[:2]
        for position, row in enumerate(before):
            if row < 222:
                assert after[position] == row
    hash_grid = lambda grid: hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()
    first = lambda grid: next(updates[offset] for offset, batch in enumerate(grid) if any(row in fresh for row in batch))
    last_first = lambda grid: max(next(updates[offset] for offset, batch in enumerate(grid) if row in batch) for row in fresh)
    return dict(status='CPU_ONLY_ILLUSTRATION_NOT_AUTHORIZED_OR_IMPLEMENTED',
        corpus_rows=3635, fresh_rows=375, window_start=2021, window_end=3647,
        original_first=first(original), original_all=last_first(original),
        proposed_first=first(reordered), proposed_all=last_first(reordered),
        swaps=len(swaps), old222_slots_unchanged=True, window_row_multiset_identical=True,
        full_off_share_identical_grid=True, grid_sha256=dict(original=hash_grid(original), proposed=hash_grid(reordered)),
        scope='Fixed V13 snapshot only. No runtime input, GPU/model call, optimizer access, or checkpoint mutation.',
        limitations=['Does not certify arbitrary concurrent arrivals or wall-clock latency.',
            'Old nonlegacy rehearsal is temporally displaced and repaid at reserved future slots.',
            'Same window doses do not imply same optimizer trajectory or per-update normalization.'])


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2))
