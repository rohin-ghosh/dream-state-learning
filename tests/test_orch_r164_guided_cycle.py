"""Synthetic CPU protocol tests only, not genuine reviews, model episodes or training."""

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r164_guided_cycle as cycle
from gpu import orch_r161_reviewed_packet_fit as fit
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from tests.test_orch_r161_reviewed_packet_fit import (
    setup, dynamic_policy, authorize_batch, fixture_grade, fixture_offer, fixture_check,
)


class SyntheticChild:
    def __init__(self, plan, tokenizer, executor, clock, raw):
        self.plan, self.tokenizer, self.executor, self.clock, self.raw = plan, tokenizer, executor, clock, raw
        self.requests = []
        self.fail = False

    def generate(self, messages, **options):
        self.requests.append(deepcopy(messages))
        self.clock.now += 1
        self.executor.state['rng_sha256'] = fit.digest(['synthetic_generation_rng', self.clock.now])
        if self.fail:
            raise RuntimeError('synthetic uncertain generation')
        return dict(raw=self.raw, token_ids=[10, 11, 2], terminal=True, truncated=False)

    def count_tokens(self, messages):
        return len(self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))


@pytest.fixture
def prepared(setup, tmp_path, monkeypatch, request):
    toy = SimpleNamespace(score_answer=lambda answer, entry: 1.0 if answer == '4' else 0.0)
    monkeypatch.setattr(cycle.gym, 'dataset', lambda index: (toy, dict(question='What is two plus two?'),
                                                          deepcopy(setup.authority['generator_binding'])))
    monkeypatch.setattr(cycle.gym, 'grade', fixture_grade)
    monkeypatch.setattr(cycle.gym, 'offer', fixture_offer)
    monkeypatch.setattr(cycle.gym, 'check', fixture_check)
    arm = getattr(request, 'param', 'parented_learning')
    root = tmp_path/'orch_r158_r164_synthetic'/arm
    root.parent.mkdir()
    setup.root = root
    source = deepcopy(setup.authority['generation_sources'][str(setup.case.root)])
    dynamic_policy(setup)
    setup.authority.update(fork_root=str(root), allow_off_policy_new=False,
                           mode='frozen' if arm == 'parented_frozen' else 'learning')
    setup.evidence.update(trusted_artifacts={}, reviewer_provenance_by_sha256={}, generation_sources={})
    for path in (*cycle.source_paths(), Path(__file__).resolve()):
        setup.authority['source_pins'][str(path)] = fit.capture.sha(path.read_bytes())
    plan = dict(root=str(root), matched_arm=root.name, source_root=str(Path(source['plan']['path']).parent/'generating_source'),
                context_limit=4096, segment_tokens=128, segments_per_sleep=2, hard_end_unix=1000,
                presleep_variant='no_distillation', system_prompt='Synthetic guided learner.', birth_prompt='CPU only.')
    plan_path = root.parent/'PLAN.json'
    plan_path.write_bytes(fit.capture.encoded(plan))
    source['plan'] = dict(path=str(plan_path), sha256=fit.capture.sha(plan_path.read_bytes()))
    source['checkpoints'] = {}
    setup.evidence['generation_sources'][str(root)] = source
    policy_sha = fit.digest(setup.authority)
    fit.create_fork(setup.authority, expected_authority_sha256=policy_sha)
    setup.executor.fork_binding = dict(fork_root=str(root), mode=setup.authority['mode'], authority_sha256=policy_sha,
        initializer_commit_sha256=setup.authority['initializer']['commit']['sha256'])
    child = SyntheticChild(plan, setup.tokenizer, setup.executor, setup.case.clock, setup.case.row['target'])
    setup.executor.child = child
    journal = (cycle.GuidedJournal(root/'stream', expected_authority_sha256=policy_sha, create=True)
               if arm == 'parented_frozen' else StreamJournal(root/'stream', create=True))
    stream = object.__new__(ContinualStream)
    initial = json.loads(Path(setup.authority['initializer']['commit']['path']).read_bytes())
    setup.original_stream_init(stream, TrainHistory(system_prompt='Synthetic guided learner.', birth_prompt='CPU only.'),
        context_limit=4096, segment_tokens=128, segments_per_sleep=2, deadline_unix=1000,
        model_state_sha256=fit.digest(initial['checkpoint_sha256']))
    journal.record('COMMITTED', dict(state=stream.checkpoint()))
    curriculum = dict(schema=cycle.SCHEMA, authority_sha256=policy_sha, plan=source['plan'],
        capture_root=str(tmp_path/'separate_CPU_capture'), hard_end_unix=1000, max_output_bytes=8*1024**2,
        tasks=[dict(task_index=index, guidance=None if arm == 'unparented_learning' else
                    dict(speaker='Astra', text='Synthetic parent: check your arithmetic.'))
               for index in (1, 2)],
        capture_specs=[dict(response='answer', target_kind='ANSWER', label='grounded_reasoning', feedback=False)])
    options = dict(child=child, stream=stream, journal=journal, executor=setup.executor, anchors=setup.anchors,
        authority=setup.authority, expected_authority_sha256=policy_sha,
        curriculum=curriculum, expected_curriculum_sha256=fit.digest(curriculum))
    state = SimpleNamespace(setup=setup, options=options, child=child, stream=stream, journal=journal,
                            curriculum=curriculum, root=root)
    try:
        yield state
    finally:
        journal.close()


