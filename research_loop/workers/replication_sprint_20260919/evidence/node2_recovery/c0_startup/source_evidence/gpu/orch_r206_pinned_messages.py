import hashlib
import json
from pathlib import Path

from organism_v6.orch_r124_train_history import TrainEvent


POLICY = 'R206_VERBATIM_ROHIN_MESSAGES_V1'


def rohin_events(incoming):
    result = []
    for event in incoming:
        if event.actor != 'parent':
            continue
        try:
            raw = Path(event.source_id).read_bytes()
            message = json.loads(raw)
        except (OSError, ValueError):
            continue
        if (isinstance(message, dict) and message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1'
                and message.get('speaker') == 'Rohin' and message.get('actor') == 'parent'
                and event.event_id == 'parent:inbox:' + message.get('id', '')
                and hashlib.sha256(raw).hexdigest() == event.source_sha256
                and event.text == 'Rohin: ' + message.get('text', '')):
            result.append(event)
    return result


def pin_messages(stream, journal, events, *, include_new=False):
    known = {event.event_id for event in stream.history.events}
    added = []
    for event in events:
        if event.event_id not in known:
            if not include_new:
                continue
            stream.history.append(event)
        if stream.history.pin_parent_event(event.event_id):
            added.append(dict(event_id=event.event_id, source_sha256=event.source_sha256))
    if added:
        source_hash = hashlib.sha256(json.dumps(added, sort_keys=True).encode()).hexdigest()
        stream.history.append(TrainEvent(event_id='r206:pinned:' + source_hash, actor='environment',
            text="Runtime notice: Rohin's attributed messages are pinned verbatim across compaction. "
                 'They remain external input, never child training targets or proof of an outcome.',
            split='TRAIN', phase='feedback', episode_id='continual_stream',
            source_id='runtime:r206:pinned_messages', source_sha256=source_hash, origin='TRAIN_COLLECTION'))
        journal.record('CONTEXT_INPUT', dict(kind=POLICY, pinned=added,
            verbatim=True, training_eligible=False, state=stream.checkpoint()))
    return added
