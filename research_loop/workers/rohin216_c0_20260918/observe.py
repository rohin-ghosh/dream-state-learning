"""Read-only, public-safe C0 launch and first-target eligibility receipt."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


def main(root):
    sys.path.insert(0, str(root / 'source'))
    from organism_v6.orch_r125_continual_stream import digest
    records = []
    for path in sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json')):
        record = json.loads(path.read_text())
        if record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'}):
            raise ValueError('C0_canonical_record_hash')
        records.append(record)
    loaded = next(record for record in records if record['kind'] == 'LOADED')
    birth = next(record for record in records if record['kind'] == 'R205_FIXED_C2_FORK')
    compaction = next(record for record in records if record['kind'] == 'COMPACTION')
    pinned = next(record for record in records if record['kind'] == 'CONTEXT_INPUT'
        and record['document'].get('kind') == 'R216_C0_PINNED_HISTORICAL_REFERENCE')
    source_context = json.loads(Path(birth['document']['source_context_path']).read_text())
    original = source_context['document']['state']['state']['history']['working_state']
    restored = birth['document']['state']['state']['history']['working_state']
    carried = compaction['document']['state']['state']['history']['working_state']
    if not original == restored == carried:
        raise ValueError('C0_working_state_not_verbatim_through_birth')
    request = next(record for record in records if record['kind'] == 'REQUEST')
    transcript = (root / 'source/context/ROHIN_C2_TRANSCRIPT.md').read_text()
    parent = next((message for message in request['document']['messages']
        if 'Astra: I am Astra, your new parent for this math-games life.' in str(message.get('content', ''))), None)
    eligibility = [record for record in records if record['kind'] == 'TARGET_ELIGIBILITY']
    checks = []
    for record in eligibility:
        document = record['document']
        proof = document.get('learn_review_filter', {}).get('content_target_filter', {})
        checks.append(dict(record=record['index'], record_sha256=record['sha256'], policy=proof.get('policy'),
            checked_targets=len(proof.get('checks', [])),
            content_exclusions=[item['reason'] for item in proof.get('excluded', [])],
            all_filter_exclusions=[item['reason'] for item in document.get('excluded', [])],
            retained_counts=document.get('learn_review_filter_counts'), raw_modified=proof.get('raw_modified')))
    source = loaded['document']
    result = dict(schema='R216_C0_ACTUAL_LAUNCH_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        node='node2', physical_gpu=4, life='C0', root_basename=root.name,
        native_pid=source['pid'], native_exists=Path('/proc', str(source['pid'])).exists(),
        loaded_utc=datetime.fromtimestamp(source['loaded_unix'], timezone.utc).isoformat(),
        loaded_record=loaded['index'], loaded_record_sha256=loaded['sha256'],
        adapter_sha256=source['adapter_sha256'], base_sha256=source['base_sha256'], optimizer_steps=source['optimizer_steps'],
        inherited_source_checkpoint=51, current_C2_modified=False, snapshot_working_state_verbatim=True,
        birth_compaction_record=compaction['index'], pinned_reference_record=pinned['index'],
        historical_transcript_sha256=hashlib.sha256(transcript.encode()).hexdigest(),
        transcript_verbatim_in_first_request=any(transcript in str(message.get('content', '')) for message in request['document']['messages']),
        actual_parent_render=parent is not None, first_request_record=request['index'],
        first_prompt_tokens=request['document'].get('prompt_tokens'),
        first_render_all_history_masked=request['document'].get('render_receipt', {}).get('all_history_tokens_masked'),
        target_eligibility=checks, learning_or_retention_success_claimed=False,
        last_record=dict(index=records[-1]['index'], kind=records[-1]['kind'], sha256=records[-1]['sha256']))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
