"""Uninstalled restart kernel; no launcher, admission substitute, or journal repair.

A future original confined driver must supply its admitted native module and
exclusively opened, fully verified journal. CPU tests supply a non-GPU child.
The existing contract remains execution_authorized=False.
"""

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

from research_loop.workers.post_recovery_node2_sleep_20260919 import restart_contract


SCHEMA = 'NODE2_INTERRUPTED_SLEEP_RUNTIME_CANDIDATE_V1'
EXECUTION_AUTHORIZED = False
require = restart_contract.require
digest = restart_contract.digest


def prepare_candidate(complete, pending, updates, *, recipe, eligibility, life, plan_bytes):
    """Bind supplied authenticated records, not a reconstruction of missing tensors."""
    plan = json.loads(plan_bytes)
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0,
        'original_sixteen_NEW_only_presentations')
    require(plan['learn_row_policy'] == plan['think_act_learn']['learn_row_policy']
        == restart_contract.ROW_POLICY, 'same_all_authentic_row_policy')
    require(plan.get('authorized_wall_extension') is None and plan.get('preupdate_recovery') is None,
        'neither_deadline_extension_nor_preupdate_spoof')
    prepared = restart_contract.prepare(complete, pending, updates, life=life,
        recipe=recipe, eligibility=eligibility, head=updates[-1],
        new_presentations=plan['new_presentations'], row_policy=plan['learn_row_policy'],
        hard_end_unix=plan['hard_end_unix'])
    contract = prepared['contract']
    require(contract['pending_rows'] == 3, 'exact_three_pending_rows')
    require(plan['hard_end_unix'] == 1789927200, 'original_node2_hard_end_only')
    checkpoint = deepcopy(complete['document']['checkpoint'])
    attempt_key = digest(dict(life=life, journal_id=contract['journal_id'],
        pending_sleep=contract['pending_sleep']))
    candidate = dict(schema=SCHEMA, contract=prepared, durable_checkpoint=checkpoint,
        original_plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
        recipe=deepcopy(recipe['document']), eligibility=deepcopy(eligibility['document']),
        attempt_key=attempt_key,
        checkpoint_name=f'sleep_{contract["pending_cycle"]:06d}_restart_{attempt_key}',
        execution_authorized=False)
    return dict(candidate=candidate, sha256=digest(candidate))


def _write_once(path, document):
    raw = json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    with path.open('xb') as output:
        output.write(raw + b'\n')
        output.flush()
        os.fsync(output.fileno())
    _sync_directory(path.parent)


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _committed_checkpoint(native, checkpoint, directory):
    require(Path(checkpoint['adapter_path']) == directory / 'adapter'
        and Path(checkpoint['optimizer_rng_path']) == directory / 'optimizer_rng.pt',
        'exact_checkpoint_namespace')
    require(json.loads((directory / 'COMMIT.json').read_bytes()) == checkpoint,
        'checkpoint_must_have_exact_COMMIT')
    native.NativeChild.verify_checkpoint(checkpoint)


class RecoveryRecorder:
    def __init__(self, candidate, journal, check_wall):
        self.candidate = candidate
        self.journal = journal
        self.check_wall = check_wall
        self.phase = 'SLEEP_RECIPE'
        self.counts = Counter()
        self.references = []

    def __call__(self, kind, document):
        self.check_wall()
        contract = self.candidate['contract']['contract']
        require(kind in ('SLEEP_RECIPE', 'TARGET_ELIGIBILITY', 'UPDATE'),
            'no_historical_generation_tool_or_other_publication')
        if kind == 'SLEEP_RECIPE':
            require(self.phase == kind and document == self.candidate['recipe'],
                'unchanged_original_sleep_recipe')
        elif kind == 'TARGET_ELIGIBILITY':
            require(self.phase == kind and document == self.candidate['eligibility'],
                'unchanged_all_rows_target_eligibility')
        else:
            require(self.phase == 'UPDATE', 'recipe_and_eligibility_before_training')
            source = document['source_sha256']
            require(source in contract['pending_row_sha256']
                and self.counts[source] < contract['new_presentations']
                and document['optimizer_step']
                == contract['durable_optimizer_steps'] + len(self.references) + 1,
                'new_recovery_updates_not_unsaved_counter_continuation')
        annotated = deepcopy(document)
        annotated['interrupted_sleep_restart'] = dict(
            epoch_sha256=self.candidate['contract']['sha256'],
            attempt_key=self.candidate['attempt_key'], compute_origin='NEW_RECOVERY_COMPUTE')
        reference = self.journal.record(kind, annotated)
        if kind == 'UPDATE':
            self.counts[document['source_sha256']] += 1
            self.references.append(reference)
        else:
            self.phase = 'TARGET_ELIGIBILITY' if kind == 'SLEEP_RECIPE' else 'UPDATE'
        return reference

    def verify_finished(self, child, receipt):
        contract = self.candidate['contract']['contract']
        expected = {source: contract['new_presentations'] for source in contract['pending_row_sha256']}
        steps = sum(expected.values())
        require(self.phase == 'UPDATE' and dict(self.counts) == expected
            and receipt['presentations'] == expected and receipt['excluded_rows'] == [],
            'full_pending_sleep_without_exclusions')
        require(receipt['optimizer_steps'] == steps
            and receipt['total_optimizer_steps'] == child.optimizer_steps
            == contract['durable_optimizer_steps'] + steps,
            'full_new_recovery_compute_accounting')
        require(receipt['frozen_base_verified'] is True
            and receipt['before_adapter_sha256'] == self.candidate['durable_checkpoint']['adapter_state_sha256']
            and receipt['after_adapter_sha256'] == child.adapter_hash()
            and receipt['after_adapter_sha256'] != receipt['before_adapter_sha256'],
            'original_learning_and_frozen_base_receipt')


