"""Rolling V2 inherits the existing node1 allocation, cohort, clock and budget."""

from organism_v6 import orch_rich_hot_node1 as previous
from organism_v6 import orch_rich_hot_node1_prompt_v2 as prompts


CONDITIONS = previous.CONDITIONS
CAP = previous.CAP
CONTEXT = previous.CONTEXT
SECONDS = previous.SECONDS
MAX_CALLS = previous.MAX_CALLS
UUIDS = previous.UUIDS
MINORS = previous.MINORS
LEASE_END = previous.LEASE_END
LEASE_MARGIN = previous.LEASE_MARGIN
HOST_SHA256 = previous.HOST_SHA256
SOURCE_SHA = previous.SOURCE_SHA
INITIAL_STATE = previous.INITIAL_STATE
VERSION = prompts.VERSION
source = previous.source
require = previous.require
allocation = previous.allocation
deadline = previous.deadline
messages = prompts.messages
outcome = prompts.outcome


def protocol():
    result = previous.protocol()
    task = dict(question='TASK_PLACEHOLDER')
    result.update(schema=VERSION, phase_version=VERSION,
        prompts={condition: messages(task, condition) for condition in CONDITIONS},
        second_prompts={condition: messages(task, condition, 'OWN_RESPONSE_PLACEHOLDER')
                        for condition in ('TWO_PASS', 'META_EVALUATE')},
        rolling='one_gpu_at_a_time_at_complete_task_boundary',
        inherit_original_global_ledger_and_deadline=True, regenerate_seen_tasks=False,
        semantic_review=prompts.review_contract())
    return result
