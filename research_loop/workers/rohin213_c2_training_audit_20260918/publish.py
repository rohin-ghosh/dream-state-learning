"""Publish fixed-cut audit counts without disclosing full private targets."""

import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import re


OWN = Path(__file__).resolve().parent
CATEGORIES = ('META_INTENT_COMPLIANCE', 'SUBSTANTIVE_CONTENT', 'MIXED', 'UNCERTAIN')


def summarize(rows):
    sources = collections.defaultdict(set)
    presentations = collections.Counter()
    for row in rows:
        assert row['classification'] in CATEGORIES
        assert row['trained'] == (row['actual_presentations'] > 0)
        if row['trained']:
            sources[row['classification']].add(row['source_sha256'])
        presentations[row['classification']] += row['actual_presentations']
    return {category: {'trained_unique': len(sources[category]),
                       'actual_presentations': presentations[category]}
            for category in CATEGORIES}


def sample_report(rows, limit=40):
    selected = sorted(rows, key=lambda row: row['source_response_index'])[-limit:]
    assert len({row['source_sha256'] for row in selected}) == len(selected)
    return {'response_indices': [row['source_response_index'] for row in selected],
            'source_sha256': [row['source_sha256'] for row in selected],
            'classifications': dict(collections.Counter(row['classification'] for row in selected)),
            'count': len(selected)}


def markdown_cell(value):
    return str(value).replace('|', '&#124;').replace('\n', '\\n').replace('\r', '\\r')


