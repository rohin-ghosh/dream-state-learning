"""Bounded saved31/1922 to pending32 recovery; Main stages and admits."""

import ast
from collections import Counter
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

from gpu import orch_r145_a40r7_recovery as previous
from organism_v6.orch_r125_continual_stream import digest, require


SCHEMA = 'R152_A40R7_RECOVERY_V1'
BASE = previous.BASE
ROOT = BASE / 'run1'
ORIGINAL_SOURCE = BASE / 'source_r145_a40r7_20260916t1630z'
ORIGINAL_PLAN = BASE / 'control_r145_a40r7_20260916t1630z' / 'PLAN.json'
ORIGINAL_CONTROL = BASE / 'control_r145_a40r7_20260916t1630z_readmit1'
ORIGINAL_GUARD = ORIGINAL_CONTROL / 'GUARD.json'
ORIGINAL_GUARD_SHA256 = '7cc737f65d5e10b62eb11dcd106cfa13d0895025e2d13460840d588303b3f180'
ORIGINAL_NATIVE_SHA256 = '3eb3d1ae2e302f4d77c75ede5f7ca667fe2eb18d71878f2232572686355b3082'
PATCHED_NATIVE_SHA256 = 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'
RECOVERY = ROOT / 'recoveries' / 'r152-a40r7-sleep32-20260916-attempt1'
GPU_UUID = previous.GPU_UUID
ALLOCATOR = previous.ALLOCATOR
SAVED_CYCLE = 31
SAVED_STEPS = 1922
CYCLE = 32
MODULE = 'gpu.orch_r152_a40r7_recovery'
NATIVE = 'gpu/orch_r125_continual_native.py'
NODE = 'gpu/orch_r137_node4_containment.py'
raw = previous.raw
sha = previous.sha
save = previous.save
save_bytes = previous.save_bytes
rng = previous.rng
optimizer_fingerprint = previous.optimizer_fingerprint
allocator_command = previous.allocator_command
runtime_environment = previous.runtime_environment
journal_records = previous.journal_records


def reference(path):
    return dict(path=str(Path(path).absolute()), sha256=sha(path))


def read_reference(value):
    require(set(value) == {'path', 'sha256'}, 'exact_file_reference')
    content = raw(value['path'])
    require(hashlib.sha256(content).hexdigest() == value['sha256'], 'bound_evidence_bytes')
    return json.loads(content)


def source_closure(source):
    source = Path(source)
    return {str(path.relative_to(source)): sha(path) for path in sorted(source.rglob('*.py'))}


def same_life_plan(plan, original):
    require(plan['root'] == original['root'] == str(ROOT)
            and plan['physical'] == original['physical'] == 7
            and plan['gpu_uuid'] == original['gpu_uuid'] == GPU_UUID, 'same_a40r7_life')
    source = Path(plan['source_root'])
    require(source.parent == BASE and source != ORIGINAL_SOURCE
            and source.name.startswith('source_r152_'), 'new_R152_source_copy_only')
    normalized = deepcopy(plan)
    normalized['source_root'] = original['source_root']
    require(original['source_root'] == str(ORIGINAL_SOURCE), 'exact_original_source')
    if 'startup_context' in original:
        relative = Path(original['startup_context']['path']).relative_to(ORIGINAL_SOURCE)
        require(plan['startup_context']['path'] == str(source / relative)
                and raw(source / relative) == raw(ORIGINAL_SOURCE / relative), 'samebytesstartup_relocation')
        normalized['startup_context']['path'] = original['startup_context']['path']
    require(normalized == original, 'only_source_and_samebytesstartup_relocation')


def verify_saved_files(checkpoint, cycle=SAVED_CYCLE, steps=SAVED_STEPS):
    directory = ROOT / 'checkpoints' / f'sleep_{cycle:06d}'
    require(checkpoint['optimizer_steps'] == steps
            and checkpoint['adapter_path'] == str(directory / 'adapter')
            and checkpoint['optimizer_rng_path'] == str(directory / 'optimizer_rng.pt'), 'saved_checkpoint_paths_steps')
    files = checkpoint['adapter_files']
    require(files and set(path.name for path in (directory / 'adapter').iterdir()) == set(files),
            'exact_adapter_inventory')
    for name, expected in files.items():
        require(Path(name).name == name and name not in ('.', '..'), 'adapter_basename')
        require(sha(directory / 'adapter' / name) == expected, 'saved_adapter_file_hash')
    hashes = checkpoint['checkpoint_sha256']
    require(set(hashes) == {'adapter', 'optimizer', 'rng'} and digest(files) == hashes['adapter']
            and sha(checkpoint['optimizer_rng_path']) == hashes['optimizer'] == hashes['rng'],
            'saved_optimizer_rng_file_hashes')


