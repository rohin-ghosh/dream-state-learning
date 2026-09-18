import ast
from copy import deepcopy
import importlib.util
import inspect
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def load(name, environment, default):
    path = Path(os.environ.get(environment,default))
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPO = Path(__file__).resolve().parents[1]
repair = load('repair','R139_REPAIR_FILE',REPO/'gpu/orch_r139_route_resume_repair.py')
original = load('original','R139_OLD_HANDOFF',REPO/'gpu/orch_r139_route_astra_handoff.py')


class MetadataTests(unittest.TestCase):
    def fixture(self):
        messages = [{'role':'user','content':'synthetic_initial_context'}]
        return dict(terminal_reason='generation_failure',actor_calls=1,reads=[],routes=[],current='start',
            task={'node':'start'},messages=messages,captures=[dict(turn=0,response=None,command=None,
                prior_reads=[],messages=deepcopy(messages),error=dict(type='TimeoutError',message='owned_lifetime_signal'))])

    def test_exact_uncharged_signal_capture(self):
        repair.metadata_contract(self.fixture(),[dict(kind='NATIVE',cycle=55,sleep=55)])

    def test_future_native_parent_or_readout_charge_fails(self):
        for row in (dict(kind='NATIVE',cycle=56),dict(kind='PARENT',cycle=56),dict(kind='NATIVE',sleep=56)):
            with self.subTest(row=row),self.assertRaisesRegex(ValueError,'no_charged'):
                repair.metadata_contract(self.fixture(),[row])

    def test_any_actual_response_fails(self):
        for response in ({},{'raw':'synthetic'},''):
            episode = self.fixture()
            episode['captures'][0]['response'] = response
            with self.subTest(response=response),self.assertRaises(ValueError):
                repair.metadata_contract(episode,[])

    def test_environment_action_fails(self):
        for key in ('reads','routes'):
            episode = self.fixture()
            episode[key] = ['executed']
            with self.subTest(key=key),self.assertRaises(ValueError):
                repair.metadata_contract(episode,[])

    def test_other_failure_not_adoptable(self):
        for error in ({'type':'ValueError','message':'x'},{'type':'TimeoutError','message':'provider_timeout'}):
            episode = self.fixture()
            episode['captures'][0]['error'] = error
            with self.subTest(error=error),self.assertRaises(ValueError):
                repair.metadata_contract(episode,[])

    def test_second_attempt_capture_not_adoptable(self):
        episode = self.fixture()
        episode['captures'].append(deepcopy(episode['captures'][0]))
        with self.assertRaises(ValueError):repair.metadata_contract(episode,[])

    def test_changed_context_not_adoptable(self):
        episode = self.fixture()
        episode['messages'] = []
        with self.assertRaises(ValueError):repair.metadata_contract(episode,[])

    def test_only_exact_two_metadata_files_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root/'cycle_0056'
            for name in repair.METADATA:repair.write(output/name,{})
            pins = {name:repair.sha(output/name) for name in repair.METADATA}
            plan = {'adopt_start':repair.ref(output/'START.json')}
            with patch.object(repair,'ROOT',root),patch.object(repair,'METADATA',pins):
                self.assertTrue(repair.adoptable_start(output,plan))
                repair.write(output/'CALL_000001.json',{})
                self.assertFalse(repair.adoptable_start(output,plan))

    def test_changed_metadata_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root/'cycle_0056'
            for name in repair.METADATA:repair.write(output/name,{})
            pins = {name:repair.sha(output/name) for name in repair.METADATA}
            plan = {'adopt_start':repair.ref(output/'START.json')}
            (output/'EPISODE_0.json').write_text('{"changed":true}')
            with patch.object(repair,'ROOT',root),patch.object(repair,'METADATA',pins):
                self.assertFalse(repair.adoptable_start(output,plan))

    def test_fresh_episode_uses_new_path_old_metadata_survives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root/'cycle_0056'
            repair.write(output/'EPISODE_0.json',{'old':'signal_metadata'})
            old = repair.sha(output/'EPISODE_0.json')
            with patch.object(repair,'ROOT',root),patch.object(repair,'METADATA',{'EPISODE_0.json':old}):
                self.assertEqual(repair.episode_path(output,0),output/'EPISODE_0_R139B.json')
                self.assertEqual(repair.episode_path(output,1),output/'EPISODE_1.json')
                self.assertEqual(repair.episode_path(root/'cycle_0057',0),root/'cycle_0057/EPISODE_0.json')
                self.assertEqual(repair.sha(output/'EPISODE_0.json'),old)


class ResumeTests(unittest.TestCase):
    def source(self):
        path = Path(os.environ.get('R139_NATIVE_SOURCE',REPO/'gpu/orch_r121_route_independent.py'))
        source = path.read_text()
        node = next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='run')
        return ast.get_source_segment(source,node)

    def test_exact_source_patch_compiles_new_readiness_only(self):
        result = repair.repair_run(self.source(),original.resume_source)
        compile(result,'<test_saved_resume>','exec')
        self.assertEqual(result.count('R139B_INDEPENDENT_ACTOR_READY.json'),2)
        self.assertNotIn('R139_INDEPENDENT_ACTOR_READY.json',result)
        self.assertNotIn('R121_INDEPENDENT_ACTOR_READY.json',result)
        self.assertEqual(result.count('episode_path(output, episode_index)'),2)

    def test_exact_optimizer_rng_context_and_history_retained(self):
        result = repair.repair_run(self.source(),original.resume_source)
        for text in ("optimizer.load_state_dict(state['optimizer'])","engine.torch.set_rng_state(state['cpu_rng'])",
                     "engine.torch.cuda.set_rng_state_all(state['cuda_rng'])",'history.extend(rows)',
                     "read(root/'OWN_CARRY.json')['reflection']","deepcopy(plan['restored_context']['parent_history'])",
                     "deepcopy(plan['restored_context']['head_settings'])"):
            self.assertIn(text,result)

    def test_write_and_obstacle_reference_same_replacement(self):
        result = repair.repair_run(self.source(),original.resume_source)
        self.assertIn('write(episode_path(output, episode_index), record)',result)
        self.assertIn('episode_path=str(episode_path(output, episode_index))',result)

    def test_resume_namespace_binds_path_helper(self):
        source = repair.repair_resume(inspect.getsource(original.resume))
        compile(source,'<test_resume_namespace>','exec')
        self.assertIn('episode_path=episode_path',source)

    def test_source_drift_fails_closed(self):
        with self.assertRaises(ValueError):repair.repair_run('bad_source',lambda text:text)
        with self.assertRaises(ValueError):repair.repair_resume('bad_source')

    def test_no_signals_and_no_prepare_launch(self):
        source = inspect.getsource(repair)
        self.assertNotIn('pidfd_send_signal',source)
        self.assertNotIn('os.kill(',source)
        self.assertNotIn('subprocess.Popen',inspect.getsource(repair.prepare))

    def test_supervisor_launches_new_script_not_attempt2(self):
        source = inspect.getsource(repair.supervise)
        self.assertIn('__file__=__file__',source)
        self.assertIn("release=lambda stage:dict(status='RELEASED'",source)
        self.assertIn('authorize(STAGE)',source)

    def test_no_metadata_replay_claim(self):
        source = inspect.getsource(repair.prepare)
        self.assertIn('no_charged_call_replayed=True',source)
        self.assertIn('new_signals=0',source)


if __name__=='__main__':
    unittest.main()
