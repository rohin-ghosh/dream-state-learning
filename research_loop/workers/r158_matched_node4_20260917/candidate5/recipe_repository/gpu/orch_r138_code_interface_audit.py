"""Post-hoc R136 interface audit; frozen scores and inputs remain unchanged."""

import argparse
import ast
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from gpu import orch_r133_code_feedback_collection as frozen


ROOT = Path('/localhome/local-rohing/orch_r136_code_feedback_20260915_attempt1/run1')
PINS = {
    'PLAN.json': '4e6c6093b50d0ec3b79be50134a60cb9f5796da8034bf85b2b65bdc50e987195',
    '../RESULTS_R136_AUTHOR.json': '6aac5f0b942eb3a06336d9c258ddc3373f71db5a4a1500162cef8f0635f3fd88',
    '../REDUCTION_R136_AUTHOR_20260915.json': 'd4080ff2bb8dfc34d976bc21c801f1943b85f0cbd7264ddf74a61a2238029a01',
}
MAX_TEXT = 4096
ERRORS = {
    'helper arity mismatch': 'HELPER_ARITY',
    'only bounded integer constants': 'NON_BOUNDED_INTEGER_CONSTANT',
    'unsupported expression syntax': 'UNSUPPORTED_SYNTAX',
    'unknown identifier': 'UNKNOWN_IDENTIFIER',
    'only ledger helper calls': 'UNSUPPORTED_CALL',
    'task_must_return_integer': 'NON_INTEGER_RETURN',
    'helper_first_argument_requires_integer_list': 'HELPER_REQUIRES_LIST',
    'helper_scalar_arguments_require_integers': 'HELPER_REQUIRES_INTEGER',
    'inverted clamp bounds': 'INVERTED_CLAMP',
}
KINDS = ('FILTER_AFFINE_SUM', 'AFFINE_CLAMP_UNIQUE_SUM',
         'UNIQUE_FILTER_AFFINE_SUM', 'CLAMP_AFFINE_COUNT')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def loads(raw):
    def unique(pairs):
        document = {}
        for key, value in pairs:
            require(key not in document, 'duplicate_artifact_key')
            document[key] = value
        return document
    return json.loads(raw, object_pairs_hook=unique)


class Snapshot:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.hashes = {}

    def read(self, relative):
        require(not Path(relative).is_absolute()
                and (relative in PINS or '..' not in Path(relative).parts), 'artifact_path')
        path = Path(self.root / relative)
        expected_path = self.root.parent / path.name if relative.startswith('../') else path
        require(path.resolve() == expected_path and path.is_file(), 'regular_artifact')
        require(path.stat().st_size <= 8 * 1024 * 1024, 'artifact_size')
        raw = path.read_bytes()
        require(len(raw) <= 8 * 1024 * 1024, 'artifact_size')
        observed = sha(raw)
        require(relative not in self.hashes or observed == self.hashes[relative], 'changed_artifact')
        require(relative not in PINS or observed == PINS[relative], 'R136_pin_mismatch')
        self.hashes[relative] = observed
        return loads(raw)

    def stable(self):
        for relative in tuple(self.hashes):
            self.read(relative)


def safe_shape(expression):
    try:
        tree = ast.parse(expression, mode='eval').body
    except (SyntaxError, ValueError, RecursionError):
        return '<invalid-expression>'
    def visit(node, depth=0):
        if depth > 12:
            return '<depth-limit>'
        if type(node) is ast.Name:
            return 'values' if node.id == 'values' else '<identifier>'
        if type(node) is ast.Constant:
            return 'N' if type(node.value) is int else '<non-integer>'
        if type(node) is ast.UnaryOp and type(node.op) is ast.USub:
            return '-' + visit(node.operand, depth + 1)
        if type(node) is ast.Call and type(node.func) is ast.Name and node.func.id in frozen.ledger.HELPERS:
            return node.func.id + '(' + ','.join(visit(arg, depth + 1) for arg in node.args) + ')'
        return '<unsupported-' + type(node).__name__ + '>'
    result = visit(tree)
    return result if len(result) <= 240 else '<shape-too-long>'


