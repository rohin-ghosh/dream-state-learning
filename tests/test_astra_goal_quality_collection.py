"""CPU-only native bridge fixtures; no actual model, GPU or source collection."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_goal_quality_collection as runner
from tests.test_astra_goal_scale_collection import fixture as portable_fixture
from tests.test_astra_event_two_hop_memory import write
from tests.test_experienced_event_goal_quality import fixtures


def options(root,state):
    return SimpleNamespace(bundle=str(root/'bundle'),bundle_sha=state.bundle_sha,model_dir=str(root/'model'),
        shard_roots=[str(root/f'shard-{shard}') for shard in range(8)])


def cli(root,state,phase,unit=None,output=None):
    values = ['--bundle',str(root/'bundle'),'--bundle-sha',state.bundle_sha,'--model-dir',str(root/'model'),
        '--phase',phase,'--output',str(output or (root/f'unit-{unit}' if unit is not None else root/phase)),
        '--gpu-uuid','fake-gpu','--shard-roots'] + [str(root/f'shard-{shard}') for shard in range(8)]
    if unit is not None:
        values += ['--unit',str(unit)]
    if phase == 'assemble':
        values += ['--unit-roots'] + [str(root/f'unit-{unit}') for unit in runner.quality.UNITS]
    return values


def fixture(root,stack):
    state = portable_fixture(root,stack)
    stack.enter_context(patch.object(runner,'ORIGINAL_PROTOCOL_SHA',runner.original.PROTOCOL_SHA))
    first = runner.original.load_inputs(SimpleNamespace(**vars(options(root,state)),shard=0))
    data = fixtures()
    runner.same(first['old_ids'],data['old_ids'],'fixture_old_id_alignment')
    for shard in range(8):
        worlds = first['registry'][shard]
        binding = dict(first['binding'],shard=shard,worlds=worlds)
        expose_sha = None
        for phase in (('expose','teach') if shard in runner.quality.REUSED_SHARDS else ('expose',)):
            directory = root/f'shard-{shard}'/phase
            directory.mkdir(parents=True)
            if phase == 'expose':
                document = data['exposures'][shard]
                calls = []
                for index,collection in enumerate(document['collections']):
                    write(directory/f'COLLECTION_{index:02d}.json',collection)
                    for capture in collection['captures']:
                        calls.append(dict(call_index=len(calls),shard=shard,role='exposure',master=collection['master'],
                            **{key:deepcopy(capture[key]) for key in ('messages','response','error')}))
            else:
                lessons = data['teachings'][shard]
                document = dict(lessons=lessons,row_count=len(lessons['rows']),curriculum_ready=lessons['ready'],source_ready=True,
                    case_failures=sum(not entry['complete'] for entry in lessons['episodes']),
                    data_status='CURRICULUM_READY' if lessons['ready'] else 'PARTIAL_TEACHING_FAILURES')
                write(directory/'LESSONS.json',lessons)
                calls = [dict(call_index=index,shard=shard,role='coached_actor',
                    **{key:deepcopy(capture[key]) for key in ('messages','response','error')}) for index,capture in enumerate(lessons['captures'])]
            for capture in calls:
                write(directory/f"CALL_{capture['call_index']:03d}.json",capture)
            write(directory/'DATA.json',document)
            write(directory/'STATES.json',dict(before=runner.PARENT_STATE,after=runner.PARENT_STATE))
            receipt = dict(schema=runner.original.SCHEMA,phase=phase,status='COMPLETE',shard=shard,fits=0,updates=0,
                trainingAllowed=False,loaded_adapter_state_sha256=runner.PARENT_STATE,adapter_state_after=runner.PARENT_STATE,
                frozen_base_unchanged=True,protocol=runner.quality.scale.breadth.PROTOCOL,parent_present=phase=='teach',
                max_native_calls=runner.original.CAPS[phase],binding=binding,
                dependencies={} if phase=='expose' else dict(exposure_result_sha256=expose_sha),
                model_calls=len(calls),role_calls=dict(Counter(capture['role'] for capture in calls)),
                **{key:document[key] for key in ('source_ready','case_failures','data_status')})
            if phase == 'teach':
                receipt.update(row_count=document['row_count'],curriculum_ready=document['curriculum_ready'])
            receipt['output_files'] = {path.name:runner.source.file_hash(path) for path in directory.glob('*.json')}
            write(directory/'RESULT.json',receipt)
            if phase == 'expose':
                expose_sha = runner.source.file_hash(directory/'RESULT.json')
    return state


class QualityCollectionTests(unittest.TestCase):
    def test_prepare_reads_failed_source_and_teaching_without_baselines_or_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root,stack)
            original = {str(path):runner.source.file_hash(path) for folder in root.glob('shard-*') for path in folder.rglob('*') if path.is_file()}
            with patch.object(runner.original,'read_stage',wraps=runner.original.read_stage) as reader:
                result = runner.main(cli(root,state,'prepare'))
            self.assertEqual(len(reader.call_args_list),12)
            self.assertEqual([call.args[1] for call in reader.call_args_list].count('expose'),8)
            self.assertEqual([call.args[1] for call in reader.call_args_list].count('teach'),4)
            self.assertTrue(all(call.args[1] != 'baseline' for call in reader.call_args_list))
            self.assertEqual((result['reused_candidate_rows'],result['eligible_train_worlds'],result['new_worlds']),(756,61,29))
            self.assertEqual((result['model_calls'],result['fits'],result['updates']),(0,0,0))
            self.assertFalse(result['trainingAllowed'])
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            reused = runner.source.read(root/'prepare/REUSED_QUALITY.json')
            self.assertEqual(reused['original_statuses'][-1],dict(shard=7,ready=False,original_rows=0))
            for path,digest in original.items():
                self.assertEqual(runner.source.file_hash(path),digest)
            for phase in ('prepare','collect'):
                with self.assertRaisesRegex(ValueError,'original_artifact_overlap_forbidden'):
                    runner.main(cli(root,state,phase,0 if phase=='collect' else None,root/'shard-0/forbidden'))
            path = root/'shard-7/teach/CALL_000.json'
            capture = runner.source.read(path)
            capture['response']['raw'] = 'ROUTE fabricated'
            write(path,capture)
            receipt_path = path.parent/'RESULT.json'
            receipt = runner.source.read(receipt_path)
            receipt['output_files'][path.name] = runner.source.file_hash(path)
            write(receipt_path,receipt)
            with self.assertRaises(ValueError):
                runner.main(cli(root,state,'prepare',output=root/'bad-original'))
            state.factory.assert_not_called()

    def test_four_readonly_units_shared_sources_native_join_and_cpu_capsule(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root,stack)
            inputs = runner.load_inputs(options(root,state))
            stack.enter_context(patch.object(runner,'load_inputs',return_value=inputs))
            results = [runner.main(cli(root,state,'collect',unit)) for unit in runner.quality.UNITS]
            self.assertEqual([result['model_calls'] for result in results],[168,192,168,168])
            self.assertEqual(sum(result['row_count'] for result in results),696)
            self.assertEqual(len(state.engines),4)
            for result,engine,unit in zip(results,state.engines,runner.quality.UNITS):
                self.assertEqual((result['status'],result['loaded_adapter_state_sha256'],result['adapter_state_after']),('COMPLETE',runner.PARENT_STATE,runner.PARENT_STATE))
                self.assertEqual((engine.steps,len(engine.optimizers)),(0,0))
                self.assertFalse(engine.parameter.requires_grad)
                self.assertEqual(result['role_calls'],dict(coached_actor=runner.quality.UNIT_CAPS[unit]))
                self.assertEqual(result['native_error_calls'],0)
                document = runner.read_unit(root/f'unit-{unit}',inputs,unit)
                self.assertEqual(len(document['rows']),runner.quality.UNIT_CAPS[unit])
            state.factory.reset_mock()
            state.token_loader.reset_mock()
            assembled = runner.main(cli(root,state,'assemble'))
            self.assertEqual((assembled['status'],assembled['row_count'],assembled['new_calls']),('COMPLETE_NO_MODEL',1452,696))
            self.assertEqual(assembled['model_calls'],0)
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            capsule = runner.source.read(root/'assemble/CAPSULE.json')['capsule']
            self.assertEqual((capsule['source_plan']['probe_goals'],capsule['source_plan']['probe_pairs']),(64,32))
            self.assertEqual(capsule['reused']['original_statuses'][-1]['ready'],False)
            path = root/'unit-0/CALL_000.json'
            capture = runner.source.read(path)
            capture['messages'][-1]['content'] += '\nforged native prompt'
            write(path,capture)
            receipt = runner.source.read(path.parent/'RESULT.json')
            receipt['output_files'][path.name] = runner.source.file_hash(path)
            write(path.parent/'RESULT.json',receipt)
            with self.assertRaisesRegex(ValueError,'quality_native_capture_drift'):
                runner.read_unit(path.parent,inputs,0)

    def test_native_errors_are_retained_case_failures_state_drift_is_failed(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root,stack)
            inputs = runner.load_inputs(options(root,state))
            stack.enter_context(patch.object(runner,'load_inputs',return_value=inputs))
            original_factory = state.factory.side_effect
            def errors(*args,**kwargs):
                engine = original_factory(*args,**kwargs)
                engine.raise_native = True
                return engine
            state.factory.side_effect = errors
            result = runner.main(cli(root,state,'collect',0))
            self.assertEqual((result['status'],result['model_calls'],result['native_error_calls'],result['row_count']),('COMPLETE',28,28,0))
            self.assertEqual(result['attempted_tasks'],28)
            runner.read_unit(root/'unit-0',inputs,0)
            def drift(*args,**kwargs):
                engine = original_factory(*args,**kwargs)
                engine.mutate_state = True
                return engine
            state.factory.side_effect = drift
            with self.assertRaisesRegex(ValueError,'quality_readonly_state_drift'):
                runner.main(cli(root,state,'collect',1))
            failed = runner.source.read(root/'unit-1/FAILED.json')
            self.assertEqual(failed['model_calls'],192)
            self.assertTrue((root/'unit-1/DATA.json').exists())

    def test_bound_protocol_import_no_ml_and_no_fit_interface(self):
        self.assertEqual(runner.PROTOCOL_SHA,'cf742f62dc45810caeea3ec68272a9e1a8c97d3b7c6c06f148639252ba1738f1')
        self.assertEqual(runner.source.file_hash(Path(runner.__file__).resolve().parents[1]/runner.PROTOCOL_PATH),runner.PROTOCOL_SHA)
        self.assertEqual((runner.NATIVE_SECONDS,runner.quality.UNIT_CAPS),(3600,{0:168,1:192,4:168,6:168}))
        script = '''
import builtins
original = builtins.__import__
def checked(name,*args,**kwargs):
    if name.split('.')[0] in ('torch','transformers','peft','tokenizers'):
        raise AssertionError(name)
    return original(name,*args,**kwargs)
builtins.__import__ = checked
from gpu import astra_goal_quality_collection
'''
        result = subprocess.run([sys.executable,'-B','-c',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
