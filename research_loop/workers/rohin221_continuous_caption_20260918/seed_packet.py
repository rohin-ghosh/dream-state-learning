"""Build a fixed, manually selected teaching packet from verified development receipts."""

import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent
TREATMENT = 'R230_FROZEN_BASE_JOKE_SEEDS_V1_N2'
SOURCE_CUT_SHA256 = 'a641c175e01d826a14393fbefe8b7d1024b61b08c9101974377f775f7f0bba14'
SELECTED = {
    46: 'Financial double meaning: a self-financing crib and not buying the argument.',
    79: 'Literary-title and business-suit wordplay with briefcase/briefcase-less contrast.',
}
DESCRIPTIONS = {1, 3, 4, 10, 16, 27, 33, 42, 56, 58, 73, 75, 82, 87,
    125, 165, 168, 169, 172, 174, 177, 179, 235, 265}
VARIANTS = {45: 43, 81: 72, 185: 73}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def normalized_caption(text):
    return re.sub(r'[^\w]+', ' ', text.casefold()).strip()


def select_examples(candidate_audit):
    if candidate_audit['frozen_cut_sha256'] != SOURCE_CUT_SHA256:
        raise ValueError('exact_reviewed_cut_required')
    pool = [row for row in candidate_audit['review_rows'] if row['status'] == 'new_pixel']
    if len(pool) != 47 or len({row['text_sha256'] for row in pool}) != 47:
        raise ValueError('exact_nonrepeat_pool_required')
    verified = {example['exact_source_span']['text_sha256']: example for example in candidate_audit['examples']}
    selected, audit_rows, seen = [], [], set()
    for row in pool:
        sequence = row['sequence']
        included = sequence in SELECTED
        if sequence in DESCRIPTIONS:
            reason = 'description_or_scene_analysis_not_seed_joke'
        elif sequence in VARIANTS:
            reason = 'near_variant_of_candidate_' + str(VARIANTS[sequence])
        elif included:
            reason = SELECTED[sequence]
        else:
            reason = 'weak_or_ambiguous_caption_without_clear_joke_payoff'
        audit_rows.append(dict(sequence=sequence, caption_sha256=row['text_sha256'],
            receipt_sha256=row['receipt_sha256'], contest_id=row['contest_id'], rank=row['rank'],
            included=included, reason=reason))
        if not included:
            continue
        proof = verified[row['text_sha256']]
        result = proof['result']
        caption = proof['literal_child_caption']
        if (not result['accepted'] or result['status'] != 'new_pixel' or result.get('replayed') is not False
                or proof['exact_source_span'].get('stage') != 'ACT'
                or proof.get('exact_generation_hashes_verified') is not True
                or not proof['novelty']['pixel_id_not_present_before_attempt']):
            raise ValueError('actual_new_noncached_ACT_proof_required')
        if digest(caption.encode()) != row['text_sha256'] or caption != row['literal_text']:
            raise ValueError('exact_literal_caption_required')
        if proof['scorer_result']['sha256'] != row['receipt_sha256']:
            raise ValueError('exact_result_receipt_required')
        if result['rank'] != row['rank'] or result['top_k'] != 50 or result['reference_count'] != 64:
            raise ValueError('unchanged_historical_rank_required')
        normalized = normalized_caption(caption)
        if normalized in seen:
            raise ValueError('duplicate_seed_caption')
        seen.add(normalized)
        selected.append(dict(seed_id='R230-SEED-' + str(len(selected) + 1).zfill(2),
            caption=caption, caption_sha256=row['text_sha256'],
            normalized_caption_sha256=digest(normalized.encode()),
            designation='TEACHING_FROM_RELEASED_DEVELOPMENT_GAME_NOT_HELD_OUT_TEST',
            scene=proof['scene'], historical_result=result, scored_utc=proof['scored_utc'],
            manual_selection_rationale=SELECTED[sequence],
            source=dict(mode='FROZEN_BASE_STANDALONE_GENERATION_NO_OPTIMIZER',
                stage='ACT', opportunity=proof['opportunity'], attempt=proof['attempt'],
                generation_file_sha256=proof['generation']['sha256'],
                request_sha256=proof['request_sha256'], response_sha256=proof['response_sha256'],
                result_receipt_sha256=proof['scorer_result']['sha256'],
                ACT_finished_utc=proof['ACT_finished_utc'],
                literal_span={key:proof['exact_source_span'][key] for key in ('start','end','line','stage','text_sha256')}),
            novelty_proof=proof['novelty']))
    if len(selected) != len(SELECTED):
        raise ValueError('missing_manually_selected_seed')
    return selected, audit_rows


