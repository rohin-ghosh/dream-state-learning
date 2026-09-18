from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('scratch_subject',
    Path(__file__).resolve().parents[1] / 'gpu/orch_r139_grid_broker_scratch.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class ScratchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff, cls.http = subject.load_runtime()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.scratch = self.root / 'scratch'
        self.addCleanup(patch.stopall)
        patch.object(subject, 'RUNTIME', self.root).start()
        patch.object(subject, 'SCRATCH', self.scratch).start()

    def test_exactly_three_literal_changes_no_source_mutation(self):
        before = {relative: subject.sha(self.handoff.BROKER_RUNTIME / relative)
                  for relative in self.handoff.BROKER_PINS}
        original = self.handoff.broker_functions(self.http, dict(after_parent=319, next_cycle=106),
            dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        wrapped = subject.broker_builder(self.handoff, self.scratch)(self.http,
            dict(after_parent=319, next_cycle=106), dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        self.assertEqual(original.__code__.co_code, wrapped.__code__.co_code)
        self.assertEqual(original.__code__.co_names, wrapped.__code__.co_names)
        changes = [(old, new) for old, new in zip(original.__code__.co_consts, wrapped.__code__.co_consts) if old != new]
        self.assertEqual(set(changes), {('/', str(self.scratch)), ('/tmp', str(self.scratch))})
        redirected = subject.literal(self.http.evaluate, '/tmp', str(self.scratch))
        self.assertEqual(redirected.__code__.co_code, self.http.evaluate.__code__.co_code)
        self.assertIs(redirected.__kwdefaults__, self.http.evaluate.__kwdefaults__)
        self.assertIn('/tmp', self.http.evaluate.__code__.co_consts)
        self.assertEqual({relative: subject.sha(self.handoff.BROKER_RUNTIME / relative) for relative in before}, before)

    def test_unknown_or_ambiguous_literal_site_rejected(self):
        def function():
            return 'unchanged'
        with self.assertRaises(ValueError):
            subject.literal(function, '/tmp', str(self.scratch))

    def test_missing_publication_cannot_create_scratch_or_dispatch(self):
        with (patch.object(subject.sys, 'argv', ['scratch', 'broker', '--expected-self-sha256', subject.sha(subject.__file__)]),
              patch.object(subject, 'load_runtime', side_effect=AssertionError('no_runtime_action')),
              patch.dict(os.environ, CUDA_VISIBLE_DEVICES='')):
            with self.assertRaisesRegex(ValueError, 'exact_frozen_plan'):
                subject.main()
        self.assertFalse(self.scratch.exists())

    def test_frozen_Main_authorization_is_not_bypassed(self):
        fake = SimpleNamespace(authorize=Mock(side_effect=ValueError('Main_not_authorized')))
        with self.assertRaisesRegex(ValueError, 'Main_not_authorized'):
            subject.authorize(fake, {}, {}, 'hash', 'broker', 10)

    def test_allocator_preserves_ten_GiB_floor(self):
        serving = subject.broker_builder(self.handoff, self.scratch)(self.http,
            dict(after_parent=319, next_cycle=106), dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        self.assertIn(10 * 1024**3, serving.__code__.co_consts)

    def test_scratch_owned_private_and_no_symlink_escape(self):
        path = subject.private_scratch()
        self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        path.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'private_owned'):
            subject.private_scratch()
        linked = self.root / 'linked'
        linked.symlink_to(self.scratch, target_is_directory=True)
        for path in (linked / 'call', self.root / '..' / 'escape', Path('/tmp/forbidden')):
            with self.assertRaises(ValueError):
                subject.runtime_path(path)

    def test_shared_slots_and_provider_constants_unchanged(self):
        self.assertEqual(str(self.http.slots.ROOT), '/tmp/orch_astra_http_slots')
        self.assertEqual(self.http.slots.LIMIT, 4)
        self.assertEqual(self.http.slots.acquire.__wrapped__.__kwdefaults__['root'], self.http.slots.ROOT)
        self.assertEqual(self.http.astra.MODEL, self.handoff.ASTRA)
        self.assertEqual(self.handoff.BROKER_PINS['gpu/orch_r118_astra_slots.py'],
                         '2c0e63311dac814044234c1fc48d4650aab4947f560620bbc79ccbbbd67d7a4d')

    def test_historical_request_does_not_touch_queue(self):
        serving = subject.broker_builder(self.handoff, self.scratch)(self.http,
            dict(after_parent=319, next_cycle=106), dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        processor = serving.__globals__['process_request']
        store = SimpleNamespace(exists=Mock(side_effect=AssertionError('no_historical_IO')))
        self.assertEqual(processor(store, {}, {}, 'P0319.request.json', None, None, None), 'HISTORICAL_NO_REDISPATCH')
        self.assertEqual(processor(store, {}, {}, 'P404431.request.json', None, None, None), 'CUMULATIVE_CAP_EXHAUSTED')
        store.exists.assert_not_called()

    def test_publication_binds_wrapper_scratch_and_unchanged_concurrency(self):
        fake = SimpleNamespace(authorize=Mock())
        publication = dict(scratch_wrapper=subject.source_ref(), raw_scratch_root=str(self.scratch),
                           shared_HTTP_slots_unchanged=True)
        subject.authorize(fake, {}, publication, 'hash', 'broker', 10)
        for key, value in [('scratch_wrapper', {}), ('raw_scratch_root', '/tmp'), ('shared_HTTP_slots_unchanged', False)]:
            with self.assertRaises(ValueError):
                subject.authorize(fake, {}, dict(publication, **{key: value}), 'hash', 'broker', 10)

    def evaluator(self, runner):
        transport = SimpleNamespace(**vars(self.http.astra.transport))
        transport.validate_config = lambda config: None
        transport.validate_request = lambda request, config: {'synthetic': 'transcript'}
        transport.build_system = lambda *args: ('synthetic system', b'synthetic prompt', {'fixture': True})
        @contextmanager
        def acquire(cutoff):
            yield {'maximum_http_concurrency': 4}
        evaluator = subject.literal(self.http.evaluate, '/tmp', str(self.scratch))
        evaluator = subject.bind(evaluator, transport=transport, authorize=lambda *args: None,
                                 slots=SimpleNamespace(acquire=acquire))
        def invoke(path):
            return evaluator(dict(id='P0320', lane_deadline_unix=10**12), path, 10**12,
                config=dict(branch='F4', family='grid', deadline_unix=10**12, min_available_bytes=0),
                launch={}, prompt_root=self.root, principles_path=self.root / 'synthetic',
                memory=lambda: 1, runner=runner)
        return invoke

    def test_real_evaluator_raw_writes_only_new_scratch(self):
        subject.private_scratch()
        def runner(prompt, directory, deadline, system):
            for name in ('API_REQUEST.json', 'DISPATCH.json', 'stdout.json'):
                (directory / name).write_text('{}')
            return dict(status='COMPLETE', actual_model=self.handoff.ASTRA)
        spy = Mock(side_effect=runner)
        call = self.scratch / 'call'
        result = self.evaluator(spy)(call)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertFalse(result['retry'])
        self.assertEqual(spy.call_count, 1)
        self.assertTrue({'REQUEST.json', 'PARENT_PROMPT.md', 'SYSTEM.txt', 'API_REQUEST.json',
                         'DISPATCH.json', 'stdout.json', 'RESULT.json'} <= {path.name for path in call.iterdir()})
        for path in call.iterdir():
            self.assertTrue(path.resolve().is_relative_to(self.scratch))
        with self.assertRaises(FileExistsError):
            self.evaluator(spy)(call)
        self.assertEqual(spy.call_count, 1)

    def test_refusal_or_error_never_retries(self):
        subject.private_scratch()
        runner = Mock(side_effect=ValueError('synthetic_refusal'))
        result = self.evaluator(runner)(self.scratch / 'refused')
        self.assertEqual(result['status'], 'MISSING')
        self.assertFalse(result['retry'])
        self.assertEqual(runner.call_count, 1)

    def test_evaluator_rejects_outside_before_any_writes(self):
        subject.private_scratch()
        runner = Mock(side_effect=AssertionError('no_dispatch'))
        outside = self.root / 'outside'
        with self.assertRaises(ValueError):
            self.evaluator(runner)(outside)
        self.assertFalse(outside.exists())
        runner.assert_not_called()

    def test_real_serve_allocator_and_disk_floor_follow_scratch(self):
        subject.private_scratch()
        serving = subject.broker_builder(self.handoff, self.scratch)(self.http,
            dict(after_parent=319, next_cycle=106), dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        principles = self.root / 'principles.txt'
        principles.write_text('synthetic')
        config_path = self.root / 'config.json'
        config_path.write_text(json.dumps(dict(principles_sha256=subject.sha(principles),
            remote_root='/synthetic/F4', deadline_unix=10**12)))
        launch_path = self.root / 'publication.json'
        launch_path.write_text('{}')
        blobs = {}
        class Store:
            def __init__(self, root):
                pass
            def shell(self, command, **kwargs):
                return SimpleNamespace(returncode=0)
            def exists(self, path):
                return str(path).endswith('LIFE_TERMINAL.json') or str(path) in blobs
            def copy(self, source, destination):
                blobs[str(destination).removeprefix('NODE:')] = Path(source).read_bytes()
            def hash(self, path):
                return hashlib.sha256(blobs[str(path)]).hexdigest()
        allocate = Mock(wraps=tempfile.mkdtemp)
        disk = Mock(return_value=SimpleNamespace(free=10 * 1024**3))
        bound = subject.bind(serving, validate_config=lambda *args: None, validate_launch=lambda *args: None,
            Store=Store, PRINCIPLES_V2_SHA256=subject.sha(principles),
            tempfile=SimpleNamespace(mkdtemp=allocate), shutil=SimpleNamespace(disk_usage=disk),
            process_request=Mock(side_effect=AssertionError('no_provider')))
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''):
            bound(config_path, launch_path, self.root, principles)
        self.assertEqual(allocate.call_args.kwargs['dir'], str(self.scratch))
        disk.assert_called_once_with(str(self.scratch))
        self.assertEqual(list(self.scratch.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
