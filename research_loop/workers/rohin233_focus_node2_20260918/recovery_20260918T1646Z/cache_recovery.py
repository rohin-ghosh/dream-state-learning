"""Restore only a stopped life's derived correction pointer to its saved boundary."""

import argparse
import os
from pathlib import Path
import json

from observe import checked, header
from recover import absent, locations, read, require, sha, write
from r226_correction_boundary import select_cache


def inspect_cache(name):
    absent(name)
    root, _, control, preserved = locations(name)
    require((control / 'RECOVERY_APPENDED.json').is_file() and not (control / 'DISPATCHED.json').exists(),
        'reconciled_but_not_dispatched_native')
    recovery = read(control / 'RECOVERY.json')
    complete = checked(Path(recovery['complete_path']))
    require(complete['sha256'] == recovery['complete_sha256'], 'same_completed_recovery_boundary')
    directory = root / 'raw/stream/records'
    records = [checked(path) for path in directory.glob('[0-9]' * 20 + '.json')
        if int(path.stem) < complete['index'] and header(path)['kind'] == 'R197_CORRECTION_CYCLE']
    after = select_cache(records, complete)
    cache = root / 'raw/stream/correction_ledger.json'
    require(sha(cache) == sha(preserved / 'stream/correction_ledger.json'), 'same_preserved_original_cache')
    return dict(arm=name, before=read(cache), after=after, before_sha256=sha(cache),
        completed_record_index=complete['index'], completed_record_sha256=complete['sha256'],
        historical_records_modified=False, reset_to_empty=False, cache_only=True,
        old_cache_preserved=True, native_not_dispatched=True, source_selector_sha256=sha(Path(__file__).with_name('r226_correction_boundary.py')))


def apply(name, expected):
    require(expected and len(expected) == 64, 'exact_tested_cache_receipt_required')
    root, _, control, _ = locations(name)
    path = control / 'CACHE_CHECK.json'
    require(sha(path) == expected, 'published_cache_check_receipt')
    candidate = inspect_cache(name)
    require(candidate == read(path), 'unchanged_verified_cache_and_complete_record')
    temporary = root / 'raw/stream/correction_ledger.r233.tmp'
    write(temporary, candidate['after'])
    os.replace(temporary, root / 'raw/stream/correction_ledger.json')
    write(control / 'CACHE_RESTORED.json', dict(check_sha256=expected,
        after_sha256=sha(root / 'raw/stream/correction_ledger.json'), historical_records_modified=False,
        learner_signals=0, previous_pointer_preserved=True))
    print(json.dumps(dict(arm=name, status='SAVED_BOUNDARY_CACHE_RESTORED', receipt_sha256=sha(control / 'CACHE_RESTORED.json'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('check', 'apply'))
    parser.add_argument('name', choices=('ASTRA7', 'CAPTION'))
    parser.add_argument('--receipt-sha256')
    arguments = parser.parse_args()
    if arguments.action == 'check':
        receipt = inspect_cache(arguments.name)
        path = locations(arguments.name)[2] / 'CACHE_CHECK.json'
        write(path, receipt)
        print(json.dumps(dict(receipt=receipt, receipt_sha256=sha(path)), indent=2))
    else:
        apply(arguments.name, arguments.receipt_sha256)
