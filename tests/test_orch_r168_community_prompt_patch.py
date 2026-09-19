"""Synthetic CPU checks only: no provider, remote, publication, or teaching proof."""

import ast
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from gpu import orch_r153_community_parents as community
from gpu import orch_r166_parent_policy as policy
from gpu import orch_r168_community_prompt_patch as successor


SOURCE = Path(community.__file__).read_bytes()
SOURCE_SHA = hashlib.sha256(SOURCE).hexdigest()


def build(source=SOURCE, expected=SOURCE_SHA, text=policy.PROMPT_POLICY):
    return successor.patch_source(source, expected_sha256=expected, policy_text=text)


def patched_prompt():
    raw, receipt = build()
    tree = ast.parse(raw)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'prompt')
    namespace = dict(vars(community))
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<CPU-fixture>', 'exec'), namespace)
    return namespace['prompt'], receipt


def test_final_policy_after_old_rules_and_payload_unchanged():
    function, receipt = patched_prompt()
    state = dict(events=[dict(actor='child', record_index=12, record_sha256='a'*64,
        text='My earlier map story'), dict(actor='child', record_index=13, text='{}')])
    memory = dict(object_delivered_turns={'map-summary-loop': 3})
    with patch.object(community.parent, 'prompt', return_value=('original PRINCIPLES', 'unused')):
        old_instruction, old_payload = community.prompt({'branch': 'C1'}, state, memory)
        instruction, payload = function({'branch': 'C1'}, state, memory)
    assert instruction == old_instruction + policy.PROMPT_POLICY + successor.FINAL_RULES
    assert instruction.rindex(successor.POLICY_MARKER) > instruction.index('silence is useful')
    assert instruction.endswith(successor.FINAL_RULES)
    assert payload == old_payload
    assert json.loads(payload)['object_delivered_turns'] == {'map-summary-loop': 3}
    assert receipt['otherwise_entire_AST_identical']


@pytest.mark.parametrize('phrase', [
    'At EACH scheduled parenting opportunity', 'Return speak=true', 'at most 90 words',
    'explicitly label it earlier', 'Never assert that the child currently remembers',
    'never rename an exhausted', 'set that repetitive move aside',
    'not automatically the whole project', 'actual shown child record indices',
    'No fabricated fallback message', 'NOT a delivered turn', 'do not bypass validation',
    'how much or how to look/check', 'No receipt means no verified outcome',
])
def test_final_contract(phrase):
    assert phrase in policy.PROMPT_POLICY + successor.FINAL_RULES


def test_entire_module_except_addition_identical():
    output, unused = build()
    original, result = ast.parse(SOURCE), ast.parse(output)
    changed = next(node for node in result.body if isinstance(node, ast.FunctionDef)
                   and node.name == 'prompt')
    changed.body.pop(-2)
    for node in successor.cadence_sites(result, 2).values():
        node.value = 3
    assert ast.dump(original) == ast.dump(result)


def test_silence_remains_silence_not_fabricated_publication():
    assert community.decision(dict(speak=False, message='', rationale=''), {}, {}) is None


def test_exhausted_mismatch_still_refused():
    reply = dict(speak=True, message='Look at your map.', rationale=json.dumps(dict(
        object_id='map-loop', source_records=[12], disposition='continue')))
    with pytest.raises(ValueError, match='object_delivered_budget_exhausted'):
        community.decision(reply, dict(events=[dict(actor='child', record_index=12)]),
                           dict(object_delivered_turns={'map-loop': 3}))


def test_same_project_different_move_and_release_accepted_without_counter_reset():
    memory = dict(object_delivered_turns={'map-summary-loop': 3, 'map-observation-choice': 2})
    reply = dict(speak=True, message='Set this correction aside. Which map detail would you inspect next?',
        rationale=json.dumps(dict(object_id='map-observation-choice', source_records=[12],
                                  disposition='set_aside')))
    community.decision(reply, dict(events=[dict(actor='child', record_index=12)]), memory)
    assert memory['object_delivered_turns'] == {'map-summary-loop': 3, 'map-observation-choice': 2}


def patched_namespace():
    raw, unused = build()
    namespace = dict(vars(community))
    functions = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef)
                 and node.name in ('validate', 'build_config', 'tick', 'prompt')]
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<CPU-cadence-fixture>', 'exec'), namespace)
    return namespace


def test_build_config_and_validate_require_two_not_three(tmp_path):
    namespace = patched_namespace()
    source = tmp_path/'principles.md'
    source.write_text('CPU fixture; not real teaching.')
    template = dict(programme_path=str(source), programme_sha256=community.parent.sha(source),
        principles_path=str(source), principles_sha256=community.parent.sha(source))
    config = namespace['build_config'](template, learner_id='C1', node='ovx3',
        root='/localhome/local-rohing/orch_r153_fixture/C1',
        source_root='/localhome/local-rohing/orch_r153_fixture/source', hard_end_unix=9999999999)
    assert config['cadence_responses'] == 2 and config['object_turn_limit'] == 3
    with pytest.raises(ValueError, match='fixed_sparse_low_effort_budget'):
        namespace['validate'](dict(config, cadence_responses=3))


@pytest.mark.parametrize('count,awaiting,expected', [
    (96, False, 'SPARSE_WAIT'), (97, False, 'SPARSE_WAIT'),
    (98, False, 'SILENT'), (99, False, 'SILENT'), (100, True, 'AWAITING_RENDER')])
def test_two_boundary_schedule_keeps_pending_guard_and_no_fake_reply(tmp_path, count, awaiting, expected):
    namespace = patched_namespace()
    namespace['validate'] = lambda config: config
    namespace['snapshot'] = lambda repository, config: dict(response_count=count)
    namespace['ledger'] = lambda output, state: dict(last_response_count=96, awaiting_render=awaiting)
    namespace['prompt'] = lambda config, state, memory: ('CPU fixture', 'CPU fixture')
    config = dict(start_after_response_count=0, hard_end_unix=9999999999)
    with patch.object(community.parent, 'strong', return_value=(
            dict(speak=False, message='', rationale=''), community.parent.STRONG, {})) as provider, \
            patch.object(community.parent, 'publish') as publication:
        assert namespace['tick'](tmp_path, config, tmp_path) == expected
        assert provider.call_count == int(expected == 'SILENT')
        publication.assert_not_called()
    if expected == 'SILENT':
        result = json.loads((tmp_path/f'parent_{count:012d}'/'RESULT.json').read_bytes())
        assert result['status'] == 'SILENT' and 'publication' not in result


@pytest.mark.parametrize('mutation', ['hash', 'double', 'policy', 'returns', 'signature', 'oversize'])
def test_refusals(mutation):
    source, expected, text = SOURCE, SOURCE_SHA, policy.PROMPT_POLICY
    if mutation == 'hash':
        expected = '0'*64
    elif mutation == 'double':
        source, unused = build()
        expected = hashlib.sha256(source).hexdigest()
    elif mutation == 'policy':
        text = 'old rules'
    elif mutation == 'returns':
        source = source.replace(b'def prompt(config, state, memory):',
            b'def prompt(config, state, memory):\n    if not state: return None')
        expected = hashlib.sha256(source).hexdigest()
    elif mutation == 'signature':
        source = source.replace(b'def prompt(config, state, memory):', b'def prompt(config, state):')
        expected = hashlib.sha256(source).hexdigest()
    else:
        source = b' ' * (successor.MAX_SOURCE_BYTES+1)
        expected = hashlib.sha256(source).hexdigest()
    with pytest.raises(ValueError):
        build(source, expected, text)
