"""R130/R132 generic, sealed, read-only benchmark of one saved checkpoint.

Corpus (exact file bytes are hashed; this module contains no benchmark items)::

    {"schema": "R130_TASKS_V1", "tasks": [
      {"task_id": "<opaque-id>", "family": "<family>",
       "messages": [{"role": "user", "content": "<held-prompt>"}],
       "scoring": {"type": "choice", "response_format": "json",
                   "choices": ["<label>"], "answer": "<key>",
                   "confidence": {"required": false}}}]}

Scoring types are choice, exact, behavior. Choice/exact require string answer
keys. Text responses are stripped at the edges only; JSON responses must be a
single object with a string answer and optional numeric confidence in [0, 1].
No fences, reasoning extraction, semantic matching, case folding, or guessed
keys. Confidence is probability the submitted answer is correct; its Brier
error is reported only on valid, explicitly keyed responses. Behavior items
have no answer/choices/confidence and receive descriptive metrics, not scores.
Cap-truncated responses retain parsing results but are ineligible for accuracy
or calibration; truncation, parsing, failures, and missing cells are separate.
The corpus author supplies all response-format instructions inside messages.
Messages are never augmented with scoring keys or prior calls.

Manifest schema R130_CHECKPOINT_MANIFEST_V1 requires adapter_path (local copied
directory), commit_path (local copy of original native COMMIT bytes), and
commit_sha256. Original absolute paths and optimizer/RNG files are never opened.

Plan schema R130_CHECKPOINT_BENCHMARK_V1 requires model_id, model_dir,
base_sha256, gpu_uuid, hard_end_unix, corpus_path/corpus_sha256,
manifest_path/manifest_sha256, output_path, source_root, sources (relative
source paths -> SHA256), and decoder == DECODER. Paths are relative to their
containing plan/manifest unless absolute. source_root must be the executing
checkout; sources must include REQUIRED_SOURCES. R130_ADMISSION_PLAN_SHA256
must equal the SHA256 of the exact plan bytes, and CUDA_VISIBLE_DEVICES must
equal gpu_uuid. The caller admits, reserves the device, guards the lease, and
launches a fresh process. This module does not launch or train anything itself.
Temperature zero denotes greedy decoding: the existing Engine uses
do_sample=False, so its sampling temperature is unused.

Run with python -m gpu.orch_r130_checkpoint_benchmark --plan PLAN. Output is a
new private node-local directory, never the checkout. It contains held content
and must NOT be exposed to the parenting agent. CLI output contains status
only, including on failure; private receipts retain error types, not exception
strings that might contain held prompts. write-once receipts are hash-bound in
COMPLETE.json/FAILED.json (not filesystem-WORM storage). SIGKILL can leave only
reservations/raw receipts, which must not be treated as completed evidence.
"""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from types import SimpleNamespace


SCHEMA = 'R130_CHECKPOINT_BENCHMARK_V1'
TASK_SCHEMA = 'R130_TASKS_V1'
MANIFEST_SCHEMA = 'R130_CHECKPOINT_MANIFEST_V1'
NATIVE_SCHEMA = 'R125_NATIVE_CONTINUITY_V1'
MODEL_ID = 'Qwen/Qwen2.5-7B-Instruct'
BASE_SHA256 = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
MAX_NEW_TOKENS = 512
DECODER = dict(temperature=0.0, do_sample=False, num_beams=1,
    max_new_tokens=MAX_NEW_TOKENS, repetition_penalty=1.0)
CONDITIONS = ('LORA_ON', 'LORA_OFF')
REQUIRED_SOURCES = (
    'gpu/orch_r130_checkpoint_benchmark.py',
    'gpu/orch_r107_capability_run.py',
    'gpu/astra_experienced_event_microloop.py',
    'gpu/orch_guided_native.py',
    'gpu/astra_pchain2_native.py',
    'gpu/astra_pchain2_prepare.py',
    'organism_v6/pcfl_vertical_train.py',
)
_IMPORT_PID = os.getpid()
_PROCESS_USED = False


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_JSON_key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('nonfinite_JSON_constant')


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=_object, parse_constant=_invalid_constant)


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _read_bound(path, expected, reason):
    raw = Path(path).read_bytes()
    require(_hash(expected) and hashlib.sha256(raw).hexdigest() == expected, reason)
    return raw


