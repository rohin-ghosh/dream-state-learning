from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r157_community_wall_extension as extension


class CommunityWallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        base = patch.object(extension, 'BASE', self.root)
        base.start(); self.addCleanup(base.stop)
        clock = patch.object(extension.time, 'time', return_value=extension.OLD_WALL - 3600)
        clock.start(); self.addCleanup(clock.stop)
        self.source = self.root / 'old_source'
        (self.source / 'gpu').mkdir(parents=True)
        (self.source / 'tests').mkdir()
        (self.source / 'gpu/__init__.py').write_text('')
        (self.source / 'tests/__init__.py').write_text('')
        (self.source / 'gpu/native.py').write_text('original_native = True\n')
        (self.source / 'startup.json').write_text('{}')
        self.life = self.root / 'orch_r153_community_C1_20260916_attempt1/life'
        (self.life / 'stream/records').mkdir(parents=True)
        (self.life / 'stream/inbox').mkdir()
        physical, gpu_uuid, pid, ticks = extension.TARGETS['C1']
        self.plan = dict(root=str(self.life), source_root=str(self.source), hard_end_unix=extension.OLD_WALL,
            lease_end_unix=extension.OLD_WALL + 600, physical=physical, gpu_uuid=gpu_uuid,
            seed=15301, context_limit=16384, segment_tokens=512, segments_per_sleep=3,
            presentation_version='unchanged', system_prompt='system', birth_prompt='birth',
            readout_revision=3, learning_rate=0.00003, model_dir='/same/model', anchors='/same/anchors')
        self.plan_path = self.write('OLD_PLAN.json', self.plan)
        self.config = dict(schema='R125_CONTINUAL_GUARD_V1', plan_path=str(self.plan_path),
            plan_sha256=extension.sha(self.plan_path), hard_end_unix=extension.OLD_WALL,
            next_reserved_unix=extension.OLD_WALL+600, host_sha256=extension.hashlib.sha256(extension.HOST.encode()).hexdigest(),
            device_containment=dict(uid=2524, gid=2524, minor=0, unit='orch-r153-native-'+'a'*32),
            resume=False, lease_path=str(self.write('OLD_LEASE.json', dict(hard_end_unix=extension.OLD_WALL,
            lease_end_unix=extension.OLD_WALL+600))), allocation_path='/old/allocation', attempt_dir='/old/attempt',
            source_pins=extension.files(self.source), r153_agent={'old': 'birth'})
        self.config['lease_sha256'] = extension.sha(self.config['lease_path'])
        self.config_path = self.write('OLD_GUARD.json', self.config)
        auth = dict(schema='R157_EXPLICIT_TEAM_NODE_RUNTIME_AUTHORIZATION_V1',host=extension.HOST,
            lives=list(extension.TARGETS), authorization_is_runtime_budget_not_provider_booking=True,
            provider_reservation_expiry_verified=False, must_abort_on_conflicting_real_reservation=True,
            purchase_or_lease_transaction_authorized=False, reset=False,learning_recipe_change=False,
            visibility_change=False,new_hard_end_utc='2026-09-19T00:00:00+00:00',
            runtime_resource_ceiling_utc='2026-09-19T00:10:00+00:00',safety_margin_seconds=600)
        self.auth = self.write('AUTH.json',auth)
        auth_sha = patch.object(extension, 'AUTH_SHA', extension.sha(self.auth))
        auth_sha.start(); self.addCleanup(auth_sha.stop)
        self.provenance = self.write('PROVENANCE.json',dict(schema='R157_NODE5_TARGETED_RESERVATION_AUDIT_V1',
            host=extension.HOST, authorization_sha256=extension.AUTH_SHA,conflicting_real_reservation_found=False,
            numeric_cutoff_is_not_booking=True,actual_reservation_receipts=[]))
        self.cpu = self.write('CPU.json',dict(passed=True,returncode=0,tests=99,
            helper_sha256=extension.sha(Path(extension.__file__).absolute()),tests_sha256=extension.sha(Path(__file__).absolute())))
        self.output = self.root/'orch_r157_community_C1_fixture'
        self.pair = dict(actor=dict(pid=pid,start_ticks=ticks),timer=dict(pid=100),supervisor=dict(pid=99))

    def write(self,name,value):
        path=self.root/name
        path.write_text(json.dumps(value,sort_keys=True))
        return path

    def stage(self):
        with (patch.object(extension.socket,'gethostname',return_value=extension.HOST),
              patch.object(extension.os,'getuid',return_value=2524),
              patch.dict(os.environ,CUDA_VISIBLE_DEVICES=''),
              patch.object(extension,'original_validate',return_value=(self.config,self.plan)),
              patch.object(extension,'process_pair',return_value=self.pair)):
            return extension.stage('C1',self.config_path,self.auth,self.provenance,self.cpu,self.output)

    def boundary(self, **changes):
        state=dict(deadline_unix=extension.OLD_WALL,pending=None,rows=[{'retained':True}],
                   sleep_frontier=1,sleep_receipts=[{'status':'COMPLETE'}])
        state.update(changes)
        document=dict(status='COMPLETE',cycle=1,resume_state=dict(state=state,sha256=extension.digest(state)))
        manifest=dict(schema='R125_STREAM_JOURNAL_V1',journal_id='fixture')
        self.write(str(self.life/'stream/JOURNAL.json'),manifest)
        record=dict(schema=manifest['schema'],journal_id='fixture',index=0,kind='SLEEP_COMPLETE',
                    previous_sha256=extension.digest(manifest),document=document)
        record['sha256']=extension.digest(record)
        path=self.life/'stream/records/00000000000000000000.json'
        path.write_text(json.dumps(record,sort_keys=True))
        intent=dict(index=0,record_sha256=record['sha256'],previous_sha256=record['previous_sha256'])
        path.with_name(path.stem+'.intent.json').write_text(json.dumps(intent))
        return extension.saved_boundary(self.life)

    def control(self):
        self.stage()
        request=extension.read(self.output/'REQUEST.json')
        boundary=self.boundary()
        path=extension.build_control(self.output,request,self.config,self.plan,boundary)
        return path,extension.read(path),extension.read(path.parent/'PLAN.json')

    def validate(self, path, config, plan):
        fake=SimpleNamespace(validate=Mock(return_value=(config,plan)))
        with patch.dict('sys.modules',{'gpu.orch_r125_continual_guard':fake}):
            result=extension.validate_resume(path)
        fake.validate.assert_called_once_with(path)
        return result

    def test_exact_runtime_authorization_not_booking(self):
        self.assertFalse(extension.authorization(self.auth,self.provenance)['provider_reservation_expiry_verified'])

    def test_authorization_bytes_changed_rejected(self):
        self.auth.write_text('{}')
        with self.assertRaisesRegex(ValueError,'exact_shared_R157'):
            extension.authorization(self.auth,self.provenance)

    def test_known_reservation_conflict_rejected(self):
        proof=extension.read(self.provenance)
        proof['conflicting_real_reservation_found']=True
        self.provenance.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError,'no_known_real_reservation_conflict'):
            extension.authorization(self.auth,self.provenance)

    def test_bound_real_reservation_earlier_than_ceiling_rejected(self):
        reservation=self.write('RESERVATION.json',dict(host=extension.HOST,reservation_end_unix=extension.NEW_WALL))
        proof=extension.read(self.provenance)
        proof['actual_reservation_receipts']=[extension.reference(reservation)]
        self.provenance.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError,'actual_reservation_must_cover'):
            extension.authorization(self.auth,self.provenance)

    def test_booking_not_required_to_honor_exact_runtime_authority(self):
        self.assertEqual(extension.read(self.provenance)['actual_reservation_receipts'],[])
        extension.authorization(self.auth,self.provenance)

    def test_all_five_exact_slots_supported(self):
        for agent,(physical,gpu_uuid,unused_pid,unused_ticks) in extension.TARGETS.items():
            with self.subTest(agent=agent):
                plan=dict(self.plan,root=str(self.root/('orch_r153_community_'+agent+'_20260916_attempt1')/'life'),
                          physical=physical,gpu_uuid=gpu_uuid)
                config=deepcopy(self.config);config['device_containment']['minor']=physical
                extension.scope(agent,config,plan)

    def test_protected_lives_never_owned(self):
        for agent in ('run1','R127','repo_reader','C6'):
            with self.subTest(agent=agent),self.assertRaisesRegex(ValueError,'only_C1_C5'):
                extension.scope(agent,self.config,self.plan)

    def test_mismatched_slot_UUID_or_root_rejected(self):
        for change in ({'physical':2},{'gpu_uuid':extension.TARGETS['C2'][1]},{'root':'/foreign'}):
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'exact_original_community_life'):
                extension.scope('C1',self.config,dict(self.plan,**change))

    def test_second_handoff_old_resume_rejected(self):
        with self.assertRaisesRegex(ValueError,'original_birth_one'):
            extension.scope('C1',dict(self.config,resume=True),self.plan)

    def test_scope_rejects_other_original_wall(self):
        with self.assertRaises(ValueError):
            extension.scope('C1',self.config,dict(self.plan,hard_end_unix=extension.OLD_WALL+1))

    def test_stage_preserves_old_sources_and_adds_only_helper_tests(self):
        before=extension.files(self.source)
        with patch.object(extension.signal,'pidfd_send_signal') as sending:
            result=self.stage()
        sending.assert_not_called()
        self.assertEqual(result['status'],'STAGED_NOT_SIGNALED')
        self.assertEqual(extension.files(self.source),before)
        copied=extension.files(self.output/'source')
        self.assertEqual(set(copied)-set(before),{extension.RELATIVE,extension.TEST_RELATIVE})
        self.assertEqual((self.output/'source').stat().st_mode&0o777,0o555)
        self.assertTrue(all(copied[key]==value for key,value in before.items()))

    def test_stage_never_overwrites(self):
        self.stage()
        with self.assertRaisesRegex(ValueError,'new_own_control'):
            self.stage()

    def test_stage_bad_CPU_proof_rejected_without_output(self):
        cpu=extension.read(self.cpu);cpu['passed']=False;self.cpu.write_text(json.dumps(cpu))
        with self.assertRaisesRegex(ValueError,'bound_actual_CPU'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_boundary_full_saved_state_only(self):
        boundary=self.boundary()
        self.assertEqual(boundary['cycle'],1)
        self.assertEqual(boundary['state_sha256'],extension.digest(boundary['record']['document']['resume_state']['state']))

    def test_incomplete_boundary_rejected(self):
        for change in ({'pending':'sleep:pending'},{'sleep_frontier':0},{'sleep_receipts':[{'status':'FAILED'}]}):
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'full_saved_quiescent'):
                self.boundary(**change)

    def test_boundary_hash_tamper_rejected(self):
        boundary=self.boundary();record=boundary['record'];record['document']['cycle']=2
        Path(boundary['reference']['path']).write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'boundary_hash'):
            extension.saved_boundary(self.life)

    def test_non_saved_tail_waits_without_rollback(self):
        self.boundary()
        (self.life/'stream/records/00000000000000000001.json').write_text(json.dumps(dict(kind='UPDATE')))
        self.assertIsNone(extension.saved_boundary(self.life))

    def test_deadline_only_plan_preserves_every_other_field(self):
        before=deepcopy(self.plan);boundary=self.boundary()
        proposed=extension.proposed_plan(self.plan,self.root/'new_source',boundary)
        extension.check_plan_delta(self.plan,proposed)
        self.assertEqual(before,self.plan)
        self.assertEqual(proposed['root'],self.plan['root'])
        self.assertEqual(proposed['authorized_wall_extension']['previous_stream_sha256'],boundary['state_sha256'])

    def test_recipe_seed_visibility_changes_rejected(self):
        proposed=extension.proposed_plan(self.plan,self.root/'new_source',self.boundary())
        for change in ({'seed':3},{'context_limit':32768},{'learning_rate':0.001},{'birth_prompt':'changed'},
                       {'root':'/newbirth'},{'readout_revision':1},{'segment_tokens':1024}):
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'all_learning_visibility'):
                extension.check_plan_delta(self.plan,dict(proposed,**change))

    def test_new_wall_or_ceiling_drift_rejected(self):
        proposed=extension.proposed_plan(self.plan,self.root/'new_source',self.boundary())
        for change in ({'hard_end_unix':extension.NEW_WALL+1},{'lease_end_unix':extension.CEILING+1}):
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'exact_deadline_only'):
                extension.check_plan_delta(self.plan,dict(proposed,**change))

    def test_startup_path_relocated_without_changing_bytes_or_prompt(self):
        plan=dict(self.plan,startup_context=dict(path=str(self.source/'startup.json'),sha256=extension.sha(self.source/'startup.json')))
        proposed=extension.proposed_plan(plan,self.root/'new_source',self.boundary())
        self.assertEqual(proposed['startup_context']['path'],str(self.root/'new_source/startup.json'))
        self.assertEqual(proposed['startup_context']['sha256'],plan['startup_context']['sha256'])

    def test_control_runtime_ceiling_label_and_resume_only(self):
        path,config,plan=self.control()
        budget=extension.read(config['lease_path'])
        self.assertTrue(config['resume'])
        self.assertNotIn('r153_agent',config)
        self.assertFalse(budget['provider_booking_verified'])
        self.assertFalse(budget['purchase_performed'])
        self.assertIn('NOT_PURCHASE_EXPIRY',budget['lease_end_field_semantics'])
        self.assertEqual(plan['root'],self.plan['root'])
        allocation=extension.read(config['allocation_path'])
        self.assertTrue(allocation['builder_entry_posted'])
        self.assertFalse(allocation['git_push_performed'])

    def test_resume_validation_delegates_original_guard(self):
        path,config,plan=self.control()
        self.assertEqual(self.validate(path,config,plan),(config,plan))

    def test_resume_validation_rejects_reset(self):
        path,config,plan=self.control();config['resume']=False
        with self.assertRaisesRegex(ValueError,'same_life_resume'):
            self.validate(path,config,plan)

    def test_resume_validation_rejects_source_mutation(self):
        path,config,plan=self.control()
        changed=Path(plan['source_root'])/'gpu/native.py';changed.chmod(0o644);changed.write_text('changed')
        with self.assertRaisesRegex(ValueError,'entire_new_source'):
            self.validate(path,config,plan)

    def test_resume_validation_rejects_device_policy_change(self):
        path,config,plan=self.control();config['device_containment']['minor']=1
        with self.assertRaisesRegex(ValueError,'unchanged_device_envelope'):
            self.validate(path,config,plan)

    def test_full_snapshot_genesis_not_zero_hash(self):
        boundary=self.boundary()
        extension.verify_snapshot(self.life/'stream',self.life,boundary)

    def test_snapshot_changed_intent_rejected(self):
        boundary=self.boundary()
        path=self.life/'stream/records/00000000000000000000.intent.json'
        data=extension.read(path);data['record_sha256']='0'*64;path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'preserved_intent'):
            extension.verify_snapshot(self.life/'stream',self.life,boundary)

    def test_snapshot_wrong_previous_hash_rejected(self):
        boundary=self.boundary();record=boundary['record'];record['previous_sha256']='0'*64
        Path(boundary['reference']['path']).write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'preserved_full_journal_chain'):
            extension.verify_snapshot(self.life/'stream',self.life,boundary)

    def test_original_validation_uses_original_source_and_no_visible_GPU(self):
        with patch.object(extension.subprocess,'run') as running:
            extension.original_validate(self.config_path)
        self.assertEqual(running.call_args.kwargs['cwd'],self.plan['source_root'])
        self.assertEqual(running.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'],'')
        self.assertIn('from gpu.orch_r125_continual_guard import validate',running.call_args.args[0][3])

    def test_all_five_single_minor_strict_envelopes(self):
        unused_path,config,plan=self.control();config['r157_config_path']='/own/guard'
        for physical,gpu_uuid,unused_pid,unused_ticks in extension.TARGETS.values():
            candidate=dict(plan,physical=physical,gpu_uuid=gpu_uuid)
            config['device_containment']['minor']=physical
            command=extension.containment_command(config,candidate)
            self.assertIn('--property=DevicePolicy=strict',command)
            self.assertIn('--property=DeviceAllow=/dev/nvidia'+str(physical)+' rw',command)
            self.assertIn('--property=NoNewPrivileges=yes',command)
            self.assertIn('--property=KillMode=control-group',command)
            self.assertIn('PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True',command)
            self.assertIn('CUDA_VISIBLE_DEVICES='+gpu_uuid,command)
            self.assertNotIn('/bin/sh',command)

    def test_protected_device_cannot_get_envelope(self):
        unused_path,config,plan=self.control();config['r157_config_path']='/own/guard'
        for physical in (2,6,7):
            config['device_containment']['minor']=physical
            with self.subTest(physical=physical),self.assertRaisesRegex(ValueError,'exact_R157_single_node'):
                extension.containment_command(config,dict(plan,physical=physical))

    def test_wrong_UUID_cannot_get_envelope(self):
        unused_path,config,plan=self.control();config['r157_config_path']='/own/guard'
        with self.assertRaisesRegex(ValueError,'exact_R157_single_node'):
            extension.containment_command(config,dict(plan,gpu_uuid=extension.TARGETS['C2'][1]))

    def test_supervisor_fresh_original_privileged_scan_then_envelope(self):
        path,config,plan=self.control()
        report=dict(clear=True,scanner_euid=0,blocking_reasons=[],gpu=dict(uuid=plan['gpu_uuid']))
        with (patch.object(extension,'validate_resume',return_value=(config,plan)),
              patch.object(extension.subprocess,'check_output',return_value=json.dumps(report)) as scan,
              patch.object(extension.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as running):
            extension.supervise(path)
        self.assertEqual(scan.call_args.args[0][:4],['sudo','-n','env','CUDA_VISIBLE_DEVICES='])
        self.assertIn('gpu.orch_r125_continual_guard',scan.call_args.args[0])
        self.assertIn('scan',scan.call_args.args[0])
        self.assertIn('--property=DevicePolicy=strict',running.call_args.args[0])

    def test_supervisor_blocked_scan_never_runs_native(self):
        path,config,plan=self.control()
        report=dict(clear=False,scanner_euid=0,blocking_reasons=['foreign_fd'],gpu=dict(uuid=plan['gpu_uuid']))
        with (patch.object(extension,'validate_resume',return_value=(config,plan)),
              patch.object(extension.subprocess,'check_output',return_value=json.dumps(report)),
              patch.object(extension.subprocess,'run') as running):
            with self.assertRaisesRegex(ValueError,'original_privileged_exclusive'):
                extension.supervise(path)
        running.assert_not_called()
        self.assertTrue((Path(config['attempt_dir'])/'FAILED.json').exists())

    def test_supervisor_cannot_retry_existing_attempt(self):
        path,config,plan=self.control();Path(config['attempt_dir']).mkdir()
        with (patch.object(extension,'validate_resume',return_value=(config,plan)),
              patch.object(extension.subprocess,'check_output') as scan):
            with self.assertRaises(FileExistsError): extension.supervise(path)
        scan.assert_not_called()

    def test_watchdog_operator_loss_only_resumes_exact_pidfd(self):
        with (patch.object(extension.select,'select',return_value=([],[],[])),
              patch.object(extension.signal,'pidfd_send_signal') as sending):
            extension.watchdog(42,43,10)
        sending.assert_called_once_with(42,signal.SIGCONT)

    def test_watchdog_disarm_never_signals(self):
        with (patch.object(extension.select,'select',return_value=([43],[],[])),
              patch.object(extension.os,'read',return_value=b'D'),
              patch.object(extension.signal,'pidfd_send_signal') as sending):
            extension.watchdog(42,43,10)
        sending.assert_not_called()

    def test_foreign_children_block_before_signals(self):
        pair=dict(actor=dict(pid=10),timer=dict(pid=9),supervisor=dict(pid=8))
        with patch.object(extension,'live_children',side_effect=lambda pid:{8:{9},9:{10},10:{11,12}}[pid]):
            with self.assertRaisesRegex(ValueError,'no_foreign_children'):
                extension.check_children(pair,11)

    def test_only_owned_readout_child_permitted(self):
        pair=dict(actor=dict(pid=10),timer=dict(pid=9),supervisor=dict(pid=8))
        with patch.object(extension,'live_children',side_effect=lambda pid:{8:{9},9:{10},10:{11}}[pid]):
            extension.check_children(pair,11)

    def test_receipt_no_overwrite(self):
        path=self.root/'immutable.json';extension.write(path,dict(first=True))
        with self.assertRaises(FileExistsError):extension.write(path,dict(first=False))
        self.assertEqual(extension.read(path),dict(first=True))

    def test_authorization_failure_never_opens_pidfd_or_signals(self):
        self.stage();self.auth.write_text('{}')
        copied=self.output/'AUTHORIZATION.json';copied.chmod(0o644);copied.write_text('{}')
        with (patch.object(extension.socket,'gethostname',return_value=extension.HOST),
              patch.object(extension.os,'getuid',return_value=2524),patch.dict(os.environ,CUDA_VISIBLE_DEVICES=''),
              patch.object(extension.os,'pidfd_open') as opened,patch.object(extension.signal,'pidfd_send_signal') as sending):
            with self.assertRaisesRegex(ValueError,'exact_shared_R157'):
                extension.handoff(self.output)
        opened.assert_not_called();sending.assert_not_called()


if __name__ == '__main__':
    unittest.main()
