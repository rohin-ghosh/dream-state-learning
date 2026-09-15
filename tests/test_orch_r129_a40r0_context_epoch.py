import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r129_a40r0_context_epoch as epoch


def fixture():
    messages = [dict(role='system', content='Reflect.'),
        dict(role='user', content=json.dumps(dict(focus='Continue reflecting.', actual_train_episodes=['archived']))),
        dict(role='user', content='Original parent109')]
    raw = 'Complete child reflection. ' * 300
    call = dict(status='COMPLETE', purpose='reflection', cycle=52,
        response=dict(messages=messages, raw=raw))
    request = dict(payload=dict(split='TRAIN', cycle=52, turn=2, mode='METACOGNITION_CONVERSATION',
        messages=messages + [dict(role='assistant', content=raw)], episodes=[dict(task_id='TRAIN-parent110')]))
    response = dict(status='COMPLETE', plan=dict(guidance='Current guidance',
        episode_guidance={'TRAIN-parent110': 'Current pending turn'}))
    return call, request, response


def test_full_child_reflection_not_summary_or_tail():
    call, request, response = fixture()
    original = deepcopy((call, request, response))
    carry = epoch.compact_context(call, request, response)
    assert carry['messages'][2]['content'] == call['response']['raw']
    assert carry['messages'][-1]['content'] == 'Current guidance\nCurrent pending turn'
    assert carry['instruction'] == 'Continue reflecting.'
    assert carry['context_changed'] and not carry['compiler_summary']
    assert carry['full_pending_messages'][:-1] == request['payload']['messages']
    assert (call, request, response) == original


@pytest.mark.parametrize('mutation', ['incomplete', 'held', 'wrong_turn', 'changed_child', 'missing_parent'])
def test_invalid_source_never_admitted(mutation):
    call, request, response = fixture()
    if mutation == 'incomplete':
        call['status'] = 'FAILED'
    elif mutation == 'held':
        request['payload']['split'] = 'HELD'
    elif mutation == 'wrong_turn':
        request['payload']['turn'] = 1
    elif mutation == 'changed_child':
        request['payload']['messages'][-1]['content'] = 'short summary'
    else:
        response['status'] = 'MISSING'
    with pytest.raises(ValueError):
        epoch.compact_context(call, request, response)


def rows():
    return [dict(kind='NATIVE', number=number, cycle=52) for number in range(1, 2006)] + [
        dict(kind='PARENT', number=number, cycle=52) for number in range(1, 111)]


def counters():
    return dict(native_completed=2005, parent_completed=78, parent_missing=30, train_segments=711,
        train_episodes=104, held_episodes=196, sleeps=49, optimizer_updates=0, triples=108,
        semantic_verified_changes=None)


def test_unreserved_2006_and_counters_not_recounted():
    inherited = counters()
    assert epoch.validate_cursor(rows(), inherited) == inherited
    with pytest.raises(ValueError):
        epoch.validate_cursor(rows() + [dict(kind='NATIVE', number=2006, cycle=52)], inherited)
    with pytest.raises(ValueError):
        epoch.validate_cursor(rows()[1:], inherited)


def test_other_lane_cannot_use_epoch():
    with pytest.raises(ValueError):
        epoch.directory(epoch.ROOT, 'a100_1')
    with pytest.raises(ValueError):
        epoch.directory(Path('/other'), epoch.LANE)


def original_source():
    path = Path(__file__).resolve().parents[1] / 'gpu/orch_r109_route_run.py'
    text = path.read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'native')
    return ast.get_source_segment(text, node)


def test_frozen_native_seam_compiles_and_preserves_future_loop():
    original = original_source()
    source = epoch.native_source(original)
    compile(source, 'epoch-fixture', 'exec')
    assert 'range(52,policy.CYCLES+1)' in source
    assert "state['pending_parent'] = pending['parent_receipt']" in source
    assert "group=frozen['train'][cycle-1]" in source
    assert "group=frozen['held'][cycle-1]" in source
    assert "native_engine.sleep(" in source
    assert "assert_no_adapter(engine.model)" in source
    assert "identical_context_claim=False" in source


def test_actual_first_call_2006_no_old_episodes_or_parent_replay(tmp_path, monkeypatch):
    class Boundary(Exception):
        pass

    class StopHeld:
        def __getitem__(self, key):
            raise Boundary('test_completed_C52_boundary')

    class NoTrainReplay:
        def __getitem__(self, key):
            raise AssertionError('C52 TRAIN replay')

    campaign = tmp_path / 'epoch'
    campaign.mkdir()
    call, request, response = fixture()
    carry = epoch.compact_context(call, request, response)
    carry['parent_receipt'] = dict(number=110, status='COMPLETE')
    written, reserved, generated = {}, [], []
    ready = dict(learned=False, files={}, model_dir='fixture', native_deadline_unix=1000,
        hard_deadline_unix=1120)

    def read(path):
        if path.name == 'READY.json':
            return ready
        if path.name == 'COHORT.json':
            return dict(train=NoTrainReplay(), held=StopHeld())
        raise AssertionError(path)

    def generate(engine, messages, reflection):
        generated.append(deepcopy(messages))
        return dict(raw='New child continuation', input_truncated=False, full_prompt_prefix_verified=True)

    def reserve(root, lane, kind, detail):
        assert kind == 'NATIVE' and not reserved
        reserved.append(detail)
        return dict(number=2006, kind=kind, **detail)

    def restore(actual, state):
        actual.update(counters())
        state['memory'] = call['response']['raw']

    policy = SimpleNamespace(allocation=lambda lane: epoch.UUID, VERSION='original', BASE_SHA='base',
        require=epoch.require, CYCLES=256, token_budget=lambda count: 512, digest=lambda value: 'hash',
        PRINCIPLES_SHA='principles', due=lambda *args, **kwargs: False)
    engine = SimpleNamespace(model=object(), tokenizer=SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [1]))
    namespace = dict(verify=lambda *args: None, policy=policy, os=__import__('os'),
        epoch_directory=lambda *args: campaign, read=read, write=lambda path, value: written.update({path.name: deepcopy(value)}),
        sha=lambda path: 'hash', time=SimpleNamespace(time=lambda: 10), BoundReached=Boundary,
        epoch_restore=restore, epoch_carry=lambda: carry, epoch_carry_reference=lambda: {'sha256': 'carry'},
        portable=SimpleNamespace(source=SimpleNamespace(native=SimpleNamespace(load_local_tokenizer=lambda path: None))),
        native_engine=SimpleNamespace(BaseEngine=lambda *args, **kwargs: engine, generate=generate),
        assert_no_adapter=lambda model: None, parent=lambda *args: pytest.fail('parent110 replay'),
        reserve=reserve, json=json)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', epoch.UUID)
    exec(compile(epoch.native_source(original_source()), 'native-epoch-test', 'exec'), namespace)
    namespace['native'](tmp_path, epoch.LANE)
    assert len(reserved) == len(generated) == 1
    assert generated[0] == carry['messages']
    checkpoint = written['CHECKPOINT_C52.json']
    assert checkpoint['native_completed'] == 2006 and checkpoint['parent_completed'] == 78
    assert checkpoint['train_episodes'] == 104 and checkpoint['sleeps'] == 50
    assert checkpoint['optimizer_updates'] == 0 and checkpoint['adapter'] is None
    assert written['CALL_002006.json']['context_epoch'] == 'R129_OVERFLOW_CONTEXT_DISTILLATION'
    assert '00110.json' in written


def test_seam_drift_fails_closed():
    with pytest.raises(ValueError):
        epoch.native_source('def native(root,lane):\n    pass\n')
