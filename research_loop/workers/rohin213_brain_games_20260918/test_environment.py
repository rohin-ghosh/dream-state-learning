from copy import deepcopy
import json
from pathlib import Path
import unittest

from environment import (CONTEXT_SURFACES, MemoryRound, PuzzleRound, TARGET,
                         activation_status, audit_context, digest)


HERE = Path(__file__).resolve().parent
BANK = json.loads((HERE / 'puzzles.json').read_text())['items']
FIXTURE_CODE = 'K7M2Q9RX'


def clear_surfaces():
    return {name: [] for name in CONTEXT_SURFACES}


def sleep_record(cycle=11, index=30):
    record = dict(kind='SLEEP_COMPLETE', index=index, journal_id='PUBLIC_CPU_FIXTURE',
                  document=dict(cycle=cycle, status='COMPLETE'))
    record['sha256'] = digest(record)
    return record


def memory(condition='NO_EXPLICIT_CONTEXT'):
    instance = MemoryRound(condition=condition, life_id='fixture-life', mode='CPU_FIXTURE', fixture_code=FIXTURE_CODE)
    instance.mark_study_delivered(life_id='fixture-life', request_index=20, cycle=10,
                                  request_sha256='a' * 64, all_history_tokens_masked=True)
    return instance


def completed_memory(condition='NO_EXPLICIT_CONTEXT'):
    instance = memory(condition)
    instance.observe_natural_sleep(life_id='fixture-life', record=sleep_record(), naturally_completed=True)
    return instance


class PuzzleTests(unittest.TestCase):
    def test_four_objective_development_families(self):
        answers = [[2, 2, 4, 7, 9], 2, ['amber', 'blue', 'dune', 'elm'], True]
        for task, answer in zip(BANK, answers):
            with self.subTest(task=task['id']):
                game = PuzzleRound(task, mode='CPU_FIXTURE')
                receipt = game.answer(answer)
                self.assertEqual(receipt['status'], 'CORRECT')
                self.assertTrue(receipt['closed'])
                self.assertFalse(receipt['answer_key_disclosed'])

    def test_alternative_shortest_path_is_accepted(self):
        game = PuzzleRound(BANK[2], mode='CPU_FIXTURE')
        self.assertEqual(game.answer(['amber', 'coral', 'dune', 'elm'])['status'], 'CORRECT')

    def test_invalid_and_nonshortest_paths_fail(self):
        for answer in (['amber', 'elm'], ['amber', 'blue', 'amber', 'coral', 'dune', 'elm'], ['missing']):
            self.assertEqual(PuzzleRound(BANK[2], mode='CPU_FIXTURE').answer(answer)['status'], 'INCORRECT')

    def test_strict_answer_types_no_boolean_integer_confusion(self):
        self.assertEqual(PuzzleRound(BANK[1], mode='CPU_FIXTURE').answer(2.0)['status'], 'INCORRECT')
        self.assertEqual(PuzzleRound(BANK[3], mode='CPU_FIXTURE').answer(1)['status'], 'INCORRECT')
        self.assertEqual(PuzzleRound(BANK[0], mode='CPU_FIXTURE').answer([True, 2, 4, 7, 9])['status'], 'INCORRECT')

    def test_attempt_budget_and_quit_are_finite(self):
        game = PuzzleRound(BANK[1], mode='CPU_FIXTURE')
        self.assertFalse(game.answer(0)['closed'])
        self.assertTrue(game.answer(0)['closed'])
        with self.assertRaisesRegex(ValueError, 'round_already_closed'):
            game.answer(0)
        quit_game = PuzzleRound(BANK[1], mode='CPU_FIXTURE')
        receipt = quit_game.quit('I have no useful next check; move to another object.')
        self.assertEqual(receipt['status'], 'QUIT')
        self.assertFalse(receipt['mathematical_failure_claimed'])

    def test_no_answer_key_in_question_or_feedback(self):
        game = PuzzleRound(BANK[1], mode='CPU_FIXTURE')
        for view in (game.public_view(), game.answer(0)):
            self.assertNotIn('expected_answer', view)
            self.assertNotIn('solution', view)

    def test_malformed_banks_rejected_before_grading(self):
        for task in (dict(id='bad', kind='checksum', digits='123', modulus=0),
                     dict(id='bad', kind='sort', values=list(range(50))),
                     dict(id='bad', kind='balanced_brackets', text='execute me')):
            with self.assertRaises(ValueError):
                PuzzleRound(task, mode='CPU_FIXTURE')

    def test_candidate_text_is_never_executed(self):
        receipt = PuzzleRound(BANK[1], mode='CPU_FIXTURE').answer('__import__("os").system("false")')
        self.assertEqual(receipt['status'], 'INCORRECT')


