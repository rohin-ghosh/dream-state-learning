"""Text-free real-host status: distinguish publication, inbox, rendering and ACT."""

from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import time

from parent_service import HERE, read, remote, save, sha, write


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def inspect(arm):
    directory = HERE / 'private' / arm
    state = read(directory / 'STATE.json')
    process = read(sorted(directory.glob('PROCESS_*.json'), key=lambda path: path.stat().st_mtime)[-1])
    observed = dict(arm=arm, native=remote(arm, dict(action='bind'), state['native'])['native'],
                    process_receipt=process, publications=[], native_signals=0,
                    sealed_scores_visible=False, semantic_row_exclusions=False)
    process_root = Path('/proc') / str(process['pid'])
    try:
        fields = (process_root / 'stat').read_text().rsplit(')', 1)[1].split()
        actual_argv = (process_root / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
        observed['parent_alive_bound'] = (fields[19] == process['start_ticks'] and
                                          fields[0] not in ('X', 'Z') and actual_argv == process['argv'])
        observed['parent_state'] = fields[0]
    except (FileNotFoundError, ProcessLookupError):
        observed['parent_alive_bound'] = False
    with Path(process['lock']).open('r') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            observed['publisher_lock_held'] = False
        except BlockingIOError:
            observed['publisher_lock_held'] = True
    observed['publisher_lock_open_by_parent'] = any(
        str(path.resolve()) == process['lock'] for path in (process_root / 'fd').glob('*'))
    for delivery in state['deliveries']:
        turn = Path(delivery['directory'])
        result = read(turn / 'RESULT.json')
        publication = delivery['receipt']['publication']
        proof_path = directory / ('DELIVERY_' + publication['id'] + '.json')
        sequence_path = directory / ('FOLLOWING_ACT_' + publication['id'] + '.json')
        sequence = read(sequence_path) if sequence_path.exists() else None
        if not proof_path.exists() and sequence is not None:
            proof_path = sequence_path
        observed['publications'].append(dict(id=publication['id'], source_sha256=publication['sha256'],
            queued_utc=utc(delivery['receipt']['delivered_unix']), inbox=delivery.get('inbox'),
            rendered_request=delivery.get('render'),
            act=delivery.get('act') or (sequence['act'] if sequence is not None else None),
            ACT_request_contains_parent_text=sequence['ACT_request_contains_parent_text'] if sequence is not None
                else True if delivery.get('act') else None,
            following_ACT_sequence_proof=str(sequence_path.relative_to(HERE)) if sequence is not None else None,
            publication_author_process={key: delivery['parent_process'][key] for key in
                                        ('pid', 'start_ticks', 'boot_id', 'started_utc')},
            publication_author_is_current_parent=(delivery['parent_process']['pid'] == process['pid'] and
                                                   delivery['parent_process']['start_ticks'] == process['start_ticks']),
            model=result['model'],
            provider_dispatch=read(turn / 'DISPATCH.json'), usage=result['usage'],
            result_sha256=sha(turn / 'RESULT.json'), provider_response_sha256=sha(turn / 'stdout.json'),
            provider_turn=str(turn.relative_to(HERE)),
            proof=str(proof_path.relative_to(HERE)) if proof_path.exists() else None,
            proof_sha256=sha(proof_path) if proof_path.exists() else None))
    observed['status'] = read(directory / 'STATUS.json')
    observed['status']['direct_ACT_prompt_receipts'] = observed['status'].pop('act_receipts', None)
    observed['status']['receipt_counter_scope'] = 'literal_parent_text_in_ACT_prompt_not_restoration_status'
    observed['counts'] = dict(queued=len(observed['publications']),
        inbox_registered=sum(bool(item['inbox']) for item in observed['publications']),
        rendered_REQUEST=sum(bool(item['rendered_request']) for item in observed['publications']),
        following_ACT=sum(bool(item['act']) for item in observed['publications']),
        ACT_prompt_exposed=sum(bool(item['act']) and item['ACT_request_contains_parent_text'] is True
                               for item in observed['publications']))
    return observed


def public_summary(arm, observed_utc):
    first = arm['publications'][0]
    latest = arm['publications'][-1]
    current = arm['process_receipt']
    return dict(schema='PAIR_PUBLIC_FIRST_REQUEST_TO_FOLLOWING_ACT_V1', arm=arm['arm'],
        observed_utc=observed_utc,
        restoration_status='RESTORED_FOLLOWING_ACT_PROVEN' if first['act'] and arm['parent_alive_bound']
            and arm['publisher_lock_held'] else 'INSPECT_CURRENT_STATUS',
        current_live_parent={key: current[key] for key in ('pid', 'start_ticks', 'boot_id', 'started_utc', 'argv', 'lock')},
        current_parent_alive=arm['parent_alive_bound'], current_parent_lock_held=arm['publisher_lock_held'],
        current_parent_health=arm.get('status', {}).get('health'),
        publication_author_process=first['publication_author_process'],
        publication_author_is_current_parent=first['publication_author_is_current_parent'],
        native_identity=arm['native'], publication_id=first['id'], queued_utc=first['queued_utc'],
        inbox=first['inbox'], exact_rendered_REQUEST=first['rendered_request'], following_ACT=first['act'],
        following_ACT_proven=bool(first['act']), ACT_prompt_exposure=first['ACT_request_contains_parent_text'],
        exposure_false_does_not_mean_not_restored=True, current_counts=arm['counts'],
        provider_model=first['model'], provider_response_sha256=first['provider_response_sha256'],
        latest_model_publication={key: latest.get(key) for key in
            ('id', 'queued_utc', 'model', 'publication_author_process', 'publication_author_is_current_parent',
             'inbox', 'rendered_request', 'act', 'ACT_request_contains_parent_text',
             'provider_response_sha256', 'provider_turn')},
        proof=first['proof'], proof_sha256=first['proof_sha256'],
        retention_claim=False, causal_improvement_claim=False, sealed_scores_visible=False,
        native_signals=0, native_restarts=0, semantic_row_exclusions=False)


def main():
    observed = dict(schema='POST_REBOOT_PAIR_PARENTS_OPERATIONAL_RECOVERY_V1',
                    observed_utc=utc(time.time()), non_material_repair=True,
                    native_signals=0, native_restarts=0, weight_changes=0, lease_changes=0,
                    old_archives_mutated=False, arms=[inspect(arm) for arm in ('learner', 'frozen')])
    observed['both_first_deliveries_proven'] = all(
        arm['publications'] and arm['publications'][0]['proof'] and arm['parent_alive_bound'] and
        arm['publisher_lock_held'] and arm['publisher_lock_open_by_parent'] for arm in observed['arms'])
    save(HERE / 'STATUS.json', observed)
    public = HERE / 'public'
    public.mkdir(exist_ok=True)
    summaries = [public_summary(arm, observed['observed_utc']) for arm in observed['arms']]
    for summary in summaries:
        save(public / (summary['arm'] + '_REQUEST_TO_ACT.json'), summary)
    save(HERE / 'SUMMARY.json', dict(observed_utc=observed['observed_utc'], arms=summaries,
         both_restored=all(item['restoration_status'] == 'RESTORED_FOLLOWING_ACT_PROVEN' for item in summaries),
         distinction='following_ACT_completion_and_ACT_prompt_exposure_are_separate'))
    if observed['both_first_deliveries_proven'] and not (HERE / 'FIRST_PAIR_DELIVERY.json').exists():
        write(HERE / 'FIRST_PAIR_DELIVERY.json', observed)
    for arm in observed['arms']:
        print(json.dumps(dict(arm=arm['arm'], parent_pid=arm['process_receipt']['pid'],
                              alive=arm['parent_alive_bound'], lock=arm['publisher_lock_held'],
                              counts=arm['counts'])))


if __name__ == '__main__':
    main()
