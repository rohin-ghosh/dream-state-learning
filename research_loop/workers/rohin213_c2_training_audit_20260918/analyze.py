"""Join completed sleep receipts to actual UPDATEs and exact TRAIN child targets."""

import collections
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path


OWN = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def utc(value):
    return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat()


def build():
    os.umask(0o077)
    evidence_path=OWN/'private/RAW_EVIDENCE.json'
    data=json.loads(evidence_path.read_bytes())
    candidates={row['source_sha256']:row for row in data['candidate_rows']}
    assert len(candidates)==len(data['candidate_rows']), 'candidate_hash_repeated_across_sleeps'
    metadata=data['selected_metadata']
    for previous,current in zip(metadata,metadata[1:]):
        assert current['index']==previous['index']+1 and current['previous_sha256']==previous['sha256']
    records=sorted([entry['record'] for entry in data['sleeps']]+[
        entry['record'] for entry in data['relevant_records']],key=lambda record:record['index'])
    private_rows=OWN/'private/rows'
    private_rows.mkdir(mode=0o700,exist_ok=True)
    labels_path=OWN/'private/CLASSIFICATIONS.json'
    labels=json.loads(labels_path.read_bytes()) if labels_path.exists() else {}
    rows=[]
    sleep_summary=[]
    for sleep in data['sleeps']:
        complete=sleep['record']
        if complete['kind']!='SLEEP_COMPLETE':
            continue
        document=complete['document']
        cycle=document['cycle']
        requests=[record for record in records if record['kind']=='SLEEP_REQUEST' and record['document']['cycle']==cycle]
        assert len(requests)==1, 'multiple_sleep_attempts_require_explicit_review'
        request=requests[0]
        interval=[record for record in records if request['index']<record['index']<complete['index']]
        eligibility=next(record for record in interval if record['kind']=='TARGET_ELIGIBILITY')
        recipe=next(record for record in interval if record['kind']=='SLEEP_RECIPE')
        updates=[record for record in interval if record['kind']=='UPDATE']
        counts=collections.Counter(record['document']['source_sha256'] for record in updates)
        assert dict(counts)==document['presentations']
        assert sum(counts.values())==document['optimizer_steps']
        assert recipe['document']['selected_old_rows']==0
        assert eligibility['document']['rehearsal_row_sha256']==[]
        retained=set(eligibility['document']['new_row_sha256'])
        assert set(counts)==retained, 'retained_is_not_automatically_trained'
        hashes=document['new_row_sha256']
        excluded=set(hashes)-retained
        exclusions=eligibility['document']['excluded']
        assert excluded=={entry['source_sha256'] for entry in exclusions}
        for source_hash in hashes:
            candidate=candidates[source_hash]
            response=data['responses'][source_hash]['record']
            stage=data['stages'][source_hash]['record']
            raw=candidate['target']
            assert candidate['actor']=='child' and candidate['split']=='TRAIN'
            assert candidate['target_loss'] is True and candidate['prefix_loss'] is False
            assert response['document']['response']['raw']==raw
            assert digest(response['document'])==source_hash
            assert stage['document']['source_sha256']==source_hash
            row_key=f'{cycle}_{response["index"]}'
            raw_path=private_rows/(row_key+'.txt')
            if not raw_path.exists():
                raw_path.write_text(raw)
            label=labels.get(row_key,dict(classification='UNREVIEWED',rationale='Full-row review pending.'))
            selected_exclusions=[entry for entry in exclusions if entry['source_sha256']==source_hash]
            entry=dict(sleep=cycle,row_key=row_key,source_response_index=response['index'],
                       source_stage=stage['document']['stage'],source_sha256=source_hash,
                       response_record_sha256=response['sha256'],stage_record_index=stage['index'],
                       stage_record_sha256=stage['sha256'],target_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                       target_characters=len(raw),first150_verbatim=raw[:150],
                       source_finished_utc=utc(response['document']['finished_unix']),
                       retained=source_hash in retained,excluded=source_hash in excluded,
                       actual_presentations=counts[source_hash],trained=counts[source_hash]>0,
                       update_indices=[record['index'] for record in updates if record['document']['source_sha256']==source_hash],
                       exclusion_reasons=sorted({item['reason'] for item in selected_exclusions}),
                       complete_record_index=complete['index'],complete_record_sha256=complete['sha256'],
                       eligibility_record_index=eligibility['index'],eligibility_record_sha256=eligibility['sha256'],
                       **label)
            rows.append(entry)
        sleep_summary.append(dict(sleep=cycle,request_record_index=request['index'],complete_record_index=complete['index'],
                                  complete_utc=utc(sleep['file_mtime_unix']),candidate_unique=len(hashes),
                                  retained_unique=len(retained),excluded_unique=len(excluded),
                                  actually_trained_unique=len(counts),actual_presentations=sum(counts.values()),
                                  update_events=len(updates),receipt_update_agreement=True))
    report=dict(schema='R213_C2_TRAINED_ROW_AUDIT_V1',source_label='ORIGINAL_C2',
                observed_utc=utc(data['observed_unix']),raw_evidence_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                completed_sleep_range=[52,63],read_only=True,signals=False,controls_modified=False,
                sleep_summary=sleep_summary,rows=rows,classification_complete=all(row['classification']!='UNREVIEWED' for row in rows),
                no_causality_claim=True,counts=dict(candidate_unique=len(rows),trained_unique=sum(row['trained'] for row in rows),
                                                excluded_unique=sum(row['excluded'] for row in rows),
                                                actual_presentations=sum(row['actual_presentations'] for row in rows)))
    categories=sorted({row['classification'] for row in rows})
    report['classification_counts']={category:dict(candidate_unique=sum(row['classification']==category for row in rows),
        trained_unique=sum(row['classification']==category and row['trained'] for row in rows),
        excluded_unique=sum(row['classification']==category and row['excluded'] for row in rows),
        presentation_weighted=sum(row['actual_presentations'] for row in rows if row['classification']==category)) for category in categories}
    for sleep in sleep_summary:
        selected=[row for row in rows if row['sleep']==sleep['sleep']]
        sleep['classification_counts']={category:dict(trained_unique=sum(row['classification']==category and row['trained'] for row in selected),
            presentation_weighted=sum(row['actual_presentations'] for row in selected if row['classification']==category)) for category in categories}
    with (OWN/'AUDIT.json').open('w') as output:
        json.dump(report,output,ensure_ascii=False,indent=2,sort_keys=True)
    fields=['sleep','source_response_index','source_stage','source_sha256','target_sha256','first150_verbatim',
            'retained','excluded','trained','actual_presentations','classification','rationale','exclusion_reasons',
            'complete_record_index','eligibility_record_index']
    with (OWN/'ROWS.csv').open('w',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    text=['# Original C2 sleeps52–63: first verified count table','',
          'Read-only original-life audit. Full-target labels are complete; see RESULT_52_63.md. No causal inference.',
          'Counts below are actual UPDATE events cross-checked against completed SLEEP_COMPLETE presentations, not candidate schedules.','',
          '| Sleep | Candidate unique | Trained unique | Excluded unique | Actual presentations | COMPLETE record |',
          '|---:|---:|---:|---:|---:|---:|']
    for sleep in sleep_summary:
        text.append('| '+' | '.join(str(sleep[key]) for key in ('sleep','candidate_unique','actually_trained_unique','excluded_unique','actual_presentations','complete_record_index'))+' |')
    text.extend(['', 'Exact first150-character target previews and full source/target hashes: `ROWS.csv` and `AUDIT.json`.',
                 'Full raw targets are kept separately under `private/rows/`, not in this public report.'])
    (OWN/'FIRST_PARTIAL.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(counts=report['counts'],classification_counts=report['classification_counts'],
                         chain_metadata_links_verified=len(metadata)-1,rows=len(rows))))


if __name__=='__main__':
    build()