def sleep_metadata(source):
    child = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
                 and node.name == 'NativeChild')
    sleep = next(node for node in child.body if isinstance(node, ast.FunctionDef) and node.name == 'sleep')
    calls = [node for node in ast.walk(sleep) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'record'
             and node.args and isinstance(node.args[0], ast.Constant)
             and node.args[0].value == 'CHECKPOINT_METADATA']
    require(len(calls) == 1 and len(calls[0].args) == 2, 'one_original_R145_metadata_event')
    document = calls[0].args[1]
    require(isinstance(document, ast.Call) and isinstance(document.func, ast.Name)
            and document.func.id == 'dict' and not document.args, 'literal_R145_metadata')
    result = {keyword.arg: ast.literal_eval(keyword.value) for keyword in document.keywords}
    require(set(result) == {'runtime_memory_policy', 'runtime_sha256', 'GPU_validation_sha256'},
            'unchanged_R145_suffix_metadata')
    return result


def pinned_evidence(plan, original_guard_path):
    from gpu.orch_r144_target_patch import patch_source
    require(Path(original_guard_path) == ORIGINAL_GUARD
            and sha(original_guard_path) == ORIGINAL_GUARD_SHA256, 'exact_original_failed_guard')
    guard = json.loads(raw(original_guard_path))
    require(guard['plan_path'] == str(ORIGINAL_PLAN)
            and guard['plan_sha256'] == sha(ORIGINAL_PLAN), 'original_guard_plan_binding')
    original = json.loads(raw(ORIGINAL_PLAN))
    same_life_plan(plan, original)
    original_pins = source_closure(ORIGINAL_SOURCE)
    require(original_pins == guard['source_pins'], 'entire_original_source_closure')
    require(original_pins[NATIVE] == ORIGINAL_NATIVE_SHA256, 'original_fatal_native_bytes')
    source = Path(plan['source_root'])
    staged_pins = source_closure(source)
    old_native = raw(ORIGINAL_SOURCE / NATIVE).decode()
    require(raw(source / NATIVE).decode() == patch_source(old_native)
            and staged_pins[NATIVE] == PATCHED_NATIVE_SHA256, 'exact_R144_patch_preserves_R145_loss')
    for name, expected in original_pins.items():
        if name != NATIVE:
            require(staged_pins.get(name) == expected, 'unchanged_original_source:' + name)
    require(staged_pins.get('gpu/orch_r152_a40r7_recovery.py') == sha(Path(__file__).absolute()),
            'actual_staged_runtime_bytes')
    runtime_name = 'gpu/orch_r145_node3_capacity_runtime.json'
    require(raw(source / runtime_name) == raw(ORIGINAL_SOURCE / runtime_name), 'original_R145_runtime_bytes')
    files = dict(guard=reference(original_guard_path), plan=reference(ORIGINAL_PLAN),
                 exit=reference(ORIGINAL_CONTROL / 'EXIT.json'), log=reference(ORIGINAL_CONTROL / 'NATIVE.log'),
                 checkpoint=reference(ROOT / 'checkpoints' / f'sleep_{SAVED_CYCLE:06d}' / 'COMMIT.json'),
                 original_runtime=reference(ORIGINAL_SOURCE / runtime_name),
                 staged_runtime=reference(source / runtime_name))
    metadata = sleep_metadata(old_native)
    require(metadata['runtime_sha256'] == files['original_runtime']['sha256'], 'original_suffix_runtime_binding')
    exited = read_reference(files['exit'])
    log = raw(files['log']['path']).decode()
    require(type(exited['exit_code']) is int and exited['exit_code'] == 1, 'original_failed_exit')
    require('ValueError: no_special_token_target_injection' in log
            and 'encode_own' in log and 'Traceback (most recent call last):' in log,
            'original_fatal_target_encoder')
    checkpoint = read_reference(files['checkpoint'])
    verify_saved_files(checkpoint)
    return dict(files=files, original_source_pins=original_pins, source_pins=staged_pins,
                checkpoint=checkpoint, sleep_metadata=metadata)


