import datetime
import hashlib
import json
import os
import pathlib
import time


ROOT = pathlib.Path('/localhome/local-rohing/orch_r177_ampere_judge_20260917')
CANDIDATES = ('released_all_v4', 'released_all_v6', 'bt_qwen_v2', 'bt_widegap_v2')
FILES = ('ADMISSION.json', 'DISPATCH_STARTED.json', 'COMPLETED.json',
         'EXPERIMENT_BUDGET.json', 'TRAIN_CONFINEMENT_PROOF.json',
         'training/TRAINING_STARTED.json',
         'training/FIRST_OPTIMIZER_STEP.json', 'training/FAILED.json',
         'training/MEASURED_BUDGET_ADMISSION.json',
         'training/FULL_POOL_SELECTION_REPORT.json',
         'training/PUBLIC_SCORING_REPORT.json')
FIELDS = frozenset(('schema', 'status', 'pid', 'startticks', 'start_ticks',
    'started_unix', 'observed_unix', 'completed_unix', 'finished_unix',
    'created_unix', 'measured_unix', 'step', 'humor_step', 'scene_fit_step',
    'completed_updates', 'actual_comparisons', 'actual_caption_draws',
    'selected_step', 'selected_checkpoint_comparisons', 'required_comparisons',
    'required_pair_target_completed', 'calibration_examples',
    'calibrated_q_meaning', 'objective', 'optimizer_state_reset',
    'pretrained_revision', 'trainable_parameter_count', 'max_seconds',
    'wall_seconds', 'run_max_seconds', 'allocation_start_unix',
    'allocation_end_unix', 'lease_end_unix', 'deadline_unix',
    'seconds_since_model_load', 'elapsed_seconds', 'seconds',
    'physical', 'physical_index', 'gpu_uuid', 'gpu_model',
    'model_examples_charged', 'model_tokens_charged',
    'measured_comparisons_per_second', 'threshold', 'human_validated',
    'full_judge_usable', 'second_blind_comparator_complete',
    'scene_fit_frozen_from_v6', 'scene_fit_selected_step', 'accepted',
    'examples', 'coverage', 'can_complete', 'expected_total_seconds',
    'training_seconds', 'calibration_seconds', 'remaining_seconds',
    'expected_fit_seconds', 'selection_seconds', 'calibration_reserve_seconds',
    'remaining_allocation_seconds', 'comparison_rate'))
FIELDS = FIELDS | frozenset(('end_unix', 'issued_unix', 'start_unix',
    'lease_safe_end_unix', 'max_gpu_seconds', 'max_steps', 'device',
    'device_uuid', 'name', 'memory_total_bytes', 'memory_free_bytes',
    'total_memory_bytes', 'free_memory_bytes', 'process_startticks',
    'completed_optimizer_steps', 'completed_steps', 'selected_scene_fit_step',
    'humor_training_example_draws', 'scene_fit_positive_example_draws',
    'scene_fit_negative_example_draws', 'accepted_count',
    'fitting_seconds', 'inference_seconds', 'conservative_remaining_seconds',
    'fixed_close_margin_seconds', 'remaining_admitted_seconds',
    'inferred_ETA_not_completion_receipt', 'target_opened',
    'target_device', 'target_physical', 'target_gpu_uuid',
    'all_other_numbered_devices_denied', 'cuda_visible_devices'))
NESTED = ('admission', 'budget', 'wall', 'experiment_budget', 'gpu',
          'tau', 'rank200_quality_threshold', 'rank200_quality_audit',
          'development_audit', 'first_optimizer', 'counts', 'training',
          'actual_capacity', 'lease')


def scalars(document):
    if not isinstance(document, dict):
        return {}
    return {key: value for key, value in document.items()
            if key in FIELDS and (value is None or isinstance(value, (str, int, float, bool)))}


def receipt(path):
    if not path.is_file():
        return {'exists': False}
    metadata = path.stat()
    if metadata.st_size > 131072:
        return {'exists': True, 'bytes': metadata.st_size, 'body': 'SKIPPED_SIZE_BOUND'}
    raw = path.read_bytes()
    document = json.loads(raw)
    result = dict(exists=True, path=str(path), bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(), mtime_unix=metadata.st_mtime,
        fields=scalars(document), field_names=sorted(document))
    for name in NESTED:
        if isinstance(document.get(name), dict):
            result.setdefault('nested', {})[name] = dict(
                field_names=sorted(document[name]), fields=scalars(document[name]))
    for name in ('judge_config', 'report'):
        reference = document.get(name)
        if isinstance(reference, dict):
            result.setdefault('references_only', {})[name] = {
                key: reference[key] for key in ('path', 'sha256', 'bytes') if key in reference}
    return result


def inspect_candidate(name):
    root = ROOT / name
    result = dict(root=str(root), exists=root.is_dir(), receipts={})
    if not root.is_dir():
        return result
    for relative in FILES:
        result['receipts'][relative] = receipt(root / relative)
    for folder in ('throughput', 'progress'):
        paths = sorted((root / 'training' / folder).glob('*.json'))
        result[folder + '_receipt_count'] = len(paths)
        for path in list(dict.fromkeys(paths[:1] + paths[-1:])):
            result['receipts'][str(path.relative_to(root))] = receipt(path)
    return result


processes = []
for entry in pathlib.Path('/proc').iterdir():
    if not entry.name.isdigit():
        continue
    try:
        if entry.stat().st_uid != os.getuid():
            continue
        arguments = entry.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')
        if '-c' in arguments or not arguments or not any('python' in arg for arg in arguments[:1]):
            continue
        cwd = str(entry.joinpath('cwd').resolve())
        if not cwd.startswith(str(ROOT)) and not any(str(ROOT) in arg for arg in arguments):
            continue
        stat_fields = entry.joinpath('stat').read_text().rsplit(')', 1)[1].split()
        processes.append(dict(pid=int(entry.name), uid=os.getuid(), state=stat_fields[0],
            start_ticks=stat_fields[19], cwd=cwd,
            entrypoints=[pathlib.Path(arg).name for arg in arguments if arg.endswith('.py')][:2]))
    except (OSError, ValueError, IndexError):
        continue

historical_pid_checks = []
for pid in (3941679, 4065988, 387461, 1055569):
    process = pathlib.Path('/proc') / str(pid)
    historical_pid_checks.append(dict(pid=pid, proc_exists=process.exists(),
        matching_scoped_process=any(row['pid'] == pid for row in processes)))

print(json.dumps(dict(schema='R206_JUDGE_PUBLIC_OPERATIONAL_READ_V1',
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    observed_unix=time.time(), host=os.uname().nodename, uid=os.getuid(),
    root=str(ROOT), root_exists=ROOT.is_dir(),
    candidate_directory_names=sorted(path.name for path in ROOT.iterdir()
        if path.is_dir() and (path.name.startswith('released_all_v') or path.name.startswith('bt_'))) if ROOT.is_dir() else [],
    processes=processes, historical_pid_checks=historical_pid_checks,
    candidates={name: inspect_candidate(name) for name in CANDIDATES},
    gpu_model_calls=0, remote_writes=0, process_controls=0,
    private_configs_rows_curves_and_reference_panels_opened=False)))
