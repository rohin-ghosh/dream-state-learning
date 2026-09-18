"""Exact-block prospective patch for frozen continual-native source copies."""

import ast
from copy import deepcopy


OLD_RECEIPT = """            record('TARGET_ELIGIBILITY', dict(version=presentation['version'], excluded=exclusions,
                new_row_sha256=[row['source_sha256'] for row in new_rows],
                rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False))
"""
NEW_RECEIPT = """        from gpu.orch_r144_sleep_targets import POLICY, encode_sleep_targets
        new_rows, old_rows, encoded, rejected_targets = encode_sleep_targets(
            new_rows, old_rows, self.tokenizer, self.plan['context_limit'], encode_own)
        exclusions.extend(rejected_targets)
        record('TARGET_ELIGIBILITY', dict(version=self.plan.get('presentation_version'),
            runtime_policy=POLICY, excluded=exclusions,
            new_row_sha256=[row['source_sha256'] for row in new_rows],
            rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False))
"""
OLD_ENCODING = """        encoded = {row['source_sha256']:encode_own(row, self.tokenizer, self.plan['context_limit'])
                   for row in new_rows+old_rows}
"""


def without_sleep(tree):
    result = deepcopy(tree)
    children = [node for node in result.body if isinstance(node, ast.ClassDef)
                and node.name == 'NativeChild']
    if len(children) != 1:
        raise ValueError('exact_native_child_class_required')
    methods = [node for node in children[0].body if isinstance(node, ast.FunctionDef)
               and node.name == 'sleep']
    if len(methods) != 1:
        raise ValueError('exact_native_sleep_required')
    methods[0].body = [ast.Pass()]
    return ast.dump(result, include_attributes=False)


def patch_source(source):
    if 'orch_r144_sleep_targets' in source:
        raise ValueError('already_patched_source_not_a_new_handoff')
    if source.count(OLD_RECEIPT) != 1 or source.count(OLD_ENCODING) != 1:
        raise ValueError('unsupported_frozen_native_blocks')
    before = ast.parse(source)
    result = source.replace(OLD_RECEIPT, NEW_RECEIPT).replace(OLD_ENCODING, '')
    after = ast.parse(result)
    if without_sleep(before) != without_sleep(after):
        raise ValueError('patch_changed_non_sleep_behavior')
    compile(result, '<r144-isolated-native>', 'exec')
    return result
