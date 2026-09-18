"""Read actual C2 journal windows and exact same-parent request exposure."""

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
CONTROL = Path('/localhome/local-rohing/orch_r204_C2_20260918_resume1/control')
SOURCE = CONTROL.parent / 'source'
sys.path.insert(0, str(SOURCE))
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


parent_ids = ('cbd12ed5973b4c0dba5004b31ac814cd', '58d80b5d4d8f4dc39eb694a70475ea38',
    'c78ccdaaa97747ae8bc57649a117e45b', '4e733c7e32c34bfe9a918c5fb90b5714')
guard = read(CONTROL / 'GUARD.json')
plan = read(CONTROL / 'PLAN.json')
process = Path('/proc/3179563')
fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
assert fields[19] == '23773135'
assert (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')[-3:] == [
    'native', '--config', str(CONTROL / 'GUARD.json')]
paths = sorted((ROOT / 'stream/records').glob('[0-9]' * 20 + '.json'))
catalog = []
for path in paths:
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    catalog.append(json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:]))
receipts, exposures, registrations = [], [], {}
for item in catalog:
    if item['index'] < 5856:
        continue
    kind = item['kind']
    if kind not in ('LOADED', 'REQUEST', 'RESPONSE', 'R184_STAGE', 'COMPACTION',
            'CONTEXT_INPUT', 'SLEEP_REQUEST', 'SLEEP_RECIPE', 'SLEEP_COMPLETE', 'INBOX'):
        continue
    record = read(paths[item['index']])
    document = record['document']
    receipt = dict(index=record['index'], kind=kind, record_sha256=record['sha256'],
        source_path=str(paths[item['index']]), file_mtime_unix=paths[item['index']].stat().st_mtime)
    for name in ('pid', 'loaded_unix', 'started_unix', 'finished_unix', 'cycle', 'stage', 'segment',
            'optimizer_steps', 'render_receipt', 'before_tokens', 'after_tokens', 'threshold_tokens',
            'carry_source_kind', 'training_eligible', 'status', 'request_sha256'):
        if name in document:
            receipt[name] = document[name]
    if kind in ('COMPACTION', 'CONTEXT_INPUT'):
        receipt['subkind'] = document.get('kind')
    if kind == 'SLEEP_COMPLETE':
        receipt['cumulative_optimizer_steps'] = document['checkpoint']['optimizer_steps']
        receipt['checkpoint_root'] = str(Path(document['checkpoint']['optimizer_rng_path']).parent)
    if kind == 'RESPONSE':
        receipt['raw_child_response'] = document['response']['raw']
    if kind == 'INBOX':
        message = document['message']
        receipt.update(inbox_id=message['id'], speaker=message.get('speaker'))
        registrations[message['id']] = receipt
    if kind == 'REQUEST':
        state = document['resume_state']['state']
        history = state['history']
        frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
        for event_raw in history['events'][frontier:]:
            identifier = event_raw['event_id'].removeprefix('parent:inbox:')
            if identifier not in parent_ids:
                continue
            event = TrainEvent(**event_raw)
            rendered = event_message(event) if state.get('presentation') else TrainHistory._message(event)
            if asdict(event) in history['events'][frontier:] and rendered in document['messages']:
                exposures.append(dict(inbox_id=identifier, request_index=record['index'],
                    started_unix=document['started_unix'], request_sha256=record['sha256'],
                    exact_visible_event_and_rendered_message=True, render_receipt=document['render_receipt']))
    receipts.append(receipt)
windows = []
for label, start, stop in (('R202_before_repair', 5856, 5976), ('R203', 5976, 6057),
        ('CURRENT_R204', 6057, len(paths))):
    selected = [item for item in receipts if start <= item['index'] < stop]
    requests = [item for item in selected if item['kind'] == 'REQUEST']
    tokens = [item['render_receipt']['token_count'] for item in requests]
    stages = [item for item in selected if item['kind'] == 'R184_STAGE']
    streak = 0
    longest = 0
    for item in stages:
        streak = streak + 1 if item['stage'] == 'THINK' else 0
        longest = max(longest, streak)
    windows.append(dict(label=label, start_index=start, stop_exclusive=stop,
        requests=len(requests), max_prompt_tokens=max(tokens, default=None),
        requests_at_or_above_12288=[item['index'] for item in requests if item['render_receipt']['token_count'] >= 12288],
        all_history_masked=all(item['render_receipt']['all_history_tokens_masked'] for item in requests),
        longest_actual_R184_THINK_stage_streak=longest,
        compactions=[item for item in selected if item['kind'] == 'COMPACTION']))
pending = []
for identifier in parent_ids:
    path = ROOT / 'stream/inbox' / (identifier + '.json')
    if path.exists() and identifier not in registrations:
        pending.append(dict(inbox_id=identifier, source_sha256=sha(path)))
source_files = ('gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r125_continual_stream.py',
    'gpu/orch_r125_continual_native.py')
source_checks = {name: dict(actual_sha256=sha(SOURCE / name), pinned_sha256=guard['source_pins'][name])
    for name in source_files}
assert all(value['actual_sha256'] == value['pinned_sha256'] for value in source_checks.values())
print(json.dumps(dict(observed_unix=time.time(), actor=dict(pid=3179563, start_ticks=fields[19], state=fields[0],
    cwd=os.readlink(process / 'cwd')), life_root=str(ROOT), guard_path=str(CONTROL / 'GUARD.json'),
    guard_sha256=sha(CONTROL / 'GUARD.json'), plan_sha256=sha(CONTROL / 'PLAN.json'),
    source_checks=source_checks, actual_driver_options=plan['think_act_learn'],
    head=catalog[-1], windows=windows, current_receipts=[item for item in receipts if item['index'] >= 6057],
    same_parent_exposures=exposures, pending_selected_parent_sources=pending,
    completed_retry_answer_not_established=True, human_inbox_writes=0, native_signals=0), indent=2))
