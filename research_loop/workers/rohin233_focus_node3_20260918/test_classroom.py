import unittest
from unittest.mock import patch

import classroom
import handoff
from pathlib import Path
import json
import tempfile
from retirement import sha


class ClassroomTests(unittest.TestCase):
    def test_only_seven_parented_and_no_control(self):
        self.assertEqual(len(classroom.MEMBERS), 7)
        self.assertNotIn('r213_r226_caption_unparented_fork', classroom.MEMBERS)

    def test_same_shared_reading_all_three(self):
        for name in classroom.MATH:
            self.assertIn(classroom.PASSAGE, classroom.shared_prompt(name, 1))

    def test_diverse_cycle_and_own_authorship(self):
        self.assertEqual(classroom.STAGES, ('MATH', 'READ', 'PROBE', 'WRITE', 'GAME'))
        for round_number in range(10):
            for name in classroom.MATH:
                text = classroom.shared_prompt(name, round_number)
                self.assertTrue(text.isascii())
                self.assertLess(len(text), 2200)
                self.assertIn('authors its own words', text)
                self.assertIn('Genuine Rohin instructions have priority', text)

    def test_repetition_changes_parent_not_rows(self):
        text = classroom.shared_prompt(classroom.MATH[0], 0, True)
        self.assertIn('Change the approach now', text)
        self.assertNotIn('exclude', text)

    def test_third_cycle_requires_change_without_response(self):
        self.assertTrue(classroom.due({}, [dict(index=10), dict(index=20), dict(index=30)]))
        self.assertFalse(classroom.due({}, [dict(index=10), dict(index=20)]))
        self.assertFalse(classroom.answered({}, [dict(index=10), dict(index=20), dict(index=30)]))

    def test_repeated_interventions_change_approach(self):
        texts = [classroom.shared_prompt(classroom.MATH[0], 0, True, variation) for variation in range(4)]
        self.assertEqual(len(set(texts)), 4)

    def test_response_needs_subsequent_complete(self):
        self.assertFalse(classroom.due(dict(RESPONSE=dict(index=20)), [dict(index=10)]))
        self.assertTrue(classroom.due(dict(RESPONSE=dict(index=20)), [dict(index=30)]))

    def test_parent_publication_rejects_control_before_any_io(self):
        with patch('classroom.subprocess.run') as runner:
            with self.assertRaises(ValueError):
                classroom.publish(None, None, 'r213_r226_caption_unparented_fork', '', '', None, {}, {})
            runner.assert_not_called()

    def test_unknown_child_rejected(self):
        with self.assertRaises(ValueError):
            classroom.shared_prompt('MATH_C_node4', 0)

    def test_handoff_never_accepts_native_or_reused_pid(self):
        old = dict(pid=100, start_ticks='900', command_sha256='abc', args=['python',
            '/root/r231_parent_operator_v1/r230_curriculum.py', '--output', '/root/r230_curriculum_live_v1'])
        config = dict(old_parent=dict(old))
        handoff.verify_old(Path('/root'), config, old)
        for changed in (dict(old, start_ticks='901'), dict(old, args=old['args'] + ['native']),
                dict(old, command_sha256='def'), dict(old, args=['python', 'other.py'])):
            with self.assertRaises(ValueError):
                handoff.verify_old(Path('/root'), config, changed)

    def test_resume_restores_publication_without_republishing(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            current = {name: dict(old_turn=4) for name in classroom.MEMBERS}
            turn = output / classroom.MATH[0] / 'turn_0000'
            turn.mkdir(parents=True)
            inbox = output / 'inbox.json'
            inbox.write_text('{}')
            prepared = dict(floor=10, before_checkpoint=dict(index=8), stage='R233_CLASSROOM_MATH')
            (turn / 'PREPARED.json').write_text(json.dumps(prepared))
            published = dict(path=str(inbox), sha256=sha(inbox), prepared_sha256=sha(turn / 'PREPARED.json'), id='real-id')
            (turn / 'PUBLISHED.json').write_text(json.dumps(published))
            round_number, math_round, caption_turn, sequence = classroom.restore(None, None, output, current)
            self.assertEqual(round_number, 0)
            self.assertEqual(math_round[classroom.MATH[0]], 0)
            self.assertEqual(sequence[classroom.MATH[0]], 1)
            self.assertEqual(current[classroom.MATH[0]]['publication']['id'], 'real-id')
            self.assertEqual(caption_turn[classroom.CAPTIONS[0]], 5)
            (turn / 'PUBLISHED.json').unlink()
            with self.assertRaisesRegex(ValueError, 'uncertain publication'):
                classroom.restore(None, None, output, {name: dict(old_turn=4) for name in classroom.MEMBERS})

    def test_resume_handoff_only_exact_old_r233_cpu(self):
        old = dict(pid=200, start_ticks='902', command_sha256='xyz', args=['python',
            '/root/r233_classroom_operator_v1/classroom.py', 'serve', '--output', '/root/r233_classroom_handoff_v1/live'])
        handoff.verify_old(Path('/root'), dict(resume_r233=True, old_parent=dict(old)), old)
        with self.assertRaises(ValueError):
            handoff.verify_old(Path('/root'), dict(old_parent=dict(old)), old)


if __name__ == '__main__':
    unittest.main()
