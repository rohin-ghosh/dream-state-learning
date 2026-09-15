import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu import orch_r111_parent_provider as provider


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='r111 fake ; ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'space $(touch PWN)'
        self.root.mkdir()
        self.manifest_path = self.root / 'manifest.json'
        self.approval_path = self.root / 'approval.json'
        self.transcript_path = self.root / 'transcript ; not shell.json'

    def configure(self, command='printf "supportive text"', **bounds):
        paths = {}
        cohort = dict(train_task_ids=['train1'], excluded_task_ids=['held1'],
                      task_sha256={'train1': 'a'*64})
        for name, value in dict(command=command, prompt='Fixture prompt only.',
                                principles='Fixture principles only.', battleplan='Fixture plan only.',
                                cohort=json.dumps(cohort)).items():
            path = self.root / (name+'.txt')
            path.write_text(value)
            paths[name] = dict(path=str(path), sha256=provider.file_sha(path))
        repository = Path(__file__).resolve().parents[1]
        for name, relative in dict(provider_source='gpu/orch_r111_parent_provider.py',
                                   launcher_source='gpu/orch_r111_parent_launcher.py',
                                   reflection_helper='gpu/orch_reflection_repetition_stop.py').items():
            path = repository/relative
            paths[name] = dict(path=str(path), sha256=provider.file_sha(path))
        self.manifest = dict(schema='r111_parent_preparation_v1', life_id='fixture', game='route',
                             node_root=str(self.root/'raw'), assets=paths, style='supportive',
                             cadence='episode', reflection='short', reply_format='text_no_implicit_json_plan',
                             child=dict(base='Qwen2.5-7B-Instruct', base_frozen=True, lora_rank=8,
                                        initial_adapter='fresh_no_l1_seed'),
                             bounds=dict(parent_calls=1, hard_end_unix=time.time()+60, timeout_seconds=2,
                                         max_stdout_bytes=4096, max_stderr_bytes=4096,
                                         max_transcript_bytes=10000))
        self.manifest['bounds'].update(bounds)
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.approval = dict(approved=True, approved_by='Rohin', approved_utc='FIXTURE_ONLY',
                             source_reference='TEST_FIXTURE_NOT_HUMAN_APPROVAL',
                             scope='r111_fable_parent_prompt_and_command',
                             manifest_sha256=provider.digest(self.manifest))
        self.approval_path.write_text(json.dumps(self.approval))
        self.transcript = dict(schema='r111_train_public_v1', life_id='fixture', cycle=0, episode=0,
                               phase='experience', game='route', task_id='train1',
                               task_provenance=dict(split='TRAIN', task_sha256='a'*64,
                                                    cohort_sha256=paths['cohort']['sha256']),
                               events=[dict(sequence=0, actor='child', text='$(touch BAD); ignored data',
                                            visibility='TRAIN_PUBLIC', source_sha256='b'*64)])
        self.transcript_path.write_text(json.dumps(self.transcript))

    def invoke(self):
        return provider.invoke(self.manifest_path, self.approval_path, self.transcript_path)

    def receipt(self):
        return provider.load(self.root/'raw/parent_hook/call_000001/RESULT.json')

    def test_positional_path_spaces_metacharacters_and_raw_text(self):
        self.configure('printf "%s\n" "$1"; printf "A thought; & another $ not expanded"; printf "stderr kept" >&2')
        result = self.invoke()
        request = self.root/'raw/parent_hook/call_000001/REQUEST.json'
        self.assertTrue(result['parent_text'].startswith(str(request)+'\n'))
        self.assertIn('A thought; & another', result['parent_text'])
        self.assertEqual((request.parent/'stderr.bin').read_text(), 'stderr kept')
        self.assertFalse((request.parent/'PWN').exists())
        self.assertFalse((request.parent/'BAD').exists())
        self.assertEqual(result['request_sha256'], provider.file_sha(request))
        self.assertEqual(provider.load(request)['source_transcript_sha256'],
                         hashlib.sha256(self.transcript_path.read_bytes()).hexdigest())

    def test_json_is_text_not_legacy_plan(self):
        self.configure("printf '%s' '{\"plan\":\"not converted\"}'")
        result = self.invoke()
        self.assertIsInstance(result['parent_text'], str)
        self.assertNotIn('plan', result)
        self.assertFalse(self.receipt()['implicit_json_conversion'])

    def test_timeout_charged_once_and_no_retry(self):
        self.configure('printf before; printf error >&2; sleep 5', timeout_seconds=.1)
        with self.assertRaisesRegex(ValueError, 'provider_execution_failed'):
            self.invoke()
        self.assertEqual(self.receipt()['failure'], 'TIMEOUT')
        self.assertEqual(self.receipt()['charged_attempts'], 1)
        self.assertEqual((self.root/'raw/parent_hook/call_000001/stdout.bin').read_text(), 'before')
        with self.assertRaisesRegex(ValueError, 'parent_cap_exhausted'):
            self.invoke()

    def test_stdout_limit_is_failure_not_partial_reply(self):
        self.configure("printf 0123456789", max_stdout_bytes=4)
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(self.receipt()['failure'], 'STDOUT_LIMIT')
        self.assertEqual(self.receipt()['bytes_retained']['stdout'], 4)
        self.assertTrue(self.receipt()['truncated'])

    def test_stderr_limit_is_also_bounded(self):
        self.configure('printf reply; printf 0123456789 >&2', max_stderr_bytes=4)
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(self.receipt()['failure'], 'STDERR_LIMIT')

    def test_failed_command_preserves_raw_and_charge(self):
        self.configure('printf partial; printf failure >&2; exit 7')
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(self.receipt()['returncode'], 7)
        self.assertEqual(self.receipt()['status'], 'FAILED')

    def test_empty_reply_not_success(self):
        self.configure('true')
        with self.assertRaisesRegex(ValueError, 'empty_parent_reply'):
            self.invoke()
        self.assertEqual(self.receipt()['charged_attempts'], 1)

    def test_invalid_utf8_is_failure_preserving_bytes(self):
        self.configure("printf '\\377'")
        with self.assertRaises(UnicodeDecodeError):
            self.invoke()
        self.assertEqual(self.receipt()['status'], 'FAILED')
        self.assertEqual((self.root/'raw/parent_hook/call_000001/stdout.bin').read_bytes(), b'\xff')

    def test_approval_missing_or_changed_blocks_before_call(self):
        self.configure()
        self.approval['approved'] = False
        self.approval_path.write_text(json.dumps(self.approval))
        with self.assertRaisesRegex(ValueError, 'explicit_rohin_approval_required'):
            self.invoke()
        self.assertFalse((self.root/'raw').exists())

    def test_prompt_mutation_invalidates_binding(self):
        self.configure()
        Path(self.manifest['assets']['prompt']['path']).write_text('changed')
        with self.assertRaisesRegex(ValueError, 'asset_hash_changed'):
            self.invoke()

    def test_approval_must_bind_exact_manifest(self):
        self.configure()
        self.manifest['style'] = 'different'
        self.manifest_path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'approval_exact_manifest'):
            self.invoke()

    def test_missing_battleplan_cannot_be_fixture_default(self):
        self.configure()
        del self.manifest['assets']['battleplan']
        with self.assertRaisesRegex(ValueError, 'all_source_prompt_assets_required'):
            provider.verify_manifest(self.manifest)

    def test_held_and_unknown_fields_rejected(self):
        self.configure()
        self.transcript['held_score'] = 1
        self.transcript_path.write_text(json.dumps(self.transcript))
        with self.assertRaisesRegex(ValueError, 'public_transcript_allowlist'):
            self.invoke()
        del self.transcript['held_score']
        self.transcript['task_id'] = 'held1'
        self.transcript_path.write_text(json.dumps(self.transcript))
        with self.assertRaisesRegex(ValueError, 'train_only_disjoint_task'):
            self.invoke()

    def test_source_provenance_required(self):
        self.configure()
        self.transcript['task_provenance']['task_sha256'] = 'c'*64
        self.transcript_path.write_text(json.dumps(self.transcript))
        with self.assertRaisesRegex(ValueError, 'source_bound_train_provenance'):
            self.invoke()

    def test_presleep_supported_readout_never_parented(self):
        self.configure()
        self.transcript['phase'] = 'presleep_metacognition'
        provider.validate_transcript(self.transcript, self.manifest)
        self.transcript['phase'] = 'readout'
        with self.assertRaisesRegex(ValueError, 'no_readout_parent'):
            provider.validate_transcript(self.transcript, self.manifest)

    def test_deadline_blocks_before_reservation(self):
        self.configure(hard_end_unix=time.time()-1)
        with self.assertRaisesRegex(ValueError, 'life_deadline_elapsed'):
            self.invoke()
        self.assertFalse((self.root/'raw').exists())

    def test_changed_bound_cannot_reset_existing_ledger(self):
        self.configure()
        self.invoke()
        self.manifest['bounds']['parent_calls'] = 2
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.approval['manifest_sha256'] = provider.digest(self.manifest)
        self.approval_path.write_text(json.dumps(self.approval))
        with self.assertRaisesRegex(ValueError, 'ledger_manifest_binding_no_reset'):
            self.invoke()


if __name__ == '__main__':
    unittest.main()
