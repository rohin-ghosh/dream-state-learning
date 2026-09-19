"""C2 receiving hooks; all process control remains an explicit Main capability."""

from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Callable

from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import (
    digest, file_bytes, journal_identity, plan_metadata_binding, read,
    recheck_consumed_wall_receipt, require, same_boundary, sha,
    validate_records, verify_source_only_plans)
from research_loop.workers.post_recovery_retention_boundary_20260918.coordinator import (
    verify_receiver_plan)
from research_loop.workers.post_recovery_retention_boundary_20260918.operations import ReceivingHooks
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.ports import changes_for, NATIVE, RUNTIME


DEADLINE = 1789927200
LEASE_END = 1789948800
GPU_UUID = 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'
TRIAL = 'C2_R216_current_conversation_maintenance'
CONFINEMENT = 'gpu.r188_node5_confinement'
R188_SHA256 = '75eed0e5e57cd7463e46fa10adeeebdb80b9ef1ce5e76a9b527c034d1e8e6481'
CHANGED_FILES = {'gpu/orch_r184_think_act_learn.py',
    'organism_v6/orch_r124_train_history.py', 'organism_v6/orch_r125_continual_stream.py'}
GUARD_RELOCATIONS = {'attempt_dir', 'plan_path', 'plan_sha256', 'lease_path',
    'lease_sha256', 'allocation_path', 'allocation_sha256', 'source_pins'}
