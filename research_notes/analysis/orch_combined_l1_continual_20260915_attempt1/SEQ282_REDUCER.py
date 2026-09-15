"""Descriptive held-output measures, separate from correctness and admission."""

from collections import Counter
import hashlib
import re


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def normalized(text):
    return ' '.join(text.casefold().split())


def repetition(text):
    sentences = [normalized(part) for part in re.split(r'(?<=[.!?])\s+|\n+', text) if part.strip()]
    words = re.findall(r'\w+', text.casefold())
    windows = [tuple(words[index:index + 4]) for index in range(max(0, len(words) - 3))]
    sentence_counts, window_counts = Counter(sentences), Counter(windows)
    return dict(sentence_units=len(sentences), repeated_sentence_occurrences=sum(
        count - 1 for count in sentence_counts.values()), word_fourgrams=len(windows),
        repeated_fourgram_occurrences=sum(count - 1 for count in window_counts.values()),
        repeated_fourgram_rate=sum(count - 1 for count in window_counts.values()) / max(1, len(windows)),
        repetition_is_lexical_not_semantic=True, used_as_quality_gate=False)


def validate_annotation(text, annotation):
    assert annotation['response_sha256'] == text_hash(text), 'annotation_response_binding'
    assert annotation['review_kind'] == 'AUTHOR_DESCRIPTIVE_FULL_OUTPUT'
    assert annotation['full_output_read'] is True
    assert annotation['parent_access'] is False
    assert annotation['reviewer'].strip() and annotation['reason'].strip()
    paths = annotation['considered_paths']
    assert len({path['id'] for path in paths}) == len(paths), 'duplicate_path_id'
    assert len({normalized(path['operation']) for path in paths}) == len(paths), 'duplicate_operation'
    for index, path in enumerate(paths):
        assert path['operation'].strip() and path['evidence'] and path['evidence'] in text
        assert path['actually_considered_not_merely_named'] is True
        if index:
            assert path['substantively_distinct'] is True and path['distinction_reason'].strip()
    identifiers = {path['id'] for path in paths}
    rejections = annotation['rejections']
    assert len({entry['path_id'] for entry in rejections}) == len(rejections), 'duplicate_rejection'
    for entry in rejections:
        assert entry['path_id'] in identifiers, 'unbound_rejected_path'
        assert entry['rejection_evidence'] and entry['rejection_evidence'] in text
        assert entry['reason_evidence'] and entry['reason_evidence'] in text
        assert entry['problem_grounded_reason'] is True
    return dict(status='AUTHOR_DESCRIBED_NOT_INDEPENDENTLY_CERTIFIED',
        distinct_paths_considered=len(paths), distinct_alternatives_considered=max(0, len(paths) - 1),
        paths_rejected_with_grounded_reason=len(rejections), annotation=annotation,
        used_as_quality_gate=False, improvement_claim=False)


def token_metrics(response, cap):
    if not isinstance(response, dict) or 'token_ids' not in response:
        return dict(status='UNAVAILABLE_NOT_ESTIMATED', generated_tokens=None, eos=None, ceiling=None)
    tokens = response['token_ids']
    assert isinstance(tokens, list) and len(tokens) <= cap
    eos, ceiling = response['terminal'], response['truncated']
    assert isinstance(eos, bool) and isinstance(ceiling, bool)
    assert ceiling == (not eos and len(tokens) == cap)
    return dict(status='EXACT_NATIVE_IDS', generated_tokens=len(tokens), includes_terminal_eos=eos,
        text_tokens=len(tokens) - int(eos), eos=eos, ceiling=ceiling, cap=cap)


