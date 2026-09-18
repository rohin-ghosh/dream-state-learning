"""Private evaluator sidecar for every completed saved adapter, without training writes."""

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from ddp_pilot import macro_spearman, require, sha, write


CASE_IDS = '6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba'


def checkpoints(root):
    output = root / 'training'
    progress = sorted(output.glob('PROGRESS_*.json'))
    current = json.loads(progress[-1].read_bytes())['completed_updates'] if progress else 0
    found = []
    for adapter in sorted(output.glob('selected_step_*')):
        step = int(adapter.name.rsplit('_', 1)[1])
        if current > step or (output / 'COMPLETED.json').exists():
            found.append((adapter.name, adapter, step))
    for name, marker in [('pilot_checkpoint', 'PILOT_COMPLETE.json'), ('completed_checkpoint', 'COMPLETED.json')]:
        if (output / marker).exists():
            receipt = json.loads((output / marker).read_bytes())
            found.append((name, output / name / 'adapter', receipt.get('completed_updates', receipt.get('optimizer_updates'))))
    return found


def score(root, name, adapter, step):
    from gpu import ny_caption_data as data
    from gpu import ny_caption_judge as helpers
    from gpu import ny_caption_contrast as contrast
    from gpu.ny_caption_scalar_judge import ScalarJudge
    import torch
    config = json.loads((root / 'PILOT_CONFIG.json').read_bytes())
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(0.42)
    destination = root / 'checkpoint_diagnostics' / name
    destination.mkdir(parents=True, mode=0o700)
    started = time.time()
    cases_path = Path(__file__).parent / 'CASES.private.json'
    cases = json.loads(cases_path.read_bytes())
    require(len(cases) == 600 and len({case['contest'] for case in cases}) == 20, 'exact600case20contest_suite')
    require(data.digest([case['case_id'] for case in cases]) == CASE_IDS, 'exact_Main_R207_suite_case_order')
    require(all(data.digest({key: value for key, value in case.items() if key != 'case_id'}) == case['case_id'] for case in cases), 'unaltered_Main_cases')
    base = json.loads((root / 'BASE_MANIFEST.source.json').read_bytes())
    base['root'] = config['model_root']
    base_ref = data.private_write(destination / 'BASE_MANIFEST.local.json', base)
    judge_config = dict(schema='R207_SCALAR_RUNTIME_V1', base_model=base_ref,
        selected_adapter_root=str(adapter), adapter={file: data.file_ref(adapter / file)
            for file in ['adapter_config.json', 'adapter_model.safetensors']}, config=dict(max_length=512))
    config_path = destination / 'SCALAR_RUNTIME.json'
    write(config_path, judge_config)
    judge = ScalarJudge(str(config_path), batch_size=8)
    records, unique = [], {}
    for case in cases:
        tokens = [judge.token_count(case['scene'], case[side]) for side in ['good', 'contrast']]
        record = {key: case[key] for key in ['case_id', 'contest', 'kind', 'top_index']}
        record['tokens'] = tokens
        if max(tokens) > judge.max_length:
            record.update(status='SKIPPED_OVERLENGTH', good_score=None, contrast_score=None)
        elif data.normalize_caption(case['good']) == data.normalize_caption(case['contrast']):
            record.update(status='SKIPPED_IDENTICAL', good_score=None, contrast_score=None)
        else:
            record['status'] = 'PENDING'
            for side in ['good', 'contrast']:
                unique.setdefault((case['scene'], case[side]), None)
        records.append(record)
    keys = list(unique)
    for offset in range(0, len(keys), 8):
        batch = keys[offset:offset + 8]
        unique.update(zip(batch, judge.score([dict(scene=scene, caption=caption) for scene, caption in batch])))
    for case, record in zip(cases, records):
        if record['status'] == 'PENDING':
            record.update(status='SCORED', good_score=unique[(case['scene'], case['good'])],
                contrast_score=unique[(case['scene'], case['contrast'])])
    contrast_finished = time.time()
    write(destination / 'CONTRAST.private.json', dict(schema='R209_EXACT_R207_CONTRAST_V1',
        optimizer_step=step, lora_rank=config['lora_rank'], case_ids_sha256=CASE_IDS,
        cases_sha256=sha(cases_path), cases=600, contests=20, no_tau_gate=True,
        unchanged_scenes_and_rows=True, checkpoint_adapter=judge_config['adapter'],
        source_sha256={file:sha(Path(__file__).parent / 'gpu' / file)
            for file in ['ny_caption_contrast.py', 'ny_caption_scalar_judge.py']},
        reused_exact_Main_cases_not_regenerated=True, records=records, **contrast.summarize(records)))
    existing_selection = root / 'training/selection' / f'STEP_{step:06d}.private.json'
    if existing_selection.exists():
        shutil.copy2(existing_selection, destination / 'SPEARMAN.private.json')
        write(destination / 'COMPLETE.json', dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            optimizer_step=step, rank=config['lora_rank'], cases=600, contests=20, case_ids_sha256=CASE_IDS,
            same_checkpoint_contrast_and_Spearman=True, contrast_with_load_seconds=contrast_finished-started,
            selection_seconds=0, reused_actual_training_selection_receipt=True,
            selection_receipt_sha256=sha(existing_selection), total_seconds=time.time()-started,
            training_updates=0, private_scores_only=True, diagnostic_gpu_shared_with_own_candidate=True))
        return
    with (root / 'SELECTION_ROWS.private.jsonl').open() as stream:
        rows = [json.loads(line) for line in stream]
    eligible = [row for row in rows if judge.token_count(row['scene'], row['caption']) <= 512]
    selected = helpers.natural_heldout_rows(eligible, 256, config['seed'] + 41)
    predictions = []
    for offset in range(0, len(selected), 8):
        batch = selected[offset:offset + 8]
        predictions.extend((row['contest_id'], row['mean'], value) for row, value in zip(batch, judge.score(batch)))
    selection_score = macro_spearman(predictions, helpers.average_ranks)
    require(math.isfinite(selection_score), 'finite_checkpoint_Spearman')
    write(destination / 'SPEARMAN.private.json', dict(optimizer_step=step, examples=len(selected),
        macro_mean_rating_spearman=selection_score, seed=config['seed'] + 41,
        panel_sha256=sha(root / 'SELECTION_ROWS.private.jsonl'), no_checkpoint_reselection_by_sidecar=True))
    write(destination / 'COMPLETE.json', dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        optimizer_step=step, rank=config['lora_rank'], cases=600, contests=20, case_ids_sha256=CASE_IDS,
        same_checkpoint_contrast_and_Spearman=True, contrast_with_load_seconds=contrast_finished-started,
        selection_seconds=time.time()-contrast_finished, total_seconds=time.time()-started,
        training_updates=0, private_scores_only=True, diagnostic_gpu_shared_with_own_candidate=True))


