import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch


PATH = Path('/tmp/astra_level1_next_batch_20260913.py')
ORIGINAL = Path('/tmp/astra_level1_batch_20260913.py')
ORIGINAL_ROSTER = Path('/tmp/astra_level1_roster_20260913_attempt1/roster.json')
ORIGINAL_ROSTER_PIN = 'ad1c8d522d295e3c1b33c7e6ed93fbf89c467d3206d61e449d6844905fa19423'
specification = importlib.util.spec_from_file_location('next_batch_tests', PATH)
batch = importlib.util.module_from_spec(specification)
specification.loader.exec_module(batch)


class BatchTests(unittest.TestCase):
    def test_frozen_twelve_unique_allocations(self):
        self.assertEqual(batch.digest(ORIGINAL_ROSTER), ORIGINAL_ROSTER_PIN)
        self.assertEqual(batch.digest(batch.DRIVER), batch.DRIVER_PIN)
        entries = json.loads(ORIGINAL_ROSTER.read_text())['entries']
        self.assertEqual(len(entries), 12)
        self.assertEqual(len({(entry['node'], entry['gpu_index']) for entry in entries}), 12)
        self.assertEqual(len({entry['root'] for entry in entries}), 12)
        for entry in entries:
            self.assertEqual(batch.digest(entry['spec']['path']), entry['spec']['sha256'])
            if entry['node'] == 'node2':
                self.assertNotEqual(entry['gpu_index'], 0)

    def test_visibility_matches_uuid_index_and_all(self):
        for value in ('2', '1, 2', 'GPU-fixture', 'all'):
            self.assertTrue(batch.selected(value, 2, 'GPU-fixture'))
        for value in ('', '12', 'GPU-other', '-1'):
            self.assertFalse(batch.selected(value, 2, 'GPU-fixture'))

    def test_exception_requires_exact_identity_or_transport_ancestor(self):
        config = {'daemon_identities': [], 'uid': 2524}
        record = dict(pid=42, comm='sshd', uid=2524, cmdline_sha256=batch.TRANSPORT_SHA)
        self.assertTrue(batch.known_exception(record, config, {42}))
        self.assertFalse(batch.known_exception(record, config, set()))
        self.assertFalse(batch.known_exception(dict(record, cmdline_sha256='changed'), config, {42}))
        config['daemon_identities'] = [dict(record, comm='daemon')]
        self.assertTrue(batch.known_exception(dict(record, comm='daemon'), config, set()))
        self.assertFalse(batch.known_exception(dict(record, comm='daemon', pid=43), config, set()))

    def fixture(self, directory):
        root = Path(directory)
        configs, entries = {}, []
        for node in batch.NODES:
            uuid = 'GPU-fixture-' + node
            configs[node] = dict(host_boot_id='fixture-boot-' + node, uid=2524, gpus={'0': uuid}, daemon_identities=[])
            spec = root / (node + '-spec.json')
            spec.write_text('{}')
            entries.append(dict(node=node, name=node + '-cell', root=str(root / (node + '-native-root')),
                                gpu_index=0, gpu_uuid=uuid, spec=dict(path=str(spec), sha256=batch.digest(spec))))
        checks = root / 'checks.json'
        checks.write_text(json.dumps(configs))
        roster = root / 'roster.json'
        roster.write_text(json.dumps(dict(prechecks=dict(path=str(checks), sha256=batch.digest(checks)), entries=entries)))
        return roster, configs, entries

    def test_all_three_nodes_filter_in_roster_order(self):
        with tempfile.TemporaryDirectory() as directory:
            roster, configs, entries = self.fixture(directory)
            for node in batch.NODES:
                path, config, chosen = batch.read_request(roster, batch.digest(roster), node, 'batch-' + node)
                self.assertEqual(path, roster)
                self.assertEqual(config, configs[node])
                self.assertEqual(chosen, [entry for entry in entries if entry['node'] == node])

    def test_roster_hash_failure_before_claim_or_native(self):
        with tempfile.TemporaryDirectory() as directory:
            roster, _, _ = self.fixture(directory)
            with patch.object(batch, 'load_runtime') as loader, patch.object(batch.subprocess, 'run') as prepare:
                for checksum in ('0' * 64, 'bad', True):
                    with self.assertRaises(ValueError):
                        batch.main(roster, checksum, 'node1', 'never-created')
                loader.assert_not_called()
                prepare.assert_not_called()
            self.assertFalse((Path(directory) / 'never-created').exists())

    def test_precheck_pin_and_missing_a100_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            roster, configs, _ = self.fixture(directory)
            metadata = json.loads(roster.read_text())
            checks = Path(metadata['prechecks']['path'])
            checks.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'precheck identity pin'):
                batch.read_request(roster, batch.digest(roster), 'a100', 'batch')
            configs.pop('a100')
            checks.write_text(json.dumps(configs))
            metadata['prechecks']['sha256'] = batch.digest(checks)
            roster.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, 'Main must supply'):
                batch.read_request(roster, batch.digest(roster), 'a100', 'batch')

    def test_unsafe_names_empty_node_and_duplicate_allocations(self):
        with tempfile.TemporaryDirectory() as directory:
            roster, _, entries = self.fixture(directory)
            for name in ('../outside', '/absolute', '.', '..', 'a/b', ''):
                with self.assertRaises(ValueError):
                    batch.read_request(roster, batch.digest(roster), 'node1', name)
            metadata = json.loads(roster.read_text())
            metadata['entries'] = [entry for entry in entries if entry['node'] != 'a100']
            roster.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, 'no cells'):
                batch.read_request(roster, batch.digest(roster), 'a100', 'batch')
            metadata['entries'].append(dict(entries[0], name='duplicate'))
            roster.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                batch.read_request(roster, batch.digest(roster), 'node1', 'batch')

    def mocks(self, entry):
        def write(path, value):
            with Path(path).open('x') as stream:
                json.dump(value, stream)
        runtime = SimpleNamespace(offline=Mock(), write=Mock(side_effect=write), verify=Mock())
        plan = dict(gpu_index=entry['gpu_index'], gpu_uuid=entry['gpu_uuid'], lease_end=100000)
        probe = SimpleNamespace(gpu_state=Mock(return_value=True))
        runtime.verify.return_value = (plan, probe)
        return runtime, plan, probe

    def test_mocked_cell_checks_env_and_fresh_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            roster, configs, entries = self.fixture(directory)
            entry = entries[2]
            runtime, plan, probe = self.mocks(entry)
            receipt = SimpleNamespace(returncode=0, stdout='{"plan_sha256":"fixture-plan"}\n', stderr='')
            with patch.object(batch, 'load_runtime', return_value=runtime), patch.object(batch, 'reservations', return_value={'mock': True}) as reservation, \
                 patch.object(batch, 'identity', return_value={'pid': 999}), patch.object(batch.time, 'time', return_value=1000), \
                 patch.object(batch.subprocess, 'run', return_value=receipt) as prepare, \
                 patch.object(batch.subprocess, 'Popen', return_value=SimpleNamespace(pid=999)) as launch, contextlib.redirect_stdout(io.StringIO()):
                batch.main(roster, batch.digest(roster), 'a100', 'fresh-a100')
                prepare.assert_called_once()
                self.assertEqual(prepare.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
                self.assertEqual(prepare.call_args.kwargs['timeout'], 180)
                self.assertIn('--allow-native', prepare.call_args.args[0])
                self.assertEqual(prepare.call_args.args[0][2], str(batch.DRIVER))
                runtime.verify.assert_called_once_with(entry['root'], 'fixture-plan', native=False)
                reservation.assert_called_once_with(configs['a100'], 0, entry['gpu_uuid'])
                probe.gpu_state.assert_called_once_with(plan)
                launch.assert_called_once()
                self.assertEqual(launch.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], entry['gpu_uuid'])
                self.assertTrue(launch.call_args.kwargs['start_new_session'])
                self.assertIn('--allow-gpu', launch.call_args.args[0])
                with self.assertRaises(FileExistsError):
                    batch.main(roster, batch.digest(roster), 'a100', 'fresh-a100')
                self.assertEqual(prepare.call_count, 1)
                self.assertEqual(launch.call_count, 1)
            batch_directory = Path(directory) / 'fresh-a100'
            self.assertEqual({path.name for path in batch_directory.iterdir()}, {'started.json', 'finished.json', 'a100-cell'})
            self.assertEqual(json.loads((batch_directory / 'finished.json').read_text())['status'], 'ALL_CONTROLLERS_SUBMITTED_NOT_RESULTS')

    def test_safety_failures_stop_before_popen_without_retry(self):
        for failure in ('prepare', 'verify', 'allocation', 'reservation', 'xml', 'lease'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                roster, _, entries = self.fixture(directory)
                runtime, plan, probe = self.mocks(entries[0])
                result = SimpleNamespace(returncode=1 if failure == 'prepare' else 0, stdout='{"plan_sha256":"fixture-plan"}\n', stderr='')
                if failure == 'verify':
                    runtime.verify.side_effect = ValueError('source/runtime mismatch')
                if failure == 'allocation':
                    plan['gpu_uuid'] = 'changed'
                if failure == 'xml':
                    probe.gpu_state.return_value = False
                if failure == 'lease':
                    plan['lease_end'] = 1000 + 5400 + 180 + 21600
                with patch.object(batch, 'load_runtime', return_value=runtime), patch.object(batch.time, 'time', return_value=1000), \
                     patch.object(batch, 'reservations', side_effect=ValueError('reserved') if failure == 'reservation' else None, return_value={}), \
                     patch.object(batch.subprocess, 'run', return_value=result) as prepare, patch.object(batch.subprocess, 'Popen') as launch:
                    with self.assertRaises(ValueError):
                        batch.main(roster, batch.digest(roster), 'node1', 'batch')
                    self.assertEqual(prepare.call_count, 1)
                    launch.assert_not_called()
                failure_receipt = json.loads((Path(directory) / 'batch/node1-cell/failure.json').read_text())
                self.assertFalse(failure_receipt['retry'])
                self.assertFalse(failure_receipt['controller_may_be_running'])
                self.assertFalse((Path(directory) / 'batch/finished.json').exists())

    def test_original_reservation_and_native_cell_bodies_preserved(self):
        original = ast.parse(ORIGINAL.read_text())
        changed = ast.parse(PATH.read_text())
        def functions(tree):
            return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        old, new = functions(original), functions(changed)
        for name in ('digest', 'identity', 'selected', 'known_exception', 'reservations'):
            self.assertEqual(ast.dump(old[name]), ast.dump(new[name]), name)
        original_loop = next(node for node in old['main'].body if isinstance(node, ast.For))
        new_loop = next(node for node in new['main'].body if isinstance(node, ast.For))
        self.assertEqual([ast.dump(node) for node in original_loop.body[1:]], [ast.dump(node) for node in new_loop.body])

    def test_explicit_cli_dispatch(self):
        with patch.object(batch, 'main') as main:
            batch.cli(['--roster', '/tmp/fixture.json', '--roster-sha256', 'a' * 64, '--node', 'a100', '--batch-name', 'fresh'])
            main.assert_called_once_with(Path('/tmp/fixture.json'), 'a' * 64, 'a100', 'fresh')


if __name__ == '__main__':
    unittest.main()