def start(prepared):
    return cycle.GuidedCycle(**prepared.options)


def external_synthetic_reviews_and_authority(prepared, runner):
    setup = prepared.setup
    candidates = []
    for number, bundle in enumerate(runner.pending['bundles']):
        setup.evidence['trusted_artifacts'].update(bundle['observed_path_hashes'])
        reviews = []
        for original in setup.case.packet['reviews']:
            document = json.loads(original['raw'])
            document['binding'] = deepcopy(bundle['review_template']['review_envelope_template']['binding'])
            path = prepared.root.parent/f'synthetic_review_{runner.index}_{number}_{document["reviewer_id"]}.json'
            path.write_bytes(fit.capture.encoded(document))
            artifact = fit.capture.eligibility.capture(str(path), path.read_bytes())
            reviews.append(artifact)
            setup.evidence['trusted_artifacts'][str(path)] = artifact['sha256']
            provenance = deepcopy(setup.case.reviewers[document['reviewer_id']])
            provenance['review_sha256'] = artifact['sha256']
            setup.evidence['reviewer_provenance_by_sha256'][artifact['sha256']] = provenance
        candidates.append(dict(packet=deepcopy(bundle['packet']), reviews=reviews))
    setup.evidence['generation_sources'][str(prepared.root)]['checkpoints'][prepared.stream.model_state_sha256] = deepcopy(runner.parent_checkpoint)
    journal_id = json.loads((prepared.root/'stream/JOURNAL.json').read_bytes())['journal_id']
    authorization = authorize_batch(setup, runner.index, runner.prior,
                                   fit_start=runner.pending['checkpoint'], journal_id=journal_id)
    return candidates, authorization


def execute(prepared, runner, replay=None):
    candidates, authorization = external_synthetic_reviews_and_authority(prepared, runner)
    result = runner.fit_pending(candidates, replay or [], batch_authorization=authorization,
                               expected_batch_authorization_sha256=fit.digest(authorization))
    return candidates, result


