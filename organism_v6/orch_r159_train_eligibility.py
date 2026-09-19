"""Pure CPU eligibility checks over caller-captured TRAIN evidence, not a trainer."""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import PurePosixPath
import re

from gpu import orch_r158_train_gym as gym
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


SCHEMA = 'R159_TRAIN_ELIGIBILITY_V1'
REVIEW_SCHEMA = 'R159_FULL_CONTEXT_REVIEW_V1'
AXES = ('grounded_operations', 'checkable_expectation_or_check',
        'reusable_content_with_scope', 'no_padding_or_fabrication')
REFLECTION_AXES = ('faithful_corrected_retelling', 'reuse_applicability')
STATUSES = ('PASS', 'FAIL', 'UNRESOLVED')
LABELS = ('grounded_reasoning', 'feedback_use')
TARGET_KINDS = ('ANSWER', 'POST_FEEDBACK_REFLECTION')
LIMITATIONS = (
    'Artifact trust roots and reviewer provenance are supplied by the caller, not authenticated here.',
    'Distinct attributed reviews and exact quotations do not prove semantic truth or actual reviewer independence.',
    'No verifier rerun, tokenizer validation, special-token audit, context-fit audit, training, or evaluation is performed.',
    'Fit-time contamination, tokenization, masking, context and presentation accounting remain required.',
    'Eligibility is conditional on supplied judgments; no retained-learning, parenting-dependence or reusable-use claim.',
    'An accepted anchor verifies its submitted answer, not the later reflection or an experience-to-consolidation outcome.',
)


class EvidenceError(ValueError):
    def __init__(self, code, status='FAIL'):
        super().__init__(code)
        self.code, self.status = code, status


def require(condition, code, status='FAIL'):
    if not condition:
        raise EvidenceError(code, status)


def digest(value):
    return gym._digest(value)


def text_sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def capture(path, raw):
    """Wrap already captured bytes without opening a path or establishing trust."""
    require(type(raw) is bytes, 'capture_requires_original_bytes')
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), raw=raw)


def finite_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def nonempty(value):
    return type(value) is str and bool(value.strip())


