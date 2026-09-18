"""Read only R188 C2 custody, fresh TRAIN record metadata and exact inputs."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
REMOTE = '''import json,hashlib,time
from pathlib import Path
base=Path('/localhome/local-rohing/orch_r153_r188_C2_20260917_recovery1')
root=Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
def ref(path): return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
out=dict(observed_unix=time.time(),control=str(base),root=str(root),receipts={},records=[],signals=0,publications=0)
for name in ('STOPPED.json','RESTORED.json','STARTED.json','SOURCE.json','control/GUARD.json','control/PLAN.json','control/OUTER_FAILED.json','control/FAILED.json','control/EXIT.json'):
 path=base/name
 if path.exists(): out['receipts'][name]=ref(path)
stop=json.loads((base/'STOPPED.json').read_bytes());restored=json.loads((base/'RESTORED.json').read_bytes())
out['loss']=dict(recorded_discarded_updates=stop['discarded_recorded_updates'],possible_unlogged_inflight=stop['possible_unlogged_inflight_update'],old_archive=restored['archive'])
out['input_recovery']=[item for item in restored['inputs'] if item['classification']!='PREFIX_REGISTERED_NO_REDELIVERY']
out['journal_source']=ref(base/'source/gpu/orch_r125_stream_journal.py')
for path in sorted((root/'stream/records').glob('[0-9]'*20+'.json')):
 if int(path.stem)<=5128: continue
 record=json.loads(path.read_bytes());doc=record['document'];kind=record['kind']
 if kind not in ('LOADED','INBOX','REQUEST','RESPONSE','COMMITTED','R184_STAGE','R184_ACT','SLEEP_RECIPE','SLEEP_COMPLETE','UPDATE'):continue
 fields={key:doc[key] for key in ('pid','loaded_unix','optimizer_steps','optimizer_step','stage','cycle','new_rows','new_presentations','selected_old_rows') if key in doc}
 if kind=='INBOX': fields={key:doc['message'].get(key) for key in ('id','speaker')}
 if kind=='R184_ACT': fields['outcome']={key:doc.get('outcome',{}).get(key) for key in ('status','executed','result_status','error_type')}
 if kind=='R184_STAGE': fields['consolidation']=doc.get('consolidation')
 out['records'].append(dict(index=record['index'],kind=kind,record_sha256=record['sha256'],reference=ref(path),mtime_unix=path.stat().st_mtime,fields=fields))
 if kind=='LOADED':
  process=Path('/proc')/str(doc['pid'])
  try:
   fields=(process/'stat').read_text().rsplit(')',1)[1].split();out['native']=dict(pid=doc['pid'],start_ticks=fields[19],state=fields[0],live=fields[0] not in ('Z','X'))
  except FileNotFoundError:out['native']=dict(pid=doc['pid'],live=False)
print(json.dumps(out))
'''


def main():
    result = subprocess.run(['bash',str(HERE.parents[3]/'gpu/ovx3_ssh.sh'),
        'python3 -B -c '+shlex.quote(REMOTE)],capture_output=True,text=True,timeout=30)
    require(result.returncode == 0, 'R188_read_only_observation:'+result.stderr[-250:])
    document = json.loads(result.stdout)
    path = HERE / ('R188_OBSERVATION_' + str(time.time_ns()) + '.json')
    write(path,document)
    print(json.dumps(dict(receipt=reference(path),native=document.get('native'),loss=document['loss'],
        records=[row for row in document['records'] if row['kind'] not in ('UPDATE','RESPONSE','COMMITTED','REQUEST')],
        first_request=next((row for row in document['records'] if row['kind']=='REQUEST'),None))))


if __name__ == '__main__':
    main()
