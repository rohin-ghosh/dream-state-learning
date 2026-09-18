"""Read-only receipt projection, not a semantic classifier or publisher to lives."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

OWN = Path(__file__).resolve().parent
FLEET = OWN.parent / 'rohin174_parenting_20260917/node4/R195_FLEET'
POLICY = 'R233_P7_CONVERGENCE_GUIDANCE_V1'


def read(path):
    return json.loads(path.read_text())


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def ref(path):
    return dict(path=str(path.relative_to(OWN.parent.parent.parent)), sha256=file_sha(path))


def unique_origins(rows):
    selected = {}
    for row in rows:
        origin = row['origin']
        key = (origin['journal_id'], origin['response_sha256'], origin['stage'])
        selected.setdefault(key, row)
    return sorted(selected.values(), key=lambda row: row['origin']['response_index'])


def direction_metrics(route):
    forwards = unique_origins(route['forwarded_P7_outputs'])
    returns = unique_origins(route['returned_actual_child_outputs'])
    verified = [row for row in returns if row.get('P7_REQUEST_render')
        and any(render.get('exact_parent_text_rendered') and render.get('all_history_tokens_masked')
            for render in row.get('child_REQUEST_parent_renders', []))
        and row.get('interpretation') == 'ACTUAL_REPLY_TO_RENDERED_P7_INPUT']
    rendered_publications = {render['publication']['id'] for row in returns
        for render in row.get('child_REQUEST_parent_renders', [])
        if render.get('exact_parent_text_rendered') and render.get('all_history_tokens_masked')}
    return dict(observed_utc=route['observed_utc'], forwarded_distinct_P7_ACT_outputs=len(forwards),
        forwarded_stages=dict(Counter(row['origin']['stage'] for row in forwards)),
        P7_publications_rendered_in_bound_child_requests=len(rendered_publications),
        returned_distinct_child_stage_outputs=len(returns),
        returned_stages=dict(Counter(row['origin']['stage'] for row in returns)),
        returned_parent_conditioned_stages_rendered_back_in_P7=len(verified),
        not_independent_conversation_count=True,
        latest_forward_origin=forwards[-1]['origin'] if forwards else None,
        latest_return_origin=returns[-1]['origin'] if returns else None,
        latest_verified_return=({key: verified[-1][key] for key in
            ('origin', 'P7_REQUEST_render', 'child_REQUEST_parent_renders')}
            if verified else None),
        forward_stage_limit=route['forward_stage_limit'], semantic_success_claim=False,
        optimizer_update_claim=False)


def retirement(receipt, physical, boundary=None):
    if receipt is None:
        return dict(physical=physical, status='FINAL_PRESERVATION_RECEIPT_PENDING',
            fresh_complete_record=boundary.get('complete_index') if boundary else None,
            complete_sha256=boundary.get('saved', {}).get('record_sha256') if boundary else None)
    native = receipt['native']
    result = {key: receipt[key] for key in ('status', 'physical', 'journal_id', 'saved',
        'head', 'suffix', 'signal', 'signaled_unix', 'retirement_verified_unix',
        'snapshot_files', 'stream_manifest_sha256', 'coherent_adapter_optimizer_RNG_history_inboxes',
        'namespace_deleted', 'SIGSTOP_used', 'PAUSED_marker', 'other_lives_signaled',
        'readout_interrupted_without_success_claim')}
    result['saved'] = {key: value for key, value in result['saved'].items()
        if key not in ('checkpoint_path', 'record_path')}
    result.update(life_alias='MATH_C' if physical == 6 else f'SCALE_physical{physical}',
        complete_record_index=int(Path(receipt['saved']['record_path']).stem),
        native_identity=dict(pid=native['pid'], start_ticks=native['start_ticks'],
            historical_identity=receipt['signal'] is None, current_alive=False),
        verified_utc=utc(receipt['retirement_verified_unix']),
        signaled_utc=utc(receipt['signaled_unix']) if receipt['signaled_unix'] else None)
    return result


def overseer_status():
    folder = FLEET / 'r229_parent7'
    poll_path = max(folder.glob('POLL_*.json'))
    poll = read(poll_path)
    adjustment = poll.get('actual_birth_and_route', {}).get('standing_overseer_curriculum', {}).get('R233_convergence_adjustment')
    expected = read(OWN / 'overseer_adjustment.json')
    result = dict(policy=POLICY, latest_poll=ref(poll_path),
        exact_adjustment_in_poll=adjustment == expected,
        status='POLL_OBSERVED_AWAITING_ACTUAL_TURN_SOURCE' if adjustment == expected else 'POLL_NOT_YET_OBSERVED',
        native_policy_changed=False, new_publisher_started=False,
        parent_restarted=False, P3_changes=False)
    for source_path in sorted(folder.glob('turn_*/SOURCE.json')):
        source = read(source_path)
        loaded = source.get('actual_birth_and_route', {}).get('standing_overseer_curriculum', {}).get('R233_convergence_adjustment')
        if loaded != expected:
            continue
        result.update(status='ACTUAL_PARENT_MODEL_INPUT_OBSERVED', source=ref(source_path),
            conditioned_on_P7_record={key: value for key, value in source['reply'].items() if key != 'text'})
        publication_path = source_path.parent / 'NEXT.json'
        if not publication_path.exists():
            break
        publication = read(publication_path)
        result.update(status='PUBLISHED_AWAITING_RENDER', publication_receipt=ref(publication_path),
            publication={key: publication['publication'][key] for key in ('id', 'sha256')},
            published_utc=utc(publication['published_unix']), sequence=publication['sequence'],
            text_sha256=hashlib.sha256(publication['message'].encode()).hexdigest())
        matching = [row for row in poll.get('render_receipts', [])
            if row['publication']['sha256'] == publication['publication']['sha256']
            and row.get('exact_text_in_messages') and row.get('all_history_tokens_masked')]
        if matching:
            render = matching[-1]
            result.update(status='ACTUAL_MASKED_REQUEST_RENDER_OBSERVED',
                rendered_request=render['delivery'], message_indices=render['message_indices'],
                request_utc=utc(render['request_mtime_unix']))
        break
    return result


def without_private_paths(value):
    if isinstance(value, dict):
        return {key: without_private_paths(item) for key, item in value.items()
            if key not in ('path', 'request_path') or not isinstance(item, str) or not item.startswith('/')}
    if isinstance(value, list):
        return [without_private_paths(item) for item in value]
    return value


def main():
    remote_path = OWN / 'private/REMOTE_STATUS.json'
    remote = read(remote_path)
    route_path = FLEET / 'r230_route_status/CURRENT.json'
    route = read(route_path)
    result = dict(schema='R233_NODE4_RECEIPT_STATUS_V1',
        generated_utc=datetime.now(timezone.utc).isoformat(),
        remote_observed_utc=utc(remote['observed_unix']),
        selected_lives=[retirement(remote['retirements'].get(str(physical)), physical,
            remote['boundaries'].get(str(physical))) for physical in (0, 1, 2, 5, 6)],
        protected_process_observations=remote['protected'],
        GPU0_GPU1='GPU0 remains Main-owned; consult actual process observations, not historical scorer identity. GPU1 vision is protected. Neither service was signaled here.',
        MATH_C_classroom='No proven cheap cross-node THINK route; explicit authorized retirement fallback.',
        P7_overseer=overseer_status(), P7_Astra7=direction_metrics(route),
        route_source=ref(route_path), P3_owner='Main; no P3 signals or source changes here.',
        bounded_guidance_review=ref(OWN / 'GUIDANCE_REVIEW.md'),
        recurring_semantic_maintenance=False)
    output = OWN / 'STATUS.json'
    temporary = output.with_suffix('.next')
    temporary.write_text(json.dumps(without_private_paths(result), sort_keys=True, indent=2) + '\n')
    temporary.replace(output)
    print(json.dumps(dict(status=str(output), sha256=file_sha(output),
        retirements=[dict(physical=row['physical'], status=row['status']) for row in result['selected_lives']],
        P7_overseer=result['P7_overseer']['status'])))


if __name__ == '__main__':
    main()
