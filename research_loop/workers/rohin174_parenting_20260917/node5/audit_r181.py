"""Read NODE5 training metadata and exact active cache/waiter provenance."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
REMOTE = '''import hashlib,json,time
from pathlib import Path
def ref(path):
 raw=Path(path).read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest())
def meta(path):
 with path.open('rb') as handle:
  handle.seek(max(0,path.stat().st_size-4096));raw=handle.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
rows=[]
for item in ITEMS:
 row=dict(label=item['label'],native=item['identity'],saved=item['saved'],plan=item['plan'],source=item['native'])
 process=Path('/proc')/str(item['identity']['pid'])
 try:
  fields=(process/'stat').read_text().rsplit(')',1)[1].split()
  row['native_live']=fields[19]==item['identity']['start_ticks'] and fields[0] not in ('Z','X')
 except FileNotFoundError: row['native_live']=False
 row['journal_source']=ref(Path(item['plan']['source_root'])/'gpu/orch_r125_stream_journal.py')
 cache=CACHES[item['label']]
 row['cache_source_expected']=cache['journal_overlay']['successor']
 row['cache_active']=row['journal_source']==cache['journal_overlay']['successor'] and row['native_live']
 row['waiter_root']=cache['output'];row['operator']=cache['operator']
 try:
  fields=(Path('/proc')/str(cache['operator']['pid'])/'stat').read_text().rsplit(')',1)[1].split()
  row['operator_live']=fields[19]==cache['operator']['start_ticks'] and fields[0] not in ('Z','X')
 except FileNotFoundError: row['operator_live']=False
 row['operator_receipts']={}
 for name in ('FAILED_CLOSED.json','RETIRED.json','SUCCESSOR_LOADED.json','LOADED_RECEIPT.json','EXIT.json'):
  path=Path(cache['output'])/name
  if path.exists(): row['operator_receipts'][name]=dict(reference=ref(path),document=json.loads(path.read_bytes()))
 paths=sorted((Path(item['storage_root'])/'stream/records').glob('[0-9]'*20+'.json'))
 row['head']=dict(meta(paths[-1]),mtime_unix=paths[-1].stat().st_mtime)
 row['latest']={}
 for path in reversed(paths[-800:]):
  entry=meta(path);kind=entry['kind']
  if kind not in ('UPDATE','SLEEP_RECIPE','SLEEP_REQUEST','SLEEP_COMPLETE','LOADED') or kind in row['latest']: continue
  document=json.loads(path.read_bytes())['document']
  allowed=('cycle','status','step','optimizer_steps','new_presentations','new_rows','selected_old_rows','available_old_rows','anchor_lambda','policy','pid','source_sha256')
  details={key:document[key] for key in allowed if key in document}
  if 'checkpoint' in document: details['checkpoint_optimizer_steps']=document['checkpoint'].get('optimizer_steps')
  row['latest'][kind]=dict(index=entry['index'],sha256=entry['sha256'],path=str(path),mtime_unix=path.stat().st_mtime,details=details)
 complete=row['latest'].get('SLEEP_COMPLETE')
 row['completed_recipe']=None
 if complete:
  for path in reversed(paths[-800:]):
   entry=meta(path)
   if entry['index']>=complete['index'] or entry['kind']!='SLEEP_RECIPE': continue
   document=json.loads(path.read_bytes())['document']
   row['completed_recipe']=dict(index=entry['index'],sha256=entry['sha256'],path=str(path),details=document)
   break
 row['observed_unix']=time.time();rows.append(row)
print(json.dumps(dict(rows=rows,observed_unix=time.time(),native_signals=0,new_messages=0,no_sealed_readouts=True)))
'''


def main():
    inventory = sorted(HERE.glob('R181_CURRENT_*.json'))[-1]
    items = read(inventory)['rows']
    require(all(not row.get('blocked') for row in items), 'fresh_native_inventory_complete')
    cache_path = HERE / 'ALL8_CACHE_STATUS_1789684377754893693.json'
    caches = {row['label']: row for row in read(cache_path)['rows']}
    recovery = HERE / 'R188_C2_AUDIT_BINDING.json'
    if recovery.exists():
        binding = read(recovery)
        current = next(row for row in items if row['label'] == 'C2')
        require(current['plan']['source_root'] == binding['output'] + '/source', 'R188_actual_C2_source_binding')
        caches['C2'] = binding
    script = REMOTE.replace('ITEMS', repr(items)).replace('CACHES', repr(caches))
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(script)], capture_output=True, text=True, timeout=70)
    require(result.returncode == 0, 'read_only_node5_audit:' + result.stderr[-250:])
    document = json.loads(result.stdout)
    document.update(inventory=reference(inventory), operator_binding=reference(cache_path))
    path = HERE / ('R181_AUDIT_' + str(time.time_ns()) + '.json')
    write(path, document)
    print(json.dumps(dict(receipt=reference(path), rows=[dict(label=row['label'],
        native_live=row['native_live'],operator_live=row['operator_live'],cache_active=row['cache_active'],
        completed_cycle=row['saved']['cycle'],completed_steps=row['saved']['optimizer_steps'],
        head=dict(index=row['head']['index'],kind=row['head']['kind']),latest=row['latest']) for row in document['rows']])))


if __name__ == '__main__':
    main()
