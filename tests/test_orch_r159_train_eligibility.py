"""Synthetic TRAIN captures and judgments only; never real held data or training."""

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r158_train_gym as gym
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6 import orch_r159_train_eligibility as eligibility
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


TARGET = ('I combine two pairs by adding 2 + 2, obtaining 4. '
          'Checking 4 - 2 = 2 recovers a pair. '
          'For two nonoverlapping groups, addition counts their total.\nAnswer: 4')
FEEDBACK_TARGET = ('Earlier I counted only one pair. The failed check rules out 2. '
                   'I now combine both pairs: 2 + 2 = 4. Checking 4 - 2 = 2 recovers a pair. '
                   'For two nonoverlapping groups, addition counts their total.\nAnswer: 4')
BINDING = dict(package_version='0.1.25', package_source_sha256='a'*64, split_ledger_sha256='b'*64)
REFLECTION = ('The environment accepted my submitted total of four. That checks this answer, not every future claim. '
              'I can reuse adding group sizes when the groups are disjoint; overlapping groups need duplicate removal. '
              'For a future pair of groups I will check the membership overlap before adding, then reverse the addition. '
              'This is a proposed procedure, not a report that I already tested a new task.')


def quote(source, text, selected=None):
    selected = text if selected is None else selected
    start = text.index(selected)
    return dict(source=source, start=start, end=start+len(selected), quote=selected)


def encoded(document):
    return gym.encoded(document)+b'\n'


