import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r135_a40r_context_epoch as epoch


def fixture(physical):
    config = epoch.slot(physical)
    messages = [dict(role='system', content='Original system verbatim.'),
        dict(role='user', content=json.dumps(dict(focus='Original pending instruction.',
            actual_train_episodes=['earlier context'], own_prior_reflection='older full memory'))),
        dict(role='user', content='Actual earlier parent advice')]
    raw = 'Beginning. ' + 'Whole actual child reflection. ' * 300 + ' End.'
    call = dict(status='COMPLETE', purpose='reflection', cycle=config['cycle'], number=config['native'],
        task_id=f"TRAIN-REFLECTION-{config['cycle']}-1", adapter_state=None, base_sha256=epoch.BASE_SHA,
        response=dict(messages=messages, raw=raw, input_truncated=False, full_prompt_prefix_verified=True))
    request = dict(payload=dict(split='TRAIN', cycle=config['cycle'], turn=2,
        mode='METACOGNITION_CONVERSATION', messages=messages + [dict(role='assistant', content=raw)],
        episodes=[dict(task_id='TRAIN-pending')]))
    receipt = dict(number=config['parent'], cycle=config['cycle'], turn=2, status=config['disposition'])
    response = dict(status='COMPLETE', plan=dict(guidance='Consumed guidance',
        episode_guidance={'TRAIN-pending': 'Consumed pending advice'}))
    return call, request, receipt, response


def counters(physical):
    config = epoch.slot(physical)
    return dict(native_completed=config['native'], parent_completed=80 if physical == 0 else 93,
        parent_missing=30 if physical == 0 else 32, train_segments=722 if physical == 0 else 819,
        train_episodes=106 if physical == 0 else 120, held_episodes=200 if physical == 0 else 228,
        sleeps=50 if physical == 0 else 57, optimizer_updates=0, triples=108 if physical == 0 else 123,
        semantic_verified_changes=None)


def rows(physical):
    config = epoch.slot(physical)
    return [dict(lane=epoch.LANE, kind=kind, number=number, cycle=config['cycle'])
        for kind, final in [('NATIVE', config['native']), ('PARENT', config['parent'])]
        for number in range(1, final + 1)]


def ready():
    return dict(learned=False, base=dict(verified=True, expected_base_sha256=epoch.BASE_SHA,
        model_dir=epoch.MODEL), model_dir=epoch.MODEL, context=32768, output_cap=8192,
        native_cap=16384, parent_cap=640, cycles=256, reflection_turns=2,
        native_deadline_unix=1789754280.0, hard_deadline_unix=1789754400.0, lease_end_unix=1789776000.0)


@pytest.mark.parametrize('physical', [0, 2])
def test_complete_child_original_system_instruction_and_full_archive(physical):
    inputs = fixture(physical)
    original = deepcopy(inputs)
    call, request, receipt, response = inputs
    carry = epoch.compact_context(physical, *inputs)
    assert inputs == original
    assert carry['messages'][0] == request['payload']['messages'][0]
    assert carry['messages'][1]['content'] == epoch.NOTICE + 'Original pending instruction.'
    assert carry['messages'][2] == dict(role='assistant', content=call['response']['raw'])
    assert carry['full_pending_messages'][:-1] == request['payload']['messages']
    assert carry['parent_receipt'] == receipt
    assert carry['context_changed'] and not carry['compiler_summary']
    assert not carry['identical_context_claim']
    assert carry['advice'] == ('Consumed guidance\nConsumed pending advice' if physical == 0 else '')


def test_missing_127_never_reads_late_complete_plan():
    class LateResponse(dict):
        def __getitem__(self, key):
            pytest.fail('Late parent content was accessed')

    call, request, receipt, response = fixture(2)
    carry = epoch.compact_context(2, call, request, receipt, LateResponse(response))
    assert carry['messages'][-1] == dict(role='user', content='')
    assert carry['full_pending_messages'][-1] == dict(role='user', content='')
    assert carry['parent_receipt']['status'] == 'MISSING'
    assert carry['late_parent_consumed'] is False
    assert carry == epoch.compact_context(2, call, request, receipt, None)


