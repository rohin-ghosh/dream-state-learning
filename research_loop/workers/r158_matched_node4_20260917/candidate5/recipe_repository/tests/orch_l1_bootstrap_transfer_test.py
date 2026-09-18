import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


from gpu import orch_l1_bootstrap_transfer_run as run
from gpu import orch_l1_bootstrap_transfer_scan as scanner
from gpu import orch_math_replication_guard as existing_scan
from organism_v6 import orch_l1_bootstrap_transfer as policy


def sample_cohort():
    return dict(tasks=[dict(id=str(index), stratum='in_family' if index < 16 else 'out_family')
                       for index in range(32)])


def test_exclusions_include_nested_train_eval_collection_and_inherited_ids():
    documents = [dict(TRAIN=[dict(id='train', question=' Same   QUESTION ')]),
        dict(eval=[dict(task_id='eval')], collection=[dict(id='collection')],
             excluded_ids=['older'], excluded_question_hashes=['older_hash'])]
    identities, hashes = policy.exclusions(documents)
    assert identities == {'train', 'eval', 'collection', 'older'}
    assert hashes == {policy.question_hash('same question'), 'older_hash'}


def test_family_strata_follow_actual_first16_not_broader_source_pool():
    assert policy.IN_FAMILIES == ('percentages',)
    assert policy.QUOTAS['percentages'] == 16 and sum(policy.QUOTAS.values()) == 32
    assert policy.CAP == 1536 and policy.SECONDS == 5400
    assert set(dict(policy.DEVICES.values())) == {4, 5, 6}


def test_cohort_is_deterministic_unique_and_excludes_question_aliases():
    records = [dict(question=f'Question {index}: what is 10% of 100?', answer='#### 10') for index in range(50)]
    exclusions = [dict(TRAIN=[dict(id='gsm8k-train-0', question=records[1]['question'])])]
    with patch.object(policy, 'QUOTAS', dict(percentages=32)):
        first = policy.cohort(records, exclusions)
        assert first == policy.cohort(records, list(reversed(exclusions)))
    assert not {'gsm8k-train-0', 'gsm8k-train-1'} & {task['id'] for task in first['tasks']}
    assert all(messages == policy.original.prompt(task, 'rich')[0]
        for task, messages in zip(first['tasks'], first['prompts']))
    assert all('gold' not in message for messages in first['prompts'] for message in messages)


def test_original_oracle_preserved_without_auto_qualification():
    response = dict(raw='I checked it.\nFINAL: 1/2', token_ids=list(range(201)), terminal=True,
        truncated=False, prompt_tokens=100)
    result = policy.score(dict(gold='0.5'), response)
    assert result['outcome_pass'] and result['token_contract_pass']
    assert result['generated_tokens'] == 200 and result['total_generated_ids'] == 201
    assert result['semantic_status'] == 'UNREVIEWED' and result['qualified_rich'] is None
    assert not policy.score(dict(gold='0.5'), dict(response, raw='FINAL: 0.5\nMore words'))['outcome_pass']


def test_truncation_not_silently_rewritten_into_original_outcome_oracle():
    response = dict(raw='FINAL: 2', token_ids=list(range(1536)), terminal=False,
        truncated=True, prompt_tokens=100)
    result = policy.score(dict(gold='2'), response)
    assert result['outcome_pass'] and result['truncated'] and not result['token_contract_pass']


def test_missing_and_failed_calls_keep_all96_denominators():
    result = policy.summarize(sample_cohort(), [dict(arm='FULL', task_id='0', error=dict(type='failure'))])
    assert result['reserved_calls'] == 1
    assert sum(arm['all']['denominator'] for arm in result['arms'].values()) == 96
    assert result['arms']['FULL']['all']['failed'] == 1
    assert result['arms']['FULL']['all']['not_completed'] == 32
    assert result['paired_outcome']['OFF']['cells'] == {'00': 32}
    assert all(arm['all']['qualified_rich'] is None for arm in result['arms'].values())


def test_pairing_and_duplicate_call_rejection():
    row = dict(arm='FULL', task_id='0', response={}, score=dict(outcome_pass=True))
    result = policy.summarize(sample_cohort(), [row])
    assert result['paired_outcome']['OFF']['net_outcome_difference'] == 1
    assert result['arms']['FULL']['in_family']['outcome_pass'] == 1
    with unittest.TestCase().assertRaises(AssertionError):
        policy.summarize(sample_cohort(), [row, row])