def test_two_continuing_synthetic_rounds_real_compiler_and_gym_protocol(prepared):
    runner = start(prepared)
    first_capture = runner.collect_next()
    assert first_capture['status'] == 'AWAITING_EXTERNAL_REVIEWS_AND_MAIN_AUTHORITY'
    assert first_capture['eligible'] is False and first_capture['answer_check']['accepted'] is True
    assert prepared.setup.executor.batches == []
    first_prefix = deepcopy(prepared.stream.rows[0]['prefix'])
    assert any('Synthetic parent:' in message['content'] for message in first_prefix)
    assert any('Training puzzle check: accepted' in message['content'] for message in prepared.child.requests[1])
    first_candidates, first = execute(prepared, runner)
    assert first['commit']['updates'] == 16 and runner.phase == 'READY'
    assert prepared.stream.sleep_frontier == len(prepared.stream.rows) == 2
    first_model = prepared.stream.model_state_sha256
    prepared.setup.case.clock.now += 1
    runner.collect_next()
    assert prepared.stream.rows[2]['model_state_sha256'] == first_model
    second_candidates, second = execute(prepared, runner, first_candidates)
    assert second['commit']['updates'] == 17 and runner.phase == 'COMPLETE'
    assert second['commit']['simulated_on_policy_rounds'] == 2 and second['commit']['on_policy_rounds'] == 0
    assert not second['commit']['training_performed'] and not second['commit']['scientific_claim']
    assert second_candidates[0]['packet']['records'][0]['raw'] != first_candidates[0]['packet']['records'][0]['raw']
    assert prepared.stream.rows[0]['prefix'] == first_prefix
    assert prepared.stream.sleep_frontier == len(prepared.stream.rows) == 4
    assert len(prepared.stream.sleep_receipts) == 2
    assert prepared.journal.latest_checkpoint()['document'] == prepared.stream.checkpoint()
    assert [batch.components[0].label for batch in prepared.setup.executor.batches] == ['NEW']*32+['REHEARSAL']
    for batch in prepared.setup.executor.batches:
        assert [component.objective_weight for component in batch.components] == [.75]+[.0625]*4


def test_capture_export_loads_without_trust_or_review_fabrication(prepared):
    receipt = start(prepared).collect_next()
    reference = receipt['captures'][0]
    loaded = fit.capture.load_packet(Path(reference['path']).parent, expected_manifest_sha256=reference['sha256'])
    assert loaded['reviews'] == []
    manifest = json.loads(Path(reference['path']).read_bytes())
    assert not manifest['trust_established'] and not manifest['reviews_generated']
    assert not manifest['verifier_replayed']


def test_no_fit_without_external_reviews_and_main_pin(prepared):
    runner = start(prepared)
    runner.collect_next()
    candidates, authorization = external_synthetic_reviews_and_authority(prepared, runner)
    with pytest.raises(ValueError, match='independent_batch_authorization_hash_required'):
        runner.fit_pending(candidates, [], batch_authorization=authorization,
                           expected_batch_authorization_sha256='0'*64)
    assert runner.phase == 'AWAITING_REVIEW' and prepared.setup.executor.batches == []
    candidates[0]['reviews'] = []
    with pytest.raises(ValueError):
        runner.fit_pending(candidates, [], batch_authorization=authorization,
                           expected_batch_authorization_sha256=fit.digest(authorization))
    assert prepared.setup.executor.batches == []


@pytest.mark.parametrize('change', ['candidate', 'rng', 'checkpoint', 'prefix'])
def test_fit_time_tamper_refuses_before_updates(prepared, change):
    runner = start(prepared)
    runner.collect_next()
    candidates, authorization = external_synthetic_reviews_and_authority(prepared, runner)
    if change == 'candidate':
        candidates[0]['packet']['label'] = 'synthetic_invalid_rewrite'
    elif change == 'rng':
        prepared.setup.executor.state['rng_sha256'] = '0'*64
    elif change == 'checkpoint':
        authorization['fit_start_checkpoint'] = runner.parent_checkpoint
    else:
        prepared.stream.rows[0]['prefix'][0]['content'] = 'changed original context'
    with pytest.raises(ValueError):
        runner.fit_pending(candidates, [], batch_authorization=authorization,
                           expected_batch_authorization_sha256=fit.digest(authorization))
    assert prepared.setup.executor.batches == []


def test_review_pause_does_not_generate_or_replay(prepared):
    runner = start(prepared)
    runner.collect_next()
    with pytest.raises(ValueError, match='cycle_not_ready'):
        runner.collect_next()
    assert len(prepared.child.requests) == 2


def test_uncertain_generation_is_terminal_never_retried(prepared):
    runner = start(prepared)
    prepared.child.fail = True
    with pytest.raises(RuntimeError, match='uncertain generation'):
        runner.collect_next()
    assert runner.phase == 'FAILED' and prepared.stream.pending is not None
    assert (prepared.root/'guided_cycles/FAILED0000.json').is_file()
    with pytest.raises(ValueError, match='cycle_not_ready'):
        runner.collect_next()
    assert len(prepared.child.requests) == 1