@pytest.mark.parametrize('physical', [0, 2])
@pytest.mark.parametrize('mutation', ['child_tail', 'prefix', 'split', 'cycle', 'turn', 'number',
    'adapter', 'base', 'parent_disposition', 'truncated', 'task'])
def test_carry_rejects_wrong_causality_or_frozen_state(physical, mutation):
    call, request, receipt, response = fixture(physical)
    if mutation == 'child_tail':
        request['payload']['messages'][-1]['content'] = call['response']['raw'][-100:]
    elif mutation == 'prefix':
        request['payload']['messages'] = [dict(role='system', content='synthetic')] + request['payload']['messages']
    elif mutation in ('split', 'cycle', 'turn'):
        request['payload'][mutation] = 'HELD' if mutation == 'split' else -1
    elif mutation == 'number':
        call['number'] -= 1
    elif mutation == 'adapter':
        call['adapter_state'] = {'adapter': 'not permitted'}
    elif mutation == 'base':
        call['base_sha256'] = 'other'
    elif mutation == 'parent_disposition':
        receipt['status'] = 'MISSING' if physical == 0 else 'COMPLETE'
    elif mutation == 'truncated':
        call['response']['input_truncated'] = True
    elif mutation == 'task':
        call['task_id'] = 'TRAIN-REFLECTION-other'
    with pytest.raises(ValueError):
        epoch.compact_context(physical, call, request, receipt, response)


@pytest.mark.parametrize('physical', [0, 2])
def test_cursor_preserves_all_charged_and_missing_counters(physical):
    inherited = counters(physical)
    assert epoch.validate_cursor(physical, rows(physical), inherited) == inherited
    for broken in [rows(physical)[1:], rows(physical) + [dict(lane=epoch.LANE, kind='NATIVE',
            number=epoch.slot(physical)['native'] + 1, cycle=epoch.slot(physical)['cycle'])]]:
        with pytest.raises(ValueError):
            epoch.validate_cursor(physical, broken, inherited)
    with pytest.raises(ValueError):
        epoch.validate_cursor(physical, rows(physical), dict(inherited, optimizer_updates=1))


@pytest.mark.parametrize('physical', [0, 2])
def test_slot_host_uuid_wrapper_and_root_fail_closed(physical):
    config = epoch.slot(physical)
    inventory = dict(physical=physical, uuid=config['uuid'])
    relocation = dict(target_physical=physical, target_uuid=config['uuid'], target_wrapper='gpu/a40r_ssh.sh')
    epoch.validate_scope(physical, epoch.HOST_SHA, inventory, relocation)
    for host, devices, moved in [('wrong', inventory, relocation),
            (epoch.HOST_SHA, dict(inventory, uuid=epoch.slot(2 if physical == 0 else 0)['uuid']), relocation),
            (epoch.HOST_SHA, dict(inventory, physical=7), relocation),
            (epoch.HOST_SHA, inventory, dict(relocation, target_wrapper='other')),
            (epoch.HOST_SHA, inventory, dict(relocation, target_physical=7))]:
        with pytest.raises(ValueError):
            epoch.validate_scope(physical, host, devices, moved)
    with pytest.raises(ValueError):
        epoch.directory(physical, '/other')
    with pytest.raises(ValueError):
        epoch.directory(physical, lane='a100_1')


@pytest.mark.parametrize('physical', [1, 3, 7, True, '0'])
def test_unowned_slot_rejected(physical):
    with pytest.raises(ValueError):
        epoch.slot(physical)


