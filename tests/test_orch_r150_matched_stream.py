"""CPU fixtures only: no model construction, held task reads, or device calls."""

from copy import deepcopy
from functools import partial
import random
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from gpu.orch_r125_continual_native import finish_sleep, prepare_sleep
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, PRESLEEP_INVITATIONS, digest, experiment_binding
from organism_v6.orch_r125_plain_context import VERSION
from organism_v6.orch_r150_matched_stream import FROZEN_AUDIT_FIELDS, MODES, MatchedStream


COHORT = digest('common seeded R150 CPU fixture cohort')


def experiment(variant='free_distillation'):
    return experiment_binding(dict(seed=37, presleep_variant=variant,
        compaction_invitation=PRESLEEP_INVITATIONS[variant], system_prompt='Standing purpose.',
        birth_prompt='Continue your inquiry.'))


def model_checkpoint(*, steps=0, rng=0, binding=None):
    adapter_state = digest(dict(rank=8, steps=steps))
    optimizer_rng = digest(dict(optimizer_steps=steps, moments={} if steps == 0 else {'fixture': steps}, rng=rng))
    files = {'adapter_model.safetensors': adapter_state, 'adapter_config.json': digest(dict(r=8))}
    return dict(schema='CPU_FAKE_NATIVE_CHECKPOINT', adapter_state_sha256=adapter_state,
        adapter_files=files, checkpoint_sha256=dict(adapter=digest(files), optimizer=optimizer_rng, rng=optimizer_rng),
        optimizer_steps=steps, experiment=deepcopy(binding if binding is not None else experiment()))


def make_stream(arm='parented_frozen', *, variant='free_distillation', cohort=COHORT):
    binding = experiment(variant)
    initial = model_checkpoint(binding=binding)
    stream = MatchedStream(TrainHistory(system_prompt=binding['system_prompt'], birth_prompt=binding['birth_prompt']),
        arm=arm, cohort_sha256=cohort, initial_checkpoint=initial,
        context_limit=16384, segment_tokens=16, segments_per_sleep=2, deadline_unix=1000,
        model_state_sha256=digest(initial['checkpoint_sha256']), experiment=binding, allow_eviction=True)
    stream.set_presentation(dict(version=VERSION, system_prompt=binding['system_prompt'],
        birth_prompt=binding['birth_prompt']), 16384)
    return stream


def token_count(messages):
    return sum(len(message['content'].split()) + 4 for message in messages)


def event(identifier, actor='environment', text='Actual environment observation.'):
    return TrainEvent(event_id=identifier, actor=actor, text=text, split='TRAIN',
        phase='feedback', episode_id='fixture', source_id='fixture:' + identifier,
        source_sha256=digest([identifier, actor, text]), origin='TRAIN_COLLECTION')


class FakeChild:
    def __init__(self, arm, binding=None):
        self.arm = arm
        self.plan = deepcopy(binding if binding is not None else experiment())
        self.random = random.Random(self.plan['seed'])
        self.optimizer_steps = 0
        self.prompts = []
        self.training_calls = []
        self.count_tokens = token_count

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        assert max_new_tokens == 16 and deadline_unix == 1000
        self.prompts.append(deepcopy(messages))
        token = self.random.randrange(100, 1000)
        return dict(raw=f'Seeded child continuation {token}.', token_ids=[token, 2], terminal=True, truncated=False)

    def checkpoint(self, directory=None):
        return model_checkpoint(steps=self.optimizer_steps, rng=self.random.getstate(), binding=self.plan)

    def sleep(self, new_rows, old_rows, anchors, record):
        before = self.checkpoint()['adapter_state_sha256']
        if self.arm == 'parented_frozen':
            return dict(kind='FROZEN_CONTROL_BOUNDARY', optimizer_steps=0, cumulative_optimizer_steps=0,
                child_token_exposures=0, anchor_token_exposures=0, presentations=[],
                before_adapter_sha256=before, after_adapter_sha256=before, frozen_base_verified=True)
        self.training_calls.append(deepcopy(new_rows))
        self.optimizer_steps += 2
        return dict(optimizer_steps=2, before_adapter_sha256=before,
            after_adapter_sha256=self.checkpoint()['adapter_state_sha256'],
            child_token_exposures=sum(len(row['token_ids']) for row in new_rows),
            anchor_token_exposures=4, presentations={row['source_sha256']: 1 for row in new_rows})


def step(stream, child=None, record=None, **kwargs):
    child = child if child is not None else FakeChild(stream.arm, stream.experiment)
    return stream.step(child.generate, token_count, record if record is not None else lambda kind, value: None,
        now=lambda: 100, **kwargs)


