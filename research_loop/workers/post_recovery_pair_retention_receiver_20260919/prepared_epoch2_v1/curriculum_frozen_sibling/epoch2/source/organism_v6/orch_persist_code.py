"""L1-only persistent integer-ledger repairs with a bounded expression oracle."""

import ast
import hashlib
import json
from pathlib import Path
import random


FAMILY = 'integer-ledger-pipelines-v1'
PARTITION = {
    'L1_mining': [FAMILY],
    'L2proposal': ['structured-text-ledger-v1'],
    'heldL3proposal': ['dependency-build-graph-v1'],
}
HELPER_SPEC = (
    'Existing ledger helpers: ge(xs, threshold) keeps integers >= threshold; '
    'affine(xs, factor, offset) maps each integer to factor*x+offset; '
    'clip(xs, low, high) clamps every integer inclusively; '
    'unique(xs) removes duplicates preserving first occurrence; '
    'sum(xs) sums integers (empty gives 0); len(xs) counts elements. '
    'Only calls to these helpers, values, and integer constants are allowed. '
    'Arguments can nest. Do not define functions or use comprehensions.'
)


def ge(values, threshold):
    return [value for value in values if value >= threshold]


def affine(values, factor, offset):
    return [factor * value + offset for value in values]


def clip(values, low, high):
    if low > high:
        raise ValueError('inverted clamp bounds')
    return [max(low, min(high, value)) for value in values]


def unique(values):
    return list(dict.fromkeys(values))


HELPERS = dict(ge=ge, affine=affine, clip=clip, unique=unique, sum=sum, len=len)
ARITY = dict(ge=2, affine=3, clip=3, unique=1, sum=1, len=1)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def validate_expression(expression):
    if not isinstance(expression, str) or len(expression) > 500:
        raise ValueError('expression must be <=500 characters')
    tree = ast.parse(expression, mode='eval')
    if len(list(ast.walk(tree))) > 100:
        raise ValueError('expression AST too large')
    for node in ast.walk(tree):
        if type(node) not in (ast.Expression, ast.Call, ast.Name, ast.Load,
                              ast.Constant, ast.UnaryOp, ast.USub):
            raise ValueError('unsupported expression syntax')
        if isinstance(node, ast.Name) and node.id not in {'values', *HELPERS}:
            raise ValueError('unknown identifier')
        if isinstance(node, ast.Constant) and (type(node.value) is not int or abs(node.value) > 1000):
            raise ValueError('only bounded integer constants')
        if isinstance(node, ast.UnaryOp) and not isinstance(node.operand, ast.Constant):
            raise ValueError('negation only for integer literals')
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in HELPERS:
                raise ValueError('only ledger helper calls')
            if node.keywords or len(node.args) != ARITY[node.func.id]:
                raise ValueError('helper arity mismatch')
    return tree


def evaluate(expression, values):
    tree = validate_expression(expression)
    result = eval(compile(tree, '<child-ledger-expression>', 'eval'),
                  {'__builtins__': {}, **HELPERS}, {'values': list(values)})
    if type(result) is not int:
        raise ValueError('task must return an integer')
    return result


def build_tasks(family=FAMILY, count=64):
    if family != FAMILY or not 1 <= count <= 64:
        raise ValueError('only declared L1 mining family may be instantiated')
    tasks = []
    for index in range(count):
        threshold = (index * 3) % 9 - 4
        factor = [-2, 3, -3, 2][index % 4]
        offset = (index * 5) % 11 - 5
        low, high = -3 - index % 3, 3 + index % 5
        specs = [
            f'Keep original values >= {threshold}; map each to {factor}*x+({offset}); sum the mapped values.',
            f'Map all values to {factor}*x+({offset}); clamp to [{low},{high}]; remove duplicates after clamping; sum.',
            f'Remove duplicate original values; keep values >= {threshold}; map to {factor}*x+({offset}); sum.',
            f'Clamp all values to [{low},{high}]; map to {factor}*x+({offset}); count mapped values >= {threshold}. Duplicates count separately.',
        ]
        generator = random.Random(1714 + index)
        inputs = [[], [0], [-9, -9, 0, 9, 9], [threshold - 1, threshold, threshold + 1]]
        inputs += [[generator.randint(-20, 20) for _ in range(12)] for _ in range(12)]
        tasks.append(dict(id=f'ledger_{index:03d}', family=FAMILY, kind=index % 4,
                          threshold=threshold, factor=factor, offset=offset,
                          low=low, high=high, spec=specs[index % 4], inputs=inputs))
    return tasks


