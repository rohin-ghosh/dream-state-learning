"""Bounded fresh-wrapper receipt reporting; no provider calls or child signals."""

from datetime import datetime
import json
from pathlib import Path
import subprocess
import time

import node3_route_binding as route
import snapshot_transport
import takeover as base

OUTPUT = base.HERE / 'r181/first_receipts'
REMOTE = '/localhome/local-rohing/research_loop/workers/rohin174_parenting_20260917/node3/r181'
NAMES = {0: 'support_free', 1: 'creative_reread', 2: 'brain_free', 3: 'brain_guided', 4: 'creative_free', 7: 'creative_select'}


def post(message):
    path = base.REPO / 'research_loop/COORDINATION.md'
    context = path.read_text().splitlines()[-4:]
    text = '\n## [Builder/node3 — actual per-life receipt] ' + datetime.now().astimezone().isoformat() + '\n\n' + message + '\n'
    patch = '*** Begin Patch\n*** Update File: ' + str(path) + '\n@@\n'
    patch += ''.join(' ' + line + '\n' for line in context)
    patch += ''.join('+' + line + '\n' for line in text.splitlines())
    patch += '*** End of File\n*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)


def remote(publications):
    script = 'root=' + repr(REMOTE) + '\npublications=' + repr(publications) + '\n'
    script += '''
import hashlib,json,re,time
from pathlib import Path
rows=[]
for physical in (0,1,2,3,4,7):
 folder=Path(root)/('physical'+str(physical));spec=json.loads((folder/'LIVE_HANDOFF.json').read_text())
 row=dict(physical=physical)
 for name in ('WAIT_FAILED.json','PREPARE_FAILED.json','CONTAINED_FAILED.json','WAIT_EXPIRED.json','EXIT.json'):
  if (folder/name).exists():row[name]=json.loads((folder/name).read_text())
 if (folder/'BOUNDARY.json').exists():
  boundary=json.loads((folder/'BOUNDARY.json').read_text())
  row['boundary']=dict(path=str(folder/'BOUNDARY.json'),sha256=hashlib.sha256((folder/'BOUNDARY.json').read_bytes()).hexdigest(),index=boundary['record']['index'],cycle=boundary['record']['document']['cycle'],observed_unix=boundary['observed_unix'])
  paths=sorted(path for path in (Path(spec['backing_root'])/'stream/records').glob('*.json') if re.fullmatch(r'\\d{20}\\.json',path.name) and int(path.stem)>boundary['record']['index'])
  for path in paths:
   record=json.loads(path.read_text())
   if record['kind'] in ('LOADED','SLEEP_RECIPE') and record['kind'] not in row:
    row[record['kind']]=dict(path=str(path),record=record,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),file_mtime_unix=path.stat().st_mtime)
   if 'SLEEP_RECIPE' in row:break
 publication=publications.get(physical)
 if publication:
  path=Path(spec['backing_root'])/'stream/inbox'/(publication['id']+'.json')
  if path.exists():
   document=json.loads(path.read_text())
   assert document['actor']=='parent' and document['split']=='TRAIN'
   row['publication']=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),inbox_id=document['id'],file_mtime_unix=path.stat().st_mtime)
 rows.append(row)
print(json.dumps(dict(rows=rows,observed_unix=time.time())))
'''
    result = subprocess.run(['bash', str(base.REPO / 'gpu/ovx2_ssh.sh'), 'python3 -B -'],
        input=script, capture_output=True, text=True, timeout=60)
    base.require(result.returncode == 0, 'fresh_wrapper_receipt_read')
    return json.loads(result.stdout)


def request_proof(physical, inbox_id, record_index):
    script = 'physical=' + repr(physical) + '\ninbox_id=' + repr(inbox_id) + '\nrecord_index=' + repr(record_index) + '\n'
    script += '''
import json,hashlib,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2')/('control'+str(physical))/'run1/stream'
inbox=json.loads((root/'inbox'/(inbox_id+'.json')).read_text())
path=root/'records'/('%020d.json'%record_index);record=json.loads(path.read_text());document=record['document']
assert record['kind']=='REQUEST' and inbox['actor']=='parent' and inbox['split']=='TRAIN'
messages=[dict(position=index,message=message) for index,message in enumerate(document['messages']) if inbox['text'] in message.get('content','')]
assert messages and document['render_receipt']['all_history_tokens_masked'] is True
print(json.dumps(dict(path=str(path),record_sha256=record['sha256'],record_index=record_index,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),file_mtime_unix=path.stat().st_mtime,started_unix=document.get('started_unix'),matching_parent_messages=messages,render_receipt=document['render_receipt'],observed_unix=time.time())))
'''
    result = subprocess.run(['bash', str(base.REPO / 'gpu/ovx2_ssh.sh'), 'python3 -B -'],
        input=script, capture_output=True, text=True, timeout=60)
    base.require(result.returncode == 0, 'exact_rendered_request_read')
    return json.loads(result.stdout)


