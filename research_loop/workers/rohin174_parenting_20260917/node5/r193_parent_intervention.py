"""One explicitly authorized original-C2 parent publication; read-only observation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
ARTIFACTS = HERE / "R193_PARENT_INTERVENTION_20260917T1759PDT"
TEXT = (
    "R193 current-evidence intervention.\n\n"
    "Your earlier missing-SymPy result came from the old environment; the current tool "
    "includes SymPy. Your first recovered receipt reported SyntaxError at /job.py:7, "
    "`.S_3_correct = 98`; parsing failed before an import. Your newer run exited "
    "successfully, but stdout was empty: that receipt did not show a value for V. "
    "What from your last attempt remains useful? What does the real evidence tell you "
    "to change? Make your next attempt implement your decision using a small "
    "calculation that runs here and prints its result. Before executing, check in one "
    "line that your action incorporates that change. Inspect the actual output and "
    "carry it forward; distinguish what you observed from what you inferred."
)
REMOTE = r'''
import hashlib,json,os,re,sys,time
from pathlib import Path

root=Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
control=Path('/localhome/local-rohing/orch_r153_r193_C2_20260917_recovery1')
directory=control/'parent_intervention_R193_20260917T1759PDT'
source=control/'source'
console=source/'gpu/orch_r127_pilot_console.py'
expected_console='be7cfab563dcfe31590329e930b73238e26d39c7b03eb16c1859cc3e91f0b683'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def store(path,document):
 raw=(json.dumps(document,sort_keys=True,indent=2)+'\n').encode()
 descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(descriptor,'wb') as stream:
  stream.write(raw);stream.flush();os.fchmod(stream.fileno(),0o400);os.fsync(stream.fileno())
 descriptor=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(descriptor)
 finally:os.close(descriptor)
def read(path):
 document=json.loads(path.read_bytes())
 digest=hashlib.sha256(json.dumps({key:value for key,value in document.items() if key!='sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 assert document['sha256']==digest
 assert document['journal_id']=='260be8b8710a42559b291797c6e14983'
 return document
def meta(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
def records():
 return sorted(path for path in (root/'stream/records').glob('*.json') if re.fullmatch(r'[0-9]{20}\.json',path.name))
def parents():
 result=[]
 for path in sorted((root/'stream/inbox').glob('*.json')):
  document=json.loads(path.read_bytes())
  if document.get('actor')=='parent':
   result.append(dict(path=str(path),sha256=sha(path),message=document))
 return result
assert len(text.split())<=150
assert sha(console)==expected_console
if mode=='publish':
 before=parents()
 markers=('r193 current-evidence intervention','.s_3_correct','current tool includes sympy')
 assert not any(any(marker in entry['message']['text'].lower() for marker in markers) for entry in before),'existing_equivalent_parent_no_retry'
 directory.mkdir(mode=0o700)
 evidence=root/'community_cpu/spool/a7f6a77d9b00742aa7a48f8a416109bec24902729774e17ac4534f0ba77c4cd1/RESULT.json'
 assert sha(evidence)=='babd5abafe72c20e7cdf53c1ad7244299da36dac14cd7040fe14d6ffd05591dc'
 result=json.loads(evidence.read_bytes())
 assert result['status']=='COMPLETE' and result['returncode']==0 and result['stdout']==''
 intent=dict(schema='R193_ONE_SHOT_PARENT_INTENT_V1',created_unix=time.time(),root=str(root),source=str(source),console_sha256=expected_console,speaker='Astra',text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),authorship='Builder-authored/Astra-attributed; user-authorized current-evidence intervention',gateway_model_call=False,automatic_parent_started=False,prior_parent_inventory=[{key:entry[key] for key in ('path','sha256')} for entry in before],head_before=meta(records()[-1]),adaptation='Historical unavailable and first SyntaxError distinguished from newer COMPLETE/0 with empty stdout; no observed value claimed.')
 store(directory/'INTENT.json',intent)
 sys.path.insert(0,str(source))
 from gpu.orch_r127_pilot_console import publish_parent
 publication=publish_parent(str(root),'Astra',text)
 assert sha(Path(publication['path']))==publication['sha256']
 receipt=dict(schema='R193_ONE_SHOT_PARENT_PUBLICATION_V1',published_unix=time.time(),publication=publication,intent_sha256=sha(directory/'INTENT.json'),text_sha256=intent['text_sha256'],word_count=len(text.split()),speaker='Astra',gateway_model_call=False,automatic_parent_started=False,rendered=False)
 store(directory/'PUBLICATION.json',receipt)
 print(json.dumps(dict(intent=intent,receipt=receipt,remote_receipt=str(directory/'PUBLICATION.json'),remote_receipt_sha256=sha(directory/'PUBLICATION.json')),sort_keys=True))
elif mode=='observe':
 publication=json.loads((directory/'PUBLICATION.json').read_bytes())['publication']
 assert sha(Path(publication['path']))==publication['sha256']
 output=dict(observed_unix=time.time(),publication=publication,registered=[],rendered=[],pids={},recent=[],last_complete=None,parent_count=len(parents()))
 paths=records();catalog=[meta(path) for path in paths if int(path.stem)>=5476]
 for item in catalog:
  path=root/'stream/records'/f"{item['index']:020d}.json"
  if item['kind'] not in ('INBOX','REQUEST','SLEEP_COMPLETE'):continue
  record=read(path);body=record['document']
  if item['kind']=='INBOX' and body['message']['id']==publication['id']:
   assert body['source_sha256']==publication['sha256'] and body['message']['text']==text
   output['registered'].append(dict(index=item['index'],record_sha256=record['sha256'],file_sha256=sha(path),mtime_ns=path.stat().st_mtime_ns))
  if item['kind']=='REQUEST':
   matches=[dict(position=position,role=message['role'],content_sha256=hashlib.sha256(message['content'].encode()).hexdigest()) for position,message in enumerate(body['messages']) if 'Astra: '+text in message.get('content','')]
   if matches:output['rendered'].append(dict(index=item['index'],record_sha256=record['sha256'],file_sha256=sha(path),started_unix=body['started_unix'],segment=body.get('segment'),matches=matches,all_history_tokens_masked=body['render_receipt']['all_history_tokens_masked']))
  if item['kind']=='SLEEP_COMPLETE':
   output['last_complete']=dict(index=item['index'],record_sha256=record['sha256'],file_sha256=sha(path),record_mtime_ns=path.stat().st_mtime_ns,cycle=body['cycle'],status=body['status'],optimizer_steps=body['optimizer_steps'],total_optimizer_steps=body['total_optimizer_steps'])
 for item in catalog[-8:]:
  record=read(root/'stream/records'/f"{item['index']:020d}.json");body=record['document']
  output['recent'].append(dict(index=item['index'],kind=item['kind'],sha256=record['sha256'],fields={key:body[key] for key in ('cycle','status','started_unix','finished_unix','optimizer_step','stage','segment','new_rows','selected_old_rows') if key in body}))
 for pid,expected in ((2930123,22768040),(2930061,22767888),(2930020,22767768)):
  try:
   fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
   output['pids'][pid]=dict(state=fields[0],start_ticks=int(fields[19]),matches_expected=int(fields[19])==expected)
  except FileNotFoundError:output['pids'][pid]=dict(alive=False)
 print(json.dumps(output,sort_keys=True))
else:raise ValueError('unknown_mode')
'''


def save(path, document):
    with path.open("x") as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("publish", "observe"))
    options = parser.parse_args()
    ARTIFACTS.mkdir(exist_ok=True)
    if options.mode == "publish":
        save(ARTIFACTS / "LOCAL_INTENT.json", dict(
            time=time.time(), text=TEXT, text_sha256=hashlib.sha256(TEXT.encode()).hexdigest(),
            speaker="Astra", gateway_model_call=False, no_retry=True,
        ))
    script = "mode=" + repr(options.mode) + "\ntext=" + repr(TEXT) + "\n" + REMOTE
    result = subprocess.run(
        ["bash", "gpu/ovx3_ssh.sh", "/localhome/local-rohing/v2/venv/bin/python -"],
        input=script, text=True, capture_output=True, timeout=90,
    )
    receipt = dict(time=time.time(), mode=options.mode, returncode=result.returncode,
                   stderr=result.stderr)
    if result.returncode == 0:
        receipt["result"] = json.loads(result.stdout)
    else:
        receipt["stdout"] = result.stdout
    path = ARTIFACTS / (options.mode.upper() + "_" + str(time.time_ns()) + ".json")
    save(path, receipt)
    print(json.dumps(dict(path=str(path), **receipt), indent=2, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
