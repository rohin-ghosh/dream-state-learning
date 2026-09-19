"""Opt-in R225 repair for assurances and static print-wrapped targets.

R213 evidence remains reproducible. This policy only narrows its eligibility;
it neither verifies claims nor edits targets, prefixes, or historical rows.
"""

import ast
import re

from organism_v6 import orch_r213_content_target_filter as legacy


POLICY = 'R225_CONTENT_BEARING_TARGETS_V2'
ASSURANCE = re.compile(r'\b(?:I|we)\s+(?:will\s+|now\s+|will\s+now\s+)?assume\b|'
    r'\b(?:I|we)\s+(?:believe|think|know|am confident|are confident)\b.{0,180}'
    r'\b(?:adequate|adequacy|accurate|correct|completed|complete|sufficient|requirements|criteria)\b|'
    r'\b(?:my|our|the)\s+(?:previous\s+|current\s+|resulting\s+)?'
    r'(?:assessments?|understanding|abstract|report|answer|reply|draft)\b.{0,100}'
    r'\b(?:adequate|accurate|correct|sufficient|meets? the|satisfies?)\b', re.I)
REFLECTIVE_ACTIVITY = re.compile(r'\b(?:reflective practices?|metacognitive techniques?|'
    r'reflections?|self.assessment|assessing our progress|our development)\b', re.I)
GENERIC_BENEFIT = re.compile(r'\b(?:beneficial|enhance|enhances|enhancements|improve|'
    r'improves|improvements|advancement|development|progress|performance)\b', re.I)
MEASUREMENT = re.compile(r'\b\d+(?:\.\d+)?\s*(?:/\s*\d+|%|rows?|updates?|'
    r'sleeps?|seeds?|steps?|captions?|trials?|pairs?|tokens?)\b', re.I)
PROSE_LABEL = re.compile(r'\b(?:abstract|essay|prose)\b', re.I)
EXPLICIT_CALCULATION = re.compile(r'\b\d+(?:\.\d+)?\s*[+*/−-]\s*\d+(?:\.\d+)?'
    r'\s*=\s*[-+]?\d')
PARENT_QUESTION = re.compile(r'^\s*(?:[-*]\s+)?(?:Astra|Parent)\s*[:,]\s*\S.*\?\s*$', re.I)


def _static_string(node, names):
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.Name):
        return node.id in names
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_string(node.left, names) and _static_string(node.right, names)
    if isinstance(node, ast.JoinedStr):
        return all(_static_string(part, names) for part in node.values)
    if isinstance(node, ast.FormattedValue):
        return _static_string(node.value, names) and (
            node.format_spec is None or _static_string(node.format_spec, names))
    return False


def _static_display_only(body):
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError, RecursionError):
        return False
    names, displayed = set(), False
    for statement in tree.body:
        if isinstance(statement, ast.Pass):
            continue
        if isinstance(statement, ast.Assign) and all(
                isinstance(target, ast.Name) for target in statement.targets):
            if not _static_string(statement.value, names):
                return False
            names.update(target.id for target in statement.targets)
            continue
        if not isinstance(statement, ast.Expr):
            return False
        if isinstance(statement.value, ast.Constant):
            continue
        call = statement.value
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == 'print' and call.args
                and all(_static_string(argument, names) for argument in call.args)
                and all(keyword.arg in ('sep', 'end')
                    and _static_string(keyword.value, names) for keyword in call.keywords)):
            return False
        displayed = True
    return displayed


def _assurance_only(unit):
    stripped = legacy.LABEL.sub('', unit.strip()).strip()
    if len(legacy.ARITHMETIC.findall(stripped)) >= 2 or EXPLICIT_CALCULATION.search(stripped):
        return False
    unquoted = re.sub(r'"[^"\n]*"|“[^”\n]*”|(?<!\w)\x27[^\x27\n]*\x27(?!\w)|‘[^’\n]*’', '', stripped)
    if ASSURANCE.search(unquoted):
        return True
    return bool(REFLECTIVE_ACTIVITY.search(stripped) and GENERIC_BENEFIT.search(stripped)
        and not MEASUREMENT.search(stripped)
        and not legacy.ARITHMETIC.search(stripped))


def scan_target(text, token_ids=None):
    evidence = legacy.scan_target(text, token_ids)
    if evidence['scan_truncated']:
        return evidence
    units = [dict(unit) for unit in evidence['units']]
    wrapped = list(evidence['code_wrapped_prose'])
    static_displays = []
    fences = {(match.start(), match.end()): match for match in legacy.FENCE.finditer(text)}
    for unit in units:
        fence = fences.get((unit['start'], unit['end']))
        if fence is not None:
            language, body = fence.group(2).strip().lower(), fence.group(3)
            if language in ('', 'py', 'python', 'python3'):
                if _static_display_only(body):
                    unit.update(classification='meta', reason='static_print_is_not_a_computed_artifact')
                    static_displays.append(dict(start=unit['start'], end=unit['end']))
                    if PROSE_LABEL.search(text) and len(legacy.WORD.findall(body)) >= 8:
                        wrapped.append(dict(start=fence.start(), end=fence.end(), language=language,
                            reason='child_labelled_prose_inside_code_fence'))
            continue
        original = text[unit['start']:unit['end']]
        if _static_display_only(original.strip()):
            unit.update(classification='meta', reason='static_print_is_not_a_computed_artifact')
            static_displays.append(dict(start=unit['start'], end=unit['end']))
        elif PARENT_QUESTION.fullmatch(original) and not legacy.DEFERRED_QUESTION.search(original):
            unit.update(classification='content', reason='actual_addressed_parent_question')
        elif _assurance_only(original):
            unit.update(classification='meta', reason='assurance_or_generic_reflection_without_artifact')
    content = sum(unit['classification'] == 'content' for unit in units)
    meta = sum(unit['classification'] == 'meta' for unit in units)
    unknown = sum(unit['classification'] == 'unknown' for unit in units)
    classification = ('mixed' if meta or unknown else 'content') if content else (
        'meta_only' if meta else 'uncertain')
    if evidence['repetition_findings']:
        classification = 'repetition_collapse'
    elif wrapped:
        classification = 'code_wrapped_prose'
    return dict(evidence, units=units, content_units=content, meta_units=meta,
        unknown_units=unknown, classification=classification, code_wrapped_prose=wrapped,
        eligible=bool(content) and not evidence['repetition_findings'] and not wrapped,
        classifier_policy=POLICY, static_display_spans=static_displays)


def apply_question_policy(text, evidence, policy):
    from organism_v6.orch_r220_question_target_filter import apply_question_policy as original

    result = original(text, evidence, policy)
    questions = result['question_target_filter']['questions']
    valid = [question for question in questions if not any(
        question['start'] < span['end'] and span['start'] < question['end']
        for span in evidence.get('static_display_spans', []))]
    result['question_target_filter']['questions'] = valid
    result['question_target_filter']['static_display_questions_excluded'] = len(questions) - len(valid)
    if result.get('classification') == 'addressed_question' and not valid:
        result.update(eligible=evidence['eligible'], classification=evidence['classification'])
        result.pop('base_classification', None)
    return result
