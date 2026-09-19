"""Exact kernel4 sleep19 target-only recovery with original admission.

Use only inside the existing admitted node3 containment, with a fresh child
loaded from sleep18. Main must acknowledge the exact recovery manifest before
GPU use. recover_rng leaves the original journal and pending sleep unchanged;
Only the pinned offending TRAIN target is excluded; encode_own and raw history remain unchanged.
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


SCHEMA = 'R144_KERNEL4_RECOVERY_V1'
BASE = Path('/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1')
ROOT = BASE / 'run1'
SOURCE = BASE / 'source1'
GPU_UUID = 'GPU-f83fb491-34ce-4176-5852-c94652151a9f'
OFFENDING = 'c13b5d1a417ef931bdd1cca49a2dc4dbaa3ea78793f70433bab3c0f7e1a0700f'
REASON = 'r144_pinned_generated_special_token_target_excluded'
HEAD = 'a9db63b469781170ff2c1b3530f8620342c8bc4d2dfe327f5c658784e76ed5d2'
SLEEP_REQUEST = 'fc81215f0d5326b920b0128630798029a69d05713dadad8bd7b8287dfd9d549b'
SAVED = 'dd89159d7b79caf20f84788ce929bfbc2c074e67fe450f09078289730d01c976'
RECOVERY = ROOT / 'recoveries' / 'r144-kernel4-sleep19-20260916-attempt1'
SEMANTICS = 'exact_three_generation_replay_then_pinned_target_only_exclusion_sleep19'
TAIL = ('SLEEP_COMPLETE', 'INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED',
        'REQUEST', 'RESPONSE', 'COMMITTED', 'INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED',
        'COMPACTION', 'SLEEP_REQUEST', 'TARGET_ELIGIBILITY')
PINS = {'control1/GUARD.json': 'd0aa69f309cb0a4667842cc8e53c105df23f906a2ca69f083b3881b00a80fd39', 'control1/PLAN.json': 'e39cac44c917eec30f30cedb7005bff2dbd2bafc9656020d78a129281ebe8013', 'control1/EXIT.json': 'b9149014d293f90a32b1c0e47fe7ceed854657cf7d69f4624cb3c3c3f3078f43', 'control1/NATIVE.log': '5a129b67cf8ad222aa4462bf444e8a38004193ea1bbbdc9fb2d0b4cbce956f02', 'run1/checkpoints/sleep_000018/COMMIT.json': '209f06a0c59f86834286661f144e70bc6a55f2ec43c7929697f922a7dbc07f1b', 'source1/gpu/orch_r125_continual_native.py': '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526', 'source1/gpu/orch_r125_continual_guard.py': '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3', 'source1/organism_v6/orch_r125_plain_context.py': 'b3859e4a45d53fc67c51add5dad8431985ca0adda901389e0206819a56245d92'}


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
            and 'ValueError: no_special_token_target_injection' in log
            and 'encode_own(row, self.tokenizer' in log, 'original_special_target_rejection')
    checkpoint = json.loads(result['run1/checkpoints/sleep_000018/COMMIT.json'])
    verify_saved_files(checkpoint)
    return result


def verify_saved_files(checkpoint):
    directory = ROOT / 'checkpoints' / 'sleep_000018'
    require(checkpoint['optimizer_steps'] == 1323
            and checkpoint['adapter_path'] == str(directory / 'adapter')
            and checkpoint['optimizer_rng_path'] == str(directory / 'optimizer_rng.pt'), 'sleep18_paths_steps')
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
            'module_sha256', 'cpu_evidence', 'target_exclusion'}, 'explicit_manifest_fields')
    require(manifest['schema'] == SCHEMA and manifest['root'] == str(ROOT)
            and manifest['recovery_root'] == str(RECOVERY) and manifest['journal_head'] == HEAD
            and manifest['semantics'] == SEMANTICS and manifest['target_exclusion'] == OFFENDING, 'exact_recovery_scope')
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


def runtime_environment(torch, proc_environ=None):
    environ = raw(f'/proc/{os.getpid()}/environ') if proc_environ is None else proc_environ
    actual = dict(item.split(b'=', 1) for item in environ.split(b'\0') if b'=' in item)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == GPU_UUID
            and actual.get(b'CUDA_VISIBLE_DEVICES') == GPU_UUID.encode(), 'inherited_original_GPU_UUID')
    require(torch.cuda.device_count() == 1, 'single_original_device')
    return dict(pid=os.getpid(), gpu_uuid=GPU_UUID, proc_environ_verified=True,
                allocator_environment=os.environ.get('PYTORCH_CUDA_ALLOC_CONF'), checked_unix=time.time())


def eligible_rows(rows, presentation, original):
    before = digest(rows)
    retained, corrections = [], []
    for row in rows:
        if row['source_sha256'] != OFFENDING:
            retained.append(row)
            continue
        require(row['split'] == 'TRAIN' and row['actor'] == 'child'
                and row['prefix_loss'] is False and row['target_loss'] is True, 'exact_child_exclusion_provenance')
        require(len(row['token_ids']) == 512 and row['terminal'] is False and row['truncated'] is True
                and [index for index, token in enumerate(row['token_ids']) if token == 151644] == [362, 372, 373],
                'exact_offending_generated_delimiters')
        corrections.append(dict(source_sha256=OFFENDING, reason=REASON))
    accepted, excluded = original(retained, presentation)
    require(digest(rows) == before, 'raw_history_carry_rows_unchanged')
    return accepted, excluded + corrections


def corrected_eligibility(document):
    expected = deepcopy(document)
    require(expected['new_row_sha256'].count(OFFENDING) == 1
            and OFFENDING not in expected['rehearsal_row_sha256'] and expected['excluded'] == [],
            'one_original_offending_NEW_target')
    expected['new_row_sha256'].remove(OFFENDING)
    expected['excluded'] = [dict(source_sha256=OFFENDING, reason=REASON, cohort='NEW')]
    return expected


def journal_records(journal):
    state = journal._scan()
    records = [journal._read_json(journal._records_fd, f'{index:020d}.json') for index in range(state['index'])]
    require(records and records[-1]['sha256'] == state['previous'], 'stable_journal_head')
    return state, records


def bind(child, stream, journal, checkpoint):
    state, records = journal_records(journal)
    require(journal.root == ROOT / 'stream' and child.plan['root'] == str(ROOT), 'same_life_root')
    require(len(records) == 1598 and tuple(item['kind'] for item in records[1583:]) == TAIL
            and records[1583]['sha256'] == SAVED and records[1596]['sha256'] == SLEEP_REQUEST
            and records[1597]['sha256'] == HEAD, 'exact_kernel4_833_841_suffix')
    require(state['request'] is None and state['response'] is None and state['sleep_request'] == {'cycle': 19}
            and state['latest']['document'] == stream.checkpoint(), 'pending_sleep19_stream_binding')
    require(len(stream.sleep_receipts) == 18 and stream.sleep_receipts[-1]['checkpoint'] == checkpoint
            and records[1583]['document']['checkpoint'] == checkpoint
            and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']), 'last_saved_sleep18')
    require(child.optimizer_steps == 1323 and checkpoint['optimizer_steps'] == 1323
            and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'loaded_sleep18_adapter1323')
    require(child.plan['segment_tokens'] == stream.segment_tokens
            and child.plan['context_limit'] == stream.context_limit
            and child.plan['hard_end_unix'] == stream.deadline_unix, 'unchanged_stream_budget')
    presentation = dict(version=child.plan['presentation_version'], system_prompt=child.plan['system_prompt'],
                        birth_prompt=child.plan['birth_prompt'])
    require(stream.presentation == presentation, 'unchanged_presentation_during_recovery')
    rows = deepcopy(stream.pending_rows())
    require(len(rows) == 3 and stream.pending == 'sleep:'+digest([row['source_sha256'] for row in rows]),
            'three_pending_child_rows')
    for row, index in zip(rows, (1585, 1588, 1592)):
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
    eligibility = records[1597]['document']
    require(eligibility['raw_modified'] is False and eligibility['version'] == presentation['version']
            and eligibility['excluded'] == []
            and eligibility['new_row_sha256'] == [row['source_sha256'] for row in rows]
            and eligibility['rehearsal_row_sha256'] == [row['source_sha256'] for row in stream.rows[:stream.sleep_frontier]],
            'all_original_new_and_rehearsal_rows')
    require(not any(item['kind'] == 'UPDATE' for item in records[1585:]), 'no_unsaved_committed_updates')
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
    require(payload['optimizer_steps'] == 1323 and payload['parameter_names'] == list(child.parameters)
            and payload.get('experiment') == checkpoint.get('experiment') == getattr(child, 'experiment', None),
            'saved_optimizer_order_experiment')
    require(child.optimizer_steps == 1323 and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'restored_adapter1323')
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
    require(child.plan['physical'] == 4 and child.plan['gpu_uuid'] == GPU_UUID, 'owned_physical4')
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
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000018/COMMIT.json'])
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
            for index in range(1583, 1598):
                for suffix in ('.json', '.intent.json'):
                    name = f'{index:020d}'+suffix
                    save_bytes(RECOVERY / name, raw(journal.root / 'records' / name))
            save(RECOVERY / 'JOURNAL_EVIDENCE.json', records[1583:])
            original_stream, original_plan = deepcopy(stream.checkpoint()), deepcopy(child.plan)
            optimizer = restore(child, checkpoint)
            before = rng(child)
            for number, index in enumerate((1585, 1588, 1592)):
                request, response = records[index]['document'], records[index+1]['document']['response']
                require(time.time() < child.plan['hard_end_unix'], 'replay_deadline')
                messages = deepcopy(request['messages'])
                save(RECOVERY / f'{number:02d}_REQUEST.json', dict(request=request, rng_before=rng(child)))
                generated = child.generate(messages, max_new_tokens=request['max_new_tokens'], deadline_unix=request['deadline_unix'])
                save(RECOVERY / f'{number:02d}_RESPONSE.json', dict(response=generated, rng_after=rng(child)))
                require(digest(generated) == digest(response), 'exact_generation_match:' + str(number))
                require(messages == request['messages'] and stream.checkpoint() == original_stream
                        and child.plan == original_plan, 'no_replay_history_plan_mutation')
                require(child.optimizer_steps == 1323 and child.adapter_hash() == checkpoint['adapter_state_sha256']
                        and optimizer_fingerprint(child) == optimizer, 'no_replay_learning_mutation')
                child.engine.verify_base()
            require(bind(child, stream, journal, checkpoint) == records, 'journal_unchanged_after_replay')
            require(pinned_evidence() == evidence and verify_runtime(child, evidence) == recipe, 'evidence_recipe_unchanged')
            require(time.time() < child.plan['hard_end_unix'], 'replay_completed_within_wall')
            receipt = dict(schema=SCHEMA, status='GENERATIONS_VERIFIED_NOT_SLEEP_RECOVERED', manifest_sha256=digest(manifest),
                original_head=HEAD, matched_generations=3, optimizer_steps=1323, optimizer_updates=0,
                historical_abandoned_updates=0, historical_update_record=None, historical_update_optimizer_step=None,
                historical_partial_backward_may_have_unrecorded_gradients=False, original_update1324_state_available=False,
                exact_update1324_replay_claim=False, original_postgeneration_rng_snapshot_available=False,
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
    require(rng(child) == replay_receipt['rng_after'] and child.optimizer_steps == 1323
            and optimizer_fingerprint(child) == replay_receipt['optimizer_state_sha256'], 'fresh_verified_replay_child')
    evidence = pinned_evidence()
    verify_runtime(child, evidence)
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000018/COMMIT.json'])
    with journal._mutex:
        records = bind(child, stream, journal, checkpoint)
        require(not (ROOT / 'checkpoints' / 'sleep_000019').exists(), 'never_repeat_saved_sleep19')
        save(RECOVERY / 'RECOMPUTE_STARTED.json', dict(manifest_sha256=digest(manifest), started_unix=time.time()))
        try:
            runtime_environment(child.torch)
            child.check('r144_recompute_sleep19')
            accounting = dict(schema=SCHEMA, semantics=SEMANTICS, recovery_root=str(RECOVERY),
                manifest_sha256=digest(manifest), original_head=HEAD, abandoned_update_record=None,
                abandoned_optimizer_step=None, historical_abandoned_updates=0, checkpoint_optimizer_steps=1323, replacement_starts_at=1324,
                historical_updates_retained=True, original_update1324_state_available=False,
                exact_update1324_replay_claim=False, replacement_attempt='r144-kernel4-sleep19-attempt1')
            journal.record('CHECKPOINT_METADATA', dict(r144_recovery=accounting))
            child.torch.cuda.synchronize()
            child.torch.cuda.reset_peak_memory_stats()
            updates = []

            def record(kind, document):
                if kind == 'TARGET_ELIGIBILITY':
                    require(document == corrected_eligibility(records[1597]['document']), 'only_pinned_target_excluded')
                elif kind == 'UPDATE':
                    require(document['optimizer_step'] == 1324+len(updates), 'replacement_contiguous_optimizer_steps')
                    require(document['source_sha256'] != OFFENDING, 'offending_target_never_trained')
                    updates.append(deepcopy(document))
                    document = dict(document, r144_attempt=accounting['replacement_attempt'],
                                    r144_original_abandoned_record=None)
                journal.record(kind, document)

            before_sleep = deepcopy(stream.checkpoint())
            receipt = child.sleep(stream.pending_rows(), stream.rows[:stream.sleep_frontier], anchors, record)
            require(stream.checkpoint() == before_sleep, 'raw_history_carry_unchanged_during_sleep')
            require(len(updates) == receipt['optimizer_steps'] == 86 and child.optimizer_steps == 1409,
                    'full_32_new_54_rehearsal_updates')
            child.torch.cuda.synchronize()
            free, total = child.torch.cuda.mem_get_info()
            memory = dict(max_allocated_bytes=child.torch.cuda.max_memory_allocated(),
                max_reserved_bytes=child.torch.cuda.max_memory_reserved(), free_bytes=free, total_bytes=total,
                observation='completed_actual_sleep19')
            memory['capacity_valid'] = (0 <= free <= total and total > 0
                and 0 <= memory['max_allocated_bytes'] <= memory['max_reserved_bytes'] <= total)
            save(RECOVERY / 'ACTUAL_SLEEP_MEMORY.json', memory)
            saved = child.checkpoint(ROOT / 'checkpoints' / 'sleep_000019')
            require(saved['optimizer_steps'] == 1409 and saved.get('experiment') == getattr(stream, 'experiment', None),
                    'replacement_checkpoint_continuity')
            receipt.update(status='COMPLETE', cycle=19, checkpoint=saved, checkpoint_sha256=saved['checkpoint_sha256'],
                new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()], r144_recovery=accounting,
                r144_memory=memory)
            stream.pending = None
            stream.commit_sleep(receipt, journal.record)
            require(journal_records(journal)[1][:1598] == records, 'original_history_prefix_preserved')
            pinned_evidence()
            save(RECOVERY / 'SLEEP_RECOMPUTED.json', dict(status='SLEEP19_SAVED', optimizer_steps=1409,
                historical_abandoned_updates=0, replacement_updates=86, memory=memory,
                exact_original_post1324_state_claim=False, finished_unix=time.time()))
            require(memory['capacity_valid'], 'invalid_GPU_memory_capacity')
            return saved
        except BaseException as error:
            save(RECOVERY / 'RECOMPUTE_FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
                original_suffix_preserved=True, no_retry=True, finished_unix=time.time()))
            raise


def adapted_supervisor():
    from gpu import orch_r125_continual_guard as guard
    require(sha(Path(guard.__file__).absolute()) == PINS['source1/gpu/orch_r125_continual_guard.py'],
            'original_guard_bytes')
    source = inspect.getsource(guard.supervise)
    before = "'gpu.orch_r125_continual_guard','native'"
    after = "'gpu.orch_r144_kernel4_recovery','native'"
    require(source.count(before) == 1, 'one_original_native_entrypoint')
    modified = source.replace(before, after)
    original_tree, modified_tree = ast.parse(source), ast.parse(modified)
    replacements = 0
    for node in ast.walk(modified_tree):
        if isinstance(node, ast.Constant) and node.value == 'gpu.orch_r144_kernel4_recovery':
            node.value = 'gpu.orch_r125_continual_guard'
            replacements += 1
    require(replacements == 1 and ast.dump(original_tree) == ast.dump(modified_tree), 'only_native_entrypoint_changed')
    namespace = dict(guard.supervise.__globals__)
    exec(compile(modified, __file__+':supervise', 'exec'), namespace)
    return namespace['supervise']


def recover_admitted_sleep(plan_path, manifest, acknowledgment):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    plan = native.validate_plan(native.read(plan_path))
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == sha(plan_path), 'original_admitted_plan_environment')
    verify_manifest(manifest, acknowledgment)
    evidence = pinned_evidence()
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000018/COMMIT.json'])
    import torch
    save(Path(plan_path).parent / 'R144_PREMODEL_ENVIRONMENT.json', runtime_environment(torch))
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        state = journal.latest_checkpoint()
        stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
        child = native.NativeChild(plan, checkpoint)
        replay = recover_rng(child, stream, journal, manifest, acknowledgment)
        anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
        save(RECOVERY / 'ANCHOR_INVENTORY.json', anchor_receipt)
        return finish_pending_sleep(child, stream, journal, anchors, manifest, acknowledgment, replay)


def cpu_provenance(plan):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    from gpu import orch_r125_continual_native as native
    from gpu.astra_pchain2_native import load_local_tokenizer
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    from organism_v6.orch_r125_plain_context import eligible_rows as original
    from types import SimpleNamespace
    evidence = pinned_evidence()
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000018/COMMIT.json'])
    probe = native.NativeChild.__new__(native.NativeChild)
    probe.plan = plan
    verify_runtime(probe, evidence)
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        latest = journal.latest_checkpoint()
        stream = ContinualStream.restore(latest['document'], expected_sha256=latest['expected_sha256'])
        stub = SimpleNamespace(plan=plan, optimizer_steps=1323, adapter_hash=lambda: checkpoint['adapter_state_sha256'])
        records = bind(stub, stream, journal, checkpoint)
        before = deepcopy(stream.checkpoint())
        require(len(stream.rows) == 57 and stream.sleep_frontier == 54, 'original57_rows54_frontier')
        tokenizer = load_local_tokenizer(plan['model_dir'])
        accepted_rows, exclusions = [], []
        for cohort, rows in [('NEW', stream.pending_rows()), ('REHEARSAL', stream.rows[:stream.sleep_frontier])]:
            accepted, excluded = eligible_rows(rows, stream.presentation, original)
            unchanged, unused = original(rows, stream.presentation)
            require(accepted == [row for row in unchanged if row['source_sha256'] != OFFENDING], 'all_other_targets_unchanged')
            exclusions.extend(dict(item, cohort=cohort) for item in excluded)
            for row in accepted:
                encoded = native.encode_own(row, tokenizer, plan['context_limit'])
                accepted_rows.append(dict(cohort=cohort, source_sha256=row['source_sha256'], input_tokens=len(encoded.input_ids)))
        offending = next(row for row in stream.rows if row['source_sha256'] == OFFENDING)
        try:
            native.encode_own(offending, tokenizer, plan['context_limit'])
        except ValueError as error:
            require(str(error) == 'no_special_token_target_injection', 'original_rejection_reason_unchanged')
        else:
            raise ValueError('native_special_token_guard_must_still_reject')
        require(exclusions == corrected_eligibility(records[1597]['document'])['excluded'], 'one_exact_exclusion')
        require(stream.checkpoint() == before, 'raw_history_carry_pending_unchanged')
        require(sum(row['cohort'] == 'NEW' for row in accepted_rows) == 2
                and sum(row['cohort'] == 'REHEARSAL' for row in accepted_rows) == 54, 'exact_86_update_schedule')
    import torch
    payload = torch.load(io.BytesIO(raw(checkpoint['optimizer_rng_path'])), map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == 1323 and len(payload['parameter_names']) == len(set(payload['parameter_names']))
            and len(payload['optimizer']['state']) == len(payload['parameter_names']), 'saved_AdamW_order_steps')
    verifier = random.Random(0)
    verifier.setstate(payload['python_rng'])
    generator = torch.Generator(device='cpu')
    generator.set_state(payload['cpu_rng'])
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].dtype == torch.uint8, 'saved_single_CUDA_RNG')
    verify_saved_files(checkpoint)
    return dict(status='PASS', original_record_count=len(records), original_head=HEAD, saved_optimizer_steps=1323,
        original_source_checkpoint_plan_AST_verified=True, raw_history_carry_pending_unchanged=True,
        native_special_token_guard_unchanged=True, accepted_rows=accepted_rows, exclusions=exclusions,
        pending_replay_requests=[digest(records[index]['document']) for index in (1585, 1588, 1592)],
        saved_parameter_names_sha256=digest(payload['parameter_names']), CPU_only=True,
        GPU_replay_not_yet_verified=True, finished_unix=time.time())


def entrypoint():
    import argparse
    from gpu import orch_r125_continual_guard as guard
    from organism_v6 import orch_r125_plain_context as presentation
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('supervise', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    config, plan = guard.validate(arguments.config)
    manifest_ref, acknowledgment = config['r144_manifest'], config['r144_acknowledgment']
    require(sha(manifest_ref['path']) == manifest_ref['sha256'], 'guard_manifest_binding')
    manifest = json.loads(raw(manifest_ref['path']))
    verify_manifest(manifest, acknowledgment)
    require(config['resume'] is True and plan['physical'] == 4 and plan['gpu_uuid'] == GPU_UUID
            and plan['root'] == str(ROOT), 'same_life_resume_only')
    if arguments.action == 'supervise':
        adapted_supervisor()(arguments.config)
    else:
        original_run, original_eligibility = guard.child.run, presentation.eligible_rows
        presentation.eligible_rows = lambda rows, context: eligible_rows(rows, context, original_eligibility)

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
