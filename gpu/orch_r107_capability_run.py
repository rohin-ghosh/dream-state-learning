"""Read-only paired adapter activation diagnostic; native evidence stays on node."""

import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import orch_guided_native as native
from gpu.orch_rich_intensity_screen import Engine
from organism_v6 import orch_combined_l1_continual as storage
from organism_v6 import orch_guided_bridge as bridge


BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_plan(plan, source_root, now):
    assert plan['schema'] == 'R107_CAPABILITY_PAIRED_V1'
    assert plan['base_sha256'] == BASE_SHA
    assert plan['training_updates'] == plan['parent_calls'] == 0
    assert plan['parent_access'] is False and plan['train_ingestion'] is False
    assert plan['max_new_tokens'] in (512, 1536)
    assert 0 < plan['task_count'] <= 64
    assert plan['call_cap'] == 2 * plan['task_count']
    assert now < plan['native_deadline_unix'] < plan['hard_deadline_unix']
    assert plan['hard_deadline_unix'] <= plan['lease_end_unix'] - 21600
    assert plan['conditions'] == ['LORA_ON', 'LORA_OFF']
    assert plan['sources']
    for relative, expected in plan['sources'].items():
        path = Path(relative)
        assert not path.is_absolute() and '..' not in path.parts
        assert sha(source_root / path) == expected, 'source_binding_changed'
    return plan


def ordered_conditions(position):
    return ('LORA_ON', 'LORA_OFF') if position % 2 == 0 else ('LORA_OFF', 'LORA_ON')


def assert_readonly(model):
    assert not any(parameter.requires_grad for parameter in model.parameters())


def assert_condition(model, condition):
    states = [module.disable_adapters for module in model.modules()
              if hasattr(module, 'disable_adapters')]
    assert states and all(state is (condition == 'LORA_OFF') for state in states)


def run(root):
    from organism_v6 import orch_r107_capability as policy

    plan_path = root / 'PLAN.json'
    plan = validate_plan(read(plan_path), Path(__file__).resolve().parents[1], time.time())
    ready = read(root / 'READY.json')
    publication = read(root / 'PUBLICATION.json')
    assert ready['status'] == 'PASS' and ready['plan_sha256'] == sha(plan_path)
    assert publication['ready_sha256'] == sha(root / 'READY.json')
    admission = read(root / 'ADMISSION.json')
    assert admission['clear'] is True and admission['uuid'] == plan['gpu_uuid']
    assert 0 <= time.time() - admission['observed_unix'] <= 90
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
    assert os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1'
    tasks = policy.tasks()
    assert len(tasks) == plan['task_count'] and policy.digest(tasks) == plan['suite_sha256']
    assert len({task['id'] for task in tasks}) == len(tasks)
    identity = bridge.AdapterIdentity.from_document(plan['adapter']).verify()
    assert identity.base_sha256 == BASE_SHA
    output = root / 'readout'
    output.mkdir(exist_ok=False)
    process = native.process_identity()
    storage.atomic_json(output / 'REQUEST.json', dict(plan_sha256=sha(plan_path),
        admission_sha256=sha(root / 'ADMISSION.json'), process=process,
        started_unix=time.time(), parent_present=False, training_updates=0))
    calls = []

    def check(label):
        if time.time() >= plan['native_deadline_unix']:
            raise TimeoutError('bounded_capability_readout:' + label)

    try:
        tokenizer = native.source.native.load_local_tokenizer(plan['model_dir'])
        options = SimpleNamespace(model_dir=plan['model_dir'], adapter_dir=identity.path,
            phase='readout', device='cuda:0', gpu_uuid=plan['gpu_uuid'],
            expected_base_sha256=BASE_SHA)
        engine = Engine(options, tokenizer, check=check)
        assert_readonly(engine.model)
        observed = native.observe_adapter(engine, identity)
        storage.atomic_json(output / 'LOADED.json', dict(process=process,
            observed=observed.document(), loaded_unix=time.time(), parent_present=False,
            training_updates=0, suite_sha256=plan['suite_sha256']))
        for position, task in enumerate(tasks):
            messages = policy.messages(task)
            for condition in ordered_conditions(position):
                check('reserve')
                assert len(calls) < plan['call_cap']
                record = dict(position=position, task_id=task['id'], family=task['family'],
                    condition=condition, messages=messages, started_unix=time.time(),
                    status='RESERVED', max_new_tokens=plan['max_new_tokens'],
                    parent_present=False, training_updates=0)
                path = output / f'CALL_{len(calls):03d}.json'
                assert not path.exists()
                storage.atomic_json(path, record)
                calls.append(record)
                try:
                    context = engine.model.disable_adapter() if condition == 'LORA_OFF' else nullcontext()
                    with context:
                        assert_readonly(engine.model)
                        assert_condition(engine.model, condition)
                        record['response'] = engine.generate(messages, max_new_tokens=plan['max_new_tokens'])
                    record.update(status='COMPLETE', outcome=policy.score(task, record['response']['raw']))
                except BaseException as error:
                    record.update(status='FAILED', error_type=type(error).__name__)
                    raise
                finally:
                    record['finished_unix'] = time.time()
                    storage.atomic_json(path, record)
                if len(calls) == 1:
                    storage.atomic_json(output / 'FIRST_CALL.json', dict(
                        call_sha256=sha(path), finished_unix=record['finished_unix']))
        assert_readonly(engine.model)
        engine.verify_base()
        assert native.observe_adapter(engine, identity) == observed
        identity.verify()
        storage.atomic_json(output / 'AFTER.json', dict(process=process,
            observed=observed.document(), frozen_base_verified=True, unchanged=True,
            parent_present=False, training_updates=0, finished_unix=time.time()))
        storage.atomic_json(output / 'COMPLETE.json', dict(status='COMPLETE',
            calls=len(calls), task_count=len(tasks), suite_sha256=plan['suite_sha256'],
            process=process, parent_present=False, training_updates=0,
            scope='SYNTHETIC_CAPABILITY_DIAGNOSTIC_NOT_BROAD_BENCHMARK',
            finished_unix=time.time()))
    except BaseException as error:
        storage.atomic_json(output / 'FAILED.json', dict(error_type=type(error).__name__,
            calls=len(calls), finished_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