def _path(value, parent):
    require(isinstance(value, str) and bool(value), 'local_path_required')
    path = Path(value)
    if not path.is_absolute():
        require('..' not in path.parts, 'relative_path_traversal')
        current = parent
        for part in path.parts:
            current = current / part
            require(not current.is_symlink(), 'symlink_artifact')
        path = parent / path
    require(not path.is_symlink(), 'symlink_artifact')
    return path.resolve(strict=True)


def validate_tasks(document):
    require(isinstance(document, dict) and set(document) == {'schema', 'tasks'}
        and document['schema'] == TASK_SCHEMA, 'task_schema')
    tasks = document['tasks']
    require(isinstance(tasks, list) and bool(tasks), 'nonempty_task_inventory')
    seen = set()
    for task in tasks:
        require(isinstance(task, dict)
            and set(task) == {'task_id', 'family', 'messages', 'scoring'}, 'task_fields')
        for field in ('task_id', 'family'):
            require(isinstance(task[field], str) and bool(task[field].strip()), 'task_identifier')
        require(task['task_id'] not in seen, 'duplicate_task_id')
        seen.add(task['task_id'])
        messages = task['messages']
        require(isinstance(messages, list) and bool(messages), 'nonempty_messages')
        for position, message in enumerate(messages):
            require(isinstance(message, dict) and set(message) == {'role', 'content'}, 'message_fields')
            require(message['role'] in ('system', 'user', 'assistant')
                and isinstance(message['content'], str) and bool(message['content']), 'message_value')
            require(message['role'] != 'system' or position == 0, 'system_message_position')
        require(messages[-1]['role'] == 'user', 'task_ends_with_user')
        scoring = task['scoring']
        require(isinstance(scoring, dict), 'scoring_object')
        kind = scoring.get('type')
        require(kind in ('choice', 'exact', 'behavior'), 'scoring_type')
        if kind == 'behavior':
            require(set(scoring) == {'type'}, 'behavior_has_no_scoring_key')
            continue
        allowed = {'type', 'answer', 'response_format', 'confidence'}
        if kind == 'choice':
            allowed.add('choices')
        require(set(scoring) <= allowed and {'type', 'answer', 'response_format'} <= set(scoring),
            'explicit_scoring_key_and_format')
        require(isinstance(scoring['answer'], str) and bool(scoring['answer'])
            and scoring['answer'] == scoring['answer'].strip(), 'exact_key_string')
        require(scoring['response_format'] in ('text', 'json'), 'response_format')
        if kind == 'choice':
            choices = scoring.get('choices')
            require(isinstance(choices, list) and bool(choices)
                and all(isinstance(choice, str) and bool(choice)
                    and choice == choice.strip() for choice in choices), 'choice_labels')
            require(len(set(choices)) == len(choices) and scoring['answer'] in choices, 'choice_key')
        if 'confidence' in scoring:
            confidence = scoring['confidence']
            require(scoring['response_format'] == 'json' and isinstance(confidence, dict)
                and set(confidence) == {'required'} and type(confidence['required']) is bool,
                'confidence_contract')
    return tasks


def score_response(task, raw):
    scoring = task['scoring']
    if scoring['type'] == 'behavior':
        return dict(scored=False, parse_valid=None, correct=None, confidence=None, brier=None)
    result = dict(scored=True, parse_valid=False, correct=None, confidence=None, brier=None)
    try:
        require(isinstance(raw, str), 'response_text_required')
        if scoring['response_format'] == 'json':
            parsed = parse_json(raw)
            require(isinstance(parsed, dict) and 'answer' in parsed
                and set(parsed) <= {'answer', 'confidence'}, 'response_JSON_shape')
            answer = parsed['answer']
            confidence = parsed.get('confidence')
            if 'confidence' in parsed:
                require('confidence' in scoring, 'unrequested_confidence')
                require(type(confidence) in (int, float) and math.isfinite(confidence)
                    and 0 <= confidence <= 1, 'confidence_range')
            require(not scoring.get('confidence', {}).get('required', False)
                or 'confidence' in parsed, 'confidence_required')
        else:
            answer, confidence = raw, None
        require(isinstance(answer, str) and bool(answer.strip()), 'answer_string_required')
        answer = answer.strip()
        if scoring['type'] == 'choice':
            require(answer in scoring['choices'], 'unknown_choice')
        correct = answer == scoring['answer']
        result.update(parse_valid=True, correct=correct, confidence=confidence,
            brier=(confidence - int(correct)) ** 2 if confidence is not None else None)
    except (ValueError, TypeError, OverflowError):
        result['parse_failure'] = 'invalid_response_format_or_choice'
    return result


