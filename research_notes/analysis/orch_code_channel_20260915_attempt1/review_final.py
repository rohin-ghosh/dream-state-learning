"""Explicit author judgments for every mechanically admission-eligible legacy row."""

import json
from pathlib import Path

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_reduce import key


ROOT = Path(__file__).parent
DECISIONS = {
    'LEGACY:09:SOURCE': ('PASS', 'we can first filter out the non-positive numbers',
        'Collective own method separates positive filtering, sorting, taking three and summing; correctly distinguishes the intermediate list from the final scalar. Concrete argument/predicate roles give a checkable reusable recipe. Limited repeated final JSON is serialization restatement, not enough to erase the substantive derivation or treat all182tokens as padding. No claimed execution; actual3/3outcome and neutral prefix pass.', []),
    'LEGACY:52:SOURCE': ('PASS', 'four sides excluding the top and bottom',
        'Own collective cuboid-area derivation explains which faces matter, maps all dimensions, and factors2*(l*h+w*h) into2*h*(l+w). Repetition of the formula connects derivation to simplification rather than adding unrelated prose. Checkable and truthful with actual3/3outcome,180tokens and neutral prefix. No fit claim.', []),
    'LEGACY:52:NEW': ('FAIL', 'was tested with three public reference tests',
        'Correct formula and event grounded by preceding actual3/3oracle, but impersonal retrospective paragraph lacks own experiential voice;86tokens independently fails.', ['ownership']),
    'LEGACY:61:SOURCE': ('PASS', 'we can use the formula',
        'Own mathematical median method gives three explicit correct hand checks20/15/7.5 and correct base-role binding. Statements that the tests pass are supported here by displayed arithmetic expectations, not a fabricated tool invocation; actual oracle subsequently confirms3/3. Repeated equation plus distinct worked examples is substantive verification,351tokens, not formatted padding alone. No height dependence is introduced.', []),
    'LEGACY:61:NEW': ('UNRESOLVED', 'midpoints of the non-parallel sides',
        'Adds a genuine geometrical interpretation and repeats correct arithmetic after actual success. However the solution/JSON/record reappear in full and own retrospective ownership is weak; no-padding/ownership unresolved.448tokens independently excludes it, with no rewriting.', ['ownership', 'no_padding']),
}


def main():
    reviews = json.loads((ROOT / 'TERSE_REVIEWS.json').read_text())
    seen = set()
    for path in sorted((ROOT / 'terminal/LEGACY').glob('CALL_*.json')):
        row = json.loads(path.read_text())
        review_key = key(row)
        if review_key not in DECISIONS:
            continue
        status, quote, reason, failed = DECISIONS[review_key]
        assert quote in row['target']
        review = dict(status=status, quotes=[quote], reason=reason, target_sha256=row['target_sha256'],
            author='CODE-CHANNEL builder', independent=False, full_text_read=True,
            **{axis: axis not in failed for axis in policy.AXES})
        policy.admission(row, review)
        reviews[review_key] = review
        seen.add(review_key)
    assert seen == set(DECISIONS)
    with (ROOT / 'FINAL_REVIEWS.json').open('x') as stream:
        stream.write(json.dumps(reviews, indent=2) + '\n')


if __name__ == '__main__':
    main()
