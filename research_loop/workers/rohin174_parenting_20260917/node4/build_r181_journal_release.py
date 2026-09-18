"""Fresh R181 plus minimal journal-cache bundle; unchanged handoff custody."""

import ast
import json
from pathlib import Path
import shutil

import build_r181_release as previous
import r181_journal_delta as journal


HOME = Path(__file__).resolve().parent
OLD = HOME / 'r181_release_20260917T2150Z'
CAPTURE = HOME / 'journal_sources_20260917T2212Z'
JOURNAL = 'gpu/orch_r125_stream_journal.py'


def build(output):
    output = Path(output).resolve()
    previous.require(output.parent == HOME and not output.exists(), 'new_owned_journal_release_only')
    previous.require(previous.sha(CAPTURE / 'MAIN_JOURNAL.py') == journal.MAIN_SHA, 'captured_Main_journal')
    for name in ('DEPLOYED_014.py', 'DEPLOYED_3.py'):
        journal.patch_journal((CAPTURE / name).read_text(), (CAPTURE / 'MAIN_JOURNAL.py').read_text())
    output.mkdir()
    for path in OLD.iterdir():
        if path.is_file() and path.name != 'BUILD_RECEIPT.json':
            shutil.copyfile(path, output / path.name)
    shutil.copyfile(HOME / 'r181_journal_delta.py', output / 'r181_journal_delta.py')
    shutil.copyfile(CAPTURE / 'MAIN_JOURNAL.py', output / 'MAIN_JOURNAL.py')
    shutil.copyfile(CAPTURE / 'MAIN_TESTS.py', output / 'MAIN_JOURNAL_TESTS.py')
    original = (OLD / 'node4_rollout.py').read_text()
    source = previous.replace(original, "    after = helpers.inventory_files(source)\n",
        "    journal_delta = helpers.module_from_file('actual_journal_delta', bundle / 'r181_journal_delta.py')\n"
        "    journal_path = source / 'gpu/orch_r125_stream_journal.py'\n"
        "    journal_text = journal_delta.patch_journal(journal_path.read_text(), (bundle / 'MAIN_JOURNAL.py').read_text())\n"
        "    journal_mode = stat.S_IMODE(journal_path.stat().st_mode)\n"
        "    journal_path.chmod(journal_mode | stat.S_IWUSR)\n"
        "    journal_path.write_text(journal_text)\n"
        "    journal_path.chmod(journal_mode)\n"
        "    after = helpers.inventory_files(source)\n")
    source = previous.replace(source,
        "    expected = dict(before, **{NATIVE: helpers.sha(source / NATIVE), POLICY: POLICY_SHA, PREFLIGHT: PREFLIGHT_SHA})\n",
        "    expected = dict(before, **{NATIVE: helpers.sha(source / NATIVE), POLICY: POLICY_SHA, PREFLIGHT: PREFLIGHT_SHA, 'gpu/orch_r125_stream_journal.py': helpers.sha(journal_path)})\n")
    (output / 'node4_rollout.py').write_text(source)
    cpu = (OLD / 'cpu_actual.py').read_text()
    cpu = previous.replace(cpu, '    prepare, integration = presleep_function(native)\n',
        "    spec = importlib.util.spec_from_file_location('journal_delta', Path(__file__).with_name('r181_journal_delta.py'))\n"
        "    journal_delta = importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(journal_delta)\n"
        "    actual_journal = source / 'gpu/orch_r125_stream_journal.py'\n"
        "    require(journal_delta.patch_journal((predecessor / 'gpu/orch_r125_stream_journal.py').read_text(), Path(__file__).with_name('MAIN_JOURNAL.py').read_text()) == actual_journal.read_text(), 'exact_actual_journal_cache_overlay')\n"
        "    cache_proof = journal_delta.run_cache_tests(Path(__file__).with_name('MAIN_JOURNAL_TESTS.py'))\n"
        "    require(cache_proof['passed'] == 5, 'five_Main_cache_tests_on_actual_source')\n"
        "    prepare, integration = presleep_function(native)\n")
    (output / 'cpu_actual.py').write_text(cpu)
    before = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
    after = {node.name: ast.dump(node) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    previous.require(set(before) == set(after), 'no_new_custody_functions')
    for name in before.keys() - {'stage'}:
        previous.require(before[name] == after[name], 'unchanged_handoff_function:' + name)
    proof = dict(schema='NODE4_R181_JOURNAL_CACHE_BUNDLE_V1', status='BUILT_NOT_LOADED',
        native_patch_unchanged=True, Main_journal_sha256=journal.MAIN_SHA,
        old_journal_shas=sorted(journal.ORIGINAL_SHAS), journal_methods_only=list(journal.REPLACED + journal.ADDED),
        deployed_transition_validation_preserved=True, unchanged_custody_and_admission=True,
        predecessor_bundle=str(OLD), files={path.name: previous.sha(path) for path in output.iterdir() if path.is_file()},
        child_signals=0, parent_publications=0)
    (output / 'BUILD_RECEIPT.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    return proof


if __name__ == '__main__':
    import sys
    print(json.dumps(build(sys.argv[1]), sort_keys=True))