def descriptive_metrics(response):
    raw, tokens = response['raw'], response['token_ids']
    lines = [line for line in raw.splitlines() if line]
    line_counts = Counter(lines)
    ngrams = Counter(tuple(tokens[position:position + 4]) for position in range(max(0, len(tokens) - 3)))
    return dict(label='descriptive_only_not_semantic_thought_units', generated_tokens=len(tokens),
        response_characters=len(raw), whitespace_words=len(raw.split()), nonempty_lines=len(lines),
        exact_repeated_lines=sum(count - 1 for count in line_counts.values()),
        exact_repeated_token_4grams=sum(count - 1 for count in ngrams.values()),
        scaffold_pattern_indicators={
            'think_tag_literal_count': raw.count('<think>') + raw.count('</think>'),
            'markdown_heading_lines': len(re.findall(r'^#{1,6}\s+', raw, re.MULTILINE)),
            'numbered_list_lines': len(re.findall(r'^\s*\d+[.)]\s+', raw, re.MULTILINE)),
            'code_fence_literal_count': raw.count('```'),
        })


def reduce_coverage(tasks, records):
    expected = {(task['task_id'], condition): task for task in tasks for condition in CONDITIONS}
    cells = {}
    for record in records:
        cell = (record['task_id'], record['condition'])
        require(cell in expected and cell not in cells, 'unexpected_or_duplicate_call_cell')
        cells[cell] = record
    result = {}
    for condition in CONDITIONS:
        selected = [cells.get((task['task_id'], condition)) for task in tasks]
        complete = [record for record in selected if record and record['status'] == 'COMPLETE']
        scored = [record['score'] for record in complete if record['score']['scored']]
        parsed = [score for score in scored if score['parse_valid']]
        valid = [record['score'] for record in complete if record.get('response_valid', False)
            and record['score']['scored'] and record['score']['parse_valid']]
        calibrated = [score for score in valid if score['brier'] is not None]
        score_count = sum(task['scoring']['type'] != 'behavior' for task in tasks)
        correct = sum(score['correct'] is True for score in valid)
        result[condition] = dict(expected_items=len(tasks), recorded_items=sum(record is not None for record in selected),
            completed_items=len(complete), missing_items=sum(record is None for record in selected),
            failed_items=sum(record is not None and record['status'] != 'COMPLETE' for record in selected),
            valid_response_items=sum(record.get('response_valid', False) for record in complete),
            truncated_items=sum(record.get('response', {}).get('truncated', False) for record in complete),
            expected_scored_items=score_count, parse_valid_items=len(parsed), valid_scored_items=len(valid),
            parse_failure_items=len(scored) - len(parsed), correct_items=correct,
            incorrect_valid_items=len(valid) - correct,
            behavior_completed_items=sum(not record['score']['scored'] for record in complete),
            accuracy_on_valid=correct / len(valid) if valid else None,
            correct_over_expected_scored=correct / score_count if score_count else None,
            parse_valid_over_expected_scored=len(parsed) / score_count if score_count else None,
            valid_scored_over_expected_scored=len(valid) / score_count if score_count else None,
            confidence_items=len(calibrated),
            mean_brier_on_valid_confidence=sum(score['brier'] for score in calibrated) / len(calibrated)
                if calibrated else None)
    return result


def _verify_sources(plan):
    root = Path(plan['source_root']).resolve(strict=True)
    require(root == Path(__file__).resolve().parents[1], 'executing_source_root_required')
    sources = plan['sources']
    require(isinstance(sources, dict) and set(REQUIRED_SOURCES) <= set(sources), 'required_source_inventory')
    for relative, expected in sources.items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts and _hash(expected), 'source_path_or_hash')
        actual = _path(relative, root)
        require(actual.is_relative_to(root) and sha(actual) == expected, 'source_binding_changed')


