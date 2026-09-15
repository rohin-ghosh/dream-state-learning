import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_parallel_broker as broker


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory=Path(self.temporary.name)
        self.root=broker.life.client.BRANCHES['A2']
        self.service=broker.life.service_for('A2')
        self.config_path=self.directory/'config.json'
        self.config=dict(remote_root=str(self.root),max_parent_calls=384,deadline_unix=100)
        self.config_path.write_text(json.dumps(self.config))
        self.sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
        self.release=dict(path='/synthetic/RELEASED.json',sha256='b'*64)
        self.runtime=dict(path='/synthetic/RUNTIME.json',sha256='a'*64)
        self.binding=dict(root=str(self.root),service=str(self.service),config_sha256=self.sha(self.config_path),
            runtime=self.runtime,release=self.release)
        self.binding_path=self.directory/'binding.json'
        self.binding_path.write_text(json.dumps(self.binding))
        self.records={self.runtime['path']:dict(release=self.release,
            inherited_bounds=dict(parent_calls=384,native_end_unix=100)),
            self.release['path']:dict(status='RELEASED',root=str(self.root))}
        self.hashes={self.runtime['path']:'a'*64,self.release['path']:'b'*64,
            str(self.root/'parent_claude/CONFIG.json'):self.sha(self.config_path)}
        self.copies={}
        self.exist_checks=[]
        self.lock_result=0
        fixture=self
        class Store:
            def __init__(self, root):
                self.root=root
            def hash(self,path):
                if str(path) in fixture.copies:
                    return hashlib.sha256(fixture.copies[str(path)]).hexdigest()
                return fixture.hashes[str(path)]
            def shell(self,script,check=True):
                if script.startswith('cat '):
                    return SimpleNamespace(stdout=json.dumps(fixture.records[script[4:]]),returncode=0)
                return SimpleNamespace(stdout='',returncode=fixture.lock_result)
            def exists(self,path):
                fixture.exist_checks.append(str(path))
                return str(path) in fixture.copies
            def copy(self,path,destination):
                fixture.copies[destination.removeprefix('NODE:')]=Path(path).read_bytes()
        self.base=SimpleNamespace(__name__='synthetic_broker',loads=json.loads,validate_config=Mock(),
            sha=self.sha,ROOT=self.directory,Store=Store,
            write=lambda path,value:Path(path).write_text(json.dumps(value)))
        for manager in (patch.object(broker,'base',self.base),patch.dict(os.environ,CUDA_VISIBLE_DEVICES='')):
            manager.start()
            self.addCleanup(manager.stop)

    def namespace(self):
        return broker.namespace(self.config_path,self.binding_path)

    def test_old_frozen_transport_without_NodeLocalStore_supported(self):
        values=self.namespace()
        self.assertNotIn('NodeLocalStore',values)
        self.assertIs(values['evaluate'],broker.delivery.astra_evaluate)

    def test_exact_own_terminal_mapping_only(self):
        store=self.namespace()['Store'](self.directory)
        for name in ('TERMINAL.json','SHARED_TERMINAL.json','OTHER.json'):
            store.exists(self.root/name)
        self.assertEqual(self.exist_checks,[str(self.service/'GUARD_TERMINAL.json')]*2+[str(self.root/'OTHER.json')])

    def test_active_ledger_config_not_stale_historical_config(self):
        self.hashes[str(self.root/'parent_claude/CONFIG.json')]='wrong'
        with self.assertRaisesRegex(ValueError,'actual_active_A2_ledger_config'):
            self.namespace()

    def test_actual_successful_lock_publishes_hashed_node_ready(self):
        store=self.namespace()['Store'](self.directory)
        with patch.object(broker.life,'identity',return_value=dict(pid=123)):
            store.shell('mkdir '+str(self.root/'parent_claude/RUNNER.lock'),check=False)
        ready=json.loads(self.copies[str(self.service/'BROKER_READY.json')])
        self.assertTrue(ready['actual_single_lane_lock_acquired'])
        self.assertEqual(ready['runtime'],self.runtime)
        self.assertEqual(ready['terminal_path'],str(self.service/'GUARD_TERMINAL.json'))

    def test_failed_lock_does_not_publish_ready(self):
        self.lock_result=1
        self.namespace()['Store'](self.directory).shell('mkdir '+str(self.root/'parent_claude/RUNNER.lock'),check=False)
        self.assertEqual(self.copies,{})

    def test_unbound_runtime_hash_fails_before_lock(self):
        self.hashes[self.runtime['path']]='wrong'
        with self.assertRaisesRegex(ValueError,'actual_node_runtime_hash'):
            self.namespace()


if __name__=='__main__':
    unittest.main()
