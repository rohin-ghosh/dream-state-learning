"""Read-only source-verified cold birth and delivered/rendered parent receipts."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def main():
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu.orch_r125_stream_journal import _digest
    from organism_v6.orch_r124_train_history import TrainHistory
    stream = ROOT / 'raw/stream'
    manifest = json.loads((stream / 'JOURNAL.json').read_bytes())
    previous = _digest(manifest)
    counts = Counter()
    loaded, requests, inboxes, stages, recipes, updates, sleeps = [], [], [], [], [], [], []
    first_input_render = {}
    child_generated_tokens = 0
    update_elapsed_seconds = None
    update_finished = []
    update_target_tokens = Counter()
    initial_state = None
    birth = (ROOT / 'BIRTH_PROMPT.txt').read_text()
    messages = {}
    for path in (stream / 'inbox').glob('*.json'):
        message = json.loads(path.read_bytes())
        messages[message['id']] = message['text']
    paths = sorted(path for path in (stream / 'records').glob('*.json') if path.stem.isdigit())
    for index, path in enumerate(paths):
        record = json.loads(path.read_bytes())
        assert record['journal_id'] == manifest['journal_id'] and record['index'] == index
        assert record['previous_sha256'] == previous
        assert record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'})
        previous = record['sha256']
        kind, document = record['kind'], record['document']
        counts[kind] += 1
        reference = dict(index=index, sha256=previous)
        if kind == 'COMMITTED' and document.get('kind') == 'BIRTH':
            state = document['state']['state']
            initial_state = dict(reference, rows=len(state['rows']), sleep_receipts=len(state['sleep_receipts']),
                pending=state['pending'], history_sha256=_digest(state['history']),
                working_state=TrainHistory.restore(state['history']).working_state)
        elif kind == 'LOADED':
            loaded.append(dict(reference, **{key: document[key] for key in (
                'pid', 'optimizer_steps', 'loaded_unix', 'resume', 'base_sha256', 'adapter_sha256')},
                utc=utc(document['loaded_unix'])))
        elif kind == 'REQUEST':
            prompt = document['messages']
            request = dict(reference, utc=utc(document['started_unix']),
                prompt_tokens=document['prompt_tokens'], max_new_tokens=document['max_new_tokens'],
                birth_exactly_once=sum(item['content'] == birth for item in prompt) == 1,
                parent_rendered_ids=[identifier for identifier, text in messages.items()
                    if any(text in item['content'] for item in prompt)])
            requests.append(request)
            for identifier in request['parent_rendered_ids']:
                first_input_render.setdefault(identifier, request)
        elif kind == 'RESPONSE':
            child_generated_tokens += len(document['response'].get('token_ids', []))
        elif kind == 'INBOX':
            message = document['message']
            inboxes.append(dict(reference, id=message['id'], speaker=message.get('speaker'),
                source_sha256=document['source_sha256']))
        elif kind == 'R184_STAGE':
            stages.append(dict(reference, **document))
        elif kind == 'SLEEP_RECIPE':
            recipes.append(dict(reference, **document))
        elif kind == 'UPDATE':
            if 'elapsed_seconds' in document:
                update_elapsed_seconds = (update_elapsed_seconds or 0.0) + document['elapsed_seconds']
            update_finished.append(document['finished_unix'])
            for loss in document.get('losses', []):
                update_target_tokens[loss['kind']] += loss['target_tokens']
            updates.append(dict(reference, **{key: document.get(key) for key in
                ('optimizer_step', 'optimizer_steps', 'source_sha256', 'row', 'presentation')}))
        elif kind == 'SLEEP_COMPLETE':
            sleeps.append(dict(reference, cycle=document['cycle'], optimizer_steps=document['optimizer_steps'],
                total_optimizer_steps=document['total_optimizer_steps'],
                saved_optimizer_steps=document['checkpoint']['optimizer_steps'],
                adapter_sha256=document['checkpoint']['adapter_state_sha256'],
                before_adapter_sha256=document.get('before_adapter_sha256'),
                after_adapter_sha256=document.get('after_adapter_sha256'),
                weight_updates_enabled=document.get('weight_updates_enabled', True),
                child_token_exposures=document.get('child_token_exposures'),
                anchor_token_exposures=document.get('anchor_token_exposures'),
                checkpoint_sha256=document['checkpoint_sha256']))
    commit_path = ROOT / 'raw/checkpoints/initial/COMMIT.json'
    checkpoint = None
    if commit_path.exists():
        commit = json.loads(commit_path.read_bytes())
        assert sha(commit['optimizer_rng_path']) == commit['checkpoint_sha256']['optimizer']
        import torch
        payload = torch.load(commit['optimizer_rng_path'], map_location='cpu', weights_only=False)
        checkpoint = dict(commit_sha256=sha(commit_path), optimizer_steps=commit['optimizer_steps'],
            saved_optimizer_steps=payload['optimizer_steps'], saved_optimizer_state_entries=len(payload['optimizer']['state']),
            checkpoint_sha256=commit['checkpoint_sha256'], initial_adapter_sha256=commit['adapter_state_sha256'])
        assert checkpoint['optimizer_steps'] == checkpoint['saved_optimizer_steps'] == checkpoint['saved_optimizer_state_entries'] == 0
        assert not torch.cuda.is_initialized()
    process = None
    if loaded:
        proc = Path('/proc') / str(loaded[-1]['pid'])
        if proc.exists():
            process = dict(pid=loaded[-1]['pid'], start_ticks=(proc / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                cgroup=(proc / 'cgroup').read_text().strip(), command_sha256=sha(proc / 'cmdline'))
    plan = json.loads((ROOT / 'control/PLAN.json').read_bytes())
    result = dict(schema='R231_CURRENT_COLD_BIRTH_RECEIPT_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        journal_id=manifest['journal_id'], verified_records=len(paths), last_record_sha256=previous,
        record_counts=dict(counts), initial_state=initial_state, initial_checkpoint=checkpoint,
        loaded=loaded, current_process=process, first_requests=requests[:4], latest_request=requests[-1:] or None,
        parent_inboxes=inboxes, first_stages=stages[:4], latest_stage=stages[-1:] or None,
        first_input_rendered_requests=first_input_render, completed_sleeps=sleeps,
        child_generated_tokens=child_generated_tokens, update_elapsed_seconds=update_elapsed_seconds,
        first_update_finished_unix=update_finished[0] if update_finished else None,
        last_update_finished_unix=update_finished[-1] if update_finished else None,
        actual_update_target_tokens_by_kind=dict(update_target_tokens),
        first_sleep_recipe=recipes[:1] or None, first_updates=updates[:2],
        confinement=json.loads((ROOT / 'control/CONFINEMENT_CHILD.json').read_bytes()),
        GPU_memory=subprocess.check_output(['nvidia-smi', '-i', str(plan['physical']), '--query-gpu=memory.used,memory.total',
            '--format=csv,noheader,nounits'], text=True).strip(),
        physical=plan['physical'], hard_end_utc=utc(plan['hard_end_unix']), context_limit=plan['context_limit'],
        segment_tokens=plan['segment_tokens'], native_sha256=sha(ROOT / 'source/gpu/orch_r125_continual_native.py'),
        plan_sha256=sha(ROOT / 'control/PLAN.json'), CPU_sha256=sha(ROOT / 'control/RECEIVING_CPU.json'))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
