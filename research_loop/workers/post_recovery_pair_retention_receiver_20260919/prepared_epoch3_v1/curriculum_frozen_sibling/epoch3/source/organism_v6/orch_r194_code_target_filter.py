"""Opt-in target exclusion only; never normalize targets or change raw history.

Every backtick/tilde fenced block is scanned, including an unclosed final block.
Fences start a line after optional indentation or Markdown quote/list markers;
same-line fenced bodies are also recognized. A closing fence must use the same
character and at least the opening length. Prose and single/double-backtick
inline code are not scanned. U+3000 is explicitly classified as
IDEOGRAPHIC_SPACE, separately from U+FF01..U+FF5E.

R195 reviews parse only source-bound child directives from committed pending
rows. Exclusions express child requests, not verified errors or truth judgments.
"""

from collections import Counter
from copy import deepcopy
import hashlib
import json
import re


POLICY = 'R194_FULLWIDTH_CODE_TARGET_EXCLUSION_V1'
ZERO_UPDATE_SCHEMA = 'R194_CODE_TARGET_FILTER_ZERO_UPDATE_V1'
NO_UPDATE_REASON = 'no_eligible_child_rows'
CODE_FILTER_SUBREASON = 'code_target_filter_excluded_all_rows'
REVIEW_POLICY = 'R195_CHILD_ROW_REVIEW_V1'
REVIEW_ZERO_UPDATE_SCHEMA = 'R195_REVIEW_FILTER_ZERO_UPDATE_V1'
REVIEW_NO_UPDATE_REASON = NO_UPDATE_REASON
REVIEW_FILTER_SUBREASON = 'review_target_filters_excluded_all_rows'
FENCE_PREFIX = r'[ \t]*(?:>[ \t]*)*'
FENCE = re.compile(FENCE_PREFIX + r'(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$')
REVIEW_DIRECTIVE = re.compile(r'Do not train: (?:row (0|[1-9][0-9]*|self)|(self)) [—-] (\S(?:.*\S)?)')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def validate_policy(plan):
    if 'code_target_filter' not in plan:
        return None
    policy = plan['code_target_filter']
    require(type(policy) is str and policy == POLICY, 'known_code_target_filter_policy')
    return policy


def validate_review_policy(plan):
    if 'learn_review_filter' not in plan:
        return None
    policy = plan['learn_review_filter']
    require(type(policy) is str and policy == REVIEW_POLICY, 'known_learn_review_filter_policy')
    return policy


def parse_learn_review(target, candidates, review_source_sha256):
    require(type(target) is str, 'review_original_target_required')
    accepted, rejected = [], []
    marker, width = None, 0
    for number, line in enumerate(target.splitlines(), 1):
        fenced = marker is not None
        if marker is None:
            opening = FENCE.fullmatch(line)
            if opening is not None:
                fence, tail = opening.groups()
                marker, width, fenced = fence[0], len(fence), True
                if re.search(re.escape(marker) + '{' + str(width) + r',}[ \t]*$', tail):
                    marker = None
        elif re.fullmatch(FENCE_PREFIX + re.escape(marker) + '{' + str(width) + r',}[ \t]*', line):
            marker = None
        text = line.strip()
        if 'do not train' not in text.lower():
            continue
        if fenced or text.startswith('>'):
            rejected.append(dict(line=number, directive=line, reason='fenced_or_quoted_directive'))
            continue
        matched = REVIEW_DIRECTIVE.fullmatch(text)
        if matched is None:
            rejected.append(dict(line=number, directive=line, reason='malformed_directive'))
            continue
        identifier, self_identifier, reason = matched.groups()
        source = review_source_sha256 if self_identifier or identifier == 'self' else candidates.get(identifier)
        if source is None:
            rejected.append(dict(line=number, directive=line, reason='unknown_or_out_of_batch_segment'))
        else:
            accepted.append(dict(line=number, source_sha256=source, child_reason=reason))
    return accepted, rejected


