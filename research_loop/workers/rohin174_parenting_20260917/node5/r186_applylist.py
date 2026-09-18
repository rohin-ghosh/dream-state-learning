"""Read actual NODE5 progress; estimate boundary time, never claim delivery."""

from datetime import datetime
import json
from pathlib import Path
import shlex
import subprocess
import time
from zoneinfo import ZoneInfo

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
REMOTE = '''import json,statistics,time
from pathlib import Path
def meta(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
rows=[]
for item in ITEMS:
 paths=sorted((Path(item['root'])/'stream/records').glob('[0-9]'*20+'.json'))
 update=[];eligibility=None;request=None;complete=None
 for path in reversed(paths[-800:]):
  entry=meta(path);kind=entry['kind']
  if kind=='UPDATE' and len(update)<6:
   doc=json.loads(path.read_bytes())['document'];update.append(dict(index=entry['index'],step=doc['optimizer_step'],time=doc['finished_unix']))
  elif kind=='TARGET_ELIGIBILITY' and eligibility is None:
   doc=json.loads(path.read_bytes())['document'];eligibility=dict(index=entry['index'],new=len(doc['new_row_sha256']),old=len(doc['rehearsal_row_sha256']))
  elif kind=='SLEEP_REQUEST' and request is None:
   doc=json.loads(path.read_bytes())['document'];request=dict(index=entry['index'],cycle=doc['cycle'])
  elif kind=='SLEEP_COMPLETE' and complete is None:
   doc=json.loads(path.read_bytes())['document'];complete=dict(index=entry['index'],cycle=doc['cycle'],step=doc['checkpoint']['optimizer_steps'],mtime=path.stat().st_mtime)
  if len(update)==6 and eligibility and request and complete: break
 row=dict(label=item['label'],latest_complete=complete,request=request,eligibility=eligibility,updates=update,estimate=None)
 if request and complete and eligibility and update and request['cycle']>complete['cycle'] and eligibility['index']>request['index']:
  total=eligibility['new']*16+eligibility['old'];done=update[0]['step']-complete['step'];remaining=max(0,total-done)
  intervals=[left['time']-right['time'] for left,right in zip(update,update[1:]) if left['index']>request['index'] and right['index']>request['index'] and left['time']>right['time']]
  if intervals:
   seconds=statistics.median(intervals);row['estimate']=dict(total_updates=total,completed_updates=done,remaining_updates=remaining,recent_seconds_per_update=seconds,remaining_update_seconds=remaining*seconds,kind='LINEAR_ESTIMATE_EXCLUDES_CHECKPOINT_AND_HANDOFF_NOT_PROMISE')
 rows.append(row)
print(json.dumps(dict(rows=rows,observed_unix=time.time(),signals=0,publications=0,no_sealed_readouts=True)))
'''


