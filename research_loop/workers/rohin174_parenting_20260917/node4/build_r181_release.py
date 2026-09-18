"""Prepare an inspectable R181 variant of the existing exact-state handoff."""

import ast
import hashlib
import json
from pathlib import Path
import shutil


HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
OLD = REPO / 'research_loop/workers/r179_context_survival_20260917/node4'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace(source, before, after):
    require(source.count(before) == 1, 'unique_existing_handoff_seam:' + before[:75])
    return source.replace(before, after, 1)


def replace_function(source, name, text):
    tree = ast.parse(source)
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + text.rstrip() + '\n' + ''.join(lines[node.end_lineno:])


HANDLER = '''def handler(physical, config):
    require(physical in ALLOWLIST and 'device_containment' in config, 'preserve_current_strict_confinement')
    module = ('gpu.orch_r179_node4_legacy_containment' if physical in (0, 1) else
        'gpu.orch_r144_a40r4_strict' if physical == 4 else 'gpu.orch_r137_node4_containment')
    return dict(module=module, supervisor='contained-supervise', inner='contained-native')
'''

SELECTED = '''def selected(physical, helpers):
    require(physical in ALLOWLIST, 'only_four_current_learning_lives')
    helpers.current_node('a40r')
    current = helpers.read(Path(__file__).parent / 'CURRENT.json')[str(physical)]
    config_path = Path(current['guard_path'])
    config, plan, original = helpers.originals(config_path)
    require(plan['root'] == current['root'] and plan['physical'] == physical
        and plan['gpu_uuid'] == helpers.LANES['a40r'][physical][1], 'exact_current_life_UUID')
    require(helpers.sha(config_path) == current['guard_sha256']
        and helpers.sha(Path(plan['source_root']) / NATIVE) == current['source_sha256'], 'exact_current_guard_and_native')
    require(plan['hard_end_unix'] == config['hard_end_unix'] == 1789754400, 'unchanged_original_wall')
    actor = helpers.identity(current['actor']['pid'])
    require(actor['start_ticks'] == current['actor']['start_ticks'], 'current_exact_PID_start_ticks')
    timer = helpers.identity(actor['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=helpers.identity(timer['parent']))
    launch = helpers.read(Path(config['attempt_dir']) / 'LAUNCH.json')
    validate_pair(pair, config_path, config, plan, launch, helpers)
    return config_path, config, plan, original, pair
'''


def build(output):
    output = Path(output).resolve()
    require(output.parent == HOME and not output.exists(), 'new_owned_release_only')
    output.mkdir()
    original = (OLD / 'node4_rollout.py').read_text()
    source = replace_function(original, 'handler', HANDLER)
    source = replace_function(source, 'selected', SELECTED)
    source = replace(source, "module = helpers.module_from_file('r179_exact_policy', bundle / 'policy.py')\n    patched = module.patch_native((source / NATIVE).read_text())",
        "module = helpers.module_from_file('r181_exact_delta', bundle / 'r181_native_delta.py')\n    patched = module.patch_native((source / NATIVE).read_text(), (bundle / 'MAIN_NATIVE.py').read_text())")
    start = source.index("    require(not (source / POLICY).exists(), 'new_policy_only')")
    end = source.index('    after = helpers.inventory_files(source)', start)
    source = source[:start] + "    require(helpers.sha(source / POLICY) == POLICY_SHA and helpers.sha(source / PREFLIGHT) == PREFLIGHT_SHA, 'existing_R179_and_preflight_unchanged')\n    if legacy:\n        require(helpers.sha(source / LEGACY) == LEGACY_SHA, 'existing_legacy_confinement_unchanged')\n" + source[end:]
    source = replace(source, '    proposed = helpers.relocated_plan(plan, source)\n',
        "    proposed = helpers.relocated_plan(plan, source)\n    proposed['rehearsal_presentations'] = 0\n")
    source = replace(source, "builder_line='[Builder] 2026-09-17 R179 NODE4 actual-source CPU/provenance PASS; unchanged life, wall and state.'",
        "builder_line='[Builder] 2026-09-17 R181 NODE4 actual-source CPU/provenance PASS; NEW16 no old rehearsal, same anchor, exact saved state and wall.'")
    original_tree = ast.parse(original)
    changed_tree = ast.parse(source)
    unchanged = ('handoff', 'preflight_scan', 'saved_evidence', 'monitor', 'validate_pair', 'validate_occupied_preflight')
    for name in unchanged:
        before = next(node for node in original_tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        after = next(node for node in changed_tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        require(ast.dump(before) == ast.dump(after), 'unchanged_exact_handoff_and_admission:' + name)
    (output / 'node4_rollout.py').write_text(source)
    cpu = (OLD / 'cpu_actual.py').read_text()
    cpu = replace(cpu, "require(policy.patch_native((predecessor / 'gpu/orch_r125_continual_native.py').read_text()) ==\n            Path(native.__file__).read_text(), 'only_exact_Main_patch')",
        "import importlib.util\n    spec = importlib.util.spec_from_file_location('r181_delta', Path(__file__).with_name('r181_native_delta.py'))\n    delta = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(delta)\n    require(delta.patch_native((predecessor / 'gpu/orch_r125_continual_native.py').read_text(), Path(__file__).with_name('MAIN_NATIVE.py').read_text()) == Path(native.__file__).read_text(), 'only_exact_Main_R181_delta')\n    require(native.select_rehearsal_rows(plan={'rehearsal_presentations': 0}, old_rows=[{'archived': True}]) == [], 'zero_old_rows_before_encoding')\n    require(len(native.presentation_schedule([{'new': True}] * 3, [])) == 48, 'NEW16_typical_three_rows_48')")
    (output / 'cpu_actual.py').write_text(cpu)
    shutil.copyfile(HOME / 'r181_native_delta.py', output / 'r181_native_delta.py')
    shutil.copyfile(REPO / 'gpu/orch_r125_continual_native.py', output / 'MAIN_NATIVE.py')
    shutil.copyfile(REPO / 'tests/test_orch_r125_continual_native.py', output / 'main_native_tests.py')
    status = json.loads((HOME / 'R178_ACTUAL_STATUS_20260917T2141Z.json').read_text())
    (output / 'CURRENT.json').write_text(json.dumps({str(row['physical']): row for row in status['rows']}, sort_keys=True, indent=2) + '\n')
    proof = dict(schema='R181_EXISTING_HANDOFF_SMALL_DELTA_V1', status='BUILT_NOT_ROLLED_OUT',
        exact_unchanged_handoff_functions=list(unchanged), original_operator_sha256=sha(OLD / 'node4_rollout.py'),
        Main_native_sha256=sha(output / 'MAIN_NATIVE.py'), Main_test_sha256=sha(output / 'main_native_tests.py'),
        files={path.name: sha(path) for path in output.iterdir() if path.is_file()},
        source_delta='R181 native only; existing R179, suffix, guard, scanner and confinement byte-preserved',
        plan_delta=dict(new_presentations=16, rehearsal_presentations=0, anchor_lambda=0.25),
        raw_pair_same_prospective_recipe=True, native_signals=0)
    (output / 'BUILD_RECEIPT.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    return proof


if __name__ == '__main__':
    import sys
    print(json.dumps(build(sys.argv[1]), sort_keys=True))
