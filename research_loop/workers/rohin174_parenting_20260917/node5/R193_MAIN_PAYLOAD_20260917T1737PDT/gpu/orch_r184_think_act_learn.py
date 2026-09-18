"""Copy-only THINK/ACT wake driver using the existing child, journal and sleep."""

from dataclasses import replace
import json
from pathlib import Path
import re
import time
import unicodedata

from organism_v6.orch_r124_train_history import CompactionRequired, TrainEvent, WorkingStateSpan
from organism_v6.orch_r125_continual_stream import digest, require
from gpu.orch_r189_outcome_allocation import (
    SCHEMA as OUTCOME_SCHEMA, OutcomeAllocation, counts, validate_counts,
)
from gpu.orch_r193_continuity import SCHEMA as CONTINUITY_SCHEMA, continuity_prompt


SCHEMA = 'R184_THINK_ACT_LEARN_V1'
STATE_FIELDS = {
    'investigation': 'investigation', 'current investigation': 'investigation',
    'finding': 'finding', 'judgment': 'judgment', 'uncertainty': 'uncertainty',
    'next intention': 'next_intention', 'next intended action': 'next_intention',
    'expected consequence': 'expected_consequence', 'prediction': 'prediction',
    'open question': 'open_question', 'unresolved question': 'open_question',
    'process adjustment': 'process_adjustment', 'note': 'note',
}
FIELD = re.compile(
    r'^\s*(?:[-*]\s+)?(?:\*\*)?(?P<kind>' + '|'.join(STATE_FIELDS)
    + r')(?:\s*\[(?P<id>[A-Za-z0-9_.-]{1,80})\])?(?:\*\*)?\s*[:：]\s*(?P<text>\S.*?)\s*$',
    re.IGNORECASE)
DELETE = re.compile(r'^\s*Forget state\s*\[([A-Za-z0-9_.-]{1,80})\]\.?\s*$', re.IGNORECASE)


STATUS_FIELD = re.compile(r'^\s*(?P<label>POSSIBILITY|EXPERIMENT|STANDING PRACTICE)'
    r'\s*\[(?P<id>[A-Za-z0-9_.-]{1,80})\]\s*[:：]\s*\S.*$', re.IGNORECASE)


def validate_config(config):
    fields = {'schema', 'trial_id', 'reflection_policy', 'think_segments', 'cpu_gate_root', 'cpu_gate_sha256'}
    optional = {'outcome_policy', 'continuity_policy', 'environment_facts'}
    require(type(config) is dict and fields <= set(config) <= fields | optional,
        'exact_think_act_learn_config')
    require(config['schema'] == SCHEMA and config['reflection_policy'] in ('explicit', 'brief'),
        'known_reflection_policy')
    require(type(config['trial_id']) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', config['trial_id']),
        'bounded_trial_id')
    require(type(config['think_segments']) is int and config['think_segments'] in (1, 2, 3),
        'bounded_declared_think_segments')
    if 'outcome_policy' in config:
        require(config['outcome_policy'] == OUTCOME_SCHEMA and config['think_segments'] == 3,
                'versioned_outcome_policy_with_three_segment_ceiling')
    if 'continuity_policy' in config:
        require(config['continuity_policy'] == CONTINUITY_SCHEMA, 'versioned_continuity_policy')
    if 'environment_facts' in config:
        require(config.get('continuity_policy') == CONTINUITY_SCHEMA
            and type(config['environment_facts']) is str
            and 0 < len(config['environment_facts'].encode()) <= 2048, 'bound_environment_facts')
    require(type(config['cpu_gate_root']) is str and Path(config['cpu_gate_root']).is_absolute()
        and type(config['cpu_gate_sha256']) is str
        and re.fullmatch(r'[0-9a-f]{64}', config['cpu_gate_sha256']), 'actual_cpu_configuration')
    return config