def make_case(tmp_path, monkeypatch, *, feedback=False, target=None, terminal=True, truncated=False,
              plain=False, render_feedback=True, earlier_capped=False, segments_per_sleep=2):
    clock = SimpleNamespace(now=100)
    monkeypatch.setattr(gym.time, 'time', lambda: clock.now)
    toy = SimpleNamespace(score_answer=lambda answer, entry: 1.0 if answer == '4' else 0.0)
    monkeypatch.setattr(gym, 'dataset', lambda index: (toy,
        dict(question='What is two plus two?', answer='SYNTHETIC_PRIVATE_REFERENCE_NOT_PUBLISHED'), deepcopy(BINDING)))
    root = tmp_path/'orch_r158_eligibility_fixture'/'parented_learning'
    root.mkdir(parents=True)
    journal = StreamJournal(root/'stream', create=True)
    stream = ContinualStream(TrainHistory(system_prompt='Observe and investigate.', birth_prompt='Synthetic TRAIN context.'),
        context_limit=4096, segment_tokens=128, segments_per_sleep=segments_per_sleep, deadline_unix=1000, model_state_sha256='f'*64)
    if plain:
        from organism_v6.orch_r125_plain_context import VERSION
        stream.set_presentation(dict(version=VERSION, system_prompt='Observe and investigate.',
                                     birth_prompt='Synthetic TRAIN context.'), 16384)
    trusted = {}

    def captured(path):
        artifact = eligibility.capture(str(path), Path(path).read_bytes())
        trusted[artifact['path']] = artifact['sha256']
        return artifact

    def attempt(raw, *, terminal=True, truncated=False):
        clock.now += 1
        stream.step(lambda messages, **kwargs: dict(raw=raw, token_ids=[10]*128 if truncated else [10, 11, 2],
            terminal=terminal, truncated=truncated), lambda messages: sum(len(message['content'].split())+4 for message in messages),
            journal.record, incoming=journal.read_inbox(), now=lambda: clock.now)
        paths = sorted((root/'stream/records').glob('[0-9]'*20+'.json'))
        response_path = next(path for path in reversed(paths) if json.loads(path.read_bytes())['kind'] == 'RESPONSE')
        response_index = json.loads(response_path.read_bytes())['index']
        artifacts = [captured(root/'stream/records'/f'{index:020d}.json')
                     for index in (response_index-1, response_index, response_index+1)]
        clock.now += 1
        checked = gym.check(root, 0, response_index)
        result_path = Path(checked['result_path'])
        publication = json.loads((result_path.parent/'PUBLICATION.json').read_bytes())
        return dict(records=artifacts, intent=captured(result_path.parent/'INTENT.json'), result=captured(result_path),
            publication=captured(result_path.parent/'PUBLICATION.json'), message=captured(publication['path']))

    try:
        journal.record('COMMITTED', dict(state=stream.checkpoint()))
        offered = gym.offer(root, 0)
        task_dir = gym.directory(root, 0)
        packet = dict(target_kind='ANSWER', label='feedback_use' if feedback else 'grounded_reasoning', task=captured(task_dir/'TASK.json'),
            task_publication=captured(task_dir/'PUBLICATION.json'), task_message=captured(offered['publication']['path']))
        if feedback:
            packet['feedback'] = attempt('I count one pair and stop.\nAnswer: 2\n',
                                        terminal=not earlier_capped, truncated=earlier_capped)
            if not render_feedback:
                Path(packet['feedback']['message']['path']).rename(tmp_path/'undelivered_feedback.json')
        selected = target if target is not None else FEEDBACK_TARGET if feedback else TARGET
        current = attempt(selected, terminal=terminal, truncated=truncated)
        packet.update({key: current[key] for key in ('records', 'intent', 'result')})
        row = deepcopy(stream.rows[-1])
    finally:
        journal.close()
    result = json.loads(packet['result']['raw'])
    request, response, committed = [json.loads(artifact['raw']) for artifact in packet['records']]
    binding = dict(target_kind='ANSWER', task_sha256=packet['task']['sha256'], target_sha256=eligibility.text_sha256(selected),
        prefix_sha256=eligibility.digest(row['prefix']), token_ids_sha256=eligibility.digest(row['token_ids']),
        result_sha256=packet['result']['sha256'], request_sha256=request['sha256'],
        response_sha256=response['sha256'], commit_sha256=committed['sha256'])
    if feedback:
        prior_raw = json.loads(packet['feedback']['records'][1]['raw'])['document']['response']['raw']
        feedback_text = json.loads(packet['feedback']['message']['raw'])['text']
        binding.update(earlier_target_sha256=eligibility.text_sha256(prior_raw),
            earlier_result_sha256=packet['feedback']['result']['sha256'],
            feedback_message_sha256=packet['feedback']['message']['sha256'])
    reviewers, reviews = {}, []
    for index in range(2):
        identity = 'reviewer_'+str(index)
        axes = {axis: dict(status='PASS', substantive=True,
            reason='Synthetic reviewer judgment over the full candidate and visible task; not a factual oracle.',
            evidence=[quote('target', selected)]) for axis in eligibility.AXES}
        if feedback:
            axes['feedback_use'] = dict(status='PASS', substantive=True,
                reason='The quoted old action counts one group; the new action counts both after rendered rejection.',
                changed_action_known=True, changed_action_or_expectation='Count both groups instead of stopping after one.',
                evidence=[quote('prior_target', prior_raw, 'I count one pair and stop.'),
                    quote('target', selected, 'I now combine both pairs: 2 + 2 = 4.'),
                    quote('feedback', feedback_text, 'Training puzzle check: not accepted')])
        review = dict(schema=eligibility.REVIEW_SCHEMA, reviewer_id=identity, principal_id='principal_'+str(index),
            session_id='independent_session_'+str(index), binding=deepcopy(binding), full_text_read=True,
            full_context_read=True, status='PASS', axes=axes,
            review_text='Full synthetic review: operations, check, applicable reuse and nonfabrication assessed separately.')
        artifact = eligibility.capture(str(tmp_path/(identity+'.json')), encoded(review))
        reviews.append(artifact)
        trusted[artifact['path']] = artifact['sha256']
        reviewers[identity] = dict(principal_id=review['principal_id'], session_id=review['session_id'],
            kind='model', source='synthetic test capture, not a real reviewer call', independence_attested=True,
            review_sha256=artifact['sha256'])
    packet['reviews'] = reviews
    monkeypatch.setattr(gym, 'dataset', Mock(side_effect=AssertionError('dataset execution forbidden')))
    monkeypatch.setattr(gym, 'grade', Mock(side_effect=AssertionError('verifier rerun forbidden')))
    monkeypatch.setattr(gym, 'offer', Mock(side_effect=AssertionError('collection forbidden')))
    monkeypatch.setattr(gym, 'check', Mock(side_effect=AssertionError('verifier execution forbidden')))
    return SimpleNamespace(packet=packet, trusted=trusted, reviewers=reviewers, row=row, result=result,
        root=root, clock=clock, result_publication=current['publication'], result_message=current['message'])


@pytest.fixture
def case(tmp_path, monkeypatch):
    return make_case(tmp_path, monkeypatch)


def compile_case(case, **kwargs):
    return eligibility.compile_candidate(case.packet, trusted_artifacts=case.trusted,
        reviewer_provenance=case.reviewers, generator_binding=BINDING, **kwargs)


def rewrite(case, artifact, change, *, trust=True, reviewer=False):
    document = json.loads(artifact['raw'])
    change(document)
    artifact.update(eligibility.capture(artifact['path'], encoded(document)))
    if trust:
        case.trusted[artifact['path']] = artifact['sha256']
    if reviewer:
        provenance = case.reviewers[document['reviewer_id']]
        provenance.update(review_sha256=artifact['sha256'], principal_id=document['principal_id'], session_id=document['session_id'])
    return document


def assert_excluded(result, reason=None):
    assert result['status'] in ('FAIL', 'UNRESOLVED')
    assert result['eligible'] is False and result['row'] is None
    if reason:
        assert any(reason in item['code'] for item in result['reasons']), result['reasons']


