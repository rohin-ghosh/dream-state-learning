"""Exclusive local journal for ContinualStream callbacks and a TRAIN parent inbox.

Create with StreamJournal(root, create=True); reopening never repairs a tail.
Publish operator messages atomically as inbox/*.json (stage under another suffix).
latest_checkpoint returns None until an authoritative checkpoint is recorded.
Raw RESPONSE data is retained without validating generation success. Recovery
keeps REQUEST pending until matching COMMITTED, and SLEEP_REQUEST pending until
a matching SLEEP_COMPLETE receipt. Metadata cannot resolve either operation.
COMPACTION accepts history-operation-only snapshots with no pending operation;
ordinary COMMITTED still requires a response except for the empty birth state.
Checksums detect retained-evidence corruption, not malicious deletion of an
entire valid journal suffix; external evidence custody remains the caller's job.
R133 experiment bindings are immutable across all authoritative transitions;
legacy checkpoints without a binding remain unmodified.
The exclusive writer caches validated state, checking retained file identities
on use. Changed files trigger full validation; open and audit always replay the
complete chain. No historical record is rewritten or discarded by this cache.
"""

from copy import deepcopy
from dataclasses import asdict
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import threading
import uuid
import weakref

from organism_v6.orch_r124_train_history import TrainEvent
from organism_v6.orch_r125_continual_stream import ContinualStream


SCHEMA = 'R125_STREAM_JOURNAL_V1'
INBOX_LIMIT = 1024 * 1024
WALL_EXTENSION_SCHEMA = 'R131_SAVED_STATE_WALL_EXTENSION_V1'
_JOURNALS = weakref.WeakSet()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_JSON_key')
        result[key] = value
    return result


def _decode(raw):
    def nonfinite(value):
        raise ValueError('nonfinite_JSON:' + value)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=nonfinite)


def validate_wall_extension(authorization):
    require(type(authorization) is dict and set(authorization) == {
        'schema', 'previous_deadline_unix', 'previous_stream_sha256', 'new_deadline_unix',
        'lease_end_unix', 'safety_margin_seconds'}
        and authorization['schema'] == WALL_EXTENSION_SCHEMA, 'exact_wall_extension_authorization')
    require(type(authorization['previous_stream_sha256']) is str
        and re.fullmatch(r'[0-9a-f]{64}', authorization['previous_stream_sha256']), 'wall_extension_prior_digest')
    for name in ('previous_deadline_unix', 'new_deadline_unix', 'lease_end_unix', 'safety_margin_seconds'):
        value = authorization[name]
        require(type(value) in (int, float) and 0 <= value < float('inf') and math.isfinite(value),
                'finite_wall_extension_budget')
    require(authorization['safety_margin_seconds'] >= 120
        and authorization['previous_deadline_unix'] < authorization['new_deadline_unix']
        <= authorization['lease_end_unix'] - authorization['safety_margin_seconds'], 'wall_extension_lease_bound')
    return authorization


def _after_fork():
    for journal in list(_JOURNALS):
        journal._close_descriptors()


os.register_at_fork(after_in_child=_after_fork)


