"""Non-material R141 PUBLIC TRAIN interface repair; CPU-only preparation CLI."""

import argparse
import ast
import json
from pathlib import Path
from types import FunctionType

from gpu import orch_r133_code_feedback_collection as frozen


SCHEMA = 'R141_PUBLIC_TRAIN_CODE_INTERFACE_V1'
PURPOSE = 'EXPLORATORY_INTERFACE_REPAIR_CONTROL'
FORMAT_EXAMPLE = '{"expression":"EXPRESSION_TEXT"}'
FORMAT_CONTRACT = (
    '\nOutput serialization reminder (format only, not a solution): '
    + FORMAT_EXAMPLE + '. EXPRESSION_TEXT is a non-executable placeholder, '
    'not code to submit. Replace it with your expression text INSIDE the JSON '
    'double quotes. The expression is a JSON string, not an unquoted expression '
    'or an evaluated result. Escape any characters as required for a JSON string. '
    'This example supplies no helper, composition, task constant or expected answer.'
)
MODELS, STAGES = frozen.MODELS, frozen.STAGES
TASK_COUNT, CALL_CAP = frozen.TASK_COUNT, frozen.CALL_CAP
MAX_NEW_TOKENS, CONTEXT_LIMIT = frozen.MAX_NEW_TOKENS, frozen.CONTEXT_LIMIT
require, digest, sha, read, write = frozen.require, frozen.digest, frozen.sha, frozen.read, frozen.write
parse_expression, evaluate, verify = frozen.parse_expression, frozen.evaluate, frozen.verify
execute_public, readonly_model = frozen.execute_public, frozen.readonly_model
SOURCE_FILES = frozen.SOURCE_FILES + (
    'gpu/orch_r133_code_feedback_guard.py',
    'tests/test_orch_r133_code_feedback_guard.py',
    'gpu/orch_r141_code_interface.py',
    'gpu/orch_r141_code_interface_guard.py',
    'tests/test_orch_r141_code_interface.py',
    'tests/test_orch_r141_code_interface_guard.py',
)
FROZEN_SOURCE_SHA256 = {
    'gpu/astra_experienced_event_microloop.py': '8e57909a6c4f2d988a434423a33e7a663c23696ffdb2ce402c2bb03b2fccbb70',
    'gpu/astra_pchain2_native.py': '7fc071bf8d614eb2374d812f23e4488a0a719f5f7eafa1ee39f350d81fc4165d',
    'gpu/orch_guided_native.py': '559d8e6ea7002f2651748ba192a57c5cf627381f6a3994d93cb02d63011a3157',
    'gpu/orch_r109_l1_public_feedback.py': '7460e322ddf5b09a96f1fb4a9dde78f4c0d21fb48109eac1810dcb6791abea82',
    'gpu/orch_r119_public_feedback.py': 'c109057608b66879f11f3661a6b17d2fc479fd10acc03f4dfea65cedd15743ba',
    'gpu/orch_r133_code_feedback_collection.py': '79b93767ed022c4aebb91f3d6aada480998effe2a07331e86ad59c5ad56dd4dd',
    'gpu/orch_r133_code_feedback_guard.py': '094fe8dfc80f51d0048bf12d3b998f9393d1b5ef981a9082cdf28af5523d8261',
    'gpu/orch_rich_hot_node2_exhaustion_v3.py': 'a9fc096b66a1fe185f84c15d50f049ce9da8e146fa8dab014c85f2bdda36b28e',
    'organism_v6/orch_guided_bridge.py': 'f7915100d7c9e5b171b8e3bc9af23e6cee00fc09612bb947d5e3c1ea777ee652',
    'organism_v6/orch_persist_code.py': '2f4a15f4538f707391716cb89d594a292278ed036572386a5dbed340a2db81a2',
    'organism_v6/orch_rich_hot_node2_exhaustion_v3.py': 'da0fcbebecefcc53ca79833edad1717cc616d0d4cba9b6e6f2e28f17cda77a82',
    'organism_v6/pcfl_vertical_train.py': '9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078',
    'tests/test_orch_r133_code_feedback_collection.py': '139db9ad31f3ab387d72bcbeafd5fd07705d7f44dc75d93a302422176c58157b',
    'tests/test_orch_r133_code_feedback_guard.py': '16e87c840dfd97dd6b1a7ca58a3243da723c0ae70f9b560ab4fdb75eb0db3f22',
}


