"""CPU-only contract tests. All prompts/keys below are artificial fixtures."""

from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import pytest

from gpu import orch_guided_native as weights
from gpu import orch_r130_checkpoint_benchmark as runner


ADAPTER_SHA256 = 'a' * 64


def task(kind='exact', **scoring):
    rule = {'type': kind}
    if kind != 'behavior':
        rule.update(answer='A', response_format='text')
    if kind == 'choice':
        rule['choices'] = ['A', 'B']
    rule.update(scoring)
    return dict(task_id='fixture-' + kind, family='synthetic-only',
        messages=[dict(role='user', content='Synthetic fixture prompt.')], scoring=rule)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')
    return runner.sha(path)


class Model:
    def __init__(self):
        self.parameter = SimpleNamespace(requires_grad=False, checksum=ADAPTER_SHA256)
        self.training = False
        self.disable_adapters = False
        self.lora_A, self.lora_B = {}, {}
        self.disable_count = 0

    def parameters(self):
        return [self.parameter]

    def named_parameters(self):
        return [('model.lora_A.default.weight', self.parameter)]

    def modules(self):
        return [self]

    def requires_grad_(self, value):
        self.parameter.requires_grad = value

    @contextmanager
    def disable_adapter(self):
        self.disable_count += 1
        self.disable_adapters = True
        try:
            yield
        finally:
            self.disable_adapters = False
            self.parameter.requires_grad = True


class Engine:
    def __init__(self, gpu_uuid):
        self.model = Model()
        self.tokenizer = SimpleNamespace(eos_token_id=99, apply_chat_template=self.tokenize)
        self.torch = SimpleNamespace(cuda=SimpleNamespace(device_count=lambda: 1,
            get_device_properties=lambda index: SimpleNamespace(uuid=gpu_uuid.removeprefix('GPU-'))))
        self.calls = []
        self.base_checks = 0
        self.base_changed = False
        self.fail_at = None
        self.raw = ' A \n'
        self.after_generate = lambda response: None

    @staticmethod
    def tokenize(messages, **options):
        assert options == dict(tokenize=True, add_generation_prompt=True, return_dict=False)
        return [ord(character) for message in messages for character in message['content']]

    def verify_base(self):
        self.base_checks += 1
        if self.base_changed:
            raise ValueError('frozen_base_changed')

    def generate(self, messages, *, max_new_tokens):
        assert max_new_tokens == 512
        assert not self.model.training
        assert not any(parameter.requires_grad for parameter in self.model.parameters())
        self.calls.append((deepcopy(messages), self.model.disable_adapters))
        if len(self.calls) == self.fail_at:
            raise RuntimeError('synthetic private exception text must not reach stdout')
        response = dict(raw=self.raw, messages=deepcopy(messages), prompt_tokens=len(self.tokenize(messages,
            tokenize=True, add_generation_prompt=True, return_dict=False)),
            token_ids=[7, 8, 99], terminal=True, truncated=False)
        self.after_generate(response)
        return response


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, '_PROCESS_USED', False)
    local = tmp_path / 'copied'
    adapter = local / 'adapter'
    adapter.mkdir(parents=True)
    (adapter / 'adapter_model.safetensors').write_bytes(b'artificial safetensors fixture, never loaded')
    dump(adapter / 'adapter_config.json', {'fixture_only': True})
    files = {path.name: runner.sha(path) for path in adapter.iterdir()}
    commit = dict(schema=runner.NATIVE_SCHEMA, base_sha256=runner.BASE_SHA256,
        adapter_path='/inaccessible/original/node/checkpoints/adapter', adapter_files=files,
        adapter_state_sha256=ADAPTER_SHA256, optimizer_rng_path='/inaccessible/original/optimizer_rng.pt',
        optimizer_steps=17, checkpoint_sha256=dict(adapter=runner.digest(files), optimizer='b' * 64, rng='b' * 64))
    commit_path = local / 'COMMIT.json'
    dump(commit_path, commit)
    manifest = dict(schema=runner.MANIFEST_SCHEMA, adapter_path='adapter', commit_path='COMMIT.json',
        commit_sha256=runner.sha(commit_path))
    manifest_path = local / 'manifest.json'
    dump(manifest_path, manifest)
    corpus_path = tmp_path / 'tasks.json'
    corpus = dict(schema=runner.TASK_SCHEMA, tasks=[task('choice'), task('behavior')])
    dump(corpus_path, corpus)
    source_root = Path(runner.__file__).resolve().parents[1]
    model_dir = tmp_path / 'model'
    model_dir.mkdir()
    plan = dict(schema=runner.SCHEMA, model_id=runner.MODEL_ID, model_dir=str(model_dir),
        base_sha256=runner.BASE_SHA256, gpu_uuid='GPU-fixture-only', hard_end_unix=time.time() + 3600,
        corpus_path='tasks.json', corpus_sha256=runner.sha(corpus_path),
        manifest_path='copied/manifest.json', manifest_sha256=runner.sha(manifest_path),
        output_path=str(tmp_path / 'private-results'), source_root=str(source_root),
        sources={relative: runner.sha(source_root / relative) for relative in runner.REQUIRED_SOURCES},
        decoder=deepcopy(runner.DECODER))
    plan_path = tmp_path / 'plan.json'

    def admit():
        dump(plan_path, plan)
        monkeypatch.setenv('R130_ADMISSION_PLAN_SHA256', runner.sha(plan_path))
        monkeypatch.setenv('CUDA_VISIBLE_DEVICES', plan['gpu_uuid'])

    admit()
    engine = Engine(plan['gpu_uuid'])
    loads = []

    def load(bound_plan, checkpoint, check):
        check('mock_load')
        loads.append((deepcopy(bound_plan), deepcopy(checkpoint)))
        return engine

    monkeypatch.setattr(runner, '_load_engine', load)
    monkeypatch.setattr(weights, 'state_hash', lambda parameters: next(iter(parameters.values())).checksum)
    return SimpleNamespace(plan=plan, plan_path=plan_path, admit=admit, engine=engine, loads=loads,
        output=Path(plan['output_path']), corpus=corpus, corpus_path=corpus_path, adapter=adapter,
        commit=commit, commit_path=commit_path, manifest=manifest, manifest_path=manifest_path)


