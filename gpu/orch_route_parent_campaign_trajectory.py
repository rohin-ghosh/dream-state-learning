"""Read-only native cycle reductions; never export tasks or response bytes."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


ARMS = ('GUIDED', 'UNPARENTED', 'NO_LORA')
ROOT = '/tmp/orch_route_parent_campaign_20260915_canonical102'


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


class Reader:
    def __init__(self):
        self.evidence = {}

    def read(self, path):
        data = path.read_bytes()
        value = json.loads(data)
        self.evidence[str(path)] = dict(bytes=len(data), sha256=checksum(data))
        return value


def safe_error(error):
    if not error:
        return None
    known = ('complete_reflection_required', 'reflection_not_answer_action_replay',
             'teacher_bytes_in_target', 'teacher_span_in_target', 'NO_VALID_REFLECTIONS', 'NO_LORA')
    return error if error in known else 'UNEXPORTED_ERROR_SHA256:' + checksum(str(error).encode())


def phase(reader, root, arm, cycle, name, observed):
    folder = root / arm / f'cycle{cycle}' / name
    if not (folder / 'REQUEST.json').exists():
        return dict(status='NOT_STARTED')
    request = reader.read(folder / 'REQUEST.json')
    complete = folder / 'COMPLETE.json'
    failed = folder / 'FAILED.json'
    terminal = reader.read(complete) if complete.exists() else reader.read(failed) if failed.exists() else {}
    status = 'COMPLETE' if complete.exists() else 'FAILED' if failed.exists() else 'RUNNING_CENSORED'
    finished = terminal.get('finished_unix')
    result = dict(status=status, started_unix=request['started_unix'], started_utc=utc(request['started_unix']),
        finished_unix=finished, finished_utc=utc(finished) if finished else None,
        elapsed_seconds=(finished or observed) - request['started_unix'],
        input_identity=request['input_adapter'], error=safe_error(terminal.get('error')))
    if (folder / 'LOADED.json').exists():
        loaded = reader.read(folder / 'LOADED.json')
        result['loaded'] = {key: loaded.get(key) for key in ('observed', 'process', 'parent_present')}
    if terminal:
        result['process'] = terminal.get('process')
        result['parent_free'] = terminal.get('parent_free')
    if name == 'sleep':
        for key in ('updates', 'fits', 'output_adapter', 'reason'):
            result[key] = terminal.get(key)
        if (folder / 'DOSE_EXPOSURE.json').exists():
            dose = reader.read(folder / 'DOSE_EXPOSURE.json')
            result['dose'] = {key: dose.get(key) for key in ('planned_presentations', 'actual_updates',
                'actual_new_target_presentations', 'actual_legacy_target_presentations', 'admitted_reflections')}
        losses = folder / 'LOSSES.jsonl'
        if losses.exists():
            data = losses.read_bytes()
            rows = [json.loads(line) for line in data.splitlines() if line.endswith(b'}')]
            reader.evidence[str(losses)] = dict(bytes=len(data), sha256=checksum(data))
            result['optimizer_steps_logged'] = len(rows)
            result['saved_step_count_matches_log'] = terminal.get('updates') == len(rows) if terminal else None
        if terminal.get('output_adapter'):
            identity = terminal['output_adapter']
            result['state_changed'] = request['input_adapter']['state_sha256'] != identity['state_sha256']
            result['base_unchanged'] = request['input_adapter']['base_sha256'] == identity['base_sha256']
            result['saved_files_verified'] = all(
                checksum((Path(identity['path']) / filename).read_bytes()) == expected
                for filename, expected in identity.get('files', []))
            result['file_verification_kind'] = 'NO_ADAPTER_EXPECTED' if identity.get('path') is None else 'SHA256'
            if arm == 'NO_LORA':
                result['no_adapter_identity_verified'] = (identity.get('path') is None
                    and identity.get('files') == [] and identity.get('kind') == 'FROZEN_QWEN_BASE_NO_ADAPTER'
                    and identity['state_sha256'] == identity['base_sha256'] and terminal.get('updates') == 0)
        result['timing_limit'] = 'Sleep envelope includes load/train/save; update receipts have no per-step timestamps.'
        return result
    calls = [reader.read(path) for path in sorted(folder.glob('CALL_*.json'))]
    episodes = [reader.read(path) for path in sorted(folder.glob('EPISODE_*.json'))]
    reflections = [reader.read(path) for path in sorted(folder.glob('REFLECTION_*.json'))]
    responses = [call['response'] for call in calls if call.get('response') is not None]
    result['calls'] = dict(attempted=len(calls), responses=len(responses), errors=sum(bool(call.get('error')) for call in calls),
        pending=sum('finished_unix' not in call for call in calls),
        output_tokens=sum(len(response.get('token_ids', [])) for response in responses),
        prompt_tokens=sum(response.get('prompt_tokens', 0) for response in responses))
    result['generation_seconds_completed_calls'] = sum(call['finished_unix'] - call['started_unix']
        for call in calls if 'finished_unix' in call)
    result['completed_episode_count'] = len(episodes)
    result['task_sha256s'] = [checksum(json.dumps(episode['task'], sort_keys=True).encode()) for episode in episodes]
    result['reflections'] = [dict(admitted=record.get('admitted', False), reason=safe_error(record.get('error')),
        outcome_success=record.get('outcome'), terminal=(record.get('response') or {}).get('terminal'),
        truncated=(record.get('response') or {}).get('truncated'),
        generated_text_tokens=(record.get('response') or {}).get('generated_text_tokens')) for record in reflections]
    result['reflection_counts'] = dict(attempted=len(reflections), admitted=sum(bool(record.get('admitted')) for record in reflections),
        failed_outcome_admitted=sum(bool(record.get('admitted')) and record.get('outcome') is False for record in reflections),
        rejection_reasons=dict(Counter(safe_error(record.get('error')) for record in reflections if not record.get('admitted'))))
    if (folder / 'THINKING_METRICS.json').exists():
        result['thinking'] = reader.read(folder / 'THINKING_METRICS.json')
    if terminal:
        result['ancillary_outcomes'] = {key: terminal.get(key) for key in ('successes', 'all_episode_count', 'paired_both_correct', 'world_denominator')}
    waits = [reader.read(path) for path in sorted((root / 'parent_queue').glob(f'*_{arm}_C{cycle}.WAIT.json'))] if name == 'experience' else []
    parents = [reader.read(path) for path in sorted((root / 'parent_raw').glob(f'*_{arm}_C{cycle}/RECEIPT.json'))] if name == 'experience' else []
    wait_seconds = sum(wait['elapsed_seconds'] for wait in waits)
    provider_seconds = sum(parent['finished_unix'] - parent['started_unix'] for parent in parents)
    result['parents'] = dict(completed_waits=len(waits), wait_seconds=wait_seconds,
        response_receipts=len(parents), provider_seconds=provider_seconds,
        actual_models=sorted({parent['actual_model'] for parent in parents}),
        raw_quarantined=all(parent.get('transcript_quarantined_from_ongoing_L1') for parent in parents),
        provider_errors=sum(bool(wait.get('provider_error')) for wait in waits),
        wait_minus_provider_seconds=wait_seconds-provider_seconds if len(waits) == len(parents) else None,
        interpretation='Wait includes broker queue/service/delivery/polling; residual is NOT isolated queue time.')
    result['other_phase_seconds'] = result['elapsed_seconds'] - wait_seconds - result['generation_seconds_completed_calls']
    result['other_phase_interpretation'] = 'Residual includes model load, environment work and unfinished waits/generation if censored.'
    return result


def snapshot(root=Path(ROOT), maximum_cycle=3):
    reader = Reader()
    observed = time.time()
    rows = []
    for arm in ARMS:
        for cycle in range(maximum_cycle + 1):
            phases = {name: phase(reader, root, arm, cycle, name, observed)
                for name in (('readout',) if cycle == 0 else ('experience', 'sleep', 'readout'))}
            row = dict(arm=arm, cycle=cycle, phases=phases)
            experience, sleep, readout = (phases.get(name, {}) for name in ('experience', 'sleep', 'readout'))
            if sleep.get('status') == 'COMPLETE' and readout.get('loaded'):
                row['fresh_parent_free_saved_child'] = dict(
                    identity_equal=sleep['output_adapter'] == readout['loaded']['observed'],
                    fresh_process=sleep['process'] != readout['loaded']['process'],
                    parent_absent=readout['loaded']['parent_present'] is False,
                    readout_status=readout['status'])
            if cycle > 1 and experience.get('loaded'):
                prior = next(previous for previous in rows if previous['arm'] == arm and previous['cycle'] == cycle-1)['phases']['sleep']
                row['previous_sleep_to_actual_experience'] = dict(
                    same_saved_state=prior.get('output_adapter') == experience['loaded']['observed'],
                    prior_saved_updates=prior.get('updates'), prior_state_changed=prior.get('state_changed'),
                    current_parent_present=experience['loaded']['parent_present'],
                    current_experience_status=experience['status'],
                    retained_behavior_demonstrated=False,
                    interpretation='Actual reloaded parameter lineage, NOT same-task parent-free behavioral retention.')
            if experience.get('started_unix') and readout.get('finished_unix'):
                row['cycle_total_seconds'] = readout['finished_unix'] - experience['started_unix']
                row['interphase_gap_seconds'] = row['cycle_total_seconds'] - sum(value['elapsed_seconds'] for value in phases.values())
            rows.append(row)
    for row in rows:
        if row['cycle']:
            previous = next(item for item in rows if item['arm'] == row['arm'] and item['cycle'] == row['cycle']-1)
            current_tasks = set(row['phases']['readout'].get('task_sha256s', []))
            previous_tasks = set(previous['phases']['readout'].get('task_sha256s', []))
            row['parent_free_previous_checkpoint_task_overlap'] = dict(shared=len(current_tasks & previous_tasks),
                current=len(current_tasks), previous=len(previous_tasks),
                interpretation='Different tasks: checkpoint changes are exploratory transfer proxies, not a retention test.')
    return dict(observed_utc=utc(observed), root=str(root), rows=rows, evidence=reader.evidence,
        source_sha256=checksum(Path(__file__).read_bytes()), raw_exported=False, writes_to_native_lives=False,
        semantic_thinking_or_retention_claim=False,
        control_identity='NO_LORA means frozen base without adapter; historical frozen-LoRA is excluded.',
        loss_semantics='Ordinary positive-likelihood SFT on admitted outcome-tagged learner reflections plus legacy replay; not negative-gradient learning.',
        thinking_limit='Execution rejection, repetition and completion are operational proxies, not verified reasoning/coherence.',
        schedule_or_allocation_changes=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(ROOT))
    parser.add_argument('--maximum-cycle', type=int, default=3)
    arguments = parser.parse_args()
    print(json.dumps(snapshot(arguments.root, arguments.maximum_cycle), indent=2))
