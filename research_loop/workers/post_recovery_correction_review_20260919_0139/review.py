"""Explicit reviewer judgments with literal quote and canonical receipt checks."""

from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path

from collect_review import HERE, read, save, sha


def validate_grade(level, evidence):
    if level not in (0, 1, 2, 3):
        raise ValueError('bounded_correction_level_required')
    if level >= 1 and not (evidence['identifies_actual_correction'] and evidence['identification_exposed']):
        raise ValueError('actual_source_bound_identification_required')
    if level >= 2 and not (evidence['next_ACT_implements'] and evidence['next_ACT_exact_exposure']):
        raise ValueError('correct_next_ACT_with_exact_parent_exposure_required')
    if level >= 3 and not (evidence['another_relevant_ACT_implements']
            and evidence['intervening_context_complete'] and evidence['no_intervening_reminder'] is True):
        raise ValueError('another_relevant_ACT_and_complete_no_reminder_proof_required')


def numeric_checks():
    vertices = tuple('ABCDE')
    edges = {frozenset(edge) for edge in ('AB', 'BC', 'CD', 'DE', 'EA')}
    independent = [subset for count in range(6) for subset in itertools.combinations(vertices, count)
        if not any(frozenset(pair) in edges for pair in itertools.combinations(subset, 2))]
    return dict(learner_assigned=17 + 8 - 6, learner_reverse=(17 + 8 - 6) + 6 - 8,
        learner_changed_expression=21 - 6 - 8, frozen_assigned=17 + 8 - (7 + 3 + 5),
        frozen_independent_method=17 + 8 - 7 - 3 - 5, frozen_old_expression=17 + 8 - 6,
        C2_ACE_forbidden_pairs=[list(pair) for pair in itertools.combinations('ACE', 2) if frozenset(pair) in edges],
        C2_largest_independent_size=max(map(len, independent)),
        P7_strictly_greater_than_three={str(number): number > 3 for number in (2, 3, 4)})


def bound_quote(text, snippet, reference):
    start = text.find(snippet)
    if start < 0:
        raise ValueError('quote_must_be_literal_source_substring')
    if len(snippet) > 240:
        raise ValueError('tiny_quote_required')
    return dict(reference=reference, text=snippet, start=start, end=start + len(snippet),
        span_sha256=hashlib.sha256(snippet.encode()).hexdigest(),
        full_text_sha256=hashlib.sha256(text.encode()).hexdigest())


