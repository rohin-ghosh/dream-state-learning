"""Bounded64-call FULL-checkpoint activation diagnostic; native raw stays on A100.

Uses the published paired runner unchanged. FULL means the continually trained
child at Laplace's first matched terminal seam after08:00, never training-OFF.
CLI phases: prepare, launch, run, reduce. No BASE rerun, training or parents.
prepare binds a single <=1800second lifetime; failed launches/calls never retry.
"""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_combined_l1_continual_run as continual
from gpu import orch_r107_capability_run as paired
from gpu import orch_r107_capability_reduce as paired_reduce
from gpu import orch_r107_capability_base as encoding
from organism_v6 import orch_combined_l1_continual as state
from organism_v6 import orch_r107_capability as policy


EXPERIMENT = 'R107_CONTINUAL_CAPABILITY_V1'
SOURCE_ROOT = Path(__file__).resolve().parents[1]
SEAM_PATH = continual.ROOT / 'R107_CONTINUATION_20260915/READOUT_SEAM.json'
TRAIN_CUTOFF = datetime(2026, 9, 15, 8, tzinfo=timezone.utc).timestamp()
GPU_UUID = continual.DEVICES[0]
REQUIRED_SOURCES = (
    'gpu/orch_r107_continual_capability_run.py',
    'tests/test_orch_r107_continual_capability.py',
    'gpu/orch_r107_capability_run.py', 'gpu/orch_r107_capability_reduce.py',
    'gpu/orch_r107_capability_base.py', 'gpu/orch_rich_intensity_screen.py',
    'gpu/orch_combined_l1_continual_run.py', 'gpu/orch_rich_hot_a100_minor_scan.py',
    'gpu/orch_rich_hot_a100_scan.py', 'gpu/orch_math_replication_guard.py',
    'organism_v6/orch_r107_capability.py', 'organism_v6/orch_guided_bridge.py',
    'organism_v6/orch_combined_l1_continual.py',
)
read, sha, write = paired.read, paired.sha, state.atomic_json
host_identity = continual.minor_scan.pinned.host_identity


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checkpoint_binding(seam_path=SEAM_PATH):
    seam_path = Path(seam_path)
    require(seam_path == SEAM_PATH, 'exact_laplace_seam_required')
    seam = read(seam_path)
    require(seam['time_unix'] >= TRAIN_CUTOFF and seam['update'] > 6628,
            'post_cutoff_final_seam_required')
    checkpoints = {}
    for arm in ('FULL', 'OFF'):
        directory = Path(seam['checkpoint_paths'][arm])
        require(directory == continual.ROOT / arm / 'checkpoints' / f'{seam["update"]:09d}',
                'exact_matched_checkpoint_path')
        checkpoints[arm] = state.verify_checkpoint(directory)
    full, off = [checkpoints[arm]['metadata'] for arm in ('FULL', 'OFF')]
    require(state.pair_boundary(full, off) == seam['update'], 'matched_final_boundary_required')
    identity = paired.bridge.AdapterIdentity.from_document(full['adapter']).verify()
    require(identity.base_sha256 == paired.BASE_SHA and
            Path(identity.path) == Path(seam['checkpoint_paths']['FULL']) / 'adapter',
            'full_child_only_not_training_off')
    return dict(seam_path=str(seam_path), seam_sha256=sha(seam_path), update=seam['update'],
        checkpoint_paths=seam['checkpoint_paths'],
        commit_sha256={arm: sha(Path(path) / 'COMMIT.json') for arm, path in seam['checkpoint_paths'].items()},
        adapter=identity.document(), corpus_sha256=full['corpus_sha256'],
        corpus_version=full['corpus_version'], training_source_sha256=full['source_sha256'],
        selection='FIRST_MATCHED_TERMINAL_SEAM_AFTER_0800_NO_SCORE_SELECTION')


def validate(plan, now):
    paired.validate_plan(plan, SOURCE_ROOT, now)
    require(plan['experiment'] == EXPERIMENT, 'wrong_experiment')
    require(plan['suite_sha256'] == policy.digest(policy.tasks()) == encoding.SUITE_SHA,
            'fixed32_suite_changed')
    require(type(plan['max_new_tokens']) is int and plan['max_new_tokens'] == 512
            and plan['task_count'] == 32 and plan['call_cap'] == 64, 'fixed64_512_cap')
    require(not plan.get('retained_calls') and 'prior_root' not in plan
            and 'new_call_cap' not in plan, 'fresh64_no_retry_or_retention')
    require(plan['physical_index'] == 0 and plan['gpu_uuid'] == GPU_UUID, 'a100_physical0_only')
    require(plan['lifetime_started_unix'] <= now and
            0 < plan['hard_deadline_unix'] - plan['lifetime_started_unix'] <= 1800
            and plan['gpu_hours_cap'] == 0.5, 'one_global_30minute_lifetime')
    require(plan['base_calls'] == 0 and plan['checkpoint']['adapter'] == plan['adapter'],
            'full_checkpoint_no_base_rerun')
    require(set(REQUIRED_SOURCES) <= set(plan['sources']), 'runtime_sources_required')
    for relative in plan['sources']:
        require((SOURCE_ROOT / relative).resolve().is_relative_to(SOURCE_ROOT), 'source_path_escape')
    binding = plan['checkpoint']
    require(Path(binding['seam_path']) == SEAM_PATH and sha(SEAM_PATH) == binding['seam_sha256'],
            'seam_binding_changed')
    for arm, path in binding['checkpoint_paths'].items():
        require(arm in ('FULL', 'OFF') and
                Path(path) == continual.ROOT / arm / 'checkpoints' / f'{binding["update"]:09d}',
                'checkpoint_path_changed')
        require(sha(Path(path) / 'COMMIT.json') == binding['commit_sha256'][arm], 'checkpoint_commit_changed')
    paired.bridge.AdapterIdentity.from_document(plan['adapter']).verify()
    return plan