def main():
    os.umask(0o077)
    extended = json.loads((OWN / 'EXTENDED_AUDIT.json').read_bytes())
    original = json.loads((OWN / 'AUDIT.json').read_bytes())
    raw = json.loads((OWN / 'private/RAW_EVIDENCE_EXTENDED.json').read_bytes())
    rows = extended['rows']
    new_rows = [row for row in rows if row['cohort'] == 'NEW']
    rehearsal = [row for row in rows if row['cohort'] == 'REHEARSAL']
    latest = extended['latest_completed_sleep']
    complete_indices = {row['sleep']: row['complete_record_index'] for row in extended['sleep_summary']}
    source_by_hash = {row['source_sha256']: row for row in extended['unique_rows']}
    original_by_hash = {row['source_sha256']: row for row in original['rows']}
    for row in new_rows:
        if row['source_sha256'] in original_by_hash:
            previous = original_by_hash[row['source_sha256']]
            for field in ('sleep', 'actual_presentations', 'classification', 'trained', 'excluded'):
                assert row[field] == previous[field], (field, row['source_response_index'])
    pending = sorted({entry['record']['document']['cycle'] for entry in raw['sleeps']
                      if entry['record']['kind'] == 'SLEEP_REQUEST'} - set(complete_indices))
    pending_sources = set(source_by_hash) - {row['source_sha256'] for row in rows}
    trained_rows = {row['source_sha256']: row for row in rows if row['trained']}
    current_rows = [row for row in new_rows if 62 <= row['sleep'] <= 65]
    samples = {
        'last40_completed_trained_new': sample_report([row for row in new_rows if row['trained']]),
        'last40_completed_new_candidates': sample_report(new_rows),
        'last40_latest_observed_candidates_including_pending': sample_report(extended['unique_rows']),
    }
    stage_counts = {stage: summarize([row for row in rows if row['source_stage'] == stage])
                    for stage in sorted({row['source_stage'] for row in rows})}
    clock = datetime.datetime.fromtimestamp(extended['observed_unix'], datetime.timezone.utc).isoformat()
    anchor = []
    for entry in raw['sleeps']:
        document = entry['record']['document']
        if entry['record']['kind'] == 'SLEEP_COMPLETE':
            anchor.append({key: document.get(key) for key in
                           ('cycle', 'child_token_exposures', 'anchor_token_exposures', 'anchor_lambda')})
    counter_mapping = []
    for entry in raw['relevant_records']:
        record = entry['record']
        if record['kind'] == 'R189_OUTCOME_CYCLE':
            next_requests = [item['record'] for item in raw['sleeps']
                             if item['record']['kind'] == 'SLEEP_REQUEST'
                             and item['record']['index'] > record['index']]
            if next_requests:
                request = min(next_requests, key=lambda item: item['index'])
                counter_mapping.append({'record_index': record['index'],
                                        'runtime_outcome_counter': record['document'].get('report', {}).get('cycle'),
                                        'next_sleep_number': request['document']['cycle']})
    report = dict(schema='R213_C2_MANUAL_AUDIT_FINAL_V1', observed_utc=clock,
                  raw_evidence_sha256=extended['raw_evidence_sha256'],
                  completed_sleep_range=[40, latest], completed_trained_unique=len(trained_rows),
                  completed_new_candidates=len(new_rows),
                  completed_new_trained=sum(row['trained'] for row in new_rows),
                  completed_new_excluded=sum(row['excluded'] for row in new_rows),
                  all_actual_presentations=sum(row['actual_presentations'] for row in rows),
                  new_actual_presentations=sum(row['actual_presentations'] for row in new_rows),
                  rehearsal_actual_presentations=sum(row['actual_presentations'] for row in rehearsal),
                  overall=summarize(rows), new_only=summarize(new_rows), rehearsal_only=summarize(rehearsal),
                  stages=stage_counts, samples=samples, per_sleep=extended['sleep_summary'],
                  sleeps62_65=dict(candidates=len(current_rows), trained=sum(row['trained'] for row in current_rows),
                                    classifications=summarize(current_rows)),
                  pending_sleep_numbers=pending,
                  pending_source_response_indices=sorted(source_by_hash[key]['source_response_index'] for key in pending_sources),
                  pending_actual_updates='NOT_ESTABLISHED_BY_THIS_CUT;NOT_ASSUMED_ZERO',
                  anchor_exposures_unclassified=anchor, runtime_counter_mapping=counter_mapping,
                  heuristic_used_for_manual_labels=False, causality_claim=False, controls_changed=False,
                  signals_sent=False)
    assert sum(item['trained_unique'] for item in report['overall'].values()) == len(trained_rows)
    assert sum(item['actual_presentations'] for item in report['overall'].values()) == report['all_actual_presentations']
    (OWN / 'FINAL_COUNTS.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (OWN / 'MANUAL_LABELS.json').write_text(json.dumps([
        {key: row[key] for key in ('source_response_index', 'source_sha256', 'classification', 'rationale')}
        for row in extended['unique_rows']], indent=2, sort_keys=True) + '\n')
    text = ['# Original C2: independently audited content of actual training', '',
            f'Fixed observation cut: {clock}; completed sleeps40–{latest}.',
            'Manual full-row review; source stage, eligibility and executed UPDATE counts are independently joined.',
            'No C2 control changes, no signals, no causal or quality claim. No heuristic gate used to label rows.', '',
            f"Completed: {report['completed_new_candidates']} NEW candidates, {report['completed_new_trained']} NEW trained, "
            f"{report['completed_new_excluded']} excluded; {report['completed_trained_unique']} distinct trained sources including rehearsal.",
            f"Actual presentations: {report['all_actual_presentations']} = {report['new_actual_presentations']} NEW + "
            f"{report['rehearsal_actual_presentations']} REHEARSAL. Every completed sleep agrees with UPDATE events.", '',
            '| Manual class | All trained distinct | All presentations | NEW trained | NEW presentations |',
            '|---|---:|---:|---:|---:|']
    for category in CATEGORIES:
        total = report['overall'][category]
        new = report['new_only'][category]
        text.append(f"| {category} | {total['trained_unique']} | {total['actual_presentations']} | {new['trained_unique']} | {new['actual_presentations']} |")
    text += ['', '## Per-sleep actual NEW training', '',
             'M=meta-intent/compliance; S=substantive content; X=mixed; U=uncertain.',
             'M/S/X/U are trained row counts, not candidates. P columns are actual presentations.', '',
             '| Sleep | Candidates | Excluded | M | S | X | U | M-P | S-P | X-P | U-P | Rehearsal-P | All-P | COMPLETE |',
             '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in report['per_sleep']:
        categories = row['new_classifications']
        values = [row['sleep'], row['new_candidates'], row['excluded_new']]
        values += [categories[category]['trained_unique'] for category in CATEGORIES]
        values += [categories[category]['actual_presentations'] for category in CATEGORIES]
        values += [row['all_actual_presentations'] - row['new_actual_presentations'], row['all_actual_presentations'], row['complete_record_index']]
        text.append('| ' + ' | '.join(map(str, values)) + ' |')
    text += ['', 'Sleep40/41 include117/120 distinct older rehearsal rows at one presentation each;',
             'their NEW targets still receive16 presentations each. Later completed sleeps contain no rehearsal.', '',
             '## The reported last40/all-meta comparison', '',
             'Samples below are explicitly bound by source IDs/hashes in FINAL_COUNTS.json; different cuts are not interchangeable.']
    for name, sample in samples.items():
        text.append(f"- {name}: {sample['count']} rows; {json.dumps(sample['classifications'], sort_keys=True)}.")
    text += ['', f"Sleeps62–65: {len(current_rows)} candidates; {sum(row['trained'] for row in current_rows)} actually trained.",
             'In the completed-trained last40 sample, pure META25 plus MIXED6 equals31 rows containing meta.',
             'That may explain a binary31/40 description, but MIXED is not relabeled as pure meta here.',
             'Under this manual rubric, THINK6731 is a substantive conceptual answer but excluded;',
             '6738/6749 are trained MIXED;6820 is a trained actual narrative;7036 is trained calculation code.',
             'Thus an all-pure-meta claim is not reproduced on this stated sample/rubric. This is not a causal rebuttal.', '',
             '## Boundaries and limitations', '',
             'Sleep means SLEEP_COMPLETE.document.cycle, not runtime-local R189 outcome counter, which resets.',
             'FINAL_COUNTS.json includes an explicit counter-to-next-sleep mapping. Journal indices are neither counter.',
             'Sleep52 trained after02:53:07.145 compaction, but all five of its targets were generated before it.',
             'The latest pending sleep is not included in completed counts; its actual update count is not established',
             'by this collector cut and must not be called zero. Pending target labels describe content only.',
             'Each UPDATE also co-trains fixed ANCHOR material (weight0.25); child/anchor token exposures are recorded',
             'separately in FINAL_COUNTS.json. These content counts do not classify all loss or all training tokens.',
             'Full-target manual review is single-auditor, with explicit rationales and uncertain cases retained.',
             'Substantive does not mean correct, useful, executed or new; MIXED remains a separate category.',
             'Public target previews are exact first150 Unicode characters, escaped only for display; full rows are private.',
             'Collection validates each full canonical journal record before projecting it. Stored SLEEP projections omit',
             'resume_state; their record SHA binds the original full record, not the smaller projection.',
             '', 'Detailed original52–63 sources/stages/hashes/eligibility/UPDATE indices: AUDIT.json and ROWS.csv.',
             'All40–65 rows and stage counts: EXTENDED_AUDIT.json and FINAL_COUNTS.json.',
             'No original C2 runtime, parent, inbox, checkpoint or lease was changed.']
    (OWN / 'FINAL_REPORT.md').write_text('\n'.join(text) + '\n')
    previews = ['# Sleeps52–63 exact150-character preview index', '',
                'The preview field is a JSON string literal: escapes represent original newlines/control characters,',
                'not repairs. Full hashes and exact UPDATE indices are in AUDIT.json. R=retained; X=excluded.', '',
                '| Sleep | RESPONSE | Stage | R | X | Actual P | Class | First150 verbatim (escaped display) |',
                '|---:|---:|---|---|---|---:|---|---|']
    for row in original['rows']:
        values = [row['sleep'], row['source_response_index'], row['source_stage'], row['retained'],
                  row['excluded'], row['actual_presentations'], row['classification'],
                  json.dumps(row['first150_verbatim'], ensure_ascii=False)]
        previews.append('| ' + ' | '.join(markdown_cell(value) for value in values) + ' |')
    (OWN / 'PREVIEWS_52_63.md').write_text('\n'.join(previews) + '\n')
    forbidden = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE).*KEY-----|\b(?:ipp2-|ovx[1-9][.-])|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|gh[pousr]_[A-Za-z0-9]{20,}')
    files = [path for path in OWN.iterdir() if path.suffix in ('.md', '.json', '.csv')]
    findings = [{'file': path.name, 'match_count': len(forbidden.findall(path.read_text()))}
                for path in files if forbidden.search(path.read_text())]
    receipt = dict(schema='R213_PUBLIC_REPORT_PATTERN_SCAN_V1',
                   scanned_files=[path.name for path in files], findings=findings,
                   status='PASS' if not findings else 'REVIEW_REQUIRED',
                   scope='Common IPv4/infrastructure-host/private-key/token patterns; not a universal secrets guarantee',
                   full_rows_private=True, private_directory_mode=oct((OWN / 'private').stat().st_mode & 0o777))
    (OWN / 'PUBLIC_SCAN.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    assert not findings, 'public_artifact_pattern_match_requires_manual_review'
    print(json.dumps({key: report[key] for key in ('completed_sleep_range', 'completed_trained_unique',
                     'all_actual_presentations', 'new_actual_presentations', 'rehearsal_actual_presentations',
                     'overall', 'samples', 'sleeps62_65')}))


if __name__ == '__main__':
    main()
