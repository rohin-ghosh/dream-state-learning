"""CPU-only scale recipe, validated-stage joins, fake fits, and bounded readouts."""

import argparse
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

from gpu import astra_goal_scale_train as runner
from tests.test_astra_corrective_sleep_train import fake_engine
from tests.test_astra_event_two_hop_memory import material_fixture, actor, write
from tests.test_astra_goal_pair_train import fixture as parent_fixture
from tests import test_experienced_event_goal_scale as scale_fixtures
from tests.test_experienced_event_two_hop import exposed_child
from tests.test_experienced_event_goal_pairs import coached_child


def cli(root, phase, arm=None, seed=0, output=None):
    values = ['--phase', phase, '--output', str(output or (root / f'seed_{seed}' / arm / phase if arm else root / 'prepare')),
              '--lesson-root', str(root / 'lesson'), '--transfer-root', str(root / 'transfer'),
              '--bundle', str(root / 'bundle'), '--bundle-sha', 'b' * 64, '--seed', str(seed), '--gpu-uuid', 'fake-gpu']
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root'):
        values += ['--' + name, str(root / name)]
    values += ['--shard-roots'] + [str(root / f'shard-{shard}') for shard in range(8)]
    if arm:
        values += ['--arm', arm]
    if phase == 'after':
        values += ['--training', str(root / f'seed_{seed}' / arm / 'train')]
    return values


def options(root):
    return argparse.Namespace(**dict(base_after=str(root/'base-after'), campaign=str(root/'campaign'),
        audit_root=str(root/'audit-root'), repair_root=str(root/'repair-root'), cycle_root=str(root/'cycle-root'),
        lesson_root=str(root/'lesson'), transfer_root=str(root/'transfer'), bundle=str(root/'bundle'),
        bundle_sha='b' * 64, shard_roots=[str(root/f'shard-{shard}') for shard in range(8)], model_dir=None))


def encoded_fixture():
    return tuple(runner.source.native.EncodedRow((9,) + (42,) * (index % 7 + 1) + (1, 10),
        (-100,) + (42,) * (index % 7 + 1) + (1, -100), (42,) * (index % 7 + 1) + (1,)) for index in range(1758))


def fixture(root, stack, material):
    state = parent_fixture(root, stack, material)
    original = runner.memory.load_inputs(options(root))
    original['binding']['transfer']['trained_state'] = runner.PARENT_STATE
    parent = original['binding']['transfer']
    manifest = dict(parent_state=runner.PARENT_STATE, adapter_files=parent['trained_adapter_files'], base_files=parent['base_files'],
        expected_base_sha256=original['arguments']['expected_base_sha256'],
        receipt_locators=dict(training=dict(sha256=parent['training_result_sha256'])))
    first = dict(shard=0, manifest=manifest, old_ids=sorted(scale_fixtures.GoalScaleTests.old_ids), registry=scale_fixtures.GoalScaleTests.registry,
        worlds=scale_fixtures.GoalScaleTests.registry[0], binding=dict(shard=0, worlds=scale_fixtures.GoalScaleTests.registry[0],
        state=runner.PARENT_STATE, protocol_sha256=runner.COLLECTION_PROTOCOL_SHA))
    stage_documents = []
    for shard in range(8):
        exposure = dict(collections=scale_fixtures.GoalScaleTests.collections[shard], source_ready=True)
        stage_documents.append(dict(expose=exposure, teach=dict(lessons=scale_fixtures.GoalScaleTests.documents[shard], curriculum_ready=True, row_count=192),
            baseline=runner.collector.execute_phase('baseline', dict(first, shard=shard, worlds=scale_fixtures.GoalScaleTests.registry[shard]),
                lambda messages, **metadata: actor(messages), exposure)))
    stage_calls = []

    def read_stage(directory, phase, inputs, exposure=None, dependencies=None):
        shard = inputs['shard']
        runner.require(Path(directory) == root / f'shard-{shard}' / phase, 'ordered_native_shard_required')
        runner.same(inputs['worlds'], scale_fixtures.GoalScaleTests.registry[shard], 'fixture_world_join')
        expected = {} if phase == 'expose' else dict(exposure_result_sha256=f'expose-{shard}')
        if phase == 'baseline':
            expected['teaching_result_sha256'] = f'teach-{shard}'
        runner.same(dependencies or {}, expected, 'fixture_dependency_join')
        stage_calls.append((shard, phase))
        return stage_documents[shard][phase], f'{phase}-{shard}'

    protocol = root / 'fit-protocol.md'
    protocol.write_text('CPU fixture only, not native fit authorization\n')
    stack.enter_context(patch.object(runner, 'PROTOCOL_PATH', str(protocol)))
    stack.enter_context(patch.object(runner, 'PROTOCOL_SHA', runner.source.file_hash(protocol)))
    stack.enter_context(patch.object(runner.memory, 'load_inputs', return_value=original))
    loader = stack.enter_context(patch.object(runner.collector, 'load_inputs', return_value=first))
    stack.enter_context(patch.object(runner.collector, 'read_stage', side_effect=read_stage))
    return SimpleNamespace(native=state, original=original, first=first, stages=stage_documents, calls=stage_calls, loader=loader)


class ScaleTrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scale_fixtures.GoalScaleTests.setUpClass()
        cls.material = material_fixture()

    def test_exact_schedule_masks_padding_common_denominator_and_three_seeds(self):
        encoded = encoded_fixture()
        full, control = (runner.dose(encoded, arm) for arm in runner.ARMS)
        counts = full['row_presentations']
        self.assertEqual([sum(counts[start:end]) for start, end in ((0,128),(128,210),(210,222),(222,1758))],
                         [12384,12384,192,24576])
        self.assertEqual(set(counts[210:]), {16})
        self.assertEqual(counts, control['row_presentations'])
        self.assertEqual(full['reference_supervised_tokens'], control['reference_supervised_tokens'])
        self.assertEqual(full['actual_supervised_tokens'], full['reference_supervised_tokens'])
        self.assertLess(control['actual_supervised_tokens'], full['actual_supervised_tokens'])
        self.assertEqual(runner.controlled_masks(encoded, runner.ARMS[1])[:222], encoded[:222])
        for update in range(1, runner.UPDATES + 1):
            offset = update - 1
            indexes, reference_batch, reference, unused, unused_scale = runner.training_batch(encoded, update, runner.ARMS[0])
            self.assertEqual(indexes, (offset%128,128+offset%82,210+(2*offset)%1548,210+(2*offset+1)%1548))
            unused, batch, reference_control, active, scale = runner.training_batch(encoded, update, runner.ARMS[1])
            self.assertEqual(reference, reference_control)
            self.assertEqual(batch['input_ids'], reference_batch['input_ids'])
            self.assertEqual(batch['attention_mask'], reference_batch['attention_mask'])
            for slot, index in enumerate(indexes):
                if index < 222:
                    self.assertEqual(batch['labels'][slot], reference_batch['labels'][slot])
                else:
                    self.assertTrue(all(label == -100 for label in batch['labels'][slot]))
                self.assertTrue(all(label == -100 for label in batch['labels'][slot][len(encoded[index].labels):]))
            self.assertAlmostEqual((7 / active) * scale, 7 / reference)
        for seed in (0,1,2):
            recipe = runner.recipe(runner.ARMS[1], seed)
            self.assertEqual(recipe['seed'], seed)
            self.assertEqual(recipe['lora_dropout'], 0.05)
            self.assertEqual(recipe['masked_row_indexes'], list(range(222,1758)))
        for seed in (-1,3,True):
            with self.assertRaises(ValueError):
                runner.recipe(runner.ARMS[0], seed)
        for update in (0,12385,True):
            with self.assertRaises(ValueError):
                runner.training_indexes(update)

    def test_prepare_all_eight_actual_documents_no_score_gate_or_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            before = {str(path): runner.source.file_hash(path) for folder in ('lesson','transfer') for path in (root/folder).rglob('*') if path.is_file()}
            result = runner.main(cli(root, 'prepare'))
            self.assertEqual((result['row_count'], result['new_actual_train_targets'], result['probe_training_rows']), (1758,1536,0))
            self.assertEqual(state.calls, [(shard,phase) for shard in range(8) for phase in ('expose','teach','baseline')])
            state.loader.assert_called_once()
            state.native.factory.assert_not_called()
            state.native.token_loader.assert_not_called()
            rows = runner.source.read(root/'prepare/TRAINING_ROWS.json')['new_trajectory_rows']
            self.assertEqual(Counter(row['shard'] for row in rows), dict.fromkeys(range(8),192))
            self.assertEqual([row['row_index'] for row in rows], list(range(1536)))
            for path, digest in before.items():
                self.assertEqual(runner.source.file_hash(path), digest)
            for flaw in ('order', 'duplicate', 'source_failure', 'incomplete', 'native_rows', 'parent', 'bundle', 'old_masks'):
                altered = options(root)
                call_count = len(state.calls)
                with ExitStack() as changes:
                    if flaw == 'order':
                        altered.shard_roots.reverse()
                    elif flaw == 'duplicate':
                        altered.shard_roots[-1] = altered.shard_roots[0]
                    elif flaw == 'source_failure':
                        changes.enter_context(patch.dict(state.stages[0]['expose'], source_ready=False))
                    elif flaw == 'incomplete':
                        changes.enter_context(patch.dict(state.stages[7]['teach'], row_count=191))
                    elif flaw == 'native_rows':
                        bad = deepcopy(state.stages[7]['teach']['lessons'])
                        bad['rows'][0]['target'] = 'fabricated'
                        changes.enter_context(patch.dict(state.stages[7]['teach'], lessons=bad))
                    elif flaw == 'parent':
                        changes.enter_context(patch.dict(state.original['binding']['transfer'], trained_state='0'*64))
                    elif flaw == 'bundle':
                        changes.enter_context(patch.dict(state.first['manifest'], adapter_files={'wrong': '0'*64}))
                    else:
                        inputs = runner.load_inputs(altered)
                        inputs['old_masks'] = []
                        with self.assertRaisesRegex(ValueError, 'unchanged_original_222_encodings_required'):
                            runner.encode_material(inputs, state.native.token_loader.return_value)
                        continue
                    with self.assertRaises(ValueError):
                        runner.load_inputs(altered)
                    if flaw == 'source_failure':
                        self.assertEqual(state.calls[call_count:], [(0,'expose')])

    def test_two_complete_fake_fits_seed_bound_reload_and_full_probe_readout(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            inputs = runner.load_inputs(options(root))
            encoded = runner.encode_material(inputs, state.native.token_loader.return_value)
            stack.enter_context(patch.object(runner, 'load_inputs', return_value=inputs))
            stack.enter_context(patch.object(runner, 'encode_material', return_value=encoded))
            trained = [runner.main(cli(root, 'train', arm, seed=2)) for arm in runner.ARMS]
            self.assertEqual([result['updates'] for result in trained], [12384,12384])
            self.assertEqual(trained[0]['reference_supervised_tokens'], trained[1]['reference_supervised_tokens'])
            self.assertGreater(trained[0]['actual_supervised_tokens'], trained[1]['actual_supervised_tokens'])
            for engine in state.native.engines[-2:]:
                self.assertEqual((engine.steps, engine.seed, len(engine.optimizers)), (12384,2,1))
            self.assertEqual(sum(scale == 1 for scale in state.native.engines[-1].backward_scales),96)
            after = [runner.main(cli(root, 'after', arm, seed=2)) for arm in runner.ARMS]
            for result, training in zip(after,trained):
                self.assertEqual(result['loaded_adapter_state_sha256'], training['adapter_state_after'])
                self.assertEqual(result['adapter_state_after'], training['adapter_state_after'])
                self.assertEqual(result['fits'],0)
                self.assertLessEqual(result['model_calls'],864)
                self.assertEqual(result['primary']['correct'],32)
                self.assertEqual(result['primary']['denominator'],32)
                self.assertEqual(result['primary']['individual']['denominator'],64)
                self.assertEqual(len(result['primary']['worlds']),16)
                self.assertEqual(len(result['panels']['PROBE']),32)
                self.assertEqual(result['panels']['TRAIN'],[])
                self.assertEqual(result['train_after'],'NOT_EVALUATED_BOUNDED_PROBE_PRIORITY')
                self.assertTrue(result['engineering_checks']['probe_pairs'])
                self.assertTrue(result['engineering_checks']['each_probe_world'])
                self.assertFalse(result['baseline_comparison']['improves_over_baseline'])
                self.assertGreaterEqual(result['generated_tokens'],0)
                calls = [runner.source.read(path) for path in (root/'seed_2'/training['arm']/'after').glob('CALL_*.json')]
                self.assertEqual(sum(call['graph']=='PROBE' for call in calls),768)
            self.assertEqual(after[0]['panels'],after[1]['panels'])
            state.native.factory.reset_mock()
            training_path = root/'seed_2'/runner.ARMS[1]/'train'
            for arm, seed in ((runner.ARMS[0],2),(runner.ARMS[1],0)):
                with self.assertRaisesRegex(ValueError, 'own_completed_goal_arm_required'):
                    runner.read_training(training_path, inputs, arm, seed)
            masks = runner.source.read(training_path/'MASKS.json')
            masks[210]['labels'] = [-100]*len(masks[210]['labels'])
            write(training_path/'MASKS.json',masks)
            receipt = runner.source.read(training_path/'RESULT.json')
            receipt['training_files']['MASKS.json'] = runner.source.file_hash(training_path/'MASKS.json')
            write(training_path/'RESULT.json',receipt)
            with self.assertRaisesRegex(ValueError,'saved_control_masks_drift'):
                runner.read_training(training_path, inputs, runner.ARMS[1],2)
            state.native.factory.assert_not_called()
            native_factory = state.native.factory.side_effect

            def invalid_factory(*args, **kwargs):
                engine = native_factory(*args, **kwargs)
                engine.invalid = True
                return engine

            state.native.factory.side_effect = invalid_factory
            def over_budget(inputs, generate, output):
                for unused in range(865):
                    generate([dict(role='user',content='fixture')],role='actor')
            with patch.object(runner,'evaluate',side_effect=over_budget):
                with self.assertRaisesRegex(ValueError,'goal_fit_native_call_cap'):
                    runner.main(cli(root,'after',runner.ARMS[0],seed=2,output=root/'over-cap'))
            failed = runner.source.read(root/'over-cap/FAILED.json')
            self.assertEqual(failed['model_calls'],864)
            self.assertTrue(failed['cap_hit'])

    def test_seed_and_nonfinite_pregradient_failure_preserve_artifacts(self):
        for seed in (0,1,2):
            with TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                engine.mean_loss = float('nan')
                stack.enter_context(patch.object(runner,'encode_material',return_value=encoded_fixture()))
                stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',return_value=runner.PARENT_STATE))
                with self.assertRaisesRegex(ValueError,'invalid_goal_loss'):
                    runner.train(engine, dict(material={'fixture':True}), Path(temporary), runner.ARMS[0],seed)
                engine.torch.manual_seed.assert_called_once_with(seed)
                engine.optimizer.step.assert_not_called()
                self.assertTrue((Path(temporary)/'DOSE.json').exists())

    def test_native_capture_replay_timing_all_eight_shards_and_forgery(self):
        native_read_stage = runner.collector.read_stage
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            exposures = []
            for shard in range(8):
                worlds = state.first['registry'][shard]
                inputs = dict(state.first, shard=shard, worlds=worlds,
                              binding=dict(state.first['binding'], shard=shard, worlds=worlds))
                dependencies, exposure = {}, None
                for phase in ('expose','teach','baseline'):
                    directory = root / f'shard-{shard}' / phase
                    directory.mkdir(parents=True)
                    calls = []
                    child = {'expose':exposed_child,'teach':coached_child,'baseline':actor}[phase]

                    def generate(messages, **metadata):
                        response = child(messages)
                        capture = dict(call_index=len(calls), shard=shard, messages=deepcopy(messages),
                                       response=deepcopy(response), error=None, **metadata)
                        calls.append(capture)
                        write(directory / f"CALL_{capture['call_index']:03d}.json", capture)
                        return response

                    document = runner.collector.execute_phase(phase,inputs,generate,exposure,
                        lambda name, value: write(directory/name,value))
                    write(directory/'DATA.json',document)
                    write(directory/'STATES.json',dict(before=runner.PARENT_STATE,after=runner.PARENT_STATE))
                    receipt = dict(schema=runner.collector.SCHEMA, phase=phase, status='COMPLETE', shard=shard,
                        fits=0, updates=0, trainingAllowed=False, loaded_adapter_state_sha256=runner.PARENT_STATE,
                        adapter_state_after=runner.PARENT_STATE, frozen_base_unchanged=True, protocol=runner.goal.breadth.PROTOCOL,
                        parent_present=phase=='teach', max_native_calls=runner.collector.CAPS[phase], binding=inputs['binding'],
                        dependencies=dict(dependencies), model_calls=len(calls), role_calls=dict(Counter(call['role'] for call in calls)),
                        **{key:document[key] for key in ('source_ready','case_failures','data_status')})
                    if phase == 'teach':
                        receipt.update(curriculum_ready=document['curriculum_ready'],row_count=document['row_count'])
                    elif phase == 'baseline':
                        receipt['summaries'] = [{key:panel[key] for key in ('master','split','condition','summary')} for panel in document['panels']]
                    receipt['output_files'] = {path.name:runner.source.file_hash(path) for path in directory.glob('*.json')}
                    write(directory/'RESULT.json',receipt)
                    if phase == 'expose':
                        exposure = document
                        exposures.append(document)
                        dependencies['exposure_result_sha256'] = runner.source.file_hash(directory/'RESULT.json')
                    elif phase == 'teach':
                        dependencies['teaching_result_sha256'] = runner.source.file_hash(directory/'RESULT.json')
            with patch.object(runner.collector,'read_stage',side_effect=native_read_stage):
                loaded = runner.load_inputs(options(root))
            self.assertEqual(len(loaded['material']['new_trajectory_rows']),1536)
            self.assertEqual(len(loaded['admission_timing']['shard_replay_seconds']),8)
            print('CPU_SYNTHETIC_NATIVE_REPLAY_TIMING ' + runner.source.json.dumps(loaded['admission_timing'],sort_keys=True))
            state.native.factory.assert_not_called()
            state.native.token_loader.assert_not_called()
            directory = root/'shard-7/teach'
            capture = runner.source.read(directory/'CALL_000.json')
            capture['response']['raw'] = 'ROUTE fabricated'
            write(directory/'CALL_000.json',capture)
            receipt = runner.source.read(directory/'RESULT.json')
            receipt['output_files']['CALL_000.json'] = runner.source.file_hash(directory/'CALL_000.json')
            write(directory/'RESULT.json',receipt)
            with self.assertRaises(ValueError):
                native_read_stage(directory,'teach',inputs,exposures[7],
                    dict(exposure_result_sha256=runner.source.file_hash(root/'shard-7/expose/RESULT.json')))

    def test_unbound_protocol_cpu_only_import_and_guard_budget(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch','transformers','peft','tokenizers'):
        raise AssertionError(name)
    return original(name,*args,**kwargs)
builtins.__import__ = checked
from gpu import astra_goal_scale_train
'''
        result = subprocess.run([sys.executable,'-B','-c',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        with patch.object(runner,'PROTOCOL_PATH',None), patch.object(runner.memory,'load_inputs') as loader:
            with self.assertRaisesRegex(ValueError,'prospective_scale_fit_protocol_not_bound'):
                runner.load_inputs(SimpleNamespace())
            loader.assert_not_called()
        guard = Path(runner.__file__).with_name('astra_goal_scale_train_guard.sh')
        self.assertEqual(subprocess.run(['bash','-n',str(guard)],capture_output=True).returncode,0)
        for text in ('test "$#" -eq 7','cat "$root/source_commit.txt"','run_stage 43200 --phase train',
                     'run_stage 10800 --phase after','admission_started + 54420','-gt 300','1789980180 - 21600',
                     'CUDA_VISIBLE_DEVICES= python3','"$index" "$uuid"','service_exceptions.json','OMP_NUM_THREADS=1',
                     'deadline - $(date +%s) - 60','--kill-after=60','test ! -e "$run"','scale_fit_protocol_not_bound'):
            self.assertIn(text,guard.read_text())
        self.assertNotIn('git -C',guard.read_text())
        self.assertEqual(runner.source.file_hash(Path(runner.__file__).resolve().parents[1]/runner.PROTOCOL_PATH),runner.PROTOCOL_SHA)


if __name__ == '__main__':
    unittest.main()
