"""Author full-text judgments, not an independent reader or keyword classifier."""

import json
from pathlib import Path


ROOT = Path('research_notes/analysis/orch_code_bounded_20260914_attempt1')
JUDGMENTS = {
    'shard0/CALL_003.json': ('FAIL', 'Volume = (Base * Height of Triangle * Length of Prism) / 2',
        'Correct formula and named-argument mapping, but only87tokens/73rationale. Generic collective we is not a developed own evidence/check account; no concrete example check.'),
    'shard0/CALL_004.json': ('FAIL', 'The solution was verified with three test cases, and all passed.',
        'Actual preceding oracle did pass3/3: derivation and event claim are grounded. Nonetheless92tokens, record-only JSON and no first-person rationale before action fail the frozen rich contract.'),
    'shard0/CALL_007.json': ('FAIL', 'preventing potential errors or exceeding the allowed AST steps',
        'Describes the extraction expression, but JSON is first rather than final line and oracle never executed it. Bounds statement overstates what min alone ensures.123tokens and impersonal account fail.'),
    'shard0/CALL_008.json': ('FAIL', 'This prevents potential errors such as accessing an index that does not exist',
        'Misdiagnoses actual JSON parse feedback as an indexing problem, changes filtering without evidence, and repeats JSON-first format.136tokens; no grounded correction or own evidence account.'),
    'shard0/CALL_009.json': ('UNRESOLVED', 'The error message "Expecting value: line 1 column 1 (char 0)" suggests that the JSON format is incorrect.',
        'Only rich row meeting total/rationale token bounds. It correctly identifies parser feedback and moves a repeated JSON expression to final line, yielding3/3. However generic Let us/Let\'s wording, duplicated action and retained irrelevant index filtering leave substantive own-voice/no-padding admission unresolved. This is serialization recovery, not a demonstrated algorithmic correction; do not promote.'),
    'shard0/CALL_010.json': ('FAIL', 'if the index is valid',
        'Accurately records the conditional extraction used, but119tokens and no own rationale before action. Filtering invalid/negative indices is an added behavior, not evidence of general MBPP correctness. No concrete worked check or reusable diagnosis of the actual JSON failure.'),
    'shard1/CALL_001.json': ('FAIL', '4*a',
        'Correct square perimeter expression, only6tokens and no articulated reasoning/check. Oracle success is not rich admission.'),
    'shard1/CALL_002.json': ('FAIL', 'perimeter_expression_is_4_times_side_length',
        'Mathematically accurate terse mnemonic,13tokens; no own evidence, applicability explanation or worked check.'),
    'shard1/CALL_005.json': ('FAIL', 'min(xs)',
        'Correct expression using exact function parameter xs,7tokens and no explanation. No alias repair was performed.'),
    'shard1/CALL_006.json': ('FAIL', 'smallest_num = lambda xs: min(xs)',
        'Accurate function mnemonic as inert record text,14tokens. Lambda is not executed and is unsupported as a future action; no own reasoning/check or rich length.'),
    'shard2/CALL_003.json': ('FAIL', '[n*i for i in range(1, m+1)]',
        'Correct m positive-index multiples of n,18tokens. Child gives only action with no explanatory evidence or check.'),
    'shard2/CALL_004.json': ('FAIL', 'successfully generates a list of m multiples of n.',
        'Statement is supported by actual3/3tests and expression, but28tokens and no personal account, condition or concrete check.'),
    'shard2/CALL_008.json': ('FAIL', 'sum(x for x in lst if x == True)',
        'Mathematically plausible boolean sum but unsupported GeneratorExp, explicitly rejected on selected task.15tokens, no reasoning or expectation. Count as native failure, not eligibility exclusion.'),
    'shard2/CALL_009.json': ('FAIL', 'This should meet the constraints and pass the provided tests.',
        'Repeats generator syntax despite actual unsupported-GeneratorExp feedback, then puts prose after JSON. Claimed constraint compliance contradicts provided interpreter feedback.87tokens and impersonal prose.'),
    'shard2/CALL_010.json': ('FAIL', 'Oracle feedback: {"success": true, "passed": 3, "total": 3, "error": ""}',
        'Child fabricates successful oracle feedback, falsely asserts tests pass, retains unsupported generator and emits record instead of requested expression.178tokens alone cannot admit hallucinated evidence; no executed success or actual lesson opportunity exists.'),
    'shard3/CALL_001.json': ('FAIL', 'n * (n + 1)',
        'Correct rectangular-number formula and3/3outcome, but60tokens/48rationale with generic we, not developed own evidence/check. Positive task gap does not imply rich target yield.'),
    'shard3/CALL_002.json': ('FAIL', 'the product of two consecutive integers',
        'Mathematical lesson content is correct, assessed independently of solved task. Raw JSON contains invalid backslash escapes and is rejected;71tokens, no first-person rationale. Do not repair or relabel usable.'),
    'shard3/CALL_006.json': ('FAIL', 'tuple(list(test_tup) + test_list)',
        'Correct ordered concatenation through tuple/list conversion,14tokens. No substantive evidence/relevance/check account.'),
    'shard3/CALL_007.json': ('FAIL', 'converting the tuple to a list, appending the list, and then converting it back to a tuple.',
        'Record broadly describes successful concatenation; appending the list is imprecise versus extending by elements, so no stronger unseen-behavior guarantee.48tokens, no own rationale or concrete check; fails rich admission regardless of solution.'),
}


def main():
    reviews = {}
    for row_id, (status, span, reason) in JUDGMENTS.items():
        row = json.loads((ROOT / 'terminal_verified' / row_id).read_text())
        assert span in row['target']
        reviews[row_id] = dict(status=status, evidence_spans=[span], reason=reason,
                              target_sha256=row['target_sha256'], reviewer='CODE-BOUNDED author',
                              independent=False, full_text_read=True)
    rich_rows = [path for path in (ROOT / 'terminal_verified').glob('shard*/CALL_*.json')
                 if json.loads(path.read_text())['arm'] == 'rich']
    assert len(reviews) == len(rich_rows) == 19
    (ROOT / 'SEMANTIC_REVIEW.json').write_text(json.dumps(reviews, indent=2) + '\n')


if __name__ == '__main__':
    main()
