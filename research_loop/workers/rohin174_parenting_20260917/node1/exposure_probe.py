"""Bounded metadata-only TRAIN suffix proof; no inbox, checkpoint or sealed file reads."""

from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import re
import stat
import time
from types import SimpleNamespace

from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
from gpu.orch_r125_stream_journal import StreamJournal, _digest, require
from gpu.orch_r127_pilot_console import _bytes
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_plain_context import event_message


LABELS = ('teach_replay', 'teach_perception', 'teach_parenting', 'classroom_brain',
          'classroom_creative', 'classroom_support')
ROOTS = {'/localhome/local-rohing/orch_r136_a100_' + label + '_20260916_attempt1/run1'
         for label in LABELS}


def request_exposes(document, event):
    checkpoint = document['resume_state']['state']
    history = checkpoint['history']
    frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
    if event.actor != 'parent' or event.split != 'TRAIN' or asdict(event) not in history['events'][frontier:]:
        return False
    rendered = event_message(event) if checkpoint.get('presentation') else TrainHistory._message(event)
    return rendered is not None and rendered in document['messages']


def validate_entry(entry):
    root = Path(entry['root'])
    require(str(root) in ROOTS, 'six_owned_learning_TRAIN_roots_only')
    publication = entry['publication']
    require(re.fullmatch('[0-9a-f]{32}', publication['id']) is not None
            and publication['path'] == str(root / 'stream/inbox' / (publication['id'] + '.json'))
            and re.fullmatch('[0-9a-f]{64}', publication['sha256']) is not None, 'exact_publication_binding')
    require(type(entry['source_record_count']) is int and entry['source_record_count'] > 0
            and re.fullmatch('[0-9a-f]{64}', entry['source_head_sha256']) is not None,
            'actual_parent_source_prefix_required')


def probe(entry, cursor=None):
    validate_entry(entry)
    root = Path(entry['root'])
    publication = entry['publication']
    state = dict(cursor) if cursor else dict(next_index=entry['source_record_count'],
        head_sha256=entry['source_head_sha256'], registration=None, exposure=None,
        completed_sleeps=[], boundaries=[], following_requests=[])
    require(state['next_index'] >= entry['source_record_count'], 'cursor_never_rewinds_source')
    remaining = 128 * 1024 * 1024
    used = 0
    with _open_stream_directory(root, 'records') as (records, unused):
        def read(index):
            nonlocal remaining, used
            try:
                metadata = os.stat(f'{index:020d}.json', dir_fd=records, follow_symlinks=False)
            except FileNotFoundError:
                return None, None
            require(stat.S_ISREG(metadata.st_mode) and metadata.st_size <= 16 * 1024 * 1024,
                    'bounded_regular_TRAIN_record')
            require(metadata.st_size + 1 <= remaining, 'aggregate_read_before_charge')
            remaining -= metadata.st_size + 1
            used += metadata.st_size + 1
            record = _read_record(records, index)
            require(record is not None, 'stable_published_record')
            reference = dict(record_index=index, record_sha256=record['sha256'],
                             filesystem_mtime_ns=metadata.st_mtime_ns, bytes=metadata.st_size)
            return record, reference

        boundary, unused = read(state['next_index'] - 1)
        require(boundary is not None and boundary['sha256'] == state['head_sha256'], 'source_or_cursor_boundary_pin')
        journal_id = boundary['journal_id']
        event = None
        if state['registration']:
            registered, unused = read(state['registration']['record_index'])
            require(registered['sha256'] == state['registration']['record_sha256'], 'prior_registration_pin')
            document = registered['document']
            event = StreamJournal._inbox_event(SimpleNamespace(inbox=root / 'stream/inbox'),
                document['message'], document['source_id'], document['source_sha256'])
        pending_tail = False
        for unused in range(128):
            record, reference = read(state['next_index'])
            if record is None:
                pending_tail = True
                break
            require(record['previous_sha256'] == state['head_sha256'] and record['journal_id'] == journal_id,
                    'actual_TRAIN_suffix_chain')
            document = record['document']
            if record['kind'] == 'INBOX' and document['message']['id'] == publication['id']:
                message = document['message']
                require(document['source_id'] == publication['path']
                        and document['source_sha256'] == publication['sha256']
                        and hashlib.sha256(_bytes(message)).hexdigest() == publication['sha256']
                        and message['actor'] == 'parent' and message['speaker'] == 'Astra',
                        'exact_published_message_registration')
                event = StreamJournal._inbox_event(SimpleNamespace(inbox=root / 'stream/inbox'),
                                                   message, document['source_id'], document['source_sha256'])
                state['registration'] = reference
            elif record['kind'] == 'REQUEST':
                envelope = document['resume_state']
                require(document['split'] == 'TRAIN' and envelope['sha256'] == _digest(envelope['state'])
                        and document['render_receipt']['all_history_tokens_masked'] is True,
                        'actual_masked_TRAIN_request_envelope')
                if event is not None and state['exposure'] is None and request_exposes(document, event):
                    state['exposure'] = dict(reference, history_sha256=_digest(envelope['state']['history']),
                                             exact_visible_history_and_rendered_message=True)
                if state['completed_sleeps']:
                    complete = state['completed_sleeps'][-1]
                    if not any(item['sleep_record_index'] == complete['record_index']
                               for item in state['following_requests']):
                        prior, unused = read(complete['record_index'])
                        require(prior['sha256'] == complete['record_sha256'], 'completed_sleep_pin')
                        previous_history = prior['document']['resume_state']['state']['history']
                        history = envelope['state']['history']
                        state['following_requests'].append(dict(reference,
                            sleep_record_index=complete['record_index'], history_sha256=_digest(history),
                            prior_raw_events_equal=history['events'][:len(previous_history['events'])] == previous_history['events'],
                            prior_operations_equal=history['operations'] == previous_history['operations']))
            elif state['exposure'] and record['kind'] == 'SLEEP_COMPLETE':
                envelope = document['resume_state']
                require(document['status'] == 'COMPLETE' and envelope['sha256'] == _digest(envelope['state'])
                        and envelope['state']['pending'] is None, 'actual_completed_sleep_only')
                state['completed_sleeps'].append(dict(reference, cycle=document['cycle'],
                    history_sha256=_digest(envelope['state']['history'])))
            elif state['exposure'] and record['kind'] in ('CONTEXT_RETAINED', 'COMPACTION', 'EVICTION'):
                state['boundaries'].append(dict(reference, kind=record['kind']))
            state.update(next_index=record['index'] + 1, head_sha256=record['sha256'])
        return dict(schema='ROHIN175_NODE1_RENDERED_SUFFIX_PROOF_V1', root=str(root), publication=publication,
            observed_unix=time.time(), cursor=state, bytes_charged=used, journal_id=journal_id,
            at_observed_tail=pending_tail, rendered=state['exposure'] is not None,
            registered=state['registration'] is not None, completed_sleeps_after_exposure=len(state['completed_sleeps']),
            coverage='record-only suffix anchored to actual parent SOURCE; no full-journal/intents audit',
            mtime_interpretation='filesystem_time_not_exact_event_time', evaluation_status='INCOMPLETE_NOT_ADJUDICATED',
            child_actions=0, raw_text_exported=False)