@pytest.mark.parametrize('key,value', [('learned', True), ('model_dir', 'other'), ('context', 65536),
    ('output_cap', 16384), ('native_cap', 16385), ('parent_cap', 641), ('cycles', 257),
    ('reflection_turns', 3), ('native_deadline_unix', 1789754281.0), ('hard_deadline_unix', 1789754401.0),
    ('lease_end_unix', 1789776001.0)])
def test_caps_base_and_deadlines_cannot_change(key, value):
    epoch.validate_ready(ready(), 1789500000)
    altered = ready()
    altered[key] = value
    with pytest.raises(ValueError):
        epoch.validate_ready(altered, 1789500000)


def test_expired_deadline_and_wrong_base_rejected():
    with pytest.raises(ValueError):
        epoch.validate_ready(ready(), 1789754280.0)
    altered = ready()
    altered['base']['expected_base_sha256'] = 'other'
    with pytest.raises(ValueError):
        epoch.validate_ready(altered, 1789500000)


@pytest.mark.parametrize('count', [0, 32768, 40000])
def test_oversized_whole_carry_fails_without_clipping(count):
    carry = epoch.compact_context(0, *fixture(0))
    original = deepcopy(carry)
    tokenizer = SimpleNamespace(apply_chat_template=lambda *args, **kwargs: list(range(count)))
    with pytest.raises(ValueError, match='whole_compact_prompt'):
        epoch.token_fit(tokenizer, carry)
    assert carry == original


def test_token_fit_uses_actual_complete_prompt_and_original_budget():
    carry = epoch.compact_context(2, *fixture(2))

    def tokenize(messages, **options):
        assert messages == carry['messages']
        assert options == dict(tokenize=True, add_generation_prompt=True, return_dict=False)
        return [1] * 32767

    result = epoch.token_fit(SimpleNamespace(apply_chat_template=tokenize), carry)
    assert result['effective_output_cap'] == 1
    assert result['model_calls'] == result['parent_calls'] == 0


def original_source():
    path = Path(__file__).resolve().parents[1] / 'gpu/orch_r109_route_run.py'
    text = path.read_text()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == epoch.DEPENDENCY_PINS['gpu/orch_r109_route_run.py']
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'native')
    return ast.get_source_segment(text, node)


@pytest.mark.parametrize('physical', [0, 2])
def test_frozen_source_seam_preserves_engine_and_future_loop(physical):
    source = epoch.native_source(original_source(), physical)
    compile(source, 'r135-seam', 'exec')
    assert 'for cycle in range(' + str(epoch.slot(physical)['cycle']) in source
    assert "group=frozen['train'][cycle-1]" in source
    assert "group=frozen['held'][cycle-1]" in source
    assert 'assert_no_adapter(engine.model)' in source
    assert "native_engine.generate(engine,actual,reflection=purpose=='reflection')" in source
    assert 'identical_context_claim=False' in source
    assert "parent_missing']+=1" in source
    assert "counters['parent_missing'] = 0" not in source
    with pytest.raises(ValueError):
        epoch.native_source('def native(root,lane):\n    pass\n', physical)


