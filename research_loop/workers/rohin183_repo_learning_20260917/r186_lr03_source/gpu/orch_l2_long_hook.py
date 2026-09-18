"""LONG-only adapter from shared training callbacks to sparse parent policy."""

from hashlib import sha256
import json
from pathlib import Path

from organism_v6.orch_l2_long_parent import LongParent, public_text


class SharedLongHook:
    def __init__(self, root, cycle, tokenizer, transport, emit):
        self.root = Path(root)
        self.cycle = cycle
        self.parent = LongParent(lambda request: self._request(transport, request),
            lambda text: len(tokenizer.encode(text, add_special_tokens=False)), emit)
        self.completed = 0
        self.question_offsets = {}
        self.original_parent_decisions = []
        experience = self.root / 'LONG' / f'cycle{cycle}' / 'experience'
        preserved = experience / 'CONTINUATION_V5/PRESERVED.json'
        if preserved.exists():
            snapshot = json.loads(preserved.read_text())
            if (cycle != 1 or snapshot['episodes'] != 4 or snapshot['child_calls'] != 16
                    or snapshot['original_calls_replayed'] != 0):
                raise ValueError('original_long_continuation_accounting_required')
            for name, expected in sorted(snapshot['files'].items()):
                if not name.startswith('LONG_PARENT_EVENT_') or Path(name).name != name:
                    continue
                raw = (experience / name).read_bytes()
                if sha256(raw).hexdigest() != expected:
                    raise ValueError('original_parent_event_accounting_drift')
                event = json.loads(raw)
                if event['event'] == 'parent_decision' and event['evaluator_called']:
                    self.original_parent_decisions.append(event)
        for previous in range(1, cycle):
            directory = self.root / 'LONG' / f'cycle{previous}'
            completion = json.loads((directory / 'experience/COMPLETE.json').read_text())
            if completion['status'] != 'COMPLETE' or completion['arm'] != 'LONG':
                raise ValueError('own_completed_training_history_required')
            for index in range(completion['episodes']):
                record = json.loads((directory / 'experience' / f'EPISODE_{index + 1:02d}.json').read_text())
                self._observe(record, previous, index)
            sleep = json.loads((directory / 'sleep/COMPLETE.json').read_text())
            if sleep['status'] != 'COMPLETE' or sleep['arm'] != 'LONG':
                raise ValueError('own_completed_sleep_history_required')
            self.parent.observe_sleep(cycle=previous, metrics=dict(scope='training', values={
                'updates': sleep['updates'], 'unchanged_weights': sleep['unchanged'],
                'no_update': sleep['updates'] == 0, 'qualified_rows': completion['admitted_rows']}))

    @staticmethod
    def _request(transport, request):
        result = transport(dict(kind='long_coach', long_request=request))
        if result.get('error'):
            raise RuntimeError('long_parent_transport_failed_no_canned_fallback')
        return result

    def __call__(self, payload):
        allowed = {'kind', 'turn', 'task', 'public_messages', 'prior_parent_messages',
                   'learner', 'child_question'}
        if set(payload) - allowed or payload.get('kind') != 'coach':
            raise ValueError('shared_training_coach_payload_only')
        learner = payload['learner']
        allowed_learner = {'cycle', 'completed_experience_episodes', 'successful_experience_episodes',
                           'previous_admitted_rows', 'recent_failures', 'previous_last_responses',
                           'algorithm', 'readout_visibility'}
        if set(learner) - allowed_learner or learner.get('readout_visibility') != 'NO_READOUT_DATA':
            raise ValueError('no_readout_scalars_in_long_parent')
        episode_index = learner['completed_experience_episodes']
        if episode_index != self.completed or learner['cycle'] != self.cycle:
            raise ValueError('long_training_episode_order_drift')
        observation = '\n'.join(public_text(message['content']) for message in payload['public_messages'])
        assistant = [message['content'] for message in payload['public_messages'] if message['role'] == 'assistant']
        new_messages = assistant[self.question_offsets.get(episode_index, 0):]
        self.question_offsets[episode_index] = len(assistant)
        questions = []
        for message in new_messages:
            for line in message.splitlines():
                stripped = line.strip()
                if stripped.upper().startswith('PARENT QUESTION:'):
                    questions.append(stripped.split(':', 1)[1].strip())
                elif '?' in stripped and ('parent' in stripped.lower() or 'coach' in stripped.lower()):
                    questions.append(stripped)
        question = payload.get('child_question', '') or '\n'.join(questions)
        result = self.parent.before_turn(cycle=self.cycle, episode_index=episode_index,
            turn=payload['turn'], observation=observation,
            question=question, metrics=dict(scope='training', values={
                'episodes': episode_index,
                'successful_episodes': learner['successful_experience_episodes'],
                'qualified_rows': learner['previous_admitted_rows']}))
        return dict(speak=bool(result['message']), message=result['message'], rationale=result['reason'],
                    long_decision=result, token_limit=256)

    def _observe(self, record, cycle, episode_index):
        responses = [capture['response']['raw'] for capture in record['captures'] if capture.get('response')]
        observation = '\n'.join(message['content'] for message in record['messages'] if message['role'] != 'assistant')
        self.parent.observe_episode(cycle=cycle, episode_index=episode_index,
            observation=observation, child_response=responses[-1] if responses else '',
            metrics=dict(scope='training', values={'episodes': 1,
                'successful_episodes': int(record['correct']),
                'generated_tokens': sum(capture['response'].get('generated_text_tokens', 0)
                                        for capture in record['captures'] if capture.get('response'))}))

    def observe_episode(self, record):
        self._observe(record, self.cycle, self.completed)
        for capture in record['captures']:
            if capture.get('response'):
                self.parent.record_exposure(cycle=self.cycle, messages=[entry['message']
                    for entry in capture['parent_messages'] if entry.get('speak') and entry.get('message')])
        self.completed += 1

    def distill_cycle(self):
        result = self.parent.distill_cycle(self.cycle)
        if self.original_parent_decisions:
            originals = {event['request_sha256']: event for event in self.original_parent_decisions}
            current = [event for event in self.parent.records if event['cycle'] == self.cycle
                       and event['evaluator_called']]
            cached = [event for event in current if event['request_sha256'] in originals]
            fresh = [event for event in current if event['request_sha256'] not in originals]
            original_seconds = sum(event['elapsed_seconds'] for event in originals.values())
            original_errors = sum(event['decision'] == 'backend_error' for event in originals.values())
            result['elapsed_parent_seconds'] = original_seconds + sum(event['elapsed_seconds'] for event in fresh)
            result['backend_errors'] += original_errors
            result['recovery_accounting'] = dict(scope='operator_cost_receipts_not_parent_context',
                original_request_seconds=original_seconds, original_backend_errors=original_errors,
                cached_request_seconds=sum(event['elapsed_seconds'] for event in cached),
                cached_request_count=len(cached), cached_provider_calls=0,
                original_decisions=self.original_parent_decisions,
                elapsed_parent_seconds_includes_original_requests=True)
        return result


def build_parent(*, root, cycle, tokenizer, transport, emit):
    return SharedLongHook(root, cycle, tokenizer, transport, emit)