def test_exclusive_reservation_prevents_retry_and_caps_positions():
    with tempfile.TemporaryDirectory(prefix='orch_l1_bootstrap_transfer_test_') as directory:
        check_reservations(Path(directory))


def check_reservations(tmp_path):
    task = dict(id='fixed')
    path, row = run.reserve(tmp_path, 0, 'FULL', task, [])
    assert json.loads(path.read_text()) == row
    with unittest.TestCase().assertRaises(FileExistsError):
        run.reserve(tmp_path, 0, 'FULL', task, [])
    with unittest.TestCase().assertRaises(AssertionError):
        run.reserve(tmp_path, 32, 'FULL', task, [])


def test_zero_memory_never_overrides_unreadable_proc_or_reservation():
    with patch.object(existing_scan, 'ALLOWED', {4, 5, 6}):
        check_snapshot()


def check_snapshot():
    uuid = policy.DEVICES['FULL'][1]
    snapshot = dict(gpu=dict(index=4, uuid=uuid, memory_used_mib=0, utilization_percent=0),
        compute_processes=[], processes=[dict(pid=123, unreadable=True)])
    assert existing_scan.evaluate_snapshot(snapshot, 4, uuid)
    snapshot['processes'] = [dict(pid=124, cvd=uuid)]
    assert existing_scan.evaluate_snapshot(snapshot, 4, uuid)
    snapshot['processes'] = [dict(pid=125, target_device_open=True)]
    assert existing_scan.evaluate_snapshot(snapshot, 4, uuid)


def test_launch_requires_main_logged_receipt_before_lifetime():
    with tempfile.TemporaryDirectory(prefix='orch_l1_bootstrap_transfer_test_') as directory:
        with patch.object(run, 'validate_inputs', lambda unused: {}):
            check_launch(Path(directory))


def check_launch(tmp_path):
    run.write(tmp_path / 'PREPARE.json', {})
    run.write(tmp_path / 'READY.json', dict(prepare_sha256=run.sha(tmp_path / 'PREPARE.json'), cpu_tests_passed=True))
    run.write(tmp_path / 'ACK.json', dict(ready_sha256=run.sha(tmp_path / 'READY.json'), acknowledged_by='Author',
        dated_builder_line='not Main', logged_receipt_acknowledged=True))
    with unittest.TestCase().assertRaises(AssertionError):
        run.launch(tmp_path, tmp_path / 'ACK.json')
    assert not (tmp_path / 'LIFETIME.json').exists()


def test_owned_stop_rejects_reused_pid_before_signal():
    child = SimpleNamespace(pid=123, poll=lambda: None)
    with patch.object(run, 'process_identity', lambda unused: dict(pid=123, start_ticks='new')):
        with unittest.TestCase().assertRaises(AssertionError):
            run.stop_owned(child, dict(pid=123, start_ticks='old'))


def test_actual_cohort_source_exclusions_and_frozen_prompt():
    root = Path(__file__).resolve().parents[1]
    path = root / 'research_notes/analysis/orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json'
    if not path.exists():
        path = root.parent / 'COHORT.json'
    document = json.loads(path.read_text())
    assert run.sha(path) == run.COHORT_SHA
    selected = {task['id'] for task in document['tasks']}
    assert len(selected) == 32 and not selected.intersection(document['excluded_ids'])
    assert {'gsm8k-train-1614', 'gsm8k-train-971', 'gsm8k-train-5643'} <= set(document['excluded_ids'])
    assert all(messages == policy.original.prompt(task, 'rich')[0]
        for task, messages in zip(document['tasks'], document['prompts']))