def prepare(root, cpu_log):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and host_identity() == continual.combined.HOST_SHA,
            'cpu_prepare_on_exact_a100')
    require(not (root / 'PLAN.json').exists(), 'one_lifetime_no_reprepare')
    require(Path(cpu_log).is_file() and 'passed' in Path(cpu_log).read_text(), 'own_cpu_tests_required')
    binding = checkpoint_binding()
    previous = read(continual.ROOT / 'PREPARE.json')
    files, context = encoding.metadata(previous['model_dir'])
    tokenizer = paired.native.source.native.load_local_tokenizer(previous['model_dir'])
    encoded = encoding.encode_suite(tokenizer, context)
    started = time.time()
    plan = dict(schema='R107_CAPABILITY_PAIRED_V1', experiment=EXPERIMENT,
        base_sha256=paired.BASE_SHA, adapter=binding['adapter'], checkpoint=binding,
        training_updates=0, parent_calls=0, parent_access=False, train_ingestion=False,
        base_calls=0, conditions=['LORA_ON', 'LORA_OFF'], max_new_tokens=512, task_count=32,
        call_cap=64, gpu_uuid=GPU_UUID, physical_index=0, model_dir=previous['model_dir'],
        suite_sha256=encoding.SUITE_SHA, lifetime_started_unix=started,
        native_deadline_unix=started + 1740, hard_deadline_unix=started + 1800,
        lease_end_unix=continual.LEASE_END, gpu_hours_cap=0.5,
        sources={str(path.relative_to(SOURCE_ROOT)): sha(path)
                 for folder in ('gpu', 'organism_v6', 'tests')
                 for path in sorted((SOURCE_ROOT / folder).rglob('*.py'))})
    validate(plan, time.time())
    write(root / 'PLAN.json', plan)
    write(root / 'RESERVATIONS.json', dict(call_cap=64, retries=0, base_calls=0,
        plan_sha256=sha(root / 'PLAN.json'), cells=[dict(position=position, task_id=task['id'],
            prompt_sha256=task['prompt_sha256'], condition=condition, max_new_tokens=512)
            for position, task in enumerate(policy.tasks()) for condition in paired.ordered_conditions(position)]))
    ready = dict(status='PASS', plan_sha256=sha(root / 'PLAN.json'),
        suite_sha256=encoding.SUITE_SHA, checkpoint=binding, tokenization=encoded,
        model_metadata=files, context=context, cpu_log_sha256=sha(cpu_log),
        reservations_sha256=sha(root / 'RESERVATIONS.json'), native_calls=0, parent_calls=0,
        training_updates=0, base_calls=0, prepared_unix=time.time())
    write(root / 'READY.json', ready)
    return ready


def validate_ready(root, plan):
    ready = read(root / 'READY.json')
    publication = read(root / 'PUBLICATION.json')
    require(ready['status'] == 'PASS' and ready['plan_sha256'] == sha(root / 'PLAN.json')
            and ready['suite_sha256'] == encoding.SUITE_SHA, 'ready_plan_changed')
    require(publication['ready_sha256'] == sha(root / 'READY.json')
            and publication['own_cpu_tests_passed'] is True
            and publication['dated_builder_publication'] and publication['board_allocation'],
            'dated_board_coord_publication_required')
    require(sha(root / 'RESERVATIONS.json') == ready['reservations_sha256'], 'reservations_changed')
    files, context = encoding.metadata(plan['model_dir'])
    require(files == ready['model_metadata'] and context == ready['context'], 'model_metadata_changed')
    return ready


