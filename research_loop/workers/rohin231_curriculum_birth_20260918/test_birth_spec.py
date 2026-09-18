from pathlib import Path
import unittest

from birth_spec import extract_birth, stage0_metrics
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory


ROOT = Path(__file__).resolve().parent


class BirthTests(unittest.TestCase):
    def test_existing_confinement_bound_to_actual_owner_and_finite_wall(self):
        from r231_runtime import receiving_command
        arguments = ['--property=User=2524', '--property=Group=2524',
                     '--property=RuntimeMaxSec=7200', '--property=DevicePolicy=strict']
        actual = receiving_command(arguments, 'child', 16000, 2000)
        self.assertIn('--property=User=1352', actual)
        self.assertIn('--property=Group=1352', actual)
        self.assertIn('--property=DevicePolicy=strict', actual)
        self.assertIn('--property=RuntimeMaxSec=13985', actual)

    def test_probe_remains_short_and_missing_owner_fails(self):
        from r231_runtime import receiving_command
        arguments = ['--property=User=2524', '--property=Group=2524', '--property=RuntimeMaxSec=60']
        self.assertIn('--property=RuntimeMaxSec=60', receiving_command(arguments, 'probe', 16000, 2000))
        with self.assertRaises(ValueError):
            receiving_command(arguments[1:], 'probe', 16000, 2000)

    def test_exact_birth_source_and_six_paragraphs(self):
        text = extract_birth((ROOT / 'BIRTH_SPEC_SOURCE.md').read_bytes())
        self.assertEqual(text, (ROOT / 'BIRTH_PROMPT.txt').read_text())
        self.assertEqual(len(text.split('\n\n')), 6)

    def test_document_modification_rejected(self):
        with self.assertRaises(ValueError):
            extract_birth((ROOT / 'BIRTH_SPEC_SOURCE.md').read_bytes() + b'changed')

    def test_birth_remains_exact_after_compaction_and_restore(self):
        birth = (ROOT / 'BIRTH_PROMPT.txt').read_text()
        history = TrainHistory(system_prompt='fixed test system', birth_prompt=birth)
        event = TrainEvent(event_id='child:fixture', actor='child', text='A synthetic actual calculation: 2 + 2 = 4.',
                           split='TRAIN', phase='experience', episode_id='fixture', source_id='fixture',
                           source_sha256='1' * 64, origin='TRAIN_COLLECTION')
        history.append(event)
        summary = TrainEvent(event_id='child:summary', actor='child', text='Synthetic summary: checked a calculation.',
                           split='TRAIN', phase='compaction', episode_id='fixture', source_id='fixture-summary',
                           source_sha256='2' * 64, origin='TRAIN_COLLECTION')
        history.compact(summary, through=history.frontier())
        restored = TrainHistory.restore(history.checkpoint())
        for candidate in (history, restored):
            rendered = candidate.render(lambda messages: sum(len(message['content']) for message in messages), 30000)
            self.assertEqual(rendered.messages[1]['content'], birth)
            self.assertEqual(sum(message['content'] == birth for message in rendered.messages), 1)
            self.assertTrue(rendered.labels and all(label == -100 for label in rendered.labels))
            self.assertEqual(rendered.target_token_ids, ())
        self.assertEqual(history.working_state['entries'], [])

    def test_stage0_needs_three_checked_non_intention_results(self):
        good = dict(correct_checked_result=True, evidence_verified=True, intention_only_act=False)
        self.assertFalse(stage0_metrics([good, good])['advance_eligible'])
        self.assertTrue(stage0_metrics([good, good, good])['advance_eligible'])
        self.assertFalse(stage0_metrics([good, good, dict(good, intention_only_act=True)])['advance_eligible'])

    def test_unknown_or_unverified_never_promotes(self):
        good = dict(correct_checked_result=True, evidence_verified=True, intention_only_act=False)
        self.assertFalse(stage0_metrics([good, good, dict(good, evidence_verified=False)])['advance_eligible'])
        self.assertFalse(stage0_metrics([good, good, dict(good, intention_only_act=None)])['advance_eligible'])


if __name__ == '__main__':
    unittest.main()
