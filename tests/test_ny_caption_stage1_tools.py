import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu.ny_caption_game import Contest, DevelopmentManifest
from gpu.ny_caption_similarity import LABEL_MODEL, LABEL_SYSTEM, MODEL_ID, MODEL_REVISION, file_pin
from gpu.ny_caption_stage1_tools import SCHEMA, execute, run_actions, validated_actions, validate_tokenizer, validate_bundle


class FixtureGame:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def inspect_image(self, contest, question):
        self.calls.append(('inspect_image', contest, question))
        return dict(ok=not self.fail, observations='Synthetic fixture only.')

    def submit_caption(self, contest, text):
        self.calls.append(('submit_caption', contest, text))
        return dict(ok=not self.fail, accepted=False)

    def snapshot(self):
        return dict(calls=list(self.calls))


class Stage1ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.manifest = DevelopmentManifest(tuple(Contest(str(index), 'Synthetic scene', 'image_' + str(index))
                                                 for index in range(3)))
        self.actions = [dict(tool='inspect_image', contest_id='0', question='What is visible?'),
                        dict(tool='submit_caption', contest_id='0', text='Synthetic test caption')]

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return file_pin(path)

    def test_only_known_development_actions(self):
        self.assertEqual(validated_actions(dict(mode='DEVELOPMENT', actions=self.actions), self.manifest), self.actions)
        for document in (dict(mode='FINAL', actions=self.actions), dict(mode='DEVELOPMENT', actions=[]),
                         dict(mode='DEVELOPMENT', actions=[dict(self.actions[0], contest_id='held')]),
                         dict(mode='DEVELOPMENT', actions=[dict(self.actions[0], command='bad')])):
            with self.assertRaises(ValueError):
                validated_actions(document, self.manifest)

    def test_receipts_snapshot_and_no_scientific_claim(self):
        game = FixtureGame()
        result = run_actions(game, self.actions, self.root)
        self.assertEqual(result['status'], 'COMPLETE_REAL_TOOL_SMOKE')
        self.assertEqual(len(game.calls), 2)
        self.assertFalse(result['scoring_validation_claim'])
        self.assertEqual(result['child_training_updates'], 0)
        receipt = json.loads((self.root / 'results/0000.json').read_text())
        self.assertEqual(receipt['actor'], 'environment')
        self.assertFalse(receipt['child_training_target'])
        self.assertEqual(len(json.loads((self.root / 'snapshots/0001.json').read_text())['calls']), 2)

    def test_tool_failure_stops_without_retry(self):
        game = FixtureGame(fail=True)
        result = run_actions(game, self.actions, self.root)
        self.assertEqual(result['status'], 'STOPPED_ON_TOOL_ERROR_NO_RETRY')
        self.assertEqual(len(game.calls), 1)
        self.assertFalse((self.root / 'requests/0001.json').exists())

    def test_bad_action_ref_prevents_model_loading(self):
        documents = dict(game_manifest=dict(mode='DEVELOPMENT', development_contest_ids=['0', '1', '2'],
            contests=[dict(contest_id=str(index), canonical_scene='Synthetic scene', image='image_' + str(index),
                           split='agent_development') for index in range(3)]))
        action_ref = self.write('actions.json', dict(mode='DEVELOPMENT', actions=self.actions))
        action_ref['sha256'] = '0' * 64
        with patch('gpu.ny_caption_stage1_tools.validate_bundle', return_value=({}, documents)), \
                patch('gpu.ny_caption_stage1_tools.load_game') as loader:
            with self.assertRaises(ValueError):
                execute({}, action_ref, self.root / 'attempt', loader=loader)
            loader.assert_not_called()
        self.assertTrue((self.root / 'attempt/FAILED.json').is_file())

    def test_attempt_directory_cannot_reset_budget_or_repeat_dispatch(self):
        output = self.root / 'attempt'
        output.mkdir()
        with patch('gpu.ny_caption_stage1_tools.validate_bundle') as validator:
            with self.assertRaises(FileExistsError):
                execute({}, {}, output)
            validator.assert_not_called()

    def test_tokenizer_closure_is_exact_and_pinned(self):
        root = self.root / 'tokenizer'
        root.mkdir()
        names = ('tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt')
        for name in names:
            (root / name).write_text('{}')
        manifest = dict(schema='NY_CHILD_TOKENIZER_V1', model_id='Qwen/Qwen2.5-7B-Instruct',
                        revision='a' * 40, root=str(root),
                        files={name: file_pin(root / name)['sha256'] for name in names})
        self.assertEqual(validate_tokenizer(manifest), root)
        (root / 'unbound.py').write_text('not executed')
        with self.assertRaisesRegex(ValueError, 'no_unbound_tokenizer_files'):
            validate_tokenizer(manifest)

    def bundle(self):
        tokenizer = self.root / 'tokenizer'
        tokenizer.mkdir()
        names = ('tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt')
        for name in names:
            (tokenizer / name).write_text('{}')
        manifest = dict(mode='DEVELOPMENT', development_contest_ids=['0', '1', '2'], contests=[
            dict(contest_id=str(index), canonical_scene='Synthetic scene', image='image_' + str(index),
                 split='agent_development') for index in range(3)])
        return dict(schema=SCHEMA, mode='DEVELOPMENT', agent_id='fixture', lane='UNPARENTED',
            visual_endpoint='http://127.0.0.1:8177', game=dict(tau=0.2, transport_retries=0,
                visual_call_limit=8, max_submissions_per_contest=8),
            judge_budget=dict(max_model_examples=16, max_model_tokens=8192, max_seconds=60),
            game_manifest=self.write('game.json', manifest), judge_config=self.write('judge.json', {}),
            similarity_runtime=self.write('similarity.json', dict(schema='NY_FROZEN_SIMILARITY_RUNTIME_V1',
                verifier_required=True, provisional_model_annotations=True,
                label_prompt_sha256=hashlib.sha256(LABEL_SYSTEM.encode()).hexdigest(),
                pixel_config=dict(embedding_model_id=MODEL_ID, embedding_revision=MODEL_REVISION,
                    rho_coarse=0.5, rho_primary=0.6, rho_fine=0.7))),
            vision_packet=self.write('images.json', dict(schema='R177_VISION_IMAGES_V1', mode='DEVELOPMENT',
                images=[dict(handle='image_' + str(index), path=str(self.root / f'image{index}.png'),
                             sha256='a' * 64, bytes=1) for index in range(3)])),
            tokenizer_manifest=self.write('tokenizer.json', dict(schema='NY_CHILD_TOKENIZER_V1',
                model_id='Qwen/Qwen2.5-7B-Instruct', revision='a' * 40, root=str(tokenizer),
                files={name: file_pin(tokenizer / name)['sha256'] for name in names})),
            verifier_scope=self.write('scope.json', dict(schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1',
                issuer='Main/Astra', no_reset=True, provider_model=LABEL_MODEL,
                active_seconds_max=60, absolute_end_unix=time.time()+600,
                allowed_pool='agent_development', lane_id='fixture',
                label_call_cap=0, pair_label_cap=0, verification_call_cap=8, retries=0,
                locked_validation_reads=0, FINAL_reads=0)))

    def validate_fixture(self, bundle):
        with patch('gpu.ny_caption_judge.validate_checkpoint', return_value=(dict(tau=dict(threshold=0.2)), {}, None)):
            return validate_bundle(self.write('bundle.json', bundle))

    def test_full_bundle_checks_precede_any_models(self):
        bundle = self.bundle()
        validated, documents = self.validate_fixture(bundle)
        self.assertEqual(validated, bundle)
        self.assertEqual(documents['verifier_scope']['allowed_pool'], 'agent_development')

    def test_no_hosted_endpoint_final_lane_or_changed_tau(self):
        bundle = self.bundle()
        for field, value in (('visual_endpoint', 'https://hosted.example'), ('visual_endpoint', 'http://127.0.0.1:99999'),
                             ('lane', 'FROZEN'), ('mode', 'FINAL')):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.validate_fixture(dict(bundle, **{field: value}))
        with self.assertRaisesRegex(ValueError, 'frozen_judge_threshold_required'):
            self.validate_fixture(dict(bundle, game=dict(bundle['game'], tau=0.1)))

    def test_training_annotation_scope_cannot_be_relabelled_as_game(self):
        bundle = self.bundle()
        scope = json.loads(Path(bundle['verifier_scope']['path']).read_text())
        for change in (dict(allowed_pool='judge_train'), dict(lane_id='other'), dict(label_call_cap=1),
                       dict(pair_label_cap=1), dict(retries=1), dict(FINAL_reads=1), dict(no_reset=False),
                       dict(absolute_end_unix=1), dict(active_seconds_max=3601), dict(provider_model='other')):
            with self.subTest(change=change):
                revised = dict(bundle, verifier_scope=self.write('altered-scope.json', dict(scope, **change)))
                with self.assertRaisesRegex(ValueError, 'separate_development_verifier_scope'):
                    self.validate_fixture(revised)

    def test_model_budget_and_retry_limits_cannot_expand(self):
        bundle = self.bundle()
        for field, value in (('max_model_examples', 65), ('max_model_tokens', 32769), ('max_seconds', 601)):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'bounded_judge'):
                self.validate_fixture(dict(bundle, judge_budget=dict(bundle['judge_budget'], **{field: value})))
        with self.assertRaisesRegex(ValueError, 'bounded_smoke_no_transport_retry'):
            self.validate_fixture(dict(bundle, game=dict(bundle['game'], transport_retries=1)))

    def test_mismatched_component_bytes_fail_before_load(self):
        bundle = self.bundle()
        Path(bundle['game_manifest']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'reference_hash_changed'):
            self.validate_fixture(bundle)


if __name__ == '__main__':
    unittest.main()
