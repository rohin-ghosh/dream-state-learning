"""INJECTED_CPU_TEST only: orchestration checks, never native assay evidence."""

import argparse
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pcfl_event_sequence_v2_followup as api


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True)


def inventory(root):
    return {path.relative_to(root).as_posix(): {'size': path.stat().st_size, 'sha256': api.pin(path)['sha256']}
            for path in root.rglob('*') if path.is_file()}


class FollowupTests(unittest.TestCase):
    def setUp(self, seed=1):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        source = self.base / 'NONNATIVE_SOURCE_FIXTURE'
        (source / 'gpu').mkdir(parents=True)
        modules = {}
        for name in ('fit', 'readout', 'outer', 'campaign', 'lifecycle'):
            path = source / 'gpu' / f'{name}.py'
            path.write_text('NONNATIVE PLACEHOLDER, NOT RUNTIME CODE\n')
            modules[name] = SimpleNamespace(__file__=str(path))
        self.runtime = SimpleNamespace(**{key: value for key, value in modules.items() if key != 'lifecycle'})
        self.runtime.fit.write = write
        self.runtime.fit.OFFLINE = ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY', 'VLLM_NO_USAGE_STATS')
        self.runtime.fit.prefix = SimpleNamespace(unseal=Mock())
        fit_sources = {modules['fit'].__file__: api.pin(modules['fit'].__file__)['sha256']}
        read_sources = {**fit_sources, modules['readout'].__file__: api.pin(modules['readout'].__file__)['sha256']}
        self.runtime.fit.source_files = lambda: fit_sources.copy()
        self.runtime.readout.source_files = lambda: read_sources.copy()
        self.runtime.outer.lifecycle = modules['lifecycle']
        self.runtime.outer.TOTAL_SECONDS = 1800
        self.runtime.outer.controller = Mock(side_effect=self.controller)
        self.runtime.campaign.SCHEMA = 'NONNATIVE_CAMPAIGN'
        self.runtime.campaign.BUDGET = {'NONNATIVE': True}
        self.runtime.acquisition = SimpleNamespace(SCHEMA='NONNATIVE_ACQUISITION', inventory=inventory,
                                                   validate=Mock(side_effect=self.acquire))
        self.gate, self.calls, self.stage_result = True, [], {}
        self.campaign = self.base / 'campaign'
        inputs = self.campaign / f'inputs/seed{seed}'
        inputs.mkdir(parents=True)
        self.runs = self.campaign / f'runs/seed{seed}'
        self.runs.mkdir(parents=True)
        for name in ('model_binding', 'base_state_receipt', 'archive', 'replay_receipt', 'shutdown_binding'):
            write(inputs / f'{name}.json', {'kind': 'INJECTED_CPU_TEST'})
        write(inputs / 'material.json', {'spec': {'learner_seed': seed, 'sha256': 'NONNATIVE'}})
        allocation = dict(gpu_index=2, gpu_uuid='GPU-NONNATIVE-2', lease_end=10**12, lease_margin_seconds=21600,
                          outer_sha256=api.pin(modules['outer'].__file__)['sha256'])
        write(inputs / 'allocation.json', allocation)
        shared = {name: api.pin(inputs / f'{name}.json') for name in ('model_binding', 'base_state_receipt', 'archive', 'replay_receipt', 'material')}
        shared.update(model_path='/nonexistent/NONNATIVE_MODEL', environment={'kind': 'INJECTED_CPU_TEST'},
                      learner_seed=seed, gpu_uuid=allocation['gpu_uuid'])
        write(inputs / 'fit_inputs.json', {**shared, 'source_files': fit_sources, 'predecessor': None})
        write(inputs / 'c0_inputs.json', {**shared, 'source_files': read_sources, 'fit_receipt': None,
                                       'shutdown_binding': api.pin(inputs / 'shutdown_binding.json')})
        self.entry = dict(seed=seed, gpu=2, spec_sha256='NONNATIVE',
                          **{name: api.pin(inputs / f'{name}.json') for name in ('allocation', 'fit_inputs', 'c0_inputs', 'material')})
        fit_root = self.runs / 'fit_outer/fit'
        fit_root.mkdir(parents=True)
        write(fit_root / 'completed.json', {'kind': 'INJECTED_CPU_TEST'})
        self.parent = api.pin(fit_root / 'completed.json')
        write(inputs / 'a200_inputs.json', {**api.checked(self.entry['c0_inputs']), 'fit_receipt': self.parent})
        for name in ('fit', 'no_write', 'a200'):
            outer = self.runs / f'{name}_outer'
            outer.mkdir(exist_ok=True)
            input_pin = self.entry['fit_inputs'] if name == 'fit' else self.entry['c0_inputs']
            if name == 'a200':
                input_pin = api.pin(inputs / 'a200_inputs.json')
            selection = {'phase': 'A200'} if name == 'fit' else {'stage': 'readout', 'state': 'NO_WRITE' if name == 'no_write' else 'A200'}
            write(outer / 'collection.json', dict(status='COMPLETED', gpu_released=True, errors=[], returncode=0,
                  retries=0, inputs=input_pin, elapsed_seconds=100, sha256='NONNATIVE', files=inventory(outer),
                  allocation_file_sha256=self.entry['allocation']['sha256'], outer_source_sha256=allocation['outer_sha256'], **selection))
        sources = {module.__file__: api.pin(module.__file__)['sha256'] for module in modules.values()}
        write(self.campaign / 'manifest.json', dict(schema='NONNATIVE_CAMPAIGN', budget={'NONNATIVE': True},
                                                   entries=[self.entry], source_files=sources))
        self.args = argparse.Namespace(root=str(self.base / 'followup'), source_root=str(source), seed=seed, gpu=2,
                                       campaign=str(self.campaign / 'manifest.json'),
                                       campaign_sha256=api.pin(self.campaign / 'manifest.json')['sha256'])

    def acquire(self, request_pin, material, inputs):
        request = api.checked(request_pin)
        self.assertEqual(set(request), {'schema', 'no_write_collection', 'a200_collection'})
        self.assertEqual(request['no_write_collection'], api.pin(self.runs / 'no_write_outer/collection.json'))
        self.assertEqual(request['a200_collection'], api.pin(self.runs / 'a200_outer/collection.json'))
        return dict(kind='INJECTED_CPU_TEST', observed_gate=self.gate, a200_fit_receipt=self.parent)

    def test_original_acquisition_operator_can_be_outside_frozen_runtime(self):
        path = Path(self.args.campaign)
        manifest = api.checked(api.pin(path))
        manifest['source_files'].pop(self.runtime.campaign.__file__)
        operator = self.base / 'standalone_acquisition_operator.py'
        operator.write_text('NONNATIVE_OPERATOR')
        manifest['source_files'][str(operator)] = api.pin(operator)['sha256']
        path.write_text(json.dumps(manifest))
        self.args.campaign_sha256 = api.pin(path)['sha256']
        result = api.prepare(self.args, self.runtime)
        plan = api.checked(result)
        self.assertEqual(plan['status'], 'READY')
        self.assertIn(api.pin(operator), plan['pins'])

    def controller(self, inputs_path, inputs_sha256, allocation_path, allocation_sha256, output, **selection):
        self.assertEqual(os.environ.get('CUDA_VISIBLE_DEVICES'), '')
        self.assertTrue(all(os.environ.get(name) == '1' for name in self.runtime.fit.OFFLINE))
        root = Path(output)
        self.assertTrue(root.is_absolute() and root.parent.is_dir() and root.parent.resolve() == root.parent)
        protected_paths = (Path(inputs_path).resolve().parent, Path(allocation_path).resolve(),
                           Path(self.runtime.fit.__file__).resolve().parents[1], Path(self.runtime.outer.__file__).resolve())
        for protected in (*protected_paths, Path(allocation_path).resolve().parent):
            api.require(not root.is_relative_to(protected) and not protected.is_relative_to(root), 'outer/input/source overlap')
        inputs = api.checked(dict(path=inputs_path, sha256=inputs_sha256))
        allocation = api.checked(dict(path=allocation_path, sha256=allocation_sha256))
        self.assertEqual(inputs['gpu_uuid'], allocation['gpu_uuid'])
        self.calls.append((selection, inputs))
        root.mkdir()
        if selection['stage'] == 'fit':
            (root / 'fit').mkdir()
            write(root / 'fit/completed.json', {'kind': 'INJECTED_CPU_TEST', 'phase': selection['phase']})
        else:
            self.assertEqual(api.checked(inputs['fit_receipt'])['phase'], selection['state'])
        result = {**dict(status='COMPLETED', gpu_released=True, errors=[], kind='INJECTED_CPU_TEST'), **self.stage_result}
        write(root / 'collection.json', result)
        return result

    def prepare(self):
        binding = api.prepare(self.args, self.runtime)
        self.args.manifest_sha256 = binding['sha256']
        return api.checked(binding)

    def test_fixed_phase_parent_order_and_separated_outer_precheck(self):
        before = inventory(self.campaign)
        plan = self.prepare()
        self.assertEqual(plan['counts'], api.COUNTS)
        self.assertEqual(plan['initial_outer_seconds'], 300)
        self.assertEqual(plan['remaining_seconds'], 6900)
        api.run(self.args, self.runtime)
        self.assertEqual([(call['phase'], call['stage'], call['state']) for call, inputs in self.calls],
                         [(phase, stage, phase if stage == 'readout' else None) for phase in api.PHASES for stage in ('fit', 'readout')])
        self.assertEqual([inputs['predecessor'] for call, inputs in self.calls if call['stage'] == 'fit'],
                         [self.parent, self.parent, self.parent, None])
        self.assertEqual(inventory(self.campaign), before)

    def test_false_gate_explicit_zero_fit_withholding(self):
        self.gate = False
        plan = self.prepare()
        self.assertEqual((plan['status'], plan['phases'], plan['counts']['fits'], plan['fit_inputs']), ('WITHHELD', [], 0, []))
        with self.assertRaisesRegex(ValueError, 'WITHHELD'):
            api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()

    def test_source_seed_and_gpu_identity_mismatches(self):
        for field, value, error in (('seed', 2, 'seed'), ('gpu', 3, 'GPU'), ('campaign_sha256', '0'*64, 'drift')):
            args = copy.copy(self.args)
            setattr(args, field, value)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, error):
                api.prepare(args, self.runtime)
        path = Path(self.runtime.fit.__file__)
        path.write_text('changed NONNATIVE source')
        with self.assertRaisesRegex(ValueError, 'drift'):
            self.prepare()

    def test_actual_input_seed_gpu_and_source_mismatch(self):
        original = api.checked(self.entry['fit_inputs'])
        for field, value in (('learner_seed', 2), ('gpu_uuid', 'GPU-WRONG'), ('source_files', {})):
            path = Path(self.entry['fit_inputs']['path'])
            path.write_text(json.dumps({**original, field: value}))
            manifest = api.checked(dict(path=self.args.campaign, sha256=self.args.campaign_sha256))
            manifest['entries'][0]['fit_inputs'] = api.pin(path)
            Path(self.args.campaign).write_text(json.dumps(manifest))
            self.args.campaign_sha256 = api.pin(self.args.campaign)['sha256']
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'identity mismatch'):
                self.prepare()

    def test_existing_root_stage_and_restart_refused(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'fresh output'):
            self.prepare()
        output = Path(self.args.root) / 'runs/B200_NEW_DOSE_fit_outer'
        output.mkdir()
        with self.assertRaisesRegex(ValueError, 'already-existing'):
            api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()
        output.rmdir()
        api.run(self.args, self.runtime)
        with self.assertRaisesRegex(ValueError, 'no resume'):
            api.run(self.args, self.runtime)
        self.assertEqual(len(self.calls), 8)

    def test_failed_stage_aborts_without_retry(self):
        self.prepare()
        self.stage_result = {'status': 'FAILED'}
        with self.assertRaisesRegex(ValueError, 'failed/unreleased'):
            api.run(self.args, self.runtime)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue((Path(self.args.root) / 'stopped.json').exists())
        self.assertFalse((Path(self.args.root) / 'completed.json').exists())

    def test_unreleased_aborts(self):
        self.stage_result = {'gpu_released': False}
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'failed/unreleased'):
            api.run(self.args, self.runtime)
        self.assertEqual(len(self.calls), 1)

    def test_readout_error_aborts_before_next_fit(self):
        self.prepare()
        original = self.controller

        def fail_readout(*args, **kwargs):
            if kwargs['stage'] == 'readout':
                self.stage_result = {'errors': ['NONNATIVE readout infrastructure failure']}
            return original(*args, **kwargs)

        self.runtime.outer.controller.side_effect = fail_readout
        with self.assertRaisesRegex(ValueError, 'failed/unreleased'):
            api.run(self.args, self.runtime)
        self.assertEqual(len(self.calls), 2)

    def test_exact_native_overlap_precheck_rejects_old_sibling_layout(self):
        binding = self.entry['fit_inputs']
        allocation = self.entry['allocation']
        with self.assertRaisesRegex(ValueError, 'outer/input/source overlap'):
            self.controller(binding['path'], binding['sha256'], allocation['path'], allocation['sha256'],
                            str(Path(binding['path']).parent / 'fit_outer'), phase='B200_NEW_DOSE', stage='fit', state=None)
        self.assertEqual(self.calls, [])

    def test_controller_exception_aborts(self):
        self.prepare()
        self.runtime.outer.controller.side_effect = RuntimeError('NONNATIVE infrastructure error')
        with self.assertRaises(RuntimeError):
            api.run(self.args, self.runtime)
        self.assertEqual(self.runtime.outer.controller.call_count, 1)
        self.assertTrue((Path(self.args.root) / 'stopped.json').exists())

    def test_budget_and_lease_rejections_before_any_controller(self):
        self.prepare()
        with patch.object(api.time, 'monotonic', side_effect=[0, 5101, 5101]):
            with self.assertRaisesRegex(ValueError, 'budget'):
                api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()
        allocation = api.checked(self.entry['allocation'])
        with patch.object(api.time, 'time', return_value=allocation['lease_end'] - 21600 - 1799):
            with self.assertRaisesRegex(ValueError, 'lease'):
                api.budget(300, api.time.monotonic(), allocation)

    def test_expired_lease_run_rejects_without_controller(self):
        self.prepare()
        allocation = api.checked(self.entry['allocation'])
        with patch.object(api.time, 'time', return_value=allocation['lease_end'] - 21600 - 1799):
            with self.assertRaisesRegex(ValueError, 'lease'):
                api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()

    def test_manifest_and_generated_input_drift_refused(self):
        plan = self.prepare()
        path = Path(plan['fit_inputs'][0]['path'])
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'provenance drift'):
            api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()

    def test_manifest_run_root_and_failed_b200_scores_do_not_select_phases(self):
        manifest = json.loads(Path(self.args.campaign).read_text())
        manifest['entries'][0]['run_root'] = str(self.runs)
        Path(self.args.campaign).write_text(json.dumps(manifest))
        self.args.campaign_sha256 = api.pin(self.args.campaign)['sha256']
        self.prepare()
        self.stage_result = {'scientific_scores': {'A': 0, 'B': 0}}
        api.run(self.args, self.runtime)
        self.assertEqual(len(self.calls), 8)

    def test_initial_failure_and_insufficient_remaining_budget(self):
        path = self.runs / 'a200_outer/collection.json'
        value = json.loads(path.read_text())
        path.write_text(json.dumps({**value, 'gpu_released': False}))
        with self.assertRaisesRegex(ValueError, 'failed/unreleased initial'):
            self.prepare()
        with self.assertRaisesRegex(ValueError, 'budget'):
            api.budget(5401, api.time.monotonic(), api.checked(self.entry['allocation']))

    def test_native_loader_refuses_alternate_source_without_importing(self):
        with self.assertRaisesRegex(ValueError, 'immutable source'):
            api.load_runtime(self.args.source_root)

    def test_validation_only_ast_boundary(self):
        original, replacement = self.base / 'old.py', self.base / 'new.py'
        original.write_text('def validate_warm_tensors(warm, trainable):\n    return False\n')
        replacement.write_text('def validate_warm_tensors(warm, trainable):\n    return True\n')
        with self.assertRaisesRegex(ValueError, 'exact scoped functions'):
            api.validate_repair(original, replacement)

    def repaired_runtime(self):
        source = Path(self.args.source_root)
        replacement = self.base / 'REPAIRED_NONNATIVE_SOURCE/gpu/fit.py'
        replacement.parent.mkdir(parents=True)
        replacement.write_text('NONNATIVE REPAIRED PLACEHOLDER\n')
        original = api.pin(self.runtime.fit.__file__)
        outer_original = api.pin(self.runtime.outer.__file__)
        outer = replacement.with_name('outer.py')
        outer.write_text('NONNATIVE REPAIRED OUTER PLACEHOLDER\n')
        repair = dict(original=original, replacement=api.pin(replacement), scope=api.REPAIR_SCOPE,
                      outer_original=outer_original, outer_replacement=api.pin(outer))
        receipt = replacement.parent.parent / 'warm_repair.json'
        write(receipt, repair)
        self.runtime.repair = {**repair, 'receipt': api.pin(receipt)}
        self.runtime.fit.__file__ = str(replacement)
        self.runtime.outer.__file__ = str(outer)
        self.runtime.fit.source_files = lambda: {str(replacement): api.pin(replacement)['sha256']}
        readout = self.runtime.readout.__file__
        self.runtime.readout.source_files = lambda: {**self.runtime.fit.source_files(), readout: api.pin(readout)['sha256']}
        self.args.source_root = str(replacement.parent.parent)
        return source, replacement

    def test_repaired_runtime_preserves_original_material_and_parent(self):
        original_source, replacement = self.repaired_runtime()
        before = inventory(self.campaign)
        with patch.object(api, 'SOURCE', original_source):
            plan = self.prepare()
            api.run(self.args, self.runtime)
        self.assertEqual(inventory(self.campaign), before)
        self.assertEqual(len(self.calls), 8)
        for selection, inputs in self.calls:
            self.assertEqual(inputs['material'], self.entry['material'])
            self.assertIn(str(replacement), inputs['source_files'])
        self.assertEqual(plan['originals'][0], api.pin(self.runs / 'fit_outer/collection.json'))
        original_allocation = api.checked(self.entry['allocation'])
        self.assertEqual(api.checked(plan['runtime_allocation']),
                         {**original_allocation, 'outer_sha256': self.runtime.repair['outer_replacement']['sha256']})
        for call in self.runtime.outer.controller.call_args_list:
            self.assertEqual(call.args[2:4], (plan['runtime_allocation']['path'], plan['runtime_allocation']['sha256']))

    def test_repair_pin_drift_refuses_run(self):
        original_source, replacement = self.repaired_runtime()
        with patch.object(api, 'SOURCE', original_source):
            self.prepare()
        replacement.write_text('NONNATIVE DRIFT\n')
        with self.assertRaisesRegex(ValueError, 'provenance drift'):
            api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()

    def test_repair_cannot_hide_unrelated_source_change(self):
        original_source, replacement = self.repaired_runtime()
        readout = Path(self.runtime.readout.__file__)
        readout.write_text('UNRELATED DRIFT\n')
        with patch.object(api, 'SOURCE', original_source):
            with self.assertRaisesRegex(ValueError, 'campaign source identity'):
                self.prepare()

    def test_repaired_source_map_requires_exact_replacement(self):
        self.repaired_runtime()
        with self.assertRaisesRegex(ValueError, 'exact single repaired'):
            api.original_sources({}, self.runtime)

    def test_repaired_source_map_translates_both_replacements(self):
        self.repaired_runtime()
        repair = self.runtime.repair
        sources = {binding['path']: binding['sha256'] for binding in (repair['replacement'], repair['outer_replacement'])}
        expected = {binding['path']: binding['sha256'] for binding in (repair['original'], repair['outer_original'])}
        self.assertEqual(api.original_sources(sources, self.runtime), expected)
        for changed, error in (({**sources, repair['outer_replacement']['path']: '0' * 64}, 'outer source drift'),
                               ({**sources, repair['outer_original']['path']: repair['outer_original']['sha256']}, 'ambiguous outer')):
            with self.assertRaisesRegex(ValueError, error):
                api.original_sources(changed, self.runtime)

    def prior_failure(self, worker=None):
        attempt = 3 if getattr(self.args, 'prior_failure', None) else 2
        self.args.root = str(self.base / f'pcfl_sequence_v2_followup_seed{self.args.seed}_20260913_attempt{attempt}')
        plan = self.prepare()
        previous = Path(self.args.root)
        outer = previous / 'runs/B200_NEW_DOSE_fit_outer'
        outer.mkdir()
        write(outer / 'collection.json', dict(status='FAILED', worker_identity=worker, returncode=None,
              stage_inventory={}, elapsed_seconds=6, sha256='NONNATIVE', retries=0, phase='B200_NEW_DOSE',
              inputs=plan['fit_inputs'][0], files={}, allocation_file_sha256=self.entry['allocation']['sha256'],
              outer_source_sha256=api.checked(self.entry['allocation'])['outer_sha256']))
        write(previous / 'stopped.json', dict(status='STOPPED', phase='B200_NEW_DOSE', stage='fit',
              elapsed_seconds=8, results=[dict(collection=api.pin(outer / 'collection.json'),
              phase='B200_NEW_DOSE', stage='fit', inputs=plan['fit_inputs'][0])]))
        if getattr(self.runtime, 'repair', None) is not None:
            plan['source_root'] = '/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix2'
            (previous / 'manifest.json').write_text(json.dumps(plan))
        write(previous / 'started.json', dict(manifest=api.pin(previous / 'manifest.json')))
        self.args.prior_failure = str(previous / 'stopped.json')
        self.args.prior_failure_sha256 = api.pin(previous / 'stopped.json')['sha256']
        self.args.root = str(self.base / 'followup_retry')

    def test_logged_preworker_failure_cost_is_charged(self):
        self.prior_failure()
        plan = self.prepare()
        self.assertEqual(plan['initial_outer_seconds'], 308)
        self.assertEqual(plan['remaining_seconds'], 6892)
        self.assertIn(plan['prior_failure'], plan['pins'])

    def test_prior_worker_execution_cannot_be_silently_retried(self):
        self.prior_failure(worker={'pid': 123})
        with self.assertRaisesRegex(ValueError, 'may have executed a worker'):
            self.prepare()

    def test_dirty_controller_environment_is_reset_before_first_stage(self):
        self.prepare()
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'GPU-UNRELATED', 'HF_HUB_OFFLINE': '0'}):
            api.run(self.args, self.runtime)
        self.assertEqual(len(self.calls), 8)

    def diagnosed_warm_failure(self, message='full parent tensor coverage differs'):
        source, replacement = self.repaired_runtime()
        with patch.object(api, 'SOURCE', source):
            self.prior_failure()
            self.prior_failure(worker={'pid': 123})
        self.args.prior_failure_kind = 'warm-prefix-validation'
        prior_root = Path(self.args.prior_failure).parent
        previous = api.checked(api.pin(prior_root / 'manifest.json'))
        previous['source_root'] = '/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix2'
        (prior_root / 'manifest.json').write_text(json.dumps(previous))
        failed_root = prior_root / 'runs/B200_NEW_DOSE_fit_outer'
        stage = failed_root / 'fit'
        (stage / 'checkpoint').mkdir(parents=True)
        write(stage / 'failure.json', dict(kind='NATIVE', message=message, partial_checkpoint_not_eligible=True,
              phase='B200_NEW_DOSE', status='FAILED', type='ActorError'))
        write(stage / 'checkpoint/train_manifest.json', dict(steps=200, config={'seed': self.args.seed},
              warm_start={'parent_path': str(self.runs / 'fit_outer/fit/checkpoint')}))
        collection = api.checked(api.pin(failed_root / 'collection.json'))
        collection.update(returncode=1, gpu_released=True,
                          files={name: value for name, value in inventory(failed_root).items() if name != 'collection.json'})
        (failed_root / 'collection.json').write_text(json.dumps(collection))
        stopped = api.checked(api.pin(self.args.prior_failure))
        stopped['results'][0]['collection'] = api.pin(failed_root / 'collection.json')
        Path(self.args.prior_failure).write_text(json.dumps(stopped))
        self.args.prior_failure_sha256 = api.pin(self.args.prior_failure)['sha256']
        return source

    def test_explicit_diagnosed_warm_failure_charges_physical_updates(self):
        source = self.diagnosed_warm_failure()
        with patch.object(api, 'SOURCE', source):
            plan = self.prepare()
        self.assertEqual(plan['prior_failed_work'], dict(fits=1, updates=200, presentations=800, readout_calls=0))
        self.assertEqual(plan['initial_outer_seconds'], 316)
        self.assertEqual(plan['counts'], api.COUNTS)

    def test_other_worker_failure_remains_ineligible(self):
        source = self.diagnosed_warm_failure(message='unrelated failure')
        with patch.object(api, 'SOURCE', source):
            with self.assertRaisesRegex(ValueError, 'only diagnosed'):
                self.prepare()

    def collector_failure(self):
        source = self.diagnosed_warm_failure()
        self.args.root = str(self.base / f'pcfl_sequence_v2_followup_seed{self.args.seed}_20260913_attempt4')
        with patch.object(api, 'SOURCE', source):
            plan = self.prepare()
        previous = Path(self.args.root)
        plan['source_root'] = '/tmp/astra_pcfl_sequence_v2_source_20260913_warmfix3'
        (previous / 'manifest.json').write_text(json.dumps(plan))
        write(previous / 'started.json', dict(manifest=api.pin(previous / 'manifest.json')))
        outer = previous / 'runs/B200_NEW_DOSE_fit_outer'
        stage = outer / 'fit'
        (stage / 'checkpoint').mkdir(parents=True)
        write(stage / 'checkpoint/train_manifest.json', dict(steps=200, config={'seed': self.args.seed},
              warm_start={'parent_path': str(self.runs / 'fit_outer/fit/checkpoint')}))
        write(stage / 'completed.json', dict(sha256='NONNATIVE', kind='NATIVE', status='COMPLETE', phase='B200_NEW_DOSE',
              updates=200, learner_seed=self.args.seed, predecessor=self.parent, inputs=plan['fit_inputs'][0]))
        (outer / 'fit_completed.json').write_bytes((stage / 'completed.json').read_bytes())
        errors = [dict(error='warm start: output must be fresh', phase='stage_evidence', type='ValueError')]
        write(outer / 'failure.json', dict(errors=errors))
        worker = {'pid': 123}
        write(outer / 'worker_exit.json', dict(returncode=0, identity=worker))
        write(outer / 'worker_release.json', dict(value=dict(identity=worker, owned_group_released=True)))
        write(outer / 'collection.json', dict(status='FAILED', worker_identity=worker, returncode=0, gpu_released=True,
              stage_inventory=inventory(stage), elapsed_seconds=185, sha256='NONNATIVE', retries=0,
              phase='B200_NEW_DOSE', inputs=plan['fit_inputs'][0], files=inventory(outer), errors=errors,
              completed_sha256=None, full_contract_released=False, automatic_promotion=False,
              allocation_file_sha256=self.entry['allocation']['sha256'],
              outer_source_sha256=api.checked(self.entry['allocation'])['outer_sha256']))
        write(previous / 'stopped.json', dict(status='STOPPED', phase='B200_NEW_DOSE', stage='fit', elapsed_seconds=187,
              results=[dict(collection=api.pin(outer / 'collection.json'), inputs=plan['fit_inputs'][0],
                            phase='B200_NEW_DOSE', stage='fit')]))
        self.args.prior_failure = str(previous / 'stopped.json')
        self.args.prior_failure_sha256 = api.pin(self.args.prior_failure)['sha256']
        self.args.prior_failure_kind = 'collector-predecessor-validation'
        self.args.root = str(self.base / f'pcfl_sequence_v2_followup_seed{self.args.seed}_20260913_attempt5')
        return source, previous

    def test_seed0_attempt5_charges_full_chain_without_reusing_attempt4(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        before = inventory(previous)
        with patch.object(api, 'SOURCE', source):
            plan = self.prepare()
            api.run(self.args, self.runtime)
        self.assertEqual(plan['prior_failed_work'], dict(fits=2, updates=400, presentations=1600, readout_calls=0))
        self.assertEqual(plan['initial_outer_seconds'], 503)
        self.assertEqual(plan['counts'], api.COUNTS)
        self.assertEqual(len(self.calls), 8)
        self.assertEqual(inventory(previous), before)
        for selection, inputs in self.calls:
            if selection['stage'] == 'fit':
                self.assertEqual(inputs['predecessor'], None if selection['phase'] == 'CLEAN_CUM600' else self.parent)
            else:
                self.assertTrue(Path(inputs['fit_receipt']['path']).is_relative_to(Path(self.args.root)))
        for attempt in (2, 3, 4):
            failed = self.base / f'pcfl_sequence_v2_followup_seed0_20260913_attempt{attempt}'
            self.assertIn(api.pin(failed / 'stopped.json'), plan['pins'])
            self.assertIn(api.pin(failed / 'manifest.json'), plan['pins'])

    def test_seed1_seed2_charge_one_failed_fit(self):
        for seed in (1, 2):
            self.setUp(seed=seed)
            source = self.diagnosed_warm_failure()
            with self.subTest(seed=seed), patch.object(api, 'SOURCE', source):
                plan = self.prepare()
            self.assertEqual(plan['prior_failed_work'], dict(fits=1, updates=200, presentations=800, readout_calls=0))
            self.assertEqual(plan['initial_outer_seconds'], 316)

    def test_collector_failure_rejected_for_other_seed(self):
        source, previous = self.collector_failure()
        with patch.object(api, 'SOURCE', source), self.assertRaisesRegex(ValueError, 'seed0 attempt4 only'):
            self.prepare()
        self.assertFalse(Path(self.args.root).exists())

    def test_collector_ancestry_cannot_drop_attempt3_or_its_cost(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        path = previous / 'manifest.json'
        original = json.loads(path.read_text())
        for field, value, error in (('prior_failure', None, 'ancestry required'),
                                    ('initial_outer_seconds', 300, 'elapsed ancestry'),
                                    ('prior_failed_work', dict(fits=0, updates=0, presentations=0, readout_calls=0), 'accounting')):
            path.write_text(json.dumps({**original, field: value}))
            (previous / 'started.json').write_text(json.dumps(dict(manifest=api.pin(path))))
            with self.subTest(field=field), patch.object(api, 'SOURCE', source), self.assertRaisesRegex(ValueError, error):
                self.prepare()
            self.assertFalse(Path(self.args.root).exists())

    def test_collector_other_error_or_worker_return_refused(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        path = previous / 'runs/B200_NEW_DOSE_fit_outer/collection.json'
        original = json.loads(path.read_text())
        stopped_path = previous / 'stopped.json'
        stopped = json.loads(stopped_path.read_text())
        for field, value in (('returncode', 1), ('errors', []), ('gpu_released', False)):
            path.write_text(json.dumps({**original, field: value}))
            stopped['results'][0]['collection'] = api.pin(path)
            stopped_path.write_text(json.dumps(stopped))
            self.args.prior_failure_sha256 = api.pin(stopped_path)['sha256']
            with self.subTest(field=field), patch.object(api, 'SOURCE', source), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse(Path(self.args.root).exists())

    def test_failed_checkpoint_drift_refused_before_prepare(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        checkpoint = previous / 'runs/B200_NEW_DOSE_fit_outer/fit/checkpoint/train_manifest.json'
        checkpoint.write_text(checkpoint.read_text() + '\n')
        with patch.object(api, 'SOURCE', source), self.assertRaisesRegex(ValueError, 'inventory drift'):
            self.prepare()

    def test_attempt5_cannot_be_nested_in_failed_attempt4(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        self.args.root = str(previous / 'attempt5')
        before = inventory(previous)
        with patch.object(api, 'SOURCE', source), self.assertRaisesRegex(ValueError, 'overlaps immutable failed'):
            self.prepare()
        self.assertEqual(inventory(previous), before)

    def test_prior_manifest_must_match_started_pin(self):
        source = self.diagnosed_warm_failure()
        previous = Path(self.args.prior_failure).parent
        path = previous / 'manifest.json'
        path.write_text(path.read_text() + '\n')
        with patch.object(api, 'SOURCE', source), self.assertRaisesRegex(ValueError, 'started manifest drift'):
            self.prepare()

    def test_readout_under_failed_attempt_is_not_eligible(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        (previous / 'runs/B200_NEW_DOSE_readout_outer').mkdir()
        with patch.object(api, 'SOURCE', source), self.assertRaisesRegex(ValueError, 'no later stages or readouts'):
            self.prepare()

    def test_ancestor_work_pin_drift_aborts_before_any_controller(self):
        self.setUp(seed=0)
        source, previous = self.collector_failure()
        with patch.object(api, 'SOURCE', source):
            self.prepare()
        ancestor = self.base / 'pcfl_sequence_v2_followup_seed0_20260913_attempt3/runs/B200_NEW_DOSE_fit_outer/fit/checkpoint/train_manifest.json'
        ancestor.write_text(ancestor.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'provenance drift'):
            api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()

    def test_runtime_allocation_cannot_change_gpu(self):
        plan = self.prepare()
        path = Path(plan['runtime_allocation']['path'])
        value = json.loads(path.read_text())
        path.write_text(json.dumps({**value, 'gpu_index': 7}))
        plan['runtime_allocation'] = api.pin(path)
        manifest = Path(self.args.root) / 'manifest.json'
        manifest.write_text(json.dumps(plan))
        self.args.manifest_sha256 = api.pin(manifest)['sha256']
        with self.assertRaisesRegex(ValueError, 'only outer source pin'):
            api.run(self.args, self.runtime)
        self.runtime.outer.controller.assert_not_called()


if __name__ == '__main__':
    unittest.main()
