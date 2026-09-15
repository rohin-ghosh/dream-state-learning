"""Explicit scope of87 action-only full texts read in three author review blocks."""

import json
from pathlib import Path

from gpu.orch_code_channel_reduce import key


ROOT = Path(__file__).parent
SOURCE_POSITIONS_READ = set(range(8, 64))
NEW_POSITIONS_READ = {11, 12, 14, 15, 19, 20, 21, 26, 27, 28, 29, 30, 31, 32,
                      37, 39, 44, 45, 46, 48, 49, 50, 51, 54, 55, 57, 58, 59, 61, 62, 63}


def main():
    reviews = json.loads((ROOT / 'SEPARATED_REVIEWS.json').read_text())
    seen = set()
    for path in sorted((ROOT / 'interim1/TERSE').glob('CALL_*.json')):
        row = json.loads(path.read_text())
        if row['position'] < 8:
            continue
        allowed = SOURCE_POSITIONS_READ if row['kind'] == 'SOURCE' else NEW_POSITIONS_READ
        assert row['position'] in allowed
        seen.add((row['position'], row['kind']))
        reviews[key(row)] = dict(status='FAIL', quotes=[row['target']],
            reason='Author read this entire literal action/record in the positions8–27,28–45,46–63 review blocks. It contains only a formula, expression, function mnemonic or JSON fields; no own explanatory evidence account or articulated checkable expectation. A successful action is not a substantive own record. No regex or token-count rule used to infer a semantic PASS. Truthfulness of absent explanatory claims is not separately adjudicated.',
            target_sha256=row['target_sha256'], author='CODE-CHANNEL builder', independent=False,
            full_text_read=True, ownership=False, grounding=False, checkable=False,
            truthful=None, no_padding=True, reusable=False)
    assert seen == {(position, 'SOURCE') for position in SOURCE_POSITIONS_READ} | {
        (position, 'NEW') for position in NEW_POSITIONS_READ}
    with (ROOT / 'TERSE_REVIEWS.json').open('x') as stream:
        stream.write(json.dumps(reviews, indent=2) + '\n')


if __name__ == '__main__':
    main()