def test_uncertain_update_blocks_next_generation_and_commit(prepared):
    runner = start(prepared)
    runner.collect_next()
    prepared.setup.executor.fail_update = True
    with pytest.raises(RuntimeError, match='uncertain update'):
        execute(prepared, runner)
    assert runner.phase == 'FAILED'
    assert prepared.stream.sleep_frontier == 0
    assert not (prepared.root/'guided_cycles/cycle0000/COMPLETE.json').exists()
    with pytest.raises(ValueError, match='cycle_not_ready'):
        runner.collect_next()


def test_fit_commit_then_journal_failure_never_reexecutes_updates(prepared, monkeypatch):
    runner = start(prepared)
    runner.collect_next()
    record = prepared.journal.record

    def failed_record(kind, document):
        if kind == 'SLEEP_COMPLETE':
            raise OSError('synthetic journal disk failure')
        return record(kind, document)

    monkeypatch.setattr(prepared.journal, 'record', failed_record)
    with pytest.raises(OSError, match='disk failure'):
        execute(prepared, runner)
    assert len(prepared.setup.executor.batches) == 16 and runner.phase == 'FAILED'
    assert (prepared.root/'batch0000/COMMIT.json').exists()
    assert prepared.stream.pending is not None
    with pytest.raises(ValueError, match='no_pending_review_boundary'):
        execute(prepared, runner)
    assert len(prepared.setup.executor.batches) == 16


def test_expired_review_wait_cannot_fit(prepared):
    runner = start(prepared)
    runner.collect_next()
    prepared.setup.case.clock.now = 1001
    with pytest.raises(ValueError, match='unexpired'):
        execute(prepared, runner)
    assert prepared.setup.executor.batches == []


@pytest.mark.parametrize('change', ['pin', 'plan', 'source', 'initializer', 'raw_history', 'context'])
def test_precollection_bindings_refuse_without_new_output(prepared, change):
    if change == 'pin':
        prepared.options['expected_curriculum_sha256'] = '0'*64
    elif change == 'plan':
        prepared.child.plan['root'] = str(prepared.setup.case.root)
    elif change == 'source':
        path = Path(next(iter(prepared.setup.authority['tokenizer_pins'])))
        path.write_text('changed pinned tokenizer artifact')
    elif change == 'initializer':
        prepared.setup.executor.state['adapter_sha256'] = '0'*64
    elif change == 'raw_history':
        prepared.stream.rows.append(deepcopy(prepared.setup.case.row))
    else:
        prepared.stream.context_limit += 1
    with pytest.raises(ValueError):
        start(prepared)
    assert not (prepared.root/'guided_cycles').exists() and prepared.child.requests == []


def test_frozen_requires_new_bound_protocol_before_collection_or_mutation(prepared):
    authority = deepcopy(prepared.setup.authority)
    authority.update(mode='frozen', fork_root=str(prepared.root.with_name('parented_frozen')))
    curriculum = deepcopy(prepared.curriculum)
    curriculum['authority_sha256'] = fit.digest(authority)
    with pytest.raises(ValueError, match='frozen_requires_bound_GuidedJournal'):
        cycle.GuidedCycle(**dict(prepared.options, authority=authority, expected_authority_sha256=fit.digest(authority),
            curriculum=curriculum, expected_curriculum_sha256=fit.digest(curriculum)))
    assert prepared.child.requests == [] and prepared.setup.executor.batches == []


def test_no_competing_coordinator_or_restart(prepared):
    start(prepared)
    with pytest.raises(ValueError, match='create_only_cycle_custody'):
        start(prepared)


def test_no_answer_records_not_claimed_accepted_or_eligible(prepared):
    runner = start(prepared)
    prepared.child.raw = 'Synthetic investigation with no answer declaration.'
    receipt = runner.collect_next()
    assert receipt['answer_check']['status'] == receipt['followup_check']['status'] == 'NO_COMPLETE_ANSWER'
    assert receipt['captures'] == [] and receipt['unavailable']
    assert receipt['eligible'] is False and prepared.setup.executor.batches == []


