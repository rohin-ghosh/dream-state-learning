"""Prospective receiver-sleep turn-taking; never edits or stops a child.

Hold the stopped R134 predecessor's custody lock throughout this phase. Keep
both directories forever. Bootstrap pins observed journal heads without sending;
only requests beginning after those heads can become new sender-sleep sources.
One reserved attempt per latest receiver sleep, strict alternating peer order,
latest source only. An attempt (including uncertain/partial custody) cannot be
retried. Verified REQUEST exposure followed by another receiver sleep is needed
before another attempt, preventing delayed publications from forming a backlog.
Neither old queued messages nor old visible context are erased. No benefit claim.
"""

import argparse
from contextlib import ExitStack
import fcntl
import os
from pathlib import Path
import re
import time

from gpu import orch_r134_classroom_relay as relay


SCHEMA = 'R140_RECEIVER_SLEEP_PACING_V1'
POLICY = dict(
    source='last_committed_child_response_at_sender_SLEEP_COMPLETE',
    source_cutoff='REQUEST_index_at_or_after_phase_head',
    receiver_clock='latest_validated_receiver_SLEEP_COMPLETE',
    max_attempts_per_receiver_sleep=1,
    rotation='sorted_other_peers_alternating_on_reservation_including_uncertainty',
    selection='latest_eligible_source_only_no_backfill',
    backpressure='verified_REQUEST_exposure_then_later_receiver_sleep',
    context='unchanged_no_erasure_no_invented_distillation',
    attribution='TRAIN_environment_Tool_Peer',
    uncertainty='never_retry_partial_reserved_or_uncertain_pairs',
)


