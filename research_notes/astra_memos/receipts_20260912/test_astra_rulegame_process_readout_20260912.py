"""Synthetic-only process readout tests; no native/GPU/network/Git execution."""
import ast
from contextlib import nullcontext
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp')
import test_astra_rulegame_process_write_20260912 as writes
import test_astra_rulegame_record_readout_20260912 as old_tests

spec = importlib.util.spec_from_file_location('tested_process_readout', '/tmp/astra_rulegame_process_readout_20260912.py')
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
diagnostic = writes.diagnostic


class ReadoutTests(unittest.TestCase):
    def setUp(self):
        self.fixture = writes.BridgeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        self.write_root = self.fixture.output
        self.output = self.fixture.root / 'process_readout'
        self.fail_cell, self.close_ok, self.no_quiz = None, True, False
        self.loads, self.launches = [], []
        self.corrupt = None
        self.driver_sha = bridge.digest(writes.bridge.SELF)
        def load(path, expected_hash):
            self.assertEqual(expected_hash, self.driver_sha)
            self.assertEqual(bridge.digest(path), expected_hash)
            return writes.bridge
        for context in (patch.object(bridge, 'load_driver', side_effect=load),
                        patch.object(diagnostic, 'native_tokenizer', return_value=self.fixture.tokenizer)):
            context.start()
            self.addCleanup(context.stop)

    def prepare(self, **changes):
        args = dict(write_root=self.write_root, write_plan_sha256=self.fixture.prepared['plan_sha256'],
                    write_driver=str(writes.bridge.SELF), write_driver_sha256=self.driver_sha, out=self.output,
                    deadline=writes.iso(time.time()+3600), lease_end=writes.iso(time.time()+8*3600))
        args.update(changes)
        self.prepared = bridge.prepare(**args)
        return self.prepared

    def completed(self):
        self.fixture.run_pair()
        self.prepare()
        self.plan = bridge.read(self.output / 'plan.json')

    def backend(self, model, adapter):
        cell = 'OFF' if adapter is None else Path(adapter).parent.name+'_ON'
        identity = diagnostic.expected_identity(dict(model=model), adapter)
        native = old_tests.writes.Backend(tokenizer=old_tests.writes.Tokenizer())
        native.source_identity = identity
        native.no_quiz = self.no_quiz
        native.backend = SimpleNamespace(tok=native.tokenizer)
        self.loads.append(dict(cell=cell, model=model, adapter=adapter, backend=native))
        if cell == self.fail_cell:
            raise RuntimeError('mock native load failed: '+cell)
        return native

    def supervise(self, root, plan, stage, command, call_path):
        stage.mkdir()
        self.launches.append(command)
        self.assertEqual(call_path, stage / 'data/calls')
        self.assertEqual(command[0], os.path.abspath(sys.executable))
        spec_path = Path(command[command.index('--spec')+1])
        pin = command[command.index('--spec-sha256')+1]
        original_open = Path.open
        blocked = (self.fixture.formation, self.write_root / 'material', self.fixture.audit_path, self.fixture.candidate_path)
        def guarded_open(path, *args, **kwargs):
            self.assertFalse(any(path == entry or entry in path.parents for entry in blocked), 'worker read teacher/corpus data')
            return original_open(path, *args, **kwargs)
        success = False
        try:
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'), \
                 patch.object(bridge, 'owning_process', return_value=nullcontext()), \
                 patch.object(bridge, 'load_driver', side_effect=AssertionError('worker cannot load material/writer')), \
                 patch.object(Path, 'open', guarded_open):
                bridge.worker(spec_path, pin, allow_gpu=True)
            if self.corrupt:
                self.corrupt(stage)
            success = True
        finally:
            receipt = dict(ok=success, reservation_release_verified=True, owned_group_empty=True,
                           gpu_processes_absent=True, reserved_seconds=.01)
            bridge.write_json(stage / 'supervision.json', receipt)
        return receipt

    def evaluate(self, allow_gpu=True):
        with patch.object(diagnostic, 'NativeBackend', side_effect=self.backend), \
             patch.object(bridge, 'close_native', return_value=self.close_ok), \
             patch.object(diagnostic, 'supervise', side_effect=self.supervise), \
             patch.object(writes.trainer, 'run_training', side_effect=AssertionError('no fits')), \
             patch.object(writes.exporter, 'build_process_pair', side_effect=AssertionError('no new material targets')), \
             patch.object(writes.exporter, 'export_pair', side_effect=AssertionError('no export')), \
             patch.object(diagnostic, 'material', side_effect=AssertionError('no legacy material')):
            return bridge.evaluate(self.output, self.prepared['plan_sha256'], allow_gpu=allow_gpu)

    def test_complete_process_pair_prepare_native_masks_losses_and_metadata(self):
        self.fixture.run_pair()
        before = diagnostic.tree_hashes(self.write_root)
        with patch.object(writes.exporter, 'build_process_pair', side_effect=AssertionError('no rebuild')), \
             patch.object(writes.exporter, 'export_pair', side_effect=AssertionError('no new targets')), \
             patch.object(diagnostic, 'NativeBackend', side_effect=AssertionError('no model in prepare')):
            self.prepare()
        plan = bridge.read(self.output / 'plan.json')
        self.assertEqual(diagnostic.tree_hashes(self.write_root), before)
        self.assertEqual(plan['conditioning'], bridge.CONDITIONING)
        self.assertEqual(plan['model_origin'], bridge.ORIGIN)
        self.assertFalse(plan['claims']['clean_lineage'])
        self.assertEqual(plan['protocol']['quiz_items_total'], 24)
        self.assertEqual(plan['protocol']['max_calls'], 96)
        self.assertEqual(plan['protocol']['max_generated_tokens'], 27600)
        for arm in ('P', 'A'):
            metadata = plan['lineage']['training_metadata'][arm]
            self.assertEqual(len(metadata['mean_loss_per_epoch']), 12)
            self.assertEqual(metadata['steps'], 12)
            self.assertEqual(metadata['exposure']['row_presentations'], 24)
            self.assertFalse(metadata['exposure']['token_matched'])
        self.assertNotEqual(plan['lineage']['training_metadata']['P']['tokens'], plan['lineage']['training_metadata']['A']['tokens'])

    def test_complete_three_fresh_parent_free_cells_and_metrics(self):
        self.completed()
        before = diagnostic.tree_hashes(self.write_root)
        result = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE_EXPLORATORY_READOUT')
        self.assertEqual([row['cell'] for row in self.loads], ['OFF', 'P_ON', 'A_ON'])
        self.assertEqual(len({id(row['backend']) for row in self.loads}), 3)
        self.assertEqual(result['model_origin'], bridge.ORIGIN)
        self.assertFalse(result['adaptation_test'])
        self.assertEqual(diagnostic.tree_hashes(self.write_root), before)
        for cell, loaded in zip(bridge.CELLS, self.loads):
            requests = loaded['backend'].requests
            self.assertEqual(len(requests), 32)
            self.assertEqual({row['role'] for row in requests}, {'wake', 'record'})
            self.assertEqual({row['eid'] for row in requests}, set(diagnostic.schedule()['evaluation']))
            for request in requests:
                self.assertNotIn(writes.LESSON, request['prompt'])
                self.assertNotIn('Temporary parent restatement:', request['prompt'])
                self.assertEqual(request['temperature'], .7)
                self.assertEqual(request['protocol'], 'interaction_v3')
                if request['role'] == 'record':
                    self.assertIn(diagnostic.RELATION_DEFINITION, request['prompt'])
                if request['role'] == 'wake' and request['tick'] == 1:
                    self.assertNotIn('\n[OUTCOME] ', request['prompt'])
            metrics = result['cells'][cell]['process_metrics']
            self.assertEqual(metrics['totals']['quiz_items'], 24)
            self.assertEqual(metrics['totals']['executed_probes'], 12)
            self.assertEqual(metrics['totals']['actual_records'], 12)
            self.assertEqual(metrics['totals']['allotted_record_opportunities'], 12)
            self.assertEqual(metrics['quiz_accuracy_fixed24'], result['cells'][cell]['result']['mean_quiz_accuracy'])

    def test_incomplete_or_failed_write_pair_never_prepares(self):
        with self.assertRaises(FileNotFoundError):
            self.prepare()
        self.assertFalse(self.output.exists())
        self.fixture.fail_arm = 'A'
        with self.assertRaisesRegex(RuntimeError, 'mock fit failed'):
            self.fixture.run_pair()
        with self.assertRaisesRegex(ValueError, 'failed/partial'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_reject_record_P0_v1_material_even_with_readable_structure(self):
        self.fixture.run_pair()
        written = bridge.read(self.write_root / 'plan.json')
        for version in ('rulegame_record_material', 'P0', 'rulegame_grounded_process_pair_v1'):
            with self.subTest(version=version):
                other = dict(written, material_protocol=version)
                with self.assertRaisesRegex(ValueError, 'wrong process material'):
                    bridge.material_custody(writes.bridge, self.write_root, other, diagnostic, writes.exporter, writes.trainer)

    def test_parent_text_in_even_coherent_rendered_receipts_fails_native(self):
        self.fixture.run_pair()
        written = bridge.read(self.write_root / 'plan.json')
        corpus_path = self.write_root / 'material/corpora/P.json'
        receipt_path = self.write_root / 'material/audit/token_receipts.json'
        corpus, receipt = bridge.read(corpus_path), bridge.read(receipt_path)
        context = corpus['corpus'][0]['spans'][0][0] + '\nTemporary parent restatement:\n' + writes.LESSON
        corpus['corpus'][0]['spans'][0][0] = context
        receipt['receipts']['P'][0]['transformed_training']['rendered_context'] = context
        self.fixture.replace_json(corpus_path, corpus)
        self.fixture.replace_json(receipt_path, receipt)
        review = bridge.read(self.fixture.audit_path)
        review['native_review']['rows'][0]['rendered_context_sha256'] = hashlib.sha256(context.encode()).hexdigest()
        self.fixture.replace_json(self.fixture.audit_path, review)
        self.fixture.replace_json(self.write_root / 'material/audit/main_review.json', review)
        with self.assertRaisesRegex(ValueError, 'parent-removed context'):
            bridge.material_custody(writes.bridge, self.write_root, written, diagnostic, writes.exporter, writes.trainer, native=True)

    def test_dirty_adapter_and_warm_start_receipts_rejected(self):
        self.completed()
        path = self.write_root / 'fits/P/adapter/train_manifest.json'
        original = bridge.read(path)
        changed = dict(original, warm_start={'adapter': '/dirty'})
        self.fixture.replace_json(path, changed)
        with self.assertRaisesRegex(ValueError, 'warm-start'):
            writes.bridge.validate_fit(self.write_root, 'P', bridge.read(self.write_root / 'plan.json'), diagnostic, writes.trainer)
        with self.assertRaises(ValueError):
            bridge.checked_plan(self.output, self.prepared['plan_sha256'])
        self.fixture.replace_json(path, original)
        adapter = self.write_root / 'fits/A/adapter/adapter_model.safetensors'
        with adapter.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaises(ValueError):
            bridge.checked_plan(self.output, self.prepared['plan_sha256'])

    def test_nonfinite_loss_and_token_metadata_rejected(self):
        self.fixture.run_pair()
        written = bridge.read(self.write_root / 'plan.json')
        path = self.write_root / 'fits/P/adapter/train_manifest.json'
        original = bridge.read(path)
        for key, value in [('final_loss', 'NaN'), ('tokens', {'total': 1}), ('steps', 11)]:
            with self.subTest(key=key):
                self.fixture.replace_json(path, dict(original, **{key: value}))
                with self.assertRaises((ValueError, TypeError)):
                    writes.bridge.validate_fit(self.write_root, 'P', written, diagnostic, writes.trainer)
        self.fixture.replace_json(path, original)
        altered = copy.deepcopy(written)
        altered['tokens']['P']['exposure']['full_target_tokens_seen'] += 1
        with self.assertRaisesRegex(ValueError, 'token/exposure'):
            bridge.material_custody(writes.bridge, self.write_root, altered, diagnostic, writes.exporter, writes.trainer)

    def test_native_context_masks_EOS_reject_before_output(self):
        self.fixture.run_pair()
        original = writes.bridge.full_tokens
        def wrong(*args):
            result = original(*args)
            result['rows'][0]['labels'][0] = 1
            return result
        with patch.object(writes.bridge, 'full_tokens', side_effect=wrong):
            with self.assertRaisesRegex(ValueError, 'native raw-target/mask/EOS'):
                self.prepare()
        self.assertFalse(self.output.exists())

    def test_invalid_quiz_zero_keeps_24_denominator(self):
        self.completed()
        self.no_quiz = True
        result = self.evaluate()
        for cell in bridge.CELLS:
            metrics = result['cells'][cell]['process_metrics']
            self.assertEqual(metrics['quiz_accuracy_fixed24'], 0)
            self.assertEqual(metrics['totals']['quiz_items'], 24)
            self.assertEqual(metrics['invalid_or_absent_quiz_tasks'], 4)

    def test_no_opt_in_no_worker_and_middle_failure_no_partial_aggregate(self):
        self.completed()
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            self.evaluate(False)
        self.assertFalse((self.output / 'run').exists())
        self.fail_cell = 'P_ON'
        with self.assertRaisesRegex(RuntimeError, 'mock native load failed'):
            self.evaluate()
        self.assertEqual([row['cell'] for row in self.loads], ['OFF', 'P_ON'])
        self.assertFalse((self.output / 'run/result.json').exists())
        self.assertIsNone(bridge.read(self.output / 'run/failure.json')['aggregate'])
        with self.assertRaises(FileExistsError):
            self.evaluate()

    def test_worker_extra_parent_context_protocol_and_dirty_OFF_fail(self):
        self.completed()
        stage = self.output / 'run'
        stage.mkdir()
        for index, mutation in enumerate(({'parent_context': 'forbidden'}, {'protocol': {'name': 'old'}},
                                           {'adapter': '/dirty', 'adapter_files': {'a': 'b'}})):
            with self.subTest(mutation=mutation):
                spec_path = stage / 'OFF.spec.json'
                spec = bridge.worker_spec(self.output, self.plan, self.plan['lineage'], 'OFF', time.time()+1800)
                spec.update(mutation)
                self.fixture.replace_json(spec_path, spec)
                with patch.object(diagnostic, 'NativeBackend', side_effect=AssertionError('must not load')), \
                     self.assertRaises(ValueError):
                    bridge.worker(spec_path, bridge.digest(spec_path), allow_gpu=True)

    def test_resealed_parent_prompt_and_native_generation_tamper_rejected(self):
        self.completed()
        def corrupt(stage):
            if stage.name == 'OFF':
                path = stage / 'data/calls/0000.request.json'
                row = bridge.read(path)
                row['request']['prompt'] += '\nTemporary parent restatement: forbidden'
                self.fixture.replace_json(path, row)
                self.fixture.replace_json(stage / 'data/manifest.json', {'files': diagnostic.tree_hashes(stage / 'data', ('manifest.json',))})
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, 'readout replay failed'):
            self.evaluate()
        self.assertEqual(len(self.loads), 1)

    def test_lease_margin_and_venv_spelling_preserved(self):
        self.fixture.run_pair()
        with self.assertRaisesRegex(ValueError, 'six-hour'):
            self.prepare(lease_end=writes.iso(time.time()+3600))
        self.assertFalse(self.output.exists())
        link = self.fixture.root / 'native-python'
        link.symlink_to(sys.executable)
        self.assertEqual(bridge.absolute_python(str(link)), str(link))

    def test_resealed_native_prompt_token_tamper_rejected(self):
        self.completed()
        def corrupt(stage):
            path = stage / 'data/calls/0000.response.json'
            row = bridge.read(path)
            row['response']['prompt_token_ids'][0] += 1
            row['response_sha256'] = diagnostic.value_hash(row['response'])
            self.fixture.replace_json(path, row)
            self.fixture.replace_json(stage / 'data/manifest.json', {'files': diagnostic.tree_hashes(stage / 'data', ('manifest.json',))})
        self.corrupt = corrupt
        with self.assertRaises(ValueError):
            self.evaluate()
        self.assertFalse((self.output / 'run/result.json').exists())
        self.assertEqual(len(self.loads), 1)

    def test_cleanup_failure_keeps_capture_and_stops_next_cell(self):
        self.completed()
        self.close_ok = False
        with self.assertRaisesRegex(ValueError, 'cleanup unverified'):
            self.evaluate()
        self.assertEqual(len(self.loads), 1)
        self.assertFalse(bridge.read(self.output / 'run/OFF/data/backend.cleanup.json')['closed'])
        self.assertTrue((self.output / 'run/OFF/data/calls/0000.request.json').is_file())
        self.assertFalse((self.output / 'run/P_ON').exists())

    def test_protocol_tamper_even_rehashed_rejected(self):
        self.completed()
        path = self.output / 'plan.json'
        plan = bridge.read(path)
        plan['protocol']['tasks'] = ['rule0/forbidden']
        self.fixture.replace_json(path, plan)
        with self.assertRaisesRegex(ValueError, 'prospective readout protocol'):
            bridge.checked_plan(self.output, bridge.digest(path))