def state_delta(source, *, preserve_status_labels=False):
    entries, deleted = [], []
    offset, fenced = 0, False
    for line in source.text.splitlines(keepends=True):
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        elif not fenced:
            matched = FIELD.fullmatch(line.rstrip('\r\n'))
            removal = DELETE.fullmatch(line.rstrip('\r\n'))
            labelled = STATUS_FIELD.fullmatch(line.rstrip('\r\n')) if preserve_status_labels else None
            if labelled:
                entries.append(WorkingStateSpan(labelled['id'], 'judgment',
                    offset + labelled.start('label'), offset + len(line.rstrip('\r\n'))))
            elif matched:
                kind = STATE_FIELDS[matched['kind'].lower()]
                entries.append(WorkingStateSpan(matched['id'] or kind, kind,
                    offset + matched.start('text'), offset + matched.end('text')))
            elif removal:
                deleted.append(removal[1])
        offset += len(line)
    return entries, deleted


def consolidate(history, source, *, preserve_status_labels=False):
    try:
        entries, deleted = state_delta(source, preserve_status_labels=preserve_status_labels)
        if not entries and not deleted:
            return dict(status='NO_EXPLICIT_STATE_DELTA', source_event_id=source.event_id)
        changed = history.update_working_state(source, entries=entries, delete=deleted)
        return dict(status='UPDATED' if changed else 'ALREADY_APPLIED',
            source_event_id=source.event_id, revision=history.working_state['revision'],
            updated_ids=[entry.id for entry in entries], deleted_ids=deleted)
    except ValueError as error:
        return dict(status='REJECTED_PRIOR_STATE_RETAINED', source_event_id=source.event_id,
                    reason=str(error))


def ready_to_act(text):
    text = unicodedata.normalize('NFKC', text)
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        elif not fenced and re.fullmatch(r'\s*(?:I am )?ready to act[.!]?\s*', line, re.IGNORECASE):
            return True
    return False


def runtime_event(trial_id, segment, stage, text):
    body = dict(schema=SCHEMA, trial_id=trial_id, segment=segment, stage=stage, text=text)
    return TrainEvent(event_id=f'r184:{trial_id}:{segment}:{stage}', actor='environment', text=text,
        split='TRAIN', phase='feedback', episode_id='continual_stream',
        source_id='runtime:r184:' + stage, source_sha256=digest(body), origin='TRAIN_COLLECTION')


def stage_prompt(stage, policy, *, think_remaining=1, continuity_policy=None, environment_facts=None):
    if continuity_policy is not None:
        require(continuity_policy == CONTINUITY_SCHEMA, 'versioned_continuity_policy')
        require(type(think_remaining) is int and think_remaining in (1, 2, 3),
                'bounded_remaining_think_segments')
        return continuity_prompt(stage, think_remaining=think_remaining, environment_facts=environment_facts)
    common = (
        'Your working state survives sleep and compaction. Update only what changed, using optional '
        'plain lines such as Investigation: ..., Judgment [name]: ..., Uncertainty: ..., '
        'Next intention: ..., Expected consequence: ..., Open question [name]: ..., '
        'Process adjustment: .... Keep these concise; omitted entries remain. To remove one '
        'explicitly write Forget state [name]. State is your assertion, not verified feedback. ')
    if stage == 'THINK':
        require(type(think_remaining) is int and think_remaining in (1, 2, 3),
            'bounded_remaining_think_segments')
        reflection = (
            'REFLECT: compare the actual result with what you expected. What changes or stays? '
            'Did you overthink, act too early, repeat an exhausted approach or lose a finding? '
            'Revisit useful older reflections. PREDICT/CHOOSE: select an attempt, its expected '
            'consequence and what it may teach. What uncertainty would more thinking resolve, '
            'and could an attempt resolve it better? Sometimes staying with an uncertainty is useful. '
            if policy == 'explicit' else
            'Reflect on the available evidence, then predict and choose your next attempt. ')
        allowance = ('You have one response for this Think stage. ' if think_remaining == 1 else
            f'You have at most {think_remaining} responses left in this Think stage. '
            'Choose whether further thinking is worth more than new data; you may act now. ')
        return ('Runtime status: THINK. ' + reflection + common + allowance
            + 'When ready, write Ready to act. '
            'Otherwise the stage budget will move to Act; that forced transition is recorded. '
            'No code written in Think is executed. No result obtained is valid.')
    if stage == 'ACT':
        return ('Runtime status: ACT. Carry your chosen intention into one actual attempt. '
            'For a calculation or program, provide a plain Python fenced block; the first code '
            'block is accepted. The CPU tool has no network or GPU. Preserve prior work. '
            'Do not claim execution until its actual receipt arrives. Failure or no feedback '
            'is a result to retain, not hide. ' + common)
    if stage == 'LEARN':
        return ('Runtime status: about to LEARN (sleep). No optimizer update has happened yet. '
            'Review the actual attempt and returned evidence or absence of feedback. '
            'What decision and unfinished work must survive? Revise your judgment, next intention '
            'and process adjustment in your own words. ' + common
            + 'Sleep trains new child responses only; parent, runtime and tool text are context, '
            'not targets. Older rows are not rehearsed.')
    raise ValueError('known_wake_or_sleep_notice')


