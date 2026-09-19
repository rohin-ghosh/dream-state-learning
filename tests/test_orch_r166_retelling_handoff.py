from copy import deepcopy
from contextlib import ExitStack, contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r166_retelling_handoff as handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        replacing = patch.object(handoff.saved, 'BASE', self.base)
        replacing.start()
        self.addCleanup(replacing.stop)
        self.source = self.base / 'old_source'
        (self.source / 'gpu').mkdir(parents=True)
        (self.source / 'tests').mkdir()
        repository = Path(handoff.__file__).resolve().parents[1]
        for name in (handoff.NATIVE_RELATIVE, handoff.saved.RELATIVE):
            (self.source / name).write_bytes((repository / name).read_bytes())
        (self.source / 'startup.txt').write_text('original birth')
        self.plan = dict(root=str(self.base / 'orch_r153_community_C1_20260916_attempt1/life'),
            community_agent_id='C1', source_root=str(self.source), physical=0,
            gpu_uuid=handoff.saved.TARGETS['C1'][1], hard_end_unix=handoff.saved.NEW_WALL,
            lease_end_unix=handoff.saved.CEILING, presleep_variant='free_distillation',
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
            birth_prompt='original birth', compaction_invitation='old invitation',
            seed=15301, readout_revision=3,
            startup_context=dict(path=str(self.source / 'startup.txt'), sha256='unchanged'))
        self.plan_path = self.write('PLAN.json', self.plan)
        self.lease = self.write('LEASE.json', dict(hard_end_unix=handoff.saved.NEW_WALL,
                                                  lease_end_unix=handoff.saved.CEILING))
        self.community = Path(self.plan['root']).parent / 'config/COMMUNITY.json'
        self.community.parent.mkdir(parents=True)
        self.community.write_text(json.dumps(dict(parent=dict(speaker='Astra'))))
        birth = self.write('BIRTH_GUARD.json', dict(r153_agent=dict(files={
            'config/COMMUNITY.json': handoff.saved.sha(self.community)})))
        self.prior = self.write('PRIOR_REQUEST.json', dict(old_config=handoff.saved.reference(birth),
            authorization=dict(path='/not/read/auth'), provenance=dict(path='/not/read/provenance')))
        self.config = dict(plan_path=str(self.plan_path), plan_sha256=handoff.saved.sha(self.plan_path),
            hard_end_unix=handoff.saved.NEW_WALL, next_reserved_unix=handoff.saved.CEILING,
            host_sha256=hashlib.sha256(handoff.saved.HOST.encode()).hexdigest(), resume=True,
            lease_path=str(self.lease), lease_sha256=handoff.saved.sha(self.lease),
            device_containment=dict(minor=0, uid=2524, gid=2524, unit='orch-r157-native-' + 'a'*32),
            r157_request=handoff.saved.reference(self.prior), attempt_dir='/unused')
        self.config_path = self.write('GUARD.json', self.config)
        self.directive = self.base / 'DIRECTIVE.md'
        self.directive.write_text('fixture directive')
        replacing = patch.object(handoff.retelling, 'DIRECTIVE_SHA256', handoff.saved.sha(self.directive))
        replacing.start()
        self.addCleanup(replacing.stop)
        self.followup = self.base / 'R153_DIRECTIVE.md'
        self.followup.write_bytes((repository / handoff.FOLLOWUP_RELATIVE).read_bytes())
        self.addendum = self.base / 'R154_ADDENDUM.md'
        self.addendum.write_bytes((repository /
            'research_loop/workers/r167_object_survival/ROHIN154_ADDENDUM.md').read_bytes())
        self.scope_document = self.write('SCOPE.json', dict(schema='R166_BUILDER_SCOPE_V1',
            directive_sha256=handoff.saved.sha(self.directive), followup_scope=dict(
                directive_path=handoff.FOLLOWUP_RELATIVE, directive_sha256=handoff.FOLLOWUP_SHA256,
                runtime_limit='No new children or retirements; native changes limited to pre-sleep invitation; original sources/recipes/controls preserved')))
        self.cpu = self.write('CPU.json', dict(passed=True, returncode=0, tests=1,
            invitation_tests_sha256=handoff.POLICY_TEST_SHA256, files={
            name: handoff.saved.sha(repository / name) for name in
            (handoff.RELATIVE, handoff.TEST_RELATIVE, handoff.POLICY_RELATIVE, handoff.saved.RELATIVE)}))
        self.output = self.base / 'orch_r166_retelling_C1_fixture'
        self.pair = dict(actor=dict(pid=2147483645), timer=dict(pid=2147483644),
                         supervisor=dict(pid=2147483643))

    def write(self, name, value):
        path = self.base / name
        path.write_text(json.dumps(value))
        return path

    def stage(self, **kwargs):
        with patch.object(handoff, 'cpu_operator'), \
                patch.object(handoff.saved, 'original_validate', return_value=(self.config, self.plan)), \
                patch.object(handoff.saved, 'authorization'), \
                patch.object(handoff, 'capture_owner', return_value=self.pair):
            return handoff.stage(self.plan['community_agent_id'], self.config_path, 1, self.directive, self.cpu, self.output,
                scope_document=self.scope_document, followup_directive=self.followup, addendum=self.addendum,
                **kwargs)

    def boundary(self, **changes):
        state = dict(deadline_unix=self.plan['hard_end_unix'], pending=None, sleep_frontier=1,
                     rows=[dict(target='own', parent_masked=True)], sleep_receipts=[dict(status='COMPLETE')],
                     carry='exact carried text', history=dict(events=['parent', 'own']))
        state.update(changes)
        return dict(state_sha256=handoff.saved.digest(state), record=dict(document=dict(
            resume_state=dict(state=state, sha256=handoff.saved.digest(state)))))

    def test_all_five_exact_community_slots(self):
        for agent, (physical, gpu_uuid, unused_pid, unused_ticks) in handoff.saved.TARGETS.items():
            plan = dict(self.plan, root=str(self.base / ('orch_r153_community_' + agent + '_20260916_attempt1/life')),
                        community_agent_id=agent, physical=physical, gpu_uuid=gpu_uuid)
            config = deepcopy(self.config)
            config['device_containment']['minor'] = physical
            self.assertTrue(handoff.scope(agent, config, plan)['parented'])

    def test_controls_and_wrong_identity_rejected(self):
        cases = [dict(presleep_variant=value) for value in ('reread', 'no_distillation', 'frozen', 'no_sleep')]
        cases += [dict(parented=False), dict(frozen=True), dict(no_sleep=True), dict(mode='frozen'),
                  dict(learning_enabled=False), dict(root='/foreign'), dict(physical=5),
                  dict(gpu_uuid=handoff.saved.TARGETS['C2'][1]), dict(community_agent_id='C2')]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                handoff.scope('C1', self.config, dict(self.plan, **change))
        with self.assertRaises(ValueError):
            handoff.scope('C6', self.config, self.plan)

    def test_parent_guided_allowed(self):
        policy = handoff.scope('C1', self.config, dict(self.plan, presleep_variant='parent_guided_distillation'))
        self.assertEqual(policy['presleep_variant'], 'parent_guided_distillation')

    def test_recipe_and_walls_are_not_amended(self):
        for change in (dict(hard_end_unix=0), dict(lease_end_unix=0), dict(new_presentations=15),
                       dict(rehearsal_presentations=2), dict(anchor_lambda=0.3)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                handoff.scope('C1', self.config, dict(self.plan, **change))

    def test_exact_isolated_patch_and_frozen_source(self):
        original = handoff.saved.files(self.source)
        with patch.object(handoff.subprocess, 'Popen') as launching, \
                patch.object(handoff.saved.signal, 'pidfd_send_signal') as signaling:
            self.stage()
        launching.assert_not_called()
        signaling.assert_not_called()
        self.assertEqual(handoff.saved.files(self.source), original)
        request = handoff.saved.read(self.output / 'REQUEST.json')
        copied = handoff.saved.files(self.output / 'source')
        self.assertEqual(set(copied) - set(original),
                         {handoff.RELATIVE, handoff.TEST_RELATIVE, handoff.POLICY_RELATIVE,
                          handoff.POLICY_TEST_RELATIVE})
        self.assertEqual((self.output / 'source' / handoff.NATIVE_RELATIVE).read_text(),
            handoff.retelling.patch_source((self.source / handoff.NATIVE_RELATIVE).read_text(), request['policy_scope']))
        self.assertTrue(all(path.stat().st_mode & 0o222 == 0
            for path in (self.output / 'source').rglob('*')))
        with patch.object(handoff.saved, 'authorization'):
            handoff.verify_request(self.output)

    def successor_validation(self):
        source = self.output / 'source'
        code = '''import json,sys
from pathlib import Path
from gpu import orch_r166_retelling_handoff as handoff
source = Path.cwd()
assert Path(handoff.__file__).resolve() == source / handoff.RELATIVE
assert Path(handoff.saved.__file__).resolve() == source / handoff.saved.RELATIVE
assert Path(handoff.retelling.__file__).resolve() == source / handoff.POLICY_RELATIVE
request = json.loads(Path(sys.argv[1]).read_text())
handoff.validate_cpu(request['cpu']['path'])
assert handoff.saved.files(source) == request['source_files']
assert request['source_files'][handoff.POLICY_TEST_RELATIVE] == handoff.POLICY_TEST_SHA256
print('SUCCESSOR_SOURCE_VALIDATED')
'''
        return subprocess.run([sys.executable, '-B', '-c', code, str(self.output / 'REQUEST.json')],
            cwd=source, env=dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1',
                                 CUDA_VISIBLE_DEVICES=''), text=True, capture_output=True, timeout=30)

    def test_actual_staged_successor_subprocess_validates_CPU_and_inventory(self):
        self.stage()
        result = self.successor_validation()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SUCCESSOR_SOURCE_VALIDATED', result.stdout)

    def test_actual_successor_subprocess_refuses_missing_or_tampered_invitation_test(self):
        self.stage()
        target = self.output / 'source' / handoff.POLICY_TEST_RELATIVE
        original = target.read_bytes()
        target.parent.chmod(0o755)
        target.unlink()
        result = self.successor_validation()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FileNotFoundError', result.stderr)
        target.write_bytes(original + b'\n')
        result = self.successor_validation()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('bound_actual_CPU_receipt', result.stderr)

    def test_new_candidate_adds_test_to_legacy_closure_without_mutating_predecessor(self):
        self.stage()
        predecessor = self.output / 'REQUEST.json'
        legacy = handoff.saved.read(predecessor)
        target = self.output / 'source' / handoff.POLICY_TEST_RELATIVE
        target.parent.chmod(0o755)
        target.unlink()
        target.parent.chmod(0o555)
        legacy['source_files'].pop(handoff.POLICY_TEST_RELATIVE)
        predecessor.chmod(0o644)
        predecessor.write_text(json.dumps(legacy))
        predecessor.chmod(0o444)
        original_files = handoff.saved.files(self.output)
        old_output = self.output
        self.output = self.base / 'orch_r166_retelling_C1_new_candidate'
        self.stage(candidate_request=predecessor, candidate_sha256=handoff.saved.sha(predecessor))
        self.assertEqual(handoff.saved.files(old_output), original_files)
        self.assertEqual(handoff.saved.read(self.output / 'REQUEST.json')['source_files'][
            handoff.POLICY_TEST_RELATIVE], handoff.POLICY_TEST_SHA256)
        result = self.successor_validation()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_staging_refuses_overwrite_and_bad_CPU(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, 'new_R166_output_only'):
            self.stage()
        cpu = handoff.saved.read(self.cpu)
        cpu['passed'] = False
        self.cpu.write_text(json.dumps(cpu))
        with self.assertRaisesRegex(ValueError, 'bound_actual_CPU'):
            self.stage()

    def test_unparented_community_provenance_rejected(self):
        self.community.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'original_parented_community'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_live_owner_prevents_prepare(self):
        with self.assertRaisesRegex(ValueError, 'old_owner_still_present'):
            handoff.require_retired(dict(actor=dict(pid=os.getpid())))

    def test_source_tampering_rejected(self):
        self.stage()
        target = self.output / 'source/startup.txt'
        target.chmod(0o644)
        target.write_text('tampered')
        with patch.object(handoff.saved, 'authorization'), self.assertRaisesRegex(ValueError, 'full_source_pins'):
            handoff.verify_request(self.output)

    def test_plan_only_relocates_source_preserves_every_other_field(self):
        before = deepcopy(self.plan)
        boundary = self.boundary()
        plan = handoff.proposed_plan(self.plan, self.output / 'source', boundary, self.base / 'unused')
        handoff.check_plan_delta(self.plan, plan)
        self.assertEqual(self.plan, before)
        self.assertEqual(plan['compaction_invitation'], before['compaction_invitation'])
        for change in (dict(seed=0), dict(birth_prompt='rewritten'), dict(readout_revision=4),
                       dict(compaction_invitation='new'), dict(hard_end_unix=0)):
            with self.assertRaisesRegex(ValueError, 'birth_experiment_walls_recipe_readouts_unchanged'):
                handoff.check_plan_delta(before, dict(plan, **change))

    def test_consumed_wall_authority_requires_actual_record(self):
        extension = dict(new_deadline_unix=self.plan['hard_end_unix'], previous_deadline_unix=1)
        old = dict(self.plan, authorized_wall_extension=extension)
        stream = self.base / 'stream'
        (stream / 'records').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'must_be_recorded'):
            handoff.proposed_plan(old, self.output, self.boundary(), stream)
        (stream / 'records/00000000000000000000.json').write_text(json.dumps(dict(
            kind='WALL_EXTENDED', document=dict(authorization=extension))))
        new = handoff.proposed_plan(old, self.output, self.boundary(), stream)
        self.assertNotIn('authorized_wall_extension', new)
        self.assertEqual(old['authorized_wall_extension'], extension)
        self.assertEqual(new['hard_end_unix'], old['hard_end_unix'])

    def test_saved_deadline_mismatch_refused(self):
        with self.assertRaisesRegex(ValueError, 'exact_current_saved_deadline'):
            handoff.proposed_plan(self.plan, self.output, self.boundary(deadline_unix=1), self.base)

    def test_strict_successor_uses_new_validator_and_same_device_envelope(self):
        with patch.object(handoff.saved.time, 'time', return_value=handoff.saved.NEW_WALL - 300):
            proposal = handoff.strict_command(self.config, self.plan, self.config_path)
        command = proposal['template']
        self.assertTrue(proposal['executable_as_is'])
        self.assertTrue(proposal['main_GO_required'])
        self.assertEqual(command[-4], handoff.MODULE)
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia0 rw', command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia1 rw', command)
        self.assertIn('--property=RuntimeMaxSec=300', command)

    def test_CLI_execution_needs_explicit_arguments_and_cannot_issue_GO(self):
        with patch.object(handoff.subprocess, 'Popen') as launching:
            for action in ('handoff', 'supervise', 'contained-native', 'execute', 'GO'):
                with self.assertRaises(SystemExit):
                    handoff.main([action])
        launching.assert_not_called()

    def saved_life(self, orphan=False):
        root = Path(self.plan['root'])
        records = root / 'stream/records'
        records.mkdir(parents=True)
        (root / 'stream/inbox').mkdir()
        manifest = dict(journal_id='fixture-journal')
        (root / 'stream/JOURNAL.json').write_text(json.dumps(manifest))
        document = self.boundary()['record']['document']
        document.update(status='COMPLETE', cycle=1, checkpoint=dict(saved='fixture-not-real-tensors'))
        record = dict(index=0, journal_id=manifest['journal_id'],
            previous_sha256=handoff.saved.digest(manifest), kind='SLEEP_COMPLETE', document=document)
        record['sha256'] = handoff.saved.digest(record)
        (records / '00000000000000000000.json').write_text(json.dumps(record))
        intent = dict(index=0, previous_sha256=record['previous_sha256'], record_sha256=record['sha256'])
        (records / '00000000000000000000.intent.json').write_text(json.dumps(intent))
        if orphan:
            (records / '00000000000000000001.intent.json').write_text('{}')
        checkpoint = root / 'checkpoints/sleep_000001'
        checkpoint.mkdir(parents=True)
        (checkpoint / 'COMMIT.json').write_text(json.dumps(document['checkpoint']))
        (checkpoint / 'adapter.fixture').write_bytes(b'exact adapter fixture')
        (checkpoint / 'optimizer_rng.fixture').write_bytes(b'exact AdamW RNG fixture')
        return root

    def prepare_fixture(self):
        with patch.object(handoff, 'cpu_operator'), patch.object(handoff.saved, 'authorization'), \
                patch.object(handoff.saved, 'original_validate'), \
                patch.object(handoff, 'boundary_cpu', return_value=dict(cpu_fixture_only=True)), \
                patch.object(handoff.saved.time, 'time', return_value=handoff.saved.NEW_WALL - 600):
            return handoff.prepare(self.output)

    def test_prepare_preserves_full_boundary_and_never_launches(self):
        self.stage()
        root = self.saved_life()
        before = handoff.saved.files(root)
        with patch.object(handoff.subprocess, 'Popen') as launching, \
                patch.object(handoff.saved.signal, 'pidfd_send_signal') as signaling:
            receipt = self.prepare_fixture()
        launching.assert_not_called()
        signaling.assert_not_called()
        self.assertTrue(receipt['no_GO'])
        self.assertEqual(handoff.saved.files(root), before)
        control = self.output / 'control'
        successor = handoff.saved.read(control / 'GUARD.json')
        self.assertEqual(successor['lease_path'], self.config['lease_path'])
        self.assertEqual(successor['lease_sha256'], self.config['lease_sha256'])
        self.assertEqual(successor['hard_end_unix'], self.config['hard_end_unix'])
        self.assertEqual(successor['next_reserved_unix'], self.config['next_reserved_unix'])
        self.assertTrue(successor['resume'])
        policy = handoff.saved.read(control / 'EFFECTIVE_POLICY.json')
        self.assertEqual(policy['followup']['directive']['sha256'], handoff.FOLLOWUP_SHA256)
        self.assertEqual(policy['original_directive']['sha256'], handoff.saved.sha(self.directive))
        self.assertEqual(policy['addendum']['sha256'], handoff.ADDENDUM_SHA256)
        self.assertFalse(policy['actual_runtime_applied'])
        self.assertFalse(policy['corrected_output_claimed'])
        self.assertEqual(handoff.saved.files(self.output / 'preserved_checkpoint'),
                         handoff.saved.files(root / 'checkpoints/sleep_000001'))
        with self.assertRaisesRegex(ValueError, 'prepare_once_no_overwrite'):
            self.prepare_fixture()

    def test_orphan_intent_is_uncertain_not_a_saved_boundary(self):
        self.stage()
        self.saved_life(orphan=True)
        with self.assertRaisesRegex(ValueError, 'no_unpaired_intent'):
            self.prepare_fixture()
        self.assertFalse((self.output / 'control/PREPARED.json').exists())

    def test_prepare_live_owner_refuses_before_copy(self):
        self.stage()
        self.saved_life()
        with patch.object(handoff, 'require_retired', side_effect=ValueError('still-live')):
            with self.assertRaisesRegex(ValueError, 'still-live'):
                self.prepare_fixture()
        self.assertFalse((self.output / 'control').exists())

    def test_prepare_requires_latest_complete_terminal_record(self):
        self.stage()
        root = self.saved_life()
        (root / 'stream/records/00000000000000000001.json').write_text(json.dumps(dict(kind='REQUEST')))
        with self.assertRaisesRegex(ValueError, 'latest_record_must_be_complete'):
            self.prepare_fixture()
        self.assertFalse((self.output / 'control').exists())

    def test_R153_followup_is_copied_bound_and_preserves_R150(self):
        self.stage()
        request = handoff.saved.read(self.output / 'REQUEST.json')
        self.assertEqual(request['directive'], handoff.saved.reference(self.directive))
        self.assertEqual(request['followup']['directive'],
                         handoff.saved.reference(self.output / 'R153_DIRECTIVE.md'))
        self.assertEqual(request['followup_origin']['directive'], handoff.saved.reference(self.followup))
        self.assertEqual((self.output / 'R153_DIRECTIVE.md').read_bytes(), self.followup.read_bytes())
        self.assertEqual((self.output / 'R153_DIRECTIVE.md').stat().st_mode & 0o222, 0)
        self.scope_document.write_text('{}')
        with patch.object(handoff.saved, 'authorization'):
            handoff.verify_request(self.output)

    def test_missing_followup_scope_refuses_before_staging(self):
        document = handoff.saved.read(self.scope_document)
        del document['followup_scope']
        self.scope_document.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, 'R153_followup_required'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_wrong_R153_directive_refuses_before_staging(self):
        self.followup.write_text('not the relay')
        with self.assertRaisesRegex(ValueError, 'exact_R153_followup_directive'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_followup_scope_must_not_authorize_retirement(self):
        document = handoff.saved.read(self.scope_document)
        document['followup_scope']['runtime_limit'] = 'Retire all children'
        self.scope_document.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, 'R153_runtime_limit_unchanged'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_tampered_staged_scope_rejected(self):
        self.stage()
        path = self.output / 'R153_SCOPE.json'
        path.chmod(0o644)
        document = handoff.saved.read(path)
        document['extra'] = 'tampered while keeping required fields'
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, 'staged_R153_followup_still_bound'):
            handoff.verify_request(self.output)

    def test_old_invitation_CPU_receipt_rejected(self):
        receipt = handoff.saved.read(self.cpu)
        receipt['files'][handoff.POLICY_RELATIVE] = '1b6e173795b277c39cb4c6b29519716fd36feebe21e99f39cecaa3ec6c145f55'
        self.cpu.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'bound_actual_CPU_receipt'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_R154_addendum_is_frozen_and_bound(self):
        self.stage()
        request = handoff.saved.read(self.output / 'REQUEST.json')
        copied = self.output / 'R154_ADDENDUM.md'
        self.assertEqual(request['addendum'], handoff.saved.reference(copied))
        self.assertEqual(request['addendum']['sha256'], handoff.ADDENDUM_SHA256)
        self.assertEqual(copied.stat().st_mode & 0o222, 0)
        self.assertEqual(copied.read_bytes(), self.addendum.read_bytes())

    def test_wrong_R154_addendum_refuses_before_staging(self):
        self.addendum.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'exact_R154_addendum'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_tampered_staged_R154_addendum_refused(self):
        self.stage()
        copied = self.output / 'R154_ADDENDUM.md'
        copied.chmod(0o644)
        copied.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'staged_R154_addendum_still_bound'):
            handoff.verify_request(self.output)

    def test_GO_binds_exact_source_plan_owner_custody_policy(self):
        expected = dict(hard_end_unix=10000, source_manifest_sha256='a'*64,
                        boundary_rule='NEXT_ACTUAL_SAVED_SLEEP')
        go = dict(schema=handoff.GO_SCHEMA, issuer='Main', decision='GO', binding=expected,
                  not_before_unix=100, expires_unix=1000)
        handoff.validate_go(go, expected, 200)
        for change in (dict(issuer='worker'), dict(decision='READY'), dict(binding={}),
                       dict(expires_unix=100), dict(expires_unix=10001),
                       dict(not_before_unix=300), dict(expires_unix=float('nan')),
                       dict(not_before_unix=float('-inf'))):
            with self.subTest(change=change), self.assertRaises(ValueError):
                handoff.validate_go(dict(go, **change), expected, 200)

    def test_preflight_actual_boundary_proof_precedes_any_signal(self):
        self.stage()
        root = self.saved_life()
        (root / 'stream/records/00000000000000000001.json').write_text(json.dumps(dict(kind='REQUEST')))
        proof = dict(cuda_initialized=False, reset=False, optimizer_steps=7)
        with patch.object(handoff, 'cpu_operator'), patch.object(handoff.saved, 'authorization'), \
                patch.object(handoff.saved, 'same'), patch.object(handoff, 'boundary_cpu', return_value=proof), \
                patch.object(handoff.signal, 'pidfd_send_signal') as sending, \
                patch.object(handoff.saved.time, 'time', return_value=handoff.saved.NEW_WALL - 600):
            result = handoff.preflight(self.output)
        sending.assert_not_called()
        self.assertTrue(result['proof_is_loader_preflight_not_current_resume_authority'])
        self.assertEqual(result['required_GO_binding']['earliest_boundary_index'], 0)
        self.assertTrue(result['strict_successor']['executable_as_is'])
        self.assertEqual(handoff.saved.bound(result['required_GO_binding']['cpu_proof']), proof)
        self.assertFalse((self.output / 'ACTIVATE_ONCE').exists())

    def test_preflight_failed_CPU_never_claims_ready(self):
        self.stage()
        self.saved_life()
        with patch.object(handoff, 'cpu_operator'), patch.object(handoff.saved, 'authorization'), \
                patch.object(handoff.saved, 'same'), \
                patch.object(handoff, 'boundary_cpu', side_effect=ValueError('checkpoint_drift')), \
                self.assertRaisesRegex(ValueError, 'checkpoint_drift'):
            handoff.preflight(self.output)
        self.assertFalse((self.output / 'readiness/READY.json').exists())

    def execute_fixture(self, events, *, proof_failure=False, stale_boundary=False, validator_failure=False,
                        uncertain_exit=False):
        request = handoff.saved.read(self.output / 'REQUEST.json')
        boundary = handoff.saved.saved_boundary(self.plan['root'])
        now = handoff.saved.NEW_WALL - 3600
        go_path = self.write('MAIN_GO_FIXTURE.json', dict(expires_unix=now+1800))
        expected = dict(max_wait_seconds=600, max_pause_seconds=600,
                        earliest_boundary_index=boundary['index'], plan=dict(sha256='fixture-plan'))

        def binding(*args):
            events.append('preflight_checked')
            return request, self.config, self.plan, expected

        @contextmanager
        def watchdog(*args):
            try:
                yield handoff.time.monotonic() + 600
            finally:
                events.append('watchdog_release')

        def preparing(*args, **kwargs):
            events.append('actual_CPU_custody')
            if proof_failure:
                raise ValueError('actual_CPU_failed')
            control = self.output / 'control'
            control.mkdir()
            handoff.saved.write(control / 'PREPARED.json', dict(fixture=True))
            return dict(plan=dict(sha256='fixture-plan'))

        def validating(*args, **kwargs):
            events.append('strict_executable_validated')
            if validator_failure:
                raise ValueError('successor_not_ready')

        with ExitStack() as stack:
            replacements = [
                patch.object(handoff, 'cpu_operator'),
                patch.object(handoff, 'activation_binding', side_effect=binding),
                patch.object(handoff, '__file__', str(Path(request['source_root']) / handoff.RELATIVE)),
                patch.object(handoff.saved, '__file__', str(Path(request['source_root']) / handoff.saved.RELATIVE)),
                patch.object(handoff.retelling, '__file__', str(Path(request['source_root']) / handoff.POLICY_RELATIVE)),
                patch.object(handoff.os, 'open', return_value=998),
                patch.object(handoff.os, 'close'),
                patch.object(handoff.os, 'pidfd_open', return_value=999),
                patch.object(handoff.fcntl, 'flock'),
                patch.object(handoff.saved, 'same'),
                patch.object(handoff.saved.time, 'time', return_value=now),
                patch.object(handoff.saved, 'check_children'),
                patch.object(handoff.saved, 'readout', return_value=dict(identity=None)),
                patch.object(handoff.saved, 'pause_watchdog', side_effect=watchdog),
                patch.object(handoff.saved, 'pause_exact', side_effect=lambda *args: events.append('pause')),
                patch.object(handoff.saved, 'wait_readout', return_value=dict(metadata_only=True)),
                patch.object(handoff, 'check_paused'),
                patch.object(handoff, 'prepare', side_effect=preparing),
                patch.object(handoff, 'validate_successor', side_effect=validating),
                patch.object(handoff.signal, 'pidfd_send_signal', side_effect=lambda descriptor, signum: events.append(signum)),
                patch.object(handoff.select, 'select', return_value=([] if uncertain_exit else [999], [], [])),
                patch.object(handoff, 'supervise', side_effect=lambda *args: events.append('strict_successor')),
            ]
            if stale_boundary:
                replacements.append(patch.object(handoff.saved, 'saved_boundary', side_effect=[boundary, None]))
            for replacing in replacements:
                stack.enter_context(replacing)
            return handoff.execute(self.output, go_path, 'fixture-go-sha')

    def test_execute_no_termination_until_actual_CPU_and_executable_ready(self):
        self.stage()
        self.saved_life()
        events = []
        self.execute_fixture(events)
        self.assertLess(events.index('preflight_checked'), events.index('pause'))
        self.assertLess(events.index('actual_CPU_custody'), events.index(handoff.signal.SIGTERM))
        self.assertLess(events.index('strict_executable_validated'), events.index(handoff.signal.SIGTERM))
        self.assertLess(events.index(handoff.signal.SIGTERM), events.index('strict_successor'))
        self.assertTrue((self.output / 'ACTUAL_BOUNDARY_READY.json').exists())
        self.assertTrue((self.output / 'OWNER_RETIRED.json').exists())

    def test_failed_actual_CPU_releases_pause_without_termination(self):
        self.stage()
        self.saved_life()
        events = []
        with self.assertRaisesRegex(ValueError, 'actual_CPU_failed'):
            self.execute_fixture(events, proof_failure=True)
        self.assertIn('watchdog_release', events)
        self.assertNotIn(handoff.signal.SIGTERM, events)
        self.assertNotIn('strict_successor', events)
        self.assertFalse((self.output / 'OWNER_RETIRED.json').exists())
        self.assertTrue(handoff.saved.read(self.output / 'ACTIVATION_FAILED.json')['no_retry'])

    def test_unready_successor_releases_pause_without_termination(self):
        self.stage()
        self.saved_life()
        events = []
        with self.assertRaisesRegex(ValueError, 'successor_not_ready'):
            self.execute_fixture(events, validator_failure=True)
        self.assertNotIn(handoff.signal.SIGTERM, events)
        self.assertIn('watchdog_release', events)

    def test_boundary_race_no_termination_or_retry(self):
        self.stage()
        self.saved_life()
        events = []
        with self.assertRaisesRegex(ValueError, 'selected_boundary_raced'):
            self.execute_fixture(events, stale_boundary=True)
        self.assertNotIn('actual_CPU_custody', events)
        self.assertNotIn(handoff.signal.SIGTERM, events)
        self.assertIn('watchdog_release', events)

    def test_duplicate_execute_never_pauses_or_dispatches(self):
        self.stage()
        self.saved_life()
        (self.output / 'ACTIVATE_ONCE').mkdir()
        events = []
        with self.assertRaises(FileExistsError):
            self.execute_fixture(events)
        self.assertNotIn('pause', events)
        self.assertNotIn(handoff.signal.SIGTERM, events)

    def test_invalid_GO_never_opens_process_handles(self):
        with patch.object(handoff, 'cpu_operator'), \
                patch.object(handoff, 'activation_binding', side_effect=ValueError('bad_GO')), \
                patch.object(handoff.os, 'pidfd_open') as handles, \
                patch.object(handoff.signal, 'pidfd_send_signal') as sending, \
                self.assertRaisesRegex(ValueError, 'bad_GO'):
            handoff.execute(self.output, self.base / 'GO.json', '0'*64)
        handles.assert_not_called()
        sending.assert_not_called()

    def test_wrong_operator_import_root_never_signals(self):
        self.stage()
        request = handoff.saved.read(self.output / 'REQUEST.json')
        with patch.object(handoff, 'cpu_operator'), \
                patch.object(handoff, 'activation_binding', return_value=(request, self.config, self.plan, {})), \
                patch.object(handoff.os, 'pidfd_open') as handles, \
                patch.object(handoff.signal, 'pidfd_send_signal') as sending, \
                self.assertRaisesRegex(ValueError, 'execute_from_exact_successor_source'):
            handoff.execute(self.output, self.base / 'GO.json', '0'*64)
        handles.assert_not_called()
        sending.assert_not_called()

    def test_strict_scanner_refusal_is_preserved_and_never_dispatches(self):
        config = dict(self.config, attempt_dir=str(self.base / 'new_attempt'), r166_go=dict(sha256='fixture'))
        report = dict(clear=False, scanner_euid=0, blocking_reasons=['foreign_process'],
                      gpu=dict(uuid=self.plan['gpu_uuid'], index=0), device_minor=0)
        with patch.object(handoff, 'validate_successor', return_value=(config, self.plan)), \
                patch.object(handoff.subprocess, 'check_output', return_value=json.dumps(report)), \
                patch.object(handoff.subprocess, 'run') as dispatching, \
                self.assertRaisesRegex(ValueError, 'original_full_exclusive_admission'):
            handoff.supervise(self.config_path)
        dispatching.assert_not_called()
        self.assertEqual(handoff.saved.read(Path(config['attempt_dir']) / 'ADMISSION.json'), report)
        self.assertTrue(handoff.saved.read(Path(config['attempt_dir']) / 'FAILED.json')['no_retry'])

    def test_duplicate_successor_never_scans(self):
        attempt = self.base / 'already_dispatched'
        attempt.mkdir()
        config = dict(self.config, attempt_dir=str(attempt))
        with patch.object(handoff, 'validate_successor', return_value=(config, self.plan)), \
                patch.object(handoff.subprocess, 'check_output') as scanning, \
                self.assertRaises(FileExistsError):
            handoff.supervise(self.config_path)
        scanning.assert_not_called()

    def native_startup_fixture(self, remove_marker=False):
        specification = importlib.util.spec_from_file_location('r166_native_guard_fixture',
            Path(handoff.__file__).with_name('orch_r125_continual_guard.py'))
        guard = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(guard)

        attempt = self.base / 'native_contract_attempt'
        config = dict(self.config, attempt_dir=str(attempt), r166_go=dict(sha256='fixture'))
        report = dict(clear=True, scanner_euid=0, blocking_reasons=[],
                      gpu=dict(uuid=self.plan['gpu_uuid'], index=0), device_minor=0)

        def dispatch(command, check):
            self.assertTrue((attempt / 'DISPATCH_ONCE').is_dir())
            self.assertTrue((attempt / 'DISPATCH_ONCE.json').is_file())
            parent_pid = os.getppid()
            ticks = Path('/proc', str(parent_pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            handoff.saved.write(attempt / 'LAUNCH.json', dict(pid=parent_pid,
                parent_start_ticks=ticks, guard_sha256=handoff.saved.sha(self.config_path),
                admission_sha256=handoff.saved.sha(attempt / 'ADMISSION.json'),
                admission_verified_unix=handoff.saved.read(attempt / 'ADMISSION_TIME.json')['verified_unix']))
            if remove_marker:
                (attempt / 'DISPATCH_ONCE').rmdir()
            reader, writer = os.pipe()
            with os.fdopen(writer, 'wb') as startup_writer:
                startup_writer.write(b'LAUNCH_READY\n')
            with os.fdopen(reader, 'rb') as startup_reader, \
                    patch.object(guard, 'validate', return_value=(config, self.plan)), \
                    patch.object(guard.sys, 'stdin', startup_reader), \
                    patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.plan['gpu_uuid']):
                guard.native_entry(self.config_path)
            return SimpleNamespace(returncode=0)

        with patch.object(handoff, 'validate_successor', return_value=(config, self.plan)), \
                patch.object(handoff.subprocess, 'check_output', return_value=json.dumps(report)), \
                patch.object(handoff, 'strict_command', return_value=dict(template=['CPU_fixture'])), \
                patch.object(handoff.subprocess, 'run', side_effect=dispatch), \
                patch.object(guard.child, 'run') as model_run:
            if remove_marker:
                with self.assertRaisesRegex(ValueError, 'actual_timeout_parent'):
                    handoff.supervise(self.config_path)
                model_run.assert_not_called()
                self.assertTrue(handoff.saved.read(attempt / 'FAILED.json')['no_retry'])
            else:
                handoff.supervise(self.config_path)
                model_run.assert_called_once_with(config['plan_path'], resume=True)
                self.assertEqual(handoff.saved.read(attempt / 'SERVICE_EXIT.json')['returncode'], 0)

    def test_supervisor_marker_passes_actual_native_startup_contract(self):
        self.native_startup_fixture()

    def test_native_startup_rejects_JSON_receipt_without_dispatch_directory(self):
        self.native_startup_fixture(remove_marker=True)

    def recovery_fixture(self):
        self.plan.update(community_agent_id='C5', physical=5, gpu_uuid=handoff.saved.TARGETS['C5'][1],
            root=str(self.base / 'orch_r153_community_C5_20260916_attempt1/life'))
        self.plan_path.write_text(json.dumps(self.plan))
        self.config['plan_sha256'] = handoff.saved.sha(self.plan_path)
        self.config['device_containment']['minor'] = 5
        self.config_path.write_text(json.dumps(self.config))
        community = Path(self.plan['root']).parent / 'config/COMMUNITY.json'
        community.parent.mkdir(parents=True)
        community.write_bytes(self.community.read_bytes())
        self.output = self.base / 'orch_r166_retelling_C5_20260917_activation3'
        self.stage()
        self.saved_life()
        boundary = handoff.saved.saved_boundary(self.plan['root'])
        checkpoint = Path(self.plan['root']) / 'checkpoints/sleep_000001/COMMIT.json'
        self.recovery_proof = dict(cuda_initialized=False, reset=False, optimizer_steps=7,
            checkpoint_path=str(checkpoint), checkpoint_sha256=handoff.saved.sha(checkpoint),
            stream_sha256=boundary['state_sha256'], adapter_state_sha256='fixture_adapter',
            bundle_sha256=dict(adapter='fixture', optimizer='fixture', rng='fixture'))
        stack = ExitStack()
        self.addCleanup(stack.close)
        for name, value in (('RECOVERY_CYCLE', 1), ('RECOVERY_INDEX', 0), ('RECOVERY_STEPS', 7)):
            stack.enter_context(patch.object(handoff, name, value))
        stack.enter_context(patch.object(handoff, 'cpu_operator'))
        stack.enter_context(patch.object(handoff.saved, 'authorization'))
        stack.enter_context(patch.object(handoff.saved, 'original_validate'))
        stack.enter_context(patch.object(handoff.saved.time, 'time', return_value=handoff.saved.NEW_WALL - 3600))
        stack.enter_context(patch.object(handoff, 'boundary_cpu', return_value=self.recovery_proof))
        prepared = handoff.prepare(self.output)
        predecessor = self.output
        (predecessor / 'attempt').mkdir()
        for name, value in {
            'EXECUTION_GO.json': dict(go=dict(path='/fixture/old_go', sha256='old')),
            'ACTIVATION_FAILED.json': dict(original_exit_confirmed=True, termination_intent_recorded=True, no_retry=True),
            'OWNER_RETIRED.json': dict(pair=self.pair, prepared=handoff.saved.reference(predecessor / 'control/PREPARED.json'),
                                       go=dict(path='/fixture/old_go', sha256='old')),
            'ACTUAL_BOUNDARY_READY.json': dict(boundary=boundary['reference']),
            'attempt/NATIVE_EXIT.json': dict(returncode=1, no_retry=True),
            'attempt/LAUNCH.json': dict(pid=2147483642),
            'MAIN_DISPATCH.json': dict(pid=2147483641),
            'attempt/DISPATCH_ONCE.json': dict(no_retry=True),
        }.items():
            handoff.saved.write(predecessor / name, value)
        (predecessor / 'attempt/NATIVE.log').write_text('fixture pre-model actual_timeout_parent')
        pins = {name: handoff.saved.sha(predecessor / name) for name in handoff.RECOVERY_PINS}
        stack.enter_context(patch.object(handoff, 'RECOVERY_PINS', pins))
        self.output = self.base / 'orch_r166_retelling_C5_recovery_fixture'
        return predecessor

    def recovery_ready(self):
        predecessor = self.recovery_fixture()
        handoff.stage_recovery(self.cpu, self.output)
        ready = handoff.preflight(self.output, recovery=True)
        return predecessor, ready

    def test_recovery_exact_failure_and_absence_custody_without_signals(self):
        predecessor = self.recovery_fixture()
        before = handoff.saved.files(predecessor)
        with patch.object(handoff.signal, 'pidfd_send_signal') as signals:
            handoff.stage_recovery(self.cpu, self.output)
            ready = handoff.preflight(self.output, recovery=True)
        signals.assert_not_called()
        self.assertEqual(handoff.saved.files(predecessor), before)
        self.assertFalse(ready['original_owners_alive'])
        self.assertEqual(ready['required_GO_binding']['boundary_rule'], handoff.RECOVERY_BOUNDARY_RULE)
        self.assertEqual(handoff.saved.bound(ready['required_GO_binding']['cpu_proof']), self.recovery_proof)
        self.assertFalse((self.output / 'OWNER_RETIRED.json').exists())
        self.assertFalse((self.output / 'ACTIVATE_ONCE').exists())
        self.assertRaises(FileExistsError, handoff.preflight, self.output, recovery=True)

    def test_recovery_refuses_tampered_failure_and_live_predecessor(self):
        predecessor = self.recovery_fixture()
        with patch.object(handoff, 'require_retired', side_effect=ValueError('live_owner')):
            self.assertRaisesRegex(ValueError, 'live_owner', handoff.stage_recovery, self.cpu, self.output)
        target = predecessor / 'attempt/NATIVE.log'
        target.write_text('a different failure')
        self.assertRaisesRegex(ValueError, 'exact_known_premodel_failure', handoff.recovery_evidence)
        self.assertFalse(self.output.exists())

    def test_recovery_rejects_unsaved_suffix_and_checkpoint_tamper(self):
        self.recovery_fixture()
        with patch.object(handoff.saved, 'saved_boundary', return_value=None):
            self.assertRaisesRegex(ValueError, 'exact_saved28', handoff.recovery_evidence)
        target = Path(self.plan['root']) / 'checkpoints/sleep_000001/adapter.fixture'
        target.write_bytes(b'tampered')
        self.assertRaisesRegex(ValueError, 'full_recovery_checkpoint_custody', handoff.recovery_evidence)

    def test_recovery_rejects_source_and_plan_drift(self):
        self.recovery_ready()
        request = handoff.saved.read(self.output / 'REQUEST.json')
        request['policy_scope']['parented'] = False
        self.assertRaisesRegex(ValueError, 'only_recovery_source_CPU_namespace_delta',
            handoff.validate_recovery_request, self.output, request)
        changed = dict(self.plan, new_presentations=17)
        self.assertRaisesRegex(ValueError, 'birth_experiment', handoff.check_plan_delta, self.plan, changed)

    def test_recovery_requires_distinct_fresh_GO_and_cannot_use_ordinary_execute(self):
        predecessor, ready = self.recovery_ready()
        go = dict(schema=handoff.RECOVERY_GO_SCHEMA, issuer='Main', decision='GO',
            not_before_unix=handoff.saved.NEW_WALL-3600, expires_unix=handoff.saved.NEW_WALL-1800,
            binding=ready['required_GO_binding'])
        path = self.write('RECOVERY_GO.json', go)
        handoff.recovery_binding(self.output, path, handoff.saved.sha(path))
        self.assertRaisesRegex(ValueError, 'ordinary_execute_not_retired_recovery',
            handoff.activation_binding, self.output, path, handoff.saved.sha(path))
        for delta in (dict(schema=handoff.GO_SCHEMA), dict(issuer='worker'), dict(binding={}),
                      dict(expires_unix=handoff.saved.NEW_WALL-3601)):
            path.write_text(json.dumps(dict(go, **delta)))
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                handoff.recovery_binding(self.output, path, handoff.saved.sha(path))

    def recovery_execution_fixture(self, failure=False, lock_busy=False):
        predecessor, ready = self.recovery_ready()
        go = dict(schema=handoff.RECOVERY_GO_SCHEMA, issuer='Main', decision='GO',
            not_before_unix=handoff.saved.NEW_WALL-3600, expires_unix=handoff.saved.NEW_WALL-1800,
            binding=ready['required_GO_binding'])
        path = self.write('RECOVERY_GO.json', go)
        guard_spec = importlib.util.spec_from_file_location('recovery_fixture_guard',
            Path(handoff.__file__).resolve().parent / 'orch_r125_continual_guard.py')
        guard = importlib.util.module_from_spec(guard_spec)
        guard_spec.loader.exec_module(guard)
        paths = (str(self.output / 'source' / handoff.RELATIVE),
                 str(self.output / 'source' / handoff.saved.RELATIVE),
                 str(self.output / 'source' / handoff.POLICY_RELATIVE))

        def guard_validate(config_path):
            config = handoff.saved.read(config_path)
            return config, handoff.saved.read(config['plan_path'])

        report = dict(clear=True, scanner_euid=0, blocking_reasons=[], device_minor=5,
                      gpu=dict(uuid=self.plan['gpu_uuid'], index=5))

        def dispatch(command, check):
            config_path = self.output / 'control/GUARD.json'
            config, plan = guard_validate(config_path)
            attempt = Path(config['attempt_dir'])
            self.assertTrue((attempt / 'DISPATCH_ONCE').is_dir())
            parent_pid = os.getppid()
            ticks = Path('/proc', str(parent_pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            handoff.saved.write(attempt / 'LAUNCH.json', dict(pid=parent_pid, parent_start_ticks=ticks,
                guard_sha256=handoff.saved.sha(config_path), admission_sha256=handoff.saved.sha(attempt / 'ADMISSION.json'),
                admission_verified_unix=handoff.saved.read(attempt / 'ADMISSION_TIME.json')['verified_unix']))
            reader, writer = os.pipe()
            with os.fdopen(writer, 'wb') as startup_writer:
                startup_writer.write(b'LAUNCH_READY\n')
            with os.fdopen(reader, 'rb') as startup_reader, patch.object(guard.sys, 'stdin', startup_reader), \
                    patch.dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']):
                guard.native_entry(config_path)
            return SimpleNamespace(returncode=0)

        with patch.object(handoff, '__file__', paths[0]), patch.object(handoff.saved, '__file__', paths[1]), \
                patch.object(handoff.retelling, '__file__', paths[2]), \
                patch.object(guard, 'validate', side_effect=guard_validate), \
                patch.dict(sys.modules, {'gpu.orch_r125_continual_guard': guard}), \
                patch.object(handoff.signal, 'pidfd_send_signal') as signals, \
                patch.object(handoff.subprocess, 'check_output', return_value=json.dumps(report),
                    side_effect=ValueError('uncertain_scan') if failure else None) as scanner, \
                patch.object(handoff.subprocess, 'run', side_effect=dispatch) as dispatching, \
                patch.object(guard.child, 'run') as model:
            import gpu
            with patch.object(gpu, 'orch_r125_continual_guard', guard, create=True):
                if lock_busy:
                    descriptor = os.open(self.base / 'orch_r157_C5_HANDOFF.lock', os.O_CREAT | os.O_RDWR, 0o600)
                    try:
                        handoff.fcntl.flock(descriptor, handoff.fcntl.LOCK_EX | handoff.fcntl.LOCK_NB)
                        self.assertRaises(BlockingIOError, handoff.execute_recovery,
                            self.output, path, handoff.saved.sha(path))
                    finally:
                        os.close(descriptor)
                    self.assertFalse((self.output / 'ACTIVATE_ONCE').exists())
                    scanner.assert_not_called()
                    signals.assert_not_called()
                    return
                elif failure:
                    self.assertRaisesRegex(ValueError, 'uncertain_scan', handoff.execute_recovery,
                        self.output, path, handoff.saved.sha(path))
                else:
                    handoff.execute_recovery(self.output, path, handoff.saved.sha(path))
                self.assertRaises(FileExistsError, handoff.execute_recovery,
                    self.output, path, handoff.saved.sha(path))
            scanner.assert_called_once()
            if failure:
                dispatching.assert_not_called()
                model.assert_not_called()
            else:
                dispatching.assert_called_once()
                model.assert_called_once_with(str(self.output / 'control/PLAN.json'), resume=True)
            signals.assert_not_called()
        self.assertFalse((self.output / 'OWNER_RETIRED.json').exists())
        self.assertTrue(handoff.saved.read(self.output / 'RECOVERY_EXECUTION.json')['no_retirement_performed'])
        config = handoff.saved.read(self.output / 'control/GUARD.json')
        self.assertTrue(config['resume'])
        self.assertEqual(config['hard_end_unix'], self.config['hard_end_unix'])

    def test_recovery_execution_reuses_strict_supervisor_and_never_retires(self):
        self.recovery_execution_fixture()

    def test_uncertain_recovery_never_replays_or_retires(self):
        self.recovery_execution_fixture(failure=True)
        self.assertTrue(handoff.saved.read(self.output / 'RECOVERY_FAILED.json')['no_retry'])

    def test_recovery_respects_original_per_life_owner_lock(self):
        self.recovery_execution_fixture(lock_busy=True)

    def test_uncertain_exit_preserves_intent_never_retries_or_claims_no_stop(self):
        self.stage()
        self.saved_life()
        events = []
        with self.assertRaisesRegex(ValueError, 'natural_exact_owned_exit'):
            self.execute_fixture(events, uncertain_exit=True)
        self.assertIn(handoff.signal.SIGTERM, events)
        self.assertNotIn('strict_successor', events)
        failure = handoff.saved.read(self.output / 'ACTIVATION_FAILED.json')
        self.assertTrue(failure['termination_intent_recorded'])
        self.assertFalse(failure['original_exit_confirmed'])
        self.assertTrue(failure['no_retry'])
        self.assertEqual(failure['recovery_disposition'], 'VERIFY_EXACT_OWNER_AND_SAVED_BOUNDARY_NO_AUTOMATIC_RETRY')


if __name__ == '__main__':
    unittest.main()
