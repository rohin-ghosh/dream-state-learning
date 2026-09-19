"""Run pinned history/stream/journal regressions against only the C2 closure."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import unittest
from unittest.mock import patch


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


class ReferenceParity(unittest.TestCase):
    def event(self, module, identifier, **changes):
        values = dict(event_id=identifier, actor='child', text='中文 "quoted"\n' + identifier,
            split='TRAIN', phase='experience', episode_id='E0', source_id='source/' + identifier,
            source_sha256=hashlib.sha256(identifier.encode()).hexdigest(), origin='TRAIN_COLLECTION')
        values.update(changes)
        return module.TrainEvent(**values)

    def histories(self):
        return [module.TrainHistory(system_prompt='S', birth_prompt='B') for module in (OLD, NEW)]

    def test_actual_preimage_checkpoint_bytes_and_restore_match(self):
        histories = self.histories()
        for index in range(32):
            for module, history in zip((OLD, NEW), histories):
                item = self.event(module, 'parent-' + str(index), actor='parent')
                history.append(item)
                history.pin_parent_event(item.event_id)
                history.append(self.event(module, 'child-' + str(index)))
                history.compact(self.event(module, 'summary-' + str(index), phase='compaction'),
                    through=history.frontier())
                if index % 3 == 0:
                    history.evict_oldest(history.frontier(), reason='synthetic-pressure')
            self.assertEqual(histories[0].to_json(), histories[1].to_json())
        for writer in histories:
            for module in (OLD, NEW):
                self.assertEqual(module.TrainHistory.from_json(writer.to_json()).to_json(), writer.to_json())
        self.assertEqual([asdict(value) for value in histories[0].events],
            [asdict(value) for value in histories[1].events])

    def test_actual_preimage_all_prefix_digests_match(self):
        histories = self.histories()
        for index in range(48):
            for module, history in zip((OLD, NEW), histories):
                history.append(self.event(module, str(index)))
            for count in range(index + 2):
                self.assertEqual(asdict(histories[0].frontier(count)), asdict(histories[1].frontier(count)))

    def test_actual_preimage_and_new_reject_same_tamper(self):
        for module in (OLD, NEW):
            history = module.TrainHistory(system_prompt='S', birth_prompt='B')
            history.append(self.event(module, 'first'))
            document = history.checkpoint()
            document['events'][0]['text'] = 'tampered'
            with self.subTest(module=module.__name__), self.assertRaises(ValueError):
                module.TrainHistory.restore(document)

    def test_actual_preimage_and_new_deepcopy_diverge_independently(self):
        for module in (OLD, NEW):
            history = module.TrainHistory(system_prompt='S', birth_prompt='B')
            history.append(self.event(module, 'first'))
            copied = deepcopy(history)
            history.append(self.event(module, 'original'))
            copied.append(self.event(module, 'copy'))
            self.assertNotEqual(copied.frontier(), history.frontier())
            for current in (history, copied):
                self.assertEqual(current.frontier().sha256,
                    module._digest([asdict(item) for item in current.events]))


class CountedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtests = 0

    def addSubTest(self, test, subtest, error):
        self.subtests += 1
        super().addSubTest(test, subtest, error)


def main():
    global OLD, NEW
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    tools = Path(__file__).resolve().parent
    checker = load('c2_epoch3_portable_checker', tools / 'cpu_check.py')
    checker.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment_required')
    manifest = json.loads(args.manifest.read_bytes())
    for name, expected in manifest['helper_pins'].items():
        checker.require(checker.raw_sha(tools / name) == expected, 'exact_frontier_helper:' + name)
    source = args.source.resolve()
    pins = checker.verify_source(source, manifest)
    sys.path.insert(0, str(source))
    OLD = load('c2_epoch2_history_reference', tools / 'epoch2_history.py')
    from organism_v6 import orch_r124_train_history as NEW
    groups = {}
    suites = [(name, unittest.defaultTestLoader.loadTestsFromModule(load('c2_snapshot_' + str(index), tools / name)))
        for index, name in enumerate(manifest['frontier_test_snapshot_pins'])]
    suites.append(('exact_preimage_parity', unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceParity)))
    with patch('subprocess.Popen', side_effect=AssertionError('no_native_processes')), \
            patch('os.kill', side_effect=AssertionError('no_native_signals')), \
            patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no_native_signals')):
        for name, suite in suites:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=CountedResult).run(suite)
            groups[name] = dict(passed=result.wasSuccessful(), tests=result.testsRun,
                subtests=result.subtests, errors=len(result.errors), failures=len(result.failures),
                skipped=len(result.skipped))
    origins = {}
    for name, module in tuple(sys.modules.items()):
        if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
            path = Path(module.__file__).resolve()
            checker.require(path.is_relative_to(source), 'no_repository_source_import:' + name)
            origins[name] = dict(path=str(path), sha256=checker.raw_sha(path))
    checker.verify_source(source, manifest)
    passed = all(value['passed'] for value in groups.values())
    print(json.dumps(dict(passed=passed, source_pins=pins, groups=groups,
        tests_run=sum(value['tests'] for value in groups.values()),
        subtests_run=sum(value['subtests'] for value in groups.values()),
        imported_source_modules=origins, test_snapshot_pins=manifest['frontier_test_snapshot_pins'],
        epoch2_history_sha256=checker.raw_sha(tools / 'epoch2_history.py'),
        synthetic_only=True, actual_C2_checkpoint_validated=False, C2_latency_validated=False,
        dispatchable=False, GPU_calls=0, native_signals=0, dispatches=0), sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
