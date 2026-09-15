import json
import time

import pytest

from gpu import orch_r108_code_parent_r115_run as run
from organism_v6 import orch_r108_code_parent_r115 as environment


class FakeEngine:
    def __init__(self, outputs=None):
        self.outputs = iter(outputs or ['Own reflection.'])
        self.calls = []

    def generate(self, messages, *, max_new_tokens):
        self.calls.append(dict(messages=messages, max_new_tokens=max_new_tokens))
        return dict(raw=next(self.outputs), token_ids=[1, 2], terminal=True, truncated=False,
            effective_generation_cap=max_new_tokens)


@pytest.fixture
def setup_driver(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'CPU_TEST_UUID')
    run.write(tmp_path / 'PLAN.json', dict(gpu_uuid='CPU_TEST_UUID', hard_deadline_unix=time.time()+3600,
        native_cap=100, parent_cap=100, life_id='cpu_f3', parent_model=run.broker.MODEL))
    return tmp_path


def test_r115_open_inspection_enacts_environment_then_delivers_actual_observation(setup_driver):
    task = run.policy.tasks('DEV')[0]
    engine = FakeEngine(['{"inspect":{"expression":"sum(values)","values":[4,-1,8]}}', 'The environment returned 11.'])
    driver = run.Driver(setup_driver, engine, evaluation=True)
    events = [environment.event(task, 'environment', task['prompt']),
        environment.event(task, 'child', 'Finished the task.', completed=True)]
    driver.open_turn(task, events, cycle=0, episode=0, parent_present=False, prefix='OPEN_TEST')
    receipt = run.read(setup_driver / 'environment/OPEN_TEST_OPEN.json')
    assert receipt['observation']['enacted'] is True and receipt['observation']['observation'] == 11
    assert len(engine.calls) == 2
    assert json.loads(engine.calls[1]['messages'][-1]['content'])['observation'] == 11
    assert receipt['sleep_eligible'] is False


@pytest.mark.parametrize('split,phase,origin', [('DEV','readout','DEV'),('FINAL','readout','FINAL'),
    ('DEV','open_turn','DEV'),('FINAL','open_observation','FINAL'),('TRAIN','open_turn','FINAL')])
def test_r115_dev_final_and_attached_open_never_enter_parent_or_sleep_buffer(setup_driver, split, phase, origin):
    task = dict(run.policy.tasks('TRAIN')[0], split=split)
    driver = run.Driver(setup_driver, FakeEngine(), evaluation=True)
    row = driver.capture('ISOLATED', task, phase, 0, [{'role':'user','content':'synthetic test'}],
        128, evaluation_origin=origin)
    assert row['routes']['sleep'] is False and row['routes']['parent'] is False
    assert row['routes']['optimizer'] is False and driver.sleep_buffer == []
    assert not (setup_driver / 'parent_queue').exists()


def test_r115_head_reflection_through_real_broker_binding_changes_native_decoder_cap(setup_driver, monkeypatch):
    task = run.policy.tasks('TRAIN')[0]
    fields = dict(run.policy.DEFAULT_FIELDS, REFLECTION=dict(mode='short', max_new_tokens=128))
    config = dict(life_id='cpu_f3', family='code', branch='F3', train_tasks={task['task_id']:task['content_sha256']},
        excluded_task_ids=[], cohort_sha256=run.broker.digest(run.policy.tasks('TRAIN')),
        principles_sha256=run.broker.PRINCIPLES_V2_SHA256, fallback_parent_fields=fields)
    run.write(setup_driver / 'BROKER_CONFIG.json', config)
    prompts = setup_driver / 'absent_prompts'
    events = [environment.event(task, 'child', 'My completed response.', completed=True)]

    def publish_response(seconds):
        request_path = setup_driver / 'parent_queue/CPU_PARENT.request.json'
        request = run.read(request_path)
        public = run.broker.validate_request(request, config)
        system, prompt, binding = run.broker.build_system(public, config, prompts,
            run.broker.ROOT / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md')
        archive = setup_driver / 'parent_transcripts/CPU_PARENT'
        run.write(archive / 'PROMPT_BINDING.json', binding)
        response = dict(id=request['id'], request_sha256=run.broker.digest(request),
            payload_sha256=request['payload_sha256'], status='COMPLETE', actual_model=run.broker.MODEL,
            finished_unix=time.time(), provider_dispatched=False, prompt_binding=binding,
            plan=dict(guidance='Notice what you assumed.'), transcript_receipt=dict(remote_root=str(archive),
                node_only=True, all_verified=True, files={'PROMPT_BINDING.json':run.sha(archive/'PROMPT_BINDING.json')}))
        run.write(setup_driver / 'parent_queue/CPU_PARENT.response.json', response)

    monkeypatch.setattr(run.time, 'sleep', publish_response)
    engine = FakeEngine()
    driver = run.Driver(setup_driver, engine)
    assert driver.parent('CPU_PARENT', task, events, 1, 0, 'experience') == 'Notice what you assumed.'
    driver.reflection('CPU_REFLECTION', task, 1, [{'role':'user','content':'Reflect freely.'}])
    assert driver.settings['status'] == 'BOUND_FOR_LANE_DECODER'
    assert engine.calls[0]['max_new_tokens'] == 128
    captured = run.read(setup_driver / 'reservations/CPU_REFLECTION.json')
    assert captured['requested_generation_cap'] == captured['response']['effective_generation_cap'] == 128


@pytest.mark.parametrize('raw', ['{"inspect":{"expression":"__import__(\"os\")","values":[]}}',
    '{"inspect":{"expression":"values.__class__","values":[]}}'])
def test_inspection_never_executes_generated_python(raw):
    assert environment.inspect_environment(raw)['enacted'] is False


def test_fixed_parser_does_not_salvage_prior_expression():
    assert environment.last_json('{"expression":"sum(values)"}\nnot the final format') is None


def test_forward_guard_cannot_replace_model_inputs(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(run, 'check', lambda root, phase: seen.append((root, phase)) or {'plan': True})
    assert run.forward_check(tmp_path, 'forward') is None
    assert seen == [(tmp_path, 'forward')]


def test_continuation_skips_every_previously_reserved_cycle(tmp_path):
    from gpu import orch_r108_code_parent_r115_continue as continuation
    run.write(tmp_path / 'reservations' / 'old.json', {'cycle': 3, 'status': 'STARTED'})
    run.write(tmp_path / 'reservations' / 'earlier.json', {'cycle': 2, 'status': 'FAILED'})
    assert continuation.resume_cycle(tmp_path) == 4


def test_unicode_native_request_uses_broker_canonical_hash(setup_driver, monkeypatch):
    task = run.policy.tasks('TRAIN')[0]
    captured = []

    def respond(seconds):
        path = setup_driver / 'parent_queue/UNICODE_PARENT.request.json'
        request = run.read(path)
        assert request['payload_sha256'] == run.broker.digest(request['payload'])
        captured.append(request)
        run.write(path.with_name('UNICODE_PARENT.response.json'), dict(status='MISSING',
            id=request['id'], request_sha256=run.broker.digest(request),
            payload_sha256=request['payload_sha256'], finished_unix=time.time()))

    monkeypatch.setattr(run.time, 'sleep', respond)
    events = [environment.event(task, 'child', 'I’m uncertain — what changed?', completed=True)]
    assert run.Driver(setup_driver, FakeEngine()).parent('UNICODE_PARENT', task, events,
        1, 0, 'experience') == ''
    assert len(captured) == 1