def journal_binding(plan, stream, journal, checkpoint):
    state, records = journal_records(journal)
    require(journal.root == ROOT / 'stream' and plan['root'] == str(ROOT), 'same_stream_root')
    saved_indices = [index for index, item in enumerate(records)
                     if item['kind'] == 'SLEEP_COMPLETE' and item['document'].get('cycle') == SAVED_CYCLE]
    require(len(saved_indices) == 1, 'one_saved_sleep31')
    saved_index = saved_indices[0]
    tail = records[saved_index + 1:]
    require(not any(item['kind'] == 'UPDATE' for item in tail), 'no_unsaved_UPDATE_permitted')
    require(state['request'] is None and state['response'] is None
            and state['sleep_request'] == {'cycle': CYCLE}
            and state['latest']['document'] == stream.checkpoint(), 'exact_pending_sleep32')
    require(len(stream.sleep_receipts) == SAVED_CYCLE
            and stream.sleep_receipts[-1]['checkpoint'] == checkpoint
            and records[saved_index]['document']['checkpoint'] == checkpoint
            and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']), 'saved31_stream_model_binding')
    require(plan['segment_tokens'] == stream.segment_tokens and plan['context_limit'] == stream.context_limit
            and plan['hard_end_unix'] == stream.deadline_unix, 'unchanged_stream_budget')
    presentation = dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                        birth_prompt=plan['birth_prompt']) if plan.get('presentation_version') else None
    require(stream.presentation == presentation and checkpoint.get('experiment') == stream.experiment,
            'unchanged_presentation_experiment')
    rows = stream.pending_rows()
    require(rows and stream.pending == 'sleep:' + digest([row['source_sha256'] for row in rows]),
            'actual_pending_child_rows')
    pair_indices = []
    position = saved_index + 1
    for row in rows:
        require([item['kind'] for item in records[position:position + 3]] == ['REQUEST', 'RESPONSE', 'COMMITTED'],
                'only_actual_committed_generation_triples')
        request = {key: value for key, value in records[position]['document'].items() if key != 'resume_state'}
        response = records[position + 1]['document']
        committed = records[position + 2]['document']
        output = response['response']
        require(request['split'] == row['split'] == 'TRAIN' and row['actor'] == 'child'
                and row['prefix_loss'] is False and row['target_loss'] is True, 'TRAIN_child_only')
        require(request['segment'] == row['segment'] == committed['segment']
                and digest(request) == response['request_sha256']
                and digest(response) == row['source_sha256'] == committed['source_sha256']
                and response['raw_saved_before_validation'] is True, 'actual_committed_raw_chain')
        require(request['messages'] == row['prefix'] and request['retry_allowed'] is False
                and request['max_new_tokens'] == plan['segment_tokens']
                and request['deadline_unix'] == plan['hard_end_unix']
                and request['model_state_sha256'] == row['model_state_sha256'] == stream.model_state_sha256,
                'original_generation_request')
        require(output['raw'] == row['target'] and output['token_ids'] == row['token_ids']
                and type(output['terminal']) is bool and output['terminal'] is row['terminal']
                and type(output['truncated']) is bool and output['truncated'] is row['truncated']
                and output['decoder'] == plan['decoder']
                and output['adapter_state_sha256'] == checkpoint['adapter_state_sha256']
                and output['base_sha256'] == checkpoint['base_sha256']
                and output['prompt_tokens'] == request['prompt_tokens'], 'original_generation_response')
        pair_indices.append(position)
        position += 3
    remaining = records[position:]
    expected_kinds = ['SLEEP_REQUEST', 'TARGET_ELIGIBILITY'] if presentation else ['SLEEP_REQUEST']
    require([item['kind'] for item in remaining] == expected_kinds, 'exact_preencoding_failure_suffix')
    if presentation:
        require(remaining[1]['document'] == dict(version=presentation['version'], excluded=[], raw_modified=False,
                new_row_sha256=[row['source_sha256'] for row in rows],
                rehearsal_row_sha256=[row['source_sha256'] for row in stream.rows[:stream.sleep_frontier]]),
                'original_allhistory_eligibility')
    return dict(journal_head=state['previous'], record_count=len(records), saved_index=saved_index,
                saved_sha256=records[saved_index]['sha256'], pair_indices=pair_indices,
                sleep_request_index=position, sleep_request_sha256=records[position]['sha256'],
                stream_sha256=stream.checkpoint()['sha256'], saved_steps=SAVED_STEPS,
                pending_cycle=CYCLE, unsaved_updates=0), records


