"""Synthetic CPU regressions, never sent to a live child or parent."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[6] / 'tests'))
from test_orch_r184_think_act_learn import ThinkActLearnTests
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, STAGE_BOUNDARY_POLICY
from gpu.orch_r193_continuity import SCHEMA as CONTINUITY_SCHEMA
from organism_v6.orch_r194_code_target_filter import REVIEW_POLICY
import r210_homework as homework


class HomeworkTests(unittest.TestCase):
    setUp = ThinkActLearnTests.setUp
    driver = ThinkActLearnTests.driver
    records = ThinkActLearnTests.records

    def configure(self):
        self.config.update(stage_boundary_policy=STAGE_BOUNDARY_POLICY,
            console_reply_policy=CONSOLE_REPLY_POLICY, continuity_policy=CONTINUITY_SCHEMA,
            pinned_messages_policy='R206_VERBATIM_ROHIN_MESSAGES_V1',
            learn_review_filter=REVIEW_POLICY,
            prose_target_filter='R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1')
        question = publish_parent(self.root, 'Rohin', 'Synthetic homework first, then two drafts.')
        parent = publish_parent(self.root, 'Astra', 'Synthetic parent: explain persistence yourself.')
        for name, value in dict(SOURCE_ID=question['id'], SOURCE_SHA=question['sha256'],
                PARENT_ID=parent['id'], PARENT_SHA=parent['sha256']).items():
            context = patch.object(homework, name, value)
            context.start()
            self.addCleanup(context.stop)
        return question, parent

    def respond(self, driver, after_unix):
        publish_parent(self.root, 'Astra', 'Synthetic feedback on the first actual homework THINK.')
        return homework.wait_for_parent(driver, after_unix, timeout=0)

    def test_two_actual_thinks_parent_feedback_then_one_tooloff_reply(self):
        question, parent = self.configure()
        later = publish_parent(self.root, 'Rohin', 'Synthetic later individual question.')
        calls = []
        driver = self.driver(['First own explanation.', 'Revised own idea.', 'My reply.'],
            lambda origin: calls.append(origin))
        original = homework.wait_for_parent

        def feedback(driver, after_unix):
            publish_parent(self.root, 'Astra', 'Synthetic feedback after actual first THINK.')
            return original(driver, after_unix, timeout=0)

        with patch.object(homework, 'wait_for_parent', side_effect=feedback):
            self.assertTrue(homework.homework_wake(driver))
        self.assertEqual(calls, [])
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK', 'THINK', 'ACT'])
        reply = self.records('R205_CONSOLE_REPLY')[0]
        self.assertEqual(reply['source_inbox_events'][0]['event_id'], 'parent:inbox:' + question['id'])
        self.assertEqual(len(reply['homework_think_origins']), 2)
        self.assertFalse(reply['outcome']['tool_execution_allowed'])
        self.assertEqual(self.records('REQUEST')[-1]['action_policy'], CONSOLE_REPLY_POLICY)
        self.assertNotIn('parent:inbox:' + later['id'], {event.event_id for event in self.stream.history.events})
        self.assertFalse(homework.homework_wake(driver))
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)
        self.assertTrue(all(row['prose_target_filter'] == self.config['prose_target_filter']
            for row in self.stream.rows))
        self.assertTrue(all(not row['prefix_loss'] for row in self.stream.rows))
        self.assertIn('homework', driver.child.calls[0][-1]['content'])
        self.assertNotIn('Answer Rohin\'s actual latest questions', driver.child.calls[0][-1]['content'])

    def test_missing_parent_feedback_never_sends_premature_human_reply(self):
        self.configure()
        driver = self.driver(['First own explanation.'])
        original = homework.wait_for_parent
        with patch.object(homework, 'wait_for_parent',
                side_effect=lambda driver, after_unix: original(driver, after_unix, timeout=0)):
            with self.assertRaisesRegex(RuntimeError, 'actual_parent_feedback_missing'):
                homework.homework_wake(driver)
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK'])

    def test_wrong_hash_rejected_before_generation(self):
        self.configure()
        driver = self.driver([])
        with patch.object(homework, 'SOURCE_SHA', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'genuine_source_hash_mismatch'):
                homework.homework_wake(driver)
        self.assertEqual(driver.child.calls, [])

    def test_other_turns_not_intercepted(self):
        publish_parent(self.root, 'Rohin', 'Another synthetic question, not the homework source.')
        self.assertFalse(homework.homework_wake(self.driver([])))

    def test_reply_phase_enters_learn_and_excludes_corrupt_think(self):
        self.configure()
        driver = self.driver(['First thought.', 'Second thought. 中文', 'English reply.', 'Review.'])
        original = homework.wait_for_parent

        def feedback(driver, after_unix):
            publish_parent(self.root, 'Astra', 'Synthetic feedback after first THINK.')
            return original(driver, after_unix, timeout=0)

        with patch.object(homework, 'wait_for_parent', side_effect=feedback):
            self.assertTrue(homework.homework_wake(driver))
        driver.prepare_sleep(1)
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')],
            ['THINK', 'THINK', 'ACT', 'LEARN'])
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)
        self.assertIn('provisional_english_target_script_quarantine',
            json.dumps(self.records('R195_LEARN_REVIEW')))

    def test_exact_committed_recovery_preserves_rows_and_does_not_replay_reply(self):
        self.configure()
        driver = self.driver(['First thought.', 'Second thought.', 'English reply.', 'Review.'])
        original = homework.wait_for_parent

        def feedback(driver, after_unix):
            publish_parent(self.root, 'Astra', 'Synthetic feedback after first THINK.')
            return original(driver, after_unix, timeout=0)

        with patch.object(homework, 'wait_for_parent', side_effect=feedback):
            homework.homework_wake(driver)
        before = self.stream.checkpoint()
        self.assertFalse(homework.allow_committed_reply_recovery(self.stream))
        with patch.object(homework, 'RECOVERY_STATE_SHA', before['sha256']):
            self.assertTrue(homework.allow_committed_reply_recovery(self.stream))
            self.assertTrue(homework.homework_wake(driver))
        self.assertEqual(before, self.stream.checkpoint())
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)
        driver.prepare_sleep(1)
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)


if __name__ == '__main__':
    unittest.main(defaultTest='HomeworkTests')
