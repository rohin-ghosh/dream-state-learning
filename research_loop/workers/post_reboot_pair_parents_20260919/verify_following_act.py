"""Prove following-ACT chronology without falsely claiming text survived compaction."""

import json
from pathlib import Path

from parent_service import HERE, read, ref, remote, rendered, require, sha, write


def verify(records, delivery, native):
    first_render = None
    request = response = committed = stage = None
    for record in records:
        kind, document = record['kind'], record.get('document', {})
        if kind == 'REQUEST':
            request, response, committed, stage = record, None, None, None
            if first_render is None and rendered(document, delivery):
                require(record['index'] > delivery['inbox']['index'], 'render_after_inbox')
                first_render = dict(ref(record), started_unix=document['started_unix'])
        elif kind == 'RESPONSE':
            response = record
        elif kind == 'COMMITTED':
            committed = record
        elif kind == 'R184_STAGE' and document.get('stage') == 'ACT' and first_render:
            require(all((request, response, committed)), 'following_ACT_complete_sources')
            require(response['document']['request_sha256'] == request['document']['pending_sha256'],
                    'following_ACT_response_request_binding')
            require(committed['document']['source_sha256'] == document['source_sha256'] and
                    committed['document']['segment'] == document['segment'] == request['document']['segment'],
                    'following_ACT_commit_stage_binding')
            require(request['index'] >= first_render['index'], 'following_ACT_after_render')
            stage = record
        elif kind == 'R184_ACT' and stage:
            require(document['origin']['record_index'] == response['index'] and
                    document['origin']['record_sha256'] == response['sha256'] and
                    document['source_sha256'] == stage['document']['source_sha256'], 'following_ACT_origin_binding')
            publication = delivery['receipt']['publication']
            history_bound = any(item.get('event_id') == 'parent:inbox:' + publication['id'] and
                                item.get('source_sha256') == publication['sha256']
                                for item in request['document']['parent_provenance'])
            return dict(publication=publication, inbox=delivery['inbox'], first_render=first_render,
                        act=dict(request=ref(request), response=ref(response), committed=ref(committed),
                                 stage=ref(stage), event=ref(record),
                                 started_unix=request['document']['started_unix'],
                                 finished_unix=response['document']['finished_unix']),
                        initial_request_exact_text_and_source_bound=True,
                        ACT_request_contains_parent_text=rendered(request['document'], delivery),
                        ACT_history_contains_parent_source=history_bound,
                        scope='INBOX_then_exact_rendered_REQUEST_then_following_committed_ACT',
                        retention_claim=False, causal_improvement_claim=False,
                        native=native, parent_process=delivery['parent_process'],
                        provider_response_sha256=delivery['receipt']['provider_response_sha256'],
                        native_signals=0, native_restarts=0, semantic_row_exclusions=False, sealed_scores_visible=False)
    raise ValueError('following_ACT_not_yet_observed')


def main():
    for arm in ('learner', 'frozen'):
        directory = HERE / 'private' / arm
        state = read(directory / 'STATE.json')
        delivery = state['deliveries'][0]
        identifier = delivery['receipt']['publication']['id']
        proof_path = directory / ('FOLLOWING_ACT_' + identifier + '.json')
        if proof_path.exists():
            proof = read(proof_path)
        else:
            observed = remote(arm, dict(action='poll', next_index=delivery['inbox']['index'] + 1,
                              previous_sha256=delivery['inbox']['sha256']), state['native'])
            proof = verify(observed['records'], delivery, state['native'])
            require(sha(Path(delivery['directory']) / 'stdout.json') == proof['provider_response_sha256'],
                    'actual_provider_response_bytes_preserved')
            source = directory / ('CHAIN_SOURCE_' + identifier + '.json')
            write(source, observed)
            proof['canonical_source_receipt'] = str(source.relative_to(HERE))
            proof['canonical_source_receipt_sha256'] = sha(source)
            write(proof_path, proof)
        print(json.dumps(dict(arm=arm, inbox=proof['inbox']['index'],
                              first_request=proof['first_render']['index'], act=proof['act'],
                              ACT_request_contains_parent_text=proof['ACT_request_contains_parent_text'])))


if __name__ == '__main__':
    main()
