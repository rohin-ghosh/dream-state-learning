import ast
from copy import deepcopy
import inspect
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r139_math_astra_handoff as handoff


class FutureBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.epoch = dict(historical_ids=['R121_C000043_E1_experience'], parent_high_water=128,
            observed_unix=100, next_cycle=44)
        self.row = dict(id='R121_C000044_E0_experience', response=False, partial=False, claim=False,
            delivered=False, reservation=dict(first=129, count=1, kind='parent', reserved_unix=101,
                metadata=dict(id='R121_C000044_E0_experience')))

    def test_future_request_is_eligible(self):
        self.assertTrue(handoff.eligible(self.row, self.epoch))

    def test_each_disposition_blocks(self):
        for key in ('response','partial','claim','delivered'):
            with self.subTest(key=key):
                row = deepcopy(self.row)
                row[key] = True
                self.assertFalse(handoff.eligible(row, self.epoch))

    def test_historical_even_late_complete_never_replayed(self):
        self.epoch['historical_ids'].append(self.row['id'])
        self.assertFalse(handoff.eligible(self.row, self.epoch))

    def test_high_water_and_time_strict(self):
        for key, value in (('first',128), ('first',127), ('reserved_unix',100), ('reserved_unix',99)):
            with self.subTest(key=key, value=value):
                row = deepcopy(self.row)
                row['reservation'][key] = value
                self.assertFalse(handoff.eligible(row, self.epoch))

    def test_no_reservation(self):
        self.row['reservation'] = None
        self.assertFalse(handoff.eligible(self.row, self.epoch))

    def test_reservation_join_and_kind(self):
        for key,value in (('count',2), ('kind','native'), ('metadata',{'id':'wrong'})):
            with self.subTest(key=key):
                row = deepcopy(self.row)
                row['reservation'][key] = value
                with self.assertRaises(ValueError):
                    handoff.eligible(row, self.epoch)

    def test_old_cycle_cannot_be_relabelled_future(self):
        self.epoch['next_cycle'] = 45
        self.assertFalse(handoff.eligible(self.row, self.epoch))

    def test_only_original_experience_requests(self):
        for identifier in ('R121_C000044_E0_reflection','R121_C000044_E2_experience','REPLAY'):
            with self.subTest(identifier=identifier):
                row = deepcopy(self.row)
                row['id'] = identifier
                with self.assertRaises(ValueError):
                    handoff.eligible(row, self.epoch)


class PolicyTests(unittest.TestCase):
    def fixture(self):
        return dict(remote_root=str(handoff.QUEUE), branch='F2', family='math', life_id='R115_F2_1',
            max_parent_calls=384, max_output_tokens=8192, deadline_unix=1789596120,
            max_budget_usd=1.0, min_available_bytes=1073741824, source_files={'old':'pin'},
            parent_effort='max', terminal_filename='TERMINAL.json', terminal_binding={},
            predecessor_config={}, queue_transport='node_local', provider_lock_scope='same',
            train_tasks={'train':'hash'}, excluded_task_ids=['sealed'], cohort_sha256='cohort',
            principles_sha256='principles', fallback_parent_fields={'NEXT_GUIDANCE':'bounded'})

    def test_only_transport_metadata_and_pins_change(self):
        old = self.fixture()
        saved = deepcopy(old)
        result = handoff.broker_config(old, {'new':'pin'})
        self.assertEqual(old, saved)
        for key in result:
            if key != 'source_files':
                self.assertEqual(result[key], old[key])
        self.assertEqual(result['source_files'], {'new':'pin'})

    def test_A2_budget_not_inherited(self):
        for key,value in (('max_parent_calls',100000), ('max_output_tokens',1024),
                          ('deadline_unix',1789596121), ('max_budget_usd',2)):
            with self.subTest(key=key):
                original = self.fixture()
                original[key] = value
                with self.assertRaises(ValueError):
                    handoff.broker_config(original, {})

    def test_other_slots_fail_closed(self):
        for key,value in (('remote_root',str(handoff.QUEUE.parent/'lane5')), ('branch','F1'), ('family','grid')):
            with self.subTest(key=key):
                original = self.fixture()
                original[key] = value
                with self.assertRaises(ValueError):
                    handoff.broker_config(original, {})

    def test_UUID_and_host_checks_are_separate(self):
        plan = dict(branch='F2', index=1, uuid=handoff.UUID, original_root=str(handoff.QUEUE))
        with patch.object(handoff.socket, 'gethostname', return_value='synthetic_node'):
            expected = handoff.hashlib.sha256(b'synthetic_node').hexdigest()
            with patch.object(handoff, 'HOST_SHA', expected):
                handoff.slot(plan)
                for key,value in (('index',5), ('uuid','wrong'), ('branch','A2'), ('original_root','wrong')):
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        handoff.slot(dict(plan, **{key:value}))
            with self.assertRaises(ValueError):
                handoff.slot(plan)


