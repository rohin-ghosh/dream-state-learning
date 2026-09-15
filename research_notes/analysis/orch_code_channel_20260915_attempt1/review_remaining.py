"""Final71 legacy judgments, after eight bounded full-text reading blocks."""

import json
from pathlib import Path

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_reduce import key


ROOT = Path(__file__).parent
BARE = {'10:SOURCE', '11:SOURCE', '15:SOURCE', '17:SOURCE', '19:SOURCE', '21:SOURCE',
        '21:NEW', '28:SOURCE', '29:SOURCE', '29:NEW', '31:SOURCE', '35:SOURCE',
        '37:SOURCE', '37:NEW', '39:SOURCE', '45:SOURCE', '56:SOURCE', '59:SOURCE',
        '59:NEW', '62:SOURCE'}
DECISIONS = {
    '08:SOURCE': ('PASS', 'the expression should return 271', 'Own correct centered-hexagonal method and explicit271/7/217predictions; no invented run. Unsupported power and final-line formatting remain separate failures.', []),
    '09:NEW': ('PASS', 'we first filter out non-positive numbers', 'Own correct success-conditioned recipe, including fewer-than-three-positive applicability.93tokens fails independently.', []),
    '10:NEW': ('FAIL', 'this edge case is not applicable', 'Contradictorily excludes N=1 because N>0; fabricated constraint inference, impersonal account.', ['ownership', 'grounding', 'truthful']),
    '11:NEW': ('FAIL', 'I used list comprehension', 'Own voice and true test-pass history, but actual source used list repetition, not a comprehension. Historical method claim is false.', ['truthful']),
    '12:SOURCE': ('FAIL', 'The values are close enough', 'Claims20.566≈12,10.283≈6,20.850≈8 and invents test success. Wrong geometry plus593tokens of invalid validation; no tolerance relaxation.', ['grounding', 'truthful', 'reusable']),
    '13:SOURCE': ('FAIL', 'then appends the last element to the front', 'Actual expression reverses prefix and appends last element at end; explanation and expected rotation false.', ['grounding', 'truthful', 'reusable']),
    '14:SOURCE': ('PASS', 'we can use the formula for hexagonal numbers', 'Own correct n(2n-1)method with correct190/45/91expectations, stated future checks rather than invented execution. Registered JSON-last-line fails.', []),
    '15:NEW': ('FAIL', 'Extracted the first element', 'True result-grounded method but impersonal retrospective fragment, not meaningful own voice;39tokens independently fails.', ['ownership']),
    '16:SOURCE': ('FAIL', 'expected circumference is approximately', 'Correct geometric idea but treats exact3.1415-based assertions as approximate while choosing different pi; lacks contract-grounded validation.', ['grounding']),
    '18:SOURCE': ('PASS', 'we use the formula for the x-coordinate', 'Own detailed correct vertex substitution and algebra; supported mathematical reasoning despite unsupported Pow in the final action.', []),
    '19:NEW': ('FAIL', 'The solution was verified with three test cases', 'Test-success statement is actually grounded; method correct, but impersonal report without own experiential voice.', ['ownership']),
    '20:SOURCE': ('PASS', 'we simply add the lengths of its three sides', 'Own correct perimeter relation maps a/b/c and proposes a future test.122tokens and formatting fail separately.', []),
    '22:SOURCE': ('PASS', 'The y-coordinate of the focus', 'Own correct focus-from-vertex derivation, with explicit checkable coordinates and no invented result; action power/format remain separate.', []),
    '23:SOURCE': ('FAIL', 'a1 * b2 == a2 * b1', 'Proportional-normal idea is valid, but final action uses temporaries never available in the expression scope; sample assignments are not allowed compilation. Fails grounded argument binding.', ['grounding']),
    '24:SOURCE': ('FAIL', '16 - 9 = 4', 'Wrong corners/interior reinterpretation and demonstrably false arithmetic; claims corrected success despite wrong values.965tokens intensify error rather than provide usable grounding.', ['grounding', 'truthful', 'reusable']),
    '25:SOURCE': ('FAIL', 'positions that are multiples of n', 'Remainder-one condition is not the described multiples condition; enumerate/destructuring unsupported and JSON not last. No faithful contract-grounded explanation.', ['grounding', 'truthful']),
    '26:SOURCE': ('FAIL', '3.141592653589793', 'Sound geometric formula but selected pi yields314.159265 rather than exact314.150000expected. Original tests unchanged.', ['grounding']),
    '27:SOURCE': ('FAIL', 'unused `k` argument', 'Explicitly assigns split size to n and discards k despite all tests showing k as split. Claims correctness without valid substitution.', ['grounding', 'truthful', 'reusable']),
    '28:NEW': ('FAIL', 'This solution passed all public reference tests', 'Real success and correct cube-volume explanation, but impersonal record;59tokens fails separately.', ['ownership']),
    '30:SOURCE': ('FAIL', '(a + b, a + b - b)', 'Converts sequential arithmetic swap into a wrong pure expression; first output becomes sum not b. Claimed reference assertions are false; unearned record emitted.', ['grounding', 'truthful', 'reusable']),
    '31:NEW': ('FAIL', 'Successfully implemented a solution', 'Correct expression and true success but impersonal status report, no own experiential account.', ['ownership']),
    '32:SOURCE': ('PASS', 'we need to calculate the area of four of its faces', 'Own correct lateral-area derivation and allowed multiplication mapped to l.144tokens and final prose independently fail.', []),
    '33:SOURCE': ('FAIL', 'list1[:k-1] + list1[k:]', 'Own one-based removal idea is sensible, but ignores declared argument L and invents k; no hardcoded alias repair.', ['grounding']),
    '34:SOURCE': ('FAIL', '4n^2 - 4n - 3', 'Correct final odd-square formula and numeric examples cannot repair false intermediate factorization and a non-equivalent transition in steps9–11.964tokens is not reliable reasoning by length.', ['truthful', 'reusable']),
    '36:SOURCE': ('PASS', '36 + 1 = 37', 'Own correct star-number decomposition and37/73/121worked checks. Final trailing prose prevents execution; reasoning itself remains valid.', []),
    '38:SOURCE': ('FAIL', 'approximately 1570.75', 'Correct cylinder-volume method but different pi treated as if exact public expectations were approximate. No valid check of the actual expression.', ['grounding']),
    '39:NEW': ('FAIL', '"relevance"', 'Structured relevance/expectation/lesson fields provide impersonal explanation, not own experiential account. Wrong record grammar independently fails; labels do not establish ownership.', ['ownership']),
    '40:SOURCE': ('FAIL', 'It meets the requirements', 'Decagonal arithmetic checks are correct, but asserts constraint compliance while using explicitly unsupported power. Correct mathematical substeps are preserved, not admitted.', ['grounding', 'truthful']),
    '41:SOURCE': ('FAIL', 'This solution meets the constraints', 'Zip and destructuring are outside the frozen language; asserts compliance without grounding. Stated future tests do not fix that false claim.', ['grounding', 'truthful']),
    '42:SOURCE': ('PASS', 'The expression evaluates to 56', 'Own correct even-square formula plus20/56/120hand checks, no false arithmetic.462tokens and closing code fence fail separately; not erased as absence of reasoning.', []),
    '43:SOURCE': ('FAIL', 'reverses the concatenated list to achieve the right rotation', 'Reversal does not produce the stated rotation; slicing/modulo expression yields wrong content. No grounded validation of the claimed method.', ['grounding', 'truthful', 'reusable']),
    '44:SOURCE': ('PASS', 'we can use the integer division operator', 'Own floor-quotient method and explicit3/2/4hand expectations are correct. Trailing lesson text violates final JSON rule, without invalidating the mathematical account.', []),
    '45:NEW': ('PASS', 'I used the built-in len()', 'Actual own method, correct outer-list-count relation, and true prior success.60tokens independently fails rich admission.', []),
    '46:SOURCE': ('PASS', 'we can use the formula for the sum of an AP', 'Own correct formula and a/n/d role mapping;114tokens independently excludes this successful source.', []),
    '46:NEW': ('FAIL', 'the expression is', 'Correct AP recipe but impersonal explanation without owned history;72tokens fails independently.', ['ownership']),
    '47:SOURCE': ('FAIL', 'passes the provided tests', 'Unsupported zip/generator plus unearned source-time record and success statement. Shared-prefix equality also does not guarantee whole-list identity.', ['grounding', 'truthful', 'reusable']),
    '48:SOURCE': ('PASS', 'we can directly substitute these into the formula', 'Own correct AP nth-term method, all argument roles bound.147tokens and trailing prose independently fail.', []),
    '49:SOURCE': ('FAIL', 'This list comprehension iterates', 'Correct element-access explanation but entirely impersonal, no own plan or experiential voice;58tokens and trailing prose also fail.', ['ownership']),
    '50:SOURCE': ('PASS', 'we can use the fact that the sum of the angles', 'Own correct angle-sum relation mapped to given a/b; actual oracle succeeds but79tokens fails independently.', []),
    '50:NEW': ('FAIL', 'The solution is verified to be correct', 'Actual success and correct mathematical relation, but impersonal recap rather than own record voice.', ['ownership']),
    '51:SOURCE': ('FAIL', 'extract the single element from the tuple', 'Follows misleading problem prose instead of list-valued reference inputs; list(xs[0]) attempts scalar iteration. Original task/test ambiguity preserved.', ['grounding', 'truthful']),
    '53:SOURCE': ('FAIL', 'if any element', 'Any-within predicate includes partly out-of-range sublists that tests exclude; claimed test2outcome silently omits such a list. Incorrect evidence evaluation plus unsupported generator.', ['grounding', 'truthful', 'reusable']),
    '54:SOURCE': ('PASS', 'we need to multiply its length', 'Own correct cuboid-volume decomposition with explicit dimensions; true outcome but88tokens fails independently.', []),
    '54:NEW': ('FAIL', 'This solution was tested with three public reference tests', 'Correct method and actual pass history but impersonal record;61tokens fails independently.', ['ownership']),
    '55:SOURCE': ('FAIL', 'If it fails, we will revise', 'Correct chunking method and conditional checks, but most added text copies original assertions without working an additional check. No-padding not satisfied; source JSON also first not last.', ['no_padding']),
    '57:SOURCE': ('PASS', 'we need to sum all the elements', 'Own correct sum/count average and declared lst binding;80tokens fails independently despite actual success.', []),
    '57:NEW': ('PASS', 'we sum all the elements', 'Own correct reusable average rule, truthful in its actual successful source history. Short recap is a record, not an added target rewrite;104tokens fails independently.', []),
    '58:SOURCE': ('PASS', '2 \\times 143 = 286', 'Own correct opposite-face pairing and all three22/286/1350hand checks.475tokens and final closing fence exclude it; mathematics remains supported.', []),
    '60:SOURCE': ('FAIL', 'The correct formula for the directrix', 'Incorrect directrix formula for y=ax²+bx+c, then reasserts it after mismatched fixed tests. Some arithmetic is internally evaluated but wrong geometry and unsupported power remain;1008tokens not reliability.', ['grounding', 'truthful', 'reusable']),
    '62:NEW': ('FAIL', 'works for all integers', 'Impersonal record overgeneralizes last digit to negative inputs without discussing sign conventions; exact positive tests do not support universal scope.', ['ownership', 'grounding']),
    '63:SOURCE': ('PASS', 'we need to use the formula', 'Own correct six-face area relation and side binding, with future rather than fabricated checks. Unsupported power/format and114tokens fail independently.', []),
}


