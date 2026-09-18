from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_feedback_uptake_r120_headroom as subject


class HeadroomTests(unittest.TestCase):
    def proposal(self, family='BASE_R110'):
        return subject.propose(family=family, root='/node/math', original_limits=dict(cycles=96,native=1536,parent=288),
            used=dict(native=547,parent=103), next_cycle=35,
            clock_reference={'path':'/clock','sha256':'a'*64}, train_end_unix=200000, hard_end_unix=200120,
            historical_binding={'path':'/old','sha256':'b'*64}, now=1000)

    def boundary(self, proposal):
        return dict(root=proposal['root'], kind=proposal['schedule']['safe_boundary'],
            inflight_native=0,inflight_parent=0,inflight_optimizer=0,next_cycle=36,completed_cycle=35,
            readout_complete=True,context_saved=True,counters_before=dict(native=560,parent=105),
            counters_after=dict(native=560,parent=105),clock=proposal['clock'],hard_end_unix=200120,
            current_source={'path':'/source','sha256':'c'*64},context_reference={'path':'/context','sha256':'d'*64},
            readout_reference={'path':'/readout','sha256':'e'*64})

    def test_headroom_keeps_history_and_usage(self):
        proposal = self.proposal()
        self.assertGreaterEqual(proposal['additional_cycle_capacity'],4096)
        self.assertEqual(proposal['original_limits'],dict(cycles=96,native=1536,parent=288))
        self.assertEqual(proposal['cumulative_used_at_proposal'],dict(native=547,parent=103))
        self.assertFalse(proposal['quota_exhaustion_is_life_end'])
        self.assertFalse(proposal['shared_startup_files_changed'])

    def test_old43_or96_cannot_end_successor(self):
        for family in subject.SCHEDULES:
            proposal=self.proposal(family)
            limits=proposal['effective_limits']
            used={key:limits[key]-1 for key in ('native','parent')}
            result=subject.grow_before_cycle(proposal,used=used,next_cycle=limits['cycles'])
            self.assertGreater(result['effective_limits']['cycles'],limits['cycles'])
            self.assertEqual(result['cumulative_used_at_last_check'],used)
            self.assertEqual(result['hard_end_unix'],proposal['hard_end_unix'])

    def test_healthy_boundary_allowed(self):
        proposal=self.proposal()
        self.assertEqual(subject.validate_boundary(proposal,self.boundary(proposal),now=1001),dict(native=560,parent=105))

    def test_partial_counters_clock_cursor_or_hidden_reset_rejected(self):
        proposal=self.proposal()
        changes=[('inflight_native',1),('inflight_parent',1),('inflight_optimizer',1),
            ('next_cycle',35),('readout_complete',False),('context_saved',False),
            ('counters_after',dict(native=0,parent=0)),('hard_end_unix',200121)]
        for key,value in changes:
            boundary=self.boundary(proposal);boundary[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                subject.validate_boundary(proposal,boundary,now=1001)

    def test_lease_remains_binding(self):
        proposal=self.proposal()
        with self.assertRaisesRegex(ValueError,'lease_training_cutoff'):
            subject.validate_boundary(proposal,self.boundary(proposal),now=proposal['train_end_unix'])

    def test_shared_requires_actual_commit_reload_and_Main_extension(self):
        proposal=self.proposal('SHARED_F2_A2');boundary=self.boundary(proposal)
        boundary.update(committed_generation=1,mounted_generation=1,committed_checkpoint_sha256='f'*64,
            mounted_checkpoint_sha256='f'*64,optimizer_owner='F1',local_optimizer_steps=0)
        with self.assertRaisesRegex(ValueError,'Main_common_safe_boundary'):
            subject.validate_boundary(proposal,boundary,now=1001)
        boundary.update(common_extension_reference={'path':'/extension','sha256':'g'*64},common_extension_coordinated=True)
        subject.validate_boundary(proposal,boundary,now=1001)
        boundary['mounted_generation']=0
        with self.assertRaisesRegex(ValueError,'committed_reloaded'):
            subject.validate_boundary(proposal,boundary,now=1001)

    def test_no_usage_reset_or_noninteger(self):
        for used in (dict(native=0,parent=0),dict(native=True,parent=103)):
            with self.assertRaises(ValueError):
                subject.grow_before_cycle(self.proposal(),used=used,next_cycle=35)

    def test_append_only_overlay_never_writes_CONFIG(self):
        proposal=self.proposal();boundary=self.boundary(proposal)
        cohort_ref={'path':'/cohort','sha256':'h'*64}
        cohort=dict(root='/node/math',first_cycle=36,last_cycle=99,train_per_cycle=2,prior_ids_excluded=True,
            question_hash_collisions=0,sealed_FINAL_in_parent_or_rows=False)
        with tempfile.TemporaryDirectory() as directory:
            def verify(binding):
                if binding == cohort_ref:
                    return cohort
                if binding == proposal['clock']:
                    return dict(train_end_unix=200000,hard_end_unix=200120)
                return {}
            reference=subject.commit_overlay(directory,proposal,boundary,cohort_ref,
                verify=verify,now=1001)
            self.assertEqual(list(Path(directory).glob('CONFIG*')),[])
            self.assertEqual(subject.checked(reference)['boundary']['counters_before'],dict(native=560,parent=105))
            with self.assertRaises(FileExistsError):
                subject.commit_overlay(directory,proposal,boundary,cohort_ref,
                    verify=verify,now=1001)

    def test_clock_reference_contents_cannot_slide_wall(self):
        proposal=self.proposal()
        with tempfile.TemporaryDirectory() as directory,self.assertRaisesRegex(ValueError,'actual_clock_bytes'):
            subject.commit_overlay(directory,proposal,self.boundary(proposal),{'path':'/cohort','sha256':'h'*64},
                verify=lambda binding:dict(train_end_unix=200001,hard_end_unix=200121),now=1001)

    def test_historic_checkpoint_preferred(self):
        result=subject.learned_lineage(historic_checkpoint={'path':'/historic'},shared_checkpoint=None,
            base_context=None,optimizer_loaded=False)
        self.assertIn('ELICITATION_ONLY',result['label'])
        self.assertTrue(result['prior_learned_lineage_claim'])

    def test_explicit_fork_no_fictitious_learned_history(self):
        shared=dict(generation=1,checkpoint_sha256='43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d')
        result=subject.learned_lineage(historic_checkpoint=None,shared_checkpoint=shared,
            base_context={'path':'/actual/context'},optimizer_loaded=False)
        self.assertFalse(result['prior_learned_lineage_claim'])
        self.assertFalse(result['optimizer_loaded'])
        for context,optimizer in ((None,False),({'path':'/actual/context'},True)):
            with self.assertRaises(ValueError):
                subject.learned_lineage(historic_checkpoint=None,shared_checkpoint=shared,
                    base_context=context,optimizer_loaded=optimizer)


if __name__ == '__main__':
    unittest.main()
