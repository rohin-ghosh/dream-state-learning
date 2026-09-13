"""Local stdlib/mock tests only; no native launcher, model or subprocess runs."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
specification = importlib.util.spec_from_file_location('additive_main_tested', Path(__file__).with_name('astra_additive_replay_main_20260913.py'))
main = importlib.util.module_from_spec(specification)
specification.loader.exec_module(main)
REAL_RUNTIME, REAL_LOAD = main.runtime, main.load
RECEIPT = Path('/tmp/astra_additive_cpu_archive_mirror_20260913_attempt1/astra_additive_replay_tiny_cpu_20260913_attempt1/receipt.json')
PROTOCOL = Path('/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md')
SPEC_KEYS = {'runner_sha256', 'repair_runtime', 'core', 'trainer', 'protocol', 'repair_history', 'seed', 'fit_seed',
             'gpu_index', 'gpu_uuid', 'expected_boot_id', 'lease_end'}


class LauncherTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='astra-additive-main-test-')
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)/'specs'
        self.base.mkdir()
        self.diag = Path(directory.name)/'diagnostics'
        self.diag.mkdir()
        self.receipt = Path(directory.name)/'receipt.json'
        self.receipt.write_bytes(RECEIPT.read_bytes())
        (self.base/'protocol.md').write_bytes(PROTOCOL.read_bytes())
        self.prechecks = Path(directory.name)/'prechecks.json'
        main.write(self.prechecks, dict(node2=dict(host_boot_id='fixture-boot', uid=0, daemon_identities=[],
                                                  gpus={str(seed): uuid for seed, uuid in main.GPUS.items()})))
        self.candidate = SimpleNamespace(CORE_PIN=main.CORE_PIN, TRAINER_PIN=main.TRAINER_PIN, REPAIR_PIN=main.REPAIR_PIN,
                                         PROTOCOL_PIN=main.PROTOCOL_PIN, allocation=Mock(), validate_spec=Mock(side_effect=self.validate_spec),
                                         runtime=Mock(return_value=SimpleNamespace(offline=Mock())),
                                         verify=Mock(), prepare=Mock(side_effect=self.native_prepare))
        self.batch = SimpleNamespace(reservations=Mock(return_value={'reservations': [], 'unresolved': []}),
                                     identity=Mock(return_value={'pid': 4321, 'start_ticks': 99}))
        self.probe = SimpleNamespace(gpu_state=Mock(return_value=True))
        for name, value in [('BASE', self.base), ('DIAGNOSTICS', self.diag), ('PRECHECKS', self.prechecks),
                            ('PRECHECKS_PIN', main.digest(self.prechecks))]:
            patcher = patch.object(main, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for patcher in [patch.object(main, 'runtime', return_value=self.candidate),
                        patch.object(main, 'load', return_value=self.batch),
                        patch.object(main.subprocess, 'Popen', side_effect=AssertionError('unmocked process spawn')),
                        patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}), redirect_stdout(io.StringIO())]:
            patcher.__enter__()
            self.addCleanup(patcher.__exit__, None, None, None)
        for seed in range(3):
            root = self.diag/f'own_replay_repair_seed{seed}_20260913_attempt1'
            root.mkdir()
            collected = Path(str(root)+'_collected')
            collected.mkdir()
            main.write(root/'spec.json', dict(runner_sha256=main.REPAIR_PIN, seed=seed, fit_seed=seed,
                                             expected_boot_id='fixture-boot', lease_end=9999999999))
            for path, data in [(root/'plan.json', {'seed': seed}), (root/'capture_complete.json', {'done': seed}),
                               (collected/'collection.json', {'collected': seed}), (collected/'scores.json', {'fixture': seed})]:
                main.write(path, data)

    def validate_spec(self, spec):
        self.assertEqual(set(spec), SPEC_KEYS)
        self.assertEqual(spec['runner_sha256'], main.RUNNER_PIN)
        for key, pin in [('core', main.CORE_PIN), ('trainer', main.TRAINER_PIN), ('protocol', main.PROTOCOL_PIN), ('repair_runtime', main.REPAIR_PIN)]:
            self.assertEqual(spec[key]['sha256'], pin)
            self.assertEqual(main.digest(spec[key]['path']), pin)
        self.assertEqual(set(spec['repair_history']), {'root', 'plan_sha256', 'completion_sha256', 'collection', 'scores_sha256'})

    def native_prepare(self, root, spec_path, spec_sha256, allow_native):
        self.assertTrue(allow_native)
        self.assertEqual(main.digest(spec_path), spec_sha256)
        spec = main.read(spec_path)
        root = Path(root)
        root.mkdir()
        plan = dict(root=str(root), specification=spec, status='READY', gpu_index=spec['gpu_index'], gpu_uuid=spec['gpu_uuid'])
        main.write(root/'plan.json', plan)
        return dict(status='NATIVE_CPU_PREPARED_NOT_LAUNCHED', plan_sha256=main.digest(root/'plan.json'))

    def ready(self, seed=0):
        main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        prepared = main.prepare(seed, main.RUNNER_PIN, self.receipt)
        root = main.root_for(seed)
        plan = main.read(root/'plan.json')
        self.candidate.verify.return_value = (None, plan, {'probe': self.probe})
        return root, prepared, plan

    def held(self, controller_code=0, collector_code=0, missing_completion=False):
        root, prepared, plan = self.ready()
        claim = Path(str(root)+'.launcher')
        claim.mkdir()
        if not missing_completion:
            main.write(root/'capture_complete.json', {'fixture_completion': True})
        controller = SimpleNamespace(pid=12345, wait=Mock(return_value=controller_code))
        collector = SimpleNamespace(pid=12346, wait=Mock(return_value=collector_code))
        return root, claim, controller, collector

    def test_01_exact_accepted_receipt(self):
        gate = main.tiny_gate(self.receipt)
        self.assertEqual(gate['sha256'], main.TINY_RECEIPT_PIN)
        self.assertEqual(gate['trainer_sha256'], main.TRAINER_PIN)
        self.assertFalse(gate['native_scientific_evidence'])

    def test_02_receipt_bytes_reject_reserialization(self):
        self.receipt.write_text(json.dumps(main.read(self.receipt), indent=2))
        with self.assertRaisesRegex(ValueError, 'receipt byte pin'):
            main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        self.assertFalse((self.base/'seed0.json').exists())
        self.candidate.prepare.assert_not_called()

    def test_03_wrong_receipt_status_checks_and_candidate_rejected(self):
        original = main.read(self.receipt)
        for change in ('status', 'checks', 'trainer_sha256'):
            modified = json.loads(json.dumps(original))
            if change == 'checks':
                modified['checks']['legacy_memory_only_parity'] = False
            else:
                modified[change] = 'wrong'
            with patch.object(main, 'read', return_value=modified):
                with self.assertRaisesRegex(ValueError, 'acceptance/config/checks'):
                    main.tiny_gate(self.receipt)

    def test_04_strict_seed_and_exact_roots(self):
        for seed in range(3):
            self.assertEqual(main.root_for(seed).name, f'additive_replay_seed{seed}_20260913_attempt1')
        self.assertEqual(len(set(main.GPUS.values())), 3)
        for seed in (True, '0', -1, 3):
            with self.assertRaises(ValueError):
                main.root_for(seed)

    def test_05_runner_byte_pin_before_execution(self):
        with patch.object(main.importlib.util, 'spec_from_file_location') as loader:
            with self.assertRaises(ValueError):
                REAL_RUNTIME('wrong')
            with self.assertRaises(ValueError):
                REAL_LOAD('no-execution', main.RUNNER, 'wrong')
            loader.assert_not_called()

    def test_06_specs_exact_history_and_source_pins(self):
        result = main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        self.assertEqual(len(result), 3)
        for seed in range(3):
            spec = main.read(self.base/f'seed{seed}.json')
            history = spec['repair_history']
            self.assertEqual(history, main.binding(self.diag/f'own_replay_repair_seed{seed}_20260913_attempt1'))
            self.assertEqual(spec['gpu_index'], seed)
            self.assertEqual(spec['gpu_uuid'], main.GPUS[seed])
            self.assertEqual(spec['expected_boot_id'], 'fixture-boot')
            self.assertEqual(spec['lease_end'], 9999999999)
            self.assertNotIn('tiny_cpu_receipt', spec)
            self.assertEqual(main.read(self.base/f'seed{seed}_gate.json')['tiny_cpu_receipt']['sha256'], main.TINY_RECEIPT_PIN)
        self.assertEqual(self.candidate.allocation.call_count, 3)

    def test_07_spec_reexecution_preserves_existing_bytes(self):
        main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        before = {path.name: path.read_bytes() for path in self.base.iterdir()}
        with self.assertRaisesRegex(ValueError, 'already exists'):
            main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.base.iterdir()})

    def test_08_source_pin_or_old_seed_error_prevents_spec_writes(self):
        with self.assertRaises(ValueError):
            main.specs(main.RUNNER_PIN, core_checksum='wrong', receipt_path=self.receipt)
        old_spec = self.diag/'own_replay_repair_seed2_20260913_attempt1/spec.json'
        changed = main.read(old_spec)
        changed['seed'] = 1
        old_spec.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, 'old original seed'):
            main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        self.assertFalse((self.base/'seed0.json').exists())

    def test_09_prepare_empty_cvd_and_gate_bound(self):
        root, prepared, plan = self.ready()
        self.assertEqual(prepared['launcher_gate']['tiny_cpu_receipt']['sha256'], main.TINY_RECEIPT_PIN)
        self.candidate.prepare.assert_called_once_with(str(root), str(self.base/'seed0.json'),
            main.digest(self.base/'seed0.json'), allow_native=True)
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            main.prepare(0, main.RUNNER_PIN, self.receipt)
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[1]}):
            with self.assertRaisesRegex(ValueError, 'empty CVD'):
                main.prepare(1, main.RUNNER_PIN, self.receipt)

    def test_10_prepare_failure_never_records_prepared(self):
        main.specs(main.RUNNER_PIN, receipt_path=self.receipt)
        self.candidate.prepare.side_effect = ValueError('fixture prepare failure')
        with self.assertRaises(ValueError):
            main.prepare(0, main.RUNNER_PIN, self.receipt)
        self.assertFalse((self.base/'seed0_prepared.json').exists())

    def test_11_changed_gate_or_plan_blocks_launch(self):
        root, prepared, plan = self.ready()
        (root/'plan.json').write_text(json.dumps(dict(plan, status='changed')))
        with self.assertRaisesRegex(ValueError, 'prepared plan/gate'):
            main.launch(0, main.RUNNER_PIN, self.receipt)
        main.subprocess.Popen.assert_not_called()

    def test_12_launch_reservation_uuid_and_three_value_verify(self):
        root, prepared, plan = self.ready()
        holder = SimpleNamespace(pid=4321)
        with patch.object(main.subprocess, 'Popen', return_value=holder) as spawn:
            result = main.launch(0, main.RUNNER_PIN, self.receipt)
        self.candidate.verify.assert_called_once_with(str(root), prepared['plan_sha256'])
        self.assertEqual(result['status'], 'LAUNCHED_NOT_RESULT')
        self.assertTrue(result['automatic_once_collection'])
        self.assertEqual(spawn.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], main.GPUS[0])
        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '')
        self.assertTrue(spawn.call_args.kwargs['start_new_session'])
        self.assertEqual(spawn.call_args.args[0][3], 'hold')
        self.assertIn(str(self.receipt), spawn.call_args.args[0])
        self.batch.reservations.assert_called_once()
        self.assertEqual(self.probe.gpu_state.call_count, 2)
        self.assertEqual(self.batch.reservations.call_args.args[1:], (0, main.GPUS[0]))
        with self.assertRaises(FileExistsError):
            main.launch(0, main.RUNNER_PIN, self.receipt)

    def test_13_reservation_conflict_preserves_claim_no_spawn(self):
        root, _, _ = self.ready()
        self.batch.reservations.side_effect = ValueError('occupied or unresolved')
        with self.assertRaisesRegex(ValueError, 'occupied'):
            main.launch(0, main.RUNNER_PIN, self.receipt)
        main.subprocess.Popen.assert_not_called()
        self.assertTrue((Path(str(root)+'.launcher')/'failure.json').is_file())

    def test_14_boot_lease_failure_never_spawns(self):
        self.ready()
        for reason in ('current boot differs', 'six-hour lease-finish margin required'):
            self.candidate.allocation.side_effect = ValueError(reason)
            with self.assertRaisesRegex(ValueError, reason):
                main.launch(0, main.RUNNER_PIN, self.receipt)
        main.subprocess.Popen.assert_not_called()

    def test_15_gpu_changes_after_reservation_never_spawns(self):
        root, _, _ = self.ready()
        self.probe.gpu_state.side_effect = [True, False]
        with self.assertRaisesRegex(ValueError, 'GPU changed'):
            main.launch(0, main.RUNNER_PIN, self.receipt)
        main.subprocess.Popen.assert_not_called()
        self.assertTrue((Path(str(root)+'.launcher')/'precheck.json').is_file())

    def test_16_success_collects_once_empty_cvd_children(self):
        root, claim, controller, collector = self.held()
        with patch.object(main.subprocess, 'Popen', side_effect=[controller, collector]) as spawn:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                self.assertEqual(main.hold(0, main.RUNNER_PIN, self.receipt), 0)
                self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], main.GPUS[0])
        self.assertEqual(spawn.call_count, 2)
        self.assertEqual([call.args[0][3] for call in spawn.call_args_list], ['controller', 'collect'])
        for call in spawn.call_args_list:
            self.assertEqual(call.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
            self.assertEqual(call.kwargs['env']['PYTHONPATH'], main.SOURCE)
            self.assertTrue(call.kwargs['start_new_session'])
        self.assertIn(main.digest(root/'capture_complete.json'), spawn.call_args_list[1].args[0])
        self.assertEqual(spawn.call_args_list[1].args[0][-1], str(root)+'_collected')
        self.assertEqual(main.read(claim/'exit.json')['returncode'], 0)
        self.assertLessEqual(main.read(claim/'controller_exit.json')['completed_unix'], main.read(claim/'collection_started.json')['started_unix'])
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
            with self.assertRaises(FileExistsError):
                main.hold(0, main.RUNNER_PIN, self.receipt)

    def test_17_failed_controller_never_collects_or_retries(self):
        _, claim, controller, collector = self.held(controller_code=9)
        with patch.object(main.subprocess, 'Popen', side_effect=[controller, collector]) as spawn:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                self.assertEqual(main.hold(0, main.RUNNER_PIN, self.receipt), 9)
        self.assertEqual(spawn.call_count, 1)
        self.assertFalse((claim/'collection_started.json').exists())
        self.assertEqual(main.read(claim/'exit.json')['returncode'], 9)

    def test_18_failed_collector_propagates_without_retry(self):
        _, claim, controller, collector = self.held(collector_code=7)
        with patch.object(main.subprocess, 'Popen', side_effect=[controller, collector]) as spawn:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                self.assertEqual(main.hold(0, main.RUNNER_PIN, self.receipt), 7)
        self.assertEqual(spawn.call_count, 2)
        self.assertEqual(main.read(claim/'collector_exit.json')['returncode'], 7)
        self.assertEqual(main.read(claim/'exit.json')['returncode'], 7)

    def test_19_missing_completion_no_collection(self):
        _, claim, controller, collector = self.held(missing_completion=True)
        with patch.object(main.subprocess, 'Popen', side_effect=[controller, collector]) as spawn:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                with self.assertRaises(FileNotFoundError):
                    main.hold(0, main.RUNNER_PIN, self.receipt)
        self.assertEqual(spawn.call_count, 1)
        self.assertTrue((claim/'holder_failure.json').exists())
        self.assertFalse((claim/'exit.json').exists())

    def test_20_holder_wrong_cvd_no_controller(self):
        self.held()
        for visibility in ('', '0', main.GPUS[1]):
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': visibility}):
                with self.assertRaisesRegex(ValueError, 'exact UUID'):
                    main.hold(0, main.RUNNER_PIN, self.receipt)
        main.subprocess.Popen.assert_not_called()

    def test_21_spawn_failure_retained_without_retry(self):
        _, claim, _, _ = self.held()
        with patch.object(main.subprocess, 'Popen', side_effect=OSError('fixture spawn failure')) as spawn:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                with self.assertRaises(OSError):
                    main.hold(0, main.RUNNER_PIN, self.receipt)
        self.assertEqual(spawn.call_count, 1)
        self.assertTrue((claim/'holder_started.json').exists())
        self.assertFalse(main.read(claim/'holder_failure.json')['controller_may_be_running'])

    def test_22_existing_collection_blocks_launch(self):
        root, _, _ = self.ready()
        Path(str(root)+'_collected').mkdir()
        with self.assertRaisesRegex(ValueError, 'already started'):
            main.launch(0, main.RUNNER_PIN, self.receipt)
        main.subprocess.Popen.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
