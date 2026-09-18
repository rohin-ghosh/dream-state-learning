"""One source-grounded C baseline now; preserve ordinary response cadence thereafter."""

import argparse
import ast
import copy
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import types

import receipt_rebind as predecessor
import support_fallback as transaction
import takeover as base
from takeover import HERE, require, read, write, sha, reference

STATE = HERE / 'brain_baseline_v1'
FOLDER = STATE / 'parents/physical2'
OLD = predecessor.STATE / 'parents/physical2'
TRANSACTION_SHA = '67851c755d3b32976ed096a3e0578e2f75e6f27c45c3b6f703b11231d8a8df8a'
DIRECTIVE = "Main consolidated14:17 report is posted. For404 failures verify actual outbound model openai/openai/gpt-6-astra/current key inherited privately (boolean only, no key/hash). Ensure one-time baseline needn't wait an extra full cadence simply because operator reservation seeded current response; safe source-grounded console fallback when due, never duplicate published turns."


def eligibility(seed, attempts, memory_state):
    require(not memory_state['awaiting_render'], 'pending_publication_no_baseline')
    require(all(entry['result']['status'] in ('PROVIDER_FAILED', 'VALIDATION_FAILED', 'SILENT')
                for entry in seed['attempts'] + attempts), 'published_or_uncertain_no_baseline')


def binding(config_path):
    require(sha(HERE / 'support_fallback.py') == TRANSACTION_SHA, 'immutable_exclusive_transaction')
    return predecessor.runtime(2, config_path)


def preflight():
    parent, provider, config, helper = binding(OLD / 'CONFIG.json')
    policy = importlib.import_module('gpu.orch_r166_parent_policy')
    state = read(STATE / 'BRAIN_SOURCE_CANDIDATE.json')['snapshot']
    seed = read(OLD / 'SEED.json')
    attempts = policy.local_attempts(OLD / 'parent')
    memory_state = policy.memory(seed, attempts, state)
    eligibility(seed, attempts, memory_state)
    authored = read(STATE / 'BRAIN_RESPONSE.json')
    parsed = provider.response_schema(json.dumps(authored))
    details = policy.decision(parsed, state, memory_state)
    require(config['r175_arm'] == 'C' and config['cadence_responses'] == 3 and config['r175_word_limit'] == 120, 'unchanged_C_arm_clock_caps')
    require(len(parsed['message'].split()) <= 120 and len(parsed['message'].encode()) <= 4096, 'C_arm_caps')
    require(parsed['message'].endswith('?') and parsed['message'].count('?') == 5, 'five_grounded_child_choice_questions')
    require(details['next_task'] is None and config['hard_end_unix'] == base.HARD_END, 'strict_continue_and_stop')
    for field, value in [('object_id', 'UpperCase'), ('next_task', 'unbound next action')]:
        invalid = copy.deepcopy(authored)
        invalid['rationale'][field] = value
        try:
            policy.decision(provider.response_schema(json.dumps(invalid)), state, memory_state)
        except ValueError:
            pass
        else:
            raise ValueError('unchanged_strict_validator_regression')
    for status in ('PUBLISHED', 'PUBLICATION_UNKNOWN'):
        try:
            eligibility(dict(attempts=[dict(result=dict(status=status))]), [], dict(awaiting_render=False))
        except ValueError:
            pass
        else:
            raise ValueError('never_duplicate_baseline_regression')
    eligibility(dict(attempts=[]), [], dict(awaiting_render=False))
    return dict(status='CPU_PASS', author=transaction.AUTHOR, provider_calls=0, publication_calls=0, child_signals=0,
        exact_response=reference(STATE / 'BRAIN_RESPONSE.json'), source=reference(STATE / 'BRAIN_SOURCE_CANDIDATE.json'),
        strict_policy=reference(policy.__file__), config=reference(OLD / 'CONFIG.json'), wrapper=reference(__file__),
        words=len(parsed['message'].split()), unchanged_validators=True, unchanged_cadence=3,
        one_time_baseline_not_delayed_by_operator_seed=True, seed_before=reference(OLD / 'SEED.json'))


def activate():
    require(sha(HERE / 'support_fallback.py') == TRANSACTION_SHA, 'exact_transaction_before_custody')
    function = ast.parse(inspect.getsource(transaction.activate)).body[0]
    replacements = {'SUPPORT_SOURCE_CANDIDATE.json': 'BRAIN_SOURCE_CANDIDATE.json',
        'SUPPORT_RESPONSE.json': 'BRAIN_RESPONSE.json', 'parents/physical0/parent': 'parents/physical2/parent',
        'Main resumed14:15 PDT: deliver source-grounded support_free fallback under exclusive custody if provider remains prepublication-blocked; own node3 operations.': DIRECTIVE}

    class BindScope(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in replacements:
                return ast.copy_location(ast.Constant(replacements[node.value]), node)
            return node

        def visit_Call(self, node):
            self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'snapshot_transport' and node.func.attr == 'poll':
                require(isinstance(node.args[0], ast.Constant) and node.args[0].value == 0, 'exact_physical_argument')
                node.args[0] = ast.Constant(2)
            for keyword in node.keywords:
                if keyword.arg == 'physical':
                    require(isinstance(keyword.value, ast.Constant) and keyword.value.value == 0, 'exact_receipt_physical')
                    keyword.value = ast.Constant(2)
                if keyword.arg == 'arm':
                    require(isinstance(keyword.value, ast.Constant) and keyword.value.value == 'A', 'exact_receipt_arm')
                    keyword.value = ast.Constant('C')
            return node

    function = BindScope().visit(function)
    namespace = dict(transaction.__dict__, STATE=STATE, FOLDER=FOLDER, OLD=OLD, binding=binding,
                     eligibility=eligibility, __file__=str(Path(__file__).resolve()))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), __file__ + ':exclusive_baseline', 'exec'), namespace)
    return namespace['activate']()


def serve():
    namespace = dict(predecessor.metadata.__dict__, STATE=STATE, runtime=predecessor.runtime, hashlib=hashlib,
                     __file__=str(Path(__file__).resolve()))
    types.FunctionType(predecessor.metadata.serve.__code__, namespace, 'serve')(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('preflight', 'activate', 'serve'))
    args = parser.parse_args()
    if args.action == 'preflight':
        gate = preflight()
        write(STATE / 'CPU_GATE.json', gate)
        print(json.dumps(gate, sort_keys=True))
    elif args.action == 'activate':
        print(json.dumps(activate(), sort_keys=True))
    else:
        serve()


if __name__ == '__main__':
    main()