def verify_checkpoint(manifest, parent):
    require(isinstance(manifest, dict) and set(manifest) ==
        {'schema', 'adapter_path', 'commit_path', 'commit_sha256'}
        and manifest['schema'] == MANIFEST_SCHEMA, 'checkpoint_manifest_schema')
    adapter = _path(manifest['adapter_path'], parent)
    commit_path = _path(manifest['commit_path'], parent)
    checkpoint = parse_json(_read_bound(commit_path, manifest['commit_sha256'], 'original_COMMIT_bytes_hash'))
    require(checkpoint['schema'] == NATIVE_SCHEMA and checkpoint['base_sha256'] == BASE_SHA256,
        'native_checkpoint_base_schema')
    require(_hash(checkpoint['adapter_state_sha256']), 'native_adapter_state_hash')
    expected = checkpoint['adapter_files']
    require(isinstance(expected, dict) and
        {'adapter_config.json', 'adapter_model.safetensors'} <= set(expected), 'native_adapter_inventory')
    for name, checksum in expected.items():
        require(isinstance(name, str) and Path(name).name == name and name not in ('.', '..')
            and _hash(checksum), 'adapter_inventory_path_or_hash')
    require(adapter.is_dir(), 'copied_adapter_directory')
    actual = {}
    for path in sorted(adapter.iterdir()):
        require(not path.is_symlink() and path.is_file(), 'adapter_inventory_regular_files_only')
        actual[path.name] = sha(path)
    require(actual == expected and digest(actual) == checkpoint['checkpoint_sha256']['adapter'],
        'native_adapter_file_binding')
    return dict(adapter_path=str(adapter), commit_path=str(commit_path),
        commit_sha256=manifest['commit_sha256'], adapter_files=actual,
        adapter_state_sha256=checkpoint['adapter_state_sha256'], base_sha256=BASE_SHA256)


def prepare(plan_path):
    plan_path = Path(plan_path).resolve(strict=True)
    plan_bytes = plan_path.read_bytes()
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
    require(os.environ.get('R130_ADMISSION_PLAN_SHA256') == plan_sha256, 'admission_plan_SHA256_binding')
    plan = parse_json(plan_bytes)
    require(plan['schema'] == SCHEMA and plan['model_id'] == MODEL_ID
        and plan['base_sha256'] == BASE_SHA256, 'frozen_model_contract')
    require(plan['decoder'] == DECODER, 'fixed_greedy_temp0_cap512_decoder')
    require(isinstance(plan['gpu_uuid'], str) and plan['gpu_uuid'].startswith('GPU-')
        and ',' not in plan['gpu_uuid'] and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'],
        'one_bound_GPU_environment')
    require(type(plan['hard_end_unix']) in (int, float) and math.isfinite(plan['hard_end_unix'])
        and time.time() < plan['hard_end_unix'], 'admission_deadline')
    _verify_sources(plan)
    model_dir = _path(plan['model_dir'], plan_path.parent)
    require(model_dir.is_dir(), 'local_model_directory')
    paths = {'plan': plan_path}
    hashes = {'plan': plan_sha256}
    documents = {}
    for name in ('corpus', 'manifest'):
        paths[name] = _path(plan[name + '_path'], plan_path.parent)
        hashes[name] = plan[name + '_sha256']
        documents[name] = parse_json(_read_bound(paths[name], hashes[name], name + '_SHA256_binding'))
    tasks = validate_tasks(documents['corpus'])
    checkpoint = verify_checkpoint(documents['manifest'], paths['manifest'].parent)
    output = Path(plan['output_path'])
    if not output.is_absolute():
        require('..' not in output.parts, 'output_path_traversal')
        output = plan_path.parent / output
    require(not output.is_symlink(), 'output_symlink')
    output = output.resolve()
    for protected in (Path(plan['source_root']).resolve(), model_dir, Path(checkpoint['adapter_path'])):
        require(not output.is_relative_to(protected) and not protected.is_relative_to(output),
            'separate_private_output_directory')
    require(not any(path.is_relative_to(output) for path in (*paths.values(), Path(checkpoint['commit_path']))),
        'output_cannot_contain_inputs')
    require(not output.exists(), 'new_output_directory_required')
    plan = dict(plan, model_dir=str(model_dir))
    return dict(plan=plan, paths=paths, hashes=hashes, tasks=tasks, checkpoint=checkpoint, output=output)


def _load_engine(plan, checkpoint, check):
    import torch
    from gpu import astra_experienced_event_microloop as source

    require(not torch.cuda.is_initialized(), 'fresh_process_without_resident_CUDA')
    tokenizer = source.native.load_local_tokenizer(plan['model_dir'])
    options = SimpleNamespace(model_dir=plan['model_dir'], device='cuda:0', phase='readout',
        expected_base_sha256=BASE_SHA256, adapter_dir=checkpoint['adapter_path'], gpu_uuid=plan['gpu_uuid'])
    return source.Engine(options, tokenizer, check=check)


