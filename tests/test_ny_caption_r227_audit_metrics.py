import hashlib
import json

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.audit_metrics import (
    apply_review, current_base_roots, hourly_rows, native_outcome_row, scored_sources,
)


def test_current_base_pointer_overrides_historical_load_and_binds_pid(tmp_path):
    phase = tmp_path / 'phase'
    current = phase / 'attempt2'
    current.mkdir(parents=True)
    (phase / 'LOADED.json').write_text(json.dumps(dict(pid=1)))
    (current / 'LOADED.json').write_text(json.dumps(dict(pid=2)))
    pointer = dict(root=str(current), scorer_root=str(phase / 'recovery_scorer'), loaded=dict(pid=2))
    (phase / 'CURRENT.json').write_text(json.dumps(pointer))
    assert current_base_roots(phase, tmp_path / 'original', tmp_path / 'shared') == (
        current, phase / 'recovery_scorer', current / 'LOADED.json')
    pointer['loaded']['pid'] = 1
    (phase / 'CURRENT.json').write_text(json.dumps(pointer))
    with pytest.raises(ValueError, match='loaded_mismatch'):
        current_base_roots(phase, tmp_path / 'original', tmp_path / 'shared')


def test_known_cached_outcomes_are_not_new_scores_or_new_reviewed_captions():
    raw = 'Literal caption.'
    digest = hashlib.sha256(raw.encode()).hexdigest()
    document = dict(raw_act=raw, report=dict(caption_sources=[dict(start=0, end=len(raw), text_sha256=digest)],
        feedback=[dict(caption_source_index=0, result=dict(ok=True, accepted=True, status='new_pixel')),
                  dict(caption_source_index=0, result=dict(ok=True, accepted=True, status='new_pixel', replayed=True)),
                  dict(result=dict(ok=False, error='unknown'))]))
    output = scored_sources(document)
    assert len(output) == 1 and output[0]['exact_source_span_verified']
    row = dict(receipt_sha256='receipt', scored=1, scored_sources=output)
    apply_review(row, {})
    assert row['unreviewed_scored_strings'] == 1
    assert row['literal_caption_attempt_reviewed'] == 0
    annotation = {'receipt': {'0': dict(classification='literal_caption_attempt', text_sha256=digest)}}
    apply_review(row, annotation)
    assert row['literal_caption_attempt_reviewed'] == 1
    annotation['receipt']['0']['text_sha256'] = 'changed'
    with pytest.raises(ValueError, match='exact_saved_source'):
        apply_review(row, annotation)


def test_think_salvage_remains_distinct_and_commentary_is_not_literal():
    raw = 'Commentary.'
    digest = hashlib.sha256(raw.encode()).hexdigest()
    document = dict(raw_act='No captions.', salvaged_THINK=dict(raw=raw), report=dict(
        caption_sources=[dict(stage='THINK', start=0, end=len(raw), text_sha256=digest)],
        feedback=[dict(caption_source_index=0, result=dict(ok=True, accepted=False))]))
    row = dict(receipt_sha256='receipt', scored=1, scored_sources=scored_sources(document))
    apply_review(row, {'receipt': {'0': dict(classification='commentary_or_program', text_sha256=digest)}})
    assert row['commentary_or_program_reviewed'] == 1
    assert row['literal_caption_attempt_reviewed'] == 0
    assert row['scored_sources'][0]['stage'] == 'THINK'
    assert document['raw_act'] == 'No captions.'


def test_hourly_partial_windows_and_duplicate_origins():
    rows = [dict(unix=100, origin_sha256='first', scored=2, accepted=1),
            dict(unix=3700, origin_sha256='second', scored=3, accepted=0)]
    buckets = hourly_rows(rows, 50, 4000)
    assert buckets['1970-01-01T00:00:00Z']['window_start_unix'] == 50
    assert buckets['1970-01-01T01:00:00Z']['window_end_unix'] == 4000
    assert sum(item['scored'] for item in buckets.values()) == 5
    with pytest.raises(ValueError, match='duplicate_ACT'):
        hourly_rows(rows + rows, 50, 4000)


def test_transport_failure_is_neither_judge_rejection_nor_format_fault():
    record = dict(index=16, sha256='record', document=dict(outcome=dict(environment=dict(
        origin=dict(record_sha256='actual-response'), report=dict(ok=False,
        error='ORIGIN_TRANSPORT_NOT_DISPATCHED', feedback=[])))))
    row = native_outcome_row(record, 123)
    assert row['transport_failure'] and row['scored'] == row['judge_rejected'] == 0
    assert not row['format_fault'] and not row['format_metrics_present']
    assert row['origin_sha256'] == 'actual-response'
