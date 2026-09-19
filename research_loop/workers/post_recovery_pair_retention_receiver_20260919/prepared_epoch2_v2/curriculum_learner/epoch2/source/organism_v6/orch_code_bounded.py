"""Finite, capability-free expression interpretation for public MBPP screening."""

import ast
import hashlib
import json
import operator


LIMIT = 256
BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
       ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
       ast.In: lambda left, right: left in right, ast.NotIn: lambda left, right: left not in right}
HELPERS = dict(sum=sum, min=min, max=max, len=len, abs=abs, round=round,
               sorted=sorted, reversed=lambda value: list(reversed(value)),
               list=list, tuple=tuple, all=all, any=any, int=int, float=float)
SPEC = ('Return an expression over the named arguments, not a function definition. '
        'Supported: numeric/bool literals, lists/tuples, arithmetic + - * / // %, '
        'comparisons, and/or/not, conditional expressions, indexing/slicing, '
        'one-generator list comprehensions, and calls sum,min,max,len,abs,round,'
        'sorted,reversed,list,tuple,all,any,int,float,range. No attributes, imports, '
        'strings, sets, dictionaries, lambdas, recursion or arbitrary execution. '
        'All containers/ranges <=256 elements; values abs<=1e12; <=10000 AST steps. '
        'Final line must be JSON {"expression":"..."}, or when requested {"record":"..."}.')


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def bounded(value, depth=0, budget=None):
    budget = [4096] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0:
        raise ValueError('aggregate value limit')
    if depth > 8:
        raise ValueError('depth limit')
    if type(value) in (list, tuple):
        if len(value) > LIMIT:
            raise ValueError('container limit')
        for item in value:
            bounded(item, depth + 1, budget)
    elif type(value) not in (int, float, bool) or not abs(value) <= 1e12:
        raise ValueError('numeric value limit')
    return value


def validate_expression(text):
    if not isinstance(text, str) or len(text) > 2000:
        raise ValueError('source limit')
    tree = ast.parse(text, mode='eval')
    allowed = (ast.Expression, ast.Constant, ast.Name, ast.Load, ast.Store, ast.List,
               ast.Tuple, ast.BinOp, ast.UnaryOp, ast.USub, ast.UAdd, ast.Not,
               ast.BoolOp, ast.And, ast.Or, ast.Compare, ast.IfExp, ast.Subscript,
               ast.Slice, ast.ListComp, ast.comprehension, ast.Call)
    nodes = list(ast.walk(tree))
    if len(nodes) > 200:
        raise ValueError('AST size limit')
    for node in nodes:
        if type(node) not in allowed + tuple(BIN) + tuple(CMP):
            raise ValueError('unsupported syntax: ' + type(node).__name__)
        if isinstance(node, ast.Constant):
            bounded(node.value)
        if isinstance(node, ast.Name) and node.id.startswith('_'):
            raise ValueError('private name')
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name)
                or node.func.id not in set(HELPERS) | {'range'} or node.keywords):
            raise ValueError('unsupported call')
        if isinstance(node, ast.ListComp) and (len(node.generators) != 1
                or node.generators[0].is_async or not isinstance(node.generators[0].target, ast.Name)):
            raise ValueError('unsupported comprehension')
    return tree.body


def evaluate(text, environment):
    tree = validate_expression(text)
    for value in environment.values():
        bounded(value)
    steps = [0]

    def visit(node, scope):
        steps[0] += 1
        if steps[0] > 10000:
            raise ValueError('step limit')
        if isinstance(node, ast.Constant):
            result = node.value
        elif isinstance(node, ast.Name):
            result = scope[node.id]
        elif isinstance(node, (ast.List, ast.Tuple)):
            result = [visit(item, scope) for item in node.elts]
            if isinstance(node, ast.Tuple):
                result = tuple(result)
        elif isinstance(node, ast.BinOp):
            left, right = visit(node.left, scope), visit(node.right, scope)
            if isinstance(node.op, ast.Mult):
                if isinstance(left, (list, tuple)) and isinstance(right, int) and len(left) * max(0, right) > LIMIT:
                    raise ValueError('multiplication allocation limit')
                if isinstance(right, (list, tuple)) and isinstance(left, int) and len(right) * max(0, left) > LIMIT:
                    raise ValueError('multiplication allocation limit')
            result = BIN[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            result = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}[type(node.op)](visit(node.operand, scope))
        elif isinstance(node, ast.BoolOp):
            result = visit(node.values[0], scope)
            for value in node.values[1:]:
                if (isinstance(node.op, ast.And) and not result) or (isinstance(node.op, ast.Or) and result):
                    break
                result = visit(value, scope)
        elif isinstance(node, ast.Compare):
            left = visit(node.left, scope)
            result = True
            for operation, comparator in zip(node.ops, node.comparators):
                right = visit(comparator, scope)
                if not CMP[type(operation)](left, right):
                    result = False
                    break
                left = right
        elif isinstance(node, ast.IfExp):
            result = visit(node.body if visit(node.test, scope) else node.orelse, scope)
        elif isinstance(node, ast.Subscript):
            container = visit(node.value, scope)
            if isinstance(node.slice, ast.Slice):
                index = slice(*(visit(item, scope) if item else None for item in
                                (node.slice.lower, node.slice.upper, node.slice.step)))
            else:
                index = visit(node.slice, scope)
            result = container[index]
        elif isinstance(node, ast.ListComp):
            generator = node.generators[0]
            result = []
            for item in visit(generator.iter, scope):
                local = dict(scope, **{generator.target.id: item})
                if all(visit(condition, local) for condition in generator.ifs):
                    result.append(visit(node.elt, local))
        elif isinstance(node, ast.Call):
            arguments = [visit(item, scope) for item in node.args]
            if node.func.id == 'range':
                sequence = range(*arguments)
                if len(sequence) > LIMIT:
                    raise ValueError('range allocation limit')
                result = list(sequence)
            else:
                result = HELPERS[node.func.id](*arguments)
        else:
            raise ValueError('unsupported node')
        return bounded(result)

    return visit(tree, environment)