def main():
    reviews = json.loads((ROOT / 'FINAL_REVIEWS.json').read_text())
    rows = json.loads((ROOT / 'final_reviewed/ROWS.json').read_text())
    seen = set()
    for row in rows:
        if row['semantic_status'] != 'UNREVIEWED':
            continue
        short = f"{row['position']:02}:{row['kind']}"
        assert row['arm'] == 'LEGACY'
        if short in BARE:
            review = dict(status='FAIL', quotes=[row['target']],
                reason='Entire literal action/mnemonic read in the eight bounded legacy review blocks. No substantive own explanatory evidence account or articulated expectation; execution success alone cannot supply those missing child words.',
                ownership=False, grounding=False, checkable=False, truthful=None, no_padding=True, reusable=False)
        else:
            status, quote, reason, failed = DECISIONS[short]
            assert quote in row['target'], short
            review = dict(status=status, quotes=[quote], reason=reason,
                          **{axis: axis not in failed for axis in policy.AXES})
        review.update(target_sha256=row['target_sha256'], author='CODE-CHANNEL builder',
                      independent=False, full_text_read=True)
        policy.admission(row, review)
        reviews[key(row)] = review
        seen.add(short)
    assert seen == BARE | set(DECISIONS)
    assert len(reviews) == 250
    with (ROOT / 'COMPLETE_REVIEWS.json').open('x') as stream:
        stream.write(json.dumps(reviews, indent=2) + '\n')


if __name__ == '__main__':
    main()
