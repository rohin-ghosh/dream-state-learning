"""Preserve the failed manifest; bind measured real-tail bytes in a new CPU candidate."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys


CONTROL = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T142337Z')
TAIL_BYTES = 335798634
TAIL_RECORDS = 79
NEW_BOUND = 512 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def manifest_delta(original, revised):
    expected = deepcopy(original)
    require(expected['selection']['max_tail_bytes'] == 128 * 1024 * 1024, 'original_manifest_limit')
    expected['selection']['max_tail_bytes'] = NEW_BOUND
    require(revised == expected, 'only_measured_tail_byte_budget_changed')


def main():
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524
        and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'original_CPU_node')
    checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

    def write(name, document):
        path = CONTROL / name
        with path.open('x') as output:
            json.dump(document, output, sort_keys=True, indent=2)
            output.flush()
            os.fsync(output.fileno())
        descriptor = os.open(CONTROL, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return dict(path=str(path), sha256=checksum(path))

    old_path = CONTROL / 'STARTUP_MANIFEST.json'
    require(checksum(old_path) == 'f5b35e1c56a90be711e35bdbd64265ee450ad9ed002a3567468da80ccdfc2d38',
        'preserved_original_manifest_bytes')
    failure = json.loads((CONTROL / 'ACTUAL_JOURNAL_CPU_FAILED.json').read_bytes())
    require(failure['error'] == 'checkpoint_tail_byte_bound_exceeded', 'exact_read_only_failure')
    original = json.loads(old_path.read_bytes())
    guard = json.loads((CONTROL / 'GUARD_CANDIDATE.json').read_bytes())
    raw = Path(guard['copy_raw'])
    records = raw / 'stream/records'
    names = sorted(path.name for path in records.iterdir())
    require(names[-1] == f'{9555:020d}.json' and len(names) == 2 * 9556,
        'same_exact_records_no_new_intents')
    tail = [(records / f'{number:020d}.json').stat().st_size for number in range(9477, 9556)]
    require(len(tail) == TAIL_RECORDS and sum(tail) == TAIL_BYTES, 'fresh_measured_tail_same')
    require(NEW_BOUND - TAIL_BYTES >= 2 * max(tail) + 16 * 1024 * 1024,
        'bounded_space_for_completion_and_recipe_receipts')
    revised = deepcopy(original)
    revised['selection']['max_tail_bytes'] = NEW_BOUND
    manifest_delta(original, revised)
    sys.path.insert(0, original['staged_source_root'])
    import math_b_startup as startup
    startup.validate_manifest(revised, (CONTROL / 'PLAN.json').read_bytes())
    manifest_pin = write('STARTUP_MANIFEST_TAIL_BYTES_V2.json', revised)
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(),
        status='MEASURED_TAIL_BUDGET_CANDIDATE_NOT_LAUNCH_AUTHORIZATION',
        old_manifest=dict(path=str(old_path), sha256=checksum(old_path)), new_manifest=manifest_pin,
        measured_tail_records=len(tail), measured_tail_bytes=sum(tail),
        old_bound=original['selection']['max_tail_bytes'], new_bound=NEW_BOUND,
        same_record_count_bound=True, same_complete_head_rows_and_runtime=True,
        old_failure_preserved=True, native_or_GPU_launch_performed=False)
    write('TAIL_BYTES_MANIFEST_V2_PROVENANCE.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
