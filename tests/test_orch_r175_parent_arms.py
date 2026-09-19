import ast
import json
from pathlib import Path

import pytest

from gpu import orch_r175_parent_arms as arms


def sources():
    root = Path(__file__).resolve().parents[1]
    return {name: (root / name).read_text() for name in arms.PATCH_PATHS}


def function_namespace(source, name, namespace):
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<isolated-parent>', 'exec'), namespace)
    return namespace[name]


@pytest.mark.parametrize('arm', list(arms.ARMS))
def test_all_caps_and_actual_provider_parser(arm):
    patched = arms.patch_sources(sources(), arm)
    specification = arms.specification(arm)
    provider = type('Policy', (), {'require': staticmethod(arms.require)})
    parse = function_namespace(patched[arms.PROVIDER_PATH], 'response_schema', {'json': json, 'policy': provider})
    response = dict(speak=True, message=' '.join(['word'] * specification['words']), rationale='evidence')
    assert parse(json.dumps(response)) == response
    response['message'] += ' overflow'
    with pytest.raises(ValueError):
        parse(json.dumps(response))
    response['message'] = 'x' * 4097
    with pytest.raises(ValueError):
        parse(json.dumps(response))
    policy = patched[arms.POLICY_PATH]
    assert f"word_budget = {specification['words']} - len(GRAMMAR.split())" in policy
    assert "if config['community_learner'] or config.get('schedule_on')" not in policy
    assert "'bound_r175_arm'" in policy
    assert 'No result obtained' in policy


@pytest.mark.parametrize('arm', list(arms.ARMS))
def test_configuration_preserves_life_and_training(arm):
    original = dict(root='/unchanged', hard_end_unix=1234, adapter='unchanged',
                    frozen=True, training_enabled=False, nested={'value': 1})
    result = arms.configure(original, arm)
    assert all(result[key] == value for key, value in original.items())
    assert result['schedule_on'] == 'response'
    assert result['cadence_responses'] == arms.ARMS[arm]['cadence']
    result['nested']['value'] = 9
    assert original['nested']['value'] == 1
    if arm == 'A':
        assert result['minimum_duration_seconds'] >= 3600


def test_rejects_drift_and_double_patch():
    original = sources()
    changed = dict(original)
    changed[arms.PROVIDER_PATH] = changed[arms.PROVIDER_PATH].replace('<= 90', '<= 91')
    with pytest.raises(ValueError, match='source_drift'):
        arms.patch_sources(changed, 'A')
    with pytest.raises(ValueError, match='no_double_patch'):
        arms.patch_sources(arms.patch_sources(original, 'A'), 'A')


def test_hands_off_blocks_second_publication():
    source = arms.patch_sources(sources(), 'H')[arms.POLICY_PATH]
    assert "status='HANDS_OFF_BASELINE_PUBLISHED'" in source
    assert source.index("status='HANDS_OFF_BASELINE_PUBLISHED'") < source.index('instruction, payload = prompt(config')


def test_bundle_is_new_and_only_parent_files_change(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / 'source'
    manifest = arms.build_bundle(root, output, 'B')
    assert {name for name, row in manifest['files'].items() if row['changed']} == set(arms.PATCH_PATHS)
    assert json.loads((output / 'ARM_BUNDLE.json').read_text()) == manifest
    with pytest.raises(FileExistsError):
        arms.build_bundle(root, output, 'B')