def _snapshot(engine, plan, checkpoint):
    from gpu import orch_guided_native as weights
    from gpu.orch_r107_capability_run import assert_condition, assert_readonly

    assert_readonly(engine.model)
    assert_condition(engine.model, 'LORA_ON')
    _require_readonly(engine.model, 'LORA_ON')
    require(engine.torch.cuda.device_count() == 1, 'one_visible_GPU')
    observed = str(engine.torch.cuda.get_device_properties(0).uuid)
    if not observed.startswith('GPU-'):
        observed = 'GPU-' + observed
    require(observed == plan['gpu_uuid'], 'CUDA_UUID_mismatch')
    engine.verify_base()
    parameters = {name: parameter for name, parameter in engine.model.named_parameters() if weights.is_lora(name)}
    require(bool(parameters), 'mounted_LoRA_required')
    adapter_sha256 = weights.state_hash(parameters)
    require(adapter_sha256 == checkpoint['adapter_state_sha256'], 'immutable_adapter_state_changed')
    identity = dict(model_id=MODEL_ID, base_sha256=BASE_SHA256, adapter_state_sha256=adapter_sha256)
    return dict(identity, model_identity_sha256=digest(identity), adapter_files=checkpoint['adapter_files'],
        model_dir=plan['model_dir'], adapter_path=checkpoint['adapter_path'],
        gpu_uuid=observed, readonly=True, eval_mode=True, frozen_base_verified=True,
        runtime=getattr(engine, 'runtime', {}))


def _require_readonly(model, condition):
    require(not any(parameter.requires_grad for parameter in model.parameters()), 'readonly_parameters_required')
    require(not model.training, 'readout_eval_mode')
    states = [module.disable_adapters for module in model.modules()
        if hasattr(module, 'lora_A') and hasattr(module, 'lora_B')]
    require(bool(states) and all(state is (condition == 'LORA_OFF') for state in states),
        'readonly_adapter_condition')