ROUTE_GATES = ('parent_delivery_fenced', 'zero_inflight_deliveries',
    'existing_ledgers_preserved', 'cpu_bridge_rebinding_ready',
    'r188_only_dispatch', 'fresh_privileged_admission_required',
    'source_adoption_before_first_think', 'no_model_load_before_writer_lock',
    'original_inbox_rescan', 'receiving_uid_access_verified',
    'explicit_owner_rebind_after_loaded', 'bounded_tail_latency_passed',
    'receiving_builder_entry_logged', 'receiving_allocation_preapproved')


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_once(path, document):
    path = Path(path)
    data = (json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    if path.exists():
        require(file_bytes(path) == data, 'immutable_receiving_artifact')
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o640)
    with os.fdopen(descriptor, 'wb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    sync_directory(path.parent)
    sync_directory(path.parent.parent)


def plan_template(old, source):
    plan = deepcopy(old)
    plan['source_root'] = str(source)
    if 'startup_context' in plan:
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        plan['startup_context']['path'] = str(Path(source) / relative)
    plan.pop('authorized_wall_extension', None)
    return plan


def verify_pins(root, pins):
    root = Path(root)
    require(root.is_absolute() and root.resolve() == root, 'literal_source_root')
    require(all(not Path(name).is_absolute() and '..' not in Path(name).parts
        and (root / name).resolve() == root / name for name in pins), 'literal_relative_source_files')
    require({str(path.relative_to(root)): sha(path) for path in root.rglob('*.py')} == pins,
        'entire_immutable_python_source_closure')


@dataclass(frozen=True)
class MainRoute:
    preflight: Callable[[dict, dict], dict]
    dependents_clear: Callable[[object], bool]
    dispatch_once: Callable[[dict], object]


class C2Receiver:
    def __init__(self, binding, staged, *, cpu_receipt_path, consumed_wall_receipt,
            python_executable, route=None):
        self.binding, self.staged = deepcopy(binding), deepcopy(staged)
        self.cpu_receipt_path = Path(cpu_receipt_path)
        self.consumed = deepcopy(consumed_wall_receipt)
        self.python = str(python_executable)
        self.route = route
        self.source = Path(staged['new_source'])
        self.control = self.source.parent / 'control'
        self.prepared = None

    def hooks(self):
        return ReceivingHooks(self.verify_prepared, self.dependents_clear,
            self.verify_checkpoint, self.prepare_receiver, self.recheck_checkpoint,
            self.verify_receiver, self.dispatch_once)

    def verify_route(self, prepared):
        require(isinstance(self.route, MainRoute), 'Main_r188_bridge_parent_adoption_route_required_before_stop')
        receipt = self.route.preflight(deepcopy(self.binding), deepcopy(prepared))
        require(receipt.get('schema') == 'C2_RETENTION_MAIN_ROUTE_V1'
            and receipt.get('life_binding_sha256') == digest(self.binding)
            and receipt.get('prepared_sha256') == digest(prepared)
            and receipt.get('source_pins_sha256') == digest(prepared['new_source_pins'])
            and receipt.get('dispatcher_module') == CONFINEMENT
            and receipt.get('deadline_unix') == DEADLINE
            and receipt.get('owner') and receipt.get('durable') is True,
            'exact_Main_owned_route_receipt')
        require(all(receipt.get(key) is True for key in ROUTE_GATES), 'Main_route_preflight_incomplete_before_stop')
        require(receipt.get('automatic_parent_adoption') is False
            and receipt.get('inflight_deliveries') == 0, 'no_automatic_parent_adoption_or_inflight_delivery')
        for key in ('evidence_pins', 'ledger_pins'):
            require(receipt.get(key) and all(Path(path).is_absolute()
                and sha(path) == expected for path, expected in receipt[key].items()), 'durable_route_' + key)
            for path in receipt[key]:
                file_bytes(path, durable=True)
        return receipt

    def verify_prepared(self, prepared):
        stage, binding = self.staged, self.binding
        require(self.control.resolve() == self.control, 'literal_receiving_control_directory')
        require(stage['life'] == 'C2' and stage['status'] == 'IMMUTABLE_SOURCE_STAGED_NOT_DISPATCHABLE',
            'C2_nonrunning_immutable_stage_only')
        require(prepared['old_guard_sha256'] == binding['guard_sha256'] == stage['old_guard_sha256']
            == sha(binding['guard_path']), 'exact_old_guard')
        require(prepared['old_source_pins'] == binding['source_pins'] == stage['old_source_pins']
            and prepared['new_source_pins'] == stage['new_source_pins'], 'exact_staged_source_pins')
        changes = {name: dict(before=prepared['old_source_pins'].get(name), after=value)
            for name, value in prepared['new_source_pins'].items()
            if prepared['old_source_pins'].get(name) != value}
        require(RUNTIME in prepared['new_source_pins'], 'epoch1_missing_C2_adoption_seam_Main_new_immutable_stage_required')
        receiving_changes = changes_for(stage['old_source'])
        require(set(prepared['old_source_pins']) | {RUNTIME} == set(prepared['new_source_pins'])
            and changes == stage['changed'] and set(changes) == CHANGED_FILES | {NATIVE, RUNTIME}
            and all(changes.get(name) == expected for name, expected in receiving_changes.items()),
            'three_retention_ports_plus_exact_C2_adoption_seam_only')
        require(prepared['new_source_pins']['gpu/r188_node5_confinement.py'] == R188_SHA256,
            'exact_old_r188_confinement')
        old, new = prepared['old_plan'], prepared['new_plan']
        require(old['source_root'] == stage['old_source'] and new == plan_template(old, self.source),
            'source_relocation_consumed_wall_only_template')
        require(old['hard_end_unix'] == binding['hard_end_unix'] == DEADLINE
            and old['lease_end_unix'] == LEASE_END and old['physical'] == 1
            and old['gpu_uuid'] == GPU_UUID and old['think_act_learn']['trial_id'] == TRIAL
            and old['learn_row_policy'] == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1', 'learned_C2_unchanged_bounds_and_recipe')
        require(stage['journal_root'] == binding['journal_root'] == str(Path(old['root']) / 'stream')
            and stage['journal_id'] == binding['journal_id'], 'original_C2_root_and_journal')
        selection = old['checkpoint_tail_recovery']
        require(selection['root'] == binding['journal_root'] and selection['journal_id'] == binding['journal_id']
            and selection['life_id'] == TRIAL and selection['persist_complete_anchors'] is True,
            'original_checkpoint_tail_reader_and_persistent_anchors')
        native = stage['native']
        require(binding['uid'] == 2524
            and all(binding[key] == native[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id'))
            and binding['command'] == native['argv'], 'exact_staged_native_identity_not_fresh_liveness')
        guard = read(binding['guard_path'])
        require(guard['source_pins'] == prepared['old_source_pins']
            and sha(guard['plan_path']) == guard['plan_sha256'] and read(guard['plan_path']) == old
            and guard['copy_raw'] == old['root'] and guard['resume'] is True, 'original_guard_plan_copy_mapping')
        for source, pins in ((stage['old_source'], prepared['old_source_pins']),
                (self.source, prepared['new_source_pins'])):
            verify_pins(source, pins)
        for plan in (old, new):
            context = plan.get('startup_context')
            if context:
                require(sha(context['path']) == context['sha256'], 'unchanged_startup_context_bytes')
        cpu = read(self.cpu_receipt_path, durable=True)
        require(cpu.get('passed') is True and cpu.get('source_pins') == prepared['new_source_pins']
            and cpu.get('scope') == 'ACTUAL_RECEIVING_SOURCE_CPU', 'real_receiving_CPU_not_synthetic_hook_tests')
        require(isinstance(self.consumed, dict) and set(self.consumed) == {'record', 'intent'},
            'exact_historical_wall_record_and_intent_required')
        record = self.consumed['record']
        validate_records([record], binding, intents={record['index']: self.consumed['intent']})
        require(record['kind'] == 'WALL_EXTENDED'
            and record['document']['authorization'] == old['authorized_wall_extension'], 'same_consumed_wall_authorization')
        for suffix, value in (('.json', record), ('.intent.json', self.consumed['intent'])):
            require(read(Path(binding['journal_root']) / 'records' / f"{record['index']:020d}{suffix}",
                durable=True) == value, 'original_historical_wall_bytes_required')
        journal_identity(binding)
        route = self.verify_route(prepared)
        self.prepared = deepcopy(prepared)
        return route

    def dependents_clear(self, handle):
        require(self.prepared is not None, 'verify_prepared_before_dependency_check')
        self.verify_route(self.prepared)
        return self.route.dependents_clear(handle) is True

    def _probe(self, mode, candidate, plan, selection=None):
        request = dict(source=str(self.source), candidate=candidate, plan=plan, selection=selection)
        path = self.control / 'cpu_requests' / (mode + '.' + digest(request) + '.json')
        write_once(path, request)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(self.source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
        result = subprocess.run([self.python, '-B', str(Path(__file__).with_name('cpu_probe.py')),
            mode, '--request', str(path)], cwd=self.source, env=environment, capture_output=True,
            text=True, timeout=120, check=True)
        proof = json.loads(result.stdout)
        write_once(path.with_suffix('.result.json'), dict(result=proof, stderr=result.stderr))
        return proof

    def verify_checkpoint(self, candidate):
        require(self.prepared is not None, 'verify_prepared_before_checkpoint')
        checkpoint = candidate['checkpoint']
        adapter = Path(checkpoint['adapter_path'])
        directory = adapter.parent
        require(directory.parent == Path(self.binding['journal_root']).parent / 'checkpoints'
            and directory.resolve() == directory and adapter.resolve() == adapter
            and Path(checkpoint['optimizer_rng_path']) == directory / 'optimizer_rng.pt'
            and read(directory / 'COMMIT.json') == checkpoint, 'exact_original_saved_checkpoint')
        paths = [directory / 'COMMIT.json', directory / 'optimizer_rng.pt', *sorted(adapter.iterdir())]
        pins = {str(path): sha(path) for path in paths}
        for path in paths:
            file_bytes(path, durable=True)
        for path in (adapter, directory, directory.parent):
            sync_directory(path)
        proof = self._probe('checkpoint', candidate, self.prepared['new_plan'])
        require(all(proof.get(key) is True for key in ('adapter_verified', 'optimizer_verified',
            'python_cpu_cuda_rng_verified', 'working_state_verified', 'no_GPU_calls')),
            'learned_C2_CPU_checkpoint_restore_proof')
        proof.update(complete_sha256=candidate['complete_sha256'], checkpoint_sha256=digest(checkpoint),
            durable_files_and_directories=True, files=pins)
        return proof

    def prepare_receiver(self, candidate, prepared, proof):
        route = self.verify_prepared(prepared)
        self.recheck_checkpoint(proof, candidate)
        plan = deepcopy(prepared['new_plan'])
        plan['checkpoint_tail_recovery'].update(complete_index=candidate['complete_index'],
            complete_sha256=candidate['complete_sha256'])
        stamp = plan_metadata_binding(self.binding, candidate, prepared['old_plan'], plan)
        scanned = self._probe('tail', candidate, plan, plan['checkpoint_tail_recovery'])
        require(scanned['complete_index'] == candidate['complete_index']
            and scanned['complete_sha256'] == candidate['complete_sha256']
            and scanned['restored_state_sha256'] == candidate['resume_state']['sha256']
            and scanned['record_count'] == candidate['head_index'] + 1
            and scanned['head_sha256'] == candidate['head_sha256']
            and scanned['prefix_work'] == 'ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY'
            and scanned['read_only'] is True and scanned['writer_lock_acquired'] is False
            and scanned['journal_writes'] == 0 and scanned['pending'] is None
            and scanned['sidecars_verified'] is True and scanned['inbox_preserved'] is True,
            'actual_readonly_tail_scan_exact_candidate_no_replay')
        self.recheck_sidecars(scanned, plan)
        receipts = dict(consumed_wall_extension=dict(self.consumed, binding=stamp, durable=True),
            checkpoint_tail_recovery=dict(binding=stamp, durable=True,
                selection_sha256=digest(plan['checkpoint_tail_recovery']),
                restored_state_sha256=scanned['restored_state_sha256'],
                head_index=candidate['head_index'], head_sha256=scanned['head_sha256'], pending=None,
                historical_body_replay=False, sidecars_verified=True, inbox_preserved=True,
                reader_source_pins_sha256=digest(prepared['new_source_pins']), cpu_receipt_sha256=digest(scanned)))
        verify_source_only_plans(prepared['old_plan'], plan, binding=self.binding, candidate=candidate, receipts=receipts)
        recheck_consumed_wall_receipt(self.binding, receipts)
        attempt = self.control / 'attempts' / digest(dict(candidate=candidate, plan=plan, route=route, proof=proof))
        old_guard = read(self.binding['guard_path'])
        require(sha(old_guard['lease_path']) == old_guard['lease_sha256']
            and sha(old_guard['allocation_path']) == old_guard['allocation_sha256'], 'unchanged_original_lease_allocation')
        write_once(attempt / 'PLAN.json', plan)
        write_once(attempt / 'LEASE.json', read(old_guard['lease_path']))
        write_once(attempt / 'RECEIVING_CPU.json', read(self.cpu_receipt_path))
        write_once(attempt / 'TAIL_CPU.json', scanned)
        write_once(attempt / 'CHECKPOINT_CPU.json', proof)
        write_once(attempt / 'MAIN_ROUTE.json', route)
        write_once(attempt / 'PLAN_METADATA_RECEIPTS.json', receipts)
        allocation = read(old_guard['allocation_path'])
        allocation.update(plan_sha256=sha(attempt / 'PLAN.json'),
            cpu_receipt_path=str(attempt / 'RECEIVING_CPU.json'),
            cpu_receipt_sha256=sha(attempt / 'RECEIVING_CPU.json'), cpu_tests_passed=True)
        write_once(attempt / 'ALLOCATION.json', allocation)
        guard = deepcopy(old_guard)
        guard.update(attempt_dir=str(attempt), plan_path=str(attempt / 'PLAN.json'), plan_sha256=sha(attempt / 'PLAN.json'),
            lease_path=str(attempt / 'LEASE.json'), lease_sha256=sha(attempt / 'LEASE.json'),
            allocation_path=str(attempt / 'ALLOCATION.json'), allocation_sha256=sha(attempt / 'ALLOCATION.json'),
            source_pins=prepared['new_source_pins'])
        write_once(attempt / 'GUARD.json', guard)
        guard_proof = self._probe('guard', candidate, plan, dict(guard_path=str(attempt / 'GUARD.json')))
        require(guard_proof.get('validated') is True and guard_proof.get('admission_bypassed') is False
            and guard_proof.get('guard_sha256') == sha(attempt / 'GUARD.json'), 'actual_receiving_guard_CPU_validation')
        write_once(attempt / 'GUARD_CPU.json', guard_proof)
        parent = dict(schema='C2_RETENTION_OWNER_REBIND_REQUIRED_V1', new_native=None,
            automatic_parent_adoption=False, parent_rebind_allowed=False,
            life_binding_sha256=digest(self.binding), receiving_guard_sha256=sha(attempt / 'GUARD.json'),
            source_epoch=prepared['epoch_id'], main_route_sha256=digest(route),
            requires=['actual_native_LOADED', 'durable_source_adoption', 'explicit_owner_rebind', 'preserved_ledgers'])
        write_once(attempt / 'OWNER_REBIND_REQUIRED.json', parent)
        receiver = dict(source_epoch=prepared['epoch_id'], plan=plan, plan_sha256=digest(plan),
            plan_metadata_receipts=receipts, resume_state_sha256=candidate['resume_state']['sha256'],
            checkpoint_sha256=digest(candidate['checkpoint']), same_journal_root=self.binding['journal_root'],
            rescans_original_inbox=True, no_model_load_before_writer_lock=True, deadline_unix=DEADLINE,
            source_adoption_not_wall_extension=True, dispatcher_module=CONFINEMENT,
            guard_path=str(attempt / 'GUARD.json'), candidate=deepcopy(candidate),
            parent_rebind_allowed=False, artifact_pins={str(path): sha(path) for path in attempt.iterdir()
                if path.name != 'RECEIVER.json'})
        verify_receiver_plan(self.binding, prepared, receiver, candidate)
        write_once(attempt / 'RECEIVER.json', receiver)
        return receiver

    def recheck_checkpoint(self, proof, frozen):
        require(proof['complete_sha256'] == frozen['complete_sha256']
            and proof['checkpoint_sha256'] == digest(frozen['checkpoint'])
            and proof.get('files') and all(sha(path) == value for path, value in proof['files'].items()),
            'same_saved_checkpoint_files')

    def recheck_sidecars(self, scanned, plan):
        expected_names = {entry['name'] for entry in plan['checkpoint_tail_recovery']['sidecars']}
        pins = scanned.get('sidecar_pins', {})
        root = Path(self.binding['journal_root'])
        require(set(pins) == expected_names and all(Path(name).name == name
            and sha(root / name) == expected for name, expected in pins.items()), 'same_original_tail_sidecars')
        for name in pins:
            file_bytes(root / name, durable=True)
        sync_directory(root)

    def verify_receiver(self, receiver, frozen):
        require(self.prepared is not None, 'verified_receiver_prepared')
        route = self.verify_prepared(self.prepared)
        same_boundary(receiver['candidate'], frozen)
        require(all(sha(path) == expected for path, expected in receiver['artifact_pins'].items()),
            'immutable_receiving_artifacts')
        attempt = Path(receiver['guard_path']).parent
        require(read(attempt / 'MAIN_ROUTE.json') == route and read(attempt / 'RECEIVER.json') == receiver,
            'exact_receiver_and_owner_route')
        recheck_consumed_wall_receipt(self.binding, receiver['plan_metadata_receipts'])
        verify_receiver_plan(self.binding, self.prepared, receiver, frozen)
        self.recheck_checkpoint(read(attempt / 'CHECKPOINT_CPU.json'), frozen)
        self.recheck_sidecars(read(attempt / 'TAIL_CPU.json'), receiver['plan'])
        guard, old = read(receiver['guard_path']), read(self.binding['guard_path'])
        require({key: value for key, value in guard.items() if key not in GUARD_RELOCATIONS}
            == {key: value for key, value in old.items() if key not in GUARD_RELOCATIONS},
            'unchanged_r188_guard_confinement_copy_mapping')

    def dispatch_once(self, token):
        require(self.prepared is not None and self.route is not None, 'Main_dispatch_capability_required')
        require(token.get('schema') == 'RETENTION_HANDOFF_TOKEN_V1'
            and token.get('old_native_exited') is True and token.get('life_binding_sha256') == digest(self.binding)
            and token.get('prepared_sha256') == digest(self.prepared)
            and token.get('epoch_id') == self.prepared['epoch_id']
            and token.get('new_source_pins') == self.prepared['new_source_pins']
            and token.get('old_pid') == self.binding['pid'] and token.get('old_start_ticks') == self.binding['start_ticks']
            and token.get('deadline_unix') == DEADLINE and time.time() < DEADLINE
            and token.get('no_cold_start') is True and token.get('no_unresolved_work_replayed') is True
            and token.get('epoch_record_required_before_first_THINK') is True
            and token.get('sha256') == digest({key: value for key, value in token.items() if key != 'sha256'}),
            'exact_unexpired_exited_source_epoch_token')
        self.verify_receiver(token['receiver'], token['exact_complete'])
        claim = self.control / 'C2_DISPATCH_CLAIM'
        claim.mkdir(mode=0o750)
        sync_directory(self.control)
        write_once(claim / 'HANDOFF.json', token)
        write_once(self.control / 'RETENTION_HANDOFF.json', token)
        result = self.route.dispatch_once(deepcopy(token))
        write_once(claim / 'RESULT.json', dict(result=result, parent_rebind_allowed=False,
            loaded=False, pid_role='DISPATCH_RESULT_NOT_NATIVE_IDENTITY'))
        return result
