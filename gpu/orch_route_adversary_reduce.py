"""Author-side deterministic reduction of the frozen adversarial inference batch."""

import argparse
from copy import deepcopy
from pathlib import Path

from gpu import orch_route_adversary as driver
from organism_v6 import orch_route_adversary as probe


def audit_arm(root, arm, prepared):
    directory = root / arm
    result = driver.source.read(directory / 'RESULT.json')
    driver.source.require(not (directory / 'FAILED.json').exists(), 'failed_arm_not_terminal_comparison')
    driver.source.require(result['status'] == 'COMPLETE_NOT_PROMOTED'
        and result['fits'] == result['updates'] == 0 and result['frozen_base_unchanged'], 'readonly_terminal_required')
    driver.source.require(result['adapter_state_before'] == result['adapter_state_after'] == driver.STATES[arm],
                          'mounted_state_receipt_join')
    driver.source.require(result['cases_sha256'] == prepared['cases_sha256']
        and result['prepare_sha256'] == driver.source.file_hash(root / 'PREPARE.json')
        and result['source_commit'] == prepared['new_source_commit'], 'frozen_preparation_join')
    for inventory in ('result_files', 'raw_call_files'):
        for name, digest in result[inventory].items():
            driver.source.require(Path(name).name == name and driver.source.file_hash(directory / name) == digest,
                                  'native_artifact_inventory_drift')
    cases, flattened, rows = [], [], []
    for index, case in enumerate(prepared['cases']):
        record = driver.source.read(directory / f'CASE_{index:03d}.json')
        captures = iter(record['native'])

        def replay(messages):
            capture = next(captures)
            driver.source.require(messages == capture['messages'], 'native_prefix_replay_drift')
            driver.source.require(capture['error'] is None, 'native_error_in_comparison')
            return deepcopy(capture['response'])

        reproduced = probe.run_case(case, replay)
        driver.source.require(next(captures, None) is None and reproduced == record, 'complete_case_replay_drift')
        cases.append(record)
        for capture in record['native']:
            native = driver.source.read(directory / f'CALL_{len(flattened):03d}.json')
            driver.source.require(native['case_index'] == index and native['index'] == len(flattened)
                and all(native[key] == capture[key] for key in ('messages', 'response', 'error')),
                'independent_raw_call_to_case_join')
            flattened.append(native)
        rows.append(dict(arm=arm, seed=case['seed'], master=case['master'], condition=case['condition'],
            goal_index=case['goal_index'], expected_first_port=case['expected_first_port'],
            actual_first_port=record['first_port'], first_correct=record['first_correct'],
            complete_correct=record['complete_correct'], route_sources_available=record['route_sources_available'],
            original_missing_addresses=case['original_missing_addresses'],
            terminal_reason=record['episode']['terminal_reason'],
            native_commands=[capture['response']['raw'] for capture in record['native']],
            final_current=record['episode']['current'], target_goal=case['task']['goal']))
    driver.source.require(len(flattened) == result['native_calls'] <= 48, 'native_budget_join')
    driver.source.require(len(list(directory.glob('CALL_*.json'))) == len(flattened)
        and len(list(directory.glob('CASE_*.json'))) == 24, 'no_hidden_case_or_call_files')
    summary = probe.summarize(cases)
    driver.source.require(summary == result['summary'], 'prospective_metric_replay_drift')
    paired = summary['paired_interventions']['rows']
    supported = [row for row in paired if row['all_route_sources_available']]
    return dict(arm=arm, native_calls=len(flattened), case_replays=len(cases), summary=summary, rows=rows,
        fully_supported_interventions=dict(denominator=len(supported),
            causal_switch_correct=sum(row['causal_switch_correct'] for row in supported),
            display_invariant_correct=sum(row['display_invariant_correct'] for row in supported)),
        seconds=result['seconds'], result_sha256=driver.source.file_hash(directory / 'RESULT.json'))


def reduce(root):
    root = Path(root)
    prepared = driver.source.read(root / 'PREPARE.json')
    driver.source.require(probe.hop.document_sha256(prepared['cases']) == prepared['cases_sha256'], 'case_inventory_drift')
    driver.source.require(driver.source.file_hash(Path(probe.__file__))
        == prepared['own_hashes']['organism_v6/orch_route_adversary.py'], 'frozen_metric_helper_required')
    reference = driver.source.read(root / 'REFERENCE.json')
    driver.source.require(reference['summary'] == probe.summarize(reference['cases']), 'reference_reduction_drift')
    arms = [audit_arm(root, arm, prepared) for arm in driver.STATES]
    return dict(status='TERMINAL_AUTHOR_AUDITED_NOT_INDEPENDENT_REVIEW_NOT_PROMOTED',
        node='node3', native_root='/tmp/orch_route_adversary_20260914_attempt1/revision2',
        terminal_models=3, model_denominator=3, replayed_cases=sum(arm['case_replays'] for arm in arms),
        case_denominator=72, actual_native_calls=sum(arm['native_calls'] for arm in arms), native_call_cap=144,
        source_commit=prepared['new_source_commit'], cases_sha256=prepared['cases_sha256'], arms=arms,
        first_available_reference=reference['summary'], fits=0, updates=0, claim=probe.CLAIM,
        independence='AUTHOR_AUDIT_WITH_PRIOR_ACCIDENTAL_BOARD_SUMMARY_EXPOSURE_DISCLOSED',
        unsupported_label='INCOMPLETE_POSITIVE_PATH_SOURCE_NOT_PROOF_OF_LOGICAL_UNIDENTIFIABILITY')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    arguments = parser.parse_args()
    driver.write(arguments.output, reduce(arguments.root))