def main():
    audit_path = sorted(HERE.glob('R181_AUDIT_*.json'))[-1]
    audit = read(audit_path)
    items = [dict(label=row['label'], root=str(Path(row['latest']['SLEEP_COMPLETE']['path']).parents[2])) for row in audit['rows']]
    script = REMOTE.replace('ITEMS', repr(items))
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(script)], capture_output=True, text=True, timeout=55)
    require(result.returncode == 0, 'read_only_applylist:' + result.stderr[-250:])
    document = json.loads(result.stdout)
    document['audit'] = reference(audit_path)
    document['parents'] = {}
    for label in ('C1','C3','C4','C5','run1','pilot','repo_reader'):
        phase = sorted(HERE.glob('ROUTE_' + label + '_*/source/R184_EFFORT_PHASE.json'))[-1]
        output = phase.parents[1] / 'parent'
        parent = dict(root=str(output), receipts={})
        for name in ('ACTIVE_PARENT','FAILED_CLOSED','WITHDRAWAL_COMPLETE','R184_FIRST_PUBLICATION','R184_FIRST_RENDERED_REQUEST'):
            path = output / (name + '.json')
            if path.exists():
                parent['receipts'][name] = dict(reference=reference(path), document=read(path))
        statuses = sorted(output.glob('STATUS_*.json'))
        if statuses:
            parent['status'] = read(statuses[-1])['status']
            parent['status_reference'] = reference(statuses[-1])
        document['parents'][label] = parent
    stamp = str(time.time_ns())
    receipt_path = HERE / ('R186_APPLYLIST_' + stamp + '.json')
    write(receipt_path, document)
    zone = ZoneInfo('America/Los_Angeles')
    clock = lambda value: datetime.fromtimestamp(value, zone).strftime('%H:%M:%S PDT')
    rows = {row['label']: row for row in audit['rows']}
    progress = {row['label']: row for row in document['rows']}
    lines = ['# NODE5 R186 apply-list — ' + clock(document['observed_unix']), '',
        '| Life | Actual latest completed | R181/cache application | Parent effort turn | Boundary estimate only |',
        '| --- | --- | --- | --- | --- |']
    for label in ('C1','C2','C3','C4','C5','run1','pilot','repo_reader'):
        row = rows[label]
        current = progress[label]
        complete = current['latest_complete']
        completion = str(complete['cycle']) + ' @' + clock(complete['mtime'])
        applied = row['plan']['rehearsal_presentations'] == 0
        application = ('APPLIED old0/new16' if applied else 'ARMED; current old sleep' + str(current['request']['cycle']))
        application += '; cache ' + ('LOADED' if row['cache_active'] else 'queued')
        application += '; operator ' + str(row['operator']['pid']) + (' live' if row['operator_live'] else 'not live')
        parent = document['parents'].get(label)
        turn = 'EXCLUDED; fixed172; no extra Astra'
        if parent:
            receipts = parent['receipts']
            turn = parent.get('status', 'pending') + '; no R184 PUB/REQUEST'
            if 'WITHDRAWAL_COMPLETE' in receipts:
                turn = 'withdrawal completed; no R184 turn; no restart'
            if 'R184_FIRST_PUBLICATION' in receipts:
                turn = 'PUB ' + receipts['R184_FIRST_PUBLICATION']['document']['publication']['id']
                turn += '; REQUEST verified' if 'R184_FIRST_RENDERED_REQUEST' in receipts else '; REQUEST pending'
            if 'FAILED_CLOSED' in receipts:
                turn += '; parent failure ' + receipts['FAILED_CLOSED']['document']['error_type']
        estimate = current['estimate']
        eta = 'boundary/cycle transition; load ETA not promised'
        if estimate:
            minutes = estimate['remaining_update_seconds'] / 60
            eta = str(estimate['remaining_updates']) + ' updates; ~' + str(round(minutes)) + ' min plus checkpoint/handoff'
        lines.append('| ' + ' | '.join((label,completion,application,turn,eta)) + ' |')
    lines += ['', 'Original C2 missed the completed41 window: original42 is already training the old recipe. Its live R181/cache waiter preserves current work and awaits complete42; no abort, suffix discard or additional parent question.',
        'run1 completed new-only49–52; C4 completed new-only39 (further completions appear in the table). Others require actual completion receipts; applied is not completed.',
        'Estimates extrapolate the last six retained UPDATE timings and exact eligible-row counts; they exclude checkpoint saving, strict admission and model loading. They are not deadlines.',
        'Exact evidence: `' + receipt_path.name + '` SHA `' + reference(receipt_path)['sha256'] + '`.',
        'No NODE2 actions. Original C2 parent limit unchanged. Existing arm/cadence/withdrawal clocks preserved.', '']
    path = HERE / ('R186_APPLYLIST_' + stamp + '.md')
    with path.open('x') as handle:
        handle.write('\n'.join(lines))
    print(json.dumps(dict(file=reference(path), evidence=reference(receipt_path), rows=document['rows'])))


if __name__ == '__main__':
    main()
