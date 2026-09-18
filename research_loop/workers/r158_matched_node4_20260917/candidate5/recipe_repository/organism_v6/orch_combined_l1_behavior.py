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
