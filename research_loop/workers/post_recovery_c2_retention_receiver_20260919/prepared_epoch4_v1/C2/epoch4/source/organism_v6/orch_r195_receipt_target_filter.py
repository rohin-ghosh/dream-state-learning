"""Conservative exclusions tied to actual attempt receipts, not semantic truth."""

import hashlib
import re

from gpu.orch_r197_correction_ledger import _execution_check


POLICY = 'R195_RECEIPT_BOUND_TARGET_FILTER_V1'
CLAIM = re.compile(r'\b(?:result|output|solution|calculation)\b[^\n.!?]{0,100}?'
    r'\b(?:is|was|were|returned|produced|showed|printed|gave|gives)\b'
    r'[^\n.!?]{0,80}?\d', re.IGNORECASE)
CAUTION = re.compile(r'\b(?:no|not|never|unverified|unknown|expect\w*|hypothes\w*|'
    r'might|should|would|could|possib\w*|if|cannot|conjectur\w*|assum\w*)\b', re.IGNORECASE)


def unsupported_claims(text):
    findings = []
    for line in text.splitlines():
        if line.lstrip().startswith(('>', '```', '~~~')) or CAUTION.search(line):
            continue
        match = CLAIM.search(line)
        if match:
            findings.append(match.group(0))
    return findings


def receipt_exclusions(rows):
    by_source = {row['source_sha256']: row for row in rows}
    excluded, checks = [], []
    for review in rows:
        for evidence in review.get('learn_review_evidence', []):
            act = by_source.get(evidence.get('act_source_sha256'))
            if act is None or act['segment'] >= review['segment']:
                checks.append(dict(review_source_sha256=review['source_sha256'],
                    status='UNKNOWN', reason='no_prior_pending_attempt'))
                continue
            outcome = evidence.get('outcome')
            if type(outcome) is not dict:
                checks.append(dict(review_source_sha256=review['source_sha256'],
                    status='UNKNOWN', reason='no_actual_outcome'))
                continue
            reference = evidence.get('response_origin')
            if type(reference) is not dict or type(reference.get('record_sha256')) is not str:
                checks.append(dict(review_source_sha256=review['source_sha256'],
                    status='UNKNOWN', reason='no_bound_response_origin'))
                continue
            check = _execution_check(outcome, act['target'], dict(response=reference))
            checks.append(dict(review_source_sha256=review['source_sha256'],
                act_source_sha256=act['source_sha256'], check=check))
            if check['provenance'] != 'MATCHED_SUPPLIED_RECEIPT':
                continue
            targets = []
            if check['import_error'] == 'YES':
                targets.append((act, 'actual_receipt_import_error', []))
            result = outcome['result']
            if (check['execution_failure'] == 'NO' and result.get('stdout') == ''
                    and result.get('stderr') == ''):
                claims = unsupported_claims(review['target'])
                if claims:
                    targets.append((review, 'numeric_result_claim_after_empty_output', claims))
            for target, reason, claims in targets:
                excluded.append(dict(source_sha256=target['source_sha256'], segment=target['segment'],
                    cohort='NEW', policy=POLICY, reason=reason,
                    raw_target_sha256=hashlib.sha256(target['target'].encode()).hexdigest(),
                    act_source_sha256=act['source_sha256'], review_source_sha256=review['source_sha256'],
                    result_sha256=outcome['result_sha256'], matched_claims=claims,
                    semantic_falsehood_claimed=False))
    return dict(policy=POLICY, excluded=excluded, checks=checks,
        claim_scope='BOUNDED_ENGLISH_NUMERIC_RESULT_PATTERNS_NOT_GENERAL_FACT_CHECKING',
        raw_modified=False, targets_normalized=False)