def test_accepted_receipts_and_two_full_reviews_preserve_exact_row_without_IO(case, monkeypatch):
    original = deepcopy(case.packet)
    monkeypatch.setattr(Path, 'read_bytes', Mock(side_effect=AssertionError('compiler file read forbidden')))
    monkeypatch.setattr(Path, 'write_bytes', Mock(side_effect=AssertionError('compiler write forbidden')))
    monkeypatch.setattr('subprocess.run', Mock(side_effect=AssertionError('remote forbidden')))
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['eligible'] is True and result['row'] == case.row
    assert result['row']['prefix_loss'] is False and result['row']['target_loss'] is True
    assert result['row']['append_eos'] is False and result['row']['token_ids'] == [10, 11, 2]
    assert result['row']['target'] == TARGET
    assert result['semantic_truth_proven'] is result['reviewer_independence_verified'] is False
    assert result['verifier_rerun'] is result['training_performed'] is result['scientific_claim'] is False
    assert all(value is False for value in result['quality_gates'].values())
    assert len(result['reviews']) == 2 and result['limitations']
    assert case.packet == original
    result['row']['prefix'].clear()
    assert case.row['prefix'] and case.packet == original


def test_actual_plain_context_render_is_preserved(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, plain=True)
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['row']['prefix'] == case.row['prefix']


@pytest.mark.parametrize('field', ['task', 'task_publication', 'task_message', 'records', 'intent', 'result', 'reviews'])
def test_missing_provenance_or_reviews_remains_unresolved(case, field):
    del case.packet[field]
    assert_excluded(compile_case(case))


@pytest.mark.parametrize('field', ['task', 'task_message', 'intent', 'result'])
def test_forged_bytes_and_self_rehashed_artifacts_do_not_replace_external_pins(case, field):
    artifact = case.packet[field]
    rewrite(case, artifact, lambda document: document.update(forged=True), trust=False)
    assert_excluded(compile_case(case), 'external_pin_mismatch')


def test_unanchored_capture_is_not_actual_provenance(case):
    del case.trusted[case.packet['result']['path']]
    result = compile_case(case)
    assert result['status'] == 'UNRESOLVED'
    assert_excluded(result, 'external_pin_missing')


@pytest.mark.parametrize('field,value', [('task_id', 'rg/countdown/1500003'), ('split', 'HELD'),
    ('answer', '5'), ('binding', dict(BINDING, package_source_sha256='0'*64)),
    ('accepted', True), ('origin', {}), ('generation_boundary', dict(terminal=False, truncated=True))])
def test_wrong_task_answer_generator_or_result_join_is_rejected(case, field, value):
    def change(document):
        document[field] = value
        if field == 'accepted':
            document['score'] = 0.0
    rewrite(case, case.packet['result'], change)
    assert_excluded(compile_case(case), 'verifier')


@pytest.mark.parametrize('score', [True, '1', -1, 2, None])
def test_invalid_verifier_scores_never_become_accepted(case, score):
    rewrite(case, case.packet['result'], lambda document: document.update(score=score))
    assert_excluded(compile_case(case), 'score_acceptance_consistency')


def test_actual_failed_result_is_retained_not_converted_to_success(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, target=TARGET.replace('Answer: 4', 'Answer: 3'))
    result = compile_case(case)
    assert_excluded(result, 'actual_verifier_not_accepted')
    assert result['outcome']['accepted'] is False and result['outcome']['score'] == 0
    assert len(result['reviews']) == 2


@pytest.mark.parametrize('terminal,truncated', [(False, False), (False, True)])
def test_capped_or_nonterminal_output_is_excluded_even_if_answer_was_accepted(tmp_path, monkeypatch, terminal, truncated):
    case = make_case(tmp_path, monkeypatch, target=TARGET+'\n', terminal=terminal, truncated=truncated)
    assert case.result['accepted'] is True
    assert_excluded(compile_case(case), 'complete_terminal_nontruncated')


@pytest.mark.parametrize('kind', ['target', 'tokens', 'prefix', 'nonTRAIN', 'parent', 'environment', 'mask'])
def test_rehashed_commit_cannot_rewrite_the_own_target_or_prefix(case, kind):
    def change(document):
        state = document['document']['state']
        row = state['state']['rows'][-1]
        if kind == 'target':
            row['target'] += ' Rewritten exemplar.'
        elif kind == 'tokens':
            row['token_ids'] = [123]
        elif kind == 'prefix':
            row['prefix'] = []
        elif kind == 'nonTRAIN':
            row['split'] = 'EVAL'
        elif kind == 'mask':
            row['prefix_loss'] = True
        else:
            row['actor'] = kind
        state['sha256'] = eligibility.digest(state['state'])
        document['sha256'] = eligibility.digest({key: value for key, value in document.items() if key != 'sha256'})
    rewrite(case, case.packet['records'][2], change)
    assert_excluded(compile_case(case), 'actual_own_training_row_join')


