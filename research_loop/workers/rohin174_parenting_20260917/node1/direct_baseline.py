"""Single no-duplicate Main-authorized console baseline, never provider output."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from fallback_drafts_v1 import DRAFTS
from first_baseline import exclusive_parent
from inventory_node1 import HERE, Reader, digest, require
from observe_publications import publications
from parent_custody import write
from parent_runner import load


def require_unpublished_results(results):
    for result in results:
        require(result.get('status') in ('MISSING', 'SILENT'), 'no_successful_publication')
        require(not any(key in result for key in ('inbox_publication', 'sent_unix', 'publication')),
                'no_uncertain_publication')


def certify_unpublished(spec_path, root):
    require(not any(entry['root'] == root for entry in publications()), 'baseline_already_published_no_duplicate')
    receipts = []
    results = []
    for attempt in sorted((spec_path.parent / 'parent').glob('parent_*')):
        require(attempt.is_dir(), 'regular_parent_attempt')
        require(not any((attempt / name).exists() for name in
                        ('ARM_PUBLISHED.json', 'PUBLISH_INTENT.json', 'PUBLICATION.json')),
                'no_parent_publication_or_intent')
        result_path = attempt / 'RESULT.json'
        require(result_path.exists(), 'no_inflight_parent_attempt')
        raw = Reader().raw(result_path)
        results.append(json.loads(raw))
        receipts.append(dict(path=str(result_path), sha256=digest(raw)))
    require_unpublished_results(results)
    return receipts


def bind_draft(physical, receipt, source, draft):
    require(physical in range(3, 8) and receipt['physical'] == physical, 'only_five_unpublished_learning_lives')
    require(digest(json.dumps(source, indent=2, sort_keys=True).encode()) == receipt['source_sha256'],
            'exact_archived_source_serialization')
    events = [event for event in source['events'] if event['actor'] == 'child'
              and event['record_index'] == draft['record_index']]
    require(len(events) == 1 and draft['anchor'] in events[0]['text'], 'actual_child_object_anchor')
    event = events[0]
    commits = [entry for entry in receipt['verification']['verified_child_commits']
               if entry['record_index'] == event['record_index'] and entry['record_sha256'] == event['record_sha256']
               and entry['text_sha256'] == digest(event['text'].encode())]
    require(len(commits) == 1, 'verified_child_commit_required')
    message = draft['message']
    require(type(message) is str and message.isascii() and len(message.split()) <= 90
            and len(message.encode()) <= 4096, 'bounded_English_own_prose_B0')
    return commits[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=range(3, 8), required=True)
    parser.add_argument('--execute', action='store_true')
    arguments = parser.parse_args()
    draft = DRAFTS[arguments.physical]
    prepared = HERE / draft['source']
    receipt = json.loads(Reader().raw(prepared / 'RECEIPT.json'))
    source_raw = Reader().raw(prepared / 'SOURCE.json')
    require(digest(source_raw) == receipt['source_sha256'], 'archived_current_TRAIN_source_pin')
    source = json.loads(source_raw)
    grounding = bind_draft(arguments.physical, receipt, source, draft)
    spec_path = Path(receipt['active_spec'])
    require(digest(spec_path.read_bytes()) == receipt['active_spec_sha256'], 'actual_parent_spec_pin')
    spec = json.loads(spec_path.read_text())
    activation = json.loads((spec_path.parent / 'PARENT_ACTIVATED.json').read_text())
    parent, config, unused_provider, selected = load(spec)
    require(receipt['label'] == activation['label'] and receipt['arm'] == spec['arm'], 'actual_main_assignment')
    require(len(draft['message'].split()) <= selected['words'], 'unchanged_arm_cap')
    directory = HERE / ('FIRST_BASELINE_' + str(time.time_ns()) + '_lane' + str(arguments.physical))
    directory.mkdir(mode=0o700)
    write(directory / 'DRAFT.json', dict(draft, grounding=grounding, source_receipt_sha256=digest((prepared / 'RECEIPT.json').read_bytes()),
          origin='DIRECT_MAIN_AUTHORIZED_ASTRA_B0_NOT_PROVIDER_OUTPUT', active_spec=str(spec_path)))
    with (directory / 'SOURCE.json').open('xb') as stream:
        stream.write(source_raw)
    write(directory / 'OWN_CPU_PROVENANCE_GO.json', dict(status='PASS', physical=arguments.physical,
          observed_unix=time.time(), source_sha256=digest(source_raw), grounding=grounding,
          operator_sha256=digest(Path(__file__).read_bytes()), drafts_sha256=digest((HERE / 'fallback_drafts_v1.py').read_bytes()),
          no_child_actions=True, no_provider_calls=True, actual_selected_word_cap=selected['words'],
          actual_message_words=len(draft['message'].split()), actual_message_bytes=len(draft['message'].encode()),
          tests=['exact_source_pin', 'actual_child_quote', 'committed_child_provenance', 'own_English_prose', 'B0_and_arm_caps']))
    if not arguments.execute:
        print(json.dumps(dict(status='PREPARED_NO_SIGNALS', directory=str(directory))), flush=True)
        return
    lock_path = HERE / ('DIRECT_BASELINE_LANE' + str(arguments.physical) + '.lock')
    lock = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        once_path = HERE / ('DIRECT_BASELINE_LANE' + str(arguments.physical) + '_ONCE.json')
        require(not once_path.exists(), 'one_direct_baseline_per_life_no_ambiguous_retry')
        with exclusive_parent(activation, spec_path, directory):
            prior = certify_unpublished(spec_path, spec['root'])
            require(time.time() < config['hard_end_unix'], 'unchanged_original_wall')
            require(digest((prepared / 'SOURCE.json').read_bytes()) == receipt['source_sha256'], 'source_pin_before_publication')
            write(directory / 'NO_PRIOR_PUBLICATION.json', dict(root=spec['root'], active_parent=activation['actor'],
                  previous_result_receipts=prior, no_active_or_uncertain_publications=True,
                  legacy_pending_inboxes_preserved=spec['preserved_pending_publications'], observed_unix=time.time()))
            write(once_path, dict(directory=str(directory), root=spec['root'], observed_unix=time.time(),
                  authorized_by='Main 2026-09-17 source-grounded exclusive-custody unpublished-baseline fallback'))
            message = draft['message']
            origin = 'DIRECT_MAIN_AUTHORIZED_ASTRA_B0_NOT_PROVIDER_OUTPUT'
            write(directory / 'PUBLISH_INTENT.json', dict(root=spec['root'], origin=origin, speaker='Astra',
                  message=message, message_sha256=digest(message.encode()), grounding=grounding,
                  observed_unix=time.time(), source_sha256=digest(source_raw)))
            started = time.time()
            try:
                publication = parent['publish'](Path(spec['repository']), config, message)
            except Exception as error:
                write(directory / 'UNKNOWN_PUBLICATION_NO_RETRY.json', dict(error_type=type(error).__name__,
                      observed_unix=time.time(), root=spec['root'], source_sha256=digest(source_raw)))
                raise
            document = dict(status='PUBLISHED_NOT_RENDERED', root=spec['root'], origin=origin, direct_B0=True,
                arm=spec['arm'], publication=publication, message_sha256=digest(message.encode()),
                word_count=len(message.split()), byte_count=len(message.encode()), grounding=grounding,
                source_sha256=digest(source_raw), source_path=str(directory / 'SOURCE.json'),
                source_record_count=source['record_count'], source_head_sha256=source['head_sha256'],
                publication_started_unix=started, observed_unix=time.time(), active_spec=str(spec_path),
                active_parent=activation['actor'], policy_sha256=spec['policy_sha256'],
                assignment_sha256=spec['assignment_sha256'], request_exposure_verified=False,
                child_signals=0, provider_calls=0, previous_response_cursor_preserved=True)
            write(directory / 'PUBLICATION.json', document)
            print(json.dumps(dict(status=document['status'], label=activation['label'], directory=str(directory),
                                  publication=publication, origin=origin)), flush=True)
    finally:
        os.close(lock)


if __name__ == '__main__':
    main()