def extract(raw, *, terminal, truncated):
    result = dict(format='UNSUPPORTED', selection='UNSUPPORTED', reason='UNSUPPORTED_WRAPPER',
                  raw_sha256=sha(raw.encode()), expression=None, expression_sha256=None,
                  ast_sha256=None, shape=None)
    if not terminal or truncated:
        return dict(result, format='EXCLUDED', selection='EXCLUDED', reason='INCOMPLETE_OR_TRUNCATED')
    if not raw.strip() or len(raw) > MAX_TEXT:
        return dict(result, reason='EMPTY_OR_SOURCE_LIMIT')
    text = raw.strip()
    fence = False
    if '```' in text:
        match = re.fullmatch(r'```(?:json|python)?\n([^`]+)\n```', text)
        if match is None:
            return dict(result, reason='AMBIGUOUS_OR_UNCLOSED_FENCE')
        text, fence = match.group(1).strip(), True
    try:
        if text.startswith('{'):
            tree = ast.parse(text, mode='eval')
            require(len(list(ast.walk(tree))) <= 256, 'WRAPPER_AST_LIMIT')
            mapping = tree.body
            require(type(mapping) is ast.Dict and len(mapping.keys) == 1, 'AMBIGUOUS_MAPPING')
            key, value = mapping.keys[0], mapping.values[0]
            require(type(key) is ast.Constant and key.value in ('expression', 'expr'), 'UNSUPPORTED_KEY')
            quoted = type(value) is ast.Constant and type(value.value) is str
            expression = value.value if quoted else ast.get_source_segment(text, value)
            form = ('QUOTED_' if quoted else 'UNQUOTED_') + key.value.upper()
        else:
            tree = ast.parse(text, mode='exec')
            require(len(list(ast.walk(tree))) <= 256 and len(tree.body) == 1, 'AMBIGUOUS_STATEMENTS')
            statement = tree.body[0]
            if type(statement) is ast.FunctionDef:
                arguments = statement.args
                require(not statement.decorator_list and statement.returns is None
                        and statement.type_comment is None and not getattr(statement, 'type_params', [])
                        and not arguments.posonlyargs and not arguments.kwonlyargs
                        and not arguments.defaults and not arguments.kw_defaults
                        and arguments.vararg is None and arguments.kwarg is None
                        and len(arguments.args) == 1 and arguments.args[0].arg == 'values'
                        and arguments.args[0].annotation is None
                        and statement.name not in {'values', *frozen.ledger.HELPERS}
                        and len(statement.body) == 1, 'UNSUPPORTED_FUNCTION')
                statement, form = statement.body[0], 'SINGLE_RETURN_FUNCTION'
            else:
                form = 'RETURN_EXPRESSION'
            require(type(statement) is ast.Return and statement.value is not None, 'UNSUPPORTED_STATEMENT')
            expression = ast.get_source_segment(text, statement.value)
        require(type(expression) is str and 0 < len(expression) <= 500, 'EXPRESSION_SOURCE_LIMIT')
        parsed = ast.parse(expression, mode='eval')
        require(len(list(ast.walk(parsed))) <= 100, 'EXPRESSION_AST_LIMIT')
        result.update(format=('FENCED_' if fence else '') + form, expression=expression,
                      expression_sha256=sha(expression.encode()),
                      ast_sha256=sha(ast.dump(parsed, include_attributes=False).encode()),
                      shape=safe_shape(expression))
        try:
            frozen.ledger.validate_expression(expression)
        except (ValueError, TypeError, SyntaxError, RecursionError) as error:
            return dict(result, selection='SANDBOX_REJECTED',
                        reason=ERRORS.get(str(error), 'BOUNDED_SANDBOX_REJECTION'))
        return dict(result, selection='SELECTED', reason=None)
    except (ValueError, TypeError, SyntaxError, RecursionError) as error:
        reasons = {'WRAPPER_AST_LIMIT', 'AMBIGUOUS_MAPPING', 'UNSUPPORTED_KEY', 'AMBIGUOUS_STATEMENTS',
                   'UNSUPPORTED_FUNCTION', 'UNSUPPORTED_STATEMENT', 'EXPRESSION_SOURCE_LIMIT', 'EXPRESSION_AST_LIMIT'}
        return dict(result, reason=str(error) if str(error) in reasons else 'INVALID_OR_UNSUPPORTED_AST')


