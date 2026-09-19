"""Run only the isolated regressions and five existing retention contracts."""

import importlib.util
from pathlib import Path
import unittest


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[3]


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def main():
    current = load('retention_tests', OWN / 'test_retention.py')
    with (OWN / 'TESTS.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromModule(current))
    choices = {
        'test_orch_r125_continual_stream.py': (
            'test_threshold_compaction_precedes_generation_and_preserves_raw_input',
            'test_threshold_reuses_prior_child_distillation_not_later_failed_code',
            'test_threshold_never_silently_drops_oversized_fresh_input'),
        'test_orch_r124_train_history.py': (
            'test_pinned_parent_is_verbatim_masked_once_across_compaction_eviction_and_restore',
            'test_child_cannot_be_pinned_and_pins_cannot_be_silently_truncated'),
    }
    suite = unittest.TestSuite()
    for filename, methods in choices.items():
        module = load(filename.removesuffix('.py'), REPOSITORY / 'tests' / filename)
        for candidate in vars(module).values():
            if isinstance(candidate, type) and issubclass(candidate, unittest.TestCase):
                for method in methods:
                    if hasattr(candidate, method):
                        suite.addTest(candidate(method))
    if suite.countTestCases() != 5:
        raise ValueError('five_exact_existing_contracts_required')
    with (OWN / 'LEGACY_TESTS.log').open('w') as log:
        legacy = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    print(f'Targeted: {result.testsRun}; existing: {legacy.testsRun}; '
        f'all_passed={result.wasSuccessful() and legacy.wasSuccessful()}')
    if not result.wasSuccessful() or not legacy.wasSuccessful():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