@pytest.mark.parametrize('axis', eligibility.AXES)
@pytest.mark.parametrize('missing', ['axis', 'evidence', 'reason', 'substantive'])
def test_each_semantic_axis_needs_substantive_attributed_quote_evidence(case, axis, missing):
    def change(document):
        if missing == 'axis':
            del document['axes'][axis]
        else:
            del document['axes'][axis][missing]
    rewrite(case, case.packet['reviews'][0], change, reviewer=True)
    result = compile_case(case)
    assert result['status'] == 'UNRESOLVED'
    assert_excluded(result, axis)


@pytest.mark.parametrize('field,value', [('quote', 'A fabricated observation'), ('start', True), ('start', -1),
    ('end', 100000), ('source', 'parent_claim')])
def test_exact_span_offsets_and_source_are_required(case, field, value):
    rewrite(case, case.packet['reviews'][0], lambda document: document['axes']['grounded_operations']['evidence'][0].update(
        {field: value}), reviewer=True)
    assert_excluded(compile_case(case), 'quote')


@pytest.mark.parametrize('field', ['target_sha256', 'prefix_sha256', 'token_ids_sha256', 'result_sha256',
    'task_sha256', 'request_sha256', 'response_sha256', 'commit_sha256'])
def test_reviews_bind_exact_target_prefix_result_and_triple(case, field):
    rewrite(case, case.packet['reviews'][0], lambda document: document['binding'].update({field: '0'*64}), reviewer=True)
    assert_excluded(compile_case(case), 'review_exact_target_prefix_result_binding')


@pytest.mark.parametrize('field', ['full_text_read', 'full_context_read', 'review_text'])
def test_answer_or_verifier_pass_cannot_substitute_for_full_reviews(case, field):
    rewrite(case, case.packet['reviews'][0], lambda document: document.pop(field), reviewer=True)
    assert_excluded(compile_case(case), 'full_text_and_context_review')


def test_answer_only_without_full_reviews_is_unresolved_not_auto_rich(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, target='Answer: 4')
    case.packet['reviews'] = []
    result = compile_case(case)
    assert result['outcome']['accepted'] is True and result['status'] == 'UNRESOLVED'
    assert_excluded(result, 'two_independent_full_context_reviews')


@pytest.mark.parametrize('duplicate', ['artifact', 'principal', 'session'])
def test_duplicate_or_aliased_reviewer_is_not_independent(case, duplicate):
    if duplicate == 'artifact':
        case.packet['reviews'][1] = deepcopy(case.packet['reviews'][0])
    else:
        field = 'principal_id' if duplicate == 'principal' else 'session_id'
        original = json.loads(case.packet['reviews'][0]['raw'])[field]
        rewrite(case, case.packet['reviews'][1], lambda document: document.update({field: original.upper()}), reviewer=True)
    assert_excluded(compile_case(case), 'distinct_attributed_independent_reviewers')


@pytest.mark.parametrize('change', ['missing', 'unattested', 'wrong_capture'])
def test_caller_supplied_reviewer_provenance_is_required(case, change):
    if change == 'missing':
        del case.reviewers['reviewer_0']
    elif change == 'unattested':
        case.reviewers['reviewer_0']['independence_attested'] = False
    else:
        case.reviewers['reviewer_0']['review_sha256'] = '0'*64
    assert_excluded(compile_case(case), 'reviewer')


@pytest.mark.parametrize('status', ['FAIL', 'UNRESOLVED'])
def test_disagreement_preserves_both_judgments_and_excludes(case, status):
    def change(document):
        document['status'] = status
        document['axes']['no_padding_or_fabrication']['status'] = status
        document['axes']['no_padding_or_fabrication']['reason'] = 'The check may be claimed rather than grounded.'
    rewrite(case, case.packet['reviews'][1], change, reviewer=True)
    result = compile_case(case)
    assert result['status'] == status
    assert [item['judgment']['status'] for item in result['reviews']] == ['PASS', status]
    assert {item['axis'] for item in result['disagreements']} == {'overall', 'no_padding_or_fabrication'}
    assert all(item['resolved'] is False for item in result['disagreements'])
    assert_excluded(result, 'no_padding_or_fabrication')


def test_feedback_use_requires_real_earlier_failure_render_and_changed_action(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, feedback=True)
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['eligible_label'] == 'feedback_use' and result['row'] == case.row
    assert result['binding']['earlier_result_sha256'] == case.packet['feedback']['result']['sha256']