def expected(task, values):
    threshold, factor, offset = task['threshold'], task['factor'], task['offset']
    low, high = task['low'], task['high']
    if task['kind'] == 0:
        return sum(factor * value + offset for value in values if value >= threshold)
    if task['kind'] == 1:
        return sum(set(max(low, min(high, factor * value + offset)) for value in values))
    if task['kind'] == 2:
        return sum(factor * value + offset for value in set(values) if value >= threshold)
    return sum(factor * max(low, min(high, value)) + offset >= threshold for value in values)


def check_expression(task, expression):
    passed = 0
    for values in task['inputs']:
        wanted = expected(task, values)
        try:
            actual = evaluate(expression, values)
        except Exception as error:
            return dict(success=False, passed=passed, total=len(task['inputs']),
                        input=values, expected=wanted, error=type(error).__name__ + ': ' + str(error))
        if actual != wanted:
            return dict(success=False, passed=passed, total=len(task['inputs']),
                        input=values, expected=wanted, observed=actual)
        passed += 1
    return dict(success=True, passed=passed, total=passed)


class Codebase:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.functions = {}
        self.records = []
        self._save()

    def _save(self):
        source = 'from organism_v6.orch_persist_code import ge, affine, clip, unique\n\n'
        for name, item in self.functions.items():
            source += f'def {name}(values):\n    return {item["expression"]}\n\n'
        (self.directory / 'ledger.py').write_text(source)
        (self.directory / 'records.json').write_text(json.dumps(self.records, indent=2))

    def patch(self, task, expression):
        result = check_expression(task, expression)
        regressions = [check_expression(item['task'], item['expression']) for item in self.functions.values()]
        result['previous_functions'] = len(regressions)
        result['regressions_pass'] = all(item['success'] for item in regressions)
        if result['success'] and result['regressions_pass']:
            self.functions[task['id']] = dict(task=task, expression=expression)
            self._save()
        return result

    def record(self, task_id, text, call_id):
        if task_id not in self.functions or not isinstance(text, str) or not text.strip():
            raise ValueError('record requires own successful event and nonempty child text')
        self.records.append(dict(task_id=task_id, text=text, call_id=call_id,
                                 event_sha256=digest(self.functions[task_id])))
        self._save()


def parse_action(text):
    lines = text.strip().splitlines()
    if not lines:
        raise ValueError('empty child response')
    action = json.loads(lines[-1])
    if not isinstance(action, dict) or set(action) not in ({'expression'}, {'record'}):
        raise ValueError('last line must be exactly expression or record JSON')
    if not isinstance(next(iter(action.values())), str):
        raise ValueError('action value must be child text')
    return action, '\n'.join(lines[:-1])


def student_prefix(task, records, previous=None, feedback=None):
    text = f'Persistent ledger task {task["id"]}: {task["spec"]}\n{HELPER_SPEC}\n'
    text += 'My stored records: ' + json.dumps(records, sort_keys=True)
    if previous is not None:
        text += '\nMy preceding attempt: ' + previous
    if feedback is not None:
        text += '\nUnit-test outcome: ' + json.dumps(feedback, sort_keys=True)
    return [{'role': 'user', 'content': text}]


def messages(task, records, arm, previous=None, feedback=None, record=False):
    prefix = student_prefix(task, records, previous, feedback)
    guidance = ('Write 150–400 tokens in first person explaining the evidence you actually have, '
                'how it supports this task, and a checkable expectation. Do not invent test results. '
                if arm == 'RICH' else 'Be terse; provide only the final JSON action. ')
    guidance += ('After this successful repair, write your own reusable lesson as the final line '
                 '{"record":"your own lesson"}.' if record else
                 'Propose a repair as the final line {"expression":"helper expression"}. '
                 'If previous tests failed, use their feedback to revise your own attempt.')
    return [{'role': 'system', 'content': guidance}] + prefix, prefix