def hex_sha256(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def unique_object(pairs):
    document = {}
    for key, value in pairs:
        require(key not in document, 'duplicate_JSON_key')
        document[key] = value
    return document


class Compiler:
    def __init__(self, trusted_artifacts, reviewer_provenance, generator_binding, excluded_task_ids):
        self.trusted = trusted_artifacts
        self.reviewers = reviewer_provenance
        self.generator = generator_binding
        self.excluded = set(excluded_task_ids)
        self.manifest = {}
        self.verifier_receipts = {}

    def read(self, artifact, label):
        require(artifact is not None, label+':missing_evidence', 'UNRESOLVED')
        require(type(artifact) is dict and set(artifact) == {'path', 'sha256', 'raw'}, label+':capture_schema')
        path = artifact['path']
        require(type(path) is str and PurePosixPath(path).is_absolute()
            and str(PurePosixPath(path)) == path and '..' not in PurePosixPath(path).parts, label+':canonical_capture_path')
        require(not any(re.search(r'(^|[_ .-])(held|final|readout|sealed|eval)([_ .-]|$)', part, re.IGNORECASE)
                        for part in PurePosixPath(path).parts), label+':evaluation_input_forbidden')
        require(type(artifact['raw']) is bytes and hex_sha256(artifact['sha256'])
            and hashlib.sha256(artifact['raw']).hexdigest() == artifact['sha256'], label+':capture_hash')
        require(path in self.trusted, label+':external_pin_missing', 'UNRESOLVED')
        require(self.trusted[path] == artifact['sha256'], label+':external_pin_mismatch')
        self.manifest[label] = dict(path=path, sha256=artifact['sha256'])

        def invalid_constant(value):
            raise EvidenceError(label+':nonfinite_JSON')

        document = json.loads(artifact['raw'], object_pairs_hook=unique_object, parse_constant=invalid_constant)
        require(type(document) is dict, label+':document_required')
        if label.endswith('.result'):
            self.verifier_receipts[label] = deepcopy(document)
        return document

    def exposure(self, request, publication_artifact, message_artifact, source_artifact, text, label):
        publication = self.read(publication_artifact, label+'.publication')
        message = self.read(message_artifact, label+'.message')
        require(publication == dict(id=message['id'], path=message_artifact['path'], sha256=message_artifact['sha256']),
                label+':published_message_binding')
        require(set(message) == {'schema', 'id', 'text', 'split', 'actor', 'speaker', 'source_receipt'}
            and message['schema'] == 'R127_ATTRIBUTED_INBOX_V1' and message['actor'] == 'environment'
            and message['speaker'] == 'Tool' and message['split'] == 'TRAIN' and message['text'] == text
            and message['source_receipt'] == dict(path=source_artifact['path'], sha256=source_artifact['sha256']),
            label+':actual_TRAIN_environment_source')
        root = PurePosixPath(request['path']).parents[2]
        require(PurePosixPath(message_artifact['path']) == root/'stream/inbox'/(message['id']+'.json')
            and PurePosixPath(publication_artifact['path']) == PurePosixPath(source_artifact['path']).parent/'PUBLICATION.json',
            label+':publication_paths')
        document = request['document']['document']
        state = document['resume_state']['state']
        history = state['history']
        expected = dict(event_id='environment:inbox:'+message['id'], actor='environment', split='TRAIN',
            text='Tool: '+text, phase='feedback', episode_id='continual_stream', source_id=message_artifact['path'],
            source_sha256=message_artifact['sha256'], origin='TRAIN_COLLECTION')
        require(expected in history['events'], label+':attributed_exposure_missing', 'UNRESOLVED')
        event = TrainEvent.restore(expected)
        rendered = event_message(event) if state.get('presentation') is not None else TrainHistory._message(event)
        require(rendered is not None and rendered in document['messages'], label+':not_actually_rendered', 'UNRESOLVED')
        return message

    def trajectory(self, evidence, task, task_artifact, label, *, require_complete=True, rendered_text=None):
        artifacts = evidence.get('records')
        require(type(artifacts) is list and len(artifacts) == 3, label+':complete_triple_missing', 'UNRESOLVED')
        records = [self.read(artifact, label+'.record'+str(index)) for index, artifact in enumerate(artifacts)]
        root = PurePosixPath(task_artifact['path']).parents[2]
        for artifact, record in zip(artifacts, records):
            require(type(record['index']) is int and record['index'] >= 0 and nonempty(record['journal_id']),
                    label+':record_identity')
            require(PurePosixPath(artifact['path']) == root/'stream/records'/f"{record['index']:020d}.json",
                    label+':same_life_record_path')
        generation = gym.verify_triple(records, task['text'] if rendered_text is None else rendered_text)
        request = records[0]['document']
        resume = request['resume_state']
        require(resume['sha256'] == digest(resume['state'])
            and request['history_sha256'] == digest(resume['state']['history']), label+':request_history_binding')
        history = TrainHistory.restore(resume['state']['history'])
        rendered = history.render(lambda messages: 0, 0, presentation=resume['state'].get('presentation'))
        require(rendered.messages == request['messages'], label+':exact_original_rendered_prefix')
        require(request['render_receipt']['all_history_tokens_masked'] is True, label+':original_prefix_not_masked')
        state = records[2]['document']['state']['state']
        row = state['rows'][-1]
        require(state['rows'][:-1] == resume['state']['rows'] and state['pending'] is None
            and row['segment'] == request['segment'] == len(resume['state']['rows']), label+':own_committed_frontier')
        require(type(generation['terminal']) is bool and type(generation['truncated']) is bool
            and not (generation['terminal'] and generation['truncated'])
            and row['terminal'] is generation['terminal'] and row['truncated'] is generation['truncated']
            and row['append_eos'] is False, label+':exact_generation_boundary')
        if require_complete:
            require(generation['terminal'] is True and generation['truncated'] is False,
                    label+':complete_terminal_nontruncated_own_row_required')
        require(type(generation['token_ids']) is list and generation['token_ids']
            and all(type(token) is int and token >= 0 for token in generation['token_ids'])
            and type(request['max_new_tokens']) is int and len(generation['token_ids']) <= request['max_new_tokens'],
            label+':original_token_IDs')
        times = (task['created_unix'], request['started_unix'], records[1]['document']['finished_unix'])
        require(all(finite_number(value) and value >= 0 for value in times)
            and list(times) == sorted(times), label+':actual_trajectory_time_order')
        return dict(records=records, generation=generation, request=dict(path=artifacts[0]['path'], document=records[0]),
            row=row, binding=dict(task_sha256=task_artifact['sha256'], target_sha256=text_sha256(row['target']),
                prefix_sha256=digest(row['prefix']), token_ids_sha256=digest(row['token_ids']),
                request_sha256=records[0]['sha256'], response_sha256=records[1]['sha256'], commit_sha256=records[2]['sha256']))

    def attempt(self, evidence, task, task_artifact, label, *, require_complete=True):
        context = self.trajectory(evidence, task, task_artifact, label, require_complete=require_complete)
        records, generation = context['records'], context['generation']
        answer = gym.parse_answer(generation['raw'], terminal=generation['terminal'], truncated=generation['truncated'])
        require(answer is not None, label+':latest_complete_answer_missing', 'UNRESOLVED')
        intent_artifact, result_artifact = evidence.get('intent'), evidence.get('result')
        intent = self.read(intent_artifact, label+'.intent')
        result = self.read(result_artifact, label+'.result')
        require(set(result) == {'schema', 'task_id', 'split', 'answer', 'origin', 'generation_boundary',
            'binding', 'score', 'accepted', 'finished_unix', 'answer_key_published'}, label+':actual_verifier_receipt_fields')
        directory = PurePosixPath(task_artifact['path']).parent/f"answer_{records[1]['index']:020d}"
        require(PurePosixPath(intent_artifact['path']) == directory/'INTENT.json'
            and PurePosixPath(result_artifact['path']) == directory/'RESULT.json', label+':actual_verifier_attempt_paths')
        require(intent == dict(response_index=records[1]['index'], response_sha256=records[1]['sha256'],
            generated_sha256=text_sha256(generation['raw']), answer=answer, task_sha256=task_artifact['sha256'],
            replay_allowed=False), label+':verifier_intent_join')
        require(result['schema'] == 'R158_TRAIN_GYM_RESULT_V1' and result['task_id'] == task['task_id']
            and result['split'] == 'TRAIN' and result['answer'] == answer and result['binding'] == task['binding']
            and result['answer_key_published'] is False
            and result['origin'] == dict(response_index=records[1]['index'], response_sha256=records[1]['sha256'],
                                         commit_sha256=records[2]['sha256'])
            and result['generation_boundary'] == dict(terminal=generation['terminal'], truncated=generation['truncated']),
            label+':actual_matching_verifier_result')
        require(finite_number(result['score']) and 0 <= result['score'] <= 1 and type(result['accepted']) is bool
            and result['accepted'] is (result['score'] == 1.0), label+':verifier_score_acceptance_consistency')
        times = (records[1]['document']['finished_unix'], result['finished_unix'])
        require(all(finite_number(value) and value >= 0 for value in times)
            and list(times) == sorted(times), label+':actual_attempt_time_order')
        context.update(result=result, result_artifact=result_artifact, answer=answer)
        context['binding']['result_sha256'] = result_artifact['sha256']
        return context

    def reflection(self, packet, task, task_artifact):
        evidence = packet.get('anchor_attempt')
        require(type(evidence) is dict, 'reflection:accepted_anchor_missing', 'UNRESOLVED')
        require(packet.get('intent') is None and packet.get('result') is None,
                'reflection:anchor_result_is_not_a_candidate_verifier_result')
        anchor = self.attempt(evidence, task, task_artifact, 'anchor_attempt', require_complete=False)
        require(anchor['result']['accepted'] is True, 'reflection:actual_accepted_anchor_required')
        self.exposure(anchor['request'], packet.get('task_publication'), packet.get('task_message'),
                      task_artifact, task['text'], 'anchor_task_exposure')
        feedback_text = ('Training puzzle check: accepted'
            + f"; verifier score {anchor['result']['score']:.3f}. This is a real check of your submitted answer."
            + ' The reference answer is not shown.')
        context = self.trajectory(packet, task, task_artifact, 'reflection', rendered_text=feedback_text)
        require(anchor['records'][2]['journal_id'] == context['records'][0]['journal_id']
            and anchor['records'][2]['index'] < context['records'][0]['index']
            and anchor['result']['finished_unix'] <= context['records'][0]['document']['started_unix'],
            'reflection:subsequent_same_life_response_required')
        require(anchor['row'] in context['records'][0]['document']['resume_state']['state']['rows'],
                'reflection:accepted_anchor_not_in_own_lineage')
        self.exposure(context['request'], evidence.get('publication'), evidence.get('message'),
                      anchor['result_artifact'], feedback_text, 'accepted_feedback_exposure')
        context.update(anchor=anchor, anchor_feedback_text=feedback_text,
            result=anchor['result'], result_artifact=anchor['result_artifact'])
        context['binding'].update(result_sha256=anchor['result_artifact']['sha256'],
            anchor_target_sha256=anchor['binding']['target_sha256'], anchor_prefix_sha256=anchor['binding']['prefix_sha256'],
            anchor_request_sha256=anchor['binding']['request_sha256'], anchor_response_sha256=anchor['binding']['response_sha256'],
            anchor_commit_sha256=anchor['binding']['commit_sha256'], anchor_result_sha256=anchor['result_artifact']['sha256'],
            anchor_feedback_message_sha256=evidence['message']['sha256'],
            anchor_feedback_publication_sha256=evidence['publication']['sha256'])
        return context

    def context(self, packet):
        task_artifact = packet.get('task')
        task = self.read(task_artifact, 'task')
        require(set(task) == {'schema', 'task_id', 'task_index', 'split', 'text', 'binding', 'created_unix', 'answer_key_published'}
            and task['schema'] == 'R158_TRAIN_GYM_TASK_V1' and task['split'] == 'TRAIN'
            and task['task_id'] == gym.task_id(task['task_index']) and task['answer_key_published'] is False,
            'actual_TRAIN_task_only')
        require(task['task_id'] not in self.excluded, 'excluded_or_contaminated_task')
        require(nonempty(task['text']), 'task_text_required')
        binding = task['binding']
        require(type(binding) is dict and set(binding) == {'package_version', 'package_source_sha256', 'split_ledger_sha256'}
            and binding['package_version'] == gym.PACKAGE_VERSION
            and hex_sha256(binding['package_source_sha256']) and hex_sha256(binding['split_ledger_sha256'])
            and binding == self.generator, 'approved_generator_version_and_TRAIN_split_ledger')
        task_path = PurePosixPath(task_artifact['path'])
        root = task_path.parents[2]
        require(task_path == root/'train_environment'/f"task_{task['task_index']:06d}"/'TASK.json'
            and root.name in ('parented_learning', 'parented_frozen', 'unparented_learning')
            and root.parent.name.startswith('orch_r158_'), 'actual_R158_task_path')
        if packet['target_kind'] == 'POST_FEEDBACK_REFLECTION':
            context = self.reflection(packet, task, task_artifact)
        else:
            context = self.attempt(packet, task, task_artifact, 'candidate')
            self.exposure(context['request'], packet.get('task_publication'), packet.get('task_message'),
                          task_artifact, task['text'], 'task_exposure')
        context['binding']['target_kind'] = packet['target_kind']
        context.update(task=task, task_artifact=task_artifact, task_publication=packet.get('task_publication'),
                       task_message=packet.get('task_message'))
        return context

    def feedback(self, evidence, context):
        require(type(evidence) is dict, 'feedback_use:earlier_chain_missing', 'UNRESOLVED')
        prior = self.attempt(evidence, context['task'], context['task_artifact'], 'earlier_attempt', require_complete=False)
        self.exposure(prior['request'], context['task_publication'], context['task_message'],
                      context['task_artifact'], context['task']['text'], 'earlier_task_exposure')
        require(prior['result']['accepted'] is False and prior['result']['score'] < 1,
                'feedback_use:actual_earlier_failure_required')
        require(prior['records'][2]['journal_id'] == context['records'][0]['journal_id']
            and prior['records'][2]['index'] < context['records'][0]['index']
            and prior['result']['finished_unix'] <= context['records'][0]['document']['started_unix'],
            'feedback_use:earlier_same_life_attempt_required')
        require(prior['row'] in context['records'][0]['document']['resume_state']['state']['rows'],
                'feedback_use:earlier_own_row_not_in_lineage')
        text = ('Training puzzle check: not accepted'
            + f"; verifier score {prior['result']['score']:.3f}. This is a real check of your submitted answer."
            + ' The reference answer is not shown.')
        self.exposure(context['request'], evidence.get('publication'), evidence.get('message'),
                      prior['result_artifact'], text, 'feedback_exposure')
        require(prior['row']['target'] != context['row']['target'], 'feedback_use:unchanged_target')
        return prior, text

    def quote(self, span, sources):
        require(type(span) is dict and set(span) == {'source', 'start', 'end', 'quote'}, 'exact_quote_span_required', 'UNRESOLVED')
        require(span['source'] in sources, 'quote_source_unavailable', 'UNRESOLVED')
        text = sources[span['source']]
        require(type(span['start']) is int and type(span['end']) is int and 0 <= span['start'] < span['end'] <= len(text)
            and nonempty(span['quote']) and text[span['start']:span['end']] == span['quote'], 'quote_span_mismatch')
        return span['source']

    def review(self, artifact, context, prior, feedback_text, label, index):
        review = self.read(artifact, 'review'+str(index))
        require(review['schema'] == REVIEW_SCHEMA, 'full_context_review_schema')
        identity = review['reviewer_id']
        require(identity in self.reviewers, 'attributed_reviewer_provenance_missing', 'UNRESOLVED')
        provenance = self.reviewers[identity]
        require(provenance['review_sha256'] == artifact['sha256']
            and nonempty(provenance['principal_id']) and nonempty(provenance['session_id'])
            and review['principal_id'] == provenance['principal_id'] and review['session_id'] == provenance['session_id']
            and provenance['kind'] in ('human', 'model') and nonempty(provenance['source']), 'reviewer_provenance_binding')
        require(provenance.get('independence_attested') is True, 'reviewer_independence_unresolved', 'UNRESOLVED')
        require(review['binding'] == context['binding'], 'review_exact_target_prefix_result_binding')
        require(review.get('full_text_read') is True and review.get('full_context_read') is True
            and nonempty(review.get('review_text')), 'attributed_full_text_and_context_review_required', 'UNRESOLVED')
        require(review.get('status') in STATUSES, 'review_status_required', 'UNRESOLVED')
        require(type(review.get('axes')) is dict, 'separate_semantic_axis_judgments_required', 'UNRESOLVED')
        axes = (*AXES, 'feedback_use') if label == 'feedback_use' else AXES
        if context['binding']['target_kind'] == 'POST_FEEDBACK_REFLECTION':
            axes = (*axes, *REFLECTION_AXES)
        sources = dict(target=context['row']['target'], prefix=json.dumps(context['row']['prefix'],
            sort_keys=True, separators=(',', ':'), allow_nan=False), task=context['task']['text'],
            result=context['result_artifact']['raw'].decode('utf-8'))
        if prior is not None:
            sources.update(prior_target=prior['row']['target'], feedback=feedback_text)
        if 'anchor' in context:
            sources.update(anchor_target=context['anchor']['row']['target'],
                anchor_result=context['anchor']['result_artifact']['raw'].decode('utf-8'),
                anchor_feedback=context['anchor_feedback_text'])
        reasons = []
        if review['status'] != 'PASS':
            reasons.append(dict(status=review['status'], code='reviewer_overall_'+review['status']))
        for axis in axes:
            judgment = review.get('axes', {}).get(axis)
            try:
                require(type(judgment) is dict, axis+':judgment_missing', 'UNRESOLVED')
                require(judgment.get('status') in STATUSES, axis+':status_missing', 'UNRESOLVED')
                if judgment['status'] != 'PASS':
                    reasons.append(dict(status=judgment['status'], code=axis+':'+judgment['status']))
                require(judgment.get('substantive') is True and nonempty(judgment.get('reason')),
                        axis+':substantive_judgment_missing', 'UNRESOLVED')
                spans = judgment.get('evidence')
                require(type(spans) is list and spans, axis+':quote_evidence_missing', 'UNRESOLVED')
                quoted = {self.quote(span, sources) for span in spans}
                require('target' in quoted, axis+':own_target_quote_required', 'UNRESOLVED')
                if axis == 'faithful_corrected_retelling':
                    require({'target', 'anchor_target', 'anchor_result', 'anchor_feedback'} <= quoted,
                            'reflection:retelling_anchor_and_feedback_quotes_required', 'UNRESOLVED')
                if axis == 'feedback_use':
                    require({'target', 'prior_target', 'feedback'} <= quoted
                        and judgment.get('changed_action_known') is True
                        and nonempty(judgment.get('changed_action_or_expectation')),
                        'feedback_use:changed_action_evidence_unresolved', 'UNRESOLVED')
                    before = {span['quote'] for span in spans if span['source'] == 'prior_target'}
                    after = {span['quote'] for span in spans if span['source'] == 'target'}
                    require(before != after, 'feedback_use:changed_action_quotes_identical', 'UNRESOLVED')
            except EvidenceError as error:
                reasons.append(dict(status=error.status, code=axis+':'+error.code))
        return review, provenance, reasons


def compile_candidate(packet, *, trusted_artifacts, reviewer_provenance, generator_binding, excluded_task_ids=()):
    """Return auditable PASS/FAIL/UNRESOLVED; only PASS includes an unchanged row.

    Pins/provenance must come from the caller's separately trusted capture path,
    never be inferred from the candidate's own hash declarations.
    """
    compiler = Compiler(trusted_artifacts, reviewer_provenance, generator_binding, excluded_task_ids)
    output = dict(schema=SCHEMA, status='UNRESOLVED', eligible=False, row=None, reasons=[], reviews=[], disagreements=[],
        evidence_manifest=compiler.manifest, supplied_verifier_receipts=compiler.verifier_receipts,
        limitations=list(LIMITATIONS), semantic_truth_proven=False,
        reviewer_independence_verified=False, verifier_rerun=False, training_performed=False,
        scientific_claim=False, reflection_truth_verified=False, consolidation_performed=False,
        quality_gates=dict(length=False, voice=False, headings=False, token_count=False))

    def record_error(error, stage):
        status = error.status if isinstance(error, EvidenceError) else 'UNRESOLVED' if isinstance(error, KeyError) else 'FAIL'
        output['reasons'].append(dict(status=status, code=stage+':'+str(error)))

    context, prior, feedback_text = None, None, None
    try:
        require(type(packet) is dict, 'candidate_packet_required')
        require(packet.get('target_kind') in TARGET_KINDS, 'explicit_supported_target_kind_required', 'UNRESOLVED')
        output['target_kind'] = packet['target_kind']
        require(packet.get('label') in LABELS, 'known_requested_label')
        output['requested_label'] = packet['label']
        context = compiler.context(packet)
        output['binding'] = deepcopy(context['binding'])
        if packet['target_kind'] == 'POST_FEEDBACK_REFLECTION':
            output['anchor_outcome'] = deepcopy(context['result'])
            output['outcome_scope'] = 'ACCEPTED_ANCHOR_ONLY_NOT_REFLECTION_TRUTH'
        else:
            output['outcome'] = deepcopy(context['result'])
            output['outcome_scope'] = 'CANDIDATE_ANSWER_ONLY_NOT_SEMANTIC_RICHNESS'
        if context['result']['accepted'] is not True:
            output['reasons'].append(dict(status='FAIL', code='candidate:actual_verifier_not_accepted'))
        if packet['label'] == 'feedback_use':
            prior, feedback_text = compiler.feedback(packet.get('feedback'), context)
            context['binding'].update(earlier_target_sha256=text_sha256(prior['row']['target']),
                earlier_result_sha256=prior['result_artifact']['sha256'],
                feedback_message_sha256=packet['feedback']['message']['sha256'])
            output['binding'] = deepcopy(context['binding'])
    except (ValueError, KeyError, TypeError, IndexError, OverflowError) as error:
        record_error(error, 'provenance')
    reviews = packet.get('reviews') if type(packet) is dict else None
    if type(reviews) is not list or len(reviews) < 2:
        output['reasons'].append(dict(status='UNRESOLVED', code='two_independent_full_context_reviews_required'))
    principals, sessions, identities = set(), set(), set()
    for index, artifact in enumerate(reviews if type(reviews) is list else []):
        retained = dict(index=index)
        output['reviews'].append(retained)
        try:
            retained['judgment'] = compiler.read(artifact, 'review'+str(index))
            require(context is not None, 'candidate_provenance_unresolved', 'UNRESOLVED')
            review, provenance, reasons = compiler.review(artifact, context, prior, feedback_text, packet['label'], index)
            retained['provenance'] = deepcopy(provenance)
            retained['reasons'] = reasons
            identity, principal, session = (value.strip().casefold() for value in
                (review['reviewer_id'], provenance['principal_id'], provenance['session_id']))
            require(identity not in identities and principal not in principals and session not in sessions,
                    'distinct_attributed_independent_reviewers_required')
            identities.add(identity)
            principals.add(principal)
            sessions.add(session)
            output['reasons'].extend(dict(reason, reviewer_id=review['reviewer_id']) for reason in reasons)
        except (ValueError, KeyError, TypeError, IndexError, OverflowError) as error:
            record_error(error, 'review'+str(index))
            retained['validation_error'] = str(error)
    for axis in ('overall', *AXES, *REFLECTION_AXES, 'feedback_use'):
        judgments = []
        for retained in output['reviews']:
            review = retained.get('judgment', {})
            axes = review.get('axes', {})
            judgment = axes.get(axis, {}) if type(axes) is dict else {}
            status = review.get('status') if axis == 'overall' else judgment.get('status') if type(judgment) is dict else None
            if status in STATUSES:
                judgments.append(dict(index=retained['index'], reviewer_id=review.get('reviewer_id'), status=status))
        if len({judgment['status'] for judgment in judgments}) > 1:
            output['disagreements'].append(dict(axis=axis, judgments=judgments, resolved=False))
    if output['disagreements']:
        output['reasons'].append(dict(status='UNRESOLVED', code='review_disagreement_not_adjudicated'))
    statuses = {reason['status'] for reason in output['reasons']}
    output['status'] = 'FAIL' if 'FAIL' in statuses else 'UNRESOLVED' if statuses else 'PASS'
    output['eligible'] = output['status'] == 'PASS'
    if output['eligible']:
        output['row'] = deepcopy(context['row'])
        output['eligible_label'] = packet['label']
    return output
