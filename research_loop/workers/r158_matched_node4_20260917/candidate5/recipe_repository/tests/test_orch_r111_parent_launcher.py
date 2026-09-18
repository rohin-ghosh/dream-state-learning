import json
from pathlib import Path
import tempfile
import unittest
import inspect
from unittest.mock import patch

from gpu.orch_r111_parent_launcher import completed_native_boundary,write_once,RELEASE_UUIDS,release
from gpu import orch_r111_parent_launcher as launcher
from gpu import orch_r111_parent_provider as provider


class ReleaseTests(unittest.TestCase):
    def test_only_exact_released_slots(self):
        self.assertEqual(set(RELEASE_UUIDS),{0,1})

    def test_ignored_background_sigint_not_used(self):
        source=inspect.getsource(release)
        self.assertNotIn('signal.SIGINT',source)
        self.assertIn('signal.SIGTERM',source)
        self.assertNotIn('signal.SIGKILL',source)
        self.assertLess(source.index("+'_STOP_CHECKPOINT.json'"),source.index('signal.SIGTERM'))

    def test_missing_or_pending_native_is_not_safe_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            campaign=root/'campaign'
            (campaign/'native').mkdir(parents=True)
            (root/'RESERVATIONS.jsonl').write_text(json.dumps(dict(kind='NATIVE'))+'\n')
            self.assertFalse(completed_native_boundary(root,campaign))
            path=campaign/'native/CALL_1.json'
            path.write_text('{}')
            self.assertFalse(completed_native_boundary(root,campaign))
            path.write_text('{"status":"COMPLETE"}')
            self.assertTrue(completed_native_boundary(root,campaign))

    def test_evidence_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json'
            write_once(path,dict(preserved=True))
            with self.assertRaises(FileExistsError):write_once(path,dict(preserved=False))


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in ('command', 'prompt', 'principles', 'battleplan'):
            (self.root/name).write_text('fixture only')
        (self.root/'cohort').write_text(json.dumps(dict(train_task_ids=['train'], excluded_task_ids=['held'],
                                                      task_sha256={'train': 'a'*64})))
        self.arguments = dict(output=self.root/'PREPARE.json', node_root='/localhome/local-rohing/orch_r111_fixture',
                              life_id='fixture', physical=0, game='route', cadence='paragraph', style='supportive',
                              reflection='short', provider_command_file=self.root/'command',
                              parent_prompt=self.root/'prompt', principles=self.root/'principles',
                              battleplan=self.root/'battleplan', cohort=self.root/'cohort',
                              parent_cap=2, native_cap=4, max_cycles=2)

    def prepare(self):
        with patch.object(launcher.time, 'time', return_value=1789466000):
            return launcher.prepare(**self.arguments)

    def test_contract_requires_real_sleep_not_contextual_base(self):
        result = self.prepare()
        manifest = provider.load(self.arguments['output'])
        self.assertEqual(manifest['child']['lora_rank'], 8)
        self.assertEqual(manifest['child']['initial_adapter'], 'fresh_no_l1_seed')
        self.assertEqual(manifest['contract']['presentations_per_row'], 16)
        self.assertTrue(manifest['contract']['parent_and_prompt_labels_masked'])
        self.assertEqual(manifest['contract']['sequential_episodes_per_sleep'], 2)
        self.assertEqual(manifest['contract']['fresh_readout']['process'], 'fresh')
        self.assertFalse(result['backend']['gpu_launch_supported'])
        self.assertFalse(result['gpu_launched'])
        self.assertEqual(result['provider_invocations'], 0)

    def test_unsupported_all_games_honestly_reported(self):
        for game in launcher.GAMES:
            self.assertFalse(launcher.backend_status(game)['gpu_launch_supported'])

    def test_approval_cannot_bypass_missing_engine(self):
        result = self.prepare()
        approval = self.root/'approval.json'
        approval.write_text(json.dumps(dict(approved=True, approved_by='Rohin', approved_utc='FIXTURE_ONLY',
                                           scope='r111_fable_parent_prompt_and_command',
                                           source_reference='TEST_NOT_AUTHORIZATION',
                                           manifest_sha256=result['manifest_sha256'])))
        with patch.object(launcher.subprocess, 'Popen') as spawn:
            with self.assertRaisesRegex(RuntimeError, 'R111_GPU_BACKEND_UNSUPPORTED'):
                launcher.launch(self.arguments['output'], approval)
            spawn.assert_not_called()

    def test_no_deadline_extension_or_foreign_slot(self):
        self.arguments['hard_end'] = '2026-09-15T18:00:00Z'
        with self.assertRaisesRegex(ValueError, 'original_hard_end'):
            self.prepare()
        self.arguments['hard_end'] = launcher.HARD_END
        self.arguments['physical'] = 4
        with self.assertRaisesRegex(ValueError, 'fable_reserved_half_only'):
            self.prepare()

    def test_no_response_relabelling_as_token_cadence(self):
        self.arguments['cadence'] = 'response'
        with self.assertRaisesRegex(ValueError, 'known_game_and_honest_cadence'):
            self.prepare()

    def test_cohort_disjointness(self):
        (self.root/'cohort').write_text(json.dumps(dict(train_task_ids=['train'], excluded_task_ids=['train'],
                                                      task_sha256={'train': 'a'*64})))
        with self.assertRaisesRegex(ValueError, 'held_exclusion_disjoint'):
            self.prepare()


if __name__=='__main__':
    unittest.main()
