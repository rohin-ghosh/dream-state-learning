"""Read-only native Tool publication proof, separate from successful judging."""

import json
from pathlib import Path
import time

from transport_preflight import HERE, REPO, remote
from restore_transport import put


def bind_new_transport(life, publication, transports, activated):
    matches = [row for row in transports if row['session_id'] == life
        and row['unix'] >= activated and row['dispatched'] is True
        and row['receipt_sha256'] == publication['receipt_sha256']
        and row['origin']['record_index'] == publication['RESPONSE']['index']
        and row['origin']['record_sha256'] == publication['RESPONSE']['sha256']]
    if len(matches) != 1:
        raise ValueError('exact_new_natural_transport_receipt_required')
    return matches[0]


def main():
    started = json.loads((HERE / 'TRANSPORT_STARTED.json').read_bytes())
    source = (REPO / 'research_loop/workers/rohin233_focus_node3_20260918/feedback_proof.py').read_text()
    source = source.split("if __name__ == '__main__':")[0]
    code = '''import sys
sys.path.insert(0,'/localhome/local-rohing/orch_r205_node3_20260918/r233_recovery_parents_v4')
''' + source + '''
import time
value=json.load(sys.stdin)
root=Path('/localhome/local-rohing/orch_r205_node3_20260918')
output=root/'r228_feedback_relay_20260918T0908Z/output'
rows=[]
for treatment in ('observation','perspective','revision','selfderive','unparented'):
 arm=root/('r213_r226_caption_'+treatment+'_fork')
 destination=output/treatment
 candidates=[]
 for path in (destination/'published').glob('*.json'):
  if path.stat().st_mtime>=value['since']:
   saved=json.loads(path.read_bytes())
   if saved['published_unix']>=value['since']: candidates.append((saved['published_unix'],path))
 proofs=[]
 for unused,path in sorted(candidates)[:3]:
  item,text=authenticated_publication(path,arm,destination)
  paths=sorted((arm/'raw/stream/records').glob('[0-9]'*20+'.json'))
  inbox=None
  for record_path in paths:
   if int(record_path.stem)<=item['ACT']['index'] or metadata(record_path)!='INBOX':continue
   row=record(record_path)
   if row['document']['message']['id']==item['inbox_id']:
    if row['document']['source_sha256']!=item['inbox_sha256']:raise ValueError('inbox_hash_changed')
    inbox=reference(row);break
  item['INBOX']=inbox
  item['publication_path']=str(path)
  proofs.append(item)
 rows.append(dict(life=arm.name,first_new_publications=proofs))
print(json.dumps(dict(unix=time.time(),rows=rows,read_only=True,no_scoring_requests=True,native_signals=[])))
'''
    value = remote('ovx2_ssh.sh', code, dict(since=started['unix']))
    transports = [json.loads(path.read_bytes()) for path in
        sorted(Path(started['runtime'], 'proxy').glob('TRANSPORT_*.json'))]
    for row in value['rows']:
        for publication in row['first_new_publications']:
            publication['new_transport_receipt'] = bind_new_transport(row['life'],
                publication, transports, started['unix'])
    result = dict(unix=time.time(), activated_unix=started['unix'], native=value, transports=transports,
        successful_judgment_not_implied_by_transport_receipt=True)
    put(HERE / ('JUDGMENT_RECEIPTS_' + str(time.time_ns()) + '.json'), result)
    put(HERE / 'JUDGMENT_RECEIPTS_LATEST.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
