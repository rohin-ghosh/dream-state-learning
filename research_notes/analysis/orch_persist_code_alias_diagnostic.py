"""Posthoc CPU-only namespace diagnostic; transformed actions are never targets."""

import argparse
import ast
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_persist_code as ledger


class ReplaceHelperPlaceholder(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id == 'xs':
            return ast.copy_location(ast.Name(id='values', ctx=node.ctx), node)
        return node


def diagnose(root):
    report = dict(posthoc=True, native_calls=0, training_allowed=False,
                  claim='COUNTERFACTUAL_INTERFACE_DIAGNOSTIC_NOT_EXECUTED_SUCCESS', arms={})
    for arm in ('RICH', 'TERSE'):
        directory = root / arm
        tasks = {task['id']: task for task in json.loads((directory / 'TASKS.json').read_text())}
        rows = []
        for path in sorted(directory.glob('CALL_*.json')):
            call = json.loads(path.read_text())
            expression = call.get('action', {}).get('expression')
            if expression is None:
                continue
            try:
                tree = ast.parse(expression, mode='eval')
            except SyntaxError:
                continue
            if not any(isinstance(node, ast.Name) and node.id == 'xs' for node in ast.walk(tree)):
                continue
            modified = ast.unparse(ReplaceHelperPlaceholder().visit(tree))
            rows.append(dict(call_id=call['id'], task_id=call['task_id'],
                             raw_call_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             original_expression=expression, counterfactual_expression=modified,
                             original_outcome=ledger.check_expression(tasks[call['task_id']], expression),
                             counterfactual_outcome=ledger.check_expression(tasks[call['task_id']], modified)))
        report['arms'][arm] = dict(rows=rows, changed_calls=len(rows),
                                  counterfactual_success_tasks=sorted({row['task_id'] for row in rows
                                                                     if row['counterfactual_outcome']['success']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    options.output.write_text(json.dumps(diagnose(options.root), indent=2, sort_keys=True))