def boundary(stream, child, journal, root, cycle):
    with patch.object(stream, 'step', wraps=partial(stream.step, now=lambda: 100)):
        prepare_sleep(child, stream, journal, cycle)
    pending = stream.checkpoint()
    pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in stream.pending_rows()])
    pending['sha256'] = digest(pending['state'])
    journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
    return finish_sleep(child, stream, journal, [], root, cycle)


def restore(stream, document=None, **kwargs):
    document = document if document is not None else stream.checkpoint()
    options = dict(expected_sha256=document['sha256'], expected_arm=stream.arm,
        expected_cohort_sha256=stream.cohort_sha256)
    options.update(kwargs)
    return MatchedStream.restore(document, **options)


def learned_receipt(stream, *, steps=2):
    checkpoint = model_checkpoint(steps=steps, binding=stream.experiment)
    return dict(status='COMPLETE', optimizer_steps=steps,
        new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], checkpoint=checkpoint)


def test_frozen_boundary_is_truthful_and_resets_cost_without_erasing_history():
    stream = make_stream()
    step(stream)
    step(stream)
    history = stream.history.checkpoint()
    rows = deepcopy(stream.rows)
    checkpoint = model_checkpoint(rng='advanced by generation only')
    receipt = stream.frozen_boundary_receipt(checkpoint, frozen_base_verified=True, cycle=1)
    record = Mock()
    saved = stream.commit_sleep(receipt, record)
    assert stream.sleep_frontier == 2 and not stream.sleep_due and stream.pending_rows() == []
    assert stream.rows == rows and stream.history.checkpoint() == history
    assert stream.sleep_receipts == [receipt]
    assert receipt['optimizer_steps'] == receipt['cumulative_optimizer_steps'] == 0
    assert receipt['presentations'] == []
    assert receipt['child_token_exposures'] == receipt['anchor_token_exposures'] == 0
    assert receipt['before_adapter_sha256'] == receipt['after_adapter_sha256']
    assert receipt['checkpoint_sha256'] == checkpoint['checkpoint_sha256']
    assert stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256'])
    record.assert_called_once_with('SLEEP_COMPLETE', dict(receipt, resume_state=saved))
    resumed = restore(stream)
    result = step(resumed)
    assert result['cost']['since_sleep_tokens'] == 2
    assert result['cost']['total_generated_tokens'] == 6
    assert resumed.rows[-1]['segment'] == 2


@pytest.mark.parametrize('field,value,error', [
    ('optimizer_steps', 1, 'no_training'),
    ('optimizer_steps', False, 'no_training'),
    ('cumulative_optimizer_steps', 1, 'no_training'),
    ('child_token_exposures', 1, 'no_training'),
    ('anchor_token_exposures', 1, 'no_training'),
    ('presentations', ['invented'], 'no_training'),
    ('presentations', {}, 'no_training'),
    ('kind', 'COMPLETE', 'explicit_frozen'),
    ('status', 'FAILED', 'explicit_frozen'),
    ('frozen_base_verified', False, 'explicit_frozen'),
    ('before_adapter_sha256', 'd' * 64, 'unchanged'),
    ('after_adapter_sha256', 'd' * 64, 'unchanged'),
    ('new_row_sha256', ['d' * 64], 'frontier'),
    ('cycle', True, 'actual_boundary_cycle'),
    ('unreported_training', True, 'exact_frozen'),
])
def test_bad_frozen_receipt_never_advances(field, value, error):
    stream = make_stream()
    step(stream)
    receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True, cycle=1)
    receipt[field] = value
    before = stream.checkpoint()
    record = Mock()
    with pytest.raises(ValueError, match=error):
        stream.commit_sleep(receipt, record)
    assert stream.checkpoint() == before
    record.assert_not_called()


@pytest.mark.parametrize('alteration', ['adapter_state', 'adapter_file', 'optimizer_steps', 'optimizer_hash', 'experiment'])
def test_frozen_checkpoint_requires_actual_bound_full_state(alteration):
    stream = make_stream()
    step(stream)
    receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
    if alteration == 'adapter_state':
        receipt['checkpoint']['adapter_state_sha256'] = receipt['after_adapter_sha256'] = 'd' * 64
    elif alteration == 'adapter_file':
        receipt['checkpoint']['checkpoint_sha256']['adapter'] = receipt['checkpoint_sha256']['adapter'] = 'd' * 64
    elif alteration == 'optimizer_steps':
        receipt['checkpoint']['optimizer_steps'] = 1
    elif alteration == 'optimizer_hash':
        receipt['checkpoint']['checkpoint_sha256'].pop('optimizer')
    else:
        receipt['checkpoint']['experiment']['seed'] += 1
    before = stream.checkpoint()
    with pytest.raises(ValueError):
        stream.commit_sleep(receipt, Mock())
    assert stream.checkpoint() == before