def filter_learn_review_targets(new_rows, old_rows, policy):
    require(type(policy) is str and policy == REVIEW_POLICY, 'known_learn_review_filter_policy')
    sources, segments = [], {}
    for row in new_rows:
        source, segment = row.get('source_sha256'), row.get('segment')
        require(row.get('split') == 'TRAIN' and row.get('actor') == 'child'
            and row.get('prefix_loss') is False and row.get('target_loss') is True
            and type(row.get('target')) is str, 'review_child_raw_targets_only')
        require(type(source) is str and re.fullmatch(r'[0-9a-f]{64}', source) is not None
            and source not in sources and type(segment) is int and segment >= 0
            and str(segment) not in segments, 'review_unique_bound_pending_rows')
        sources.append(source)
        segments[str(segment)] = source
    receipt_proof, receipt_vetoes = None, {}
    evidence_rows = [row for row in new_rows if 'learn_review_evidence' in row]
    if evidence_rows:
        from organism_v6.orch_r195_receipt_target_filter import POLICY as receipt_policy, receipt_exclusions
        require(all(type(row['learn_review_evidence']) is list
            and all(type(evidence) is dict for evidence in row['learn_review_evidence']) for row in evidence_rows),
            'receipt_evidence_list_of_objects')
        receipt_proof = receipt_exclusions(deepcopy(new_rows))
        require(type(receipt_proof) is dict and receipt_proof.get('policy') == receipt_policy
            and type(receipt_proof.get('excluded')) is list and receipt_proof.get('raw_modified') is False
            and receipt_proof.get('targets_normalized') is False, 'receipt_filter_proof_contract')
        by_source = {row['source_sha256']: row for row in new_rows}
        for exclusion in receipt_proof['excluded']:
            require(type(exclusion) is dict and exclusion.get('source_sha256') in by_source,
                'receipt_exclusion_bound_to_pending_row')
            target = by_source[exclusion['source_sha256']]
            require(exclusion.get('policy') == receipt_policy and exclusion.get('cohort') == 'NEW'
                and exclusion.get('segment') == target['segment']
                and exclusion.get('raw_target_sha256') == hashlib.sha256(target['target'].encode()).hexdigest()
                and exclusion.get('semantic_falsehood_claimed') is False
                and type(exclusion.get('reason')) is str and exclusion['reason'],
                'receipt_exclusion_preserves_raw_target_and_scope')
            receipt_vetoes.setdefault(target['source_sha256'], []).append(exclusion)
    prose_proof, prose_vetoes = None, {}
    if any('prose_target_filter' in row for row in new_rows):
        from organism_v6.orch_r203_prose_target_filter import prose_exclusions
        prose_proof = prose_exclusions(new_rows)
        prose_vetoes = {exclusion['source_sha256']: exclusion for exclusion in prose_proof['excluded']}
    content_proof, content_vetoes = None, {}
    if any('content_target_filter' in row for row in new_rows):
        from organism_v6.orch_r213_content_target_filter import content_exclusions
        content_proof = content_exclusions(new_rows)
        content_vetoes = {exclusion['source_sha256']: exclusion for exclusion in content_proof['excluded']}
    reviews, vetoes = [], {}
    for index, row in enumerate(new_rows):
        if 'learn_review' not in row:
            continue
        annotation = row['learn_review']
        require(type(annotation) is dict and set(annotation) == {
            'schema', 'candidate_source_sha256', 'review_source_sha256'}
            and annotation['schema'] == REVIEW_POLICY
            and annotation['review_source_sha256'] == row['source_sha256']
            and type(annotation['candidate_source_sha256']) is list
            and annotation['candidate_source_sha256'] == sources[:index + 1],
            'review_exact_committed_pending_candidates_including_self')
        candidates = {segment: source for segment, source in segments.items()
            if source in annotation['candidate_source_sha256']}
        accepted, rejected = parse_learn_review(row['target'], candidates, row['source_sha256'])
        reviews.append(dict(review_source_sha256=row['source_sha256'], annotation_sha256=digest(annotation),
            raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
            candidate_source_sha256=list(annotation['candidate_source_sha256']), accepted=accepted, rejected=rejected))
        for directive in accepted:
            vetoes.setdefault(directive['source_sha256'], []).append(dict(
                review_source_sha256=row['source_sha256'], **directive))
    retained, excluded = [], []
    for index, row in enumerate(new_rows):
        source = row['source_sha256']
        if source in vetoes or source in receipt_vetoes or source in prose_vetoes or source in content_vetoes:
            exclusion = dict(source_sha256=source, segment=row['segment'], cohort='NEW',
                row_index=index, raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                policy=REVIEW_POLICY, reason='child_requested_do_not_train' if source in vetoes
                    else 'receipt_bound_provisional_quarantine' if source in receipt_vetoes
                    else prose_vetoes[source]['reason'] if source in prose_vetoes
                    else content_vetoes[source]['reason'])
            if source in vetoes:
                exclusion['directives'] = vetoes[source]
            if source in receipt_vetoes:
                exclusion['receipt_exclusions'] = receipt_vetoes[source]
            if source in prose_vetoes:
                exclusion['prose_exclusions'] = [prose_vetoes[source]]
            if source in content_vetoes:
                exclusion['content_exclusions'] = [content_vetoes[source]]
            excluded.append(exclusion)
        else:
            retained.append(row)
    old_sources = [row['source_sha256'] for row in old_rows]
    proof = dict(policy=REVIEW_POLICY, input_row_sha256=dict(NEW=sources, REHEARSAL=old_sources),
        retained_row_sha256=dict(NEW=[row['source_sha256'] for row in retained], REHEARSAL=old_sources),
        retained_counts=dict(NEW=len(retained), REHEARSAL=len(old_rows)),
        excluded_counts=dict(NEW=len(excluded), REHEARSAL=0), reviews=reviews, excluded=excluded,
        raw_modified=False, targets_normalized=False, exclusion_basis='CHILD_REQUEST_NOT_VERIFIED_ERROR')
    if receipt_proof is not None:
        proof.update(receipt_filter=receipt_proof,
            receipt_filter_evidence_sha256=digest([dict(source_sha256=row['source_sha256'],
                evidence=row['learn_review_evidence']) for row in evidence_rows]),
            exclusion_basis='CHILD_REQUEST_OR_PROVISIONAL_RECEIPT_QUARANTINE')
    if prose_proof is not None:
        proof.update(prose_target_filter=prose_proof,
            exclusion_basis='CHILD_REQUEST_OR_PROVISIONAL_TARGET_QUARANTINE')
    if content_proof is not None:
        proof.update(content_target_filter=content_proof,
            exclusion_basis='CHILD_REQUEST_OR_PROVISIONAL_TARGET_QUARANTINE')
    return retained, old_rows, proof