def watch(root):
    os.umask(0o077)
    config = json.loads((root / 'PILOT_CONFIG.json').read_bytes())
    output = root / 'checkpoint_diagnostics'
    output.mkdir(mode=0o700)
    write(output / 'WATCH_STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(),
        exact_case_ids_sha256=CASE_IDS, all_saved_checkpoints=True, training_mutated=False,
        unsaved_non_improving_selection_evaluations_are_not_saved_checkpoints=True,
        runtime_seconds_budget=int(config['training_end_unix']-time.time())))
    while time.time() < config['training_end_unix'] - 180:
        for name, adapter, step in checkpoints(root):
            target = output / name
            if target.exists():
                continue
            with (output / (name + '.log')).open('x') as log:
                result = subprocess.run([sys.executable, '-B', __file__, 'score', '--root', str(root),
                    '--name', name, '--adapter', str(adapter), '--step', str(step)],
                    stdout=log, stderr=subprocess.STDOUT, check=False, timeout=900)
            if result.returncode:
                target.mkdir(mode=0o700, exist_ok=True)
                write(target / 'FAILED.json', dict(status=result.returncode, observed_unix=time.time(), no_retry=True))
        if (root / 'training/COMPLETED.json').exists() or (root / 'OUTER_EXIT.json').exists():
            break
        time.sleep(10)
    write(output / 'WATCH_EXIT.json', dict(observed_unix=time.time(), training_updates=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['watch', 'score'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--name')
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--step', type=int)
    arguments = parser.parse_args()
    if arguments.mode == 'watch':
        watch(arguments.root)
    else:
        score(arguments.root, arguments.name, arguments.adapter, arguments.step)