def test_rejected_actual_check_not_upgraded_by_capture(prepared):
    runner = start(prepared)
    prepared.child.raw = 'Synthetic mistake.\nAnswer: 2'
    receipt = runner.collect_next()
    assert receipt['answer_check']['accepted'] is False
    assert receipt['eligible'] is False
    assert prepared.setup.executor.batches == []


def test_only_explicit_curriculum_no_task_replay_or_unparented_nudge(prepared):
    authority = deepcopy(prepared.setup.authority)
    authority['fork_root'] = str(prepared.root.with_name('unparented_learning'))
    curriculum = deepcopy(prepared.curriculum)
    curriculum['authority_sha256'] = fit.digest(authority)
    with pytest.raises(ValueError, match='unparented_has_no_parent_guidance'):
        cycle.validate_curriculum(curriculum, fit.digest(curriculum), authority, fit.digest(authority))
    for task in curriculum['tasks']:
        task['guidance'] = None
    assert cycle.validate_curriculum(curriculum, fit.digest(curriculum), authority, fit.digest(authority))['runnable']
    curriculum['tasks'][1]['task_index'] = curriculum['tasks'][0]['task_index']
    with pytest.raises(ValueError, match='curriculum_no_task_replay'):
        cycle.validate_curriculum(curriculum, fit.digest(curriculum), authority, fit.digest(authority))


@pytest.mark.parametrize('prepared', ['unparented_learning'], indirect=True)
def test_unparented_learning_executes_without_parent_targets_or_guidance(prepared):
    runner = start(prepared)
    runner.collect_next()
    candidates, result = execute(prepared, runner)
    assert result['commit']['updates'] == 16
    assert all(row['actor'] == 'child' for row in prepared.stream.rows)
    assert not any(event.actor == 'parent' for event in prepared.stream.history.events)
    assert not (prepared.root/'guided_cycles/cycle0000/GUIDANCE_PUBLICATION.json').exists()
    assert candidates[0]['packet']['reviews'] == []


@pytest.mark.parametrize('prepared', ['unparented_learning'], indirect=True)
def test_unparented_foreign_parent_inbox_stops_before_generation(prepared):
    runner = start(prepared)
    cycle.gym.console.publish_parent(prepared.root, 'Astra', 'Synthetic forbidden parent contamination.')
    with pytest.raises(ValueError, match='unparented_inbox_contamination'):
        runner.collect_next()
    assert prepared.child.requests == [] and runner.phase == 'FAILED'


def test_reflection_capture_joins_actual_rendered_feedback_no_target_rewrite(prepared):
    prepared.curriculum['capture_specs'] = [dict(response='followup', target_kind='POST_FEEDBACK_REFLECTION',
                                                label='grounded_reasoning', feedback=False)]
    prepared.options['expected_curriculum_sha256'] = fit.digest(prepared.curriculum)
    runner = start(prepared)
    receipt = runner.collect_next()
    packet = runner.pending['bundles'][0]['packet']
    assert packet['target_kind'] == 'POST_FEEDBACK_REFLECTION' and receipt['captures']
    row = json.loads(packet['records'][2]['raw'])['document']['state']['state']['rows'][-1]
    assert row == prepared.stream.rows[-1] and row['target'] == prepared.child.raw
    assert any('Training puzzle check: accepted' in message['content'] for message in row['prefix'])
    assert prepared.setup.executor.batches == []


def matched_inputs(prepared):
    authorities, curricula = {}, {}
    for arm in cycle.ARMS:
        authority, curriculum = deepcopy(prepared.setup.authority), deepcopy(prepared.curriculum)
        authority.update(fork_root=str(prepared.root.with_name(arm)), mode='frozen' if arm == 'parented_frozen' else 'learning')
        curriculum.update(authority_sha256=fit.digest(authority), capture_root=str(prepared.root.parent.parent/f'captures_{arm}'))
        if arm == 'unparented_learning':
            for task in curriculum['tasks']:
                task['guidance'] = None
        authorities[arm], curricula[arm] = authority, curriculum
    return authorities, curricula