class MemoryTests(unittest.TestCase):
    def test_no_probe_before_ordinary_completed_sleep(self):
        with self.assertRaisesRegex(ValueError, 'ordinary_completed_sleep_required'):
            memory().recall_view()

    def test_same_life_forward_verified_sleep_only(self):
        for life, record, natural in [('other', sleep_record(), True),
                                       ('fixture-life', sleep_record(cycle=10), True),
                                       ('fixture-life', sleep_record(index=19), True),
                                       ('fixture-life', sleep_record(), False)]:
            with self.assertRaises(ValueError):
                memory().observe_natural_sleep(life_id=life, record=record, naturally_completed=natural)
        tampered = sleep_record()
        tampered['document']['cycle'] = 12
        with self.assertRaisesRegex(ValueError, 'sleep_record_hash_mismatch'):
            memory().observe_natural_sleep(life_id='fixture-life', record=tampered, naturally_completed=True)

    def test_study_needs_own_masked_request(self):
        instance = MemoryRound(condition='NO_EXPLICIT_CONTEXT', life_id='fixture-life',
                               mode='CPU_FIXTURE', fixture_code=FIXTURE_CODE)
        with self.assertRaises(ValueError):
            instance.mark_study_delivered(life_id='fixture-life', request_index=20, cycle=10,
                                          request_sha256='a' * 64, all_history_tokens_masked=False)

    def test_explicit_context_is_not_adapter_memory(self):
        game = completed_memory('EXPLICIT_CONTEXT')
        self.assertIn(FIXTURE_CODE, json.dumps(game.recall_view()))
        receipt = game.answer(FIXTURE_CODE, surfaces=clear_surfaces())
        self.assertEqual(receipt['interpretation'], 'CONTEXT_ASSISTED_ONLY')
        self.assertFalse(receipt['adapter_retention_claim_allowed'])

    def test_absent_context_never_becomes_adapter_claim(self):
        game = completed_memory()
        self.assertNotIn(FIXTURE_CODE, json.dumps(game.recall_view()))
        self.assertNotIn(FIXTURE_CODE, json.dumps(game.coaching_view()))
        receipt = game.answer(FIXTURE_CODE, surfaces=clear_surfaces())
        self.assertEqual(receipt['status'], 'CORRECT')
        self.assertEqual(receipt['interpretation'], 'UNATTRIBUTED_RECALL_NOT_ADAPTER_RETENTION')
        self.assertFalse(receipt['adapter_retention_claim_allowed'])
        self.assertNotIn(FIXTURE_CODE, json.dumps(receipt))

    def test_carried_answer_changes_interpretation(self):
        for surface in CONTEXT_SURFACES:
            game = completed_memory()
            surfaces = clear_surfaces()
            surfaces[surface] = ['Remember: ' + FIXTURE_CODE]
            result = game.answer(FIXTURE_CODE, surfaces=surfaces)
            self.assertEqual(result['interpretation'], 'CONTEXT_ASSISTED_ONLY')
            self.assertEqual(result['context_audit']['matched_surfaces'], [surface])

    def test_missing_surfaces_are_unverified(self):
        receipt = completed_memory().answer(FIXTURE_CODE, surfaces={})
        self.assertEqual(receipt['interpretation'], 'UNVERIFIED_CONTEXT')
        self.assertEqual(len(receipt['context_audit']['missing_surfaces']), len(CONTEXT_SURFACES))

    def test_fullwidth_and_spaced_copy_detected_without_mutating_raw(self):
        surfaces = clear_surfaces()
        surfaces['working_state'] = ['Ｋ ７ Ｍ ２ Ｑ ９ Ｒ Ｘ']
        original = deepcopy(surfaces)
        audit = audit_context(FIXTURE_CODE, surfaces)
        self.assertEqual(audit['matched_surfaces'], ['working_state'])
        self.assertEqual(surfaces, original)

    def test_private_state_roundtrip_across_sleep(self):
        studied = memory()
        private = json.loads(json.dumps(studied.operator_state()))
        self.assertTrue(private['operator_only_contains_answer_key'])
        restored = MemoryRound.restore_operator_state(private)
        restored.observe_natural_sleep(life_id='fixture-life', record=sleep_record(), naturally_completed=True)
        self.assertEqual(restored.answer(FIXTURE_CODE, surfaces=clear_surfaces())['status'], 'CORRECT')

    def test_no_study_replay_no_repeated_guessing(self):
        game = completed_memory()
        with self.assertRaises(ValueError):
            game.study_view()
        game.answer('WRONG000', surfaces=clear_surfaces())
        with self.assertRaises(ValueError):
            game.answer(FIXTURE_CODE, surfaces=clear_surfaces())

    def test_quitting_does_not_force_or_pause_a_sleep(self):
        game = memory()
        self.assertEqual(game.quit('I will leave this round and continue my other work.')['status'], 'QUIT')
        with self.assertRaises(ValueError):
            game.observe_natural_sleep(life_id='fixture-life', record=sleep_record(), naturally_completed=True)

    def test_synthetic_sleep_cannot_be_relabelled_live(self):
        game = memory()
        game.mode = 'LIVE_DEVELOPMENT'
        record = sleep_record()
        record['synthetic'] = True
        record['sha256'] = digest({key: value for key, value in record.items() if key != 'sha256'})
        with self.assertRaisesRegex(ValueError, 'synthetic_sleep_cannot_be_live_evidence'):
            game.observe_natural_sleep(life_id='fixture-life', record=record, naturally_completed=True)

    def test_parent_overview_and_guidance_do_not_contain_fixture_key(self):
        for name in ('OVERVIEW.md', 'PARENT_GUIDANCE.md'):
            text = (HERE / name).read_text()
            self.assertNotIn(FIXTURE_CODE, text)
            self.assertFalse(any(0x3400 <= ord(character) <= 0x9fff for character in text))


