import copy
import datetime
import json
from pathlib import Path
import sys

from gpu import astra_semantic_train_probe as probe
from gpu.astra_mini_sudoku_diagnostic import check_free

attempt, root_index, controller, device = sys.argv[1:]
root = Path.home() / f'astra_diagnostics/astra_semantic_exact_train_20260912_attempt{attempt}/root{root_index}'
assert (root / 'COMPLETED.json').is_file() and not (root / 'FAILED.json').exists()
assert not Path('/proc', controller).exists()
out, manifest, evidence, requests = probe.verify_probe(root)
tokenizer = probe.diagnostic.w0.load_local_tokenizer(manifest['runtime_config'])
held = probe.held_generation_summary(Path(manifest['original']), evidence, int(root_index), tokenizer)
report = probe.reduce_records(requests, probe.collect_records(root, manifest['states']), tokenizer, evidence['adapters'], held)
report.update(root_index=int(root_index), original_label=evidence['original_report']['label'],
    original_gates=copy.deepcopy(evidence['original_report']['gates']),
    original_report_sha256=manifest['original_report_sha256'], gate_evaluation='not rerun or replaced')
assert report == probe.read(root / 'supplementary_report.json')
assert probe.file_hash(root / 'supplementary_report.json') == probe.read(root / 'COMPLETED.json')['report_sha256']
cleanups = list(root.glob('*.cleanup.json'))
assert len(cleanups) == 3
for path in cleanups:
    cleanup = probe.read(path)
    assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
gpu, xml = check_free(device)
probe.write(root, 'MAIN_TERMINAL_AUDIT.json', dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='NATIVE_EXACT_TRAIN_REPLAY_AND_RELEASE_PASS', native_reduction_equal=True,
    controller_absent=True, cleanup_count=3, report_sha256=probe.file_hash(root / 'supplementary_report.json'),
    gpu=gpu, xml=xml, released=True))
print(json.dumps(dict(status='NATIVE_EXACT_TRAIN_REPLAY_AND_RELEASE_PASS', root_index=root_index,
    report_sha256=probe.file_hash(root / 'supplementary_report.json'))))