class SavedStateTests(unittest.TestCase):
    def test_successor_has_exact_contract_and_honest_segment(self):
        prior = dict(root='old', source_root='old_source', parent_models=['old_model'],
            contract=dict(initial_checkpoint={}, initial_optimizer_steps=1, inherited_counters={}, next_cycle=15,
                parent_wait_seconds=0, anchor_loss_weight=.25, optimizer_reset=False),
            bounds={'hard_end_unix':200}, prospective_capacity={'native':100,'parent':400},
            final_schedule=[{'key':'fixed'}], initial_state={'historical_flag':False}, train={'sha256':'train'})
        request = dict(source_manifest={'pin':'source'}, tests={'pin':'tests'}, predecessor_plan={'pin':'old'})
        release = dict(preserved={}, checkpoint={'saved':'adapter_adamw_rng'},
            counters={'optimizer_steps':15041,'native':1114,'parent':128}, next_cycle=44)
        with patch.object(handoff, 'ref', side_effect=lambda path: {'path':str(path),'sha256':'hash'}):
            result = handoff.successor_plan(prior, request, release, {'history':'whole'}, {'carry':'whole'})
        for key in ('bounds','prospective_capacity','final_schedule','initial_state','train'):
            self.assertEqual(result[key], prior[key])
        self.assertEqual(result['contract']['initial_checkpoint'], release['checkpoint'])
        self.assertEqual(result['contract']['initial_optimizer_steps'],15041)
        self.assertEqual(result['contract']['inherited_counters'],release['counters'])
        self.assertEqual(result['contract']['next_cycle'],44)
        self.assertEqual(result['contract']['parent_wait_seconds'],0)
        self.assertEqual(result['parent_models'],[handoff.MODEL])
        self.assertFalse(result['r139_segment']['historical_replay'])
        self.assertFalse(result['r139_segment']['optimizer_reset'])
        self.assertEqual(prior['contract']['next_cycle'],15)

    def test_exact_history_extend_and_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial = [{'source_call_path':str(root/'initial.json'),'source_call_sha256':'initial'}]
            rows = {}
            for cycle in (15,16):
                rows[cycle] = [{'source_call_path':str(root/f'{cycle}_{index}.json'),
                    'source_call_sha256':f'{cycle}_{index}'} for index in range(6)]
                handoff.write(root/f'cycle{cycle:06d}/ROWS.json',rows[cycle])
                handoff.write(root/f'cycle{cycle:06d}/sleep/COMPLETE.json',{'checkpoint':{'pin':str(cycle)}})
            handoff.write(root/'COMMITTED.json',{'checkpoint':{'pin':'16'}})
            run = SimpleNamespace(control=SimpleNamespace(checked=lambda reference:deepcopy(initial)))
            prior = dict(initial_history={},contract={'next_cycle':15})
            with patch.object(handoff,'OLD_ROOT',root), patch.object(handoff,'sha',side_effect=lambda path:Path(path).stem):
                result = handoff.history_at(run,prior,16)
            self.assertEqual(result,initial+rows[15]+rows[16])

    def test_missing_history_cycle_fails(self):
        run = SimpleNamespace(control=SimpleNamespace(checked=lambda reference:[]))
        with tempfile.TemporaryDirectory() as temporary, patch.object(handoff,'OLD_ROOT',Path(temporary)):
            with self.assertRaises(FileNotFoundError):
                handoff.history_at(run,dict(initial_history={},contract={'next_cycle':15}),16)

    def test_historical_queues_archive_only(self):
        source = inspect.getsource(handoff.build_successor)
        self.assertIn("ROOT/'historical'/folder/path.name",source)
        self.assertIn("(ROOT/folder).mkdir(exist_ok=False)",source)
        self.assertNotIn("write(ROOT/'parent_pending'",source)

    def test_final_history_walk_prevents_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first,second,third = root/'first',root/'second',root/'third'
            handoff.write(third/'PLAN.json',{'predecessor_root':str(second)})
            handoff.write(second/'PLAN.json',{'predecessor_root':str(first)})
            handoff.write(first/'PLAN.json',{})
            (first/'sealed'/'ORIGINAL_FINAL').mkdir(parents=True)
            self.assertTrue(handoff.final_seen(third,'ORIGINAL_FINAL'))
            self.assertFalse(handoff.final_seen(third,'NOT_RUN'))

    def test_final_walk_terminates_on_cycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            handoff.write(root/'PLAN.json',{'predecessor_root':str(root)})
            self.assertFalse(handoff.final_seen(root,'NOT_RUN'))


