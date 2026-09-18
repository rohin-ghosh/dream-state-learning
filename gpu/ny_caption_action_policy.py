"""Child-selected caption batches with gradual volume changes and real feedback."""

from copy import deepcopy
from threading import RLock

from gpu.orch_r189_outcome_allocation import (
    SCHEMA as OUTCOME_SCHEMA, OutcomeAllocation, counts, validate_tokens,
)


SCHEMA = 'R187_CAPTION_ACTION_POLICY_V1'
OUTCOME_ACTION_SCHEMA = 'R189_CAPTION_ACTION_POLICY_V1'
HELP = ('Choose a direction and guess count for this action. Send one caption_batch JSON '
    'object with tool, contest_id, direction, count, and captions. Captions must be your '
    'own generated strings, exactly count items. Start with at most 10; later increase '
    'by at most 2x, up to 100. You may reduce the count. The runtime returns each '
    'caption\'s actual acceptance/repeat feedback. Then decide whether more thinking '
    'or new data is worthwhile; redundant data may justify more thinking. Small '
    'observed differences are not automatically evidence for a general hypothesis.')


def valid_batch(action):
    return (type(action) is dict and set(action) == {'tool', 'contest_id', 'direction', 'count', 'captions'}
        and action['tool'] == 'caption_batch'
        and all(type(action[field]) is str and bool(action[field].strip())
                and len(action[field].encode()) <= 2048 for field in ('contest_id', 'direction'))
        and type(action['count']) is int and 1 <= action['count'] <= 100
        and type(action['captions']) is list and len(action['captions']) == action['count']
        and all(type(caption) is str and bool(caption.strip()) and len(caption.encode()) <= 4096
                for caption in action['captions']))


class CaptionActionPolicy:
    def __init__(self, game, state=None, *, outcome_policy=None):
        if outcome_policy not in (None, OUTCOME_SCHEMA):
            raise ValueError('unknown_caption_outcome_policy')
        self.game = game
        self.previous = {}
        self.lock = RLock()
        self.allocation = OutcomeAllocation() if outcome_policy else None
        if state is not None:
            if type(state) is not dict:
                raise ValueError('invalid_caption_action_state')
            expected = {'schema', 'previous'}
            schema = SCHEMA
            if state.get('schema') == OUTCOME_ACTION_SCHEMA and self.allocation is not None:
                expected.add('allocation')
                schema = OUTCOME_ACTION_SCHEMA
            if set(state) != expected or state.get('schema') != schema:
                raise ValueError('invalid_caption_action_state')
            if schema == OUTCOME_ACTION_SCHEMA:
                self.allocation = OutcomeAllocation(state['allocation'])
            if type(state['previous']) is not dict:
                raise ValueError('invalid_previous_caption_policy')
            for contest, previous in state['previous'].items():
                if (type(contest) is not str or type(previous) is not dict
                        or set(previous) != {'count', 'direction'} or type(previous['count']) is not int
                        or not 1 <= previous['count'] <= 100 or type(previous['direction']) is not str):
                    raise ValueError('invalid_previous_caption_policy')
            self.previous = deepcopy(state['previous'])

    def snapshot(self):
        with self.lock:
            if self.allocation is not None:
                return dict(schema=OUTCOME_ACTION_SCHEMA, previous=deepcopy(self.previous),
                            allocation=self.allocation.snapshot())
            return dict(schema=SCHEMA, previous=deepcopy(self.previous))

    def guidance(self, contest_id):
        with self.lock:
            if self.allocation is None:
                raise ValueError('outcome_policy_not_enabled')
            return self.allocation.guidance(contest_id)

    def _rejected_batch(self, action, report, cycle_metrics):
        if self.allocation is not None:
            contest = action.get('contest_id') if type(action) is dict else None
            if type(contest) is str and contest.strip() and len(contest.encode()) <= 2048:
                requested = action.get('count')
                if type(requested) is not int or not 1 <= requested <= 100:
                    requested = 0
                report['outcome_allocation'] = self.allocation.record(contest,
                    counts(requested=requested, not_dispatched=requested), cycle_metrics=cycle_metrics)
                report['schema'] = OUTCOME_ACTION_SCHEMA
        return report

    def submit(self, action, *, cycle_metrics=None):
        with self.lock:
            if cycle_metrics is not None:
                validate_tokens(cycle_metrics)
                if self.allocation is None:
                    raise ValueError('stage_metrics_require_outcome_policy')
            if not valid_batch(action):
                return self._rejected_batch(action,
                    dict(ok=False, error='invalid_caption_batch', feedback=[], help=HELP), cycle_metrics)
            contest = action['contest_id']
            previous = self.previous.get(contest)
            maximum = min(100, 2 * previous['count']) if previous else 10
            if action['count'] > maximum:
                return self._rejected_batch(action, dict(ok=False, error='batch_growth_too_large',
                    allowed_count_max=maximum, feedback=[], executed_captions=0), cycle_metrics)
            self.previous[contest] = dict(count=action['count'], direction=action['direction'])
            feedback = []
            for ordinal, caption in enumerate(action['captions'], 1):
                try:
                    result = self.game.submit_caption(contest, caption)
                except Exception as error:
                    feedback.append(dict(ordinal=ordinal, outcome='UNKNOWN_AFTER_DISPATCH',
                        error_type=type(error).__name__, accepted=None, repeat=None))
                    break
                visible = {key: deepcopy(result[key]) for key in (
                    'ok', 'accepted', 'status', 'q', 'scene_fit', 'pixel_id', 'submission_id',
                    'rejection_reason', 'replayed', 'error', 'pause_required') if key in result}
                feedback.append(dict(ordinal=ordinal, result=visible,
                    repeat=result.get('status') == 'repeat' if result.get('ok', True) else None))
                if result.get('pause_required'):
                    break
            report = dict(schema=SCHEMA, ok=len(feedback) == action['count']
                and all('result' in item and item['result'].get('ok', True) for item in feedback),
                contest_id=contest, direction=action['direction'], requested_count=action['count'],
                returned_count=len(feedback), feedback=feedback,
                next_stage='THINK', instruction='Use these observations to revise your next action; '
                'decide whether further thinking or new data is more useful.')
            if self.allocation is not None:
                observation = counts(requested=action['count'], not_dispatched=action['count'])
                for item in feedback:
                    observation['not_dispatched'] -= 1
                    result = item.get('result', {})
                    if not result.get('ok', True) or type(result.get('accepted')) is not bool:
                        observation['unknown'] += 1
                    elif result.get('replayed') is True:
                        observation['cached'] += 1
                        item['repeat'] = True
                    elif result['accepted'] and result.get('status') not in ('new_pixel', 'repeat'):
                        observation['unknown'] += 1
                    else:
                        observation['evaluated'] += 1
                        observation['quality_accepted'] += int(result['accepted'])
                        observation['successes'] += int(result['accepted'] and result['status'] == 'new_pixel')
                        observation['repeats'] += int(result['accepted'] and result['status'] == 'repeat')
                report['schema'] = OUTCOME_ACTION_SCHEMA
                report['outcome_allocation'] = self.allocation.record(contest, observation,
                    cycle_metrics=cycle_metrics)
                report['instruction'] = report['outcome_allocation']['guidance_next']['instruction']
            return report