def reference_program(record):
    tree = ast.parse(record['code'])
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError('reference not single function')
    function = tree.body[0]
    if function.decorator_list or function.args.defaults or function.args.vararg or function.args.kwarg or function.args.kwonlyargs:
        raise ValueError('reference signature unsupported')
    names = [argument.arg for argument in function.args.args]
    if not function.body or not isinstance(function.body[-1], ast.Return):
        raise ValueError('reference missing return')
    program = []
    for statement in function.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            program.append((statement.targets[0].id, ast.unparse(statement.value)))
        elif isinstance(statement, ast.Return) and statement is function.body[-1]:
            program.append((None, ast.unparse(statement.value)))
        else:
            raise ValueError('reference statements unsupported')
        validate_expression(program[-1][1])
    return function.name, names, program


def extract_task(record):
    if record['test_setup_code'].strip():
        raise ValueError('test setup unsupported')
    name, names, program = reference_program(record)
    tests = []
    for source in record['test_list'] + record.get('challenge_test_list', []):
        body = ast.parse(source).body
        if len(body) != 1 or not isinstance(body[0], ast.Assert):
            raise ValueError('oracle assert required')
        comparison = body[0].test
        if not isinstance(comparison, ast.Compare) or len(comparison.ops) != 1 or not isinstance(comparison.ops[0], ast.Eq):
            raise ValueError('oracle equality required')
        call = comparison.left
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != name or call.keywords or len(call.args) != len(names):
            raise ValueError('oracle direct positional call required')
        values = [bounded(ast.literal_eval(argument)) for argument in call.args]
        wanted = bounded(ast.literal_eval(comparison.comparators[0]))
        scope = dict(zip(names, values))
        for target, expression in program:
            actual = evaluate(expression, scope)
            if target is not None:
                scope[target] = actual
        if actual != wanted:
            raise ValueError('reference oracle mismatch')
        tests.append(dict(arguments=values, expected=wanted, source=source))
    if len(tests) < 3:
        raise ValueError('at least three tests')
    family = 'sequence/list transformations' if any(isinstance(value, (list, tuple)) for test in tests for value in test['arguments']) else 'scalar arithmetic'
    return dict(id=record['task_id'], text=record['text'], arguments=names, function=name,
                family=family, tests=tests, reference_pass=True)


def check(task, expression):
    passed = 0
    for test in task['tests']:
        comparison = ast.parse(test['source']).body[0].test
        arguments = [ast.literal_eval(argument) for argument in comparison.left.args]
        expected = ast.literal_eval(comparison.comparators[0])
        try:
            actual = evaluate(expression, dict(zip(task['arguments'], arguments)))
        except Exception as error:
            return dict(success=False, passed=passed, total=len(task['tests']), error=str(error),
                        arguments=test['arguments'], expected=test['expected'])
        if actual != expected:
            return dict(success=False, passed=passed, total=len(task['tests']),
                        arguments=test['arguments'], expected=test['expected'], observed=actual)
        passed += 1
    return dict(success=True, passed=passed, total=passed)


def prompt(task, arm, history, record=False):
    user = task['text'] + '\nArguments: ' + ', '.join(task['arguments']) + '\n' + SPEC
    user += '\nPublic reference tests: ' + json.dumps([test['source'] for test in task['tests']])
    for row in history:
        user += '\nMy prior response: ' + row['target'] + '\nOracle feedback: ' + json.dumps(row['feedback'])
    user += '\nWrite my own reusable record of this successful solution.' if record else '\nPropose a solution; use any grounded feedback to correct my prior attempt.'
    student = [{'role': 'user', 'content': user}]
    guidance = ('Write 150–400 generated tokens in first person before your JSON action last line. '
                'Explain actual evidence, relevance to the goal, and a checkable expectation. '
                'After failure revise using the feedback; after success write a specific reusable lesson. '
                'Do not invent execution results or pad prose.' if arm == 'rich' else
                'Be terse. Output only the requested JSON action on the last line.')
    return [{'role': 'system', 'content': guidance}] + student, student


def parse_action(text, record=False):
    lines = text.strip().splitlines()
    value = json.loads(lines[-1])
    key = 'record' if record else 'expression'
    if not isinstance(value, dict) or set(value) != {key} or not isinstance(value[key], str) or not value[key].strip():
        raise ValueError('invalid final action')
    return value[key], '\n'.join(lines[:-1])