@pytest.mark.parametrize('physical', [0, 2])
def test_pending_turn_executes_once_no_train_or_parent_replay(tmp_path, monkeypatch, physical):
    class Boundary(Exception):
        pass

    class StopHeld:
        def __getitem__(self, index):
            raise Boundary('test_completed_pending_cycle')

    class NoTrainReplay:
        def __getitem__(self, index):
            pytest.fail('Historical train replay')

    config = epoch.slot(physical)
    campaign = tmp_path / 'epoch'
    campaign.mkdir()
    carry = epoch.compact_context(physical, *fixture(physical))
    written, reserved, generated = {}, [], []

    def read(path):
        if path.name == 'READY.json':
            return dict(learned=False, files={}, model_dir='fixture', native_deadline_unix=1000, hard_deadline_unix=1120)
        if path.name == 'COHORT.json':
            return dict(train=NoTrainReplay(), held=StopHeld())
        pytest.fail(str(path))

    def generate(engine, messages, reflection):
        assert reflection
        generated.append(deepcopy(messages))
        return dict(raw='New native continuation', input_truncated=False, full_prompt_prefix_verified=True)

    def reserve(root, lane, kind, detail):
        assert kind == 'NATIVE' and not reserved
        reserved.append(detail)
        return dict(number=config['native'] + 1, kind=kind, **detail)

    def restore(actual, state):
        actual.update(counters(physical))
        state['memory'] = carry['messages'][2]['content']

    policy = SimpleNamespace(allocation=lambda lane: config['uuid'], VERSION='original', BASE_SHA=epoch.BASE_SHA,
        require=epoch.require, CYCLES=256, token_budget=lambda count: 512, digest=lambda value: 'hash',
        PRINCIPLES_SHA='principles', due=lambda *args, **kwargs: False)
    engine = SimpleNamespace(model=object(), tokenizer=SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [1]))
    namespace = dict(verify=lambda *args: None, policy=policy, os=os, epoch_directory=lambda *args: campaign,
        read=read, write=lambda path, value: written.update({path.name: deepcopy(value)}), sha=lambda path: 'hash',
        time=SimpleNamespace(time=lambda: 10), BoundReached=Boundary, epoch_restore=restore,
        epoch_carry=lambda: carry, epoch_archive_reference=lambda: {'sha256': 'archive'},
        portable=SimpleNamespace(source=SimpleNamespace(native=SimpleNamespace(load_local_tokenizer=lambda path: None))),
        native_engine=SimpleNamespace(BaseEngine=lambda *args, **kwargs: engine, generate=generate),
        assert_no_adapter=lambda model: None, parent=lambda *args: pytest.fail('parent replay'),
        reserve=reserve, json=json)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', config['uuid'])
    exec(compile(epoch.native_source(original_source(), physical), 'r135-native-test', 'exec'), namespace)
    namespace['native'](tmp_path, epoch.LANE)
    assert len(reserved) == len(generated) == 1
    assert reserved[0]['task_id'] == f"TRAIN-REFLECTION-{config['cycle']}-2"
    assert generated[0] == carry['messages']
    checkpoint = written[f"CHECKPOINT_C{config['cycle']}.json"]
    assert checkpoint['native_completed'] == config['native'] + 1
    assert checkpoint['parent_completed'] == counters(physical)['parent_completed']
    assert checkpoint['parent_missing'] == counters(physical)['parent_missing']
    assert checkpoint['train_episodes'] == counters(physical)['train_episodes']
    assert checkpoint['sleeps'] == counters(physical)['sleeps'] + 1
    assert checkpoint['optimizer_updates'] == 0 and checkpoint['adapter'] is None
    assert written[f"CALL_{config['native'] + 1:06d}.json"]['context_epoch'] == epoch.LABEL
    assert written[f"{config['parent']:05d}.json"]['parent']['status'] == config['disposition']


@pytest.mark.parametrize('physical', [0, 2])
@pytest.mark.parametrize('conflict', ['none', 'intent', 'call', 'wrong_first'])
def test_first_reservation_checks_full_prefix_under_lock(tmp_path, monkeypatch, physical, conflict):
    ledger = tmp_path / 'RESERVATIONS.jsonl'
    content = ''.join(json.dumps(row) + '\n' for row in rows(physical))
    ledger.write_text(content)
    config = dict(epoch.slot(physical), root=str(tmp_path), ledger_sha=hashlib.sha256(content.encode()).hexdigest())
    monkeypatch.setitem(epoch.SLOTS, physical, config)
    module = SimpleNamespace(old=SimpleNamespace(policy=SimpleNamespace(NATIVE_CAP=16384),
        reserve=lambda *args: pytest.fail('First reservation delegated unsafely')))
    reserve = epoch.first_native_reserver(module, physical)
    detail = dict(cycle=config['cycle'], purpose='reflection', task_id=f"TRAIN-REFLECTION-{config['cycle']}-2")
    if conflict == 'intent':
        with ledger.open('a') as stream:
            stream.write(json.dumps(dict(kind='PARENT', number=config['parent'] + 1)) + '\n')
    elif conflict == 'call':
        path = tmp_path / 'other_campaign/native'
        path.mkdir(parents=True)
        (path / f"CALL_{config['native'] + 1:06d}.json").write_text('{}')
    elif conflict == 'wrong_first':
        detail['purpose'] = 'train_episode'
    before = ledger.read_bytes()
    if conflict != 'none':
        with pytest.raises(ValueError):
            reserve(tmp_path, epoch.LANE, 'NATIVE', detail)
        assert ledger.read_bytes() == before
    else:
        result = reserve(tmp_path, epoch.LANE, 'NATIVE', detail)
        assert result['number'] == config['native'] + 1
        assert ledger.read_bytes().startswith(before)
        assert len(ledger.read_text().splitlines()) == len(rows(physical)) + 1


