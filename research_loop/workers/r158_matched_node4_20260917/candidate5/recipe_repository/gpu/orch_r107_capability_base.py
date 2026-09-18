"""CPU preparation and Main-launched, node-local PUREBASE synthetic32 readout.

--root ROOT --prepare consumes PLAN.json without loading model weights; --root
ROOT runs once. Main supplies native/hard/lease deadlines, model_dir, gpu_uuid,
physical_index=3, device_minor=3, sources, and the fixed suite/hash/cap fields
validated below. adapter must be null. No retained calls or deadline resets.

PUBLICATION.json binds ready_sha256, own_cpu_tests_passed=true and a nonempty
dated_builder_publication. ADMISSION.json binds plan_sha256 and embeds snapshot
from the existing node3 privileged full/proc scanner, including created_utc.
Main owns allocation, guardian, receipt publication and native launch. No scan,
reservation, model, GPU or provider call is made by CPU preparation.

readout/CALL_*.json and INTENT_*.json stay on node. RESULTS.json is compact:
all32 denominators, exact machine outcomes, completion and token counts only.
PUREBASE is not adapter-OFF, and this panel is not a broad benchmark.
"""

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import orch_guided_native as native
from gpu import orch_oracle_repair_guard as scanner
from gpu.orch_rich_intensity_screen import Engine
from organism_v6 import orch_combined_l1_base as base
from organism_v6 import orch_combined_l1_continual as storage
from organism_v6 import orch_r107_capability as policy


SCHEMA = 'R107_CAPABILITY_PUREBASE_V1'
BASE_SHA = base.BASE_SHA
SUITE_SHA = '32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c'
SOURCE_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SOURCES = (
    'gpu/orch_r107_capability_base.py',
    'tests/test_orch_r107_capability_base.py',
    'gpu/orch_rich_intensity_screen.py',
    'gpu/astra_portable_actor_bundle.py',
    'gpu/astra_experienced_event_microloop.py',
    'gpu/orch_guided_native.py',
    'gpu/orch_oracle_repair_guard.py',
    'organism_v6/orch_r107_capability.py',
    'organism_v6/orch_combined_l1_base.py',
    'organism_v6/orch_combined_l1_continual.py',
    'organism_v6/orch_rich_intensity.py',
    'organism_v6/pcfl_vertical_train.py',
    'organism_v6/orch_code_bounded.py',
)
MODEL_METADATA = ('config.json', 'generation_config.json', 'tokenizer.json',
    'tokenizer_config.json', 'special_tokens_map.json', 'chat_template.jinja',
    'vocab.json', 'merges.txt')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_plan(plan, source_root, now):
    require(plan['schema'] == SCHEMA, 'purebase_schema_required')
    require(plan['base_sha256'] == BASE_SHA and plan['adapter'] is None,
            'purebase_identity_required')
    for name, expected in (('training_updates', 0), ('parent_calls', 0),
                           ('max_new_tokens', 512), ('task_count', 32), ('call_cap', 32)):
        require(type(plan[name]) is int and plan[name] == expected, 'fixed_' + name)
    require(plan['parent_access'] is False and plan['train_ingestion'] is False,
            'read_only_diagnostic_required')
    require(plan['conditions'] == ['PUREBASE'], 'purebase_condition_required')
    require(not plan.get('retained_calls') and 'prior_root' not in plan
            and 'new_call_cap' not in plan, 'fresh32_no_replay')
    require(now < plan['native_deadline_unix'] < plan['hard_deadline_unix']
            <= plan['lease_end_unix'] - 21600, 'fixed_deadline_or_lease_violation')
    require(plan['physical_index'] == plan['device_minor'] == 3
            and plan['gpu_uuid'] == scanner.DEVICES[3], 'main_node3_slot3_only')
    require(Path(plan['model_dir']).is_absolute(), 'absolute_local_model_required')
    tasks = policy.tasks()
    require(len(tasks) == 32 and plan['suite_sha256'] == policy.digest(tasks) == SUITE_SHA,
            'fixed_suite_changed')
    require(set(REQUIRED_SOURCES) <= set(plan['sources']), 'runtime_sources_required')
    for relative, expected in plan['sources'].items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts
                and (source_root / path).resolve().is_relative_to(source_root.resolve()),
                'unsafe_source_path')
        require(sha(source_root / path) == expected, 'source_binding_changed')
    return plan


