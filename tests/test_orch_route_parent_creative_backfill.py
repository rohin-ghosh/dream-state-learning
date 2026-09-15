from copy import deepcopy
import unittest
from unittest.mock import patch

from gpu import orch_route_parent_creative_backfill as runner
from gpu import orch_route_parent_creative_backfill_parent as parent
from organism_v6 import orch_route_parent_creative_backfill as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


class CreativeBackfillTests(unittest.TestCase):
    def test_exact_authority_allocation_and_caps(self):
        plan=policy.proposal()
        self.assertEqual(plan['physical_index'],1)
        self.assertEqual(policy.ARMS,('GUIDED',))
        self.assertEqual(policy.CAPS['cycles'],4)
        self.assertEqual(policy.CAPS['seconds'],7200)
        self.assertEqual(policy.CAPS['child_calls_per_lane'],256)
        self.assertEqual(policy.CAPS['parent_calls_per_lane'],48)
        self.assertEqual(policy.CAPS['source_calls'],0)
        self.assertEqual(plan['maximum_saved_updates'],sum(GoalReplayLayout(2,policy.presentations_for_cycle(cycle)).updates for cycle in range(1,5)))
        self.assertEqual(plan['authority'],'R104_AND_STANDING_BUILDER_NOT_R105')

    def test_fixed_first_groups_not_score_selection(self):
        original=policy.canonical.cohort(set())
        pristine=deepcopy(original)
        with patch.object(policy,'BASELINE_COHORT_SHA256',policy.digest(original)):
            selected=policy.cohort(set())
        self.assertEqual(original,pristine)
        self.assertEqual(selected['train'],original['train'][:4])
        self.assertEqual(selected['held'],original['held'][:5])
        for group in selected['train']+selected['held']:
            self.assertEqual(len(policy.shared.tasks(group[0])),2)
        self.assertEqual(selected['cell']['style'],'creative')
        self.assertEqual(selected['presentations_by_cycle'],[4,16,16,16])

    def test_cohort_provenance_drift_rejected(self):
        with patch.object(policy,'BASELINE_COHORT_SHA256','bad'):
            with self.assertRaises(ValueError):policy.cohort(set())

    def test_no_extra_cycle_or_control(self):
        for cycle in (0,5,True):
            with self.assertRaises(ValueError):policy.presentations_for_cycle(cycle)
        for arm in ('UNPARENTED','NO_LORA','FROZEN'):
            with self.assertRaises(ValueError):policy.next_identity({},arm,1)

    def test_same_child_lineage_no_reset(self):
        initial=dict(base_sha256='base',state_sha256='initial')
        child=dict(base_sha256='base',state_sha256='learned')
        previous=dict(arm='GUIDED',cycle=1,phase='sleep',status='COMPLETE',output_adapter=child)
        self.assertEqual(policy.next_identity(initial,'GUIDED',2,previous),child)
        for update in (dict(cycle=2),dict(arm='UNPARENTED'),dict(status='FAILED'),dict(output_adapter=dict(child,base_sha256='wrong'))):
            with self.assertRaises(ValueError):policy.next_identity(initial,'GUIDED',2,dict(previous,**update))

    def test_parent_blind_and_actual_creative_provider(self):
        payload=dict(kind='coach',turn=0,task={},public_messages=[],prior_parent_messages=[],learner={})
        result=policy.parent_payload(payload)
        self.assertEqual(result['cell'],policy.CELL)
        self.assertEqual(result['cell']['provider'],'openai/openai/gpt-6-astra')
        for private in ('HELD','sealed_score','/tmp/private'):
            with self.assertRaises(ValueError):policy.parent_payload(dict(payload,learner=dict(text=private)))

    def test_posting_is_required_and_hash_bound(self):
        posted=dict(author='Main',board_posted=True,ready_sha256='ready',proposal_sha256='proposal',builder_receipt='dated actual receipt')
        policy.validate_posted(posted,'ready','proposal')
        for update in (dict(author='Builder'),dict(board_posted=False),dict(ready_sha256='wrong'),dict(proposal_sha256='wrong'),dict(builder_receipt='')):
            with self.assertRaises(ValueError):policy.validate_posted(dict(posted,**update),'ready','proposal')

    def final_receipts(self):
        child=dict(state_sha256='saved')
        sleep=dict(status='COMPLETE',arm='UNPARENTED',cycle=8,phase='sleep',output_adapter=child,process=['boot',1,1])
        readout=dict(status='COMPLETE',arm='UNPARENTED',cycle=8,phase='readout',input_adapter=child,
            parent_free=True,process=['boot',2,2],finished_unix=10)
        return dict(status='COMPLETE',finished_unix=11),sleep,readout

    def test_natural_final_readout_and_exit_required(self):
        guard,sleep,readout=self.final_receipts()
        policy.validate_completion(guard,sleep,readout,False,False)
        for guardian_alive,child_alive in ((True,False),(False,True)):
            with self.assertRaises(ValueError):policy.validate_completion(guard,sleep,readout,guardian_alive,child_alive)
        for update in (dict(cycle=7),dict(parent_free=False),dict(input_adapter={}),dict(process=sleep['process']),dict(status='FAILED')):
            with self.assertRaises(ValueError):policy.validate_completion(guard,sleep,dict(readout,**update),False,False)

    def test_broker_rejects_other_arms_cycles_and_budget(self):
        saved={key:getattr(parent.broker,key) for key in ('ROOT','policy','PATTERN','SYSTEM')}
        try:
            parent.configure()
            payload=policy.parent_payload(dict(kind='coach',turn=0,task={},public_messages=[],prior_parent_messages=[],learner={}))
            request=dict(id='0000_GUIDED_C1',payload=payload)
            self.assertEqual(parent.broker.validated_request('0000_GUIDED_C1.request.json',request),payload)
            for name in ('0000_UNPARENTED_C1.request.json','0000_NO_LORA_C1.request.json','0000_GUIDED_C5.request.json','0048_GUIDED_C1.request.json'):
                with self.assertRaises(ValueError):parent.broker.validated_request(name,request)
        finally:
            for key,value in saved.items():setattr(parent.broker,key,value)

    def test_configuration_only_maps_physical_one(self):
        saved={key:getattr(runner.run,key) for key in ('policy','ROOT','RUN_MODULE','DEVICES')}
        try:
            runner.configure()
            self.assertEqual(runner.run.DEVICES,{'GUIDED':(1,runner.run.guardian.DEVICES[1])})
        finally:
            for key,value in saved.items():setattr(runner.run,key,value)


if __name__=='__main__':
    unittest.main()
