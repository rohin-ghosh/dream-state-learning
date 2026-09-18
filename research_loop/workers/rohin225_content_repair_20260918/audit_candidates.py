"""Compare prospective policy evidence without modifying historical targets."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_r213_content_target_filter as legacy
from organism_v6 import orch_r225_content_target_filter as repaired


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    records = []
    for path in args.inputs:
        payload = path.read_bytes()
        document = json.loads(payload)
        cycles = document['cycles'] if 'cycles' in document else [document]
        for cycle in cycles:
            for entry in cycle['rows']:
                row = entry['row']
                actual_updates = entry['actual_update_count'] if 'actual_update_count' in entry else entry['actual_updates']
                if type(actual_updates) is not int or actual_updates < 0:
                    raise ValueError('actual_nonnegative_update_count_required')
                original = legacy.scan_target(row['target'], row.get('token_ids'))
                proposed = repaired.scan_target(row['target'], row.get('token_ids'))
                records.append(dict(cycle=cycle['cycle'], segment=row['segment'],
                    source_sha256=row['source_sha256'],
                    raw_target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                    audit_input_sha256=hashlib.sha256(payload).hexdigest(),
                    actual_updates=actual_updates,
                    legacy_eligible=original['eligible'],
                    legacy_classification=original['classification'],
                    prospective_eligible=proposed['eligible'],
                    prospective_classification=proposed['classification']))
    output = dict(schema='R225_PROSPECTIVE_CONTENT_AUDIT_V1',
        observed_utc=datetime.now(timezone.utc).isoformat(),
        legacy_policy=legacy.POLICY, prospective_policy=repaired.POLICY,
        history_modified=False, deployed=False, raw_text_included=False,
        correctness_verified=False, rows=records)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(output=str(args.output), candidates=len(records),
        previously_trained_now_excluded=[dict(cycle=row['cycle'], segment=row['segment'],
            actual_updates=row['actual_updates']) for row in records
            if row['actual_updates'] and not row['prospective_eligible']])))


if __name__ == '__main__':
    main()
