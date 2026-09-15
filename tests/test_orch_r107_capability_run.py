import tempfile
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
import json
import sys

import pytest

from gpu import orch_r107_capability_run as runner


def plan(root):
    source = root / 'driver.py'
    source.write_text('immutable')
    return dict(schema='R107_CAPABILITY_PAIRED_V1', base_sha256=runner.BASE_SHA,
        training_updates=0, parent_calls=0, parent_access=False, train_ingestion=False,
        max_new_tokens=512, task_count=32, call_cap=64, native_deadline_unix=200,
        hard_deadline_unix=250, lease_end_unix=30000,
        conditions=['LORA_ON', 'LORA_OFF'], sources={'driver.py': runner.sha(source)})


def test_plan_binds_sources_and_bounded_readonly_scope():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        original = plan(root)
        assert runner.validate_plan(original, root, 100) == original
        (root / 'driver.py').write_text('changed')
        with pytest.raises(AssertionError):
            runner.validate_plan(original, root, 100)


@pytest.mark.parametrize('field,value', [
    ('training_updates', 1), ('parent_calls', 1), ('parent_access', True),
    ('train_ingestion', True), ('call_cap', 65), ('task_count', 0),
    ('max_new_tokens', 8192), ('native_deadline_unix', 50),
    ('hard_deadline_unix', 100), ('lease_end_unix', 1000),
    ('conditions', ['FULL', 'MASKED']), ('base_sha256', 'other'),
])
def test_invalid_plan_rejected(field, value):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        original = plan(root)
        original[field] = value
        with pytest.raises(AssertionError):
            runner.validate_plan(original, root, 100)


def test_readonly_and_balanced_order():
    assert runner.ordered_conditions(0) == ('LORA_ON', 'LORA_OFF')
    assert runner.ordered_conditions(1) == ('LORA_OFF', 'LORA_ON')
    model = SimpleNamespace(parameters=lambda: [SimpleNamespace(requires_grad=True)])
    with pytest.raises(AssertionError):
        runner.assert_readonly(model)


def test_condition_checks_actual_disabled_layers():
    layer = SimpleNamespace(disable_adapters=False, lora_A={}, lora_B={})
    method_only = SimpleNamespace(disable_adapters=lambda: None)
    model = SimpleNamespace(modules=lambda: [method_only, layer])
    runner.assert_condition(model, 'LORA_ON')
    with pytest.raises(AssertionError):
        runner.assert_condition(model, 'LORA_OFF')


@pytest.mark.parametrize('fail_generation', [False, True])
def test_native_workflow_reserves_calls_and_preserves_readonly_pair(tmp_path, monkeypatch, fail_generation):
    import organism_v6

    tasks = [dict(id='fixed_0', family='math'), dict(id='fixed_1', family='code')]
    policy = SimpleNamespace(tasks=lambda: tasks, digest=lambda unused: 'suite',
        messages=lambda task: [dict(role='user', content=task['id'])],
        score=lambda task, text: dict(correct=text == 'answer'))
    monkeypatch.setitem(sys.modules, 'organism_v6.orch_r107_capability', policy)
    monkeypatch.setattr(organism_v6, 'orch_r107_capability', policy, raising=False)
    document = plan(tmp_path)
    document.update(task_count=2, call_cap=4, suite_sha256='suite', adapter={},
        gpu_uuid='GPU-test', model_dir='/unused')
    for name, value in (
        ('PLAN.json', document),
        ('ADMISSION.json', dict(clear=True, uuid='GPU-test', observed_unix=99)),
    ):
        (tmp_path / name).write_text(json.dumps(value))
    (tmp_path / 'READY.json').write_text(json.dumps(dict(status='PASS', plan_sha256=runner.sha(tmp_path / 'PLAN.json'))))
    (tmp_path / 'PUBLICATION.json').write_text(json.dumps(dict(ready_sha256=runner.sha(tmp_path / 'READY.json'))))
    monkeypatch.setattr(runner, 'validate_plan', lambda document, source, now: document)
    monkeypatch.setattr(runner.time, 'time', lambda: 100)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-test')
    monkeypatch.setenv('HF_HUB_OFFLINE', '1')
    monkeypatch.setenv('TRANSFORMERS_OFFLINE', '1')
    identity = SimpleNamespace(path='/unused/adapter', base_sha256=runner.BASE_SHA)
    identity.verify = lambda: identity
    identity.document = lambda: dict(state_sha256='fixed')
    monkeypatch.setattr(runner.bridge, 'AdapterIdentity', SimpleNamespace(from_document=lambda document: identity))
    monkeypatch.setattr(runner.native, 'observe_adapter', lambda engine, expected: identity)
    monkeypatch.setattr(runner.native.source.native, 'load_local_tokenizer', lambda directory: object())
    observed = []

    class Model:
        disable_adapters = False
        lora_A = {}
        lora_B = {}

        def parameters(self):
            return [SimpleNamespace(requires_grad=False)]

        def modules(self):
            return [self]

        @contextmanager
        def disable_adapter(self):
            self.disable_adapters = True
            try:
                yield
            finally:
                self.disable_adapters = False

    class Engine:
        def __init__(self, options, tokenizer, check):
            self.model = Model()

        def generate(self, messages, max_new_tokens):
            observed.append(self.model.disable_adapters)
            if fail_generation:
                raise RuntimeError('synthetic_failure')
            return dict(raw='answer', token_ids=[1], truncated=False, terminal=True)

        def verify_base(self):
            assert not self.model.disable_adapters

    monkeypatch.setattr(runner, 'Engine', Engine)
    if fail_generation:
        with pytest.raises(RuntimeError):
            runner.run(tmp_path)
        assert runner.read(tmp_path / 'readout/FAILED.json')['calls'] == 1
        assert runner.read(tmp_path / 'readout/CALL_000.json')['status'] == 'FAILED'
        assert not (tmp_path / 'readout/COMPLETE.json').exists()
    else:
        runner.run(tmp_path)
        assert observed == [False, True, True, False]
        assert runner.read(tmp_path / 'readout/COMPLETE.json')['calls'] == 4
        assert runner.read(tmp_path / 'readout/AFTER.json')['unchanged']
        with pytest.raises(FileExistsError):
            runner.run(tmp_path)
