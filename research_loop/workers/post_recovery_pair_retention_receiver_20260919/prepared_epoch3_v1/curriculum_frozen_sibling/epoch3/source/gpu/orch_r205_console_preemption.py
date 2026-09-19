"""Cooperative generation checks; never interrupt optimizer work or rewind RNG."""

import time

from gpu.orch_r205_reading_policy import is_reading, reference
from gpu.orch_r206_pinned_messages import rohin_events


POLICY = 'R205_CONSOLE_PREEMPTION_V1'


class ConsoleInterrupt:
    def __init__(self, journal, stream, *, poll_seconds=0.1, clock=time.monotonic):
        self.journal = journal
        self.stream = stream
        self.poll_seconds = poll_seconds
        self.clock = clock
        self.next_poll = float('-inf')
        self.interruption = None

    def __call__(self):
        if self.interruption is not None:
            return self.interruption
        now = self.clock()
        if now < self.next_poll:
            return None
        self.next_poll = now + self.poll_seconds
        seen = {event.event_id for event in self.stream.history.events}
        incoming = [event for event in rohin_events(self.journal.read_inbox())
            if event.event_id not in seen and not is_reading(event.text.removeprefix('Rohin: '))]
        if incoming:
            self.interruption = dict(policy=POLICY, observed_unix=time.time(),
                source_inbox_events=[reference(event) for event in incoming])
        return self.interruption


def stopping_criteria(transformers, interrupt):
    class ConsoleBoundary(transformers.StoppingCriteria):
        def __call__(self, input_ids, scores, **kwargs):
            return interrupt() is not None

    return transformers.StoppingCriteriaList([ConsoleBoundary()])
