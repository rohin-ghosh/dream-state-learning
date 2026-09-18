"""Regression gates for explicit764-row scope, not the superseded26 layout."""

from collections import Counter
from pathlib import Path
from unittest.mock import patch

import pytest

from gpu import orch_rich_breadth_bootstrap_scale as run
from gpu.orch_l2_rich_math_bootstrap import read, sha
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout
from tests.orch_rich_breadth_bootstrap_test import encoded_row


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / 'research_notes/analysis/orch_rich_breadth_bootstrap_20260915_attempt1/scale764'


def test_entire764_snapshot_qualification_gold_prefix_bindings_no1000gate():
    assert run.validate_packet(ARTIFACT)['rows'] == 764
    assert run.validate_packet(ARTIFACT)['tasks'] == 563
    assert sha(ARTIFACT / 'PACKET/ADMITTED_ROWS.json') == run.PACKET_SHA


def test_standard_layout_exact6208updates_and16presentations_each():
    assert type(run.LAYOUT) is GoalReplayLayout
    assert run.LAYOUT.updates == 6208 and run.LAYOUT.group_sizes == (128, 20, 62, 12, 764)
    counts = Counter(index for update in range(1, 6209) for index in run.LAYOUT.training_indexes(update))
    assert all(counts[index] == 16 for index in range(210, 986))
    assert sum(counts[index] for index in range(222, 986)) == 12224
    assert sum(counts[index] for index in range(128)) == 6208
    assert sum(counts[index] for index in range(128, 210)) == 6208
    assert sum(counts[index] for index in range(210, 222)) == 192
    assert sum(counts.values()) == 4 * 6208


def test_all24832_batch_slots_matched_full_off_and_old_labels_unchanged():
    rows = tuple(encoded_row((12,) * (index % 3 + 1) + (99,)) for index in range(986))
    audit = run.common.token_audit(rows, run.LAYOUT, 0)
    assert audit['full_off_inputs_identical'] and audit['full_off_legacy_labels_identical']
    assert audit['full_supervised_tokens'] == audit['new_supervised_tokens'] + audit['off_supervised_tokens']
    assert run.LAYOUT.masked_row_indexes('NEW_TRAJECTORY_LOSS_OFF') == tuple(range(222, 986))


def test_existing_reserved64_exact_no_new_selection_or_training_overlap():
    cohort = read(ARTIFACT / 'COHORT.json')
    assert cohort['tasks'] == read(ARTIFACT / 'TASKS_SOURCE.json')['held_tasks']
    assert cohort['held_outcomes_inspected'] is False and cohort['new_selection'] is False
    assert Counter(task['family'] for task in cohort['tasks']) == dict(geometry_measurement=32, age_time_relations=32)
    train = {row['task_id'] for row in read(ARTIFACT / 'PACKET/ADMITTED_ROWS.json')}
    assert not train & {task['id'] for task in cohort['tasks']}
    assert cohort['prompts'] == [run.scale.original.prompt(task, 'rich')[0] for task in cohort['tasks']]


def test_pair_caps12hours24gpuh112calls_each_and_lease_margin():
    assert run.SECONDS == 12 * 3600 and run.GPU_HOURS == 24
    assert run.MATH_TASKS == 64 and run.CALLS_PER_CELL == 64 + 48
    assert run.CALLS_TOTAL == 224 and run.CALLS_TOTAL == len(run.CELLS) * run.CALLS_PER_CELL
    assert set(index for index, uuid in run.DEVICES.values()) == {0, 1}
    assert run.LEASE_END - 21600 > 1789442100 + run.SECONDS


def test_phase_boundaries_and_exclusive_call_reservations(tmp_path):
    with patch.object(run.common, 'policy', run):
        for index in range(112):
            cap = 1536 if index < 64 else 160
            run.common.reserve(tmp_path, index, [], cap, {})
        with pytest.raises(AssertionError):
            run.common.reserve(tmp_path, 112, [], 160, {})
        with pytest.raises(AssertionError):
            run.common.reserve(tmp_path, 64, [], 1536, {})
        with pytest.raises(FileExistsError):
            run.common.reserve(tmp_path, 0, [], 1536, {})


def test_superseded26_attempt_preserved_not_restarted():
    old = ARTIFACT.parent
    assert read(old / 'SUPERSEDED_STOP.json')['historical_launch_already_started'] is True
    assert all(value['updates'] == 8 for value in read(old / 'SUPERSEDED_STOP.json')['cells'].values())
    assert read(old / 'TERMINAL.json')['readout_calls'] == 0
    assert all(read(old / 'TERMINAL.json')['release'].values())
    assert sha(old / 'source.tar') == 'a6de5326d445bfc9bb0ff42d4796224fbe81602588ef62b6eff1f1ff4b1fbabb'


def test_privileged_scanner_adapter_keeps_exact_host_binding():
    expected = run.existing_scan.policy.HOST_SHA
    assert run.HOST_SHA == expected
    with patch.object(run.os, 'geteuid', return_value=0), patch.object(run.socket, 'gethostname', return_value='[REDACTED_HOST]'):
        def scanner(index, service):
            assert run.existing_scan.policy.HOST_SHA == expected
            assert dict(run.existing_scan.policy.DEVICES.values()) == dict(run.DEVICES.values())
            return dict(clear=True)
        with patch.object(run.existing_scan, 'policy'), patch.object(run.existing_scan, 'scan', side_effect=scanner):
            assert run.scan(0, Path('service.json'))['clear']


def test_admission_repair_cannot_reset_global_clock():
    import inspect
    source = inspect.getsource(run.common.launch)
    assert 'started = time.time() if original_started_unix is None else original_started_unix' in source
    assert 'hard_deadline_unix=started + policy.SECONDS' in source
    assert 'native_deadline_unix=started + policy.SECONDS - 360' in source
