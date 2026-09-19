"""Bind unchanged receiving tests and actual read-only state proof to the new manifest."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys


CONTROL = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T142337Z')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524
        and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'original_node_CPU_only')

    def pin(path):
        return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

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
        return pin(path)

    original = json.loads((CONTROL / 'STAGED_READY_FOR_MAIN.json').read_bytes())
    source = Path(original['source'])
    sys.path.insert(0, str(source))
    from pending_sleep_contract import digest
    import math_b_startup as startup
    current = {str(path.relative_to(source)): pin(path)['sha256'] for path in source.rglob('*.py')}
    require(current == original['source_pins'] and digest(current) == original['source_pins_sha256'],
        'same_exact_204_source_closure')
    manifest_path = CONTROL / 'STARTUP_MANIFEST_TAIL_BYTES_V2.json'
    manifest = json.loads(manifest_path.read_bytes())
    startup.validate_manifest(manifest, (CONTROL / 'PLAN.json').read_bytes())
    proof_path = CONTROL / 'ACTUAL_JOURNAL_CPU_V3_VERIFIED.json'
    proof = json.loads(proof_path.read_bytes())
    require(proof['status'] == 'ACTUAL_READ_ONLY_CHECKPOINT_TAIL_STATE_VERIFIED_NO_NATIVE'
        and proof['record_count'] == 9556 and proof['pending_rows'] == 3
        and proof['rows'] == 580 and proof['sleep_frontier'] == 577
        and proof['startup_manifest'] == pin(manifest_path)
        and proof['source_pins_sha256'] == original['source_pins_sha256'], 'actual_proof_current_manifest')
    cpu = json.loads((CONTROL / 'RECEIVING_CPU.json').read_bytes())
    require(cpu['passed'] is True and cpu['source_pins'] == current, 'prior_52_receiving_tests_same_source')
    cpu.update(startup_manifest=pin(manifest_path),
        prior_receiving_cpu=pin(CONTROL / 'RECEIVING_CPU.json'), actual_journal_cpu=pin(proof_path),
        actual_journal_cpu_summary=dict(records=9556, rows=580, pending_rows=3, sleep_frontier=577,
            tail_records=79, tail_bytes=335798634, raw_record_bytes_hashed=28196897216,
            seconds=proof['elapsed_seconds']),
        tail_budget_provenance=pin(CONTROL / 'TAIL_BYTES_MANIFEST_V2_PROVENANCE.json'),
        host_inbox_mapping_proof=pin(CONTROL / 'ACTUAL_JOURNAL_HOST_INBOX_MAPPING_REPAIR.json'),
        original_tests_reused_without_runtime_code_change=True,
        supplemented_utc=datetime.now(timezone.utc).isoformat())
    cpu_pin = write('RECEIVING_CPU_V2.json', cpu)
    allocation = json.loads((CONTROL / 'ALLOCATION_CANDIDATE.json').read_bytes())
    require(allocation['builder_entry_logged'] is False, 'do_not_claim_builder_manifest_amendment')
    allocation.update(cpu_receipt_path=cpu_pin['path'], cpu_receipt_sha256=cpu_pin['sha256'])
    allocation_pin = write('ALLOCATION_CANDIDATE_V2.json', allocation)
    guard = json.loads((CONTROL / 'GUARD_CANDIDATE.json').read_bytes())
    guard.update(pending_sleep_recovery=pin(manifest_path), allocation_path=allocation_pin['path'],
        allocation_sha256=allocation_pin['sha256'])
    guard_pin = write('GUARD_CANDIDATE_V2.json', guard)
    receipt = {key: value for key, value in original.items() if key not in ('source_pins', 'CPU_log_tail')}
    receipt.update(status='ACTUAL_STATE_AND_RECEIVING_CPU_PASS_NEW_MANIFEST_AWAITING_MAIN_BINDING',
        utc=datetime.now(timezone.utc).isoformat(), startup_manifest=pin(manifest_path),
        receiving_cpu=cpu_pin, candidate_guard=guard_pin, candidate_allocation=allocation_pin,
        actual_journal_cpu=pin(proof_path), actual_journal_cpu_summary=cpu['actual_journal_cpu_summary'],
        prior_receipt=pin(CONTROL / 'STAGED_READY_FOR_MAIN.json'),
        admission_blocker='Main14:31 Builder binds old128MiB manifest; revised512MiB exact manifest needs explicit binding',
        original_allocation_gate_unchanged=True,
        owner_available_bytes=os.statvfs(CONTROL).f_bavail * os.statvfs(CONTROL).f_frsize)
    write('STAGED_READY_FOR_MAIN_V2.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
