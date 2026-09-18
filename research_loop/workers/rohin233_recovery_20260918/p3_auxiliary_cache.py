"""Select an existing correction-cache receipt at a completed recovery boundary."""

import hashlib
import json


def select_cache(records, complete):
    if complete['kind'] != 'SLEEP_COMPLETE' or complete['document']['status'] != 'COMPLETE':
        raise ValueError('completed_boundary_required')
    candidates = [record for record in records if record['kind'] == 'R197_CORRECTION_CYCLE'
        and record['index'] < complete['index']]
    if not candidates:
        raise ValueError('no_bound_historical_correction_state')
    selected = max(candidates, key=lambda record: record['index'])
    canonical = json.dumps({key: value for key, value in selected.items() if key != 'sha256'},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != selected['sha256']:
        raise ValueError('historical_correction_record_hash')
    cycles = selected['document']['ledger']['cycles']
    if not cycles or max(item['cycle'] for item in cycles) > complete['document']['cycle']:
        raise ValueError('no_correction_from_later_cycle')
    return dict(record_index=selected['index'], record_sha256=selected['sha256'])
