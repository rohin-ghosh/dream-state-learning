"""New C0 lineage only; inherited snapshot, no writes to original C2."""

import hashlib
from pathlib import Path

from gpu import r205_runtime as runtime
from organism_v6.orch_r124_train_history import TrainEvent


TRIAL = 'R216_C0_SNAPSHOT51_MATH'
DEVICE = 'GPU-d304a15c-516a-16a0-a926-a560304077cc'


def pin_reference(stream, journal):
    path = Path(__file__).resolve().parents[1] / 'context/ROHIN_C2_TRANSCRIPT.md'
    raw = path.read_bytes()
    source = hashlib.sha256(raw).hexdigest()
    event_id = 'r216:c0:historical-transcript:' + source
    if any(event.event_id == event_id for event in stream.history.events):
        return
    event = TrainEvent(event_id=event_id, actor='parent', split='TRAIN',
        text=('Astra: Historical reference transcript, pinned verbatim below. These are earlier '
            'Rohin/C2 exchanges, not new messages to C0 or instructions to impersonate either '
            'speaker. You are C0, a new snapshot51 fork; original C2 continues separately. '
            'External reference words are context only, never imported training targets.\n\n'
            + raw.decode()), source_sha256=source, phase='feedback', episode_id='continual_stream',
        source_id=str(path), origin='TRAIN_COLLECTION')
    stream.history.append(event)
    if not stream.history.pin_parent_event(event_id):
        raise ValueError('C0_historical_reference_pin_failed')
    journal.record('CONTEXT_INPUT', dict(kind='R216_C0_PINNED_HISTORICAL_REFERENCE',
        source_sha256=source, event_id=event_id, verbatim=True, training_eligible=False,
        historical_not_new_human_message=True, state=stream.checkpoint()))


def main():
    runtime.MODULE = 'gpu.r216_c0_runtime'
    runtime.DEVICES = {4: (DEVICE, '0000:ce:00.0')}
    runtime.TRIALS = (TRIAL,)
    runtime.receive_peer = lambda driver: None
    compact = runtime.compact_birth

    def compact_and_pin(stream, journal):
        compact(stream, journal)
        pin_reference(stream, journal)

    runtime.compact_birth = compact_and_pin
    runtime.main()


if __name__ == '__main__':
    main()