@pytest.mark.parametrize('missing', ['feedback', 'result', 'publication', 'message', 'records'])
def test_unknown_or_missing_feedback_chain_excludes_without_downgrading_label(tmp_path, monkeypatch, missing):
    case = make_case(tmp_path, monkeypatch, feedback=True)
    if missing == 'feedback':
        del case.packet['feedback']
    else:
        del case.packet['feedback'][missing]
    result = compile_case(case)
    assert_excluded(result)
    assert result['requested_label'] == 'feedback_use' and 'eligible_label' not in result


@pytest.mark.parametrize('change', ['unknown_action', 'no_changed_action', 'no_prior_quote', 'no_feedback_quote'])
def test_feedback_label_needs_reviewed_evidenced_change_not_just_correctness(tmp_path, monkeypatch, change):
    case = make_case(tmp_path, monkeypatch, feedback=True)
    def revise(document):
        judgment = document['axes']['feedback_use']
        if change == 'unknown_action':
            judgment['changed_action_known'] = False
        elif change == 'no_changed_action':
            del judgment['changed_action_or_expectation']
        else:
            source = 'prior_target' if change == 'no_prior_quote' else 'feedback'
            judgment['evidence'] = [span for span in judgment['evidence'] if span['source'] != source]
    rewrite(case, case.packet['reviews'][0], revise, reviewer=True)
    result = compile_case(case)
    assert result['status'] == 'UNRESOLVED'
    assert_excluded(result, 'changed_action_evidence_unresolved')


def test_earlier_success_is_not_failed_feedback(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, feedback=True)
    rewrite(case, case.packet['feedback']['result'], lambda document: document.update(score=1.0, accepted=True))
    assert_excluded(compile_case(case), 'actual_earlier_failure_required')


def test_no_feedback_dependence_inferred_for_grounded_reasoning(case):
    result = compile_case(case)
    assert result['eligible_label'] == 'grounded_reasoning'
    assert 'earlier_result_sha256' not in result['binding']


def test_excluded_task_and_nonTRAIN_task_cannot_enter(case):
    assert_excluded(compile_case(case, excluded_task_ids=['rg/countdown/1500000']), 'excluded_or_contaminated_task')
    rewrite(case, case.packet['task'], lambda document: document.update(split='EVAL'))
    assert_excluded(compile_case(case), 'actual_TRAIN_task_only')


def test_evaluation_named_capture_rejected_without_reading_files(case):
    case.packet['task']['path'] = '/unopened/sealed/TASK.json'
    assert_excluded(compile_case(case), 'evaluation_input_forbidden')


def test_queued_feedback_is_not_rendered_exposure(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, feedback=True, render_feedback=False)
    assert case.result['accepted'] is True
    assert_excluded(compile_case(case), 'attributed_exposure_missing')


@pytest.mark.parametrize('value', [None, [], 'PASS'])
def test_malformed_review_axes_preserve_a_disposition_instead_of_crashing(case, value):
    rewrite(case, case.packet['reviews'][0], lambda document: document.update(axes=value), reviewer=True)
    assert_excluded(compile_case(case), 'separate_semantic_axis_judgments')


def test_review_axis_with_nonobject_judgment_is_unresolved(case):
    rewrite(case, case.packet['reviews'][0], lambda document: document['axes'].update(grounded_operations=[]), reviewer=True)
    assert_excluded(compile_case(case), 'judgment_missing')


@pytest.mark.parametrize('raw', [b'{"accepted":true,"accepted":false}', b'{"score":NaN}', b'{"score":Infinity}'])
def test_duplicate_or_nonfinite_receipt_JSON_is_rejected(case, raw):
    artifact = case.packet['result']
    artifact.update(eligibility.capture(artifact['path'], raw))
    case.trusted[artifact['path']] = artifact['sha256']
    assert_excluded(compile_case(case), 'JSON')


def test_prefix_task_substring_without_attributed_publication_is_not_exposure(case):
    rewrite(case, case.packet['task_message'], lambda document: document.update(actor='parent', speaker='Astra'))
    publication = case.packet['task_publication']
    rewrite(case, publication, lambda document: document.update(sha256=case.packet['task_message']['sha256']))
    assert_excluded(compile_case(case), 'actual_TRAIN_environment_source')


def test_generator_and_split_ledger_need_external_approval(case):
    result = eligibility.compile_candidate(case.packet, trusted_artifacts=case.trusted,
        reviewer_provenance=case.reviewers, generator_binding=dict(BINDING, split_ledger_sha256='c'*64))
    assert_excluded(result, 'approved_generator_version_and_TRAIN_split_ledger')


def test_unicode_spans_use_exact_codepoint_offsets_not_word_counts():
    compiler = eligibility.Compiler({}, {}, {}, ())
    text = '检查：2 + 2 = 4。'
    span = quote('target', text, '2 + 2 = 4')
    assert compiler.quote(span, {'target': text}) == 'target'
    span['start'] += 1
    with pytest.raises(eligibility.EvidenceError, match='quote_span_mismatch'):
        compiler.quote(span, {'target': text})


