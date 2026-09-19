"""R134 node-local, TRAIN-only classroom sidecar; never starts a child.

CLI (native roots, not their stream/ subdirectories):
  python3 -m gpu.orch_r134_classroom_relay --state-dir /node/relay-r134 \
    --child A1005=/node/child5 --child A1006=/node/child6 \
    --child A1007=/node/child7 --cadence sleep --total-polls 1

All-to-all peers, 3..16 distinct roots; parents/configs are not accessed. Default
cadence releases the last committed response at each validated SLEEP_COMPLETE.
`committed` releases each response; `experience_group --group-size N` releases
the last response of each N committed segments. No relay truncation: oversized
messages are rejected, and the source terminal/truncated flags are retained.

R134_CLASSROOM_RELAY_V1 receipts (create-only, 0400, retained .partial links):
  CONFIG: frozen children, journal identities, cadence and limits.
  source_<digest>: sender, journal_id, split, segment, exact raw, terminal,
    truncated, response_sha256, and REQUEST/RESPONSE/COMMITTED record references.
    References bind absolute path, exact file/intent hashes, record/document hashes.
  intent_<pair>: sender-response/receiver identity, source receipt, text hash.
  publication_<pair>: exact R127 inbox id/path/hash after acknowledged dispatch.
  observed_publication_<pair>: matching journal inbox when dispatch was uncertain.
  consumption_<pair>: first receiver REQUEST containing that environment event
    and its rendered text. This means request exposure, not successful inference.
  uncertain_<pair>: dispatch raised; intent alone also permanently forbids retry.
  rejected_<source>: exact response exceeds message limit; never shortened.

R127's existing _inbox API requires speaker=Tool for environment events. Text
starts `Peer A1005: ...` (or `Peer A1005 (source truncated): ...`), so the child
sees `Tool: Peer A1005: ...`, never a fabricated child/assistant event. Only the
response text crosses peers; request prefixes and parent inboxes do not.

Polls are bounded by records, journal bytes, serialized message bytes, dispatch attempts,
and a persistent total-attempt limit. Restart revalidates the source journals
incrementally from genesis, but never retries a pair with any intent artifact,
even a partial intent. Torn source tails wait untouched; invalid published
evidence fails closed. No journal writer locks, child callbacks, GPU imports,
network, subprocesses, recovery, or deletion. Keep the same state directory on
restart; deleting custody evidence is not a supported reset. Run provenance
checks/tests before main chooses configs or launches anything.
"""

import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

from gpu import orch_r127_pilot_console as inbox_api
from gpu.orch_r125_stream_journal import SCHEMA as JOURNAL_SCHEMA
from gpu.orch_r125_stream_journal import StreamJournal, _decode, _digest, require
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import SCHEMA as STREAM_SCHEMA
from organism_v6.orch_r125_plain_context import event_message


SCHEMA = 'R134_CLASSROOM_RELAY_V1'
DEFAULT_LIMITS = dict(max_message_bytes=16384, max_messages_per_poll=6,
    max_total_messages=1000, max_records_per_poll=96,
    max_scan_bytes_per_poll=128 * 1024 * 1024, max_record_bytes=16 * 1024 * 1024)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _exists(directory, name):
    try:
        entry = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return False
    require(stat.S_ISREG(entry.st_mode), 'regular_receipt_required')
    return True


class _PollLimit(Exception):
    pass


class _Budget:
    def __init__(self, limits):
        self.remaining = limits['max_scan_bytes_per_poll']
        self.file_limit = limits['max_record_bytes']

    def read(self, directory, name):
        size = os.stat(name, dir_fd=directory, follow_symlinks=False).st_size
        require(size <= self.file_limit, 'record_size_limit')
        if size > self.remaining:
            raise _PollLimit()
        self.remaining -= size
        return inbox_api._read(directory, name, min(size, self.file_limit))