def build_tasks(seed, inventory=None):
    require(type(inventory) is dict, 'Main_hash_only_exclusions_required_no_preview')
    return frozen.build_tasks(seed, inventory)


def messages(task, stage='draft', draft=None, feedback=None):
    result = frozen.messages(task, stage, draft, feedback)
    result[0]['content'] += FORMAT_CONTRACT
    return result


def response_metrics(task, response):
    raw = response['raw']
    complete = response['terminal'] and not response['truncated']
    result = dict(complete=complete, raw_sha256=digest(raw), format_valid=False,
                  safe_expression=False, semantic_correct=None,
                  strict_success=verify(task, raw), eligible_success=False)
    try:
        expression = parse_expression(raw)
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return result
    result['format_valid'] = True
    result['expression_sha256'] = digest(expression)
    try:
        tree = frozen.ledger.validate_expression(expression)
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return result
    result['safe_expression'] = True
    result['expression_ast_sha256'] = digest(ast.dump(tree, include_attributes=False))
    result['semantic_correct'] = result['strict_success']
    result['eligible_success'] = bool(complete and result['strict_success'])
    return result


def correction(task, before, after):
    first, last = response_metrics(task, before), response_metrics(task, after)
    both_formatted = first['format_valid'] and last['format_valid']
    both_safe = first['safe_expression'] and last['safe_expression']
    complete = first['complete'] and last['complete']
    return dict(before=first, after=last, complete_pair=complete,
                raw_changed=before['raw'] != after['raw'],
                expression_text_changed=(first['expression_sha256'] != last['expression_sha256'])
                if both_formatted else None,
                expression_ast_changed=(first['expression_ast_sha256'] != last['expression_ast_sha256'])
                if both_safe else None,
                format_recovered=bool(complete and not first['format_valid'] and last['format_valid']),
                failed_to_passed=bool(complete and not first['strict_success'] and last['strict_success']),
                semantic_correction=bool(complete and both_safe
                                         and not first['semantic_correct'] and last['semantic_correct']),
                rows_admitted=0, fit_updates=0, persistence_claim=False,
                metacognition_claim=False, four_way_benchmark=False)


def source_hashes():
    repository = Path(__file__).resolve().parents[1]
    actual = {name: sha(repository / name) for name in SOURCE_FILES}
    require(all(actual[name] == expected for name, expected in FROZEN_SOURCE_SHA256.items()),
            'exact_R136_frozen_producer_helpers_guard_required')
    return actual


def prepare(root, seed, inventory=None):
    source_hashes()
    return _prepare(root, seed, inventory)


def verified(root, require_launchable=False):
    plan, tasks = _verified(root, require_launchable=True)
    require(read(Path(root) / 'TASKS.json')['schema'] == SCHEMA, 'R141_tasks_envelope_required')
    return plan, tasks


def run_episodes(root, tasks, generate, check=lambda label: None):
    _, prepared = verified(root, require_launchable=True)
    require(tasks == prepared, 'only_exact_fresh_R141_prepared_tasks')
    return _run_episodes(root, tasks, generate, check)


_namespace = dict(frozen.__dict__, SCHEMA=SCHEMA, build_tasks=build_tasks,
                  messages=messages, correction=correction, source_hashes=source_hashes,
                  verified=verified, run_episodes=run_episodes)
_prepare = FunctionType(frozen.prepare.__code__, _namespace, 'prepare', frozen.prepare.__defaults__)
_verified = FunctionType(frozen.verified.__code__, _namespace, 'verified', frozen.verified.__defaults__)
_run_episodes = FunctionType(frozen.run_episodes.__code__, _namespace, 'run_episodes',
                           frozen.run_episodes.__defaults__)
collect = FunctionType(frozen.collect.__code__, _namespace, 'collect')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--seed')
    parser.add_argument('--exclusions', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        require(args.exclusions is not None, 'Main_hash_only_exclusions_required_no_preview')
        plan = prepare(args.root, args.seed, read(args.exclusions))
    else:
        plan, _ = verified(args.root)
    print(json.dumps(dict(status=plan['status'], purpose=PURPOSE, tasks=TASK_COUNT,
                          native_call_cap=CALL_CAP, gpu_reserved=False, gpu_launched=False,
                          fit_updates=0, four_way_benchmark=False), sort_keys=True))


if __name__ == '__main__':
    main()