@pytest.mark.parametrize('raw,valid,correct', [
    ('A', True, True), (' A\n', True, True), ('B', True, False),
    ('a', False, None), ('Answer: A', False, None), ('A or B', False, None),
    ('<think>A</think>A', False, None), ('', False, None),
])
def test_choice_parser_never_extracts_guessed_answers(raw, valid, correct):
    score = runner.score_response(task('choice'), raw)
    assert score['parse_valid'] is valid
    assert score['correct'] is correct


def test_exact_scoring_is_not_semantic_or_case_insensitive():
    assert runner.score_response(task(), ' A \n')['correct'] is True
    assert runner.score_response(task(), 'a')['correct'] is False
    assert runner.score_response(task(), 'Answer: A')['correct'] is False
    assert runner.score_response(task(), 'other')['parse_valid'] is True


@pytest.mark.parametrize('raw,valid,correct,brier', [
    ('{"answer":"A","confidence":0.8}', True, True, 0.04),
    ('{"answer":"B","confidence":0.8}', True, False, 0.64),
    ('{"answer":"A"}', True, True, None),
    ('{"answer":"C","confidence":0.8}', False, None, None),
    ('{"answer":"A","confidence":true}', False, None, None),
    ('{"answer":"A","confidence":null}', False, None, None),
    ('{"answer":"A","confidence":2}', False, None, None),
    ('{"answer":"A","confidence":NaN}', False, None, None),
    ('{"answer":"A","confidence":1e999}', False, None, None),
    ('{"answer":"A","answer":"B"}', False, None, None),
    ('{"answer":"A","explanation":"fixture"}', False, None, None),
    ('```json\n{"answer":"A"}\n```', False, None, None),
    ('{"answer":"A"} trailing', False, None, None),
    ('["A"]', False, None, None),
    ('{"answer":1}', False, None, None),
])
def test_json_confidence_parser(raw, valid, correct, brier):
    score = runner.score_response(task('choice', response_format='json', confidence={'required': False}), raw)
    assert score['parse_valid'] is valid
    assert score['correct'] is correct
    if brier is None:
        assert score['brier'] is None
    else:
        assert score['brier'] == pytest.approx(brier)


