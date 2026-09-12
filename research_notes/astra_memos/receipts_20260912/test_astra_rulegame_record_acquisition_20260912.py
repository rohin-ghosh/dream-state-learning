"""CPU synthetic records/scorers only; no native model/tokenizer, GPU or network."""
from contextlib import nullcontext
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.path.insert(0, '/tmp')
import test_astra_rulegame_record_write_20260912 as writes

spec = importlib.util.spec_from_file_location('tested_record_acquisition', '/tmp/astra_rulegame_record_acquisition_20260912.py')
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
diagnostic = writes.diagnostic


class Tokenizer(writes.Tokenizer):
    is_fast = True

    def __call__(self, text, **kwargs):
        return dict(input_ids=self.encode(text), offset_mapping=[[index, index+1] for index in range(len(text))])


class Scorer:
    def __init__(self, spec):
        self.spec = spec
        self.receipt = dict(mock=True, training=False, adapter_count=0 if spec.get('adapter') is None else 1)

    def score(self, request):
        candidates = request['candidates']
        offset = next(index for index, (left, right) in enumerate(zip(candidates[0]['response_ids'], candidates[1]['response_ids'])) if left != right)
        values = [[-.2]*len(candidate['response_ids']) for candidate in candidates]
        values[0][offset] = {'OFF': -2., 'P': -.5, 'A': -1.}[self.spec['cell']]
        values[1][offset] = -3.
        return dict(token_logprobs=values, native_forwards=bridge.forward_inputs(request))

    def close(self):
        return True


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = writes.BridgeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        path = self.fixture.output / 'plan.json'
        plan = diagnostic.read(path)
        plan['python'] = os.path.abspath(sys.executable)
        self.fixture.replace_json(path, plan)
        self.fixture.prepared['plan_sha256'] = bridge.digest(path)
        self.fixture.run_pair()
        self.patch_driver = patch.object(bridge.runtime, 'load_driver', return_value=writes.bridge)
        self.patch_driver.start()
        self.addCleanup(self.patch_driver.stop)
        self.patch_pin = patch.object(bridge, 'WRITE_PLAN_SHA', self.fixture.prepared['plan_sha256'])
        self.patch_pin.start()
        self.addCleanup(self.patch_pin.stop)
        self.tokenizer = Tokenizer()
        self.output = self.fixture.root / 'acquisition'
        self.loads, self.launches = [], []
        self.fail_cell, self.corrupt = None, None

    def prepare(self, **changes):
        args = dict(write_root=self.fixture.output, write_plan_sha256=self.fixture.prepared['plan_sha256'],
            write_driver=str(writes.bridge.SELF), out=self.output, deadline=writes.iso(time.time()+3600), lease_end=writes.iso(time.time()+8*3600))
        args.update(changes)
        with patch.object(diagnostic, 'native_tokenizer', return_value=self.tokenizer), \
             patch.object(bridge, 'NativeScorer', side_effect=AssertionError('no scoring during prepare')):
            self.prepared = bridge.prepare(**args)
        return self.prepared

    def scorer(self, spec):
        self.loads.append(spec)
        if spec['cell'] == self.fail_cell:
            raise RuntimeError('mock scoring failure '+self.fail_cell)
        return Scorer(spec)

    def supervise(self, root, plan, stage, command, call_path):
        stage.mkdir()
        self.launches.append((stage, command))
        self.assertEqual(command[0], os.path.abspath(sys.executable))
        self.assertEqual(call_path, stage / 'data/calls')
        controller = bridge.read(root / 'run/controller.json')
        self.assertEqual(controller['hard_end'], plan['lease_end'])
        self.assertLessEqual(controller['hard_end']-controller['started_wall'], 1800)
        self.assertEqual(controller['cleanup_reserve'], 140)
        spec_path = Path(command[command.index('--spec')+1])
        pin = command[command.index('--spec-sha256')+1]
        success = False
        try:
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'), patch.object(bridge.runtime, 'owning_process', return_value=nullcontext()):
                bridge.worker(spec_path, pin, allow_gpu=True)
            if self.corrupt:
                self.corrupt(stage)
            success = True
        finally:
            receipt = dict(ok=success, reservation_release_verified=True, reserved_seconds=.01)
            bridge.write_json(stage / 'supervision.json', receipt)
        return receipt

    def run_all(self):
        with patch.object(diagnostic, 'native_tokenizer', return_value=self.tokenizer), \
             patch.object(bridge, 'NativeScorer', side_effect=self.scorer), \
             patch.object(diagnostic, 'supervise', side_effect=self.supervise), \
             patch.object(writes.trainer, 'run_training', side_effect=AssertionError('no fits')), \
             patch.object(diagnostic, 'run_evaluation', side_effect=AssertionError('no gym/readout')):
            return bridge.run(self.output, self.prepared['plan_sha256'], allow_gpu=True)

    def test_prepare_exact_four_records_ablation_and_foil_bytes(self):
        before = diagnostic.tree_hashes(self.fixture.output)
        self.prepare()
        plan = bridge.read(self.output / 'plan.json')
        self.assertEqual(plan['protocol']['requests'], 24)
        self.assertEqual([row['record_id'] for row in plan['records']], ['P0', 'P1', 'A0', 'A1'])
        for record in plan['records']:
            self.assertTrue(record['raw'].startswith('\n ') and record['raw'].endswith('\t\n'))
            self.assertEqual(record['context'].replace('\n'+diagnostic.RELATION_DEFINITION, '', 1), record['removed_context'])
            self.assertIn('Actual world response:', record['removed_context'])
            self.assertIn('"try", "observed", "predicted", and "relation"', record['removed_context'])
            start, stop = record['foil']['truth_span']
            foil_stop = record['foil']['foil_span'][1]
            self.assertEqual(record['raw'][:start].encode(), record['foil']['text'][:start].encode())
            self.assertEqual(record['raw'][stop:].encode(), record['foil']['text'][foil_stop:].encode())
        for request in plan['requests']:
            prefix = request['payload']['prompt_input_ids']
            self.assertEqual(prefix, self.tokenizer.encode(request['rendered_prompt']))
            for candidate in request['candidates']:
                self.assertEqual(candidate['labels'], [-100]*len(prefix)+candidate['response_ids'])
                self.assertEqual(candidate['predictor_positions'], [index-1 for index in candidate['label_positions']])
                self.assertEqual(candidate['response_ids'].count(self.tokenizer.eos_token_id), 1)
                self.assertNotIn(candidate['text'], request['rendered_prompt'])
        self.assertEqual(before, diagnostic.tree_hashes(self.fixture.output))
        self.assertFalse(self.loads)

    def test_full_mock_three_processes_24_requests_48_forwards(self):
        self.prepare()
        before = diagnostic.tree_hashes(self.fixture.output)
        result = self.run_all()
        self.assertEqual([spec['cell'] for spec in self.loads], ['OFF', 'P', 'A'])
        self.assertIsNone(self.loads[0]['adapter'])
        self.assertEqual(self.loads[1]['adapter'], str(self.fixture.output / 'fits/P/adapter'))
        self.assertEqual(self.loads[2]['adapter'], str(self.fixture.output / 'fits/A/adapter'))
        self.assertEqual(sum(cell['costs']['requests'] for cell in result['cells'].values()), 24)
        self.assertEqual(sum(cell['costs']['candidate_forwards'] for cell in result['cells'].values()), 48)
        self.assertEqual(result['generations'], 0)
        self.assertEqual(len(result['summary']['all_record_comparisons']), 8)
        for condition in bridge.CONTEXTS:
            self.assertTrue(result['summary']['contexts'][condition]['stronger_P_specific_selective_carriage'])
            self.assertEqual(result['summary']['contexts'][condition]['own_record_acquisition_vs_OFF'], {'P': True, 'A': True})
        for cell in result['cells'].values():
            for row in cell['rows']:
                for name in ('truth', 'foil'):
                    score = row[name]
                    self.assertAlmostEqual(score['sum_logprob']/score['scored_tokens'], score['mean_logprob'])
        self.assertEqual(before, diagnostic.tree_hashes(self.fixture.output))

    def test_shared_equal_gain_not_called_no_acquisition(self):
        self.prepare()
        result = self.run_all()
        captures = copy.deepcopy(result['cells'])
        captures['A']['rows'] = copy.deepcopy(captures['P']['rows'])
        summary = bridge.summarize(captures)
        for row in summary['contexts'].values():
            self.assertEqual(row['own_record_acquisition_vs_OFF'], {'P': True, 'A': True})
            self.assertFalse(row['stronger_P_specific_selective_carriage'])
            self.assertIn('shared/nonselective acquisition', row['interpretation'])
        self.assertTrue(summary['stronger_P_criterion_not_required_for_parameter_acquisition'])

    def test_both_own_records_required_no_average_or_crossarm_filter(self):
        self.prepare()
        result = self.run_all()
        captures = copy.deepcopy(result['cells'])
        for index, row in enumerate(captures['P']['rows']):
            if row['record_id'] == 'P1':
                captures['P']['rows'][index] = copy.deepcopy(captures['OFF']['rows'][index])
        summary = bridge.summarize(captures)
        for row in summary['contexts'].values():
            self.assertFalse(row['own_record_acquisition_vs_OFF']['P'])
            self.assertFalse(row['stronger_P_specific_selective_carriage'])
        captures['A']['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'all cross-arm'):
            bridge.summarize(captures)

    def test_null_wrong_duplicate_escaped_relation_rejected(self):
        raw = ' { "try": [0,0,0], "observed":true, "predicted":true, "relation" : "matched" }\n'
        cases = [raw.replace('"predicted":true', '"predicted":null'), raw.replace('matched', 'mismatched'),
            raw.replace('"relation" : "matched"', '"relation":"matched", "relation":"matched"'),
            raw.replace('matched', r'ma\u0074ched')]
        for candidate in cases:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                bridge.foil(candidate)
        self.assertEqual(bridge.foil(raw)['text'], raw.replace('matched', 'mismatched'))

    def test_mapping_occurrence_must_be_exactly_one(self):
        needle = '\n'+diagnostic.RELATION_DEFINITION
        for text in ('no mapping', needle+needle):
            with self.assertRaisesRegex(ValueError, 'occur once'):
                bridge.remove_mapping(text, diagnostic)

    def test_mismatched_foil_flip_preserves_all_other_bytes(self):
        raw = '\t{"try": [1,2,3], "observed":false,"predicted": true, "relation" : "mismatched"}\n '
        result = bridge.foil(raw)
        self.assertEqual(result['text'], raw.replace('"mismatched"', '"matched"'))
        self.assertEqual(result['original_relation'], 'mismatched')

    def test_fourth_record_rejection_publishes_nothing(self):
        original = bridge.foil
        seen = []
        def reject_last(raw):
            seen.append(raw)
            if len(seen) == 4:
                raise ValueError('fourth record rejected; no replacement')
            return original(raw)
        with patch.object(bridge, 'foil', side_effect=reject_last), self.assertRaisesRegex(ValueError, 'fourth record'):
            self.prepare()
        self.assertEqual(len(seen), 4)
        self.assertFalse(self.output.exists())

    def test_full_and_removed_patterns_separate_not_scaffold_free(self):
        self.prepare()
        result = self.run_all()
        captures = copy.deepcopy(result['cells'])
        for cell in ('P', 'A'):
            for index, row in enumerate(captures[cell]['rows']):
                if row['context_condition'] == 'MAPPING_SENTENCE_REMOVED':
                    captures[cell]['rows'][index] = copy.deepcopy(captures['OFF']['rows'][index])
        summary = bridge.summarize(captures)
        self.assertEqual(summary['own_acquisition_context_pattern'], {'P': 'FULL_only', 'A': 'FULL_only'})
        self.assertIn('not unique semantic mechanism', summary['mapping_ablation_limit'])

    def test_offset_gap_join_eos_and_truncation_fail(self):
        context, raw = 'CTX:', '{"try":[0,0,0],"observed":true,"predicted":true,"relation":"matched"}'
        span = bridge.foil(raw)['truth_span']
        prefix = self.tokenizer.encode(context)
        with self.assertRaisesRegex(ValueError, 'overlength'):
            bridge.encode_candidate(self.tokenizer, 'X'*4096, self.tokenizer.encode('X'*4096), raw, span)
        class Gap(Tokenizer):
            def __call__(self, text, **kwargs):
                encoded = super().__call__(text, **kwargs)
                encoded['offset_mapping'][1][0] = 0
                return encoded
        with self.assertRaisesRegex(ValueError, 'offset coverage'):
            bridge.encode_candidate(Gap(), context, prefix, raw, span)
        class Join(Tokenizer):
            def __call__(self, text, **kwargs):
                encoded = super().__call__(text, **kwargs)
                encoded['input_ids'].pop(len(context))
                encoded['offset_mapping'][len(context)-1][1] += 1
                encoded['offset_mapping'].pop(len(context))
                return encoded
        with self.assertRaisesRegex(ValueError, 'boundary straddle'):
            bridge.encode_candidate(Join(), context, prefix, raw, span)
        eos_tokenizer = Tokenizer()
        eos_tokenizer.eos_token_id = ord('{')+1
        with self.assertRaisesRegex(ValueError, 'raw target/EOS'):
            bridge.encode_candidate(eos_tokenizer, context, prefix, raw, span)

    def test_changed_material_base_and_saved_adapter_fail_before_prepare(self):
        for target in (self.fixture.output / 'material/corpora/P.json', self.fixture.model / 'weights.fixture',
                       self.fixture.output / 'fits/P/adapter/DONE'):
            payload = target.read_bytes()
            target.write_bytes(payload+b'changed')
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.prepare()
            target.write_bytes(payload)
            self.assertFalse(self.output.exists())

    def test_wrong_plan_pin_lease_and_freshness(self):
        for changes in (dict(write_plan_sha256='0'*64), dict(deadline=writes.iso(time.time()+100)),
                        dict(lease_end=writes.iso(time.time()+3600)), dict(out=self.fixture.output)):
            with self.assertRaises(ValueError):
                self.prepare(**changes)
        self.prepare()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_protocol_tamper_even_rehashed_fails(self):
        self.prepare()
        path = self.output / 'plan.json'
        plan = bridge.read(path)
        plan['protocol']['contexts'][1] = 'SCAFFOLD_FREE'
        self.fixture.replace_json(path, plan)
        pin = bridge.digest(path)
        self.fixture.replace_json(self.output / 'plan.sha256.json', dict(sha256=pin))
        with self.assertRaisesRegex(ValueError, 'prospective protocol'):
            bridge.checked_plan(self.output, pin)

    def test_missing_inclusive_window_and_lease_are_not_relaxed(self):
        with self.assertRaisesRegex(ValueError, '1800s'):
            self.prepare(deadline=writes.iso(time.time()+1790))
        self.assertEqual(bridge.protocol()['cleanup_seconds'], 140)
        self.assertEqual(bridge.protocol()['worker_seconds'], 600)
        self.assertEqual(bridge.protocol()['lease_margin_seconds'], 21600)

    def test_gpu_opt_in_before_any_work(self):
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            bridge.run('missing', 'missing')
        with self.assertRaisesRegex(ValueError, 'allow-gpu'):
            bridge.worker('missing', 'missing')

    def test_scoring_failure_preserves_partial_no_retry(self):
        self.prepare()
        self.fail_cell = 'P'
        with self.assertRaisesRegex(RuntimeError, 'mock scoring failure'):
            self.run_all()
        failure = bridge.read(self.output / 'run/failure.json')
        self.assertEqual(failure['completed_cells'], ['OFF'])
        self.assertIsNone(failure['aggregate'])
        self.assertEqual(len(self.loads), 2)
        with self.assertRaises(FileExistsError):
            self.run_all()

    def test_worker_spec_hash_and_actual_native_offsets_fail_closed(self):
        self.prepare()
        plan = bridge.read(self.output / 'plan.json')
        (self.output / 'run').mkdir()
        spec = bridge.worker_spec(self.output, plan, 'OFF', time.time()+1800)
        spec['requests'][0]['candidates'][0]['predictor_positions'][0] += 1
        path = self.output / 'run/OFF.spec.json'
        bridge.write_json(path, spec)
        with self.assertRaisesRegex(ValueError, 'worker spec changed'):
            bridge.worker(path, '0'*64, allow_gpu=True)
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='2'), \
             patch.object(bridge.runtime, 'owning_process', return_value=nullcontext()), \
             patch.object(diagnostic, 'native_tokenizer', return_value=self.tokenizer), \
             self.assertRaisesRegex(ValueError, 'offset audit differs'):
            bridge.worker(path, bridge.digest(path), allow_gpu=True)
        self.assertFalse(self.loads)

    def test_cleanup_failure_blocks_later_cells(self):
        self.prepare()
        with patch.object(Scorer, 'close', return_value=False), self.assertRaisesRegex(ValueError, 'cleanup unverified'):
            self.run_all()
        self.assertEqual(len(self.loads), 1)

    def test_raw_score_trace_tamper_rejected(self):
        self.prepare()
        def corrupt(stage):
            path = stage / 'data/calls/0000.response.json'
            record = bridge.read(path)
            record['response']['token_logprobs'][0][0] -= 1
            self.fixture.replace_json(path, record)
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, 'capture seal changed'):
            self.run_all()
        self.assertEqual(len(self.loads), 1)

    def test_bad_scores_native_forward_or_prefix_rejected(self):
        self.prepare()
        request = bridge.read(self.output / 'plan.json')['requests'][0]
        response = Scorer(dict(cell='OFF')).score(request)
        for mutation in (lambda row: row['token_logprobs'][0].pop(),
                         lambda row: row['token_logprobs'][0].__setitem__(0, float('nan')),
                         lambda row: row['native_forwards'][0]['input_ids'][0].__setitem__(0, 12345),
                         lambda row: row['token_logprobs'][0].__setitem__(0, -1)):
            altered = copy.deepcopy(response)
            mutation(altered)
            with self.assertRaises(ValueError):
                bridge.validate_scores(request, altered)

    def test_conditional_assay_version_never_accepted(self):
        self.prepare()
        request = bridge.read(self.output / 'plan.json')['requests'][0]
        response = Scorer(dict(cell='OFF')).score(request)
        request['version'] = 'conditional-dual-map-fixed-endpoints-v2-20260912'
        with self.assertRaisesRegex(ValueError, 'protocol/candidates'):
            bridge.validate_scores(request, response)

    def test_real_carrier_score_uses_cpu_mock_native_model_two_forwards(self):
        _, conditional, carrier = bridge.modules(str(writes.SOURCE))
        raw = '{"try":[0,0,0],"observed":true,"predicted":true,"relation":"matched"}'
        contrast = bridge.foil(raw)
        tokenizer = Tokenizer()
        tokenizer.eos_token_id = 0
        context, prefix = 'CTX:', tokenizer.encode('CTX:')
        request = dict(version=bridge.VERSION, operation='score_raw_record_relation', payload=dict(prompt_input_ids=prefix),
            candidates=[dict(candidate_id=name, **bridge.encode_candidate(tokenizer, context, prefix, text, span)) for name, text, span in
                [('truth', raw, contrast['truth_span']), ('foil', contrast['text'], contrast['foil_span'])]])
        visited = []
        class Tensor:
            def __init__(self, value):
                self.value = value
            def detach(self):
                return self
            def cpu(self):
                return self
            def tolist(self):
                return self.value
            def unsqueeze(self, axis):
                return Tensor([self.value])
        class Grid:
            def __getitem__(self, index):
                if isinstance(index, tuple):
                    visited.append(index)
                    return SimpleNamespace(cpu=lambda: -.25)
                return self
            def float(self):
                return self
        class CpuTorch:
            long = object()
            def tensor(self, value, **kwargs):
                return Tensor(value)
            def arange(self, length, **kwargs):
                return Tensor(list(range(length)))
            def ones_like(self, tensor):
                return Tensor([[1]*len(row) for row in tensor.value])
            def inference_mode(self):
                return nullcontext()
            def log_softmax(self, value, **kwargs):
                return Grid()
            def isfinite(self, value):
                return SimpleNamespace(all=lambda: SimpleNamespace(item=lambda: True))
            def allclose(self, *args, **kwargs):
                return True
        class Model:
            def __init__(self, path):
                self.name_or_path = str(path)
                self.config = SimpleNamespace(use_cache=False)
                self.training = False
                self.hook = None
            def named_parameters(self):
                return [('mock_parameter', SimpleNamespace(requires_grad=False, numel=lambda: 1, dtype='mock'))]
            def register_forward_pre_hook(self, hook, **kwargs):
                self.hook = hook
                return SimpleNamespace(remove=lambda: setattr(self, 'hook', None))
            def __call__(self, **kwargs):
                self.hook(self, (), kwargs)
                return SimpleNamespace(logits=Grid())
        core = SimpleNamespace(torch=CpuTorch(), model=Model(self.fixture.model), close=lambda: True)
        with patch.object(conditional, 'HFScorer', return_value=core), \
             patch.object(conditional, 'scoring_groups', side_effect=AssertionError('no conditional assay routing')):
            scorer = bridge.NativeScorer(dict(source_root=str(writes.SOURCE), model=str(self.fixture.model), adapter=None))
            result = scorer.score(request)
            self.assertEqual(len(result['native_forwards']), 2)
            self.assertEqual(len(result['token_logprobs'][0]), len(request['candidates'][0]['response_ids']))
            self.assertEqual(result['native_forwards'], bridge.forward_inputs(request))
            self.assertEqual(visited, [(index-1, token) for candidate in request['candidates']
                for index, (token, label) in enumerate(zip(candidate['input_ids'], candidate['labels'])) if label != -100])
            self.assertTrue(scorer.close())


if __name__ == '__main__':
    unittest.main()
