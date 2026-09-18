"""Finite actual Astra parent, bound to repaired birth1 and fresh TRAIN evidence."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
ORIGINAL = REPOSITORY / 'research_loop/workers/rohin183_repo_learning_20260917'
REFERENCE = REPOSITORY / 'research_notes/analysis/ROHIN_C2_CONVERSATION_2026-09-17.md'
OUTPUT = HERE / 'birth1_parent_r204'
ROOT = '/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1'
HANDOFF = ROOT + '/r204_boundary_20260918t0356z'


def write(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)


REMOTE = r'''
import pathlib,json,os,hashlib
root=pathlib.Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
new=root/'r204_boundary_20260918t0356z'
result=dict(ready=False,events=[],responses=[],rendered=[])
if (new/'DISPATCHED.json').exists():
 paths=sorted((root/'life/stream/records').glob('[0-9]'*20+'.json'))
 boundary=json.loads((new/'BOUNDARY.json').read_bytes())['index']
 loaded=None
 for path in paths[-100:]:
  with path.open('rb') as stream:stream.seek(max(0,path.stat().st_size-4096));tail=stream.read()
  meta=json.loads(b'{'+tail[tail.rfind(b',"index":')+1:])
  if meta['index']<=boundary or meta['kind'] not in ['LOADED','INBOX','REQUEST','RESPONSE']:continue
  record=json.loads(path.read_bytes());doc=record['document'];reference=dict(record_index=record['index'],record_sha256=record['sha256'])
  if meta['kind']=='LOADED':loaded=dict(pid=doc['pid'],**reference)
  elif meta['kind']=='RESPONSE':
   result['responses'].append(record['index'])
   raw=doc['response'].get('raw')
   if isinstance(raw,str):result['events'].append(dict(actor='child',text=raw[:6000],**reference))
  elif meta['kind']=='INBOX':
   message=doc['message']
   result['events'].append(dict(actor=message['actor'],speaker=message.get('speaker'),text=message['text'][:6000],**reference))
  elif meta['kind']=='REQUEST':
   for message in WAITING:
    if any('Astra: '+message['message'] in entry.get('content','') for entry in doc['messages']):
     result['rendered'].append(dict(id=message['id'],all_history_tokens_masked=doc.get('render_receipt',{}).get('all_history_tokens_masked'),**reference))
 if loaded:
  process=pathlib.Path('/proc')/str(loaded['pid'])
  result['ready']=process.exists() and str(new/'control/GUARD.json') in (process/'cmdline').read_bytes().decode().split('\0')
  result['loaded']=loaded
 result['events']=result['events'][-8:]
print(json.dumps(result))
'''


def main():
    sys.path.insert(0, str(REPOSITORY))
    from gpu.orch_r133_programme_parent import prompt, publish
    from gpu.orch_route_parent_campaign_providers import strong, STRONG
    reference = REFERENCE.read_bytes()
    assert hashlib.sha256(reference).hexdigest() == '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d'
    assert json.loads((ORIGINAL / 'parent1/EXIT.json').read_bytes())['calls_reserved'] == 12
    assert os.environ.get('NVIDIA_API_KEY'), 'existing_provider_environment_required_no_key_export'
    config = json.loads((ORIGINAL / 'PARENT_CONFIG.json').read_bytes())
    config.update(source_root=HANDOFF + '/source', maximum_calls=3,
        parent_style='Responsive repository evidence; renderer has been repaired, not a claim the child was incapable')
    OUTPUT.mkdir(mode=0o700)
    write(OUTPUT / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), status='WAITING_REPAIRED_LOADED_AND_NEW_RESPONSE',
        model=STRONG, maximum_new_calls=3, previous_parent_calls=12, reference_bytes=len(reference),
        reference_sha256=hashlib.sha256(reference).hexdigest(), reference_bulk_pasted=False,
        provider_key_exported=False, original_parent_preserved=True))
    waiting = []
    seen_rendered = set()
    calls = 0
    last_response = None
    last_call = 0
    deadline = min(config['hard_end_unix'] - 125, time.time() + 1500)
    while time.time() < deadline:
        program = REMOTE.replace('for message in WAITING:', 'for message in ' + repr(waiting) + ':')
        result = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx_ssh.sh'), '/usr/bin/python3 -B -c ' + shlex.quote(program)],
            capture_output=True, text=True, timeout=30, check=True)
        snapshot = json.loads(result.stdout)
        for rendered in snapshot['rendered']:
            if rendered['id'] not in seen_rendered:
                write(OUTPUT / ('RENDERED_' + rendered['id'] + '.json'), dict(rendered, observed_unix=time.time()))
                seen_rendered.add(rendered['id'])
        new_responses = [index for index in snapshot['responses'] if last_response is None or index > last_response]
        pending = any(message['id'] not in seen_rendered for message in waiting)
        if snapshot['ready'] and not pending and calls < 3 and len(new_responses) >= (1 if calls == 0 else 3) and time.time() - last_call >= 300:
            directory = OUTPUT / f'call_{calls:03d}'
            directory.mkdir()
            state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=snapshot['events'])
            instruction, payload = prompt(config, state)
            instruction += ('\nParent-only clean reference follows. Read it in full as background; do not copy its creative test, '
                'future original-C2 exchanges, or bulk reference passages to this child. Respond to this child’s actual current '
                'repository work and returned tool observations. Distinguish the prior visibility bug from learner capability.\n' + reference.decode())
            write(directory / 'SOURCE.json', snapshot)
            write(directory / 'INTENT.json', dict(started_unix=time.time(), retry=False, model=STRONG))
            calls += 1
            last_response = max(new_responses)
            last_call = time.time()
            response, model, usage = strong(payload, directory, min(config['hard_end_unix'], time.time() + 125), instruction, reasoning_effort='medium')
            write(directory / 'RESPONSE.json', dict(response=response, model=model, usage=usage, finished_unix=time.time()))
            if response['speak']:
                publication = publish(REPOSITORY, config, response['message'])
                write(directory / 'PUBLICATION.json', dict(publication=publication, published_unix=time.time(), rendered=False))
                waiting.append(dict(id=publication['id'], message=response['message']))
            else:
                write(directory / 'SILENT.json', dict(observed_unix=time.time(), rationale=response.get('rationale')))
        if calls == 3 and not pending:
            break
        time.sleep(3)
    write(OUTPUT / 'EXIT.json', dict(finished_unix=time.time(), calls_reserved=calls, rendered_ids=sorted(seen_rendered), no_retry=True))


if __name__ == '__main__':
    main()