def test_confidence_required_and_unrequested_are_explicit():
    required = task(response_format='json', confidence={'required': True})
    assert not runner.score_response(required, '{"answer":"A"}')['parse_valid']
    assert not runner.score_response(task(response_format='json'),
        '{"answer":"A","confidence":0.5}')['parse_valid']


@pytest.mark.parametrize('mutate', [
    lambda document: document['tasks'].append(deepcopy(document['tasks'][0])),
    lambda document: document['tasks'][0]['scoring'].pop('answer'),
    lambda document: document['tasks'][0]['scoring'].update(answer='C'),
    lambda document: document['tasks'][0]['scoring'].update(confidence={'required': False}),
    lambda document: document['tasks'][0]['scoring'].update(semantic_rubric='forbidden'),
    lambda document: document['tasks'][0]['messages'][0].update(role='tool'),
    lambda document: document['tasks'][0]['messages'][0].update(role='assistant'),
    lambda document: document['tasks'][1]['scoring'].update(answer='A'),
    lambda document: document.update(schema='other'),
])
def test_task_schema_rejects_ambiguous_contracts(setup, mutate):
    mutate(setup.corpus)
    with pytest.raises(ValueError):
        runner.validate_tasks(setup.corpus)


def test_behavior_is_descriptive_not_semantic_or_scored():
    response = dict(raw='<think>\n# fixture\n1. line\nrepeat\nrepeat\n```', token_ids=[1] * 6)
    metrics = runner.descriptive_metrics(response)
    assert metrics['exact_repeated_lines'] == 1
    assert metrics['exact_repeated_token_4grams'] == 2
    assert metrics['generated_tokens'] == 6
    assert metrics['response_characters'] == len(response['raw'])
    assert metrics['scaffold_pattern_indicators']['markdown_heading_lines'] == 1
    assert 'not_semantic_thought_units' in metrics['label']
    assert runner.score_response(task('behavior'), response['raw'])['correct'] is None


def test_coverage_separates_missing_failure_parse_and_correct():
    tasks = [dict(task(), task_id=str(position)) for position in range(4)]
    records = [
        dict(task_id='0', condition='LORA_ON', status='COMPLETE', response_valid=True,
            score=runner.score_response(task(), 'A')),
        dict(task_id='1', condition='LORA_ON', status='COMPLETE', response_valid=True,
            score=runner.score_response(task(), '')),
        dict(task_id='2', condition='LORA_ON', status='FAILED'),
    ]
    scores = runner.reduce_coverage(tasks, records)
    active = scores['LORA_ON']
    assert active['correct_items'] == active['parse_valid_items'] == 1
    assert active['parse_failure_items'] == active['failed_items'] == active['missing_items'] == 1
    assert active['accuracy_on_valid'] == 1
    assert active['correct_over_expected_scored'] == 0.25
    assert scores['LORA_OFF']['missing_items'] == 4
    assert scores['LORA_OFF']['accuracy_on_valid'] is None
    assert scores['LORA_OFF']['correct_over_expected_scored'] == 0
    with pytest.raises(ValueError, match='duplicate_call_cell'):
        runner.reduce_coverage(tasks, records + records[:1])


