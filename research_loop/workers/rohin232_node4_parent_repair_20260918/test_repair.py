"""CPU-only regressions against the real pinned B/C bundles, with no transport."""

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import parent as entrypoint
import repair


PHYSICAL = int(os.environ.get('R232_TEST_PHYSICAL', '3'))


class RepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('subprocess.run', side_effect=AssertionError('no_remote_or_provider_calls')):
            cls.module, cls.frozen, unused_policy, cls.original_config = entrypoint.load_runtime(PHYSICAL)
        cls.repairs = __import__('parent_repairs')

    def setUp(self):
        self.config = copy.deepcopy(self.original_config)
        self.policy = repair.adapt(self.frozen, self.config)
        self.seed = dict(schema=self.frozen.SCHEMA, journal_id='synthetic-test-journal', attempts=[],
            object_delivered_turns={'existing_object': 7}, last_response_count=10,
            last_request_count=10, prospective_request_count=10, credits={}, grammar_delivered=False)
        self.state = dict(split='TRAIN', journal_id='synthetic-test-journal', response_count=11,
            request_count=11, sleep_count=0, head_sha256='f' * 64, caught_up=True, source_bytes=0,
            delivered={}, events=[
                dict(actor='child', record_index=10, record_sha256='a' * 64,
                     text='I choose caption experiment. I have no verified result.'),
                dict(actor='environment', speaker='Tool', record_index=11, record_sha256='b' * 64,
                     text='An actual tool observation.'),
                dict(actor='parent', speaker='Astra', record_index=12, record_sha256='c' * 64,
                     text='A parent question.'),
            ])
        self.memory = self.frozen.memory(self.seed, [], self.state)
        self.details = dict(object_id='existing_object', source_records=[10], disposition='continue',
            next_task=None, perception=dict(record_index=10, record_sha256='a' * 64,
                quote='I choose caption experiment.'), credit=None, relapse_credit_id=None)

    def response(self, message='What next observation would test your caption experiment?', details=None):
        return dict(speak=True, message=message, rationale=json.dumps(self.details if details is None else details))

    def release(self):
        details = copy.deepcopy(self.details)
        details.update(disposition='set_aside', next_task='caption experiment next check',
            continuity=dict(chosen_object=dict(record_index=10, record_sha256='a' * 64,
                quote='caption experiment'), move_kind='test', progress_basis='UNVERIFIED_NEXT_STEP',
                environment_receipts=[]))
        message = ('Shall we set aside this correction as unresolved and not yet verified, '
            'keep your object, and try caption experiment next check?')
        return self.response(message, details)

    def test_only_exact_four_configs_can_bind(self):
        for physical in (0, 1, 4, 7, 8, -1, True, '3'):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'only_four_R230'):
                repair.expected_config(physical)
        for key, value in (
            ('root', '/localhome/local-rohing/orch_other/life'), ('source_root', '/untrusted/source'),
            ('branch', 'C2'), ('programme', 'unparented'), ('cadence_responses', 1),
            ('r175_arm', 'A'), ('r175_word_limit', 999), ('hard_end_unix', 9999999999),
        ):
            candidate = dict(self.config, **{key: value})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'exact_bound_R230_config'):
                repair.adapt(self.frozen, candidate)
        candidate = copy.deepcopy(self.config)
        candidate[repair.MARKER]['source_pins_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_bound_R230_config'):
            repair.adapt(self.frozen, candidate)

    def test_source_pin_and_loaded_source_impersonation_rejected(self):
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary:
            impostor = Path(temporary) / 'impostor.py'
            impostor.write_text('untrusted source')
            with self.assertRaisesRegex(ValueError, 'source_pin_mismatch'):
                repair.checked_file(impostor, '0' * 64)
        impostor = types.SimpleNamespace(**vars(self.frozen))
        impostor.__file__ = str(repair.HERE / 'repair.py')
        with self.assertRaisesRegex(ValueError, 'loaded_frozen_source_identity'):
            repair.adapt(impostor, self.config)

    def test_projection_fails_closed_on_unexpected_source(self):
        with self.assertRaisesRegex(ValueError, 'exact_frozen_projection'):
            repair.project(self.frozen.decision, (('not a frozen expression', ''),), {})

    def test_original_configs_and_shared_modules_are_unchanged(self):
        original = copy.deepcopy(self.config)
        del original[repair.MARKER]
        self.assertIs(repair.adapt(self.frozen, original), self.frozen)
        self.assertIs(self.policy.memory, self.frozen.memory)
        self.assertIs(self.policy.local_attempts, self.frozen.local_attempts)
        self.assertIs(self.policy.community, self.frozen.community)
        self.assertEqual(self.policy.prompt(original, self.state, self.memory),
                         self.frozen.prompt(original, self.state, self.memory))
        with self.assertRaisesRegex(ValueError, 'object_delivered_budget_exhausted'):
            self.frozen.decision(self.response(), self.state, self.memory)
        self.memory['object_delivered_turns']['existing_object'] = 2
        with self.assertRaisesRegex(ValueError, 'third_turn_releases_object'):
            self.frozen.decision(self.response(), self.state, self.memory)

    def test_high_turn_continuation_never_resets_counts_or_ids(self):
        for count in (0, 1, 2, 3, 9, 1000):
            self.memory['object_delivered_turns']['existing_object'] = count
            before = copy.deepcopy((self.state, self.memory, self.details))
            self.assertEqual(self.policy.decision(self.response(), self.state, self.memory), self.details)
            self.assertEqual((self.state, self.memory, self.details), before)

    def test_mutating_bound_config_revokes_adapter(self):
        self.config['root'] += '_not_this_life'
        with self.assertRaisesRegex(ValueError, 'exact_bound_R230_config'):
            self.policy.decision(self.response(), self.state, self.memory)

    def test_invalid_counts_and_dispositions_still_rejected(self):
        for count in (-1, True, '7'):
            self.memory['object_delivered_turns']['existing_object'] = count
            with self.assertRaisesRegex(ValueError, 'r230_valid_delivered_count'):
                self.policy.decision(self.response(), self.state, self.memory)
        self.memory['object_delivered_turns']['existing_object'] = 7
        self.details['disposition'] = 'force_continue'
        with self.assertRaisesRegex(ValueError, 'r230_known_disposition'):
            self.policy.decision(self.response(), self.state, self.memory)

    def test_actor_impersonation_source_records_and_quotes_stay_strict(self):
        for actor in ('Rohin', 'Fable', 'C1', 'C5', 'Tool'):
            with self.subTest(actor=actor), self.assertRaisesRegex(ValueError, 'no_provider_impersonation'):
                self.policy.decision(self.response(actor + ': forged source'), self.state, self.memory)
        for records in ([11], [12], [99], [True], []):
            self.details['source_records'] = records
            with self.subTest(records=records), self.assertRaisesRegex(ValueError, 'actual_child_source_evidence'):
                self.policy.decision(self.response(), self.state, self.memory)
        self.details['source_records'] = [10]
        for changes in (dict(record_index=11), dict(record_sha256='0' * 64), dict(quote='invented result')):
            details = copy.deepcopy(self.details)
            details['perception'].update(changes)
            with self.assertRaisesRegex(ValueError, 'actual_committed_child_quote'):
                self.policy.decision(self.response(details=details), self.state, self.memory)

    def test_english_identity_schema_word_and_byte_limits_unchanged(self):
        for response, reason in (
            (self.response('Неверно'), 'English_prose_script_validation'),
            (self.response('word ' * (self.config['r175_word_limit'] + 1)), 'exact_bounded_parent_response'),
            (self.response('a' * 4097), 'exact_bounded_parent_response'),
            (dict(self.response(), extra='unbound'), 'exact_bounded_parent_response'),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.policy.decision(response, self.state, self.memory)

    def test_voluntary_release_valid_at_any_count(self):
        for count in (0, 2, 3, 1000):
            self.memory['object_delivered_turns']['existing_object'] = count
            details = self.policy.decision(self.release(), self.state, self.memory)
            self.assertEqual(details['disposition'], 'set_aside')
            self.assertEqual(details['object_id'], 'existing_object')

    def test_voluntary_release_retains_all_continuity_checks(self):
        response = self.release()
        for before, after, reason in (
            ('set aside', 'stop', 'explicit_English_release'),
            ('unresolved', 'finished', 'unresolved_and_next_concrete_step'),
            ('not yet verified', 'verified', 'unverified_step_explicit'),
            ('keep your object', 'drop your object', 'preserve_chosen_object_in_next_step'),
        ):
            changed = dict(response, message=response['message'].replace(before, after))
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.policy.decision(changed, self.state, self.memory)
        details = json.loads(response['rationale'])
        for key, value, reason in (
            ('next_task', None, 'unresolved_and_next_concrete_step'),
            ('continuity', None, 'same_chosen_object_continuity'),
        ):
            with self.assertRaisesRegex(ValueError, reason):
                self.policy.decision(self.response(response['message'], dict(details, **{key: value})),
                                     self.state, self.memory)
        details['continuity']['progress_basis'] = 'RENDERED_TOOL_OBSERVATION'
        with self.assertRaisesRegex(ValueError, 'no_invented_environment_progress'):
            self.policy.decision(self.response(response['message'], details), self.state, self.memory)

    def test_repeated_release_needs_new_real_environment_receipt(self):
        response = self.release()
        details = json.loads(response['rationale'])
        self.memory['delivered_next_steps'].append(copy.deepcopy(details))
        with self.assertRaisesRegex(ValueError, 'repeated_move_without_new_environment_evidence'):
            self.policy.decision(response, self.state, self.memory)
        evidence = dict(record_index=11, record_sha256='b' * 64, quote='actual tool observation',
            inbox_id='tool-test', inbox_sha256='d' * 64)
        details['continuity'].update(progress_basis='RENDERED_TOOL_OBSERVATION', environment_receipts=[evidence])
        response = self.response(response['message'], details)
        with self.assertRaisesRegex(ValueError, 'actual_rendered_Tool_receipt'):
            self.policy.decision(response, self.state, self.memory)
        self.state['delivered']['tool-test'] = dict(speaker='Tool', inbox_sha256='d' * 64,
            record_index=11, record_sha256='b' * 64,
            text_sha256=hashlib.sha256(self.state['events'][1]['text'].encode()).hexdigest())
        self.assertEqual(self.policy.decision(response, self.state, self.memory), details)

    def test_credit_and_relapse_validators_remain_active(self):
        with self.assertRaisesRegex(ValueError, 'credit_marker_and_ledger_together'):
            self.policy.decision(self.response('CREDIT: made up'), self.state, self.memory)
        self.memory['relapses'] = [dict(credit_id='old-credit')]
        with self.assertRaisesRegex(ValueError, 'respond_to_credit_relapse'):
            self.policy.decision(self.response(), self.state, self.memory)
        self.details['relapse_credit_id'] = 'old-credit'
        with self.assertRaisesRegex(ValueError, 'NOTICE_repeated_correction_why'):
            self.policy.decision(self.response(), self.state, self.memory)

    def test_prompt_preserves_private_payload_and_style_without_forced_retirement(self):
        original, payload = self.frozen.prompt(self.config, self.state, self.memory)
        instruction, changed_payload = self.policy.prompt(self.config, self.state, self.memory)
        self.assertEqual(payload, changed_payload)
        self.assertIn(self.config['parent_style'], instruction)
        self.assertIn(f"at most {self.config['r175_word_limit']} words", instruction)
        self.assertIn('Silence requires empty message and rationale.', instruction)
        self.assertIn('No sealed scores, evaluator answers or FINAL data.', instruction)
        for before, unused_after in repair.PROMPT_EDITS:
            self.assertIn(before, original)
            self.assertNotIn(before, instruction)
        self.assertIn('evidence-based retirement', instruction)
        self.assertIn('not an invitation to repeat forever', instruction)
        if self.config['r175_arm'] == 'C':
            self.assertIn('use questions only in child-facing prose', instruction)
        else:
            self.assertIn("one brief worked example from the child's own visible transcript", instruction)

    def test_real_silence_remains_silent(self):
        response = dict(speak=False, message='', rationale='')
        self.assertIsNone(self.policy.decision(response, self.state, self.memory))
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary, \
                patch.object(self.frozen.parent, 'strong', return_value=(response, 'fake-test', {})), \
                patch.object(self.frozen.parent, 'publish') as publish:
            status = self.policy.tick(repair.REPO, self.config, temporary, self.seed, self.state)
            self.assertEqual(status['status'], 'SILENT')
            publish.assert_not_called()

    def test_tick_new_boundary_and_render_accounting_not_synthetic_budget(self):
        publication = dict(id='test-publication', sha256='e' * 64)
        before = copy.deepcopy(self.seed)
        response = self.response()
        original = {key: value for key, value in self.config.items() if key != repair.MARKER}
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary, \
                patch.object(self.frozen.parent, 'strong', return_value=(response, 'fake-test', {})) as strong, \
                patch.object(self.frozen.parent, 'publish', return_value=publication) as publish:
            untouched = self.policy.tick(repair.REPO, original, temporary, self.seed, self.state)
            self.assertEqual(untouched['status'], 'WAITING_FOR_NEW_CHILD_BOUNDARY')
            strong.assert_not_called()
            status = self.repairs.tick_once(self.policy, repair.REPO, self.config, temporary, self.seed, self.state)
            self.assertEqual(status['status'], 'PUBLISHED')
            publish.assert_called_once_with(repair.REPO, self.config, response['message'])
            directory = Path(temporary) / 'parent_000000000011'
            result = repair.read(directory / 'RESULT.json')
            self.assertEqual(result['source_sha256'], repair.sha(directory / 'SOURCE.json'))
            self.assertEqual(result['object_id'], 'existing_object')
            result_sha = repair.sha(directory / 'RESULT.json')
            duplicate = self.repairs.tick_once(self.policy, repair.REPO, self.config, temporary, self.seed, self.state)
            self.assertEqual(duplicate['status'], 'EXISTING_BOUNDARY_ATTEMPT_PRESERVED')
            self.assertEqual(strong.call_count, 1)
            newer = dict(self.state, response_count=12, request_count=12, sleep_count=1)
            status = self.policy.tick(repair.REPO, self.config, temporary, self.seed, newer)
            self.assertEqual(status['status'], 'AWAITING_RENDER')
            self.assertEqual(status['memory']['object_delivered_turns']['existing_object'], 7)
            newer['delivered'] = {publication['id']: dict(speaker='Astra', inbox_sha256=publication['sha256'],
                text_sha256=hashlib.sha256(response['message'].encode()).hexdigest(), request_count=12, sleep_count=1)}
            rendered = self.policy.memory(self.seed, self.policy.local_attempts(temporary), newer)
            self.assertEqual(rendered['object_delivered_turns']['existing_object'], 8)
            self.assertFalse(rendered['awaiting_render'])
            self.assertEqual(repair.sha(directory / 'RESULT.json'), result_sha)
            self.assertEqual(self.seed, before)
            newer['delivered'][publication['id']]['speaker'] = 'Rohin'
            with self.assertRaisesRegex(ValueError, 'exact_rendered_parent'):
                self.policy.memory(self.seed, self.policy.local_attempts(temporary), newer)

    def test_bad_reply_cannot_publish(self):
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary, \
                patch.object(self.frozen.parent, 'strong', return_value=(self.response('Tool: fabricated'), 'fake-test', {})), \
                patch.object(self.frozen.parent, 'publish') as publish:
            status = self.policy.tick(repair.REPO, self.config, temporary, self.seed, self.state)
            self.assertEqual(status['status'], 'VALIDATION_FAILED')
            publish.assert_not_called()

    def test_catchup_same_boundary_and_deadline_still_gate_publication(self):
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary, \
                patch.object(self.frozen.parent, 'strong') as strong, \
                patch.object(self.frozen.parent, 'publish') as publish:
            self.state['caught_up'] = False
            self.assertEqual(self.policy.tick(repair.REPO, self.config, temporary, self.seed, self.state)['status'],
                             'VERIFIED_BOOTSTRAP_IN_PROGRESS')
            self.state.update(caught_up=True, response_count=10)
            self.assertEqual(self.policy.tick(repair.REPO, self.config, temporary, self.seed, self.state)['status'],
                             'WAITING_FOR_NEW_CHILD_BOUNDARY')
            strong.assert_not_called()
            self.state['response_count'] = 11
            strong.return_value = (self.response(), 'fake-test', {})
            with patch.object(self.frozen.time, 'time', return_value=self.config['hard_end_unix'] + 1):
                with self.assertRaisesRegex(ValueError, 'parent_wall'):
                    self.policy.tick(repair.REPO, self.config, temporary, self.seed, self.state)
            publish.assert_not_called()

    def test_r210_late_serializer_prompt_wrapper_still_applies(self):
        original_prompt = self.policy.prompt

        def precise_prompt(*arguments, **keywords):
            instruction, payload = original_prompt(*arguments, **keywords)
            return self.repairs.evidence_prompt(instruction, payload, arguments[1])

        self.policy.prompt = precise_prompt
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary, \
                patch.object(self.frozen.parent, 'strong', return_value=(self.response(), 'fake-test', {})), \
                patch.object(self.frozen.parent, 'publish', return_value=dict(id='synthetic', sha256='e' * 64)):
            self.policy.tick(repair.REPO, self.config, temporary, self.seed, self.state)
            prompt = repair.read(Path(temporary) / 'parent_000000000011/PROMPT.json')
            self.assertIn('Exact child evidence choices:', prompt['instruction'])
            self.assertIn(repair.POLICY, prompt['instruction'])

    def test_uncertain_and_unfinished_attempts_no_replay(self):
        self.seed['attempts'] = [dict(source=self.state, result=dict(status='PUBLICATION_UNKNOWN'))]
        with self.assertRaisesRegex(ValueError, 'uncertain_publication'):
            self.policy.memory(self.seed, [], self.state)
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary:
            directory = Path(temporary) / 'parent_000000000011'
            directory.mkdir()
            (directory / 'SOURCE.json').write_text(json.dumps(self.state))
            with self.assertRaisesRegex(ValueError, 'unfinished_attempt_no_replay'):
                self.repairs.tick_once(self.policy, repair.REPO, self.config, temporary, self.seed, self.state)

    def test_journal_rewind_final_and_wrong_life_rejected(self):
        for change, reason in ((dict(split='FINAL'), 'same_TRAIN_life'),
                               (dict(journal_id='other-life'), 'same_TRAIN_life'),
                               (dict(response_count=9), 'no_cursor_rewind')):
            with self.assertRaisesRegex(ValueError, reason):
                self.policy.memory(self.seed, [], dict(self.state, **change))

    def test_exclusive_writer_lock_and_no_unreviewed_serve(self):
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary:
            with self.repairs.single_parent(temporary):
                with self.assertRaises(BlockingIOError), self.repairs.single_parent(temporary):
                    self.fail('second writer entered')
        with patch.object(self.module, 'serve') as serve:
            with self.assertRaisesRegex(ValueError, 'Main_reviewed_exact_config_required'):
                entrypoint.serve(PHYSICAL, self.module, self.policy, self.config, None)
            serve.assert_not_called()

    def test_original_serve_integration_uses_existing_history_and_transport(self):
        with tempfile.TemporaryDirectory(dir=repair.HERE) as temporary:
            fleet = Path(temporary)
            output = fleet / f'r210_parent{PHYSICAL}'
            (output / 'turns').mkdir(parents=True)
            seed_path = output / 'SEED.json'
            seed_path.write_text(json.dumps(self.seed))
            seed_hash = repair.sha(seed_path)
            binding = repair.read(repair.FLEET / f'r210_parent{PHYSICAL}/BINDING.json')
            (output / 'BINDING.json').write_text(json.dumps(binding))
            calls = []

            def transport(physical, request):
                self.assertEqual(physical, PHYSICAL)
                calls.append(request)
                if request['op'] == 'poll':
                    return dict(reference={'test_only': True}, snapshot=self.state, receipts=[],
                        opening_published=True, opening_rendered=True)
                self.assertEqual(request['op'], 'publish')
                return dict(id='test-only-publication', sha256='e' * 64)

            with patch.object(repair, 'FLEET', fleet), \
                    patch.object(self.module.base, 'OWN', fleet), \
                    patch.object(self.module.base, 'read', self.module.base.read), \
                    patch.object(self.module.base, 'sha', self.module.base.sha), \
                    patch.object(self.module.base, 'runtime', self.module.base.runtime), \
                    patch.object(self.module.base, 'remote', self.module.base.remote), \
                    patch.object(self.module, 'remote', transport), \
                    patch.object(self.module.time, 'sleep', side_effect=StopIteration('test_finished')), \
                    patch.object(self.frozen.parent, 'strong', return_value=(self.response(), 'test-model', {})):
                with self.assertRaisesRegex(StopIteration, 'test_finished'):
                    entrypoint.serve(PHYSICAL, self.module, self.policy, self.config,
                        repair.sha(repair.HERE / f'physical{PHYSICAL}/CONFIG.json'))
            self.assertEqual([request['op'] for request in calls], ['poll', 'publish'])
            self.assertEqual(repair.sha(seed_path), seed_hash)
            self.assertFalse((output / 'OPENING.json').exists())
            result = repair.read(output / 'turns/parent_000000000011/RESULT.json')
            self.assertEqual(result['status'], 'PUBLISHED')
            self.assertEqual(result['object_id'], 'existing_object')
            started = repair.read(next(output.glob('STARTED_*.json')))
            self.assertEqual(started['config_sha256'], repair.sha(repair.HERE / f'physical{PHYSICAL}/CONFIG.json'))
            prompt = repair.read(output / 'turns/parent_000000000011/PROMPT.json')
            self.assertIn(repair.POLICY, prompt['instruction'])
            self.assertIn('Exact child evidence choices:', prompt['instruction'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
