"""CPU fixtures only; real staged adapter tests generate TRAIN tasks in tmp_path."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_r159_train_service as service
from gpu import orch_r158_train_gym as gym
from gpu.orch_r150_matched_journal import MatchedJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import PRESLEEP_INVITATIONS, experiment_binding
from organism_v6.orch_r150_matched_stream import MatchedStream


BINDING = dict(package_version='0.1.25', package_source_sha256='a'*64, split_ledger_sha256='b'*64)


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gym.encoded(document)+b'\n')
    return service.reference(path)


@pytest.fixture
def life(tmp_path, monkeypatch):
    base = tmp_path/'orch_r158_service_fixture'
    root = base/'unparented_learning'
    root.mkdir(parents=True)
    source = base/'source'
    repository = Path(service.__file__).resolve().parents[1]
    for relative in service.SOURCE_FILES:
        target = source/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository/relative, target)
    plan = dict(schema='R125_NATIVE_CONTINUITY_V1', root=str(root), source_root=str(source),
        matched_arm=root.name, hard_end_unix=time.time()+1800, lease_end_unix=time.time()+3600)
    cohort = dict(schema='R150_MATCHED_CONTINUAL_COHORT_V1', fresh_histories=True,
        initial_optimizer_steps=0, evaluations_gate_continuation=False,
        initial_directory=str(base/'common_initial'), common=dict(source_root=str(source)),
        members={arm: dict(root=str(base/arm)) for arm in service.ARMS})
    cohort_ref = write(base/'COHORT.json', cohort)
    plan['matched_cohort'] = cohort_ref
    plan_ref = write(base/'unparented_learning.PLAN.json', plan)
    commit = write(base/'common_initial/COMMIT.json', dict(schema='SYNTHETIC_INITIAL_CHECKPOINT'))
    capacity = dict(schema='R151_MATCHED_INITIAL_CAPACITY_V1', status='PASS', state_restored=True,
        restoration_status='VERIFIED', optimizer_updates=0, generation_calls=0, stream_data_written=False,
        synthetic_shape_only=True, scientific_evaluation=False, plan_sha256=plan_ref['sha256'])
    capacity_ref = write(base/'common_initial/capacity_validation/RESULT.json', capacity)
    observation = dict(optimizer_steps=0, adapter_state_sha256='e'*64)
    write(base/'common_initial/INITIALIZED.json', dict(schema=cohort['schema'], cohort_sha256=cohort_ref['sha256'],
        checkpoint_commit_sha256=commit['sha256'], source_plan_sha256=plan_ref['sha256'],
        generation_calls=0, optimizer_updates=0, observed_initial_state=observation,
        initialization_validation=dict(capacity_ref, schema=capacity['schema'], status='PASS')))
    write(base/'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json',
        dict(status='SERVICE_EXIT_VERIFIED', cgroup_empty_verified=True, service_returncode=0))
    write(root/'INITIAL_STATE_VERIFIED.json', dict(observation, arm=root.name, cohort_sha256=cohort_ref['sha256']))
    experiment = experiment_binding(dict(seed=37, presleep_variant='free_distillation',
        compaction_invitation=PRESLEEP_INVITATIONS['free_distillation'], system_prompt='Synthetic CPU TRAIN context.',
        birth_prompt='Investigate supplied problems.'))
    initial = dict(checkpoint_sha256=dict(adapter='c'*64, optimizer='d'*64, rng='e'*64), optimizer_steps=0,
        adapter_state_sha256='f'*64, experiment=experiment)
    stream = MatchedStream(TrainHistory(system_prompt=experiment['system_prompt'], birth_prompt=experiment['birth_prompt']),
        arm=root.name, cohort_sha256=cohort_ref['sha256'], initial_checkpoint=initial,
        context_limit=16384, segment_tokens=512, segments_per_sleep=1000,
        deadline_unix=plan['hard_end_unix'], model_state_sha256=service._digest(initial['checkpoint_sha256']),
        experiment=experiment)
    journal = MatchedJournal(root/'stream', arm=root.name, cohort_sha256=cohort_ref['sha256'], create=True)
    journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
    config = service.prepare(plan_ref, 'one-synthetic-owner', time.time()+1200)
    real_dataset = gym.dataset
    toy = SimpleNamespace(score_answer=lambda answer, entry: 1.0 if answer == '4' else 0.0)
    monkeypatch.setattr(gym, 'dataset', lambda index: (toy, dict(question='What is two plus two?', answer='4'), deepcopy(BINDING)))
    calls = []

    def api(action, task_index=0, response_index=None):
        calls.append((action, task_index, response_index))
        if action == 'preflight':
            return dict(schema='R159_STAGED_GYM_PREFLIGHT_V1', binding=deepcopy(BINDING),
                origins={name: str(source/name) for name in service.SOURCE_FILES if name.endswith('.py')},
                task_ids=[gym.task_id(index) for index in range(3)], offered=False, checked=False)
        if action == 'offer':
            return gym.offer(root, task_index)
        return gym.check(root, task_index, response_index)

    case = SimpleNamespace(root=root, base=base, source=source, stream=stream, journal=journal,
        config=config, calls=calls, api=api, real_dataset=real_dataset, services=[])
    yield case
    for watcher in case.services:
        watcher.close()
    journal.close()


def start(life, *, fresh=True, api=None):
    watcher = service.Service(life.config, fresh=fresh, api=life.api if api is None else api)
    life.services.append(watcher)
    return watcher


def generate(life, raw='No submission.', *, incoming=True, terminal=True, truncated=False, defer_commit=False):
    captured = []

    def record(kind, document):
        if kind == 'COMMITTED' and defer_commit:
            captured.append(document)
        else:
            life.journal.record(kind, document)

    life.stream.step(lambda *args, **kwargs: dict(raw=raw,
        token_ids=[10]*512 if truncated else [10, 11, 2], terminal=terminal, truncated=truncated),
        lambda messages: sum(len(message['content'].split())+4 for message in messages), record,
        incoming=life.journal.read_inbox() if incoming else (), now=time.time)
    return captured


def drain(watcher):
    for unused in range(1000):
        if watcher.state['terminal'] is not None:
            break
        if watcher.state['phase'] != 'OFFER' and watcher.state['cursor'] > watcher.head():
            break
        watcher.tick()
    else:
        pytest.fail('bounded fixture drain did not settle')
    return watcher.state


def checks(life):
    return [call for call in life.calls if call[0] == 'check']


def test_actual_journal_stays_writer_owned_and_history_read_only(life):
    watcher = start(life)
    before = {path.name: path.read_bytes() for path in (life.root/'stream/records').iterdir()}
    watcher.tick()
    assert watcher.state['offers'] == 1
    assert before == {path.name: path.read_bytes() for path in (life.root/'stream/records').iterdir()}
    generate(life, 'Reasoning.\nAnswer: 4')
    before = {path.name: path.read_bytes() for path in (life.root/'stream/records').iterdir()}
    drain(watcher)
    assert checks(life) and watcher.state['accepted'] is True
    assert before == {path.name: path.read_bytes() for path in (life.root/'stream/records').iterdir()}
    assert life.stream.rows[-1]['prefix_loss'] is False
    assert life.stream.rows[-1]['actor'] == 'child'


def test_future_only_skips_preexisting_responses_and_resumes_without_replay(life):
    generate(life, 'Answer: 4')
    watcher = start(life)
    floor = watcher.state['floor']
    drain(watcher)
    assert not checks(life) and watcher.state['exposures'] == 0
    generate(life, 'Answer: 4')
    drain(watcher)
    saved = watcher.state['cursor']
    watcher.close()
    resumed = start(life, fresh=False)
    assert resumed.state['cursor'] == saved > floor
    for unused in range(5):
        assert resumed.tick()['status'] == 'WAIT_FUTURE'
    assert len(checks(life)) == 1
    assert [call[0] for call in life.calls].count('offer') == 1


def test_pending_uncommitted_answer_is_not_judged(life):
    watcher = start(life)
    watcher.tick()
    pending = generate(life, 'Answer: 4', defer_commit=True)
    drain(watcher)
    assert not checks(life) and watcher.state['exposures'] == 0
    life.journal.record('COMMITTED', pending[0])
    drain(watcher)
    assert len(checks(life)) == 1 and watcher.state['exposures'] == 1


def test_inflight_before_owner_is_never_a_future_candidate(life):
    pending = generate(life, 'Answer: 4', defer_commit=True)
    watcher = start(life)
    watcher.tick()
    life.journal.record('COMMITTED', pending[0])
    drain(watcher)
    assert watcher.state['exposures'] == 0 and not checks(life)


@pytest.mark.parametrize('raw,terminal,truncated', [
    ('Answer: 4\n', False, True), ('<answer>4</answer>', False, False),
    ('I think the answer is 4', True, False), ('<answer>4', True, False),
    ('Answer: 4\nAnswer:', True, False), ('<answer>4</answer>\n<answer>5', True, False),
])
def test_no_heuristic_answer_or_partial_judging(life, raw, terminal, truncated):
    watcher = start(life)
    watcher.tick()
    generate(life, raw, terminal=terminal, truncated=truncated)
    drain(watcher)
    assert not checks(life) and watcher.state['exposures'] == 1
    assert list((life.root/'train_environment/task_000000').glob('answer_*')) == []


@pytest.mark.parametrize('raw', ['Answer: 4', 'ACT: 4\n', '<answer>4</answer>', 'Answer: 2\nFINAL ANSWER: 4'])
def test_fixed_helper_declaration_semantics(life, raw):
    watcher = start(life)
    watcher.tick()
    generate(life, raw)
    drain(watcher)
    assert watcher.state['accepted'] is True and len(checks(life)) == 1


def test_no_answer_waits_future_instead_of_regrading_old_response(life):
    watcher = start(life)
    watcher.tick()
    generate(life)
    drain(watcher)
    for unused in range(5):
        watcher.tick()
    assert watcher.state['exposures'] == 1 and not checks(life)
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['exposures'] == 2 and len(checks(life)) == 1


def test_six_exposures_abandon_without_invented_score_or_feedback(life):
    watcher = start(life)
    watcher.tick()
    for unused in range(6):
        generate(life)
        drain(watcher)
    assert watcher.state['exposures'] == 6 and watcher.state['offers'] == 1
    assert not checks(life) and watcher.state['feedback'] is None
    assert len(list((life.root/'stream/inbox').glob('*.json'))) == 1
    generate(life)
    drain(watcher)
    assert watcher.state['offers'] == 2
    assert watcher.state['outcomes'] == [dict(task_index=0, observation='NO_SUBMISSION/ABANDONED',
        checked=0, checker_attempts=0, exposed_responses=6)]
    assert 'score' not in str(watcher.state['outcomes'])


def test_accepted_requires_later_actual_feedback_render_not_queue(life):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['feedback'] is not None
    generate(life, 'Answer: 4', incoming=False)
    drain(watcher)
    assert watcher.state['offers'] == 1 and len(checks(life)) == 1
    generate(life, 'I saw the actual feedback.')
    drain(watcher)
    assert watcher.state['offers'] == 2
    assert watcher.state['outcomes'][0]['observation'] == 'ACCEPTED'


def test_pending_feedback_barrier_survives_six_exposures(life):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 2')
    drain(watcher)
    for unused in range(7):
        generate(life, incoming=False)
        drain(watcher)
    assert watcher.state['offers'] == 1 and watcher.state['exposures'] == 6
    assert len(checks(life)) == 1 and watcher.state['feedback'] is not None
    generate(life, 'Acknowledged the failed check.')
    drain(watcher)
    assert watcher.state['offers'] == 2
    assert watcher.state['outcomes'][0]['observation'] == 'ABANDONED_AFTER_CHECK'


def test_two_checked_answers_advance_only_after_second_feedback(life):
    watcher = start(life)
    drain(watcher)
    generate(life, 'Answer: 2')
    drain(watcher)
    generate(life, 'Revise after feedback.\nAnswer: 3')
    drain(watcher)
    assert watcher.state['task_checks'] == 2 and watcher.state['offers'] == 1
    generate(life, 'Answer: 4', incoming=False)
    drain(watcher)
    assert len(checks(life)) == 2 and watcher.state['offers'] == 1
    generate(life, 'I received the second failed check.')
    drain(watcher)
    assert watcher.state['offers'] == 2
    assert watcher.state['outcomes'][0]['observation'] == 'TWO_CHECKED'


def test_last_task_global_forty_eight_check_cap(life):
    watcher = start(life)
    watcher.state.update(task_index=23, offers=23, check_calls=46)
    watcher.append('SYNTHETIC_CAP_FRONTIER')
    drain(watcher)
    generate(life, 'Answer: 2')
    drain(watcher)
    generate(life, 'Answer: 3')
    drain(watcher)
    generate(life, 'I received the second failed check.')
    drain(watcher)
    assert watcher.state['terminal']['status'] == 'COMPLETE'
    assert watcher.state['offers'] == 24 and watcher.state['check_calls'] == 48
    assert [call[1] for call in life.calls if call[0] == 'offer'] == [23]
    assert len(set(checks(life))) == 2
    before = list(life.calls)
    watcher.tick()
    assert life.calls == before


def test_all_twenty_four_offer_indices_are_fixed_and_sequential(life):
    watcher = start(life)
    for index in range(24):
        watcher.tick()
        assert watcher.state['task_index'] == index
        watcher.state.update(exposures=6, last_commit=watcher.state['cursor']-1)
        watcher.advance()
    assert [call[1] for call in life.calls if call[0] == 'offer'] == list(range(24))
    assert watcher.state['offers'] == 24 and not checks(life)
    assert watcher.state['terminal']['status'] == 'COMPLETE'


@pytest.mark.parametrize('action', ['offer', 'check'])
@pytest.mark.parametrize('timing', ['before', 'after'])
def test_uncertain_exception_never_retries_even_when_publication_exists(life, action, timing):
    def broken(current, task_index=0, response_index=None):
        if current == action:
            if timing == 'after':
                life.api(current, task_index, response_index)
            raise RuntimeError('synthetic uncertain side effect')
        return life.api(current, task_index, response_index)

    watcher = start(life, api=broken)
    watcher.tick()
    if action == 'check':
        generate(life, 'Answer: 4')
        drain(watcher)
    assert watcher.state['terminal']['status'] == 'UNCERTAIN_NO_RETRY'
    before = list(life.calls)
    watcher.close()
    resumed = start(life, fresh=False)
    resumed.tick()
    assert life.calls == before


def test_crash_after_durable_intent_is_terminal_on_resume(life):
    def interrupted(action, task_index=0, response_index=None):
        if action == 'offer':
            raise KeyboardInterrupt()
        return life.api(action, task_index, response_index)

    watcher = start(life, api=interrupted)
    with pytest.raises(KeyboardInterrupt):
        watcher.tick()
    assert watcher.state['pending_action']['action'] == 'offer'
    watcher.close()
    before = list(life.calls)
    resumed = start(life, fresh=False)
    assert resumed.state['terminal']['status'] == 'UNCERTAIN_NO_RETRY'
    assert life.calls == before


def test_helper_no_complete_answer_consumes_attempt_but_waits_future(life):
    def no_answer(action, task_index=0, response_index=None):
        if action == 'check':
            life.calls.append((action, task_index, response_index))
            return dict(status='NO_COMPLETE_ANSWER', checked=False, response_index=response_index)
        return life.api(action, task_index, response_index)

    watcher = start(life, api=no_answer)
    watcher.tick()
    generate(life, 'Answer: 4')
    drain(watcher)
    for unused in range(3):
        watcher.tick()
    assert watcher.state['checked'] == 0 and watcher.state['task_checks'] == 1
    assert watcher.state['feedback'] is None and len(checks(life)) == 1


def test_single_owner_nonblocking_and_manual_task_zero_refused(life):
    watcher = start(life)
    with pytest.raises(BlockingIOError):
        start(life, fresh=False)
    with pytest.raises(FileExistsError):
        start(life)
    gym.offer(life.root, 0)
    watcher.tick()
    assert watcher.state['terminal']['status'] == 'STOPPED_NO_RETRY'
    assert [call for call in life.calls if call[0] == 'offer'] == []


def test_fresh_owner_refuses_existing_manual_environment(life):
    gym.offer(life.root, 0)
    with pytest.raises(ValueError, match='no_prior_offers'):
        start(life)
    assert not (life.root/'train_service_r159').exists()


@pytest.mark.parametrize('field', ['INITIALIZED.json', 'INITIAL_STATE_VERIFIED.json', 'LIFECYCLE.json'])
def test_absent_activation_gate_does_not_create_service(life, field):
    key = {'INITIALIZED.json': 'initialized', 'INITIAL_STATE_VERIFIED.json': 'birth', 'LIFECYCLE.json': 'lifecycle'}[field]
    Path(life.config[key]['path']).unlink()
    with pytest.raises(FileNotFoundError):
        start(life)
    assert not (life.root/'train_service_r159').exists() and not life.calls


@pytest.mark.parametrize('key,field,value', [('lifecycle', 'service_returncode', 1),
    ('lifecycle', 'cgroup_empty_verified', False), ('birth', 'cohort_sha256', '0'*64),
    ('initialized', 'generation_calls', 1)])
def test_unadmitted_or_unclean_birth_is_rejected(life, key, field, value):
    path = Path(life.config[key]['path'])
    document = json.loads(path.read_bytes())
    document[field] = value
    life.config[key] = write(path, document)
    with pytest.raises(ValueError):
        start(life)
    assert not life.calls


def test_capacity_failure_and_absent_life_never_start(life):
    path = life.base/'common_initial/capacity_validation/RESULT.json'
    document = json.loads(path.read_bytes())
    document['status'] = 'FAIL'
    reference = write(path, document)
    initialized_path = Path(life.config['initialized']['path'])
    initialized = json.loads(initialized_path.read_bytes())
    initialized['initialization_validation'].update(reference)
    life.config['initialized'] = write(initialized_path, initialized)
    with pytest.raises(ValueError, match='actual_capacity_PASS'):
        start(life)
    life.config['root'] = str(life.base/'parented_learning')
    with pytest.raises(ValueError, match='existing_born_life'):
        start(life)
    assert not Path(life.config['root']).exists()


@pytest.mark.parametrize('change', ['owner', 'source', 'service', 'caps', 'deadline'])
def test_resume_bound_config_and_source_hashes(life, change):
    watcher = start(life)
    watcher.close()
    if change == 'owner':
        life.config['owner_id'] = 'other-owner'
    elif change == 'source':
        (life.source/'organism_v6/bootstrap_reasoning_gym.txt').write_text('tampered')
    elif change == 'service':
        life.config['service_sha256'] = '0'*64
    elif change == 'caps':
        life.config['caps']['tasks'] = 25
    else:
        life.config['deadline_unix'] += 1
    with pytest.raises(ValueError):
        start(life, fresh=False)
    assert [call[0] for call in life.calls] == ['preflight']


def test_wall_expiry_persists_terminal_without_helper_call(life):
    watcher = start(life)
    watcher.clock = lambda: life.config['deadline_unix']
    watcher.tick()
    assert watcher.state['terminal']['status'] == 'STOPPED_NO_RETRY'
    assert 'wall' in watcher.state['terminal']['reason']
    assert [call[0] for call in life.calls] == ['preflight']


@pytest.mark.parametrize('budget', ['read_bytes', 'record_reads', 'output_bytes', 'polls', 'ledger_bytes'])
def test_runtime_budgets_stop_without_additional_external_actions(life, budget):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 4')
    before = list(life.calls)
    if budget == 'ledger_bytes':
        watcher.ledger_bytes = life.config['limits'][budget]-65536
    elif budget == 'output_bytes':
        watcher.state['output_reserved'] = life.config['limits'][budget]
    else:
        watcher.state[budget] = life.config['limits'][budget]
    drain(watcher)
    assert watcher.state['terminal']['status'] == 'STOPPED_NO_RETRY'
    assert life.calls == before


def test_oversized_record_fails_before_read_or_check(life):
    watcher = start(life)
    watcher.tick()
    path = life.root/'stream/records'/f"{watcher.state['cursor']:020d}.json"
    with path.open('wb') as output:
        output.truncate(life.config['limits']['record_bytes']+1)
    watcher.tick()
    assert 'bounded_record_bytes' in watcher.state['terminal']['reason']
    assert not checks(life)


def test_background_readout_envelope_not_counted_or_followed(life):
    watcher = start(life)
    watcher.tick()
    record = dict(schema='R125_STREAM_JOURNAL_V1', journal_id=watcher.state['identity']['journal_id'],
        index=watcher.state['cursor'], previous_sha256=watcher.state['previous_record'], kind='READOUT',
        document=dict(path='/do/not/open/sealed/readout.json', response=dict(raw='Answer: 4')))
    record['sha256'] = service._digest(record)
    write(life.root/'stream/records'/f"{record['index']:020d}.json", record)
    assert watcher.tick()['status'] == 'BACKGROUND_NOT_COUNTED'
    assert watcher.state['exposures'] == 0 and not checks(life)


def test_task_must_be_rendered_not_merely_queued(life):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 4', incoming=False)
    drain(watcher)
    assert watcher.state['exposures'] == 0 and not checks(life)
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['exposures'] == 1 and len(checks(life)) == 1


def test_child_quoting_feedback_cannot_forge_environment_exposure(life):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 4')
    drain(watcher)
    generate(life, watcher.state['feedback']['text'], incoming=False)
    drain(watcher)
    generate(life, 'It appeared in my previous response.', incoming=False)
    drain(watcher)
    assert watcher.state['offers'] == 1 and watcher.state['feedback'] is not None


@pytest.mark.parametrize('changed', ['target', 'journal_id', 'previous_sha256'])
def test_forged_response_or_forward_chain_stops_without_check(life, changed):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 4')
    records = sorted((life.root/'stream/records').glob('*.json'))
    path = next(path for path in records if json.loads(path.read_bytes()).get('kind') == 'RESPONSE')
    record = json.loads(path.read_bytes())
    if changed == 'target':
        record['document']['response']['raw'] = 'Answer: 5'
    else:
        record[changed] = '0'*(32 if changed == 'journal_id' else 64)
        record['sha256'] = service._digest({key: value for key, value in record.items() if key != 'sha256'})
    path.chmod(0o600)
    path.write_bytes(gym.encoded(record))
    drain(watcher)
    assert watcher.state['terminal']['status'] == 'STOPPED_NO_RETRY' and not checks(life)


@pytest.mark.parametrize('field,value', [('accepted', False), ('status', 'PROPOSED'), ('result_path', '/wrong/RESULT.json')])
def test_checker_return_must_match_actual_receipt_and_full_path(life, field, value):
    def mismatched(action, task_index=0, response_index=None):
        result = life.api(action, task_index, response_index)
        if action == 'check':
            result[field] = value
        return result

    watcher = start(life, api=mismatched)
    watcher.tick()
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['terminal']['status'] == 'UNCERTAIN_NO_RETRY'
    assert watcher.state['pending_action']['action'] == 'check'


def test_verifier_exception_is_not_zero_or_feedback(life, monkeypatch):
    def failed(*args, **kwargs):
        raise ArithmeticError('synthetic verifier exception')

    watcher = start(life)
    watcher.tick()
    monkeypatch.setattr(gym, 'grade', failed)
    generate(life, 'Answer: 4')
    drain(watcher)
    assert watcher.state['terminal']['status'] == 'UNCERTAIN_NO_RETRY'
    assert watcher.state['checked'] == 0 and watcher.state['feedback'] is None
    assert list((life.root/'train_environment/task_000000').glob('answer_*/RESULT.json')) == []


def test_growing_record_cannot_bypass_reserved_read_size(life, monkeypatch):
    watcher = start(life)
    watcher.tick()
    generate(life, 'Answer: 4')
    original = service.bounded_record

    def grow(directory, index, limit):
        path = life.root/'stream/records'/f'{index:020d}.json'
        path.chmod(0o600)
        with path.open('ab') as output:
            output.write(b' '*100)
        return original(directory, index, limit)

    monkeypatch.setattr(service, 'bounded_record', grow)
    watcher.tick()
    assert watcher.state['terminal']['status'] == 'STOPPED_NO_RETRY' and not checks(life)


def test_torn_owner_ledger_refuses_automatic_recovery(life):
    watcher = start(life)
    watcher.close()
    (watcher.directory/'99999999.json.partial').write_bytes(b'{')
    with pytest.raises(ValueError, match='incomplete_ledger'):
        start(life, fresh=False)
    assert not (life.root/'train_environment').exists()


def test_expired_resume_records_stop_without_offering(life):
    watcher = start(life)
    watcher.close()
    resumed = service.Service(life.config, fresh=False, api=life.api,
        clock=lambda: life.config['deadline_unix']+1)
    life.services.append(resumed)
    resumed.tick()
    assert resumed.state['terminal']['status'] == 'STOPPED_NO_RETRY'
    assert not (life.root/'train_environment').exists()


def test_staged_helper_timeout_kills_only_its_local_process(life, monkeypatch):
    monkeypatch.setattr(service, 'HELPER_SCRIPT', 'import time; time.sleep(20)')
    life.config['limits']['helper_seconds'] = 1
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        service.StagedGym(life.config)('preflight')
    assert time.monotonic()-started < 5


def test_helper_stdout_budget_is_enforced(life, monkeypatch):
    monkeypatch.setattr(service, 'HELPER_SCRIPT', 'print("x" * 200000)')
    with pytest.raises(ValueError, match='helper_output_budget'):
        service.StagedGym(life.config)('preflight')


def test_frozen_helper_bytes_are_not_substitutable(life):
    path = life.source/'gpu/orch_r158_train_gym.py'
    path.write_bytes(path.read_bytes()+b'\n')
    life.config['sources']['gpu/orch_r158_train_gym.py'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='staged_source_inventory'):
        start(life)
    assert not life.calls


def test_missing_bootstrap_fails_staged_preflight_before_offers(life):
    (life.source/'organism_v6/bootstrap_reasoning_gym.txt').unlink()
    with pytest.raises(FileNotFoundError):
        start(life)
    assert not (life.root/'train_environment').exists()


def test_staged_import_schema_failure_is_terminal_not_mocked_success(life):
    life.config['python'] = str(Path(sys.executable).resolve())
    life.config['dependency_paths'] = []
    api = service.StagedGym(life.config)
    broken = deepcopy(life.config)
    broken['sources']['gpu/orch_r158_train_gym.py'] = '0'*64
    with pytest.raises(ValueError, match='helper_failure'):
        service.StagedGym(broken)('preflight')
    assert not (life.root/'train_environment').exists()
    assert callable(api)


def real_dependencies():
    import reasoning_gym
    return [str(Path(reasoning_gym.__file__).resolve().parents[1])]


def test_actual_staged_helper_full_path_preflight_and_three_TRAIN_families(life):
    life.config['dependency_paths'] = real_dependencies()
    watcher = start(life, api=service.StagedGym(life.config))
    assert watcher.state['terminal'] is None
    assert watcher.state['generator_binding']['package_version'] == '0.1.25'
    for index in range(3):
        drain(watcher)
        assert watcher.state['task_index'] == index
        unused_source, entry, unused_binding = life.real_dataset(index)
        generate(life, '<answer>'+str(entry['answer'])+'</answer>')
        drain(watcher)
        assert watcher.state['accepted'] is True, watcher.state['terminal']
        generate(life, 'I received the actual TRAIN check result.')
        drain(watcher)
    assert watcher.state['check_calls'] == 3 and watcher.state['offers'] == 4
    assert len(watcher.state['outcomes']) == 3
    assert all(item['observation'] == 'ACCEPTED' for item in watcher.state['outcomes'])


def test_actual_staged_preflight_CLI_no_activation(life):
    life.config['dependency_paths'] = real_dependencies()
    config_path = life.base/'service.CONFIG.json'
    write(config_path, life.config)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    completed = subprocess.run([sys.executable, '-B', '-m', 'gpu.orch_r159_train_service', 'preflight',
        '--config', str(config_path)], env=environment, capture_output=True, timeout=60)
    assert completed.returncode == 0, completed.stderr.decode()
    result = json.loads(completed.stdout)
    assert result['schema'] == 'R159_STAGED_GYM_PREFLIGHT_V1'
    assert result['origins']['gpu/orch_r158_train_gym.py'] == str(life.source/'gpu/orch_r158_train_gym.py')
    assert not (life.root/'train_environment').exists()
    assert not (life.root/'train_service_r159').exists()
