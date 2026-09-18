"""One explicitly enabled, context-only Rohin conversation before wake resumes."""

from pathlib import Path
import json
import re
import time

from organism_v6.orch_r124_train_history import TrainEvent
from organism_v6.orch_r125_continual_stream import digest, require


SCHEMA = 'R194_CONSOLE_REFLECTION_V1'
PROMPT = (
    'Runtime status: THINK — interactive reflection with Rohin. ACT and LEARN are held: '
    'no tools will execute and no sleep or optimizer update will occur in this mode. '
    'Answer Rohin\'s latest turn directly in ordinary prose, without a fixed field block. '
    'Consider your actual recent attempts and feedback, your current judgment and approach, '
    'what changed or remains unresolved. Nothing changed is an acceptable answer. '
    'Distinguish historical observations from current environment facts; do not invent '
    'executions or outcomes. This exchange is kept as masked context, not training targets. '
    'Only a new Rohin console turn saying exactly "done" or "/resume" resumes the normal cycle.'
)


def validate_config(config):
    require(type(config) is dict and set(config) == {'schema', 'session_id'}
            and config['schema'] == SCHEMA and type(config['session_id']) is str
            and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', config['session_id']), 'versioned_console_reflection_config')
    return config


class ConsoleReflection:
    def __init__(self, child, stream, journal, config, *, environment_facts=''):
        self.config = validate_config(config)
        self.child, self.stream, self.journal = child, stream, journal
        self.session = config['session_id']
        self.environment_facts = environment_facts

    def _event(self, name, text):
        return TrainEvent(event_id=f'r194:{self.session}:{name}', actor='environment', text=text,
            split='TRAIN', phase='feedback', episode_id='continual_stream',
            source_id=f'runtime:r194:{self.session}:{name}', source_sha256=digest(text), origin='TRAIN_COLLECTION')

    def _contains(self, name):
        return any(event.event_id == f'r194:{self.session}:{name}' for event in self.stream.history.events)

    def _control(self, mode, incoming=()):
        for event in incoming:
            self.stream.history.append(event)
        self.stream.history.append(self._event(mode, 'Console reflection mode: ' + mode))
        self.journal.record('CONTEXT_INPUT', dict(schema=SCHEMA, session_id=self.session, mode=mode,
            training_eligible=False, state=self.stream.checkpoint()))
        self.journal.record('R194_MODE', dict(schema=SCHEMA, session_id=self.session, mode=mode,
            act_held=mode == 'REFLECTION', learn_held=mode == 'REFLECTION', time_unix=time.time()))

    def enter(self):
        if self._contains('RUN'):
            return False
        if not self._contains('REFLECTION'):
            require(self.stream.pending is None and not self.stream.pending_rows(),
                    'console_mode_enters_at_complete_sleep_boundary')
            self._control('REFLECTION')
        return True

    def poll_once(self):
        if not self.enter():
            return 'RESUMED'
        seen = {event.event_id for event in self.stream.history.events}
        for event in self.journal.read_inbox():
            if event.actor != 'parent' or event.event_id in seen:
                continue
            message = json.loads(Path(event.source_id).read_text())
            if message.get('schema') != 'R127_ATTRIBUTED_INBOX_V1' or message.get('speaker') != 'Rohin':
                continue
            if message['text'].strip().casefold() in ('done', '/resume'):
                self._control('RUN', incoming=(event,))
                return 'RESUMED'
            prompt = PROMPT
            if self.environment_facts:
                prompt += '\nCurrent environment facts (tools remain held): ' + self.environment_facts
            notice = self._event('turn:' + digest(event.event_id), prompt)
            result = self.stream.step(self.child.generate, self.child.count_tokens, self.journal.record,
                incoming=(event, notice), train_response=False,
                compaction_threshold=min(self.stream.context_limit * 3 // 4,
                    self.stream.context_limit - self.stream.segment_tokens))
            self.journal.record('R194_TURN', dict(schema=SCHEMA, session_id=self.session,
                parent_event_id=event.event_id, response_event_id=result['response_event_id'],
                response_sha256=result['source_sha256'], cost=result['cost'],
                stage='THINK', training_eligible=False, act_held=True, learn_held=True))
            return 'ANSWERED'
        return 'WAITING'

    def wait_until_resumed(self, *, now=time.time, pause=time.sleep):
        while now() < self.stream.deadline_unix:
            status = self.poll_once()
            if status == 'RESUMED':
                return True
            if status == 'WAITING':
                pause(min(0.25, max(0, self.stream.deadline_unix - now())))
        self.journal.record('R194_WALL_STOP', dict(schema=SCHEMA, session_id=self.session,
            act_held=True, learn_held=True, resumed=False))
        return False