def evaluate_selected(selection, task):
    result = dict(status=selection['selection'], reason=selection['reason'], public_executable=False,
                  checked=0, matched=0, diagnostic_pass=False)
    if selection['selection'] != 'SELECTED':
        return result
    expression = selection['expression']
    inputs = deepcopy(task['verification_inputs'])
    require(len(inputs) == 20, 'exact_saved_20_checks')
    try:
        frozen.evaluate(expression, deepcopy(task['public_input']))
        result['public_executable'] = True
        observed = [frozen.evaluate(expression, values) for values in inputs]
    except (ValueError, TypeError, SyntaxError, RecursionError) as error:
        return dict(result, status='INTERPRETER_REJECTED',
                    reason=ERRORS.get(str(error), 'BOUNDED_INTERPRETER_REJECTION'))
    expected = [frozen.public.expected(task, values) for values in inputs]
    matched = sum(actual == wanted for actual, wanted in zip(observed, expected))
    return dict(result, status='DIAGNOSTIC_CHECK_PASS' if matched == 20 else 'DIAGNOSTIC_CHECK_FAIL',
                checked=20, matched=matched, diagnostic_pass=matched == 20)


def revision(before, after):
    if not before['complete'] or not after['complete']:
        return dict(classification='EXCLUDED_INCOMPLETE_PAIR')
    first, last = before['selection'], after['selection']
    if first['raw_sha256'] == last['raw_sha256']:
        category = 'EXACT_OUTPUT_UNCHANGED'
    elif first['ast_sha256'] is not None and first['ast_sha256'] == last['ast_sha256']:
        category = 'SURFACE_ONLY_SAME_EXPRESSION_AST'
    elif first['ast_sha256'] is not None and last['ast_sha256'] is not None:
        category = 'EXPRESSION_AST_CHANGED'
    else:
        category = 'UNSUPPORTED_CHANGE'
    return dict(classification=category,
                canonical_transition=before['canonical']['category'] + '->' + after['canonical']['category'],
                diagnostic_transition=before['diagnostic']['status'] + '->' + after['diagnostic']['status'],
                diagnostic_failed_to_passed=not before['diagnostic']['diagnostic_pass']
                    and after['diagnostic']['diagnostic_pass'])


def summarize(rows):
    groups = {}
    for model in frozen.MODELS:
        stages, forks = {}, {}
        for stage in frozen.STAGES:
            selected = [row for row in rows if row['model'] == model and row['stage'] == stage]
            stages[stage] = dict(planned=len(selected), complete=sum(row['complete'] for row in selected),
                canonical_pass=sum(row['canonical']['success'] for row in selected),
                canonical_categories=dict(Counter(row['canonical']['category'] for row in selected)),
                formats=dict(Counter(row['selection']['format'] for row in selected)),
                diagnostic_status=dict(Counter(row['diagnostic']['status'] for row in selected)),
                diagnostic_reasons=dict(Counter(row['diagnostic']['reason'] for row in selected if row['diagnostic']['reason'])),
                diagnostic_pass_tasks=[row['task_index'] for row in selected if row['diagnostic']['diagnostic_pass']])
        index = {(row['task_index'], row['stage']): row for row in rows if row['model'] == model}
        for stage in frozen.STAGES[1:]:
            pairs = [revision(index[position, 'draft'], index[position, stage]) for position in range(16)]
            forks[stage] = dict(classifications=dict(Counter(pair['classification'] for pair in pairs)),
                canonical_transitions=dict(Counter(pair['canonical_transition'] for pair in pairs if 'canonical_transition' in pair)),
                diagnostic_transitions=dict(Counter(pair['diagnostic_transition'] for pair in pairs if 'diagnostic_transition' in pair)),
                diagnostic_failed_to_passed=sum(pair.get('diagnostic_failed_to_passed', False) for pair in pairs),
                changed_AST_tasks=[position for position, pair in enumerate(pairs) if pair['classification'] == 'EXPRESSION_AST_CHANGED'])
        pairs = [revision(index[position, frozen.STAGES[1]], index[position, frozen.STAGES[2]]) for position in range(16)]
        groups[model] = dict(stages=stages, draft_to_forks=forks,
            feedback_vs_neutral=dict(Counter(pair['classification'] for pair in pairs)),
            actual_feedback_information=dict(Counter(
                'ACTUAL_OUTPUT_NO_EXPECTED' if row['canonical']['category'] in ('TASK_PASS', 'TASK_CHECK_FAILURE')
                else row['canonical']['category'] for row in rows if row['model'] == model and row['stage'] == 'draft')))
    paired_models = {}
    index = {(row['task_index'], row['model'], row['stage']): row for row in rows}
    for stage in frozen.STAGES:
        counts = Counter()
        for position in range(16):
            full, base = [index[position, model, stage] for model in frozen.MODELS]
            if not full['complete'] or not base['complete']:
                counts['EXCLUDED_INCOMPLETE'] += 1
            else:
                counts['BOTH_DIAGNOSTIC_PASS' if full['diagnostic']['diagnostic_pass'] and base['diagnostic']['diagnostic_pass']
                       else 'FULL_ONLY_DIAGNOSTIC_PASS' if full['diagnostic']['diagnostic_pass']
                       else 'BASE_ONLY_DIAGNOSTIC_PASS' if base['diagnostic']['diagnostic_pass']
                       else 'BOTH_DIAGNOSTIC_FAIL'] += 1
        paired_models[stage] = dict(counts)
    return dict(models=groups, task_paired_models=paired_models)