def target_contract(plan, stream, tokenizer):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r144_sleep_targets import POLICY, REJECTION, encode_sleep_targets
    new_rows, old_rows = deepcopy(stream.pending_rows()), deepcopy(stream.rows[:stream.sleep_frontier])
    if plan.get('presentation_version'):
        from organism_v6.orch_r125_plain_context import eligible_rows
        presentation = dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                            birth_prompt=plan['birth_prompt'])
        new_rows, excluded_new = eligible_rows(new_rows, presentation)
        old_rows, excluded_old = eligible_rows(old_rows, presentation)
        require(not excluded_new and not excluded_old, 'only_actual_specialtoken_exclusions')
    new_rows, old_rows, encoded, excluded = encode_sleep_targets(
        new_rows, old_rows, tokenizer, plan['context_limit'], native.encode_own)
    require(excluded and all(row['reason'] == REJECTION for row in excluded), 'actual_specialtoken_rows_required')
    schedule = native.presentation_schedule(new_rows, old_rows) if new_rows else [('REHEARSAL', row) for row in old_rows]
    eligibility = dict(version=plan.get('presentation_version'), runtime_policy=POLICY, excluded=excluded,
                       new_row_sha256=[row['source_sha256'] for row in new_rows],
                       rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False)
    return dict(eligibility=eligibility,
                schedule=[dict(cohort=cohort, source_sha256=row['source_sha256']) for cohort, row in schedule],
                expected_updates=len(schedule), expected_total_steps=SAVED_STEPS + len(schedule),
                all_rows_checked=len(stream.rows), max_input_tokens=max(
                    (len(sample.input_ids) for sample in encoded.values()), default=0))


def verify_loaded_native(plan):
    from gpu import orch_r125_continual_native as native
    require(Path(native.__file__).absolute() == Path(plan['source_root']) / NATIVE,
            'actual_copied_native_import')
    source = raw(Path(plan['source_root']) / NATIVE).decode()
    child = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
                 and node.name == 'NativeChild')
    for name in ('generate', 'sleep', 'checkpoint', 'verify_checkpoint'):
        original = next(node for node in child.body if isinstance(node, ast.FunctionDef) and node.name == name)
        current = ast.parse(textwrap.dedent(inspect.getsource(getattr(native.NativeChild, name)))).body[0]
        require(ast.dump(original) == ast.dump(current), 'unchanged_loaded_native:' + name)


def checkpoint_payload(checkpoint, torch):
    verify_saved_files(checkpoint)
    payload = torch.load(io.BytesIO(raw(checkpoint['optimizer_rng_path'])), map_location='cpu', weights_only=False)
    names = payload['parameter_names']
    require(payload['optimizer_steps'] == SAVED_STEPS and names and len(names) == len(set(names))
            and len(payload['optimizer']['state']) == len(names)
            and payload.get('experiment') == checkpoint.get('experiment'), 'saved_AdamW_order_steps_experiment')
    random.Random(0).setstate(payload['python_rng'])
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].dtype == torch.uint8
            and payload['cuda_rng'][0].device.type == 'cpu', 'saved_single_CUDA_rng_payload')
    return payload


