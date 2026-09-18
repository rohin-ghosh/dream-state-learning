"""Prospective outcome-driven guidance; observations are not learning claims."""

from copy import deepcopy


SCHEMA = 'R189_OUTCOME_ALLOCATION_V1'
WINDOW = 3
COUNTS = ('requested', 'evaluated', 'successes', 'quality_accepted', 'repeats',
          'cached', 'unknown', 'not_dispatched')
STAGES = ('THINK', 'ACT', 'LEARN')
PARENT_STOP_CHECK = (
    'Should you keep thinking, or are you better off with new data? In a new environment '
    'or with sustained observed failure, encourage guided exploration, meta-thinking about '
    'the approach and wider hypotheses. With repeated actual success, encourage holding '
    'the successful method, acting again with small changes, and consolidating it in the '
    'child\'s own working state. If data is redundant, think more or reduce guess volume. '
    'Unknown feedback is not failure or success; process exit alone is not task success. '
    'Do not supply answers, captions, or a compulsory recurring template.')


def counts(**values):
    result = dict.fromkeys(COUNTS, 0)
    result.update(values)
    validate_counts(result)
    return result


def validate_counts(value):
    if (type(value) is not dict or set(value) != set(COUNTS)
            or any(type(number) is not int or number < 0 for number in value.values())
            or value['requested'] != sum(value[key] for key in (
                'evaluated', 'cached', 'unknown', 'not_dispatched'))
            or value['successes'] > value['evaluated']
            or value['quality_accepted'] > value['evaluated']
            or value['repeats'] > value['quality_accepted']
            or value['successes'] + value['repeats'] > value['evaluated']):
        raise ValueError('invalid_observed_outcome_counts')


def validate_tokens(value):
    if (type(value) is not dict or set(value) != set(STAGES)
            or any(type(number) is not int or number < 0 for number in value.values())):
        raise ValueError('actual_stage_token_counts_required')


def rates(value):
    denominator = value['evaluated']
    return dict(evaluated=denominator,
        success_rate=value['successes'] / denominator if denominator else None,
        quality_acceptance_rate=value['quality_accepted'] / denominator if denominator else None,
        repeat_rate=value['repeats'] / denominator if denominator else None)


def sum_counts(rows):
    return {key: sum(row[key] for row in rows) for key in COUNTS}


