"""Read actual pinned journal/state on CPU; publish receipts only in unique staging."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


CONTROL = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T142337Z')
MANIFEST_NAME = 'STARTUP_MANIFEST_TAIL_BYTES_V2.json'
RECEIPT_PREFIX = 'ACTUAL_JOURNAL_CPU_V3'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(4 * 1024 * 1024):
            result.update(block)
    return result.hexdigest()


def write_receipt(name, document):
    with (CONTROL / name).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(CONTROL, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def verify_pins(source, expected, digest):
    require(not source.is_symlink() and source.resolve() == source, 'unredirected_staged_source')
    current = {}
    for path in source.rglob('*.py'):
        require(not path.is_symlink() and path.resolve().is_relative_to(source), 'regular_source_paths')
        current[str(path.relative_to(source))] = checksum(path)
    require(current == expected['source_pins'], 'exact_source_closure_unchanged')
    require(digest(current) == expected['source_pins_sha256'], 'same_source_closure_digest')
    return current


def assert_no_compute(query):
    require(query.returncode == 0, 'GPU_census_must_succeed')
    require(not query.stdout.strip(), 'native_present_do_not_open_journal')


def readonly_class(base, logical_inbox=None):
    class ReadOnlyJournal(base):
        def _scan(self):
            if logical_inbox is not None:
                self.inbox = logical_inbox
            return super()._scan()

        def _publish(self, *args, **kwargs):
            raise ValueError('read_only_proof_no_publication')

        def record(self, *args, **kwargs):
            raise ValueError('read_only_proof_no_record')

    return ReadOnlyJournal


def main():
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524
        and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'original_node_CPU_only')
    expected = json.loads((CONTROL / 'STAGED_READY_FOR_MAIN.json').read_bytes())
    require(expected['source_pins_sha256'] == '617cc5da47436fecf521cea0ed45cab09e65bc2634aa3d2a166a194011a2395e',
        'reviewed_source_only')
    for name in ('plan', 'startup_manifest', 'receiving_cpu', 'candidate_guard'):
        require(checksum(Path(expected[name]['path'])) == expected[name]['sha256'], 'unchanged_' + name)
    source = Path(expected['source'])
    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    verify_pins(source, expected, digest)
    query = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,process_name',
        '--format=csv,noheader'], capture_output=True, text=True, timeout=20)
    assert_no_compute(query)
    sys.path.insert(0, str(source))
    import math_b_startup as startup
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    plan_bytes = (CONTROL / 'PLAN.json').read_bytes()
    manifest = json.loads((CONTROL / MANIFEST_NAME).read_bytes())
    expected_manifest = json.loads((CONTROL / 'STARTUP_MANIFEST.json').read_bytes())
    expected_manifest['selection']['max_tail_bytes'] = 512 * 1024 * 1024
    require(manifest == expected_manifest, 'only_measured_tail_byte_budget_revision')
    unused, plan, envelope, selection = startup.validate_manifest(manifest, plan_bytes)
    original_guard = json.loads((CONTROL / 'ORIGINAL_GUARD.json').read_bytes())
    raw = Path(original_guard['copy_raw'])
    require(raw.parent.name == 'r213_math_b_fork' and raw.name == 'raw'
        and raw.resolve() == raw, 'original_host_raw_only')
    original_selection = deepcopy(selection)
    selection['root'] = str(raw / 'stream')
    require(original_selection['root'] == str(Path(plan['root']) / 'stream'), 'original_guest_mapping')
    journal_class = readonly_class(startup.make_journal_class(StreamJournal, selection),
        Path(original_selection['root']) / 'inbox')
    contract = envelope['candidate']['contract']['contract']
    started = time.monotonic()
    write_receipt(RECEIPT_PREFIX + '_STARTED.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        pid=os.getpid(), source_pins_sha256=expected['source_pins_sha256'], source=str(source),
        host_root=selection['root'], guest_root=original_selection['root'],
        mapping_only_for_read_only_host_CPU_test=True, model_or_GPU_launch=False,
        inbox_path_comparison_uses_original_guest_path=True,
        inbox_reads_use_original_host_directory_descriptor=True))
    with journal_class(raw / 'stream', create=False) as journal:
        receipt = deepcopy(journal.checkpoint_tail_receipt)
        signatures = deepcopy(journal._record_signatures)
        require(receipt['record_count'] == contract['old_head']['index'] + 1
            and receipt['head_sha256'] == contract['old_head']['sha256'], 'actual_exact_old_head')
        require(journal.latest_checkpoint() == dict(document=contract['preserved_state'],
            expected_sha256=contract['preserved_state']['sha256']), 'actual_exact_pending_state')
        restored = ContinualStream.restore(contract['preserved_state'],
            expected_sha256=contract['preserved_state']['sha256'])
        require(restored.checkpoint() == contract['preserved_state'], 'actual_lossless_stream_restore')
        require([row['source_sha256'] for row in restored.pending_rows()]
            == contract['pending_row_sha256'], 'every_pending_row_retained')
        require(journal._record_snapshot() == signatures, 'original_journal_unmodified')
        receipt.update(pending_rows=len(restored.pending_rows()), rows=len(restored.rows),
            sleep_frontier=restored.sleep_frontier,
            preserved_state_sha256=contract['preserved_state']['sha256'])
    verify_pins(source, expected, digest)
    require(not ('torch' in sys.modules and sys.modules['torch'].cuda.is_initialized()),
        'no_CUDA_initialization')
    receipt.update(status='ACTUAL_READ_ONLY_CHECKPOINT_TAIL_STATE_VERIFIED_NO_NATIVE',
        utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started,
        source_pins_sha256=expected['source_pins_sha256'], source=str(source),
        mapping_only_for_read_only_host_CPU_test=True, original_guest_root=original_selection['root'],
        original_host_root=selection['root'], native_or_GPU_launch_performed=False,
        original_plan_and_manifest_unchanged=True, original_journal_writes_performed=False,
        pending_sleep_not_executed=True,
        startup_manifest=dict(path=str(CONTROL / MANIFEST_NAME), sha256=checksum(CONTROL / MANIFEST_NAME)))
    write_receipt(RECEIPT_PREFIX + '_VERIFIED.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        write_receipt(RECEIPT_PREFIX + '_FAILED.json', dict(utc=datetime.now(timezone.utc).isoformat(),
            error_type=type(error).__name__, error=str(error), automatic_retry=False,
            native_or_GPU_launch_performed=False))
        raise