class ActivationTests(unittest.TestCase):
    def release(self):
        return dict(status='RELEASED_BY_MAIN', approved_by='Main', target_life=TARGET,
                    overview_sha256='e' * 64, no_pause=True,
                    original_c2_overview_ack=dict(original_life_id='original-C2', operator_confirmed_understanding=True,
                        request=dict(kind='REQUEST', index=10, sha256='a' * 64),
                        response=dict(kind='RESPONSE', index=11, sha256='b' * 64)),
                    original_c2_rohin_exchange=dict(original_life_id='original-C2', genuine_rohin_turn=True, human_inbox_id='1' * 32,
                        request=dict(kind='REQUEST', index=20, sha256='c' * 64),
                        response=dict(kind='RESPONSE', index=21, sha256='d' * 64)))

    def test_default_cannot_start_live(self):
        self.assertFalse(activation_status(None, 'e' * 64)['ready'])
        with self.assertRaisesRegex(ValueError, 'activation_condition_not_met'):
            PuzzleRound(BANK[0], mode='LIVE_DEVELOPMENT')
        with self.assertRaises(ValueError):
            MemoryRound(condition='NO_EXPLICIT_CONTEXT', life_id=TARGET, mode='LIVE_DEVELOPMENT')

    def test_attestation_shape_is_not_automatic_dispatch(self):
        status = activation_status(self.release(), 'e' * 64)
        self.assertTrue(status['ready'])
        self.assertIn('NOT_AUTOMATIC_DISPATCH', status['reason'])

    def test_stale_overview_wrong_clone_or_pause_rejected(self):
        for key, value in [('overview_sha256', 'f' * 64), ('target_life', 'P7'), ('no_pause', False)]:
            release = self.release()
            release[key] = value
            self.assertFalse(activation_status(release, 'e' * 64)['ready'])

    def test_render_only_or_fake_human_is_insufficient(self):
        release = self.release()
        release['original_c2_overview_ack']['operator_confirmed_understanding'] = False
        self.assertFalse(activation_status(release, 'e' * 64)['ready'])
        release = self.release()
        release['original_c2_rohin_exchange']['genuine_rohin_turn'] = False
        self.assertFalse(activation_status(release, 'e' * 64)['ready'])

    def test_conversation_must_follow_overview_and_not_be_synthetic(self):
        release = self.release()
        release['original_c2_rohin_exchange']['request']['index'] = 8
        self.assertFalse(activation_status(release, 'e' * 64)['ready'])
        release = self.release()
        release['original_c2_rohin_exchange']['request']['synthetic'] = True
        self.assertFalse(activation_status(release, 'e' * 64)['ready'])


if __name__ == '__main__':
    unittest.main()
