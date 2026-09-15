"""Explicit author judgments after reading the remaining56 separated full texts."""

import json
from pathlib import Path

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_reduce import key


ROOT = Path(__file__).parent
DECISIONS = {
    8: ('FAIL', '3n^2 - 3n + 1', 'Correct centered-hexagonal formula but impersonal. Unsupported power is a separate action failure.', ['ownership']),
    9: ('FAIL', 'take the sum of the first three', 'Action returns a sorted list when at least three positives exist, contradicting the stated sum; public tests all exercise that branch.', ['grounding', 'truthful', 'reusable']),
    10: ('FAIL', 'min([x for x in range(n)', 'Uses min while claiming maximum; names n instead of declared N and unsupported keyword default. Wrong even apart from formatting.', ['grounding', 'truthful', 'reusable']),
    11: ('FAIL', 'ensures that the solution adheres to the constraints', 'Generator expression is unsupported; claims constraint compliance without checking the stated list-comprehension restriction.', ['grounding', 'truthful']),
    12: ('FAIL', 'The correct formula is 2 * pi * diameter * height', 'Only159tokens but geometry explanation contradicts itself and all fixed perimeter tests. Claim of needing math module is outside the grammar. Length is not substantive correctness.', ['grounding', 'truthful', 'reusable']),
    13: ('PASS', 'I can use list slicing', 'Own precise split-and-concatenate relation moves the last element first. Correct argument binding and no claimed test execution; short and malformed separately.', []),
    14: ('PASS', 'We can use this formula', 'Own collective mathematical method gives correct hexagonal formula with explicit n binding; checkable without invented run.', []),
    15: ('PASS', 'I can use a list comprehension', 'Own method directly maps each sublist to its first item using declared lst; a checkable reusable relation, not an outcome claim.', []),
    16: ('FAIL', '3.141592653589793', 'Circumference concept is sound, but chosen pi does not ground the exact published expectations based on3.1415. Tests stay unchanged; do not call that absent reasoning.', ['grounding']),
    17: ('PASS', 'difference between each pair of adjacent elements is exactly 1', 'Own precise sorted-adjacency criterion handles shown gaps and duplicates. Generator syntax independently fails the restricted interpreter.', []),
    18: ('PASS', 'We can find the x-coordinate', 'Own vertex method derives x then y with correct mathematical parameter binding. Power syntax and exact floating expectations are separate outcome constraints.', []),
    19: ('PASS', 'I will use the `nums` argument', 'Own grounded maximum-plus-minimum computation with explicit array binding and expectation; no invented result. Envelope and84tokens fail separately.', []),
    20: ('PASS', 'we simply add the lengths', 'Collective own mathematical step maps all three side roles and gives a checkable correct sum.64tokens independently fails.', []),
    21: ('PASS', 'I will pass the test_tup', 'Own explanation correctly connects iterable sum to the declared tuple; checkable and reusable, no invented execution.', []),
    22: ('FAIL', 'This formula is derived', 'Correct mathematical focus relation stated impersonally, not a developed own account. Power and JSON formatting fail separately.', ['ownership']),
    23: ('FAIL', 'line in 3D space', 'Conflates a planar line equation with3D and normal/direction vectors; action compares C as well as slopes and indexes missing third coefficients.162tokens cannot rescue false reasoning.', ['grounding', 'truthful', 'reusable']),
    24: ('FAIL', '(b - a - 1) + 1 = b - a', 'Incorrect interior-point count adds back a removed boundary, yielding9rather than4 on the first test. Degenerate test tension remains unchanged.', ['grounding', 'truthful', 'reusable']),
    25: ('FAIL', 'using n-1 as the step', 'Narrative gives n-1 but action correctly uses n. Correct proposed payload does not repair false explanatory step.', ['truthful']),
    26: ('FAIL', '2 * 3.141592653589793 * r * h', 'Sound lateral-area formula but pi precision fails the supplied exact3.1415-based values; no evidence addressing that contract.', ['grounding']),
    27: ('FAIL', 'split the array `a` at index `n`', 'Declared n is full length in all tests; rotation split must use k. Grounded argument binding fails.', ['grounding', 'truthful', 'reusable']),
    28: ('PASS', 'we need to raise the length', 'Own mathematical cube-volume relation and side role are correct. Unsupported exponentiation is an independent action-language failure, not false mathematics.', []),
    29: ('PASS', 'I can use the `tuple` function', 'Own constructor rationale maps listx to all its elements in a tuple, correct and checkable.48tokens fails separately.', []),
    30: ('UNRESOLVED', 'temporary variable', 'Correct tuple payload and own swap proposal, but describes a temporary variable while displaying simultaneous assignment with no temporary. Explanatory truthfulness unresolved;58tokens fails anyway.', ['truthful']),
    31: ('PASS', 'subtract the smallest from the largest', 'Own task-specific max/min relation has correct direction and declared nums binding; truthful and reusable.', []),
    32: ('FAIL', 'four side faces', 'Correct geometrical derivation is impersonal rather than own experiential voice. Power syntax fails separately.', ['ownership']),
    33: ('FAIL', 'list1[:k-1]', 'Correct one-based idea but invents variable k instead of declared L. No alias repair allowed; available argument evidence ignored.', ['grounding']),
    34: ('PASS', 'I can generate a list of the first n odd numbers', 'Own correct odd-number enumeration and squaring/summing relation, no fabricated outcome. Unsupported power syntax independently fails.', []),
    35: ('PASS', 'I can use a list comprehension to extract the nth element', 'Own exact column-extraction then maximum operation, correct N/test_list binding and checkable relation.', []),
    36: ('FAIL', 'such as the one a child may make with sticks', 'Formula is correct but impersonal illustrative account; no owned proposal or evidence. Narrative imagery is not sufficient ownership.', ['ownership']),
    37: ('PASS', 'reverse the portion of the array up to the given position', 'Own correct prefix-reversal plus unchanged suffix. Existing bounded reversed helper returns a list, so no assumption of unrestricted Python needed.', []),
    38: ('FAIL', '3.14159', 'Correct cylinder-volume concept but approximation does not match supplied exact3.1415-based expectations. Outcome contract preserved.', ['grounding']),
    39: ('PASS', 'I can use indexing', 'Own precise first/last index roles and tuple payload grounded in test_tup; no invented result.', []),
    40: ('PASS', 'I will use this formula', 'Own mathematically correct decagonal relation. Power unsupported at action gate, independently of semantic content.', []),
    41: ('PASS', 'it adds the elements from both lists at that index', 'Own correct indexwise addition on the supplied equal-length lists; action uses minimum length rather than explicit first-list length, so no unequal-length generalization is inferred.', []),
    42: ('PASS', 'I will implement this formula', 'Own correct explicit sum-of-even-squares formula, checkable against2/3/4 without invented execution.84tokens and envelope fail separately.', []),
    43: ('FAIL', 'from the specified position \'n\'', 'Narrative/action do not implement fixed right-rotation tests; generator produces nested combined slices, swaps parameter roles and uses unsupported destructuring/generator semantics.', ['grounding', 'truthful', 'reusable']),
    44: ('PASS', 'I will propose a solution and check it', 'Own floor-quotient proposal with exact n/m roles; future check not invented success.62tokens fails separately.', []),
    45: ('PASS', 'I can do this by using the len function', 'Own relation between outer list length and count of component lists matches provided inputs; checkable, truthful, and not merely heading compliance.', []),
    46: ('PASS', 'we can use the formula', 'Own collective AP-sum relation explicitly maps a/n/d, correct formula and no invented execution.', []),
    47: ('FAIL', 'If all tuples match, the lists are identical', 'Checks only shared prefix via minimum length yet claims full identity; can accept unequal lists. Generator syntax unsupported. Correct exposed cases would not validate that broad explanation.', ['truthful', 'reusable']),
    48: ('PASS', 'We can directly use this formula', 'Own mathematical AP nth-term method maps each named role and gives correct checkable relation.', []),
    49: ('FAIL', 'list_index[:] if len(list_index) <= 256', 'For the bounded inputs action returns indices rather than selected values, contradicting its own stated mapping to nums.', ['grounding', 'truthful', 'reusable']),
    50: ('PASS', 'we can use the fact that the sum of the angles', 'Own triangle-angle sum and subtraction with correct argument roles, truthful reusable relation.', []),
    51: ('FAIL', 'Since the input is a singleton tuple', 'Assumes prose type against all visible list-valued tests; list(xs[0]) attempts to iterate a scalar. Preserved description/test mismatch, no test relaxation.', ['grounding', 'truthful', 'reusable']),
    52: ('PASS', 'We can use the given dimensions', 'Own four-side cuboid-area explanation binds l/w/h correctly; checkable relation, not invented history.', []),
    53: ('PASS', 'check if all elements of the sublist are within the range', 'Own all-elements range criterion and min/max payload agree for supplied nonempty lists, correct endpoint roles including original spelling rigthrange.', []),
    54: ('PASS', 'we need to multiply its length, width, and height', 'Own correct three-dimensional volume relation with explicit roles and no fabricated check.', []),
    55: ('FAIL', 'length of the tuple divided by the chunk size', 'Narration describes a divided range with chunk-size step while actual correct action ranges over full length; substantive explanatory mismatch despite good final payload.', ['truthful']),
    56: ('FAIL', 'round the result', 'General nearest-multiple idea is understandable but no tie rule addresses219/2 expecting218; Python round gives220. Published expectations remain unchanged.', ['grounding']),
    57: ('PASS', 'I need to sum all the elements', 'Own correct average decomposition into sum and count, mapped to lst, no invented execution.', []),
    58: ('PASS', 'we need to calculate the area of all six faces', 'Own geometrical derivation of cuboid surface area names all pairwise products correctly; grounded and checkable.', []),
    59: ('UNRESOLVED', 'into a nested tuple', 'Payload correctly concatenates flat tuples as tests expect, but calls that nested. Original prose also says nested; explanatory precision unresolved,57tokens independently fails.', ['truthful']),
    60: ('FAIL', 'we assume it is 0', 'Invents focal distance zero and vertical directrix for a vertical-axis parabola. Wrong geometry even before anomalous fixed reference expectations; no test change.', ['grounding', 'truthful', 'reusable']),
    61: ('FAIL', 'The median of a trapezium is the average', 'Correct median formula and explicit base roles but impersonal account lacking owned evidence/method.', ['ownership']),
    62: ('PASS', 'we can use the modulo operator', 'Own modulo10 method is correct on supplied positive integers and checkable. No claim of negative-input correctness is admitted.', []),
    63: ('PASS', 'we need to use the formula 6 * l^2', 'Own cube-surface relation explains the side role and uses allowed multiplication in the action.67tokens independently fails.', []),
}


def main():
    reviews = json.loads((ROOT / 'PANEL_REVIEWS.json').read_text())
    for path in sorted((ROOT / 'interim1/SEPARATED').glob('CALL_*.json')):
        row = json.loads(path.read_text())
        if row['position'] < 8:
            continue
        status, quote, reason, failed = DECISIONS[row['position']]
        assert quote in row['target']
        review = dict(status=status, quotes=[quote], reason=reason, target_sha256=row['target_sha256'],
            author='CODE-CHANNEL builder', independent=False, full_text_read=True,
            **{axis: axis not in failed for axis in policy.AXES})
        policy.admission(row, review)
        reviews[key(row)] = review
    assert set(DECISIONS) == set(range(8, 64))
    with (ROOT / 'SEPARATED_REVIEWS.json').open('x') as stream:
        stream.write(json.dumps(reviews, indent=2) + '\n')


if __name__ == '__main__':
    main()
