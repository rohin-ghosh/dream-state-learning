"""One newly authorized metadata-only final audit, with no science retries."""

import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import prep_common as common
import prepare


SCRIPT = r'''
import hashlib,json,os,stat,time
from pathlib import Path
os.umask(0o077)
old=Path('/localhome/local-rohing/orch_r167_fleet_20260917_generation2')
operation=Path('/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1/R159_FINAL_PER_LIFE_AUDIT2')
operation.mkdir(parents=True,mode=0o700,exist_ok=False)
started=time.time()
deadline=time.monotonic()+85
used=0
cache={}
def write(path,document):
 raw=json.dumps(document,sort_keys=True,separators=(',',':')).encode()
 with path.open('xb') as stream:
  stream.write(raw);stream.flush();os.fsync(stream.fileno())
def read(path):
 global used
 path=Path(path)
 if path in cache:return cache[path]
 assert time.monotonic()<deadline,'audit_85s_read_wall'
 assert path.is_relative_to(old) and path==path.resolve(),'exact_old_metadata_path'
 relative=path.relative_to(old)
 allowed=(len(relative.parts)==3 and relative.parts[0]=='lives' and relative.name=='REGISTERED.json')
 allowed=allowed or (len(relative.parts)==2 and relative.parts[0]=='ledger' and any(relative.name.endswith('.'+label+'.json') for label in ('RESERVED','COMPLETE','FAILED')))
 allowed=allowed or (len(relative.parts)==3 and relative.parts[0]=='attempts' and relative.name in ('REFUSED.json','UNRESOLVED.json'))
 allowed=allowed or (len(relative.parts)==4 and relative.parts[0]=='attempts' and relative.parts[2:] == ('sealed','COMPLETE.json'))
 assert allowed,'metadata_file_allowlist'
 descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 with os.fdopen(descriptor,'rb') as stream:
  before=os.fstat(stream.fileno())
  assert stat.S_ISREG(before.st_mode) and before.st_size<=131072,'128KiB_per_file'
  assert used+before.st_size<=REQUEST['reserved_bytes'],'new_audit_budget_only'
  write(operation/('READ_%05d.json'%len(cache)),dict(path=str(path),bytes=before.st_size,charged_before_read=True,observed_unix=time.time()))
  used+=before.st_size
  raw=stream.read(before.st_size)
  after=os.fstat(stream.fileno())
  assert len(raw)==before.st_size and all(getattr(before,field)==getattr(after,field) for field in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')),'changed_metadata_file'
 value=(json.loads(raw),hashlib.sha256(raw).hexdigest())
 cache[path]=value
 return value
def verify(reference,path):
 document,checksum=read(path)
 assert reference==dict(path=str(path),sha256=checksum),'exact_completion_reservation_reference'
 return document
write(operation/'ONCE.json',dict(scope='R159_FINAL_PER_LIFE_AUDIT2',request=REQUEST,started_unix=started,no_retry=True))
try:
 rows=[]
 associated=set()
 for life in REQUEST['lives']:
  name=life['life_id']
  registration=old/'lives'/name/'REGISTERED.json'
  row=dict(life_id=name,registered=registration.exists(),initial_completed_jobs=0,forward_completed_jobs=0,completed_calls=0,
   paired_checkpoints=0,unpaired_completed_checkpoints=0,charged_calls=0,failed_jobs=0,refused_jobs=0,unresolved_jobs=0,
   no_attempt_record_jobs=0,attempted_without_terminal_jobs=0,missing_jobs=8,missingness='')
  if not registration.exists():
   assert life['source_status']=='MISSING_CUSTODY_NOT_NEGATIVE','unexpected_registration_missing'
   row['missingness']='NOT_ENROLLED_MISSING_CUSTODY_NOT_NEGATIVE'
   rows.append(row);continue
  registered,checksum=read(registration)
  slots=registered['slots']
  assert len(slots)==8,'eight_frozen_condition_jobs'
  sleeps=sorted({slot['sleep'] for slot in slots})
  assert len(sleeps)==4 and sleeps[0]==0 and sleeps[2]==sleeps[1]+1 and sleeps[3]==sleeps[2]+1,'initial_and_three_consecutive_sleeps'
  completed={}
  for slot in slots:
   sleep,condition,key=slot['sleep'],slot['condition'],slot['key']
   assert slot['life_id']==name and slot['model_calls']==3 and condition in ('LORA_ON','LORA_OFF'),'fixed_registered_cell'
   expected=hashlib.sha256(json.dumps(dict(life_id=name,sleep=sleep,condition=condition),sort_keys=True,separators=(',',':')).encode()).hexdigest()
   assert key==expected and key not in associated,'registered_job_key_life_sleep_association'
   associated.add(key)
   reservation_path=old/'ledger'/(key+'.RESERVED.json')
   complete_path=old/'ledger'/(key+'.COMPLETE.json')
   failed_path=old/'ledger'/(key+'.FAILED.json')
   attempt=old/'attempts'/key
   reservation=None
   if reservation_path.exists():
    reservation,reservation_hash=read(reservation_path)
    assert reservation['key']==key and reservation['calls_charged']==3 and reservation['tokens_charged']==1536,'fixed_charged_job'
    assert reservation['execution']['path']==str(old/'jobs'/(key+'.CONFIG.json')),'registered_execution_path'
    row['charged_calls']+=3
   if complete_path.exists():
    complete,complete_hash=read(complete_path)
    assert reservation is not None and complete['status']=='COMPLETE' and complete['calls']==3 and not failed_path.exists(),'complete_not_failed'
    verify(complete['reservation'],reservation_path)
    native,native_hash=read(attempt/'sealed/COMPLETE.json')
    assert native['status']=='COMPLETE' and native['calls']==3 and native['execution_sha256']==reservation['execution']['sha256'],'completed_native_execution_binding'
    assert native['parent_access'] is False and native['completed_unix']<=1789659000,'completed_within_original_wall'
    commit_hash=native['checkpoint_commit_sha256']
    assert len(commit_hash)==64,'native_checkpoint_hash'
    completed.setdefault(sleep,{})[condition]=commit_hash
    row['initial_completed_jobs' if sleep==0 else 'forward_completed_jobs']+=1
    row['completed_calls']+=3
   elif failed_path.exists():
    failure,failure_hash=read(failed_path)
    assert reservation is not None,'failed_job_has_charged_attempt'
    verify(failure['reservation'],reservation_path)
    row['failed_jobs']+=1
   elif (attempt/'REFUSED.json').exists():
    refused,refused_hash=read(attempt/'REFUSED.json')
    assert refused['calls_charged']==0,'refusal_not_a_charged_science_retry'
    row['refused_jobs']+=1
   elif (attempt/'UNRESOLVED.json').exists():
    read(attempt/'UNRESOLVED.json')
    row['unresolved_jobs']+=1
   elif attempt.exists() or reservation is not None:
    row['attempted_without_terminal_jobs']+=1
   else:row['no_attempt_record_jobs']+=1
  for sleep,conditions in completed.items():
   if len(conditions)==2:
    assert len(set(conditions.values()))==1,'paired_checkpoint_commit_mismatch'
    row['paired_checkpoints']+=1
   else:row['unpaired_completed_checkpoints']+=1
  row['missing_jobs']=8-row['initial_completed_jobs']-row['forward_completed_jobs']
  row['missingness']='INCOMPLETE_AT_CLOSED_WALL_NOT_A_RETENTION_OUTCOME' if row['missing_jobs'] else 'COMPLETE_EXECUTION_COVERAGE'
  rows.append(row)
 for path in (old/'ledger').glob('*.RESERVED.json'):
  assert path.name.removesuffix('.RESERVED.json') in associated,'unassociated_reserved_job'
 for path in (old/'ledger').glob('*.COMPLETE.json'):
  assert path.name.removesuffix('.COMPLETE.json') in associated,'unassociated_completed_job'
 totals={field:sum(row[field] for row in rows) for field in ('initial_completed_jobs','forward_completed_jobs','completed_calls','paired_checkpoints','unpaired_completed_checkpoints','charged_calls','failed_jobs','refused_jobs','unresolved_jobs','no_attempt_record_jobs','attempted_without_terminal_jobs','missing_jobs')}
 result=dict(status='R159_FINAL_PER_LIFE_EXECUTION_AUDIT_COMPLETE',scope='R159_FINAL_PER_LIFE_AUDIT2',started_unix=started,
  observed_unix=time.time(),rows=rows,totals=totals,metadata_bytes_charged=used,metadata_files_read=len(cache),
  reserved_bytes=REQUEST['reserved_bytes'],per_file_cap=131072,read_ledger_path=str(operation),
  association_basis='FROZEN_REGISTERED_JOB_KEYS_PLUS_CHARGED_AND_NATIVE_COMPLETION_HASH_JOINS',
  pairing_basis='BOTH_COMPLETED_CONDITIONS_SAME_ORIGINAL_CHECKPOINT_COMMIT_HASH',
  config_payloads_read=0,response_files_read=0,score_files_read=0,adapter_files_read=0,journal_payloads_read=0,
  gpu_calls=0,provider_calls=0,model_calls=0,signals_sent=0,old_ledger_writes=0)
 write(operation/'PUBLIC_METADATA.json',result)
 print(json.dumps(result,sort_keys=True))
except BaseException as error:
 result=dict(status='R159_FINAL_PER_LIFE_EXECUTION_AUDIT_FAILED_NO_FOLLOWUP',scope='R159_FINAL_PER_LIFE_AUDIT2',
  error_type=type(error).__name__,reason=str(error) if isinstance(error,AssertionError) else 'METADATA_AUDIT_ERROR',
  metadata_bytes_charged=used,observed_unix=time.time(),read_ledger_path=str(operation))
 write(operation/'FAILED.json',result)
 print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    scope, proposal, ledger = prepare.setup()
    prior_path=prepare.HERE.parent/'r167_object_survival/fleet_generation2/R159_PER_LIFE_COVERAGE_1789655831858085795.json'
    earlier=common.read(prior_path)
    request=dict(scope='R159_FINAL_PER_LIFE_AUDIT2',reserved_bytes=8*prepare.MIB,
        per_file_bytes=128*1024,wall_seconds=90,original_scope_evidence=common.ref(prior_path),
        lives=[dict(life_id=row['life_id'],source_status=row['source_status']) for row in earlier['lives']])
    allocation=ledger.reserve('R159_FINAL_PER_LIFE_AUDIT2','_campaign','metadata',request['reserved_bytes'],discovery=True)
    common.write(prepare.PREP/'R159_FINAL_PER_LIFE_AUDIT2_REQUEST.json',dict(request,allocation=allocation))
    result=json.loads(prepare.wrapper('ovx','R159_FINAL_PER_LIFE_AUDIT2','python3 -B -',
        ('REQUEST='+repr(request)+'\n'+SCRIPT).encode(),seconds=90))
    reference=common.write(prepare.PREP/'R159_FINAL_PER_LIFE_AUDIT2.json',dict(result,allocation=allocation))
    if result['status']!='R159_FINAL_PER_LIFE_EXECUTION_AUDIT_COMPLETE':
        print(json.dumps(dict(result,evidence=reference)))
        return
    observed=datetime.fromtimestamp(result['observed_unix'],timezone.utc)
    local=observed.astimezone(ZoneInfo('America/Los_Angeles'))
    totals=result['totals']
    lines=['# R159 final per-life execution audit — '+local.strftime('%Y-%m-%d %H:%M:%S PDT'),'',
        '**New metadata observation: '+observed.strftime('%Y-%m-%d %H:%M:%S UTC')+' / '+local.strftime('%H:%M:%S PDT')+'.** This is not the earlier 08:29 snapshot or a science rerun.', '',
        f"**{totals['initial_completed_jobs']+totals['forward_completed_jobs']} completed condition jobs / {totals['completed_calls']} completed calls; {totals['charged_calls']} charged calls.** Initial: {totals['initial_completed_jobs']} jobs. Forward: {totals['forward_completed_jobs']} jobs. Verified paired checkpoints: {totals['paired_checkpoints']}.", '',
        '| Life | Initial completed jobs | Forward completed jobs | Paired checkpoints | Missing / 8 jobs | Refused | Failed | Unresolved/unterminated | No attempt record |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in result['rows']:
        lines.append('| '+ ' | '.join(str(value) for value in (row['life_id'],row['initial_completed_jobs'],row['forward_completed_jobs'],row['paired_checkpoints'],row['missing_jobs'],row['refused_jobs'],row['failed_jobs'],row['unresolved_jobs']+row['attempted_without_terminal_jobs'],row['no_attempt_record_jobs']))+' |')
    lines.extend(['', 'Each condition job contains exactly three frozen calls. A pair means both conditions completed against the same original checkpoint COMMIT hash, not that either retained anything. No condition assignment, response, rubric annotation, or outcome is disclosed.', '',
        'C5 and repo_reader lack old-campaign registration: each contributes eight missing jobs, not eight failed or attempted jobs. For registered lives, missing jobs are reported separately from refusals, charged failures and absent attempts. “No attempt record” does not establish whether the source was uncaptured or merely unexecuted; no journal/adapter audit was authorized.', '',
        f"Audit reads: **{result['metadata_bytes_charged']:,} bytes / {result['metadata_files_read']} metadata files**, each charged before an exact-size read, ≤128 KiB/file. A fresh 8 MiB envelope was reserved inside the existing R172 discovery cap (authorization maximum: 16 MiB). No refund/reset; the earlier failed 1 MiB observation remains consumed.", '',
        'Evidence: `preparation1/R159_FINAL_PER_LIFE_AUDIT2.json`; request/allocation: `preparation1/R159_FINAL_PER_LIFE_AUDIT2_REQUEST.json`; remote pre-read ledger: `'+result['read_ledger_path']+'`.', '',
        'No GPU/provider/model call, signal, old-ledger write, response/score/map disclosure, adapter read or journal-payload read. Exactly one new sanctioned-wrapper observation; no automatic follow-up.'])
    report=common.write(prepare.HERE/'R159_FINAL_PER_LIFE_AUDIT2.md', ('\n'.join(lines)+'\n').encode())
    print(json.dumps(dict(status=result['status'],observed_utc=observed.isoformat(),totals=totals,
        bytes_read=result['metadata_bytes_charged'],files_read=result['metadata_files_read'],evidence=report)))


if __name__=='__main__':
    main()