def _write_once(path, payload):
    raw = payload if isinstance(payload, bytes) else (
        json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def _validate_response(response, messages, prompt_tokens, eos_token_id):
    require(isinstance(response, dict) and isinstance(response.get('raw'), str), 'response_raw_required')
    tokens = response.get('token_ids')
    require(isinstance(tokens, list) and 0 < len(tokens) <= MAX_NEW_TOKENS
        and all(type(token) is int and token >= 0 for token in tokens), 'response_tokens_required')
    require(response.get('messages') == messages and response.get('prompt_tokens') == prompt_tokens,
        'response_prompt_identity')
    terminal = tokens[-1] == eos_token_id
    require(response.get('terminal') is terminal
        and response.get('truncated') is (not terminal and len(tokens) == MAX_NEW_TOKENS),
        'response_termination_identity')
    require(terminal or response['truncated'], 'unexplained_early_termination')


def run(plan_path):
    global _PROCESS_USED

    require(os.getpid() == _IMPORT_PID and not _PROCESS_USED, 'one_checkpoint_per_fresh_process')
    context = prepare(plan_path)
    _PROCESS_USED = True
    plan, checkpoint = context['plan'], context['checkpoint']
    tasks, output = context['tasks'], context['output']
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    receipts, records = {}, []
    before_after_verified = False

    def write(name, value):
        receipts[name] = _write_once(output / name, value)

    def check(label):
        require(time.time() < plan['hard_end_unix'], 'benchmark_deadline')
        require(os.environ.get('R130_ADMISSION_PLAN_SHA256') == context['hashes']['plan'],
            'admission_plan_SHA256_binding')
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_bound_GPU_environment')

    def verify_inputs():
        check('inputs')
        for name, path in context['paths'].items():
            require(sha(path) == context['hashes'][name], 'immutable_input_changed')
        _verify_sources(plan)
        current = verify_checkpoint(parse_json(_read_bound(context['paths']['manifest'],
            context['hashes']['manifest'], 'manifest_SHA256_binding')),
            context['paths']['manifest'].parent)
        require(current == checkpoint, 'immutable_checkpoint_changed')

    provenance = dict(schema=SCHEMA, pid=os.getpid(), ppid=os.getppid(),
        plan_sha256=context['hashes']['plan'], corpus_sha256=context['hashes']['corpus'],
        manifest_sha256=context['hashes']['manifest'], checkpoint=checkpoint,
        model_id=MODEL_ID, base_sha256=BASE_SHA256, decoder=DECODER, conditions=list(CONDITIONS),
        training_updates=0, optimizer_loaded=False, parent_present=False, history_present=False,
        held_artifacts_private=True, started_unix=time.time())
    try:
        write('REQUEST.json', provenance)
        for name, path in context['paths'].items():
            write(name.upper() + '.original.json', _read_bound(path, context['hashes'][name],
                'immutable_input_changed'))
        write('COMMIT.original.json', _read_bound(checkpoint['commit_path'], checkpoint['commit_sha256'],
            'original_COMMIT_bytes_hash'))
        verify_inputs()
        engine = _load_engine(plan, checkpoint, check)
        before = None
        try:
            before = _snapshot(engine, plan, checkpoint)
            verify_inputs()
            write('BEFORE.json', dict(before, status='PASS', observed_unix=time.time()))
            from gpu.orch_r107_capability_run import assert_readonly, ordered_conditions, readonly_condition

            for position, task in enumerate(tasks):
                for condition in ordered_conditions(position):
                    verify_inputs()
                    name = f'CALL_{len(records):05d}'
                    messages = deepcopy(task['messages'])
                    record = dict(task_id=task['task_id'], family=task['family'], condition=condition,
                        position=position, messages=deepcopy(messages), status='RESERVED',
                        started_unix=time.time(), corpus_sha256=context['hashes']['corpus'],
                        plan_sha256=context['hashes']['plan'], decoder=DECODER)
                    write(name + '.RESERVED.json', record)
                    started = time.perf_counter()
                    try:
                        prompt_ids = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                            add_generation_prompt=True, return_dict=False)
                        require(isinstance(prompt_ids, list) and bool(prompt_ids)
                            and all(type(token) is int and token >= 0 for token in prompt_ids),
                            'prompt_token_ids_required')
                        record.update(prompt_token_ids=prompt_ids, prompt_token_ids_sha256=digest(prompt_ids))
                        with readonly_condition(engine.model, condition):
                            _require_readonly(engine.model, condition)
                            generation_started = time.perf_counter()
                            try:
                                response = engine.generate(messages, max_new_tokens=MAX_NEW_TOKENS)
                                record['response'] = deepcopy(response)
                            finally:
                                record['generation_seconds'] = time.perf_counter() - generation_started
                        record['status'] = 'GENERATED'
                        write(name + '.RAW.json', record)
                        require(messages == task['messages'], 'task_messages_mutated')
                        _validate_response(response, task['messages'], len(prompt_ids), engine.tokenizer.eos_token_id)
                        assert_readonly(engine.model)
                        _require_readonly(engine.model, 'LORA_ON')
                        verify_inputs()
                        record.update(status='COMPLETE', response_valid=not response['truncated'],
                            score=score_response(task, response['raw']),
                            descriptive=descriptive_metrics(response))
                    except BaseException as error:
                        record.update(status='FAILED', error_type=type(error).__name__)
                        raise
                    finally:
                        record.update(finished_unix=time.time(), elapsed_seconds=time.perf_counter() - started)
                        records.append(record)
                        write(name + '.json', record)
        finally:
            try:
                after = _snapshot(engine, plan, checkpoint)
                require(before is not None and after == before, 'before_after_model_identity_changed')
                verify_inputs()
                write('AFTER.json', dict(after, status='PASS', unchanged=True, observed_unix=time.time()))
                before_after_verified = True
            except BaseException as error:
                write('AFTER.json', dict(status='FAILED', unchanged=False, error_type=type(error).__name__,
                    observed_unix=time.time()))
                raise
        require(len(records) == 2 * len(tasks), 'all_expected_calls_required')
        verify_inputs()
        for name, expected in receipts.items():
            require(sha(output / name) == expected, 'immutable_receipt_changed')
        complete = dict(provenance, status='COMPLETE', calls=len(records),
            before_after_verified=before_after_verified, coverage=reduce_coverage(tasks, records),
            receipts=dict(receipts), finished_unix=time.time())
        write('COMPLETE.json', complete)
        return complete
    except BaseException as error:
        write('FAILED.json', dict(provenance, status='FAILED', error_type=type(error).__name__,
            before_after_verified=before_after_verified, calls=len(records),
            coverage=reduce_coverage(tasks, records), receipts=dict(receipts), finished_unix=time.time()))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description='Private R130/R132 checkpoint benchmark; caller owns GPU admission.')
    parser.add_argument('--plan', type=Path, required=True)
    options = parser.parse_args(argv)
    try:
        run(options.plan)
    except BaseException:
        print('FAILED: inspect private node-local receipts; no held content is printed.')
        return 1
    print('COMPLETE: private node-local receipts saved; no held content is printed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
