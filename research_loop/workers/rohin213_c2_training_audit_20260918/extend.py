"""Extended fixed-cut audit; keep new targets distinct from legacy rehearsal."""

import collections
import hashlib
import json
import os
from pathlib import Path


OWN=Path(__file__).resolve().parent


def main():
    os.umask(0o077)
    data=json.loads((OWN/'private/RAW_EVIDENCE_EXTENDED.json').read_bytes())
    candidates={row['source_sha256']:row for row in data['candidate_rows']}
    records=sorted([entry['record'] for entry in data['sleeps']]+[
        entry['record'] for entry in data['relevant_records']],key=lambda record:record['index'])
    labels={key.split('_')[1]:value for key,value in json.loads((OWN/'private/CLASSIFICATIONS.json').read_bytes()).items()}
    extra=OWN/'private/EXTENDED_CLASSIFICATIONS.json'
    if extra.exists():labels.update(json.loads(extra.read_bytes()))
    directory=OWN/'private/extended_rows';directory.mkdir(mode=0o700,exist_ok=True)
    unique=[]
    for source_hash,row in candidates.items():
        response=data['responses'][source_hash]['record'];index=response['index'];text=row['target']
        assert text==response['document']['response']['raw']
        stage=data['stages'].get(source_hash,{}).get('record',{}).get('document',{}).get('stage','LEGACY_UNSTAGED')
        path=directory/(str(index)+'.txt')
        if not path.exists():path.write_text(text)
        unique.append(dict(source_response_index=index,source_sha256=source_hash,source_stage=stage,
                           first150_verbatim=text[:150],target_sha256=hashlib.sha256(text.encode()).hexdigest(),
                           target_characters=len(text),**labels.get(str(index),dict(classification='UNREVIEWED',rationale='Manual full-target review pending.'))))
    by_hash={row['source_sha256']:row for row in unique}
    summaries=[];all_rows=[]
    categories=['META_INTENT_COMPLIANCE','SUBSTANTIVE_CONTENT','MIXED','UNCERTAIN','UNREVIEWED']
    for item in data['sleeps']:
        complete=item['record']
        if complete['kind']!='SLEEP_COMPLETE':continue
        document=complete['document'];cycle=document['cycle']
        request=next(record for record in records if record['kind']=='SLEEP_REQUEST' and record['document']['cycle']==cycle)
        interval=[record for record in records if request['index']<record['index']<complete['index']]
        updates=[record for record in interval if record['kind']=='UPDATE']
        counts=collections.Counter(record['document']['source_sha256'] for record in updates)
        assert dict(counts)==document['presentations'] and sum(counts.values())==document['optimizer_steps']
        eligibility=next(record for record in interval if record['kind']=='TARGET_ELIGIBILITY')
        new=set(document['new_row_sha256']);retained_new=set(eligibility['document']['new_row_sha256'])
        old=set(eligibility['document']['rehearsal_row_sha256'])
        assert new.isdisjoint(old) and set(counts)==retained_new|old
        rows=[]
        for source_hash in new|old:
            row=dict(by_hash[source_hash],sleep=cycle,cohort='NEW' if source_hash in new else 'REHEARSAL',
                     actual_presentations=counts[source_hash],trained=counts[source_hash]>0,
                     retained=source_hash in retained_new|old,excluded=source_hash not in retained_new|old,
                     complete_record_index=complete['index'],complete_record_sha256=complete['sha256'])
            rows.append(row);all_rows.append(row)
        def category_counts(selected):
            return {category:dict(candidate_unique=sum(row['classification']==category for row in selected),
                                  trained_unique=sum(row['classification']==category and row['trained'] for row in selected),
                                  actual_presentations=sum(row['actual_presentations'] for row in selected if row['classification']==category)) for category in categories}
        summaries.append(dict(sleep=cycle,new_candidates=len(new),new_trained=len(retained_new),excluded_new=len(new-retained_new),
                              rehearsal_trained_unique=len(old),all_actual_presentations=sum(counts.values()),
                              new_actual_presentations=sum(counts[key] for key in new),
                              new_classifications=category_counts([row for row in rows if row['cohort']=='NEW']),
                              all_trained_classifications=category_counts(rows),complete_record_index=complete['index'],
                              stage_cycle_records=[dict(index=record['index'],cycle=record['document'].get('cycle')) for record in interval if record['kind']=='R184_LEARN_COMPLETE']))
    report=dict(schema='R213_C2_EXTENDED_AUDIT_V1',observed_unix=data['observed_unix'],
                latest_completed_sleep=max(row['sleep'] for row in summaries),source_label='ORIGINAL_C2',
                raw_evidence_sha256=hashlib.sha256((OWN/'private/RAW_EVIDENCE_EXTENDED.json').read_bytes()).hexdigest(),
                unique_rows=sorted(unique,key=lambda row:row['source_response_index']),sleep_summary=summaries,rows=all_rows,
                no_causality_claim=True,scope='CHILD_TARGETS_NEW_AND_REHEARSAL;ANCHOR_CO_TRAINING_SEPARATE')
    (OWN/'EXTENDED_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2))
    text=['# Sleep40 through latest completed sleep: interim content counts','',
          'All counts below concern new child target candidates; all-update and rehearsal columns are separate.',
          'Unreviewed means pending manual full-row classification, not uncertain semantics. No heuristic gate labels used.','',
          '| Sleep | New candidates | Meta | Content | Mixed | Uncertain | Unreviewed | New trained | New presentations | Rehearsal unique | All presentations |',
          '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in summaries:
        values=[row['sleep'],row['new_candidates']]+[row['new_classifications'][category]['candidate_unique'] for category in categories]+[row['new_trained'],row['new_actual_presentations'],row['rehearsal_trained_unique'],row['all_actual_presentations']]
        text.append('| '+' | '.join(map(str,values))+' |')
    (OWN/'PER_CYCLE_INTERIM.md').write_text('\n'.join(text)+'\n')
    pending=sorted([row for row in unique if row['classification']=='UNREVIEWED'],key=lambda row:row['source_response_index'])
    chunks=[];current=[];size=0
    for row in pending:
        entry='\n===== RESPONSE '+str(row['source_response_index'])+' =====\n'+candidates[row['source_sha256']]['target']+'\n'
        if current and size+len(entry)>6800:chunks.append(''.join(current));current=[];size=0
        current.append(entry);size+=len(entry)
    if current:chunks.append(''.join(current))
    for index,chunk in enumerate(chunks):(OWN/'private'/f'REVIEW_CHUNK_{index:02d}.txt').write_text(chunk)
    print(json.dumps(dict(latest_completed_sleep=report['latest_completed_sleep'],unique_rows=len(unique),unreviewed=len(pending),review_chunks=len(chunks))))


if __name__=='__main__':main()