def test_earlier_capped_but_actually_checked_failure_is_evidence_not_an_admitted_target(tmp_path, monkeypatch):
    case = make_case(tmp_path, monkeypatch, feedback=True, earlier_capped=True)
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['row'] == case.row and result['row']['terminal'] is True and result['row']['truncated'] is False
    prior = json.loads(case.packet['feedback']['result']['raw'])
    assert prior['accepted'] is False and prior['generation_boundary']['truncated'] is True


@pytest.mark.parametrize('details', [{'error': 'verifier threw'}, {'status': 'FAIL'}, {'exception': 'synthetic failure'}])
def test_exception_receipt_cannot_be_mapped_to_success_and_details_survive(case, details):
    rewrite(case, case.packet['result'], lambda document: document.update(details))
    result = compile_case(case)
    assert_excluded(result, 'actual_verifier_receipt_fields')
    for key, value in details.items():
        assert result['supplied_verifier_receipts']['candidate.result'][key] == value


@pytest.mark.parametrize('target', [
    '2+2=4. Check: 4-2=2. Add sizes only for disjoint groups.\nAnswer: 4',
    'I add 2 and 2 to get 4; subtracting 2 checks this. This applies to disjoint pairs.\nAnswer: 4',
    '## Operation\n2+2=4.\n## Check\n4-2=2.\n## Scope\nTwo disjoint pairs.\nAnswer: 4',
    '两个不重叠的组各有两个，合计四个。用四减二得到二进行核对。此法适用于不重叠的组。\nAnswer: 4',
])
def test_register_language_headings_and_short_length_are_not_quality_proxies(tmp_path, monkeypatch, target):
    case = make_case(tmp_path, monkeypatch, target=target)
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['row']['target'] == target and result['row']['token_ids'] == [10, 11, 2]


def make_reflection_case(tmp_path, monkeypatch, *, terminal=True, truncated=False, render_feedback=True,
                         evict_task=False, failed_chain=False):
    case = make_case(tmp_path, monkeypatch, plain=True, feedback=failed_chain, segments_per_sleep=4)
    anchor = {key: deepcopy(case.packet[key]) for key in ('records', 'intent', 'result')}
    anchor.update(publication=case.result_publication, message=case.result_message)
    anchor_binding = json.loads(case.packet['reviews'][0]['raw'])['binding']
    anchor_target = case.row['target']
    checkpoint = json.loads(anchor['records'][2]['raw'])['document']['state']
    stream = ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
    if not render_feedback:
        Path(anchor['message']['path']).rename(tmp_path/'undelivered_accepted_feedback.json')
    if evict_task:
        stream.history.evict_oldest(stream.history.frontier(), reason='synthetic explicit old-context eviction')
    target = REFLECTION if not failed_chain else (
        'After the failed single-pair count, I now account for both disjoint groups before adding. '+REFLECTION)
    journal = StreamJournal(case.root/'stream')
    try:
        case.clock.now += 1
        stream.step(lambda messages, **kwargs: dict(raw=target, token_ids=[31]*128 if truncated else [31, 32, 2],
            terminal=terminal, truncated=truncated), lambda messages: sum(len(message['content'].split())+4 for message in messages),
            journal.record, incoming=journal.read_inbox(), now=lambda: case.clock.now)
        paths = sorted((case.root/'stream/records').glob('[0-9]'*20+'.json'))
        response = next(json.loads(path.read_bytes()) for path in reversed(paths)
                        if json.loads(path.read_bytes())['kind'] == 'RESPONSE')
        artifacts = []
        for index in (response['index']-1, response['index'], response['index']+1):
            path = case.root/'stream/records'/f'{index:020d}.json'
            artifact = eligibility.capture(str(path), path.read_bytes())
            artifacts.append(artifact)
            case.trusted[artifact['path']] = artifact['sha256']
        case.row = deepcopy(stream.rows[-1])
    finally:
        journal.close()
    case.packet.update(target_kind='POST_FEEDBACK_REFLECTION', anchor_attempt=anchor, records=artifacts)
    del case.packet['intent']
    del case.packet['result']
    records = [json.loads(artifact['raw']) for artifact in artifacts]
    binding = dict(target_kind='POST_FEEDBACK_REFLECTION', task_sha256=case.packet['task']['sha256'],
        target_sha256=eligibility.text_sha256(target), prefix_sha256=eligibility.digest(case.row['prefix']),
        token_ids_sha256=eligibility.digest(case.row['token_ids']), request_sha256=records[0]['sha256'],
        response_sha256=records[1]['sha256'], commit_sha256=records[2]['sha256'], result_sha256=anchor['result']['sha256'],
        anchor_target_sha256=anchor_binding['target_sha256'], anchor_prefix_sha256=anchor_binding['prefix_sha256'],
        anchor_request_sha256=anchor_binding['request_sha256'], anchor_response_sha256=anchor_binding['response_sha256'],
        anchor_commit_sha256=anchor_binding['commit_sha256'], anchor_result_sha256=anchor['result']['sha256'],
        anchor_feedback_message_sha256=anchor['message']['sha256'], anchor_feedback_publication_sha256=anchor['publication']['sha256'])
    if failed_chain:
        for field in ('earlier_target_sha256', 'earlier_result_sha256', 'feedback_message_sha256'):
            binding[field] = anchor_binding[field]
    feedback_text = json.loads(anchor['message']['raw'])['text']
    for artifact in case.packet['reviews']:
        def review(document):
            document['binding'] = binding
            document['review_text'] = ('Synthetic full reflection review, independently considering its retelling, '
                'proposed future procedure and applicability. Anchor acceptance is not reflection truth.')
            for axis in eligibility.AXES:
                document['axes'][axis]['evidence'] = [quote('target', target)]
            document['axes']['faithful_corrected_retelling'] = dict(status='PASS', substantive=True,
                reason='Retells the accepted calculation and observed feedback without claiming an unobserved future test.',
                evidence=[quote('target', target), quote('anchor_target', anchor_target),
                    quote('anchor_result', anchor['result']['raw'].decode()), quote('anchor_feedback', feedback_text)])
            document['axes']['reuse_applicability'] = dict(status='PASS', substantive=True,
                reason='Use only for disjoint groups; check overlap first and reverse the addition as a proposed future check.',
                evidence=[quote('target', target, 'overlapping groups need duplicate removal.')])
            if failed_chain:
                failed = case.packet['feedback']
                before = json.loads(failed['records'][1]['raw'])['document']['response']['raw']
                feedback = json.loads(failed['message']['raw'])['text']
                document['axes']['feedback_use'].update(
                    evidence=[quote('prior_target', before), quote('feedback', feedback),
                        quote('target', target, 'I now account for both disjoint groups before adding.')],
                    changed_action_or_expectation='The proposed future procedure checks both groups, rather than stopping after one.')
        rewrite(case, artifact, review, reviewer=True)
    return case


