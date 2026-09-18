"""Synthetic CPU fixtures only; no model generation, fit, GPU or network."""
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timedelta, timezone
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import citation_sleep_diagnostic as diagnostic


TARGET = '{"case_id":"t02","checks":[{"group":"box","cells":[[3,3],[3,4]],"digit":1}],"lesson":"Check box members for duplicates."}'
BOARD = [[2, 4, 4, 1], [4, 1, 2, 4], [2, 2, 1, 1], [1, 3, 4, 4]]


class Tokenizer:
    eos_token_id = 0
    pad_token_id = 0
    merged = ()

    def pieces(self, text):
        result = []
        cursor = 0
        while cursor < len(text):
            matched = next((value for value in self.merged if text.startswith(value, cursor)), None)
            piece = matched or text[cursor]
            token = 1000 + self.merged.index(piece) if matched else ord(piece) + 10
            result.append((token, (cursor, cursor+len(piece))))
            cursor += len(piece)
        return result

    def encode(self, text, add_special_tokens=False):
        return [token for token, _ in self.pieces(text)]

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        parts = self.pieces(text)
        return dict(input_ids=[token for token, _ in parts], offset_mapping=[offset for _, offset in parts])

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return '<user>\n' + messages[0]['content'] + '\n<assistant>\n'


class MergedTokenizer(Tokenizer):
    merged = ('"box', ':"t', ':1')


class Model:
    def __init__(self, path, adapter, tokenizer, panel):
        self.path, self.adapter_path, self.tok, self.panel = path, adapter, tokenizer, panel
        self.calls = []

    def generation_identity(self):
        return diagnostic.base.model_backend.configured_generation_identity(self.path, self.adapter_path)

    def batch(self, prompts, max_tokens, temperature, seeds):
        self.calls.append(dict(prompts=prompts, max_tokens=max_tokens, temperature=temperature, seeds=seeds))
        record = json.loads(TARGET)
        record['case_id'] = self.panel[len(self.calls)-1]['case_id']
        return [json.dumps(record, separators=(',', ':'))]


class CitationSleepTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.cleanup)
        self.model = self.root/'model'
        self.model.mkdir()
        (self.model/'config.json').write_text(json.dumps(dict(model_type='qwen2', num_hidden_layers=28, hidden_size=3584)))
        (self.model/'tokenizer.json').write_text('{}')
        (self.model/'tokenizer_config.json').write_text('{}')
        (self.model/'model.safetensors').write_bytes(b'SYNTHETIC NOT WEIGHTS')
        self.pins = diagnostic.base.formation.local_files(self.model)
        self.panel = []
        for index in range(8):
            board = copy.deepcopy(BOARD)
            if index != 1:
                board[0][0], board[0][1] = index//4+1, index%4+1
            self.panel.append(dict(case_id=f't{index+1:02}', episode_id=f'rg/mini_sudoku/{1851300+index}',
                                   candidate=board, candidate_sha256=diagnostic.sha(diagnostic.base.formation.policy._encoded(board)),
                                   split='train', origin='SYNTHETIC CPU FIXTURE'))
        self.provenance = dict(original_raw_text=TARGET, output_sha256=diagnostic.TARGET_SHA,
                               bad_source_note='SYNTHETIC BAD SOURCE NOTE; NEVER SLEEP',
                               original_request={'prompt':'SYNTHETIC PARENT EXAMPLE; NEVER SLEEP'}, panel=self.panel,
                               source_config=dict(task=diagnostic.base.TASK, expected_files=self.pins))
        self.source, self.source_prep = self.root/'source', self.root/'source_prep'
        self.source.mkdir()
        self.source_prep.mkdir()
        self.prep = self.root/'prep'
        self.tokenizer = Tokenizer()
        self.models = []

    def cleanup(self):
        for path in self.root.rglob('*'):
            if path.is_dir():
                path.chmod(0o755)
        self.temporary.cleanup()

    def prepare(self, tokenizer=None):
        with patch.object(diagnostic, 'source_snapshot', return_value=copy.deepcopy(self.provenance)):
            return diagnostic.prepare(self.prep, self.source, self.source_prep, self.model, self.pins,
                                      tokenizer=tokenizer or self.tokenizer)

    @contextmanager
    def backend(self, path, adapter):
        model = Model(path, adapter, self.tokenizer, self.panel)
        self.models.append(model)
        yield model

    def write_fit(self, destination, spec):
        destination.mkdir()
        proof = diagnostic.read(self.prep/'preflight.json')['proof'][destination.name.removeprefix('fit_')]
        manifest = dict(config=spec['config'], steps=32, micro_batches=32, nonfinite_batches=0, final_loss=.1,
                        base_model=str(self.model), corpus=dict(sha256=spec['corpus_sha256'], n_items=1, n_encoded=1, n_skipped_no_target=0),
                        truncation={key:0 for key in ('items_truncated','context_tokens_dropped','target_tokens_dropped','items_split')},
                        tokens=dict(total=proof['input_tokens'], target=proof['supervised_tokens']), train_tokens_seen=proof['train_tokens_seen'])
        (destination/'train_manifest.json').write_text(json.dumps(manifest))
        (destination/'adapter_config.json').write_text(json.dumps(dict(r=8, lora_alpha=16, lora_dropout=.05,
                                                                       target_modules=diagnostic.trainer.ALL_PROJ)))
        (destination/'adapter_model.safetensors').write_bytes(b'SYNTHETIC ADAPTER NOT WEIGHTS')
        (destination/'DONE').write_text('SYNTHETIC')

    def simulated_run(self, fail_at=None):
        self.prepare()
        run = self.root/'run'
        called = []
        real_load = diagnostic.load_preparation

        def load(path, *, native=False, tokenizer=None):
            return real_load(path, native=False, tokenizer=tokenizer)

        def worker(command, *, log_path, timeout, device):
            stage = log_path.stem
            called.append((stage, command, timeout))
            log_path.write_text('SYNTHETIC WORKER; NO SUBPROCESS')
            diagnostic.write(log_path.with_suffix('.cleanup.json'), dict(pid=100+len(called), device=device, cleanup_error=None,
                owned_group_empty=True, gpu_processes_absent=True, reservation_release_verified=True))
            if stage == fail_at:
                raise RuntimeError('synthetic stage failure')
            output = Path(command[command.index('--out')+1])
            if stage.startswith('fit_'):
                self.write_fit(output, diagnostic.read(run/f'{stage}.command.json'))
            else:
                adapter = command[command.index('--adapter')+1] if '--adapter' in command else None
                diagnostic.evaluate(self.prep, output, stage, adapter=adapter, backend_factory=self.backend, allow_synthetic=True)

        deadline = (datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
        environment = dict(V6_MODEL=str(self.model), CUDA_VISIBLE_DEVICES='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        with patch.object(diagnostic, 'load_preparation', side_effect=load), patch.object(diagnostic.base.supervisor,'run_worker',side_effect=worker), \
             patch.dict(diagnostic.os.environ, environment), patch.object(diagnostic.base.model_backend,'MODEL',str(self.model)):
            if fail_at:
                with self.assertRaisesRegex(RuntimeError, 'synthetic stage failure'):
                    diagnostic.execute(self.prep, run, '1', deadline)
                return run, called, None
            result = diagnostic.execute(self.prep, run, '1', deadline)
        return run, called, result

    def test_exact_prefix_no_lesson_or_closing_brace(self):
        prefix, ranges = diagnostic.prefix_and_ranges(TARGET)
        self.assertEqual(prefix, TARGET[:ranges['end_byte']])
        self.assertTrue(prefix.endswith('}]'))
        self.assertNotIn('lesson', prefix)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(prefix)

    def test_changed_raw_rejected(self):
        for target in (TARGET+' ', TARGET.replace('"digit":1','"digit":2'), TARGET.replace('duplicates','repeats')):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError,'exact selected raw'):
                diagnostic.prefix_and_ranges(target)

    def test_actual_board_mismatch_rejected(self):
        self.provenance['panel'][1]['candidate'][2][2] = 2
        with self.assertRaisesRegex(ValueError,'t02 board'):
            diagnostic.token_preflight(self.provenance, self.tokenizer)

    def test_fixed_panel_order(self):
        self.provenance['panel'].reverse()
        with self.assertRaisesRegex(ValueError,'fixed transfer panel'):
            diagnostic.token_preflight(self.provenance,self.tokenizer)

    def test_sleep_excludes_note_example_and_lesson_bytes(self):
        self.prepare()
        for arm in diagnostic.ARMS:
            data = (self.prep/f'{arm}.corpus.json').read_text()
            self.assertNotIn('Check box members for duplicates.', data)
            self.assertNotIn('SYNTHETIC BAD SOURCE NOTE', data)
            self.assertNotIn('SYNTHETIC PARENT EXAMPLE', data)
        self.assertEqual(diagnostic.read(self.prep/'provenance.json')['original_raw_text'], TARGET)

    def test_mask_and_exact_input_parity(self):
        corpora, check = diagnostic.token_preflight(self.provenance,self.tokenizer)
        self.assertEqual(check['proof']['full']['input_ids'], check['proof']['syntax']['input_ids'])
        self.assertGreater(check['proof']['full']['supervised_tokens'],check['proof']['syntax']['supervised_tokens'])
        self.assertGreater(check['proof']['syntax']['supervised_tokens'],0)
        for token in check['partition']:
            start, end = token['start_byte'], token['end_byte']
            case = any(start < right and end > left for left,right in check['ranges']['case'])
            content = any(start < right and end > left for left,right in check['ranges']['content'])
            self.assertEqual(token['full'],not case)
            self.assertEqual(token['syntax'],not case and not content)
        self.assertEqual([span[0] for span in corpora['full']['corpus'][0]['spans']],
                         [span[0] for span in corpora['syntax']['corpus'][0]['spans']])

    def test_cross_boundary_token_excluded_conservatively(self):
        _, check = diagnostic.token_preflight(self.provenance,MergedTokenizer())
        case = next(row for row in check['partition'] if row['text'] == ':"t')
        content = next(row for row in check['partition'] if row['text'] == '"box')
        self.assertFalse(case['full'])
        self.assertFalse(case['syntax'])
        self.assertTrue(content['full'])
        self.assertFalse(content['syntax'])

    def test_bad_offsets_rejected(self):
        class Overlap(Tokenizer):
            def __call__(self,*args,**kwargs):
                value = super().__call__(*args,**kwargs)
                value['offset_mapping'][1] = (0,2)
                return value
        with self.assertRaisesRegex(ValueError,'overlapping/gapped'):
            diagnostic.token_preflight(self.provenance,Overlap())

    def test_no_eos_or_continuation_and_no_truncation(self):
        _, check = diagnostic.token_preflight(self.provenance,self.tokenizer)
        self.assertFalse(check['eos_appended'])
        self.assertFalse(check['continuation_present'])
        for proof in check['proof'].values():
            self.assertNotIn(self.tokenizer.eos_token_id,proof['input_ids'])
            self.assertLess(proof['input_tokens'],4096)

    def test_input_budget_fails_without_truncating(self):
        class Huge(Tokenizer):
            def apply_chat_template(self,*args,**kwargs):
                return 'X'*4096 + super().apply_chat_template(*args,**kwargs)
        with self.assertRaisesRegex(ValueError,'truncation/headroom'):
            diagnostic.token_preflight(self.provenance,Huge())

    def test_immutable_exclusive_preparation(self):
        result = self.prepare()
        self.assertEqual(result['status'],'SYNTHETIC_CPU_ONLY')
        diagnostic.base.receipts.verify_inventory(self.prep)
        with self.assertRaisesRegex(ValueError,'fresh canonical'):
            self.prepare()
        with self.assertRaisesRegex(ValueError,'synthetic preparation'):
            diagnostic.load_preparation(self.prep,native=True)

    def test_runtime_tokenizer_change_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError,'runtime tokenizer changed'):
            diagnostic.load_preparation(self.prep,tokenizer=MergedTokenizer())

    def test_trainer_api_exact_and_fresh_base(self):
        self.prepare()
        config=diagnostic.read(self.prep/'config.json')
        for arm in diagnostic.ARMS:
            spec=diagnostic.training_spec(self.prep,self.root/f'fit_{arm}',arm,config)
            actual=spec['config']
            for key,value in dict(rank=8,alpha=16,dropout=.05,lr=1e-4,optimizer='adamw',batch_size=1,
                                  grad_accum=1,epochs=32,max_steps=32,seed=1729,pack=False,add_eos=False,chat_template=False).items():
                self.assertEqual(actual[key],value)
            self.assertNotIn('--adapter',spec['argv'])
            self.assertTrue(spec['fresh_base'])

    def test_fit_receipt_checks_steps_mask_and_token_dose(self):
        self.prepare()
        config=diagnostic.read(self.prep/'config.json')
        proof=diagnostic.read(self.prep/'preflight.json')['proof']['full']
        output=self.root/'fit_full'
        spec=diagnostic.training_spec(self.prep,output,'full',config)
        self.write_fit(output,spec)
        diagnostic.verify_fit(output,spec,proof)
        manifest=diagnostic.read(output/'train_manifest.json')
        manifest['steps']=31
        (output/'train_manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'wrong/incomplete'):
            diagnostic.verify_fit(output,spec,proof)

    def test_mock_eval_eight_calls_and_strict_scorer(self):
        self.prepare()
        result=diagnostic.evaluate(self.prep,self.root/'off','off',backend_factory=self.backend,allow_synthetic=True)
        self.assertEqual(result['generation_calls'],8)
        for call in self.models[0].calls:
            self.assertEqual((call['max_tokens'],call['temperature'],call['seeds']),(128,0.0,[7101]))
            self.assertNotIn('SOURCE NOTE',call['prompts'][0])
        for index,row in enumerate(result['records']):
            self.assertEqual(row['score'],diagnostic.base.score_record(row['capture']['text'],self.panel[index]))
            self.assertIsNone(row['capture']['actual_output_tokens'])

    def test_native_raw_stop_and_adapter_routing(self):
        output=self.root/'capture'
        output.mkdir()
        adapter=self.root/'adapter'
        adapter.mkdir()
        (adapter/'adapter_config.json').write_text('{}')
        (adapter/'adapter_model.safetensors').write_bytes(b'SYNTHETIC')
        model=Model(str(self.model),str(adapter),self.tokenizer,self.panel)
        model._LoRARequest=lambda *values:values
        row=diagnostic.request_for(self.panel[1],self.tokenizer)
        seen=[]
        def generate(prompts,params,**kwargs):
            seen.append((prompts,params,kwargs))
            response=SimpleNamespace(text=TARGET,token_ids=[2]*41,finish_reason='stop',stop_reason=None)
            return [SimpleNamespace(request_id='synthetic',prompt=prompts[0],prompt_token_ids=row['prompt_token_ids'],finished=True,outputs=[response])]
        model.llm=SimpleNamespace(generate=generate)
        with patch.dict('sys.modules',{'vllm':SimpleNamespace(SamplingParams=lambda **kwargs:kwargs)}):
            capture=diagnostic.Capture(model,str(self.model),output,str(adapter))
            result=capture.generate_record(row)
        self.assertEqual(result['actual_output_tokens'],41)
        self.assertEqual(seen[0][1],[dict(max_tokens=128,temperature=0.0,seed=7101)])
        self.assertEqual(seen[0][2]['lora_request'],('life',1,str(adapter)))

    def test_length_stop_preserves_raw_before_failure(self):
        output=self.root/'length'
        output.mkdir()
        row=diagnostic.request_for(self.panel[1],self.tokenizer)
        model=Model(str(self.model),None,self.tokenizer,self.panel)
        response=SimpleNamespace(text=TARGET,token_ids=[2]*128,finish_reason='length',stop_reason=None)
        model.llm=SimpleNamespace(generate=lambda *args,**kwargs:[SimpleNamespace(request_id='fixture',prompt=row['rendered_prompt'],
            prompt_token_ids=row['prompt_token_ids'],finished=True,outputs=[response])])
        with patch.dict('sys.modules',{'vllm':SimpleNamespace(SamplingParams=lambda **kwargs:kwargs)}):
            with self.assertRaisesRegex(ValueError,'native protocol failure'):
                diagnostic.Capture(model,str(self.model),output,None).generate_record(row)
        events=[json.loads(line) for line in (output/'generations.jsonl').read_text().splitlines()]
        self.assertEqual([row['kind'] for row in events],['request','raw_return','output'])
        self.assertEqual(events[-1]['text'],TARGET)
        self.assertEqual(events[-1]['finish_reason'],'length')

    def test_lease_timezone_and_headroom(self):
        with self.assertRaisesRegex(ValueError,'timezone'):
            diagnostic.lease_check('2999-01-01T00:00:00',60)
        with self.assertRaisesRegex(ValueError,'headroom'):
            diagnostic.lease_check('2000-01-01T00:00:00Z',60)

    def test_controller_order_shared_off_and_replay(self):
        run,called,result=self.simulated_run()
        self.assertEqual([row[0] for row in called],diagnostic.PROTOCOL['order'])
        self.assertTrue(all(0<row[2]<=840 for row in called))
        self.assertEqual(len(self.models),3)
        self.assertEqual(sum(len(model.calls) for model in self.models),24)
        self.assertIsNone(self.models[0].adapter_path)
        self.assertEqual([Path(model.adapter_path).name for model in self.models[1:]],['fit_full','fit_syntax'])
        replay=diagnostic.analyze(run,self.prep)
        self.assertEqual(replay['gain_vs_shared_off'],result['gain_vs_shared_off'])
        self.assertEqual(result['reads']['off']['counts']['t02']['denominator'],1)
        self.assertEqual(result['reads']['off']['counts']['other7_exposed_development']['denominator'],7)

    def test_failure_stops_no_retry_or_later_stage(self):
        run,called,_=self.simulated_run('fit_full')
        self.assertEqual([row[0] for row in called],['off','fit_full'])
        self.assertTrue((run/'FAILED.json').is_file())
        self.assertFalse((run/'COMPLETED.json').exists())

    def test_replay_rejects_mutated_raw(self):
        run,_,_=self.simulated_run()
        log=run/'off'/'generations.jsonl'
        log.chmod(0o644)
        log.write_text(log.read_text()+'{}\n')
        with self.assertRaisesRegex(ValueError,'artifact hash mismatch'):
            diagnostic.analyze(run,self.prep)

    def test_cli_preparation_and_worker_plumbing(self):
        pins=self.root/'pins.json'
        pins.write_text(json.dumps(dict(model_path=str(self.model),files=self.pins)))
        with patch.object(diagnostic,'prepare',return_value={'status':'fixture'}) as call,redirect_stdout(io.StringIO()):
            diagnostic.main(['--source-run',str(self.source),'--source-preparation',str(self.source_prep),
                             '--model-path',str(self.model),'--pins',str(pins),'--out',str(self.prep)])
        call.assert_called_once_with(str(self.prep),str(self.source),str(self.source_prep),str(self.model),self.pins)
        with patch.object(diagnostic.base.supervisor,'selected_device',return_value='1'), \
             patch.object(diagnostic,'evaluate',return_value={'status':'fixture'}) as call,redirect_stdout(io.StringIO()):
            diagnostic.main(['--preparation',str(self.prep),'--out',str(self.root/'on'),'--condition','full',
                             '--adapter',str(self.root/'fit_full'),'--device','1','--lease-deadline-utc','2999-01-01T00:00:00Z','--allow-gpu'])
        self.assertEqual(call.call_args.kwargs['adapter'],str(self.root/'fit_full'))

    def test_cli_requires_explicit_device_lease_and_opt_in(self):
        with self.assertRaisesRegex(ValueError,'Main GPU opt-in'):
            diagnostic.main(['--preparation',str(self.prep),'--out',str(self.root/'run')])


if __name__ == '__main__':
    unittest.main()