@pytest.mark.parametrize('arm', ['parented_learning', 'unparented_learning'])
def test_learning_delegates_original_positive_step_and_noeligible_contract(arm):
    stream = make_stream(arm)
    step(stream)
    receipt = learned_receipt(stream, steps=0)
    with pytest.raises(ValueError, match='positive_optimizer_steps'):
        stream.commit_sleep(receipt, Mock())
    receipt.update(no_update_reason='no_eligible_child_rows', presentations={},
        child_token_exposures=0, anchor_token_exposures=0)
    with patch.object(ContinualStream, 'commit_sleep', autospec=True, wraps=ContinualStream.commit_sleep) as original:
        stream.commit_sleep(receipt, Mock())
        original.assert_called_once()
    assert restore(stream).sleep_frontier == 1
    step(stream)
    stream.commit_sleep(learned_receipt(stream), Mock())
    assert restore(stream).sleep_frontier == 2


def test_original_stream_and_learning_arms_cannot_accept_frozen_receipt():
    frozen = make_stream()
    step(frozen)
    receipt = frozen.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
    with pytest.raises(ValueError, match='positive_optimizer_steps'):
        ContinualStream.commit_sleep(frozen, receipt, Mock())
    learning = make_stream('parented_learning')
    step(learning)
    with pytest.raises(ValueError, match='learning_cannot_use_frozen_boundary'):
        learning.commit_sleep(receipt, Mock())
    with pytest.raises(ValueError, match='frozen_boundary_only'):
        learning.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)


@pytest.mark.parametrize('incoming', [
    [event('parent', actor='parent')],
    [event('environment'), event('parent', actor='parent')],
    [event('parent', actor='parent'), event('environment')],
])
def test_unparented_preflights_entire_batch_before_any_side_effect(incoming):
    stream = make_stream('unparented_learning')
    before = stream.checkpoint()
    generate, count, record, now = Mock(), Mock(), Mock(), Mock()
    with pytest.raises(ValueError, match='unparented_parent_channel_forbidden'):
        stream.step(generate, count, record, incoming=iter(incoming), now=now)
    assert stream.checkpoint() == before
    for callback in (generate, count, record, now):
        callback.assert_not_called()


def test_real_environment_allowed_and_parent_input_never_becomes_target():
    for arm in MODES:
        stream = make_stream(arm)
        incoming = [event('tool', text='ENVIRONMENT_INPUT_ONLY_SENTINEL')]
        if arm != 'unparented_learning':
            incoming.append(event('parent', actor='parent', text='PARENT_INPUT_ONLY_SENTINEL'))
        records = []
        step(stream, record=lambda kind, value: records.append((kind, value)), incoming=incoming)
        request = next(value for kind, value in records if kind == 'REQUEST')
        assert request['render_receipt']['all_history_tokens_masked'] is True
        row = stream.rows[0]
        assert row['actor'] == 'child' and row['split'] == 'TRAIN'
        assert row['prefix_loss'] is False and row['target_loss'] is True
        assert 'ENVIRONMENT_INPUT_ONLY_SENTINEL' in str(row['prefix'])
        assert 'INPUT_ONLY_SENTINEL' not in row['target']
        assert all(name not in str(request['messages']) for name in MODES)
        assert COHORT not in str(request['messages'])


def test_injected_parent_history_is_rejected_on_step_and_restore():
    stream = make_stream('unparented_learning')
    stream.history.append(event('parent', actor='parent'))
    generate = Mock()
    with pytest.raises(ValueError, match='unparented_parent_channel_forbidden'):
        stream.step(generate, token_count, Mock(), now=lambda: 100)
    with pytest.raises(ValueError, match='unparented_parent_channel_forbidden'):
        restore(stream)
    generate.assert_not_called()


def test_readout_inputs_cannot_be_constructed_as_training_events():
    document = event('real').__dict__
    for changes in ({'split': 'HELD'}, {'phase': 'readout'}, {'origin': 'READOUT'}):
        with pytest.raises(ValueError):
            TrainEvent(**dict(document, **changes))


@pytest.mark.parametrize('field,value', [
    ('arm', 'parented_learning'), ('cohort_sha256', 'd' * 64),
    ('parent_channel', 'allow'), ('learning', 'frozen'), ('lora_rank', 0), ('schema', 'UNKNOWN'),
])
def test_rehashed_policy_tamper_refused(field, value):
    stream = make_stream('unparented_learning')
    document = stream.checkpoint()
    document['state']['matched'][field] = value
    document['sha256'] = digest(document['state'])
    with pytest.raises(ValueError, match='resume_matched_policy_mismatch'):
        restore(stream, document)