def reflection_events(history):
    stage = None
    result = []
    for event in history.events:
        if event.actor == 'environment' and event.source_id.startswith('runtime:r184:'):
            stage = event.source_id.rsplit(':', 1)[-1]
        elif event.actor == 'child':
            if stage == 'THINK':
                result.append(event)
            stage = None
    return result


class ThinkActLearn:
    def __init__(self, child, stream, journal, config, *, executor=None, new_presentations=16,
                 outcome_reader=None):
        self.config = validate_config(config)
        self.child, self.stream, self.journal = child, stream, journal
        self.executor = executor or self._cpu
        require(type(new_presentations) is int and new_presentations in (4, 16, 32),
            'declared_copy_presentations')
        self.new_presentations = new_presentations
        self.last_response = None
        self.last_consolidation = None
        self.outcome_reader = outcome_reader
        self.allocation = None
        self.cycle_metrics = dict(THINK=0, ACT=0, LEARN=0)
        self.last_allocation = None
        self.cycle_phase = 'NOT_STARTED'
        if config.get('outcome_policy') == OUTCOME_SCHEMA:
            saved = next((event for event in reversed(stream.history.events)
                if event.actor == 'environment' and event.source_id == 'runtime:r189:outcome_allocation'), None)
            state = None
            if saved is not None:
                document = json.loads(saved.text)
                require(saved.source_sha256 == digest(document), 'bound_outcome_allocation_event')
                state = document['allocation']
            self.allocation = OutcomeAllocation(state)

    def generate_stage(self, stage, *, extra='', think_remaining=1):
        incoming = list(self.journal.read_inbox())
        if self.last_consolidation and self.last_consolidation['status'] == 'REJECTED_PRIOR_STATE_RETAINED':
            extra += ('\nYour last state edit was rejected and prior state retained: '
                      + self.last_consolidation['reason'])
        prompt = stage_prompt(stage, self.config['reflection_policy'], think_remaining=think_remaining,
            continuity_policy=self.config.get('continuity_policy'),
            environment_facts=self.config.get('environment_facts')) + extra
        if self.allocation is not None:
            guidance = self.allocation.guidance(self.config['trial_id'])
            prompt += '\nOutcome-driven allocation: ' + guidance['instruction']
        incoming.append(runtime_event(self.config['trial_id'], len(self.stream.rows), stage, prompt))

        def recorded(kind, document):
            if kind == 'COMMITTED':
                source = next(event for event in reversed(self.stream.history.events) if event.actor == 'child')
                self.last_consolidation = consolidate(self.stream.history, source,
                    preserve_status_labels=self.config.get('continuity_policy') == CONTINUITY_SCHEMA)
                document = dict(document, state=self.stream.checkpoint())
            receipt = self.journal.record(kind, document)
            if kind == 'RESPONSE':
                self.last_response = dict(kind='TRAIN_CHILD_RESPONSE', record_index=receipt['index'],
                                          record_sha256=receipt['sha256'])
            return receipt

        result = self.stream.step(self.child.generate, self.child.count_tokens, recorded, incoming=incoming)
        if self.allocation is not None:
            self.cycle_metrics[stage] += result['cost']['segment_tokens']
        self.journal.record('R184_STAGE', dict(schema=SCHEMA, trial_id=self.config['trial_id'], stage=stage,
            segment=result['segment'], source_sha256=result['source_sha256'],
            consolidation=self.last_consolidation, runtime_notice_is_target=False))
        return result

    def _cpu(self, origin):
        from gpu.orch_r153_community_transport import cpu_once
        return cpu_once(str(self.journal.root.parent), self.journal._manifest['journal_id'], origin,
            self.config['cpu_gate_sha256'], gate_root=self.config['cpu_gate_root'], start=True)

    def act(self):
        self.cycle_phase = 'ACT'
        result = self.generate_stage('ACT')
        from gpu.orch_r153_community_transport import code_route
        route, unused_report = code_route(self.stream.rows[-1]['target'])
        if route == 'CPU':
            try:
                outcome = self.executor(self.last_response)
            except Exception as error:
                outcome = dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None,
                               error_type=type(error).__name__)
        else:
            outcome = dict(status='NO_CPU_ATTEMPT' if route == 'NONE' else 'UNSUPPORTED_TOOL', executed=False)
        self.journal.record('R184_ACT', dict(schema=SCHEMA, segment=result['segment'],
            source_sha256=result['source_sha256'], origin=self.last_response, outcome=outcome))
        if outcome.get('status') != 'PUBLISHED':
            text = ('Tool status: ' + outcome['status'] + '. No successful execution is established. '
                    'An unknown dispatch is not retried automatically. Continue from the evidence available.')
            notice = runtime_event(self.config['trial_id'], len(self.stream.rows), 'TOOL_STATUS', text)
            self.stream.history.append(notice)
        if self.allocation is not None:
            self.record_outcome(outcome, dispatched=route == 'CPU')
        self.cycle_phase = 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN'
        return outcome

    def record_outcome(self, outcome, *, dispatched):
        observation = counts(requested=1, unknown=int(dispatched), not_dispatched=int(not dispatched))
        evaluation = dict(status='NO_TASK_EVALUATOR', receipt=None)
        if dispatched and self.outcome_reader is not None:
            try:
                result = self.outcome_reader(self.last_response, outcome)
                require(type(result) is dict and set(result) == {'observation', 'receipt'},
                        'explicit_task_evaluation')
                require(type(result['receipt']) is str and 0 < len(result['receipt'].encode()) <= 2048,
                        'actual_task_evaluation_receipt')
                validate_counts(result['observation'])
                observation = result['observation']
                evaluation = dict(status='TASK_EVALUATOR_RETURNED', receipt=result['receipt'])
            except Exception as error:
                evaluation = dict(status='TASK_EVALUATION_UNKNOWN', receipt=None,
                                  error_type=type(error).__name__)
        self.last_allocation = self.allocation.record(self.config['trial_id'], observation,
            cycle_metrics=self.cycle_metrics)
        self.last_allocation.update(evaluation=evaluation, volume_unit='act_opportunities',
                                    quality_metrics_applicable=False)
        document = dict(allocation=self.allocation.snapshot(), report=self.last_allocation)
        self.stream.history.append(TrainEvent(
            event_id=f'r189:{self.config["trial_id"]}:{len(self.stream.rows)}:outcome',
            actor='environment', text=json.dumps(document, sort_keys=True), split='TRAIN', phase='feedback',
            episode_id='continual_stream', source_id='runtime:r189:outcome_allocation',
            source_sha256=digest(document), origin='TRAIN_COLLECTION'))
        self.journal.record('R189_OUTCOME_CYCLE', dict(document, state=self.stream.checkpoint()))

    def wake(self):
        require(not self.stream.pending_rows(), 'copy_starts_at_completed_sleep_boundary')
        self.cycle_metrics = dict(THINK=0, ACT=0, LEARN=0)
        self.cycle_phase = 'THINK'
        budget = self.config['think_segments']
        if self.allocation is not None:
            budget = self.allocation.guidance(self.config['trial_id'])['think_segments_budget']
        for position in range(budget):
            result = self.generate_stage('THINK', think_remaining=budget - position)
            chosen = ready_to_act(self.stream.rows[-1]['target'])
            if chosen:
                break
        self.journal.record('R184_TRANSITION', dict(schema=SCHEMA, from_stage='THINK', to_stage='ACT',
            segment=result['segment'], cause='child_ready' if chosen else 'forced_stage_budget',
            child_chosen=chosen, opportunity=True, think_segments_used=position + 1,
            think_segments_budget=budget))
        return self.act()

    def prepare_sleep(self, cycle):
        if self.config.get('continuity_policy') == CONTINUITY_SCHEMA:
            require(self.cycle_phase == 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN',
                    'sleep_waits_for_complete_bounded_think_act_feedback_cycle')
        try:
            rendered = self.stream.history.render(self.child.count_tokens,
                self.stream.context_limit, presentation=self.stream.presentation)
            should_compact = rendered.token_count >= self.stream.context_limit * 3 // 4
        except CompactionRequired:
            should_compact = True
        reviewed = []
        if should_compact and self.config.get('continuity_policy') != CONTINUITY_SCHEMA:
            for event in reflection_events(self.stream.history):
                self.generate_stage('THINK', extra='\nCompaction review: revisit this exact earlier reflection '
                    'before distilling what must survive. No tool is executed in this review.\n' + event.text)
                reviewed.append(event.event_id)
        self.generate_stage('LEARN')
        source = next(event for event in reversed(self.stream.history.events) if event.actor == 'child')
        if should_compact:
            summary = replace(source, event_id=f'r184:summary:{cycle}', phase='compaction')
            self.stream.history.compact(summary,
                through=self.stream.history.frontier(len(self.stream.history.events) - 1))
            self.journal.record('COMPACTION', dict(kind='CHILD_COMPACTION', state=self.stream.checkpoint(),
                reviewed_reflection_ids=reviewed, working_state_preserved=True))
        self.journal.record('R184_SLEEP_NOTICE', dict(cycle=cycle, new_rows=len(self.stream.pending_rows()),
            selected_old_rows=0, new_presentations=self.new_presentations, actual_optimizer_complete=False,
            reviewed_reflection_ids=reviewed, compaction=should_compact))
        if self.allocation is not None:
            total = sum(self.cycle_metrics.values())
            self.journal.record('R189_LEARN_ALLOCATION', dict(cycle=cycle,
                outcome_cycle=self.last_allocation, stage_tokens=dict(self.cycle_metrics),
                think_share_including_learn=self.cycle_metrics['THINK'] / total if total else None,
                allocation=self.allocation.snapshot(), runtime_and_feedback_target=False))


