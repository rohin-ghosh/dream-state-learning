import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prep_common as common
import r172_runner as runner
import r172_scheduler as scheduler
import design
from gpu import orch_r130_checkpoint_benchmark as native
from gpu import orch_r130_benchmark_sidecar as sidecar


class ReceivingVerifierTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.clock = patch.object(common.time, 'time', return_value=common.END-12000)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def fixture(self, adapter_cap=1000):
        capture = self.root / 'capture'
        files = {}
        for name, raw in {'adapter_model.safetensors':b'synthetic adapter', 'adapter_config.json':b'{}'}.items():
            files[name] = common.write(capture/'adapter'/name, raw)['sha256']
        commit = dict(schema=native.NATIVE_SCHEMA, base_sha256=native.BASE_SHA256,
            adapter_state_sha256='a'*64, adapter_files=files,
            checkpoint_sha256=dict(adapter=native.digest(files)))
        reference = common.write(capture/'COMMIT.original.json',commit)
        manifest = dict(schema=native.MANIFEST_SCHEMA,adapter_path='adapter',
            commit_path='COMMIT.original.json',commit_sha256=reference['sha256'])
        ledger = common.Ledger(self.root/'ledger',dict(metadata=10000,adapter=adapter_cap,
            per_life=10000,discovery=0),['life'])
        return capture,manifest,ledger

    def test_unchanged_verifier_returns_full_generator_checkpoint(self):
        capture,manifest,ledger = self.fixture()
        result = runner.verified_checkpoint(manifest,capture,ledger,'life','cpu1')
        self.assertEqual(result['adapter_state_sha256'],'a'*64)
        self.assertEqual(result['base_sha256'],native.BASE_SHA256)
        self.assertEqual(set(result['adapter_files']),{'adapter_config.json','adapter_model.safetensors'})
        self.assertEqual(ledger.totals()['adapter'],len(b'synthetic adapter{}'))
        self.assertGreater(ledger.totals()['metadata'],0)

    def test_changed_adapter_rejected_and_failed_read_charged(self):
        capture,manifest,ledger = self.fixture()
        (capture/'adapter/adapter_model.safetensors').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'native_adapter_file_binding'):
            runner.verified_checkpoint(manifest,capture,ledger,'life','cpu1')
        self.assertEqual(ledger.totals()['adapter'],len(b'changed{}'))
        with self.assertRaisesRegex(ValueError,'consumed'):
            runner.verified_checkpoint(manifest,capture,ledger,'life','cpu1')

    def test_adapter_budget_refusal_prevents_native_verifier_reads(self):
        capture,manifest,ledger = self.fixture(adapter_cap=1)
        with patch.object(native,'verify_checkpoint',side_effect=AssertionError('unpaid verifier read')):
            with self.assertRaisesRegex(ValueError,'aggregate_read_budget'):
                runner.verified_checkpoint(manifest,capture,ledger,'life','cpu1')

    def test_manifest_cannot_redirect_adapter_reads(self):
        capture,manifest,ledger = self.fixture()
        with self.assertRaisesRegex(ValueError,'manifest_paths'):
            runner.verified_checkpoint(dict(manifest,adapter_path='../other'),capture,ledger,'life','cpu1')
        self.assertEqual(ledger.totals()['metadata'],0)

    def test_incomplete_model_closure_cannot_be_frozen(self):
        with self.assertRaisesRegex(ValueError,'complete_frozen_generator_source_closure'):
            runner.verify_source_closure(self.root,dict(files={'r172_runner.py':'a'*64}))

    def test_exact_lease_uuid_list_and_dictionary(self):
        self.assertEqual(runner.device_uuid(dict(uuid_by_index=['first','second']),1),'second')
        self.assertEqual(runner.device_uuid(dict(uuid_by_index={'0':'first','1':'second'}),0),'first')

    def test_preparation_scope_cannot_authorize_execution(self):
        reference = common.write(self.root/'preparation.json',dict(gpu_execution_authorized_now=False))
        with self.assertRaisesRegex(ValueError,'preparation_scope_is_not_execution_GO'):
            runner.validate_go(reference['path'],{}, {}, {})

    def test_foreign_host_is_not_a_self_consistent_device_admission(self):
        config=dict(physical=0,gpu_uuid=sidecar.DEVICES[0])
        lease=dict(node='ovx',uuid_by_index=[sidecar.DEVICES[0],sidecar.DEVICES[1]],
            lease_end_unix=common.END+21600,hard_deadline_unix=common.END)
        with patch.object(runner.socket,'gethostname',return_value='synthetic-other-host'):
            with self.assertRaisesRegex(ValueError,'node2_devices_only'):
                runner.validate_receiver_identity(config,lease)

    def reservation(self,condition='LORA_ON',sleep=11,capture_hash='a'*64):
        return dict(life_id='life',sleep=sleep,condition=condition,
            physical=0 if condition=='LORA_ON' else 1,pipeline=dict(path='synthetic',sha256='a'*64),
            capture=dict(path='synthetic-capture',sha256=capture_hash),execution_ref=dict(path='synthetic',sha256='b'*64))

    def test_different_companion_capture_rejected_before_second_charge(self):
        runner.reserve(self.root,self.reservation(),common.END+21600,common.END-12000)
        with self.assertRaisesRegex(ValueError,'paired_conditions_exact_same_capture'):
            runner.reserve(self.root,self.reservation('LORA_OFF',capture_hash='b'*64),common.END+21600,common.END-11990)
        self.assertEqual(len(list((self.root/'ledger').glob('*.RESERVED.json'))),1)

    def test_same_companion_capture_allowed_without_retry(self):
        runner.reserve(self.root,self.reservation(),common.END+21600,common.END-12000)
        runner.reserve(self.root,self.reservation('LORA_OFF'),common.END+21600,common.END-11990)
        with self.assertRaisesRegex(ValueError,'once_only'):
            runner.reserve(self.root,self.reservation(),common.END+21600,common.END-11980)

    def test_scheduler_and_design_choose_oldest_per_life_not_arrival(self):
        for sleep,ready in ((11,20),(12,10)):
            common.write(self.root/'receiving_transfers'/f'life_{sleep:06d}'/'COMPLETE.json',
                dict(life_id='life',sleep=sleep,observed_unix=ready,capture=dict(path='synthetic',sha256='a'*64)))
        self.assertEqual(scheduler.candidates(self.root,'LORA_ON')[0]['sleep'],11)
        cells=[dict(life_id='life',sleep=sleep,condition='LORA_ON',ready=True,ready_unix=ready,key=str(sleep))
            for sleep,ready in ((11,20),(12,10))]
        self.assertEqual(design.choose_ready(cells,set(),{},'LORA_ON')['sleep'],11)

    def test_missing_earlier_receipt_is_not_a_fleet_barrier(self):
        common.write(self.root/'receiving_transfers/life_000012/COMPLETE.json',
            dict(life_id='life',sleep=12,observed_unix=10,capture=dict(path='synthetic',sha256='a'*64)))
        self.assertEqual(scheduler.candidates(self.root,'LORA_ON')[0]['sleep'],12)

    def test_custody_held_life_does_not_block_eligible_peer(self):
        for name in ('held','eligible'):
            common.write(self.root/f'receiving_transfers/{name}_000011/COMPLETE.json',
                dict(life_id=name,sleep=11,observed_unix=10,capture=dict(path='synthetic',sha256='a'*64)))
        for filename in ('REGISTERED.json','TRAIN_FREEZE.json'):
            common.write(self.root/'lives/eligible'/filename,dict(synthetic=True))
        common.write(self.root/'receiving_allowances/eligible_000011.json',dict(synthetic=True))
        rows=scheduler.candidates(self.root,'LORA_ON',ready=lambda cell:scheduler.preparation_ready(self.root,cell))
        self.assertEqual([row['life_id'] for row in rows],['eligible'])
        self.assertFalse((self.root/'scheduler_once').exists())

    def test_receiver_lease_array_through_scheduler_configuration(self):
        lease=common.write(self.root/'lease.json',dict(uuid_by_index=[sidecar.DEVICES[0],sidecar.DEVICES[1]]))
        for filename in ('REGISTERED.json','TRAIN_FREEZE.json'):
            common.write(self.root/'lives/life'/filename,dict(synthetic=True))
        common.write(self.root/'receiving_allowances/life_000011.json',dict(synthetic=True))
        cell=dict(life_id='life',sleep=11,condition='LORA_OFF',capture={},transfer={},baseline_authority=None)
        config=scheduler.configuration(dict(lease=lease),cell,1,self.root)
        self.assertEqual(config['gpu_uuid'],sidecar.DEVICES[1])
        self.assertEqual(config['physical'],1)

    def test_complete_source_fixture_and_added_unpinned_python(self):
        required=set(native.REQUIRED_SOURCES)|{'r172_runner.py','r172_scheduler.py','prep_common.py',
            'gpu/orch_r167_fleet_eval.py','gpu/orch_r167_object_probe_queue.py',
            'gpu/orch_r167_object_survival_eval.py','gpu/orch_r130_benchmark_sidecar.py',
            'gpu/orch_rich_hot_node2_scan.py','tests/test_orch_r167_fleet_eval.py','test_runner_preparation.py'}
        files={name:common.write(self.root/name,b'pass\n')['sha256'] for name in required}
        runner.verify_source_closure(self.root,dict(files=files))
        common.write(self.root/'gpu/extra_unpinned.py',b'pass\n')
        with self.assertRaisesRegex(ValueError,'complete_python_source_closure'):
            runner.verify_source_closure(self.root,dict(files=files))

    def allowance_fixture(self):
        reservations={}
        for kind in ('metadata','adapter'):
            copied=common.write(self.root/f'control/global_reservations/{kind}.json',dict(
                status='CHARGED_BEFORE_IO_NO_REFUND',kind=kind,life_id='life',bytes=1000,failures_charged=True))
            reservations[kind]=dict(original=dict(path=f'/synthetic-original/{kind}.json',sha256=copied['sha256']),receiving_copy=copied)
        capture=dict(path='synthetic-capture',sha256='a'*64)
        document=dict(status='GLOBAL_PRECHARGED_RECEIVING_ALLOWANCE',life_id='life',capture=capture,
            proposal_sha256=common.PROPOSAL_SHA,allowance_id='b'*64,metadata_bytes=1000,adapter_bytes=1000,
            global_reservations=reservations)
        reference=common.write(self.root/'allowance.json',document)
        return dict(life_id='life',capture=capture,receiving_read_allowance=reference),document

    def test_receiver_uses_same_byte_reservation_without_origin_path_rewrite(self):
        config,document=self.allowance_fixture()
        with patch.object(runner,'ROOT',self.root):
            allowance,ledger=runner.receiving_allowance(config)
        self.assertEqual(allowance['adapter_bytes'],1000)
        self.assertEqual(ledger.totals()['adapter'],0)

    def test_forged_copy_hash_cannot_expand_receiver_allowance(self):
        config,document=self.allowance_fixture()
        document['global_reservations']['adapter']['original']['sha256']='c'*64
        config['receiving_read_allowance']=common.write(self.root/'changed_allowance.json',document)
        with patch.object(runner,'ROOT',self.root):
            with self.assertRaisesRegex(ValueError,'same_byte_global_reservation_copy'):
                runner.receiving_allowance(config)


if __name__ == '__main__':
    unittest.main()