class _JournalView:
    _checkpoint = staticmethod(StreamJournal._checkpoint)
    _unchanged = staticmethod(StreamJournal._unchanged)
    _inbox_event = StreamJournal._inbox_event
    _advance = StreamJournal._advance

    def __init__(self, name, root, stack):
        self.name, self.root = name, root
        self.inbox = root / 'stream' / 'inbox'
        self.directory = stack.enter_context(inbox_api._directory(root / 'stream'))
        self.records = stack.enter_context(inbox_api._directory(root / 'stream' / 'records'))
        self.inbox_directory = stack.enter_context(inbox_api._directory(self.inbox))
        raw = inbox_api._read(self.directory, 'JOURNAL.json', 4096)
        self.manifest = _decode(raw)
        require(type(self.manifest) is dict and set(self.manifest) == {'schema', 'journal_id'}
            and self.manifest['schema'] == JOURNAL_SCHEMA
            and type(self.manifest['journal_id']) is str
            and re.fullmatch(r'[0-9a-f]{32}', self.manifest['journal_id']), 'journal_manifest')
        self.manifest_sha256 = _sha(raw)
        self.state = dict(index=0, previous=_digest(self.manifest), latest=None,
            request=None, response=None, sleep_request=None, inbox={})
        self.request_ref = self.response_ref = None
        self.last_source = self.ready = None
        self.receiver_index = 0

    def reference(self, record, raw, intent_raw):
        return dict(path=str(self.root / 'stream' / 'records' / f'{record["index"]:020d}.json'),
            sha256=_sha(raw), intent_sha256=_sha(intent_raw), record_sha256=record['sha256'],
            document_sha256=_digest(record['document']))

    def check_paths(self):
        for path, pinned in ((self.root / 'stream', self.directory),
                (self.root / 'stream' / 'records', self.records), (self.inbox, self.inbox_directory)):
            with inbox_api._directory(path) as current:
                before, after = os.fstat(pinned), os.fstat(current)
                require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), 'journal_directory_replaced')

    def next_record(self, budget):
        index = self.state['index']
        name, intent_name = f'{index:020d}.json', f'{index:020d}.intent.json'
        if not _exists(self.records, name) or not _exists(self.records, intent_name):
            return None
        raw = budget.read(self.records, name)
        intent_raw = budget.read(self.records, intent_name)
        intent = _decode(intent_raw)
        record = _decode(raw)
        require(type(record) is dict and set(record) == {
            'schema', 'journal_id', 'index', 'kind', 'previous_sha256', 'document', 'sha256'},
            'journal_record_fields')
        require(record['schema'] == JOURNAL_SCHEMA and record['journal_id'] == self.manifest['journal_id']
            and type(record['index']) is int and record['index'] == index
            and record['previous_sha256'] == self.state['previous']
            and record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'}),
            'journal_chain_integrity')
        require(intent == StreamJournal._intent(record), 'journal_intent_binding')
        StreamJournal._validate_entry(record['kind'], record['document'])
        self._advance(self.state, record['kind'], record['document'])
        self.state['index'], self.state['previous'] = index + 1, record['sha256']
        return record, self.reference(record, raw, intent_raw)


