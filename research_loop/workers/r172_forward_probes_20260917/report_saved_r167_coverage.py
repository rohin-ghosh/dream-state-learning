"""Render only saved operational metadata; unavailable per-life fields stay missing."""

import json
from datetime import datetime, timezone
from pathlib import Path

import prep_common as common
import prepare


def main():
    scope, proposal, ledger = prepare.setup()
    old = prepare.HERE.parent/'r167_object_survival/fleet_generation2'
    latest_path = old/'takeover_monitor1/0082.json'
    prior_path = old/'R159_PER_LIFE_COVERAGE_1789655831858085795.json'
    reader = common.Reader(ledger, '_campaign', 'saved_R167_coverage_projection1', [latest_path, prior_path])
    latest, latest_ref = reader.document(latest_path)
    earlier, earlier_ref = reader.document(prior_path)
    common.require(latest['sealed_content_read'] is False and earlier['score_or_response_content_read'] is False,
        'operational_metadata_only')
    common.require('lives' not in latest, 'latest_snapshot_has_only_aggregate_attribution')
    rows=[]
    for life in earlier['lives']:
        initial=sum(0 in sleeps for sleeps in life['complete'].values())
        rows.append(dict(life_id=life['life_id'],initial_completed_jobs_at_earlier_snapshot=initial,
            earlier_snapshot_unix=earlier['observed_unix'],initial_completed_jobs_at_latest_snapshot=None,
            forward_completed_jobs_at_latest_snapshot=None,paired_checkpoints_at_latest_snapshot=None,
            missing_jobs_at_latest_snapshot=None,source_status_at_earlier_snapshot=life['source_status'],
            missingness='LATEST_SNAPSHOT_CONTAINS_NO_PER_LIFE_ATTRIBUTION'))
    result=dict(status='SAVED_OPERATIONAL_COUNTS_WITH_EXPLICIT_ATTRIBUTION_MISSINGNESS',
        observation_unix=latest['observed_unix'],snapshot=latest_ref,earlier_per_life_snapshot=earlier_ref,
        initial_completed_jobs=sum(row['initial_completed_jobs'] for row in latest['conditions'].values()),
        forward_completed_jobs=sum(row['prospective_sleep_completed_jobs'] for row in latest['conditions'].values()),
        paired_checkpoints=latest['matched_completed_checkpoints'],completed_jobs=latest['completed_jobs'],
        charged_calls=latest['calls_charged'],failed_jobs=latest['failed_jobs'],rows=rows,
        new_remote_reads=0,provider_calls=0,model_calls=0,sealed_text_or_score_reads=0,
        observation_UTC=datetime.fromtimestamp(latest['observed_unix'],timezone.utc).isoformat())
    common.write(prepare.PREP/'R159_SAVED_0829_COVERAGE.json',result)
    lines=['# R159 saved execution coverage — September 17, 2026, 08:29:03 PDT', '',
        '**Observation: 15:29:03 UTC / 08:29:03 PDT, NOT a post-wall recount.** No remote read or retry was performed.', '',
        '## Verified aggregate coverage', '',
        '- 71 completed condition jobs / 213 charged calls: **37 initial jobs / 111 calls; 34 forward jobs / 102 calls**.',
        '- **34 paired completed checkpoints** are recorded in aggregate; no per-life pairing breakdown was saved.',
        '- 0 failed jobs, 71 released jobs, 0 unresolved attempts in this observation. A separate 15:34:45 UTC ownership observation confirmed release; it is not the count timestamp.',
        '- The fixed old campaign declared 21 lives / 168 condition jobs. Thus 97 declared jobs were not recorded complete at this snapshot; their per-life capture/admission/pending missingness cannot be reconstructed from this snapshot.', '',
        '## Per-life attribution limit', '',
        '**The requested exact per-life 08:29 table cannot be recovered from the saved 08:29 snapshot:** it contains only aggregate counters, not life IDs or job keys. Receiver-copy markers are not evaluation completions, and recorded process identities are not completion receipts. No count is inferred from either.', '',
        'The table preserves the last existing per-life initial counts at **07:37:11 PDT / 14:37:11 UTC** only as older evidence. They are not relabeled as 08:29 counts. “NR” means not recorded in the 08:29 snapshot, never zero, negative retention, or an execution failure.', '',
        '| Life | Initial completed jobs, 07:37 only | Initial jobs, 08:29 | Forward jobs, 08:29 | Paired checkpoints, 08:29 | Missingness / earlier custody status |',
        '| --- | ---: | --- | --- | --- | --- |']
    for row in rows:
        status='Earlier missing custody; latest attribution NR' if row['source_status_at_earlier_snapshot']=='MISSING_CUSTODY_NOT_NEGATIVE' else 'Latest per-life attribution NR'
        lines.append(f"| {row['life_id']} | {row['initial_completed_jobs_at_earlier_snapshot']} | NR | NR | NR | {status} |")
    lines.extend(['', '## Evidence', '',
        '- Aggregate source: `../r167_object_survival/fleet_generation2/takeover_monitor1/0082.json`.',
        '- Earlier per-life source: `../r167_object_survival/fleet_generation2/R159_PER_LIFE_COVERAGE_1789655831858085795.json`.',
        '- Hash-bound machine projection: `preparation1/R159_SAVED_0829_COVERAGE.json`.',
        '- Post-wall release, separately timed: `RESOURCE_HANDOFF_20260917T1543Z.md`.',
        '- Retention semantics and the R159 private report remain private. This report concerns executed-call coverage only.',
        '', 'Exact 08:29 per-life attribution remains unavailable from the permitted local snapshot. No new remote metadata collection is assumed or requested here.'])
    reference=common.write(prepare.HERE/'R159_SAVED_0829_COVERAGE.md', ('\n'.join(lines)+'\n').encode())
    print(json.dumps(dict(status=result['status'],completed_jobs=result['completed_jobs'],forward_jobs=result['forward_completed_jobs'],
        lives=len(rows),per_life_latest_attribution_available=False,evidence=reference)))


if __name__=='__main__':
    main()