def metadata(model_dir):
    model = Path(model_dir)
    result = {name: sha(model / name) for name in MODEL_METADATA if (model / name).is_file()}
    require({'config.json', 'tokenizer.json', 'tokenizer_config.json'} <= set(result),
            'local_model_metadata_required')
    config = read(model / 'config.json')
    require(config['model_type'] == 'qwen2', 'frozen_qwen_required')
    return result, config['max_position_embeddings']


def encode_suite(tokenizer, context):
    encoded = []
    for task in policy.tasks():
        tokens = tokenizer.apply_chat_template(policy.messages(task), tokenize=True,
            add_generation_prompt=True, return_dict=False)
        require(0 < len(tokens) <= 4096 and len(tokens) + 512 <= context,
                'prompt_or_context_bound')
        encoded.append(dict(task_id=task['id'], content_sha256=task['content_sha256'],
            prompt_sha256=task['prompt_sha256'], prompt_tokens=len(tokens),
            encoded_sha256=policy.digest(tokens)))
    return encoded


def prepare(root):
    root = Path(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_requires_empty_cvd')
    require(not (root / 'READY.json').exists() and not (root / 'readout').exists(),
            'fresh_preparation_required')
    plan = validate_plan(read(root / 'PLAN.json'), SOURCE_ROOT, time.time())
    files, context = metadata(plan['model_dir'])
    tokenizer = native.source.native.load_local_tokenizer(plan['model_dir'])
    encoded = encode_suite(tokenizer, context)
    require(metadata(plan['model_dir'])[0] == files, 'metadata_changed_during_prepare')
    validate_plan(plan, SOURCE_ROOT, time.time())
    ready = dict(status='PASS', plan_sha256=sha(root / 'PLAN.json'), suite_sha256=SUITE_SHA,
        base_sha256=BASE_SHA, adapter=None, max_new_tokens=512, call_cap=32,
        native_calls=0, parent_calls=0, training_updates=0, encoded_prompts=32,
        tokenization=encoded, model_metadata=files, context=context,
        base_tensor_verification='REQUIRED_NATIVE_BEFORE_AND_AFTER', prepared_unix=time.time())
    storage.atomic_json(root / 'READY.json', ready)
    return ready


def admission(root, plan):
    receipt = read(root / 'ADMISSION.json')
    require(receipt['plan_sha256'] == sha(root / 'PLAN.json'), 'admission_plan_mismatch')
    snapshot = receipt['snapshot']
    observed = datetime.fromisoformat(snapshot['created_utc'].replace('Z', '+00:00'))
    require(observed.tzinfo is not None and 0 <= time.time() - observed.timestamp() <= 90,
            'fresh_privileged_admission_required')
    require(snapshot['scanner_euid'] == 0 and snapshot['clear'] is True
            and snapshot['blocking_reasons'] == scanner.evaluate(snapshot, 3) == [],
            'full_proc_scan_not_clear')
    require(snapshot['gpu']['uuid'] == plan['gpu_uuid'], 'admission_uuid_mismatch')


def verify_frozen(engine):
    count = base.verify_no_adapter(engine.model.named_parameters(),
        getattr(engine.model, 'peft_config', None))
    engine.verify_base()
    return dict(no_adapter_verified=True, frozen_base_verified=True,
        base_sha256=BASE_SHA, parameter_count=count, training_updates=0, parent_calls=0)


def response_summary(task, response, eos):
    tokens = response['token_ids']
    require(isinstance(tokens, list) and len(tokens) <= 512
            and all(type(token) is int and token >= 0 for token in tokens), 'native_token_violation')
    terminal, truncated = response['terminal'], response['truncated']
    require(type(terminal) is bool and type(truncated) is bool
            and terminal == (tokens[-1:] == [eos]) and eos not in tokens[:-1]
            and truncated == (not terminal and len(tokens) == 512), 'native_completion_violation')
    require(response['messages'] == policy.messages(task), 'native_prompt_changed')
    require(type(response['prompt_tokens']) is int and 0 < response['prompt_tokens'] <= 4096
            and isinstance(response['raw'], str), 'native_response_invalid')
    outcome = policy.score(task, response['raw'])
    completion = 'truncated' if truncated else 'complete' if terminal else 'incomplete'
    return dict(completion=completion, category=outcome['category'] if terminal else completion,
        passed=terminal and outcome['passed'], machine_outcome=outcome,
        generated_tokens=len(tokens), content_tokens=len(tokens) - int(terminal),
        prompt_tokens=response['prompt_tokens'])


def compact_results(output, calls, verified):
    rows = []
    for position, task in enumerate(policy.tasks()):
        row = dict(position=position, task_id=task['id'], family=task['family'],
            content_sha256=task['content_sha256'], prompt_sha256=task['prompt_sha256'],
            condition='PUREBASE', base_sha256=BASE_SHA, adapter=None, max_new_tokens=512,
            completion='missing', category='missing', passed=False, machine_outcome=None,
            generated_tokens=None, content_tokens=None, prompt_tokens=None)
        if position < len(calls):
            call = calls[position]
            row.update(call_path=f'CALL_{position:03d}.json',
                call_sha256=sha(output / f'CALL_{position:03d}.json'), native_status=call['status'])
            if 'summary' in call:
                row.update(call['summary'])
            if call['status'] != 'COMPLETE':
                row.update(completion='execution_error', category='execution_error', passed=False,
                           error_type=call.get('error_type'))
        rows.append(row)
    def counts(selected):
        return dict(tasks=len(selected), passed=sum(row['passed'] for row in selected),
            completions=dict(Counter(row['completion'] for row in selected)),
            categories=dict(Counter(row['category'] for row in selected)),
            generated_tokens=sum(row['generated_tokens'] or 0 for row in selected),
            content_tokens=sum(row['content_tokens'] or 0 for row in selected))
    return dict(schema=SCHEMA, suite_sha256=SUITE_SHA, condition='PUREBASE',
        base_sha256=BASE_SHA, adapter=None, native_reserved_calls=len(calls),
        native_completed_calls=sum(call['status'] == 'COMPLETE' for call in calls),
        before_after_verified=verified, totals=counts(rows),
        families={family: counts([row for row in rows if row['family'] == family])
                  for family in policy.FAMILIES}, rows=rows, training_updates=0, parent_calls=0,
        scope='SYNTHETIC32_DIAGNOSTIC_NOT_BROAD_BENCHMARK')


def run(root):
    root = Path(root)
    plan = validate_plan(read(root / 'PLAN.json'), SOURCE_ROOT, time.time())
    ready = read(root / 'READY.json')
    publication = read(root / 'PUBLICATION.json')
    require(ready['status'] == 'PASS' and ready['plan_sha256'] == sha(root / 'PLAN.json')
            and ready['suite_sha256'] == SUITE_SHA and ready['native_calls'] == 0,
            'ready_plan_mismatch')
    require(publication['ready_sha256'] == sha(root / 'READY.json')
            and publication['own_cpu_tests_passed'] is True
            and bool(publication['dated_builder_publication']), 'publication_required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1',
            'native_offline_uuid_environment_required')
    files, context = metadata(plan['model_dir'])
    require(files == ready['model_metadata'] and context == ready['context'], 'metadata_drift')
    tokenizer = native.source.native.load_local_tokenizer(plan['model_dir'])
    require(encode_suite(tokenizer, context) == ready['tokenization'], 'encoded_suite_drift')
    admission(root, plan)
    output = root / 'readout'
    output.mkdir(exist_ok=False)
    storage.atomic_json(output / 'REQUEST.json', dict(plan_sha256=sha(root / 'PLAN.json'),
        ready_sha256=sha(root / 'READY.json'), publication_sha256=sha(root / 'PUBLICATION.json'),
        admission_sha256=sha(root / 'ADMISSION.json'), process=native.process_identity(),
        started_unix=time.time(), condition='PUREBASE', adapter=None, call_cap=32,
        training_updates=0, parent_calls=0))
    calls, engine, failure = [], None, None
    before_verified, after_verified, finalizing = False, False, False

    def check(label):
        deadline = plan['hard_deadline_unix'] if finalizing and label == 'base_hash' else plan['native_deadline_unix']
        if time.time() >= deadline:
            raise TimeoutError('purebase_fixed_deadline:' + label)

    try:
        check('load')
        engine = Engine(base.options(plan['model_dir'], plan['gpu_uuid']), tokenizer, check=check)
        storage.atomic_json(output / 'BEFORE.json', verify_frozen(engine))
        before_verified = True
        for position, task in enumerate(policy.tasks()):
            check('reserve')
            base.verify_no_adapter(engine.model.named_parameters(), getattr(engine.model, 'peft_config', None))
            record = dict(position=position, task_id=task['id'], family=task['family'],
                content_sha256=task['content_sha256'], prompt_sha256=task['prompt_sha256'],
                base_sha256=BASE_SHA, adapter=None, condition='PUREBASE', max_new_tokens=512,
                messages=policy.messages(task), status='RESERVED', started_unix=time.time())
            require(len(calls) < plan['call_cap'], 'call_cap_exhausted')
            storage.atomic_json(output / f'INTENT_{position:03d}.json', record)
            path = output / f'CALL_{position:03d}.json'
            storage.atomic_json(path, record)
            calls.append(record)
            try:
                check('dispatch')
                record['response'] = engine.generate(record['messages'], max_new_tokens=512)
                record['summary'] = response_summary(task, record['response'], tokenizer.eos_token_id)
                require(record['response']['prompt_tokens'] == ready['tokenization'][position]['prompt_tokens'],
                        'native_prompt_token_drift')
                record['status'] = 'COMPLETE'
            except BaseException as error:
                record.update(status='FAILED', error_type=type(error).__name__)
                raise
            finally:
                record['finished_unix'] = time.time()
                storage.atomic_json(path, record)
    except BaseException as error:
        failure = error
    finally:
        finalizing = True
        try:
            require(engine is not None, 'engine_not_loaded')
            after = verify_frozen(engine)
            require(metadata(plan['model_dir'])[0] == files, 'metadata_drift_after')
            after_verified = True
            storage.atomic_json(output / 'AFTER.json', dict(after, status='PASS', finished_unix=time.time()))
        except BaseException as error:
            storage.atomic_json(output / 'AFTER.json', dict(status='FAILED',
                error_type=type(error).__name__, finished_unix=time.time()))
            failure = failure or error
        results = compact_results(output, calls, before_verified and after_verified)
        storage.atomic_json(output / 'RESULTS.json', results)
        if failure is not None:
            storage.atomic_json(output / 'FAILED.json', dict(error_type=type(failure).__name__,
                calls=len(calls), finished_unix=time.time()))
        else:
            storage.atomic_json(output / 'COMPLETE.json', dict(status='COMPLETE', calls=len(calls),
                suite_sha256=SUITE_SHA, results_sha256=sha(output / 'RESULTS.json'),
                before_after_verified=True, finished_unix=time.time()))
    if failure is not None:
        raise failure
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    arguments = parser.parse_args()
    result = prepare(arguments.root) if arguments.prepare else run(arguments.root)
    print(json.dumps({key: value for key, value in result.items() if key not in ('rows', 'tokenization')}))
