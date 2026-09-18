"""Source-bound reading discussion without blocking ordinary learner cycles."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re

from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


POLICY = 'R205_READING_DISCUSSION_V1'
DISCUSSION_POLICY = 'R222_DEEP_WORK_DISCUSSION_V1'


def is_deep_work(text):
    return re.search(r'\b(?:really\s+)?think\s+(?:deeply\s+)?(?:about|through)\s+(?:this|it|that)\b|'
        r'\bwork\s+(?:through\s+)?(?:this|it|that|the\s+(?:question|problem))\s+'
        r'(?:through\s+)?with\s+(?:your|the)\s+parent\b', text, re.IGNORECASE) is not None


def is_reading(text):
    return (len(text.split()) > 600 or re.search(r'\bread\s+this\b', text, re.IGNORECASE) is not None
        or is_deep_work(text))


def reference(event):
    return dict(event_id=event.event_id, source_id=event.source_id, source_sha256=event.source_sha256)


def parent_fields(event, speaker):
    if event.actor != 'parent':
        return None
    try:
        raw = Path(event.source_id).read_bytes()
        message = json.loads(raw)
    except (OSError, ValueError):
        return None
    if not (isinstance(message, dict) and message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1'
            and message.get('actor') == 'parent' and message.get('speaker') == speaker
            and event.event_id == 'parent:inbox:' + message.get('id', '')
            and hashlib.sha256(raw).hexdigest() == event.source_sha256
            and event.text == speaker + ': ' + message.get('text', '')):
        return None
    fields = {}
    for line in message['text'].splitlines():
        match = re.fullmatch(r'(Reading|Section|Child response|Judgment|Restatement|Behavior change|'
            r'Release reading|Rework reading|Artifact response|Artifact|Limitations):\s*(.*)', line)
        if match:
            if match[1] in fields:
                return None
            fields[match[1]] = match[2].strip()
    identifier = fields.get('Reading', fields.get('Release reading', fields.get('Rework reading', '')))
    if not re.fullmatch(r'[0-9a-f]{32}', identifier):
        return None
    if any(fields.get(name, identifier) != identifier for name in ('Release reading', 'Rework reading')):
        return None
    fields['Reading'] = identifier
    return fields


def rendered(event, request):
    state = request['resume_state']['state']
    if event.event_id in state['history'].get('pinned_parent_event_ids', []):
        message = dict(role='user', content=event.text)
    else:
        message = event_message(event) if state.get('presentation') else TrainHistory._message(event)
    return request['render_receipt']['all_history_tokens_masked'] and message in request['messages']


class ReadingPolicy:
    def __init__(self, journal, *, parent_speaker='Astra', discussion_policy=None):
        if discussion_policy not in (None, DISCUSSION_POLICY):
            raise ValueError('known_deep_work_discussion_policy')
        self.journal = journal
        self.parent_speaker = parent_speaker
        self.discussion_policy = discussion_policy
        self.entries = {}
        self.reviewed_parent_ids = set()
        self.completed = set()
        self.latest_reply_indices = {}
        paths = sorted((journal.root / 'records').glob('[0-9]' * 20 + '.json'))
        for path in reversed(paths):
            with path.open('rb') as stream:
                stream.seek(max(0, path.stat().st_size - 4096))
                tail = stream.read()
            metadata = json.loads(b'{' + tail[tail.rfind(b',"index":') + 1:])
            if metadata['kind'] == 'R205_CONSOLE_REPLY':
                document = self.record(metadata['index'], metadata['sha256'])['document']
                self.completed.update(item['event_id'] for item in document['source_inbox_events'])
                for item in document['source_inbox_events']:
                    self.latest_reply_indices.setdefault(item['event_id'], metadata['index'])
            if metadata['kind'] == 'R205_READING_STATE' and not hasattr(self, 'restored_index'):
                document = self.record(metadata['index'], metadata['sha256'])['document']
                if document['schema'] != POLICY or document['parent_speaker'] != parent_speaker:
                    raise ValueError('reading_state_policy_or_parent_mismatch')
                self.entries = document['entries']
                self.reviewed_parent_ids = set(document['reviewed_parent_ids'])
                self.restored_index = metadata['index']
        for identifier in self.completed:
            if (identifier in self.entries
                    and self.latest_reply_indices[identifier] > getattr(self, 'restored_index', -1)):
                self.entries[identifier]['status'] = 'REPLIED'
        journal.record('R205_READING_POLICY_ACTIVE', dict(schema=POLICY,
            parent_speaker=parent_speaker, pid=os.getpid(), discussion_policy=discussion_policy,
            minimum_substantive_exchanges=3 if discussion_policy else 2,
            module_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            ordinary_cycles_continue=True, human_sources_recreated=False))

    def record(self, index, expected_sha256=None):
        path = self.journal.root / 'records' / f'{index:020d}.json'
        record = json.loads(path.read_bytes())
        payload = {key: value for key, value in record.items() if key != 'sha256'}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
            allow_nan=False).encode()).hexdigest()
        if digest != record['sha256'] or (expected_sha256 and digest != expected_sha256):
            raise ValueError('reading_journal_source_hash_mismatch')
        return record

    def save(self, reason):
        self.journal.record('R205_READING_STATE', dict(schema=POLICY, reason=reason,
            parent_speaker=self.parent_speaker, entries=deepcopy(self.entries),
            reviewed_parent_ids=sorted(self.reviewed_parent_ids)))

    def entry(self, event):
        text = event.text.removeprefix('Rohin: ')
        result = dict(source=reference(event), status='DISCUSSING',
            word_count=len(text.split()), turns=[], release=None)
        if self.discussion_policy:
            result.update(discussion_policy=self.discussion_policy, minimum_substantive_exchanges=3,
                artifact_required=True, artifact_kind='abstract' if re.search(r'\babstract\b', text, re.I) else 'reading')
        return result

    def artifact(self, entry, fields):
        turn = next((turn for turn in entry['turns']
            if str(turn['response']['record_index']) == fields.get('Artifact response')
            and turn.get('judgment', {}).get('substantive')), None)
        if turn is None:
            return dict(accepted=False, reason='artifact_requires_actual_reviewed_THINK')
        excerpts = {}
        for name in ('Artifact', 'Limitations'):
            value = fields.get(name, '')
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except ValueError:
                    return dict(accepted=False, reason='artifact_excerpt_invalid_encoding')
            if not isinstance(value, str) or not value:
                return dict(accepted=False, reason='artifact_and_limitations_required')
            excerpts[name] = value
        record = self.record(turn['response']['record_index'], turn['response']['record_sha256'])
        raw = record['document']['response']['raw']
        word_count = len(excerpts['Artifact'].split())
        maximum = 150 if entry.get('artifact_kind') == 'abstract' else 600
        valid = (excerpts['Artifact'] != excerpts['Limitations']
            and all(value in raw for value in excerpts.values()) and 0 < word_count <= maximum)
        return dict(accepted=valid, reason='source_bound_artifact' if valid else 'artifact_missing_or_over_word_limit',
            response=deepcopy(turn['response']), word_count=word_count, word_limit=maximum,
            artifact_sha256=hashlib.sha256(excerpts['Artifact'].encode()).hexdigest(),
            limitations_sha256=hashlib.sha256(excerpts['Limitations'].encode()).hexdigest(),
            semantic_correctness_claimed=False)

    def observe(self, incoming, seen):
        from gpu.orch_r206_pinned_messages import rohin_events
        human_sources = {event.event_id: event for event in rohin_events(incoming)}
        for event in human_sources.values():
            identifier = event.event_id
            if identifier in self.entries or identifier in self.completed or identifier in seen:
                continue
            text = event.text.removeprefix('Rohin: ')
            if is_reading(text):
                self.entries[identifier] = self.entry(event)
                self.save('GENUINE_NEW_READING_CLASSIFIED')
        for event in incoming:
            if event.event_id in self.reviewed_parent_ids:
                continue
            fields = parent_fields(event, self.parent_speaker)
            if not fields:
                continue
            identifier = 'parent:inbox:' + fields['Reading']
            if ('Rework reading' in fields and self.discussion_policy
                    and identifier in self.completed and identifier in human_sources
                    and self.entries.get(identifier, {}).get('status') not in ('DISCUSSING', 'RELEASED')):
                self.entries[identifier] = self.entry(human_sources[identifier])
                self.entries[identifier].update(rework_parent_source=reference(event),
                    revision_of_reply_index=self.latest_reply_indices[identifier])
                self.reviewed_parent_ids.add(event.event_id)
                self.save('PARENT_REQUESTED_WORKED_REVISION_OF_GENUINE_HUMAN_SOURCE')
            entry = self.entries.get(identifier)
            if not entry or entry['status'] != 'DISCUSSING':
                continue
            if 'Judgment' not in fields and 'Release reading' not in fields:
                continue
            self.reviewed_parent_ids.add(event.event_id)
            judgment = self.judge(entry, event, fields) if 'Judgment' in fields else None
            accepted = [turn for turn in entry['turns'] if turn.get('judgment', {}).get('substantive')]
            released = False
            artifact = self.artifact(entry, fields) if entry.get('artifact_required') else None
            minimum = entry.get('minimum_substantive_exchanges', 2)
            if ('Release reading' in fields and len(accepted) >= minimum
                    and (artifact is None or artifact['accepted'])):
                latest_finished = max(turn['finished_unix'] for turn in accepted)
                if Path(event.source_id).stat().st_mtime >= latest_finished:
                    entry['status'] = 'RELEASED'
                    entry['release'] = reference(event)
                    if artifact is not None:
                        entry['artifact'] = artifact
                    released = True
            self.journal.record('R205_READING_PARENT_RECEIPT', dict(schema=POLICY,
                reading_source=entry['source'], parent_source=reference(event),
                section=fields.get('Section'), judgment=judgment,
                release_requested='Release reading' in fields, release_accepted=released,
                accepted_exchange_count=len(accepted), minimum_substantive_exchanges=minimum,
                artifact=artifact, ordinary_cycles_continue=True))
            self.save('ACTUAL_PARENT_JUDGMENT_OR_RELEASE')

    def judge(self, entry, event, fields):
        response_index = fields.get('Child response', '')
        turn = next((item for item in entry['turns']
            if str(item['response']['record_index']) == response_index), None)
        reason = 'unbound_child_THINK_or_section'
        if turn and fields.get('Section') == turn['section']:
            response = self.record(turn['response']['record_index'], turn['response']['record_sha256'])
            raw = response['document']['response']['raw']
            restatement, change = fields.get('Restatement', ''), fields.get('Behavior change', '')
            source_bound = (restatement and change and restatement != change
                and restatement in raw and change in raw
                and Path(event.source_id).stat().st_mtime >= turn['finished_unix'])
            substantive = bool(source_bound and fields.get('Judgment') == 'substantive')
            reason = 'substantive' if substantive else 'needs_work_or_unbound_child_excerpts'
            judgment = dict(parent_source=reference(event), substantive=substantive,
                restatement=restatement, concrete_behavior_change=change, reason=reason)
            turn['judgment'] = judgment
            return judgment
        return dict(parent_source=reference(event), substantive=False, reason=reason)

    def pending_ids(self):
        return {identifier for identifier, entry in self.entries.items() if entry['status'] == 'DISCUSSING'}

    def ready(self, event, seen):
        if event.event_id in self.entries:
            return self.entries[event.event_id]['status'] == 'RELEASED'
        if event.event_id in self.completed:
            return False
        return event.event_id not in seen

    def instruction(self):
        identifiers = [identifier.removeprefix('parent:inbox:') for identifier in self.pending_ids()]
        if not identifiers:
            return ''
        return ('\nReading discussion (not a final console reply) for genuine source IDs: '
            + ', '.join(sorted(identifiers)) + '. Consider actual parent guidance, restate the reading '
            'concretely in your own words, and choose a concrete behavior change. Ordinary cycles '
            'and ordinary human replies continue; do not wait for a parent or claim completion. '
            'Each task keeps its recorded minimum (three for new deep-work tasks) of substantive '
            'parent-child THINK exchanges, then an explicit source-bound parent release. '
            'Deep-work release requires your actual artifact and evidence limitations; an abstract '
            'must be at most 150 words. Supplied words are never your targets.')

    def capture_think(self, request, request_origin, response, response_origin):
        history = [TrainEvent(**raw) for raw in request['resume_state']['state']['history']['events']]
        for identifier in sorted(self.pending_ids()):
            entry = self.entries[identifier]
            reading = next((event for event in history if event.event_id == identifier), None)
            if reading is None or reading.source_sha256 != entry['source']['source_sha256'] or not rendered(reading, request):
                continue
            used = {turn['parent_guidance']['event_id'] for turn in entry['turns']}
            after = max((turn['finished_unix'] for turn in entry['turns']), default=0)
            candidates = []
            for event in history:
                if event.event_id in used:
                    continue
                fields = parent_fields(event, self.parent_speaker)
                if not fields or 'parent:inbox:' + fields['Reading'] != identifier or fields.get('Section') not in ('1', '2', '3', '4'):
                    continue
                published = Path(event.source_id).stat().st_mtime
                if published >= after and rendered(event, request):
                    candidates.append((published, event, fields))
            if not candidates:
                continue
            unused_time, parent, fields = max(candidates, key=lambda candidate: candidate[0])
            entry['turns'].append(dict(section=fields['Section'], parent_guidance=reference(parent),
                request=deepcopy(request_origin), response=deepcopy(response_origin),
                finished_unix=response['finished_unix'], judgment={}))
            self.save('ACTUAL_MASKED_PARENT_CHILD_THINK_EXCHANGE')

    def mark_replied(self, event):
        self.completed.add(event.event_id)
        latest = max((self.journal.root / 'records').glob('[0-9]' * 20 + '.json'))
        record = self.record(int(latest.stem))
        if (record['kind'] == 'R205_CONSOLE_REPLY'
                and event.event_id in {item['event_id'] for item in record['document']['source_inbox_events']}):
            self.latest_reply_indices[event.event_id] = record['index']
        if event.event_id in self.entries:
            self.entries[event.event_id]['status'] = 'REPLIED'
            self.save('READING_CONSOLE_REPLY_RECORDED')

    def reply_evidence(self, event):
        entry = self.entries.get(event.event_id)
        if entry is None:
            return None
        return dict(policy=POLICY, reading_source=deepcopy(entry['source']),
            parent_release=deepcopy(entry['release']),
            minimum_substantive_exchanges=entry.get('minimum_substantive_exchanges', 2),
            revision_of_reply_index=entry.get('revision_of_reply_index'), artifact=deepcopy(entry.get('artifact')),
            substantive_exchanges=[deepcopy(turn) for turn in entry['turns']
                if turn.get('judgment', {}).get('substantive')])

    def reply_instruction(self, event):
        entry = self.entries.get(event.event_id, {})
        if 'revision_of_reply_index' not in entry:
            return ''
        return ('\nThis is a worked revision of your earlier reply to the same genuine human message. '
            'Begin with "Worked revision:". Give your own completed artifact and evidence limits; '
            'do not claim the human sent a new message or claim outcomes that have not been observed.')
