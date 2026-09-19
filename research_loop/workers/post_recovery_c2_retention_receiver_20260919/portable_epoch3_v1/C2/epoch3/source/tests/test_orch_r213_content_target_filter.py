from copy import deepcopy
import hashlib

import pytest

from organism_v6 import orch_r194_code_target_filter as review
from organism_v6 import orch_r213_content_target_filter as content


def row(text, segment=1):
    return dict(actor='child', split='TRAIN', prefix_loss=False, target_loss=True,
        source_sha256=hashlib.sha256((str(segment) + text).encode()).hexdigest(),
        segment=segment, target=text, content_target_filter=content.POLICY)


@pytest.mark.parametrize('text', [
    'Continue thinking: I believe I have an adequate understanding.',
    'I have modified the narrative.',
    'I believe that restating the facts, explaining my decisions, and verifying that I have completed all requested tasks will demonstrate my understanding.',
    'I believe that incorporating self-regulation and metacognition will improve my work.',
    'Intention: I will ask Rohin to define "deep loneliness".',
    'Working State:\n- I have reviewed the provided overview and have identified the key points.\n- I have checked that I have completed all tasks as requested by Rohin.',
    'I will write a richer story and improve my understanding.',
    'Nothing changed.',
    'Ready to act.',
    'I have learned from 16 presentations of my own rows.',
    'I checked V = 3.',
    'PRESERVE: The narrative now includes an encounter between Byte and another learning agent, which introduces elements of cooperation and problem-solving.',
    'This approach is expected to result in a more realistic and engaging narrative.',
    'While I cannot verify this without further review, I proceed on the assumption that these changes improve the quality of the narrative.',
    'The correct formula and the equation at n=3 were derived and set up using SymPy.',
])
def test_meta_alone_is_not_eligible(text):
    result = content.scan_target(text)
    assert not result['eligible']
    assert result['classification'] == 'meta_only'


@pytest.mark.parametrize('text', [
    '84(26+3V)/30 = 98; V = 3.',
    'V = 3',
    '1+16+81+256 = 354',
    'Even the windmill knows this meeting\'s ridiculous.',
    'Byte opened the door and found a folded map inside.',
    'The working state survives verbatim; the adapter stores learned patterns.',
    'I prefer C2 because Byte is a character rather than my name.',
    'I believe loneliness means wanting a reply when nobody answers.',
    'I will replace the second paragraph with a scene where Byte steals a map.',
    'I will compare the formula against the sum at n = 4.',
    '```python\nprint(3 * 4 * 7)\n```',
    '```markdown\nModified:\n"Byte opened the door and found a folded map inside."\n```',
    '```text\nThe working state survives verbatim; the adapter stores learned patterns.\n```',
    'I have revised the story.\n\nByte opened the door and found a folded map inside.',
])
def test_concrete_content_is_preserved(text):
    assert content.scan_target(text)['eligible']


@pytest.mark.parametrize('text', ['', '...', '```python\npass\n```', '```python\n# a comment\n```',
    '```python\nprint(\n```', '```python\nforget_state:"previous_interaction"\n```'])
def test_uncertain_targets_are_separately_quarantined(text):
    result = content.scan_target(text)
    assert not result['eligible']
    assert result['classification'] == 'uncertain'


def test_bounded_scan_cannot_pass_an_uninspected_tail():
    result = content.scan_target('Byte opened the door. ' + 'x' * content.MAX_SCAN_CHARACTERS)
    assert result['scan_truncated'] and not result['eligible']


def test_markdown_fence_does_not_launder_meta():
    assert not content.scan_target('```markdown\nI have modified the narrative.\n```')['eligible']


@pytest.mark.parametrize('text', [
    'Byte found familiar ' + 'ter ' * 5 + 'terrain.',
    'Byte opened the door. ' + 'round the river ' * 4,
    'Byte found ' + 'Ter, ter TER ter ter.'
])
def test_repetition_collapse_excludes_content(text):
    result = content.scan_target(text)
    assert not result['eligible']
    assert result['classification'] == 'repetition_collapse'
    assert result['repetition_findings']


def test_repetition_thresholds_and_actual_model_tokens():
    assert not content.repetition_findings(['ter'] * 4, 'word')
    assert not content.repetition_findings(['round', 'the', 'river'] * 3, 'word')
    assert content.repetition_findings(['ter'] * 5, 'word')
    assert content.repetition_findings([1, 2, 3] * 4, 'model_token')
    target = row('Byte opened the door and found a folded map inside.')
    target['token_ids'] = [42] * 5
    proof = content.content_exclusions([target])
    assert proof['excluded'][0]['reason'] == 'repetition_collapse_target'


def test_labelled_story_in_python_print_is_not_a_story_artifact():
    text = 'Story:\n```python\nprint("Byte opened the door and found a folded map inside.")\n```'
    result = content.scan_target(text)
    assert not result['eligible'] and result['classification'] == 'code_wrapped_prose'
    assert content.scan_target('```python\nprint(3 * 4 * 7)\n```')['eligible']
    assert content.scan_target('```markdown\nStory:\nByte opened the door and found a folded map inside.\n```')['eligible']


def test_opt_in_original_bytes_and_provenance():
    rows = [row('I have completed every task.'), row('V = 3', 2)]
    before = deepcopy(rows)
    retained, old, proof = review.filter_learn_review_targets(rows, [], review.REVIEW_POLICY)
    assert rows == before
    assert retained == rows[1:] and old == []
    exclusion = proof['excluded'][0]
    assert exclusion['source_sha256'] == rows[0]['source_sha256']
    assert exclusion['raw_target_sha256'] == hashlib.sha256(rows[0]['target'].encode()).hexdigest()
    assert exclusion['reason'] == 'meta_only_target'
    assert proof['content_target_filter']['raw_modified'] is False
    del rows[0]['content_target_filter']
    assert review.filter_learn_review_targets(rows, [], review.REVIEW_POLICY)[0] == rows


def test_unsupported_policy_and_external_target_rejected():
    target = row('V = 3')
    target['content_target_filter'] = 'invented'
    with pytest.raises(ValueError, match='known_content'):
        content.content_exclusions([target])
    target['content_target_filter'] = content.POLICY
    target['actor'] = 'parent'
    with pytest.raises(ValueError, match='child_targets_only'):
        content.content_exclusions([target])


def test_zero_dose_proof_preserves_optimizer_and_adapter():
    rows = [row('I have completed every task.')]
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
    receipt['total_optimizer_steps'] += 1
    with pytest.raises(ValueError, match='unchanged_learning_state'):
        review.validate_review_zero_update_receipt(receipt, rows, [])
