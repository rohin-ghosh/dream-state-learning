"""One R188 kernel0 model rollback with unchanged pending history and journal."""

import hashlib
import json
from pathlib import Path
import time


ROOT = '/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1'
ARCHIVE = '/localhome/local-rohing/orch_r188_node4_20260917t2315z/kernel0'
UUID = 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def validate_plan(plan):
    binding = plan['r188_sleep_rollback']
    require(plan['physical'] == 0 and plan['root'] == ROOT and plan['gpu_uuid'] == UUID,
        'R188_exact_kernel0_only')
    require(plan['hard_end_unix'] == 1789754400 and plan['rehearsal_presentations'] == 0
        and plan['new_presentations'] == 16 and plan['anchor_lambda'] == 0.25,
        'R188_same_wall_new_only_recipe')
    require(binding['schema'] == 'R188_KERNEL0_SAVED40_ROLLBACK_V1'
        and binding['archive_root'] == ARCHIVE and binding['saved_cycle'] == 40
        and binding['saved_optimizer_steps'] == 4207 and binding['uncertain_inflight_update'] is True,
        'R188_exact_saved_rollback_not_exact_inflight_continuation')
    require(binding['discarded_logged_updates'] > 0 and binding['discarded_steps'][0] == 4208
        and binding['discarded_steps'][-1] - 4207 == binding['discarded_logged_updates'],
        'R188_exact_logged_discard_range')
    return binding


def validate_runtime(plan, stream, journal, child):
    binding = validate_plan(plan)
    archive = Path(ARCHIVE)
    require(sha(archive / 'ARCHIVED.json') == binding['archive_receipt_sha256']
        and sha(archive / 'STOPPED.json') == binding['stop_receipt_sha256'], 'R188_archive_and_stop_pins')
    require(sha(binding['checkpoint_path']) == binding['checkpoint_sha256'], 'R188_saved_model_commit')
    checkpoint = read(binding['checkpoint_path'])
    require(child.optimizer_steps == checkpoint['optimizer_steps'] == 4207
        and child.adapter_hash() == checkpoint['adapter_state_sha256'], 'R188_restored_saved_adapter_optimizer')
    require(journal.latest_checkpoint()['expected_sha256'] == binding['pending_state_sha256']
        and isinstance(stream.pending, str) and stream.pending.startswith('sleep:')
        and len(stream.rows) == binding['rows'] and stream.sleep_frontier == binding['sleep_frontier'],
        'R188_pending_waking_suffix_preserved_no_generation_replay')
    require(stream.presentation == dict(version=plan['presentation_version'],
        system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
        and stream.context_limit == plan['context_limit'], 'R188_no_pending_presentation_change')
    require(sha(Path(ROOT) / 'stream/records' / binding['head_file']) == binding['head_file_sha256'],
        'R188_original_logged_update_head_preserved')
    return binding


def record_rollback(child, stream, journal, binding):
    require(binding == child.plan['r188_sleep_rollback'], 'R188_exact_plan_binding')
    binding = validate_runtime(child.plan, stream, journal, child)
    once = Path(ARCHIVE) / 'ROLLBACK_CONSUMED'
    once.mkdir()
    receipt = dict(schema=binding['schema'], saved_cycle=40, restored_optimizer_steps=4207,
        discarded_logged_updates=binding['discarded_logged_updates'], discarded_steps=binding['discarded_steps'],
        uncertain_inflight_update=True, exact_inflight_continuation=False,
        RNG='restored_last_COMPLETE_not_post_generation_or_interrupted_sleep',
        waking_history_and_inbox_preserved=True, consumed_generation_replayed=False,
        original_records_removed=0, archive_root=ARCHIVE, observed_unix=time.time())
    journal.record('R188_AUTHORIZED_SLEEP_ROLLBACK', receipt)
    with (once / 'RECEIPT.json').open('x') as output:
        json.dump(receipt, output, sort_keys=True, indent=2, allow_nan=False)


def patch_native(source):
    replacements = [
        ("                    and isinstance(plan.get('preupdate_recovery'), dict))",
         "                    and (isinstance(plan.get('preupdate_recovery'), dict)\n                    or isinstance(plan.get('r188_sleep_rollback'), dict)))"),
        ("                if recovering:\n                    from gpu.orch_r138_kernel_recovery import recover_rng\n                    recover_rng(child, stream, journal, plan['preupdate_recovery'])",
         "                if recovering:\n                    if plan.get('r188_sleep_rollback') is not None:\n                        from gpu.orch_r188_node4_sleep_rollback import record_rollback\n                        record_rollback(child, stream, journal, plan['r188_sleep_rollback'])\n                    else:\n                        from gpu.orch_r138_kernel_recovery import recover_rng\n                        recover_rng(child, stream, journal, plan['preupdate_recovery'])"),
        ("    return plan\n", "    if plan.get('r188_sleep_rollback') is not None:\n        from gpu.orch_r188_node4_sleep_rollback import validate_plan as validate_rollback\n        validate_rollback(plan)\n    return plan\n"),
    ]
    patched = source
    for before, after in replacements:
        require(patched.count(before) == 1, 'R188_unique_actual_native_seam')
        patched = patched.replace(before, after, 1)
    restored = patched
    for before, after in reversed(replacements):
        restored = restored.replace(after, before, 1)
    require(restored == source, 'R188_all_other_native_bytes_unchanged')
    compile(patched, '<R188_exact_kernel0_native>', 'exec')
    return patched
