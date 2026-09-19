"""One bounded stdout-only snapshot; run via stdin on the original SSH route."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
ROOT = Path('/localhome/local-rohing/post_sampling_custody_diagnostics_20260919/'
    '21df1fcbff9c54358c2474541bd399a2ab2572c58aa73046a255d1d851517d8f')
RUNTIME = ('construct_candidate.py', 'execution.py', 'sealed_runner.py',
    'dispatch_sampling.py', 'prepare_executable.py', 'report_sampling.py',
    'release_failed_claims.py')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def select(value, names):
    return {name: value[name] for name in names.split() if name in value}


def project_cell(value):
    result = select(value, 'status budget generated_tokens prompt_tokens initial_context_sha256 '
        'no_updates parent_tokens learn_or_other_reply_tokens contest_id seed diagnostic_epoch_sha256')
    result['events'] = []
    for event in value['events']:
        projected = select(event, 'origin actual_generated_tokens prompt_tokens requested_max_new_tokens '
            'terminal truncated token_bin_end')
        score = event['score']
        projected['score'] = select(score, 'request_sha256 judge_epoch_sha256 diagnostic_epoch_sha256 new_pixels')
        projected['score']['results'] = []
        for row in score['results']:
            outcome = select(row['result'], 'ok contest_id accepted rank reference_count top_k status '
                'pixel_id pixel_count submission_id cached replayed rejection_reason')
            if 'error' in row['result']:
                outcome['error'] = select(row['result']['error'], 'code')
            projected['score']['results'].append(dict(caption_sha256=row['caption_sha256'], result=outcome))
        result['events'].append(projected)
    return result


def project_complete(value):
    result = select(value, 'unix condition actual_generated_tokens unchanged_identity elapsed_seconds '
        'judge_epoch_sha256 diagnostic_epoch_sha256 source_age parent_tokens training_updates '
        'raw_acceptance_not_certified_literal_jokes')
    result['cells'] = [dict(contest_id=cell['contest_id'], seed=cell['seed'],
        source_object_sha256=digest(cell)) for cell in value['cells']]
    return result


def project_config(value):
    return select(value, 'root condition diagnostic_epoch_sha256 job_id job_identity block_id '
        'execution_incarnation_sha256 source_checkpoint original_parameter_identity seeds expected_scene_ids '
        'token_budget scenes parent_tokens training_updates source_context_loaded plain_base '
        'adapter_sha256 judge_rank judge_step source_manifest_sha256 primary_config_sha256')


def envelope(path, projector=None, json_content=True):
    path = Path(path)
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
        raise ValueError('only_regular_files_inside_bound_root')
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('bounded_file_read')
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError('bounded_file_read')
    result = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    if json_content:
        original = json.loads(raw)
        result['source_object_sha256'] = digest(original)
        result['payload'] = projector(original) if projector else original
        result['projection_sha256'] = digest(result['payload'])
    return result


def capture():
    documents = {name: envelope(ROOT / name) for name in (
        'REGISTRY.json', 'PREPARED.json', 'SOURCE_FREEZE.json', 'BLOCK_COMPLETE.json')}
    documents['PREREGISTRATION.md'] = envelope(ROOT / 'PREREGISTRATION.md', json_content=False)
    registry = documents['REGISTRY.json']['payload']
    if Path(registry['root']) != ROOT or len(registry['jobs']) != 3:
        raise ValueError('wrong_block')
    runtime_files = {name: envelope(ROOT / 'runtime' / name, json_content=False) for name in RUNTIME}
    jobs = []
    for declared in registry['jobs']:
        job_root = Path(declared['root'])
        if job_root != ROOT / 'jobs' / declared['job_id']:
            raise ValueError('wrong_job_path')
        config = envelope(job_root / 'CONFIG.json', project_config)
        view = Path(config['payload']['root'])
        if view != job_root / 'view':
            raise ValueError('wrong_view_path')
        condition = config['payload']['condition']
        if Path(condition).name != condition:
            raise ValueError('invalid_condition_component')
        output = view / 'players' / condition
        cells = []
        for scene in registry['expected_scene_ids']:
            for seed in registry['diagnostic_epoch']['sampling_seeds']:
                cells.append(dict(contest_id=scene, seed=seed,
                    result=envelope(output / f'{scene}_{seed}' / 'RESULT.json', project_cell)))
        jobs.append(dict(arm=declared['arm'], job_id=declared['job_id'], config=config,
            loaded=envelope(output / 'LOADED.json'), complete=envelope(output / 'COMPLETE.json', project_complete),
            completion_verified=envelope(job_root / 'COMPLETION_VERIFIED.json'), cells=cells))
    freeze = documents['SOURCE_FREEZE.json']['payload']
    if any(runtime_files[name]['sha256'] != freeze['files'][name] for name in RUNTIME):
        raise ValueError('runtime_source_changed_no_report_execution')
    command = ['/localhome/local-rohing/v2/venv/bin/python', '-B',
        str(ROOT / 'runtime/report_sampling.py'), '--root', str(ROOT)]
    reported = subprocess.run(command, capture_output=True, timeout=90,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), check=False)
    if len(reported.stdout) > MAX_OUTPUT_BYTES:
        raise ValueError('bounded_report_output')
    report = dict(command=command, returncode=reported.returncode,
        stdout_sha256=hashlib.sha256(reported.stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(reported.stderr).hexdigest(), payload=None)
    if reported.returncode == 0:
        report['payload'] = json.loads(reported.stdout)
    for job in jobs:
        for cell in job['cells']:
            reference = cell['result']
            if reference:
                refreshed = envelope(reference['path'], project_cell)
                if refreshed['sha256'] != reference['sha256']:
                    raise ValueError('cell_changed_during_snapshot')
    return dict(schema='PUBLIC_SAMPLING_ACCOUNTING_SNAPSHOT_V1', root=str(ROOT),
        captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        documents=documents, runtime_files=runtime_files, jobs=jobs, runtime_report=report,
        private_panels_read=False, caption_text_exported=False, model_tensors_read=False,
        source_mutations=False, projector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if __file__ != '<stdin>' else None)


if __name__ == '__main__':
    payload = json.dumps(capture(), sort_keys=True, indent=2, allow_nan=False) + '\n'
    if len(payload.encode()) > MAX_OUTPUT_BYTES:
        raise ValueError('bounded_public_export')
    print(payload, end='')