class ReceiverSleepPacing(relay.ClassroomRelay):
    def __init__(self, children, state_dir, predecessor, *, hard_end_unix, **limits):
        self.predecessor_stack = ExitStack()
        self.hard_end_unix = hard_end_unix
        self.predecessor_path = Path(predecessor).absolute()
        self.phase = None
        self.epochs, self.eligible = {}, {}
        self.slots = {name: {} for name in children}
        self.inherited_pending, self.inherited_exposures = {}, {}
        self.unknown_predecessor_attempt = False
        try:
            relay.require(type(hard_end_unix) in (int, float)
                and time.time() < hard_end_unix < float('inf'), 'finite_future_phase_wall')
            destination = Path(state_dir).absolute()
            relay.require(destination != self.predecessor_path
                and destination not in self.predecessor_path.parents
                and self.predecessor_path not in destination.parents, 'separate_phase_custody')
            for root in map(lambda value: Path(value).absolute(), children.values()):
                relay.require(root != self.predecessor_path and root not in self.predecessor_path.parents
                    and self.predecessor_path not in root.parents, 'predecessor_outside_children')
            self.predecessor_directory = self.predecessor_stack.enter_context(
                relay.inbox_api._directory(self.predecessor_path))
            metadata = os.fstat(self.predecessor_directory)
            relay.require(metadata.st_uid == os.geteuid() and not metadata.st_mode & 0o077,
                'private_predecessor_custody')
            fcntl.flock(self.predecessor_directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.predecessor_files = self._predecessor_manifest()
            self.predecessor_binding = dict(path=str(self.predecessor_path),
                device=metadata.st_dev, inode=metadata.st_ino,
                files_sha256=relay._digest(self.predecessor_files), files=self.predecessor_files)
            old_config = self._old('CONFIG')
            relay.require(old_config['schema'] == relay.SCHEMA and old_config['cadence'] == 'sleep',
                'sleep_cadence_predecessor')
            inherited_attempts = self._inherited_attempts(children)
            super().__init__(children, state_dir, cadence='sleep', **limits)
            relay.require(self._load('CONFIG')['children'] == old_config['children'],
                'same_predecessor_child_journals')
            relay.require(self.limits['max_total_messages'] <= old_config['limits']['max_total_messages'],
                'predecessor_total_budget_not_extended')
            self.attempted.update(inherited_attempts)
            self._recover_slots()
            relay.require(len(self.attempted) <= self.limits['max_total_messages'], 'inherited_total_limit')
            if relay._exists(self.directory, 'PHASE.json'):
                self.phase = self._load('PHASE')
                relay.require(self.phase['schema'] == SCHEMA
                    and self.phase['config_sha256'] == self._receipt('CONFIG')['sha256']
                    and set(self.phase['heads']) == set(children), 'phase_binding')
            else:
                relay.require(not relay._exists(self.directory, 'PHASE.partial'),
                    'incomplete_phase_no_implicit_reset')
            self.inherited_count = len(inherited_attempts)
        except BaseException:
            self.close()
            raise

    def close(self):
        if hasattr(self, 'stack'):
            super().close()
        self.predecessor_stack.close()

    def _predecessor_manifest(self):
        result, total = {}, 0
        with os.scandir(self.predecessor_directory) as entries:
            for entry in entries:
                relay.require(len(result) < 50000 and entry.is_file(follow_symlinks=False)
                    and re.fullmatch(r'(CONFIG|[a-z_]+_[a-f0-9]{64})\.(json|partial)', entry.name),
                    'bounded_regular_predecessor_receipts')
                size = entry.stat(follow_symlinks=False).st_size
                total += size
                relay.require(size <= relay.inbox_api.INBOX_LIMIT and total <= 64 * 1024 * 1024,
                    'predecessor_byte_limit')
                raw = relay.inbox_api._read(self.predecessor_directory, entry.name, size)
                result[entry.name] = dict(bytes=size, sha256=relay._sha(raw))
        return result

    def _old(self, identifier):
        name = identifier + '.json'
        raw = relay.inbox_api._read(self.predecessor_directory, name, relay.inbox_api.INBOX_LIMIT)
        relay.require(relay._sha(raw) == self.predecessor_files[name]['sha256'],
            'predecessor_receipt_changed')
        return relay._decode(raw)

    def _inherited_attempts(self, children):
        attempted = {match[1] for name in self.predecessor_files
            if (match := re.fullmatch(r'intent_([a-f0-9]{64})\.(json|partial)', name))}
        for pair in sorted(attempted):
            if 'intent_' + pair + '.json' not in self.predecessor_files:
                self.unknown_predecessor_attempt = True
                continue
            intent = self._old('intent_' + pair)
            relay.require(intent['receiver'] in children and intent['sender'] in children
                and intent['receiver'] != intent['sender'] and intent['pair'] == pair,
                'predecessor_intent_identity')
            if 'consumption_' + pair + '.json' in self.predecessor_files:
                continue
            bound = intent['source_receipt']
            source_path = Path(bound['path'])
            relay.require(source_path.parent == self.predecessor_path
                and re.fullmatch(r'source_[a-f0-9]{64}\.json', source_path.name)
                and self.predecessor_files[source_path.name]['sha256'] == bound['sha256'],
                'predecessor_source_binding')
            source = self._old(source_path.stem)
            self.inherited_pending[pair] = dict(intent=intent, source=source)
        return attempted

    def _persist(self, identifier, fields):
        if identifier == 'CONFIG':
            fields = dict(fields, policy=POLICY, predecessor=self.predecessor_binding,
                hard_end_unix=self.hard_end_unix)
        document = dict(fields, schema=SCHEMA, id=identifier)
        raw = relay.inbox_api._bytes(document)
        name = identifier + '.json'
        if relay._exists(self.directory, name):
            relay.require(relay.inbox_api._read(self.directory, name,
                relay.inbox_api.INBOX_LIMIT) == raw, 'immutable_pacing_receipt_conflict')
            return dict(path=str(self.path / name), sha256=relay._sha(raw))
        relay.require(not relay._exists(self.directory, identifier + '.partial'),
            'incomplete_pacing_receipt_no_retry')
        result = relay.inbox_api._publish(self.directory, self.path, document)
        return dict(path=result['path'], sha256=result['sha256'])

    def _receipt(self, identifier):
        raw = relay.inbox_api._read(self.directory, identifier + '.json', relay.inbox_api.INBOX_LIMIT)
        return dict(path=str(self.path / (identifier + '.json')), sha256=relay._sha(raw))

    def _recover_slots(self):
        with os.scandir(self.directory) as entries:
            for entry in entries:
                match = re.fullmatch(r'slot_(.+)_([0-9]{20})_([a-f0-9]{64})\.(json|partial)', entry.name)
                if not match:
                    continue
                name, epoch, pair = match[1], int(match[2]), match[3]
                relay.require(name in self.slots and entry.is_file(follow_symlinks=False), 'regular_pacing_slot')
                existing = self.slots[name].get(epoch)
                relay.require(existing is None or existing == pair, 'one_reservation_per_receiver_sleep')
                self.slots[name][epoch] = pair
                self.attempted.add(pair)

    def _observe_inherited(self, view, record, reference):
        checkpoint = record['document']['resume_state']['state']
        history = checkpoint['history']
        frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
        for pair, pending in self.inherited_pending.items():
            if pair in self.inherited_exposures or pending['intent']['receiver'] != view.name:
                continue
            intent, source = pending['intent'], pending['source']
            for event in history['events'][frontier:]:
                if event['actor'] != 'environment' or not event['event_id'].startswith('environment:inbox:'):
                    continue
                registered = view.state['inbox'].get(event['event_id'].removeprefix('environment:inbox:'))
                if registered is None or registered['message'].get('source_receipt') != intent['source_receipt']:
                    continue
                message = registered['message']
                expected = view._inbox_event(message, registered['source_id'], registered['source_sha256'])
                text = self._text(source)
                relay.require(message['actor'] == 'environment' and message['speaker'] == 'Tool'
                    and message['text'] == text and relay._sha(text.encode()) == intent['text_sha256']
                    and event == vars(expected), 'exact_inherited_peer_binding')
                rendered = (relay.event_message(expected) if checkpoint.get('presentation')
                    else relay.TrainHistory._message(expected))
                if rendered is None or rendered not in record['document']['messages']:
                    continue
                self._persist('inherited_consumption_' + pair, dict(status='IN_REQUEST', pair=pair,
                    receiver=view.name, predecessor_source=intent['source_receipt'], receiver_request=reference))
                self.inherited_exposures[pair] = record['index']
                break

    def _accept(self, view, record, reference):
        super()._accept(view, record, reference)
        view.ready = None
        if record['kind'] == 'REQUEST':
            self._observe_inherited(view, record, reference)
        if self.phase is None:
            return
        head = self.phase['heads'][view.name]
        if record['index'] + 1 == head['index']:
            relay.require(record['sha256'] == head['previous'], 'original_phase_head_unchanged')
        if record['kind'] != 'SLEEP_COMPLETE' or record['index'] < head['index']:
            return
        prior = self.epochs.get(view.name)
        if prior is not None and int(Path(prior['path']).stem) not in self.slots[view.name]:
            self._persist('skipped_' + relay._digest(dict(receiver=view.name, epoch=prior)),
                dict(status='SUPERSEDED_RECEIVER_INTERVAL_NO_BACKFILL', receiver=view.name,
                    epoch=prior, replacement=reference))
        self.epochs[view.name] = reference
        source = view.last_source
        if source is None or int(Path(source['request']['path']).stem) < head['index']:
            return
        previous = self.eligible.get(view.name)
        if previous is not None:
            self._persist('superseded_' + relay._digest(dict(old=previous['source']['id'], new=source['id'])),
                dict(status='SUPERSEDED_FOR_FUTURE_SELECTION', sender=view.name,
                    source=previous['source'], replacement=source['id']))
        self.eligible[view.name] = dict(source=source, cadence_receipt=reference)

    def _caught_up(self):
        for view in self.views:
            name = f'{view.state["index"]:020d}'
            if any(relay._exists(view.records, name + suffix)
                for suffix in ('.json', '.intent.json', '.json.partial', '.intent.json.partial')):
                return False
        return True

    def _receiver_available(self, receiver, epoch):
        if self.unknown_predecessor_attempt or epoch in self.slots[receiver.name]:
            return False
        for pair, pending in self.inherited_pending.items():
            if pending['intent']['receiver'] == receiver.name:
                if pair not in self.inherited_exposures or self.inherited_exposures[pair] >= epoch:
                    return False
        previous = self.slots[receiver.name]
        if not previous:
            return True
        last = max(previous)
        relay.require(last <= epoch, 'receiver_epoch_not_regressed')
        pair = previous[last]
        slot = f'slot_{receiver.name}_{last:020d}_{pair}'
        if not relay._exists(self.directory, slot + '.json'):
            return False
        if self._load(slot)['status'] == 'SKIPPED_OVERSIZE':
            return True
        if not relay._exists(self.directory, 'consumption_' + pair + '.json'):
            return False
        consumed = self._load('consumption_' + pair)
        relay.require(consumed['status'] == 'IN_REQUEST', 'verified_prior_exposure')
        return int(Path(consumed['receiver_request']['path']).stem) < epoch

    def _send(self, receiver, budget):
        if receiver.name not in self.epochs or len(self.attempted) >= self.limits['max_total_messages']:
            return 0
        epoch_ref = self.epochs[receiver.name]
        epoch = int(Path(epoch_ref['path']).stem)
        if not self._receiver_available(receiver, epoch):
            return 0
        peers = sorted(view.name for view in self.views if view is not receiver)
        sender = peers[len(self.slots[receiver.name]) % len(peers)]
        selected = self.eligible.get(sender)
        if selected is None:
            return 0
        source = selected['source']
        pair = self._pair(source, receiver)
        if pair in self.attempted:
            return 0
        sender_view = next(view for view in self.views if view.name == sender)
        for view, references in ((sender_view, [source['request'], source['response'], source['committed'],
                selected['cadence_receipt']]), (receiver, [epoch_ref])):
            view.check_paths()
            for reference in references:
                path = Path(reference['path'])
                relay.require(relay._sha(budget.read(view.records, path.name)) == reference['sha256']
                    and relay._sha(budget.read(view.records, path.stem + '.intent.json'))
                    == reference['intent_sha256'], 'pacing_source_or_epoch_changed')
        if not self._caught_up():
            return 0
        with relay.inbox_api._directory(self.predecessor_path) as current:
            metadata = os.fstat(current)
            relay.require((metadata.st_dev, metadata.st_ino) ==
                (self.predecessor_binding['device'], self.predecessor_binding['inode'])
                and self._predecessor_manifest() == self.predecessor_files,
                'predecessor_custody_unchanged_before_publication')
        bound = self._persist('source_' + source['id'], source)
        text = self._text(source)
        envelope = dict(schema=relay.inbox_api.SCHEMA, id='0' * 32, text=text, split='TRAIN',
            actor='environment', speaker='Tool', source_receipt=bound)
        oversized = len(relay.inbox_api._bytes(envelope)) > self.limits['max_message_bytes']
        fields = dict(status='SKIPPED_OVERSIZE' if oversized else 'RESERVED', pair=pair,
            sender=sender, receiver=receiver.name, receiver_journal_id=receiver.manifest['journal_id'],
            receiver_sleep=epoch_ref, source_receipt=bound, text_sha256=relay._sha(text.encode()),
            cadence_receipt=selected['cadence_receipt'], rotation_index=len(self.slots[receiver.name]))
        self.slots[receiver.name][epoch] = pair
        self.attempted.add(pair)
        self._persist(f'slot_{receiver.name}_{epoch:020d}_{pair}', fields)
        if oversized:
            return 1
        self._persist('intent_' + pair, dict(fields, status='INTENT'))
        try:
            publication = relay.inbox_api._inbox(receiver.root, 'Tool', text, bound)
            self._persist('publication_' + pair, dict(status='PUBLISHED', pair=pair, inbox=publication))
        except Exception as error:
            self._persist('uncertain_' + pair, dict(status='DISPATCH_UNCERTAIN_NO_RETRY',
                pair=pair, error_type=type(error).__name__))
        return 1

    def poll(self):
        relay.require(not self.closed, 'pacing_closed')
        budget = relay._Budget(self.limits)
        count = attempts = idle = 0
        if time.time() >= self.hard_end_unix:
            return dict(schema=SCHEMA, status='WALL_EXPIRED', dispatch_attempts=0)
        try:
            for view in self.views:
                view.check_paths()
                relay.require(relay._sha(budget.read(view.directory, 'JOURNAL.json'))
                    == view.manifest_sha256, 'pacing_journal_manifest_changed')
            while count < self.limits['max_records_per_poll'] and idle < len(self.views):
                view = self.views[self.turn % len(self.views)]
                self.turn += 1
                result = view.next_record(budget)
                if result is None:
                    idle += 1
                    continue
                idle = 0
                self._accept(view, *result)
                count += 1
            if idle == len(self.views) and self._caught_up():
                if self.phase is None:
                    fields = dict(config_sha256=self._receipt('CONFIG')['sha256'],
                        phase_started_unix=time.time(), pid=os.getpid(),
                        heads={view.name: dict(index=view.state['index'], previous=view.state['previous'])
                            for view in self.views})
                    self._persist('PHASE', fields)
                    self.phase = self._load('PHASE')
                else:
                    relay.require(all(view.state['index'] >= self.phase['heads'][view.name]['index']
                        for view in self.views), 'phase_prefix_not_lost')
                    for receiver in self.views:
                        if attempts >= self.limits['max_messages_per_poll'] or time.time() >= self.hard_end_unix:
                            break
                        attempts += self._send(receiver, budget)
        except relay._PollLimit:
            pass
        except BaseException:
            self.close()
            raise
        return dict(schema=SCHEMA, status='ACTIVE' if self.phase else 'BOOTSTRAPPING_NO_SEND',
            records=count, dispatch_attempts=attempts, total_reserved_pairs=len(self.attempted),
            inherited_attempts=self.inherited_count,
            total_limit_reached=len(self.attempted) >= self.limits['max_total_messages'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', action='append', required=True)
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--predecessor', required=True)
    parser.add_argument('--hard-end-unix', type=float, required=True)
    parser.add_argument('--total-polls', type=int, default=1)
    parser.add_argument('--poll-seconds', type=float, default=2)
    for name, default in relay.DEFAULT_LIMITS.items():
        parser.add_argument('--' + name.replace('_', '-'), type=int, default=default)
    args = parser.parse_args(argv)
    relay.require(1 <= args.total_polls <= 1000000 and 0.01 <= args.poll_seconds <= 3600,
        'bounded_pacing_polls')
    children = {}
    for child in args.child:
        name, separator, root = child.partition('=')
        relay.require(separator and root and name not in children, 'unique_pacing_child')
        children[name] = root
    with ReceiverSleepPacing(children, args.state_dir, args.predecessor,
            hard_end_unix=args.hard_end_unix,
            **{name: getattr(args, name) for name in relay.DEFAULT_LIMITS}) as pacing:
        for index in range(args.total_polls):
            report = pacing.poll()
            print(relay.inbox_api._bytes(report).decode().strip(), flush=True)
            if report['status'] == 'WALL_EXPIRED':
                break
            if index + 1 < args.total_polls:
                time.sleep(min(args.poll_seconds, max(0, args.hard_end_unix - time.time())))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