class ClassroomRelay:
    """One nonblocking state-directory owner; poll() performs no sleeping."""

    def __init__(self, children, state_dir, *, cadence='sleep', group_size=4, **limits):
        self.stack = ExitStack()
        self.closed = False
        try:
            require(3 <= len(children) <= 16, 'three_to_sixteen_children_required')
            require(cadence in ('committed', 'sleep', 'experience_group'), 'cadence')
            require(type(group_size) is int and group_size > 0, 'positive_group_size')
            require(not (set(limits) - set(DEFAULT_LIMITS)), 'unknown_limit')
            self.limits = dict(DEFAULT_LIMITS, **limits)
            require(all(type(value) is int and value > 0 for value in self.limits.values()), 'positive_limits')
            require(self.limits['max_total_messages'] <= 10000
                and self.limits['max_message_bytes'] <= inbox_api.INBOX_LIMIT // 2
                and self.limits['max_scan_bytes_per_poll'] >= 4 * self.limits['max_record_bytes'] + 8192,
                'bounded_limits')
            self.cadence, self.group_size = cadence, group_size
            self.path = Path(state_dir).absolute()
            require('..' not in self.path.parts, 'parent_path_component_forbidden')
            roots = [Path(root).absolute() for root in children.values()]
            require(len(set(roots)) == len(roots), 'distinct_child_roots')
            for root in roots:
                require('..' not in root.parts and self.path != root
                    and self.path not in root.parents and root not in self.path.parents,
                    'separate_relay_custody_directory')
                require(not any(other in root.parents for other in roots), 'nonoverlapping_child_roots')
            self.views = []
            for name, root in sorted(zip(children, roots)):
                require(type(name) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,47}', name), 'plain_peer_name')
                self.views.append(_JournalView(name, root, self.stack))
            require(len({view.manifest['journal_id'] for view in self.views}) == len(self.views), 'distinct_journals')
            with inbox_api._directory(self.path.parent) as parent:
                try:
                    os.mkdir(self.path.name, 0o700, dir_fd=parent)
                    os.fsync(parent)
                except FileExistsError:
                    pass
            self.directory = self.stack.enter_context(inbox_api._directory(self.path))
            metadata = os.fstat(self.directory)
            require(metadata.st_uid == os.geteuid() and not metadata.st_mode & 0o077, 'private_relay_custody')
            fcntl.flock(self.directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
            config = dict(children=[dict(name=view.name, root=str(view.root),
                journal_id=view.manifest['journal_id'], manifest_sha256=view.manifest_sha256)
                for view in self.views], cadence=cadence, group_size=group_size, limits=self.limits)
            self._persist('CONFIG', config)
            self.attempted = set()
            with os.scandir(self.directory) as entries:
                for entry in entries:
                    matched = re.fullmatch(r'intent_([0-9a-f]{64})\.(json|partial)', entry.name)
                    if matched:
                        require(entry.is_file(follow_symlinks=False), 'regular_intent_required')
                        self.attempted.add(matched[1])
                        require(len(self.attempted) <= self.limits['max_total_messages'], 'attempt_limit_evidence')
            self.turn = 0
        except BaseException:
            self.close()
            raise

    def close(self):
        self.closed = True
        self.stack.close()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()

    def _persist(self, identifier, fields):
        document = dict(fields, schema=SCHEMA, id=identifier)
        raw = inbox_api._bytes(document)
        name = identifier + '.json'
        if _exists(self.directory, name):
            require(os.stat(name, dir_fd=self.directory, follow_symlinks=False).st_size == len(raw),
                'immutable_receipt_conflict')
            require(inbox_api._read(self.directory, name, len(raw)) == raw, 'immutable_receipt_conflict')
            return dict(path=str(self.path / name), sha256=_sha(raw))
        require(not _exists(self.directory, identifier + '.partial'), 'incomplete_receipt_no_retry')
        result = inbox_api._publish(self.directory, self.path, document)
        return dict(path=result['path'], sha256=result['sha256'])

    def _load(self, identifier):
        return _decode(inbox_api._read(self.directory, identifier + '.json', inbox_api.INBOX_LIMIT))

    @staticmethod
    def _pair(source, receiver):
        return _digest(dict(sender_journal_id=source['journal_id'], response_sha256=source['response_sha256'],
            receiver_journal_id=receiver.manifest['journal_id']))

    @staticmethod
    def _text(source):
        status = ' (source truncated)' if source['truncated'] else ''
        return 'Peer ' + source['sender'] + status + ': ' + source['raw']

    def _source(self, view, record, reference):
        document = record['document']
        row = document['state']['state']['rows'][-1]
        require(row['split'] == 'TRAIN' and row['actor'] == 'child', 'committed_TRAIN_child_only')
        response = view.response_ref
        require(view.request_ref is not None and response is not None, 'source_request_response_required')
        generated = view.last_response['response']
        require(view.last_request.get('schema') == view.last_response.get('schema') == STREAM_SCHEMA
            and view.last_response.get('raw_saved_before_validation') is True, 'source_stream_response_schema')
        for evidence in (view.last_request, view.last_response, generated, document, row):
            require(evidence.get('split', 'TRAIN') == 'TRAIN'
                and evidence.get('actor', 'child') == 'child'
                and evidence.get('origin', 'TRAIN_COLLECTION') == 'TRAIN_COLLECTION',
                'source_TRAIN_child_provenance')
        require(type(generated.get('raw')) is str and type(generated.get('truncated')) is bool
            and type(generated.get('terminal')) is bool
            and not (generated['terminal'] and generated['truncated'])
            and row['terminal'] == generated['terminal'] and row['truncated'] == generated['truncated'],
            'source_generation_flags')
        require(type(generated.get('token_ids')) is list and generated['token_ids']
            and all(type(token) is int and token >= 0 for token in generated['token_ids'])
            and len(generated['token_ids']) <= view.last_request['max_new_tokens']
            and (not generated['truncated'] or len(generated['token_ids']) == view.last_request['max_new_tokens']),
            'source_generation_tokens')
        source = dict(sender=view.name, journal_id=view.manifest['journal_id'], split='TRAIN',
            segment=row['segment'], raw=generated['raw'], truncated=generated['truncated'],
            terminal=generated['terminal'], response_sha256=document['source_sha256'],
            request=view.request_ref, response=response, committed=reference)
        source['id'] = _digest(source)
        return source

    def _observe_consumption(self, view, record, reference):
        request = record['document']
        checkpoint = request['resume_state']['state']
        history = checkpoint['history']
        frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
        messages = request['messages']
        for event in history['events'][frontier:]:
            if event['actor'] != 'environment' or not event['event_id'].startswith('environment:inbox:'):
                continue
            identifier = event['event_id'].removeprefix('environment:inbox:')
            registered = view.state['inbox'].get(identifier)
            if registered is None:
                continue
            message = registered['message']
            bound = message.get('source_receipt')
            if not isinstance(bound, dict) or Path(bound['path']).parent != self.path:
                continue
            matched = re.fullmatch(r'source_([0-9a-f]{64})\.json', Path(bound['path']).name)
            if not matched:
                continue
            source = self._load('source_' + matched[1])
            source['id'] = matched[1]
            pair = self._pair(source, view)
            if pair not in self.attempted or _exists(self.directory, 'consumption_' + pair + '.json'):
                continue
            if not _exists(self.directory, 'intent_' + pair + '.json'):
                continue
            intent = self._load('intent_' + pair)
            raw = inbox_api._read(self.directory, 'source_' + matched[1] + '.json', inbox_api.INBOX_LIMIT)
            text = self._text(source)
            expected = view._inbox_event(message, registered['source_id'], registered['source_sha256'])
            require(bound == intent['source_receipt'] and bound['sha256'] == _sha(raw)
                and message['actor'] == 'environment' and message['speaker'] == 'Tool'
                and message['text'] == text and intent['text_sha256'] == _sha(text.encode())
                and event == vars(expected), 'consumption_exact_peer_binding')
            rendered = event_message(expected) if checkpoint.get('presentation') else TrainHistory._message(expected)
            if rendered is None or rendered not in messages:
                continue
            publication = dict(id=message['id'], path=registered['source_id'], sha256=registered['source_sha256'])
            if _exists(self.directory, 'publication_' + pair + '.json'):
                require(self._load('publication_' + pair)['inbox'] == publication,
                    'consumption_publication_binding')
            else:
                self._persist('observed_publication_' + pair, dict(status='OBSERVED_INBOX',
                    pair=pair, inbox=publication, receiver_request=reference))
            self._persist('consumption_' + pair, dict(status='IN_REQUEST', pair=pair,
                source_receipt=bound, inbox=publication, receiver_request=reference))

    def _accept(self, view, record, reference):
        kind, document = record['kind'], record['document']
        if kind == 'REQUEST':
            view.request_ref = reference
            view.last_request = {key: value for key, value in document.items() if key != 'resume_state'}
            self._observe_consumption(view, record, reference)
        elif kind == 'RESPONSE':
            view.response_ref, view.last_response = reference, document
        elif kind == 'COMMITTED' and document['state']['state']['rows']:
            source = self._source(view, record, reference)
            view.last_source = source
            if self.cadence == 'committed' or (self.cadence == 'experience_group'
                    and (source['segment'] + 1) % self.group_size == 0):
                view.ready = dict(source=source, cadence_receipt=reference)
            view.request_ref = view.response_ref = None
        elif kind == 'SLEEP_COMPLETE' and self.cadence == 'sleep' and view.last_source:
            require(view.last_source['response_sha256'] in document['new_row_sha256'], 'cadence_source_binding')
            view.ready = dict(source=view.last_source, cadence_receipt=reference)

    def _dispatch(self, view, budget, remaining):
        source = view.ready['source']
        text = self._text(source)
        envelope = dict(schema=inbox_api.SCHEMA, id='0' * 32, text=text, split='TRAIN',
            actor='environment', speaker='Tool', source_receipt=dict(
                path=str(self.path / ('source_' + source['id'] + '.json')), sha256='0' * 64))
        if len(inbox_api._bytes(envelope)) > self.limits['max_message_bytes']:
            self._persist('rejected_' + source['id'], dict(status='MESSAGE_LIMIT',
                source=source, max_message_bytes=self.limits['max_message_bytes']))
            view.ready = None
            return 0
        used = 0
        if len(self.attempted) == self.limits['max_total_messages']:
            view.ready, view.receiver_index = None, 0
            return used
        while view.receiver_index < len(self.views):
            receiver = self.views[view.receiver_index]
            pair = self._pair(source, receiver)
            if receiver is view or pair in self.attempted:
                view.receiver_index += 1
                continue
            if used == remaining or len(self.attempted) == self.limits['max_total_messages']:
                break
            view.check_paths()
            receiver.check_paths()
            references = {item['path']: item for item in
                (source['request'], source['response'], source['committed'], view.ready['cadence_receipt'])}
            for reference in references.values():
                raw = budget.read(view.records, Path(reference['path']).name)
                require(_sha(raw) == reference['sha256'], 'source_changed_before_publication')
                intent_raw = budget.read(view.records, Path(reference['path']).stem + '.intent.json')
                require(_sha(intent_raw) == reference['intent_sha256'], 'source_intent_changed_before_publication')
            bound = self._persist('source_' + source['id'], source)
            self.attempted.add(pair)
            self._persist('intent_' + pair, dict(status='INTENT', pair=pair,
                sender=source['sender'], receiver=receiver.name,
                receiver_journal_id=receiver.manifest['journal_id'], source_receipt=bound,
                text_sha256=_sha(text.encode()), cadence_receipt=view.ready['cadence_receipt']))
            try:
                publication = inbox_api._inbox(receiver.root, 'Tool', text, bound)
                self._persist('publication_' + pair, dict(status='PUBLISHED', pair=pair, inbox=publication))
            except Exception as error:
                self._persist('uncertain_' + pair, dict(status='DISPATCH_UNCERTAIN_NO_RETRY',
                    pair=pair, error_type=type(error).__name__))
            used += 1
            view.receiver_index += 1
        if view.receiver_index == len(self.views):
            view.ready, view.receiver_index = None, 0
        return used

    def poll(self):
        require(not self.closed, 'relay_closed')
        budget = _Budget(self.limits)
        count = attempts = 0
        previous_attempts = len(self.attempted)
        try:
            for view in self.views:
                view.check_paths()
                require(_sha(budget.read(view.directory, 'JOURNAL.json')) == view.manifest_sha256,
                    'journal_manifest_changed')
            idle = 0
            while count < self.limits['max_records_per_poll'] and idle < len(self.views):
                view = self.views[self.turn % len(self.views)]
                self.turn += 1
                if view.ready is not None:
                    used = self._dispatch(view, budget, self.limits['max_messages_per_poll'] - attempts)
                    attempts += used
                    if view.ready is not None:
                        idle += 1
                        continue
                result = view.next_record(budget)
                if result is None:
                    idle += 1
                    continue
                idle = 0
                record, reference = result
                self._accept(view, record, reference)
                count += 1
        except _PollLimit:
            pass
        except BaseException:
            self.close()
            raise
        return dict(schema=SCHEMA, records=count, dispatch_attempts=len(self.attempted) - previous_attempts,
            total_attempts=len(self.attempted), scanned_bytes=self.limits['max_scan_bytes_per_poll'] - budget.remaining,
            total_limit_reached=len(self.attempted) >= self.limits['max_total_messages'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--child', action='append', required=True, metavar='NAME=NATIVE_ROOT')
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--cadence', choices=('committed', 'sleep', 'experience_group'), default='sleep')
    parser.add_argument('--group-size', type=int, default=4)
    parser.add_argument('--total-polls', type=int, default=1)
    parser.add_argument('--poll-seconds', type=float, default=1.0)
    for name, default in DEFAULT_LIMITS.items():
        parser.add_argument('--' + name.replace('_', '-'), type=int, default=default)
    args = parser.parse_args(argv)
    require(1 <= args.total_polls <= 1000000 and 0.01 <= args.poll_seconds <= 3600, 'finite_poll_budget')
    children = {}
    for child in args.child:
        name, separator, root = child.partition('=')
        require(separator and root and name not in children, 'unique_child_assignment')
        children[name] = root
    with ClassroomRelay(children, args.state_dir, cadence=args.cadence, group_size=args.group_size,
            **{name: getattr(args, name) for name in DEFAULT_LIMITS}) as relay:
        for index in range(args.total_polls):
            print(json.dumps(relay.poll(), sort_keys=True), flush=True)
            if index + 1 < args.total_polls:
                time.sleep(args.poll_seconds)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
