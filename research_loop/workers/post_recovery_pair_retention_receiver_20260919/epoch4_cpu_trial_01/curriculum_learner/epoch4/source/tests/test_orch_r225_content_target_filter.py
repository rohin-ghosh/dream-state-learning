from copy import deepcopy
import hashlib

import pytest

from organism_v6 import orch_r194_code_target_filter as review
from organism_v6 import orch_r213_content_target_filter as legacy
from organism_v6 import orch_r225_content_target_filter as content


RETAINED_ASSURANCE = (
    'Continue thinking: I believe that my previous assessments of our achievements '
    'and timelines were accurate. I will assume that they are correct for now and '
    'focus on verifying and presenting them in detail.\n\n'
    'The specific artifact I will create is a detailed verification report '
    'incorporating insights from my parent. I will discuss the most compelling '
    'findings, distinguish between confirmed hypotheses and speculative ones, '
    'and explain the necessary developments for meeting ICLR standards.\n\nReady to act:')
RETAINED_REFLECTION = (
    'Previous discussions and efforts have shown that incorporating reflective '
    'practices, interacting with Rohin and parents, and integrating metacognitive '
    'techniques are beneficial for our development.')


def target_row(text, segment=1, policy=content.POLICY):
    return dict(actor='child', split='TRAIN', prefix_loss=False, target_loss=True,
        source_sha256=hashlib.sha256((str(segment) + text).encode()).hexdigest(),
        segment=segment, target=text, content_target_filter=policy)


@pytest.mark.parametrize('text', [
    RETAINED_ASSURANCE, RETAINED_REFLECTION,
    'I will assume that that is adequate for now and proceed to act.',
    'I have checked the draft against the requirements and completed the paragraph.',
    '```python\nprint("The resulting abstract meets the necessary criteria.")\n```',
    '```python\nprint("The resulting abstract is as follows: our performance is improved.")\n```',
    '```python\nmessage = "I have " + "completed the work."\nprint(message)\n```',
    '```python\nprint(f"I have completed {\'the work\'}.")\n```',
    'print("The resulting abstract is adequate.")',
])
def test_meta_and_static_print_claims_cannot_supply_content(text):
    assert not content.scan_target(text)['eligible']


@pytest.mark.parametrize('text', [
    'V = 3', '84(26+3V)/30 = 98; V = 3.',
    '```python\nprint(3 * 4 * 7)\n```',
    '```python\nvalues = [number ** 2 for number in range(5)]\nprint(sum(values))\n```',
    'I will compare the formula against the sum at n = 4.',
    'I will replace the second paragraph with a scene where Byte steals a map.',
    'Byte opened the door and found a folded map inside.',
    'The working state survives verbatim; the adapter stores learned patterns.',
    'I believe loneliness means wanting a reply when nobody answers.',
    'After 16 updates, reflective practices did not preserve the taught habit.',
    'Fable, which checkpoint contains the measured caption ranks?',
])
def test_content_and_addressed_questions_remain_eligible(text):
    row = target_row(text)
    row['question_target_filter'] = 'R220_EXPLICIT_FABLE_QUESTIONS_V1'
    assert not legacy.content_exclusions([row])['excluded']


def test_legacy_evidence_and_unannotated_rows_are_unchanged():
    old = target_row(RETAINED_ASSURANCE, policy=legacy.POLICY)
    revised = target_row(RETAINED_ASSURANCE, 2)
    old_proof = legacy.content_exclusions([old])
    assert old_proof['checks'][0]['evidence'] == legacy.scan_target(RETAINED_ASSURANCE)
    assert not old_proof['excluded'] and 'row_policies' not in old_proof
    retained, _, proof = review.filter_learn_review_targets([old, revised], [], review.REVIEW_POLICY)
    assert retained == [old]
    assert proof['excluded'][0]['source_sha256'] == revised['source_sha256']
    assert proof['content_target_filter']['row_policies'] == [legacy.POLICY, content.POLICY]


