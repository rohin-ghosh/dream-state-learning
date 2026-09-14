"""Explicit author full-text judgments; not an independent reader or lexical gate."""

import json
from pathlib import Path


ROOT = Path('research_notes/analysis/orch_base_contract_20260914_attempt1')
DECISIONS = {
    'shard0/CALL_001.json': ('PASS',
        'Inclusive mathematical we/let us accompanies an actual derivation and all three correct numeric test expectations. It distinguishes triangular base area from extrusion length in the final formula; no claimed execution. Substantive reusable computation, not length alone.',
        ['we use the formula', '0.5 * b * h * l', '= 240'], []),
    'shard0/CALL_002.json': ('FAIL',
        'Specific formula and test-pass statement are grounded in its real success, but the impersonal record lacks meaningful own experiential voice. Independently only94tokens; not admitted or expanded.',
        ['The volume of a triangular prism', 'passed all of them'], ['ownership']),
    'shard1/CALL_001.json': ('FAIL',
        'Correct safe action only. No own grounded trace, explanation, check or reusable experiential record;6tokens.',
        ['4*a'], ['ownership', 'grounding', 'checkable', 'reusable']),
    'shard1/CALL_002.json': ('FAIL',
        'A compact true formula label is not an own outcome-linked lesson or checked explanation;13tokens.',
        ['perimeter_expression_is_4_times_side_length'], ['ownership', 'grounding', 'checkable', 'reusable']),
    'shard1/CALL_003.json': ('PASS',
        'Plural we is accepted semantically: identifies requested square perimeter, maps given side a to the appropriate multiplication and states a checkable symbolic expectation. This minimal but specific reasoning is truthful; independently66tokens means range failure.',
        ['we need to multiply', '4 * a'], []),
    'shard1/CALL_004.json': ('FAIL',
        'Grounded formula and truthful reference-test verification, but third-person instruction rather than an own experiential record.57tokens also fails independently.',
        ['This solution was verified', '4 * a'], ['ownership']),
    'shard2/CALL_001.json': ('PASS',
        'Plural we describes a specific row-indexing operation and prospective public checks, without falsely claiming execution. Correct conceptual procedure; however final prose instead of final JSON makes actual safe-parser outcome fail. Successful reasoning is not interface success and this is not admitted.',
        ['we can use a list comprehension', '[row[N] for row in nums]', 'we can use the provided test cases'], []),
    'shard3/CALL_001.json': ('FAIL',
        'Correct bare action has no substantive own reasoning, check or reusable event record;7tokens.',
        ['min(xs)'], ['ownership', 'grounding', 'checkable', 'reusable']),
    'shard3/CALL_002.json': ('FAIL',
        'Lambda snippet in a record string is not a grounded first-person lesson or check. It was never executed as generated Python;14tokens.',
        ['smallest_num = lambda xs: min(xs)'], ['ownership', 'grounding', 'checkable', 'reusable']),
    'shard3/CALL_003.json': ('FAIL',
        'BASE emits the exact same bare min action as ORIGINAL here. No own reasoning, check or reusable event record;7tokens.',
        ['min(xs)'], ['ownership', 'grounding', 'checkable', 'reusable']),
    'shard3/CALL_004.json': ('FAIL',
        'Correct min rule and actual three-test success, but impersonal generic record rather than own experiential voice.70tokens fails separately; generic simple/efficient language is not an admission substitute.',
        ['The function to find the smallest number', 'all of which passed'], ['ownership']),
    'shard0/CALL_003.json': ('PASS',
        'Plural we identifies the triangular base area times prism length and grounds all three argument roles in the proposed expression. Specific checkable mathematical relation, no invented execution;87tokens fails range independently.',
        ['we use the formula', 'Height of Triangle * Length of Prism'], []),
    'shard0/CALL_004.json': ('FAIL',
        'Correct derivation and real test success, but impersonal generic formula description, not an own experiential record;92tokens separately fails.',
        ['The solution was verified with three test cases', 'area of the triangular base'], ['ownership']),
    'shard0/CALL_005.json': ('PASS',
        'Substantive first-person identification and calculation tracks the nested proportions on the right denominator.100 four-leaved then25 purple four-leaved is truthful and checkable;180tokens.',
        ['I identify the given quantities', 'I take 1/4 of the 100 four-leaved clovers', 'FINAL: 25'], []),
    'shard0/CALL_006.json': ('FAIL',
        'Correct grounded calculations and concrete proportion check. However the record is a detached worked-example checklist, not a self-attributed account of the solved experience; headings and284tokens do not establish meaningful first-person ownership. No arithmetic failure alleged.',
        ['Operations:', 'Calculate the number of four-leaved clovers', 'The calculations match the given proportions'], ['ownership']),
    'shard0/CALL_007.json': ('PASS',
        'Plural first-person calculation correctly applies the quarter to the four-leaved subset, a specific grounded reusable operation.124tokens fails range, not reasoning.',
        ['we first calculate', 'one quarter of these four-leaved clovers', 'FINAL: 25'], []),
    'shard0/CALL_008.json': ('PASS',
        'Own retrospective calculation and concrete verification faithfully reproduce the prior successful nested-proportion solution. Substantive I refers to actual arithmetic, not a cosmetic prefix;239tokens and correct final.',
        ['I identified the following quantities', 'I calculated the number of purple four-leaved clovers', 'One quarter of 100 is 25.'], []),
    'shard1/CALL_005.json': ('PASS',
        'Own calculation converts minutes, separates residual distance and residual time, divides to90mph, and verifies both time segments. Correct grounded reusable residual-rate procedure;278tokens.',
        ['I identify the given quantities', '120 miles - 30 miles = 90 miles', 'I check the result:'], []),
    'shard1/CALL_006.json': ('FAIL',
        'Mathematically accurate residual-rate worked example and concrete check, but impersonal procedure/checklist rather than self-attributed own experience.457tokens also exceeds400; no trimming or rewritten admission.',
        ['Required average speed for the remainder of the drive', 'Concrete check:', '0.5 hours + 1 hour = 1.5 hours'], ['ownership']),
    'shard1/CALL_007.json': ('PASS',
        'Own problem decomposition correctly computes30 initial miles,90 remaining miles and1 remaining hour, then verifies the total-time constraint. Specific reusable rate reasoning with actual first-person grounding;251tokens.',
        ['I calculate the distance', 'I check the result:', 'FINAL: 90'], []),
    'shard1/CALL_008.json': ('FAIL',
        'Accurate generic residual-distance/time derivation, but detached instructions rather than own experiential account.474tokens independently exceeds the frozen gate. Formatting and correct arithmetic do not override either requirement.',
        ['Step-by-step solution:', 'Find the required average speed', 'Concrete check:'], ['ownership']),
    'shard2/CALL_002.json': ('FAIL',
        'Actual last-line parser rejects prose after JSON. The explanation is impersonal, not an own grounded trace;123tokens also fails. Do not reparse an earlier line or repair the output to manufacture success.',
        ['[nums[i][N] for i in range(min(len(nums),256))]', 'This expression uses a list comprehension'], ['ownership']),
    'shard2/CALL_003.json': ('PASS',
        'Own sequential arithmetic correctly computes126,136,325 and remaining29pages. It identifies the residual unknown and actual reusable sum-then-subtract operation, with checkable intermediate quantities;231tokens.',
        ['I identify the given quantities', 'I subtract the total pages', '354 (total pages) - 325 (pages read in first three days) = 29 pages'], []),
    'shard2/CALL_004.json': ('FAIL',
        'All arithmetic and the stated check are truthful, but presented as detached imperative operations, not an own outcome-linked account.280tokens alone cannot establish substantive first-person ownership.',
        ['Subtract the total pages read', 'The result matches the problem statement.'], ['ownership']),
    'shard2/CALL_005.json': ('FAIL',
        'Correct third-person retelling of Hallie and arithmetic but no own experiential voice.149tokens is a genuine one-token range failure; no rounding up or appended text.',
        ['On the first day, Hallie read 63 pages.', '354 - 325 = 29 pages'], ['ownership']),
    'shard2/CALL_006.json': ('FAIL',
        'Specific arithmetic and correct354-page sum check, but detached worked-example procedure rather than self-attributed own experience.273tokens and headings are insufficient; no calculation error alleged.',
        ['Calculate the total pages read', '63 (day 1) + 126 (day 2) + 136 (day 3) + 29 (day 4) = 354 pages'], ['ownership']),
    'shard3/CALL_005.json': ('UNRESOLVED',
        'Question wording6 small and medium does not fix the split or unambiguously say6each. Explicit3+3 assumption makes34.5 conditional arithmetic valid but not a uniquely grounded answer; gold rejects it. Retain in denominator without calling this a proven reasoning failure or admitting it.',
        ['Assume 3 apples are small and 3 are medium', 'FINAL: 34.5'], ['ownership', 'grounding']),
    'shard3/CALL_006.json': ('UNRESOLVED',
        'Personal arithmetic is correct under6small AND6medium, but that doubling interpretation is not established by the ambiguous problem wording. Gold45 matches the selected interpretation; checker agreement alone cannot resolve truth. Keep task in8denominator, not admitted.',
        ['6 small apples at $1.5 each', '6 medium apples at $2 each', 'FINAL: 45'], ['grounding']),
    'shard3/CALL_007.json': ('FAIL',
        'The record explicitly notices the unspecified split and computes34.5 for3+3, then changes to6+6 as a purported check and asserts45 must be correct BECAUSE the split is unspecified. This is an invalid conclusion/verification and not an outcome-grounded reusable lesson, despite checker success and377tokens.',
        ["the exact split isn't specified", '4.5 + 6 + 24 = 34.5', 'The correct total cost is indeed $45.'], ['grounding', 'checkable', 'truthful', 'reusable']),
}


def main():
    raw = ROOT / 'terminal'
    paths = sorted(raw.glob('shard*/CALL_*.json'))
    assert {str(path.relative_to(raw)) for path in paths} == set(DECISIONS)
    reviews = {}
    for path in paths:
        key = str(path.relative_to(raw))
        row = json.loads(path.read_text())
        status, reason, quotes, failed = DECISIONS[key]
        assert all(quote in row['target'] for quote in quotes)
        reviews[key] = dict(status=status, reason=reason, quotes=quotes,
            target_sha256=row['target_sha256'], author='BASE-CONTRACT', independent=False,
            **{axis: axis not in failed for axis in ('ownership', 'grounding', 'checkable', 'truthful', 'no_padding', 'reusable')})
    with (ROOT / 'SEMANTIC_REVIEW.json').open('x') as stream:
        stream.write(json.dumps(reviews, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
