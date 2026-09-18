"""Fixed withdrawal controller and native bridge, not a model loader or launcher."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import random
import time

from gpu import orch_r125_continual_native as native
from gpu import orch_r144_sleep_targets as targets
from organism_v6.orch_r125_plain_context import eligible_rows
from research_loop.workers.rohin172_c2_pilot_20260917.continuation import custody


require = custody.require
digest = custody.digest


class GenerationRNG:
    def __init__(self, capture, restore, state):
        self.capture, self.restore, self.state = capture, restore, deepcopy(state)
        self.active = False

    @contextmanager
    def isolated(self):
        require(not self.active, 'no_nested_generation_RNG_swap')
        training = deepcopy(self.capture())
        self.active = True
        try:
            self.restore(deepcopy(self.state))
            yield
        finally:
            try:
                self.state = deepcopy(self.capture())
            finally:
                try:
                    self.restore(training)
                finally:
                    self.active = False


def transition(bundle, tokenizer, context_limit):
    carry, evidence = bundle['carry'], bundle['evidence']
    protected = [dict(role='assistant', content=carry['text'])]
    protected.extend(dict(role='user', content='Recorded environment observation:\n' + event['text'])
                     for event in evidence)
    messages = [dict(role='system', content=bundle['plan']['system_prompt']),
                dict(role='user', content=bundle['plan']['birth_prompt']), *protected]
    count = lambda value: len(tokenizer.apply_chat_template(value, tokenize=True,
                                add_generation_prompt=True, return_dict=False))
    require(count(protected) <= 2048, 'protected_carry_evidence_over_2048_no_trimming')
    require(count(messages) + 512 <= context_limit, 'carry_cannot_fit_preserve_and_stop')
    selected = {carry['event_id'], *(event['event_id'] for event in evidence)}
    receipt = dict(schema=custody.SCHEMA, kind='EXPLICIT_MATCHED_WITHDRAWAL_CONTEXT_TRANSITION',
        transition_count=1, raw_history_sha256=bundle['stream']['state']['history']['state_sha256'],
        carry_event=carry, evidence_events=evidence, messages=messages,
        protected_token_count=count(protected), prompt_token_count=count(messages),
        omitted_event_ids=[event['event_id'] for event in bundle['stream']['state']['history']['events']
                           if event['event_id'] not in selected],
        raw_history_preserved=True, new_parent_peer_or_sleep_reminder=False,
        semantic_adequacy='Main_bound_spans_not_an_automated_semantic_judgment')
    return messages, receipt


def sleep_material(new_rows, old_rows, tokenizer, plan):
    new_rows, old_rows = deepcopy(new_rows), deepcopy(old_rows)
    exclusions = []
    if plan.get('presentation_version'):
        presentation = dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                            birth_prompt=plan['birth_prompt'])
        new_rows, rejected = eligible_rows(new_rows, presentation)
        exclusions.extend(dict(item, cohort='NEW') for item in rejected)
        old_rows, rejected = eligible_rows(old_rows, presentation)
        exclusions.extend(dict(item, cohort='REHEARSAL') for item in rejected)
    new_rows, old_rows, encoded, rejected = targets.encode_sleep_targets(
        new_rows, old_rows, tokenizer, plan['context_limit'], native.encode_own)
    exclusions.extend(rejected)
    schedule = native.presentation_schedule(new_rows, old_rows) if new_rows else [
        ('REHEARSAL', row) for row in old_rows]
    return dict(new_rows=new_rows, old_rows=old_rows, encoded=encoded, schedule=schedule,
        eligibility=dict(version=plan.get('presentation_version'), runtime_policy=targets.POLICY,
            excluded=exclusions, new_row_sha256=[row['source_sha256'] for row in new_rows],
            rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False))


class NativeRuntime:
    """Caller supplies an already-contained fresh NativeChild and bound anchor inventory."""

    execution_kind = 'NATIVE_LOW_LEVEL_BRIDGE_NOT_ACTIVATED'

    def __init__(self, child, executor, anchors):
        from gpu.orch_r108_guided_native import validate_anchor_inventory
        require(type(child) is native.NativeChild and type(executor) is custody.exact.NativeExecutor
                and executor.child is child, 'tested_exact_native_executor_only')
        validate_anchor_inventory(anchors)
        self.child, self.executor, self.anchors = child, executor, anchors
        self.tokenizer, self.plan = child.tokenizer, child.plan

    def restore_saved(self, saved, binding):
        admitted = custody.admitted_from_saved(saved, binding, self.executor.fork_binding)
        before = self.executor.restore_admitted_checkpoint(admitted)
        return before

    def capture_rng(self):
        return dict(cpu=self.child.torch.get_rng_state(), cuda=self.child.torch.cuda.get_rng_state_all(),
                    python=random.getstate())

    def restore_rng(self, state):
        require(len(state['cuda']) == 1, 'one_saved_RNG_device_no_remapping_or_reseeding')
        self.child.torch.set_rng_state(state['cpu'])
        self.child.torch.cuda.set_rng_state_all(state['cuda'])
        random.setstate(state['python'])

    def rng_digest(self, state):
        from organism_v6.pcfl_vertical_train import _state_hash
        return _state_hash(state)

    def state(self):
        return self.executor.snapshot()

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.child.torch.cuda.synchronize()
        before = time.monotonic()
        result = self.child.generate(messages, max_new_tokens=max_new_tokens, deadline_unix=deadline_unix)
        self.child.torch.cuda.synchronize()
        return dict(result, synchronized_HF_seconds=time.monotonic() - before)

    def sleep(self, new_rows, old_rows, material, *, updates, record):
        require((self.executor.fork_binding['mode'] == 'learning') == updates, 'updates_bound_to_fork_mode')
        if updates:
            return self.child.sleep(new_rows, old_rows, self.anchors, record)
        record('TARGET_ELIGIBILITY', material['eligibility'])
        return dict(optimizer_steps=0, total_optimizer_steps=self.child.optimizer_steps,
                    no_update_reason='withdrawal_updates_disabled', presentations={},
                    child_token_exposures=0, anchor_token_exposures=0)

    def save(self, directory, *, generation_rng):
        reference = self.executor.checkpoint(directory / 'native')
        from io import BytesIO
        handle = BytesIO()
        self.child.torch.save(generation_rng, handle)
        custody.write_once(directory / 'generation_rng.pt', raw=handle.getvalue())
        return dict(native_checkpoint=reference, generation_rng_sha256=custody.sha(handle.getvalue()),
                    state=self.state())


def matched_initial(on, off):
    require(on['arm'] == custody.ARMS[0] and off['arm'] == custody.ARMS[1], 'matched_ON_OFF_identity')
    for field in ('binding_sha256', 'initial_state', 'initial_generation_rng_sha256',
                  'transition_sha256', 'workspace_inventory_sha256', 'runtime_match', 'source_pins_sha256'):
        require(on[field] == off[field], 'matched_initial_' + field)
    return dict(schema=custody.SCHEMA, status='MATCHED_INITIAL_RECEIPTS_NOT_LAUNCH_AUTHORITY',
                updates_only_treatment_difference=True, source_checkpoint_selected=False)


def run_arm(runtime, bundle, output, *, arm, binding_sha256, pins, now=time.time):
    """Exercise the full controller on CPU; production entry deliberately fails closed."""
    require(arm in custody.ARMS, 'fixed_arm')
    if isinstance(runtime, NativeRuntime) or runtime.execution_kind != 'CPU_FIXTURE_ONLY':
        raise NotImplementedError('native_activation_requires_paired_supervisor_deadline_guard_and_tool_custody_bridge')
    custody.verify_pins(pins)
    config = custody.pilot()['continuation']
    require(runtime.plan['context_limit'] == bundle['plan']['context_limit'], 'inherited_context_limit')
    output.mkdir(parents=True, exist_ok=False)
    started = now()
    deadline = min(started + config['maximum_wall_seconds_per_arm'], runtime.plan['hard_end_unix'])
    require(started < deadline, 'positive_fixed_wall_budget')
    updates = arm == custody.ARMS[0]
    generated, completed, record_index = 0, 0, 0
    rows, messages = [], []
    old_rows = deepcopy(bundle['stream']['state']['rows'])
    bank = GenerationRNG(runtime.capture_rng, runtime.restore_rng, runtime.capture_rng())

    def record(kind, document):
        nonlocal record_index
        result = dict(schema=custody.SCHEMA, execution_kind=runtime.execution_kind, kind=kind,
                      arm=arm, index=record_index, document=document)
        custody.write_once(output / f'{record_index:04d}_{kind}.json', result)
        record_index += 1
        return result

    def checkpoint(label):
        directory = output / label
        directory.mkdir()
        state = runtime.save(directory, generation_rng=deepcopy(bank.state))
        custody.write_once(directory / 'CONTROLLER.json', dict(schema=custody.SCHEMA,
            generated_tokens=generated, completed_cycles=completed, rows=rows, messages=messages,
            generation_rng_sha256=runtime.rng_digest(bank.state), deadline_unix=deadline,
            state=state, auto_resume=False))
        return state

    try:
        messages, change = transition(bundle, runtime.tokenizer, runtime.plan['context_limit'])
        custody.write_once(output / 'TRANSITION.json', change)
        initial = dict(schema=custody.SCHEMA, execution_kind=runtime.execution_kind, arm=arm,
            binding_sha256=binding_sha256, initial_state=runtime.state(),
            initial_generation_rng_sha256=runtime.rng_digest(bank.state),
            transition_sha256=digest(change), workspace_inventory_sha256=runtime.workspace_digest,
            source_pins_sha256=digest(pins), runtime_match=runtime.match,
            synthetic_fixture=True, throughput_or_C2_scientific_claim=False)
        custody.write_once(output / 'INITIAL.json', initial)
        for cycle in range(config['completed_wake_sleep_cycles']):
            frontier = len(rows)
            for segment in range(config['ordinary_segments_per_cycle'] + config['presleep_own_segments_per_cycle']):
                require(now() < deadline, 'fixed_four_hour_wall_exhausted')
                require(generated < config['maximum_generated_tokens_per_arm'], 'fixed_4608_token_budget_exhausted')
                prefix = runtime.tokenizer.apply_chat_template(messages, tokenize=True,
                    add_generation_prompt=True, return_dict=False)
                require(len(prefix) + 512 <= runtime.plan['context_limit'], 'context_overflow_preserve_carry_no_recompact')
                request = record('REQUEST', dict(cycle=cycle, segment=segment,
                    segment_kind='ordinary' if segment < 2 else 'presleep_own_no_invitation',
                    messages=deepcopy(messages), actual_prompt_ids=prefix, prefix_labels=[-100] * len(prefix),
                    cap=512, new_parent_peer_or_sleep_reminder=False))
                with bank.isolated():
                    response = runtime.generate(deepcopy(messages), max_new_tokens=512, deadline_unix=deadline)
                returned = record('RESPONSE', dict(response=deepcopy(response), request_sha256=digest(request)))
                token_ids = response['token_ids']
                require(type(token_ids) is list and 0 < len(token_ids) <= 512
                        and all(type(value) is int and value >= 0 for value in token_ids), 'actual_bounded_generated_tokens')
                generated += len(token_ids)
                require(generated <= 4608, 'actual_4608_token_limit')
                require(type(response['terminal']) is bool
                        and (not response['terminal'] or token_ids[-1] == runtime.tokenizer.eos_token_id),
                        'actual_EOS_not_a_synthetic_token_count')
                visible = token_ids[:-1] if response['terminal'] else token_ids
                require(runtime.tokenizer.decode(visible, skip_special_tokens=False,
                    clean_up_tokenization_spaces=False) == response['raw'], 'actual_response_roundtrip')
                row = dict(segment=len(old_rows) + len(rows), split='TRAIN', actor='child',
                    event_id=f'withdrawal:cycle:{cycle}:segment:{segment}', prefix=deepcopy(messages),
                    target=response['raw'], token_ids=token_ids, append_eos=False,
                    prefix_loss=False, target_loss=True, source_sha256=digest(returned),
                    model_state_sha256=runtime.state()['adapter_sha256'], terminal=response['terminal'],
                    truncated=response.get('truncated', False))
                rows.append(row)
                record('ACTUAL_OWN_ROW', dict(row=row, actual_input_ids=prefix + token_ids,
                    actual_labels=[-100] * len(prefix) + token_ids,
                    history_and_environment_targets=0, eligibility_deferred_to_inherited_sleep_policy=True))
                messages.append(dict(role='assistant', content=response['raw']))
                checkpoint(f'segment_{cycle}_{segment}')
                require(now() < deadline, 'generation_finished_after_fixed_wall_preserved_incomplete')
            new_rows = rows[frontier:]
            material = sleep_material(new_rows, old_rows, runtime.tokenizer, runtime.plan)
            record('SLEEP_PLAN', dict(cycle=cycle, eligibility=material['eligibility'],
                registered_schedule=[dict(kind=kind, source_sha256=row['source_sha256'])
                                     for kind, row in material['schedule']],
                anchor_lambda=0.25, new_presentations=16, rehearsal_presentations=1))
            before, generation_before = runtime.state(), runtime.rng_digest(bank.state)
            result = runtime.sleep(new_rows, old_rows, material, updates=updates, record=record)
            after = runtime.state()
            require(runtime.rng_digest(bank.state) == generation_before, 'training_must_not_consume_generation_RNG')
            require(after['base_sha256'] == before['base_sha256'] and after['base_frozen'] is True,
                    'frozen_base_preserved')
            if not updates:
                require(after == before and result['optimizer_steps'] == 0
                        and not result['presentations'], 'OFF_exact_state_no_optimizer_or_RNG_updates')
            else:
                expected_steps = len(material['schedule'])
                require(result['optimizer_steps'] == expected_steps
                        and after['optimizer_steps'] - before['optimizer_steps'] == expected_steps,
                        'ON_inherited_actual_update_dose')
            require(now() < deadline, 'sleep_finished_after_fixed_wall_preserved_incomplete')
            completed += 1
            record('WITHDRAWAL_SLEEP_BOUNDARY', dict(cycle=cycle, updates_enabled=updates,
                result=result, before=before, after=after, native_SLEEP_COMPLETE_not_fabricated=True))
            old_rows.extend(deepcopy(new_rows))
            checkpoint(f'cycle_{cycle}')
        result = dict(schema=custody.SCHEMA, status='CPU_FIXTURE_COMPLETE_NOT_C2_EXECUTION',
            completed_cycles=completed, generated_tokens=generated, maximum_generated_tokens=4608,
            maximum_wall_seconds=14400, transition_count=1, new_reminders=0, GPU_launch=False)
        custody.write_once(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        saved, save_error = None, None
        try:
            saved = checkpoint('stopped')
        except BaseException as failure:
            save_error = dict(type=type(failure).__name__, error=str(failure))
        custody.write_once(output / 'FAILED.json', dict(schema=custody.SCHEMA,
            execution_kind=runtime.execution_kind, status='PRESERVED_INCOMPLETE_NO_RETRY',
            completed_cycles=completed, generated_tokens=generated, error_type=type(error).__name__,
            error=str(error), saved_state=saved, save_failure=save_error, auto_extension=False))
        raise