def test_copied_adapter_uses_original_commit_bytes_without_original_paths(setup, monkeypatch):
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        assert '/inaccessible/' not in str(path)
        assert 'optimizer_rng.pt' not in str(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', guarded_open)
    context = runner.prepare(setup.plan_path)
    assert context['checkpoint']['adapter_path'] == str(setup.adapter)
    result = runner.run(setup.plan_path)
    assert result['before_after_verified']
    assert (setup.output / 'COMMIT.original.json').read_bytes() == setup.commit_path.read_bytes()
    assert result['checkpoint']['adapter_state_sha256'] == ADAPTER_SHA256
    assert result['optimizer_loaded'] is False and result['training_updates'] == 0


@pytest.mark.parametrize('mutation', ['extra', 'missing', 'changed', 'symlink', 'directory', 'traversal'])
def test_adapter_file_inventory_is_exact(setup, mutation):
    if mutation == 'extra':
        (setup.adapter / 'extra.bin').write_bytes(b'not in COMMIT')
    elif mutation == 'missing':
        (setup.adapter / 'adapter_model.safetensors').unlink()
    elif mutation == 'changed':
        (setup.adapter / 'adapter_model.safetensors').write_bytes(b'changed')
    elif mutation == 'symlink':
        (setup.adapter / 'link').symlink_to(setup.commit_path)
    elif mutation == 'directory':
        (setup.adapter / 'unexpected-directory').mkdir()
    else:
        setup.commit['adapter_files']['../escape'] = 'a' * 64
        dump(setup.commit_path, setup.commit)
        setup.manifest['commit_sha256'] = runner.sha(setup.commit_path)
    with pytest.raises(ValueError, match='adapter_'):
        runner.verify_checkpoint(setup.manifest, setup.manifest_path.parent)


def test_commit_hash_is_exact_bytes_not_reencoded_json(setup):
    setup.commit_path.write_text(json.dumps(setup.commit))
    with pytest.raises(ValueError, match='COMMIT_bytes_hash'):
        runner.verify_checkpoint(setup.manifest, setup.manifest_path.parent)


@pytest.mark.parametrize('which', ['adapter_digest', 'state_hash', 'base', 'schema'])
def test_commit_native_contract_checked_before_load(setup, which):
    if which == 'adapter_digest':
        setup.commit['checkpoint_sha256']['adapter'] = '0' * 64
    elif which == 'state_hash':
        setup.commit['adapter_state_sha256'] = 'invalid'
    elif which == 'base':
        setup.commit['base_sha256'] = '0' * 64
    else:
        setup.commit['schema'] = 'wrong'
    dump(setup.commit_path, setup.commit)
    setup.manifest['commit_sha256'] = runner.sha(setup.commit_path)
    with pytest.raises(ValueError):
        runner.verify_checkpoint(setup.manifest, setup.manifest_path.parent)


@pytest.mark.parametrize('which', ['environment', 'plan_bytes', 'corpus', 'manifest', 'device', 'expired',
    'decoder', 'model_id', 'base', 'source_missing', 'source_hash', 'source_traversal', 'source_decoy'])
def test_admission_and_source_bindings_block_before_engine_load(setup, monkeypatch, which, tmp_path):
    if which == 'environment':
        monkeypatch.delenv('R130_ADMISSION_PLAN_SHA256')
    elif which == 'plan_bytes':
        setup.plan_path.write_bytes(setup.plan_path.read_bytes() + b' ')
    elif which in ('corpus', 'manifest'):
        path = getattr(setup, which + '_path')
        path.write_bytes(path.read_bytes() + b' ')
    elif which == 'device':
        monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-wrong')
    else:
        if which == 'expired':
            setup.plan['hard_end_unix'] = 1
        elif which == 'decoder':
            setup.plan['decoder']['max_new_tokens'] = 513
        elif which == 'model_id':
            setup.plan['model_id'] = 'different model'
        elif which == 'base':
            setup.plan['base_sha256'] = '0' * 64
        elif which == 'source_missing':
            setup.plan['sources'].pop(runner.REQUIRED_SOURCES[0])
        elif which == 'source_hash':
            setup.plan['sources'][runner.REQUIRED_SOURCES[0]] = '0' * 64
        elif which == 'source_traversal':
            setup.plan['sources']['../outside.py'] = '0' * 64
        else:
            setup.plan['source_root'] = str(tmp_path)
        setup.admit()
    with pytest.raises(ValueError):
        runner.run(setup.plan_path)
    assert not setup.loads and not setup.output.exists()


@pytest.mark.parametrize('which', ['adapter', 'model', 'checkout', 'existing', 'symlink'])
def test_output_cannot_overwrite_inputs_or_checkout(setup, which, tmp_path):
    if which == 'adapter':
        setup.plan['output_path'] = str(setup.adapter / 'output')
    elif which == 'model':
        setup.plan['output_path'] = str(Path(setup.plan['model_dir']) / 'output')
    elif which == 'checkout':
        setup.plan['output_path'] = str(Path(runner.__file__).parent / 'forbidden-output')
    elif which == 'existing':
        setup.output.mkdir()
    else:
        target = tmp_path / 'target'
        target.mkdir()
        setup.output.symlink_to(target, target_is_directory=True)
    setup.admit()
    with pytest.raises(ValueError):
        runner.run(setup.plan_path)
    assert not setup.loads


def test_success_identical_empty_context_paired_calls_private_hashed_receipts(setup):
    complete = runner.run(setup.plan_path)
    assert len(setup.loads) == 1
    assert len(setup.engine.calls) == 4
    assert [disabled for _, disabled in setup.engine.calls] == [False, True, True, False]
    expected_messages = [item['messages'] for item in setup.corpus['tasks'] for _ in runner.CONDITIONS]
    assert [messages for messages, _ in setup.engine.calls] == expected_messages
    assert setup.engine.model.disable_count == 2
    assert setup.engine.base_checks == 2
    assert not setup.engine.model.parameter.requires_grad
    assert complete['before_after_verified']
    assert complete['coverage']['LORA_ON']['correct_items'] == 1
    assert complete['coverage']['LORA_OFF']['behavior_completed_items'] == 1
    assert setup.output.stat().st_mode & 0o777 == 0o700
    for name, expected in complete['receipts'].items():
        assert runner.sha(setup.output / name) == expected
        assert (setup.output / name).stat().st_mode & 0o777 == 0o600
    record = runner.parse_json((setup.output / 'CALL_00000.json').read_bytes())
    assert record['response']['raw'] == setup.engine.raw
    assert record['response']['token_ids'] == [7, 8, 99]
    assert record['prompt_token_ids_sha256'] == runner.digest(record['prompt_token_ids'])
    assert record['elapsed_seconds'] >= record['generation_seconds'] >= 0
    assert record['started_unix'] <= record['finished_unix']
    with pytest.raises(ValueError, match='fresh_process'):
        runner.run(setup.plan_path)
    assert len(setup.loads) == 1


def test_forked_import_is_not_fresh(setup, monkeypatch):
    monkeypatch.setattr(runner, '_IMPORT_PID', os.getpid() + 1)
    with pytest.raises(ValueError, match='fresh_process'):
        runner.run(setup.plan_path)
    assert not setup.loads


def test_parse_failure_is_recorded_without_becoming_success(setup):
    setup.engine.raw = 'Not a choice'
    complete = runner.run(setup.plan_path)
    for coverage in complete['coverage'].values():
        assert coverage['parse_failure_items'] == 1
        assert coverage['correct_items'] == 0
        assert coverage['accuracy_on_valid'] is None
        assert coverage['correct_over_expected_scored'] == 0


def test_generation_failure_preserves_partial_coverage_and_after_verification(setup):
    setup.engine.fail_at = 2
    with pytest.raises(RuntimeError):
        runner.run(setup.plan_path)
    failed = runner.parse_json((setup.output / 'FAILED.json').read_bytes())
    assert failed['before_after_verified']
    assert not (setup.output / 'COMPLETE.json').exists()
    assert failed['coverage']['LORA_ON']['missing_items'] == 1
    assert failed['coverage']['LORA_OFF']['failed_items'] == 1
    assert failed['coverage']['LORA_OFF']['correct_items'] == 0
    assert failed['coverage']['LORA_OFF']['missing_items'] == 1
    assert not setup.engine.model.parameter.requires_grad
    assert 'synthetic private exception' not in (setup.output / 'CALL_00001.json').read_text()
    assert (setup.output / 'CALL_00001.RESERVED.json').is_file()


def test_truncation_preserves_raw_parsing_but_never_scores_as_success(setup):
    setup.engine.after_generate = lambda response: response.update(
        token_ids=[7] * 512, terminal=False, truncated=True)
    complete = runner.run(setup.plan_path)
    for coverage in complete['coverage'].values():
        assert coverage['truncated_items'] == 2
        assert coverage['valid_response_items'] == coverage['valid_scored_items'] == 0
        assert coverage['parse_valid_items'] == 1
        assert coverage['parse_failure_items'] == 0
        assert coverage['correct_items'] == 0
        assert coverage['accuracy_on_valid'] is None
        assert coverage['correct_over_expected_scored'] == 0
    record = runner.parse_json((setup.output / 'CALL_00000.json').read_bytes())
    assert record['response']['raw'] == setup.engine.raw
    assert record['score']['parse_valid'] is True
    assert record['response_valid'] is False


def test_unexplained_early_stop_is_invalid(setup):
    setup.engine.after_generate = lambda response: response.update(
        token_ids=[7], terminal=False, truncated=False)
    with pytest.raises(ValueError, match='early_termination'):
        runner.run(setup.plan_path)
    assert not (setup.output / 'COMPLETE.json').exists()


def test_relative_manifest_path_cannot_hide_symlink_parent(setup):
    alias = setup.manifest_path.parent / 'alias'
    alias.symlink_to(setup.manifest_path.parent, target_is_directory=True)
    setup.manifest['adapter_path'] = 'alias/adapter'
    with pytest.raises(ValueError, match='symlink'):
        runner.verify_checkpoint(setup.manifest, setup.manifest_path.parent)


def test_corpus_loader_checks_the_same_bytes_it_parses(setup, monkeypatch):
    original = Path.read_bytes

    def replaced_read(path):
        raw = original(path)
        return raw + b' ' if path == setup.corpus_path else raw

    monkeypatch.setattr(Path, 'read_bytes', replaced_read)
    with pytest.raises(ValueError, match='corpus_SHA256_binding'):
        runner.run(setup.plan_path)
    assert not setup.loads


def test_eval_state_drift_stops_before_next_call(setup):
    setup.engine.after_generate = lambda response: setattr(setup.engine.model, 'training', True)
    with pytest.raises(ValueError, match='eval_mode'):
        runner.run(setup.plan_path)
    assert len(setup.engine.calls) == 1
    assert (setup.output / 'CALL_00000.RAW.json').exists()


def test_failed_load_produces_receipt_and_cannot_retry_process(setup, monkeypatch):
    def fail(*args):
        raise RuntimeError('fixture load error')

    monkeypatch.setattr(runner, '_load_engine', fail)
    with pytest.raises(RuntimeError):
        runner.run(setup.plan_path)
    failed = runner.parse_json((setup.output / 'FAILED.json').read_bytes())
    assert failed['calls'] == 0 and failed['before_after_verified'] is False
    assert all(coverage['missing_items'] == 2 for coverage in failed['coverage'].values())
    with pytest.raises(ValueError, match='fresh_process'):
        runner.run(setup.plan_path)


@pytest.mark.parametrize('which', ['adapter_state', 'base_state', 'file', 'source', 'admission', 'response', 'messages', 'receipt'])
def test_mutation_cannot_produce_complete_receipt(setup, monkeypatch, which):
    def mutate(response):
        if which == 'adapter_state':
            setup.engine.model.parameter.checksum = 'c' * 64
        elif which == 'base_state':
            setup.engine.base_changed = True
        elif which == 'file':
            (setup.adapter / 'adapter_config.json').write_bytes(b'modified')
        elif which == 'source':
            original = runner.sha
            monkeypatch.setattr(runner, 'sha', lambda path: '0' * 64
                if str(path).endswith(runner.REQUIRED_SOURCES[0]) else original(path))
        elif which == 'admission':
            monkeypatch.setenv('R130_ADMISSION_PLAN_SHA256', '0' * 64)
        elif which == 'response':
            response['token_ids'] = [7] * 513
        elif which == 'messages':
            response['messages'].append({'role': 'user', 'content': 'mutated fixture'})
        else:
            (setup.output / 'REQUEST.json').write_bytes(b'changed receipt')

    setup.engine.after_generate = mutate
    with pytest.raises(ValueError):
        runner.run(setup.plan_path)
    assert not (setup.output / 'COMPLETE.json').exists()
    assert (setup.output / 'FAILED.json').is_file()
    assert (setup.output / 'CALL_00000.RAW.json').is_file()
    if which not in ('response', 'messages', 'receipt'):
        after = runner.parse_json((setup.output / 'AFTER.json').read_bytes())
        assert after['unchanged'] is False


@pytest.mark.parametrize('which', ['trainable', 'training', 'wrong_device', 'two_devices', 'disabled'])
def test_readonly_snapshot_preconditions(setup, which):
    if which == 'trainable':
        setup.engine.model.parameter.requires_grad = True
    elif which == 'training':
        setup.engine.model.training = True
    elif which == 'wrong_device':
        setup.engine.torch.cuda.get_device_properties = lambda index: SimpleNamespace(uuid='GPU-wrong')
    elif which == 'two_devices':
        setup.engine.torch.cuda.device_count = lambda: 2
    else:
        setup.engine.model.disable_adapters = True
    with pytest.raises((ValueError, AssertionError)):
        runner.run(setup.plan_path)
    assert not setup.engine.calls
    assert not (setup.output / 'COMPLETE.json').exists()


def test_real_engine_loader_is_readout_only_and_fresh_without_torch_load(tmp_path, monkeypatch):
    from gpu import astra_experienced_event_microloop as source

    fresh = SimpleNamespace(is_initialized=lambda: False)
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(cuda=fresh))
    tokenizer = object()
    monkeypatch.setattr(source.native, 'load_local_tokenizer', lambda directory: tokenizer)
    received = []

    def engine(options, received_tokenizer, *, check):
        assert options.phase == 'readout'
        assert options.expected_base_sha256 == runner.BASE_SHA256
        assert options.adapter_dir == str(tmp_path / 'copied-adapter')
        assert received_tokenizer is tokenizer
        received.append(options)
        return 'mock_engine'

    monkeypatch.setattr(source, 'Engine', engine)
    plan = dict(model_dir=str(tmp_path), gpu_uuid='GPU-fixture-only')
    checkpoint = dict(adapter_path=str(tmp_path / 'copied-adapter'))
    assert runner._load_engine(plan, checkpoint, lambda label: None) == 'mock_engine'
    assert len(received) == 1
    fresh.is_initialized = lambda: True
    with pytest.raises(ValueError, match='resident_CUDA'):
        runner._load_engine(plan, checkpoint, lambda label: None)
    assert len(received) == 1


def test_write_once_never_overwrites(tmp_path):
    path = tmp_path / 'receipt.json'
    checksum = runner._write_once(path, {'fixture': True})
    with pytest.raises(FileExistsError):
        runner._write_once(path, {'fixture': False})
    assert runner.sha(path) == checksum


def test_cli_keeps_parent_blind_on_failure(monkeypatch, capsys):
    def fail(path):
        raise ValueError('private synthetic fixture answer and prompt')

    monkeypatch.setattr(runner, 'run', fail)
    assert runner.main(['--plan', 'fixture.json']) == 1
    captured = capsys.readouterr()
    assert 'private synthetic fixture' not in captured.out + captured.err
    assert 'FAILED:' in captured.out


def test_json_duplicate_keys_and_nonfinite_constants_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        runner.parse_json('{"schema":"one","schema":"two"}')
    with pytest.raises(ValueError, match='nonfinite'):
        runner.parse_json('{"value":Infinity}')
