"""One-shot support_none sleep11 recovery, never an admission/launch bypass.

Use only inside the existing admitted node3 containment, with a fresh child
loaded from sleep10. Main must acknowledge the exact recovery manifest before
GPU use. recover_rng leaves the original journal and pending sleep unchanged;
finish_pending_sleep explicitly accounts for the abandoned historical update.
There is deliberately no standalone GPU launch entry point or automatic retry.
"""

import ast
from copy import deepcopy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import random
import textwrap
import time

from organism_v6.orch_r125_continual_stream import digest, require


SCHEMA = 'R142_SUPPORT_RECOVERY_V1'
BASE = Path('/localhome/local-rohing/orch_r133_node3_support_none_20260916_attempt1')
ROOT = BASE / 'run1'
SOURCE = BASE / 'source1'
GPU_UUID = 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8'
ALLOCATOR = 'expandable_segments:True'
HEAD = 'ccd4e1c2949fcf51a64c2081e3ea756991de0bd37e46978464db963587b2fca2'
SLEEP_REQUEST = 'a8c8871687d5ecf6d955f32970ad78b384654e5587981eb8dca406eb93dde2a5'
SAVED = '100017b46e08ca8825c38c1c3f5c30d35749651372270effcdfd354357a727b0'
RECOVERY = ROOT / 'recoveries' / 'r142-support-sleep11-20260916-attempt1'
SEMANTICS = 'preserve_historical_abandoned_update411_recompute_sleep11_from_sleep10'
TAIL = ('SLEEP_COMPLETE', 'INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED',
        'REQUEST', 'RESPONSE', 'COMMITTED', 'SLEEP_REQUEST', 'TARGET_ELIGIBILITY', 'UPDATE')
PINS = {
    'control1/GUARD.json': '9dd831e48976573a36128c7fe8b809d7526ea74978703021e7a9a37455475dc4',
    'control1/PLAN.json': '5a5b796f02d084fb14e4874f87afd46f05461e96838c611ef1cbbd902b58b666',
    'control1/EXIT.json': 'f509c6e073eb8daf9161e873e3a91b9845c5e6adccf2cb3c61d1e348d49f97c6',
    'control1/NATIVE.log': '3c07f7852be31b99e85685cb5ed9245bddb459fd4d82a0c0a83afda98b4371eb',
    'run1/checkpoints/sleep_000010/COMMIT.json': '9f0dcd1ef2e2cac231f0a59885cfa4ce188411f91ee6ebc25c31939d4d325cf9',
    'source1/gpu/orch_r125_continual_native.py': '6b46401e5f8ff92d95e018b481d2303a55a3ce7c8e617aec65faa64bbc8381c7',
    'source1/gpu/orch_r133_node3_programmes.py': '9f78c7983e4cc0c6142f9500ee0f95af2878120639db4557074a932742373e0c',
}


