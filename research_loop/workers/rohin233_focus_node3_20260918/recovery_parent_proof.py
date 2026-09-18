"""Actual post-recovery parent/provider delivery, separate from historical turns."""

import argparse
import hashlib
import json
from pathlib import Path

from adaptive_parent import message
from classroom import load_helpers
from recovery import utc
from recovery_proof import project as native_projection
from retirement import identity, PROTECTED, public_identity, record, sha


def act_after_parent(helper, root, name, publication, delivery):
    if not delivery.get('REQUEST'):
        return None
    expected = 'Astra: ' + publication['text']
    requests, responses = {}, {}
    for path, kind in helper.records(root, name, delivery['REQUEST']['index'] - 1):
        if kind not in ('REQUEST', 'RESPONSE', 'R184_ACT'):
            continue
        value = record(path)
        document = value['document']
        reference = dict(index=value['index'], sha256=value['sha256'])
        if kind == 'REQUEST' and any(item.get('role') == 'user' and item.get('content') == expected
                for item in document['messages']):
            if not document['render_receipt']['all_history_tokens_masked']:
                raise ValueError('external_parent_tokens_must_stay_masked')
            digest = hashlib.sha256(json.dumps({key: content for key, content in document.items()
                if key != 'resume_state'}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            requests[digest] = reference
        elif kind == 'RESPONSE' and document['request_sha256'] in requests:
            responses[value['index']] = dict(RESPONSE=reference, ACT_REQUEST=requests[document['request_sha256']])
        elif kind == 'R184_ACT' and document['origin']['record_index'] in responses:
            response = responses[document['origin']['record_index']]
            if (document['origin']['kind'] != 'TRAIN_CHILD_RESPONSE'
                    or document['origin']['record_sha256'] != response['RESPONSE']['sha256']):
                raise ValueError('actual_own_ACT_origin_required')
            return dict(ACT=reference, **response, parent_present_and_masked_in_ACT_request=True,
                correctness_or_training_success_not_inferred=True)
    return None


def process(receipt):
    if not receipt.exists():
        return None
    expected = json.loads(receipt.read_bytes())['process']
    try:
        actual = identity(expected['pid'])
        match = all(actual[key] == expected[key] for key in ('pid', 'start_ticks', 'command_sha256'))
        return dict(**public_identity(actual), same_identity_alive=match and actual['state'] not in ('Z', 'X'))
    except (FileNotFoundError, ProcessLookupError):
        return dict(pid=expected['pid'], same_identity_alive=False)


def latest_completed_model_parent(deliveries):
    return next((item for item in reversed(deliveries)
        if item['parent_kind'] == 'ACTUAL_MODEL_PROVIDER'
        and item['delivery'].get('REQUEST') and item.get('actual_ACT_after_parent')), None)


def project(root):
    natives = native_projection(root)
    config = json.loads((root / 'r233_classroom_operator_v2/CONFIG_PRIVATE.json').read_bytes())
    helper, bound = load_helpers(root, config, recovering=True)
    helper.MEMBERS = tuple(PROTECTED)
    rows = []
    for native in natives['lives']:
        name = native['life']
        output = root / ('r233_all_five_caption_epochs_v1' if 'unparented' in name
            else 'r233_classroom_handoff_v1/live')
        deliveries = []
        for directory in sorted((output / name).glob('turn_*')):
            publication_path = directory / 'PUBLISHED.json'
            if not publication_path.exists() or native['LOADED'] is None:
                continue
            prepared_path = directory / 'PREPARED.json'
            prepared = json.loads(prepared_path.read_bytes())
            if prepared['floor'] < native['LOADED']['index']:
                continue
            publication = json.loads(publication_path.read_bytes())
            if (publication['prepared_sha256'] != sha(prepared_path)
                    or sha(Path(publication['path'])) != publication['sha256']):
                raise ValueError('unchanged_source_bound_parent_required')
            delivery = helper.actual_delivery(root, name, publication, prepared['floor'])
            item = dict(parent_id=publication['id'], parent_sha256=publication['sha256'],
                published_utc=publication['published_utc'], delivery=delivery,
                parent_kind='SCRIPTED_NOT_MODEL_PROVIDER')
            result_path = directory / 'PROVIDER_RESULT.json'
            if result_path.exists():
                result = json.loads(result_path.read_bytes())
                if message(result, sha(directory / 'PROVIDER_REQUEST.json')) != publication['text']:
                    raise ValueError('exact_actual_provider_text_must_be_published')
                item.update(parent_kind='ACTUAL_MODEL_PROVIDER',
                    provider_model=result['model'], provider_response_sha256=result['provider_response_sha256'],
                    provider_dispatch_sha256=result['provider_dispatch_sha256'])
                item['actual_ACT_after_parent'] = act_after_parent(helper, root, name, publication, delivery)
            deliveries.append(item)
        rendered = [item for item in deliveries if item['delivery']['REQUEST']]
        model_rendered = [item for item in rendered if item['parent_kind'] == 'ACTUAL_MODEL_PROVIDER']
        rows.append(dict(life=name, gpu=native['gpu'], native_status=native['status'],
            new_parent_publications=len(deliveries), first_new_render=rendered[0] if rendered else None,
            latest_parent=deliveries[-1] if deliveries else None,
            latest_completed_model_parent=latest_completed_model_parent(deliveries),
            first_new_model_render=model_rendered[0] if model_rendered else None))
    output = root / 'r233_recovery_services_v4'
    heartbeat_path = root / 'r233_classroom_handoff_v1/live/HEARTBEAT.json'
    heartbeat = json.loads(heartbeat_path.read_bytes())
    return dict(observed_utc=utc(), rows=rows, new_parent_render_count=sum(bool(row['first_new_render']) for row in rows),
        new_model_parent_render_count=sum(bool(row['first_new_model_render']) for row in rows),
        new_model_parent_ACT_count=sum(bool(row['latest_completed_model_parent']) for row in rows),
        services={name:process(output / (name + '.json')) for name in ('classroom','caption_gpu7','math_debate')},
        feedback_service=process(root / 'r233_recovery_services_v3/feedback.json'),
        classroom_service_end_unix=heartbeat.get('service_end_unix'), heartbeat_utc=heartbeat['observed_utc'],
        native_signals=0, new_shared_conclusion_not_established=True,
        historical_turns_not_counted_as_recovery=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    options = parser.parse_args()
    print(json.dumps(project(options.root), indent=2, sort_keys=True))