def cpu_provenance(plan, original_guard_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    from gpu import orch_r125_continual_native as native
    from gpu.astra_pchain2_native import load_local_tokenizer
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, verify_experiment_resume
    import torch
    require(not torch.cuda.is_initialized(), 'no_CPU_gate_CUDA_context')
    native.validate_plan(plan)
    evidence = pinned_evidence(plan, original_guard_path)
    verify_loaded_native(plan)
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        state = journal.latest_checkpoint()
        stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
        verify_experiment_resume(plan, stream.experiment)
        binding, records = journal_binding(plan, stream, journal, evidence['checkpoint'])
        targets = target_contract(plan, stream, load_local_tokenizer(plan['model_dir']))
        checkpoint_payload(evidence['checkpoint'], torch)
        require(journal_records(journal)[1] == records, 'CPU_journal_unchanged')
    require(not torch.cuda.is_initialized(), 'CPU_gate_did_not_initialize_CUDA')
    return dict(schema=SCHEMA, status='PASS', CPU_only=True, held_contents_read=False,
                module_sha256=sha(Path(__file__).absolute()), plan=deepcopy(plan), evidence=evidence,
                journal=binding, targets=targets, original_postgeneration_rng_snapshot_available=False)


def make_manifest(plan, provenance, cpu_gate_ref):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_manifest_build')
    require(gate_provenance(cpu_gate_ref) == provenance, 'CPU_gate_is_exact_provenance')
    require(provenance.get('schema') == SCHEMA and provenance.get('status') == 'PASS'
            and provenance.get('CPU_only') is True and provenance.get('held_contents_read') is False
            and provenance['plan'] == plan and provenance['module_sha256'] == sha(Path(__file__).absolute()),
            'same_module_plan_CPU_gate')
    require(provenance['evidence'] == pinned_evidence(plan, ORIGINAL_GUARD), 'CPU_evidence_still_current')
    return dict(schema=SCHEMA, root=str(ROOT), recovery_root=str(RECOVERY), allocator=ALLOCATOR,
                module_sha256=provenance['module_sha256'], cpu_evidence=deepcopy(cpu_gate_ref),
                provenance=deepcopy(provenance))


def build_manifest(plan, original_guard_path, cpu_evidence_ref):
    require(Path(original_guard_path) == ORIGINAL_GUARD, 'exact_original_guard_path')
    return make_manifest(plan, gate_provenance(cpu_evidence_ref), cpu_evidence_ref)


def gate_provenance(reference):
    gate = read_reference(reference)
    require(set(gate) == {'status', 'exit_code', 'tests', 'provenance', 'source_pins',
                          'module_sha256', 'finished_unix'}, 'exact_Main_CPU_gate_fields')
    require(gate['status'] == 'PASS' and type(gate['exit_code']) is int and gate['exit_code'] == 0,
            'real_CPU_tests_passed')
    require(set(gate['tests']) == {'path', 'sha256'}
            and sha(gate['tests']['path']) == gate['tests']['sha256'], 'bound_real_CPU_test_log')
    provenance = read_reference(gate['provenance'])
    require(gate['source_pins'] == provenance['evidence']['source_pins']
            and gate['module_sha256'] == provenance['module_sha256'], 'same_tested_provenance_source_closure')
    return provenance


def verify_manifest(manifest, ack):
    require(set(manifest) == {'schema', 'root', 'recovery_root', 'allocator', 'module_sha256',
                              'cpu_evidence', 'provenance'}, 'exact_manifest_fields')
    require(manifest['schema'] == SCHEMA and manifest['root'] == str(ROOT)
            and manifest['recovery_root'] == str(RECOVERY) and manifest['allocator'] == ALLOCATOR
            and manifest['module_sha256'] == sha(Path(__file__).absolute()), 'exact_recovery_scope_module')
    approved = read_reference(ack)
    require(approved.get('author') == 'Main' and approved.get('approved') is True
            and approved.get('manifest_sha256') == digest(manifest), 'exact_Main_ACK_required')
    provenance = gate_provenance(manifest['cpu_evidence'])
    require(provenance == manifest['provenance'] and provenance.get('schema') == SCHEMA
            and provenance.get('status') == 'PASS' and provenance.get('CPU_only') is True
            and provenance.get('held_contents_read') is False
            and provenance['module_sha256'] == manifest['module_sha256'], 'bound_CPU_provenance')
    require(provenance['evidence'] == pinned_evidence(provenance['plan'], ORIGINAL_GUARD),
            'all_original_staged_checkpoint_evidence_unchanged')
    return provenance


def restore(child, checkpoint):
    child.verify_checkpoint(checkpoint)
    require(isinstance(child.optimizer, child.torch.optim.AdamW), 'actual_AdamW')
    payload = checkpoint_payload(checkpoint, child.torch)
    require(payload['parameter_names'] == list(child.parameters)
            and payload.get('experiment') == child.experiment
            and child.optimizer_steps == SAVED_STEPS
            and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'loaded_saved31_adapter_order')
    child.engine.verify_base()
    expected = optimizer_fingerprint(child, payload['optimizer'])
    child.optimizer.load_state_dict(payload['optimizer'])
    require(optimizer_fingerprint(child) == expected, 'exact_saved_AdamW')
    child.torch.set_rng_state(payload['cpu_rng'])
    child.torch.cuda.set_rng_state_all(payload['cuda_rng'])
    random.setstate(payload['python_rng'])
    require(rng(child) == dict(python=digest(payload['python_rng']), cpu=digest(payload['cpu_rng'].tolist()),
            cuda=[digest(value.tolist()) for value in payload['cuda_rng']]), 'exact_saved_Python_CPU_CUDA_RNG')
    return expected


def replay_generations(child, stream, journal, provenance, destination):
    checkpoint = provenance['evidence']['checkpoint']
    binding, records = journal_binding(child.plan, stream, journal, checkpoint)
    require(binding == provenance['journal'], 'CPU_bound_journal_before_replay')
    before_stream, before_plan = deepcopy(stream.checkpoint()), deepcopy(child.plan)
    optimizer = restore(child, checkpoint)
    before_rng = rng(child)
    for number, index in enumerate(binding['pair_indices']):
        request = records[index]['document']
        require(time.time() < child.plan['hard_end_unix'], 'replay_within_original_wall')
        messages = deepcopy(request['messages'])
        save(destination / f'{number:02d}_REQUEST.json', dict(request=request, rng_before=rng(child)))
        output = child.generate(messages, max_new_tokens=request['max_new_tokens'], deadline_unix=request['deadline_unix'])
        save(destination / f'{number:02d}_RESPONSE.json', dict(response=output, rng_after=rng(child)))
        require(digest(output) == digest(records[index + 1]['document']['response']), 'exact_committed_generation_match')
        require(messages == request['messages'] and stream.checkpoint() == before_stream
                and child.plan == before_plan, 'no_replay_history_or_plan_mutation')
        require(child.optimizer_steps == SAVED_STEPS and child.adapter_hash() == checkpoint['adapter_state_sha256']
                and optimizer_fingerprint(child) == optimizer, 'no_replay_learning_mutation')
        child.engine.verify_base()
    require(journal_records(journal)[1] == records, 'no_replay_journal_append')
    require(time.time() < child.plan['hard_end_unix'], 'replay_finished_within_original_wall')
    receipt = dict(status='GENERATIONS_VERIFIED_NOT_SLEEP_RECOVERED', matched_generations=len(binding['pair_indices']),
                   journal_head=binding['journal_head'], optimizer_steps=SAVED_STEPS, optimizer_updates=0,
                   optimizer_state_sha256=optimizer, rng_before=before_rng, rng_after=rng(child),
                   original_postgeneration_rng_snapshot_available=False,
                   verification='exact_committed_outputs_from_saved_RNG_not_comparison_to_missing_final_RNG', no_retry=True)
    save(destination / 'GENERATIONS_VERIFIED.json', receipt)
    return receipt


class SleepRecorder:
    def __init__(self, journal, targets, metadata):
        self.journal, self.targets, self.metadata = journal, deepcopy(targets), deepcopy(metadata)
        self.eligibility_seen = False
        self.metadata_seen = False
        self.updates = []

    def __call__(self, kind, document):
        if kind == 'TARGET_ELIGIBILITY':
            require(not self.eligibility_seen and not self.metadata_seen and not self.updates
                    and document == self.targets['eligibility'], 'exact_once_CPU_eligibility')
            self.eligibility_seen = True
        elif kind == 'CHECKPOINT_METADATA':
            require(self.eligibility_seen and not self.metadata_seen and not self.updates
                    and document == self.metadata, 'exact_existing_R145_metadata')
            self.metadata_seen = True
        elif kind == 'UPDATE':
            position = len(self.updates)
            require(self.eligibility_seen and self.metadata_seen and position < len(self.targets['schedule']),
                    'no_extra_or_unadmitted_updates')
            expected = self.targets['schedule'][position]
            require(document['optimizer_step'] == SAVED_STEPS + position + 1
                    and document['source_sha256'] == expected['source_sha256']
                    and document['losses'][0]['kind'] == expected['cohort'], 'exact_contiguous_CPU_update_schedule')
            self.updates.append(deepcopy(document))
        else:
            raise ValueError('unexpected_pending_sleep_event:' + kind)
        self.journal.record(kind, document)

    def complete(self):
        require(self.eligibility_seen and len(self.updates) == self.targets['expected_updates']
                and self.metadata_seen == bool(self.targets['schedule']), 'complete_CPU_bound_sleep_schedule')


def finish_pending_sleep(child, stream, journal, anchors, provenance, replay_receipt, destination):
    require(read_reference(reference(destination / 'GENERATIONS_VERIFIED.json')) == replay_receipt,
            'saved_replay_receipt')
    require(rng(child) == replay_receipt['rng_after'] and child.optimizer_steps == SAVED_STEPS
            and optimizer_fingerprint(child) == replay_receipt['optimizer_state_sha256']
            and child.adapter_hash() == provenance['evidence']['checkpoint']['adapter_state_sha256'],
            'same_restored_replayed_child')
    binding, records = journal_binding(child.plan, stream, journal, provenance['evidence']['checkpoint'])
    require(binding == provenance['journal'], 'unchanged_journal_before_sleep')
    require(not (ROOT / 'checkpoints' / f'sleep_{CYCLE:06d}').exists(), 'never_repeat_checkpointed_sleep32')
    before = deepcopy(stream.checkpoint())
    pending = deepcopy(stream.pending_rows())
    recorder = SleepRecorder(journal, provenance['targets'], provenance['evidence']['sleep_metadata'])
    receipt = child.sleep(deepcopy(pending), deepcopy(stream.rows[:stream.sleep_frontier]), anchors, recorder)
    recorder.complete()
    require(stream.checkpoint() == before, 'raw_allhistory_carry_unchanged_during_sleep')
    targets = provenance['targets']
    require(receipt['optimizer_steps'] == targets['expected_updates']
            and child.optimizer_steps == receipt['total_optimizer_steps'] == targets['expected_total_steps']
            and receipt['excluded_rows'] == targets['eligibility']['excluded']
            and receipt['presentations'] == dict(Counter(row['source_sha256'] for row in targets['schedule'])),
            'completed_exact_exclusions_and_schedule')
    checkpoint = child.checkpoint(ROOT / 'checkpoints' / f'sleep_{CYCLE:06d}')
    verify_saved_files(checkpoint, CYCLE, targets['expected_total_steps'])
    require(checkpoint.get('experiment') == stream.experiment, 'same_child_experiment_after_sleep32')
    receipt.update(status='COMPLETE', cycle=CYCLE, checkpoint=checkpoint,
                   checkpoint_sha256=checkpoint['checkpoint_sha256'],
                   new_row_sha256=[row['source_sha256'] for row in pending])
    stream.pending = None
    stream.commit_sleep(receipt, journal.record)
    require(journal_records(journal)[1][:len(records)] == records, 'original_history_prefix_preserved')
    save(destination / 'SLEEP32_SAVED.json', dict(status='SLEEP32_SAVED', checkpoint=checkpoint,
         original_journal_head=binding['journal_head'], matched_generations=replay_receipt['matched_generations'],
         original_postgeneration_rng_snapshot_available=False, no_retry=True, finished_unix=time.time()))
    return checkpoint


def failed(path, error, action):
    try:
        save(path, dict(status='FAILED', action=action, error_type=type(error).__name__, error=str(error),
                        no_retry=True, child_must_be_discarded=True, finished_unix=time.time()))
    except Exception:
        pass


def recover_admitted_sleep(plan_path, manifest, acknowledgment):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, verify_experiment_resume
    plan = native.validate_plan(native.read(plan_path))
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == sha(plan_path), 'original_admitted_plan_environment')
    provenance = verify_manifest(manifest, acknowledgment)
    require(plan == provenance['plan'], 'admitted_exact_CPU_plan')
    verify_loaded_native(plan)
    import torch
    environment = runtime_environment(torch)
    previous.verify_topology()
    with StreamJournal(ROOT / 'stream', create=False) as journal:
        with journal._mutex:
            state = journal.latest_checkpoint()
            stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
            verify_experiment_resume(plan, stream.experiment)
            binding, records = journal_binding(plan, stream, journal, provenance['evidence']['checkpoint'])
            require(binding == provenance['journal'], 'exact_CPU_bound_pending32_before_model')
            require(not any(path.is_symlink() for path in (RECOVERY, *RECOVERY.parents)), 'no_recovery_symlinks')
            RECOVERY.parent.mkdir(mode=0o700, exist_ok=True)
            RECOVERY.mkdir(mode=0o700)
            try:
                save(RECOVERY / 'MANIFEST.json', manifest)
                save(RECOVERY / 'ACKNOWLEDGMENT.json', read_reference(acknowledgment))
                save(RECOVERY / 'RUNTIME_ENVIRONMENT.json', environment)
                for name, item in provenance['evidence']['files'].items():
                    save_bytes(RECOVERY / (name + '.original'), raw(item['path']))
                save(RECOVERY / 'ORIGINAL_SUFFIX.json', records[binding['saved_index']:])
                for index in range(binding['saved_index'], binding['record_count']):
                    for suffix in ('.json', '.intent.json'):
                        name = f'{index:020d}' + suffix
                        save_bytes(RECOVERY / name, raw(journal.root / 'records' / name))
                child = native.NativeChild(plan, provenance['evidence']['checkpoint'])
                require(target_contract(plan, stream, child.tokenizer) == provenance['targets'], 'actual_CPU_target_gate_match')
                anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
                save(RECOVERY / 'ANCHOR_INVENTORY.json', anchor_receipt)
                replay = replay_generations(child, stream, journal, provenance, RECOVERY)
                verify_manifest(manifest, acknowledgment)
                return finish_pending_sleep(child, stream, journal, anchors, provenance, replay, RECOVERY)
            except BaseException as error:
                failed(RECOVERY / 'FAILED.json', error, 'restore-replay-sleep32')
                raise