def validate_scan(report, now):
    observed = datetime.fromisoformat(report['created_utc']).timestamp()
    require(0 <= now - observed <= 90 and report['scanner_euid'] == 0
            and report['host_sha256'] == continual.combined.HOST_SHA, 'fresh_privileged_a100_scan_required')
    require(report['clear'] is True and report['blocking_reasons'] == []
            and report['gpu']['index'] == 0 and report['gpu']['uuid'] == GPU_UUID,
            'a100_zero_not_clear')
    require(type(report['device_minor']) is int and report['device_minor'] >= 0
            and report['device_path'] == f'/dev/nvidia{report["device_minor"]}', 'kernel_minor_required')
    require(report['minor_scanner_sha256'] == sha(continual.minor_scan.__file__)
            and report['scanner_sha256'] == sha(continual.minor_scan.pinned.__file__),
            'a100_scanner_sources_changed')


def reduce(root):
    plan = read(root / 'PLAN.json')
    output = root / 'readout'
    if (output / 'COMPLETE.json').exists():
        result = paired_reduce.reduce(root)
        result['process_boundary_disclosure'] = 'All64 cells in one fresh process; no retained cells.'
    else:
        records = []
        for path in sorted(output.glob('CALL_*.json')):
            call = read(path)
            task = policy.tasks()[call['position']]
            require(call['task_id'] == task['id'] and call['messages'] == policy.messages(task), 'call_identity_changed')
            arm = {'LORA_ON': 'ON', 'LORA_OFF': 'OFF'}[call['condition']]
            response = call.get('response')
            if response is not None:
                response = dict(response, max_new_tokens=512)
            if call['status'] != 'COMPLETE':
                response = dict(response or {}, error=call.get('error_type', 'unfinished_reservation'))
            records.append(policy.capture(task, arm, response, checkpoint_sha256=plan['adapter']['state_sha256'],
                base_sha256=plan['base_sha256'], lora_enabled=arm == 'ON'))
        result = policy.reduce_paired(records, checkpoint_sha256=plan['adapter']['state_sha256'],
            base_sha256=plan['base_sha256'], max_new_tokens=512)
        result['before_after_verified'] = False
    result.update(experiment=EXPERIMENT, base_calls=0, training_updates=0, parent_calls=0,
        raw_text_included=False, native_root=str(root), checkpoint=plan['checkpoint'],
        plan_sha256=sha(root / 'PLAN.json'), measured_unix=time.time())
    write(root / 'RESULTS_COMPACT.json', result)
    return result


def run(root):
    require(host_identity() == continual.combined.HOST_SHA, 'native_exact_a100')
    plan = validate(read(root / 'PLAN.json'), time.time())
    ready = validate_ready(root, plan)
    admission = read(root / 'ADMISSION.json')
    validate_scan(admission['snapshot'], time.time())
    require(admission['plan_sha256'] == sha(root / 'PLAN.json'), 'admission_plan_changed')
    tokenizer = paired.native.source.native.load_local_tokenizer(plan['model_dir'])
    require(encoding.encode_suite(tokenizer, ready['context']) == ready['tokenization'], 'prompt_tokens_changed')
    try:
        paired.run(root)
    finally:
        if (root / 'readout').exists():
            reduce(root)


def launch(root):
    require(host_identity() == continual.combined.HOST_SHA and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
            'launch_cpu_on_exact_a100')
    plan = validate(read(root / 'PLAN.json'), time.time())
    validate_ready(root, plan)
    require(not (root / 'readout').exists(), 'no_native_replay')
    (root / 'LAUNCH_ONCE').mkdir(exist_ok=False)
    report = continual.scan(0, continual.ROOT / 'SERVICE_IDENTITY.json')
    write(root / 'FULL_SCAN.json', report)
    validate_scan(report, time.time())
    write(root / 'ADMISSION.json', dict(clear=True, uuid=GPU_UUID, observed_unix=time.time(),
        plan_sha256=sha(root / 'PLAN.json'), snapshot=report))
    seconds = math.floor(plan['hard_deadline_unix'] - time.time() - 5)
    require(seconds > 0, 'lifetime_exhausted_no_launch')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(SOURCE_ROOT))
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(seconds) + 's',
        continual.PYTHON, '-B', '-m', 'gpu.orch_r107_continual_capability_run', 'run', '--root', str(root)]
    with (root / 'native.log').open('x') as log:
        child = subprocess.Popen(command, cwd=SOURCE_ROOT, env=environment, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    identity = continual.minor_scan.pinned.identity(Path('/proc') / str(child.pid))
    receipt = dict(status='LAUNCHED', timeout_identity=identity, command=command,
        admission_sha256=sha(root / 'ADMISSION.json'), plan_sha256=sha(root / 'PLAN.json'),
        hard_deadline_unix=plan['hard_deadline_unix'], calls_cap=64, base_calls=0,
        launched_unix=time.time())
    write(root / 'LAUNCH.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'launch', 'run', 'reduce'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cpu-log', type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'prepare':
        result = prepare(arguments.root, arguments.cpu_log)
    else:
        result = globals()[arguments.phase](arguments.root)
    if result is not None:
        print(json.dumps({key: value for key, value in result.items()
                         if key not in ('tokenization', 'sources', 'source_receipts', 'task_pairs')}, sort_keys=True))
