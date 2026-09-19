"""One-shot A40R7 sleep23 recovery; requires proven suffix memory repair.

Preserve the historical abandoned UPDATE1167 and all raw/history/carry.
Original privileged admission and strict actual-minor4 containment remain.
No model may load before a bound Main GPU proof and exact manifest ACK.
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


SCHEMA = 'R145_A40R7_A40R7_RECOVERY_V1'
BASE = Path('/localhome/local-rohing/orch_r136_raw_unparented_none_a40r7_20260916_attempt1')
ROOT = BASE / 'run1'
SOURCE = BASE / 'source1'
GPU_UUID = 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'
ALLOCATOR = 'expandable_segments:True'
HEAD = '1b542ccb0d93b2aadeb02b9c1ab7655c932ebd834d808b7d1134ba9bb3c6258f'
SLEEP_REQUEST = '05729e24594bf0298616294b5811fd80b100c6a13389aa6cf55bdc0665bd7dd9'
SAVED = '1650667c892cfe0446460f793ee203ff540d1ca94a288d488430ca613b073a48'
RECOVERY = ROOT / 'recoveries' / 'r145-a40r7-sleep23-20260916-attempt1'
SEMANTICS = 'preserve_historical_abandoned_update1167_recompute_sleep23_from_sleep22'
TAIL = ('SLEEP_COMPLETE', 'REQUEST', 'RESPONSE', 'COMMITTED',
        'REQUEST', 'RESPONSE', 'COMMITTED', 'SLEEP_REQUEST', 'TARGET_ELIGIBILITY', 'UPDATE')
PINS = {'control1/EXIT.json': 'ca10c8214b5b603cca90af9cdbfa8a1d80288357ebef1a20c2f30b4c71db7de3', 'control1/GUARD.json': '5058979cea71a857d661546362a229fdd043200836c8549b30788d68f05ff5b1', 'control1/LAUNCH.json': 'e74448908b1893007b2d5c42393a61ecaea885fd4deb0ff9653d3a4124cf9d8b', 'control1/NATIVE.log': '0f7183e915b8ef1cc88dd225b433507dfd35fded2ae44c1174b776696d3471e3', 'control1/PLAN.json': 'a475762f42a44c6fbcae67e6b2107993bc02753da468d67d82adf0d5ca7d2760', 'run1/checkpoints/sleep_000022/COMMIT.json': 'd9f716b7cb5a60fc9d81fb6dd1e772e49ef528fc61a79ca22d122e2ab83c0843', 'source1/gpu/orch_r125_continual_guard.py': '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3', 'source1/gpu/orch_r125_continual_native.py': '6b46401e5f8ff92d95e018b481d2303a55a3ce7c8e617aec65faa64bbc8381c7', 'source1/organism_v6/orch_r125_plain_context.py': 'b3859e4a45d53fc67c51add5dad8431985ca0adda901389e0206819a56245d92', 'source1/gpu/orch_r137_node4_containment.py': '74cca3f1061f848da049b19e98797c5925e7646002c82147399b0c1131c4dcd2'}



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
    checkpoint = json.loads(result['run1/checkpoints/sleep_000022/COMMIT.json'])
    verify_saved_files(checkpoint)
    return result


def verify_saved_files(checkpoint):
    directory = ROOT / 'checkpoints' / 'sleep_000022'
    require(checkpoint['optimizer_steps'] == 1166
            and checkpoint['adapter_path'] == str(directory / 'adapter')
            and checkpoint['optimizer_rng_path'] == str(directory / 'optimizer_rng.pt'), 'sleep22_paths_steps')
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
            'module_sha256', 'cpu_evidence', 'allocator', 'memory'}, 'explicit_manifest_fields')
    require(manifest['schema'] == SCHEMA and manifest['root'] == str(ROOT)
            and manifest['recovery_root'] == str(RECOVERY) and manifest['journal_head'] == HEAD
            and manifest['semantics'] == SEMANTICS and manifest['allocator'] == ALLOCATOR, 'exact_recovery_scope')
    require(manifest['module_sha256'] == sha(Path(__file__).absolute()), 'reviewed_recovery_module')
    verify_memory(manifest['memory'])
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
    require(sorted(allowed) == sorted(['--property=DeviceAllow=/dev/nvidia4 rw',
            '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw']),
            'only_a40r7_physical7')
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
    require(len(records) == 1375 and tuple(item['kind'] for item in records[1365:]) == TAIL
            and records[1365]['sha256'] == SAVED and records[1372]['sha256'] == SLEEP_REQUEST
            and records[1374]['sha256'] == HEAD, 'exact_a40r7_1365_1374_suffix')
    require(state['request'] is None and state['response'] is None and state['sleep_request'] == {'cycle': 23}
            and state['latest']['document'] == stream.checkpoint(), 'pending_sleep23_stream_binding')
    require(len(stream.sleep_receipts) == 22 and stream.sleep_receipts[-1]['checkpoint'] == checkpoint
            and records[1365]['document']['checkpoint'] == checkpoint
            and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']), 'last_saved_sleep22')
    require(child.optimizer_steps == 1166 and checkpoint['optimizer_steps'] == 1166
            and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'loaded_sleep22_adapter1166')
    require(child.plan['segment_tokens'] == stream.segment_tokens
            and child.plan['context_limit'] == stream.context_limit
            and child.plan['hard_end_unix'] == stream.deadline_unix, 'unchanged_stream_budget')
    presentation = dict(version=child.plan['presentation_version'], system_prompt=child.plan['system_prompt'],
                        birth_prompt=child.plan['birth_prompt'])
    require(stream.presentation == presentation, 'unchanged_presentation_during_recovery')
    rows = deepcopy(stream.pending_rows())
    require(len(rows) == 2 and stream.pending == 'sleep:'+digest([row['source_sha256'] for row in rows]),
            'two_pending_child_rows')
    for row, index in zip(rows, (1366, 1369)):
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
    eligibility = records[1373]['document']
    require(eligibility['raw_modified'] is False and eligibility['version'] == presentation['version']
            and eligibility['excluded'] == []
            and eligibility['new_row_sha256'] == [row['source_sha256'] for row in rows]
            and eligibility['rehearsal_row_sha256'] == [row['source_sha256'] for row in stream.rows[:stream.sleep_frontier]],
            'all_original_new_and_rehearsal_rows')
    require(records[1374]['document']['optimizer_step'] == 1167
            and records[1374]['document']['source_sha256'] == rows[0]['source_sha256'], 'one_historical_update1167')
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
    require(payload['optimizer_steps'] == 1166 and payload['parameter_names'] == list(child.parameters)
            and payload.get('experiment') == checkpoint.get('experiment') == getattr(child, 'experiment', None),
            'saved_optimizer_order_experiment')
    require(child.optimizer_steps == 1166 and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'restored_adapter1166')
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
    require(child.plan['physical'] == 7 and child.plan['gpu_uuid'] == GPU_UUID, 'owned_physical7')
    source = evidence['source1/gpu/orch_r125_continual_native.py'].decode()
    if getattr(child, 'r145_memory_binding', None) is not None:
        source = verified_sleep_source(source, child.r145_memory_binding)
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
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000022/COMMIT.json'])
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
            for index in range(1365, 1375):
                for suffix in ('.json', '.intent.json'):
                    name = f'{index:020d}'+suffix
                    save_bytes(RECOVERY / name, raw(journal.root / 'records' / name))
            save(RECOVERY / 'JOURNAL_EVIDENCE.json', records[1365:])
            original_stream, original_plan = deepcopy(stream.checkpoint()), deepcopy(child.plan)
            optimizer = restore(child, checkpoint)
            before = rng(child)
            for number, index in enumerate((1366, 1369)):
                request, response = records[index]['document'], records[index+1]['document']['response']
                require(time.time() < child.plan['hard_end_unix'], 'replay_deadline')
                messages = deepcopy(request['messages'])
                save(RECOVERY / f'{number:02d}_REQUEST.json', dict(request=request, rng_before=rng(child)))
                generated = child.generate(messages, max_new_tokens=request['max_new_tokens'], deadline_unix=request['deadline_unix'])
                save(RECOVERY / f'{number:02d}_RESPONSE.json', dict(response=generated, rng_after=rng(child)))
                require(digest(generated) == digest(response), 'exact_generation_match:' + str(number))
                require(messages == request['messages'] and stream.checkpoint() == original_stream
                        and child.plan == original_plan, 'no_replay_history_plan_mutation')
                require(child.optimizer_steps == 1166 and child.adapter_hash() == checkpoint['adapter_state_sha256']
                        and optimizer_fingerprint(child) == optimizer, 'no_replay_learning_mutation')
                child.engine.verify_base()
            require(bind(child, stream, journal, checkpoint) == records, 'journal_unchanged_after_replay')
            require(pinned_evidence() == evidence and verify_runtime(child, evidence) == recipe, 'evidence_recipe_unchanged')
            require(time.time() < child.plan['hard_end_unix'], 'replay_completed_within_wall')
            receipt = dict(schema=SCHEMA, status='GENERATIONS_VERIFIED_NOT_SLEEP_RECOVERED', manifest_sha256=digest(manifest),
                original_head=HEAD, matched_generations=2, optimizer_steps=1166, optimizer_updates=0,
                historical_abandoned_updates=1, historical_update_record=1374, historical_update_optimizer_step=1167,
                historical_partial_backward_may_have_unrecorded_gradients=True, original_update1167_state_available=False,
                exact_update1167_replay_claim=False, original_postgeneration_rng_snapshot_available=False,
                verification='exact_committed_outputs_from_saved_RNG_not_comparison_to_missing_final_RNG',
                rng_before=before, rng_after=rng(child), optimizer_state_sha256=optimizer,
                pending_unchanged=True, stream_sha256=original_stream['sha256'], no_retry=True, finished_unix=time.time())
            save(RECOVERY / 'GENERATIONS_VERIFIED.json', receipt)
            return receipt
        except BaseException as error:
            save(RECOVERY / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
                child_must_be_discarded=True, no_retry=True, finished_unix=time.time()))
            raise


class ReplacementRecorder:
    def __init__(self, journal, eligibility, binding, attempt):
        self.journal = journal
        self.eligibility = deepcopy(eligibility)
        self.binding = binding
        self.attempt = attempt
        self.sources = eligibility['new_row_sha256'] * 16 + eligibility['rehearsal_row_sha256']
        require(len(self.sources) == 76, 'exact_76_original_presentations')
        self.updates = []
        self.eligibility_seen = False
        self.metadata_seen = False

    def __call__(self, kind, document):
        if kind == 'TARGET_ELIGIBILITY':
            require(not self.eligibility_seen and not self.metadata_seen and not self.updates
                    and document == self.eligibility, 'identical_once_training_eligibility')
            self.eligibility_seen = True
        elif kind == 'CHECKPOINT_METADATA':
            from gpu.orch_r145_suffix_boundary import POLICY
            expected = dict(runtime_memory_policy=POLICY, runtime_sha256=self.binding['runtime']['sha256'],
                            GPU_validation_sha256=self.binding['proof']['sha256'])
            require(self.eligibility_seen and not self.metadata_seen and not self.updates
                    and document == expected, 'one_exact_proven_runtime_metadata_only')
            self.metadata_seen = True
        elif kind == 'UPDATE':
            require(self.eligibility_seen and self.metadata_seen and len(self.updates) < len(self.sources),
                    'eligibility_and_proof_metadata_before_updates')
            require(document['optimizer_step'] == 1167+len(self.updates)
                    and document['source_sha256'] == self.sources[len(self.updates)],
                    'replacement_exact_contiguous_original_schedule')
            self.updates.append(deepcopy(document))
            document = dict(document, r145_a40r7_attempt=self.attempt, r145_a40r7_original_abandoned_record=1374)
        else:
            raise ValueError('unexpected_pending_sleep_event:' + kind)
        self.journal.record(kind, document)

    def complete(self):
        require(self.eligibility_seen and self.metadata_seen and len(self.updates) == 76,
                'complete_original_76_updates_and_one_runtime_metadata')


def finish_pending_sleep(child, stream, journal, anchors, manifest, acknowledgment, replay_receipt):
    verify_manifest(manifest, acknowledgment)
    require(json.loads(raw(RECOVERY / 'GENERATIONS_VERIFIED.json')) == replay_receipt
            and replay_receipt['manifest_sha256'] == digest(manifest), 'bound_generation_receipt')
    require(rng(child) == replay_receipt['rng_after'] and child.optimizer_steps == 1166
            and optimizer_fingerprint(child) == replay_receipt['optimizer_state_sha256'], 'fresh_verified_replay_child')
    evidence = pinned_evidence()
    verify_runtime(child, evidence)
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000022/COMMIT.json'])
    with journal._mutex:
        records = bind(child, stream, journal, checkpoint)
        require(not (ROOT / 'checkpoints' / 'sleep_000023').exists(), 'never_repeat_saved_sleep23')
        save(RECOVERY / 'RECOMPUTE_STARTED.json', dict(manifest_sha256=digest(manifest), started_unix=time.time()))
        try:
            runtime_environment(child.torch)
            child.check('r145_a40r7_recompute_sleep23')
            accounting = dict(schema=SCHEMA, semantics=SEMANTICS, recovery_root=str(RECOVERY),
                manifest_sha256=digest(manifest), original_head=HEAD, abandoned_update_record=1374,
                abandoned_optimizer_step=1167, checkpoint_optimizer_steps=1166, replacement_starts_at=1167,
                historical_updates_retained=True, original_update1167_state_available=False,
                exact_update1167_replay_claim=False, replacement_attempt='r145_a40r7-a40r7-sleep23-attempt1')
            journal.record('CHECKPOINT_METADATA', dict(r145_a40r7_recovery=accounting))
            child.torch.cuda.synchronize()
            child.torch.cuda.reset_peak_memory_stats()
            record = ReplacementRecorder(journal, records[1373]['document'], manifest['memory'],
                                         accounting['replacement_attempt'])
            before_sleep = deepcopy(stream.checkpoint())
            receipt = child.sleep(stream.pending_rows(), stream.rows[:stream.sleep_frontier], anchors, record)
            record.complete()
            require(stream.checkpoint() == before_sleep, 'raw_history_carry_unchanged_during_sleep')
            require(len(record.updates) == receipt['optimizer_steps'] == 76 and child.optimizer_steps == 1242,
                    'full_32_new_44_rehearsal_updates')
            child.torch.cuda.synchronize()
            free, total = child.torch.cuda.mem_get_info()
            memory = dict(max_allocated_bytes=child.torch.cuda.max_memory_allocated(),
                max_reserved_bytes=child.torch.cuda.max_memory_reserved(), free_bytes=free, total_bytes=total,
                observation='completed_actual_sleep23')
            memory['capacity_valid'] = (0 <= free <= total and total > 0
                and 0 <= memory['max_allocated_bytes'] <= memory['max_reserved_bytes'] <= total)
            save(RECOVERY / 'ACTUAL_SLEEP_MEMORY.json', memory)
            saved = child.checkpoint(ROOT / 'checkpoints' / 'sleep_000023')
            require(saved['optimizer_steps'] == 1242 and saved.get('experiment') == stream.experiment,
                    'replacement_checkpoint_continuity')
            receipt.update(status='COMPLETE', cycle=23, checkpoint=saved, checkpoint_sha256=saved['checkpoint_sha256'],
                new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()], r145_a40r7_recovery=accounting,
                r145_a40r7_memory=memory)
            stream.pending = None
            stream.commit_sleep(receipt, journal.record)
            require(journal_records(journal)[1][:1375] == records, 'original_history_prefix_preserved')
            pinned_evidence()
            save(RECOVERY / 'SLEEP_RECOMPUTED.json', dict(status='SLEEP23_SAVED', optimizer_steps=1242,
                historical_abandoned_updates=1, replacement_updates=76, memory=memory,
                exact_original_post1167_state_claim=False, finished_unix=time.time()))
            require(memory['capacity_valid'], 'invalid_GPU_memory_capacity')
            return saved
        except BaseException as error:
            save(RECOVERY / 'RECOMPUTE_FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
                original_suffix_preserved=True, no_retry=True, finished_unix=time.time()))
            raise


def adapted_node_function(action):
    from gpu import orch_r137_node4_containment as programmes
    require(action in ('contained_supervise', 'contained_native'), 'original_contained_actions_only')
    require(sha(Path(programmes.__file__).absolute()) == PINS['source1/gpu/orch_r137_node4_containment.py'],
            'original_node_launcher_bytes')
    function = getattr(programmes, action)
    source = inspect.getsource(function)
    before = 'gpu.orch_r137_node4_containment' if action == 'contained_supervise' else 'gpu.orch_r125_continual_guard'
    require(source.count(repr(before)) == 1, 'one_exact_entrypoint_relocation')
    modified = source.replace(repr(before), repr('gpu.orch_r145_a40r7_recovery'))
    tree = ast.parse(modified)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == 'gpu.orch_r145_a40r7_recovery':
            node.value = before
    require(ast.dump(tree) == ast.dump(ast.parse(source)), 'only_entrypoint_literal_changed')
    namespace = dict(function.__globals__)
    if action == 'contained_supervise':
        def contained_command(physical, minor, uid, gid, unit, source_root, command, lifetime):
            require(physical == 7 and minor == 4 and uid == gid == 2524, 'exact_original_identity_minor')
            verify_topology()
            return allocator_command(programmes.device_containment_command(
                physical, minor, uid, gid, unit, source_root, command, lifetime))
        namespace['device_containment_command'] = contained_command
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
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000022/COMMIT.json'])
    import torch
    environment = runtime_environment(torch)
    save(Path(plan_path).parent / 'R145_A40R7_PREMODEL_ENVIRONMENT.json', environment)
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        state = journal.latest_checkpoint()
        stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
        verify_experiment_resume(plan, stream.experiment)
        require(checkpoint.get('experiment') == stream.experiment, 'original_stream_model_experiment')
        child = native.NativeChild(plan, checkpoint)
        child.r145_memory_binding = manifest['memory']
        replay = recover_rng(child, stream, journal, manifest, acknowledgment)
        anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
        save(RECOVERY / 'ANCHOR_INVENTORY.json', anchor_receipt)
        saved = finish_pending_sleep(child, stream, journal, anchors, manifest, acknowledgment, replay)
        return saved



MEMORY_HELPERS = {
    'orch_r145_suffix_boundary.py': '632c519fd4c5a840d13b1e9503e61f512340ee9361ef95dcd43cbaf704ee0ce5',
    'orch_r145_suffix_loss.py': 'd5e69655fd30f3317d114bd4aab2025024fdfb1521664b536d54ad61069bf026',
    'orch_r145_node3_capacity_recovery.py': '3fce935672ffd4d19119fde7e503f5956262caa584c860fe45afe14efea0daf3',
    'orch_r144_target_patch.py': '3036dfd7b749f76d328f05330ef3b7afd664a0da599e80fc57d3e5d3e9876c1b',
}


def verify_topology():
    import stat
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict((key.strip(), value.strip()) for key, value in
                      (line.split(':', 1) for line in path.read_text().splitlines() if ':' in line))
        if fields.get('GPU UUID') == GPU_UUID:
            matches.append(int(fields['Device Minor']))
    require(matches == [4], 'actual_UUID_minor4')
    device = Path('/dev/nvidia4').lstat()
    require(stat.S_ISCHR(device.st_mode) and os.major(device.st_rdev) == 195
            and os.minor(device.st_rdev) == 4, 'actual_target_character_device')


def verify_memory(binding):
    from gpu import orch_r145_suffix_boundary as boundary
    require(set(binding) == {'proof', 'runtime', 'coverage'}, 'exact_memory_binding_fields')
    directory = Path(__file__).absolute().parent
    for name, expected in MEMORY_HELPERS.items():
        require(sha(directory / name) == expected, 'unchanged_Main_memory_helper:' + name)
    for reference in binding.values():
        require(set(reference) == {'path', 'sha256'} and sha(reference['path']) == reference['sha256'],
                'bound_memory_proof_or_runtime')
    runtime = binding['runtime']
    require(runtime['path'] == str(directory / boundary.RUNTIME_FILE), 'actual_source_runtime_file')
    proof = json.loads(raw(binding['proof']['path']))
    boundary.validate_gpu_proof(proof, runtime['sha256'])
    coverage = json.loads(raw(binding['coverage']['path']))
    require(coverage['status'] == 'PASS' and coverage['journal_head'] == HEAD
            and coverage['checkpoint_sha256'] == PINS['run1/checkpoints/sleep_000022/COMMIT.json']
            and coverage['proof_sha256'] == binding['proof']['sha256']
            and coverage['runtime_sha256'] == runtime['sha256']
            and coverage['all_46_rows_encoded'] is True and coverage['no_target_or_context_change'] is True,
            'actual_A40R7_CPU_coverage_binding')
    memory = proof['longest_child_prospective_only']['memory']
    require(memory['full_input_tokens'] >= coverage['max_input_tokens']
            and memory['logits_tokens'] >= coverage['max_logits_tokens']
            and memory['total_bytes'] <= coverage['device_total_bytes'], 'proven_shape_capacity_covers_A40R7')
    return proof


def verified_sleep_source(source, binding):
    from gpu import orch_r145_suffix_boundary as boundary
    verify_memory(binding)
    return boundary.patch_source(source, PINS['source1/gpu/orch_r125_continual_native.py'],
        binding['runtime']['sha256'], binding['proof']['path'], binding['proof']['sha256'])


def cpu_provenance(plan):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    from types import SimpleNamespace
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, verify_experiment_resume
    evidence = pinned_evidence()
    checkpoint = json.loads(evidence['run1/checkpoints/sleep_000022/COMMIT.json'])
    native.validate_plan(plan)
    verify_topology()
    verify_original_absent()
    probe = native.NativeChild.__new__(native.NativeChild)
    probe.plan = plan
    verify_runtime(probe, evidence)
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        latest = journal.latest_checkpoint()
        stream = ContinualStream.restore(latest['document'], expected_sha256=latest['expected_sha256'])
        verify_experiment_resume(plan, stream.experiment)
        child = SimpleNamespace(plan=plan, optimizer_steps=1166,
            adapter_hash=lambda: checkpoint['adapter_state_sha256'])
        records = bind(child, stream, journal, checkpoint)
        from gpu.astra_pchain2_native import load_local_tokenizer
        tokenizer = load_local_tokenizer(plan['model_dir'])
        encoded = [native.encode_own(row, tokenizer, plan['context_limit']) for row in stream.rows]
        require(len(encoded) == 46 and stream.sleep_frontier == 44, 'all46_rows_original_frontier44')
        from gpu.orch_r145_suffix_loss import loss_window
        contracts = [loss_window(sample) for sample in encoded]
        import torch
        payload = torch.load(io.BytesIO(raw(checkpoint['optimizer_rng_path'])), map_location='cpu', weights_only=False)
        require(payload['optimizer_steps'] == 1166 and len(payload['parameter_names']) == len(set(payload['parameter_names']))
                and len(payload['optimizer']['state']) == len(payload['parameter_names']), 'saved_AdamW_order_and_state')
        random.Random(0).setstate(payload['python_rng'])
        torch.Generator(device='cpu').set_state(payload['cpu_rng'])
        require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].dtype == torch.uint8, 'saved_single_CUDA_RNG')
        require(journal_records(journal)[1] == records, 'CPU_provenance_does_not_mutate_journal')
        return dict(status='PASS', record_count=1375, journal_head=HEAD, saved_steps=1166,
            replacement_updates=76, expected_total_steps=1242, historical_abandoned_updates=1,
            all_46_rows_encoded=True, no_target_or_context_change=True, original_source_closure=True,
            actual_minor=4, CPU_only=True, max_input_tokens=max(len(sample.input_ids) for sample in encoded),
            max_logits_tokens=max(item['logits_to_keep'] for item in contracts),
            held_contents_read=False, finished_unix=time.time())


def verify_original_absent():
    launch = json.loads(raw(BASE / 'control1/LAUNCH.json'))
    timeout_stat = Path('/proc', str(launch['pid']), 'stat')
    if timeout_stat.exists():
        require(timeout_stat.read_text().rsplit(')', 1)[1].split()[19] != launch['parent_start_ticks'],
                'original_timeout_identity_still_present')
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            arguments = (directory / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        require(str(BASE / 'control1/GUARD.json').encode() not in arguments,
                'original_config_actor_still_present')


def entrypoint():
    import argparse
    from gpu import orch_r125_continual_guard as guard
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('contained-supervise', 'contained-native', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    config, plan = guard.validate(arguments.config)
    manifest_ref, acknowledgment = config['r145_a40r7_manifest'], config['r145_a40r7_acknowledgment']
    require(sha(manifest_ref['path']) == manifest_ref['sha256'], 'guard_manifest_binding')
    manifest = json.loads(raw(manifest_ref['path']))
    verify_manifest(manifest, acknowledgment)
    require(config['resume'] is True and plan['physical'] == 7 and plan['root'] == str(ROOT), 'same_life_resume_only')
    if arguments.action == 'contained-supervise':
        adapted_node_function('contained_supervise')(arguments.config)
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