def test_matched_triplet_reports_interfaces_not_admission(prepared):
    authorities, curricula = matched_inputs(prepared)
    report = cycle.validate_matched(curricula, {arm: fit.digest(value) for arm, value in curricula.items()},
                                   authorities, {arm: fit.digest(value) for arm, value in authorities.items()})
    assert report['all_three_interfaces_supported'] and report['status'] == 'CONFIGURATION_COMPARISON_NOT_ADMISSION'
    assert report['arms']['parented_frozen']['journal_requirement'] == 'GuidedJournal'
    assert prepared.child.requests == []


@pytest.mark.parametrize('field', ['initializer', 'anchors_sha256', 'tokenizer_sha256', 'generator_binding'])
def test_matched_triplet_common_inputs_must_match(prepared, field):
    authorities, curricula = matched_inputs(prepared)
    authorities['unparented_learning'][field] = 'changed'
    curricula['unparented_learning']['authority_sha256'] = fit.digest(authorities['unparented_learning'])
    with pytest.raises(ValueError, match='matched_common_'):
        cycle.validate_matched(curricula, {arm: fit.digest(value) for arm, value in curricula.items()},
                               authorities, {arm: fit.digest(value) for arm, value in authorities.items()})


def test_installed_generator_mismatch_no_offer_no_generation(prepared, monkeypatch):
    runner = start(prepared)
    monkeypatch.setattr(cycle.gym, 'dataset', lambda index: (None, None, {'untrusted': True}))
    with pytest.raises(ValueError, match='installed_TRAIN_generator_authority'):
        runner.collect_next()
    assert not (prepared.root/'train_environment').exists() and prepared.child.requests == []


def test_existing_uncertain_verifier_intent_never_replayed(prepared):
    runner = start(prepared)
    directory = cycle.gym.directory(prepared.root, 1)
    directory.mkdir(parents=True)
    (directory/'TASK.json').write_text('synthetic prior uncertain offer')
    with pytest.raises(FileExistsError):
        runner.collect_next()
    assert prepared.child.requests == [] and runner.phase == 'FAILED'


def test_output_budget_exhaustion_does_not_retry_capture_or_call(prepared):
    prepared.curriculum['max_output_bytes'] = 16384
    prepared.options['expected_curriculum_sha256'] = fit.digest(prepared.curriculum)
    runner = start(prepared)
    with pytest.raises(ValueError, match='output_budget'):
        runner.collect_next()
    assert runner.phase == 'FAILED' and len(prepared.child.requests) == 2
    assert list(Path(prepared.curriculum['capture_root']).iterdir()) == []


def test_existing_native_frozen_boundary_cannot_be_truthfully_committed(prepared):
    runner = start(prepared)
    runner.collect_next()
    checkpoint = json.loads(Path(runner.pending['checkpoint']['path']).read_bytes())
    receipt = dict(status='COMPLETE', optimizer_steps=0, no_update_reason='frozen_control', presentations={},
        child_token_exposures=0, anchor_token_exposures=0, checkpoint=checkpoint,
        checkpoint_sha256=checkpoint['checkpoint_sha256'],
        new_row_sha256=[row['source_sha256'] for row in prepared.stream.pending_rows()])
    with pytest.raises(ValueError, match='sleep_actual_positive_optimizer_steps'):
        prepared.stream.commit_sleep(receipt, prepared.journal.record)
    assert prepared.stream.sleep_frontier == 0 and prepared.setup.executor.batches == []


def test_existing_native_presleep_compaction_preserved_without_fitting_raw_summary(prepared, monkeypatch):
    plan_path = Path(prepared.curriculum['plan']['path'])
    prepared.child.plan.update(presleep_variant='free_distillation', compaction_invitation='Synthetic compact invitation.')
    plan_path.write_bytes(fit.capture.encoded(prepared.child.plan))
    prepared.curriculum['plan']['sha256'] = fit.capture.sha(plan_path.read_bytes())
    prepared.setup.evidence['generation_sources'][str(prepared.root)]['plan'] = deepcopy(prepared.curriculum['plan'])
    prepared.options['expected_curriculum_sha256'] = fit.digest(prepared.curriculum)
    step = prepared.stream.step

    def controlled_step(*args, **kwargs):
        kwargs['now'] = lambda: prepared.setup.case.clock.now
        return step(*args, **kwargs)

    monkeypatch.setattr(prepared.stream, 'step', controlled_step)
    runner = start(prepared)
    receipt = runner.collect_next()
    assert receipt['presleep_variant'] == 'free_distillation' and receipt['pending_raw_rows'] == 3
    assert len(prepared.child.requests) == 3
    assert any('Synthetic compact invitation.' in message['content'] for message in prepared.child.requests[-1])
    candidates, result = execute(prepared, runner)
    assert result['commit']['updates'] == 16
    assert len(prepared.stream.rows) == prepared.stream.sleep_frontier == 3
    assert result['commit']['on_policy_new_rows'] == 1