class OutcomeAllocation:
    def __init__(self, state=None):
        self.environments = {}
        if state is None:
            return
        if (type(state) is not dict or set(state) != {'schema', 'environments'}
                or state['schema'] != SCHEMA or type(state['environments']) is not dict):
            raise ValueError('invalid_outcome_allocation_state')
        for environment, entry in state['environments'].items():
            self._environment(environment)
            if (type(entry) is not dict or set(entry) != {'cycles', 'totals', 'recent'}
                    or type(entry['cycles']) is not int or entry['cycles'] < 1
                    or type(entry['recent']) is not list
                    or len(entry['recent']) != min(WINDOW, entry['cycles'])):
                raise ValueError('invalid_outcome_environment_state')
            validate_counts(entry['totals'])
            for row in entry['recent']:
                validate_counts(row)
            recent = sum_counts(entry['recent'])
            if any(recent[key] > entry['totals'][key] for key in COUNTS):
                raise ValueError('outcome_totals_below_recent_counts')
            if entry['cycles'] <= WINDOW and recent != entry['totals']:
                raise ValueError('outcome_totals_disagree_with_full_window')
        self.environments = deepcopy(state['environments'])

    @staticmethod
    def _environment(environment):
        if type(environment) is not str or not environment.strip() or len(environment.encode()) > 2048:
            raise ValueError('bounded_environment_identifier_required')

    def snapshot(self):
        return dict(schema=SCHEMA, environments=deepcopy(self.environments))

    def guidance(self, environment):
        self._environment(environment)
        entry = self.environments.get(environment, dict(cycles=0, totals=counts(), recent=[]))
        recent = entry['recent']
        evidence = sum_counts(recent)
        latest = recent[-1] if recent else counts()
        observed_cycles = sum(row['evaluated'] > 0 for row in recent)
        success_cycles = sum(row['successes'] > 0 for row in recent)
        if not recent:
            mode = 'GUIDED_EXPLORATION'
        elif not latest['evaluated'] and not latest['cached']:
            mode = 'UNOBSERVED_OUTCOME'
        elif (latest['cached'] or latest['repeats']) and not latest['successes']:
            mode = 'REDUNDANT_DATA'
        elif observed_cycles < 2:
            mode = 'GUIDED_EXPLORATION'
        elif latest['successes'] and success_cycles >= 2:
            mode = 'CONSOLIDATE_SUCCESS'
        elif not evidence['successes']:
            mode = 'SUSTAINED_FAILURE'
        else:
            mode = 'ASSESS_EVIDENCE'
        instructions = {
            'GUIDED_EXPLORATION': 'This environment is new or evidence is sparse. Use guided exploration: '
                'think about how to succeed here, consider wider hypotheses, then choose an informative attempt.',
            'UNOBSERVED_OUTCOME': 'No evaluated outcome arrived for the last attempt. Inspect the missing '
                'feedback; do not treat silence, an execution receipt or a child claim as task success or failure. '
                'Do not blindly retry an unknown dispatch.',
            'REDUNDANT_DATA': 'Recent output repeated existing data. Think about a different test or reduce '
                'guess volume. Retain useful methods, not identical answers; duplicates do not earn new progress.',
            'CONSOLIDATE_SUCCESS': 'Repeated observed success supports trying the successful method again '
                'with small changes. Prefer acting and consolidating now: carry the useful method, its evidence '
                'and uncertainty in your own working state so sleep can strengthen it. Do not copy old answers.',
            'SUSTAINED_FAILURE': 'Success has not been observed across repeated evaluated attempts. Spend '
                'more thought on the approach and effort allocation; consider wider hypotheses and an '
                'informative test rather than mechanically repeating failures.',
            'ASSESS_EVIDENCE': 'Outcomes are mixed. Reconsider the uncertainty and whether more thinking or '
                'new data would resolve it. Make a gradual change; preserve what the actual evidence supports.',
        }
        return dict(schema=SCHEMA, mode=mode, think_segments_budget=1 if mode == 'CONSOLIDATE_SUCCESS' else 3,
            instruction=instructions[mode] + ' You may choose to act earlier. Small samples do not establish '
                'a general explanation; this is an effort-allocation heuristic, not proof of learning.',
            evidence=dict(recent=evidence, lifetime=deepcopy(entry['totals']),
                          observed_cycles=observed_cycles, success_cycles=success_cycles),
            rates=dict(recent=rates(evidence), lifetime=rates(entry['totals'])))

    def record(self, environment, observation, *, cycle_metrics=None):
        self._environment(environment)
        validate_counts(observation)
        if cycle_metrics is not None:
            validate_tokens(cycle_metrics)
        entry = self.environments.setdefault(environment, dict(cycles=0, totals=counts(), recent=[]))
        entry['cycles'] += 1
        entry['totals'] = sum_counts((entry['totals'], observation))
        entry['recent'] = (entry['recent'] + [deepcopy(observation)])[-WINDOW:]
        wake_tokens = None if cycle_metrics is None else cycle_metrics['THINK'] + cycle_metrics['ACT']
        all_tokens = None if cycle_metrics is None else sum(cycle_metrics.values())
        return dict(schema=SCHEMA, environment=environment, cycle=entry['cycles'],
            observation=deepcopy(observation), stage_tokens=deepcopy(cycle_metrics),
            think_token_share=cycle_metrics['THINK'] / wake_tokens if wake_tokens else None,
            think_share_including_learn=cycle_metrics['THINK'] / all_tokens if all_tokens else None,
            guess_volume=observation['requested'], running_success_rate=rates(entry['totals'])['success_rate'],
            guidance_next=self.guidance(environment), retained_learning_claim=False)