def main():
    base.write(OUTPUT / 'STARTED.json', dict(pid=__import__('os').getpid(), observed_unix=time.time(),
        stop_unix=base.HARD_END, only_readonly_remote_calls=True, no_provider_calls=True, no_signals=True))
    cursors = {}
    while time.time() < base.HARD_END:
        candidates = {}
        for physical in base.PHYSICALS:
            folder = route.folder_for(physical)
            for attempt in sorted((folder / 'parent').glob('parent_*')):
                if not (attempt / 'PROVIDER_COMPLETION.json').exists() or not (attempt / 'RESULT.json').exists():
                    continue
                result = base.read(attempt / 'RESULT.json')
                if result['status'] == 'PUBLISHED':
                    candidates[physical] = dict(attempt=str(attempt), result=result, result_ref=base.reference(attempt / 'RESULT.json'))
                    break
        observed = remote({physical: row['result']['publication'] for physical, row in candidates.items()})
        for row in observed['rows']:
            physical = row['physical']
            for kind in ('boundary', 'LOADED', 'SLEEP_RECIPE'):
                destination = OUTPUT / (kind + '_' + str(physical) + '.json')
                if kind not in row or destination.exists():
                    continue
                base.write(destination, dict(physical=physical, observed_unix=observed['observed_unix'], evidence=row[kind]))
                if kind == 'SLEEP_RECIPE':
                    recipe = row[kind]['record']['document']
                    base.require(recipe['policy'] == 'R181_NEW_ONLY_V1' and recipe['selected_old_rows'] == 0
                                 and recipe['new_presentations'] == 16, 'actual_new_only_sleep_recipe')
                    post(f"{NAMES[physical]} first actual **SLEEP_RECIPE**: {json.dumps(recipe, sort_keys=True)}; record{row[kind]['record']['index']} SHA{row[kind]['record']['sha256']}, recorded {datetime.fromtimestamp(row[kind]['file_mtime_unix']).astimezone().isoformat()}. Exact receipt `{destination.relative_to(base.REPO)}`. This proves the selected recipe, not completed updates or a learning outcome. Same R179 backing state and pending inboxes preserved;16:50 stop/17:00 ceiling unchanged.")
            for kind in ('WAIT_FAILED.json', 'CONTAINED_FAILED.json', 'WAIT_EXPIRED.json'):
                destination = OUTPUT / (kind[:-5] + '_' + str(physical) + '.json')
                if kind in row and not destination.exists():
                    base.write(destination, row[kind])
                    post(f"{NAMES[physical]} operational receipt `{destination.relative_to(base.REPO)}`: {json.dumps(row[kind], sort_keys=True)}. No automatic retry or learner reset; inspect exact saved-boundary custody before further action.")
            if physical not in candidates or 'publication' not in row:
                continue
            candidate = candidates[physical]
            publication = candidate['result']['publication']
            base.require(row['publication']['sha256'] == publication['sha256'], 'actual_published_inbox_bytes')
            published = OUTPUT / ('PROVIDER_PUBLISHED_' + str(physical) + '.json')
            if not published.exists():
                base.write(published, dict(candidate=candidate, actual_inbox=row['publication'], observed_unix=observed['observed_unix']))
                post(f"{NAMES[physical]} first genuine post-rebind provider **PUBLISHED** inbox `{publication['id']}` at {datetime.fromtimestamp(row['publication']['file_mtime_unix']).astimezone().isoformat()}; actual model `{candidate['result']['model']}`. Source/provider/result and actual inbox-byte receipts `{published.relative_to(base.REPO)}`. Rendering not yet asserted; no shared-baseline resend.")
            rendered = OUTPUT / ('PROVIDER_RENDERED_' + str(physical) + '.json')
            if rendered.exists():
                continue
            if physical not in cursors:
                cursors[physical] = base.read(route.folder_for(physical) / 'LIVE_BOOTSTRAP_READY.json')['cursor']
            snapshot = snapshot_transport.poll(physical, cursors[physical])
            cursors[physical] = snapshot['cursor']
            delivery = snapshot['snapshot']['delivered'].get(publication['id'])
            if delivery:
                proof = request_proof(physical, publication['id'], delivery['record_index'])
                base.require(proof['record_sha256'] == delivery['record_sha256'], 'reducer_actual_request_binding')
                base.write(rendered, dict(publication=base.reference(published), delivered=delivery,
                    actual_request=proof, observed_unix=time.time(), journal_id=snapshot['snapshot']['journal_id']))
                post(f"{NAMES[physical]} genuine provider turn `{publication['id']}` now **RENDERED**, exact TRAIN REQUEST{delivery['record_index']} SHA{delivery['record_sha256']}, sleep{delivery['sleep_count']}, request started {datetime.fromtimestamp(proof['started_unix']).astimezone().isoformat()}. `{rendered.relative_to(base.REPO)}` contains actual framed parent message and masked render proof. Render exposure is not a learned-outcome claim.")
        time.sleep(min(30, max(0, base.HARD_END - time.time())))
    base.write(OUTPUT / 'TERMINAL.json', dict(status='UNCHANGED_1650_OBSERVER_STOP', observed_unix=time.time()))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        base.write(OUTPUT / 'OBSERVER_FAILED.json', dict(error_type=type(error).__name__, reason=str(error)[:500], observed_unix=time.time()))
        raise
