"""Bounded read-only process and journal receipts; no response prose export."""

import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


REMOTE = r'''
import datetime,hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1/math_d1')
def read(path):return json.loads(path.read_bytes())
def identity(pid):
    process=pathlib.Path('/proc')/str(pid)
    try:
        stat=(process/'stat').read_text().rsplit(')',1)[1].split()
        return dict(pid=int(pid),state=stat[0],start_ticks=stat[19],uid=process.stat().st_uid,
            cwd=os.readlink(process/'cwd'),ppid=int(stat[1]))
    except OSError:return dict(pid=int(pid),present=False)
actors={}
if (root/'STARTED.json').exists():
    for name,entry in read(root/'STARTED.json')['processes'].items():
        actual=identity(entry['pid'])
        actual['same_start_ticks']=actual.get('start_ticks')==entry['start_ticks']
        actors[name]=actual
for process in pathlib.Path('/proc').iterdir():
    if not process.name.isdigit():continue
    try:
        if process.stat().st_uid!=2524:continue
        arguments=(process/'cmdline').read_bytes().decode().split('\0')
        if str(root/'control/GUARD.json') in arguments and 'native' in arguments and 'timeout' not in arguments[0]:
            actors['native']=identity(process.name)
    except (OSError,UnicodeError):pass
receipts={}
for name in ['LAUNCH.json','EXIT.json','FAILED.json','OUTER_FAILED.json','OUTER_EXIT.json','PRE_SERVICE_ADMISSION.json','CONFINEMENT_CHILD.json']:
    path=root/'control'/name
    if path.exists():
        document=read(path)
        if name=='PRE_SERVICE_ADMISSION.json':
            report=document['report'];document=dict(verified_unix=document['verified_unix'],clear=report['clear'],blocking_reasons=report['blocking_reasons'])
        elif name=='CONFINEMENT_CHILD.json':document={key:document[key] for key in ['observed_unix','pid','gpu_uuid','target_minor','checks']}
        receipts[name]=document
events=[]
paths=sorted((root/'raw/stream/records').glob('*.json'))
for path in paths[-120:]:
    if path.name.endswith('.intent.json'):continue
    with path.open('rb') as handle:
        handle.seek(max(0,path.stat().st_size-4096));tail=handle.read()
    metadata=json.loads(b'{'+tail[tail.rfind(b',"index":')+1:])
    if metadata['index']<5847:continue
    row={key:metadata[key] for key in ['index','kind','sha256']}
    row['mtime_utc']=datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat()
    kind=metadata['kind']
    if kind in ['LOADED','INBOX','R184_STAGE','R184_GENERATION','R184_TRANSITION','R184_LEARN_COMPLETE','SLEEP_COMPLETE','SLEEP_RECIPE','TARGET_ELIGIBILITY','UPDATE','TERMINAL','REQUEST','RESPONSE']:
        document=read(path)['document']
        if kind=='LOADED':row.update({key:document.get(key) for key in ['pid','optimizer_steps','adapter_sha256','loaded_unix','resume']})
        elif kind=='INBOX':row.update(speaker=document['message'].get('speaker'),message_id=document['message']['id'],text_sha256=hashlib.sha256(document['message']['text'].encode()).hexdigest())
        elif kind in ['SLEEP_RECIPE','TARGET_ELIGIBILITY','SLEEP_COMPLETE','UPDATE']:
            row.update({key:document[key] for key in ['cycle','status','new_rows','new_presentations','selected_old_rows','available_old_rows','optimizer_step','optimizer_steps','optimizer_steps_before','optimizer_steps_after','updates','finished_unix'] if key in document})
            if 'excluded_rows' in document:row['excluded_rows_count']=len(document['excluded_rows'])
            if 'excluded' in document:row['excluded_count']=len(document['excluded'])
            for key in ['learn_review_filter','code_target_filter_receipt']:
                if isinstance(document.get(key),dict):row[key]={name:document[key][name] for name in ['candidate_counts','retained_counts','excluded_counts','policy'] if name in document[key]}
            if kind=='TARGET_ELIGIBILITY':row['fields']=list(document)
        else:
            row.update({key:document[key] for key in ['stage','segment','cycle','status','started_unix','finished_unix','stage_tokens'] if key in document})
            if kind=='RESPONSE':
                response=document.get('response',{})
                row['raw_response_present']=isinstance(response.get('raw'),str)
                if row['raw_response_present']:row['raw_characters']=len(response['raw'])
        events.append(row)
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=12)
output=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actors=actors,receipts=receipts,
    events=events,nvml_processes=gpu.stdout.strip().splitlines(),read_only=True)
print(json.dumps(output))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(REMOTE)],
        capture_output=True, text=True, timeout=30, check=True)
    document = json.loads(result.stdout)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = Path(__file__).resolve().parent / 'receipts' / ('LIVE_' + stamp + '.json')
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in json.dumps(document, indent=2).splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)
    print(json.dumps(document))


if __name__ == '__main__':
    main()