def scan_target(text):
    require(type(text) is str, 'code_target_filter_raw_text_required')
    marker, width, blocks = None, 0, 0
    counts, affected = Counter(), set()

    def collect(body):
        for character in body:
            point = ord(character)
            if 0xFF01 <= point <= 0xFF5E or point == 0x3000:
                counts[point] += 1
                affected.add(blocks)

    for line in text.splitlines():
        if marker is None:
            opening = FENCE.fullmatch(line)
            if opening is None:
                continue
            fence, tail = opening.groups()
            marker, width = fence[0], len(fence)
            blocks += 1
            inline_close = re.search(re.escape(marker) + '{' + str(width) + r',}[ \t]*$', tail)
            if inline_close is not None:
                collect(tail[:inline_close.start()])
                marker = None
            continue
        if re.fullmatch(FENCE_PREFIX + re.escape(marker) + '{' + str(width) + r',}[ \t]*', line):
            marker = None
        else:
            collect(line)
    return dict(fenced_blocks=blocks, unclosed_fenced_block=marker is not None,
        affected_blocks=sorted(affected), glyph_count=sum(counts.values()),
        codepoints=[dict(codepoint=f'U+{point:04X}', count=count,
            category='IDEOGRAPHIC_SPACE' if point == 0x3000 else 'FULLWIDTH_ASCII_RANGE')
            for point, count in sorted(counts.items())])


def filter_sleep_targets(new_rows, old_rows, policy):
    require(policy == POLICY and type(policy) is str, 'known_code_target_filter_policy')
    retained = {'NEW': [], 'REHEARSAL': []}
    inputs, excluded = {}, []
    for cohort, rows in (('NEW', new_rows), ('REHEARSAL', old_rows)):
        inputs[cohort] = []
        for index, row in enumerate(rows):
            require(row.get('split') == 'TRAIN' and row.get('actor') == 'child'
                and row.get('prefix_loss') is False and row.get('target_loss') is True,
                'code_target_filter_child_targets_only')
            source = row['source_sha256']
            require(type(source) is str and re.fullmatch(r'[0-9a-f]{64}', source) is not None,
                'code_target_filter_source_hash_required')
            inputs[cohort].append(source)
            evidence = scan_target(row['target'])
            if evidence['glyph_count']:
                excluded.append(dict(source_sha256=source, cohort=cohort, row_index=index,
                    raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                    policy=POLICY, reason='fullwidth_glyph_in_fenced_code', evidence=evidence))
            else:
                retained[cohort].append(row)
    proof = dict(policy=POLICY, input_row_sha256=inputs, excluded=excluded,
        retained_row_sha256={cohort: [row['source_sha256'] for row in rows]
            for cohort, rows in retained.items()},
        retained_counts={cohort: len(rows) for cohort, rows in retained.items()},
        excluded_counts={cohort: sum(item['cohort'] == cohort for item in excluded) for cohort in retained},
        raw_modified=False, targets_normalized=False)
    return retained['NEW'], retained['REHEARSAL'], proof


