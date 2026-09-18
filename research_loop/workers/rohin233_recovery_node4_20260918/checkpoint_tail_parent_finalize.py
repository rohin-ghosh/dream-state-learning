"""Export bounded delivery evidence; never publish messages or signal lives."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from checkpoint_tail_parent_current import refresh
from deadline_resume import read, sha, write


OWN = Path(__file__).resolve().parent
MANIFEST = OWN / 'private/checkpoint_tail_parent_r233_control/MANIFEST.json'


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def finalize(disposition):
    delivery_path = OWN / 'CHECKPOINT_TAIL_V_DELIVERY.json'
    delivery = read(delivery_path)
    act_path = OWN / 'CHECKPOINT_TAIL_PARENT_FIRST_ACT.public.json'
    act_cut = read(act_path)
    actual_act = act_cut['first_ACT']
    if (act_cut['status'] != 'COMMITTED_ACT_VERIFIED' or not actual_act['commit']
            or not actual_act['stage_record'] or actual_act['stage'] != 'ACT'
            or not delivery.get('first_render') or not delivery.get('inbox_receipt')):
        raise ValueError('no_final_delivery_claim_without_verified_INBOX_REQUEST_committed_ACT')
    manifest = read(MANIFEST)
    output = Path(manifest['output'])
    attempts = []
    brief = Path(manifest['policy_addendum']).read_text()
    for result_path in sorted(output.glob('parent_*/RESULT.json')):
        result = read(result_path)
        source_path = result_path.parent / 'SOURCE.json'
        intent_path = result_path.parent / 'DISPATCH_INTENT.json'
        system_path = result_path.parent / 'SYSTEM.txt'
        intent = read(intent_path)
        source = read(source_path)
        if (sha(source_path) != intent['source_sha256'] or sha(system_path) != intent['system_sha256']
                or source['head_sha256'] != result['source_head_sha256'] or brief not in system_path.read_text()):
            raise ValueError('actual_dispatched_current_brief_and_source')
        attempts.append(dict(status=result['status'], result_sha256=sha(result_path),
            source_response_count=result['source_response_count'], source_head_sha256=result['source_head_sha256'],
            source_sha256=sha(source_path), system_sha256=sha(system_path),
            started_utc=utc(result['started_unix']), finished_utc=utc(result['finished_unix']),
            published_utc=utc(result['sent_unix']) if result.get('inbox_publication') else None,
            publication=result.get('inbox_publication'), message=result.get('response', {}).get('message'),
            publication_is_not_render_proof=True))
    current = refresh(MANIFEST, 'CORRECTION_INBOX_REQUEST_FIRST_COMMITTED_ACT_VERIFIED')
    current['actual_first_ACT'] = actual_act
    current['first_ACT_proof_basis'] = act_cut['proof_basis']
    current_path = OWN / 'CHECKPOINT_TAIL_PARENT_LIVE.public.json'
    public = read(current_path)
    archive = OWN / 'private' / ('PARENT_PUBLIC_PREVIOUS_' + sha(current_path) + '.json')
    if not archive.exists():
        write(archive, public)
    public.update(actual_first_ACT=actual_act, first_ACT_proof_basis=act_cut['proof_basis'],
        first_ACT_cut_sha256=sha(act_path),
        original_correction_verbatim_in_ACT_request=act_cut['original_correction_verbatim_in_ACT_request'],
        provider_correction_verbatim_in_ACT_request=act_cut['provider_correction_verbatim_in_ACT_request'])
    temporary = current_path.with_suffix('.final.tmp')
    write(temporary, public)
    os.replace(temporary, current_path)
    receipt = dict(schema='R233_C2_PARENT_CORRECTION_FINAL_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        delivery_observed_utc=delivery['observed_utc'], delivery_sha256=sha(delivery_path),
        original_source=read(OWN / 'CHECKPOINT_TAIL_V_CORRECTION_PUBLISHED.json')['source'],
        original_publication=read(OWN / 'CHECKPOINT_TAIL_V_CORRECTION_PUBLISHED.json'),
        current_parent=current, current_brief_sha256=sha(Path(manifest['policy_addendum'])),
        current_parent_config_sha256=sha(Path(manifest['config_path'])),
        inbox_receipt=delivery['inbox_receipt'], first_render=delivery['first_render'],
        first_render_started_utc=utc(delivery['first_render']['started_unix']),
        first_ACT=actual_act, first_ACT_finished_utc=utc(actual_act['finished_unix']),
        first_ACT_cut_sha256=sha(act_path), first_ACT_proof_basis=act_cut['proof_basis'],
        original_correction_verbatim_in_ACT_request=act_cut['original_correction_verbatim_in_ACT_request'],
        provider_correction_verbatim_in_ACT_request=act_cut['provider_correction_verbatim_in_ACT_request'],
        compaction_before_ACT=act_cut['compaction'],
        first_THINK=next((stage for stage in delivery['stages'] if stage['stage']=='THINK'), None),
        actual_new_parent_attempts=attempts, semantic_disposition=disposition,
        contextual_confounds=['Old pre-handoff Byte request f3df03f60e984c54a3ee5ece885e000b '
            'was registered after the newer correction. The new provider explicitly acknowledged the conflict.'],
        native=delivery['native'], native_signals=[], journal_writes=0, duplicate_native_dispatches=0,
        supplied_context_not_unaided_recall=True, no_adapter_retention_claim=True,
        continuation='Same R233 CPU parent remains alive, cadence1 through 2026-09-20T18:00:00Z; no native action.')
    destination = OWN / 'CHECKPOINT_TAIL_PARENT_DELIVERY_FINAL.public.json'
    write(destination, receipt)
    print(json.dumps(dict(path=str(destination), sha256=sha(destination),
        request=delivery['first_render']['index'], ACT=actual_act['record']['index'],
        first_ACT_finished_utc=receipt['first_ACT_finished_utc'], current_parent=current['parent']), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--disposition', required=True)
    options = parser.parse_args()
    finalize(options.disposition)
