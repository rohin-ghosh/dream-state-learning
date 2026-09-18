"""Pure, source-pinned R150 guard transformation for new frozen snapshots only."""

import ast
import hashlib


ORIGINAL_SHA256 = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'
OLD_VALIDATION = "    plan = child.validate_plan(child.read(config['plan_path']))\n"
NEW_VALIDATION = OLD_VALIDATION + """    from gpu import orch_r150_matched_native as matched
    matched.validate_plan(plan)
    child.require(config.get('phase') in ('initialize', 'run'), 'r150_explicit_phase')
    child.require(type(config.get('resume')) is bool, 'r150_explicit_resume_boolean')
    child.require(config.get('matched_cohort_sha256') == plan['matched_cohort']['sha256'],
                  'r150_exact_cohort_binding')
    child.require(config.get('matched_arm') == plan['matched_arm'], 'r150_exact_arm_binding')
    child.require(config['phase'] != 'initialize'
        or (config['matched_arm'] == 'parented_learning' and config['resume'] is False),
                  'r150_designated_fresh_initializer')
"""
OLD_DISPATCH = "    child.run(config['plan_path'], resume=config['resume'])\n"
NEW_DISPATCH = """    from gpu import orch_r150_matched_native as matched
    os.environ['R150_COHORT_SHA256'] = config['matched_cohort_sha256']
    if config['phase'] == 'initialize':
        matched.initialize(config['plan_path'])
    else:
        matched.run(config['plan_path'], resume=config['resume'])
"""


def _text(source):
    if not isinstance(source, str):
        raise TypeError('guard_source_must_be_text')
    return source


def _original(source):
    _text(source)
    if 'orch_r150_matched_native' in source or 'R150_COHORT_SHA256' in source:
        raise ValueError('prepatched_guard_source')
    if source.count(OLD_VALIDATION) != 1 or source.count(OLD_DISPATCH) != 1:
        raise ValueError('unsupported_or_duplicate_guard_blocks')
    if hashlib.sha256(source.encode('utf-8')).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('unsupported_frozen_guard_sha256')


def _non_target_ast(source):
    tree = ast.parse(source)
    for name in ('validate', 'native_entry'):
        targets = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
        if len(targets) != 1:
            raise ValueError('exact_guard_target_functions_required')
        targets[0].body = [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def _render(source):
    return source.replace(OLD_VALIDATION, NEW_VALIDATION).replace(OLD_DISPATCH, NEW_DISPATCH)


def revert_source(patched: str) -> str:
    """Verify and reverse only this exact patch; reject any additional edits."""
    _text(patched)
    if patched.count(NEW_VALIDATION) != 1 or patched.count(NEW_DISPATCH) != 1:
        raise ValueError('unsupported_or_duplicate_patched_guard_blocks')
    original = patched.replace(NEW_VALIDATION, OLD_VALIDATION).replace(NEW_DISPATCH, OLD_DISPATCH)
    _original(original)
    if _render(original) != patched or _non_target_ast(original) != _non_target_ast(patched):
        raise ValueError('guard_patch_changed_non_target_source')
    compile(patched, '<r150-frozen-guard>', 'exec')
    return original


def patch_source(source: str) -> str:
    """Return patched UTF-8 source text without reading, writing, or executing it."""
    _original(source)
    patched = _render(source)
    if revert_source(patched) != source:
        raise ValueError('guard_patch_not_exactly_reversible')
    return patched