def raw(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_evidence_path')
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_evidence_symlinks')
    return path.read_bytes()


def sha(path):
    return hashlib.sha256(raw(path)).hexdigest()


def save_bytes(path, value):
    with Path(path).open('xb') as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save(path, document):
    save_bytes(path, (json.dumps(document, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())


def pinned_evidence():
    result = {}
    for name, expected in PINS.items():
        value = raw(BASE / name)
        require(hashlib.sha256(value).hexdigest() == expected, 'original_evidence_hash:' + name)
        result[name] = value
    guard = json.loads(result['control1/GUARD.json'])
    require(guard['plan_sha256'] == PINS['control1/PLAN.json'], 'original_guard_plan_binding')
    for name, expected in guard['source_pins'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'source_relative_path')
        require(sha(SOURCE / name) == expected, 'original_source_closure:' + name)
    exited = json.loads(result['control1/EXIT.json'])
    log = result['control1/NATIVE.log'].decode()
    require(type(exited['exit_code']) is int and exited['exit_code'] == 1, 'original_failed_exit')
    require(log.count('Traceback (most recent call last):') == 1
            and 'torch.OutOfMemoryError: CUDA out of memory.' in log
            and '(loss*weight).backward()' in log, 'original_backward_OOM')
    checkpoint = json.loads(result['run1/checkpoints/sleep_000010/COMMIT.json'])
    verify_saved_files(checkpoint)
    return result


def verify_saved_files(checkpoint):
    directory = ROOT / 'checkpoints' / 'sleep_000010'
    require(checkpoint['optimizer_steps'] == 410
            and checkpoint['adapter_path'] == str(directory / 'adapter')
            and checkpoint['optimizer_rng_path'] == str(directory / 'optimizer_rng.pt'), 'sleep10_paths_steps')
    files = checkpoint['adapter_files']
    require(set(path.name for path in (directory / 'adapter').iterdir()) == set(files), 'exact_adapter_inventory')
    for name, expected in files.items():
        require(Path(name).name == name and name not in ('.', '..'), 'adapter_basename')
        require(sha(directory / 'adapter' / name) == expected, 'adapter_file_hash')
    hashes = checkpoint['checkpoint_sha256']
    require(digest(files) == hashes['adapter']
            and sha(checkpoint['optimizer_rng_path']) == hashes['optimizer'] == hashes['rng'], 'saved_file_hashes')


def verify_manifest(manifest, acknowledgment):
    require(set(manifest) == {'schema', 'root', 'recovery_root', 'semantics', 'journal_head',
            'module_sha256', 'cpu_evidence', 'allocator'}, 'explicit_manifest_fields')
    require(manifest['schema'] == SCHEMA and manifest['root'] == str(ROOT)
            and manifest['recovery_root'] == str(RECOVERY) and manifest['journal_head'] == HEAD
            and manifest['semantics'] == SEMANTICS and manifest['allocator'] == ALLOCATOR, 'exact_recovery_scope')
    require(manifest['module_sha256'] == sha(Path(__file__).absolute()), 'reviewed_recovery_module')
    reference = manifest['cpu_evidence']
    require(set(reference) == {'path', 'sha256'} and sha(reference['path']) == reference['sha256'], 'CPU_evidence_hash')
    cpu = json.loads(raw(reference['path']))
    require(cpu.get('status') == 'PASS' and cpu.get('module_sha256') == manifest['module_sha256'], 'CPU_gate_same_module')
    require(set(acknowledgment) == {'path', 'sha256'}
            and sha(acknowledgment['path']) == acknowledgment['sha256'], 'Main_acknowledgment_hash')
    acknowledged = json.loads(raw(acknowledgment['path']))
    require(acknowledged.get('author') == 'Main' and acknowledged.get('approved') is True
            and acknowledged.get('manifest_sha256') == digest(manifest), 'Main_acknowledges_exact_manifest')


def allocator_command(command):
    command = list(command)
    require(command.count('/usr/bin/env') == 1, 'one_contained_env')
    position = command.index('/usr/bin/env')
    require(command[position+1] == '-i' and '--property=DevicePolicy=strict' in command[:position],
            'original_strict_clean_environment')
    allowed = [item for item in command[:position] if item.startswith('--property=DeviceAllow=/dev/nvidia')]
    require(sorted(allowed) == sorted(['--property=DeviceAllow=/dev/nvidia6 rw',
            '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw']),
            'only_support_physical6')
    require('CUDA_VISIBLE_DEVICES='+GPU_UUID in command[position+2:], 'contained_GPU_UUID')
    require(not any(item.startswith(('PYTORCH_CUDA_ALLOC_CONF=', 'PYTORCH_ALLOC_CONF='))
                    for item in command), 'no_conflicting_allocator')
    command.insert(position+2, 'PYTORCH_CUDA_ALLOC_CONF='+ALLOCATOR)
    return command


def runtime_environment(torch, proc_environ=None):
    environ = raw(f'/proc/{os.getpid()}/environ') if proc_environ is None else proc_environ
    actual = dict(item.split(b'=', 1) for item in environ.split(b'\0') if b'=' in item)
    for key, expected in [('CUDA_VISIBLE_DEVICES', GPU_UUID), ('PYTORCH_CUDA_ALLOC_CONF', ALLOCATOR)]:
        require(os.environ.get(key) == expected and actual.get(key.encode()) == expected.encode(),
                'inherited_native_environment:' + key)
    require('PYTORCH_ALLOC_CONF' not in os.environ and b'PYTORCH_ALLOC_CONF' not in actual,
            'no_allocator_alias_override')
    require(torch.cuda.device_count() == 1 and torch.cuda.memory.get_allocator_backend() == 'native',
            'single_native_allocator_device')
    return dict(pid=os.getpid(), allocator=ALLOCATOR, allocator_backend='native', gpu_uuid=GPU_UUID,
                proc_environ_verified=True, checked_unix=time.time())


def journal_records(journal):
    state = journal._scan()
    records = [journal._read_json(journal._records_fd, f'{index:020d}.json') for index in range(state['index'])]
    require(records and records[-1]['sha256'] == state['previous'], 'stable_journal_head')
    return state, records


def bind(child, stream, journal, checkpoint):
    state, records = journal_records(journal)
    require(journal.root == ROOT / 'stream' and child.plan['root'] == str(ROOT), 'same_life_root')
    require(len(records) == 515 and tuple(item['kind'] for item in records[504:]) == TAIL
            and records[504]['sha256'] == SAVED and records[512]['sha256'] == SLEEP_REQUEST
            and records[514]['sha256'] == HEAD, 'exact_support_504_514_suffix')
    require(state['request'] is None and state['response'] is None and state['sleep_request'] == {'cycle': 11}
            and state['latest']['document'] == stream.checkpoint(), 'pending_sleep11_stream_binding')
    require(len(stream.sleep_receipts) == 10 and stream.sleep_receipts[-1]['checkpoint'] == checkpoint
            and records[504]['document']['checkpoint'] == checkpoint
            and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']), 'last_saved_sleep10')
    require(child.optimizer_steps == 410 and checkpoint['optimizer_steps'] == 410
            and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'loaded_sleep10_adapter410')
    require(child.plan['segment_tokens'] == stream.segment_tokens
            and child.plan['context_limit'] == stream.context_limit
            and child.plan['hard_end_unix'] == stream.deadline_unix, 'unchanged_stream_budget')
    presentation = dict(version=child.plan['presentation_version'], system_prompt=child.plan['system_prompt'],
                        birth_prompt=child.plan['birth_prompt'])
    require(stream.presentation == presentation, 'unchanged_presentation_during_recovery')
    rows = deepcopy(stream.pending_rows())
    require(len(rows) == 2 and stream.pending == 'sleep:'+digest([row['source_sha256'] for row in rows]),
            'two_pending_child_rows')
    for row, index in zip(rows, (506, 509)):
        request = {key: value for key, value in records[index]['document'].items() if key != 'resume_state'}
        response = records[index+1]['document']
        commit = records[index+2]['document']
        output = response['response']
        require(request['split'] == row['split'] == 'TRAIN' and row['actor'] == 'child'
                and row['prefix_loss'] is False and row['target_loss'] is True, 'only_committed_TRAIN_child')
        require(request['segment'] == row['segment'] == commit['segment']
                and digest(request) == response['request_sha256']
                and digest(response) == row['source_sha256'] == commit['source_sha256']
                and response['raw_saved_before_validation'] is True, 'committed_raw_chain')
        require(request['messages'] == row['prefix'] and request['retry_allowed'] is False
                and request['max_new_tokens'] == child.plan['segment_tokens']
                and request['deadline_unix'] == child.plan['hard_end_unix']
                and request['model_state_sha256'] == row['model_state_sha256'] == stream.model_state_sha256,
                'original_generation_request')
        require(output['raw'] == row['target'] and output['token_ids'] == row['token_ids']
                and type(output['terminal']) is bool and output['terminal'] is row['terminal']
                and type(output['truncated']) is bool and output['truncated'] is row['truncated']
                and output['decoder'] == child.plan['decoder']
                and output['adapter_state_sha256'] == checkpoint['adapter_state_sha256']
                and output['base_sha256'] == checkpoint['base_sha256']
                and output['prompt_tokens'] == request['prompt_tokens'], 'original_generation_response')
    eligibility = records[513]['document']
    require(eligibility['raw_modified'] is False and eligibility['version'] == presentation['version']
            and eligibility['excluded'] == []
            and eligibility['new_row_sha256'] == [row['source_sha256'] for row in rows]
            and eligibility['rehearsal_row_sha256'] == [row['source_sha256'] for row in stream.rows[:stream.sleep_frontier]],
            'all_original_new_and_rehearsal_rows')
    require(records[514]['document']['optimizer_step'] == 411
            and records[514]['document']['source_sha256'] == rows[0]['source_sha256'], 'one_historical_update411')
    return records


def rng(child):
    return dict(python=digest(random.getstate()), cpu=digest(child.torch.get_rng_state().tolist()),
                cuda=[digest(value.tolist()) for value in child.torch.cuda.get_rng_state_all()])


def optimizer_fingerprint(child, state=None):
    def encode(value):
        if isinstance(value, child.torch.Tensor):
            tensor = value.detach().cpu().contiguous()
            value_bytes = tensor.reshape(-1).view(child.torch.uint8).numpy().tobytes()
            return dict(dtype=str(tensor.dtype), shape=list(tensor.shape), sha256=hashlib.sha256(value_bytes).hexdigest())
        if isinstance(value, dict):
            return [[repr(key), encode(item)] for key, item in sorted(value.items(), key=lambda pair: repr(pair[0]))]
        if isinstance(value, (list, tuple)):
            return [encode(item) for item in value]
        require(value is None or type(value) in (int, float, bool, str), 'optimizer_state_type')
        return value
    return digest(encode(child.optimizer.state_dict() if state is None else state))


def restore(child, checkpoint):
    verify_saved_files(checkpoint)
    child.verify_checkpoint(checkpoint)
    require(isinstance(child.optimizer, child.torch.optim.AdamW), 'actual_AdamW')
    payload = child.torch.load(io.BytesIO(raw(checkpoint['optimizer_rng_path'])), map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == 410 and payload['parameter_names'] == list(child.parameters)
            and payload.get('experiment') == checkpoint.get('experiment') == getattr(child, 'experiment', None),
            'saved_optimizer_order_experiment')
    require(child.optimizer_steps == 410 and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'restored_adapter410')
    child.engine.verify_base()
    expected = optimizer_fingerprint(child, payload['optimizer'])
    child.optimizer.load_state_dict(payload['optimizer'])
    require(optimizer_fingerprint(child) == expected, 'exact_saved_AdamW')
    child.torch.set_rng_state(payload['cpu_rng'])
    child.torch.cuda.set_rng_state_all(payload['cuda_rng'])
    random.setstate(payload['python_rng'])
    require(rng(child) == dict(python=digest(payload['python_rng']), cpu=digest(payload['cpu_rng'].tolist()),
            cuda=[digest(value.tolist()) for value in payload['cuda_rng']]), 'exact_saved_RNG')
    verify_saved_files(checkpoint)
    return expected


def verify_runtime(child, evidence):
    original = json.loads(evidence['control1/PLAN.json'])
    normalized = deepcopy(child.plan)
    normalized['source_root'] = original['source_root']
    if 'startup_context' in original:
        relative = Path(original['startup_context']['path']).relative_to(SOURCE)
        relocated = Path(child.plan['source_root']) / relative
        require(child.plan['startup_context']['path'] == str(relocated)
                and raw(relocated) == raw(SOURCE / relative), 'exact_startup_relocation')
        normalized['startup_context']['path'] = original['startup_context']['path']
    require(normalized == original, 'no_recipe_deadline_visibility_changes')
    require(child.plan['physical'] == 6 and child.plan['gpu_uuid'] == GPU_UUID, 'owned_physical6')
    source = evidence['source1/gpu/orch_r125_continual_native.py'].decode()
    original_class = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'NativeChild')
    for name in ('generate', 'sleep', 'checkpoint', 'verify_checkpoint'):
        original_method = next(node for node in original_class.body if isinstance(node, ast.FunctionDef) and node.name == name)
        current = ast.parse(textwrap.dedent(inspect.getsource(getattr(child, name)))).body[0]
        require(ast.dump(original_method, include_attributes=False) == ast.dump(current, include_attributes=False),
                'unchanged_native_method:' + name)
    return digest(source)


def recover_rng(child, stream, journal, manifest, acknowledgment):
    verify_manifest(manifest, acknowledgment)
    environment = runtime_environment(child.torch)
    evidence = pinned_evidence()
    recipe = verify_runtime(child, evidence)
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000010/COMMIT.json'])
    with journal._mutex:
        records = bind(child, stream, journal, checkpoint)
        require(not RECOVERY.parent.is_symlink(), 'no_recovery_parent_symlink')
        RECOVERY.parent.mkdir(mode=0o700, exist_ok=True)
        RECOVERY.mkdir(mode=0o700)
        try:
            save(RECOVERY / 'MANIFEST.json', manifest)
            save(RECOVERY / 'ACKNOWLEDGMENT.json', acknowledgment)
            save(RECOVERY / 'RUNTIME_ENVIRONMENT.json', environment)
            for name, value in evidence.items():
                save_bytes(RECOVERY / name.replace('/', '__'), value)
            for index in range(504, 515):
                for suffix in ('.json', '.intent.json'):
                    name = f'{index:020d}'+suffix
                    save_bytes(RECOVERY / name, raw(journal.root / 'records' / name))
            save(RECOVERY / 'JOURNAL_EVIDENCE.json', records[504:])
            original_stream, original_plan = deepcopy(stream.checkpoint()), deepcopy(child.plan)
            optimizer = restore(child, checkpoint)
            before = rng(child)
            for number, index in enumerate((506, 509)):
                request, response = records[index]['document'], records[index+1]['document']['response']
                require(time.time() < child.plan['hard_end_unix'], 'replay_deadline')
                messages = deepcopy(request['messages'])
                save(RECOVERY / f'{number:02d}_REQUEST.json', dict(request=request, rng_before=rng(child)))
                generated = child.generate(messages, max_new_tokens=request['max_new_tokens'], deadline_unix=request['deadline_unix'])
                save(RECOVERY / f'{number:02d}_RESPONSE.json', dict(response=generated, rng_after=rng(child)))
                require(digest(generated) == digest(response), 'exact_generation_match:' + str(number))
                require(messages == request['messages'] and stream.checkpoint() == original_stream
                        and child.plan == original_plan, 'no_replay_history_plan_mutation')
                require(child.optimizer_steps == 410 and child.adapter_hash() == checkpoint['adapter_state_sha256']
                        and optimizer_fingerprint(child) == optimizer, 'no_replay_learning_mutation')
                child.engine.verify_base()
            require(bind(child, stream, journal, checkpoint) == records, 'journal_unchanged_after_replay')
            require(pinned_evidence() == evidence and verify_runtime(child, evidence) == recipe, 'evidence_recipe_unchanged')
            require(time.time() < child.plan['hard_end_unix'], 'replay_completed_within_wall')
            receipt = dict(schema=SCHEMA, status='GENERATIONS_VERIFIED_NOT_SLEEP_RECOVERED', manifest_sha256=digest(manifest),
                original_head=HEAD, matched_generations=2, optimizer_steps=410, optimizer_updates=0,
                historical_abandoned_updates=1, historical_update_record=514, historical_update_optimizer_step=411,
                historical_partial_backward_may_have_unrecorded_gradients=True, original_update411_state_available=False,
                exact_update411_replay_claim=False, original_postgeneration_rng_snapshot_available=False,
                verification='exact_committed_outputs_from_saved_RNG_not_comparison_to_missing_final_RNG',
                rng_before=before, rng_after=rng(child), optimizer_state_sha256=optimizer,
                pending_unchanged=True, stream_sha256=original_stream['sha256'], no_retry=True, finished_unix=time.time())
            save(RECOVERY / 'GENERATIONS_VERIFIED.json', receipt)
            return receipt
        except BaseException as error:
            save(RECOVERY / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
                child_must_be_discarded=True, no_retry=True, finished_unix=time.time()))
            raise


def finish_pending_sleep(child, stream, journal, anchors, manifest, acknowledgment, replay_receipt):
    verify_manifest(manifest, acknowledgment)
    require(json.loads(raw(RECOVERY / 'GENERATIONS_VERIFIED.json')) == replay_receipt
            and replay_receipt['manifest_sha256'] == digest(manifest), 'bound_generation_receipt')
    require(rng(child) == replay_receipt['rng_after'] and child.optimizer_steps == 410
            and optimizer_fingerprint(child) == replay_receipt['optimizer_state_sha256'], 'fresh_verified_replay_child')
    evidence = pinned_evidence()
    verify_runtime(child, evidence)
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000010/COMMIT.json'])
    with journal._mutex:
        records = bind(child, stream, journal, checkpoint)
        require(not (ROOT / 'checkpoints' / 'sleep_000011').exists(), 'never_repeat_saved_sleep11')
        save(RECOVERY / 'RECOMPUTE_STARTED.json', dict(manifest_sha256=digest(manifest), started_unix=time.time()))
        try:
            runtime_environment(child.torch)
            child.check('r142_recompute_sleep11')
            accounting = dict(schema=SCHEMA, semantics=SEMANTICS, recovery_root=str(RECOVERY),
                manifest_sha256=digest(manifest), original_head=HEAD, abandoned_update_record=514,
                abandoned_optimizer_step=411, checkpoint_optimizer_steps=410, replacement_starts_at=411,
                historical_updates_retained=True, original_update411_state_available=False,
                exact_update411_replay_claim=False, replacement_attempt='r142-support-sleep11-attempt1')
            journal.record('CHECKPOINT_METADATA', dict(r142_recovery=accounting))
            child.torch.cuda.synchronize()
            child.torch.cuda.reset_peak_memory_stats()
            updates = []

            def record(kind, document):
                if kind == 'TARGET_ELIGIBILITY':
                    require(document == records[513]['document'], 'identical_training_eligibility')
                elif kind == 'UPDATE':
                    require(document['optimizer_step'] == 411+len(updates), 'replacement_contiguous_optimizer_steps')
                    updates.append(deepcopy(document))
                    document = dict(document, r142_attempt=accounting['replacement_attempt'],
                                    r142_original_abandoned_record=514)
                journal.record(kind, document)

            receipt = child.sleep(stream.pending_rows(), stream.rows[:stream.sleep_frontier], anchors, record)
            require(len(updates) == receipt['optimizer_steps'] == 52 and child.optimizer_steps == 462,
                    'full_32_new_20_rehearsal_updates')
            child.torch.cuda.synchronize()
            free, total = child.torch.cuda.mem_get_info()
            memory = dict(max_allocated_bytes=child.torch.cuda.max_memory_allocated(),
                max_reserved_bytes=child.torch.cuda.max_memory_reserved(), free_bytes=free, total_bytes=total,
                observation='completed_actual_sleep11')
            memory['capacity_valid'] = (0 <= free <= total and total > 0
                and 0 <= memory['max_allocated_bytes'] <= memory['max_reserved_bytes'] <= total)
            save(RECOVERY / 'ACTUAL_SLEEP_MEMORY.json', memory)
            saved = child.checkpoint(ROOT / 'checkpoints' / 'sleep_000011')
            require(saved['optimizer_steps'] == 462 and saved.get('experiment') == stream.experiment,
                    'replacement_checkpoint_continuity')
            receipt.update(status='COMPLETE', cycle=11, checkpoint=saved, checkpoint_sha256=saved['checkpoint_sha256'],
                new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()], r142_recovery=accounting,
                r142_memory=memory)
            stream.pending = None
            stream.commit_sleep(receipt, journal.record)
            require(journal_records(journal)[1][:515] == records, 'original_history_prefix_preserved')
            pinned_evidence()
            save(RECOVERY / 'SLEEP_RECOMPUTED.json', dict(status='SLEEP11_SAVED', optimizer_steps=462,
                historical_abandoned_updates=1, replacement_updates=52, memory=memory,
                exact_original_post411_state_claim=False, finished_unix=time.time()))
            require(memory['capacity_valid'], 'invalid_GPU_memory_capacity')
            return saved
        except BaseException as error:
            save(RECOVERY / 'RECOMPUTE_FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
                original_suffix_preserved=True, no_retry=True, finished_unix=time.time()))
            raise


