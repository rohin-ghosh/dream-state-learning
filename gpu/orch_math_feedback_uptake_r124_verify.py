"""Read-only paired DEV verification; exports hashes and counts, never text."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r124_readout as run


def validate_call(call, task_id, messages, checkpoint):
    run.require(call['status'] == 'COMPLETE' and call['split'] == 'DEV', 'complete_DEV_only')
    run.require(call['task_id'] == task_id and call['messages'] == messages, 'exact_ordered_task_prompt')
    run.require(len(messages) == 2 and [item['role'] for item in messages] == ['system', 'user'], 'empty_context')
    run.require(call['checkpoint'] == checkpoint, 'actual_checkpoint_binding')
    run.require(all(call[key] is True for key in ('parent_free', 'empty_context', 'never_rows_or_buffer', 'raw_saved_before_parser')), 'visibility_contract')
    response = call['response']
    run.require(isinstance(response['raw'], str) and bool(response['raw']), 'nonempty_full_text')
    run.require(response['messages'] == messages and response['input_truncated'] is False, 'unaltered_full_input')
    run.require(response['requested_generation_cap'] == response['effective_generation_cap'] == 2048, 'matched_cap')
    run.require(call['token_count'] == len(response['token_ids']) > 0, 'full_token_ID_count')
    run.require(all(type(token) is int for token in response['token_ids']), 'actual_integer_token_IDs')
    return dict(task_id=task_id, tokens=call['token_count'], characters=len(response['raw']),
        text_sha256=hashlib.sha256(response['raw'].encode()).hexdigest(),
        token_ids_sha256=run.math.policy.digest(response['token_ids']),
        terminal=response['terminal'], truncated=response['truncated'], completed_unix=call['completed_unix'])


def verify(branch):
    root = run.ROOT / branch
    plan = run.validate(root)
    request = run.control.checked(plan['probe_request'])
    prompts = run.control.checked(request['prompts'])
    tasks = run.control.checked(request['dev'])
    roles = {}
    processes = []
    for role in ('before', 'after'):
        output = root / 'paired_DEV' / role
        complete, result = run.read(output / 'COMPLETE.json'), run.read(output / 'PROCESS_RESULT.json')
        run.require(complete['completed'] == 8 and complete['parent'] == complete['optimizer_steps'] == 0, 'full_denominator_no_parent_or_training')
        run.require(result['status'] == 'COMPLETE' and result['returncode'] == 0, 'actual_successful_process_exit')
        loaded, after = run.read(output / 'LOADED.json'), run.read(output / 'AFTER.json')
        run.require(loaded['adapter'] == after['adapter'] and after['completed'] == after['planned'] == 8, 'unchanged_readonly_adapter')
        run.require(loaded['optimizer_loaded'] is False and loaded['checkpoint'] == plan['paired_checkpoints'][role], 'actual_readonly_checkpoint')
        processes.append(loaded['process'])
        paths = sorted(output.glob('CALL_*.json'))
        run.require(len(paths) == 8, 'exactly_eight_call_files')
        calls = [dict(validate_call(run.read(path), task['id'], messages, plan['paired_checkpoints'][role]),
            artifact=run.ref(path)) for path, task, messages in zip(paths, tasks, prompts)]
        roles[role] = dict(calls=calls, tokens=sum(call['tokens'] for call in calls),
            checkpoint=plan['paired_checkpoints'][role],
            receipts={name:run.ref(output / name) for name in ('BATCH.request.json', 'LOADED.json',
                'COMPLETE.json', 'PROCESS_RESULT.json', 'MOUNTED_BEFORE.json', 'AFTER.json')})
    run.require(processes[0] != processes[1], 'distinct_fresh_processes')
    before = run.checkpoint_before(Path(plan['predecessor_root']), plan['paired_sleep_cycle'], plan['paired_checkpoints']['after'])
    run.require(before == plan['paired_checkpoints']['before'], 'before_is_actual_TRAIN_source_predecessor')
    return dict(schema='R124_MATCHED_DEV_VERIFIED_V1', branch=branch, root=str(root), observed_unix=time.time(),
        plan=run.ref(root/'PLAN.json'), saved_sleep_cycle=plan['paired_sleep_cycle'],
        prompts=request['prompts'], prompt_semantic_sha256=request['prompt_semantic_sha256'],
        roles=roles, exact_text_changed=sum(left['text_sha256'] != right['text_sha256']
            for left,right in zip(roles['before']['calls'],roles['after']['calls'])),
        exact_tokens_changed=sum(left['token_ids_sha256'] != right['token_ids_sha256']
            for left,right in zip(roles['before']['calls'],roles['after']['calls'])),
        interpretation='RESPONSE_CHANGE_ONLY_NOT_IMPROVEMENT_OR_MATCHED_CONTROL_EFFECT',
        semantic_reasoning_quality='UNKNOWN_REQUIRES_AUTHOR_REVIEW',
        counters=run.read(root/'COUNTERS.json'),
        continuation={name:run.ref(root/name) for name in ('LOADED.json','OPTIMIZER_RESTORED.json') if (root/name).exists()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('branch', choices=('F2', 'A2'))
    print(json.dumps(verify(parser.parse_args().branch), sort_keys=True, indent=2))
