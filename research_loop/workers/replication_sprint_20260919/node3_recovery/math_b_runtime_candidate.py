"""Offline original-sleep kernel for math B; no launcher or journal repair."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

import pending_sleep_contract as preparation
from recovery_primitives import (
    RecoveryRecorder, _committed_checkpoint, _sync_directory, _write_once,
)


SCHEMA = 'NODE3_MATH_B_FULL_PENDING_SLEEP_RUNTIME_CANDIDATE_V1'
require = preparation.require
digest = preparation.digest
FAST_AUDIT_POLICY = 'ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY'


def prepare_candidate(complete, pending, suffix, *, plan_bytes, expected_plan_sha256):
    prepared = preparation.prepare(complete, pending, suffix, life='r213_math_b_fork',
        plan_bytes=plan_bytes, expected_plan_sha256=expected_plan_sha256)
    original = prepared['contract']
    require(original['diagnostic_records'] == [], 'math_B_original_plain_sleep_only')
    contract = dict(deepcopy(original), checkpoint_sha256=deepcopy(
        original['durable_checkpoint']['checkpoint_sha256']), new_presentations=16,
        durable_optimizer_steps=original['recovery_optimizer_start'],
        recorded_uncheckpointed_updates=original['recorded_unsaved_updates'])
    attempt_key = digest(dict(life=contract['life'], journal_id=contract['journal_id'],
        pending_sleep=contract['pending_sleep']))
    candidate = dict(schema=SCHEMA, source_contract_sha256=prepared['sha256'],
        contract=dict(contract=contract, sha256=digest(contract)),
        durable_checkpoint=deepcopy(original['durable_checkpoint']),
        recipe=deepcopy(suffix[0]['document']), eligibility=deepcopy(suffix[1]['document']),
        original_plan_sha256=expected_plan_sha256, attempt_key=attempt_key,
        checkpoint_name=f'sleep_{contract["pending_cycle"]:06d}_restart_{attempt_key}',
        execution_authorized=False)
    return dict(candidate=candidate, sha256=digest(candidate))


def finish_pending_sleep(envelope, *, expected_sha256, native, journal,
                         plan_bytes, anchor_factory, clock=time.time, execution_plan=None):
    """Execute only inside a future freshly admitted original confined driver.

    The supplied journal must already hold its exclusive writer lock, preserve
    the same stream, and implement an original checkpoint+tail fast audit.
    No full-history audit, generation, tool, compaction, or provider is called.
    """
    candidate = deepcopy(envelope['candidate'])
    require(envelope['sha256'] == expected_sha256 == digest(candidate), 'pinned_candidate')
    require(candidate['schema'] == SCHEMA and candidate['execution_authorized'] is False,
        'uninstalled_candidate_only')
    prepared = candidate['contract']
    contract = prepared['contract']
    require(prepared['sha256'] == digest(contract) and contract['execution_authorized'] is False
        and contract['life'] == 'r213_math_b_fork', 'bound_math_B_candidate')
    require(hashlib.sha256(plan_bytes).hexdigest() == candidate['original_plan_sha256'],
        'unchanged_original_plan_bytes')
    plan = json.loads(plan_bytes)
    if execution_plan is not None:
        allowed = dict(plan, source_root=execution_plan['source_root'])
        require(execution_plan == allowed, 'only_staged_source_location_may_change')
        require(Path(execution_plan['source_root']).is_absolute(), 'absolute_staged_source')
        plan = deepcopy(execution_plan)
    require(plan['hard_end_unix'] == contract['hard_end_unix'] == preparation.HARD_END,
        'original_deadline_unchanged')

    def check_wall():
        require(clock() < contract['hard_end_unix'], 'original_hard_end_expired')

    check_wall()
    root = Path(plan['root'])
    attempt_key = digest(dict(life=contract['life'], journal_id=contract['journal_id'],
        pending_sleep=contract['pending_sleep']))
    require(candidate['attempt_key'] == attempt_key and candidate['checkpoint_name']
        == f'sleep_{contract["pending_cycle"]:06d}_restart_{attempt_key}', 'stable_attempt_identity')
    destination = root / 'checkpoints' / candidate['checkpoint_name']
    attempts = root / 'interrupted_sleep_restarts'
    require(not attempts.is_symlink() and not (root / 'checkpoints').is_symlink(),
        'no_redirected_new_namespaces')
    require(not os.path.lexists(destination), 'never_overwrite_or_adopt_checkpoint')
    require(not os.path.lexists(attempts / attempt_key), 'consumed_attempt_no_retry')
    audit = journal.checkpoint_tail_audit()
    require(audit['record_count'] == contract['old_head']['index'] + 1
        and audit['head_sha256'] == contract['old_head']['sha256']
        and audit['prefix_work'] == FAST_AUDIT_POLICY and audit['pending_preserved'] is True,
        'fresh_verified_checkpoint_tail_not_fullstream_replay')
    require(journal.latest_checkpoint() == dict(document=contract['preserved_state'],
        expected_sha256=contract['preserved_state']['sha256']), 'exact_pending_stream_required')
    stream = native.ContinualStream.restore(contract['preserved_state'],
        expected_sha256=contract['preserved_state']['sha256'])
    require(stream.checkpoint() == contract['preserved_state'], 'lossless_pending_restore')
    native.verify_experiment_resume(plan, stream.experiment)
    durable = candidate['durable_checkpoint']
    require(durable['checkpoint_sha256'] == contract['checkpoint_sha256']
        and durable['optimizer_steps'] == contract['durable_optimizer_steps']
        and durable['experiment'] == stream.experiment, 'durable_not_unsaved_checkpoint')
    directory = Path(durable['adapter_path']).parent
    require(directory == root / 'checkpoints' / f'sleep_{contract["pending_cycle"] - 1:06d}',
        'last_durable_sleep_only')
    _committed_checkpoint(native, durable, directory)
    attempts.mkdir(exist_ok=True)
    _sync_directory(root)
    attempt = attempts / attempt_key
    attempt.mkdir(exist_ok=False)
    _sync_directory(attempts)
    accounting = dict(schema=SCHEMA, candidate_sha256=expected_sha256,
        pending_sleep=contract['pending_sleep'], old_head=contract['old_head'],
        complete=contract['complete'], started_unix=clock(),
        recorded_unsaved_updates=contract['recorded_unsaved_updates'],
        full_new_updates_required=48, rng_origin=contract['rng_origin'],
        exact_resident_continuity_claimed=False, historical_generation_or_tool_reexecution=False,
        no_automatic_retry=True, recovery_checkpoint_directory=str(destination))
    completion = None
    learned = None
    try:
        _write_once(attempt / 'STARTED.json', accounting)
        check_wall()
        journal.record('INTERRUPTED_SLEEP_RESTART', accounting)
        child = native.NativeChild(deepcopy(plan), deepcopy(durable))
        require(child.optimizer_steps == contract['durable_optimizer_steps']
            and child.adapter_hash() == durable['adapter_state_sha256'], 'restored_durable_child')
        anchors = anchor_factory(child)
        recorder = RecoveryRecorder(candidate, journal, check_wall)
        receipt = child.sleep(deepcopy(stream.pending_rows()),
            deepcopy(stream.rows[:stream.sleep_frontier]), anchors, recorder)
        recorder.verify_finished(child, receipt)
        require(stream.checkpoint() == contract['preserved_state'], 'pending_preserved_during_sleep')
        check_wall()
        checkpoint = child.checkpoint(destination)
        _committed_checkpoint(native, checkpoint, destination)
        require(checkpoint['experiment'] == stream.experiment
            and checkpoint['base_sha256'] == durable['base_sha256']
            and checkpoint['optimizer_steps'] == child.optimizer_steps
            and checkpoint['adapter_state_sha256'] == receipt['after_adapter_sha256'],
            'new_commit_matches_recovery_compute')
        accounting = dict(accounting, recovery_updates=len(recorder.references),
            recovery_start_steps=contract['durable_optimizer_steps'],
            recovery_end_steps=child.optimizer_steps, finished_unix=clock())
        receipt = dict(deepcopy(receipt), status='COMPLETE',
            new_row_sha256=contract['pending_row_sha256'], checkpoint=checkpoint,
            checkpoint_sha256=checkpoint['checkpoint_sha256'], cycle=contract['pending_cycle'],
            interrupted_sleep_restart=accounting)

        def publish_complete(kind, document):
            nonlocal completion
            check_wall()
            require(kind == 'SLEEP_COMPLETE', 'only_original_completion_transition')
            completion = journal.record(kind, document)

        stream.pending = None
        stream.commit_sleep(receipt, publish_complete)
        require(journal.latest_checkpoint() == dict(document=stream.checkpoint(),
            expected_sha256=stream.checkpoint()['sha256']), 'published_complete_is_authoritative')
        learned = journal.record('R184_LEARN_COMPLETE', dict(cycle=contract['pending_cycle'],
            state_revision=stream.history.working_state['revision'],
            working_state=stream.history.working_state, checkpoint=checkpoint,
            parent_required_for_next_cycle=False))
        _write_once(attempt / 'COMPLETED.json', dict(accounting=accounting,
            complete=completion, paired_LEARN=learned,
            final_stream_sha256=stream.checkpoint()['sha256']))
        return dict(status='FULL_PENDING_SLEEP_COMPLETE_AND_PAIRED_LEARN',
            complete=completion, paired_LEARN=learned, checkpoint=checkpoint,
            accounting=accounting, child=child, stream=stream,
            completed_sleeps=contract['pending_cycle'])
    except BaseException as error:
        failure = dict(error_type=type(error).__name__, complete=completion,
            paired_LEARN=learned, no_automatic_retry=True,
            failed_checkpoint_and_attempt_preserved=True)
        try:
            _write_once(attempt / 'FAILED.json', failure)
        except OSError:
            pass
        raise
