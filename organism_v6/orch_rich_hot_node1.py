"""Node1's frozen high-budget raw supply, reusing the tested node2 prompts."""

from datetime import datetime, timezone

from organism_v6 import orch_rich_hot_node2 as source


CONDITIONS = source.CONDITIONS
CAP = 8192
CONTEXT = 16384
SECONDS = 12 * 3600
MAX_CALLS = 24576
HOST_SHA256 = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
LEASE_END = datetime(2026, 9, 19, tzinfo=timezone.utc).timestamp()
LEASE_MARGIN = 6 * 3600
UUIDS = ('GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d', 'GPU-4b071167-a06a-773c-f947-60cb8c2f7512',
         'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14',
         'GPU-f83fb491-34ce-4176-5852-c94652151a9f', 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30',
         'GPU-06b31c8f-7a96-d812-23f3-df3444d95397', 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98')
MINORS = (3, 2, 1, 0, 7, 6, 5, 4)
SOURCE_SHA = source.SOURCE_SHA
INITIAL_STATE = source.INITIAL_STATE
messages = source.messages
outcome = source.outcome
require = source.require


def allocation(index):
    require(type(index) is int and index in range(8), 'owned_node1_indices_only')
    return CONDITIONS[index // 2], index % 2


def deadline(started):
    result = min(started + SECONDS, LEASE_END - LEASE_MARGIN)
    require(result - started > 600, 'insufficient_verified_lease_margin')
    return result


def protocol():
    task = dict(question='TASK_PLACEHOLDER')
    return dict(schema='ORCH_RICH_HOT_NODE1_V1', conditions=list(CONDITIONS),
        max_new_tokens=CAP, context=CONTEXT, maximum_calls=MAX_CALLS,
        maximum_seconds=SECONDS, maximum_assigned_gpu_hours=96,
        batch_size=512, maximum_batches=8, continuation='prospectively_frozen_next_batch_same_ledger_clock',
        second_pass_conditions=['TWO_PASS', 'META_EVALUATE'], second_pass='own_first_pass_even_if_incorrect',
        prompts={condition: messages(task, condition) for condition in CONDITIONS},
        second_prompts={condition: messages(task, condition, 'OWN_RESPONSE_PLACEHOLDER')
                        for condition in ('TWO_PASS', 'META_EVALUATE')},
        review_blocks_calls=False, admitted_rows=0, fits=0, updates=0,
        lease_end_utc='2026-09-19T00:00:00+00:00', lease_margin_seconds=LEASE_MARGIN,
        host_sha256=HOST_SHA256, uuid_by_index=list(UUIDS), minor_by_index=list(MINORS),
        claim='RAW_TRAIN_SUPPLY_NOT_SEMANTIC_QUALIFICATION_OR_LEARNING')
