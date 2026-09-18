"""CPU-testable continual TRAIN scheduler; no model, optimizer or shell launcher."""

import copy
import hashlib
import json
import math
import time

from organism_v6.orch_r124_train_history import CompactionRequired, TrainEvent, TrainHistory


SCHEMA = 'R125_CONTINUAL_STREAM_V1'
EXPERIMENT_SCHEMA = 'R133_CONTINUAL_EXPERIMENT_V1'
PRESLEEP_INVITATIONS = {
    'free_distillation': 'You are about to sleep. Distill from your history what you want to carry forward.',
    'reread_select': (
        'You are about to sleep. Re-read your visible history and select the passages you want '
        'to carry forward. Copy those passages verbatim rather than writing a new summary.'),
    'no_distillation': '',
    'parent_guided_distillation': (
        'You are about to sleep. Re-read the guidance your parent has supplied in this conversation '
        'and use it to distill from your history what you want to carry forward. '
        'If no parent guidance is present, choose for yourself.'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def valid_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(
        character in '0123456789abcdef' for character in value)


def experiment_binding(plan):
    seed = plan.get('seed', 0)
    require(type(seed) is int and 0 <= seed < 2**32, 'explicit_experiment_seed')
    variant = plan.get('presleep_variant', 'free_distillation')
    require(type(variant) is str and variant in PRESLEEP_INVITATIONS, 'known_presleep_variant')
    require(plan['compaction_invitation'] == PRESLEEP_INVITATIONS[variant], 'exact_posted_prompts')
    return dict(schema=EXPERIMENT_SCHEMA, seed=seed, presleep_variant=variant,
        compaction_invitation=plan['compaction_invitation'], system_prompt=plan['system_prompt'],
        birth_prompt=plan['birth_prompt'], seed_initialization='before_lora')


def validate_experiment(binding):
    require(type(binding) is dict and set(binding) == {'schema', 'seed', 'presleep_variant',
        'compaction_invitation', 'system_prompt', 'birth_prompt', 'seed_initialization'}, 'exact_experiment_binding')
    require(all(type(binding[key]) is str and binding[key].strip() for key in ('system_prompt', 'birth_prompt'))
        and binding == experiment_binding(binding), 'exact_experiment_binding')
    return binding


def verify_experiment_resume(plan, binding):
    requested = experiment_binding(plan)
    if binding is None:
        require(requested['seed'] == 0 and requested['presleep_variant'] == 'free_distillation',
                'legacy_experiment_configuration_frozen')
    else:
        require(validate_experiment(binding) == requested, 'resume_experiment_mismatch')


class ContinualStream:
    def __init__(self, history, *, context_limit, segment_tokens,
                 segments_per_sleep, deadline_unix, model_state_sha256, allow_eviction=False,
                 experiment=None):
        require(isinstance(history, TrainHistory), 'TRAIN_history_required')
        require(type(context_limit) is int and type(segment_tokens) is int
                and 0 < segment_tokens < context_limit, 'bounded_context_and_segment')
        require(type(segments_per_sleep) is int and segments_per_sleep > 0, 'positive_sleep_interval')
        require(type(deadline_unix) in (int, float) and math.isfinite(deadline_unix), 'finite_runtime_wall')
        require(type(allow_eviction) is bool, 'explicit_eviction_mode')
        require(valid_sha256(model_state_sha256), 'bound_model_state_required')
        self.history = history
        self.context_limit = context_limit
        self.segment_tokens = segment_tokens
        self.segments_per_sleep = segments_per_sleep
        self.deadline_unix = deadline_unix
        self.allow_eviction = allow_eviction
        self.model_state_sha256 = model_state_sha256
        self.rows = []
        self.sleep_frontier = 0
        self.pending = None
        self.sleep_receipts = []
        self.presentation = None
        self.experiment = copy.deepcopy(validate_experiment(experiment)) if experiment is not None else None

    def set_presentation(self, presentation, context_limit):
        from organism_v6.orch_r125_plain_context import VERSION
        require(self.pending is None and self.sleep_frontier == len(self.rows),
                'presentation_requires_saved_sleep_boundary')
        require(type(presentation) is dict and set(presentation) == {'version', 'system_prompt', 'birth_prompt'}
                and presentation['version'] == VERSION
                and all(type(value) is str and value.strip() for value in presentation.values()),
                'exact_plain_presentation')
        require(type(context_limit) is int and 16384 <= context_limit <= 32768,
                'plain_context_at_least_16k')
        self.presentation = copy.deepcopy(presentation)
        self.context_limit = context_limit

    @property
    def sleep_due(self):
        return len(self.rows) - self.sleep_frontier >= self.segments_per_sleep

    def pending_rows(self):
        return copy.deepcopy(self.rows[self.sleep_frontier:])

    def render(self, token_count):
        while True:
            try:
                return self.history.render(token_count, self.context_limit-self.segment_tokens,
                                           presentation=self.presentation)
            except CompactionRequired:
                if not self.allow_eviction:
                    raise
                frontier = self.history.visible_frontier.event_count
                if self.history.operations and self.history.operations[-1]['kind'] == 'compaction':
                    through = self.history.frontier(frontier)
                elif frontier >= len(self.history.events):
                    raise
                else:
                    through = self.history.frontier(frontier+1)
                self.history.evict_oldest(through,
                    reason='R125 explicit oldest-context removal to reserve the next segment')

    def step(self, generate, token_count, record, *, incoming=(), now=time.time):
        require(self.pending is None, 'unresolved_request_never_redispatched')
        require(now() < self.deadline_unix, 'runtime_wall')
        for event in incoming:
            require(isinstance(event, TrainEvent) and event.actor in ('parent', 'environment'),
                    'external_input_never_child_authored')
            self.history.append(event)
        rendered = self.render(token_count)
        messages = copy.deepcopy(rendered.messages)
        actual_prompt_tokens = token_count(copy.deepcopy(messages))
        require(type(actual_prompt_tokens) is int and actual_prompt_tokens >= 0
                and actual_prompt_tokens + self.segment_tokens <= self.context_limit, 'exact_prompt_budget')
        segment = len(self.rows)
        require(now() < self.deadline_unix, 'runtime_wall_after_context_preparation')
        request = dict(schema=SCHEMA, segment=segment, split='TRAIN', messages=messages,
            prompt_tokens=actual_prompt_tokens, max_new_tokens=self.segment_tokens,
            deadline_unix=self.deadline_unix, started_unix=now(),
            history_sha256=digest(self.history.checkpoint()),
            render_receipt=dict(token_count=rendered.token_count,
                all_history_tokens_masked=all(label == -100 for label in rendered.labels)),
            model_state_sha256=self.model_state_sha256, parent_wait_seconds=0, retry_allowed=False)
        self.pending = digest(request)
        record('REQUEST', dict(copy.deepcopy(request), resume_state=self.checkpoint()))
        response = generate(copy.deepcopy(messages), max_new_tokens=self.segment_tokens,
                            deadline_unix=self.deadline_unix)
        finished = now()
        receipt = dict(schema=SCHEMA, request_sha256=self.pending, response=copy.deepcopy(response),
                       finished_unix=finished, raw_saved_before_validation=True)
        record('RESPONSE', copy.deepcopy(receipt))
        require(isinstance(response, dict) and isinstance(response.get('raw'), str), 'actual_child_text')
        tokens = response.get('token_ids')
        require(isinstance(tokens, list) and 0 < len(tokens) <= self.segment_tokens
                and all(type(token) is int and token >= 0 for token in tokens), 'actual_bounded_child_tokens')
        require(type(response.get('terminal')) is bool, 'actual_EOS_flag')
        require(type(response.get('truncated')) is bool, 'actual_cap_flag')
        require(not (response['terminal'] and response['truncated']), 'EOS_and_cap_not_both')
        require(not response['truncated'] or len(tokens) == self.segment_tokens, 'cap_flag_matches_tokens')
        source_sha256 = digest(receipt)
        child_event = TrainEvent(event_id=f'child:segment:{segment}', actor='child', text=response['raw'],
            split='TRAIN', phase='experience', episode_id='continual_stream',
            source_id='response:'+self.pending, source_sha256=source_sha256, origin='TRAIN_COLLECTION')
        self.history.append(child_event)
        row = dict(segment=segment, split='TRAIN', actor='child', event_id=child_event.event_id,
            prefix=messages, target=response['raw'], token_ids=list(tokens), append_eos=False,
            prefix_loss=False, target_loss=True, source_sha256=source_sha256,
            model_state_sha256=self.model_state_sha256,
            terminal=response['terminal'], truncated=response['truncated'])
        self.rows.append(row)
        since_sleep_tokens = sum(len(item['token_ids']) for item in self.rows[self.sleep_frontier:])
        cost = dict(segment_tokens=len(tokens), prompt_tokens=actual_prompt_tokens,
            context_limit=self.context_limit, since_sleep_tokens=since_sleep_tokens,
            generation_context_tokens=actual_prompt_tokens+len(tokens),
            total_generated_tokens=sum(len(item['token_ids']) for item in self.rows),
            generation_seconds=max(0.0, finished-request['started_unix']))
        from organism_v6.orch_r125_plain_context import cost_sentence
        cost_text = cost_sentence(cost) if self.presentation else '[cost] '+json.dumps(cost, sort_keys=True)
        self.history.append(TrainEvent(event_id=f'cost:segment:{segment}', actor='environment', split='TRAIN',
            text=cost_text, source_sha256=digest(cost), phase='feedback',
            episode_id='continual_stream', source_id='cost:'+self.pending, origin='TRAIN_COLLECTION'))
        reserved = self.pending
        self.pending = None
        result = dict(segment=segment, source_sha256=source_sha256, cost=cost,
            sleep_due=self.sleep_due, continue_after_EOS=response['terminal'],
            stopped_only_by_wall=finished >= self.deadline_unix)
        try:
            record('COMMITTED', dict(result, state=self.checkpoint()))
        except BaseException:
            self.pending = reserved
            raise
        return result

    def commit_sleep(self, receipt, record):
        require(self.pending is None, 'no_sleep_during_unresolved_generation')
        require(self.sleep_frontier < len(self.rows), 'new_child_rows_required')
        expected = [row['source_sha256'] for row in self.rows[self.sleep_frontier:]]
        require(receipt.get('new_row_sha256') == expected, 'sleep_exact_new_child_frontier')
        require(receipt.get('status') == 'COMPLETE', 'sleep_must_complete')
        require(type(receipt.get('optimizer_steps')) is int and (receipt['optimizer_steps'] > 0
                or self.presentation is not None and receipt['optimizer_steps'] == 0
                and receipt.get('no_update_reason') == 'no_eligible_child_rows'
                and not receipt.get('presentations') and receipt.get('child_token_exposures') == 0
                and receipt.get('anchor_token_exposures') == 0),
                'sleep_actual_positive_optimizer_steps')
        references = receipt.get('checkpoint_sha256', {})
        require(set(references) == {'adapter', 'optimizer', 'rng'}, 'full_learning_state_receipt')
        require(all(valid_sha256(value) for value in references.values()), 'checkpoint_hashes_required')
        self.sleep_frontier = len(self.rows)
        self.sleep_receipts.append(copy.deepcopy(receipt))
        self.model_state_sha256 = digest(references)
        try:
            record('SLEEP_COMPLETE', dict(copy.deepcopy(receipt), resume_state=self.checkpoint()))
        except BaseException:
            self.pending = 'sleep:'+digest(receipt)
            raise
        return self.checkpoint()

    def checkpoint(self):
        state = dict(schema=SCHEMA, history=self.history.checkpoint(),
            context_limit=self.context_limit, segment_tokens=self.segment_tokens,
            segments_per_sleep=self.segments_per_sleep, deadline_unix=self.deadline_unix,
            allow_eviction=self.allow_eviction, rows=copy.deepcopy(self.rows),
            model_state_sha256=self.model_state_sha256,
            sleep_frontier=self.sleep_frontier, pending=self.pending,
            sleep_receipts=copy.deepcopy(self.sleep_receipts))
        if self.presentation is not None:
            state['presentation'] = copy.deepcopy(self.presentation)
        if self.experiment is not None:
            state['experiment'] = copy.deepcopy(self.experiment)
        return dict(state=state, sha256=digest(state))

    @classmethod
    def restore(cls, document, *, expected_sha256):
        state = document['state']
        require(document['sha256'] == expected_sha256 == digest(state), 'bound_stream_checkpoint')
        require(state['schema'] == SCHEMA, 'known_stream_schema')
        stream = cls(TrainHistory.restore(state['history']),
            context_limit=state['context_limit'], segment_tokens=state['segment_tokens'],
            segments_per_sleep=state['segments_per_sleep'], deadline_unix=state['deadline_unix'],
            model_state_sha256=state['model_state_sha256'],
            allow_eviction=state['allow_eviction'], experiment=state.get('experiment'))
        stream.rows = copy.deepcopy(state['rows'])
        require([row['segment'] for row in stream.rows] == list(range(len(stream.rows))), 'contiguous_child_frontier')
        require(all(row['split'] == 'TRAIN' and row['actor'] == 'child'
                    and row['prefix_loss'] is False and row['target_loss'] is True for row in stream.rows),
                'restored_child_targets_only')
        require(type(state['sleep_frontier']) is int and 0 <= state['sleep_frontier'] <= len(stream.rows),
                'valid_sleep_frontier')
        stream.sleep_frontier = state['sleep_frontier']
        stream.pending = state['pending']
        stream.sleep_receipts = copy.deepcopy(state['sleep_receipts'])
        if 'presentation' in state:
            pending, frontier = stream.pending, stream.sleep_frontier
            stream.pending, stream.sleep_frontier = None, len(stream.rows)
            stream.set_presentation(state['presentation'], stream.context_limit)
            stream.pending, stream.sleep_frontier = pending, frontier
        return stream
