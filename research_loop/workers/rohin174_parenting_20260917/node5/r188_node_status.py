"""Current-node metadata audit, including load versus launch and old-recipe eligibility."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,time
from pathlib import Path
def ref(path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def metadata(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
rows=[]
for item in ITEMS:
 if item.get('blocked'):
  rows.append(item);continue
 process=Path('/proc')/str(item['identity']['pid']);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
 assert fields[19]==item['identity']['start_ticks'] and fields[0] not in ('Z','X')
 row=dict(label=item['label'],native=item['identity'],live=True,plan=item['plan'],root=item['storage_root'],loaded=None,latest={},completed_recipe=None)
 source=Path(item['plan']['source_root']);row['journal_source']=ref(source/'gpu/orch_r125_stream_journal.py')
 config=json.loads(Path(item['config_ref']['path']).read_bytes())
 assert ref(Path(item['config_ref']['path']))==item['config_ref']
 row['expected_overlay_sha256']=CACHE_SHA[item['label']]
 row['cache_source_pinned']=row['journal_source']['sha256']==CACHE_SHA[item['label']]==config['source_pins']['gpu/orch_r125_stream_journal.py']
 paths=sorted((Path(item['storage_root'])/'stream/records').glob('[0-9]'*20+'.json'))
 row['head']=metadata(paths[-1])
 for path in reversed(paths[-1000:]):
  meta=metadata(path);kind=meta['kind']
  if kind not in ('LOADED','SLEEP_RECIPE','SLEEP_REQUEST','SLEEP_COMPLETE','UPDATE','REQUEST') or kind in row['latest']:continue
  doc=json.loads(path.read_bytes())['document']
  if kind=='LOADED' and doc['pid']!=item['identity']['pid']:continue
  fields={key:doc[key] for key in ('pid','cycle','status','new_rows','new_presentations','selected_old_rows','loaded_unix','started_unix','finished_unix','optimizer_steps','optimizer_step') if key in doc}
  if 'checkpoint' in doc:fields['total_optimizer_steps']=doc['checkpoint']['optimizer_steps']
  row['latest'][kind]=dict(index=meta['index'],record_sha256=meta['sha256'],reference=ref(path),mtime_unix=path.stat().st_mtime,fields=fields)
  if kind=='LOADED':row['loaded']=row['latest'][kind]
 complete=row['latest'].get('SLEEP_COMPLETE')
 if complete:
  for path in reversed(paths[-1000:]):
   meta=metadata(path)
   if meta['index']>=complete['index'] or meta['kind']!='SLEEP_RECIPE':continue
   doc=json.loads(path.read_bytes())['document'];row['completed_recipe']=dict(index=meta['index'],record_sha256=meta['sha256'],new_rows=doc['new_rows'],new_presentations=doc['new_presentations'],selected_old_rows=doc['selected_old_rows']);break
 row['cache_loaded']=row['cache_source_pinned'] and row['loaded'] is not None
 row['old_recipe_active']=item['plan']['rehearsal_presentations']!=0
 rows.append(row)
print(json.dumps(dict(observed_unix=time.time(),rows=rows,all_eight_live=len(rows)==8 and all(row.get('live') for row in rows),all_eight_loaded=len(rows)==8 and all(row.get('loaded') for row in rows),signals=0,publications=0)))
'''


def main():
    inventory = sorted(HERE.glob('R181_CURRENT_*.json'))[-1]
    cache_binding = HERE / 'ALL8_CACHE_STATUS_1789684377754893693.json'
    cache_sha = {row['label']: row['journal_overlay']['successor']['sha256']
                 for row in read(cache_binding)['rows']}
    cache_sha['C2'] = read(HERE / 'R188_C2_AUDIT_BINDING.json')['journal_overlay']['successor']['sha256']
    script = REMOTE.replace('ITEMS', repr(read(inventory)['rows'])).replace('CACHE_SHA', repr(cache_sha))
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(script)],
        capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, 'current_node_audit:' + result.stderr[-350:])
    document = json.loads(result.stdout)
    document['inventory'] = reference(inventory)
    document['cache_binding'] = reference(cache_binding)
    document['cache_proof'] = 'Exact deployed overlay plus guard source pin; not whole-file equality to canonical Main source.'
    document['rendered_inputs'] = reference(sorted(HERE.glob('R188_RENDERED_INPUTS_*.json'))[-1])
    path = HERE / ('R188_NODE5_STATUS_' + str(time.time_ns()) + '.json')
    write(path, document)
    print(json.dumps(dict(receipt=reference(path), all_eight_live=document['all_eight_live'],
        all_eight_loaded=document['all_eight_loaded'], rows=[dict(label=row['label'],
            pid=row.get('native',{}).get('pid'), cache_loaded=row.get('cache_loaded'),
            old_recipe_active=row.get('old_recipe_active'), loaded=row.get('loaded'),
            complete=row.get('latest',{}).get('SLEEP_COMPLETE'), completed_recipe=row.get('completed_recipe'))
            for row in document['rows']])))


if __name__ == '__main__':
    main()