class ExecutionSeparationTests(unittest.TestCase):
    def test_release_tail_removes_only_guard_launch(self):
        source = (Path(__file__).resolve().parents[1]/'gpu/orch_math_feedback_uptake_r124_boundary.py').read_text()
        tree = ast.parse(source)
        original = ast.get_source_segment(source,next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='execute'))+'\n'
        result = handoff.release_source(original)
        ast.parse(result)
        self.assertIn("signal.pidfd_send_signal(descriptor, signal.SIGSTOP)",result)
        self.assertIn("signal.pidfd_send_signal(descriptor, signal.SIGTERM)",result)
        self.assertIn('existing_readout_finishes_without_signal',result)
        self.assertIn('no_post_boundary_charges',result)
        self.assertIn('run.build_successor(request, release)',result)
        self.assertNotIn('subprocess.Popen',result)
        self.assertIn('if paused and not released:',result)

    def test_unknown_release_source_rejected(self):
        with self.assertRaises(ValueError):
            handoff.release_source('def execute():\n    return\n')

    def test_prepare_check_do_not_call_models_or_signals(self):
        for function in (handoff.prepare,handoff.check,handoff.broker_stage,handoff.broker_check):
            with self.subTest(function=function.__name__):
                source = inspect.getsource(function)
                self.assertNotIn('pidfd_send_signal',source)
                self.assertNotIn('Popen',source)
                self.assertNotIn('.evaluate(',source)
                self.assertNotIn('.guard(',source)

    def test_original_wrapper_context_all_remote_commands(self):
        self.assertIn("BROKER_OLD/'gpu/ovx3_ssh.sh'",inspect.getsource(handoff.remote))
        self.assertIn('active.base.Store(BROKER_OLD)',inspect.getsource(handoff.broker_serve))

    def test_no_paired_probe_replay_exact_restore_used(self):
        source = inspect.getsource(handoff.run_native)
        self.assertIn('paired_probe=lambda root, plan: None',source)
        self.assertIn('run.resident.__code__',source)
        self.assertNotIn('torch.manual_seed',source)
        self.assertNotIn('max_new_tokens',source)

    def test_guard_waits_for_bound_broker(self):
        source = inspect.getsource(handoff.run_native)
        self.assertLess(source.index('prospective_broker_ready_first'),source.index('run.old.guard(ROOT)'))
        self.assertIn('single_successor_activation',source)

    def test_authorization_exact_published_bytes(self):
        valid = dict(authorized=True,publication='commit',approved_intake=handoff.DIRECTIVE,
            request_sha256='hash',source_manifest_sha256='hash')
        with patch.object(handoff,'verify_source'),patch.object(handoff,'sha',return_value='hash'):
            with patch.object(handoff,'read',return_value=valid):
                handoff.authorize()
            for key,value in (('authorized',False),('publication',''),('approved_intake','other'),('request_sha256','other'),('source_manifest_sha256','other')):
                with self.subTest(key=key),patch.object(handoff,'read',return_value=dict(valid,**{key:value})), self.assertRaises(ValueError):
                    handoff.authorize()

    def test_immutable_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'RECEIPT.json'
            handoff.write(path,{'done':True})
            with self.assertRaises(FileExistsError):
                handoff.write(path,{'done':False})
            self.assertEqual(json.loads(path.read_text()),{'done':True})


if __name__ == '__main__':
    unittest.main()
