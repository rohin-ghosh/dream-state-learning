"""Matched odd-roster checkpoint-derived raw supply, never an improvement claim."""

from organism_v6 import orch_rich_hot_node2_floor98 as comparator


MAX_CALLS = 8192
CALLS_PER_SHARD = 8192
MAX_BATCHES = comparator.MAX_BATCHES
TASKS_PER_BATCH = comparator.TASKS_PER_BATCH
CLASSIFICATION = 'CHECKPOINT_DERIVED_NOT_IMPROVED'


def task_at(document, batch, position):
    if position % 2 or not 0 <= position < TASKS_PER_BATCH:
        raise ValueError('physical0_even_cursor_required')
    task = comparator.task_at(document, batch, position + 1)
    return dict(task, comparator_physical_gpu=1, comparator_task_id=task['id'])


messages = comparator.messages
outcome = comparator.outcome
route_task = comparator.route_task


def validate_handoff(handoff, commit, commit_sha256):
    metadata = commit['metadata']
    if (handoff['schema'] != 'COMBINED_CONTINUAL_FULL_CHILD_READY_V1'
            or handoff['status'] != 'DURABLE_CHECKPOINT_HELD_SCORES_NOT_REQUIRED'
            or '/FULL/checkpoints/' not in handoff['checkpoint']
            or handoff['updates'] <= 0 or metadata['update'] != handoff['updates']
            or metadata['adapter'] != handoff['adapter']
            or handoff['commit_sha256'] != commit_sha256
            or metadata['corpus_sha256'] != handoff['corpus_sha256']
            or handoff['parent_present'] is not False):
        raise ValueError('exact_saved_continual_FULL_required')
    return metadata
