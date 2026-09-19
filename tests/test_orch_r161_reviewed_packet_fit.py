"""Synthetic CPU fixtures only: no actual accepted candidates, training, or scientific proof."""

from copy import deepcopy
import fcntl
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r161_reviewed_packet_fit as fit
from organism_v6 import orch_r125_plain_context as plain
from tests.test_orch_r159_train_eligibility import BINDING, make_case
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r124_train_history import TrainHistory
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r158_train_gym import offer as fixture_offer, check as fixture_check, grade as fixture_grade


class Tokenizer:
    eos_token_id = 2
    pad_token_id = 0
    all_special_ids = [0, 2, 63]
    chat_template = 'CPU_FIXTURE_EXACT_PREFIX_V1'

    def __init__(self, target):
        self.target = target
        self.calls = []

    def get_vocab(self):
        return {str(index): index for index in range(64)}

    def apply_chat_template(self, messages, **options):
        assert options == dict(tokenize=True, add_generation_prompt=True, return_dict=False)
        self.calls.append(deepcopy(messages))
        return [40+len(message['content']) % 10 for message in messages]+[50]

    def decode(self, token_ids, **options):
        assert options == dict(skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if token_ids == [0]:
            return '<|endoftext|>'
        return self.target


def initial_state():
    return dict(adapter_sha256='a'*64, optimizer_sha256='b'*64, rng_sha256='c'*64,
                optimizer_steps=0, base_sha256=fit.native.BASE_SHA256, base_frozen=True)


def checkpoint(directory, state):
    directory.mkdir()
    adapter = directory/'adapter'
    adapter.mkdir()
    adapter_raw = fit.capture.encoded(dict(CPU_ONLY_SYNTHETIC_STATE=state['adapter_sha256']))
    (adapter/'adapter.safetensors').write_bytes(adapter_raw)
    payload = fit.capture.encoded(dict(CPU_ONLY_SYNTHETIC_STATE=state))
    (directory/'optimizer_rng.pt').write_bytes(payload)
    files = {'adapter.safetensors': fit.capture.sha(adapter_raw)}
    document = dict(base_sha256=state['base_sha256'], optimizer_steps=state['optimizer_steps'],
        adapter_state_sha256=state['adapter_sha256'], adapter_path=str(adapter), adapter_files=files,
        optimizer_rng_path=str(directory/'optimizer_rng.pt'),
        checkpoint_sha256=dict(adapter=fit.digest(files), optimizer=fit.capture.sha(payload), rng=fit.capture.sha(payload)))
    raw = fit.capture.encoded(document)
    (directory/'COMMIT.json').write_bytes(raw)
    return dict(path=str(directory/'COMMIT.json'), sha256=fit.capture.sha(raw))


class Executor:
    contract = fit.CONTRACT
    execution_kind = 'CPU_TEST_ONLY'

    def __init__(self):
        self.state = initial_state()
        self.batches = []
        self.fail_update = False
        self.bad_ack = False
        self.bad_checkpoint = False
        self.frozen_checkpoint_mutates = False

    def snapshot(self):
        return deepcopy(self.state)

    def update(self, batch):
        self.batches.append(batch)
        self.state['optimizer_steps'] += 1
        self.state['adapter_sha256'] = fit.digest(['synthetic_adapter', self.state['optimizer_steps']])
        self.state['optimizer_sha256'] = fit.digest(['synthetic_AdamW', self.state['optimizer_steps']])
        self.state['rng_sha256'] = fit.digest(['synthetic_RNG', self.state['optimizer_steps']])
        if self.fail_update:
            raise RuntimeError('CPU simulated uncertain update')
        return dict(batch_sha256='0'*64 if self.bad_ack else batch.sha256,
                    optimizer_step=self.state['optimizer_steps'])

    def checkpoint(self, directory):
        if self.frozen_checkpoint_mutates:
            self.state['rng_sha256'] = 'f'*64
        reference = checkpoint(directory, self.state)
        if self.bad_checkpoint:
            (directory/'optimizer_rng.pt').write_bytes(b'tampered')
        return reference

    def verify_checkpoint(self, reference):
        document = json.loads(Path(reference['path']).read_bytes())
        return json.loads(Path(document['optimizer_rng_path']).read_bytes())['CPU_ONLY_SYNTHETIC_STATE']


@pytest.fixture
def setup(tmp_path, monkeypatch):
    generating_state = dict(initial_state(), adapter_sha256='e'*64, optimizer_steps=123)
    generating_checkpoint = checkpoint(tmp_path/'generating_checkpoint', generating_state)
    generating_document = json.loads(Path(generating_checkpoint['path']).read_bytes())
    model_state = fit.digest(generating_document['checkpoint_sha256'])
    original_init = ContinualStream.__init__

    def lineage_init(instance, *args, **kwargs):
        kwargs['model_state_sha256'] = model_state
        original_init(instance, *args, **kwargs)

    monkeypatch.setattr(ContinualStream, '__init__', lineage_init)
    case = make_case(tmp_path, monkeypatch)
    packet = deepcopy(case.packet)
    reviews, packet['reviews'] = packet['reviews'], []
    candidate = dict(packet=packet, reviews=reviews)
    tokenizer = Tokenizer(case.row['target'])
    anchors = {family: [dict(family=family, source_condition='PURE_BASE', split='TRAIN',
        verified_competent=True, source_call_sha256='d'*64,
        encoded=fit.EncodedRow((40, 10, 2), (-100, 10, 2), (10, 2)))]
        for family in ('code', 'math', 'simulated_tools', 'concise_answer')}
    tokenizer_path = tmp_path/'tokenizer.json'
    tokenizer_path.write_text('CPU_ONLY_SYNTHETIC_TOKENIZER')
    source_directory = tmp_path/'generating_source'
    source_directory.mkdir()
    source_file = source_directory/'native.py'
    source_file.write_text('CPU_ONLY_SYNTHETIC_GENERATOR_SOURCE')
    plan_path = tmp_path/'generating.PLAN.json'
    plan_path.write_bytes(fit.capture.encoded(dict(root=str(case.root), matched_arm=case.root.name,
                                                 source_root=str(source_directory))))
    source_paths = [*fit.REQUIRED_SOURCES, Path(__file__)]
    authority = dict(schema=fit.SCHEMA, contract=fit.CONTRACT,
        fork_root=str(tmp_path/'labelled_packet_fork'), fork_label='CPU_FIXTURE_NOT_A_SCIENTIFIC_ARM',
        protected_roots=[str(case.root)], mode='learning', execution_kind='CPU_TEST_ONLY', context_limit=4096,
        source_pins={str(path.resolve()): fit.capture.sha(path.read_bytes()) for path in source_paths},
        tokenizer_pins={str(tokenizer_path): fit.capture.sha(tokenizer_path.read_bytes())},
        tokenizer_class=fit.implementation_name(tokenizer), executor_class=fit.implementation_name(Executor()),
        tokenizer_sha256=fit.fingerprint_tokenizer(tokenizer), anchors_sha256=fit.digest(fit.anchor_document(anchors)),
        initializer=dict(commit=checkpoint(tmp_path/'common_initial', initial_state()), state=initial_state()),
        generation_sources={str(case.root): dict(
            plan=dict(path=str(plan_path), sha256=fit.capture.sha(plan_path.read_bytes())),
            source_pins={str(source_file): fit.capture.sha(source_file.read_bytes())},
            checkpoints={model_state: generating_checkpoint})},
        trusted_artifacts=deepcopy(case.trusted), reviewer_provenance=deepcopy(case.reviewers),
        generator_binding=deepcopy(BINDING), excluded_task_ids=[])
    monkeypatch.setattr(plain, 'eligible_rows', Mock(side_effect=AssertionError('prefix rewriting forbidden')))
    monkeypatch.setattr(plain, 'replay_prefix', Mock(side_effect=AssertionError('prefix rewriting forbidden')))
    monkeypatch.setattr(fit.native.NativeChild, 'sleep', Mock(side_effect=AssertionError('native sleep forbidden')))
    return SimpleNamespace(case=case, candidate=candidate, tokenizer=tokenizer, anchors=anchors,
                           authority=authority, executor=Executor(), root=Path(authority['fork_root']),
                           original_stream_init=original_init)


def prepare(setup, new=None, replay=None, **options):
    return fit.prepare_fit([setup.candidate] if new is None else new, [] if replay is None else replay,
        authority=setup.authority, expected_authority_sha256=fit.digest(setup.authority),
        tokenizer=setup.tokenizer, anchors=setup.anchors, **options)


def create(setup):
    setup.executor.fork_binding = dict(fork_root=str(setup.root), mode=setup.authority['mode'],
        authority_sha256=fit.digest(setup.authority),
        initializer_commit_sha256=setup.authority['initializer']['commit']['sha256'])
    return fit.create_fork(setup.authority, expected_authority_sha256=fit.digest(setup.authority))


def execute(setup, new=None, replay=None, *, index=0, previous=None):
    return fit.fit_batch([setup.candidate] if new is None else new, [] if replay is None else replay,
        authority=setup.authority, expected_authority_sha256=fit.digest(setup.authority),
        batch_index=index, previous_commit_sha256=previous, tokenizer=setup.tokenizer,
        anchors=setup.anchors, executor=setup.executor)


def inject_row(monkeypatch, setup, change):
    original = fit.capture.compile_reviewed

    def compile_row(*args, **kwargs):
        decision = original(*args, **kwargs)
        assert decision['eligible']
        change(decision['row'])
        return decision

    monkeypatch.setattr(fit.capture, 'compile_reviewed', compile_row)


def test_exact_original_prefix_tokens_masks_and_schedule(setup):
    original = deepcopy(setup.candidate)
    batches, report = prepare(setup)
    assert setup.candidate == original
    assert all(messages == setup.case.row['prefix'] for messages in setup.tokenizer.calls)
    assert len(batches) == 16
    target = tuple(setup.case.row['token_ids'])
    for batch in batches:
        own = batch.components[0]
        assert own.target_ids == target
        assert own.labels == (-100,)*(len(own.input_ids)-len(target))+target
        assert [part.objective_weight for part in batch.components] == [0.75]+[0.0625]*4
        assert [part.label for part in batch.components] == ['NEW']+[
            'ANCHOR:'+family for family in sorted(setup.anchors)]
    assert report['child_token_exposures'] == 16*len(target)
    assert report['anchor_token_exposures'] == 16*4*2
    assert report['mix_kind'] == 'OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION'
    assert report['status'] == 'CPU_PREFLIGHT_ONLY_NOT_TRAINED'
    assert report['synthetic_fixture'] and not report['scientific_claim']
    assert not setup.root.exists()


def test_mock_execution_checkpoint_and_previous_replay_once(setup):
    create(setup)
    first = execute(setup)
    assert first['commit']['updates'] == 16
    assert not first['commit']['training_performed']
    second = execute(setup, new=[], replay=[setup.candidate], index=1, previous=first['sha256'])
    assert second['commit']['updates'] == 1
    assert second['commit']['child_token_exposures'] == len(setup.case.row['token_ids'])
    assert setup.executor.batches[-1].components[0].label == 'REHEARSAL'
    assert len(list((setup.root/'batch0000').glob('UPDATE*.json'))) == 16
    assert len(list((setup.root/'batch0001').glob('UPDATE*.json'))) == 1


def test_new16_plus_previous1_accounting(setup, monkeypatch):
    unused, first = prepare(setup)
    original = fit.capture.compile_reviewed
    calls = 0

    def another_cpu_row(*args, **kwargs):
        nonlocal calls
        decision = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            decision['binding']['response_sha256'] = 'e'*64
            decision['row']['source_sha256'] = 'f'*64
        return decision

    monkeypatch.setattr(fit.capture, 'compile_reviewed', another_cpu_row)
    original_lineage = fit._generation_lineage

    def another_cpu_lineage(*args):
        lineage = original_lineage(*args)
        if calls == 1:
            lineage['response_record_sha256'] = 'e'*64
            lineage['row_source_sha256'] = 'f'*64
        return lineage

    monkeypatch.setattr(fit, '_generation_lineage', another_cpu_lineage)
    batches, report = prepare(setup, replay=[setup.candidate], previous_admitted=first['admitted'])
    assert len(batches) == 17
    assert [batch.components[0].label for batch in batches] == ['NEW']*16+['REHEARSAL']
    assert sorted(report['presentations'].values()) == [1, 16]


@pytest.mark.parametrize('actor', ['parent', 'environment', 'tool'])
def test_no_parent_environment_tool_targets(setup, monkeypatch, actor):
    inject_row(monkeypatch, setup, lambda row: row.update(actor=actor))
    with pytest.raises(ValueError, match='child_targets_only'):
        prepare(setup)


@pytest.mark.parametrize('change,reason', [
    ({'split': 'DEV'}, 'child_targets_only'),
    ({'prefix_loss': True}, 'child_targets_only'),
    ({'target_loss': False}, 'child_targets_only'),
    ({'token_ids': [10, 11, 3]}, 'actual_terminal_eos'),
    ({'target': 'rewritten'}, 'native_target_roundtrip'),
    ({'token_ids': [-1, 2]}, 'actual_native_target_ids'),
    ({'token_ids': [100, 2]}, 'tokens_in_pinned_vocabulary'),
])
def test_fit_time_encoder_refusals(setup, monkeypatch, change, reason):
    inject_row(monkeypatch, setup, lambda row: row.update(change))
    with pytest.raises(ValueError, match=reason):
        prepare(setup)


def test_context_overflow_refused_without_cropping(setup):
    setup.authority['context_limit'] = 3
    with pytest.raises(ValueError, match='whole_source_no_training_trim'):
        prepare(setup)


def test_special_token_new_row_excluded_not_rewritten_or_admitted(setup, monkeypatch):
    inject_row(monkeypatch, setup, lambda row: row.update(token_ids=[10, 63, 2]))
    original = deepcopy(setup.candidate)
    batches, report = prepare(setup)
    assert batches == () and report['admitted'] == {}
    assert report['planned_updates'] == report['child_token_exposures'] == report['anchor_token_exposures'] == 0
    assert report['exclusions'][0]['reason'] == fit.targets.REJECTION
    assert report['exclusions'][0]['cohort'] == 'NEW'
    assert setup.candidate == original


def test_tampered_original_capture_refused(setup):
    setup.candidate['packet']['records'][1]['raw'] += b' '
    with pytest.raises(ValueError, match='independent_artifact_hash_join'):
        prepare(setup)


def test_tampered_review_refused(setup):
    setup.candidate['reviews'][0]['raw'] += b' '
    with pytest.raises(ValueError, match='independent_artifact_hash_join'):
        prepare(setup)


def test_caller_exclusions_not_bypassed(setup):
    setup.authority['excluded_task_ids'] = [json.loads(setup.candidate['packet']['task']['raw'])['task_id']]
    with pytest.raises(ValueError, match='reviewed_candidate_not_eligible'):
        prepare(setup)


def test_missing_review_refused(setup):
    setup.candidate['reviews'] = setup.candidate['reviews'][:1]
    with pytest.raises(ValueError, match='supplied_review'):
        prepare(setup)


def test_duplicate_response_refused(setup):
    with pytest.raises(ValueError, match='duplicate_response_or_source'):
        prepare(setup, new=[setup.candidate, setup.candidate])


def test_unadmitted_replay_refused(setup):
    with pytest.raises(ValueError, match='rehearsal_requires_exact_previous'):
        prepare(setup, new=[], replay=[setup.candidate])


def test_previous_cannot_be_new_or_omitted(setup):
    unused, first = prepare(setup)
    with pytest.raises(ValueError, match='previous_response_cannot_be_new'):
        prepare(setup, previous_admitted=first['admitted'])
    with pytest.raises(ValueError, match='all_previous_eligible_replayed_once'):
        prepare(setup, new=[], previous_admitted=first['admitted'])


def test_rehearsal_row_hash_must_match(setup):
    unused, first = prepare(setup)
    next(iter(first['admitted'].values()))['row_sha256'] = '0'*64
    with pytest.raises(ValueError, match='rehearsal_requires_exact_previous'):
        prepare(setup, new=[], replay=[setup.candidate], previous_admitted=first['admitted'])


def test_frozen_no_update_unchanged_full_state(setup):
    setup.authority['mode'] = 'frozen'
    setup.executor.update = Mock(side_effect=AssertionError('frozen update forbidden'))
    create(setup)
    result = execute(setup)['commit']
    assert result['before_state'] == result['after_state'] == initial_state()
    assert result['updates'] == result['child_token_exposures'] == result['anchor_token_exposures'] == 0
    assert not result['anchor_mix_applied']
    assert result['presentations'] == {} and list(result['planned_presentations'].values()) == [16]
    setup.executor.update.assert_not_called()


def test_empty_exact_no_update(setup):
    create(setup)
    result = execute(setup, new=[])['commit']
    assert result['before_state'] == result['after_state']
    assert result['updates'] == 0


@pytest.mark.parametrize('failure', ['fail_update', 'bad_ack', 'bad_checkpoint'])
def test_uncertain_update_checkpoint_is_terminal_no_retry(setup, failure):
    setattr(setup.executor, failure, True)
    create(setup)
    with pytest.raises((ValueError, RuntimeError)):
        execute(setup)
    assert (setup.root/'batch0000'/'INTENT.json').is_file()
    assert (setup.root/'batch0000'/'FAILED.json').is_file()
    assert not (setup.root/'batch0000'/'COMMIT.json').exists()
    count = len(setup.executor.batches)
    with pytest.raises(ValueError, match='existing_or_uncertain'):
        execute(setup)
    with pytest.raises(ValueError, match='previous_failed_boundary_never_advanced'):
        execute(setup, index=1, previous='0'*64)
    assert len(setup.executor.batches) == count


def test_frozen_checkpoint_cannot_change_rng(setup):
    setup.authority['mode'] = 'frozen'
    setup.executor.frozen_checkpoint_mutates = True
    create(setup)
    with pytest.raises(ValueError, match='saved_optimizer_RNG_state_verified'):
        execute(setup)
    assert not (setup.root/'batch0000'/'COMMIT.json').exists()


def test_create_only_and_duplicate_batch(setup):
    create(setup)
    with pytest.raises(FileExistsError):
        create(setup)
    execute(setup)
    with pytest.raises(ValueError, match='existing_or_uncertain'):
        execute(setup)


def test_competing_lock_refused_without_dispatch(setup):
    create(setup)
    with (setup.root/'LOCK').open('r+') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            execute(setup)
    assert setup.executor.batches == []
    assert not (setup.root/'batch0000').exists()


def test_authority_hash_and_ledger_immutable(setup):
    with pytest.raises(ValueError, match='external_authority_hash_required'):
        fit.create_fork(setup.authority, expected_authority_sha256='0'*64)
    create(setup)
    setup.authority['fork_label'] = 'changed'
    with pytest.raises(ValueError, match='fork_authority_immutable'):
        execute(setup)


@pytest.mark.parametrize('which', ['tokenizer', 'source', 'initializer'])
def test_pinned_files_changed_refused(setup, tmp_path, which):
    if which == 'tokenizer':
        Path(next(iter(setup.authority['tokenizer_pins']))).write_text('changed')
    elif which == 'source':
        path = tmp_path/'injected.py'
        path.write_text('changed')
        setup.authority['source_pins'][str(path)] = '0'*64
    else:
        path = Path(setup.authority['initializer']['commit']['path']).parent/'optimizer_rng.pt'
        path.write_text('changed')
    with pytest.raises(ValueError, match='pinned_file_changed'):
        prepare(setup)


def test_tokenizer_object_fingerprint_refused(setup):
    setup.tokenizer.chat_template += 'changed'
    with pytest.raises(ValueError, match='tokenizer_fingerprint_changed'):
        prepare(setup)


def test_initial_full_state_mismatch_refused_before_intent(setup):
    create(setup)
    setup.executor.state['rng_sha256'] = 'f'*64
    with pytest.raises(ValueError, match='exact_loaded_initializer'):
        execute(setup)
    assert not (setup.root/'batch0000').exists()


def test_anchor_tamper_and_bad_masks_refused(setup):
    setup.anchors['code'][0]['encoded'] = fit.EncodedRow((40, 10, 2), (40, 10, 2), (10, 2))
    with pytest.raises(ValueError, match='pinned_encoded_anchor_inventory'):
        prepare(setup)
    setup.authority['anchors_sha256'] = fit.digest(fit.anchor_document(setup.anchors))
    with pytest.raises(ValueError, match='anchor_target_mask_join'):
        prepare(setup)


def test_four_competent_train_anchor_families_required(setup):
    setup.anchors.pop('math')
    with pytest.raises(ValueError, match='competent_base_anchor_each_family'):
        prepare(setup)


def test_nonzero_common_initializer_refused(setup):
    setup.authority['initializer']['state']['optimizer_steps'] = 1
    with pytest.raises(ValueError, match='common_zero_update_initializer'):
        prepare(setup)


def test_no_external_executor_without_real_validation(setup):
    setup.authority['execution_kind'] = 'EXTERNALLY_VALIDATED_EXECUTOR'
    with pytest.raises(KeyError, match='executor_validation'):
        prepare(setup)


def test_budget_refusals(setup):
    with pytest.raises(ValueError, match='candidate_count_budget'):
        prepare(setup, new=[setup.candidate]*2, limits=fit.Limits(max_candidates=1))
    with pytest.raises(ValueError, match='bounded_packet_payload'):
        prepare(setup, limits=fit.Limits(max_payload_bytes=100))
    with pytest.raises(ValueError, match='fit_output_budget'):
        prepare(setup, limits=fit.Limits(max_output_bytes=100))


def test_protected_root_and_symlink_refusals(setup, tmp_path):
    setup.authority['fork_root'] = str(setup.case.root/'never_create')
    with pytest.raises(ValueError, match='no_protected_life_mutation'):
        create(setup)
    link = tmp_path/'linked'
    link.symlink_to(setup.case.root, target_is_directory=True)
    setup.authority['fork_root'] = str(link/'never_create')
    with pytest.raises((OSError, ValueError)):
        create(setup)
    assert not (setup.case.root/'never_create').exists()


def test_forbidden_path_refused_without_opening(setup):
    setup.candidate['reviews'][0]['path'] = '/unread/sealed/review.json'
    with pytest.raises(ValueError, match='held_or_evaluation_path_forbidden'):
        prepare(setup)


def test_special_token_exclusion_also_deduplicated_across_commits(setup, monkeypatch):
    inject_row(monkeypatch, setup, lambda row: row.update(token_ids=[10, 63, 2]))
    create(setup)
    first = execute(setup)
    assert first['commit']['admitted'] == {} and len(first['commit']['consumed']) == 1
    assert first['commit']['updates'] == 0
    with pytest.raises(ValueError, match='previous_response_cannot_be_new'):
        execute(setup, index=1, previous=first['sha256'])
    assert setup.executor.batches == []


def test_previous_receipt_tamper_cannot_dispatch(setup):
    create(setup)
    first = execute(setup)
    Path(first['path']).write_bytes(Path(first['path']).read_bytes()+b' ')
    with pytest.raises(ValueError, match='pinned_file_changed'):
        execute(setup, new=[], replay=[setup.candidate], index=1, previous=first['sha256'])
    assert len(setup.executor.batches) == 16


def test_previous_checkpoint_tamper_cannot_dispatch(setup):
    create(setup)
    first = execute(setup)
    (setup.root/'batch0000'/'checkpoint'/'optimizer_rng.pt').write_bytes(b'changed')
    with pytest.raises(ValueError, match='pinned_file_changed'):
        execute(setup, new=[], replay=[setup.candidate], index=1, previous=first['sha256'])
    assert len(setup.executor.batches) == 16


def test_orphan_attempt_without_failed_marker_stays_terminal(setup):
    create(setup)
    (setup.root/'batch0000').mkdir()
    with pytest.raises(ValueError, match='existing_or_uncertain'):
        execute(setup)
    assert setup.executor.batches == []


def test_mask_corruption_refused(setup, monkeypatch):
    original = fit.native.encode_own

    def broken_encoder(*args):
        sample = original(*args)
        return fit.EncodedRow(sample.input_ids, sample.input_ids, sample.target_ids)

    monkeypatch.setattr(fit.native, 'encode_own', broken_encoder)
    with pytest.raises(ValueError, match='exact_prefix_mask_and_target'):
        prepare(setup)


def test_anchor_round_robin_order_preserved(setup):
    extra = deepcopy(setup.anchors['code'][0])
    extra['encoded'] = fit.EncodedRow((41, 11, 12, 2), (-100, 11, 12, 2), (11, 12, 2))
    setup.anchors['code'].append(extra)
    setup.authority['anchors_sha256'] = fit.digest(fit.anchor_document(setup.anchors))
    batches, report = prepare(setup)
    code_samples = [next(part.target_ids for part in batch.components if part.label == 'ANCHOR:code')
                    for batch in batches]
    assert code_samples == [(10, 2), (11, 12, 2)]*8
    assert report['anchor_token_exposures'] == 16*4*2+8


def test_state_and_class_contracts_refused(setup):
    setup.authority['executor_class'] = 'unbound.OtherExecutor'
    create(setup)
    with pytest.raises(ValueError, match='pinned_executor_class'):
        execute(setup)
    assert setup.executor.batches == []


def test_tokenizer_implementation_pin_required(setup):
    setup.authority['source_pins'].pop(str(Path(__file__).resolve()))
    with pytest.raises(ValueError, match='injected_implementation_source_pin'):
        prepare(setup)


def test_tokenizer_mutation_during_encoding_refused(setup):
    original = setup.tokenizer.apply_chat_template

    def mutate(*args, **kwargs):
        setup.tokenizer.chat_template = 'changed'
        return original(*args, **kwargs)

    setup.tokenizer.apply_chat_template = mutate
    with pytest.raises(ValueError, match='tokenizer_changed_during_encoding'):
        prepare(setup)


def test_input_files_preserved_through_mock_execution(setup):
    originals = {path: Path(path).read_bytes() for path in setup.authority['trusted_artifacts'] if Path(path).is_file()}
    create(setup)
    execute(setup)
    assert all(Path(path).read_bytes() == raw for path, raw in originals.items())


def test_nonfinite_state_or_unfrozen_base_refused(setup):
    create(setup)
    setup.executor.state['base_frozen'] = False
    with pytest.raises(ValueError, match='frozen_base_and_optimizer_state'):
        execute(setup)
    assert setup.executor.batches == []


def test_ledger_output_budget_is_cumulative(tmp_path):
    budget = fit.OutputBudget(len(fit.capture.encoded({'value': 1})))
    with fit.capture.gym.console._directory(tmp_path) as directory:
        fit._write(directory, 'first.json', {'value': 1}, budget)
        with pytest.raises(ValueError, match='ledger_output_budget'):
            fit._write(directory, 'second.json', {'value': 1}, budget)
    assert not (tmp_path/'second.json').exists()


def test_executor_cannot_be_bound_to_raw_life(setup):
    create(setup)
    setup.executor.fork_binding['fork_root'] = str(setup.case.root)
    with pytest.raises(ValueError, match='executor_is_bound_to_new_fork'):
        execute(setup)
    assert setup.executor.batches == []


def test_initializer_optimizer_rng_fingerprints_checked(setup):
    setup.authority['initializer']['state']['optimizer_sha256'] = 'f'*64
    setup.executor.state['optimizer_sha256'] = 'f'*64
    create(setup)
    with pytest.raises(ValueError, match='loaded_boundary_optimizer_RNG_binding'):
        execute(setup)
    assert setup.executor.batches == []


def test_later_raw_sleep_generation_never_attributed_to_untouched_fork(setup):
    unused, report = prepare(setup)
    lineage = next(iter(report['generation_lineage'].values()))['target']
    assert lineage['source_root'] == str(setup.case.root)
    assert lineage['source_arm'] == 'parented_learning'
    assert lineage['model_state_sha256'] == setup.case.row['model_state_sha256']
    assert lineage['generating_adapter_state_sha256'] == 'e'*64
    assert lineage['generating_optimizer_steps'] == 123
    assert fit.digest(lineage['generating_checkpoint_sha256']) == setup.case.row['model_state_sha256']
    assert lineage['generating_checkpoint'] != setup.authority['initializer']['commit']
    assert lineage['relation'] == 'OFF_POLICY_EXTERNAL_OWN_TRAJECTORY'
    assert lineage['own_text_origin'] == 'ORIGINAL_GENERATING_CHILD_NOT_CONSUMING_FORK'
    assert not lineage['generated_by_consuming_fork']
    assert not lineage['common_initializer_proven']
    assert report['on_policy_rounds'] == 0


def test_missing_generation_checkpoint_evidence_refused(setup):
    setup.authority['generation_sources'][str(setup.case.root)]['checkpoints'] = {}
    with pytest.raises(KeyError):
        prepare(setup)


def test_fork_initial_checkpoint_cannot_replace_generating_checkpoint(setup):
    sources = setup.authority['generation_sources'][str(setup.case.root)]
    sources['checkpoints'][setup.case.row['model_state_sha256']] = setup.authority['initializer']['commit']
    with pytest.raises(ValueError, match='generating_checkpoint_model_state_join'):
        prepare(setup)


def test_generation_model_state_in_row_must_match_original_request(setup, monkeypatch):
    inject_row(monkeypatch, setup, lambda row: row.update(model_state_sha256='0'*64))
    with pytest.raises(ValueError, match='compiled_row_generation_lineage_join'):
        prepare(setup)


def test_original_source_plan_cannot_change_arm(setup):
    source = setup.authority['generation_sources'][str(setup.case.root)]
    path = Path(source['plan']['path'])
    plan = json.loads(path.read_bytes())
    plan['matched_arm'] = 'unparented_learning'
    path.write_bytes(fit.capture.encoded(plan))
    source['plan']['sha256'] = fit.capture.sha(path.read_bytes())
    with pytest.raises(ValueError, match='actual_generating_plan_arm_and_root'):
        prepare(setup)


def test_generating_source_file_tamper_refused(setup):
    source = setup.authority['generation_sources'][str(setup.case.root)]
    Path(next(iter(source['source_pins']))).write_text('changed')
    with pytest.raises(ValueError, match='pinned_file_changed'):
        prepare(setup)


def test_isolated_lineage_sibling_requires_original_common_initial_bytes(setup):
    evidence = deepcopy(setup.candidate['packet'])
    request = json.loads(evidence['records'][0]['raw'])
    initial = json.loads(Path(setup.authority['initializer']['commit']['path']).read_bytes())
    request['document']['resume_state']['state']['initial_checkpoint'] = initial
    source = setup.authority['generation_sources'][str(setup.case.root)]
    generating = json.loads(Path(source['checkpoints'][setup.case.row['model_state_sha256']]['path']).read_bytes())
    request['document']['resume_state']['state']['sleep_receipts'] = [dict(checkpoint=generating)]
    evidence['records'][0]['raw'] = fit.capture.encoded(request)
    lineage = fit._generation_lineage(evidence, setup.authority, fit.capture.Reader(fit.capture.Limits()))
    assert lineage['relation'] == 'OFF_POLICY_SIBLING_BOOTSTRAP'
    assert lineage['common_initializer_proven']
    assert lineage['generating_optimizer_steps'] == 123
    assert not lineage['generated_by_consuming_fork']


def test_no_onpolicy_round_claim_without_round_integration(setup):
    authority = dict(setup.authority, fork_root=str(setup.case.root))
    with pytest.raises(ValueError, match='on_policy_generation_requires_future_round_authority'):
        fit._generation_lineage(setup.candidate['packet'], authority, fit.capture.Reader(fit.capture.Limits()))


@pytest.mark.parametrize('sample', [
    fit.EncodedRow((40, 10, 2, 13), (-100, 10, 2, -100), (10, 2)),
    fit.EncodedRow((40, 10, 13, 2, 13), (-100, 10, -100, 2, -100), (10, 2)),
])
def test_anchor_full_sequence_masks_and_exposures_preserved(setup, sample):
    setup.anchors['code'][0]['encoded'] = sample
    setup.authority['anchors_sha256'] = fit.digest(fit.anchor_document(setup.anchors))
    before = deepcopy(setup.anchors)
    batches, report = prepare(setup)
    for batch in batches:
        component = next(part for part in batch.components if part.label == 'ANCHOR:code')
        assert component.input_ids == sample.input_ids
        assert component.labels == sample.labels
        assert component.target_ids == sample.target_ids
        assert component.objective_weight == 0.0625
    assert report['anchor_token_exposures'] == 16*4*2
    assert setup.anchors == before


def test_anchor_labels_must_match_unmasked_input_ids(setup):
    setup.anchors['code'][0]['encoded'] = fit.EncodedRow((40, 10, 2, 13), (-100, 11, 2, -100), (11, 2))
    setup.authority['anchors_sha256'] = fit.digest(fit.anchor_document(setup.anchors))
    with pytest.raises(ValueError, match='anchor_input_label_alignment'):
        prepare(setup)


def test_failed_commit_publication_never_advanced_even_if_file_present(setup, monkeypatch):
    create(setup)
    original_write = fit._write

    def failed_publish(directory, name, document, budget):
        result = original_write(directory, name, document, budget)
        if name == 'COMMIT.json':
            raise OSError('CPU simulated fsync/publication failure')
        return result

    monkeypatch.setattr(fit, '_write', failed_publish)
    with pytest.raises(OSError, match='publication failure'):
        execute(setup)
    prior = setup.root/'batch0000'/'COMMIT.json'
    assert prior.exists() and (prior.parent/'FAILED.json').exists()
    with pytest.raises(ValueError, match='previous_failed_boundary_never_advanced'):
        execute(setup, new=[], replay=[setup.candidate], index=1, previous=fit.capture.sha(prior.read_bytes()))
    assert len(setup.executor.batches) == 16


def test_native_executor_helper_closure_pins_required(setup):
    setup.authority['executor_class'] = fit.NATIVE_EXECUTOR_CLASS
    with pytest.raises(ValueError, match='native_executor_loss_fingerprint_pins'):
        prepare(setup)
    for path in fit.native_executor_source_paths():
        setup.authority['source_pins'][path] = fit.capture.sha(Path(path).read_bytes())
    batches, unused = prepare(setup)
    assert len(batches) == 16


def test_actual_native_executor_component_contract_without_torch_execution(setup):
    executor_module = pytest.importorskip('gpu.orch_r161_native_executor')
    setup.anchors['code'][0]['encoded'] = fit.EncodedRow((40, 10, 2, 13), (-100, 10, 2, -100), (10, 2))
    setup.authority['anchors_sha256'] = fit.digest(fit.anchor_document(setup.anchors))
    batches, unused = prepare(setup)
    executor = object.__new__(executor_module.NativeExecutor)
    executor.child = SimpleNamespace(plan=dict(context_limit=setup.authority['context_limit']))
    for batch in batches:
        assert executor._components(batch) == batch.components
    assert executor_module.CONTRACT == fit.CONTRACT


def dynamic_policy(setup):
    setup.evidence = dict(trusted_artifacts=setup.authority.pop('trusted_artifacts'),
        reviewer_provenance_by_sha256={value['review_sha256']: value
                                      for value in setup.authority.pop('reviewer_provenance').values()},
        generation_sources=setup.authority.pop('generation_sources'), excluded_task_ids=[])
    setup.authority.update(evidence_mode=fit.DYNAMIC, fit_limits=fit.asdict(fit.Limits()),
        reader_limits=fit.asdict(fit.capture.Limits()), allow_off_policy_new=True)


def authorize_batch(setup, index=0, prior=None, *, fit_start=None, journal_id='1'*32):
    parent = prior['commit']['checkpoint'] if prior else setup.authority['initializer']['commit']
    parent_state = prior['commit']['after_state'] if prior else setup.authority['initializer']['state']
    return dict(schema=fit.BATCH_AUTHORIZATION_SCHEMA, fork_policy_sha256=fit.digest(setup.authority),
        batch_index=index, previous_commit_sha256=prior['sha256'] if prior else None,
        previous_batch_authorization_sha256=prior['commit']['batch_authorization_sha256'] if prior else None,
        parent_checkpoint=deepcopy(parent), parent_state_sha256=fit.digest(parent_state),
        fit_start_checkpoint=deepcopy(fit_start or parent), fit_start_state=setup.executor.snapshot(),
        learner_journal_id=journal_id, **deepcopy(setup.evidence))


def prepare_dynamic(setup, authorization, *, new=None, replay=None, expected=None, **options):
    return fit.prepare_fit([setup.candidate] if new is None else new, replay or [], authority=setup.authority,
        expected_authority_sha256=fit.digest(setup.authority), tokenizer=setup.tokenizer, anchors=setup.anchors,
        batch_authorization=authorization,
        expected_batch_authorization_sha256=expected if expected is not None else fit.digest(authorization),
        batch_index=authorization['batch_index'], previous_commit_sha256=authorization['previous_commit_sha256'], **options)


def execute_dynamic(setup, authorization, *, new=None, replay=None, expected=None):
    return fit.fit_batch([setup.candidate] if new is None else new, replay or [], authority=setup.authority,
        expected_authority_sha256=fit.digest(setup.authority), tokenizer=setup.tokenizer, anchors=setup.anchors,
        executor=setup.executor, batch_authorization=authorization,
        expected_batch_authorization_sha256=expected if expected is not None else fit.digest(authorization),
        batch_index=authorization['batch_index'], previous_commit_sha256=authorization['previous_commit_sha256'])


class SyntheticContinuingLearner:
    def __init__(self, setup, tmp_path, monkeypatch):
        self.setup, self.monkeypatch = setup, monkeypatch
        arm = 'parented_frozen' if setup.authority['mode'] == 'frozen' else 'parented_learning'
        self.root = tmp_path/'orch_r158_r161_cpu_rounds'/arm
        self.root.parent.mkdir()
        setup.root = self.root
        setup.authority['fork_root'] = str(self.root)
        dynamic_policy(setup)
        setup.authority['allow_off_policy_new'] = False
        create(setup)
        self.journal = StreamJournal(self.root/'stream', create=True)
        self.journal_id = json.loads((self.root/'stream'/'JOURNAL.json').read_bytes())['journal_id']
        self.stream = object.__new__(ContinualStream)
        initial = json.loads(Path(setup.authority['initializer']['commit']['path']).read_bytes())
        setup.original_stream_init(self.stream, TrainHistory(system_prompt='Synthetic guided learner.',
            birth_prompt='CPU fixture, not a real learner.'), context_limit=4096, segment_tokens=128,
            segments_per_sleep=2, deadline_unix=1000, model_state_sha256=fit.digest(initial['checkpoint_sha256']))
        self.journal.record('COMMITTED', dict(state=self.stream.checkpoint()))
        source = deepcopy(setup.evidence['generation_sources'][str(setup.case.root)])
        plan_path = self.root.parent/'PLAN.json'
        original_plan = json.loads(Path(source['plan']['path']).read_bytes())
        original_plan['root'] = str(self.root)
        original_plan['matched_arm'] = arm
        plan_path.write_bytes(fit.capture.encoded(original_plan))
        source['plan'] = dict(path=str(plan_path), sha256=fit.capture.sha(plan_path.read_bytes()))
        source['checkpoints'] = {}
        setup.evidence['generation_sources'][str(self.root)] = source
        self.candidates = []

    def capture(self, path):
        artifact = fit.capture.eligibility.capture(str(path), Path(path).read_bytes())
        self.setup.evidence['trusted_artifacts'][artifact['path']] = artifact['sha256']
        return artifact

    def generate_round(self, index, prior=None, *, generating_checkpoint=None):
        setup, gym = self.setup, fit.capture.gym
        setup.case.clock.now += 1
        gym.console.publish_parent(self.root, 'Astra', 'CPU synthetic guidance: check your own arithmetic.')
        source = SimpleNamespace(score_answer=lambda answer, entry: 1.0 if answer == '4' else 0.0)
        with self.monkeypatch.context() as scoped:
            scoped.setattr(gym, 'dataset', lambda task: (source, dict(question='What is two plus two?'), deepcopy(BINDING)))
            scoped.setattr(gym, 'grade', fixture_grade)
            offered = fixture_offer(self.root, index)
            records = []

            def record(kind, document):
                receipt = self.journal.record(kind, document)
                if kind in ('REQUEST', 'RESPONSE', 'COMMITTED'):
                    records.append(self.capture(receipt['path']))

            def generate(messages, **options):
                assert any('CPU synthetic guidance' in message['content'] for message in messages)
                setup.case.clock.now += 0.5
                setup.executor.state['rng_sha256'] = fit.digest(['CPU synthetic generation RNG', index])
                return dict(raw=setup.case.row['target'], token_ids=[10, 11, 2], terminal=True, truncated=False)

            setup.case.clock.now += 1
            self.stream.step(generate, lambda messages: 128, record,
                             incoming=self.journal.read_inbox(), now=lambda: setup.case.clock.now)
            response_index = json.loads(records[1]['raw'])['index']
            checked = fixture_check(self.root, index, response_index)
        task_dir = gym.directory(self.root, index)
        result_path = Path(checked['result_path'])
        packet = dict(target_kind='ANSWER', label='grounded_reasoning', reviews=[], records=records,
            task=self.capture(task_dir/'TASK.json'), task_publication=self.capture(task_dir/'PUBLICATION.json'),
            task_message=self.capture(offered['publication']['path']), intent=self.capture(result_path.parent/'INTENT.json'),
            result=self.capture(result_path))
        context = fit.capture.eligibility.Compiler(setup.evidence['trusted_artifacts'], {}, BINDING, []).context(packet)
        reviews = []
        for review_index, template in enumerate(setup.candidate['reviews']):
            document = json.loads(template['raw'])
            document['binding'] = context['binding']
            document['review_text'] = 'CPU synthetic round review; not a genuine external review or scientific proof.'
            path = self.root.parent/f'round{index}_review{review_index}.json'
            path.write_bytes(fit.capture.encoded(document))
            artifact = self.capture(path)
            reviews.append(artifact)
            setup.evidence['reviewer_provenance_by_sha256'][artifact['sha256']] = dict(
                principal_id=document['principal_id'], session_id=document['session_id'], kind='model',
                source='CPU synthetic fixture review', independence_attested=True, review_sha256=artifact['sha256'])
        candidate = dict(packet=packet, reviews=reviews)
        self.candidates.append(candidate)
        parent = generating_checkpoint or (prior['commit']['checkpoint'] if prior else setup.authority['initializer']['commit'])
        parent_document = json.loads(Path(parent['path']).read_bytes())
        setup.evidence['generation_sources'][str(self.root)]['checkpoints'][self.stream.model_state_sha256] = parent
        assert self.stream.model_state_sha256 == fit.digest(parent_document['checkpoint_sha256'])
        boundary_root = self.root/'generation_boundaries'
        boundary_root.mkdir(exist_ok=True)
        start = checkpoint(boundary_root/f'round{index}', setup.executor.snapshot())
        authorization = authorize_batch(setup, index, prior, fit_start=start, journal_id=self.journal_id)
        return candidate, authorization

    def commit_to_stream(self, result):
        document = json.loads(Path(result['commit']['checkpoint']['path']).read_bytes())
        receipt = dict(status='COMPLETE', optimizer_steps=result['commit']['updates'],
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint=document, checkpoint_sha256=document['checkpoint_sha256'])
        self.stream.commit_sleep(receipt, self.journal.record)


def test_dynamic_two_genuinely_new_CPU_journal_rounds_with_same_learner(setup, tmp_path, monkeypatch):
    learner = SyntheticContinuingLearner(setup, tmp_path, monkeypatch)
    policy_sha = fit.digest(setup.authority)
    try:
        first_candidate, first_authorization = learner.generate_round(0)
        assert first_authorization['fit_start_state']['rng_sha256'] != setup.authority['initializer']['state']['rng_sha256']
        first = execute_dynamic(setup, first_authorization, new=[first_candidate])
        assert first['commit']['updates'] == 16
        assert first['commit']['on_policy_new_rows'] == 1
        learner.commit_to_stream(first)
        second_candidate, second_authorization = learner.generate_round(1, first)
        assert second_authorization['previous_batch_authorization_sha256'] == fit.digest(first_authorization)
        assert second_candidate['reviews'][0]['sha256'] != first_candidate['reviews'][0]['sha256']
        assert json.loads(second_candidate['reviews'][0]['raw'])['reviewer_id'] == json.loads(first_candidate['reviews'][0]['raw'])['reviewer_id']
        second = execute_dynamic(setup, second_authorization, new=[second_candidate], replay=[first_candidate])
        assert second['commit']['updates'] == 17
        assert second['commit']['simulated_on_policy_rounds'] == 2
        assert second['commit']['on_policy_rounds'] == 0 and not second['commit']['training_performed']
        assert set(second['commit']['policy_relations'].values()) == {'ON_POLICY_NEW_AT_PARENT_BOUNDARY', 'HISTORICAL_ELIGIBLE_REPLAY'}
        assert first['commit']['before_state'] == first_authorization['fit_start_state']
        assert second['commit']['before_state'] == second_authorization['fit_start_state']
        assert fit.digest(setup.authority) == policy_sha
        assert second['commit']['learner_frontier'] > first['commit']['learner_frontier']
        assert len(learner.stream.rows) == 2
    finally:
        learner.journal.close()


def test_dynamic_off_policy_requires_explicit_policy_and_keeps_lineage(setup):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    result = execute_dynamic(setup, authorization)
    assert result['commit']['on_policy_new_rows'] == result['commit']['on_policy_rounds'] == 0
    assert result['commit']['batch_authorization_sha256'] == fit.digest(authorization)
    assert next(iter(result['commit']['generation_lineage'].values()))['target']['generating_optimizer_steps'] == 123


def test_dynamic_missing_authorization_no_dispatch(setup):
    dynamic_policy(setup)
    create(setup)
    with pytest.raises(ValueError, match='independent_batch_authorization_hash_required'):
        execute(setup)
    assert setup.executor.batches == []


@pytest.mark.parametrize('field,value', [
    ('fork_policy_sha256', '0'*64), ('batch_index', 1), ('previous_commit_sha256', '0'*64),
    ('previous_batch_authorization_sha256', '0'*64), ('parent_state_sha256', '0'*64),
])
def test_dynamic_unbound_first_batch_refused(setup, field, value):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    authorization[field] = value
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare_dynamic(setup, authorization)
    assert setup.executor.batches == []


def test_dynamic_candidate_self_hashes_do_not_authorize_new_evidence(setup):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    expected = fit.digest(authorization)
    authorization['trusted_artifacts']['/unread/new_capture.json'] = 'a'*64
    with pytest.raises(ValueError, match='independent_batch_authorization_hash_required'):
        prepare_dynamic(setup, authorization, expected=expected)


def test_dynamic_caps_and_ledger_previous_maps_cannot_be_overridden(setup):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    with pytest.raises(ValueError, match='immutable_fit_caps'):
        prepare_dynamic(setup, authorization, limits=fit.Limits(max_candidates=64))
    with pytest.raises(ValueError, match='immutable_reader_caps'):
        prepare_dynamic(setup, authorization, reader=fit.capture.Reader(fit.capture.Limits(max_files=64)))
    with pytest.raises(ValueError, match='dynamic_previous_evidence_loaded_from_ledger_only'):
        prepare_dynamic(setup, authorization, previous_admitted={})


@pytest.mark.parametrize('field', ['adapter_sha256', 'optimizer_sha256', 'optimizer_steps', 'base_sha256'])
def test_dynamic_generation_cannot_hide_updates(setup, field):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    authorization['fit_start_state'][field] = 1 if field == 'optimizer_steps' else 'f'*64
    with pytest.raises(ValueError):
        prepare_dynamic(setup, authorization)
    assert setup.executor.batches == []


@pytest.mark.parametrize('which', ['trusted_artifacts', 'reviewer_provenance_by_sha256', 'generation_sources'])
def test_dynamic_old_authorized_pins_cannot_be_changed_or_removed(setup, which):
    dynamic_policy(setup)
    create(setup)
    first = execute_dynamic(setup, authorize_batch(setup))
    authorization = authorize_batch(setup, 1, first)
    key = next(iter(authorization[which]))
    authorization[which].pop(key)
    with pytest.raises(ValueError, match='removed_old_evidence_pin'):
        prepare_dynamic(setup, authorization, new=[], replay=[setup.candidate])
    authorization = authorize_batch(setup, 1, first)
    authorization[which][key] = '0'*64
    with pytest.raises(ValueError, match='changed_old_evidence_pin'):
        prepare_dynamic(setup, authorization, new=[], replay=[setup.candidate])


def test_dynamic_replayed_authorization_and_wrong_chain_refused(setup):
    dynamic_policy(setup)
    create(setup)
    first_authorization = authorize_batch(setup)
    first = execute_dynamic(setup, first_authorization)
    with pytest.raises(ValueError, match='existing_or_uncertain'):
        execute_dynamic(setup, first_authorization)
    second = authorize_batch(setup, 1, first)
    second['previous_batch_authorization_sha256'] = 'f'*64
    with pytest.raises(ValueError, match='batch_authorization_chain'):
        prepare_dynamic(setup, second, new=[], replay=[setup.candidate])


def test_dynamic_old_pin_cannot_be_shadowed_in_another_map(setup):
    dynamic_policy(setup)
    create(setup)
    first = execute_dynamic(setup, authorize_batch(setup))
    second = authorize_batch(setup, 1, first)
    old_path = next(iter(second['trusted_artifacts']))
    second['generation_sources']['/unread/additional_life'] = dict(plan=dict(path=old_path, sha256='f'*64))
    with pytest.raises(ValueError, match='cross_map_or_old_path_pin_changed'):
        prepare_dynamic(setup, second, new=[], replay=[setup.candidate])


def test_dynamic_changed_journal_identity_refused(setup):
    dynamic_policy(setup)
    create(setup)
    first = execute_dynamic(setup, authorize_batch(setup))
    second = authorize_batch(setup, 1, first, journal_id='2'*32)
    with pytest.raises(ValueError, match='continuing_learner_journal_identity'):
        prepare_dynamic(setup, second, new=[], replay=[setup.candidate])


def test_dynamic_wrong_parent_checkpoint_refused(setup):
    dynamic_policy(setup)
    create(setup)
    first = execute_dynamic(setup, authorize_batch(setup))
    second = authorize_batch(setup, 1, first)
    second['parent_checkpoint'] = setup.authority['initializer']['commit']
    with pytest.raises(ValueError, match='exact_parent_fit_boundary'):
        prepare_dynamic(setup, second, new=[], replay=[setup.candidate])


def test_dynamic_post_generation_rng_not_reset_to_previous_fit(setup, tmp_path, monkeypatch):
    learner = SyntheticContinuingLearner(setup, tmp_path, monkeypatch)
    try:
        candidate, authorization = learner.generate_round(0)
        setup.executor.state['rng_sha256'] = setup.authority['initializer']['state']['rng_sha256']
        with pytest.raises(ValueError, match='exact_loaded_initializer_or_previous_state'):
            execute_dynamic(setup, authorization, new=[candidate])
        assert setup.executor.batches == []
    finally:
        learner.journal.close()


@pytest.mark.parametrize('stale', ['model', 'time'])
def test_dynamic_old_own_trajectory_not_claimed_new_onpolicy(setup, tmp_path, monkeypatch, stale):
    learner = SyntheticContinuingLearner(setup, tmp_path, monkeypatch)
    try:
        first_candidate, authorization = learner.generate_round(0)
        first = execute_dynamic(setup, authorization, new=[first_candidate])
        if stale == 'time':
            learner.commit_to_stream(first)
            setup.case.clock.now = first['commit']['committed_unix']-5
        second_candidate, second_authorization = learner.generate_round(1, first,
            generating_checkpoint=setup.authority['initializer']['commit'] if stale == 'model' else None)
        reason = 'on_policy_NEW_requires_current_parent_model' if stale == 'model' else 'own_generation_must_follow_previous_fit_commit'
        with pytest.raises(ValueError, match=reason):
            prepare_dynamic(setup, second_authorization, new=[second_candidate], replay=[first_candidate])
        assert len(setup.executor.batches) == 16
    finally:
        learner.journal.close()


def test_dynamic_empty_parent_state_file_cannot_fake_post_generation_rng(setup):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    authorization['fit_start_state']['rng_sha256'] = 'f'*64
    setup.executor.state['rng_sha256'] = 'f'*64
    with pytest.raises(ValueError, match='loaded_boundary_optimizer_RNG_binding'):
        execute_dynamic(setup, authorization)
    assert setup.executor.batches == []


def test_dynamic_new_exclusion_cannot_be_removed_later(setup):
    dynamic_policy(setup)
    setup.evidence['excluded_task_ids'] = ['additional_CPU_exclusion']
    create(setup)
    first = execute_dynamic(setup, authorize_batch(setup))
    second = authorize_batch(setup, 1, first)
    second['excluded_task_ids'] = []
    with pytest.raises(ValueError, match='cannot_remove_previous_exclusions'):
        prepare_dynamic(setup, second, new=[], replay=[setup.candidate])


def test_dynamic_failed_batch_cannot_take_new_authorization(setup):
    dynamic_policy(setup)
    create(setup)
    setup.executor.fail_update = True
    authorization = authorize_batch(setup)
    with pytest.raises(RuntimeError):
        execute_dynamic(setup, authorization)
    authorization['trusted_artifacts']['/unread/fresh_reference'] = 'f'*64
    with pytest.raises(ValueError, match='existing_or_uncertain'):
        execute_dynamic(setup, authorization)
    assert len(setup.executor.batches) == 1


def test_dynamic_no_offpolicy_fallback_for_unauthorized_source(setup):
    dynamic_policy(setup)
    setup.authority['allow_off_policy_new'] = False
    create(setup)
    with pytest.raises(ValueError, match='off_policy_NEW_not_authorized'):
        execute_dynamic(setup, authorize_batch(setup))
    assert setup.executor.batches == []


def test_dynamic_frozen_own_generation_then_zero_update_fit(setup, tmp_path, monkeypatch):
    setup.authority['mode'] = 'frozen'
    learner = SyntheticContinuingLearner(setup, tmp_path, monkeypatch)
    try:
        candidate, authorization = learner.generate_round(0)
        setup.executor.update = Mock(side_effect=AssertionError('frozen update forbidden'))
        result = execute_dynamic(setup, authorization, new=[candidate])['commit']
        assert result['before_state'] == result['after_state'] == authorization['fit_start_state']
        assert result['on_policy_new_rows'] == 1
        assert result['updates'] == result['on_policy_rounds'] == result['simulated_on_policy_rounds'] == 0
        assert result['presentations'] == {} and result['anchor_token_exposures'] == 0
        setup.executor.update.assert_not_called()
    finally:
        learner.journal.close()


def test_dynamic_batch_cannot_override_trainer_policy(setup):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    authorization['source_pins'] = {}
    with pytest.raises(ValueError, match='exact_batch_evidence_authorization'):
        prepare_dynamic(setup, authorization)


def test_dynamic_fit_start_checkpoint_cannot_escape_fork(setup, tmp_path):
    dynamic_policy(setup)
    create(setup)
    authorization = authorize_batch(setup)
    authorization['fit_start_checkpoint'] = checkpoint(tmp_path/'outside_post_generation', initial_state())
    with pytest.raises(ValueError, match='post_generation_checkpoint_inside_fork'):
        prepare_dynamic(setup, authorization)


def test_dynamic_authorization_size_is_capped_by_policy(setup):
    dynamic_policy(setup)
    limits = fit.Limits(max_payload_bytes=100)
    setup.authority['fit_limits'] = fit.asdict(limits)
    fit.create_fork(setup.authority, expected_authority_sha256=fit.digest(setup.authority), limits=limits)
    with pytest.raises(ValueError, match='batch_authorization_budget'):
        prepare_dynamic(setup, authorize_batch(setup), limits=limits)
