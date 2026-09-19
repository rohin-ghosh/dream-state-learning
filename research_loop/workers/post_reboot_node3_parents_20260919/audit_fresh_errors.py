"""Read-only proof of fresh natural failure, Tool INBOX and masked REQUEST."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from transport_preflight import HERE, remote
from restore_transport import put


def latest_failures(rows):
    latest = {}
    for row in rows:
        if 'transport_failure' not in row:
            continue
        life = row['life']
        if life not in latest or row['transport_failure']['unix'] > latest[life]['transport_failure']['unix']:
            latest[life] = row
    return [latest[life] for life in sorted(latest)]


def attach_report(transport, path, reports):
    origin_sha = transport['origin']['record_sha256']
    matches = [row for row in reports if row.get('result', {}).get('origin',
        row.get('origin', {})).get('record_sha256') == origin_sha]
    if len(matches) > 1:
        raise ValueError('unique_failed_origin_report_required')
    report = matches[0] if matches else {}
    if report.get('transport_failure', transport) != transport:
        raise ValueError('unchanged_actual_VM_transport_failure_required')
    return dict(report, life=transport['session_id'], transport_failure=transport,
        transport_path=str(path), result=report.get('result', dict(
            status=report.get('status', 'NEW_NATURAL_FAILURE_FEEDBACK_PENDING'))))


def main():
    started = json.loads((HERE/'OPERATIONAL_ERRORS_STARTED.json').read_bytes())
    baseline = json.loads((HERE/'BINDINGS.json').read_bytes())
    snapshot = json.loads((HERE/'OPERATIONAL_ERRORS_LATEST.json').read_bytes())
    transport_started = json.loads((HERE/'TRANSPORT_STARTED.json').read_bytes())
    authoritative = []
    for path in sorted(Path(transport_started['output']).glob('TRANSPORT_*.json')):
        transport = json.loads(path.read_bytes())
        if transport.get('dispatched') is False and transport.get('receipt_sha256') is None:
            authoritative.append(attach_report(transport, path, snapshot['rows']))
    rows = latest_failures(authoritative)
    for row in rows:
        raw = Path(row['transport_path']).read_bytes()
        if json.loads(raw) != row['transport_failure']:
            raise ValueError('unchanged_actual_VM_transport_failure_required')
        row['transport_file_sha256'] = hashlib.sha256(raw).hexdigest()
    code = (HERE/'node_bridge.py').read_text().split("if __name__ == '__main__':")[0] + '''
value=json.load(sys.stdin)
retirement,adaptive,helper,bindings=load_helpers()
exact=exact_bindings(retirement,helper,bindings)
assert exact==value['bindings'],'native_incarnation_changed'
rows=[]
for selected in value['rows']:
 life=selected['life']; transport=selected['transport_failure']; saved=selected.get('result',{})
 assert life in CAPTIONS and transport['session_id']==life
 if not saved.get('INBOX'):
  rows.append(dict(life=life,status=saved.get('status','FAILED_NO_DELIVERY_PROOF'),INBOX=None))
  continue
 arm=ROOT/life/'raw'; origin=transport['origin']
 actual=retirement.record(arm/'stream/records'/f"{saved['ACT_record']['index']:020d}.json")
 response=retirement.record(arm/'stream/records'/f"{origin['record_index']:020d}.json")
 assert actual['sha256']==saved['ACT_record']['sha256'] and actual['kind']=='R184_ACT'
 assert retirement.sha(arm/'stream/records'/f"{actual['index']:020d}.json")==saved['ACT_record']['file_sha256']
 assert response['kind']=='RESPONSE' and response['sha256']==origin['record_sha256']
 assert actual['document']['origin']==origin and actual['journal_id']==response['journal_id']
 environment=actual['document']['outcome']['environment']
 assert environment['origin']==origin and not environment.get('receipt_sha256')
 assert environment['report']['error']=='ORIGIN_TRANSPORT_NOT_DISPATCHED' and not environment['report'].get('feedback')
 assert transport['dispatched'] is False and transport['receipt_sha256'] is None
 publication=saved['publication']; published_path=Path(publication['path'])
 assert published_path.resolve().is_relative_to(arm/'stream/inbox')
 assert retirement.sha(published_path)==publication['sha256']
 incoming=json.loads(published_path.read_bytes())
 assert incoming['id']==publication['id'] and incoming['actor']=='environment' and incoming['speaker']=='Tool'
 assert incoming['source_receipt']==saved['source_receipt']
 projection_path=Path(saved['source_receipt']['path'])
 assert projection_path.resolve().is_relative_to(ROOT/'post_reboot_node3_operational_errors_20260919'/life)
 assert retirement.sha(projection_path)==saved['source_receipt']['sha256']
 projection=json.loads(projection_path.read_bytes())
 assert projection['transport_failure']==transport and projection['transport_file_sha256']==selected['transport_file_sha256']
 assert projection['origin']==origin and projection['scorer_receipt'] is False and projection['no_ACT_replay'] is True
 assert projection['text']==incoming['text'] and projection['window']['bound_bytes']==67108864
 assert projection['window']['total_bytes']>67108864 and projection['window']['all_ancestry_preserved'] is True
 inbox=retirement.record(arm/'stream/records'/f"{saved['INBOX']['index']:020d}.json")
 assert inbox['kind']=='INBOX' and inbox['sha256']==saved['INBOX']['sha256']
 assert inbox['document']['message']['id']==publication['id'] and inbox['document']['source_sha256']==publication['sha256']
 request=None
 for path in sorted((arm/'stream/records').glob('[0-9]'*20+'.json')):
  if int(path.stem)<=inbox['index'] or retirement.metadata(path)!='REQUEST':continue
  candidate=retirement.record(path); document=candidate['document']
  if any(message.get('role')=='user' and message.get('content')=='Tool: '+incoming['text'] for message in document['messages']):
   assert document['started_unix']>=saved['published_unix'] and document['render_receipt']['all_history_tokens_masked'] is True
   request=dict(index=candidate['index'],sha256=candidate['sha256'],started_unix=document['started_unix'],all_history_tokens_masked=True)
   break
 finished=response['document']['finished_unix']
 rows.append(dict(life=life,origin=origin,source_finished_unix=finished,failure_unix=transport['unix'],
  ACT=dict(index=actual['index'],sha256=actual['sha256']),INBOX=dict(index=inbox['index'],sha256=inbox['sha256']),
  REQUEST=request,published_unix=saved['published_unix'],publication=publication,
  projection=saved['source_receipt'],minimal_original_bytes=projection['window']['total_bytes'],
  bound_bytes=67108864,source_generated_after_reporter_started=finished>=value['reporter_started_unix'],
  source_generated_after_main_resume=finished>=value['main_resume_unix'],
  no_scorer_dispatch=True,no_judgment=True,no_ACT_replay=True,
  status='FRESH_FAILURE_TOOL_MASKED_REQUEST_VERIFIED' if request and finished>=value['reporter_started_unix'] else 'EXPLICIT_FRESHNESS_AND_REQUEST_FIELDS_REQUIRED'))
print(json.dumps(dict(unix=time.time(),rows=rows,read_only=True,no_publications=True,native_signals=[])))
'''
    value = remote('ovx2_ssh.sh',code,dict(bindings=baseline['bindings'],rows=rows,
        reporter_started_unix=started['unix'],main_resume_unix=1789782480))
    value['reporter_started_unix'] = started['unix']
    value['main_resume_utc'] = '2026-09-19T01:48:00Z'
    value['source_snapshot_unix'] = snapshot['unix']
    put(HERE/('FRESH_OPERATIONAL_CHAINS_'+str(time.time_ns())+'.json'),value)
    put(HERE/'FRESH_OPERATIONAL_CHAINS_LATEST.json',value)
    for row in value['rows']:
        summary = {key:row.get(key) for key in ('life','status','origin','ACT','INBOX','REQUEST',
            'source_generated_after_reporter_started','source_generated_after_main_resume','minimal_original_bytes')}
        for key in ('source_finished_unix','failure_unix','published_unix'):
            if key in row:
                summary[key.replace('_unix','_utc')] = datetime.fromtimestamp(row[key],timezone.utc).isoformat()
        print(json.dumps(summary))


if __name__=='__main__':
    main()