class StreamJournal:
    def __init__(self, root, *, create=False):
        require(type(create) is bool, 'explicit_create_flag')
        self.root = Path(root).absolute()
        self.inbox = self.root / 'inbox'
        self._owner = os.getpid()
        self._mutex = threading.RLock()
        self._fds = []
        self._closed = False
        self._failed = False
        _JOURNALS.add(self)
        try:
            if create:
                self.root.mkdir(mode=0o700, parents=False, exist_ok=False)
                parent = os.open(self.root.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
                try:
                    os.fsync(parent)
                finally:
                    os.close(parent)
            self._root_fd = self._open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            flags = os.O_RDWR | (os.O_CREAT | os.O_EXCL if create else 0)
            self._lock_fd = self._open('WRITER.lock', flags, self._root_fd)
            require(stat.S_ISREG(os.fstat(self._lock_fd).st_mode), 'regular_writer_lock')
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if create:
                os.mkdir('records', mode=0o700, dir_fd=self._root_fd)
                os.mkdir('inbox', mode=0o700, dir_fd=self._root_fd)
                self._publish(self._root_fd, 'JOURNAL.json', dict(schema=SCHEMA, journal_id=uuid.uuid4().hex))
            self._records_fd = self._open('records', os.O_RDONLY | os.O_DIRECTORY, self._root_fd)
            self._inbox_fd = self._open('inbox', os.O_RDONLY | os.O_DIRECTORY, self._root_fd)
            self._manifest = self._read_json(self._root_fd, 'JOURNAL.json')
            require(type(self._manifest) is dict and set(self._manifest) == {'schema', 'journal_id'}
                    and self._manifest['schema'] == SCHEMA
                    and re.fullmatch(r'[0-9a-f]{32}', self._manifest['journal_id']) is not None,
                    'journal_manifest')
            self._state = self._reload_state()
        except BaseException:
            self._close_descriptors()
            raise

    def _open(self, name, flags, directory=None):
        descriptor = os.open(name, flags | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
                             mode=0o600, dir_fd=directory)
        self._fds.append(descriptor)
        return descriptor

    def _close_descriptors(self):
        self._closed = True
        descriptors, self._fds = self._fds, []
        for descriptor in reversed(descriptors):
            os.close(descriptor)

    def close(self):
        if self._closed:
            return
        with self._mutex:
            self._close_descriptors()

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.close()

    def _ensure_open(self):
        require(os.getpid() == self._owner and not self._closed, 'journal_closed_or_inherited')
        require(not self._failed, 'journal_failed_no_retry')
        root = os.stat(self.root, follow_symlinks=False)
        bound = os.fstat(self._root_fd)
        require((root.st_dev, root.st_ino) == (bound.st_dev, bound.st_ino), 'journal_root_replaced')
        for name, descriptor in (('WRITER.lock', self._lock_fd), ('records', self._records_fd),
                                 ('inbox', self._inbox_fd)):
            current = os.stat(name, dir_fd=self._root_fd, follow_symlinks=False)
            bound = os.fstat(descriptor)
            require((current.st_dev, current.st_ino) == (bound.st_dev, bound.st_ino), 'journal_binding_replaced')

    @staticmethod
    def _publish(directory, name, document):
        raw = _encoded(document) + b'\n'
        partial = name + '.partial'
        descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                             mode=0o600, dir_fd=directory)
        with os.fdopen(descriptor, 'wb') as stream:
            os.fsync(directory)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(partial, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        os.fsync(directory)
        os.unlink(partial, dir_fd=directory)
        os.fsync(directory)

    @staticmethod
    def _read_bytes(directory, name, limit=None):
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=directory)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), 'regular_file_required')
            require(limit is None or before.st_size <= limit, 'inbox_size_limit')
            raw = stream.read() if limit is None else stream.read(limit + 1)
            require(limit is None or len(raw) <= limit, 'inbox_size_limit')
            after = os.fstat(stream.fileno())
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            def identity(value):
                return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns
            require(identity(before) == identity(after) == identity(current), 'file_changed_during_read')
            return raw

    @classmethod
    def _read_json(cls, directory, name):
        return _decode(cls._read_bytes(directory, name))

    @staticmethod
    def _checkpoint(document):
        require(type(document) is dict and set(document) == {'state', 'sha256'}, 'stream_checkpoint_fields')
        require(type(document['state']) is dict and document['sha256'] == _digest(document['state']),
                'stream_checkpoint_integrity')
        ContinualStream.restore(document, expected_sha256=document['sha256'])
        return dict(document=deepcopy(document), expected_sha256=document['sha256'])

    @staticmethod
    def _unchanged(before, after, changed):
        require(set(before) == set(after) and all(before[key] == after[key] for key in before if key not in changed),
                'unexpected_stream_state_transition')
        if 'history' in changed:
            old, new = before['history'], after['history']
            require(all(old[key] == new[key] for key in ('schema', 'system_prompt', 'birth_prompt'))
                    and new['events'][:len(old['events'])] == old['events']
                    and new['operations'][:len(old['operations'])] == old['operations'],
                    'history_must_extend_not_reset')

    def _inbox_event(self, message, path, source_sha256):
        attributed = type(message) is dict and message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1'
        expected = {'id', 'text', 'split', 'actor'}
        if attributed:
            expected |= {'schema', 'speaker', 'source_receipt'}
        require(type(message) is dict and set(message) == expected, 'exact_inbox_schema')
        require(type(message['id']) is str and bool(message['id'].strip())
                and type(message['text']) is str, 'inbox_id_and_text')
        if attributed:
            require(message['split'] == 'TRAIN' and message['actor'] in ('parent', 'environment'), 'TRAIN_attributed_inbox_only')
            if message['actor'] == 'parent':
                require(message['speaker'] in ('Astra', 'Fable', 'Rohin') and message['source_receipt'] is None,
                    'actual_parent_attribution')
            else:
                receipt = message['source_receipt']
                require(message['speaker'] == 'Tool' and type(receipt) is dict and set(receipt) == {'path', 'sha256'}
                    and type(receipt['path']) is str and Path(receipt['path']).is_absolute()
                    and type(receipt['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', receipt['sha256']),
                    'tool_result_provenance')
        else:
            require(message['split'] == 'TRAIN' and message['actor'] == 'parent', 'TRAIN_parent_inbox_only')
        require(type(path) is str and Path(path).parent == self.inbox and Path(path).name.endswith('.json'),
                'inbox_source_path')
        text = message['speaker'] + ': ' + message['text'] if attributed else message['text']
        return TrainEvent(event_id=message['actor'] + ':inbox:' + message['id'], actor=message['actor'], text=text,
                          split='TRAIN', phase='feedback' if message['actor'] == 'environment' else 'experience', episode_id='continual_stream', source_id=path,
                          source_sha256=source_sha256, origin='TRAIN_COLLECTION')

    def _advance(self, state, kind, document):
        if kind == 'INBOX':
            require(set(document) == {'message', 'source_id', 'source_sha256'}, 'inbox_receipt_fields')
            self._inbox_event(document['message'], document['source_id'], document['source_sha256'])
            identifier = document['message']['id']
            require(identifier not in state['inbox'], 'duplicate_inbox_registration')
            state['inbox'][identifier] = deepcopy(document)
            return
        if kind == 'RESPONSE':
            require(state['request'] is not None and state['response'] is None, 'response_without_unique_request')
            require(document.get('request_sha256') == state['latest']['document']['state']['pending'],
                    'response_request_binding')
            state['response'] = deepcopy(document)
            return
        if kind not in ('REQUEST', 'COMMITTED', 'CONTEXT_COMMITTED', 'CONTEXT_INPUT', 'COMPACTION', 'PRESENTATION', 'SLEEP_REQUEST', 'SLEEP_COMPLETE', 'WALL_EXTENDED'):
            return
        key = 'state' if kind in ('COMMITTED', 'CONTEXT_COMMITTED', 'CONTEXT_INPUT', 'COMPACTION', 'PRESENTATION', 'WALL_EXTENDED') else 'resume_state'
        require(key in document, 'authoritative_checkpoint_required')
        checkpoint = self._checkpoint(document[key])
        current = checkpoint['document']['state']
        previous = state['latest']['document']['state'] if state['latest'] else None
        if previous is not None:
            require(current.get('experiment') == previous.get('experiment'), 'journal_experiment_configuration_frozen')
        if kind == 'WALL_EXTENDED':
            require(set(document) == {'schema', 'authorization', 'plan_sha256', 'state'}
                and document['schema'] == 'R131_WALL_EXTENDED_V1'
                and type(document['plan_sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', document['plan_sha256']),
                'exact_wall_extension_record')
            authorization = validate_wall_extension(document['authorization'])
            require(previous is not None and previous['pending'] is None and current['pending'] is None
                and state['request'] is None and state['response'] is None and state['sleep_request'] is None
                and previous['sleep_frontier'] == len(previous['rows']) and previous['sleep_receipts']
                and previous['sleep_receipts'][-1].get('status') == 'COMPLETE', 'wall_extension_saved_sleep_boundary')
            require(authorization['previous_stream_sha256'] == state['latest']['expected_sha256']
                and authorization['previous_deadline_unix'] == previous['deadline_unix']
                and authorization['new_deadline_unix'] == current['deadline_unix'], 'wall_extension_exact_prior_binding')
            require(_encoded({key: value for key, value in previous.items() if key != 'deadline_unix'})
                == _encoded({key: value for key, value in current.items() if key != 'deadline_unix'}),
                'wall_extension_only_deadline_changes')
        elif kind == 'REQUEST':
            require(state['request'] is None and state['sleep_request'] is None, 'unresolved_request_never_bypassed')
            request = {name: value for name, value in document.items() if name != 'resume_state'}
            require(request.get('split') == 'TRAIN' and type(request.get('segment')) is int
                    and request['segment'] == len(current['rows']) and current['pending'] == _digest(request),
                    'request_checkpoint_binding')
            if previous is not None:
                require(previous['pending'] is None, 'unresolved_checkpoint')
                self._unchanged(previous, current, {'history', 'pending'})
            state['request'], state['response'] = deepcopy(request), None
        elif kind == 'COMMITTED':
            require(current['pending'] is None, 'commit_must_clear_pending')
            if previous is None:
                require(not current['rows'] and not current['sleep_receipts'] and current['sleep_frontier'] == 0,
                        'only_empty_initial_commit')
            else:
                require(state['request'] is not None and state['response'] is not None,
                        'commit_requires_request_and_response')
                require(state['request'].get('training_eligible', True) is True,
                        'context_only_response_never_training_target')
                self._unchanged(previous, current, {'history', 'pending', 'rows'})
                rows, prior = current['rows'], previous['rows']
                require(len(rows) == len(prior) + 1 and rows[:-1] == prior, 'commit_child_frontier')
                response = state['response']
                require(document.get('segment') == len(prior)
                        and document.get('source_sha256') == rows[-1]['source_sha256'] == _digest(response)
                        and rows[-1]['prefix'] == state['request']['messages']
                        and rows[-1]['target'] == response['response']['raw']
                        and rows[-1]['token_ids'] == response['response']['token_ids'], 'commit_response_binding')
            state['request'], state['response'] = None, None
        elif kind == 'CONTEXT_COMMITTED':
            require(previous is not None and state['request'] is not None and state['response'] is not None
                    and state['sleep_request'] is None and current['pending'] is None
                    and state['request'].get('training_eligible') is False
                    and document.get('training_eligible') is False, 'context_commit_requires_masked_response')
            self._unchanged(previous, current, {'history', 'pending'})
            response = state['response']
            prior_events = previous['history']['events']
            events = current['history']['events']
            require(events[:len(prior_events)] == prior_events and len(events) == len(prior_events) + 2
                    and events[-2]['actor'] == 'child'
                    and events[-2]['event_id'] == document.get('response_event_id')
                    and events[-2]['text'] == response['response']['raw']
                    and events[-2]['source_sha256'] == document.get('source_sha256') == _digest(response)
                    and events[-1]['actor'] == 'environment'
                    and current['history']['operations'] == previous['history']['operations']
                    and current['history'].get('working_state') == previous['history'].get('working_state'),
                    'context_response_exact_history_append')
            state['request'], state['response'] = None, None
        elif kind == 'CONTEXT_INPUT':
            require(previous is not None and previous['pending'] is None and current['pending'] is None
                    and state['request'] is None and state['response'] is None and state['sleep_request'] is None,
                    'context_input_requires_idle_state')
            self._unchanged(previous, current, {'history'})
            prior_events = previous['history']['events']
            events = current['history']['events']
            require(events[:len(prior_events)] == prior_events and len(events) > len(prior_events)
                    and all(event['actor'] in ('parent', 'environment') for event in events[len(prior_events):])
                    and current['history']['operations'] == previous['history']['operations']
                    and current['history'].get('working_state') == previous['history'].get('working_state'),
                    'context_input_only_external_events')
        elif kind == 'COMPACTION':
            require(previous is not None and previous['pending'] is None and current['pending'] is None
                    and state['request'] is None and state['sleep_request'] is None,
                    'compaction_cannot_clear_pending')
            self._unchanged(previous, current, {'history'})
            require(current['history']['events'] == previous['history']['events']
                    and len(current['history']['operations']) > len(previous['history']['operations']),
                    'compaction_only_history_operations_advance')
        elif kind == 'PRESENTATION':
            require(previous is not None and previous['pending'] is None and current['pending'] is None
                    and state['request'] is None and state['sleep_request'] is None
                    and previous['sleep_frontier'] == len(previous['rows']),
                    'presentation_requires_saved_sleep_boundary')
            require({key: value for key, value in previous.items() if key not in ('presentation', 'context_limit')}
                    == {key: value for key, value in current.items() if key not in ('presentation', 'context_limit')},
                    'unexpected_stream_state_transition')
            require(current.get('presentation') is not None, 'plain_presentation_required')
        elif kind == 'SLEEP_REQUEST':
            require(previous is not None and previous['pending'] is None
                    and state['request'] is None and state['sleep_request'] is None,
                    'unresolved_operation_before_sleep')
            self._unchanged(previous, current, {'pending'})
            rows = current['rows'][current['sleep_frontier']:]
            require(rows and current['pending'] == 'sleep:' + _digest([row['source_sha256'] for row in rows]),
                    'sleep_request_frontier_binding')
            state['sleep_request'] = {name: value for name, value in document.items() if name != 'resume_state'}
        else:
            require(previous is not None and (previous['pending'] is None or state['sleep_request'] is not None)
                    and state['request'] is None
                    and current['pending'] is None, 'sleep_cannot_bypass_request')
            self._unchanged(previous, current, {'pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'})
            receipt = {name: value for name, value in document.items() if name != 'resume_state'}
            if current.get('experiment') is not None:
                require(receipt.get('checkpoint', {}).get('experiment') == current['experiment'],
                        'sleep_model_experiment_binding')
            if state['sleep_request'] is not None and 'cycle' in state['sleep_request']:
                require(receipt.get('cycle') == state['sleep_request']['cycle'], 'sleep_cycle_binding')
            rows = current['rows']
            filter_no_update = False
            if any(name in receipt for name in ('code_target_filter', 'learn_review_filter',
                    'code_target_filter_zero_update', 'learn_review_zero_update', 'no_update_subreason')):
                from organism_v6.orch_r194_code_target_filter import validate_filter_zero_update_receipt
                filter_no_update = validate_filter_zero_update_receipt(
                    receipt, rows[previous['sleep_frontier']:], rows[:previous['sleep_frontier']])
            require(previous['sleep_frontier'] < current['sleep_frontier'] == len(rows)
                    and current['sleep_receipts'] == previous['sleep_receipts'] + [receipt]
                    and receipt.get('new_row_sha256') == [row['source_sha256'] for row in rows[previous['sleep_frontier']:]]
                    and receipt.get('status') == 'COMPLETE'
                    and type(receipt.get('optimizer_steps')) is int and (receipt['optimizer_steps'] > 0
                    or filter_no_update
                    or current.get('presentation') is not None and receipt['optimizer_steps'] == 0
                    and receipt.get('no_update_reason') == 'no_eligible_child_rows'
                    and not receipt.get('presentations') and receipt.get('child_token_exposures') == 0
                    and receipt.get('anchor_token_exposures') == 0),
                    'sleep_frontier_binding')
            references = receipt.get('checkpoint_sha256', {})
            require(type(references) is dict and set(references) == {'adapter', 'optimizer', 'rng'}
                    and all(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) for value in references.values())
                    and current['model_state_sha256'] == _digest(references), 'sleep_checkpoint_binding')
            state['sleep_request'] = None
        state['latest'] = checkpoint

    def _scan(self):
        self._ensure_open()
        require(not any(name.endswith('.partial') for name in os.listdir(self._root_fd)), 'incomplete_journal_initialization')
        require(self._read_json(self._root_fd, 'JOURNAL.json') == self._manifest, 'journal_manifest_changed')
        names = set(os.listdir(self._records_fd))
        indices = set()
        for name in names:
            matched = re.fullmatch(r'(\d{20})(?:\.intent)?\.json', name)
            require(matched is not None, 'incomplete_or_unexpected_journal_tail')
            indices.add(int(matched[1]))
        require(sorted(indices) == list(range(len(indices))), 'noncontiguous_journal')
        state = dict(index=0, previous=_digest(self._manifest), latest=None, request=None,
                     response=None, sleep_request=None, inbox={})
        for index in sorted(indices):
            name = f'{index:020d}.json'
            intent_name = f'{index:020d}.intent.json'
            require(name in names and intent_name in names, 'incomplete_journal_tail')
            record = self._read_json(self._records_fd, name)
            intent = self._read_json(self._records_fd, intent_name)
            require(type(record) is dict and set(record) == {
                'schema', 'journal_id', 'index', 'kind', 'previous_sha256', 'document', 'sha256'}, 'journal_record_fields')
            payload = {key: value for key, value in record.items() if key != 'sha256'}
            require(record['schema'] == SCHEMA and record['journal_id'] == self._manifest['journal_id']
                    and type(record['index']) is int and record['index'] == index
                    and record['previous_sha256'] == state['previous'] and record['sha256'] == _digest(payload),
                    'journal_chain_integrity')
            require(intent == self._intent(record), 'journal_intent_binding')
            self._validate_entry(record['kind'], record['document'])
            self._advance(state, record['kind'], record['document'])
            state['index'], state['previous'] = index + 1, record['sha256']
        require(set(os.listdir(self._records_fd)) == names, 'journal_changed_during_scan')
        return state

    @staticmethod
    def _file_identity(entry):
        return (entry.st_dev, entry.st_ino, entry.st_mode, entry.st_size,
                entry.st_mtime_ns, entry.st_ctime_ns)

    def _record_snapshot(self):
        with os.scandir(self._records_fd) as entries:
            return {entry.name: self._file_identity(entry.stat(follow_symlinks=False))
                    for entry in entries}

    def _reload_state(self, snapshot=None):
        self._ensure_open()
        before = self._record_snapshot() if snapshot is None else snapshot
        state = self._scan()
        require(self._record_snapshot() == before, 'journal_changed_during_scan')
        self._record_signatures = before
        return state

    def _validated_state(self):
        self._ensure_open()
        require(not any(name.endswith('.partial') for name in os.listdir(self._root_fd)),
                'incomplete_journal_initialization')
        require(self._read_json(self._root_fd, 'JOURNAL.json') == self._manifest,
                'journal_manifest_changed')
        snapshot = self._record_snapshot()
        if snapshot != self._record_signatures:
            self._state = self._reload_state(snapshot)
        return self._state

    def audit(self):
        """Revalidate every retained byte and transition, regardless of cache."""
        with self._mutex:
            self._state = self._reload_state()
            return dict(record_count=self._state['index'], head_sha256=self._state['previous'])

    @staticmethod
    def _validate_entry(kind, document):
        require(type(kind) is str and re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', kind) is not None, 'journal_kind')
        require(type(document) is dict, 'journal_document_object')

    @staticmethod
    def _intent(record):
        return dict(schema=SCHEMA, journal_id=record['journal_id'], index=record['index'],
                    previous_sha256=record['previous_sha256'], record_sha256=record['sha256'])

    def record(self, kind, document):
        with self._mutex:
            self._ensure_open()
            try:
                self._validate_entry(kind, document)
                document = _decode(_encoded(document))
                state = self._validated_state()
                index, previous = state['index'], state['previous']
                self._advance(state, kind, document)
                record = dict(schema=SCHEMA, journal_id=self._manifest['journal_id'], index=index,
                              kind=kind, previous_sha256=previous, document=document)
                record['sha256'] = _digest(record)
                self._publish(self._records_fd, f'{index:020d}.intent.json', self._intent(record))
                self._publish(self._records_fd, f'{index:020d}.json', record)
                for name in (f'{index:020d}.intent.json', f'{index:020d}.json'):
                    self._record_signatures[name] = self._file_identity(
                        os.stat(name, dir_fd=self._records_fd, follow_symlinks=False))
                state['index'], state['previous'] = index + 1, record['sha256']
                return dict(index=index, path=str(self.root / 'records' / f'{index:020d}.json'), sha256=record['sha256'])
            except BaseException:
                self._failed = True
                raise

    def latest_checkpoint(self):
        with self._mutex:
            return deepcopy(self._validated_state()['latest'])

    def read_inbox(self):
        """Return canonical, repeatable parent events; never wait or delete input."""
        with self._mutex:
            state = self._validated_state()
            known = state['inbox']
            paths, candidates = {}, {}
            for name in sorted(os.listdir(self._inbox_fd)):
                entry = os.stat(name, dir_fd=self._inbox_fd, follow_symlinks=False)
                require(not stat.S_ISLNK(entry.st_mode), 'inbox_symlink_forbidden')
                if not name.endswith('.json'):
                    continue
                raw = self._read_bytes(self._inbox_fd, name, INBOX_LIMIT)
                message, source_sha256 = _decode(raw), hashlib.sha256(raw).hexdigest()
                path = str(self.inbox / name)
                self._inbox_event(message, path, source_sha256)
                paths[path] = source_sha256
                identifier = message['id']
                existing = known.get(identifier) or candidates.get(identifier)
                if existing:
                    require(existing['source_sha256'] == source_sha256, 'conflicting_inbox_id_bytes')
                else:
                    candidates[identifier] = dict(message=message, source_id=path, source_sha256=source_sha256)
            for receipt in known.values():
                require(paths.get(receipt['source_id']) == receipt['source_sha256'], 'registered_inbox_file_missing_or_changed')
            for identifier, receipt in candidates.items():
                self.record('INBOX', receipt)
                known[identifier] = receipt
            return [self._inbox_event(receipt['message'], receipt['source_id'], receipt['source_sha256'])
                    for receipt in known.values()]
