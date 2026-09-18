"""CPU interaction sequencer. Emits requests; deliberately has no model transport."""

import copy

from organism_v6 import orch_math_feedback_uptake as policy


class Cycle:
    def __init__(self, tasks, cycle, previous=()):
        policy.require(len(tasks) == policy.EPISODES and len({task['id'] for task in tasks}) == policy.EPISODES, 'two_unique_tasks')
        policy.require(all(task['split'] == 'TRAIN' for task in tasks), 'train_only')
        policy.require(1 <= cycle <= policy.CYCLES, 'bounded_cycle')
        self.tasks = copy.deepcopy(tasks)
        self.cycle = cycle
        self.previous = copy.deepcopy(previous)
        self.records = {task['id']: [] for task in self.tasks}
        self.plans = []
        self.events = []
        self.phase = 'experience'
        self.position = 0
        self.reserved = None
        self.failed = None

    def next_action(self):
        policy.require(not self.failed, 'terminal_failure_no_retry')
        policy.require(self.reserved is None, 'outstanding_request_no_duplicate')
        if self.phase == 'sleep':
            return dict(kind='SLEEP', cycle=self.cycle, rows=self.rows(),
                new_row_window_seconds_per_episode=60, whole_round_minimum=1,
                rehearse_all_prior_rows_once=True, preserve_seed_old_mix=True)
        if self.phase == 'complete':
            return dict(kind='FRESH_PARENT_FREE_READOUT', cycle=self.cycle, held=policy.HELD_PER_CYCLE,
                retention=policy.RETENTION if self.cycle == policy.CYCLES else 0)
        if self.phase == 'parent':
            round_number = len(self.plans) + 1
            return dict(kind='PARENT', id=f'C{self.cycle}_P{round_number}',
                payload=policy.parent_payload(self.tasks, self.records, self.cycle, round_number, self.previous))
        order = [task['id'] for task in self.tasks] if not self.plans else self.plans[-1]['order']
        task = next(task for task in self.tasks if task['id'] == order[self.position])
        return dict(kind='CHILD', id=f'C{self.cycle}_{self.phase}_{self.position}',
            task_id=task['id'], purpose=self.phase, max_new_tokens=policy.GENERATION,
            messages=policy.child_messages(task, self.records[task['id']], self.phase,
                self.plans[-1] if self.plans else None))

    def reserve(self):
        action = self.next_action()
        policy.require(action['kind'] in ('CHILD', 'PARENT'), 'only_call_reservation')
        self.reserved = copy.deepcopy(action)
        self.events.append(dict(event='RESERVED_NO_RETRY', action_sha256=policy.digest(action),
            kind=action['kind'], id=action['id']))
        return copy.deepcopy(action)

    def finish_child(self, response=None, error=None):
        policy.require(self.reserved is not None and self.reserved['kind'] == 'CHILD', 'reserved_child_required')
        action = self.reserved
        task = next(task for task in self.tasks if task['id'] == action['task_id'])
        try:
            call = policy.record(task, action['purpose'], response, error)
        except Exception:
            self.fail('invalid_child_record')
            raise
        self.records[task['id']].append(call)
        self.events.append(dict(event='CHILD_RECORDED', action_sha256=policy.digest(action), record_sha256=policy.digest(call)))
        self.reserved = None
        self.position += 1
        if self.position == policy.EPISODES:
            self.position = 0
            self.phase = 'sleep' if self.phase == 'revision' else 'parent'
        return copy.deepcopy(call)

    def finish_parent(self, plan, actual_model, transcript_receipt):
        policy.require(self.reserved is not None and self.reserved['kind'] == 'PARENT', 'reserved_parent_required')
        try:
            policy.require(actual_model == policy.STRONG, 'verified_strong_parent_required')
            policy.require(transcript_receipt['node_only'] is True and transcript_receipt['all_verified'] is True, 'node_transcript_required')
            policy.require(transcript_receipt['request_sha256'] == policy.digest(self.reserved), 'parent_request_binding')
            policy.require(transcript_receipt['plan_sha256'] == policy.digest(plan), 'parent_plan_binding')
            policy.validate_plan(plan, self.tasks)
        except Exception:
            self.fail('invalid_parent_or_unarchived_transcript')
            raise
        self.events.append(dict(event='PARENT_RECORDED', request_sha256=policy.digest(self.reserved),
            transcript_receipt=copy.deepcopy(transcript_receipt), actual_model=actual_model))
        self.plans.append(copy.deepcopy(plan))
        self.reserved = None
        self.phase = 'check' if len(self.plans) == 1 else 'revision'

    def rows(self):
        policy.require(self.phase == 'sleep' and not self.failed, 'interaction_before_write')
        return [row for task in self.tasks for row in policy.sleep_rows(task, self.records[task['id']],
            [[plan['guidance'], plan['episode_guidance'][task['id']]] for plan in self.plans])]

    def sleep_complete(self, presentations, prior_replay_complete, old_mix_complete):
        rows = self.rows()
        expected = {row['source_record_sha256'] for row in rows}
        policy.require(set(presentations) == expected, 'every_child_row_trained')
        policy.require(all(type(count) is int and count > 0 for count in presentations.values()), 'actual_write_required')
        for task in self.tasks:
            policy.require(len({presentations[row['source_record_sha256']] for row in rows if row['episode_id'] == task['id']}) == 1, 'matched_row_presentations')
        policy.require(prior_replay_complete is True and old_mix_complete is True, 'rehearsal_not_optional')
        self.events.append(dict(event='SLEEP_RECORDED', actual_presentations=dict(presentations)))
        self.phase = 'complete'

    def fail(self, reason):
        self.failed = reason
        self.events.append(dict(event='TERMINAL_FAILURE', reason=reason, outstanding=copy.deepcopy(self.reserved)))

    def snapshot(self):
        return copy.deepcopy(dict(schema=policy.SCHEMA, cycle=self.cycle, phase=self.phase,
            records=self.records, plans=self.plans, events=self.events, outstanding=self.reserved,
            failed=self.failed, planned_native_experience_calls=6, planned_parent_calls=2))
