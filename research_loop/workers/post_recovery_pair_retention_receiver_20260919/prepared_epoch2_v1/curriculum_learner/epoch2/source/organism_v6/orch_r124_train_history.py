"""TRAIN-only inference history; no tokenizer, model, scheduler or filesystem calls.

Callers verify source_id/source_sha256 against actual TRAIN collection receipts.
Pinned prompts are caller-supplied, never inferred from a draft. Raw events and
view-operation receipts remain append-only even after compaction or eviction.
The token counter must measure the exact rendered chat template; callers reserve
space for additional input/output and mask the final composed prefix themselves.
Checkpoint hashes detect corruption, not authorship: pin state_sha256 externally
when restoring a checkpoint from outside the current trusted process.
Optional working-state text is sliced only from an appended child event. The
caller interprets optional JSON/prose fields and explicit deletion requests;
storage never unescapes, rewrites or synthesizes text. The attributed state view
has a fixed 2048 UTF-8-byte cap (not tokens), including provenance overhead. Plain
presentation emits only joined child texts, bounded conservatively by that same
cap. State follows birth, before the raw turns and current runtime status; the
caller's exact token counter still bounds and masks the entire history.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Callable


SCHEMA = 'R124_TRAIN_HISTORY_V1'
ACTORS = frozenset(('child', 'parent', 'environment'))
PHASES = frozenset(('episode', 'experience', 'open_turn', 'open_train',
                    'presleep', 'reflection', 'compaction', 'feedback'))
ASSERTION = 'CHILD_ASSERTION_NOT_VERIFIED_FACT'
WORKING_STATE_SCHEMA = 'THINK_ACT_STATE_V1'
WORKING_STATE_BYTE_BUDGET = 2048
WORKING_STATE_KINDS = frozenset(('finding', 'uncertainty', 'next_intention',
                               'open_question', 'prediction', 'note', 'investigation',
                               'judgment', 'expected_consequence', 'process_adjustment'))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_JSON_key')
        result[key] = value
    return result


@dataclass(frozen=True)
class TrainEvent:
    event_id: str
    actor: str
    text: str
    split: str
    phase: str
    episode_id: str
    source_id: str
    source_sha256: str
    origin: str

    def __post_init__(self):
        for name, value in asdict(self).items():
            require(type(value) is str, 'event_string_field:' + name)
            require(name == 'text' or bool(value.strip()), 'empty_event_field:' + name)
        require(self.actor in ACTORS, 'unknown_actor')
        require(self.split == 'TRAIN', 'TRAIN_only_event')
        require(self.origin == 'TRAIN_COLLECTION', 'readout_origin_forbidden')
        require(self.phase in PHASES, 'unknown_or_readout_phase')
        require(_hash(self.source_sha256), 'source_sha256_required')

    @classmethod
    def restore(cls, document):
        require(type(document) is dict and set(document) == set(cls.__dataclass_fields__),
                'exact_event_fields')
        return cls(**document)


@dataclass(frozen=True)
class WorkingStateSpan:
    id: str
    kind: str
    start: int
    end: int

    def __post_init__(self):
        require(type(self.id) is str and bool(self.id.strip()), 'working_state_id_required')
        require(type(self.kind) is str and self.kind in WORKING_STATE_KINDS, 'working_state_kind')
        require(type(self.start) is int and type(self.end) is int
                and 0 <= self.start < self.end, 'working_state_source_span')


class WorkingStateOverflow(ValueError):
    def __init__(self, byte_count):
        self.byte_count = byte_count
        self.byte_budget = WORKING_STATE_BYTE_BUDGET
        super().__init__(f'working_state_overflow:{byte_count}>{self.byte_budget}; '
                         'explicit_child_revision_or_deletion_required; prior_state_unchanged')


@dataclass(frozen=True)
class Frontier:
    event_count: int
    sha256: str

    def __post_init__(self):
        require(type(self.event_count) is int and self.event_count >= 0, 'frontier_count')
        require(_hash(self.sha256), 'frontier_sha256')

    @classmethod
    def restore(cls, document):
        require(type(document) is dict and set(document) == {'event_count', 'sha256'},
                'exact_frontier_fields')
        return cls(**document)


@dataclass(frozen=True)
class MaskedInput:
    """All labels mask history, including historical child and parent tokens."""

    messages: list[dict[str, str]]
    labels: tuple[int, ...]
    token_count: int

    @property
    def target_token_ids(self):
        return ()


class CompactionRequired(ValueError):
    def __init__(self, token_count, token_budget):
        self.token_count = token_count
        self.token_budget = token_budget
        super().__init__(f'compaction_required:{token_count}>{token_budget}; '
                         'no_silent_eviction_or_prompt_truncation')


class TrainHistory:
    def __init__(self, *, system_prompt: str, birth_prompt: str):
        require(type(system_prompt) is str and bool(system_prompt.strip()), 'system_prompt_required')
        require(type(birth_prompt) is str and bool(birth_prompt.strip()), 'birth_prompt_required')
        self._system_prompt = system_prompt
        self._birth_prompt = birth_prompt
        self._events = []
        self._by_id = {}
        self._operations = []
        self._working_entries = {}
        self._working_updates = []
        self._pinned_parent_event_ids = []

    @property
    def events(self):
        """Immutable raw collection events; summaries live in operation receipts."""
        return tuple(self._events)

    @property
    def operations(self):
        return tuple(deepcopy(self._operations))

    @property
    def working_state(self):
        """Detached active assertions, with runtime-bound source identities."""
        return dict(schema=WORKING_STATE_SCHEMA, revision=len(self._working_updates),
                    entries=deepcopy(list(self._working_entries.values())))

    @property
    def working_state_updates(self):
        return tuple(deepcopy(self._working_updates))

    @property
    def visible_frontier(self):
        """Exclusive raw-event prefix already compacted or explicitly evicted."""
        if self._operations:
            return Frontier.restore(self._operations[-1]['through'])
        return self.frontier(0)

    def append(self, event: TrainEvent) -> bool:
        require(type(event) is TrainEvent, 'typed_event_required')
        if event.event_id in self._by_id:
            require(self._by_id[event.event_id] == event, 'conflicting_event_id')
            return False
        self._events.append(event)
        self._by_id[event.event_id] = event
        return True

    def pin_parent_event(self, event_id):
        require(event_id in self._by_id and self._by_id[event_id].actor == 'parent',
                'only_existing_parent_input_can_be_pinned')
        if event_id in self._pinned_parent_event_ids:
            return False
        self._pinned_parent_event_ids.append(event_id)
        return True

    def frontier(self, event_count=None) -> Frontier:
        count = len(self._events) if event_count is None else event_count
        require(type(count) is int and 0 <= count <= len(self._events), 'frontier_out_of_range')
        return Frontier(count, _digest([asdict(event) for event in self._events[:count]]))

    def _check_frontier(self, frontier):
        require(type(frontier) is Frontier, 'typed_frontier_required')
        require(frontier == self.frontier(frontier.event_count), 'frontier_hash_mismatch')

    def _summary(self):
        if self._operations and self._operations[-1]['kind'] == 'compaction':
            return TrainEvent.restore(self._operations[-1]['summary'])
        return None

    def _record(self, kind, through, **fields):
        operation = dict(kind=kind, at=asdict(self.frontier()),
                         before=asdict(self.visible_frontier), through=asdict(through), **fields)
        operation['receipt_sha256'] = _digest(operation)
        self._operations.append(operation)
        return deepcopy(operation)

    def update_working_state(self, source: TrainEvent, *, entries=(), delete=()) -> bool:
        """Apply one optional child-authored delta per actual committed raw event.

        Entries are WorkingStateSpan(id, kind, start, end), with Python character
        offsets and an exclusive end. Text and provenance are derived, never
        supplied. Callers interpret child-chosen IDs/kinds and explicit delete
        requests from optional output fields; this store does not infer intent.
        No JSON decoding, labels or response format are required here. Omitted
        existing IDs remain active; replacement or deletion of an ID is explicit.
        Exact retries are no-ops, conflicting/stale sources fail. Invalid deltas
        raise ValueError without modifying history, state or update receipts;
        callers may append their own masked environment explanation afterward.
        This validates recorded provenance, not an external collection receipt.
        """
        return self._update_working_state(source, entries=entries, delete=delete, at=self.frontier())

    def _update_working_state(self, source, *, entries, delete, at):
        require(type(source) is TrainEvent and source.actor == 'child', 'own_child_state_source_required')
        self._check_frontier(at)
        require(self._by_id.get(source.event_id) == source, 'working_state_source_identity')
        require(source in self._events[:at.event_count], 'working_state_committed_raw_source_required')
        require(type(entries) in (tuple, list) and all(type(entry) is WorkingStateSpan for entry in entries),
                'typed_working_state_entries_required')
        require(type(delete) in (tuple, list) and all(type(identifier) is str and identifier.strip()
                for identifier in delete), 'explicit_working_state_delete_ids_required')
        entries, delete = tuple(entries), tuple(delete)
        identifiers = [entry.id for entry in entries]
        require(len(set(identifiers)) == len(identifiers) and len(set(delete)) == len(delete),
                'duplicate_working_state_id')
        require(not set(identifiers).intersection(delete), 'working_state_update_delete_conflict')
        require(bool(entries or delete), 'nonempty_working_state_delta_required')
        require(all(entry.end <= len(source.text) for entry in entries), 'working_state_source_span')
        require(all(source.text[entry.start:entry.end].strip() for entry in entries),
                'working_state_text_required')
        proposed = dict(entries=[asdict(entry) for entry in entries], delete=list(delete))
        source_fields = dict(source_event_id=source.event_id, source_id=source.source_id,
                             source_sha256=source.source_sha256)
        command = dict(**source_fields, **proposed)
        for previous in self._working_updates:
            if previous['source_event_id'] == source.event_id or previous['source_id'] == source.source_id:
                require(all(previous[key] == value for key, value in command.items()),
                        'conflicting_working_state_source')
                return False
        if self._working_updates:
            previous = self._working_updates[-1]
            previous_source = self._by_id[previous['source_event_id']]
            require(at.event_count >= previous['at']['event_count']
                    and self._events.index(source) > self._events.index(previous_source),
                    'stale_working_state_source')
        require(all(identifier in self._working_entries for identifier in delete),
                'unknown_working_state_delete_id')
        candidate = deepcopy(self._working_entries)
        for identifier in delete:
            del candidate[identifier]
        for entry in entries:
            candidate[entry.id] = dict(**asdict(entry), text=source.text[entry.start:entry.end], **source_fields)
        revision = len(self._working_updates) + 1
        message = self._working_message(candidate, revision)
        byte_count = len(message['content'].encode('utf-8')) if message else 0
        if byte_count > WORKING_STATE_BYTE_BUDGET:
            raise WorkingStateOverflow(byte_count)
        receipt = dict(revision=revision, at=asdict(at), **command)
        receipt['receipt_sha256'] = _digest(receipt)
        self._working_entries = candidate
        self._working_updates.append(receipt)
        return True

    @staticmethod
    def _working_message(entries, revision, *, plain=False):
        if not entries:
            return None
        if plain:
            return dict(role='assistant', content='\n\n'.join(entry['text'] for entry in entries.values()))
        parts = ['Child working state (not a verified fact)',
                 _json(dict(schema=WORKING_STATE_SCHEMA, revision=revision))]
        for entry in entries.values():
            parts.extend((_json({key: value for key, value in entry.items() if key != 'text'}), entry['text']))
        return dict(role='assistant', content='\n'.join(parts))

    def compact(self, summary: TrainEvent, *, through: Frontier) -> bool:
        """Explicit child summary of an exact raw prefix; retain newer raw events.

        The summary is archived separately, not counted in raw frontiers. A new
        summary may shorten the same frontier again; a stale frontier cannot
        move the active view backwards. Identical summary retries are no-ops.
        """
        require(type(summary) is TrainEvent and summary.actor == 'child', 'child_summary_required')
        require(summary.phase in ('reflection', 'compaction') and bool(summary.text.strip()),
                'explicit_nonempty_child_compaction')
        self._check_frontier(through)
        require(through.event_count > 0, 'nonempty_compaction_frontier')
        if summary.event_id in self._by_id:
            require(self._by_id[summary.event_id] == summary, 'conflicting_event_id')
            prior = next((operation for operation in self._operations
                          if operation['kind'] == 'compaction'
                          and operation['summary']['event_id'] == summary.event_id), None)
            require(prior is not None and prior['through'] == asdict(through),
                    'conflicting_summary_frontier_or_raw_event_id')
            return False
        require(through.event_count >= self.visible_frontier.event_count, 'frontier_regression')
        self._record('compaction', through, summary=asdict(summary), summary_status=ASSERTION)
        self._by_id[summary.event_id] = summary
        return True

    def evict_oldest(self, through: Frontier, *, reason: str) -> dict:
        """R125 opt-in view eviction, never raw deletion or automatic overflow handling.

        Drops the active summary, if any, and visible raw events through the
        supplied exclusive frontier. An equal frontier can drop only a summary.
        The returned receipt and a rendered omission notice make loss explicit.
        """
        require(type(reason) is str and bool(reason.strip()), 'explicit_eviction_reason_required')
        self._check_frontier(through)
        before = self.visible_frontier
        require(through.event_count >= before.event_count, 'frontier_regression')
        summary = self._summary()
        if through == before and summary is None:
            if self._operations:
                prior = self._operations[-1]
                if prior['kind'] == 'eviction' and prior['through'] == asdict(through) and prior['reason'] == reason:
                    return deepcopy(prior)
            raise ValueError('eviction_requires_visible_events')
        dropped = [event.event_id for event in self._events[before.event_count:through.event_count]]
        return self._record('eviction', through, reason=reason, dropped_event_ids=dropped,
                            dropped_summary_id=summary.event_id if summary else None)

    def render(self, token_count: Callable[[list[dict[str, str]]], int],
               token_budget: int, *, split='TRAIN', presentation=None,
               retained_parent_event_id=None) -> MaskedInput:
        """Strict, non-mutating render. Overflow requires an explicit caller action."""
        require(split == 'TRAIN', 'history_forbidden_in_readout')
        require(type(token_budget) is int and token_budget >= 0, 'nonnegative_token_budget')
        require(callable(token_count), 'token_counter_required')
        require(retained_parent_event_id is None or
                retained_parent_event_id in self._by_id and
                self._by_id[retained_parent_event_id].actor == 'parent',
                'retention_requires_existing_parent_input')
        messages = [dict(role='system', content=self._system_prompt),
                    dict(role='user', content=self._birth_prompt)]
        summary = self._summary()
        if summary:
            messages.append(self._message(summary, dict(summary_status=ASSERTION,
                            consumed_frontier=asdict(self.visible_frontier))))
        receipt = next((operation for operation in reversed(self._operations)
                        if operation['kind'] == 'eviction'), None)
        if receipt:
            notice = dict(kind='EXPLICIT_OLDEST_HISTORY_EVICTION',
                          omitted_frontier=receipt['through'], receipt_sha256=receipt['receipt_sha256'],
                          reason=receipt['reason'], raw_evidence_preserved=True,
                          historical_omission=True, later_compaction_present=bool(summary))
            messages.append(dict(role='user', content='History omission notice (not a child assertion):\n' + _json(notice)))
        for event in self._events[self.visible_frontier.event_count:]:
            if event.event_id not in self._pinned_parent_event_ids:
                messages.append(self._message(event))
        if retained_parent_event_id is not None and retained_parent_event_id not in self._pinned_parent_event_ids:
            retained = self._by_id[retained_parent_event_id]
            if retained in self._events[:self.visible_frontier.event_count]:
                messages.append(self._message(retained))
        if presentation is not None:
            from organism_v6.orch_r125_plain_context import VERSION, replay_prefix
            require(presentation['version'] == VERSION, 'known_presentation_version')
            messages = replay_prefix(messages, presentation)
        working_message = self._working_message(self._working_entries, len(self._working_updates),
                                               plain=presentation is not None)
        if working_message:
            messages.insert(2, working_message)
        pinned = [dict(role='user', content=self._by_id[event_id].text)
                  for event_id in self._pinned_parent_event_ids]
        insertion = 3 if working_message else 2
        messages[insertion:insertion] = pinned
        count = token_count(deepcopy(messages))
        require(type(count) is int and count >= 0, 'invalid_token_count')
        if count > token_budget:
            raise CompactionRequired(count, token_budget)
        return MaskedInput(messages=messages, labels=(-100,) * count, token_count=count)

    @staticmethod
    def _message(event, extra=None):
        labels = dict(child='Child assertion (not a verified fact)',
                      parent='Parent advice (not an observed fact)',
                      environment='Recorded environment observation')
        metadata = asdict(event)
        metadata.pop('text')
        metadata.update(extra or {})
        return dict(role='assistant' if event.actor == 'child' else 'user',
                    content=labels[event.actor] + '\n' + _json(metadata) + '\n' + event.text)

    def checkpoint(self) -> dict:
        document = dict(schema=SCHEMA, system_prompt=self._system_prompt, birth_prompt=self._birth_prompt,
                        events=[asdict(event) for event in self._events],
                        operations=deepcopy(self._operations), frontier=asdict(self.frontier()))
        if self._working_updates:
            document['working_state'] = dict(**self.working_state, updates=deepcopy(self._working_updates),
                                            rendered_byte_budget=WORKING_STATE_BYTE_BUDGET)
        if self._pinned_parent_event_ids:
            document['pinned_parent_event_ids'] = list(self._pinned_parent_event_ids)
        document['state_sha256'] = _digest(document)
        return document

    def to_json(self) -> str:
        """Serialize for caller-owned persistence; state_sha256 hashes the payload."""
        return _json(self.checkpoint())

    @classmethod
    def restore(cls, document: dict, *, expected_sha256=None):
        fields = {'schema', 'system_prompt', 'birth_prompt', 'events', 'operations', 'frontier', 'state_sha256'}
        require(type(document) is dict and fields <= set(document)
                <= fields | {'working_state', 'pinned_parent_event_ids'},
            'exact_checkpoint_fields')
        require(document['schema'] == SCHEMA, 'checkpoint_schema')
        payload = {key: value for key, value in document.items() if key != 'state_sha256'}
        require(_hash(document['state_sha256']) and _digest(payload) == document['state_sha256'],
                'checkpoint_integrity')
        if expected_sha256 is not None:
            require(_hash(expected_sha256) and expected_sha256 == document['state_sha256'],
                    'checkpoint_external_binding')
        require(type(document['events']) is list and type(document['operations']) is list, 'checkpoint_lists')
        history = cls(system_prompt=document['system_prompt'], birth_prompt=document['birth_prompt'])
        events = [TrainEvent.restore(event) for event in document['events']]
        position = 0
        for operation in document['operations']:
            require(type(operation) is dict and {'kind', 'at', 'through'} <= set(operation), 'operation_fields')
            at = Frontier.restore(operation['at'])
            require(position <= at.event_count <= len(events), 'operation_frontier_order')
            for event in events[position:at.event_count]:
                require(history.append(event), 'duplicate_checkpoint_event')
            position = at.event_count
            history._check_frontier(at)
            through = Frontier.restore(operation['through'])
            if operation['kind'] == 'compaction':
                require('summary' in operation, 'summary_required')
                require(history.compact(TrainEvent.restore(operation['summary']), through=through),
                        'duplicate_compaction_receipt')
            elif operation['kind'] == 'eviction':
                require('reason' in operation, 'eviction_reason_required')
                previous_count = len(history._operations)
                history.evict_oldest(through, reason=operation['reason'])
                require(len(history._operations) == previous_count + 1, 'duplicate_eviction_receipt')
            else:
                raise ValueError('unknown_history_operation')
            require(history._operations[-1] == operation, 'operation_integrity_or_frontier')
        for event in events[position:]:
            require(history.append(event), 'duplicate_checkpoint_event')
        require(history.frontier() == Frontier.restore(document['frontier']), 'checkpoint_frontier')
        if 'working_state' in document:
            state = document['working_state']
            require(type(state) is dict and set(state) == {
                'schema', 'revision', 'entries', 'updates', 'rendered_byte_budget'}, 'working_state_fields')
            require(state['schema'] == WORKING_STATE_SCHEMA
                    and type(state['revision']) is int and state['revision'] > 0
                    and type(state['rendered_byte_budget']) is int
                    and state['rendered_byte_budget'] == WORKING_STATE_BYTE_BUDGET,
                    'working_state_schema_or_bound')
            require(type(state['updates']) is list and bool(state['updates'])
                    and type(state['entries']) is list, 'working_state_checkpoint_lists')
            for update in state['updates']:
                require(type(update) is dict and set(update) == {
                    'revision', 'at', 'source_event_id', 'source_id', 'source_sha256',
                    'entries', 'delete', 'receipt_sha256'}, 'working_state_update_fields')
                require(type(update['source_event_id']) is str
                        and update['source_event_id'] in history._by_id, 'working_state_source_identity')
                require(type(update['entries']) is list and all(type(entry) is dict
                        and set(entry) == {'id', 'kind', 'start', 'end'} for entry in update['entries']),
                        'working_state_entry_fields')
                source = history._by_id[update['source_event_id']]
                accepted = history._update_working_state(source,
                    entries=[WorkingStateSpan(**entry) for entry in update['entries']],
                    delete=update['delete'], at=Frontier.restore(update['at']))
                require(accepted and _json(history._working_updates[-1]) == _json(update),
                        'working_state_update_integrity')
            require(_json(history.checkpoint()['working_state']) == _json(state), 'working_state_integrity')
        if 'pinned_parent_event_ids' in document:
            pinned = document['pinned_parent_event_ids']
            require(type(pinned) is list and bool(pinned) and all(type(item) is str for item in pinned),
                    'pinned_parent_event_ids_list')
            for event_id in pinned:
                require(history.pin_parent_event(event_id), 'duplicate_pinned_parent_event')
        require(history.checkpoint() == document, 'checkpoint_roundtrip_integrity')
        return history

    @classmethod
    def from_json(cls, text: str, *, expected_sha256=None):
        def invalid_constant(value):
            raise ValueError('nonfinite_JSON_constant:' + value)
        document = json.loads(text, object_pairs_hook=_object, parse_constant=invalid_constant)
        return cls.restore(document, expected_sha256=expected_sha256)
