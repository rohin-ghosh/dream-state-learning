"""Stage1 continuous caption-game integration; FINAL is deliberately unsupported."""

from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import time

from organism_v6.orch_r124_train_history import TrainEvent
from gpu.ny_caption_action_policy import CaptionActionPolicy, valid_batch
from gpu.orch_r184_think_act_learn import consolidate, ready_to_act
from gpu.orch_r193_continuity import (
    PARENT_QUESTION, SCHEMA as CONTINUITY_POLICY, continuity_prompt,
)
from gpu.orch_r191_exploration_dataset import ExplorationDataset
from gpu.orch_r189_outcome_allocation import (
    PARENT_STOP_CHECK, SCHEMA as OUTCOME_POLICY, counts, rates, validate_counts, validate_tokens,
)


LANES = ('PARENTED', 'UNPARENTED')
SCHEMA = 'R177_CAPTION_DEVELOPMENT_V1'
STAGED_SCHEMA = 'R189_CAPTION_DEVELOPMENT_V1'
TOOLS = frozenset(('inspect_image', 'submit_caption', 'caption_batch'))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def save_once(path, value):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path and not path.is_symlink(), 'canonical_output')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = encoded(value)
    with path.open('xb') as stream:
        os.chmod(path, 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


@dataclass(frozen=True)
class DevelopmentConfig:
    lane: str
    stage_sleeps: int = 2
    selection_sleep: int = 18
    child_token_cap: int = 30000
    segment_tokens: int = 512
    parent_every_tokens: int = 5000
    parent_max_words: int = 150
    max_pending_tools: int = 8
    mode: str = 'DEVELOPMENT'
    outcome_policy: str | None = None
    outcome_window_tokens: int = 1000
    continuity_policy: str | None = None
    feedback_timeout_seconds: float = 120

    def __post_init__(self):
        require(self.mode == 'DEVELOPMENT', 'FINAL_not_implemented_or_authorized')
        require(self.lane in LANES, 'R161_two_learning_lineages_only')
        for name in ('stage_sleeps', 'selection_sleep', 'child_token_cap', 'segment_tokens',
                     'parent_every_tokens', 'parent_max_words', 'max_pending_tools'):
            require(type(getattr(self, name)) is int and getattr(self, name) > 0, 'positive_integer:' + name)
        require(self.selection_sleep == 18 and self.stage_sleeps in (2, 18), 'fixed_smoke_and_selection_sleeps')
        require(self.child_token_cap == 30000 and self.segment_tokens == 512, 'common_registered_output_budget')
        require(self.parent_every_tokens == 5000 and self.parent_max_words == 150, 'registered_parent_budget')
        require(self.max_pending_tools <= 8, 'bounded_pending_tool_queue')
        require(self.outcome_policy in (None, OUTCOME_POLICY), 'known_outcome_policy')
        require(self.continuity_policy in (None, CONTINUITY_POLICY), 'known_continuity_policy')
        require(type(self.outcome_window_tokens) is int and 1 <= self.outcome_window_tokens <= self.child_token_cap,
            'positive_bounded_outcome_window')
        require(type(self.feedback_timeout_seconds) in (int, float)
            and math.isfinite(self.feedback_timeout_seconds) and self.feedback_timeout_seconds > 0,
            'positive_finite_feedback_timeout')

    @property
    def parent_enabled(self):
        return self.lane == 'PARENTED'


def parse_actions(raw, *, allow_invalid_batch=False):
    require(type(raw) is str and len(raw.encode()) <= 65536, 'bounded_child_text')
    text = raw.translate(str.maketrans({'“': '"', '”': '"', '‘': "'", '’': "'"}))
    decoder = json.JSONDecoder()
    found = []
    cursor = 0
    while cursor < len(text):
        start = text.find('{', cursor)
        if start < 0:
            break
        try:
            value, size = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            cursor = start + 1
            continue
        cursor = start + size
        if type(value) is not dict or value.get('tool') not in TOOLS:
            continue
        tool = value['tool']
        if tool == 'caption_batch':
            if valid_batch(value) or allow_invalid_batch:
                found.append(value)
                require(len(found) <= 8, 'at_most_eight_actions_per_generation')
            continue
        argument = 'question' if tool == 'inspect_image' else 'text'
        if set(value) != {'tool', 'contest_id', argument}:
            continue
        if not all(type(value[name]) is str and value[name].strip() for name in ('contest_id', argument)):
            continue
        found.append(value)
        require(len(found) <= 8, 'at_most_eight_actions_per_generation')
    return found


def allocation_view(allocation):
    require(type(allocation) is dict and set(allocation) == {
        'schema', 'mode', 'instruction', 'think_segments_budget', 'rates', 'evidence'}
        and allocation['schema'] == OUTCOME_POLICY, 'public_allocation_schema')
    require(type(allocation['think_segments_budget']) is int
        and allocation['think_segments_budget'] in (1, 3), 'registered_think_budget')
    require(allocation['mode'] in ('GUIDED_EXPLORATION', 'UNOBSERVED_OUTCOME', 'REDUNDANT_DATA',
        'CONSOLIDATE_SUCCESS', 'SUSTAINED_FAILURE', 'ASSESS_EVIDENCE')
        and type(allocation['instruction']) is str and len(allocation['instruction'].encode()) <= 4096,
        'public_allocation_instruction')
    evidence = allocation['evidence']
    require(type(evidence) is dict and set(evidence) == {
        'recent', 'lifetime', 'observed_cycles', 'success_cycles'}, 'aggregate_evidence_only')
    for scope in ('recent', 'lifetime'):
        validate_counts(evidence[scope])
    require(all(type(evidence[key]) is int and 0 <= evidence[key] <= 3
        for key in ('observed_cycles', 'success_cycles')), 'bounded_observed_cycles')
    require(allocation['rates'] == {scope: rates(evidence[scope]) for scope in ('recent', 'lifetime')},
        'aggregate_rates_only')
    return deepcopy(allocation)


def parent_request(policy, *, recent_child_text, own_feedback, token_count, prior_object_turns,
                   allocation=None, continuity_policy=None):
    require(continuity_policy in (None, CONTINUITY_POLICY), 'known_continuity_policy')
    require(type(policy) is dict and set(policy) == {'version', 'model_id', 'text'}, 'versioned_parent_policy')
    require(all(type(value) is str and value.strip() for value in policy.values()), 'explicit_parent_fields')
    require(type(recent_child_text) is str and len(recent_child_text.encode()) <= 32768,
            'bounded_own_child_context')
    require(type(own_feedback) is list and len(encoded(own_feedback)) <= 32768, 'bounded_own_feedback')
    request = dict(model_id=policy['model_id'], policy_version=policy['version'],
        messages=[dict(role='system', content=policy['text'] + '\n'
            'Reply in English, at most 150 words. Offer process guidance, not captions or punchlines. '
            'Only this learner\'s work and public game feedback are supplied. Never request reference captions. '
            'A no-op is allowed. If the same mismatch has occupied three parent turns, mark it unresolved '
            'and suggest a concrete next investigation that advances the object. Do not prescribe a recurring '
            'thought format or reward length. Return JSON with guidance and object_id strings.'),
            dict(role='user', content=json.dumps(dict(recent_child_text=recent_child_text,
                own_public_feedback=own_feedback, child_tokens=token_count,
                prior_object_turns=prior_object_turns), ensure_ascii=False))])
    if allocation is not None:
        visible = allocation_view(allocation)
        request['messages'][0]['content'] += '\n' + PARENT_STOP_CHECK
        body = json.loads(request['messages'][1]['content'])
        body['outcome_allocation'] = visible
        request['messages'][1]['content'] = json.dumps(body, ensure_ascii=False)
    if continuity_policy is not None:
        request['messages'][0]['content'] += '\n' + PARENT_QUESTION
    return request


class DevelopmentBridge:
    def __init__(self, config, game, receipts, *, parent=None, policy=None, executor=None,
                 action_state=None, state=None, now=time.time):
        require(isinstance(config, DevelopmentConfig), 'registered_development_config')
        self.config, self.game = config, game
        require(callable(now), 'feedback_clock_required')
        self.now = now
        if state is not None:
            require(type(state) is dict and 'action_policy' in state, 'bridge_state_schema')
            require(action_state is None or action_state == state['action_policy'], 'action_state_mismatch')
            action_state = state['action_policy']
        self.action_policy = CaptionActionPolicy(game, action_state, outcome_policy=config.outcome_policy)
        self.root = Path(receipts).absolute()
        require(self.root.resolve() == self.root, 'private_canonical_receipts')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.parent, self.policy = parent, policy
        require((config.parent_enabled and parent is not None and policy is not None)
                or (not config.parent_enabled and parent is None and policy is None),
                'parent_required_only_on_parented_lineage')
        self.pending = []
        self.parent_pending = None
        self.next_parent_tokens = 0
        self.total_tokens = 0
        self.generation_count = 0
        self.parent_count = 0
        self.object_turns = {}
        self.feedback = []
        self.recent_raw = ''
        self.closed = False
        self.learning = False
        self.defer_tools = False
        self.deferred_action = None
        self.staged = None
        if config.outcome_policy is not None or config.continuity_policy is not None:
            manifest = getattr(game, 'manifest', None)
            require(manifest is not None and manifest.contests, 'public_development_contests_required')
            self.contest_ids = tuple(contest.contest_id for contest in manifest.contests)
            require(all(type(contest) is str and contest.strip() for contest in self.contest_ids),
                'public_contest_identifiers')
            self.staged = dict(phase='THINK', contest_id=self.contest_ids[0], cycle=0,
                think_segments_used=0, allocation=self._guidance(self.contest_ids[0]),
                transition=None, cycle_metrics=dict.fromkeys(('THINK', 'ACT', 'LEARN'), 0),
                total_stage_tokens=dict.fromkeys(('THINK', 'ACT', 'LEARN'), 0),
                window_tokens=config.outcome_window_tokens, window_new_pixels={},
                coverage_base=self._observed_coverage(), buffered_feedback=[],
                feedback_timeout_seconds=config.feedback_timeout_seconds,
                feedback_started_unix=None, feedback_deadline_unix=None)
            if config.continuity_policy is not None:
                self.staged['last_consolidation'] = None
        if state is not None:
            self._restore(state)
        self.executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix='caption-tool')
        self.parent_executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix='caption-parent')
        self.owns_executor = executor is None

    def _restore(self, state):
        expected = set(self.checkpoint())
        require(set(state) == expected and state['schema'] == self.checkpoint()['schema']
            and state['lane'] == self.config.lane and state['stage'] == 'DEVELOPMENT'
            and state['external_text_training_target'] is False, 'bridge_state_schema')
        require(state['pending_tool_ids'] == [] and state['pending_parent_id'] is None,
            'unresolved_dispatch_state_never_replayed')
        for field in ('child_tokens', 'generation_count', 'parent_count', 'next_parent_tokens'):
            require(type(state[field]) is int and state[field] >= 0, 'bridge_state_counters')
        require(state['child_tokens'] <= self.config.child_token_cap, 'child_token_budget_exceeded')
        require(type(state['object_turns']) is dict and all(type(key) is str and type(value) is int
            and value >= 0 for key, value in state['object_turns'].items()), 'bridge_state_object_turns')
        require(type(state['feedback']) is list and len(state['feedback']) <= 16
            and type(state['recent_raw']) is str and len(state['recent_raw'].encode()) <= 65536,
            'bridge_state_context')
        require(digest(state['game']) == digest(self.game.snapshot()), 'restore_game_state_first')
        if self.staged is not None:
            staged = state['staged']
            require(state['outcome_policy'] == self.config.outcome_policy and type(staged) is dict
                and set(staged) == set(self.staged) and staged['phase'] in ('THINK', 'ACT')
                and staged['contest_id'] in self.contest_ids, 'staged_state_schema')
            allocation = staged['allocation']
            require(allocation == self._guidance(staged['contest_id']), 'staged_allocation_mismatch')
            if allocation is not None:
                allocation_view(allocation)
            require(type(staged['buffered_feedback']) is list and len(staged['buffered_feedback']) <= 1,
                'bounded_buffered_feedback')
            require(staged['feedback_timeout_seconds'] == self.config.feedback_timeout_seconds
                and staged['feedback_started_unix'] is None and staged['feedback_deadline_unix'] is None,
                'resolved_feedback_budget_state')
            for document in staged['buffered_feedback']:
                event = TrainEvent.restore(document)
                require(event.actor == 'environment' and event.split == 'TRAIN'
                    and event.phase == 'feedback' and event.event_id.startswith('environment:caption:'),
                    'actual_environment_feedback_only')
            if self.config.continuity_policy is not None:
                require(state['continuity_policy'] == self.config.continuity_policy,
                    'continuity_policy_state_binding')
                last = staged['last_consolidation']
                require(last is None or type(last) is dict and last.get('status') in (
                    'UPDATED', 'ALREADY_APPLIED', 'NO_EXPLICIT_STATE_DELTA', 'REJECTED_PRIOR_STATE_RETAINED'),
                    'typed_consolidation_receipt')
            validate_tokens(staged['cycle_metrics'])
            validate_tokens(staged['total_stage_tokens'])
            require(sum(staged['total_stage_tokens'].values()) == state['child_tokens']
                and all(staged['cycle_metrics'][stage] <= staged['total_stage_tokens'][stage]
                        for stage in ('THINK', 'ACT', 'LEARN')), 'staged_token_accounting')
            require(type(staged['cycle']) is int and staged['cycle'] >= 0
                and type(staged['think_segments_used']) is int, 'staged_cycle_counters')
            require(type(staged['window_tokens']) is int
                and staged['window_tokens'] == self.config.outcome_window_tokens
                and type(staged['window_new_pixels']) is dict
                and type(staged['coverage_base']) is int and staged['coverage_base'] >= 0,
                'fixed_pixel_window_state')
            windows = max(1, math.ceil(state['child_tokens'] / self.config.outcome_window_tokens))
            require(all(type(key) is str and key.isascii() and key.isdigit() and str(int(key)) == key
                and 0 <= int(key) < windows and type(value) is int and value >= 0
                for key, value in staged['window_new_pixels'].items()), 'pixel_window_counts')
            if self.config.outcome_policy is not None:
                require(staged['coverage_base'] + sum(staged['window_new_pixels'].values()) == self._observed_coverage(),
                    'pixel_coverage_matches_observations')
            used = staged['think_segments_used']
            budget = 3 if allocation is None else allocation['think_segments_budget']
            require((staged['phase'] == 'THINK' and 0 <= used < budget and staged['transition'] is None)
                or (staged['phase'] == 'ACT' and 1 <= used <= budget
                    and staged['transition'] in ('CHILD_READY', 'BUDGET_EXHAUSTED')), 'staged_transition_state')
            self.staged = deepcopy(staged)
        self.total_tokens = state['child_tokens']
        for field in ('generation_count', 'parent_count', 'next_parent_tokens', 'object_turns', 'feedback', 'recent_raw'):
            setattr(self, field, deepcopy(state[field]))

    def _observed_coverage(self):
        if self.config.outcome_policy is None:
            return 0
        return sum(entry['totals']['successes'] for entry in
            self.action_policy.snapshot()['allocation']['environments'].values())

    def _guidance(self, contest_id):
        if self.config.outcome_policy is None:
            return None
        return allocation_view(self.action_policy.guidance(contest_id))

    def _think_budget(self):
        allocation = self.staged['allocation']
        return 3 if allocation is None else allocation['think_segments_budget']

    def pixel_readout(self):
        require(self.staged is not None, 'outcome_policy_not_enabled')
        window = self.staged['window_tokens']
        cumulative = self.staged['coverage_base']
        windows = []
        for index in range(math.ceil(self.total_tokens / window)):
            used = min(window, self.total_tokens - index * window)
            pixels = self.staged['window_new_pixels'].get(str(index), 0)
            cumulative += pixels
            windows.append(dict(window=index, child_token_start=index * window,
                child_token_end=index * window + used, child_tokens=used,
                status='FULL' if used == window else 'UNDERFILLED', new_accepted_pixels=pixels,
                new_accepted_pixels_per_child_token=pixels / used, cumulative_coverage=cumulative))
        return dict(schema='R190_CAPTION_PIXEL_WINDOWS_V1', primary_metric='NEW_ACCEPTED_PIXELS_PER_CHILD_TOKEN_WINDOW',
            window_tokens=window, provisional_developer_default=window == 1000, provisional=True, windows=windows,
            outcome_attribution='ACT_END_CHILD_TOKEN_WINDOW', cumulative_coverage=cumulative,
            new_accepted_pixels_per_child_token=(
                (cumulative - self.staged['coverage_base']) / self.total_tokens if self.total_tokens else None),
            coverage_base=self.staged['coverage_base'], coverage_scope='OBSERVED_ACTION_NEW_PIXELS',
            unobserved_archive_coverage_not_inferred=True, child_tokens=self.total_tokens)

    def _feedback_timeout(self, identifier, deadline_unix):
        path = self.root / 'tool_timeouts' / (identifier + '.json')
        if not path.exists():
            self._store('tool_timeouts', identifier, dict(schema=STAGED_SCHEMA,
                status='UNKNOWN_AFTER_DISPATCH', tool_request_id=identifier, deadline_unix=deadline_unix,
                feedback_started_unix=self.staged['feedback_started_unix'],
                feedback_timeout_seconds=self.config.feedback_timeout_seconds,
                cycle_metrics=dict(self.staged['cycle_metrics']), accepted=None, retry_allowed=False,
                sleep_allowed=False, result_not_inferred=True, physical_cancellation_claimed=False,
                provider_may_continue_until_its_guard=True))

    def _start_feedback_budget(self):
        require(self.staged['feedback_started_unix'] is None and self.staged['feedback_deadline_unix'] is None,
            'feedback_budget_never_restarted')
        started = self.now()
        require(type(started) in (int, float) and math.isfinite(started), 'finite_feedback_clock')
        self.staged.update(feedback_started_unix=started,
            feedback_deadline_unix=started + self.config.feedback_timeout_seconds)

    def _store(self, kind, identifier, value):
        return save_once(self.root / kind / (identifier + '.json'), value)

    def _single_caption(self, action, cycle_metrics):
        with self.action_policy.lock:
            try:
                result = self.game.submit_caption(action['contest_id'], action['text'])
            except Exception as error:
                result = dict(ok=False, error='UNKNOWN_AFTER_DISPATCH', error_type=type(error).__name__,
                    accepted=None)
            visible = {key: deepcopy(result[key]) for key in ('ok', 'accepted', 'status', 'q',
                'scene_fit', 'pixel_id', 'submission_id', 'rejection_reason', 'replayed', 'error',
                'error_type', 'pause_required') if key in result}
            observation = counts(requested=1, unknown=1)
            if result.get('ok', True) and type(result.get('accepted')) is bool:
                if result.get('replayed') is True:
                    observation = counts(requested=1, cached=1)
                elif not result['accepted'] or result.get('status') in ('new_pixel', 'repeat'):
                    observation = counts(requested=1, evaluated=1,
                        quality_accepted=int(result['accepted']),
                        successes=int(result['accepted'] and result.get('status') == 'new_pixel'),
                        repeats=int(result['accepted'] and result.get('status') == 'repeat'))
            visible['outcome_allocation'] = self.action_policy.allocation.record(
                action['contest_id'], observation, cycle_metrics=cycle_metrics)
            return visible

    def _tool(self, action, identifier, cycle_metrics=None):
        started = time.time()
        try:
            if action['tool'] == 'inspect_image':
                result = self.game.inspect_image(action['contest_id'], action['question'])
            elif action['tool'] == 'caption_batch':
                result = self.action_policy.submit(action,
                    cycle_metrics=cycle_metrics if self.config.outcome_policy is not None else None)
            elif self.config.outcome_policy is not None:
                result = self._single_caption(action, cycle_metrics)
            else:
                result = self.game.submit_caption(action['contest_id'], action['text'])
            status = 'RETURNED_REAL_TOOL_RESULT'
        except Exception as error:
            result = dict(error='tool_execution_failed', error_type=type(error).__name__,
                          observations=None, accepted=None)
            status = 'FAILED_NOT_AN_OBSERVATION'
        receipt = dict(schema=SCHEMA, kind='TOOL', request=action, result=result,
            started_unix=started, finished_unix=time.time(), status=status,
            child_training_target=False)
        if self.staged is not None:
            receipt.update(outcome_policy=self.config.outcome_policy, cycle_metrics=cycle_metrics)
        reference = self._store('tool_results', identifier, receipt)
        return result, reference

    def _parent(self, request, identifier):
        started = time.time()
        try:
            result = self.parent(request)
            require(type(result) is dict and set(result) == {'guidance', 'object_id'}, 'parent_reply_fields')
            guidance = result['guidance']
            require(type(guidance) is str and len(guidance.split()) <= self.config.parent_max_words,
                    'parent_word_budget')
            require(type(result['object_id']) is str and len(result['object_id']) <= 256,
                    'bounded_parent_object')
            status = 'COMPLETE' if guidance.strip() else 'NO_OP'
        except Exception as error:
            result = dict(guidance='', object_id='', error_type=type(error).__name__)
            status = 'MISSING'
        receipt = dict(schema=SCHEMA, kind='PARENT', request=request, response=result,
            status=status, started_unix=started, finished_unix=time.time(),
            speaker='Astra', child_training_target=False)
        reference = self._store('parent_results', identifier, receipt)
        return receipt, reference

    def _schedule_parent(self, recent_child_text):
        if self.config.parent_enabled and self.parent_pending is None and self.total_tokens >= self.next_parent_tokens:
            identifier = f'{self.parent_count:08d}'
            request = parent_request(self.policy, recent_child_text=recent_child_text[-8000:],
                own_feedback=self.feedback[-8:], token_count=self.total_tokens,
                prior_object_turns=dict(self.object_turns),
                allocation=None if self.staged is None else self.staged['allocation'],
                continuity_policy=self.config.continuity_policy)
            self._store('parent_requests', identifier, dict(request=request, child_tokens=self.total_tokens))
            self.parent_pending = (identifier, self.parent_executor.submit(self._parent, request, identifier))
            self.parent_count += 1
            self.next_parent_tokens = self.total_tokens + self.config.parent_every_tokens

    def flush_tools(self, *, deadline_unix=None, now=time.time):
        """Bound this wait, not the provider thread; timeout neither cancels nor retries it."""
        if self.staged is not None and self.staged['phase'] == 'AWAIT_FEEDBACK':
            require(type(deadline_unix) in (int, float) and math.isfinite(deadline_unix),
                'feedback_requires_known_deadline')
            require(len(self.pending) == 1, 'unresolved_dispatch_never_replayed')
            require(self.staged['feedback_deadline_unix'] is not None, 'feedback_budget_requires_dispatch')
            deadline_unix = min(deadline_unix, self.staged['feedback_deadline_unix'])
            self.staged['feedback_deadline_unix'] = deadline_unix
            remaining = deadline_unix - now()
            identifier, future = self.pending[0]
            if remaining <= 0:
                self._feedback_timeout(identifier, deadline_unix)
                raise ValueError('feedback_deadline_reached')
            try:
                future.result(timeout=remaining)
            except TimeoutError:
                self._feedback_timeout(identifier, deadline_unix)
                raise
            if now() >= deadline_unix:
                self._feedback_timeout(identifier, deadline_unix)
                raise ValueError('feedback_deadline_reached')
        events = []
        while self.pending and self.pending[0][1].done():
            identifier, future = self.pending[0]
            result, reference = future.result()
            self.pending.pop(0)
            self.feedback.append(result)
            self.feedback = self.feedback[-16:]
            events.append(self._event('environment', identifier, result, reference))
            if self.staged is not None:
                allocation = result.get('outcome_allocation')
                observation = None if allocation is None else allocation['observation']
                if observation is not None:
                    validate_counts(observation)
                    new_pixels = observation['successes']
                else:
                    results = [item.get('result', {}) for item in result['feedback']] if 'feedback' in result else [result]
                    new_pixels = sum(bool(item.get('ok', True)) and item.get('accepted') is True
                        and item.get('status') == 'new_pixel' and item.get('replayed') is not True for item in results)
                index = str(max(0, self.total_tokens - 1) // self.staged['window_tokens'])
                self.staged['window_new_pixels'][index] = self.staged['window_new_pixels'].get(index, 0) + new_pixels
                self._store('action_cycles', identifier, dict(schema=STAGED_SCHEMA,
                    cycle=self.staged['cycle'], contest_id=self.staged['contest_id'],
                    child_token_start=self.total_tokens - sum(self.staged['cycle_metrics'].values()),
                    child_token_end=self.total_tokens, stage_tokens=dict(self.staged['cycle_metrics']),
                    transition=self.staged['transition'], observation=observation, new_accepted_pixels=new_pixels,
                    feedback_receipt=reference, pixel_readout=self.pixel_readout(), caption_text_included=False))
        if self.staged is not None and self.staged['phase'] == 'AWAIT_FEEDBACK':
            require(len(events) == 1 and not self.pending, 'one_actual_action_receipt_required')
            self.staged.update(phase='THINK', cycle=self.staged['cycle'] + 1,
                think_segments_used=0, transition=None, cycle_metrics=dict.fromkeys(('THINK', 'ACT', 'LEARN'), 0),
                feedback_started_unix=None, feedback_deadline_unix=None,
                allocation=self._guidance(self.staged['contest_id']))
        return events

    def before_generation(self, recent_child_text='', *, deadline_unix=None, now=time.time):
        require(not self.closed, 'bridge_closed')
        if self.staged is None:
            self._schedule_parent(recent_child_text)
        events = self.flush_tools(deadline_unix=deadline_unix, now=now)
        if self.staged is not None:
            events = [TrainEvent.restore(document) for document in self.staged['buffered_feedback']] + events
            self.staged['buffered_feedback'] = []
            self._schedule_parent(recent_child_text)
        if self.parent_pending is not None and self.parent_pending[1].done():
            identifier, future = self.parent_pending
            receipt, reference = future.result()
            self.parent_pending = None
            if receipt['status'] == 'COMPLETE':
                object_id = receipt['response']['object_id']
                self.object_turns[object_id] = self.object_turns.get(object_id, 0) + 1
                events.append(self._event('parent', identifier, receipt['response']['guidance'], reference))
        if self.staged is not None:
            events.append(self._stage_event())
        return events

    def _stage_event(self):
        stage = self.staged['phase']
        require(stage in ('THINK', 'ACT') and not self.learning, 'wake_stage_only')
        allocation = None if self.staged['allocation'] is None else allocation_view(self.staged['allocation'])
        if stage == 'THINK':
            instruction = ('THINK: Consider the actual feedback and choose a direction and guess count. '
                'No tools execute during THINK. To act early, write Ready to act on its own line '
                'or the JSON object {"ready_to_act":true}. Otherwise ACT follows the thinking budget. '
                f'Thinking segments remaining: {self._think_budget() - self.staged["think_segments_used"]}.')
        else:
            instruction = ('ACT: Send exactly one tool JSON object: caption_batch with contest_id, direction, '
                'count and captions; submit_caption with contest_id and text; or inspect_image with contest_id '
                'and question. Only ACT dispatches tools. Each caption receives its actual feedback before '
                'the next THINK. An unknown result is not success or failure and is never automatically retried. '
                f'Transition: {self.staged["transition"]}.')
        if self.config.continuity_policy is not None:
            if stage == 'THINK':
                instruction = continuity_prompt('THINK', think_remaining=(
                    self._think_budget() - self.staged['think_segments_used'])) + '\n' + instruction
            else:
                instruction = ('ACT: Deliberately continue the approach chosen in your last THINK. '
                    'Check in one line whether this action incorporates the change you chose. '
                    'Preserve useful work; do not restart merely because another cycle or sleep occurred. '
                    'If useful, update a POSSIBILITY, EXPERIMENT or STANDING PRACTICE in your own text '
                    'with its evidence and uncertainty, or retain an unfinished Next intention. '
                    'These are revisable judgments, not verified facts; no fixed block is required. '
                    'Use only the caption JSON tools below.\n' + instruction)
            last = self.staged['last_consolidation']
            if last is not None and last['status'] == 'REJECTED_PRIOR_STATE_RETAINED':
                instruction += '\nYour state edit was rejected; prior state is retained: ' + last['reason']
        text = instruction
        if allocation is not None:
            text += '\nAllocation applies only to contest ' + self.staged['contest_id'] + ': ' + json.dumps(
                allocation, ensure_ascii=False, sort_keys=True)
        text += ('\nThe primary readout is NEW ACCEPTED PIXELS per child-token window and cumulative coverage, '
            'not acceptance-rate maximization or a single funniest caption. Keep bounded breadth and '
            'small informative variations even while consolidating a useful method; duplicates are not progress.')
        return TrainEvent(event_id=f'environment:caption:r189:{self.generation_count}:{stage}',
            actor='environment', split='TRAIN', phase='experience', episode_id='continual_stream',
            source_id='runtime:r189:caption:' + stage, source_sha256=digest(text),
            origin='TRAIN_COLLECTION', text=text)

    @contextmanager
    def learning_phase(self):
        require(not self.learning and not (self.staged is not None and self.pending),
            'learn_requires_resolved_action')
        self.learning = True
        try:
            yield
        finally:
            self.learning = False

    @contextmanager
    def native_generation(self):
        require(not self.defer_tools and self.deferred_action is None, 'one_native_generation_at_a_time')
        self.defer_tools = True
        try:
            yield
            if self.deferred_action is not None:
                action, identifier, metrics = self.deferred_action
                require(len(self.pending) == 1 and self.pending[0][0] == identifier,
                    'committed_action_matches_pending_request')
                self._start_feedback_budget()
                self.pending[0] = (identifier, self.executor.submit(self._tool, action, identifier, metrics))
        finally:
            self.defer_tools = False
            self.deferred_action = None

    def _event(self, actor, identifier, value, reference):
        text = value if type(value) is str else json.dumps(value, ensure_ascii=False, sort_keys=True)
        return TrainEvent(event_id=f'{actor}:caption:{identifier}', actor=actor, split='TRAIN',
            phase='feedback' if actor == 'environment' else 'experience',
            episode_id='continual_stream', source_id=reference['path'],
            source_sha256=reference['sha256'], origin='TRAIN_COLLECTION', text=text)

    def after_generation(self, response):
        require(type(response) is dict and type(response.get('raw')) is str, 'actual_native_response')
        tokens = response.get('token_ids')
        require(type(tokens) is list and all(type(token) is int and token >= 0 for token in tokens),
                'actual_generated_token_ids')
        require(self.staged is None or self.staged['phase'] != 'AWAIT_FEEDBACK',
            'await_actual_feedback_before_generation')
        self.total_tokens += len(tokens)
        self.recent_raw = response['raw']
        require(self.total_tokens <= self.config.child_token_cap, 'child_token_budget_exceeded')
        generation = self.generation_count
        self.generation_count += 1
        if self.staged is not None:
            self._after_staged_generation(response, generation)
            return
        for ordinal, action in enumerate(parse_actions(response['raw'])):
            identifier = f'{generation:08d}_{ordinal:02d}'
            if len(self.pending) >= self.config.max_pending_tools:
                self._store('tool_rejections', identifier, dict(action=action, reason='pending_queue_full',
                    model_called=False, at_child_tokens=self.total_tokens))
                continue
            self._store('tool_requests', identifier, dict(action=action, child_tokens=self.total_tokens))
            self.pending.append((identifier, self.executor.submit(self._tool, action, identifier)))

    def _after_staged_generation(self, response, generation):
        stage = 'LEARN' if self.learning else self.staged['phase']
        self.staged['cycle_metrics'][stage] += len(response['token_ids'])
        self.staged['total_stage_tokens'][stage] += len(response['token_ids'])
        self._store('stage_events', f'{generation:08d}', dict(schema=STAGED_SCHEMA,
            stage=stage, cycle=self.staged['cycle'], contest_id=self.staged['contest_id'],
            generated_tokens=len(response['token_ids']), total_child_tokens=self.total_tokens,
            cycle_metrics=dict(self.staged['cycle_metrics']), caption_text_included=False))
        if stage == 'LEARN':
            return
        if stage == 'THINK':
            self.staged['think_segments_used'] += 1
            ready = ready_to_act(response['raw'])
            try:
                decision = json.loads(response['raw'])
            except (ValueError, TypeError):
                decision = None
            ready_json = (type(decision) is dict and set(decision) == {'ready_to_act'}
                and decision['ready_to_act'] is True)
            ready = not response.get('truncated', False) and (ready or ready_json)
            if ready or self.staged['think_segments_used'] >= self._think_budget():
                self.staged.update(phase='ACT', transition='CHILD_READY' if ready else 'BUDGET_EXHAUSTED')
            return
        identifier = f'{generation:08d}_00'
        try:
            actions = parse_actions(response['raw'], allow_invalid_batch=True)
        except ValueError:
            actions = []
        valid = len(actions) == 1 and actions[0].get('contest_id') in self.contest_ids
        metrics = dict(self.staged['cycle_metrics'])
        self._store('tool_requests', identifier, dict(action=actions[0] if valid else None,
            raw=response['raw'], child_tokens=self.total_tokens, cycle_metrics=metrics,
            outcome_policy=self.config.outcome_policy, transition=self.staged['transition']))
        self.staged['phase'] = 'AWAIT_FEEDBACK'
        if not valid:
            self._start_feedback_budget()
            result = dict(ok=False, error='one_public_contest_action_required', dispatched=False,
                accepted=None, observations=None)
            reference = self._store('tool_rejections', identifier, dict(result=result,
                status='NOT_DISPATCHED', cycle_metrics=metrics, child_training_target=False))
            future = Future()
            future.set_result((result, reference))
        else:
            self.staged['contest_id'] = actions[0]['contest_id']
            if self.defer_tools:
                self.deferred_action = (actions[0], identifier, metrics)
                future = Future()
            else:
                self._start_feedback_budget()
                future = self.executor.submit(self._tool, actions[0], identifier, metrics)
        self.pending.append((identifier, future))

    def generate(self, native_generate, messages, **arguments):
        require(self.staged is None or self.staged['phase'] != 'AWAIT_FEEDBACK',
            'await_actual_feedback_before_generation')
        require(self.total_tokens + arguments['max_new_tokens'] <= self.config.child_token_cap,
                'reserve_full_generation_before_call')
        response = native_generate(messages, **arguments)
        self.after_generation(response)
        return response

    def checkpoint(self):
        state = dict(schema=SCHEMA, lane=self.config.lane, child_tokens=self.total_tokens,
            generation_count=self.generation_count, parent_count=self.parent_count,
            next_parent_tokens=self.next_parent_tokens, object_turns=dict(self.object_turns),
            pending_tool_ids=[identifier for identifier, unused in self.pending],
            pending_parent_id=None if self.parent_pending is None else self.parent_pending[0],
            game=self.game.snapshot(), action_policy=self.action_policy.snapshot(), feedback=self.feedback,
            recent_raw=self.recent_raw,
            external_text_training_target=False, stage='DEVELOPMENT')
        if self.staged is not None:
            state.update(schema=STAGED_SCHEMA, outcome_policy=self.config.outcome_policy,
                staged=deepcopy(self.staged))
        if self.config.continuity_policy is not None:
            state['continuity_policy'] = self.config.continuity_policy
        return deepcopy(state)

    def close(self):
        self.closed = True
        if self.owns_executor:
            self.executor.shutdown(wait=True)
            self.parent_executor.shutdown(wait=True)


class GenerationProxy:
    def __init__(self, child, bridge):
        self.child, self.bridge = child, bridge

    def __getattr__(self, name):
        return getattr(self.child, name)

    def generate(self, messages, **arguments):
        return self.bridge.generate(self.child.generate, messages, **arguments)


class JournalProxy:
    def __init__(self, journal, config):
        self.journal, self.config = journal, config

    def record(self, *arguments, **keywords):
        return self.journal.record(*arguments, **keywords)

    def read_inbox(self):
        events = self.journal.read_inbox()
        if not self.config.parent_enabled:
            require(all(event.actor != 'parent' for event in events), 'unparented_lineage_rejects_parent_inbox')
        return events


def drive_native(child, stream, journal, anchors, root, bridge, plan_path, *, completed_sleeps=0,
                 native_module=None, now=time.time, exploration_dataset=None):
    if native_module is None:
        from gpu import orch_r125_continual_native as native_module
    require(bridge.config.lane in LANES, 'both_development_lineages_learn')
    require(child.plan['segment_tokens'] == bridge.config.segment_tokens, 'same_segment_budget')
    require(child.plan['segments_per_sleep'] == 2, 'verified_two_episode_sleep_recipe')
    require(child.plan.get('presleep_variant', 'free_distillation') == 'free_distillation',
            'same_registered_replay_variant')
    proxy = GenerationProxy(child, bridge)
    journal = JournalProxy(journal, bridge.config)
    dataset = exploration_dataset
    if bridge.staged is not None and dataset is None:
        try:
            dataset_root = Path(journal.journal.root) / 'exploration'
            life_id = getattr(bridge.game, 'agent_id', 'caption-' + digest(str(Path(root).resolve()))[:24])
            dataset = ExplorationDataset(dataset_root, life_id)
        except Exception as error:
            journal.record('R191_CAPTION_EXPORT_FAILED', dict(phase='INITIALIZATION', error_type=type(error).__name__))
    capture = None

    def export_stage(saved, *, outcome=None, feedback_reference=None, late=False, status):
        if dataset is None:
            return
        try:
            request = saved['source'].get('request')
            require(type(request) is dict and type(request.get('sha256')) is str
                and type(request.get('path')) is str, 'actual_request_journal_reference_required')
            source = deepcopy(saved['source'])
            if feedback_reference is not None:
                source['feedback'] = deepcopy(feedback_reference)
            row_id = 'caption:' + request['sha256'] + ':' + saved['stage']
            row = dict(row_id=row_id + (':late-feedback' if late else ''), cycle=saved['cycle'],
                stage=saved['stage'], action=deepcopy(saved['action']), outcome=deepcopy(outcome),
                state_before=deepcopy(saved['state_before']), state_after=deepcopy(saved['state_after']),
                parent_turns=deepcopy(saved['parent_turns']), source=source,
                transition=saved['transition'], status=status,
                committed='committed' in source, stage_tokens=deepcopy(saved['stage_tokens']),
                parent_turn_scope='INCOMING_TO_THIS_GENERATION',
                continuity_policy=bridge.config.continuity_policy, outcome_policy=bridge.config.outcome_policy,
                external_text_training_target=False)
            if late:
                row['late_feedback_for'] = row_id
                row['late_feedback_only'] = True
            dataset.append(row)
        except Exception as error:
            journal.record('R191_CAPTION_EXPORT_FAILED', dict(phase=saved['stage'], cycle=saved['cycle'],
                late_feedback=late, error_type=type(error).__name__))

    def export_late(saved, future):
        try:
            outcome, reference = future.result()
        except Exception as error:
            journal.record('R191_CAPTION_EXPORT_FAILED', dict(phase='LATE_FEEDBACK', cycle=saved['cycle'],
                error_type=type(error).__name__))
            return
        export_stage(saved, outcome=outcome, feedback_reference=reference, late=True,
            status='LATE_REAL_TOOL_RECEIPT_NO_REDISPATCH')

    def recorded(kind, document):
        if bridge.config.continuity_policy is not None and kind == 'COMMITTED':
            source = next(event for event in reversed(stream.history.events) if event.actor == 'child')
            require(source.event_id == stream.rows[-1]['event_id']
                and source.source_sha256 == stream.rows[-1]['source_sha256'], 'actual_committed_child_state_source')
            bridge.staged['last_consolidation'] = consolidate(stream.history, source, preserve_status_labels=True)
            document = dict(document, state=stream.checkpoint(), continuity_policy=bridge.config.continuity_policy,
                consolidation=deepcopy(bridge.staged['last_consolidation']))
        if capture is not None:
            if kind == 'REQUEST':
                capture['state_before'] = deepcopy(document['resume_state'])
            elif kind == 'RESPONSE':
                capture['action'] = deepcopy(document['response'])
            elif kind == 'COMMITTED':
                capture['state_after'] = deepcopy(document['state'])
                capture['transition'] = bridge.staged['transition']
                capture['stage_tokens'] = dict(bridge.staged['cycle_metrics'])
        reference = journal.record(kind, document)
        if capture is not None and kind in ('REQUEST', 'RESPONSE', 'COMMITTED'):
            capture['source'][kind.lower()] = deepcopy(reference)
        return reference

    recent = bridge.recent_raw
    while now() < child.plan['hard_end_unix'] and completed_sleeps < bridge.config.stage_sleeps:
        incoming = bridge.before_generation(recent, deadline_unix=child.plan['hard_end_unix'], now=now) + journal.read_inbox()
        if not bridge.config.parent_enabled:
            require(all(event.actor != 'parent' for event in incoming), 'unparented_lineage_rejects_parent_inbox')
        if bridge.staged is None:
            stream.step(proxy.generate, child.count_tokens, journal.record, incoming=incoming)
        else:
            capture = dict(stage=bridge.staged['phase'], cycle=bridge.staged['cycle'],
                action=None, state_before=None, state_after=None, source={},
                parent_turns=[dict(asdict(event), target_loss=False) for event in incoming if event.actor == 'parent'],
                transition=bridge.staged['transition'], stage_tokens=None)
            try:
                with bridge.native_generation():
                    stream.step(proxy.generate, child.count_tokens, recorded, incoming=incoming)
            except BaseException:
                export_stage(capture, status='GENERATION_OR_COMMIT_FAILED_OUTCOME_UNOBSERVED')
                raise
            if capture['stage'] != 'ACT':
                export_stage(capture, status='COMMITTED_NO_TOOL_DISPATCH')
        recent = bridge.recent_raw
        completed_action = False
        if bridge.staged is not None and bridge.staged['phase'] == 'AWAIT_FEEDBACK':
            try:
                feedback = bridge.flush_tools(deadline_unix=child.plan['hard_end_unix'], now=now)
            except Exception:
                export_stage(capture, status='FEEDBACK_UNOBSERVED_NO_RETRY')
                if bridge.pending:
                    saved = deepcopy(capture)
                    bridge.pending[0][1].add_done_callback(lambda future, saved=saved: export_late(saved, future))
                raise
            require(not bridge.staged['buffered_feedback'], 'previous_feedback_must_be_delivered_before_action')
            bridge.staged['buffered_feedback'] = [asdict(event) for event in feedback]
            journal.record('R189_ACTION_FEEDBACK', dict(schema=STAGED_SCHEMA,
                event_ids=[event.event_id for event in feedback], state=stream.checkpoint(),
                bridge=bridge.checkpoint(), all_external_text_masked=True))
            export_stage(capture, outcome=bridge.feedback[-1], feedback_reference=dict(
                path=feedback[0].source_id, sha256=feedback[0].source_sha256), status='ACTUAL_FEEDBACK_RECEIVED')
            completed_action = True
        if not stream.sleep_due or (bridge.staged is not None and not completed_action):
            continue
        cycle = completed_sleeps + 1
        if bridge.staged is None:
            native_module.prepare_sleep(proxy, stream, journal, cycle)
        else:
            journal.record('R189_SLEEP_BOUNDARY', dict(schema=STAGED_SCHEMA, cycle=cycle,
                completed_action_cycle=bridge.staged['cycle'], extra_presleep_generation=False,
                pending_child_rows=len(stream.pending_rows()), pixel_readout=bridge.pixel_readout()))
        new_rows = stream.pending_rows()
        pending = stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + native_module.digest([row['source_sha256'] for row in new_rows])
        pending['sha256'] = native_module.digest(pending['state'])
        journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
        checkpoint = native_module.finish_sleep(child, stream, journal, anchors, root, cycle)
        completed_sleeps = cycle
        save_once(Path(root) / 'caption_game' / f'sleep_{cycle:06d}.json', bridge.checkpoint())
        native_module.fresh_readout(child, plan_path, checkpoint, cycle)
    result = dict(schema=SCHEMA, stage='DEVELOPMENT', lane=bridge.config.lane,
        completed_sleeps=completed_sleeps, target_sleeps=bridge.config.stage_sleeps,
        complete=completed_sleeps == bridge.config.stage_sleeps,
        child_tokens=bridge.total_tokens, optimizer_steps=child.optimizer_steps,
        parent_calls=bridge.parent_count, retained_learning_claim=False,
        final_launch_authorized=False, stopped_at_saved_boundary=stream.pending is None and
        stream.sleep_frontier == len(stream.rows))
    if bridge.staged is not None:
        result.update(schema=STAGED_SCHEMA, outcome_policy=bridge.config.outcome_policy,
            pixel_readout=bridge.pixel_readout())
    if bridge.config.continuity_policy is not None:
        result['continuity_policy'] = bridge.config.continuity_policy
    return result