def finish_interrupted_sleep(envelope, *, expected_sha256, native, journal,
                             plan_bytes, anchors, clock=time.time):
    """Candidate body for a future admitted process, NOT an entry/admission route.

    This never opens/repairs an old journal or calls generate, tools, presleep,
    fresh_readout, run_loop, or a process launcher. Failure consumes its claim;
    any saved-but-unpublished checkpoint needs explicit reconciliation.
    """
    candidate = deepcopy(envelope['candidate'])
    require(envelope['sha256'] == expected_sha256 == digest(candidate), 'pinned_candidate')
    require(candidate['schema'] == SCHEMA and candidate['execution_authorized'] is False,
        'uninstalled_candidate_only')
    prepared = candidate['contract']
    contract = prepared['contract']
    require(prepared['sha256'] == digest(contract) and contract['execution_authorized'] is False,
        'unaltered_non_authorizing_contract')
    require(hashlib.sha256(plan_bytes).hexdigest() == candidate['original_plan_sha256'],
        'unchanged_original_plan_bytes')
    plan = json.loads(plan_bytes)
    require(plan['hard_end_unix'] == contract['hard_end_unix'] == 1789927200,
        'original_deadline_unchanged')

    def check_wall():
        require(clock() < contract['hard_end_unix'], 'original_hard_end_expired')

    check_wall()
    root = Path(plan['root'])
    attempt_key = digest(dict(life=contract['life'], journal_id=contract['journal_id'],
        pending_sleep=contract['pending_sleep']))
    require(candidate['attempt_key'] == attempt_key and candidate['checkpoint_name']
        == f'sleep_{contract["pending_cycle"]:06d}_restart_{attempt_key}', 'stable_pending_sleep_identity')
    destination = root / 'checkpoints' / candidate['checkpoint_name']
    attempts = root / 'interrupted_sleep_restarts'
    require(not attempts.is_symlink() and not (root / 'checkpoints').is_symlink(),
        'no_redirected_new_namespaces')
    require(not os.path.lexists(destination), 'never_overwrite_or_adopt_checkpoint')
    require(not os.path.lexists(attempts / attempt_key), 'restart_attempt_consumed_no_auto_retry')
    audit = journal.audit()
    require(audit == dict(record_count=contract['old_head']['index'] + 1,
        head_sha256=contract['old_head']['sha256']), 'fresh_fully_verified_exact_old_head')
    latest = journal.latest_checkpoint()
    require(latest == dict(document=contract['preserved_state'],
        expected_sha256=contract['preserved_state']['sha256']), 'exact_current_pending_stream')
    stream = native.ContinualStream.restore(contract['preserved_state'],
        expected_sha256=contract['preserved_state']['sha256'])
    require(stream.checkpoint() == contract['preserved_state'], 'lossless_rows_history_working_state_restore')
    native.verify_experiment_resume(plan, stream.experiment)
    durable = candidate['durable_checkpoint']
    require(durable['checkpoint_sha256'] == contract['checkpoint_sha256']
        and durable['optimizer_steps'] == contract['durable_optimizer_steps']
        and durable['experiment'] == stream.experiment, 'durable_not_incomplete_checkpoint')
    saved_directory = Path(durable['adapter_path']).parent
    require(saved_directory == root / 'checkpoints' / f'sleep_{contract["pending_cycle"] - 1:06d}',
        'last_durable_sleep_only')
    _committed_checkpoint(native, durable, saved_directory)
    check_wall()
    attempts.mkdir(exist_ok=True)
    _sync_directory(root)
    attempt = attempts / attempt_key
    attempt.mkdir(exist_ok=False)
    _sync_directory(attempts)
    recorder = RecoveryRecorder(candidate, journal, check_wall)
    started = clock()
    accounting = dict(schema=SCHEMA, candidate_sha256=expected_sha256,
        contract_sha256=prepared['sha256'], attempt_key=attempt_key,
        old_head=contract['old_head'], durable_complete=contract['complete'],
        pending_sleep=contract['pending_sleep'], pending_cycle=contract['pending_cycle'],
        retained_rows=contract['retained_rows'], pending_rows=contract['pending_rows'],
        durable_optimizer_steps=contract['durable_optimizer_steps'],
        recorded_uncheckpointed_updates=contract['recorded_uncheckpointed_updates'],
        actual_lost_compute_not_fully_known=True,
        recorded_uncheckpointed_updates_not_reused=True,
        rng_origin=contract['rng_origin'], exact_resident_continuity_claimed=False,
        historical_generation_or_tool_reexecution=False, no_automatic_retry=True,
        hard_end_unix=contract['hard_end_unix'], started_unix=started,
        recovery_checkpoint_directory=str(destination))
    completion_reference = None
    try:
        _write_once(attempt / 'STARTED.json', accounting)
        check_wall()
        journal.record('INTERRUPTED_SLEEP_RESTART', accounting)
        child = native.NativeChild(deepcopy(plan), deepcopy(durable))
        require(child.optimizer_steps == contract['durable_optimizer_steps']
            and child.adapter_hash() == durable['adapter_state_sha256'], 'restored_durable_child')
        check_wall()
        receipt = child.sleep(deepcopy(stream.pending_rows()),
            deepcopy(stream.rows[:stream.sleep_frontier]), anchors, recorder)
        recorder.verify_finished(child, receipt)
        require(stream.checkpoint() == contract['preserved_state'], 'pending_state_preserved_during_sleep')
        check_wall()
        checkpoint = child.checkpoint(destination)
        _committed_checkpoint(native, checkpoint, destination)
        require(checkpoint['experiment'] == stream.experiment
            and checkpoint['base_sha256'] == durable['base_sha256']
            and checkpoint['optimizer_steps'] == child.optimizer_steps
            and checkpoint['adapter_state_sha256'] == receipt['after_adapter_sha256'],
            'completed_checkpoint_matches_recovery_compute')
        check_wall()
        finished_accounting = dict(accounting, recovery_recorded_updates=len(recorder.references),
            recovery_optimizer_steps=receipt['optimizer_steps'],
            recovery_first_update=recorder.references[0], recovery_last_update=recorder.references[-1],
            finished_unix=clock(), elapsed_recovery_seconds=clock() - started)
        receipt = dict(deepcopy(receipt), status='COMPLETE',
            new_row_sha256=contract['pending_row_sha256'], checkpoint=checkpoint,
            checkpoint_sha256=checkpoint['checkpoint_sha256'], cycle=contract['pending_cycle'],
            interrupted_sleep_restart=finished_accounting)

        def publish_complete(kind, document):
            nonlocal completion_reference
            check_wall()
            require(kind == 'SLEEP_COMPLETE', 'only_original_completion_transition')
            completion_reference = journal.record(kind, document)

        stream.pending = None
        stream.commit_sleep(receipt, publish_complete)
        require(journal.latest_checkpoint() == dict(document=stream.checkpoint(),
            expected_sha256=stream.checkpoint()['sha256']), 'published_completion_is_authoritative')
        result = dict(status='COMPLETE_FULL_PENDING_SLEEP_RESTART', accounting=finished_accounting,
            complete_reference=completion_reference, checkpoint=checkpoint,
            stream_state=stream.checkpoint(), paired_LEARN_published=False)
        _write_once(attempt / 'COMPLETED.json', dict(status=result['status'],
            accounting=finished_accounting, complete_reference=completion_reference,
            final_stream_sha256=result['stream_state']['sha256']))
        return result
    except BaseException as error:
        failure = dict(status='FAILED_OR_UNKNOWN_NO_AUTOMATIC_RETRY',
            candidate_sha256=expected_sha256, attempt_key=attempt_key,
            error_type=type(error).__name__, recovery_recorded_updates=len(recorder.references),
            actual_recovery_compute_not_fully_known=True,
            complete_reference_if_returned=completion_reference,
            checkpoint_or_partial_must_not_be_promoted=True)
        try:
            _write_once(attempt / 'FAILED_OR_UNKNOWN.json', failure)
        except BaseException:
            pass
        raise


if __name__ == '__main__':
    raise SystemExit('OFFLINE CANDIDATE ONLY: no installed original admission/launch integration')
