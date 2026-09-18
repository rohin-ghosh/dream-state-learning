"""CPU correctness fixtures are not measured model throughput."""

import ast
import json
import math
import os
from pathlib import Path
import tempfile
import unittest

from gpu import ny_caption_generation_profile as profile


TEST_ROOT = Path(os.environ.get('PROFILE_TEST_TMP', str(profile.SCOPE)))


class ProfileTests(unittest.TestCase):
    def test_actual_tokens_stop_after_eos_not_at_max_budget(self):
        rows = [[1, 2, 11, 99, 0, 0], [1, 2, 12, 13, 14, 15]]
        self.assertEqual(profile.token_counts(rows, 2, {99}, 0), [2, 4])

    def test_eos_counted_even_when_pad_equals_eos(self):
        self.assertEqual(profile.token_counts([[1, 2, 99, 99]], 1, {99}, 99), [2])

    def test_ambiguous_padding_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            profile.token_counts([[1, 0]], 1, {99}, 0)

    def test_per_life_not_aggregate(self):
        result = profile.rates([256, 512], 10)
        self.assertEqual(result['per_life_tokens_per_second'], [25.6, 51.2])
        self.assertEqual(result['aggregate_tokens_per_second'], 76.8)

    def test_invalid_denominators_and_counts(self):
        for seconds in (0, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                profile.rates([256], seconds)
        with self.assertRaises(ValueError):
            profile.rates([0], 1)

    def test_receipt_is_exclusive_and_readonly(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            path = Path(directory) / 'receipt.json'
            expected = profile.immutable(path, dict(value=1))
            self.assertEqual(profile.file_hash(path), expected)
            self.assertEqual(path.stat().st_mode & 0o222, 0)
            with self.assertRaises(FileExistsError):
                profile.immutable(path, dict(value=2))
            self.assertEqual(json.loads(path.read_text()), dict(value=1))

    def test_trial_name_does_not_collide_with_receipt_filename(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            expected = profile.receipt(root, 'trial.json', name='2048_1_shape_first_256',
                                       generation=profile.rates([256], 10))
            document = json.loads((root / 'trial.json').read_text())
            self.assertEqual(document['name'], '2048_1_shape_first_256')
            self.assertEqual(document['generation']['per_life_tokens_per_second'], [25.6])
            self.assertEqual(profile.file_hash(root / 'trial.json'), expected)

    def test_strict_actual_minor_not_physical_index(self):
        root = Path('/tmp') / profile.SCOPE / 'unit'
        command = profile.containment_command(root, 5, 'r177-caption-profile-test', 2524, 2524)
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia5 rw', command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia6 rw', command)
        self.assertIn('CUDA_VISIBLE_DEVICES=' + profile.GPU_UUID, command)
        self.assertIn('--property=RuntimeMaxSec=1100', command)
        self.assertIn('--property=ProtectSystem=strict', command)
        self.assertIn('--property=ReadWritePaths=' + str(root), command)

    def test_nonroot_identity_required(self):
        with self.assertRaises(ValueError):
            profile.containment_command(Path('/tmp'), 5, 'unit', 0, 0)

    def test_shared_deadline_cannot_restart_twenty_minute_budget(self):
        self.assertEqual(profile.bounded_runtime(2200, 1000), 1100)
        self.assertEqual(profile.bounded_runtime(2200, 2000), 190)
        with self.assertRaisesRegex(ValueError, 'window_exhausted'):
            profile.bounded_runtime(2200, 2171)

    def test_shortened_budget_is_actual_systemd_property(self):
        command = profile.containment_command(Path('/tmp'), 5, 'unit', 2524, 2524, 190)
        self.assertIn('--property=RuntimeMaxSec=190', command)
        for lifetime in (0, 1101, 1.5):
            with self.assertRaisesRegex(ValueError, 'bounded_containment'):
                profile.containment_command(Path('/tmp'), 5, 'unit', 2524, 2524, lifetime)

    def test_invalid_deadline_fails_closed(self):
        for deadline in (math.inf, math.nan):
            with self.assertRaisesRegex(ValueError, 'finite_authorization'):
                profile.bounded_runtime(deadline, 1000)

    def test_pytorch_UUID_bytes_do_not_depend_on_display_prefix(self):
        from types import SimpleNamespace
        from uuid import UUID
        actual = SimpleNamespace(bytes=list(UUID(profile.GPU_UUID.removeprefix('GPU-')).bytes))
        result = profile.cuda_identity(actual)
        self.assertTrue(result['matches'])
        self.assertEqual(result['normalized_uuid'], profile.GPU_UUID)
        self.assertEqual(result['raw_bytes'], actual.bytes)

    def test_UUID_normalization_never_admits_another_device(self):
        from types import SimpleNamespace
        self.assertFalse(profile.cuda_identity(SimpleNamespace(bytes=[0] * 16))['matches'])
        for raw in ([], [0] * 15, [256] * 16, [-1] * 16, [True] * 16, 'x' * 16):
            with self.assertRaisesRegex(ValueError, '16_byte'):
                profile.cuda_identity(SimpleNamespace(bytes=raw))

    def test_transformers5_tokenizer_requires_explicit_list_result(self):
        class Tokenizer:
            def apply_chat_template(self, messages, **arguments):
                self_test.assertIs(arguments.get('return_dict'), False)
                return [42] * (33 + messages[1]['content'].count(' synthetic'))

        self_test = self
        for target in (2048, 12288):
            messages = profile.synthetic_messages(Tokenizer(), target)
            self.assertEqual(33 + messages[1]['content'].count(' synthetic'), target)

    def test_actual_journal_on_synthetic_records_only(self):
        from gpu.orch_r125_stream_journal import StreamJournal
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            journal = StreamJournal(Path(directory) / 'journal', create=True)
            try:
                result = journal.record('PROFILE_SYNTHETIC', dict(texts=['synthetic fixture']))
                self.assertEqual(result['index'], 0)
                self.assertTrue(Path(result['path']).is_file())
            finally:
                journal.close()

    def test_actual_render_preserves_synthetic_prompt_and_masks(self):
        from organism_v6.orch_r124_train_history import TrainHistory
        from organism_v6.orch_r125_plain_context import VERSION
        history = TrainHistory(system_prompt='synthetic', birth_prompt='symbols')
        rendered = history.render(lambda messages: 4, 100, presentation=dict(
            version=VERSION, system_prompt='synthetic', birth_prompt='symbols'))
        self.assertEqual(rendered.labels, (-100,) * 4)
        self.assertEqual(rendered.messages, [dict(role='system', content='synthetic'), dict(role='user', content='symbols')])

    def test_native_generation_is_cached_not_logit_logging(self):
        source = Path('gpu/orch_r125_continual_native.py').read_text()
        tree = ast.parse(source)
        methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'generate']
        self.assertEqual(len(methods), 1)
        body = ast.get_source_segment(source, methods[0])
        self.assertIn('use_cache=True', body)
        self.assertIn('model.generate(', body)
        self.assertNotIn('output_logits', body)
        self.assertNotIn('output_scores', body)

    def test_exact_native_encode_own_preserves_mask_and_ids(self):
        tokenizer = type('Tokenizer', (), dict(eos_token_id=99, pad_token_id=None, all_special_ids=[99],
            apply_chat_template=lambda self, messages, **kwargs: [10, 11],
            decode=lambda self, tokens, **kwargs: 'fixture'))()
        encode = profile.extracted(Path('gpu/orch_r125_continual_native.py'), 'encode_own', remove_import=True,
            namespace=dict(require=profile.require, EncodedRow=profile.EncodedRow))
        row = dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
                   prefix=[], token_ids=[22, 99], terminal=True, target='fixture')
        actual = encode(row, tokenizer, 8)
        self.assertEqual(actual.input_ids, (10, 11, 22, 99))
        self.assertEqual(actual.labels, (-100, -100, 22, 99))
        self.assertEqual(actual.target_ids, (22, 99))
        with self.assertRaisesRegex(ValueError, 'no_training_trim'):
            encode(row, tokenizer, 3)

    def test_timing_synchronizes_outside_callback(self):
        calls = []
        result, elapsed = profile.timed(lambda: calls.append('work'), lambda: calls.append('sync'))
        self.assertEqual(calls, ['sync', 'work', 'sync'])
        self.assertIsNone(result)
        self.assertGreaterEqual(elapsed, 0)

    def test_hard_end_matches_conservative_existing_wall(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(profile.HARD_END, timezone.utc).isoformat(), '2026-09-18T18:00:00+00:00')


if __name__ == '__main__':
    unittest.main()
