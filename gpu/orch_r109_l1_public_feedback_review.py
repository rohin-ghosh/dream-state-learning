"""Post-terminal descriptive revisions; never changes frozen scores or targets."""

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re
import time

from gpu import orch_r109_l1_public_feedback as pilot
from organism_v6 import orch_persist_code as ledger


def diagnostic(public):
    if 'observed' in public:
        return 'INTERPRETER_OUTPUT'
    error = public.get('error', '')
    for text, label in (
        ('JSONDecodeError', 'JSON_DECODE'),
        ('last line must be exactly', 'JSON_SCHEMA'),
        ('expression_required', 'JSON_SCHEMA'),
        ('unknown identifier', 'UNKNOWN_IDENTIFIER'),
        ('arity', 'ARITY'),
        ('SyntaxError', 'EXPRESSION_SYNTAX'),
        ('unsupported expression', 'EXPRESSION_SYNTAX'),
    ):
        if text in error:
            return label
    return 'OTHER_DIAGNOSTIC'


def shape(text):
    stripped = text.strip()
    result = dict(whole_response_json=False, exact_expression_key=False,
                  alternate_expr_key=False, wrapper='NONE', expression=None,
                  identifiers=[], unknown_identifiers=[], uses_list_literal=False,
                  expression_AST_parsed=False, original_expression_AST_valid=False)
    try:
        parsed = json.loads(stripped)
        result.update(whole_response_json=True, wrapper='WHOLE_JSON')
    except ValueError:
        fenced = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', stripped, re.S)
        try:
            parsed = json.loads(fenced[1] if fenced else stripped.splitlines()[-1])
            result['wrapper'] = 'FENCED_JSON' if fenced else 'LAST_LINE_JSON'
        except (ValueError, IndexError):
            return result
    if not isinstance(parsed, dict):
        return result
    result['keys'] = sorted(parsed)
    result['exact_expression_key'] = set(parsed) == {'expression'}
    result['alternate_expr_key'] = 'expr' in parsed
    expression = parsed.get('expression', parsed.get('expr'))
    if not isinstance(expression, str):
        return result
    result['expression'] = expression
    try:
        tree = ast.parse(expression, mode='eval')
        names = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)})
        result.update(expression_AST_parsed=True, identifiers=names,
                      unknown_identifiers=sorted(set(names) - {'values', *ledger.HELPERS}),
                      uses_list_literal=any(isinstance(node, ast.List) for node in ast.walk(tree)))
        ledger.validate_expression(expression)
        result['original_expression_AST_valid'] = True
    except (ValueError, SyntaxError):
        pass
    return result


def revision(before, after, first_public, last_public, frozen):
    initial, final = shape(before), shape(after)
    comparable = initial['expression_AST_parsed'] and final['expression_AST_parsed']
    return dict(raw_changed=before != after,
                expression_changed=initial['expression'] != final['expression'],
                diagnostic_transition=diagnostic(first_public) + '->' + diagnostic(last_public),
                expression_AST_comparable=comparable,
                unknown_identifiers_removed=sorted(set(initial['unknown_identifiers']) - set(final['unknown_identifiers'])) if comparable else [],
                general_values_introduced=bool(comparable and 'values' not in initial['identifiers'] and 'values' in final['identifiers']),
                list_literal_removed=bool(comparable and initial['uses_list_literal'] and not final['uses_list_literal']),
                exact_key_introduced=not initial['exact_expression_key'] and final['exact_expression_key'],
                before_shape=initial, after_shape=final,
                frozen_before_success=frozen['before_success'], frozen_after_success=frozen['after_success'],
                frozen_success_candidate=frozen['verified_failed_to_passed_candidate'],
                descriptive_only=True, functional_admission=False, semantic_review='PENDING')


def review(root, output):
    terminal = pilot.read(root / 'TERMINAL.json')
    guard = pilot.read(root / 'GUARD_TERMINAL.json')
    pilot.require(terminal['status'] == 'COMPLETE' and guard['returncode'] == 0, 'actual_complete_before_review')
    pilot.require(not output.exists() and not output.resolve().is_relative_to(root.resolve()), 'separate_new_review_root')
    output.mkdir(parents=True)
    rows, captures = [], []
    for task in pilot.read(root / 'TASKS.json')['tasks']:
        for branch in pilot.BRANCHES:
            folder = root / 'episodes' / task['id'] / branch
            first = pilot.read(folder / 'draft.CALL.json')
            last = pilot.read(folder / 'continuation.CALL.json')
            first_public = pilot.read(folder / 'draft.PUBLIC.json')
            last_public = pilot.read(folder / 'continuation.PUBLIC.json')
            pilot.require(set(first_public) <= pilot.PUBLIC_KEYS and set(last_public) <= pilot.PUBLIC_KEYS,
                          'public_whitelist_remains_exact')
            frozen = pilot.read(folder / 'COMPLETE.json')
            row = revision(first['response']['raw'], last['response']['raw'], first_public, last_public, frozen)
            row.update(task_id=task['id'], source_task_id=task['source_task_id'], branch=branch,
                       source_files={name:dict(path=str(folder / name), sha256=pilot.sha(folder / name))
                                     for name in ('draft.CALL.json', 'continuation.CALL.json',
                                                  'draft.PUBLIC.json', 'continuation.PUBLIC.json', 'COMPLETE.json')})
            rows.append(row)
            captures.extend([first_public, last_public])
    pilot.write(output / 'NATIVE_REVISION_TABLE.json', rows)
    reductions = {}
    for branch in pilot.BRANCHES:
        selected = [row for row in rows if row['branch'] == branch]
        reductions[branch] = dict(episodes=len(selected),
            counts={key:sum(bool(row[key]) for row in selected) for key in
                    ('raw_changed', 'expression_changed', 'unknown_identifiers_removed', 'general_values_introduced',
                     'list_literal_removed', 'exact_key_introduced', 'frozen_before_success',
                     'frozen_after_success', 'frozen_success_candidate')},
            diagnostic_transitions=dict(Counter(row['diagnostic_transition'] for row in selected)),
            shape_counts={phase:{key:sum(bool(row[phase][key]) for row in selected) for key in
                ('whole_response_json','exact_expression_key','alternate_expr_key','uses_list_literal',
                 'original_expression_AST_valid')} for phase in ('before_shape','after_shape')})
    compact = dict(schema='R109_POST_COMPLETION_DESCRIPTIVE_REVISION_V1', root=str(root), observed_unix=time.time(),
                   review_source_sha256=pilot.sha(__file__), terminal_sha256=pilot.sha(root / 'TERMINAL.json'),
                   guard_terminal_sha256=pilot.sha(root / 'GUARD_TERMINAL.json'),
                   native_table=dict(path=str(output / 'NATIVE_REVISION_TABLE.json'),
                                     sha256=pilot.sha(output / 'NATIVE_REVISION_TABLE.json')),
                   branches=reductions, responses=len(captures),
                   interpreter_outputs=sum('observed' in capture for capture in captures),
                   diagnostic_only_attempts=sum('error' in capture for capture in captures),
                   executed_field_caveat='Frozen public_tests_executed=1 counts attempted probes even if parsing failed; not executed-code or passed-test count.',
                   frozen_scores_unchanged=True, salvaged_text_never_executed_or_rescored=True,
                   raw_and_expressions_node_only=True, fit_updates=0, rows_admitted=0)
    pilot.write(output / 'COMPACT.json', compact)
    print(json.dumps(compact, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    review(arguments.root, arguments.output)
