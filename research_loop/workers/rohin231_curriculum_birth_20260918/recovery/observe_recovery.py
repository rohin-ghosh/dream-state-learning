"""Read-only sanitized journal/process receipt for the recovery epoch."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def observe(root, physical):
    epoch = root / 'recovery_6144'
    control = epoch / ('control_admission2' if (epoch / 'control_admission2').exists() else 'control')
    plan = read(epoch / 'control/PLAN.json')
    preservation = read(epoch / 'control/PRESERVATION.json')
    stream = root / 'raw/stream'
    manifest = read(stream / 'JOURNAL.json')
    previous = digest(manifest)
    counts = Counter()
    loaded, requests, sleeps, responses, updates, stages = [], [], [], [], [], []
    inbox = [read(path) for path in (stream / 'inbox').glob('*.json')]
    birth = (root / 'BIRTH_PROMPT.txt').read_text()
    first_render = {}
    epoch_record = None
    paths = sorted(path for path in (stream / 'records').glob('*.json') if path.stem.isdigit())
    for index, path in enumerate(paths):
        record = read(path)
        assert record['index'] == index and record['previous_sha256'] == previous
        assert record['journal_id'] == manifest['journal_id']
        assert record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
        previous = record['sha256']
        kind, document = record['kind'], record['document']
        counts[kind] += 1
        reference = dict(index=index, sha256=previous)
        if kind == 'LOADED':
            loaded.append(dict(reference, **{key: document[key] for key in
                ('pid', 'optimizer_steps', 'loaded_unix', 'resume', 'adapter_sha256', 'base_sha256')},
                utc=utc(document['loaded_unix'])))
        elif kind == 'R232_RECOVERY_CONTEXT':
            epoch_record = dict(reference, state_sha256=document['state']['sha256'],
                previous_sha256=document['previous_sha256'], evidence_sha256=document['evidence_sha256'])
        elif kind == 'REQUEST':
            rendered = [item['id'] for item in inbox if any(item['text'] in message['content']
                for message in document['messages'])]
            request = dict(reference, started_unix=document['started_unix'], utc=utc(document['started_unix']),
                prompt_tokens=document['prompt_tokens'], max_new_tokens=document['max_new_tokens'],
                original_birth_exactly_once=sum(message['content'] == birth for message in document['messages']) == 1,
                rendered_inbox_ids=rendered)
            requests.append(request)
            for identifier in rendered:
                first_render.setdefault(identifier, request)
        elif kind == 'RESPONSE':
            responses.append(dict(reference, token_count=len(document['response'].get('token_ids', [])),
                finished_unix=document['finished_unix']))
        elif kind == 'UPDATE':
            updates.append(dict(reference, optimizer_step=document['optimizer_step'],
                finished_unix=document['finished_unix']))
        elif kind == 'SLEEP_COMPLETE':
            sleeps.append(dict(reference, cycle=document['cycle'],
                optimizer_steps=document['checkpoint']['optimizer_steps'],
                adapter_sha256=document['checkpoint']['adapter_state_sha256'],
                checkpoint_sha256=document['checkpoint']['checkpoint_sha256']))
        elif kind == 'R184_STAGE':
            stages.append(dict(reference, stage=document.get('stage'), cycle=document.get('cycle')))
    resumed = [item for item in loaded if item['index'] > epoch_record['index']]
    latest = resumed[-1] if resumed else None
    process = None
    if latest:
        proc = Path('/proc', str(latest['pid']))
        if proc.exists():
            fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
            process = dict(pid=latest['pid'], state=fields[0], start_ticks=fields[19],
                command_sha256=sha(proc / 'cmdline'), cgroup_sha256=sha(proc / 'cgroup'))
    exit_time = preservation['old_exit']['finished_unix']
    post_requests = [item for item in requests if latest and item['index'] > latest['index']]
    result = dict(schema='R232_RECOVERY_CURRENT_V1', observed_utc=utc(time.time()), physical=physical,
        journal_id=manifest['journal_id'], verified_record_count=len(paths), head_sha256=previous,
        record_counts=dict(counts), epoch_record=epoch_record, old_exit_utc=utc(exit_time),
        original_native_pid=preservation['old_pid'], original_native_absent=not Path('/proc', str(preservation['old_pid'])).exists(),
        preserved_state_sha256=preservation['coherent_state']['sha256'],
        preserved_checkpoint_sha256=preservation['checkpoint']['checkpoint_sha256'],
        preserved_optimizer_steps=preservation['checkpoint']['optimizer_steps'],
        preservation_manifest_sha256=sha(epoch / 'control/PRESERVATION.json'),
        context_limit=plan['context_limit'], compaction_threshold=plan['context_limit'] * 3 // 4,
        segment_tokens=plan['segment_tokens'], hard_end_utc=utc(plan['hard_end_unix']),
        birth_sha256=preservation['birth_sha256'], source_module_sha256=sha(epoch / 'source/gpu/r232_recovery.py'),
        plan_sha256=sha(epoch / 'control/PLAN.json'), guard_sha256=sha(control / 'GUARD.json'),
        CPU_sha256=sha(epoch / 'control/RECEIVING_CPU.json'),
        loaded=resumed, current_process=process, first_post_recovery_requests=post_requests[:3],
        latest_request=requests[-1:] or None, first_inbox_render=first_render,
        current_inbox_ids=[dict(id=item['id'], speaker=item.get('speaker')) for item in inbox],
        completed_sleeps=sleeps, generated_tokens=sum(item['token_count'] for item in responses),
        post_recovery_generated_tokens=sum(item['token_count'] for item in responses if latest and item['index'] > latest['index']),
        post_recovery_responses=[item for item in responses if latest and item['index'] > latest['index']],
        actual_update_count=len(updates), post_recovery_update_count=sum(item['index'] > latest['index'] for item in updates) if latest else 0,
        actual_downtime_seconds=latest['loaded_unix'] - exit_time if latest else None,
        latest_stage=stages[-1:] or None, no_gap_claim=False,
        GPU_memory_mib=subprocess.check_output(['nvidia-smi', '-i', str(physical),
            '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], text=True).strip())
    for name in ('MEMORY.json', 'CONFINEMENT_CHILD.json', 'FAILED.json', 'EXIT.json'):
        path = (epoch / 'control' / name) if name == 'MEMORY.json' else control / name
        if path.exists():
            value = read(path)
            if name == 'CONFINEMENT_CHILD.json':
                value = {key: value[key] for key in ('physical', 'pid', 'denied_foreign_minors', 'observed_unix')}
            result[name[:-5].lower()] = value
    return result


if __name__ == '__main__':
    roots = [Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918'),
        Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')]
    print(json.dumps([observe(root, physical) for physical, root in enumerate(roots)], indent=2, sort_keys=True))
