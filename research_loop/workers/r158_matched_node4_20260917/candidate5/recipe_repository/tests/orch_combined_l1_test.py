"""Pure combined-source, native-dose and pre-readout child handoff regression."""

from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from gpu import orch_combined_l1_run as run
from gpu import orch_combined_l1_watch as watcher
from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from tests.orch_rich_breadth_bootstrap_test import encoded_row


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / 'research_notes/analysis/orch_combined_l1_20260915_attempt1'


def test_entire_frozen_inventory_and_single_exact_target_duplicate():
    manifest = run.validate_corpus(ARTIFACT)
    assert manifest['rows'] == 2394 and len(manifest['duplicates']) == 1
    assert manifest['duplicates'][0]['corpus'] == 'TWO_PASS9'
    packet = read(ARTIFACT / 'PACKET/ADMITTED_ROWS.json')
    assert [entry['row'] for entry in packet[:1452]] == read(ARTIFACT / 'SEQ266/TRAINING_ROWS.json')['new_trajectory_rows']
    assert [entry['row'] for entry in packet[1452:2216]] == read(ARTIFACT / 'SOURCES/MATH764.json')
    assert [entry['corpus'] for entry in packet].count('INTENSITY56') == 56
    assert [entry['corpus'] for entry in packet].count('TWO_PASS9') == 8


def test_exact19248updates_16presentations_and_matched_old_dose():
    layout = run.LAYOUT
    assert layout.updates == 19248 and layout.new_trajectory_rows == 2394
    counts = Counter(index for update in range(1, layout.updates + 1) for index in layout.training_indexes(update))
    assert all(counts[index] == 16 for index in range(210, 2616))
    assert sum(counts[index] for index in range(222, 2616)) == 38304
    assert sum(counts[index] for index in range(128)) == 19248
    assert sum(counts[index] for index in range(128, 210)) == 19248
    assert sum(counts[index] for index in range(210, 222)) == 192


def test_every_batch_full_off_input_and_old_label_equivalence():
    rows = tuple(encoded_row((12,) * (index % 3 + 1) + (99,)) for index in range(2616))
    audit = run.common.token_audit(rows, run.LAYOUT, 0)
    assert audit['full_off_inputs_identical'] and audit['full_off_legacy_labels_identical']
    assert audit['full_supervised_tokens'] == audit['new_supervised_tokens'] + audit['off_supervised_tokens']


def test_encoder_reuses_original1452_boundary_and_all_whole_rich_targets():
    packet = read(ARTIFACT / 'PACKET/ADMITTED_ROWS.json')
    original = run.math_encoder.digest(packet)
    with patch.object(run.route, 'encode_new_rows', return_value=(encoded_row(),) * 1452) as terse:
        with patch.object(run.math_encoder, 'encode_rows', return_value=(encoded_row(),)) as rich:
            encoded = run.encode_rows(packet, object())
    assert len(encoded) == 2394 and rich.call_count == 942
    assert terse.call_args.args[0] == [entry['row'] for entry in packet[:1452]]
    assert run.math_encoder.digest(packet) == original
    with pytest.raises(AssertionError):
        run.encode_rows(packet[:-1], object())


def test_held_both_families_and_source_text_worlds_disjoint():
    packet = read(ARTIFACT / 'PACKET/ADMITTED_ROWS.json')
    math_ids = {entry['row']['task_id'] for entry in packet if entry['encoding'] == 'math'}
    held = read(ARTIFACT / 'COHORT.json')
    assert len(held['tasks']) == 64 and not math_ids & {task['id'] for task in held['tasks']}
    routes = read(ARTIFACT / 'ROUTE_COHORT.json')
    assert len(routes['probes']) == 16 and routes['conditions'] == ['OWN_TEXT', 'UNAVAILABLE']
    serialized = run.json.dumps(packet, ensure_ascii=False)
    for probe in routes['probes']:
        assert not any(identity in serialized for identity in run.route.goal.identifiers(probe['collection']['world']))


def test_budgets_and_original_generation_caps():
    assert run.SECONDS == 43200 and run.GPU_HOURS == 24
    assert run.CALLS_TOTAL == 2 * (64 + 16 * 4 * 2 * 6 + 48) == 1760
    assert run.MATH_CAP == 1536 and run.LEGACY_CAP == 160
    assert set(index for index, uuid in run.DEVICES.values()) == {0, 1}


def test_handoff_is_complete_child_only_and_does_not_wait_held_scores(tmp_path):
    directory = tmp_path / 'COMBINED_FULL/fit'
    directory.mkdir(parents=True)
    write(directory / 'COMPLETE.json', dict(status='COMPLETE', updates=19248,
        input_adapter=dict(state_sha256='initial'), output_adapter=dict(state_sha256='learned')))
    for name in ('PREPARE.json', 'source.tar'):
        (tmp_path / name).write_text('test_fixture')
    adapter = SimpleNamespace(path=str(directory / 'adapter'), state_sha256='learned',
        document=lambda: dict(path=str(directory / 'adapter'), state_sha256='learned'))
    with patch.object(run.common.bridge.AdapterIdentity, 'from_document', return_value=adapter):
        run.handoff(tmp_path)
    handoff = read(tmp_path / 'FULL_CHILD_HANDOFF.json')
    assert handoff['recipient'] == 'Anscombe' and handoff['held_results_required'] is False
    assert handoff['schema'] == 'COMBINED_L1_FULL_CHILD_READY_V1'
    assert not (tmp_path / 'COMBINED_FULL/readout').exists()
    write(directory / 'COMPLETE.json', dict(status='COMPLETE', updates=8))
    with pytest.raises(AssertionError):
        run.handoff(tmp_path)


def test_watcher_copies_exact_handoff_without_reading_held_results(tmp_path):
    document = dict(schema='COMBINED_L1_FULL_CHILD_READY_V1', status='FIT_COMPLETE_HELD_SCORES_NOT_REQUIRED',
        recipient='Anscombe', updates=19248, child_path='/native/verified/adapter')
    result = SimpleNamespace(returncode=0, stdout=run.json.dumps(document))
    with patch.object(watcher.subprocess, 'run', return_value=result) as called:
        watcher.watch(ROOT, tmp_path, watcher.time.time() + 10)
    assert read(tmp_path / 'FULL_CHILD_HANDOFF.json') == document
    assert 'FULL_CHILD_HANDOFF.json' in called.call_args.args[0][-1]
    assert 'readout' not in called.call_args.args[0][-1]


def test_scanner_policy_keeps_host_and_exact_two_devices():
    with patch.object(run.os, 'geteuid', return_value=0), patch.object(run.socket, 'gethostname', return_value='[REDACTED_HOST]'):
        def scan(index, service):
            assert run.scanner.policy.HOST_SHA == run.HOST_SHA
            assert run.scanner.policy.DEVICES == run.DEVICES
            return dict(clear=True)
        with patch.object(run.scanner, 'policy'), patch.object(run.scanner, 'scan', side_effect=scan):
            assert run.scan(0, Path('service.json'))['clear']
