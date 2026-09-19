"""Read-only receipt refresh independent of slow or throttled provider calls."""

import json
import os
from pathlib import Path
import time

from recover import HERE, atomic, remote, save, utc


def refresh():
    os.umask(0o077)
    baseline = json.loads((HERE / 'BINDINGS.json').read_bytes())
    first_turns = json.loads((HERE / 'FIRST_TURNS.json').read_bytes())
    proof = remote(dict(mode='receipts', bindings=baseline['bindings'],
        publishers=baseline['publishers'], first_turns=first_turns))
    if proof['helper_sha256'] != baseline['helper_sha256']:
        raise ValueError('original_node_helpers_required_for_receipt_verification')
    proof['audited_utc'] = utc()
    save(HERE / 'receipt_history' / (str(time.time_ns()) + '.json'), proof)
    for row in proof['receipts']:
        path = HERE / 'first_verified' / (row['life'] + '.json')
        if row['state'] == 'ACT_CHAIN_VERIFIED' and not path.exists():
            save(path, dict(audited_utc=proof['audited_utc'], binding=baseline['bindings'][row['life']],
                first_relative=first_turns[row['life']], receipt=row))
    atomic(HERE / 'AUDIT_LATEST.json', proof)
    summary = dict(utc=proof['audited_utc'], rows=[dict(life=row['life'],
        state=row['state'], parent_id=row.get('parent_id'), published_utc=row.get('published_utc'),
        INBOX=(row.get('delivery') or {}).get('INBOX'),
        REQUEST=(row.get('delivery') or {}).get('REQUEST'),
        ACT_chain=row.get('actual_ACT_after_parent')) for row in proof['receipts']],
        task_uptake_established=False, native_signals=0, math_parent_changes=0)
    print(json.dumps(summary, indent=2))
    return proof


if __name__ == '__main__':
    refresh()
