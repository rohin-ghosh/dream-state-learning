"""Copy-only THINK/ACT wake driver using the existing child, journal and sleep."""

from copy import deepcopy
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unicodedata

from organism_v6.orch_r124_train_history import CompactionRequired, TrainEvent, WorkingStateSpan
from organism_v6.orch_r125_continual_stream import digest, require
from gpu.orch_r189_outcome_allocation import (
    SCHEMA as OUTCOME_SCHEMA, OutcomeAllocation, counts, validate_counts,
)
from gpu.orch_r193_continuity import SCHEMA as CONTINUITY_SCHEMA, continuity_prompt


SCHEMA = 'R184_THINK_ACT_LEARN_V1'
JUDGMENT_POLICY = 'R198_JUDGMENT_FIRST_V1'
EFFORT_POLICY = 'R201_OUTCOME_EFFORT_V1'
STAGE_BOUNDARY_POLICY = 'R203_STAGE_BOUNDARIES_V1'
STRUCTURED_THINK_POLICY = 'R202_WIDE_NARROW_WIDE_V1'
STRUCTURED_THINK_PROMPT = (
    'Structured THINK experiment: move from wide to narrow and back to wide, with one sentence '
    'per top-level question and free flow inside relevant narrow notes. Your parent may advise '
    'during Think; make gradual changes, not a drastic replacement of your approach. '
    'Start wide: What am I, and what do I accurately know about my LoRA, carried working state, '
    'and the proposed boat/river learning process? What is my largest current goal? '
    'Narrow: What happened last time? What do I think about it? What else was I thinking about '
    'then? Descend from the larger goal to the smaller relevant notes in the last context. '
    'For material that seems irrelevant: What do I think about it now? How can I condense it '
    'without changing the original observation? Briefly look back across it so useful findings '
    'and unfinished questions are not lost. Nothing changed remains a valid answer. '
    'Return wide: How can I learn from this, and what does it preserve or change about how I '
    'investigate and act? Predictions and choice: What do I need to do next? What do I think '
    'will happen? What do I want to happen? What will I actually do? What did I do last time, '
    'and what small change will I make now? Would more thought resolve a specific uncertainty, '
    'or would an attempt give better new evidence? Parent conversation is THINK; an actual '
    'message or completed artifact intended for Rohin is ACT. Choose when to act using '
    'Ready to act; the existing stage budget and fallback still apply.')
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
    optional = {'outcome_policy', 'continuity_policy', 'environment_facts', 'console_reflection', 'code_policy',
        'judgment_policy', 'learn_review_filter', 'correction_ledger', 'effort_policy',
        'structured_think_policy', 'stage_boundary_policy', 'prose_target_filter'}
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
    if 'effort_policy' in config:
        require(config['effort_policy'] == EFFORT_POLICY and config.get('outcome_policy') == OUTCOME_SCHEMA,
            'versioned_effort_policy_requires_outcome_tracking')
    if 'continuity_policy' in config:
        require(config['continuity_policy'] == CONTINUITY_SCHEMA, 'versioned_continuity_policy')
    if 'environment_facts' in config:
        require(config.get('continuity_policy') == CONTINUITY_SCHEMA
            and type(config['environment_facts']) is str
            and 0 < len(config['environment_facts'].encode()) <= 2048, 'bound_environment_facts')
    if 'console_reflection' in config:
        from gpu.orch_r194_console_reflection import validate_config as validate_console
        validate_console(config['console_reflection'])
    if 'code_policy' in config:
        from gpu.orch_r153_code_blocks import NFKC_POLICY, POLICY
        require(config['code_policy'] in (POLICY, NFKC_POLICY), 'known_code_policy')
    if 'judgment_policy' in config:
        require(config['judgment_policy'] == JUDGMENT_POLICY, 'known_judgment_policy')
    if 'structured_think_policy' in config:
        require(config['structured_think_policy'] == STRUCTURED_THINK_POLICY
            and config.get('judgment_policy') == JUDGMENT_POLICY,
            'versioned_structured_think_requires_judgment_first')
    if 'stage_boundary_policy' in config:
        require(config['stage_boundary_policy'] == STAGE_BOUNDARY_POLICY,
            'known_stage_boundary_policy')
    if 'prose_target_filter' in config:
        from organism_v6.orch_r203_prose_target_filter import POLICY as PROSE_POLICY
        require(config['prose_target_filter'] == PROSE_POLICY
            and 'learn_review_filter' in config, 'prose_quarantine_requires_review_filter')
    if 'learn_review_filter' in config:
        from organism_v6.orch_r194_code_target_filter import validate_review_policy
        validate_review_policy(config)
    if 'correction_ledger' in config:
        from gpu.orch_r197_correction_ledger import SCHEMA as CORRECTION_SCHEMA
        require(config['correction_ledger'] == CORRECTION_SCHEMA, 'known_correction_ledger')
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