def build_packet(candidate_audit):
    examples, audit_rows = select_examples(candidate_audit)
    packet = dict(schema='R230_SOURCE_BOUND_CAPTION_SEED_PACKET_V1', treatment_id=TREATMENT,
        prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        requested_example_range=[10, 12], selected_examples=len(examples), quota_filled=False,
        shortfall_reason='Only two clearly joke-like, deduplicated constructions retained after manually inspecting all47 noncached new-pixel ACT candidates; no padding with descriptions or weak variants.',
        source_cut=dict(file='R227_FLEET_COUNTS_20260918T093638Z.json', sha256=SOURCE_CUT_SHA256,
            latest_raw_accepted=281, raw_new_pixels=47, raw_repeats=234, new_scored_strings=420),
        selection=dict(manually_reviewed=47, selected=2, excluded=45, not_blind=True,
            no_independent_humor_certification=True, semantic_dedup='Two distinct scenes and joke mechanisms; excluded near-variants remain documented.',
            sources_not_eligible_as_seeds='234 scorer repeats and149 cached results were excluded before quality review.'),
        examples=examples,
        usage=dict(role='SUPPLIED_TEACHING_CONTEXT_NOT_CHILD_GENERATION_OR_FRESH_TOOL_FEEDBACK',
            count_as_new_exploration=False, count_as_new_attempts=False, count_as_new_acceptances=False,
            show_rank_as_historical=True, preserve_frozen_base_unseeded_control=True,
            scoring_policy_unchanged=True, training_eligibility_unchanged=True,
            no_retroactive_own_response_targets=True,
            teaching_scenes_not_unseen_evaluation=True,
            exact_seed_echoes_report_separately_from_new_exploration=True,
            paraphrase_overlap_requires_descriptive_review_not_assumed_novelty=True),
        rollout=dict(status='PREPARED_NOT_DELIVERED',
            owners=dict(P3='Main', node3_C2_lineage='Copernicus', additional_node2_player='Cicero', C0='Main-designated owner only when C0 plays'),
            required_receipt_fields=['treatment_id','packet_sha256','context_sha256','life_id','journal_id',
                'source_context_record_index','source_context_record_sha256','published_utc',
                'first_rendered_REQUEST_index','first_rendered_REQUEST_sha256','first_rendered_REQUEST_utc',
                'first_post_seed_ACT_origin_sha256'],
            curve_boundary='First actual REQUEST rendering seed context, not merely inbox publication or wall-clock delivery. ACTs generated from earlier requests remain pre-seed even if scored later.',
            cohort_labels=['pre_seed','post_R230_FROZEN_BASE_JOKE_SEEDS_V1_N2'],
            formerly_unparented_label='unparented_with_supplied_seed_context; no longer an unseeded control',
            recipients_must_use_same_packet_version=True),
        privacy=dict(sealed_or_FINAL_panels_included=False, reference_caption_panels_included=False,
            credentials_or_infrastructure_addresses_included=False),
        historical_resubmissions=0, scoring_calls_made=0, delivery_actions_taken=0)
    audit = dict(schema='R230_MANUAL_SEED_SELECTION_AUDIT_V1', treatment_id=TREATMENT,
        source_cut_sha256=SOURCE_CUT_SHA256, manually_reviewed=47, selected=2, excluded=45,
        reason_counts=dict(selected_clear_joke_like=2, description_or_scene_analysis=24,
            near_variant=3, weak_or_ambiguous=18), rows=audit_rows,
        caveat='Descriptive teaching selection only, not a new scoring gate, LEARN filter or claim that selected examples are objectively funny.')
    return packet, audit


def child_context(packet):
    lines = ['SUPPLIED DEVELOPMENT EXAMPLES — ' + packet['treatment_id'], '',
        'These two worked examples were generated earlier by a frozen-base control on released development scenes.',
        'They are supplied teaching context, not your attempts or new judge feedback. The ranks below are historical,',
        'against64 reference captions under the existing top50/relevance rule. Acceptance is not a guarantee of humor.',
        'Use them to see possible wordplay, then explore your own new captions. Copying a supplied seed is not new exploration.', '']
    for example in packet['examples']:
        lines += ['Released development Scene' + str(example['scene']['number']) + ':',
            example['scene']['description'], '', example['caption'],
            'Historical rank: ' + str(example['historical_result']['rank']) + ' of65; accepted, noncached, new cluster at its original scoring.', '']
    lines += ['No fixed caption count or output format is required. Keep guessing with actual captions each opportunity.',
        'These examples do not change the judge, the scoring rules, or learning eligibility.']
    return '\n'.join(lines) + '\n'


def add_file(path, content):
    if path.exists():
        raise ValueError('immutable_seed_packet_already_exists')
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n' + ''.join('+' + line + '\n' for line in content.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, check=True, capture_output=True)


def main():
    private_audit = json.loads(Path('/tmp/r230-base-seed-candidate-audit.json').read_bytes())
    packet, audit = build_packet(private_audit)
    packet_path = ROOT / 'R230_FROZEN_BASE_SEED_PACKET_v1.json'
    context_path = ROOT / 'R230_SEED_CONTEXT_v1.txt'
    context = child_context(packet)
    packet['child_context'] = dict(file=context_path.name, sha256=digest(context.encode()))
    add_file(packet_path, json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False))
    add_file(context_path, context)
    audit['packet_sha256'] = digest(packet_path.read_bytes())
    add_file(ROOT / 'R230_SEED_SELECTION_AUDIT_v1.json', json.dumps(audit, indent=2, sort_keys=True))
    print(json.dumps(dict(packet=str(packet_path), packet_sha256=digest(packet_path.read_bytes()),
        context=str(context_path), context_sha256=digest(context_path.read_bytes()), selected=2,
        requested=[10,12], delivered=False), sort_keys=True))


if __name__ == '__main__':
    main()
