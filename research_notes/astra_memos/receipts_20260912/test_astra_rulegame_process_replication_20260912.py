"""Mocked CPU seed replication boundaries; no native/backend/GPU invocation."""
import ast
from contextlib import nullcontext
from dataclasses import asdict
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp')
import test_astra_rulegame_process_write_20260912 as writes
import test_astra_rulegame_process_readout_20260912 as reads

spec = importlib.util.spec_from_file_location('tested_replication', '/tmp/astra_rulegame_process_replication_20260912.py')
replica = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replica
spec.loader.exec_module(replica)
diagnostic, trainer = writes.diagnostic, writes.trainer


class ReplicationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = writes.BridgeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        self.fixture.run_pair()
        self.reference = self.fixture.output
        self.reference_pin = self.fixture.prepared['plan_sha256']
        self.reference_before = diagnostic.tree_hashes(self.reference)
        self.loads, self.launches = [], []
        self.cli_dispatches = []
        self.fail_cell, self.no_quiz, self.close_ok = None, False, True
        self.reader = None
        for context in (patch.object(diagnostic, 'native_tokenizer', return_value=self.fixture.tokenizer),
                        patch.object(replica.base_readout, 'load_driver', return_value=replica.base_write)):
            context.start()
            self.addCleanup(context.stop)

    def prepare_write(self, seed=0, **changes):
        self.writer = replica.WritePhase(seed)
        self.write_root = self.fixture.root / ('seed'+str(seed)+'_write')
        args = dict(reference_root=self.reference, reference_plan_sha256=self.reference_pin,
                    out=self.write_root, device='2', deadline=writes.iso(time.time()+3600),
                    lease_end=writes.iso(time.time()+8*3600))
        args.update(changes)
        with patch.object(writes.exporter, 'build_process_pair', side_effect=AssertionError('no new pair targets')), \
             patch.object(writes.exporter, 'export_pair', side_effect=AssertionError('no re-export')), \
             patch.object(replica.base_write, 'load_native', side_effect=AssertionError('prepare cannot load model')):
            self.prepared_write = self.writer.prepare(**args)
        self.write_plan = diagnostic.read(self.write_root/'plan.json')
        return self.prepared_write

    def mock_training(self, items, tokenizer, base, cfg, out_dir, **kwargs):
        self.assertEqual(cfg.seed, self.writer.fit_seed)
        result = self.fixture.training(items, tokenizer, base, cfg, out_dir, **kwargs)
        path = Path(out_dir)/'train_meta.json'
        metadata = diagnostic.read(path)
        metadata['seed'] = cfg.seed
        self.fixture.replace_json(path, metadata)
        return result

    def dispatch_cli(self, command, phase, class_name):
        self.assertEqual(command[:3], [os.path.abspath(sys.executable), '-B', str(replica.SELF)])
        self.cli_dispatches.append((phase.fit_seed, list(command)))
        with patch.object(replica, class_name, return_value=phase) as factory, \
             patch('sys.stdout', new=io.StringIO()) as output:
            replica.main(command[3:])
        factory.assert_called_once_with(phase.fit_seed)
        return json.loads(output.getvalue())

    def supervise_write(self, root, plan, stage, command):
        stage.mkdir()
        self.launches.append(command)
        self.assertIn('_write-worker', command)
        self.assertEqual(command[0], os.path.abspath(sys.executable))
        controller = diagnostic.read(root/'run/controller.json')
        self.assertLessEqual(controller['hard_end']-controller['started_wall'], 1200)
        self.assertEqual(controller['cleanup_reserve'], 140)
        arm = command[command.index('--arm')+1]
        token = command[command.index('--launch-token')+1]
        pin = command[command.index('--plan-sha256')+1]
        success = False
        try:
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'):
                self.dispatch_cli(command, self.writer, 'WritePhase')
            success = True
        finally:
            receipt = dict(ok=success, reservation_release_verified=True, reserved_seconds=.01,
                           owned_group_empty=True, gpu_processes_absent=True)
            replica.base_write.write_json(stage/'supervision.json', receipt)
        return receipt

    def run_write(self):
        with patch.object(self.writer, 'load_native', side_effect=self.fixture.load_native), \
             patch.object(self.writer, 'worker_ownership', return_value=nullcontext()), \
             patch.object(trainer, 'run_training', side_effect=self.mock_training), \
             patch.object(diagnostic, 'supervise', side_effect=self.supervise_write), \
             patch.object(replica.ReadoutPhase, 'evaluate', side_effect=AssertionError('no automatic readout')):
            command = [os.path.abspath(sys.executable), '-B', str(replica.SELF), 'write',
                       '--fit-seed', str(self.writer.fit_seed), '--root', str(self.write_root),
                       '--plan-sha256', self.prepared_write['plan_sha256'], '--allow-gpu']
            return self.dispatch_cli(command, self.writer, 'WritePhase')

    def prepare_readout(self, seed=None, **changes):
        seed = self.writer.fit_seed if seed is None else seed
        self.reader = replica.ReadoutPhase(seed)
        self.readout_root = self.fixture.root / ('seed'+str(seed)+'_readout')
        args = dict(write_root=self.write_root, write_plan_sha256=self.prepared_write['plan_sha256'],
            write_driver=replica.SELF, write_driver_sha256=replica.base_write.digest(replica.SELF),
            out=self.readout_root, deadline=writes.iso(time.time()+3600), lease_end=writes.iso(time.time()+8*3600))
        args.update(changes)
        self.prepared_readout = self.reader.prepare(**args)
        self.readout_plan = diagnostic.read(self.readout_root/'plan.json')
        return self.prepared_readout

    def backend(self, model, adapter):
        return reads.ReadoutTests.backend(self, model, adapter)

    def supervise_readout(self, root, plan, stage, command, call_path):
        stage.mkdir()
        self.launches.append(command)
        self.assertIn('_readout-worker', command)
        self.assertEqual(call_path, stage/'data/calls')
        self.assertEqual(command[0], os.path.abspath(sys.executable))
        controller = diagnostic.read(root/'run/controller.json')
        self.assertLessEqual(controller['hard_end']-controller['started_wall'], 1800)
        self.assertEqual(controller['cleanup_reserve'], 140)
        spec_path = Path(command[command.index('--spec')+1])
        pin = command[command.index('--spec-sha256')+1]
        original_open = Path.open
        forbidden = (self.fixture.formation, self.write_root/'material', self.fixture.audit_path, self.fixture.candidate_path)
        def guarded(path, *args, **kwargs):
            self.assertFalse(any(path == item or item in path.parents for item in forbidden), 'readout read parent/material')
            return original_open(path, *args, **kwargs)
        success = False
        try:
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'), \
                 patch.object(self.reader, 'owning_process', return_value=nullcontext()), \
                 patch.object(self.reader, 'load_driver', side_effect=AssertionError('worker cannot load writer')), \
                 patch.object(Path, 'open', guarded):
                self.dispatch_cli(command, self.reader, 'ReadoutPhase')
            success = True
        finally:
            receipt = dict(ok=success, reservation_release_verified=True, owned_group_empty=True,
                           gpu_processes_absent=True, reserved_seconds=.01)
            replica.base_write.write_json(stage/'supervision.json', receipt)
        return receipt

    def run_readout(self):
        with patch.object(diagnostic, 'NativeBackend', side_effect=self.backend), \
             patch.object(self.reader, 'close_native', return_value=self.close_ok), \
             patch.object(diagnostic, 'supervise', side_effect=self.supervise_readout), \
             patch.object(trainer, 'run_training', side_effect=AssertionError('readout cannot fit')), \
             patch.object(writes.exporter, 'build_process_pair', side_effect=AssertionError('no new material')):
            command = [os.path.abspath(sys.executable), '-B', str(replica.SELF), 'evaluate',
                       '--fit-seed', str(self.reader.fit_seed), '--root', str(self.readout_root),
                       '--plan-sha256', self.prepared_readout['plan_sha256'], '--allow-gpu']
            return self.dispatch_cli(command, self.reader, 'ReadoutPhase')

    def reseal_plan(self, root, value):
        self.fixture.replace_json(root/'plan.json', value)
        return replica.base_write.digest(root/'plan.json')

    def test_both_seeds_complete_fresh_pairs_and_separate_readouts(self):
        for seed in (0, 1):
            self.prepare_write(seed)
            self.assertEqual(self.write_plan['config'], dict(diagnostic.read(self.reference/'plan.json')['config'], seed=seed))
            result = self.run_write()
            self.assertEqual(result['fit_seed'], seed)
            self.assertFalse(result['automatic_promotion'])
            self.assertFalse((self.fixture.root/('seed'+str(seed)+'_readout')).exists())
            self.prepare_readout()
            result = self.run_readout()
            self.assertEqual(result['fit_seed'], seed)
            self.assertEqual(result['protocol']['gen_seed'], 20260912)
            self.assertEqual(result['protocol']['quiz_items_total'], 24)
            self.assertEqual(result['protocol']['max_calls'], 96)
            self.assertFalse(result['automatic_promotion'])
            for cell, item in result['cells'].items():
                metrics = item['process_metrics']
                self.assertEqual(metrics['totals']['quiz_items'], 24)
                self.assertEqual(metrics['totals']['allotted_record_opportunities'], 12)
                extra = metrics['persistent_output_diagnostics']
                self.assertEqual(extra['valid_prediction_denominator'], metrics['totals']['valid_predicted_probes'])
                self.assertLessEqual(extra['global_unique_triples'], extra['sum_task_local_unique_triples'])
                self.assertNotIn('scientific_pass', item)
        self.assertEqual([x['cell'] for x in self.loads], ['OFF', 'P_ON', 'A_ON']*2)
        self.assertEqual(diagnostic.tree_hashes(self.reference), self.reference_before)
        self.assertEqual(len({id(x['backend']) for x in self.loads}), 6)
        for seed in (0, 1):
            kinds = [command[3] for actual_seed, command in self.cli_dispatches if actual_seed == seed]
            self.assertEqual(kinds, ['write', '_write-worker', '_write-worker',
                                    'evaluate', '_readout-worker', '_readout-worker', '_readout-worker'])
        for _, command in self.cli_dispatches:
            argv = command[3:]
            required = {'write': ('--root', '--plan-sha256', '--fit-seed'),
                        'evaluate': ('--root', '--plan-sha256', '--fit-seed'),
                        '_write-worker': ('--root', '--plan-sha256', '--arm', '--launch-token'),
                        '_readout-worker': ('--spec', '--spec-sha256')}[argv[0]]
            for flag in required:
                index = argv.index(flag)
                invalid = argv[:index]+argv[index+2:]
                with self.subTest(command=argv[0], missing=flag), \
                     patch('sys.stderr', new=io.StringIO()), \
                     patch.object(replica, 'WritePhase', side_effect=AssertionError('parser must reject first')), \
                     patch.object(replica, 'ReadoutPhase', side_effect=AssertionError('parser must reject first')), \
                     self.assertRaises(SystemExit) as stopped:
                    replica.main(invalid)
                self.assertEqual(stopped.exception.code, 2)

    def test_raw_material_exact_copy_and_seed_not_generation_seed(self):
        self.prepare_write(1)
        self.assertEqual(diagnostic.tree_hashes(self.reference/'material'), diagnostic.tree_hashes(self.write_root/'material'))
        self.assertIsNone(self.write_plan['init_adapter'])
        self.assertEqual(self.write_plan['replication']['planned_fit_seeds'], [0, 1])
        self.assertEqual(self.write_plan['replication']['generation_seed'], 20260912)
        self.assertEqual(self.write_plan['tokens'], diagnostic.read(self.reference/'plan.json')['tokens'])

    def test_only_zero_one_fit_seeds(self):
        for seed in (2, -1, 3, True, '0', None):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                replica.WritePhase(seed)
            with self.assertRaises(ValueError):
                replica.ReadoutPhase(seed)

    def test_historical_seed_two_recipe_and_bytes_unchanged(self):
        self.prepare_write()
        self.assertEqual(replica.base_write.fit_config(trainer, self.fixture.model).seed, 2)
        self.assertEqual(replica.base_write.digest(replica.WRITE_SOURCE), replica.WRITE_SHA)
        self.assertEqual(replica.base_write.digest(replica.READOUT_SOURCE), replica.READOUT_SHA)

    def test_seed_or_recipe_or_contract_resealed_tamper_rejected(self):
        self.prepare_write()
        original = self.write_plan
        for changes in ({'fit_seed': 1}, {'fit_seed': False}, {'config': dict(original['config'], seed=2)},
                        {'config': dict(original['config'], lr=.01)}, {'init_adapter': '/warm'},
                        {'replication': dict(original['replication'], automatic_promotion=True)}):
            pin = self.reseal_plan(self.write_root, dict(original, **changes))
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.writer.checked_plan(self.write_root, pin)

    def test_reference_wrong_protocol_or_hash_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare_write(reference_plan_sha256='0'*64)
        original = diagnostic.read(self.reference/'plan.json')
        wrong = dict(original, protocol='rulegame_record_write_v2')
        pin = self.reseal_plan(self.reference, wrong)
        with self.assertRaises(ValueError):
            self.prepare_write(reference_plan_sha256=pin)

    def test_reference_incomplete_or_mutated_completion_rejected(self):
        self.fixture.replace_json(self.reference/'run/result.json', {'status': 'FAILED', 'arms': {}})
        with self.assertRaises(ValueError):
            self.prepare_write()
        self.assertFalse((self.fixture.root/'seed0_write').exists())

    def test_fresh_roots_deadlines_and_no_clipping(self):
        for values in ({'out': self.reference}, {'out': self.fixture.formation/'nested'},
                       {'deadline': writes.iso(time.time()+1100)}, {'device': '0,1'},
                       {'lease_end': writes.iso(time.time()+6*3600)}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.prepare_write(**values)
        self.prepare_write()
        with self.assertRaises(ValueError):
            self.prepare_write()
        bounds = self.write_plan['replication']
        self.assertEqual(sum(bounds[k] for k in ('write_controller_seconds', 'write_collection_seconds',
                         'readout_controller_seconds', 'readout_collection_seconds')), 3600)
        self.assertFalse(bounds['combined_controller'])

    def test_readout_requires_own_seed_complete_new_pair(self):
        self.prepare_write()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.prepare_readout()
        self.run_write()
        with self.assertRaises(ValueError):
            self.prepare_readout(seed=1)
        with self.assertRaises(ValueError):
            self.prepare_readout(write_driver=replica.WRITE_SOURCE, write_driver_sha256=replica.WRITE_SHA)

    def test_loss_token_metadata_and_seed_summary_rejected(self):
        self.prepare_write()
        self.run_write()
        path = self.write_root/'fits/P/adapter/train_meta.json'
        original = diagnostic.read(path)
        for changed in (dict(original, seed=2), dict(original, steps=11), dict(original, tokens=0)):
            self.fixture.replace_json(path, changed)
            with self.assertRaises(ValueError):
                self.writer.validate_fit(self.write_root, 'P', self.write_plan, diagnostic, trainer)
        self.fixture.replace_json(path, original)
        manifest = self.write_root/'fits/P/adapter/train_manifest.json'
        bad = diagnostic.read(manifest)
        bad['nonfinite_batches'] = 1
        self.fixture.replace_json(manifest, bad)
        with self.assertRaises(ValueError):
            self.writer.validate_fit(self.write_root, 'P', self.write_plan, diagnostic, trainer)

    def test_changed_raw_target_mask_or_parent_context_rejected(self):
        self.prepare_write()
        path = self.write_root/'material/corpora/P.json'
        data = diagnostic.read(path)
        data['corpus'][0]['spans'][0][0] += '\nREVIEW_PARENT_TEXT_ONLY'
        self.fixture.replace_json(path, data)
        with self.assertRaises(ValueError):
            self.writer.checked_plan(self.write_root, self.prepared_write['plan_sha256'])

    def test_failed_second_fit_preserves_partial_and_never_readout(self):
        self.prepare_write()
        self.fixture.fail_arm = 'A'
        with self.assertRaisesRegex(RuntimeError, 'mock fit failed A'):
            self.run_write()
        self.assertTrue((self.write_root/'run/failure.json').exists())
        self.assertFalse((self.write_root/'run/result.json').exists())
        self.assertTrue((self.write_root/'fits/P/manifest.json').exists())
        with self.assertRaises(FileExistsError):
            self.run_write()
        with self.assertRaises(ValueError):
            self.prepare_readout()

    def test_gpu_opt_in_required_for_all_run_paths(self):
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            replica.WritePhase(0).write_pair('/not/read', '0'*64)
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            replica.ReadoutPhase(0).evaluate('/not/read', '0'*64)
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            replica.WritePhase(0).worker('/not/read', 'P', '0'*64, 'token')
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            replica.ReadoutPhase(0).worker('/not/read', '0'*64)

    def test_readout_seed_protocol_and_generation_tamper(self):
        self.prepare_write()
        self.run_write()
        self.prepare_readout()
        original = self.readout_plan
        for changed in (dict(original, fit_seed=1), dict(original, protocol=dict(original['protocol'], gen_seed=1)),
                        dict(original, protocol=dict(original['protocol'], task_prefix='PARENT'))):
            pin = self.reseal_plan(self.readout_root, changed)
            with self.assertRaises(ValueError):
                self.reader.checked_plan(self.readout_root, pin)

    def test_wrong_seed_in_completed_write_result_rejected(self):
        self.prepare_write()
        self.run_write()
        path = self.write_root/'run/result.json'
        data = diagnostic.read(path)
        data['fit_seed'] = 1
        self.fixture.replace_json(path, data)
        with self.assertRaisesRegex(ValueError, 'seed/promotion'):
            self.prepare_readout()

    def test_failed_readout_middle_cell_has_no_aggregate_or_retry(self):
        self.prepare_write()
        self.run_write()
        self.prepare_readout()
        self.fail_cell = 'P_ON'
        with self.assertRaisesRegex(RuntimeError, 'mock native load failed'):
            self.run_readout()
        self.assertTrue((self.readout_root/'run/failure.json').exists())
        self.assertFalse((self.readout_root/'run/result.json').exists())
        self.assertEqual([x['cell'] for x in self.loads], ['OFF', 'P_ON'])
        with self.assertRaises(FileExistsError):
            self.run_readout()

    def test_invalid_quizzes_keep_fixed_denominators(self):
        self.prepare_write()
        self.run_write()
        self.prepare_readout()
        self.no_quiz = True
        result = self.run_readout()
        for cell in result['cells'].values():
            metrics = cell['process_metrics']
            self.assertEqual(metrics['quiz_accuracy_fixed24'], 0)
            self.assertEqual(metrics['invalid_or_absent_quiz_tasks'], 4)
            self.assertEqual(metrics['totals']['quiz_items'], 24)

    def test_interpreter_spelling_and_worker_extra_context(self):
        self.prepare_write()
        self.run_write()
        self.prepare_readout()
        self.assertEqual(self.readout_plan['python'], os.path.abspath(sys.executable))
        specs = self.reader.worker_spec(self.readout_root, self.readout_plan, self.readout_plan['lineage'], 'OFF', time.time()+1800)
        specs['parent_text'] = 'forbidden'
        path = self.fixture.root/'spec.json'
        replica.base_write.write_json(path, specs)
        with self.assertRaisesRegex(ValueError, 'extra context'):
            self.reader.worker(path, replica.base_write.digest(path), allow_gpu=True)

    def test_release_failure_never_complete(self):
        self.prepare_write()
        self.run_write()
        self.prepare_readout()
        self.close_ok = False
        with self.assertRaises(ValueError):
            self.run_readout()
        self.assertFalse((self.readout_root/'run/result.json').exists())

    def test_full_metrics_remain_descriptive_not_registered_gate(self):
        contract = replica.contract(0)
        self.assertFalse(contract['automatic_promotion'])
        self.assertIn('Main-side', contract['scientific_criterion'])
        with patch('sys.stdout', new=io.StringIO()) as output, self.assertRaises(SystemExit) as stopped:
            replica.main(['--help'])
        self.assertEqual(stopped.exception.code, 0)
        self.assertIn('prepare-readout', output.getvalue())
        self.assertNotIn('run-seed', output.getvalue())

    def test_static_readout_generation_algorithm_preserved(self):
        original = ast.parse(replica.READOUT_SOURCE.read_text())
        local = ast.parse(replica.SELF.read_text())
        before = next(node for node in original.body if isinstance(node, ast.FunctionDef) and node.name == 'worker')
        phase = next(node for node in local.body if isinstance(node, ast.ClassDef) and node.name == 'ReadoutPhase')
        after = next(node for node in phase.body if isinstance(node, ast.FunctionDef) and node.name == 'worker')
        after.args.args = after.args.args[1:]
        class Unqualify(ast.NodeTransformer):
            def visit_Attribute(self, node):
                node = self.generic_visit(node)
                if isinstance(node.value, ast.Name) and node.value.id in ('self', 'base_readout'):
                    return ast.copy_location(ast.Name(node.attr, node.ctx), node)
                return node
        self.assertEqual(ast.dump(before, include_attributes=False),
                         ast.dump(Unqualify().visit(after), include_attributes=False))

    def test_saved_adapter_mutation_rejects_readout(self):
        self.prepare_write()
        self.run_write()
        path = self.write_root/'fits/P/adapter/adapter_model.safetensors'
        with path.open('ab') as stream:
            stream.write(b'forged')
        with self.assertRaises(ValueError):
            self.prepare_readout()

    def test_resealed_material_cannot_change_reference_bytes(self):
        self.prepare_write()
        path = self.write_root/'material/corpora/P.json'
        corpus = diagnostic.read(path)
        corpus['corpus'][0]['spans'][1][0] += ' repaired target'
        self.fixture.replace_json(path, corpus)
        files = diagnostic.tree_hashes(self.write_root/'material', ('manifest.json',))
        self.fixture.replace_json(self.write_root/'material/manifest.json', {'files': files})
        changed = dict(self.write_plan, material_files=files,
                       material_manifest_sha256=replica.base_write.digest(self.write_root/'material/manifest.json'))
        pin = self.reseal_plan(self.write_root, changed)
        with self.assertRaisesRegex(ValueError, 'reference material/lineage'):
            self.writer.checked_plan(self.write_root, pin)

    def test_failed_prepare_cannot_be_resumed_as_write(self):
        self.prepare_write()
        replica.base_write.write_json(self.write_root/'prepare_failure.json', {'error': 'synthetic retained failure'})
        with self.assertRaisesRegex(ValueError, 'failed preparation'):
            self.run_write()
        self.assertFalse((self.write_root/'run').exists())

    def test_symlink_metadata_and_frozen_helper_tamper_rejected(self):
        path = self.fixture.root/'aliased.json'
        path.symlink_to(self.fixture.audit_path)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            replica.bytes_read(path)
        with self.assertRaisesRegex(ValueError, 'frozen helper changed'):
            replica.load_support(replica.WRITE_SOURCE, '0'*64, 'never_loaded_bad_helper')

    def test_readout_requires_full_separate_eighteen_hundred_seconds(self):
        self.prepare_write()
        self.run_write()
        with self.assertRaisesRegex(ValueError, '1800s'):
            self.prepare_readout(deadline=writes.iso(time.time()+1700))
        self.assertFalse(self.readout_root.exists())

    def test_both_prepare_commands_real_parser_and_dispatch_for_each_seed(self):
        for seed in (0, 1):
            self.writer = replica.WritePhase(seed)
            self.write_root = self.fixture.root/('seed'+str(seed)+'_write')
            prefix = [os.path.abspath(sys.executable), '-B', str(replica.SELF)]
            deadline, lease = writes.iso(time.time()+3600), writes.iso(time.time()+8*3600)
            command = prefix+['prepare-write', '--fit-seed', str(seed),
                '--reference-write-root', str(self.reference), '--reference-write-plan-sha256', self.reference_pin,
                '--out', str(self.write_root), '--device', '2', '--deadline', deadline, '--lease-end', lease]
            self.prepared_write = self.dispatch_cli(command, self.writer, 'WritePhase')
            self.write_plan = diagnostic.read(self.write_root/'plan.json')
            self.assertEqual(self.write_plan['fit_seed'], seed)
            self.run_write()
            self.reader = replica.ReadoutPhase(seed)
            self.readout_root = self.fixture.root/('seed'+str(seed)+'_readout')
            command = prefix+['prepare-readout', '--fit-seed', str(seed), '--write-root', str(self.write_root),
                '--write-plan-sha256', self.prepared_write['plan_sha256'],
                '--write-driver-sha256', replica.base_write.digest(replica.SELF),
                '--out', str(self.readout_root), '--deadline', deadline, '--lease-end', lease]
            self.prepared_readout = self.dispatch_cli(command, self.reader, 'ReadoutPhase')
            plan = diagnostic.read(self.readout_root/'plan.json')
            self.assertEqual(plan['fit_seed'], seed)
            self.assertFalse((self.readout_root/'run').exists())


if __name__ == '__main__':
    unittest.main()