def adapted_node_function(action):
    from gpu import orch_r133_node3_programmes as programmes
    require(action in ('supervise', 'contained_native'), 'only_original_node_launch_functions')
    require(sha(Path(programmes.__file__).absolute()) == PINS['source1/gpu/orch_r133_node3_programmes.py'],
            'original_node_launcher_bytes')
    source = inspect.getsource(getattr(programmes, action))
    before = ('gpu.orch_r133_node3_programmes' if action == 'supervise' else 'gpu.orch_r125_continual_guard')
    require(source.count(repr(before)) == 1, 'one_exact_entrypoint_relocation')
    modified = source.replace(repr(before), repr('gpu.orch_r142_support_recovery'))
    original_tree, modified_tree = ast.parse(source), ast.parse(modified)
    replacements = 0
    for node in ast.walk(modified_tree):
        if isinstance(node, ast.Constant) and node.value == 'gpu.orch_r142_support_recovery':
            node.value = before
            replacements += 1
    require(replacements == 1 and ast.dump(original_tree) == ast.dump(modified_tree), 'only_entrypoint_literal_changed')
    namespace = dict(getattr(programmes, action).__globals__)
    if action == 'supervise':
        def contained_command(plan, policy, command, lifetime):
            require(policy['minor'] == 6 and programmes.device_minor(plan['gpu_uuid']) == 6,
                    'actual_UUID_minor6_not_index_assumption')
            return allocator_command(programmes.containment_command(plan, policy, command, lifetime))
        namespace['containment_command'] = contained_command
    exec(compile(modified, str(Path(__file__).absolute())+':'+action, 'exec'), namespace)
    return namespace[action]


