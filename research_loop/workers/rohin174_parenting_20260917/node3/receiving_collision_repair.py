"""Nonmaterial response-clock attempt naming repair; preserve the original ledger."""

import argparse
import ast
import importlib
import inspect
import json
from pathlib import Path

import receiving_parent as receiver


def response_named_tick(original):
    tree = ast.parse(inspect.getsource(original))
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant)
        and node.left.value == 'parent_%012d'
        and ast.dump(node.right) == ast.dump(ast.parse("state['request_count']", mode='eval').body)]
    formatted = [node for node in ast.walk(tree) if isinstance(node, ast.JoinedStr)
        and len(node.values) == 2 and isinstance(node.values[0], ast.Constant)
        and node.values[0].value == 'parent_' and isinstance(node.values[1], ast.FormattedValue)
        and ast.dump(node.values[1].value) == ast.dump(ast.parse("state['request_count']", mode='eval').body)]
    receiver.base.require(len(matches) + len(formatted) == 1, 'one_request_keyed_attempt_name')
    if matches:
        matches[0].left.value = 'parent_%012d_response_%012d'
        matches[0].right = ast.parse("(state['request_count'], state['response_count'])", mode='eval').body
    else:
        formatted[0].values.extend(ast.parse("f\"_response_{state['response_count']:012d}\"", mode='eval').body.values)
    namespace = dict(original.__globals__)
    exec(compile(ast.fix_missing_locations(tree), __file__, 'exec'), namespace)
    return namespace[original.__name__]


def install(original_runtime):
    def runtime(physical, config_path):
        result = original_runtime(physical, config_path)
        policy = importlib.import_module('gpu.orch_r166_parent_policy')
        response_tick = inspect.getclosurevars(policy.tick).nonlocals['original_tick']
        cells = dict(zip(response_tick.__code__.co_freevars, response_tick.__closure__))
        previous = cells['strict_tick'].cell_contents
        replacement = response_named_tick(previous)
        receiver.base.require(replacement.__globals__['prompt'] is policy.prompt, 'same_actual_prompt')
        cells['strict_tick'].cell_contents = replacement
        return result

    return runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'serve'))
    arguments = parser.parse_args()
    receiver.STATE = receiver.STATE / 'support_collision_repair_v1'
    receiver.effort.runtime = install(receiver.effort.runtime)
    result = receiver.serve(0, preflight=arguments.action == 'preflight')
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