def test_post_feedback_reflection_is_not_answer_imitation_or_automatically_verified(tmp_path, monkeypatch):
    case = make_reflection_case(tmp_path, monkeypatch)
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['target_kind'] == 'POST_FEEDBACK_REFLECTION' and result['row'] == case.row
    assert result['row']['target'] == REFLECTION and result['row']['token_ids'] == [31, 32, 2]
    assert result['row']['prefix_loss'] is False and result['row']['target_loss'] is True
    assert result['anchor_outcome']['accepted'] is True and 'outcome' not in result
    assert result['outcome_scope'] == 'ACCEPTED_ANCHOR_ONLY_NOT_REFLECTION_TRUTH'
    assert result['semantic_truth_proven'] is result['reflection_truth_verified'] is result['consolidation_performed'] is False
    assert gym.parse_answer(REFLECTION, terminal=True, truncated=False) is None
    assert 'candidate.result' not in result['supplied_verifier_receipts']
    assert result['binding']['anchor_result_sha256'] == case.packet['anchor_attempt']['result']['sha256']
    gym.check.assert_not_called()
    gym.grade.assert_not_called()


def test_reflection_can_use_rendered_feedback_after_task_is_explicitly_evicted(tmp_path, monkeypatch):
    case = make_reflection_case(tmp_path, monkeypatch, evict_task=True)
    task_text = json.loads(case.packet['task']['raw'])['text']
    assert not any(task_text in message['content'] for message in case.row['prefix'])
    assert any('Training puzzle check: accepted' in message['content'] for message in case.row['prefix'])
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['row']['prefix'] == case.row['prefix']


@pytest.mark.parametrize('field', ['anchor_attempt', 'result', 'intent', 'records', 'publication', 'message'])
def test_reflection_requires_complete_actual_accepted_anchor_and_publication(tmp_path, monkeypatch, field):
    case = make_reflection_case(tmp_path, monkeypatch)
    if field == 'anchor_attempt':
        del case.packet[field]
    else:
        del case.packet['anchor_attempt'][field]
    assert_excluded(compile_case(case))


def test_reflection_queued_accepted_feedback_does_not_count_as_rendered(tmp_path, monkeypatch):
    case = make_reflection_case(tmp_path, monkeypatch, render_feedback=False)
    assert_excluded(compile_case(case), 'task_actually_rendered')


@pytest.mark.parametrize('field,value', [('accepted', False), ('task_id', 'rg/countdown/1500003'),
    ('answer', '3'), ('origin', {}), ('split', 'EVAL')])
