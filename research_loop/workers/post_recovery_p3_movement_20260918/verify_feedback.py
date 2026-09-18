"""Read-only attribution for own TRAIN results; exports no caption/panel payloads."""

import hashlib
import json
from pathlib import Path


def file_json(path, expected=None):
    raw = Path(path).read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if expected is not None and checksum != expected:
        raise ValueError('immutable_file_hash_mismatch')
    return json.loads(raw), checksum


def projected_result(result, response):
    origin = result['origin']
    if origin['kind'] != 'TRAIN_CHILD_RESPONSE' or response['kind'] != 'RESPONSE':
        raise ValueError('own_TRAIN_RESPONSE_required')
    if origin['record_index'] != response['index'] or origin['record_sha256'] != response['sha256']:
        raise ValueError('exact_result_origin_required')
    if result['raw_act'] != response['document']['response']['raw']:
        raise ValueError('unaltered_raw_ACT_required')
    report = result['report']
    metrics = report['format_metrics']
    return dict(origin=origin, result_unix=result['unix'], ok=report['ok'], error=report.get('error'),
        format_metrics={key: metrics.get(key) for key in ('candidate_lines', 'recovered_count',
            'ambiguous_caption_lines', 'unparsed_line_count', 'format_fault', 'planned_count_required',
            'no_caption_act', 'caption_text_normalized', 'active_scene_fallback', 'format_policy')},
        feedback=[dict(ordinal=row['ordinal'], repeat=row.get('repeat'),
            result={key: row['result'].get(key) for key in ('rank', 'accepted', 'status',
                'rejection_reason', 'replayed', 'top_k', 'reference_count')}) for row in report['feedback']],
        original_raw_verified=True, judge_epoch_embedded_in_result=False)


def collect(root, journal_id, inboxes, acts, verified):
    root = Path(root)
    life = root / 'life'
    output = dict(feedback=[], tokens=[], judge_service=None, remote_writes=0, scoring_calls=0,
        reference_panel_reads=0, native_signals=[], publications=0)
    session = None
    for item in inboxes:
        incoming, inbox_sha = file_json(life / 'stream/inbox' / (item['id'] + '.json'), item['sha256'])
        projection, projection_sha = file_json(**dict(path=incoming['source_receipt']['path'],
            expected=incoming['source_receipt']['sha256']))
        if incoming['text'] != projection['text']:
            raise ValueError('exact_projected_Tool_text_required')
        result, result_sha = file_json(projection['result']['path'], projection['result']['sha256'])
        origin = result['origin']
        if acts.get(str(origin['record_index'])) != origin['record_sha256']:
            raise ValueError('only_selected_post_LOAD_ACTs')
        record, unused = verified(life / 'stream/records' / f'{origin["record_index"]:020d}.json', journal_id)
        row = projected_result(result, record)
        row.update(inbox_id=item['id'], inbox_sha256=inbox_sha, projection_sha256=projection_sha,
            result_sha256=result_sha)
        output['feedback'].append(row)
        selected_session = Path(projection['result']['path']).parents[2]
        if session is not None and session != selected_session:
            raise ValueError('unexpected_mixed_result_sessions')
        session = selected_session
    for index, expected in acts.items():
        record, unused = verified(life / 'stream/records' / f'{int(index):020d}.json', journal_id)
        if record['sha256'] != expected:
            raise ValueError('selected_ACT_hash_mismatch')
        response = record['document']['response']
        output['tokens'].append(dict(index=int(index), record_sha256=expected,
            finished_unix=record['document']['finished_unix'], generated_tokens=len(response['token_ids']),
            prompt_tokens=response['prompt_tokens'], truncated=response['truncated'],
            raw_text_sha256=hashlib.sha256(response['raw'].encode()).hexdigest(),
            characters=len(response['raw']), whitespace_words=len(response['raw'].split())))
    if session is not None:
        service = session.parent
        config, config_sha = file_json(service / 'CONFIG.private.json')
        prior, prior_sha = file_json(config['prior_config']['path'], config['prior_config']['sha256'])
        loaded, loaded_sha = file_json(service / 'LOADED.json')
        listening, listening_sha = file_json(session / 'LISTENING.json')
        if loaded['pid'] != listening['pid']:
            raise ValueError('same_scorer_loaded_listener_required')
        judge, judge_sha = file_json(prior['arguments']['judge_config'])
        output['judge_service'] = dict(config_sha256=config_sha, prior_config_sha256=prior_sha,
            loaded_sha256=loaded_sha, listening_sha256=listening_sha, pid=loaded['pid'],
            loaded_unix=loaded['unix'], judge_runtime_current_sha256=judge_sha,
            judge_runtime_schema=judge.get('schema'), same_loaded_listener=True,
            immutable_per_attempt_judge_epoch_proved=False,
            limitation='RESULT binds own ACT but has no immutable per-attempt judge epoch; current runtime hash is not proof of historical in-memory bytes.')
    return output
