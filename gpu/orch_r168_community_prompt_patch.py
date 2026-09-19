"""CPU-only, source-pinned community prompt successor; no lifecycle operations."""

import ast
import hashlib


MARKER = 'R168_FINAL_R154_TWO_BOUNDARY_TEACHING_V2'
POLICY_MARKER = 'ROHIN154_EXISTING_PARENTED_ATTENTION_ALLOCATION_V2'
MAX_SOURCE_BYTES = 1024 * 1024
FINAL_RULES = (
    '\n\n' + MARKER + '\n'
    'These final instructions supersede earlier silence and project-switching advice. '
    'At EACH scheduled parenting opportunity, provide one concrete, brief teaching or '
    'attention-allocation invitation grounded in the shown child TRAIN records. Do not use '
    'silence as the default or wait for an ideal object. Return speak=true with a nonempty '
    'English message of at most 90 words, as Astra, using the unchanged response schema. '
    'Keep rationale a JSON-encoded string containing exactly object_id, source_records, '
    'and disposition; cite actual shown child record indices, not invented evidence. '
    'If the latest own retelling is empty or the live object is unclear, accurately point '
    'to an earlier project or attention problem evidenced in the shown TRAIN records, '
    'explicitly label it earlier, and invite the child to choose whether to continue it '
    'or re-perceive it. Never assert that the child currently remembers it or that an '
    'earlier project is necessarily its current choice. Do not manufacture an object '
    'or evidence if no suitable child record is available. '
    'Keep the SAME chosen project moving. On an exhausted correction, set that repetitive '
    'move aside, not automatically the whole project; choose a genuinely different '
    'evidence-grounded attention or action within it. object_id tracks the actual '
    'mismatch/step identity within the same project, not a lifetime project ID: '
    'preserve it for the same mismatch, never rename an exhausted '
    'mismatch to reset its count. Preserve all delivered-turn counters and the third-turn '
    'set_aside disposition and explicit release wording for that move. '
    'Every message should invite a varied, responsive act of rich re-perception and '
    'judgment about how much or how to look/check; not recurring bullets or introspective '
    'volume. Use genuine Tool receipts to distinguish attempted actions from outcomes; '
    'a child claim of correct code is not verification. No fabricated fallback message, '
    'resend, synthetic result, or replay of an earlier opportunity is permitted. '
    'A failed provider response, invalid response, silence, or publication without '
    'rendering is NOT a delivered turn. These instructions do not bypass validation '
    'or authorize evaluation access, cadence changes, or any child/runtime change.\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cadence_sites(tree, expected):
    selected = {}
    for function in tree.body:
        if not isinstance(function, ast.FunctionDef):
            continue
        matches = []
        if function.name == 'build_config':
            matches = [node.value for node in ast.walk(function) if isinstance(node, ast.keyword)
                       and node.arg == 'cadence_responses']
        elif function.name == 'validate':
            matches = [node.comparators[0] for node in ast.walk(function)
                if isinstance(node, ast.Compare) and len(node.comparators) == 1
                and isinstance(node.left, ast.Subscript)
                and isinstance(node.left.slice, ast.Constant)
                and node.left.slice.value == 'cadence_responses'
                and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq)]
        elif function.name == 'tick':
            matches = [node.right for node in ast.walk(function) if isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Add) and isinstance(node.left, ast.Name)
                and node.left.id == 'baseline']
        else:
            continue
        require(function.name not in selected and len(matches) == 1
                and isinstance(matches[0], ast.Constant) and matches[0].value == expected,
                'exact_cadence_site_'+function.name)
        selected[function.name] = matches[0]
    require(set(selected) == {'build_config', 'validate', 'tick'}, 'three_cadence_sites')
    return selected


def patch_source(source, *, expected_sha256, policy_text):
    """Return new bytes and AST proof; caller separately admits both source closures."""
    require(type(source) is bytes and len(source) <= MAX_SOURCE_BYTES, 'bounded_source')
    require(hashlib.sha256(source).hexdigest() == expected_sha256, 'original_source_pin')
    require(type(policy_text) is str and 0 < len(policy_text.encode()) <= 32768,
            'bounded_policy')
    require(policy_text.count(POLICY_MARKER) == 1 and MARKER not in policy_text,
            'exact_current_policy_marker')
    text = source.decode('utf-8')
    require(MARKER not in text, 'already_patched')
    original = ast.parse(text)
    sites = cadence_sites(original, 3)
    byte_lines = source.splitlines(keepends=True)
    offsets = [sum(map(len, byte_lines[:node.lineno-1]))+node.col_offset for node in sites.values()]
    modified = source
    for offset in sorted(offsets, reverse=True):
        require(modified[offset:offset+1] == b'3', 'exact_cadence_literal')
        modified = modified[:offset] + b'2' + modified[offset+1:]
    functions = [node for node in original.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'prompt']
    require(len(functions) == 1, 'one_prompt')
    function = functions[0]
    require(ast.unparse(function.args) == 'config, state, memory', 'prompt_signature')
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    require(len(returns) == 1 and returns[0] is function.body[-1], 'single_final_return')
    returned = returns[0]
    require(isinstance(returned.value, ast.Tuple)
            and isinstance(returned.value.elts[0], ast.Name)
            and returned.value.elts[0].id == 'instruction', 'instruction_return')
    require('silence is useful' in ast.get_source_segment(text, function),
            'expected_old_community_rules')
    lines = modified.decode('utf-8').splitlines(keepends=True)
    insertion = '    instruction += ' + repr(policy_text + FINAL_RULES) + '\n'
    patched = ''.join(lines[:returned.lineno-1]) + insertion + ''.join(lines[returned.lineno-1:])
    compiled = ast.parse(patched)
    changed = next(node for node in compiled.body if isinstance(node, ast.FunctionDef)
                   and node.name == 'prompt')
    addition = changed.body.pop(-2)
    require(isinstance(addition, ast.AugAssign) and isinstance(addition.op, ast.Add)
            and addition.target.id == 'instruction'
            and addition.value.value == policy_text + FINAL_RULES, 'only_final_literal_append')
    for node in cadence_sites(compiled, 2).values():
        node.value = 3
    require(ast.dump(compiled) == ast.dump(original), 'entire_AST_otherwise_identical')
    output = patched.encode('utf-8')
    require(len(output) <= MAX_SOURCE_BYTES, 'bounded_output')
    compile(patched, '<isolated-community-prompt-successor>', 'exec')
    return output, dict(schema='R168_PARENT_PROMPT_CADENCE_PATCH_V2', marker=MARKER,
        original_sha256=expected_sha256, patched_sha256=hashlib.sha256(output).hexdigest(),
        policy_sha256=hashlib.sha256(policy_text.encode()).hexdigest(),
        final_rules_sha256=hashlib.sha256(FINAL_RULES.encode()).hexdigest(),
        final_instruction_literal_added=True, otherwise_entire_AST_identical=True,
        cadence_changed=dict(before=3, after=2, sites=sorted(sites)),
        validators_changed='cadence equality only', native_changed=False,
        decision_ledger_provider_publication_transport_identical=True,
        delivered_floor_not_guaranteed=True,
        activation_authorized=False)
