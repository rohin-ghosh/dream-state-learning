from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from gpu.orch_r107_route_parent_long_engine import Engine
from gpu import orch_r107_route_parent_long_protocol as protocol
from gpu import orch_r107_route_parent_long_run as run
from organism_v6 import orch_r107_route_parent_long as policy
from tests.test_orch_r107_route_parent import minimal_engine


class LongRouteTests(unittest.TestCase):
    def envelope(self, suffix=''):
        plan = dict(guidance='Grounded coaching', rationale='Observed uncertainty',
                    order=['TRAIN-test'], episode_guidance={'TRAIN-test':'Consider the actual receipt.'})
        return dict(model=protocol.strong.STRONG, status='completed', usage={'output_tokens':10},
                    output=[dict(type='message', content=[dict(type='output_text', text=json.dumps(plan) + suffix)])])

    def test_twenty_train_episodes_and_fresh_disjoint_readouts(self):
        from organism_v6 import orch_r107_route_parent_r108 as prior
        seen = set()
        for index in (2, 3, 6):
            seen.update(prior.identifiers(prior.cohort([], index)))
        for index in (1, 5):
            cohort = policy.cohort(seen, index)
            self.assertEqual(len(cohort['train']), 10)
            self.assertEqual(sum(len(group['tasks']) for group in cohort['train']), 20)
            self.assertEqual(sum(len(group['tasks']) for group in cohort['held']), 40)
            self.assertFalse(seen & policy.identifiers(cohort))
            seen.update(policy.identifiers(cohort))

    def test_only_released_long_life_slots(self):
        for index in (0, 2, 3, 4, 6, 7):
            with self.assertRaises(ValueError):
                policy.allocation(index)

    def test_separate_additive_caps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in (1, 5):
                for count in range(20):
                    result = run.spend(root, index, 'PARENT', {})
                with self.assertRaises(ValueError):
                    run.spend(root, index, 'PARENT', {})
            self.assertEqual(result['aggregate_number'], 40)
            self.assertEqual(policy.NATIVE_CAP, 700)

    def test_native_cap_consumption_never_resets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [dict(index=1,kind='NATIVE') for count in range(700)]
            (root/'RESERVATIONS.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
            before = (root/'RESERVATIONS.jsonl').read_bytes()
            with self.assertRaises(ValueError):
                run.spend(root, 1, 'NATIVE', {})
            self.assertEqual((root/'RESERVATIONS.jsonl').read_bytes(), before)
            self.assertEqual(run.spend(root, 5, 'NATIVE', {})['aggregate_number'], 701)

    def test_real_minimal_engine_response_contract(self):
        engine = minimal_engine()
        engine.__class__ = Engine
        response = engine.generate([dict(role='user',content='actual prompt')],max_new_tokens=8192)
        self.assertFalse(response['input_truncated'])
        self.assertTrue(response['full_prompt_prefix_verified'])

    def test_modified_prompt_prefix_rejected(self):
        engine = minimal_engine(corrupt=True)
        engine.__class__ = Engine
        with self.assertRaises(AssertionError):
            engine.generate([dict(role='user',content='actual prompt')],max_new_tokens=8192)

    def test_cycle_ten_parent_payload_and_held_exclusion(self):
        group = policy.cohort([], 1)['train'][9]
        engine = minimal_engine('No valid action.')
        engine.__class__ = Engine
        record = policy.episode(group['world'],group['tasks'][0],
            lambda messages:engine.generate(messages,max_new_tokens=8192),{},'Prior own reflection')
        payload = policy.parent_payload(1,10,1,record,['prior reflection'],['prior parent'])
        self.assertEqual(payload['cycle'],10)
        for cycle in (0,11,True):
            with self.assertRaises(ValueError):
                policy.validate_parent_payload(dict(payload,cycle=cycle))
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(dict(payload,held={}))
        self.assertIn('Prior own reflection',record['messages'][0]['content'])

    def test_real_broker_accepts_cycle_ten_without_dispatch(self):
        from gpu.orch_r107_route_parent_long_broker import process, existing
        campaign=Path('/test/campaign_long')
        store=SimpleNamespace(exists=lambda path:True)
        for identifier in ('GUIDED_SLEEP_C1_P1','GUIDED_SLEEP_C10_P2'):
            process(store,campaign,campaign/existing.QUEUE/(identifier+'.request.json'),None,None,0,'hash')
        for identifier in ('GUIDED_SLEEP_C0_P1','GUIDED_SLEEP_C11_P1','GUIDED_SLEEP_C1_P3'):
            with self.assertRaises(ValueError):
                process(store,campaign,campaign/existing.QUEUE/(identifier+'.request.json'),None,None,0,'hash')

    def test_strict_parent_response_unchanged(self):
        envelope=self.envelope()
        self.assertEqual(protocol.parse(envelope,['TRAIN-test']),protocol.STRICT_PARSE(envelope,['TRAIN-test']))
        self.assertEqual(protocol.protocol_status(envelope),'STRICT_JSON')

    def test_exact_redundant_brace_recovery_without_raw_mutation(self):
        envelope=self.envelope('\n}')
        original=deepcopy(envelope)
        with self.assertRaises(json.JSONDecodeError):
            protocol.STRICT_PARSE(envelope,['TRAIN-test'])
        self.assertEqual(protocol.parse(envelope,['TRAIN-test']),protocol.parse(self.envelope(),['TRAIN-test']))
        self.assertEqual(protocol.protocol_status(envelope),'SINGLE_REDUNDANT_CLOSING_BRACE')
        self.assertEqual(envelope,original)

    def test_ambiguous_parent_extra_content_rejected(self):
        for suffix in ('}}',' another answer','\n{}','\n[]','\n{'):
            with self.assertRaises((AssertionError,json.JSONDecodeError)):
                protocol.parse(self.envelope(suffix),['TRAIN-test'])

    def test_repair_does_not_weaken_identity_or_episode_binding(self):
        with self.assertRaises(AssertionError):
            protocol.parse(dict(self.envelope('}'),model='different'),['TRAIN-test'])
        with self.assertRaises(AssertionError):
            protocol.parse(self.envelope('}'),['HELD-forbidden'])

    def test_local_protocol_context_restores_shared_function(self):
        before=protocol.strong.parse
        with protocol.parsing_context():
            self.assertIs(protocol.strong.parse,protocol.parse)
        self.assertIs(protocol.strong.parse,before)

    def test_existing_reasoning_system_and_remaining_context(self):
        self.assertTrue(policy.SYSTEM.startswith('Reason through'))
        self.assertEqual(policy.token_budget(32760),8)
        with self.assertRaises(ValueError):
            policy.token_budget(32768)


if __name__ == '__main__':
    unittest.main()
