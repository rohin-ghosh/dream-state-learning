"""Bind named CPU results to the immutable caption candidate, not to admission."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = ['TESTS_LOCAL_V2.txt', 'TESTS_NODE_V2.txt', 'TESTS_FOCUSED_VALID_V2.txt',
        'TESTS_FOCUSED_V2.txt', 'ORIGINAL_BASELINE_FAILURE.txt', 'COMMITTED_BINARY_VERIFIED.json',
        'ACTUAL_CPU_V2.json', 'STAGED_V2.json', 'test_caption_tail.py', 'node_probe.py', 'verify_saved.py',
        'stage_and_probe.py', 'prepare.py', 'caption_tail_runtime.py', 'fetch_original.py']
    for name, count in [('TESTS_LOCAL_V2.txt', 23), ('TESTS_NODE_V2.txt', 23),
            ('TESTS_FOCUSED_VALID_V2.txt', 126)]:
        text = (HERE / name).read_text()
        if f'Ran {count} tests' not in text or not text.rstrip().endswith('OK'):
            raise ValueError('required_CPU_test_failed:' + name)
    actual = json.loads((HERE / 'ACTUAL_CPU_V2.json').read_bytes())
    if actual['returncode'] != 0 or not actual['result']['passed']:
        raise ValueError('actual_saved_checkpoint_probe_failed')
    manifest = json.loads((HERE / 'prepared_v2/MANIFEST.json').read_bytes())
    receipt = dict(schema='CAPTION_NAMED_CPU_PROVENANCE_V1', passed=True,
        scope='non_material_original_source_checkpoint_tail_reader_only_not_full_suite_or_admission',
        recorded_utc=datetime.now(timezone.utc).isoformat(), source=manifest['source'],
        source_pins=manifest['source_pins'], delta=manifest['delta'],
        source_manifest_sha256=sha(HERE / 'prepared_v2/MANIFEST.json'),
        candidate_plan_sha256=sha(HERE / 'prepared_v2/PLAN_CANDIDATE.json'),
        files={name:sha(HERE / name) for name in files},
        tests=dict(worker_local=23, worker_node2=23, focused_original_closure=126),
        known_issues=[dict(test='test_r227_caption.R227CaptionTests.test_only_caption_slots_and_no_filter_configuration',
            status='fails_identically_in_unchanged_original_node2_source',
            reason='obsolete_five_slot_topology_assertion_not_caption_node2_mapping'),
            dict(test='test_ny_caption_life', status='not_collected_in_system_python',
                reason='pytest_not_installed_in_VM_system_python')],
        native_launches=0, native_signals=[], model_loaded=False, journal_writes=0,
        fresh_admission=False, native_namespace_verified=False, launch_ready=False)
    with (HERE / 'CPU_TEST_RECEIPT.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
    print(json.dumps(dict(passed=True, receipt_sha256=sha(HERE / 'CPU_TEST_RECEIPT.json'),
        source_manifest_sha256=receipt['source_manifest_sha256'], candidate_plan_sha256=receipt['candidate_plan_sha256'])))


if __name__ == '__main__':
    main()