def zero_update_authorization(proof, *, rehearsal_presentations, optimizer_steps, adapter_sha256):
    require(proof['policy'] == POLICY and proof['input_row_sha256']['NEW']
        and proof['retained_counts'] == {'NEW': 0, 'REHEARSAL': 0}, 'r194_all_candidate_rows_excluded')
    require(type(rehearsal_presentations) is int and rehearsal_presentations in (0, 1),
        'r194_bound_rehearsal_selection')
    require(type(optimizer_steps) is int and optimizer_steps >= 0, 'r194_actual_optimizer_counter')
    require(type(adapter_sha256) is str and re.fullmatch(r'[0-9a-f]{64}', adapter_sha256) is not None,
        'r194_actual_adapter_hash')
    return dict(schema=ZERO_UPDATE_SCHEMA, policy=POLICY,
        eligibility_sha256=digest(proof), rehearsal_presentations=rehearsal_presentations,
        optimizer_steps_before=optimizer_steps, adapter_sha256=adapter_sha256)


def validate_zero_update_receipt(receipt, new_rows, old_rows):
    authorization = receipt['code_target_filter_zero_update']
    require(type(authorization) is dict and set(authorization) == {
        'schema', 'policy', 'eligibility_sha256', 'rehearsal_presentations',
        'optimizer_steps_before', 'adapter_sha256'} and authorization['schema'] == ZERO_UPDATE_SCHEMA
        and authorization['policy'] == POLICY, 'r194_exact_zero_update_authorization')
    rehearsal = authorization['rehearsal_presentations']
    require(type(rehearsal) is int and rehearsal in (0, 1), 'r194_bound_rehearsal_selection')
    new_retained, old_retained, proof = filter_sleep_targets(new_rows, old_rows if rehearsal else [], POLICY)
    require(new_rows and not new_retained and not old_retained
        and receipt.get('code_target_filter') == proof
        and receipt.get('excluded_rows') == proof['excluded']
        and authorization['eligibility_sha256'] == digest(proof), 'r194_actual_raw_exclusions_required')
    require(type(receipt.get('optimizer_steps')) is int and receipt['optimizer_steps'] == 0
        and receipt.get('no_update_reason') == NO_UPDATE_REASON and receipt.get('presentations') == {}
        and receipt.get('no_update_subreason') == CODE_FILTER_SUBREASON
        and type(receipt.get('child_token_exposures')) is int and receipt['child_token_exposures'] == 0
        and type(receipt.get('anchor_token_exposures')) is int and receipt['anchor_token_exposures'] == 0,
        'r194_zero_update_no_anchor_only_training')
    steps = authorization['optimizer_steps_before']
    adapter = authorization['adapter_sha256']
    require(type(steps) is int and steps >= 0 and type(receipt.get('total_optimizer_steps')) is int
        and receipt['total_optimizer_steps'] == steps
        and receipt.get('before_adapter_sha256') == receipt.get('after_adapter_sha256') == adapter
        and type(adapter) is str and re.fullmatch(r'[0-9a-f]{64}', adapter) is not None,
        'r194_unchanged_learning_state')
    checkpoint = receipt.get('checkpoint', {})
    require(type(checkpoint) is dict and type(checkpoint.get('optimizer_steps')) is int
        and checkpoint['optimizer_steps'] == steps
        and checkpoint.get('adapter_state_sha256') == adapter, 'r194_checkpoint_matches_no_update')
    require(receipt.get('code_target_filter_counts') == dict(NEW=0, REHEARSAL=0)
        and receipt.get('code_target_filter_presentations') == {}, 'r194_no_scheduled_presentations')


def review_zero_update_authorization(review_proof, code_proof, *, rehearsal_presentations,
        optimizer_steps, adapter_sha256):
    final_proof = review_proof if code_proof is None else code_proof
    require(review_proof['policy'] == REVIEW_POLICY and review_proof['input_row_sha256']['NEW']
        and final_proof['retained_counts'] == dict(NEW=0, REHEARSAL=0), 'r195_all_candidate_rows_excluded')
    require(type(rehearsal_presentations) is int and rehearsal_presentations in (0, 1),
        'r195_bound_rehearsal_selection')
    require(type(optimizer_steps) is int and optimizer_steps >= 0 and type(adapter_sha256) is str
        and re.fullmatch(r'[0-9a-f]{64}', adapter_sha256) is not None, 'r195_actual_learning_state')
    return dict(schema=REVIEW_ZERO_UPDATE_SCHEMA, policy=REVIEW_POLICY,
        eligibility_sha256=digest(dict(learn_review_filter=review_proof, code_target_filter=code_proof)),
        rehearsal_presentations=rehearsal_presentations, optimizer_steps_before=optimizer_steps,
        adapter_sha256=adapter_sha256)