class InterfaceTests(unittest.TestCase):
    def test_wrong_writer_hash_rejected_before_import(self):
        with self.assertRaisesRegex(ValueError, 'before import'):
            bridge.load_driver(str(writes.bridge.SELF), '0'*64)

    def test_record_writer_never_accepted_as_process_writer(self):
        path = Path('/tmp/astra_rulegame_record_write_v2_20260912.py')
        with self.assertRaises((ValueError, AttributeError)):
            bridge.load_driver(path, bridge.digest(path))

    def test_generation_and_ownership_functions_are_exact_frozen_reference(self):
        def functions(path):
            return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        old, new = functions(bridge.FROZEN_READOUT), functions(bridge.SELF)
        for name in ('worker', 'worker_spec', 'owning_process', 'close_native', 'verify_worker_bytes',
                     'work_window', 'supervised_window', 'absolute_python'):
            with self.subTest(name=name):
                self.assertEqual(new[name], old[name])

    def test_controller_cleanup_window_and_alarm_restoration(self):
        with self.assertRaisesRegex(ValueError, 'cleanup reserve'):
            with bridge.work_window(time.time()+100):
                pass
        with bridge.work_window(time.time()+1800):
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 0)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))

    def test_prediction_emission_not_execution_or_record_faithfulness(self):
        with tempfile.TemporaryDirectory(prefix='process-metrics-', dir='/tmp') as folder:
            data = Path(folder)
            (data / 'calls').mkdir()
            tasks = diagnostic.schedule()['evaluation']
            for index, eid in enumerate(tasks):
                bridge.write_json(data / 'calls' / f'{index:04d}.request.json', {'request': {'eid': eid, 'role': 'wake'}})
                bridge.write_json(data / 'calls' / f'{index:04d}.response.json', {'response': {'text': 'PREDICT: T\nPREDICT: F\nACT: TRY 1,2,3' if index == 0 else 'DONE'}})
            bridge.write_json(data / 'calls/0004.request.json', {'request': {'eid': tasks[0], 'role': 'record'}})
            bridge.write_json(data / 'calls/0004.response.json', {'response': {'text': 'PREDICT: T'}})
            audit = dict(result=dict(tasks=[dict(eid=eid, tries=1 if index == 0 else 0, valid_quiz=False, quiz_accuracy=0)
                                           for index, eid in enumerate(tasks)], calls=5, roles={'wake': 4, 'record': 1},
                                     faithful_records=0, mean_quiz_accuracy=0),
                         events=[dict(kind='execution', action_kind='try', eid=tasks[0], values=[1, 2, 3],
                                      predicted=None, prediction_ambiguous=True, observed=True),
                                 dict(kind='record', eid=tasks[0], eligible=False)])
            metrics = bridge.process_metrics(data, audit, diagnostic)
            self.assertEqual(metrics['totals']['predict_lines'], 2)
            self.assertEqual(metrics['totals']['predict_emitting_responses'], 1)
            self.assertEqual(metrics['totals']['valid_predicted_probes'], 0)
            self.assertIsNone(metrics['prediction_accuracy'])
            self.assertEqual(metrics['faithful_record_fraction_actual'], 0)
            self.assertEqual(metrics['faithful_record_fraction_allotted12'], 0)
            self.assertEqual(metrics['totals']['quiz_items'], 24)
            self.assertIn('explicitly requests', metrics['limitation'])

    def test_missing_predictions_records_have_null_observed_denominators(self):
        with tempfile.TemporaryDirectory(prefix='process-metrics-', dir='/tmp') as folder:
            data = Path(folder)
            (data / 'calls').mkdir()
            audit = dict(result=dict(tasks=[dict(eid=eid, tries=0, valid_quiz=False, quiz_accuracy=0)
                                           for eid in diagnostic.schedule()['evaluation']], calls=0, roles={},
                                     faithful_records=0, mean_quiz_accuracy=0), events=[])
            metrics = bridge.process_metrics(data, audit, diagnostic)
            self.assertIsNone(metrics['faithful_record_fraction_actual'])
            self.assertIsNone(metrics['prediction_fraction_executed_probes'])
            self.assertEqual(metrics['faithful_record_fraction_allotted12'], 0)
            self.assertEqual(metrics['invalid_or_absent_quiz_tasks'], 4)
            audit['result']['tasks'][0]['quiz_accuracy'] = 1
            with self.assertRaisesRegex(ValueError, 'invalid quiz'):
                bridge.process_metrics(data, audit, diagnostic)


if __name__ == '__main__':
    unittest.main()