def test_bound_digest_wrong_resume_and_removed_receipts_refused():
    stream = make_stream()
    step(stream)
    stream.commit_sleep(stream.frozen_boundary_receipt(model_checkpoint(rng=1), frozen_base_verified=True), Mock())
    with pytest.raises(ValueError, match='resume_matched_policy_mismatch'):
        restore(stream, expected_arm='parented_learning')
    with pytest.raises(ValueError, match='resume_matched_policy_mismatch'):
        restore(stream, expected_cohort_sha256='d' * 64)
    document = stream.checkpoint()
    pinned = document['sha256']
    document['state']['sleep_receipts'] = []
    document['sha256'] = digest(document['state'])
    with pytest.raises(ValueError, match='bound_stream_checkpoint'):
        restore(stream, document, expected_sha256=pinned)
    with pytest.raises(ValueError, match='matched_receipt_state_binding'):
        restore(stream, document)


def test_failed_frozen_completion_is_not_silently_retryable():
    stream = make_stream()
    step(stream)
    receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
    with pytest.raises(OSError, match='disk failure'):
        stream.commit_sleep(receipt, Mock(side_effect=OSError('disk failure')))
    assert stream.pending == 'sleep:' + digest(receipt)
    assert stream.sleep_receipts == [receipt]
    with pytest.raises(ValueError, match='no_sleep_during_unresolved_generation'):
        stream.commit_sleep(receipt, Mock())
    with pytest.raises(ValueError, match='unresolved_request_never_redispatched'):
        step(stream)


@pytest.mark.parametrize('variant', ['free_distillation', 'no_distillation', 'reread_select', 'parent_guided_distillation'])
def test_same_initial_and_boundary_schedule_compaction_and_context(variant, tmp_path):
    traces = []
    for arm in MODES:
        stream = make_stream(arm, variant=variant)
        child = FakeChild(arm, stream.experiment)
        records = []
        journal = SimpleNamespace(record=lambda kind, value: records.append((kind, deepcopy(value))), read_inbox=lambda: [])
        initial = stream.checkpoint()
        boundaries = [(0, len(stream.rows), stream.sleep_frontier)]
        for cycle in (1, 2):
            step(stream, child, journal.record, incoming=[event(f'tool:{cycle}')])
            step(stream, child, journal.record)
            assert stream.sleep_due
            boundary(stream, child, journal, tmp_path / arm, cycle)
            assert not stream.sleep_due and stream.pending_rows() == []
            boundaries.append((cycle, len(stream.rows), stream.sleep_frontier))
            stream = restore(stream)
        expected_frontiers = [0, 2, 4] if variant == 'no_distillation' else [0, 3, 6]
        assert [frontier for _, _, frontier in boundaries] == expected_frontiers
        assert len(stream.history.operations) == (0 if variant == 'no_distillation' else 2)
        assert child.training_calls == [] if arm == 'parented_frozen' else len(child.training_calls) == 2
        traces.append(dict(initial_experiment=initial['state']['experiment'],
            initial_checkpoint=initial['state']['initial_checkpoint'], boundaries=boundaries,
            prompts=child.prompts, kinds=[kind for kind, _ in records],
            events=[(item.actor, item.phase, item.text) for item in stream.history.events],
            operations=[(item['kind'], item['at']['event_count'], item['through']['event_count'],
                item['summary']['text']) for item in stream.history.operations],
            costs=[value['cost'] for kind, value in records if kind == 'COMMITTED']))
    assert traces[0] == traces[1] == traces[2]


def test_frozen_helper_requires_explicit_caller_base_verification():
    stream = make_stream()
    step(stream)
    with pytest.raises(ValueError, match='caller_must_verify_frozen_base'):
        stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=False)


def test_native_optional_frozen_audit_fields_are_truthful_and_roundtrip():
    stream = make_stream()
    step(stream)
    receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
    receipt.update(FROZEN_AUDIT_FIELDS)
    stream.commit_sleep(receipt, Mock())
    assert restore(stream).sleep_receipts == [receipt]


@pytest.mark.parametrize('field,value', [
    ('total_optimizer_steps', 1), ('total_optimizer_steps', False),
    ('weight_updates_enabled', True), ('anchor_mix_applied', True),
    ('configured_anchor_lambda', 1.0), ('context_compaction_schedule', 'SKIPPED'),
    ('no_update_reason', 'no_eligible_child_rows'),
])
def test_inconsistent_optional_audit_fields_are_refused(field, value):
    stream = make_stream()
    step(stream)
    receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
    receipt[field] = value
    with pytest.raises(ValueError, match='truthful_frozen_audit_fields'):
        stream.commit_sleep(receipt, Mock())
