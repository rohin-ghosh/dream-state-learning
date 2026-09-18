import json
import os
from pathlib import Path
import re
import time


def disposition(commit_exists, matches, verified_snapshot):
    if not verified_snapshot:
        return 'UNKNOWN_INCOMPLETE_JOURNAL_COVERAGE'
    if not commit_exists:
        return 'MISSING_COMMIT' if not matches else 'JOURNAL_BOUNDARY_WITHOUT_COMMIT'
    if not matches:
        return 'ORPHAN_COMMIT_NO_SLEEP_COMPLETE_IN_VERIFIED_SNAPSHOT'
    if len(matches) != 1 or not matches[0]['exact_checkpoint_binding']:
        return 'AMBIGUOUS_OR_MISMATCHED_BOUNDARY'
    return 'COMPLETED_BOUNDARY_METADATA_BOUND_PENDING_CUSTODY'


def observe(base):
    root = base['ROOT']
    reader = base['Reader'](root)
    digest, canonical = base['digest'], base['canonical']
    cohort_raw, cohort_ref = reader.read(root/'COHORT.json')
    if digest(cohort_raw) != base['COHORT']:
        raise ValueError('wrong_cohort')
    result = dict(schema='R159_SLEEP_BOUNDARY_METADATA_INVENTORY_V1', started_unix=time.time(),
        cohort=cohort_ref, arms={}, source_read_end_unix=base['END'], source_written=False,
        adapter_optimizer_rng_payload_read=False, readouts_opened=False, held_contents_returned=False,
        copied_checkpoints=False, enrolled=False, dispatched=False, exact_event_times_inferred=False)
    for arm in base['ARMS']:
        arm_root = root/arm
        commits, entries = {}, {}
        report = dict(root=str(arm_root), intended={}, sleep_complete_records=[], coverage='UNKNOWN')
        result['arms'][arm] = report
        for milestone in (1, 2, 4):
            checkpoint = arm_root/'checkpoints'/f'sleep_{milestone:06d}'/'COMMIT.json'
            entry = dict(source_commit_path=str(checkpoint), commit_exists=False)
            entries[milestone] = report['intended'][str(milestone)] = entry
            try:
                document, reference = reader.document(checkpoint)
                commits[milestone] = document
                entry.update(commit_exists=True, commit=reference,
                    metadata=base['fields'](document, ('created_unix','optimizer_steps','adapter_state_sha256','base_sha256')),
                    commit_document_sha256=digest(canonical(document)))
            except FileNotFoundError:
                entry['missing_at_observation'] = True
            except (ValueError, OSError, KeyError, TypeError) as error:
                entry['read_error_type'] = type(error).__name__
        matches = {milestone: [] for milestone in entries}
        directory = arm_root/'stream/records'
        verified = False
        try:
            manifest, manifest_ref = reader.document(arm_root/'stream/JOURNAL.json')
            report['journal_manifest'] = manifest_ref
            base['regular_path'](directory)
            names = set(os.listdir(directory))
            indices = sorted(int(name[:-5]) for name in names if re.fullmatch(r'\d{20}\.json', name))
            previous = digest(canonical(manifest))
            report['snapshot_record_count'] = len(indices)
            report['verified_record_count'] = 0
            for expected, index in enumerate(indices):
                if index != expected:
                    raise ValueError('noncontiguous_journal')
                document, reference = reader.document(directory/f'{index:020d}.json')
                intent, intent_ref = reader.document(directory/f'{index:020d}.intent.json')
                payload = {key: value for key,value in document.items() if key != 'sha256'}
                if (document['index'] != index or document['previous_sha256'] != previous
                    or document['sha256'] != digest(canonical(payload))
                    or document['journal_id'] != manifest['journal_id'] or document['schema'] != manifest['schema']
                    or intent != dict(schema=document['schema'], journal_id=document['journal_id'], index=index,
                        previous_sha256=previous, record_sha256=document['sha256'])):
                    raise ValueError('chain_or_intent_binding')
                previous = document['sha256']
                report['verified_record_count'] += 1
                if document['kind'] != 'SLEEP_COMPLETE':
                    continue
                body = document['document']
                checkpoint = body.get('checkpoint', {})
                checkpoint_path = Path(checkpoint.get('adapter_path', '/unknown')).parent/'COMMIT.json'
                state = body.get('resume_state', {})
                saved = state.get('state', {})
                receipts = saved.get('sleep_receipts', [])
                matched = saved.get('matched', {})
                event = dict(index=index, record=reference, intent=intent_ref, chain_sha256=previous,
                    source_commit_path=str(checkpoint_path), cycle=body.get('cycle'),
                    status=body.get('status'), sleep_receipt_count=len(receipts),
                    checkpoint_document_sha256=digest(canonical(checkpoint)))
                report['sleep_complete_records'].append(event)
                for milestone, entry in entries.items():
                    if str(checkpoint_path) != entry['source_commit_path']:
                        continue
                    receipt = {key: value for key,value in body.items() if key != 'resume_state'}
                    valid = (body.get('status') == 'COMPLETE' and body.get('cycle') == milestone
                        and len(receipts) == milestone and bool(receipts) and receipts[-1] == receipt
                        and checkpoint == commits.get(milestone)
                        and state.get('sha256') == digest(canonical(saved))
                        and matched.get('arm') == arm and matched.get('cohort_sha256') == base['COHORT']
                        and body.get('checkpoint_sha256') == checkpoint.get('checkpoint_sha256'))
                    matches[milestone].append(dict(event, exact_checkpoint_binding=valid))
            report['listing_stable'] = names == set(os.listdir(directory))
            report['all_intents_paired'] = names == {name for index in indices
                for name in (f'{index:020d}.json', f'{index:020d}.intent.json')}
            report['last_chain_sha256'] = previous
            report['journal_observed_unix'] = time.time()
            verified = report['listing_stable'] and report['all_intents_paired']
            report['coverage'] = 'VERIFIED_STABLE_RETAINED_SNAPSHOT' if verified else 'INCOMPLETE_OR_MOVING_SNAPSHOT'
        except (ValueError, OSError, KeyError, TypeError) as error:
            report['coverage'] = 'INCOMPLETE'
            report['error_type'] = type(error).__name__
        for milestone, entry in entries.items():
            entry['boundary_matches'] = matches[milestone]
            entry['disposition'] = disposition(entry['commit_exists'], matches[milestone],
                verified and 'read_error_type' not in entry)
        report['source_owner_complete_history_attestation'] = 'REQUIRED_NOT_INFERRED'
    result.update(observed_unix=time.time(), scanned_bytes=reader.bytes, scanned_files=reader.files,
                  scan_limit_bytes=reader.limit, metadata_return_limit_bytes=base['RETURN_LIMIT'])
    if len(json.dumps(result).encode()) > base['RETURN_LIMIT']:
        raise ValueError('metadata_return_limit')
    return result
