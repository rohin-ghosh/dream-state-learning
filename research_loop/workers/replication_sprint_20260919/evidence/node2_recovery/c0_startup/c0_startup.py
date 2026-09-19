"""C0 pending-sleep continuation inside the original confined entry chain."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import signal
import time

import c0_kernel as kernel
import c0_tail as tail


SCHEMA = 'C0_PENDING_SLEEP_STARTUP_V1'
TRIAL = 'R216_C0_SNAPSHOT51_MATH'
LIFE = '/localhome/local-rohing/orch_r216_C0_20260918_attempt2'
ORIGINAL_SOURCE = LIFE + '/source_r233_lease_continuation'
ORIGINAL_PLAN = LIFE + '/control_r233_lease_continuation/PLAN.json'
ORIGINAL_GUARD = LIFE + '/control_r233_lease_continuation/GUARD.json'
GUARD_SHA = 'acf4d2d015874af1cc9585a25de63827e7d7ec36acd7a4509bce09671985f6c2'
ROOT = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
RAW = LIFE + '/raw'
STAGED_SOURCE = LIFE + '/source_c0_pending_v1'
CONTROL = LIFE + '/control_c0_pending_v1'
MODULE = 'gpu.c0_pending_entry'
require = kernel.require
digest = kernel.digest


def bound_bytes(descriptor):
    require(type(descriptor) is dict and set(descriptor) == {'path', 'sha256'}, 'exact_file_binding')
    path = Path(descriptor['path'])
    require(path.is_absolute() and not path.is_symlink(), 'absolute_unredirected_receipt')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == descriptor['sha256'], 'receipt_bytes_changed')
    return raw


def validate_manifest(manifest, plan_bytes):
    require(manifest['schema'] == SCHEMA and manifest['life'] == 'C0', 'C0_only_manifest')
    original_bytes = bound_bytes(manifest['original_plan'])
    wall = kernel.observed_wall_compatibility(original_bytes, 'C0')
    original, execution = json.loads(original_bytes), json.loads(plan_bytes)
    require(original['source_root'] == ORIGINAL_SOURCE and original['root'] == ROOT,
        'original_C0_namespace')
    require(manifest['staged_source_root'] == STAGED_SOURCE
        and execution == kernel.relocated_execution_plan(original, STAGED_SOURCE),
        'only_source_location_delta_no_other_plan_change')
    require(manifest['source_path_bindings'] == [dict(field='startup_context.path',
        original=original['startup_context']['path'], execution=execution['startup_context']['path'],
        sha256=original['startup_context']['sha256'])], 'explicit_same_bytes_startup_path_relocation')
    require(hashlib.sha256(plan_bytes).hexdigest() == manifest['execution_plan_sha256'],
        'execution_plan_bytes_pin')
    require(manifest['applied_wall'] == wall and execution['hard_end_unix'] == kernel.FINAL_BOUND,
        'same_authorization_finalbound_no_new_extension')
    require(execution['physical'] == 4
        and execution['gpu_uuid'] == 'GPU-d304a15c-516a-16a0-a926-a560304077cc'
        and execution['think_act_learn']['trial_id'] == TRIAL, 'original_C0_slot_trial')
    envelope = json.loads(bound_bytes(manifest['candidate']))
    candidate = envelope['candidate']
    require(envelope['sha256'] == digest(candidate), 'candidate_content_pin')
    contract = candidate['contract']['contract']
    require(candidate['original_plan_sha256'] == wall['original_plan_sha256']
        and contract['life'] == 'C0' and contract['pending_cycle'] == 146
        and contract['durable_optimizer_steps'] == 8412 and contract['pending_rows'] == 3
        and contract['recorded_uncheckpointed_updates'] == 48,
        'C0_original_pending_sleep_scope')
    selection = tail.validate_selection(manifest['selection'], Path(execution['root']) / 'stream', TRIAL)
    require(selection['journal_id'] == contract['journal_id']
        and selection['complete_index'] == contract['complete']['index']
        and selection['complete_sha256'] == contract['complete']['sha256'], 'exact_COMPLETE_selection')
    require(selection['sidecars'] == [dict(name='correction_ledger.json',
        kind='R197_CORRECTION_CYCLE', required=True)], 'preserve_C0_correction_sidecar')
    return original_bytes, execution, envelope, selection


def validate_guard_binding(config, manifest, plan_bytes):
    validate_manifest(manifest, plan_bytes)
    original = json.loads(bound_bytes(manifest['original_guard']))
    require(manifest['original_guard']['sha256'] == GUARD_SHA, 'original_guard_pin')
    allowed = {'plan_path', 'plan_sha256', 'attempt_dir', 'source_pins',
        'allocation_path', 'allocation_sha256', 'pending_sleep_recovery'}
    require(set(config) == set(original) | {'pending_sleep_recovery'}
        and all(config[key] == value for key, value in original.items() if key not in allowed),
        'preserve_original_guard_namespace_admission_and_lease')
    require(config['resume'] is True and config['copy_raw'] == RAW
        and config['attempt_dir'] == CONTROL and config['plan_path'] == CONTROL + '/PLAN.json'
        and config['allocation_path'] == CONTROL + '/ALLOCATION.json'
        and config['plan_sha256'] == manifest['execution_plan_sha256'], 'unique_receiving_control')
    delta = json.loads(bound_bytes(manifest['source_delta']))
    require(delta['schema'] == 'C0_EXECUTION_SOURCE_DELTA_V1'
        and delta['original_source_pins'] == original['source_pins']
        and delta['original_plan_sha256'] == manifest['original_plan']['sha256']
        and delta['execution_plan_sha256'] == config['plan_sha256'], 'exact_original_source_delta_binding')
    additions = delta['additions']
    require(set(additions) == {'c0_kernel.py', 'c0_applied_wall_validation.py',
        'c0_restart_contract.py', 'c0_tail.py', 'c0_startup.py', 'gpu/c0_pending_entry.py'}
        and not (set(additions) & set(original['source_pins']))
        and config['source_pins'] == dict(original['source_pins'], **additions),
        'only_six_additions_no_original_source_edit')
    return delta


def make_journal_class(base, selection):
    class PendingSleepJournal(base):
        def __init__(self, root, *, create=False):
            require(create is False, 'never_create_or_reset_original_journal')
            self._checkpoint_tail = tail.validate_selection(selection, root, TRIAL)
            super().__init__(root, create=False)

        def _scan(self):
            return tail.scan(self, self._checkpoint_tail)

        def checkpoint_tail_audit(self):
            with self._mutex:
                self._state = self._reload_state()
                return deepcopy(self.checkpoint_tail_receipt)

        def audit(self):
            raise ValueError('use_explicit_checkpoint_tail_audit_not_full_JSON_replay')

        def record(self, kind, document):
            reference = super().record(kind, document)
            if kind == 'SLEEP_COMPLETE':
                tail.persist_complete(self, reference)
            return reference

    return PendingSleepJournal


def resume(plan_path, *, resume, manifest, native, journal_class, build_inventory,
           run_loop, clock=time.time):
    require(resume is True, 'explicit_same_life_resume_only')
    plan_bytes = Path(plan_path).read_bytes()
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == hashlib.sha256(plan_bytes).hexdigest(),
        'original_guard_admitted_execution_plan_environment')
    original_bytes, plan, envelope, selection = validate_manifest(manifest, plan_bytes)
    require(native.validate_plan(deepcopy(plan)) == plan, 'original_native_plan_validation')
    require(clock() < kernel.FINAL_BOUND, 'original_hard_end_expired')
    previous = signal.signal(signal.SIGALRM,
        lambda signum, frame: (_ for _ in ()).throw(TimeoutError('native_wall')))
    signal.setitimer(signal.ITIMER_REAL, kernel.FINAL_BOUND - clock())
    try:
        with journal_class(Path(plan['root']) / 'stream', create=False) as journal:
            anchor_receipt = {}

            def anchors_for(child):
                anchors, receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
                anchor_receipt.update(receipt)
                return anchors

            recovered = kernel.finish_interrupted_sleep(envelope, expected_sha256=envelope['sha256'],
                native=native, journal=journal, plan_bytes=original_bytes, execution_plan=plan,
                anchor_factory=anchors_for, clock=clock)
            child, stream = recovered['child'], recovered['stream']
            journal.record('LOADED', dict(pid=os.getpid(), runtime=child.engine.runtime,
                base_sha256=native.BASE_SHA256, adapter_sha256=child.adapter_hash(),
                optimizer_steps=child.optimizer_steps, anchors=anchor_receipt, resume=True,
                loaded_unix=clock(), **(dict(plasticity=child.plasticity)
                    if getattr(child, 'plasticity', None) is not None else {})))
            journal.record('C0_PENDING_SLEEP_STARTUP_COMPLETE', dict(schema=SCHEMA,
                candidate_sha256=envelope['sha256'], original_plan_sha256=manifest['original_plan']['sha256'],
                execution_plan_sha256=manifest['execution_plan_sha256'], source_root=plan['source_root'],
                complete=recovered['complete_reference'], paired_LEARN=recovered['paired_LEARN'],
                audit=deepcopy(journal.checkpoint_tail_receipt), wall_extension_reapplied=False,
                original_hard_end_unix=kernel.FINAL_BOUND, no_rows_discarded=True,
                rng_origin=recovered['accounting']['rng_origin'], exact_resident_continuity_claimed=False))
            return run_loop(child, stream, journal, recovered['anchors'], plan, Path(plan['root']),
                plan_path, recovered['completed_sleeps'])
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