def test_reflection_wrong_or_unaccepted_anchor_cannot_support_eligibility(tmp_path, monkeypatch, field, value):
    case = make_reflection_case(tmp_path, monkeypatch)
    def change(document):
        document[field] = value
        if field == 'accepted':
            document['score'] = 0.0
    rewrite(case, case.packet['anchor_attempt']['result'], change)
    assert_excluded(compile_case(case))


@pytest.mark.parametrize('axis', eligibility.REFLECTION_AXES)
@pytest.mark.parametrize('missing', ['axis', 'evidence', 'reason', 'substantive'])
def test_reflection_needs_separate_full_retelling_and_applicability_judgments(tmp_path, monkeypatch, axis, missing):
    case = make_reflection_case(tmp_path, monkeypatch)
    def change(document):
        if missing == 'axis':
            del document['axes'][axis]
        else:
            del document['axes'][axis][missing]
    rewrite(case, case.packet['reviews'][0], change, reviewer=True)
    assert_excluded(compile_case(case), axis)


@pytest.mark.parametrize('source', ['anchor_target', 'anchor_result', 'anchor_feedback', 'target'])
def test_faithful_retelling_quotes_both_experience_and_actual_reflection(tmp_path, monkeypatch, source):
    case = make_reflection_case(tmp_path, monkeypatch)
    def change(document):
        judgment = document['axes']['faithful_corrected_retelling']
        judgment['evidence'] = [span for span in judgment['evidence'] if span['source'] != source]
    rewrite(case, case.packet['reviews'][0], change, reviewer=True)
    assert_excluded(compile_case(case), 'quote')


@pytest.mark.parametrize('field', ['target_sha256', 'prefix_sha256', 'anchor_target_sha256', 'anchor_prefix_sha256',
    'anchor_result_sha256', 'anchor_response_sha256', 'anchor_commit_sha256', 'anchor_feedback_message_sha256', 'target_kind'])
def test_reflection_reviews_are_bound_to_both_anchor_and_new_target(tmp_path, monkeypatch, field):
    case = make_reflection_case(tmp_path, monkeypatch)
    rewrite(case, case.packet['reviews'][0], lambda document: document['binding'].update({field: '0'*64}), reviewer=True)
    assert_excluded(compile_case(case), 'review_exact_target_prefix_result_binding')


@pytest.mark.parametrize('terminal,truncated', [(False, False), (False, True)])
def test_reflection_must_be_own_complete_terminal_output(tmp_path, monkeypatch, terminal, truncated):
    case = make_reflection_case(tmp_path, monkeypatch, terminal=terminal, truncated=truncated)
    assert_excluded(compile_case(case), 'complete_terminal_nontruncated')


@pytest.mark.parametrize('status', ['FAIL', 'UNRESOLVED'])
def test_prior_acceptance_never_overrides_reflection_review_failure_or_disagreement(tmp_path, monkeypatch, status):
    case = make_reflection_case(tmp_path, monkeypatch)
    def change(document):
        document['axes']['faithful_corrected_retelling'].update(status=status,
            reason='The reflection overstates what the verifier established; proposed reuse was not actually tested.')
    rewrite(case, case.packet['reviews'][1], change, reviewer=True)
    result = compile_case(case)
    assert result['anchor_outcome']['accepted'] is True and result['status'] == status
    assert_excluded(result, 'faithful_corrected_retelling')
    assert any(item['axis'] == 'faithful_corrected_retelling' for item in result['disagreements'])


def test_reflection_cannot_relabel_anchor_response_or_its_result_as_a_new_target(tmp_path, monkeypatch):
    case = make_reflection_case(tmp_path, monkeypatch)
    case.packet['records'] = deepcopy(case.packet['anchor_attempt']['records'])
    assert_excluded(compile_case(case))


def test_reflection_does_not_accept_an_unbound_candidate_verifier_receipt(tmp_path, monkeypatch):
    case = make_reflection_case(tmp_path, monkeypatch)
    case.packet['result'] = case.packet['anchor_attempt']['result']
    assert_excluded(compile_case(case), 'anchor_result_is_not_a_candidate_verifier_result')


def test_reflection_supports_stricter_failed_feedback_use_only_with_its_own_chain(tmp_path, monkeypatch):
    case = make_reflection_case(tmp_path, monkeypatch, failed_chain=True)
    result = compile_case(case)
    assert result['status'] == 'PASS', result['reasons']
    assert result['eligible_label'] == 'feedback_use' and result['target_kind'] == 'POST_FEEDBACK_REFLECTION'
    del case.packet['feedback']
    assert_excluded(compile_case(case), 'earlier_chain_missing')


@pytest.mark.parametrize('kind', [None, 'REFLECTION', 'ENVIRONMENT', 'EVAL'])
def test_target_kind_is_explicit_not_inferred_from_voice_or_answer_words(case, kind):
    case.packet['target_kind'] = kind
    assert_excluded(compile_case(case), 'explicit_supported_target_kind_required')
