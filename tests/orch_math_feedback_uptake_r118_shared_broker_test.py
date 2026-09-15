from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_shared_broker as broker


class SharedBrokerTests(unittest.TestCase):
    def test_only_exact_A2_terminal_is_redirected(self):
        self.assertEqual(broker.terminal_path(broker.LANE/'TERMINAL.json'),broker.LANE/'SHARED_TERMINAL.json')
        for path in (broker.LANE/'parent_queue/x.response.json',broker.LANE.parent/'lane1/TERMINAL.json',
                broker.LANE/'SHARED_TERMINAL.json'):
            self.assertEqual(broker.terminal_path(path),path)

    def test_missing_activation_prevents_serve(self):
        with tempfile.TemporaryDirectory() as folder:
            binding=Path(folder)/'binding.json'
            binding.write_text('{}')
            with patch.object(broker,'validate_binding',side_effect=ValueError('missing activation')), \
                    patch.object(broker.shared,'serve') as serve:
                with self.assertRaisesRegex(ValueError,'missing activation'):
                    broker.serve('config','launch','prompts','principles',binding)
            serve.assert_not_called()

    def test_new_process_store_maps_terminal_preserves_delivery_and_restores(self):
        with tempfile.TemporaryDirectory() as folder:
            binding=Path(folder)/'binding.json'
            binding.write_text('{}')
            queried=[]
            class Store:
                def __init__(self,*args):pass
                def exists(self,path):
                    queried.append(path)
                    return False
            def serve(*args):
                broker.shared.Store().exists(broker.LANE/'TERMINAL.json')
                self.assertIs(broker.shared.evaluate,broker.delivery.astra_evaluate)
                self.assertEqual(args,('config','launch','prompts','principles'))
            with patch.object(broker,'validate_binding'),patch.object(broker.shared,'Store',Store), \
                    patch.object(broker.shared,'serve',side_effect=serve):
                broker.serve('config','launch','prompts','principles',binding)
                self.assertIs(broker.shared.Store,Store)
            self.assertEqual(queried,[broker.LANE/'SHARED_TERMINAL.json'])

    def test_validate_requires_actual_native_activation_and_same_caps(self):
        with tempfile.TemporaryDirectory() as folder:
            config_path=Path(folder)/'config.json'
            config=dict(remote_root=str(broker.LANE),deadline_unix=500,max_parent_calls=384)
            config_path.write_text(json.dumps(config))
            config_sha=broker.shared.sha(config_path)
            refs={key:dict(path=str(broker.LANE/name),sha256=key+'_sha') for key,name in (
                ('release','shared_handoff_r118/release/RELEASED.json'),('activation','SHARED_ACTIVATION.json'),
                ('ready','SHARED_CLIENT_READY.json'))}
            documents={'release':dict(status='RELEASED',root=str(broker.LANE)),
                'activation':dict(release=refs['release'],ready_sha256=refs['ready']['sha256'],
                    shared_learner={'branch':'A2'},inherited_bounds={'native_end_unix':500,'parent_calls':384}),
                'ready':dict(command_module='gpu.orch_math_feedback_uptake_r118_shared_run')}
            hashes={value['path']:value['sha256'] for value in refs.values()}
            hashes[str(broker.LANE/'parent_claude/CONFIG.json')]=config_sha
            store=Mock()
            store.hash.side_effect=lambda path:hashes[str(path)]
            store.shell.side_effect=lambda command:SimpleNamespace(stdout=json.dumps(documents[
                next(key for key,value in refs.items() if value['path'] in command)]))
            source_files={name:'source_sha' for name in ('gpu/orch_math_feedback_uptake_r118_shared_broker.py',
                'gpu/orch_math_feedback_uptake_r118_broker.py','gpu/orch_r118_astra_slots.py')}
            binding=dict(root=str(broker.LANE),config_sha256=config_sha,prior_broker_identity={'pid':999999999},
                source_files=source_files,drain_verified=True,charged_retries=0,**refs)
            original_sha=broker.shared.sha
            with patch.object(broker.shared,'validate_config'),patch.object(broker.shared,'sha',side_effect=
                    lambda path:original_sha(path) if Path(path)==config_path else 'source_sha'):
                self.assertEqual(broker.validate_binding(store,config_path,binding),config)
                documents['activation']['inherited_bounds']['parent_calls']=385
                with self.assertRaisesRegex(ValueError,'original_bounds'):
                    broker.validate_binding(store,config_path,binding)


if __name__=='__main__':unittest.main()