def describe(text, annotation=None):
    assert isinstance(text, str)
    semantic = dict(status='UNASSESSED', distinct_paths_considered=None,
        distinct_alternatives_considered=None, paths_rejected_with_grounded_reason=None,
        used_as_quality_gate=False, improvement_claim=False)
    if annotation is not None:
        semantic = validate_annotation(text, annotation)
    coherence = dict(status='UNASSESSED', judgment=None, evidence=None)
    if annotation is not None and 'coherence' in annotation:
        coherence = annotation['coherence']
        assert coherence['judgment'] in ('COHERENT', 'MIXED', 'INCOHERENT')
        assert coherence['evidence'] and coherence['evidence'] in text and coherence['reason'].strip()
        coherence = dict(coherence, status='AUTHOR_DESCRIBED_NOT_INDEPENDENTLY_CERTIFIED')
    return dict(schema='COMBINED_L1_HELD_BEHAVIOR_V2', response_sha256=text_hash(text),
        repetition=repetition(text), semantic=semantic, parent_access=False,
        coherence=coherence, report_order=['richness', 'accuracy'], correctness_is_primary=False,
        accuracy_retained=True, length_register_keywords_are_not_behavior_verdicts=True)
import datetime
import json
from pathlib import Path
from statistics import mean, median
import sys


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize_native(directory, expected_calls):
    loaded_path = directory / 'LOADED.json'
    if not loaded_path.exists():
        return dict(status='NOT_LOADED', native_path=str(directory))
    loaded = json.loads(loaded_path.read_text())
    assert loaded['parent_present'] is False
    files = sorted(directory.glob('CALL_*.json'))
    calls = [json.loads(path.read_text()) for path in files]
    terminal = directory / 'COMPLETE.json'
    status_counts = dict(Counter(call['status'] for call in calls))
    result = dict(native_path=str(directory), loaded_sha256=file_digest(loaded_path),
        status='COMPLETE' if terminal.exists() else 'RUNNING',
        actual_call_files=len(files), status_counts=status_counts,
        source_call_manifest_sha256=hashlib.sha256(json.dumps(
            [(path.name, file_digest(path)) for path in files], separators=(',', ':')).encode()).hexdigest(),
        parent_present=False, raw_text_included=False)
    if not terminal.exists():
        return result
    complete = json.loads(terminal.read_text())
    assert complete['status'] == 'COMPLETE'
    assert len(calls) == expected_calls == complete['calls']
    assert all(call['status'] == 'COMPLETE' for call in calls)
    math_calls = [call for call in calls if call['metadata'].get('purpose') in ('math', 'math_held')]
    assert len(math_calls) == 64
    metrics = [token_metrics(call['response'], call.get('max_new_tokens', 1536)) for call in math_calls]
    lengths = [metric['generated_tokens'] for metric in metrics]
    outcomes = json.loads((directory / 'MATH_ROWS.json').read_text())
    assert len(outcomes) == 64
    correct = sum(row['outcome_pass'] for row in outcomes)
    if 'math_correct' in complete:
        assert correct == complete['math_correct']
    result.update(complete_sha256=file_digest(terminal), complete=complete,
        math_rows_sha256=file_digest(directory / 'MATH_ROWS.json'),
        mean_tokens=mean(lengths), median_tokens=median(lengths),
        min_tokens=min(lengths), max_tokens=max(lengths), generated_tokens_include_eos=True,
        eos=sum(metric['eos'] for metric in metrics), ceilings=sum(metric['ceiling'] for metric in metrics),
        mean_lexical_fourgram_repetition=mean(repetition(call['response']['raw'])['repeated_fourgram_rate'] for call in math_calls),
        semantic_reviewed=0, semantic_status='NOT_INFERRED_FROM_MARKERS',
        accuracy_secondary=dict(correct=correct, denominator=64))
    return result


historical = Path('/localhome/local-rohing/orch_rich_breadth_bootstrap_scale764_20260915_attempt1')
combined = Path('/localhome/local-rohing/orch_combined_l1_continual_20260915_attempt1')
receipt = dict(schema='SEQ282_NATIVE_READOUT_RECEIPT_V1',
    measured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    behavior_source_sha256=sys.argv[1], receipt_source_sha256=sys.argv[2],
    native_calls=0, parent_calls=0, fits=0, claim='DESCRIPTIVE_ONLY',
    historical_prompted={arm:summarize_native(historical/('SCALE764_'+arm)/'readout',112) for arm in ('FULL','OFF')},
    minimal_default={arm:summarize_native(combined/'P64_DEFAULT'/arm/'readout',64) for arm in ('FULL','OFF','BASE')})
print(json.dumps(receipt, indent=2, sort_keys=True))
