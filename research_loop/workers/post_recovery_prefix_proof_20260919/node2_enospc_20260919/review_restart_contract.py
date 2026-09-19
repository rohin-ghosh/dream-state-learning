"""Bounded CPU-only review probes against exact helper and test bytes."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HELPER_SHA = 'ce7fda824274563985a66020ca5f3b0afb59865f13adc00af304acf1111d67a1'
TEST_SHA = 'baf2771b55e7584aa8bd061360aca4c8a96fb7e380aeb029b112c14139c626eb'


def load_module(name, path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('reviewed_source_changed:' + str(path))
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def run():
    directory = Path(__file__).resolve().parents[2] / 'post_recovery_node2_sleep_20260919'
    helper = load_module('restart_contract', directory / 'restart_contract.py', HELPER_SHA)
    tests = load_module('reviewed_restart_tests', directory / 'test_restart_contract.py', TEST_SHA)

    def fixture():
        case = tests.RestartContractTests()
        case.setUp()
        return case

    outcomes = []
    case = fixture()
    baseline = case.contract()['contract']
    case.options['new_presentations'] = 2
    altered = case.contract()['contract']
    assert altered['new_presentations'] == 2
    outcomes.append(dict(probe='changed_recipe_presentation_count_accepted',
        original_presentations=baseline['new_presentations'], accepted_presentations=2,
        original_total=baseline['pending_rows'] * baseline['new_presentations'],
        accepted_total=altered['pending_rows'] * altered['new_presentations']))

    case = fixture()
    original_updates = deepcopy(case.updates)
    case.updates = case.updates[:1]
    altered = case.contract()['contract']
    assert altered['recorded_uncheckpointed_updates'] == 1
    outcomes.append(dict(probe='known_update_suffix_omitted_accepted',
        fixture_durable_update_count=len(original_updates), accepted_count=1,
        missing_indices=[item['index'] for item in original_updates[1:]],
        still_requires_full_journal_verification=altered['full_journal_tail_verification_required']))

    case = fixture()
    case.options['life'] = 'Astra7'
    altered = case.contract()['contract']
    assert altered['life'] == 'Astra7'
    outcomes.append(dict(probe='same_journal_relabelled_between_allowed_lives_accepted',
        original_life='C0', accepted_life='Astra7', journal_id=altered['journal_id']))

    case = fixture()
    original_sha = case.pending['sha256']
    state = case.pending['document']['resume_state']['state']
    state['history'] = dict(working_state='different self-sealed history')
    case.reseal_pending()
    altered = case.contract()['contract']
    assert altered['preserved_state']['state']['history'] == state['history']
    assert altered['pending_sleep']['sha256'] != original_sha
    outcomes.append(dict(probe='resealed_history_not_externally_authenticated',
        original_pending_sha256=original_sha,
        accepted_pending_sha256=altered['pending_sleep']['sha256'],
        note='Different digest must be rejected by exact external selection, not inferred authentic from self-hash.'))

    case = fixture()
    original_state = deepcopy(case.pending['document']['resume_state'])
    result = case.contract()
    assert result['contract']['preserved_state'] == original_state
    assert result['sha256'] == helper.digest(result['contract'])
    result['contract']['preserved_state']['state']['rows'].clear()
    assert case.pending['document']['resume_state'] == original_state
    outcomes.append(dict(probe='exact_state_copy_and_no_aliasing', result='PASS'))

    for name, expected in [('restart_contract.py', HELPER_SHA), ('test_restart_contract.py', TEST_SHA)]:
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
    return dict(schema='INDEPENDENT_RESTART_CONTRACT_REVIEW_PROBES_V1',
        helper_sha256=HELPER_SHA, tests_sha256=TEST_SHA, model_execution=False,
        node_access=False, runtime_changes=False, outcomes=outcomes)


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--receipt':
        raise SystemExit('use --receipt NEW_LOCAL_PATH')
    report = run()
    report['reviewer_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with Path(sys.argv[2]).open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(report, sort_keys=True))