def run_loop(child, stream, journal, anchors, plan, root, plan_path, completed_sleeps):
    from gpu.orch_r125_continual_native import finish_sleep, fresh_readout
    require(plan['rehearsal_presentations'] == 0, 'R184_new_rows_only')
    driver = ThinkActLearn(child, stream, journal, plan['think_act_learn'],
        new_presentations=plan['new_presentations'])
    while time.time() < plan['hard_end_unix']:
        driver.wake()
        cycle = completed_sleeps + 1
        driver.prepare_sleep(cycle)
        new_rows = stream.pending_rows()
        pending = stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in new_rows])
        pending['sha256'] = digest(pending['state'])
        journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
        checkpoint = finish_sleep(child, stream, journal, anchors, root, cycle)
        completed_sleeps = cycle
        journal.record('R184_LEARN_COMPLETE', dict(cycle=cycle, state_revision=stream.history.working_state['revision'],
            working_state=stream.history.working_state, checkpoint=checkpoint, parent_required_for_next_cycle=False))
        fresh_readout(child, plan_path, checkpoint, cycle)
        if plan['max_sleeps'] is not None and completed_sleeps >= plan['max_sleeps']:
            break
    journal.record('TERMINAL', dict(status='R184_SCREEN_STOP', completed_sleeps=completed_sleeps))