def recover_admitted_sleep(plan_path, manifest, acknowledgment):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, verify_experiment_resume
    plan = native.validate_plan(native.read(plan_path))
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == sha(plan_path), 'original_admitted_plan_environment')
    verify_manifest(manifest, acknowledgment)
    evidence = pinned_evidence()
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000010/COMMIT.json'])
    import torch
    environment = runtime_environment(torch)
    save(Path(plan_path).parent / 'R142_PREMODEL_ENVIRONMENT.json', environment)
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        state = journal.latest_checkpoint()
        stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
        verify_experiment_resume(plan, stream.experiment)
        require(checkpoint.get('experiment') == stream.experiment, 'original_stream_model_experiment')
        child = native.NativeChild(plan, checkpoint)
        replay = recover_rng(child, stream, journal, manifest, acknowledgment)
        anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
        save(RECOVERY / 'ANCHOR_INVENTORY.json', anchor_receipt)
        saved = finish_pending_sleep(child, stream, journal, anchors, manifest, acknowledgment, replay)
        return saved


def entrypoint():
    import argparse
    from gpu import orch_r125_continual_guard as guard
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('supervise', 'contained-native', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--release', type=Path)
    arguments = parser.parse_args()
    config, plan = guard.validate(arguments.config)
    manifest_ref, acknowledgment = config['r142_manifest'], config['r142_acknowledgment']
    require(sha(manifest_ref['path']) == manifest_ref['sha256'], 'guard_manifest_binding')
    manifest = json.loads(raw(manifest_ref['path']))
    verify_manifest(manifest, acknowledgment)
    require(config['resume'] is True and plan['physical'] == 6 and plan['root'] == str(ROOT), 'same_life_resume_only')
    if arguments.action == 'supervise':
        require(arguments.release is not None, 'original_release_required')
        adapted_node_function('supervise')(arguments.config, arguments.release)
    elif arguments.action == 'contained-native':
        adapted_node_function('contained_native')(arguments.config)
    else:
        original_run = guard.child.run

        def recovered_run(plan_path, *, resume=False):
            require(resume is True, 'never_fresh_initialization')
            recover_admitted_sleep(plan_path, manifest, acknowledgment)
            import gc
            import torch
            gc.collect()
            torch.cuda.empty_cache()
            guard.child.run = original_run
            original_run(plan_path, resume=True)

        guard.child.run = recovered_run
        guard.native_entry(arguments.config)


if __name__ == '__main__':
    entrypoint()