def diagnose(records, tasks):
    selections = [extract(record['response']['raw'], terminal=record['response']['terminal'],
                          truncated=record['response']['truncated']) for record in records]
    selection_manifest = digest([{key: value for key, value in selection.items() if key != 'expression'}
                                 for selection in selections])
    rows = []
    for record, selection in zip(records, selections):
        response = record['response']
        task = tasks[record['task_index']]
        diagnostic = evaluate_selected(selection, task)
        rows.append(dict(planned_call=record['planned_call'], task_index=record['task_index'],
            model=record['model'], stage=record['stage'], complete=response['terminal'] and not response['truncated'],
            canonical=deepcopy(record['canonical']), selection=selection, diagnostic=diagnostic))
    return rows, selection_manifest


def validate_headers(author, reduced):
    require(author['schema'] == 'R136_AUTHOR_RESULTS_V1'
            and author['status'] == 'COMPLETE_AUTHOR_REDERIVED'
            and reduced['status'] == 'COMPLETE', 'completed_R136_only')
    require(reduced['expected_plan_sha256'] == PINS['PLAN.json']
            and reduced['evidence_sha256'] == author['integrity']['evidence_sha256'], 'author_reduction_join')


def audit(root):
    snapshot = Snapshot(root)
    plan = snapshot.read('PLAN.json')
    author = snapshot.read('../RESULTS_R136_AUTHOR.json')
    reduced = snapshot.read('../REDUCTION_R136_AUTHOR_20260915.json')
    validate_headers(author, reduced)
    require(plan['source_sha256'] == frozen.source_hashes() == reduced['producer_source_sha256'], 'frozen_source_pins')
    task_document = snapshot.read('TASKS.json')
    require(snapshot.hashes['TASKS.json'] == plan['tasks_sha256'], 'task_pin')
    snapshot.read('EXCLUSIONS.json')
    require(snapshot.hashes['EXCLUSIONS.json'] == plan['exclusions_sha256'], 'exclusion_pin')
    for relative, expected in author['integrity']['terminal_sha256'].items():
        snapshot.read(relative)
        require(snapshot.hashes[relative] == expected, 'terminal_pin')
    tasks = task_document['tasks']
    require(len(tasks) == 16 and all(task['split'] == 'TRAIN' for task in tasks), 'public_TRAIN_only')
    records = []
    require(len(reduced['cells']) == 96, 'fixed_96_cells')
    for cell in reduced['cells']:
        task = tasks[cell['task_index']]
        require(frozen.digest(task['id']) == cell['task_id_sha256'], 'task_identity')
        prefix = 'episodes/' + task['id'] + '/' + cell['model'] + '/' + cell['stage']
        call, intent = snapshot.read(prefix + '.CALL.json'), snapshot.read(prefix + '.INTENT.json')
        require(snapshot.hashes[prefix + '.CALL.json'] == cell['call_sha256']
                and snapshot.hashes[prefix + '.INTENT.json'] == cell['intent_sha256'], 'call_intent_pins')
        require(call['reserved_call'] == cell['planned_call'] and call['task_id'] == task['id']
                and call['model'] == cell['model'] and call['stage'] == cell['stage'], 'cell_identity')
        records.append(dict(cell, canonical=cell['outcome'], response=call['response'], intent=intent,
            public=snapshot.read(prefix + '.PUBLIC.json'), verify=snapshot.read(prefix + '.VERIFY.json')))
    require({record['planned_call'] for record in records} == set(range(1, 97)), 'no_duplicate_cell')
    require(not list(snapshot.root.glob('episodes/*/*/*.FAILURE.json')), 'no_failure_outputs')
    rows, selection_manifest = diagnose(records, tasks)
    record_index = {(record['task_index'], record['model'], record['stage']): record for record in records}
    for record in records:
        task, raw = tasks[record['task_index']], record['response']['raw']
        receipt = frozen.execute_public(task, raw)
        correct = frozen.verify(task, raw)
        require(record['public'] == receipt and record['verify'] == dict(success=correct), 'strict_receipts_unchanged')
        category = ('TASK_PASS' if correct else 'TASK_CHECK_FAILURE') if 'observed' in receipt else (
            'PARSER_ERROR' if 'expression' not in receipt else 'SANDBOX_ERROR' if not receipt['interpreter_started'] else 'INTERPRETER_ERROR')
        require(record['canonical']['category'] == category and record['canonical']['success'] == correct,
                'canonical_outcome_unchanged')
        require(record['canonical']['complete_response'] == (record['response']['terminal']
                    and not record['response']['truncated'])
                and record['canonical']['truncated'] == record['response']['truncated'], 'completion_unchanged')
        draft = record_index[record['task_index'], record['model'], 'draft']['response']['raw']
        stage = record['stage']
        prefix = frozen.messages(task, stage, None if stage == 'draft' else draft,
            frozen.execute_public(task, draft) if stage == 'interpreter_feedback' else None)
        require(record['intent']['messages'] == record['response']['messages'] == prefix,
                'actual_feedback_prefix_unchanged_no_gold')
    examples, seen = [], set()
    for row in rows:
        selection = row['selection']
        key = (row['model'], selection['format'], row['diagnostic']['status'], row['diagnostic']['reason'])
        if row['complete'] and key not in seen and len(examples) < 10:
            seen.add(key)
            examples.append(dict(planned_call=row['planned_call'], task_index=row['task_index'], model=row['model'],
                stage=row['stage'], format=selection['format'], diagnostic_status=row['diagnostic']['status'],
                reason=row['diagnostic']['reason'], schematic_only=selection['shape'],
                raw_sha256=selection['raw_sha256']))
    compact_cells = [[row['planned_call'], row['task_index'], row['model'], row['stage'], row['complete'],
                     row['canonical']['category'], row['selection']['format'], row['diagnostic']['status'],
                     row['diagnostic']['reason'], row['diagnostic']['matched'],
                     row['selection']['raw_sha256'], row['selection']['ast_sha256']] for row in rows]
    revisions = []
    index = {(row['task_index'], row['model'], row['stage']): row for row in rows}
    for model in frozen.MODELS:
        for position in range(16):
            before = index[position, model, 'draft']
            forks = {stage: revision(before, index[position, model, stage]) for stage in frozen.STAGES[1:]}
            revisions.append(dict(task_index=position, family=KINDS[tasks[position]['kind']], model=model, forks=forks))
    snapshot.stable()
    require(plan['source_sha256'] == frozen.source_hashes(), 'source_stability')
    return dict(schema='R138_R136_POSTHOC_INTERFACE_DIAGNOSTIC_V1', status='COMPLETE_DIAGNOSTIC_ONLY',
        generated_utc=datetime.now(timezone.utc).isoformat(), canonical_scores_unchanged=True,
        interpretation='Post-hoc interface sensitivity on existing public TRAIN outputs, not a benchmark replacement or learning claim.',
        provider_calls=0, GPU_calls=0, training_updates=0, admissions=0, input_writes=0,
        extraction_policy='Whole single expression/expr mapping, optional single fence, or single return; no repair or candidate search.',
        selection_before_any_diagnostic_expected_comparison=True, selection_manifest_sha256=selection_manifest,
        aggregate=summarize(rows), task_paired_revisions=revisions, sanitized_examples=examples,
        cell_columns=['planned_call', 'task_index', 'model', 'stage', 'complete', 'canonical_category',
                      'diagnostic_format', 'diagnostic_status', 'diagnostic_reason', 'saved_checks_matched',
                      'raw_utf8_sha256', 'expression_AST_sha256'], cells=compact_cells,
        provenance=dict(root=str(snapshot.root), fixed_pins=PINS, source_sha256=plan['source_sha256'],
                        auditor_sha256=sha(Path(__file__).read_bytes()), verified_artifacts=len(snapshot.hashes),
                        evidence_sha256=digest(snapshot.hashes), tasks_sha256=plan['tasks_sha256'],
                        task_id_sha256=[frozen.digest(task['id']) for task in tasks],
                        saved_author_evidence_sha256=reduced['evidence_sha256'], stable=True),
        raw_exported=False, numeric_task_constants_exported=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--expected-self-sha256', required=True)
    args = parser.parse_args()
    require(args.root == ROOT, 'exact_R136_root')
    require(sha(Path(__file__).read_bytes()) == args.expected_self_sha256, 'auditor_source_pin')
    print(json.dumps(audit(args.root), sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