def stage_prompt(stage, policy, *, think_remaining=1, continuity_policy=None, environment_facts=None,
                 judgment_policy=None, structured_think_policy=None):
    if structured_think_policy is not None:
        require(structured_think_policy == STRUCTURED_THINK_POLICY
            and judgment_policy == JUDGMENT_POLICY,
            'versioned_structured_think_requires_judgment_first')
        prompt = stage_prompt(stage, policy, think_remaining=think_remaining,
            continuity_policy=continuity_policy, environment_facts=environment_facts,
            judgment_policy=judgment_policy)
        return prompt + ('\n' + STRUCTURED_THINK_PROMPT if stage == 'THINK' else '')
    if judgment_policy is not None:
        require(judgment_policy == JUDGMENT_POLICY, 'known_judgment_policy')
        prompt = stage_prompt(stage, policy, think_remaining=think_remaining,
            continuity_policy=continuity_policy, environment_facts=environment_facts)
        if stage == 'THINK':
            opening = ('Runtime status: THINK. First, judge your last attempt: did it succeed, '
                'and how good was it? Did it do what you intended, and what actual receipt '
                'supports that judgment? If there was no attempt or no result, say so. '
                'Then continue your reflection. ')
            return opening + prompt.removeprefix('Runtime status: THINK. ')
        if stage == 'ACT':
            return prompt.replace('For a calculation or program provide a plain Python fenced block.',
                'An ACT may be a worked hand calculation or another language-native attempt, '
                'not only a program. Show the actual calculation or work in prose, or provide '
                'a plain Python fenced block when you choose execution. A prose answer is not '
                'an execution receipt or automatic proof; keep it unverified until independent '
                'tool, parent, or judge feedback supports it.')
        return prompt
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
        self.dataset = None
        self.last_stage_export = None
        self.last_transition = None
        self.last_act_evidence = None
        self.corrections = None
        self.correction_thinks = []
        self.correction_parents = []
        self.correction_parent_ids = {event.event_id for event in stream.history.events if event.actor == 'parent'}
        if 'correction_ledger' in config:
            self.restore_corrections()
        if config.get('continuity_policy') == CONTINUITY_SCHEMA:
            from gpu.orch_r191_exploration_dataset import ExplorationDataset
            self.dataset = ExplorationDataset(journal.root / 'exploration', config['trial_id'])
        if config.get('outcome_policy') == OUTCOME_SCHEMA:
            saved = next((event for event in reversed(stream.history.events)
                if event.actor == 'environment' and event.source_id == 'runtime:r189:outcome_allocation'), None)
            state = None
            if saved is not None:
                document = json.loads(saved.text)
                require(saved.source_sha256 == digest(document), 'bound_outcome_allocation_event')
                state = document['allocation']
            self.allocation = OutcomeAllocation(state)

    def effort_guidance(self):
        guidance = self.allocation.guidance(self.config['trial_id'])
        if self.config.get('effort_policy') == EFFORT_POLICY:
            guidance['effort_policy'] = EFFORT_POLICY
            guidance['think_segments_budget'] = (2 if guidance['mode'] in (
                'CONSOLIDATE_SUCCESS', 'ASSESS_EVIDENCE') else 3)
            if guidance['mode'] == 'CONSOLIDATE_SUCCESS':
                guidance['instruction'] += (' Use medium Think to judge quality, then preserve and '
                    'reinforce the supported practice through another attempt with small variations. '
                    'This does not change the declared sleep dose or turn unknown results into successes.')
            elif guidance['mode'] in ('SUSTAINED_FAILURE', 'GUIDED_EXPLORATION', 'REDUNDANT_DATA'):
                guidance['instruction'] += (' Think longer and consider more alternative approaches; '
                    'choose one informative next attempt instead of repeating a failed action unchanged.')
        if self.config.get('stage_boundary_policy') == STAGE_BOUNDARY_POLICY:
            guidance['think_segments_budget'] = min(2, guidance['think_segments_budget'])
            guidance['instruction'] += (' Use at most two consecutive autonomous THINK responses '
                'before the next attempt; you may act earlier. Consider alternatives within that budget.')
        return guidance

    def restore_corrections(self):
        path = self.journal.root / 'correction_ledger.json'
        if not path.exists():
            return
        try:
            require(not path.is_symlink(), 'regular_correction_cache')
            cached = json.loads(path.read_text())
            index = cached['record_index']
            require(type(index) is int and index >= 0, 'actual_correction_record_index')
            record = json.loads((self.journal.root / 'records' / f'{index:020d}.json').read_text())
            require(record['kind'] == 'R197_CORRECTION_CYCLE'
                and record['sha256'] == cached['record_sha256']
                and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
                and record['document']['ledger']['life_id'] == self.config['trial_id'],
                'bound_correction_ledger_cache')
            self.corrections = record['document']['ledger']
            last_source = self.corrections['cycles'][-1]['input'].get('source') or {}
            last_event_id = last_source.get('event_id')
            last_position = next((index for index, event in enumerate(self.stream.history.events)
                if event.event_id == last_event_id), None)
            if last_position is None:
                self.correction_parents.append(dict(reminder=None, reason='unrecorded_parent_interval'))
            else:
                self.correction_parents.extend(dict(event_id=event.event_id,
                    source_sha256=event.source_sha256, reminder=None)
                    for event in self.stream.history.events[last_position + 1:] if event.actor == 'parent')
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.journal.record('R197_STATE_CACHE_ERROR', dict(operation='restore',
                error_type=type(error).__name__, correction_history_unknown=True))

    def record_corrections(self, outcome, raw_act):
        if 'correction_ledger' not in self.config:
            return
        from gpu.orch_r197_correction_ledger import update_ledger
        self.corrections = update_ledger(self.corrections, life_id=self.config['trial_id'],
            cycle=len(self.stream.sleep_receipts) + 1, raw_think=self.correction_thinks,
            raw_act=raw_act, completed_sleeps=len(self.stream.sleep_receipts), execution=outcome,
            parent_interventions=self.correction_parents,
            source=dict(response=deepcopy(self.last_response), event_id=self.stream.rows[-1]['event_id']))
        reference = self.journal.record('R197_CORRECTION_CYCLE', dict(ledger=self.corrections,
            semantic_labels='UNADJUDICATED_UNLESS_EXPLICITLY_SOURCE_BOUND',
            runtime_repair_is_not_child_correction=True))
        self.correction_parents = []
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=self.journal.root, prefix='.correction-',
                    suffix='.tmp', delete=False) as output:
                temporary = Path(output.name)
                json.dump(dict(record_index=reference['index'], record_sha256=reference['sha256']), output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.journal.root / 'correction_ledger.json')
        except OSError as error:
            self.journal.record('R197_STATE_CACHE_ERROR', dict(operation='save',
                error_type=type(error).__name__, journal_record=reference))
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def generate_stage(self, stage, *, extra='', think_remaining=1):
        state_before = deepcopy(self.stream.history.working_state)
        incoming = list(self.journal.read_inbox())
        boundary_policy = self.config.get('stage_boundary_policy') == STAGE_BOUNDARY_POLICY
        if boundary_policy:
            from organism_v6.orch_r124_train_history import WORKING_STATE_BYTE_BUDGET
            seen = {event.event_id for event in self.stream.history.events}
            human_ids = set()
            for event in incoming:
                if event.actor != 'parent' or event.event_id in seen:
                    continue
                try:
                    message = json.loads(Path(event.source_id).read_bytes())
                except (OSError, ValueError):
                    continue
                if message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1' and message.get('speaker') == 'Rohin':
                    human_ids.add(event.event_id)
            if stage != 'THINK' and human_ids:
                incoming = [event for event in incoming if event.event_id not in human_ids]
                self.journal.record('R203_CONSOLE_DEFERRED', dict(stage=stage,
                    event_ids=sorted(human_ids), destination='NEXT_THINK',
                    reason='human_question_must_not_be_answered_inside_ACT_or_LEARN'))
            elif human_ids:
                extra += ('\nThis is a THINK conversation. Answer Rohin\'s actual latest questions '
                    'directly in ordinary prose, including your own conclusions; you may disagree '
                    'or refuse. Do not answer a person with a LEARN field block. A subsequent '
                    'finished artifact intended for Rohin is ACT.')
            entries = {entry['id']: entry for entry in state_before['entries']}
            attributed = self.stream.history._working_message(entries, state_before['revision'])
            used = len(attributed['content'].encode()) if attributed else 0
            extra += (f'\nWorking-state capacity is {WORKING_STATE_BYTE_BUDGET} UTF-8 bytes including '
                f'source metadata; current attributed state uses {used} bytes. A too-large edit is '
                'rejected as a whole, retaining the old state. Keep entries concise, replace an '
                'existing named entry, or explicitly use Forget state [name] for an obsolete '
                'entry; do not delete unresolved work merely to fit. No fixed field block is required.')
        parent_turns = [dict(asdict(event), target_loss=False) for event in incoming if event.actor == 'parent']
        if 'correction_ledger' in self.config:
            for event in incoming:
                if event.actor == 'parent' and event.event_id not in self.correction_parent_ids:
                    self.correction_parents.append(dict(event_id=event.event_id,
                        source_sha256=event.source_sha256, reminder=None))
                    self.correction_parent_ids.add(event.event_id)
        captured = {}
        if self.last_consolidation and self.last_consolidation['status'] == 'REJECTED_PRIOR_STATE_RETAINED':
            extra += ('\nYour last state edit was rejected and prior state retained: '
                      + self.last_consolidation['reason'])
        if stage == 'LEARN' and 'learn_review_filter' in self.config:
            candidates = [dict(row=item['segment'], source_sha256=item['source_sha256'],
                raw_preview=item['target'][:1200], preview_truncated=len(item['target']) > 1200)
                for item in self.stream.pending_rows()]
            extra += ('\nProtect this sleep: review the new responses below against the actual receipts. '
                'You may veto any of these rows, including garbage code or an unsupported claimed result. '
                'Write one standalone line per veto: Do not train: row <number> — <reason>. '
                'To veto this LEARN response itself, write Do not train: self — <reason>. '
                'Only these pending rows and this review can be vetoed; no old row is rewritten. '
                'A veto preserves the raw history but excludes the row from training. Runtime checks '
                'can exclude additional rows even if you keep them. No result obtained is valid. '
                'Keep an observation separate from a conjecture or a later reinterpretation. '
                'Pending raw response previews: ' + json.dumps(candidates, ensure_ascii=False))
        prompt = stage_prompt(stage, self.config['reflection_policy'], think_remaining=think_remaining,
            continuity_policy=self.config.get('continuity_policy'),
            environment_facts=self.config.get('environment_facts'),
            judgment_policy=self.config.get('judgment_policy'),
            structured_think_policy=self.config.get('structured_think_policy')) + extra
        if self.allocation is not None:
            guidance = self.effort_guidance()
            prompt += '\nOutcome-driven allocation: ' + guidance['instruction']
        incoming.append(runtime_event(self.config['trial_id'], len(self.stream.rows), stage, prompt))

        def recorded(kind, document):
            if kind == 'COMMITTED':
                if 'prose_target_filter' in self.config:
                    self.stream.rows[-1]['prose_target_filter'] = self.config['prose_target_filter']
                source = next(event for event in reversed(self.stream.history.events) if event.actor == 'child')
                self.last_consolidation = consolidate(self.stream.history, source,
                    preserve_status_labels=self.config.get('continuity_policy') == CONTINUITY_SCHEMA)
                if stage == 'LEARN' and 'learn_review_filter' in self.config:
                    review = self.stream.rows[-1]
                    review['learn_review'] = dict(schema=self.config['learn_review_filter'],
                        candidate_source_sha256=[item['source_sha256'] for item in self.stream.pending_rows()],
                        review_source_sha256=review['source_sha256'])
                    if self.last_act_evidence is not None:
                        review['learn_review_evidence'] = [deepcopy(self.last_act_evidence)]
                document = dict(document, state=self.stream.checkpoint())
            receipt = self.journal.record(kind, document)
            if kind in ('REQUEST', 'RESPONSE'):
                captured[kind] = dict(record_index=receipt['index'], record_sha256=receipt['sha256'])
                if kind == 'RESPONSE':
                    captured['response'] = deepcopy(document['response'])
            if kind == 'RESPONSE':
                self.last_response = dict(kind='TRAIN_CHILD_RESPONSE', record_index=receipt['index'],
                                          record_sha256=receipt['sha256'])
            return receipt

        try:
            options = (dict(compaction_threshold=min(self.stream.context_limit * 3 // 4,
                self.stream.context_limit - self.stream.segment_tokens)) if boundary_policy else {})
            result = self.stream.step(self.child.generate, self.child.count_tokens, recorded,
                incoming=incoming, **options)
        except Exception as error:
            if self.dataset is not None:
                self.export_stage(stage, state_before, parent_turns, captured,
                    outcome=dict(status='GENERATION_OR_COMMIT_FAILED', error_type=type(error).__name__),
                    committed=False)
            raise
        if self.allocation is not None:
            self.cycle_metrics[stage] += result['cost']['segment_tokens']
        if stage == 'THINK' and 'correction_ledger' in self.config:
            self.correction_thinks.append(self.stream.rows[-1]['target'])
        self.journal.record('R184_STAGE', dict(schema=SCHEMA, trial_id=self.config['trial_id'], stage=stage,
            segment=result['segment'], source_sha256=result['source_sha256'],
            consolidation=self.last_consolidation, runtime_notice_is_target=False))
        if stage == 'LEARN' and 'learn_review_filter' in self.config:
            from organism_v6.orch_r194_code_target_filter import filter_learn_review_targets
            unused_new, unused_old, review_proof = filter_learn_review_targets(
                self.stream.pending_rows(), [], self.config['learn_review_filter'])
            self.journal.record('R195_LEARN_REVIEW', dict(trial_id=self.config['trial_id'],
                cycle=len(self.stream.sleep_receipts) + 1, proof=review_proof,
                raw_modified=False, targets_normalized=False, optimizer_complete=False))
        if self.dataset is not None:
            self.last_stage_export = (stage, state_before, parent_turns, captured)
            if stage != 'ACT':
                self.export_stage(*self.last_stage_export, outcome=None, committed=True)
        return result

    def export_stage(self, stage, state_before, parent_turns, captured, *, outcome, committed):
        response = captured.get('response')
        reference = captured.get('RESPONSE', captured.get('REQUEST', {}))
        source = dict(journal_root=str(self.journal.root), request=captured.get('REQUEST'),
            response=captured.get('RESPONSE'), committed=committed,
            policy=self.config.get('continuity_policy'))
        identifier = f'{stage}:{reference.get("record_sha256", digest(source))}'
        row = dict(row_id=identifier, cycle=len(self.stream.sleep_receipts) + 1, stage=stage,
            action=response, outcome=deepcopy(outcome), state_before=state_before,
            state_after=deepcopy(self.stream.history.working_state), parent_turns=parent_turns,
            parent_turns_scope='NEW_INPUTS_BEFORE_STAGE', source=source,
            transition=dict(phase=self.cycle_phase, think_to_act=deepcopy(self.last_transition)),
            retained_in_weights=None)
        if committed:
            row.update(context=deepcopy(self.stream.rows[-1]['prefix']),
                target=deepcopy(self.stream.rows[-1]['target']),
                training_mask=dict(prefix_loss=False, target_loss=True))
        try:
            self.dataset.append(row)
            self.journal.record('R191_DATASET_ROW', dict(path=str(self.dataset.path), row_id=identifier,
                stage=stage, cycle=row['cycle'], outcome_recorded=outcome is not None))
        except (ValueError, OSError) as error:
            self.journal.record('R191_EXPORT_ERROR', dict(row_id=identifier, error_type=type(error).__name__,
                journal_preserved=True, retry_via_journal_backfill=True))

    def _cpu(self, origin):
        if self.config['trial_id'] in {
                'R203_MATH_COMM_B_node1_clone1',
                'R203_REPO_EVIDENCE_C_node1_clone1',
                'R203_CREATIVE_STRUCTURED_A_node1_clone1',
                'R203_MATH_SELF_DERIVE_C_node1_clone1'}:
            from gpu.r184_cpu_bridge import call
            return call(self.config, origin)
        from gpu.orch_r153_community_transport import EXISTING_LIFE_CPU_POLICY, cpu_once
        return cpu_once(str(self.journal.root.parent), self.journal._manifest['journal_id'], origin,
            self.config['cpu_gate_sha256'], gate_root=self.config['cpu_gate_root'], start=True,
            root_policy=EXISTING_LIFE_CPU_POLICY,
            **({'code_policy': self.config['code_policy']} if 'code_policy' in self.config else {}))

    def act(self):
        self.cycle_phase = 'ACT'
        result = self.generate_stage('ACT')
        raw_act = self.stream.rows[-1]['target']
        from gpu.orch_r153_community_transport import code_route
        route, unused_report = code_route(self.stream.rows[-1]['target'],
            **({'code_policy': self.config['code_policy']} if 'code_policy' in self.config else {}))
        if route == 'CPU':
            try:
                outcome = self.executor(self.last_response)
            except Exception as error:
                outcome = dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None,
                               error_type=type(error).__name__)
        else:
            status = 'NO_CPU_ATTEMPT' if route == 'NONE' else 'UNSUPPORTED_TOOL'
            if route == 'NONE' and self.config.get('judgment_policy') == JUDGMENT_POLICY:
                status = 'LANGUAGE_RESPONSE_UNVERIFIED'
            outcome = dict(status=status, executed=False)
        self.last_act_evidence = dict(act_source_sha256=result['source_sha256'],
            response_origin=deepcopy(self.last_response), outcome=deepcopy(outcome))
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
        self.record_corrections(outcome, raw_act)
        if self.dataset is not None:
            self.export_stage(*self.last_stage_export, outcome=outcome, committed=True)
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
        self.last_allocation['guidance_next'] = self.effort_guidance()
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
        self.last_transition = None
        self.last_act_evidence = None
        self.correction_thinks = []
        budget = self.config['think_segments']
        if self.allocation is not None:
            budget = self.effort_guidance()['think_segments_budget']
        if self.config.get('stage_boundary_policy') == STAGE_BOUNDARY_POLICY:
            budget = min(budget, 2)
        for position in range(budget):
            result = self.generate_stage('THINK', think_remaining=budget - position)
            chosen = ready_to_act(self.stream.rows[-1]['target'])
            if chosen:
                break
        self.last_transition = dict(schema=SCHEMA, from_stage='THINK', to_stage='ACT',
            segment=result['segment'], cause='child_ready' if chosen else 'forced_stage_budget',
            child_chosen=chosen, opportunity=True, think_segments_used=position + 1,
            think_segments_budget=budget)
        self.journal.record('R184_TRANSITION', self.last_transition)
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
    require(plan.get('learn_review_filter') == plan['think_act_learn'].get('learn_review_filter'),
        'same_learn_review_policy_in_driver_and_trainer')
    driver = ThinkActLearn(child, stream, journal, plan['think_act_learn'],
        new_presentations=plan['new_presentations'])
    console = None
    if 'console_reflection' in plan['think_act_learn']:
        from gpu.orch_r194_console_reflection import ConsoleReflection
        console = ConsoleReflection(child, stream, journal, plan['think_act_learn']['console_reflection'],
            environment_facts=plan['think_act_learn'].get('environment_facts', ''))
    while time.time() < plan['hard_end_unix']:
        if console is not None and not console.wait_until_resumed():
            break
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
