"""Run isolated adoption, retention and existing CPU contracts; logs stay here."""

import importlib.util
import argparse
import sys
import unittest

import adoption


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', default='CPU_TESTS.log')
    arguments = parser.parse_args()
    adoption.require(adoption.Path(arguments.log).name == arguments.log, 'worker_log_only')
    adoption.verify_phase2()
    suite = unittest.defaultTestLoader.loadTestsFromModule(load('adoption_tests', adoption.OWN / 'test_adoption.py'))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(
        load('phase2_retention_tests', adoption.PHASE2 / 'test_retention.py')))
    choices = {
        'test_orch_r125_continual_stream.py': (
            'test_threshold_compaction_precedes_generation_and_preserves_raw_input',
            'test_threshold_reuses_prior_child_distillation_not_later_failed_code',
            'test_threshold_never_silently_drops_oversized_fresh_input'),
        'test_orch_r124_train_history.py': (
            'test_pinned_parent_is_verbatim_masked_once_across_compaction_eviction_and_restore',
            'test_child_cannot_be_pinned_and_pins_cannot_be_silently_truncated'),
    }
    count = 0
    for filename, methods in choices.items():
        path = adoption.REPOSITORY / 'tests' / filename
        expected = adoption.read(adoption.PHASE2 / 'PROVENANCE.json')['test_contract_sha256']['tests/' + filename]
        adoption.require(adoption.sha(path.read_bytes()) == expected, 'existing_test_contract_changed')
        module = load(filename.removesuffix('.py'), path)
        for candidate in vars(module).values():
            if isinstance(candidate, type) and issubclass(candidate, unittest.TestCase):
                for method in methods:
                    if hasattr(candidate, method):
                        suite.addTest(candidate(method))
                        count += 1
    adoption.require(count == 5, 'five_existing_retention_contracts')
    continuation = adoption.OWN.parent / 'rohin231_curriculum_birth_20260918/recovery_20260918T1646Z'
    sys.path.insert(0, str(continuation))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(
        load('existing_continuation_tests', continuation / 'test_continue_pair.py')))
    with (adoption.OWN / arguments.log).open('x') as output:
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    print(f'CPU tests: {result.testsRun}; failures: {len(result.failures)}; errors: {len(result.errors)}')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