def test_prepare_and_verify_cli_have_no_launch_side_effects(monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'not-empty')
    with pytest.raises(ValueError, match='CPU_only_prepare'):
        epoch.prepare(0)
    source = Path(epoch.__file__).read_text()
    tree = ast.parse(source)
    prepare = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'prepare')
    calls = [node.func.id for node in ast.walk(prepare) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert not {'native', 'guard', 'scan', 'publication', 'first_native_reserver'}.intersection(calls)
    assert "choices=('prepare', 'verify', 'native', 'guard', 'scan')" in source


def disk_fixture(tmp_path, monkeypatch, physical):
    config = dict(epoch.slot(physical), root=str(tmp_path / 'lane'))
    monkeypatch.setitem(epoch.SLOTS, physical, config)
    root = Path(config['root'])
    prior = root / config['prior_version'] / ('campaign_' + epoch.LANE)
    (prior / 'native').mkdir(parents=True)
    (prior / 'parent_queue').mkdir()
    (root / 'source').mkdir()
    monkeypatch.setattr(epoch, 'SOURCE_TREE', root / 'source')
    (root / 'lease_r120_v2').mkdir(exist_ok=True)
    monkeypatch.setattr(epoch, 'scope', lambda index: epoch.slot(index))
    failed = dict(counters(physical), error=dict(type='ValueError', message='uncropped_context_fit'))
    records = {'READY.json': ready(), 'FAILED.json': failed,
        'TERMINAL.json': dict(status='FAILED'), 'LAUNCH.json': dict(pid=999999999, uuid=config['uuid']),
        'GUARD_LAUNCH.json': dict(pid=999999998), f"CHECKPOINT_C{config['checkpoint']}.json": dict(adapter=None)}
    records['READY.json']['files'] = {}
    call, request, receipt, response = fixture(physical)
    call_name = f"native/CALL_{config['native']:06d}.json"
    records[call_name] = call
    for name, value in records.items():
        epoch.write(prior / name, value)
    for key, name in [('ready_sha', 'READY.json'), ('failed_sha', 'FAILED.json'),
            ('terminal_sha', 'TERMINAL.json'), ('call_sha', call_name)]:
        config[key] = epoch.sha(prior / name)
    ledger = root / 'RESERVATIONS.jsonl'
    ledger.write_text(''.join(json.dumps(row) + '\n' for row in rows(physical)))
    config['ledger_sha'] = epoch.sha(ledger)
    epoch.write(root / 'SOURCE_SHA256.json', {})
    monkeypatch.setattr(epoch, 'MANIFEST_SHA', epoch.sha(root / 'SOURCE_SHA256.json'))
    epoch.write(root / 'lease_r120_v2/RELOCATION.json', {})
    request_path = prior / 'parent_queue' / f"GUIDED_SLEEP_C{config['cycle']}_P{config['parent']}.request.json"
    epoch.write(request_path, request)
    receipt['request_sha256'] = epoch.sha(request_path)
    response_path = request_path.with_name(request_path.name.replace('.request.', '.response.'))
    if physical == 0:
        archive = root / 'parent_transcripts/consumed'
        archive.mkdir(parents=True)
        epoch.write(archive / 'PLAN.json', response['plan'])
        response['archive'] = dict(remote_root=str(archive), files={'PLAN.json': epoch.sha(archive / 'PLAN.json')})
        response['request_sha256'] = epoch.sha(request_path)
        receipt['archive'] = response['archive']
        epoch.write(response_path, response)
        receipt['response_sha256'] = epoch.sha(response_path)
    else:
        response_path.write_text('invalid late content must never be parsed')
    epoch.write(prior / f"PARENT_{config['parent']:05d}.json", receipt)
    return root, prior, config


@pytest.mark.parametrize('physical', [0, 2])
def test_disk_evidence_join_preserves_missing_even_with_invalid_late_file(tmp_path, monkeypatch, physical):
    root, prior, config = disk_fixture(tmp_path, monkeypatch, physical)
    before = (root / 'RESERVATIONS.jsonl').read_bytes()
    result = epoch.fresh_evidence(physical)
    assert result['counters'] == counters(physical)
    assert result['carry']['parent_receipt']['status'] == config['disposition']
    assert (root / 'RESERVATIONS.jsonl').read_bytes() == before
    assert not epoch.directory(physical).exists()


def test_exact_existing_shared_source_symlink_is_accepted_not_arbitrary_alias(tmp_path, monkeypatch):
    root, prior, config = disk_fixture(tmp_path, monkeypatch, 2)
    source = root / 'source'
    policy = source / 'policy.py'
    policy.write_text('FROZEN = True\n')
    (root / 'SOURCE_SHA256.json').write_text(json.dumps({'policy.py': epoch.sha(policy)}))
    monkeypatch.setattr(epoch, 'MANIFEST_SHA', epoch.sha(root / 'SOURCE_SHA256.json'))
    shared = tmp_path / 'exact_original_source'
    source.rename(shared)
    source.symlink_to(shared, target_is_directory=True)
    monkeypatch.setattr(epoch, 'SOURCE_TREE', shared)
    assert epoch.fresh_evidence(2)['counters'] == counters(2)
    monkeypatch.setattr(epoch, 'SOURCE_TREE', tmp_path / 'unapproved_source')
    with pytest.raises(ValueError, match='exact_original_shared_source_target'):
        epoch.fresh_evidence(2)


def test_shared_source_individual_file_redirect_fails_closed(tmp_path, monkeypatch):
    root, prior, config = disk_fixture(tmp_path, monkeypatch, 2)
    outside = tmp_path / 'other_policy.py'
    outside.write_text('same bytes do not authorize another source path\n')
    (root / 'source/policy.py').symlink_to(outside)
    (root / 'SOURCE_SHA256.json').write_text(json.dumps({'policy.py': epoch.sha(outside)}))
    monkeypatch.setattr(epoch, 'MANIFEST_SHA', epoch.sha(root / 'SOURCE_SHA256.json'))
    with pytest.raises(ValueError, match='original_source_unchanged'):
        epoch.fresh_evidence(2)


@pytest.mark.parametrize('conflict', ['next_call', 'ledger', 'response_join', 'checkpoint_adapter'])
def test_disk_preflight_rejects_conflicts_without_writing(tmp_path, monkeypatch, conflict):
    root, prior, config = disk_fixture(tmp_path, monkeypatch, 0)
    if conflict == 'next_call':
        (prior / f"native/CALL_{config['native'] + 1:06d}.json").write_text('{}')
    elif conflict == 'ledger':
        with (root / 'RESERVATIONS.jsonl').open('a') as stream:
            stream.write('{}\n')
    elif conflict == 'response_join':
        path = prior / f"PARENT_{config['parent']:05d}.json"
        data = epoch.read(path)
        data['request_sha256'] = 'incorrect'
        path.write_text(json.dumps(data))
    elif conflict == 'checkpoint_adapter':
        (prior / f"CHECKPOINT_C{config['checkpoint']}.json").write_text(json.dumps(dict(adapter={'lora': True})))
    with pytest.raises(ValueError):
        epoch.fresh_evidence(0)
    assert not epoch.directory(0).exists()


@pytest.mark.parametrize('physical', [0, 2])
def test_prepare_end_to_end_CPU_only_and_epoch_tamper_rejected(tmp_path, monkeypatch, physical):
    root, prior, config = disk_fixture(tmp_path, monkeypatch, physical)
    source_root = tmp_path / 'source'
    (source_root / 'gpu').mkdir(parents=True)
    (source_root / 'tests').mkdir()
    source = source_root / 'gpu/orch_r135_a40r_context_epoch.py'
    source.write_bytes(Path(epoch.__file__).read_bytes())
    tests = source_root / 'tests/test_orch_r135_a40r_context_epoch.py'
    tests.write_text('synthetic CPU test evidence')
    monkeypatch.setattr(epoch, '__file__', str(source))
    epoch.write(source_root / 'CPU_TESTS.json', dict(exit_code=0, source_sha256=epoch.sha(source),
        tests_sha256=epoch.sha(tests)))
    model = tmp_path / 'model'
    model.mkdir()
    (model / 'tokenizer.json').write_text('{}')
    monkeypatch.setattr(epoch, 'MODEL', str(model))
    data = epoch.read(prior / 'READY.json')
    data['model_dir'] = data['base']['model_dir'] = str(model)
    (prior / 'READY.json').write_text(json.dumps(data))
    config['ready_sha'] = epoch.sha(prior / 'READY.json')
    monkeypatch.setattr(epoch, 'DEPENDENCY', source_root)
    monkeypatch.setattr(epoch, 'dependencies', lambda: None)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    original_getsource = epoch.inspect.getsource
    fake_native = lambda: None
    monkeypatch.setattr(epoch.inspect, 'getsource', lambda function: original_source()
        if function is fake_native else original_getsource(function))
    module = SimpleNamespace(old=SimpleNamespace(native=fake_native, verify=lambda *args: None))
    monkeypatch.setattr(epoch, 'runtime', lambda physical: module)
    tokenizer = SimpleNamespace(apply_chat_template=lambda *args, **kwargs: [1] * 1234)

    def load_tokenizer(model_dir, **kwargs):
        assert kwargs == dict(local_files_only=True, trust_remote_code=False)
        return tokenizer

    monkeypatch.setitem(epoch.sys.modules, 'transformers', SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=load_tokenizer)))
    ledger_before = (root / 'RESERVATIONS.jsonl').read_bytes()
    result = epoch.prepare(physical)
    output = epoch.directory(physical)
    assert result['launch_authorized'] is False
    assert result['token_fit']['prompt_tokens'] == 1234
    assert (output / 'READY.json').read_bytes() == (prior / 'READY.json').read_bytes()
    assert epoch.read(output / 'CARRY.json')['parent_receipt']['status'] == config['disposition']
    assert epoch.read(output / 'ARCHIVE_CONTEXT.json')['full_pending_messages']
    assert not any((output / name).exists() for name in ('PUBLICATION.json', 'native', 'GUARD_ONCE', 'NATIVE_ONCE'))
    assert (root / 'RESERVATIONS.jsonl').read_bytes() == ledger_before
    assert epoch.verify(physical, pristine=True)['counters'] == counters(physical)
    with pytest.raises(ValueError, match='new_epoch_only'):
        epoch.prepare(physical)
    data = epoch.read(output / 'EPOCH.json')
    data['counters']['parent_missing'] = 0
    (output / 'EPOCH.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='unchanged_failed_cursor'):
        epoch.verify(physical)
