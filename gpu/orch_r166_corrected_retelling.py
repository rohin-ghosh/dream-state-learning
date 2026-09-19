"""Prospective TRAIN invitation patch; never manufactures a corrected target."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path


SCHEMA = 'R166_CORRECTED_RETELLING_V1'
DIRECTIVE_SHA256 = 'af4e4414563fdc37a2f7994680d017454dd03e8085b22911cb5bdd0da693a41f'
VARIANTS = ('free_distillation', 'parent_guided_distillation')
INVITATION = (
    'Before sleep, carry forward the actual object or project you have been working on '
    'in the visible conversation. Retell it in your own words with concrete details that '
    'matter, a useful connection or another angle, and the next step you can justify. '
    'Keep the object moving forward rather than repeat a template or invent a new project. '
    'Include the most recent correction actually visible in your conversation: distinguish '
    'what you previously claimed, what the real feedback '
    'or evidence showed, and what you now hold, including anything still unresolved. '
    'Keep a justified correction rather than restoring the earlier claim. If the same '
    'correction has returned, notice that and consider why. Decide what deserves closer '
    'perception or checking, how to examine it, and how much attention is worthwhile. '
    'Ground that judgment in a concrete uncertainty or observation, not repeated claims '
    'of being reflective. Do not invent a correction, result, or certainty, and do not '
    'copy your parent\'s words. Use ordinary prose, not a required set of headings. '
    'If no correction is visible, keep what your actual experience supports without '
    'inventing one. If no object is visible, acknowledge that rather than fabricate a '
    'memory of work. Proposed actions are not executed results.'
)
OLD_INVITATION = "    invitation_text = child.plan['compaction_invitation']\n"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def validate_scope(scope):
    require(type(scope) is dict and set(scope) == {
        'schema', 'root', 'directive_sha256', 'parented', 'presleep_variant'}, 'exact_retelling_scope')
    require(scope['schema'] == SCHEMA and scope['directive_sha256'] == DIRECTIVE_SHA256,
            'bound_Rohin150_directive')
    require(scope['parented'] is True and scope['presleep_variant'] in VARIANTS,
            'parented_distilling_life_only')
    root = scope['root']
    require(type(root) is str and Path(root).is_absolute() and str(Path(root)) == root
            and '..' not in Path(root).parts, 'canonical_scoped_life_root')
    return scope


def invitation(child, stream, journal, cycle, scope):
    validate_scope(scope)
    require(child.plan['root'] == scope['root']
            and child.plan.get('presleep_variant', 'free_distillation') == scope['presleep_variant'],
            'exact_retelling_life_and_original_variant')
    require(type(cycle) is int and cycle > 0 and stream.pending is None and stream.sleep_due,
            'completed_experience_presleep_boundary')
    parent_refs = []
    for event in stream.history.events[stream.history.visible_frontier.event_count:]:
        require(event.split == 'TRAIN', 'TRAIN_history_only')
        if event.actor == 'parent':
            parent_refs.append(dict(event_id=event.event_id, source_sha256=event.source_sha256))
    journal.record('PRESLEEP_RETELLING_INVITATION', dict(schema=SCHEMA,
        cycle=cycle, scope=scope, scope_sha256=digest(scope),
        invitation_sha256=hashlib.sha256(INVITATION.encode()).hexdigest(),
        original_invitation_sha256=hashlib.sha256(child.plan['compaction_invitation'].encode()).hexdigest(),
        pre_render_parent_references=parent_refs,
        actual_exposure_evidence='SUBSEQUENT_REQUEST_RENDER_RECEIPT',
        incoming_parent_messages='READ_BY_UNCHANGED_NATIVE_STEP_AFTER_THIS_RECORD',
        raw_birth_and_experiment_unchanged=True, target_rewritten=False,
        correction_correctness='NOT_VERIFIED_BY_INVITATION', optimizer_recipe_unchanged=True))
    return INVITATION


def without_prepare_sleep(tree):
    result = deepcopy(tree)
    nodes = [node for node in result.body if isinstance(node, ast.FunctionDef)
             and node.name == 'prepare_sleep']
    require(len(nodes) == 1, 'one_native_prepare_sleep')
    nodes[0].body = [ast.Pass()]
    return ast.dump(result, include_attributes=False)


def patch_source(source, scope):
    validate_scope(scope)
    require(type(source) is str and 'orch_r166_corrected_retelling' not in source,
            'new_retelling_source_handoff_only')
    require(source.count(OLD_INVITATION) == 1, 'exact_native_invitation_block')
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name == 'prepare_sleep']
    require(len(nodes) == 1 and OLD_INVITATION.strip() in ast.get_source_segment(source, nodes[0]),
            'invitation_inside_prepare_sleep')
    replacement = ('    from gpu.orch_r166_corrected_retelling import invitation as retelling_invitation\n'
                   '    invitation_text = retelling_invitation(child, stream, journal, cycle, '
                   + repr(scope) + ')\n')
    patched = source.replace(OLD_INVITATION, replacement)
    require(without_prepare_sleep(tree) == without_prepare_sleep(ast.parse(patched)),
            'all_non_presleep_AST_unchanged')
    compile(patched, '<r166-isolated-native>', 'exec')
    return patched
