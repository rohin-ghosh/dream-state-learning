"""Reattach C2's existing Astra provider/configuration with the R202 policy brief."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[5]
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(HERE.parents[1]))
from gpu import orch_r133_programme_parent as parent
from gpu import orch_route_parent_campaign_providers as providers
from provider_route import routed
from console_baseline import parent_census


def snapshot(repository, config):
    script = '''import hashlib,json,re
from pathlib import Path
root=Path(ROOT)
paths=sorted((root/'stream/records').glob('[0-9]'*20+'.json'))
catalog=[]
for path in paths:
 with path.open('rb') as handle:
  handle.seek(max(0,path.stat().st_size-4096));raw=handle.read()
 item=json.loads(b'{'+raw[raw.rfind(b',"index":')+1:]);catalog.append(item)
commits=[item for item in catalog if item['kind'] in ('COMMITTED','CONTEXT_COMMITTED','CONTEXT_INPUT','SLEEP_COMPLETE','COMPACTION')]
cut=commits[-1]['index']
visible=[item for item in catalog if item['index']<=cut]
events=[];consumed={};boundaries=[];parent_consumptions=[];response_count=0;request_count=0
recent=[item['index'] for item in visible if item['kind'] in ('RESPONSE','INBOX')][-12:]
for item in visible:
 kind=item['kind'];index=item['index']
 if kind=='REQUEST':
  request_count+=1
  if boundaries and boundaries[-1]['next_request_index'] is None:boundaries[-1]['next_request_index']=index
 if kind=='RESPONSE':
  response_count+=1;boundaries.append(dict(response_count=response_count,record_index=index,next_request_index=None))
 if kind=='INBOX' or index in recent:
  record=json.loads(paths[index].read_bytes());document=record['document']
  assert record['sha256']==hashlib.sha256(json.dumps({key:value for key,value in record.items() if key!='sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
  if kind=='INBOX':
   message=document['message'];consumed[message['id']]=dict(record_index=index,record_sha256=record['sha256'])
   if message['actor']=='parent':parent_consumptions.append(dict(record_index=index,speaker=message.get('speaker'),inbox_id=message['id']))
   if index in recent:events.append(dict(actor=message['actor'],speaker=message.get('speaker'),text=message['text'],record_index=index,record_sha256=record['sha256']))
  elif kind=='RESPONSE':events.append(dict(actor='child',text=document['response']['raw'],record_index=index,record_sha256=record['sha256']))
print(json.dumps(dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1',response_count=response_count,request_count=request_count,
 record_count=cut+1,head_sha256=commits[-1]['sha256'],events=events,consumed_inbox=consumed,
 boundaries=boundaries,parent_consumptions=parent_consumptions,committed_context_cut=cut)))
'''.replace('ROOT', repr(config['root']))
    return parent.remote(repository, config, script)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--policy-addendum', type=Path)
    parser.add_argument('--immediate-new-source', action='store_true')
    parser.add_argument('--priority-policy-update', action='store_true')
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_bytes())
    require = parent.require
    require(config['root'] == '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life', 'same_original_C2_parent')
    require(parent_census(config['root'], os.getpid()) == [], 'no_second_C2_parent')
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'existing_provider_credential_privately_present')
    lock_path = Path(config['existing_parent_lock'])
    descriptor = os.open(lock_path, os.O_RDONLY | os.O_NOFOLLOW)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    original = providers.strong

    def strong(prompt, directory, deadline, instruction=providers.SYSTEM, *, reasoning_effort=None):
        return routed(original, directory)(prompt, directory, deadline, instruction, reasoning_effort=reasoning_effort)

    original_publish = parent.publish

    def publish(repository, binding, message):
        require(not re.search(r'(?i)\bn\s*=\s*4\b|\b354\b|\bV\s*=\s*3\b', message), 'no_math_answer_or_followup_hint')
        return original_publish(repository, binding, message)

    parent.snapshot = snapshot
    parent.strong = strong
    parent.publish = publish
    if arguments.policy_addendum:
        original_prompt = parent.prompt
        addendum = arguments.policy_addendum.read_text()

        def prompt(binding, state):
            instruction, payload = original_prompt(binding, state)
            return instruction + '\n\nCurrent operator-relayed parent policy:\n' + addendum, payload

        parent.prompt = prompt
    require(not (arguments.immediate_new_source and arguments.priority_policy_update),
        'one_explicit_parent_priority_source')
    if arguments.priority_policy_update:
        require(arguments.policy_addendum is not None, 'explicit_new_parent_policy_required')
    if arguments.immediate_new_source or arguments.priority_policy_update:
        original_cursor = parent.resume_cursor

        def resume_cursor(binding):
            reserved = original_cursor(binding)
            current = snapshot(REPOSITORY, binding)['response_count']
            require(current >= reserved if arguments.priority_policy_update else current > reserved,
                'new_policy_may_revisit_current_source_without_replaying_prior_publication')
            return current - binding['cadence_responses']

        parent.resume_cursor = resume_cursor
    try:
        parent.serve(arguments.config, REPOSITORY, arguments.output)
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    main()
