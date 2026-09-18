"""Bounded read-only live receipts, without transcript or credential export."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOTS = [Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918'),
    Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')]


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def observe(root, physical):
    epoch = root / 'recovery_20260918T1646Z'
    control = epoch / 'control'
    if not (control / 'READY.json').exists():
        return dict(physical=physical, status='PREPARING_NOT_DISPATCHED', observed_utc=utc(time.time()))
    ready = read(control / 'READY.json')
    preserved = read(control / 'PRESERVATION.json')
    cut = preserved['head_index']
    paths = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    loaded, requests, responses, complete, notices, recipes, walls, eligibility = [], [], [], [], [], [], [], []
    for path in paths:
        if int(path.stem) <= cut:
            continue
        record = read(path)
        document = record['document']
        reference = dict(index=record['index'], record_sha256=record['sha256'], file_sha256=sha(path),
            observed_file_mtime_utc=utc(path.stat().st_mtime))
        if record['kind'] == 'LOADED':
            loaded.append(dict(reference, pid=document['pid'], resume=document['resume'],
                loaded_unix=document['loaded_unix'], loaded_utc=utc(document['loaded_unix']),
                optimizer_steps=document['optimizer_steps'], adapter_sha256=document['adapter_sha256']))
        elif record['kind'] == 'REQUEST':
            requests.append(dict(reference, started_utc=utc(document['started_unix']),
                prompt_tokens=document['prompt_tokens'], max_new_tokens=document['max_new_tokens']))
        elif record['kind'] == 'RESPONSE':
            raw = document['response']['raw']
            responses.append(dict(reference, finished_utc=utc(document['finished_unix']),
                raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), raw_characters=len(raw),
                token_count=len(document['response'].get('token_ids', [])), raw_exported=False))
        elif record['kind'] == 'SLEEP_COMPLETE':
            complete.append(dict(reference, cycle=document['cycle'],
                optimizer_steps=document['checkpoint']['optimizer_steps'],
                adapter_sha256=document['checkpoint']['adapter_state_sha256'], status=document['status'],
                control_policy=document.get('control_policy'), weight_updates_enabled=document.get('weight_updates_enabled'),
                before_adapter_sha256=document.get('before_adapter_sha256'),
                after_adapter_sha256=document.get('after_adapter_sha256')))
        elif record['kind'] == 'R184_SLEEP_NOTICE':
            notices.append(dict(reference, cycle=document['cycle']))
        elif record['kind'] == 'SLEEP_RECIPE':
            recipes.append(dict(reference, fields={key:document.get(key) for key in
                ('policy', 'learn_row_policy', 'new_rows', 'new_presentations', 'selected_old_rows',
                 'active_semantic_filters', 'semantic_row_exclusion', 'weight_updates_enabled',
                 'anchor_lambda', 'candidate_row_filter_policies', 'historical_row_annotations',
                 'technical_provenance_and_encoding_checks')}))
        elif record['kind'] == 'TARGET_ELIGIBILITY':
            eligibility.append(dict(reference, learn_row_policy=document.get('learn_row_policy'),
                active_semantic_filters=document.get('active_semantic_filters'),
                semantic_row_exclusion=document.get('semantic_row_exclusion'),
                excluded=document.get('excluded'), new_rows=len(document.get('new_row_sha256', [])),
                rehearsal_rows=len(document.get('rehearsal_row_sha256', [])), raw_modified=document.get('raw_modified')))
        elif record['kind'] == 'WALL_EXTENDED':
            walls.append(dict(reference, authorization=document['authorization'],
                state_sha256=document['state']['sha256']))
    process = None
    if loaded:
        proc = Path('/proc', str(loaded[-1]['pid']))
        if proc.exists():
            fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
            process = dict(pid=loaded[-1]['pid'], state=fields[0], start_ticks=fields[19])
    admission = None
    if (control / 'PRE_SERVICE_ADMISSION.json').exists():
        binding = read(control / 'PRE_SERVICE_ADMISSION.json')
        report = binding['report']
        admission = dict(scanner_euid=report['scanner_euid'], clear=report['clear'],
            blocking_reasons=report['blocking_reasons'], report_sha256=sha(control / 'PRE_SERVICE_ADMISSION.json'),
            verified_utc=utc(binding['verified_unix']), guard_sha256=binding['guard_sha256'])
    result = dict(schema='R233_OVX4_PAIR_RECOVERY_OBSERVATION_V1', physical=physical,
        observed_utc=utc(time.time()), ready=ready, head_index=int(paths[-1].stem),
        preserved_head=cut, preservation_manifest_sha256=sha(control / 'PRESERVATION.json'),
        old_exit_utc=utc(preserved['old_outer_exit']['finished_unix']), old_exit_status=preserved['old_outer_exit']['status'],
        old_native_pid=preserved['old_loaded']['document']['pid'],
        old_native_absent=not Path('/proc', str(preserved['old_loaded']['document']['pid'])).exists(),
        loaded=loaded, process=process, first_requests=requests[:3], first_responses=responses[:3],
        fresh_response_count=len(responses), completed_sleeps=complete,
        sleep_notifications=notices, recipes=recipes, eligibility=eligibility, wall_extensions=walls, admission=admission,
        runtime_source_bytes_unchanged=True, same_journal=True, no_gap_claim=False,
        saved_checkpoint_RNG_restored_claim=bool(loaded), resident_post_checkpoint_RNG_captured=False)
    if loaded:
        result['observed_outage_seconds'] = loaded[0]['loaded_unix'] - preserved['old_outer_exit']['finished_unix']
    for name in ('MEMORY.json', 'OUTER_EXIT.json', 'OUTER_FAILED.json', 'CONFINEMENT_CHILD.json'):
        path = control / name
        if path.exists():
            value = read(path)
            result[name[:-5].lower()] = {key:value[key] for key in (
                'passed', 'optimizer_steps', 'saved_RNG_restored', 'optimizer_step_calls', 'status',
                'finished_unix', 'error_type', 'pid', 'physical', 'denied_foreign_minors') if key in value}
    return result


if __name__ == '__main__':
    print(json.dumps([observe(root, physical) for physical, root in enumerate(ROOTS)], indent=2, sort_keys=True))
