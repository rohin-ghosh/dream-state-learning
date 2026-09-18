"""Read-only bounded Tool audit; identical old text is not a fresh delivery."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from recovery_proof import project as native_projection
from retirement import metadata, record, sha


def reference(value):
    return dict(index=value['index'], sha256=value['sha256'])


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def render_after_inbox(values, item, text, floor):
    inbox = None
    for value in values:
        if value['index'] <= floor:
            continue
        document = value['document']
        if value['kind'] == 'INBOX' and document['message']['id'] == item['inbox_id']:
            if document['source_sha256'] != item['inbox_sha256']:
                raise ValueError('exact_Tool_inbox_source_required')
            inbox = reference(value)
        if value['kind'] != 'REQUEST' or inbox is None or value['index'] <= inbox['index']:
            continue
        if document['started_unix'] < item['published_unix']:
            continue
        if any(message.get('role') == 'user' and message.get('content') == 'Tool: ' + text
                for message in document['messages']):
            if not document['render_receipt']['all_history_tokens_masked']:
                raise ValueError('Tool_tokens_must_remain_masked')
            return dict(INBOX=inbox, REQUEST=dict(**reference(value), started_unix=document['started_unix']),
                exact_text_after_bound_inbox=True, identical_text_unique_attribution_not_claimed=True)
    return dict(INBOX=inbox, REQUEST=None, bounded_search_only=True)


def authenticated_publication(path, arm, output):
    saved = json.loads(path.read_bytes())
    inbox_path = Path(saved['publication']['path'])
    result_path = Path(saved['result']['path'])
    if (not inbox_path.resolve().is_relative_to(arm / 'raw/stream/inbox')
            or not result_path.resolve().is_relative_to(arm / 'raw/stream/records')
            or sha(inbox_path) != saved['publication']['sha256']
            or sha(result_path) != saved['result']['sha256']):
        raise ValueError('same_life_bound_publication_and_result_required')
    inbox = json.loads(inbox_path.read_bytes())
    projection_path = Path(inbox['source_receipt']['path'])
    if (not projection_path.resolve().is_relative_to(output / 'projections')
            or sha(projection_path) != inbox['source_receipt']['sha256']):
        raise ValueError('unchanged_projection_required')
    projection = json.loads(projection_path.read_bytes())
    if (inbox['id'] != saved['publication']['id'] or inbox['actor'] != 'environment'
            or inbox['speaker'] != 'Tool' or inbox['split'] != 'TRAIN'
            or projection['text'] != inbox['text'] or projection['result'] != saved['result']):
        raise ValueError('authenticated_plain_Tool_only')
    act = record(result_path)
    origin = act['document']['origin']
    response = record(result_path.with_name(f"{origin['record_index']:020d}.json"))
    environment = act['document']['outcome']['environment']
    transport = environment['source_transport']
    if (act['kind'] != 'R184_ACT' or origin != saved['origin'] or environment['origin'] != origin
            or origin['kind'] != 'TRAIN_CHILD_RESPONSE' or response['kind'] != 'RESPONSE'
            or response['sha256'] != origin['record_sha256']
            or transport['journal_id'] != act['journal_id']
            or transport['authenticated_operator_transport'] is not True
            or transport['child_network_access'] is not False):
        raise ValueError('own_response_and_authenticated_transport_required')
    report = environment['report']
    error = report.get('error')
    feedback = report.get('feedback', [])
    item = dict(inbox_id=inbox['id'], inbox_sha256=sha(inbox_path), ACT=reference(act),
        RESPONSE=reference(response), publication_sha256=sha(path), projection_sha256=sha(projection_path),
        result_file_sha256=sha(result_path), receipt_sha256=environment['receipt_sha256'],
        judge_epoch_sha256=digest(environment.get('judge_epoch')),
        published_unix=saved['published_unix'], feedback_result_count=len(feedback),
        scored_result_count=sum(entry.get('result', {}).get('ok') is True
            and type(entry['result'].get('rank')) is int
            and type(entry['result'].get('accepted')) is bool for entry in feedback),
        no_judgment='No judgment:' in inbox['text'], rank_lines=inbox['text'].count('\nRank '),
        error=error if error in ('no_caption_found', 'scene_not_unambiguously_identified', None)
            else 'other_error_preserved_by_hash', error_sha256=digest(error), source_authenticated=True)
    return item, inbox['text']


def project(root):
    natives = native_projection(root)
    output = root / 'r228_feedback_relay_20260918T0908Z/output'
    cursor_path = output / 'CURSORS.json'
    cursors = json.loads(cursor_path.read_bytes())
    rows = []
    for native in natives['lives']:
        if 'caption_' not in native['life']:
            continue
        arm = root / native['life']
        treatment = native['life'].removeprefix('r213_r226_caption_').removesuffix('_fork')
        destination = output / treatment
        paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))[-512:]
        values = [record(path) for path in paths if metadata(path) in ('INBOX', 'REQUEST')]
        publications = sorted((destination / 'published').glob('*.json'),
            key=lambda path: path.stat().st_mtime)[-16:]
        candidates = []
        for path in publications:
            item, text = authenticated_publication(path, arm, destination)
            if item['ACT']['index'] <= native['LOADED']['index']:
                continue
            item['delivery'] = render_after_inbox(values, item, text, native['LOADED']['index'])
            candidates.append(item)
        rendered = [item for item in candidates if item['delivery']['REQUEST']]
        rows.append(dict(life=native['life'], gpu=native['gpu'], LOADED=native['LOADED'],
            examined_post_load_publications=len(candidates), relay_cursor=cursors[treatment],
            journal_index_at_cut=int(paths[-1].stem), latest=candidates[-1] if candidates else None,
            latest_chronological_render=rendered[-1] if rendered else None))
    return dict(observed_utc=datetime.now(timezone.utc).isoformat(), rows=rows,
        maximum_publications_per_life=16, maximum_recent_records_per_life=512,
        no_new_scoring_calls=True, audit_inbox_writes=0, native_signals=0,
        pending_not_proof_of_transport_failure=True,
        identical_text_unique_attribution_not_claimed=True,
        audit_source_sha256=sha(Path(__file__)) if Path(__file__).is_file() else None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(project(arguments.root), indent=2, sort_keys=True))
