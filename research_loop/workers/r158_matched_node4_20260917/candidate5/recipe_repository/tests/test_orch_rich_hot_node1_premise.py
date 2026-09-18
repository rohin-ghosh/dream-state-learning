import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import orch_rich_hot_node1_premise as policy
from gpu.orch_rich_hot_node1_premise_board import observation, require_board


class PremisePreservingTests(unittest.TestCase):
    def test_only_requested_slot_and_unchanged_unhinted_control(self):
        original=policy.previous.messages(dict(question='Given facts'), 'ORIGINAL_RICH')
        self.assertEqual(policy.allocation(3),policy.previous.allocation(3))
        for index in (0,1,2,4,5,6,7):
            with self.assertRaises(ValueError):policy.allocation(index)
        self.assertEqual(original,policy.previous.messages(dict(question='Given facts'),'ORIGINAL_RICH'))
        self.assertIn('EXHAUSTION_ONLY',original[0]['content'])

    def test_exact_givens_and_gold_visibility(self):
        question='Two people share 18 units equally at the given rate.'
        messages=policy.messages(dict(question=question,gold='GOLD_CANARY'),'LIGHT_BRANCH')
        self.assertEqual(messages[1]['content'],question)
        self.assertNotIn('GOLD_CANARY',str(messages))
        self.assertIn('sharing rule',messages[0]['content'])
        self.assertIn('Do not invent',messages[0]['content'])

    def test_different_methods_without_fabricating_second(self):
        self.assertIn('two materially different solution methods',policy.INSTRUCTION)
        self.assertIn('explicitly report that inability',policy.INSTRUCTION)
        self.assertIn('hypothetical problem with changed givens',policy.INSTRUCTION)
        self.assertIn('instead of falsely rejecting one',policy.INSTRUCTION)

    def test_old_approach_counts_not_promoted_to_methods(self):
        result=policy.assess(dict(raw='WORKED_APPROACH_COUNT: 2\nREJECTED_APPROACH: changed rate'))
        self.assertEqual(result['self_reported_worked_approach_count'],2)
        self.assertIsNone(result['self_reported_worked_method_count'])
        self.assertIsNone(result['semantic_verified_worked_method_count'])
        self.assertFalse(result['premise_variants_count_as_methods'])

    def test_method_claims_and_inability_stay_unverified(self):
        result=policy.assess(dict(raw='WORKED_METHOD_COUNT: 1\nPREMISES_PRESERVED: YES\nINABILITY: no distinct second method\nREJECTED_METHOD: NONE'))
        self.assertEqual(result['self_reported_worked_method_count'],1)
        self.assertEqual(result['self_reported_premises_preserved'],'YES')
        self.assertIsNone(result['semantic_verified_premise_preservation'])
        self.assertFalse(result['admission'])
        self.assertTrue(result['earlier_9_of_12_not_method_branch_evidence'])

    def test_unchanged_oracle_context_and_quota(self):
        self.assertIs(policy.outcome,policy.previous.outcome)
        self.assertEqual(policy.MAX_CALLS,policy.previous.MAX_CALLS)
        self.assertEqual(policy.token_budget(32000),768)
        self.assertEqual(policy.protocol()['preserved_unhinted_slots'],[0,1])

    def test_board_exact_publication_required(self):
        requirement=dict(expected_line='EXACT MAIN ALLOCATION')
        with self.assertRaises(ValueError):observation('staged request only',requirement)
        with self.assertRaises(ValueError):observation('EXACT MAIN ALLOCATION extra',requirement)
        self.assertEqual(observation('header\nEXACT MAIN ALLOCATION\n',requirement)['index'],3)

    def test_missing_board_approval_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            requirement=root/'BOARD_REQUIREMENT.json'
            requirement.write_text(json.dumps(dict(expected_line='EXACT MAIN ALLOCATION')))
            (root/'PUBLICATION.json').write_text(json.dumps(dict(files={'BOARD_REQUIREMENT.json':hashlib.sha256(requirement.read_bytes()).hexdigest()})))
            with patch.object(policy,'ROOT',str(root)):
                with self.assertRaises(FileNotFoundError):require_board(root,3)

    def test_board_gate_precedes_any_stop_or_launch(self):
        from gpu import orch_rich_hot_node1_premise_run as runner
        from gpu import orch_rich_hot_node1_premise_boundary as boundary
        with patch.object(runner.scanner,'host'), patch.object(runner,'require_board',side_effect=RuntimeError('BOARD_REQUIRED')), patch.object(runner.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(RuntimeError,'BOARD_REQUIRED'):
                runner.supervise(Path(policy.ROOT),3)
            launch.assert_not_called()
        with patch.object(boundary.scanner,'host'), patch.object(boundary,'require_board',side_effect=RuntimeError('BOARD_REQUIRED')), patch.object(boundary.os,'killpg') as stop:
            with self.assertRaisesRegex(RuntimeError,'BOARD_REQUIRED'):
                boundary.checkpoint(Path('/prior'),Path(policy.ROOT),3,Path('/floor'))
            stop.assert_not_called()