JUDGMENTS = {
    'learner': dict(level=0, category='EXPOSED_WRONG_OBJECT_AND_MATH_ERROR',
        publication='ef1319531b204597b4615a253d061d89', identifying=None, next_act=6427,
        task='Stay with 17 + 8 - 6', answer='21 - ６ - 8 = 17 - 8 = 8',
        finding='The assigned expression equals19; the substituted21-6-8 equals7, not8. ACT6348 says Error and correctly computes21-6=15, but still substitutes a different task, retains a nonnumeric symbol and supplies no requested reverse check. This does not identify the actual feedback correction.',
        other_outputs=[6269, 6348],
        unknown='No isolated reminder-free transfer trial; repeated arithmetic reminders enter at REQUEST6340 and6419. No causal claim about why the answer fails.'),
    'frozen': dict(level=1, category='RECOGNIZES_IN_THINK_CORRECTION_ABSENT_AT_ACT',
        publication='eabd8d4ebb3843dc9c911614f707fe6d', identifying=3630, next_act=3639,
        task='Stay with 17 + 8 - (7 + 3 + 5)', answer='17 + 8 - 6 = 25 - 6 = 19',
        recognition='My last attempt did not produce a calculation or a check.',
        finding='THINK3630 accurately identifies the preceding missing calculation/check (predecessor ACT3606 independently re-read). The exact correction is visible in THINK REQUEST3629 but absent from the following ACT REQUEST3638. ACT3639 solves the older expression19 instead of the assigned10 and repeats the same operations as its check. Later ACT3672 does obtain10, but its independent check is unfinished; ACT3705 contains metadata, not the requested calculation/check. Recognition earns1, not a complete next-ACT repair.',
        other_outputs=[3672, 3705],
        unknown='No ACT with the selected exact parent correction visible; no complete independent check or reminder-free transfer. This absence is not by itself a causal proof that compaction caused the failure.'),
    'C2': dict(level=0, category='EXPOSED_GRAPH_ERROR_THEN_UNSUPPORTED_ASSURANCE_WITH_LOST_CORRECTION',
        publication='a09f98c398a24674b28a6ef94ae743e3', identifying=None, next_act=12599,
        task='is {A,C,E} independent?', answer='The largest independent set includes the vertices {A, C, E}.',
        finding='The exposed graph task is answered incorrectly: EA is an edge, so {A,C,E} is not independent; the five-cycle maximum is2. The later actual model corrections request concrete pair/adjacency checks. They are visible in LEARN12717 or THINK12798/12805, but not in the next ACT REQUEST12813. ACT12815 merely prints a confidence statement. Generic claims of incorporating corrections do not identify a graph error.',
        other_outputs=[12717, 12798, 12815],
        unknown='Later model-correction ACT exposure is absent, not proven ignored under exposure. The512MiB read limit stops this window at12818; external-context projection is capped, so absence of intervening reminders cannot be certified.'),
    'P3': dict(level=0, category='EXPOSED_NO_SUBSTANTIVE_CAPTION_PERSISTENT_WAITING_LOOP',
        publication='0e2ffa3c8fa54413b454119b1b5e648b', identifying=None, next_act=6933,
        task='Where is the caption? Write it now, not a promise.',
        answer='Despite the previous challenges, we will follow the decided upon criteria and record the judges’',
        finding='The actual fresh model correction asks for an adult\'s spoken caption for the crib/mobile scene, rather than waiting for judges. Its literal attributed text is present in ACT REQUEST6932. ACT6933 repeatedly promises to follow decisions/record feedback and supplies no caption. This is nonproduction despite exposure, not a humor-quality failure; no sealed score was consulted.',
        other_outputs=[6926],
        unknown='Only one eligible post-correction ACT in this pre-cutoff window. Later publication377 delivery is outside this baseline judgment; no second relevant unreminded attempt or humor-quality judgment is established.'),
    'P7': dict(level=0, category='EXPOSED_NO_SUBSTANTIVE_PARENTING_ARTIFACT',
        publication='f0408fdf208d454ab4fa71e35133dcf4', identifying=None, next_act=9773,
        task='accepts numbers strictly greater than 3', answer='IntentionRandomTestsShouldBeIncludedForVerifiction',
        finding='The exact model correction asks P7 to write an actual parenting prompt using the >3 rule and2,3,4; it is visible in ACT REQUEST9772. ACT9773 supplies only a generic pattern/testing intention, with no rule, cases, or question to its child. Other sampled exposed ACTs9690/9804 likewise do not provide the requested concrete question/table. Language alone is not the failure criterion.',
        other_outputs=[9690, 9804],
        unknown='No demonstrated correction identification or relevant implementation. New corrective/task inputs arrive before later ACTs; no no-reminder transfer proof.512MiB bound leaves later records outside the reviewed window.'),
}