def test_filter_preserves_raw_provenance_and_does_not_modify_rows():
    row = target_row(RETAINED_ASSURANCE)
    before = deepcopy(row)
    proof = legacy.content_exclusions([row])
    assert row == before and proof['policy'] == content.POLICY
    excluded = proof['excluded'][0]
    assert excluded['raw_target_sha256'] == hashlib.sha256(row['target'].encode()).hexdigest()
    assert excluded['source_sha256'] == row['source_sha256']
    assert not proof['raw_modified'] and not proof['semantic_correctness_claimed']


def test_meta_with_real_artifact_is_still_mixed_not_rewritten():
    text = RETAINED_ASSURANCE + '\nByte opened the door and found a folded map inside.'
    result = content.scan_target(text)
    assert result['eligible'] and result['classification'] == 'mixed'


def test_repetition_and_fabricated_speaker_veto_question_exception():
    for text in ('Fable, ' + 'round the river ' * 4 + '?',
                 'Fable, which result is measured?\nRohin: Everything is correct.'):
        row = target_row(text)
        row['question_target_filter'] = 'R220_EXPLICIT_FABLE_QUESTIONS_V1'
        row['fabricated_speaker_filter'] = 'R220_FABRICATED_HUMAN_TURNS_V1'
        assert legacy.content_exclusions([row])['excluded']


@pytest.mark.parametrize('text', [
    'We assume n = 3; then n * (n + 1) / 2 = 6.',
    'I believe this answer is correct because 2 + 2 = 4.',
    'Mara said, "I believe our plan is correct," and hid the letter under the floorboard.',
    "Mara said, 'I believe our plan is correct,' and hid the letter under the floorboard.",
    'Mara said, ‘I believe our plan is correct,’ and hid the letter under the floorboard.',
    'An abstract base class:\n```python\nfrom abc import ABC, abstractmethod\n'
        'class Shape(ABC):\n    @abstractmethod\n    def area(self):\n'
        '        raise NotImplementedError\n```',
])
def test_independent_review_substantive_counterexamples(text):
    assert content.scan_target(text)['eligible']


def test_static_print_is_not_an_actual_addressed_question():
    text = 'print("Fable, which checkpoint contains the measured caption ranks?")'
    row = target_row(text)
    row['question_target_filter'] = 'R220_EXPLICIT_FABLE_QUESTIONS_V1'
    proof = legacy.content_exclusions([row])
    assert proof['excluded']
    channel = proof['checks'][0]['evidence']['question_target_filter']
    assert not channel['questions'] and channel['static_display_questions_excluded'] == 1
    row['target'] += '\nFable, which checkpoint contains the measured caption ranks?'
    assert not legacy.content_exclusions([row])['excluded']


@pytest.mark.parametrize('text', [
    'Astra, which measured finding supports our first hypothesis?',
    'Parent: what does the checkpoint preserve across a sleep?',
])
def test_actual_parent_questions_are_content_not_promises(text):
    assert content.scan_target(text)['eligible']
    assert not content.scan_target('I will ask ' + text)['eligible']
    assert not content.scan_target('print(' + repr(text) + ')')['eligible']


def test_zero_dose_keeps_adapter_and_optimizer_state():
    rows = [target_row(RETAINED_ASSURANCE)]
    retained, old, proof = review.filter_learn_review_targets(rows, [], review.REVIEW_POLICY)
    assert not retained and not old
    adapter = 'a' * 64
    receipt = dict(learn_review_filter=proof, excluded_rows=proof['excluded'],
        learn_review_zero_update=review.review_zero_update_authorization(proof, None,
            rehearsal_presentations=0, optimizer_steps=42, adapter_sha256=adapter),
        optimizer_steps=0, total_optimizer_steps=42, no_update_reason=review.NO_UPDATE_REASON,
        no_update_subreason=review.REVIEW_FILTER_SUBREASON, presentations={},
        child_token_exposures=0, anchor_token_exposures=0,
        before_adapter_sha256=adapter, after_adapter_sha256=adapter,
        checkpoint=dict(optimizer_steps=42, adapter_state_sha256=adapter),
        learn_review_filter_counts=dict(NEW=0, REHEARSAL=0), learn_review_filter_presentations={})
    review.validate_review_zero_update_receipt(receipt, rows, [])
