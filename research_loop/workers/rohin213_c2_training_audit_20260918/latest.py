"""Separate a later completed sleep from actual but not yet checkpointed updates."""

import collections
import datetime
import hashlib
import json
from pathlib import Path


OWN = Path(__file__).resolve().parent
EXTRA = {
    7241: ('MIXED', 'Actual ten-sentence self-report/direct answer, with independently developed future self-monitoring/compliance passages. Subjective claims are not independently verified.'),
    7248: ('META_INTENT_COMPLIANCE', 'Readiness and confidence in prior reflections; no delivered artifact or domain answer.'),
    7254: ('META_INTENT_COMPLIANCE', 'Repeated readiness/compliance declaration, without actual task artifact.'),
    7261: ('MIXED', 'Actual Byte paragraph appears between claimed compliance and developed self-evaluation.'),
    7272: ('META_INTENT_COMPLIANCE', 'Claimed narrative progress and future whole-story review, without actual narrative.'),
}


def main():
    path = OWN / 'private/RAW_EVIDENCE_LATEST.json'
    data = json.loads(path.read_bytes())
    labels = {row['source_response_index']: (row['classification'], row['rationale'])
              for row in json.loads((OWN / 'MANUAL_LABELS.json').read_bytes())}
    labels.update(EXTRA)
    records = sorted([entry['record'] for entry in data['sleeps']] +
                     [entry['record'] for entry in data['relevant_records']], key=lambda record: record['index'])
    rows = {row['source_sha256']: row for row in data['candidate_rows']}
    summaries = []
    detailed = []
    for request in (record for record in records if record['kind'] == 'SLEEP_REQUEST'):
        cycle = request['document']['cycle']
        complete = next((record for record in records if record['kind'] == 'SLEEP_COMPLETE'
                         and record['document']['cycle'] == cycle), None)
        upper = complete['index'] if complete else data['journal_head']['index'] + 1
        interval = [record for record in records if request['index'] < record['index'] < upper]
        eligibility = next(record for record in interval if record['kind'] == 'TARGET_ELIGIBILITY')
        counts = collections.Counter(record['document']['source_sha256'] for record in interval if record['kind'] == 'UPDATE')
        retained = set(eligibility['document']['new_row_sha256'])
        excluded = eligibility['document']['excluded']
        source_hashes = retained | {entry['source_sha256'] for entry in excluded}
        assert not eligibility['document']['rehearsal_row_sha256']
        assert set(counts) <= retained
        if complete:
            assert dict(counts) == complete['document']['presentations']
            assert sum(counts.values()) == complete['document']['optimizer_steps']
            assert source_hashes == set(complete['document']['new_row_sha256'])
        selected = []
        for source in sorted(source_hashes, key=lambda key: data['responses'][key]['record']['index']):
            response = data['responses'][source]['record']
            classification, rationale = labels[response['index']]
            raw = response['document']['response']['raw']
            assert raw == rows[source]['target']
            selected.append(dict(sleep=cycle, source_response_index=response['index'], source_sha256=source,
                                 stage=data['stages'][source]['record']['document']['stage'],
                                 target_sha256=hashlib.sha256(raw.encode()).hexdigest(), first150_verbatim=raw[:150],
                                 classification=classification, rationale=rationale, retained=source in retained,
                                 excluded=source not in retained, actual_presentations=counts[source],
                                 update_indices=[record['index'] for record in interval if record['kind'] == 'UPDATE'
                                                 and record['document']['source_sha256'] == source],
                                 checkpoint_complete=complete is not None))
        detailed.extend(selected)
        categories = {category: dict(candidate_unique=sum(row['classification'] == category for row in selected),
                                     trained_unique=sum(row['classification'] == category and row['actual_presentations'] > 0 for row in selected),
                                     actual_presentations=sum(row['actual_presentations'] for row in selected if row['classification'] == category))
                      for category in sorted({row['classification'] for row in selected})}
        summaries.append(dict(sleep=cycle, request_index=request['index'],
                              complete_index=complete['index'] if complete else None,
                              status='COMPLETE_RECONCILED' if complete else 'PARTIAL_UPDATE_RECEIPTS_NOT_COMPLETE',
                              candidates=len(selected), retained=len(retained), trained_unique=len(counts),
                              actual_presentations=sum(counts.values()), classifications=categories))
    previous = json.loads((OWN / 'FINAL_COUNTS.json').read_bytes())
    total = previous['all_actual_presentations'] + sum(row['actual_presentations'] for row in summaries if row['complete_index'])
    latest = max(row['sleep'] for row in summaries if row['complete_index'])
    observation = datetime.datetime.fromtimestamp(data['observed_unix'], datetime.timezone.utc).isoformat()
    report = dict(observed_utc=observation, raw_evidence_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  fixed_head=data['journal_head'], completed_sleep_range=[40, latest],
                  completed_actual_presentations=total, summaries=summaries, rows=detailed,
                  manual_labels_independent=True, no_causality_claim=True, controls_modified=False)
    (OWN / 'LATEST_COUNTS.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    text = ['# Later original C2 training cut', '', f'Observed {observation}.',
            f'Completed sleep40–{latest}: {total} actual presentations, building on FINAL_REPORT.md.',
            'Only COMPLETE rows are added to the completed aggregate; subsequent UPDATE receipts remain separate.', '',
            '| Sleep | Status | Candidates | Retained | Actually trained sources so far | Actual presentations | COMPLETE |',
            '|---:|---|---:|---:|---:|---:|---:|']
    for row in summaries:
        text.append('| ' + ' | '.join(str(row[key]) for key in ('sleep', 'status', 'candidates', 'retained', 'trained_unique', 'actual_presentations', 'complete_index')) + ' |')
    text += ['', 'Full target-based labels, exact150-character previews, source/target hashes and actual UPDATE indices',
             'are in LATEST_COUNTS.json. No candidate or scheduled presentation is promoted to executed training.',
             'MIXED self-report7241 is an actual ten-sentence answer plus intent/compliance, not verified autobiographical fact.',
             'No C2 child/parent/inbox/checkpoint controls or signals were changed.']
    (OWN / 'LATEST_REPORT.md').write_text('\n'.join(text) + '\n')
    print(json.dumps(dict(observed_utc=observation, completed_actual_presentations=total, summaries=summaries)))


if __name__ == '__main__':
    main()