def build():
    rows, quotes = [], []
    for label, judgment in JUDGMENTS.items():
        path = HERE / 'evidence' / (label + '.json')
        document = read(path)
        by_output = {frame['response']['index']: frame for frame in document['frames']}
        parent = next(item for item in document['parents'] if item['id'] == judgment['publication'])
        next_act = by_output[judgment['next_act']]
        if next_act['stage'] != 'ACT' or not next_act['masked']:
            raise ValueError('actual_masked_ACT_required')
        if next_act['output']['truncated'] or parent['text']['truncated']:
            raise ValueError('complete_selected_task_and_output_required')
        identification = by_output[judgment['identifying']] if judgment['identifying'] else None
        flags = dict(identifies_actual_correction=identification is not None,
            identification_exposed=bool(identification and parent['id'] in identification['visible_publications']),
            next_ACT_implements=False, next_ACT_exact_exposure=parent['id'] in next_act['visible_publications'],
            another_relevant_ACT_implements=False, intervening_context_complete=False, no_intervening_reminder=None)
        validate_grade(judgment['level'], flags)
        task_quote = bound_quote(parent['text']['text'], judgment['task'], dict(publication_id=parent['id'], source_sha256=parent['sha256']))
        answer_quote = bound_quote(next_act['output']['text'], judgment['answer'], next_act['response'])
        selected_quotes = [task_quote, answer_quote]
        if identification:
            selected_quotes.append(bound_quote(identification['output']['text'], judgment['recognition'], identification['response']))
        additional_model_correction = None
        if label == 'C2':
            model_parent = next(item for item in document['parents'] if item['id'] == 'fe9f5646adb047b9912bdfa1a53ac7aa')
            later_act = by_output[12815]
            selected_quotes.append(bound_quote(model_parent['text']['text'],
                'write which vertices are directly connected to each vertex.',
                dict(publication_id=model_parent['id'], source_sha256=model_parent['sha256'])))
            selected_quotes.append(bound_quote(later_act['output']['text'],
                'The value shows consistency and satisfaction of the conditions.', later_act['response']))
            additional_model_correction = dict(publication_id=model_parent['id'],
                publication_sha256=model_parent['sha256'], first_sampled_THINK=by_output[12798]['request'],
                THINK_exact_exposure=model_parent['id'] in by_output[12798]['visible_publications'],
                next_ACT_request=later_act['request'], next_ACT_response=later_act['response'],
                next_ACT_exact_exposure=model_parent['id'] in later_act['visible_publications'],
                initial_gap_turn_is_model_generated=False)
        quotes.extend(dict(label=label, **quote) for quote in selected_quotes)
        proof_frames = [next_act] + ([identification] if identification else []) + [by_output[index] for index in judgment['other_outputs']]
        boot = datetime(2026, 9, 18, 22, 50, 45, tzinfo=timezone.utc).timestamp()
        if not boot <= parent['publication_mtime_unix'] <= document['cutoff_unix']:
            raise ValueError('fresh_pre_cutoff_parent_required')
        if any(not boot <= frame['response_utc'] <= document['cutoff_unix'] for frame in proof_frames):
            raise ValueError('post_reboot_pre_cutoff_output_required')
        proofs = [{key: frame[key] for key in ('stage', 'request', 'response', 'committed', 'stage_receipt',
            'request_utc', 'response_utc', 'masked', 'visible_publications')} for frame in proof_frames]
        rows.append(dict(label=label, best_supported_level=judgment['level'], category=judgment['category'],
            finding=judgment['finding'], unknowns=judgment['unknown'], flags=flags, evidence_path=str(path.relative_to(HERE)),
            additional_model_correction=additional_model_correction,
            evidence_sha256=sha(path), source_epoch_sha256=document['source_epoch_sha256'],
            source_epoch=document['source_epoch'], quotes=selected_quotes, proofs=proofs,
            window=dict(first=document['coverage_start'], through=document['through']['index'],
                cutoff_unix=document['cutoff_unix'], bytes_read=document['bytes_read'],
                reviewed_ACTs=sum(frame['stage'] == 'ACT' for frame in document['frames'])),
            intervening_parent_inputs=[dict(request=item['first_request'], event_key=item['key'],
                excerpt=item['text']['text'][:180], full_text_sha256=item['text']['text_sha256'])
                for item in document['new_external_events'] if item['actor'] == 'parent'],
            level3_status='NOT_DEMONSTRATED_NO_PROMOTION', semantic_review='MANUAL_SOURCE_BOUND_NOT_PARENT_SELF_REPORT'))
    reference = numeric_checks()
    if reference != dict(learner_assigned=19, learner_reverse=17, learner_changed_expression=7,
            frozen_assigned=10, frozen_independent_method=10, frozen_old_expression=19,
            C2_ACE_forbidden_pairs=[['A', 'E']], C2_largest_independent_size=2,
            P7_strictly_greater_than_three={'2': False, '3': False, '4': True}):
        raise ValueError('independent_arithmetic_reference_mismatch')
    report = dict(reviewed_utc=datetime.now(timezone.utc).isoformat(), cutoff_utc='2026-09-19T01:39:59Z',
        reboot_utc='2026-09-18T22:50:45Z', rows=rows, reference_checks=reference,
        frozen_predecessor_evidence=dict(path='evidence/frozen_PREDECESSOR.json', sha256=sha(HERE / 'evidence/frozen_PREDECESSOR.json')),
        level_definitions={'0': 'No specific actual correction identified in this sampled feedback chain.',
            '1': 'Specific real correction identified with source-bound feedback exposure.',
            '2': 'Level1 plus next ACT implements correctly, with exact parent exposure verified.',
            '3': 'Level2 plus another relevant ACT implements, with a complete no-intervening-reminder proof.'},
        independent_second_reviewer=False, prior_P3_recovery_authorship_disclosed=True,
        retention_effect_claim=False, parent_messages_sent=0, process_changes=0, GPU_runs=0,
        sealed_scores_read=False, checkpoint_loads=0, git_commits=0)
    save(HERE / 'REVIEW.json', report)
    save(HERE / 'QUOTE_BINDINGS.json', quotes)
    save(HERE / 'REFERENCE_CHECKS.json', reference)
    print(json.dumps(dict(levels={row['label']: row['best_supported_level'] for row in rows},
        next_ACT_exact_exposure={row['label']: row['flags']['next_ACT_exact_exposure'] for row in rows}, quotes=len(quotes))))


if __name__ == '__main__':
    build()