def native_case(directory, fail_generation=False, fail_after=False):
    root = Path(directory)
    tasks = [dict(id=str(index), gold='10', question='What is 10% of 100?', family='percentages',
                  stratum='in_family') for index in range(32)]
    prompts = [policy.original.prompt(task, 'rich')[0] for task in tasks]
    run.write(root / 'COHORT.json', dict(tasks=tasks, prompts=prompts))
    run.write(root / 'PREPARE.json', {})
    run.write(root / 'LIFETIME.json', dict(native_deadline_unix=time.time() + 100))
    response = dict(raw='FINAL: 10', token_ids=list(range(201)), terminal=True, truncated=False, prompt_tokens=101)
    engine = SimpleNamespace(generate=Mock(return_value=response))
    if fail_generation:
        engine.generate.side_effect = RuntimeError('native_failure')
    identity = SimpleNamespace(document=lambda: dict(state='saved'))
    loaded = SimpleNamespace(engine=engine, observed=identity, process=('boot', 123, 456),
        verify_unchanged=Mock(return_value=identity))
    if fail_after:
        loaded.verify_unchanged.side_effect = RuntimeError('state_drift')
    prepared = dict(bundle='existing', model_dir='existing', identities=dict(FULL={}))
    uuid = policy.DEVICES['FULL'][1]
    actual_path = Path

    def path_constructor(value):
        if value == '/proc/self/environ':
            return SimpleNamespace(read_bytes=lambda: ('CUDA_VISIBLE_DEVICES=' + uuid).encode())
        return actual_path(value)

    with patch.object(run, 'validate_inputs', return_value=prepared), patch.object(run, 'Path', path_constructor):
        with patch.object(run.portable, 'verify_base_files') as base_check:
            with patch.object(run.bridge.AdapterIdentity, 'from_document', return_value=identity):
                with patch.object(run.native, 'load_stage', return_value=loaded) as load:
                    with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=uuid):
                        if fail_generation or fail_after:
                            with unittest.TestCase().assertRaises((RuntimeError, AssertionError)):
                                run.run(root, 'FULL')
                        else:
                            run.run(root, 'FULL')
    assert load.call_count == 1 and loaded.verify_unchanged.call_count == 1
    assert load.call_args.kwargs['engine_factory'] is run.Engine
    assert load.call_args.args[0].fresh_process and not load.call_args.args[0].parent_present
    assert base_check.call_count == (1 if fail_after else 2)
    assert engine.generate.call_count == (1 if fail_generation else 32)
    assert all(call.kwargs == {'max_new_tokens': 1536} for call in engine.generate.call_args_list)
    return root


def test_native_seam_uses32_fixed_prompts_and_verifies_before_after():
    with tempfile.TemporaryDirectory(prefix='orch_l1_bootstrap_transfer_test_') as directory:
        root = native_case(directory)
        assert run.read(root / 'FULL/TERMINAL.json')['status'] == 'COMPLETE'
        assert (root / 'FULL/AFTER.json').exists()


def test_native_error_has_one_reservation_no_retry_and_after_check():
    with tempfile.TemporaryDirectory(prefix='orch_l1_bootstrap_transfer_test_') as directory:
        root = native_case(directory, fail_generation=True)
        assert run.read(root / 'FULL/TERMINAL.json')['status'] == 'FAILED'
        assert 'error' in run.read(root / 'FULL/CALL_00.json')
        assert len(list((root / 'FULL').glob('CALL_*.json'))) == 1


def test_after_identity_failure_never_reports_complete():
    with tempfile.TemporaryDirectory(prefix='orch_l1_bootstrap_transfer_test_') as directory:
        root = native_case(directory, fail_after=True)
        assert run.read(root / 'FULL/TERMINAL.json')['status'] == 'IDENTITY_VERIFICATION_FAILED'
        assert not (root / 'FULL/AFTER.json').exists()


def test_host_binding_hashes_exact_identity_without_plaintext_output():
    with patch.object(scanner.socket, 'gethostname', return_value='synthetic-test-host'):
        assert scanner.host_identity() == hashlib.sha256(b'synthetic-test-host').hexdigest()
        assert scanner.host_identity() != policy.HOST_SHA


def test_wrong_host_fails_before_scan_or_input_access():
    with patch.object(scanner, 'host_identity', return_value='0' * 64):
        with unittest.TestCase().assertRaises(AssertionError):
            scanner.scan(4, Path('/nonexistent-service'))
    with patch.object(run, 'host_identity', return_value='0' * 64):
        with unittest.TestCase().assertRaises(AssertionError):
            run.validate_inputs(run.ROOT)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(function) for name, function in sorted(globals().items())
                              if name.startswith('test_') and callable(function))


if __name__ == '__main__':
    unittest.main()
