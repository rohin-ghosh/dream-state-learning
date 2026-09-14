"""CPU fixtures only: quality fit admission, masks, saved state and readouts."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_goal_quality_train as runner
from tests.test_astra_goal_pair_train import fixture as parent_fixture
from tests.test_astra_event_two_hop_memory import material_fixture, actor, write
from tests.test_astra_corrective_sleep_train import fake_engine
from tests.test_experienced_event_goal_quality import fixtures, child
from tests.test_experienced_event_two_hop_lesson import Tokenizer


def encoded_fixture():
    return tuple(runner.source.native.EncodedRow((9,) + (42,) * (index % 7 + 1) + (151645, 10),
        (-100,) + (42,) * (index % 7 + 1) + (151645, -100), (42,) * (index % 7 + 1) + (151645,))
        for index in range(1674))


def options(root):
    return SimpleNamespace(**{name: str(root/name.replace('_', '-')) for name in (
        'base_after', 'campaign', 'audit_root', 'repair_root', 'cycle_root')},
        lesson_root=str(root/'lesson'), transfer_root=str(root/'transfer'),
        bundle=str(root/'bundle'), bundle_sha='b'*64, model_dir=None,
        shard_roots=[str(root/f'shard-{shard}') for shard in range(8)],
        quality_root=str(root/'assembled'), unit_roots=None)


def cli(root, phase, arm=None, output=None):
    values = ['--phase', phase, '--output', str(output or root/phase), '--gpu-uuid', 'fake-gpu']
    for key, value in vars(options(root)).items():
        if value is not None:
            values += ['--'+key.replace('_', '-')] + (value if isinstance(value, list) else [value])
    if arm:
        values += ['--arm', arm, '--baseline', str(root/'baseline')]
    if phase == 'after':
        values += ['--training', str(root/'train')]
    return values


def fixture(root, stack, capsule):
    data = material_fixture()
    state = parent_fixture(root, stack, data)
    original = runner.memory.load_inputs(options(root))
    original['binding']['transfer']['trained_state'] = runner.PARENT_STATE
    parent = original['binding']['transfer']
    admitted = dict(binding=dict(protocol_sha256=runner.COLLECTION_PROTOCOL_SHA), manifest=dict(
        parent_state=runner.PARENT_STATE, expected_base_sha256=original['arguments']['expected_base_sha256'],
        receipt_locators=dict(training=dict(sha256=parent['training_result_sha256'])),
        adapter_files=parent['trained_adapter_files'], base_files=parent['base_files']),
        exposures=capsule['original_exposures'])
    stack.enter_context(patch.object(runner.memory, 'load_inputs', return_value=original))
    stack.enter_context(patch.object(runner.collector, 'load_inputs', return_value=admitted))
    stack.enter_context(patch.object(runner, 'read_assembly', return_value=capsule))
    return SimpleNamespace(native=state, original=original, admitted=admitted)


def save_training(directory, inputs, encoded, arm):
    directory.mkdir()
    write(directory/'TRAINING_ROWS.json', inputs['material'])
    write(directory/'REFERENCE_MASKS.json', [asdict(row) for row in encoded])
    write(directory/'MASKS.json', [asdict(row) for row in runner.controlled_masks(encoded, arm)])
    write(directory/'RECIPE.json', runner.recipe(arm))
    evidence = runner.dose(encoded, arm)
    write(directory/'DOSE.json', evidence)
    (directory/'LOSSES.jsonl').write_text(''.join(runner.source.json.dumps(dict(batch,mean_loss=1.,loss=batch['loss_scale']))+'\n'
                                              for batch in evidence['batches']))
    (directory/'adapter').mkdir()
    (directory/'adapter/adapter_model.safetensors').write_bytes(b'CPU fixture not native weights')
    write(directory/'adapter/adapter_config.json', dict(r=8,fixture_state='a'*64))
    write(directory/'STATES.json', dict(before=runner.PARENT_STATE,after='a'*64))
    receipt = dict(schema=runner.SCHEMA,phase='train',status='COMPLETE',arm=arm,seed=0,fits=1,updates=2928,
        trainingAllowed=True,model_calls=0,
        loaded_adapter_state_sha256=runner.PARENT_STATE,adapter_state_after='a'*64,frozen_base_unchanged=True,
        parent_present=False,binding=inputs['binding'],baseline_contract_sha256=runner.goal.document_sha256(inputs['binding']['readout']),
        **{key:evidence[key] for key in ('actual_supervised_tokens','reference_supervised_tokens','row_presentations')},
        training_files={name:runner.source.file_hash(directory/name) for name in runner.TRAINING_FILES},
        adapter_files={path.name:runner.source.file_hash(path) for path in (directory/'adapter').iterdir()})
    write(directory/'RESULT.json',receipt)
    return receipt


class QualityFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = fixtures()
        cls.units = [runner.quality.collect_unit(cls.data['exposures'],unit,child) for unit in runner.quality.UNITS]
        cls.capsule = runner.quality.assemble(cls.data['exposures'],cls.data['teachings'],cls.units)

    def test_exact_2928_schedule_four_presentations_masks_and_denominator(self):
        encoded = encoded_fixture()
        full, control = (runner.dose(encoded,arm) for arm in runner.ARMS)
        counts = full['row_presentations']
        self.assertEqual([sum(counts[start:end]) for start,end in ((0,128),(128,210),(210,222),(222,1674))],
                         [2928,2928,48,5808])
        self.assertEqual(set(counts[210:]),{4})
        self.assertEqual(counts,control['row_presentations'])
        self.assertEqual(full['reference_supervised_tokens'],control['reference_supervised_tokens'])
        self.assertEqual(full['actual_supervised_tokens'],full['reference_supervised_tokens'])
        self.assertLess(control['actual_supervised_tokens'],full['actual_supervised_tokens'])
        self.assertEqual(runner.controlled_masks(encoded,runner.ARMS[1])[:222],encoded[:222])
        for update in range(1,2929):
            indexes, expected, reference, unused, unused_scale = runner.training_batch(encoded,update,runner.ARMS[0])
            unused,indexed,reference_control,active,scale = runner.training_batch(encoded,update,runner.ARMS[1])
            offset=update-1
            self.assertEqual(indexes,(offset%128,128+offset%82,210+(2*offset)%1464,210+(2*offset+1)%1464))
            self.assertEqual(expected['input_ids'],indexed['input_ids'])
            self.assertEqual(expected['attention_mask'],indexed['attention_mask'])
            self.assertEqual(reference,reference_control)
            self.assertAlmostEqual(7/active*scale,7/reference)
            for slot,index in enumerate(indexes):
                if index<222:
                    self.assertEqual(expected['labels'][slot],indexed['labels'][slot])
                else:
                    self.assertEqual(set(indexed['labels'][slot]),{-100})
                self.assertTrue(all(label==-100 for label in indexed['labels'][slot][len(encoded[index].labels):]))
        for seed in (1,2,True,-1):
            with self.assertRaises(ValueError): runner.recipe(runner.ARMS[0],seed)
        for update in (0,2929,True):
            with self.assertRaises(ValueError): runner.training_indexes(update)

    def test_prepare_exact_rows_no_model_and_parent_or_probe_drift_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root=Path(temporary)
            state=fixture(root,stack,self.capsule)
            before={str(path):runner.source.file_hash(path) for directory in ('lesson','transfer')
                    for path in (root/directory).rglob('*') if path.is_file()}
            result=runner.main(cli(root,'prepare'))
            self.assertEqual((result['row_count'],result['new_actual_train_targets'],result['probe_training_rows']),(1674,1452,0))
            state.native.factory.assert_not_called()
            state.native.token_loader.assert_not_called()
            for path,digest in before.items(): self.assertEqual(runner.source.file_hash(path),digest)
            state.admitted['manifest']['parent_state']='x'*64
            with self.assertRaisesRegex(ValueError,'same_37ec'): runner.load_inputs(options(root))
            state.admitted['manifest']['parent_state']=runner.PARENT_STATE
            bad=deepcopy(self.capsule)
            bad['rows'][0]['assistant'] += self.capsule['source_plan']['probes'][0]['world']['edges'][0]['event']
            with patch.object(runner,'read_assembly',return_value=bad), self.assertRaisesRegex(ValueError,'probe_identifiers'):
                runner.load_inputs(options(root))
            with self.assertRaises(FileExistsError): runner.main(cli(root,'prepare'))
            with self.assertRaisesRegex(ValueError,'overlap'): runner.main(cli(root,'prepare',output=root/'lesson/forbidden'))

    def test_partial_probe_scoring_preserves_unavailable_and_full_denominators(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root=Path(temporary)
            fixture(root,stack,self.capsule)
            inputs=runner.load_inputs(options(root))
            calls=[]
            def generate(messages,**metadata):
                calls.append(dict(messages=deepcopy(messages),**metadata))
                return actor(messages)
            summary=runner.evaluate(inputs,generate,root)
            self.assertEqual(len(summary['panels']['PROBE']),32)
            self.assertEqual(len(summary['panels']['TRAIN']),4)
            self.assertEqual(summary['primary']['denominator'],32)
            self.assertEqual(summary['primary']['individual']['denominator'],64)
            self.assertEqual({panel['shard'] for panel in summary['panels']['TRAIN']},{0,1,4,6})
            self.assertLessEqual(len(calls),960)
            bad=next(entry for entry in self.capsule['source_plan']['probes'] if not entry['source_ready'])
            observed=[call for call in calls if call.get('master')==bad['master'] and call.get('condition')=='OWN_TEXT']
            self.assertTrue(any('MEMORY UNAVAILABLE' in message['content'] for call in observed for message in call['messages']))
            forged=self.data['exposures'][bad['shard']]['collections'][bad['world_index']]['records'][0]['event']['raw']
            self.assertFalse(any(forged in message['content'] for call in observed for message in call['messages']))
            good=self.data['exposures'][2]['collections'][0]
            runtime=runner.quality.runtime(2)
            episodes=[runtime.run_episode(good['world'],task,actor,runtime.exact_text_store(good).__getitem__)
                      for task in runtime.build_tasks(good['world'])]
            actual=runner.summarize_world(good,episodes,runtime)
            expected=runtime.summarize_pairs(good,episodes)
            for key in ('individual','paired','pairs','scores'): runner.same(actual[key],expected[key],'same_strict_scoring')

    def test_saved_train_receipt_state_masks_schedule_and_nonfinite_guard(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root=Path(temporary)
            fixture(root,stack,self.capsule)
            inputs=runner.load_inputs(options(root))
            encoded=encoded_fixture()
            inputs['old_masks']=[asdict(row) for row in encoded[:222]]
            receipt=save_training(root/'saved',inputs,encoded,runner.ARMS[1])
            saved,unused=runner.read_training(root/'saved',inputs,runner.ARMS[1])
            self.assertEqual(saved['adapter_state_after'],'a'*64)
            with self.assertRaises(ValueError): runner.read_training(root/'saved',inputs,runner.ARMS[0])
            changed=runner.source.read(root/'saved/MASKS.json')
            changed[210]['labels']=[-100]*len(changed[210]['labels'])
            write(root/'saved/MASKS.json',changed)
            receipt['training_files']['MASKS.json']=runner.source.file_hash(root/'saved/MASKS.json')
            write(root/'saved/RESULT.json',receipt)
            with self.assertRaisesRegex(ValueError,'saved_control_masks'): runner.read_training(root/'saved',inputs,runner.ARMS[1])
            engine=fake_engine()
            engine.mean_loss=float('nan')
            (root/'nan').mkdir()
            with patch.object(runner,'encode_material',return_value=encoded), patch('organism_v6.pcfl_vertical_train._state_hash',return_value=runner.PARENT_STATE):
                with self.assertRaisesRegex(ValueError,'invalid_goal_loss'): runner.train(engine,inputs,root/'nan',runner.ARMS[0])
            engine.optimizer.step.assert_not_called()
            self.assertTrue((root/'nan/DOSE.json').exists())

    def test_baseline_native_replay_and_fresh_state_reload_cap(self):
        native_read_baseline=runner.read_baseline
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root=Path(temporary)
            state=fixture(root,stack,self.capsule)
            inputs=runner.load_inputs(options(root))
            stack.enter_context(patch.object(runner,'load_inputs',return_value=inputs))
            baseline=runner.main(cli(root,'baseline'))
            self.assertEqual((baseline['fits'],baseline['updates'],baseline['adapter_state_after']),(0,0,runner.PARENT_STATE))
            verified,baseline_sha=runner.read_baseline(root/'baseline',inputs)
            self.assertEqual(verified['model_calls'],baseline['model_calls'])
            encoded=encoded_fixture()
            inputs['old_masks']=[asdict(row) for row in encoded[:222]]
            receipt=save_training(root/'train',inputs,encoded,runner.ARMS[0])
            receipt['baseline_result_sha256']=baseline_sha
            write(root/'train/RESULT.json',receipt)
            stack.enter_context(patch.object(runner,'read_baseline',return_value=(baseline,baseline_sha)))
            stack.enter_context(patch.object(runner,'encode_material',return_value=encoded))
            stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',return_value='a'*64))
            result=runner.main(cli(root,'after',runner.ARMS[0]))
            self.assertEqual((result['fits'],result['updates'],result['loaded_adapter_state_sha256']),(0,0,'a'*64))
            self.assertEqual(result['training_result_sha256'],runner.source.file_hash(root/'train/RESULT.json'))
            self.assertEqual(state.native.factory.call_args.args[0].adapter_dir,str(root/'train/adapter'))
            def excess(inputs,generate,output):
                for unused in range(961): generate(self.capsule['rows'][0]['prefix'],role='actor')
            with patch.object(runner,'evaluate',side_effect=excess), self.assertRaisesRegex(ValueError,'native_call_cap'):
                runner.main(cli(root,'after',runner.ARMS[0],root/'over-cap'))
            self.assertEqual(runner.source.read(root/'over-cap/FAILED.json')['model_calls'],960)
            capture=runner.source.read(root/'baseline/CALL_000.json')
            capture['messages'][-1]['content']+='forged'
            write(root/'baseline/CALL_000.json',capture)
            baseline['output_files']['CALL_000.json']=runner.source.file_hash(root/'baseline/CALL_000.json')
            write(root/'baseline/RESULT.json',baseline)
            with self.assertRaisesRegex(ValueError,'baseline_(native_prompt|readout_replay)_drift'):
                native_read_baseline(root/'baseline',inputs)

    def test_assembly_requires_all_original_native_and_four_unit_captures(self):
        from tests.test_astra_goal_quality_collection import fixture as collection_fixture, cli as collection_cli, options as collection_options
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root=Path(temporary)
            state=collection_fixture(root,stack)
            admitted=runner.collector.load_inputs(collection_options(root,state))
            with patch.object(runner.collector,'load_inputs',return_value=admitted):
                for unit in runner.quality.UNITS:
                    runner.collector.main(collection_cli(root,state,'collect',unit))
                runner.collector.main(collection_cli(root,state,'assemble'))
            selected=SimpleNamespace(quality_root=str(root/'assemble'),unit_roots=[str(root/f'unit-{unit}') for unit in runner.quality.UNITS])
            stack.enter_context(patch.object(runner,'ASSEMBLY_SHA',runner.source.file_hash(root/'assemble/CAPSULE.json')))
            stack.enter_context(patch.object(runner,'ASSEMBLY_RESULT_SHA',runner.source.file_hash(root/'assemble/RESULT.json')))
            capsule=runner.read_assembly(selected,admitted)
            self.assertEqual(capsule['row_count'],1452)
            self.assertEqual(capsule['reused']['original_statuses'][-1]['ready'],False)
            original=runner.source.read(root/'unit-0/CALL_000.json')
            original['messages'][-1]['content']+='forged'
            write(root/'unit-0/CALL_000.json',original)
            receipt=runner.source.read(root/'unit-0/RESULT.json')
            receipt['output_files']['CALL_000.json']=runner.source.file_hash(root/'unit-0/CALL_000.json')
            write(root/'unit-0/RESULT.json',receipt)
            with self.assertRaisesRegex(ValueError,'quality_native_capture_drift'):
                runner.read_assembly(selected,admitted)
            with patch.object(runner,'ASSEMBLY_SHA','f'*64), self.assertRaisesRegex(ValueError,'exact_actual_quality'):
                runner.read_assembly(selected,admitted)

    def test_actual_target_encoding_masks_history_eot_and_no_truncation(self):
        tokenizer=Tokenizer()
        encoded=runner.encode_new_rows(self.capsule['rows'],tokenizer)
        self.assertEqual(len(encoded),1452)
        for row, source_row in zip(encoded,self.capsule['rows']):
            self.assertEqual(tokenizer.decode(row.target_ids),source_row['assistant']+tokenizer.eos_token)
            self.assertEqual(row.labels[-1],-100)
            self.assertEqual([label for label in row.labels if label!=-100],list(row.target_ids))
        forged=deepcopy(self.capsule['rows'])
        forged[0]['assistant'] += tokenizer.eos_token
        with self.assertRaisesRegex(ValueError,'special_token'):
            runner.encode_new_rows(forged,tokenizer)
        forged[0]['assistant']='ROUTE '+'z '*3000
        with self.assertRaisesRegex(ValueError,'untruncated_bounded'):
            runner.encode_new_rows(forged,tokenizer)

    def test_protocol_guard_and_no_ml_import(self):
        self.assertEqual(runner.source.file_hash(runner.PROTOCOL_PATH),runner.PROTOCOL_SHA)
        guard=Path(runner.__file__).with_name('astra_goal_quality_train_guard.sh')
        subprocess.run(['bash','-n',str(guard)],check=True)
        body=guard.read_text()
        for fragment in ('BASELINE:2|FULL_TARGET:0|NEW_TRAJECTORY_LOSS_OFF:1','14760','3960','--phase baseline',
                         'run_stage 10800','run_stage 3600','source_commit.txt','scanner.py','service_exceptions.json','21600'):
            self.assertIn(fragment,body)
        self.assertNotIn('git -C',body)
        self.assertGreater(body.index('test ! -f "$root/baseline/RESULT.json"'),body.index('run_stage 10800'))
        subprocess.run([sys.executable,'-B','-c',"import sys; from gpu import astra_goal_quality_train; assert not any(name in sys.modules for name in ('torch','transformers','peft','tokenizers'))"],check=True)

    def test_train_enters_without_baseline_results_but_after_requires_them(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root=Path(temporary)
            fixture(root,stack,self.capsule)
            self.assertFalse((root/'baseline').exists())
            with patch.object(runner,'read_baseline',side_effect=AssertionError('TRAIN must not read outcomes')) as reader, \
                 patch.object(runner,'train',side_effect=ValueError('CPU_TRAIN_ENTRY')) as fit:
                with self.assertRaisesRegex(ValueError,'CPU_TRAIN_ENTRY'):
                    runner.main(cli(root,'train',runner.ARMS[0]))
                fit.assert_called_once()
                reader.assert_not_called()
            failed=runner.source.read(root/'train/FAILED.json')
            self.assertEqual(failed['baseline_status'],'NOT_READ_TRAIN_INDEPENDENT_OF_BASELINE_RESULTS')
            self.assertIn('baseline_contract_sha256',failed)
            with self.assertRaises(FileNotFoundError):
                runner.main(cli(root,'after',runner.ARMS[0]))


if __name__ == '__main__':
    unittest.main()