@pytest.mark.parametrize('prepared', ['parented_frozen'], indirect=True)
def test_frozen_two_rounds_exact_state_and_truthful_custom_journal(prepared):
    runner = start(prepared)
    runner.collect_next()
    first_fit_start = deepcopy(prepared.setup.executor.snapshot())
    candidates, first = execute(prepared, runner)
    assert first['commit']['updates'] == 0 and first['commit']['planned_presentations']
    assert first['commit']['before_state'] == first['commit']['after_state'] == first_fit_start
    assert prepared.setup.executor.batches == []
    assert prepared.stream.sleep_receipts[-1]['no_update_reason'] == 'frozen_control'
    first_model_state = prepared.stream.model_state_sha256
    prepared.setup.case.clock.now += 1
    runner.collect_next()
    assert prepared.stream.rows[2]['model_state_sha256'] == first_model_state
    second_fit_start = deepcopy(prepared.setup.executor.snapshot())
    unused, second = execute(prepared, runner, candidates)
    assert second['commit']['before_state'] == second['commit']['after_state'] == second_fit_start
    assert not second['commit']['training_performed'] and second['commit']['updates'] == 0
    assert second['commit']['on_policy_rounds'] == second['commit']['simulated_on_policy_rounds'] == 0
    assert prepared.setup.executor.batches == [] and len(prepared.child.requests) == 4
    assert prepared.stream.sleep_frontier == 4 and runner.phase == 'COMPLETE'
    expected = prepared.stream.checkpoint()
    prepared.journal.close()
    with cycle.GuidedJournal(prepared.root/'stream', expected_authority_sha256=runner.policy_sha) as reopened:
        assert reopened.latest_checkpoint()['document'] == expected


@pytest.mark.parametrize('prepared', ['parented_frozen'], indirect=True)
@pytest.mark.parametrize('change', ['reason', 'frontier', 'optimizer', 'checkpoint', 'commit_path', 'exposures'])
def test_frozen_custom_boundary_rejects_tamper_without_next_generation(prepared, monkeypatch, change):
    runner = start(prepared)
    runner.collect_next()
    record = prepared.journal.record

    def changed_record(kind, document):
        if kind == cycle.FROZEN_EVENT:
            document = deepcopy(document)
            if change == 'reason':
                document['no_update_reason'] = 'no_eligible_child_rows'
            elif change == 'frontier':
                document['new_row_sha256'] = []
            elif change == 'optimizer':
                document['optimizer_steps'] = 1
            elif change == 'checkpoint':
                document['checkpoint_sha256']['optimizer'] = '0'*64
            elif change == 'commit_path':
                document['reviewed_fit_commit']['path'] = str(prepared.root.parent/'external_COMMIT.json')
            else:
                document['child_token_exposures'] = 1
            document['resume_state']['state']['sleep_receipts'][-1] = {
                key: value for key, value in document.items() if key != 'resume_state'}
            document['resume_state']['sha256'] = fit.digest(document['resume_state']['state'])
        return record(kind, document)

    monkeypatch.setattr(prepared.journal, 'record', changed_record)
    with pytest.raises(ValueError):
        execute(prepared, runner)
    assert runner.phase == 'FAILED' and prepared.stream.pending is not None
    assert prepared.setup.executor.batches == [] and len(prepared.child.requests) == 2


@pytest.mark.parametrize('prepared', ['parented_frozen'], indirect=True)
def test_frozen_unbound_journal_policy_refused_on_reopen(prepared):
    prepared.journal.close()
    with pytest.raises(ValueError, match='frozen_journal_independent_policy_pin'):
        cycle.GuidedJournal(prepared.root/'stream', expected_authority_sha256='0'*64)
