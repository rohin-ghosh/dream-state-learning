"""Author's explicit first-eight full-text judgments, never automatic admission."""

import json
from pathlib import Path

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_reduce import key


ROOT = Path(__file__).parent
DECISIONS = {
    'LEGACY:00:SOURCE': ('FAIL', 'base times height', 'Correct argument-to-formula mapping but impersonal; no own evidential account. Independently50tokens.', ['ownership']),
    'LEGACY:00:NEW': ('FAIL', 'passed all public reference tests', 'True success-conditioned fact and usable formula, but no meaningful own voice; independently35tokens.', ['ownership']),
    'LEGACY:01:SOURCE': ('PASS', 'we can use a list comprehension', 'Own collective method maps rows and N to an explicit checkable extraction; public inputs satisfy stated bounds. No invented run. Syntax and length fail independently.', []),
    'LEGACY:02:SOURCE': ('PASS', 'we can use the formula', 'Own mathematical proposal gives the correct octagonal relation and says tests can now be checked rather than inventing execution. Syntax and105tokens fail independently.', []),
    'LEGACY:03:SOURCE': ('FAIL', 'If all these assertions pass', 'Correct filter and conditional rather than invented success, but most of the row reprints the original assertions without deriving an example. No substantive additional check; JSON is first, not last.', ['no_padding']),
    'LEGACY:04:SOURCE': ('FAIL', 'Given the feedback', 'Invents a feedback event; mislists an odd digit among evens, ignores boolean reference expectations, and emits undefined temporaries/unsupported strings. Task prose/test mismatch is retained, not repaired.', ['grounding', 'truthful', 'reusable']),
    'LEGACY:05:SOURCE': ('FAIL', '"record":"Success"', 'Bare expression then unearned success-record; final wrong action key. No own evidence or check; success not yet observed.', ['ownership', 'grounding', 'checkable', 'truthful', 'reusable']),
    'LEGACY:06:SOURCE': ('UNRESOLVED', 'All the tests pass', 'Correct hand-derived35/56/84 and passing final expression, with collective mathematical ownership. Repeated formulas and long test expansions leave no-padding unresolved;679tokens independently fails. Does not prove absent reasoning.', ['no_padding']),
    'LEGACY:06:NEW': ('FAIL', 'This expression was tested', 'Test-success statement is true after3/3actual oracle; correct tetrahedral lesson but impersonal and invalid JSON escape.100tokens independently fails.', ['ownership']),
    'LEGACY:07:SOURCE': ('FAIL', 'ensuring the rotation wraps around correctly', 'Proposed modulo fix does not implement claimed wraparound, has wrong precedence and fails the first fixed test. No grounded validation of the altered expression.', ['grounding', 'truthful', 'reusable']),
    'SEPARATED:00:SOURCE': ('FAIL', 'The area of a parallelogram', 'Correct method but impersonal;53tokens and inline ACTION is not the frozen final JSON grammar.', ['ownership']),
    'SEPARATED:01:SOURCE': ('PASS', 'I can use a list comprehension', 'Own explanation maps rows and N to a checkable extraction with valid-index condition; truthful and reusable.67tokens and inline ACTION independently fail.', []),
    'SEPARATED:02:SOURCE': ('PASS', 'I will use this formula', 'Own correct octagonal formula agrees with the algebraically equivalent expression; no invented outcome.50tokens and inline ACTION fail independently.', []),
    'SEPARATED:03:SOURCE': ('PASS', 'I will use a list comprehension', 'Own filter proposal names both lists and specifies exact exclusion behavior, a grounded reusable checkable relation.69tokens and inline ACTION fail independently.', []),
    'SEPARATED:04:SOURCE': ('FAIL', 'classify it as even or odd', 'Narrative classifies digit values while action uses position parity; unsupported lambda/enumerate/map/strings. Boolean test mismatch is not resolved. No accepted semantics or grounded check.', ['grounding', 'truthful', 'reusable']),
    'SEPARATED:05:SOURCE': ('PASS', 'include it in the result if its length is not equal to K', 'Own task-specific filter, exact arguments and checkable applicability; no invented result.74tokens and inline ACTION fail independently.', []),
    'SEPARATED:06:SOURCE': ('PASS', 'we can use the formula T(n)', 'Collective mathematical method connects tetrahedral and triangular numbers with a correct explicit relation, no claimed execution.89tokens and inline ACTION fail independently.', []),
    'SEPARATED:07:SOURCE': ('FAIL', 'rotate the first n items', 'Adds a second rotation unsupported by fixed tests; actual slicing recombines the prefix rather than doing the described rotation. Task description and tests also diverge; no repair allowed.', ['grounding', 'truthful', 'reusable']),
    'TERSE:00:SOURCE': ('FAIL', 'b*h', 'Correct bare action, no own explanation, evidence or expectation.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:00:NEW': ('FAIL', 'b*h', 'Bare expression record after real success; no own experiential lesson.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:01:SOURCE': ('FAIL', 'nums[i][N]', 'Correct bare indexed extraction, no own evidential explanation.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:01:NEW': ('FAIL', 'nums[i][N]', 'Repeats successful expression as record, without a substantive lesson.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:02:SOURCE': ('FAIL', 'n*(3*n-2)', 'Correct bare octagonal expression but no own method/evidence account.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:02:NEW': ('FAIL', 'def is_octagonal', 'Inert function mnemonic is not executed; lacks own evidence or learned lesson.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:03:SOURCE': ('FAIL', 'x not in list2', 'Correct filtering action only; no substantive ownership/evidence.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:03:NEW': ('FAIL', 'x not in list2', 'Copies successful action into record without own account.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:04:SOURCE': ('FAIL', 'map(int,str(n))', 'Unsupported calls; no own account and fixed boolean outcome not achieved.', ['ownership', 'grounding', 'checkable', 'truthful', 'reusable']),
    'TERSE:05:SOURCE': ('FAIL', 'len(t) != K', 'Correct bare filter but no own evidence or check.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:05:NEW': ('FAIL', 'len(t) != K', 'Successful expression copied as record, no substantive own lesson.', ['ownership', 'grounding', 'checkable', 'reusable']),
    'TERSE:06:SOURCE': ('FAIL', 'sum([int(i*(i+1)*(i+2)/6)', 'Sums tetrahedral rather than triangular values, yielding70not35 for5. No rationale/check.', ['ownership', 'grounding', 'checkable', 'truthful', 'reusable']),
    'TERSE:07:SOURCE': ('FAIL', '*[0]+list1', 'Prepends zeros rather than required slice combination and fails first test. No rationale/check.', ['ownership', 'grounding', 'checkable', 'truthful', 'reusable']),
}


def main():
    reviews = {}
    for arm in policy.ARMS:
        for path in sorted((ROOT / 'panel1' / arm).glob('CALL_*.json')):
            row = json.loads(path.read_text())
            if row['position'] >= 8:
                raise ValueError('first_eight_only')
            review_key = key(row)
            status, quote, reason, failed_axes = DECISIONS[review_key]
            assert quote in row['target']
            review = dict(status=status, quotes=[quote], reason=reason, target_sha256=row['target_sha256'],
                author='CODE-CHANNEL builder', independent=False, full_text_read=True,
                **{axis: axis not in failed_axes for axis in policy.AXES})
            policy.admission(row, review)
            reviews[review_key] = review
    assert set(reviews) == set(DECISIONS)
    with (ROOT / 'PANEL_REVIEWS.json').open('x') as stream:
        stream.write(json.dumps(reviews, indent=2) + '\n')


if __name__ == '__main__':
    main()
