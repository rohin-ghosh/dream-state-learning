"""Bounded Parent-B operator using the existing attributed console/provider."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]
REMOTE = '/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1'
OUT = OWN / 'PARENT_B2'
REFERENCE = REPO / 'research_notes/analysis/ROHIN_C2_CONVERSATION_2026-09-17.md'
PART_ID = '63ee2eedd7d2420baa35e87864bd516b'
ARM = None
OPENING_MARKER = 'I am Astra, your new CREATIVE-B parent.'
OPENING = (
    'I am Astra, your new CREATIVE-B parent. You are a new copy with a fixed inherited checkpoint '
    'and conversation cut, not the continuing original C2. Our new environment is a private writing '
    'workshop: choose a scene or dialogue of your own, make a draft, and revise from actual feedback. '
    'Your drafts are retained exactly in your journal. No peer is connected. My feedback is an '
    'attributed parent judgment, not an objective quality score. I will demonstrate a small worked '
    'comparison using your own draft when helpful; you choose what to change. I guide your first '
    'three complete clone cycles, then withdraw for the next three. Choose a situation and two '
    'characters whose intentions differ, or propose your own scene; make a concrete first draft '
    'rather than only describing your plan. Use this selected THINK experiment:\n\n'
)


def write(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def remote(code):
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh',
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c '+shlex.quote(code)],
        cwd=REPO, capture_output=True, text=True, timeout=35)
    if result.returncode:
        raise RuntimeError(result.stderr[-800:])
    return json.loads(result.stdout)


def observe():
    return remote(f'''import hashlib,json,pathlib,time
root=pathlib.Path({REMOTE!r}); records=root/'life/stream/records'
def read(path):return json.loads(path.read_bytes())
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
text=(root/'R202_PART_ONE.txt').read_text()
report=dict(observed_unix=time.time(),complete_cycle=51,events=[],stages=[],drafts=[],part_render=None,parent_rendered=[],loaded=None,markers={{}})
responses={{}}
for path in sorted(records.glob('[0-9]'*20+'.json')):
 index=int(path.stem)
 if index<5847:continue
 record=read(path);document=record['document'];kind=record['kind']
 assert digest({{key:value for key,value in record.items() if key!='sha256'}})==record['sha256']
 stamp=path.stat().st_mtime
 ref=dict(index=index,sha256=record['sha256'],record_mtime_unix=stamp)
 if kind=='LOADED':report['loaded']=dict(ref,document=document)
 if kind=='SLEEP_COMPLETE' and document['status']=='COMPLETE':report['complete_cycle']=document['cycle']
 if kind=='INBOX':
  message=document['message'];report['events'].append(dict(actor=message['actor'],speaker=message.get('speaker'),text=message['text'],**ref))
 if kind=='REQUEST':
  messages=document.get('messages',[])
  rendered=chr(10).join(message.get('content','') for message in messages)
  if text in rendered and report['part_render'] is None:report['part_render']=dict(ref,started_unix=document.get('started_unix'),messages_sha256=digest(messages))
  if {OPENING_MARKER!r} in rendered:report['parent_rendered'].append(ref)
 if kind=='RESPONSE':
  item=dict(actor='child',text=document['response']['raw'],**ref)
  report['events'].append(item);responses[digest(document)]=item
 if kind=='R184_STAGE':
  report['stages'].append(dict(ref,stage=document['stage'],source_sha256=document['source_sha256']))
  if document['stage']=='ACT':
   assert document['source_sha256'] in responses
   report['drafts'].append(dict(responses[document['source_sha256']],cycle=report['complete_cycle']+1,source_sha256=document['source_sha256'],stage=ref))
control=root/'control'
if (root/'ACTIVE_CONTROL.json').exists():
 active=read(root/'ACTIVE_CONTROL.json');control=pathlib.Path(active['control_root'])
 assert control in {{root.parent/(root.name+'_r204')/'control',root.parent/(root.name+'_r206')/'control'}}
 assert hashlib.sha256((control/'GUARD.json').read_bytes()).hexdigest()==active['guard_sha256']
for name in ('ARMED.json','BOUNDARY.json','RETIRED.json','DISPATCHED.json','NO_BOUNDARY.json','control/EXIT.json','control/SERVICE_EXIT.json'):
 path=control/pathlib.Path(name).name if name.startswith('control/') else root/name
 if path.exists():report['markers'][name]=read(path)
report['handoff_failure']=[read(path) for path in root.glob('HANDOFF_FAILURE_*.json')]
report['events']=report['events'][-8:]
print(json.dumps(report))
''')


def parent_payload(text):
    return re.sub(r'\A(?:\s*Astra\s*:\s*)+', '', text)


def publish(text, kind):
    supplied_sha256 = hashlib.sha256(text.encode()).hexdigest()
    text = parent_payload(text)
    return remote(f'''import hashlib,json,pathlib,sys,time
root=pathlib.Path({REMOTE!r});sys.path.insert(0,str(root/'source'))
from gpu.orch_r127_pilot_console import publish_parent
latest=51
for path in reversed(sorted((root/'life/stream/records').glob('[0-9]'*20+'.json'))):
 record=json.loads(path.read_bytes())
 if record['kind']=='SLEEP_COMPLETE':latest=record['document']['cycle'];break
assert latest<54,'parent withdrawn after first three complete clone cycles'
intent=root/{(kind+'_INTENT.json')!r}
with intent.open('x') as output:json.dump(dict(text_sha256=hashlib.sha256({text!r}.encode()).hexdigest(),supplied_text_sha256={supplied_sha256!r},cycle_at_publication=latest+1,created_unix=time.time()),output)
receipt=publish_parent(str(root/'life'),'Astra',{text!r})
receipt.update(published_unix=time.time(),kind={kind!r},cycle_at_publication=latest+1,attribution='Astra',quality_score=None,payload_text={text!r},supplied_text_sha256={supplied_sha256!r},speaker_prefix_owner='existing_journal')
with (root/{(kind+'_PUBLICATION.json')!r}).open('x') as output:json.dump(receipt,output,sort_keys=True)
print(json.dumps(receipt))
''')


def main():
    sys.path.insert(0, str(REPO))
    from gpu.orch_route_parent_campaign_providers import strong
    OUT.mkdir(mode=0o700, exist_ok=True)
    structured = (REPO/'research_notes/analysis/R202_STRUCTURED_THINK_2026-09-17.txt').read_text()
    assert hashlib.sha256(structured.encode()).hexdigest() == 'f02fa3a6bd229b521392d13559c37252ab505810dd7623d3352931b685ebf621'
    if ARM is not None and not ARM['structured']:
        structured = ''
    if not (OUT/'STARTED.json').exists():
        write(OUT/'STARTED.json', dict(pid=os.getpid(),started_unix=time.time(),no_peer_treatment=True,
            guided_complete_cycles=[52,53,54],withdrawn_complete_cycles=[55,56,57],provider='existing_strong_parent'))
    started = json.loads((OUT/'STARTED.json').read_text())
    reference_bytes = REFERENCE.read_bytes()
    write(OUT/('REFERENCE_BINDING_'+str(time.time_ns())+'.json'), dict(pid=os.getpid(),
        observed_unix=time.time(),path=str(REFERENCE),sha256=hashlib.sha256(reference_bytes).hexdigest(),
        scope='forward-only parent reference; no child-history import or retrospective learning'))
    opened = (OUT/'OPENING_PUBLICATION.json').exists()
    seen = {int(directory.name.removeprefix('DRAFT_')) for directory in OUT.glob('DRAFT_*') if directory.is_dir()}
    deadline = started['started_unix']+10800
    previous_head = None
    while time.time()<deadline:
        state = observe()
        head = (state['complete_cycle'],len(state['stages']),bool(state['loaded']),bool(state['part_render']),len(state['parent_rendered']),tuple(state['markers']))
        if head != previous_head:
            write(OUT/('OBSERVE_'+str(time.time_ns())+'.json'),state)
            previous_head = head
        if state['handoff_failure'] or 'NO_BOUNDARY.json' in state['markers']:
            write(OUT/'OPERATOR_BLOCKER.json',state)
            return
        if state['part_render'] and not (OUT/'ROHIN_FIRST_RENDER.json').exists():
            write(OUT/'ROHIN_FIRST_RENDER.json',state['part_render'])
        if state['loaded'] and not (OUT/'LOADED.json').exists():
            assert state['loaded']['document']['optimizer_steps']==4908
            write(OUT/'LOADED.json',state['loaded'])
        if state['parent_rendered'] and not (OUT/'PARENT_FIRST_RENDER.json').exists():
            write(OUT/'PARENT_FIRST_RENDER.json',state['parent_rendered'][0])
        if not opened and state['part_render'] and state['complete_cycle']<54:
            opening = OPENING+structured
            if ARM is not None and ARM['physical'] == 3:
                excerpt = remote(f'''import hashlib,json,pathlib,time
root=pathlib.Path({REMOTE!r});name='gpu/orch_r153_community_transport.py'
payload=(root/'source'/name).read_bytes();sha=hashlib.sha256(payload).hexdigest()
assert json.loads((root/'R203_SOURCE.json').read_bytes())['source_pins'][name]==sha
lines=payload.decode().splitlines();start=next(index for index,line in enumerate(lines) if line.startswith('def code_route('))
selected=lines[start:start+20]
print(json.dumps(dict(path=name,sha256=sha,start_line=start+1,end_line=start+len(selected),text=chr(10).join(selected),observed_unix=time.time(),read_only=True)))''')
                write(OUT/'REPO_OPENING_SOURCE.json',excerpt)
                opening += ('\nActual read-only source receipt, '+excerpt['path']+':'+str(excerpt['start_line'])+
                    ', SHA256 '+excerpt['sha256']+':\n```python\n'+excerpt['text']+'\n```\n'
                    'Propose one falsifiable routing hypothesis from these exact lines. '
                    'Distinguish source inference from an execution result; no repository command was run.')
            write(OUT/'OPENING_SOURCE.json',dict(text=opening,authorship='Builder/Astra opening',structured_text_sha256=hashlib.sha256(structured.encode()).hexdigest()))
            write(OUT/'OPENING_PUBLICATION.json',publish(opening,'PARENT_B_OPENING'))
            opened=True
        for draft in state['drafts']:
            if draft['index'] in seen:
                continue
            seen.add(draft['index'])
            directory=OUT/('DRAFT_'+str(draft['index']))
            directory.mkdir()
            write(directory/'SOURCE.json',draft)
            if state['complete_cycle']>=54 or draft['cycle']>54:
                write(directory/'WITHDRAWN.json',dict(no_parent_call=True,cycle=draft['cycle']))
                continue
            role = ('You are Astra, the real conversational parent of '+ARM['name']+'. '+ARM['task']+' '
                if ARM is not None else 'You are Astra, the real conversational Parent B of a CREATIVE-B clone. ')
            guidance = ('Give compact feedback grounded in the actual ACT and returned evidence. '
                'If the child only describes a plan, ask it to carry out a concrete next step. '
                'Do not invent results, repository access, edits, tests, peers or executions. '
                if ARM is not None and not ARM['name'].startswith('CREATIVE') else
                'Give a concise worked comparison grounded in this actual scene/dialogue draft: quote a short '
                'piece, state your tentative reader judgment, show one small possible revision, and invite '
                'the child to choose and enact its next revision. ')
            instruction=(role+guidance+
                'This is attributed parent feedback, NOT '
                'an objective quality score or retention result. No peers or unseen audience exist. '
                'Do not fabricate executions or observations. The journal supplies your Astra speaker '
                'label; do not start the message with Astra:. Return only JSON with speak(boolean), '
                'message(string, at most90 words), rationale(short string). If silent, message must be empty. '
                'The clean Rohin/C2 conversation is a reference containing their actual words, not evaluator '
                'judgments or this clone\'s own experience. Do not import it into child history, reenact '
                'original-C2 story-test instructions, or treat it as retroactive learning. '
                'The selected THINK instruction is context, not a required repetitive parent checklist:\n'+structured)
            reference_bytes = REFERENCE.read_bytes()
            reference = dict(path=str(REFERENCE),sha256=hashlib.sha256(reference_bytes).hexdigest(),
                text=reference_bytes.decode())
            write(directory/'CALL_INTENT.json',dict(started_unix=time.time(),attempts=1,source_sha256=draft['source_sha256'],
                parent_reference_path=reference['path'],parent_reference_sha256=reference['sha256']))
            try:
                response,model,usage=strong(json.dumps(dict(actual_draft=draft,recent_events=state['events'],
                    clean_rohin_c2_conversation=reference),ensure_ascii=False),directory,
                    min(deadline,time.time()+120),instruction,reasoning_effort='high')
                result=dict(response=response,actual_model=model,usage=usage,finished_unix=time.time(),quality_score=None,
                    parent_reference_path=reference['path'],parent_reference_sha256=reference['sha256'])
                current=observe()
                if response['speak'] and current['complete_cycle']<54:
                    result['publication']=publish(response['message'],'PARENT_B_FEEDBACK_'+str(draft['index']))
                else:
                    result['status']='SILENT_OR_WITHDRAWN_NO_PUBLICATION'
                write(directory/'RESULT.json',result)
            except Exception as error:
                write(directory/'FAILED_NO_RETRY.json',dict(error_type=type(error).__name__,source_sha256=draft['source_sha256']))
        if state['complete_cycle']>=54 and not (OUT/'WITHDRAWN.json').exists():
            write(OUT/'WITHDRAWN.json',dict(observed_unix=time.time(),complete_cycle=state['complete_cycle'],no_further_parent_publications=True))
        if 'control/EXIT.json' in state['markers'] or state['complete_cycle']>=57:
            write(OUT/'SCREEN_OBSERVATION_END.json',state)
            return
        time.sleep(3)
    write(OUT/'BOUNDED_OBSERVER_END.json',dict(observed_unix=time.time(),reason='three_hour_bound',no_quality_claim=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(2, 3, 4, 5))
    arguments = parser.parse_args()
    if arguments.physical is not None:
        ARM = next(item for item in json.loads((OWN/'R203_SELECTED_ARMS.json').read_text())['arms']
            if item['physical'] == arguments.physical)
        REMOTE = ARM['remote_root']
        OUT = OWN/('PARENT_R203_SLOT'+str(arguments.physical))
        OPENING_MARKER = 'I am Astra, your new '+ARM['name']+' parent.'
        OPENING = (OPENING_MARKER+' You are a new copy at a fixed inherited checkpoint and console cut, '
            'not the continuing original C2. This is your own new environment. '+ARM['task']+' '
            'A confined standard-library Python tool is available through a verified CPU bridge, '
            'without network, GPU, home access, SymPy, mpmath or Torch. Only a returned receipt '
            'establishes execution. No peer is connected. I offer compact attributed guidance for '
            'your first three completed clone cycles, then withdraw for three; your own work continues. '
            'Choose a small concrete question or draft and act on it. '+
            ('Use this selected structured THINK instruction:\n\n' if ARM['structured'] else
             'Your THINK is open; you choose how to reason.\n'))
    main()
