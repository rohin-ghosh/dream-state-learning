"""Admitted math-B pending-sleep startup; no reset, provider or launcher."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import signal
import time

import checkpoint_tail_runtime as tail
import math_b_runtime_candidate as kernel
from pending_sleep_contract import HARD_END, ORIGINAL_GPUS, digest, relocated_execution_plan, require


SCHEMA = 'NODE3_MATH_B_INTERRUPTED_SLEEP_STARTUP_V1'


def bound_bytes(descriptor):
    require(type(descriptor) is dict and set(descriptor) == {'path', 'sha256'}, 'exact_file_binding')
    path = Path(descriptor['path'])
    require(path.is_absolute() and not path.is_symlink(), 'absolute_unredirected_receipt')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == descriptor['sha256'], 'receipt_bytes_changed')
    return raw


def validate_manifest(manifest, plan_bytes):
    require(manifest['schema'] == SCHEMA and manifest['life'] == 'r213_math_b_fork',
        'only_original_math_B_interrupted_sleep')
    original_bytes = bound_bytes(manifest['original_plan'])
    original, execution = json.loads(original_bytes), json.loads(plan_bytes)
    require(hashlib.sha256(plan_bytes).hexdigest() == manifest['execution_plan_sha256'],
        'source_bound_execution_plan')
    require(execution == relocated_execution_plan(original, manifest['staged_source_root']),
        'only_source_location_delta_no_scientific_change')
    staged_source = Path(manifest['staged_source_root'])
    require(staged_source.is_absolute() and staged_source.parent.name == 'r213_math_b_fork'
        and staged_source.name.startswith('source_ws6_pending_math_b_')
        and staged_source != Path(original['source_root']), 'unique_original_life_source_staging')
    require((execution['physical'], execution['gpu_uuid']) == ORIGINAL_GPUS['r213_math_b_fork']
        and execution['hard_end_unix'] == HARD_END < execution['lease_end_unix'],
        'original_GPU_and_wall_only')
    envelope = json.loads(bound_bytes(manifest['candidate']))
    require(envelope['sha256'] == digest(envelope['candidate']), 'candidate_content_pin')
    contract = envelope['candidate']['contract']['contract']
    require(envelope['candidate']['original_plan_sha256'] == manifest['original_plan']['sha256']
        and contract['preserved_state']['state']['deadline_unix'] == HARD_END,
        'pending_state_matches_original_wall_not_new_extension')
    authorization = execution.get('authorized_wall_extension')
    require(authorization is None or authorization['new_deadline_unix'] == HARD_END,
        'only_already_consumed_wall_declaration')
    require(execution['think_act_learn']['trial_id'] == 'R213_NEW_MATH_B', 'original_math_B_ledger_identity')
    selection = tail.validate_selection(manifest['selection'],
        Path(execution['root']) / 'stream', execution['think_act_learn']['trial_id'])
    expected_sidecars = ([dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
        if execution['think_act_learn'].get('correction_ledger') == 'R197_CORRECTION_LEDGER_V1' else [])
    require(selection['sidecars'] == expected_sidecars, 'preserve_original_correction_ledger_sidecar')
    require(selection['journal_id'] == contract['journal_id']
        and selection['complete_index'] == contract['complete']['index']
        and selection['complete_sha256'] == contract['complete']['sha256'],
        'exact_durable_complete_selection')
    return original_bytes, execution, envelope, selection


def make_journal_class(base, selection):
    class PendingSleepJournal(base):
        def __init__(self, root, *, create=False):
            require(create is False, 'never_create_or_reset_original_journal')
            self._checkpoint_tail = tail.validate_selection(selection, root, 'R213_NEW_MATH_B')
            super().__init__(root, create=False)

        def _scan(self):
            return tail.scan(self, self._checkpoint_tail)

        def checkpoint_tail_audit(self):
            with self._mutex:
                self._state = self._reload_state()
                return deepcopy(self.checkpoint_tail_receipt)

        def audit(self):
            raise ValueError('use_explicit_checkpoint_tail_audit_not_full_semantic_replay_claim')

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
        'original_guard_admitted_plan_environment')
    original_bytes, plan, envelope, selection = validate_manifest(manifest, plan_bytes)
    require(native.validate_plan(deepcopy(plan)) == plan, 'original_plan_validation_unchanged')
    require(clock() < HARD_END, 'original_hard_end_expired')
    old_handler = signal.signal(signal.SIGALRM,
        lambda signum, frame: (_ for _ in ()).throw(TimeoutError('native_wall')))
    signal.setitimer(signal.ITIMER_REAL, HARD_END - clock())
    try:
        with journal_class(Path(plan['root']) / 'stream', create=False) as journal:
            anchor_state = {}

            def anchors_for(child):
                anchors, receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
                anchor_state.update(anchors=anchors, receipt=receipt)
                return anchors

            recovered = kernel.finish_pending_sleep(envelope, expected_sha256=envelope['sha256'],
                native=native, journal=journal, plan_bytes=original_bytes,
                execution_plan=plan, anchor_factory=anchors_for, clock=clock)
            child, stream = recovered['child'], recovered['stream']
            require(stream.deadline_unix == HARD_END and stream.pending is None,
                'finished_sleep_same_deadline')
            journal.record('LOADED', dict(pid=os.getpid(), runtime=child.engine.runtime,
                base_sha256=native.BASE_SHA256, adapter_sha256=child.adapter_hash(),
                optimizer_steps=child.optimizer_steps, anchors=anchor_state['receipt'],
                resume=True, loaded_unix=clock(),
                **(dict(plasticity=child.plasticity) if getattr(child, 'plasticity', None) is not None else {})))
            journal.record('NODE3_PENDING_SLEEP_STARTUP_COMPLETE', dict(schema=SCHEMA,
                candidate_sha256=envelope['sha256'], source_root=plan['source_root'],
                original_plan_sha256=manifest['original_plan']['sha256'],
                execution_plan_sha256=manifest['execution_plan_sha256'],
                exact_complete=recovered['complete'], paired_LEARN=recovered['paired_LEARN'],
                journal_audit=deepcopy(journal.checkpoint_tail_receipt),
                wall_extension_reapplied=False, original_hard_end_unix=HARD_END,
                no_rows_discarded=True, no_historical_generation_replayed=True))
            return run_loop(child, stream, journal, anchor_state['anchors'], plan,
                Path(plan['root']), plan_path, recovered['completed_sleeps'])
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