def adapted_node_function(action, manifest):
    from gpu import orch_r137_node4_containment as programmes
    require(action in ('contained_supervise', 'contained_native'), 'original_contained_actions_only')
    expected = manifest['provenance']['evidence']['original_source_pins'][NODE]
    require(sha(Path(programmes.__file__).absolute()) == expected, 'original_pinned_R137_node_bytes')
    function = getattr(programmes, action)
    source = inspect.getsource(function)
    before = 'gpu.orch_r137_node4_containment' if action == 'contained_supervise' else 'gpu.orch_r125_continual_guard'
    require(source.count(repr(before)) == 1, 'one_exact_entrypoint_relocation')
    modified = source.replace(repr(before), repr(MODULE))
    tree = ast.parse(modified)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == MODULE:
            node.value = before
    require(ast.dump(tree) == ast.dump(ast.parse(source)), 'only_entrypoint_literal_changed')
    namespace = dict(function.__globals__)
    if action == 'contained_supervise':
        def contained_command(physical, minor, uid, gid, unit, source_root, command, lifetime):
            require(physical == 7 and minor == 4 and uid == gid == 2524, 'original_identity_and_minor')
            previous.verify_topology()
            return allocator_command(programmes.device_containment_command(
                physical, minor, uid, gid, unit, source_root, command, lifetime))
        namespace['device_containment_command'] = contained_command
    exec(compile(modified, str(Path(__file__).absolute()) + ':' + action, 'exec'), namespace)
    return namespace[action]


