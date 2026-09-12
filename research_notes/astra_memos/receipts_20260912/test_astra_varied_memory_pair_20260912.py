"""CPU stubs only: no native tokenizer, tensor loading, workers, or GPU queries."""
from contextlib import ExitStack
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


side = load('/tmp/astra_varied_memory_pair_20260912.py', 'varied_pair_test')
memory = load('/tmp/astra_memory_only_20260912.py', 'varied_memory_test_helper')
memory.bind(Path.cwd(), '/tmp/astra_fading_sentinel_20260912.py')
side.memory, side.old, side.base = memory, memory.old, memory.base
side.trainer, side.dev, side.exact = memory.trainer, memory.dev, memory.exact
from organism_v6 import varied_memory_replay_corpus
side.varied = varied_memory_replay_corpus


class VariedPairTests(unittest.TestCase):
    def setUp(self):
        now = time.time()
        self.state = {'lora': dict(shape=[2, 2], dtype='torch.float32', sha256='before')}
        self.saved = {'lora': dict(shape=[2, 2], dtype='torch.float32', sha256='after')}
        self.parent = dict(parent='/fixture/original/fit_teach/adapter', parent_files={'weight':'parent'},
            provenance={}, readout_files={}, readout=dict(cases=[], requests=[], native_inputs=[]))
        self.plan = dict(model='/fixture/model', model_files={'base':'hash'}, seed=0, device='3',
            parent=self.parent, parent_state=self.state, materialroot='/fixture/material',
            material_files={arm+'.json':arm for arm in side.ARMS}, config=side.config('/fixture/model'),
            templates={name:dict(cases=[], requests=[], native_inputs=[]) for name in ('dev','exact')},
            deadline=now+4000, real_lease_end=now+7200)

    def receipt(self):
        return dict(ok=True, error=None, returncode=0, reserved_seconds=1., device='3',
            reservation_release_verified=True, owned_group_empty=True, gpu_processes_absent=True)

    def manifest(self, arm):
        expected = side.COUNTS[arm]
        warm = dict(mode='WEIGHT_WARM_START_FRESH_OPTIMIZER', parent_path=self.parent['parent'],
            parent_files=self.parent['parent_files'], parent_files_after=self.parent['parent_files'],
            parent_unchanged=True, base_frozen=True, initialized_loaded_state_check=True, phase_seed=0, adapter_count=1,
            optimizer_initial_state_entries=0, optimizer_state_restored=False, optimizer_state_saved=False,
            optimizer_initialization='fresh_per_write', phase_steps=320, parent_cumulative_steps=80, cumulative_steps=400,
            source_state=self.state, initialized_state=self.state, final_state=self.saved, dtype_conversions={})
        return dict(config=copy.deepcopy(self.plan['config']), base_model=self.plan['model'], steps=320, micro_batches=320,
            epochs_run=10, nonfinite_batches=0, empty=False, final_loss=1.,
            corpus=dict(sha256=arm, n_items=128, n_encoded=128, n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            tokens=dict(total=expected['input_per_epoch'], context=expected['context_per_epoch'], target=1000),
            train_tokens_seen=expected['input_presentations'], warm_start=warm)

    def test_valid_manifests_both_arms(self):
        for arm in side.ARMS:
            side.validate_manifest(self.plan, arm, self.manifest(arm), self.state, self.saved)

    def test_exact_native_counts_target_equality_not_input_matching(self):
        self.assertEqual(side.COUNTS['SINGLE_VIEW']['input_presentations'], 66160)
        self.assertEqual(side.COUNTS['FOUR_VIEW']['input_presentations'], 67120)
        self.assertEqual({value['target_presentations'] for value in side.COUNTS.values()}, {10000})
        self.assertEqual({value['presentations_per_source'] for value in side.COUNTS.values()}, {40})

    def test_cli_exact_recipe_and_original_forks(self):
        forks = side.paths(Path('/fixture/fits'), self.parent['parent'])
        self.assertEqual({row['parent'] for row in forks.values()}, {self.parent['parent']})
        self.assertEqual(len({row['adapter'] for row in forks.values()}), 2)
        for arm, row in forks.items():
            command = side.fit_command(self.plan, arm, row['adapter'])
            self.assertEqual(command[command.index('--init-adapter')+1], self.parent['parent'])
            for option, value in (('--seed','0'),('--epochs','10'),('--lr','0.0003'),('--overflow','truncate'),('--batch-size','4')):
                self.assertEqual(command[command.index(option)+1], value)
            self.assertEqual(command[command.index('--corpus')+1], '/fixture/material/'+arm+'.json')
            self.assertIn('--no-pack', command)
            self.assertNotIn('--chat-template', command)

    def test_cli_config_mutation_rejected(self):
        self.plan['config']['seed'] = 1
        with self.assertRaisesRegex(ValueError, 'CLI'):
            side.fit_command(self.plan, 'SINGLE_VIEW', '/fixture/child')

    def test_fit_counts_loss_and_epoch_failures(self):
        for field, value in (('steps',160),('micro_batches',319),('epochs_run',20),('nonfinite_batches',1),
                ('empty',True),('final_loss',float('nan')),('train_tokens_seen',66161)):
            manifest = self.manifest('SINGLE_VIEW')
            manifest[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, 'SINGLE_VIEW', manifest, self.state, self.saved)

    def test_material_tokens_skips_splits_rejected(self):
        for section, field, value in (('tokens','target',999),('tokens','context',5617),('tokens','total',6712),
                ('corpus','sha256','wrong'),('corpus','n_items',32),('corpus','n_encoded',127),('corpus','n_skipped_no_target',1),
                ('truncation','items_split',1),('truncation','context_tokens_dropped',1),('truncation','target_tokens_dropped',1)):
            manifest = self.manifest('SINGLE_VIEW')
            manifest[section][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, 'SINGLE_VIEW', manifest, self.state, self.saved)

    def test_parent_optimizer_freezing_and_cumulative_failures(self):
        for field, value in (('parent_path','/fixture/SEQ107'),('parent_unchanged',False),('base_frozen',False),
                ('initialized_loaded_state_check',False),('phase_seed',1),('adapter_count',2),('optimizer_initial_state_entries',1),
                ('optimizer_state_restored',True),('optimizer_state_saved',True),('phase_steps',160),
                ('parent_cumulative_steps',240),('cumulative_steps',560),('dtype_conversions',{'lora':'bf16'})):
            manifest = self.manifest('FOUR_VIEW')
            manifest['warm_start'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, 'FOUR_VIEW', manifest, self.state, self.saved)

    def test_source_initialized_saved_state_must_match_receipts(self):
        for field in ('source_state','initialized_state','final_state'):
            manifest = self.manifest('FOUR_VIEW')
            manifest['warm_start'][field] = {'wrong':{}}
            with self.subTest(field=field), self.assertRaises(ValueError):
                side.validate_manifest(self.plan, 'FOUR_VIEW', manifest, self.state, self.saved)

    def test_deadline_startup_lease_and_cleanup_bounds(self):
        now = time.time()
        self.assertEqual(side.bounds(now-30, now+4000, now+7200), now+1470)
        for values in ((now,now+1499,now+7200),(now,now+4000,now+1509),(now-1351,now+4000,now+7200),
                (now,float('nan'),now+7200),(True,now+4000,now+7200)):
            with self.subTest(values=values), self.assertRaises(ValueError): side.bounds(*values)
        with patch.object(side.time,'time',return_value=1000):
            with self.assertRaisesRegex(ValueError,'150s'): side.budget(1149.9)
            side.budget(1150.1)

    def test_no_launch_without_flag_or_wrong_device(self):
        with self.assertRaisesRegex(ValueError,'Main allocation'): side.run('/fixture')
        with patch.object(Path,'resolve',lambda path,**kwargs:path), patch.object(side.old,'read_plan',return_value=self.plan), \
                patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'9'}), patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(ValueError,'device'): side.run('/fixture',True)
        mkdir.assert_not_called()

    def test_six_hour_real_lease_never_extends_pair_or_cleanup_deadline(self):
        with patch.object(side.time,'time',return_value=10000.):
            self.assertEqual(side.bounds(10000.,10000.+6*3600,10000.+6*3600),11500.)
            self.assertEqual(side.bounds(10000.,11500.,10000.+6*3600),11500.)
            self.assertEqual(side.bounds(10000.,10000.+6*3600,11510.),11500.)
            with self.assertRaises(ValueError):side.bounds(10000.,11499.,10000.+6*3600)
            with self.assertRaises(ValueError):side.bounds(10000.,10000.+6*3600,11509.)

    def test_root0_only_before_writes(self):
        self.plan['seed'] = 1
        with patch.object(Path,'resolve',lambda path,**kwargs:path), patch.object(side.old,'read_plan',return_value=self.plan), \
                patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'3'}), patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(ValueError,'root0'): side.run('/fixture',True)
        mkdir.assert_not_called()

    def test_stale_root_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError,'fresh'): side.memory.fresh(temporary)

    def test_wrong_source_or_helper_pin(self):
        with patch.object(Path,'resolve',lambda path,**kwargs:path):
            with self.assertRaisesRegex(ValueError,'immutable'): side.bind('/wrong','/helper','/fading')
            with patch.object(Path,'read_bytes',return_value=b'wrong'), self.assertRaisesRegex(ValueError,'helper'):
                side.bind('/fixture/'+side.SOURCE_ID,'/helper','/fading')

    def test_execute_has_three_workers_and_never_reduces(self):
        calls = []
        fit = dict(parent=self.parent['parent'],adapter='/fixture/run/SINGLE_VIEW/adapter',adapter_files={'child':'hash'})
        with patch.object(side.memory,'fresh',side_effect=lambda path,*args:path), patch.object(Path,'mkdir'), \
                patch.object(side.old,'write'), patch.object(side.old,'seal'), patch.object(side,'verify'), \
                patch.object(side,'verify_fit',return_value=fit), patch.object(side.base,'expected_identity',return_value={}), \
                patch.object(side.base,'supervise',side_effect=lambda *args:calls.append(args) or self.receipt()), \
                patch.object(side.trainer,'_warm_inventory',return_value=fit['adapter_files']), \
                patch.object(side.dev,'verify'), patch.object(side.exact,'verify'), \
                patch.object(side,'capture_receipt',return_value={'captured':True}), \
                patch.object(side.dev,'reduce') as dev_reduce, patch.object(side.exact,'reduce') as exact_reduce:
            result = side.execute_arm(Path('/fixture'),Path('/fixture/run'),self.plan,'SINGLE_VIEW',time.time()+1500)
        self.assertEqual(len(calls),3)
        self.assertEqual(set(result['captures']),{'dev','exact'})
        dev_reduce.assert_not_called()
        exact_reduce.assert_not_called()
        self.assertEqual(calls[1][1]['adapter'],fit['adapter'])

    def test_reduce_requires_both_captures(self):
        with patch.object(side.dev,'reduce') as reducer, self.assertRaisesRegex(ValueError,'both arms'):
            side.reduce_pair(Path('/fixture'),self.plan,{'SINGLE_VIEW':{}},time.time()+1500)
        reducer.assert_not_called()

    def test_both_panels_reduce_despite_zero_scores(self):
        captured = {arm:dict(fit={},captures={name:{'capture':name} for name in ('dev','exact')}) for arm in side.ARMS}
        observed = []
        def reduce(root,count):
            observed.append(str(root))
            return dict(complete=True,counts=dict(total=count,correct=0))
        with patch.object(side,'capture_receipt',side_effect=lambda root,template:{'capture':root.name}), \
                patch.object(side.dev,'reduce',side_effect=lambda root:reduce(root,48)), \
                patch.object(side.exact,'reduce',side_effect=lambda root:reduce(root,16)), \
                patch.object(side.base,'digest',return_value='hash'),patch.object(side.old,'write'):
            result = side.reduce_pair(Path('/fixture'),self.plan,captured,time.time()+1500)
        self.assertEqual(len(observed),4)
        self.assertEqual(set(result),set(side.ARMS))
        self.assertEqual(result['FOUR_VIEW']['readouts']['exact']['reduction']['counts']['correct'],0)

    def test_all_four_captures_checked_before_first_reduction(self):
        captured = {arm:dict(fit={},captures={name:{} for name in ('dev','exact')}) for arm in side.ARMS}
        sequence=[]
        def capture(root,template):
            sequence.append('capture:'+str(root))
            return {}
        def reduce(root,count):
            self.assertEqual(sum(item.startswith('capture:') for item in sequence),4)
            sequence.append('reduce:'+str(root))
            return dict(complete=True,counts={'total':count,'correct':0})
        with patch.object(side,'capture_receipt',side_effect=capture),patch.object(side.base,'digest',return_value='hash'), \
                patch.object(side.old,'write'),patch.object(side.dev,'reduce',side_effect=lambda root:reduce(root,48)), \
                patch.object(side.exact,'reduce',side_effect=lambda root:reduce(root,16)):
            side.reduce_pair(Path('/fixture'),self.plan,captured,time.time()+1500)
        self.assertTrue(all(item.startswith('capture:') for item in sequence[:4]))

    def test_phase_guard_prevents_worker_spawn_near_deadline(self):
        with patch.object(side.time,'time',return_value=1000.),patch.object(side.base,'supervise') as supervise, \
                patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(ValueError,'150s'):
                side.execute_arm(Path('/fixture'),Path('/fixture/run'),self.plan,'SINGLE_VIEW',1149.)
        supervise.assert_not_called()
        mkdir.assert_not_called()

    def test_incomplete_reduction_rejected(self):
        captured = {arm:dict(captures={name:{} for name in ('dev','exact')}) for arm in side.ARMS}
        with patch.object(side,'capture_receipt',return_value={}),patch.object(side.dev,'reduce',return_value=dict(complete=False,counts={'total':47})):
            with self.assertRaisesRegex(ValueError,'not zero'):
                side.reduce_pair(Path('/fixture'),self.plan,captured,time.time()+1500)

    def controller(self, fail_arm=None, released=True, missing=False, reducer_error=False):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            observed = []
            def execute(root,pair,plan,arm,effective):
                observed.append('capture:'+arm)
                stage = pair/arm
                for name in ('fit-worker','dev/run/worker','exact/run/worker'):
                    worker = stage/name
                    worker.mkdir(parents=True)
                    side.old.write(worker/'process.json',{'pid':100})
                    if not (missing and arm == 'FOUR_VIEW' and name == 'exact/run/worker'):
                        side.old.write(worker/'supervision.json',self.receipt())
                if arm == fail_arm: raise ValueError('stub technical failure')
                return dict(fit=dict(adapter=str(stage/'adapter'),supervision=self.receipt()),captures={'dev':{},'exact':{}})
            def reduce(root,plan,captured,effective):
                observed.append('reduce:both')
                if reducer_error: raise ValueError('stub reducer failure')
                return {arm:dict(value,readouts={'dev':{'correct':0},'exact':{'correct':0}}) for arm,value in captured.items()}
            stack.enter_context(patch.object(side.old,'read_plan',return_value=self.plan))
            stack.enter_context(patch.object(side.base,'digest',return_value='hash'))
            stack.enter_context(patch.object(side,'verify',return_value=self.plan))
            stack.enter_context(patch.object(side,'verify_fit',side_effect=lambda plan,stage,arm:dict(adapter=str(stage/'adapter'))))
            stack.enter_context(patch.object(side,'execute_arm',side_effect=execute))
            stack.enter_context(patch.object(side,'reduce_pair',side_effect=reduce))
            stack.enter_context(patch.object(side.base.supervisor,'gpu_processes_absent',return_value=released))
            stack.enter_context(patch.object(side.signal,'signal'))
            timer = stack.enter_context(patch.object(side.signal,'setitimer'))
            stack.enter_context(patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'3'}))
            try: result = side.run(root,True)
            except ValueError: result = side.base.read(root/'run/terminal.json')
            self.assertEqual(timer.call_args_list[-1].args,(side.signal.ITIMER_REAL,0))
            self.assertLessEqual(timer.call_args_list[0].args[1],1360)
            with self.assertRaisesRegex(ValueError,'fresh'): side.run(root,True)
            return result,observed

    def test_controller_success_defers_outcomes_and_records_cost(self):
        result,observed = self.controller()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(observed,['capture:SINGLE_VIEW','capture:FOUR_VIEW','reduce:both'])
        self.assertEqual(result['worker_reserved_seconds'],6.)
        self.assertTrue(result['release_verified'])
        self.assertTrue(result['worker_accounting_complete'])
        self.assertFalse(result['gate_evaluated'])
        self.assertFalse(result['automatic_progression'])
        self.assertEqual(result['real_lease_end'],self.plan['real_lease_end'])

    def test_controller_failed_first_arm_never_reduces_or_retries(self):
        result,observed = self.controller(fail_arm='SINGLE_VIEW')
        self.assertEqual(result['status'],'FAILED_PARTIAL_NO_RETRY')
        self.assertEqual(observed,['capture:SINGLE_VIEW'])
        self.assertEqual(result['worker_reserved_seconds'],3.)

    def test_controller_second_failure_preserves_first_capture(self):
        result,observed = self.controller(fail_arm='FOUR_VIEW')
        self.assertEqual(result['status'],'FAILED_PARTIAL_NO_RETRY')
        self.assertEqual(set(result['captured']),{'SINGLE_VIEW'})
        self.assertNotIn('reduce:both',observed)

    def test_controller_requires_release_and_all_worker_receipts(self):
        for args in (dict(released=False),dict(missing=True),dict(reducer_error=True)):
            with self.subTest(args=args):
                result,_ = self.controller(**args)
                self.assertEqual(result['status'],'FAILED_PARTIAL_NO_RETRY')
                if args.get('missing'): self.assertFalse(result['worker_accounting_complete'])

    def test_main_gate_and_global_ceiling_not_automatic(self):
        self.assertEqual(side.SECONDS,1500)
        self.assertEqual(side.PROGRESSION['qualifying_arm'],'FOUR_VIEW')
        self.assertEqual([side.PROGRESSION[key] for key in ('dev_memory_min','exact_memory_min','dev_habit_min','dev_act_min')],[15,15,30,31])
        self.assertTrue(side.PROGRESSION['single_scores_irrelevant'])
        self.assertEqual(side.PROGRESSION['eligible_next_seeds'],[1,2])
        self.assertFalse(side.PROGRESSION['automatic_progression'])

    def test_native_material_receipt_counts_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)/'material'
            root.mkdir()
            parentroot = Path('/fixture/original')
            totals = {arm:dict(input_tokens=row['input_presentations'],context_tokens=row['context_presentations'],target_tokens=10000)
                      for arm,row in side.COUNTS.items()}
            manifest = dict(original_teach_path=str(parentroot/'teach.json'),original_teach_sha256=side.varied.ORIGINAL_TEACH_SHA256,
                source_hashes=side.varied.source_hashes(),seeds=[0,1,2],recipe=side.varied.RECIPE,claim=side.CLAIM,token_totals=totals)
            receipt = dict(status='ACTUAL_NATIVE_TOKENIZER_AUDIT_PASS_NO_FIT',source_commit=side.SOURCE_ID,source_root=str(side.base.REPO),
                material=str(root),material_manifest_sha256=side.MATERIAL_SHA,preparation_script_sha256=side.PREPARER_SHA,
                source_hashes=manifest['source_hashes'],original_plan_sha256=memory.PINS['0'][0],original_teach_sha256=side.varied.ORIGINAL_TEACH_SHA256,
                model=self.plan['model'],model_files=self.plan['model_files'],tokenizer_matches_original_model_files=True,
                no_model_forward_or_training=True,origin_authenticated=False,origin='UNRESOLVED_LOCAL_HASHES_ONLY',
                native_tokenizer_class='fixture.Native',token_totals=totals)
            audit = dict(tokenizer_class='fixture.Native',compute_matched=False,arms={arm:dict(ten_epochs=total,
                per_epoch={key:value//10 for key,value in total.items()}) for arm,total in totals.items()})
            mapping={'manifest.json':manifest,'native_prepare.json':receipt,'token_audit.json':audit}
            stack.enter_context(patch.object(side.base,'read',side_effect=lambda path:mapping[Path(path).name]))
            stack.enter_context(patch.object(side.old,'read_plan',return_value=self.plan))
            stack.enter_context(patch.object(side.base,'digest',side_effect=lambda path:side.MATERIAL_SHA if Path(path).name=='manifest.json' else memory.PINS['0'][0]))
            stack.enter_context(patch.object(side.base,'tree_hashes',return_value={'manifest.json':side.MATERIAL_SHA}))
            stack.enter_context(patch.object(side.varied,'verify'))
            self.assertEqual(side.inspect_material(root)['parentroot'],str(parentroot))
            for field,value in (('model','wrong'),('original_plan_sha256','wrong'),('source_commit','wrong'),('origin_authenticated',True),
                    ('no_model_forward_or_training',False),('preparation_script_sha256','wrong')):
                prior=receipt[field]
                receipt[field]=value
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'receipt'):side.inspect_material(root)
                receipt[field]=prior
            audit['arms']['FOUR_VIEW']['per_epoch']['input_tokens']+=1
            with self.assertRaisesRegex(ValueError,'counts'): side.inspect_material(root)

    def test_prepare_only_verifies_existing_material_and_seals_root0(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            parent = Path(temporary)
            materialroot=parent/'material'
            materialroot.mkdir()
            (materialroot/'sentinel').write_text('immutable')
            root=parent/'fits_root0_attempt1'
            bound=dict(materialroot=str(materialroot),material_files=self.plan['material_files'],native_prepare_path=str(parent/'native_prepare.json'),
                native_prepare_sha256='receipt',parentroot='/fixture/original',model=self.plan['model'],model_files=self.plan['model_files'])
            exported=dict(audit={'schedule':'actual'},corpora={arm:{'corpus':['frozen']} for arm in side.ARMS})
            def read(path):
                name=Path(path).name
                if name=='token_audit.json':return exported['audit']
                if name in [arm+'.json' for arm in side.ARMS]:return exported['corpora'][name[:-5]]
                return {}
            stack.enter_context(patch.object(side,'inspect_material',return_value=bound))
            stack.enter_context(patch.object(side.base,'model_hashes',return_value=self.plan['model_files']))
            stack.enter_context(patch.object(side.memory,'parent_record',return_value=self.parent))
            stack.enter_context(patch.object(side.old,'state_inventory',return_value=self.state))
            stack.enter_context(patch.object(side.trainer,'_warm_inventory',return_value=self.parent['parent_files']))
            warm=stack.enter_context(patch.object(side.trainer,'_warm_parent'))
            stack.enter_context(patch.object(side.base,'native_tokenizer',return_value=object()))
            stack.enter_context(patch.object(side.base,'read',side_effect=read))
            export=stack.enter_context(patch.object(side.varied,'export_native',return_value=exported))
            stack.enter_context(patch.object(side.memory,'subset'))
            stack.enter_context(patch.object(side.memory,'template',return_value=self.parent['readout']))
            stack.enter_context(patch.object(side,'sources',return_value={'sidecar':'hash'}))
            result=side.prepare(materialroot,root,'3',self.plan['deadline'],self.plan['real_lease_end'])
            plan=json.loads((root/'plan.json').read_text())
            self.assertEqual(result['status'],'PREPARED_ROOT0_NOT_LAUNCHED')
            self.assertEqual(plan['seed'],0)
            self.assertEqual(plan['aggregate_a40_seconds'],5400)
            self.assertEqual(plan['campaign_pair_ceiling'],3)
            self.assertEqual(plan['arm_order'],list(side.ARMS))
            self.assertEqual({call.args[0] for call in warm.call_args_list},{self.parent['parent']})
            self.assertEqual(len({call.args[1] for call in warm.call_args_list}),2)
            self.assertEqual(export.call_args.args[-1],(0,1,2))
            self.assertEqual({path.name for path in materialroot.iterdir()},{'sentinel'})
            self.assertEqual((materialroot/'sentinel').read_text(),'immutable')
            self.assertEqual({path.name for path in root.iterdir()},{'plan.json','plan.sha256.json'})
            with self.assertRaisesRegex(ValueError,'fresh'):
                side.prepare(materialroot,root,'3',self.plan['deadline'],self.plan['real_lease_end'])


if __name__ == '__main__':
    unittest.main()