def validate_review_zero_update_receipt(receipt, new_rows, old_rows):
    authorization = receipt['learn_review_zero_update']
    require(type(authorization) is dict and set(authorization) == {
        'schema', 'policy', 'eligibility_sha256', 'rehearsal_presentations',
        'optimizer_steps_before', 'adapter_sha256'} and authorization['schema'] == REVIEW_ZERO_UPDATE_SCHEMA
        and authorization['policy'] == REVIEW_POLICY, 'r195_exact_zero_update_authorization')
    rehearsal = authorization['rehearsal_presentations']
    require(type(rehearsal) is int and rehearsal in (0, 1), 'r195_bound_rehearsal_selection')
    retained_new, retained_old, review_proof = filter_learn_review_targets(
        new_rows, old_rows if rehearsal else [], REVIEW_POLICY)
    excluded = list(review_proof['excluded'])
    code_proof = None
    if 'code_target_filter' in receipt:
        retained_new, retained_old, code_proof = filter_sleep_targets(retained_new, retained_old, POLICY)
        excluded.extend(code_proof['excluded'])
        require(receipt['code_target_filter'] == code_proof
            and receipt.get('code_target_filter_counts') == dict(NEW=0, REHEARSAL=0)
            and receipt.get('code_target_filter_presentations') == {}, 'r195_bound_fullwidth_exclusions')
    require(new_rows and not retained_new and not retained_old
        and receipt.get('learn_review_filter') == review_proof and receipt.get('excluded_rows') == excluded
        and authorization['eligibility_sha256'] == digest(dict(
            learn_review_filter=review_proof, code_target_filter=code_proof)), 'r195_actual_raw_review_required')
    require(type(receipt.get('optimizer_steps')) is int and receipt['optimizer_steps'] == 0
        and receipt.get('no_update_reason') == NO_UPDATE_REASON
        and receipt.get('no_update_subreason') == REVIEW_FILTER_SUBREASON
        and receipt.get('presentations') == {}
        and type(receipt.get('child_token_exposures')) is int and receipt['child_token_exposures'] == 0
        and type(receipt.get('anchor_token_exposures')) is int and receipt['anchor_token_exposures'] == 0,
        'r195_zero_update_no_anchor_only_training')
    steps, adapter = authorization['optimizer_steps_before'], authorization['adapter_sha256']
    require(type(steps) is int and steps >= 0 and type(receipt.get('total_optimizer_steps')) is int
        and receipt['total_optimizer_steps'] == steps and type(adapter) is str
        and re.fullmatch(r'[0-9a-f]{64}', adapter) is not None
        and receipt.get('before_adapter_sha256') == receipt.get('after_adapter_sha256') == adapter,
        'r195_unchanged_learning_state')
    checkpoint = receipt.get('checkpoint')
    require(type(checkpoint) is dict and type(checkpoint.get('optimizer_steps')) is int
        and checkpoint['optimizer_steps'] == steps and checkpoint.get('adapter_state_sha256') == adapter,
        'r195_checkpoint_matches_no_update')
    require(receipt.get('learn_review_filter_counts') == dict(NEW=0, REHEARSAL=0)
        and receipt.get('learn_review_filter_presentations') == {}, 'r195_no_scheduled_presentations')


def validate_filter_zero_update_receipt(receipt, new_rows, old_rows):
    code_authorization = 'code_target_filter_zero_update' in receipt
    review_authorization = 'learn_review_zero_update' in receipt
    require(not (code_authorization and review_authorization), 'one_target_filter_zero_update_authorization')
    if review_authorization:
        validate_review_zero_update_receipt(receipt, new_rows, old_rows)
        return True
    if code_authorization:
        require('learn_review_filter' not in receipt, 'review_requires_combined_zero_update_authorization')
        validate_zero_update_receipt(receipt, new_rows, old_rows)
        return True
    if receipt.get('optimizer_steps') == 0:
        require(receipt.get('no_update_subreason') not in (CODE_FILTER_SUBREASON, REVIEW_FILTER_SUBREASON),
            'target_filter_zero_update_authorization_required')
        for name in ('code_target_filter', 'learn_review_filter'):
            if name in receipt:
                proof = receipt[name]
                require(type(proof) is dict and proof.get('retained_counts') != dict(NEW=0, REHEARSAL=0),
                    'target_filter_zero_update_authorization_required')
    return False