def entrypoint():
    import argparse
    from gpu import orch_r125_continual_guard as guard
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('contained-supervise', 'contained-native', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    attempt = None
    try:
        unvalidated = json.loads(raw(arguments.config))
        candidate = Path(unvalidated['attempt_dir'])
        if candidate.parent == BASE and candidate.name.startswith('control_r152_') and candidate.is_dir():
            attempt = candidate
        config, plan = guard.validate(arguments.config)
        manifest = read_reference(config['r152_manifest'])
        acknowledgment = config['r152_acknowledgment']
        provenance = verify_manifest(manifest, acknowledgment)
        require(config['resume'] is True and plan == provenance['plan'], 'same_life_exact_resume_only')
        policy = config['device_containment']
        require(policy['minor'] == 4 and policy['uid'] == policy['gid'] == 2524, 'original_strict_identity')
        if arguments.action != 'native':
            adapted_node_function(arguments.action.replace('-', '_'), manifest)(arguments.config)
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
                return original_run(plan_path, resume=True)

            guard.child.run = recovered_run
            try:
                guard.native_entry(arguments.config)
            finally:
                guard.child.run = original_run
    except BaseException as error:
        if attempt is not None:
            failed(attempt / ('R152_' + arguments.action.upper().replace('-', '_') + '_FAILED.json'),
                   error, arguments.action)
        raise


if __name__ == '__main__':
    entrypoint()
