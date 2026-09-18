"""Non-material CPU regressions for native bindings and journal recovery."""

from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r125_continual_native as native
from gpu.orch_r125_continual_native import NativeChild
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


def make_plan(directory):
    directory = Path(directory)
    return dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
        system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
        compaction_invitation=native.COMPACTION_INVITATION,
        new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
        seed=0, segments_per_sleep=2, segment_tokens=16, context_limit=8192,
        max_sleeps=2, physical=0, gpu_uuid='GPU-synthetic',
        hard_end_unix=time.time()+600, lease_end_unix=time.time()+1000,
        decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05,
                     no_repeat_ngram_size=16),
        root=str(directory/'life'), model_dir=str(directory/'model'),
        anchors=str(directory/'anchors'), source_root=str(directory/'source'))


class Tokenizer:
    eos_token_id = 2
    all_special_ids = [0, 1, 2]

    def apply_chat_template(self, messages, **kwargs):
        if kwargs != dict(tokenize=True, add_generation_prompt=True, return_dict=False):
            raise AssertionError('unexpected chat template options')
        return [1] + [ord(character)+100 for message in messages for character in message['content']]

    def decode(self, tokens, **kwargs):
        if kwargs != dict(skip_special_tokens=False, clean_up_tokenization_spaces=False):
            raise AssertionError('unexpected decode options')
        return ''.join(chr(token-100) for token in tokens)


class EncodingAndPlanTests(unittest.TestCase):
    def test_experiment_seed_and_variant_defaults_are_explicit_in_binding(self):
        plan = make_plan('/tmp/synthetic-r133')
        default = native.experiment_binding(plan)
        del plan['seed']
        self.assertEqual(native.experiment_binding(plan), default)
        self.assertEqual(default['seed'], 0)
        self.assertEqual(default['presleep_variant'], 'free_distillation')
        self.assertEqual(default['seed_initialization'], 'before_lora')
        self.assertIs(native.validate_plan(plan), plan)
        for variant, invitation in native.PRESLEEP_INVITATIONS.items():
            candidate = dict(plan, seed=1, presleep_variant=variant, compaction_invitation=invitation)
            self.assertIs(native.validate_plan(candidate), candidate)
            self.assertEqual(native.experiment_binding(candidate)['seed'], 1)
        self.assertEqual(len(set(native.PRESLEEP_INVITATIONS.values())), 4)
        self.assertEqual(native.PRESLEEP_INVITATIONS['no_distillation'], '')

    def test_experiment_requires_known_variant_and_exact_invitation(self):
        plan = make_plan('/tmp/synthetic-r133')
        for variant in ('unknown', None, [], True):
            with self.subTest(variant=variant), self.assertRaisesRegex(ValueError, 'known_presleep_variant'):
                native.validate_plan(dict(plan, presleep_variant=variant))
        for variant, invitation in native.PRESLEEP_INVITATIONS.items():
            with self.subTest(variant=variant), self.assertRaisesRegex(ValueError, 'exact_posted_prompts'):
                native.validate_plan(dict(plan, presleep_variant=variant, compaction_invitation=invitation+' '))

    def test_legacy_resumes_allow_only_seed0_free_distillation(self):
        plan = make_plan('/tmp/synthetic-r133')
        native.verify_experiment_resume(plan, None)
        for change in [dict(seed=1)] + [dict(presleep_variant=variant, compaction_invitation=invitation)
                for variant, invitation in native.PRESLEEP_INVITATIONS.items() if variant != 'free_distillation']:
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'legacy_experiment_configuration_frozen'):
                native.verify_experiment_resume(dict(plan, **change), None)

    def test_readout_revision_uses_new_artifacts_without_replacing_old_calls(self):
        self.assertEqual(native.readout_name({}, 2), 'sleep_000002')
        self.assertEqual(native.readout_name({'readout_revision': 2}, 2), 'sleep_000002_r2')
        for revision in (0, -1, True, '2'):
            with self.subTest(revision=revision), self.assertRaisesRegex(ValueError, 'positive_readout_revision'):
                native.readout_name({'readout_revision': revision}, 2)

    def test_new_only_rehearsal_preserves_archived_rows(self):
        old_rows = [{'source_sha256': 'old', 'actor': 'child'}]
        before = deepcopy(old_rows)
        self.assertEqual(native.select_rehearsal_rows({'rehearsal_presentations': 0}, old_rows), [])
        self.assertEqual(old_rows, before)
        self.assertIs(native.select_rehearsal_rows({'rehearsal_presentations': 1}, old_rows), old_rows)
        self.assertEqual(len(native.presentation_schedule([{'new': 1}] * 3,
            native.select_rehearsal_rows({'rehearsal_presentations': 0}, old_rows))), 48)
        for invalid in (True, -1, 2, '0'):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'explicit_rehearsal'):
                native.select_rehearsal_rows({'rehearsal_presentations': invalid}, old_rows)

    def test_presleep_inbox_only_replies_to_unseen_parent_once(self):
        previous = SimpleNamespace(event_id='parent:old', actor='parent')
        incoming = SimpleNamespace(event_id='parent:new', actor='parent')
        child = SimpleNamespace(generate=Mock(), count_tokens=Mock())
        stream = SimpleNamespace(pending=None, sleep_due=True,
            history=SimpleNamespace(events=[previous]), step=Mock())
        journal = SimpleNamespace(read_inbox=Mock(return_value=[previous, incoming]), record=Mock())
        self.assertTrue(native.respond_to_presleep_inbox(child, stream, journal, 4))
        self.assertEqual(stream.step.call_args.kwargs['incoming'], [incoming])
        self.assertEqual(stream.step.call_count, 1)
        stream.history.events.append(incoming)
        self.assertFalse(native.respond_to_presleep_inbox(child, stream, journal, 4))
        self.assertEqual(stream.step.call_count, 1)

    def test_presleep_environment_only_does_not_add_generation(self):
        child = SimpleNamespace(generate=Mock(), count_tokens=Mock())
        stream = SimpleNamespace(pending=None, sleep_due=True,
            history=SimpleNamespace(events=[]), step=Mock())
        journal = SimpleNamespace(read_inbox=Mock(return_value=[
            SimpleNamespace(event_id='tool:new', actor='environment')]), record=Mock())
        self.assertFalse(native.respond_to_presleep_inbox(child, stream, journal, 4))
        stream.step.assert_not_called()

    def row(self):
        return dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
            prefix=[dict(role='system', content='s'), dict(role='user', content='p')],
            token_ids=[197, 198, 2], target='ab', terminal=True)

    def test_encode_masks_entire_prefix_and_preserves_native_eos(self):
        row = self.row()
        before = deepcopy(row)
        encoded = native.encode_own(row, Tokenizer(), 6)
        self.assertEqual(encoded.input_ids, (1, 215, 212, 197, 198, 2))
        self.assertEqual(encoded.labels, (-100, -100, -100, 197, 198, 2))
        self.assertEqual(encoded.target_ids, (197, 198, 2))
        self.assertEqual(row, before)

    def test_genuine_generated_endoftext_is_not_a_role_injection(self):
        class QwenTokenizer(Tokenizer):
            pad_token_id = 0

            def decode(self, tokens, **kwargs):
                return ''.join('<|endoftext|>' if token == 0 else chr(token-100) for token in tokens)

        row = dict(self.row(), token_ids=[197, 0, 198, 2], target='a<|endoftext|>b')
        encoded = native.encode_own(row, QwenTokenizer(), 7)
        self.assertEqual(encoded.target_ids, (197, 0, 198, 2))
        self.assertEqual(encoded.labels[:3], (-100, -100, -100))
        with self.assertRaisesRegex(ValueError, 'no_special_token_target_injection'):
            native.encode_own(dict(row, token_ids=[197, 1, 198, 2]), QwenTokenizer(), 7)

    def test_nonterminal_target_never_gets_synthetic_eos(self):
        row = dict(self.row(), token_ids=[197, 198], terminal=False)
        encoded = native.encode_own(row, Tokenizer(), 5)
        self.assertEqual(encoded.input_ids, (1, 215, 212, 197, 198))
        self.assertEqual(encoded.target_ids, (197, 198))

    def test_encode_rejects_visibility_and_token_mutations(self):
        cases = [
            ({'split': 'HELD'}, 'child_targets_only'),
            ({'actor': 'parent'}, 'child_targets_only'),
            ({'prefix_loss': True}, 'child_targets_only'),
            ({'target_loss': False}, 'child_targets_only'),
            ({'prefix_loss': 0}, 'child_targets_only'),
            ({'target_loss': 1}, 'child_targets_only'),
            ({'token_ids': []}, 'actual_native_target_ids'),
            ({'token_ids': [True, 2]}, 'actual_native_target_ids'),
            ({'token_ids': [-1, 2]}, 'actual_native_target_ids'),
            ({'token_ids': [197.0, 2]}, 'actual_native_target_ids'),
            ({'token_ids': [197, 198]}, 'actual_terminal_eos'),
            ({'token_ids': [197, 2, 2]}, 'no_special_token_target_injection'),
            ({'token_ids': [1, 2]}, 'no_special_token_target_injection'),
            ({'terminal': False}, 'no_special_token_target_injection'),
            ({'target': 'rewritten'}, 'native_target_roundtrip'),
        ]
        for changes, reason in cases:
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, reason):
                native.encode_own(dict(self.row(), **changes), Tokenizer(), 100)

    def test_encode_rejects_one_token_over_budget_without_trimming(self):
        row = self.row()
        before = deepcopy(row)
        with self.assertRaisesRegex(ValueError, 'whole_source_no_training_trim'):
            native.encode_own(row, Tokenizer(), 5)
        self.assertEqual(row, before)

    def test_schedule_rounds_then_old_rows_once_without_mutation(self):
        new_rows = [dict(source_sha256='first'), dict(source_sha256='second')]
        old_rows = [dict(source_sha256='old-first'), dict(source_sha256='old-second')]
        before = deepcopy((new_rows, old_rows))
        schedule = native.presentation_schedule(new_rows, old_rows)
        self.assertEqual([(kind, row['source_sha256']) for kind, row in schedule],
            [('NEW', 'first'), ('NEW', 'second')]*16
            + [('REHEARSAL', 'old-first'), ('REHEARSAL', 'old-second')])
        self.assertTrue(all(row is new_rows[index % 2] for index, (_, row) in enumerate(schedule[:32])))
        self.assertEqual((new_rows, old_rows), before)
        self.assertEqual(len(native.presentation_schedule(new_rows, [])), 32)
        with self.assertRaisesRegex(ValueError, 'new_rows_required'):
            native.presentation_schedule([], old_rows)

    def test_plan_accepts_inclusive_limits_and_unbounded_sleep_count(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(native.time, 'time', return_value=100):
            plan = make_plan(directory)
            for changes in (dict(segment_tokens=1, context_limit=2),
                            dict(segment_tokens=1024, context_limit=8192, physical=7),
                            dict(max_sleeps=None, hard_end_unix=880, lease_end_unix=1000)):
                candidate = dict(plan, **changes)
                self.assertIs(native.validate_plan(candidate), candidate)

    def test_plan_rejects_contract_schedule_path_and_wall_mutations(self):
        cases = [
            ('schema', 'other', 'frozen_native_contract'),
            ('base_sha256', '0'*64, 'frozen_native_contract'),
            ('system_prompt', native.SYSTEM+' ', 'exact_posted_prompts'),
            ('birth_prompt', 'other', 'exact_posted_prompts'),
            ('compaction_invitation', 'other', 'exact_posted_prompts'),
            ('new_presentations', 15, 'declared_presentation_and_anchor_schedule'),
            ('rehearsal_presentations', 2, 'declared_presentation_and_anchor_schedule'),
            ('anchor_lambda', 0.5, 'declared_presentation_and_anchor_schedule'),
            *[('seed', value, 'explicit_experiment_seed') for value in (True, -1, 2**32, 1.5, '1', None)],
            ('segments_per_sleep', 3, 'initial_native_schedule'),
            *[('segment_tokens', value, 'bounded_native_segment') for value in (True, 0, 1025, 1.5)],
            *[('context_limit', value, 'bounded_native_context') for value in (True, 16, 8193)],
            *[('max_sleeps', value, 'explicit_smoke_or_long_life') for value in (True, 0, -1, 1.5)],
            *[('physical', value, 'explicit_gpu_identity') for value in (True, -1, 8)],
            ('gpu_uuid', 'other', 'explicit_gpu_identity'),
            *[('hard_end_unix', value, 'within_lease_wall') for value in (100, 99, 981)],
            ('decoder', {}, 'posted_decoder'),
            *[(key, 'relative', 'absolute_path:'+key) for key in ('root', 'model_dir', 'anchors', 'source_root')],
        ]
        with tempfile.TemporaryDirectory() as directory, patch.object(native.time, 'time', return_value=100):
            plan = make_plan(directory)
            for key, value, reason in cases:
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, reason):
                    native.validate_plan(dict(plan, **{key: value}))
            source = Path(plan['source_root'])
            source.mkdir()
            alias = Path(directory)/'alias'
            alias.symlink_to(source, target_is_directory=True)
            for root in (source, source/'raw', alias/'raw'):
                with self.subTest(root=root), self.assertRaisesRegex(ValueError, 'raw_outside_source_tree'):
                    native.validate_plan(dict(plan, root=str(root)))


class StartupContextPlanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.plan = make_plan(temporary.name)
        self.source = Path(self.plan['source_root'])
        self.source.mkdir()
        self.startup = self.source / 'startup.md'

    def bind(self, text='You are a new pilot. Keep notes and learn from feedback.\n'):
        self.startup.write_text(text)
        self.plan['birth_prompt'] = text
        self.plan['startup_context'] = dict(version='R127_STARTUP_V1', path=str(self.startup),
                                           sha256=native.sha(self.startup))
        return self.plan

    def test_pinned_startup_accepts_exact_text_without_mutating_plan(self):
        plan = self.bind()
        before = deepcopy(plan)
        self.assertIs(native.validate_plan(plan), plan)
        self.assertEqual(plan, before)

    def test_legacy_birth_stays_frozen_without_startup_binding(self):
        for binding in ({}, {'startup_context': None}):
            plan = dict(self.plan, **binding)
            self.assertIs(native.validate_plan(plan), plan)
            with self.assertRaisesRegex(ValueError, 'exact_posted_prompts'):
                native.validate_plan(dict(plan, birth_prompt='unbound new startup'))

    def test_startup_binding_requires_exact_fields_and_version(self):
        plan = self.bind()
        binding = plan['startup_context']
        variants = [[], 'R127_STARTUP_V1', {}, dict(binding, version='R127_STARTUP_V2'),
                    dict(binding, machine_configuration='must not enter binding')]
        variants.extend({key: value for key, value in binding.items() if key != omitted}
                        for omitted in binding)
        for candidate in variants:
            with self.subTest(binding=candidate), self.assertRaisesRegex(ValueError, 'exact_R127_startup_binding'):
                native.validate_plan(dict(plan, startup_context=candidate))

    def test_startup_hash_rejects_wrong_pin_and_changed_source(self):
        plan = self.bind()
        with self.assertRaisesRegex(ValueError, 'pinned_startup_source'):
            native.validate_plan(dict(plan, startup_context=dict(plan['startup_context'], sha256='0' * 64)))
        self.startup.write_text('Changed after the plan was pinned.\n')
        with self.assertRaisesRegex(ValueError, 'pinned_startup_source'):
            native.validate_plan(plan)

    def test_startup_path_must_be_absolute_inside_source_and_not_symlink(self):
        plan = self.bind()
        outside = self.source.with_name(self.source.name + '-other')
        outside.mkdir()
        outside_file = outside / 'startup.md'
        outside_file.write_bytes(self.startup.read_bytes())
        alias = self.source / 'alias.md'
        alias.symlink_to(self.startup)
        escaped = self.source / 'escaped'
        escaped.symlink_to(outside, target_is_directory=True)
        for path in ('startup.md', str(outside_file), str(alias), str(escaped / 'startup.md')):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'pinned_startup_source'):
                native.validate_plan(dict(plan, startup_context=dict(plan['startup_context'], path=path)))

    def test_startup_excludes_mismatch_empty_machine_configuration_and_placeholders(self):
        plan = self.bind()
        with self.assertRaisesRegex(ValueError, 'child_facing_startup_only'):
            native.validate_plan(dict(plan, birth_prompt=plan['birth_prompt'] + 'extra'))
        cases = [('', 'child_facing_startup_only'),
                 ('Hello.\n## Machine-side configuration\nprivate paths', 'child_facing_startup_only'),
                 ('Welcome [PILOT_NAME].', 'startup_placeholders_filled'),
                 ('Workspace: [WORKSPACE_PATH]', 'startup_placeholders_filled')]
        for text, reason in cases:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, reason):
                native.validate_plan(self.bind(text))

    def test_startup_limit_counts_utf8_bytes(self):
        for text in ('a' * 16384, 'é' * 8192):
            with self.subTest(length=len(text)):
                plan = self.bind(text)
                self.assertIs(native.validate_plan(plan), plan)
                with self.assertRaisesRegex(ValueError, 'child_facing_startup_only'):
                    native.validate_plan(self.bind(text + 'a'))

    def test_startup_does_not_relax_system_or_compaction_prompts(self):
        plan = self.bind()
        for field in ('system_prompt', 'compaction_invitation'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'exact_posted_prompts'):
                native.validate_plan(dict(plan, **{field: plan[field] + ' changed'}))


class SeedInitializationTests(unittest.TestCase):
    def setUp(self):
        from gpu import astra_experienced_event_microloop as source
        self.source = source
        self.plan = make_plan('/tmp/synthetic-r133')
        self.events = []
        self.generator = random.Random()
        self.torch = Mock(float32='fp32')
        self.parameter = Mock(dtype='fp32')
        self.base = Mock()
        self.model = Mock(config=SimpleNamespace(max_position_embeddings=32768, use_cache=True))
        self.model.to.return_value = self.model
        self.model.named_parameters.return_value = [('model.lora_A.default.weight', self.parameter)]
        self.engine = SimpleNamespace(torch=self.torch, model=self.base, hook=Mock())
        self.peft = SimpleNamespace(LoraConfig=Mock(), get_peft_model=Mock(side_effect=self.initialize))
        self.initial_values = []
        self.torch.manual_seed.side_effect = self.seed_torch
        self.torch.cuda.manual_seed_all.side_effect = lambda seed: self.events.append(('cuda_seed', seed))
        self.start_patch(patch.dict(sys.modules, peft=self.peft))
        self.start_patch(patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.plan['gpu_uuid']))
        self.start_patch(patch.object(source.native, 'load_local_tokenizer', return_value=Tokenizer()))
        self.load = self.start_patch(patch.object(source, 'Engine', side_effect=self.load_engine))
        self.python_seed = self.start_patch(patch.object(native.random, 'seed',
            side_effect=lambda seed: self.events.append(('python_seed', seed))))
        self.python_restore = self.start_patch(patch.object(native.random, 'setstate'))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def seed_torch(self, seed):
        self.events.append(('torch_seed', seed))
        self.generator.seed(seed)

    def load_engine(self, options, tokenizer, *, check):
        self.assertEqual(options.phase, 'readout')
        self.assertEqual(options.device, 'cuda:0' if options.adapter_dir else 'cpu')
        self.events.append(('load', options.adapter_dir))
        self.engine.model = self.model if options.adapter_dir else self.base
        return self.engine

    def initialize(self, base, config, **kwargs):
        self.assertIs(base, self.base)
        self.assertEqual(kwargs, dict(autocast_adapter_dtype=True))
        self.events.append(('lora', None))
        self.initial_values.append(tuple(self.generator.random() for unused in range(4)))
        return self.model

    def test_seed_applies_before_lora_for_new_lives_and_recipe_is_unchanged(self):
        from gpu.astra_pchain2_native import TARGET_MODULES
        for seed in (0, 1, 1):
            self.events.clear()
            child = NativeChild(dict(self.plan, seed=seed))
            self.assertEqual(self.events, [('load', None), ('python_seed', seed), ('torch_seed', seed),
                ('cuda_seed', seed), ('lora', None), ('python_seed', seed), ('torch_seed', seed), ('cuda_seed', seed)])
            self.assertEqual(child.experiment['seed'], seed)
        self.assertEqual(self.initial_values[1], self.initial_values[2])
        self.assertNotEqual(self.initial_values[0], self.initial_values[1])
        self.peft.LoraConfig.assert_called_with(r=8, lora_alpha=16, lora_dropout=0.05,
            target_modules=list(TARGET_MODULES), bias='none', task_type='CAUSAL_LM',
            init_lora_weights=True, use_rslora=False, use_dora=False)
        self.assertFalse(self.model.config.use_cache)
        self.torch.optim.AdamW.assert_called_with([self.parameter], lr=3e-5,
            betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01, foreach=False, fused=False)

    def checkpoint_and_payload(self, seed, bound=True):
        binding = native.experiment_binding(dict(self.plan, seed=seed))
        checkpoint = dict(adapter_path='/tmp/synthetic-r133/saved-adapter',
            optimizer_rng_path='/tmp/synthetic-r133/saved-rng', adapter_state_sha256='a'*64)
        payload = dict(parameter_names=['model.lora_A.default.weight'], optimizer={'saved': True},
            optimizer_steps=19, cpu_rng='saved_cpu', cuda_rng=['saved_cuda'], python_rng='saved_python')
        if bound:
            checkpoint['experiment'] = binding
            payload['experiment'] = deepcopy(binding)
        return checkpoint, payload

    def test_existing_legacy_and_seeded_lineages_restore_rng_without_any_reseeding(self):
        for seed, bound in ((0, False), (0, True), (1, True)):
            checkpoint, payload = self.checkpoint_and_payload(seed, bound)
            self.torch.load.return_value = payload
            with patch.object(NativeChild, 'verify_checkpoint'), \
                    patch.object(NativeChild, 'adapter_hash', return_value=checkpoint['adapter_state_sha256']):
                child = NativeChild(dict(self.plan, seed=seed), checkpoint)
            self.assertEqual(child.optimizer_steps, 19)
            self.torch.set_rng_state.assert_called_with('saved_cpu')
            self.torch.cuda.set_rng_state_all.assert_called_with(['saved_cuda'])
            self.python_restore.assert_called_with('saved_python')
            self.torch.optim.AdamW.return_value.load_state_dict.assert_called_with({'saved': True})
        self.peft.get_peft_model.assert_not_called()
        self.torch.manual_seed.assert_not_called()
        self.torch.cuda.manual_seed_all.assert_not_called()
        self.python_seed.assert_not_called()

    def test_optimizer_seed_binding_mismatch_fails_before_restoring_rng(self):
        checkpoint, payload = self.checkpoint_and_payload(1)
        payload['experiment']['seed'] = 0
        self.torch.load.return_value = payload
        with patch.object(NativeChild, 'verify_checkpoint'), \
                self.assertRaisesRegex(ValueError, 'optimizer_experiment_binding'):
            NativeChild(dict(self.plan, seed=1), checkpoint)
        self.torch.set_rng_state.assert_not_called()
        self.torch.cuda.set_rng_state_all.assert_not_called()
        self.python_restore.assert_not_called()
        self.peft.get_peft_model.assert_not_called()

    def test_seed_change_on_legacy_checkpoint_fails_before_model_load(self):
        checkpoint, payload = self.checkpoint_and_payload(0, bound=False)
        with self.assertRaisesRegex(ValueError, 'legacy_experiment_configuration_frozen'):
            NativeChild(dict(self.plan, seed=1), checkpoint)
        self.load.assert_not_called()
        self.peft.get_peft_model.assert_not_called()

    def test_checkpoint_binds_experiment_in_commit_and_hashed_rng_payload(self):
        child = NativeChild(dict(self.plan, seed=1))
        self.engine.verify_base = Mock()
        self.model.save_pretrained.side_effect = lambda path, **kwargs: (path.mkdir(), (path/'weights').write_bytes(b'adapter'))
        self.torch.save.side_effect = lambda payload, stream: stream.write(b'synthetic payload')
        with tempfile.TemporaryDirectory() as directory, patch.object(child, 'adapter_hash', return_value='a'*64):
            checkpoint = child.checkpoint(Path(directory)/'checkpoint')
            payload = self.torch.save.call_args.args[0]
            self.assertEqual(checkpoint['experiment'], native.experiment_binding(dict(self.plan, seed=1)))
            self.assertEqual(payload['experiment'], checkpoint['experiment'])
            self.assertEqual(checkpoint['checkpoint_sha256']['rng'], native.sha(checkpoint['optimizer_rng_path']))
            NativeChild.verify_checkpoint(checkpoint)


class SyntheticChild:
    def __init__(self, plan, checkpoint=None):
        self.plan = plan
        self.experiment = deepcopy(checkpoint.get('experiment')) if checkpoint else native.experiment_binding(plan)
        self.tokenizer = Tokenizer()
        self.engine = SimpleNamespace(runtime={'synthetic': True})
        self.optimizer_steps = checkpoint['optimizer_steps'] if checkpoint else 0
        self.generations = 0
        self.sleeps = []
        self.loaded_checkpoint = checkpoint
        if checkpoint:
            NativeChild.verify_checkpoint(checkpoint)
            native.verify_experiment_resume(plan, self.experiment)

    def adapter_hash(self):
        return digest(['synthetic-adapter', self.optimizer_steps])

    def checkpoint(self, directory):
        directory = Path(directory)
        adapter_path = directory/'adapter'
        adapter_path.mkdir(parents=True)
        (adapter_path/'weights').write_text(str(self.optimizer_steps))
        optimizer_path = directory/'optimizer_rng.pt'
        optimizer_path.write_text('synthetic optimizer and RNG '+str(self.optimizer_steps))
        files = {'weights': native.sha(adapter_path/'weights')}
        checkpoint = dict(base_sha256=native.BASE_SHA256, adapter_path=str(adapter_path),
            adapter_files=files, adapter_state_sha256=self.adapter_hash(),
            optimizer_rng_path=str(optimizer_path), optimizer_steps=self.optimizer_steps,
            checkpoint_sha256=dict(adapter=digest(files), optimizer=native.sha(optimizer_path),
                                   rng=native.sha(optimizer_path)))
        if self.experiment is not None:
            checkpoint['experiment'] = deepcopy(self.experiment)
        native.write_once(directory/'COMMIT.json', checkpoint)
        return checkpoint

    def count_tokens(self, messages):
        return sum(len(message['content'].split())+4 for message in messages)

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.generations += 1
        if self.generations > 12:
            raise AssertionError('synthetic generation budget exhausted')
        if deadline_unix != self.plan['hard_end_unix'] or max_new_tokens != self.plan['segment_tokens']:
            raise AssertionError('generation budget changed')
        raw = 'own '+str(self.generations)
        return dict(raw=raw, token_ids=[ord(character)+100 for character in raw]+[2],
                    terminal=True, truncated=False)

    def sleep(self, new_rows, old_rows, anchors, record):
        self.sleeps.append(deepcopy((new_rows, old_rows)))
        schedule = native.presentation_schedule(new_rows, old_rows)
        self.optimizer_steps += len(schedule)
        record('UPDATE', dict(optimizer_step=self.optimizer_steps, synthetic=True))
        return dict(optimizer_steps=len(schedule), total_optimizer_steps=self.optimizer_steps)


class NativeLoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.plan = make_plan(self.directory)
        Path(self.plan['root']).mkdir()
        self.plan_path = self.directory/'plan.json'
        native.write_once(self.plan_path, self.plan)
        self.children = []
        self.readouts = []
        self.fail_generate = False
        self.fail_sleep = False
        self.stop_after_readout = None
        self.stop_before_readout = None
        self.start_patch(patch.object(native, 'NativeChild', side_effect=self.make_child))
        self.start_patch(patch.object(native, 'fresh_readout', side_effect=self.observe_readout))
        self.start_patch(patch('gpu.orch_r107_base_anchors_inventory.build_inventory',
                               return_value=({}, {'synthetic': True})))
        self.start_patch(patch.object(native.signal, 'signal'))
        self.start_patch(patch.object(native.signal, 'setitimer'))
        self.start_patch(patch.object(native.subprocess, 'Popen', side_effect=AssertionError('no launches')))
        self.start_patch(patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def make_child(self, plan, checkpoint=None):
        child = SyntheticChild(plan, checkpoint)
        if self.fail_generate:
            child.generate = self.interrupt
        if self.fail_sleep:
            child.sleep = self.interrupt
        self.children.append(child)
        return child

    @staticmethod
    def interrupt(*args, **kwargs):
        raise RuntimeError('synthetic interruption')

    def records(self):
        return [native.read(path) for path in sorted((Path(self.plan['root'])/'stream'/'records').glob('*.json'))
                if not path.name.endswith('.intent.json')]

    def observe_readout(self, child, plan_path, checkpoint, cycle):
        records = self.records()
        self.assertIn(records[-1]['kind'], ('LOADED', 'SLEEP_COMPLETE'))
        committed = next(record for record in reversed(records)
                         if record['kind'] in ('COMMITTED', 'SLEEP_COMPLETE'))
        self.assertEqual(committed['kind'], 'COMMITTED' if cycle == 0 else 'SLEEP_COMPLETE')
        state = committed['document']['state' if cycle == 0 else 'resume_state']['state']
        self.assertEqual(state['model_state_sha256'], digest(checkpoint['checkpoint_sha256']))
        self.assertEqual(child.optimizer_steps, checkpoint['optimizer_steps'])
        self.assertEqual(plan_path, self.plan_path)
        if self.stop_before_readout == cycle:
            self.interrupt()
        native.write_once(Path(self.plan['root'])/'readouts'/f'sleep_{cycle:06d}_DISPATCH.json',
                          dict(cycle=cycle, synthetic=True))
        self.readouts.append(cycle)
        if self.stop_after_readout == cycle:
            self.interrupt()

    def restore(self):
        with StreamJournal(Path(self.plan['root'])/'stream') as journal:
            return ContinualStream.restore(**journal.latest_checkpoint())

    def test_two_sleeps_use_native_compaction_order_and_real_journal(self):
        native.run(self.plan_path)
        records = self.records()
        expected = ['COMMITTED', 'LOADED']
        for unused in range(2):
            expected += ['REQUEST', 'RESPONSE', 'COMMITTED']*3
            expected += ['COMPACTION', 'SLEEP_REQUEST', 'UPDATE', 'SLEEP_COMPLETE']
        expected += ['REQUEST', 'RESPONSE', 'COMMITTED', 'TERMINAL']
        self.assertEqual([record['kind'] for record in records], expected)
        self.assertEqual(self.readouts, [0, 1, 2])
        stream = self.restore()
        self.assertIsNone(stream.pending)
        self.assertEqual(stream.sleep_frontier, 6)
        self.assertEqual(len(stream.rows), 7)
        self.assertEqual(len(stream.sleep_receipts), 2)
        self.assertEqual([len(new) for new, old in self.children[0].sleeps], [3, 3])
        self.assertEqual([len(old) for new, old in self.children[0].sleeps], [0, 3])
        self.assertEqual(self.children[0].optimizer_steps, 99)
        self.assertEqual([row['source_sha256'] for row in stream.pending_rows()], [stream.rows[-1]['source_sha256']])
        self.assertEqual(stream.rows[-1]['model_state_sha256'], stream.model_state_sha256)
        self.assertEqual(Counter(operation['kind'] for operation in stream.history.operations), {'compaction': 2})
        for index, operation in enumerate(stream.history.operations):
            self.assertEqual(operation['summary']['text'], stream.rows[index*3+2]['target'])
            self.assertEqual(operation['summary']['actor'], 'child')
        self.assertFalse(records[-1]['document']['retained_learning_claim'])

    def test_empty_summary_does_not_stop_continuation_or_invent_compaction(self):
        original = SyntheticChild.generate

        def generate(child, messages, **kwargs):
            response = original(child, messages, **kwargs)
            response.update(raw='', token_ids=[2], terminal=True, truncated=False)
            return response

        with patch.object(SyntheticChild, 'generate', generate):
            native.run(self.plan_path)
        records = self.records()
        stream = self.restore()
        self.assertEqual(sum(record['kind'] == 'COMPACTION_SKIPPED' for record in records), 2)
        self.assertEqual(len(stream.rows), 7)
        self.assertEqual(len(stream.sleep_receipts), 2)
        self.assertEqual(len(stream.history.operations), 0)
        budget = stream.history.events[0]
        self.assertEqual(budget.event_id, 'runtime:birth_budget')
        self.assertEqual(budget.actor, 'environment')
        self.assertIn('context_limit', budget.text)

    def select_experiment(self, variant, seed=0):
        self.plan.update(presleep_variant=variant, compaction_invitation=native.PRESLEEP_INVITATIONS[variant], seed=seed)
        self.plan_path.write_text(json.dumps(self.plan))
        self.start_patch(patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)))

    def test_no_distillation_preserves_history_frontier_and_context_through_sleep(self):
        self.select_experiment('no_distillation')
        observations = []
        original = native.prepare_sleep

        def prepare(child, stream, journal, cycle):
            before = stream.checkpoint()
            rendered = stream.render(child.count_tokens)
            original(child, stream, journal, cycle)
            self.assertEqual(stream.checkpoint(), before)
            self.assertEqual(stream.render(child.count_tokens), rendered)
            observations.append(before)

        with patch.object(native, 'prepare_sleep', side_effect=prepare):
            native.run(self.plan_path)
        records = self.records()
        stream = self.restore()
        self.assertEqual(len(observations), 2)
        self.assertEqual(stream.sleep_frontier, 4)
        self.assertEqual(len(stream.rows), 5)
        self.assertEqual([len(new) for new, old in self.children[0].sleeps], [2, 2])
        self.assertEqual([len(old) for new, old in self.children[0].sleeps], [0, 2])
        self.assertEqual(self.children[0].optimizer_steps, 66)
        self.assertEqual(self.readouts, [0, 1, 2])
        self.assertEqual(stream.history.visible_frontier.event_count, 0)
        self.assertEqual(stream.history.operations, ())
        self.assertFalse(any(event.phase in ('presleep', 'compaction') for event in stream.history.events))
        self.assertFalse(any(record['kind'].startswith('COMPACTION') for record in records))
        for record in records:
            if record['kind'] == 'SLEEP_COMPLETE':
                cycle = record['document']['cycle']
                self.assertEqual(record['document']['resume_state']['state']['history'],
                                 observations[cycle-1]['state']['history'])
        for earlier in stream.rows[:4]:
            self.assertIn(earlier['target'], str(stream.rows[-1]['prefix']))
        for row in stream.rows:
            encoded = native.encode_own(row, Tokenizer(), 32768)
            prefix_size = len(encoded.input_ids)-len(row['token_ids'])
            self.assertEqual(encoded.labels[:prefix_size], (-100,)*prefix_size)
            self.assertEqual(encoded.labels[prefix_size:], tuple(row['token_ids']))

    def test_parent_guidance_uses_ordinary_inbox_and_masks_all_prefix_tokens(self):
        self.select_experiment('parent_guided_distillation', seed=1)
        original = native.prepare_sleep
        guidance = 'PARENT_ONLY_SENTINEL select the observation rather than the prediction.'

        def prepare(child, stream, journal, cycle):
            native.write_once(journal.inbox/f'guidance-{cycle}.json',
                dict(id=f'guide-{cycle}', actor='parent', split='TRAIN', text=guidance))
            original(child, stream, journal, cycle)

        with patch.object(native, 'prepare_sleep', side_effect=prepare):
            native.run(self.plan_path)
        stream = self.restore()
        self.assertEqual(len([event for event in stream.history.events if event.actor == 'parent']), 2)
        self.assertEqual([len(new) for new, old in self.children[0].sleeps], [3, 3])
        self.assertEqual(self.readouts, [0, 1, 2])
        for index in (2, 5):
            row = stream.rows[index]
            self.assertIn(guidance, str(row['prefix']))
            self.assertIn(self.plan['compaction_invitation'], str(row['prefix']))
            self.assertNotIn('PARENT_ONLY_SENTINEL', row['target'])
            encoded = native.encode_own(row, Tokenizer(), 32768)
            prefix_size = len(encoded.input_ids)-len(row['token_ids'])
            self.assertEqual(encoded.labels[:prefix_size], (-100,)*prefix_size)
            self.assertEqual(encoded.labels[prefix_size:], tuple(row['token_ids']))
        self.assertTrue(all(row['actor'] == 'child' and row['target_loss'] is True
                            and row['prefix_loss'] is False for row in stream.rows))

    def test_reread_selection_receives_history_and_carries_child_passages(self):
        self.select_experiment('reread_select')
        native.run(self.plan_path)
        stream = self.restore()
        for index in (2, 5):
            row = stream.rows[index]
            self.assertIn(self.plan['compaction_invitation'], str(row['prefix']))
            self.assertIn(stream.rows[index-2]['target'], str(row['prefix']))
            self.assertIn(stream.rows[index-1]['target'], str(row['prefix']))
            self.assertEqual(stream.history.operations[index//3]['summary']['text'], row['target'])
        self.assertEqual(self.readouts, [0, 1, 2])

    def test_resume_rejects_seed_variant_and_prompt_changes_before_loading(self):
        self.stop_at_committed_sleep()
        before = self.records()
        source = Path(self.plan['source_root'])
        source.mkdir()
        startup = source/'changed-startup.md'
        startup.write_text('Changed initial prompt.')
        changes = [dict(seed=1), dict(birth_prompt=startup.read_text(), startup_context=dict(
            version='R127_STARTUP_V1', path=str(startup), sha256=native.sha(startup)))]
        changes += [dict(presleep_variant=variant, compaction_invitation=invitation)
                    for variant, invitation in native.PRESLEEP_INVITATIONS.items() if variant != 'free_distillation']
        for change in changes:
            self.plan_path.write_text(json.dumps(dict(self.plan, **change)))
            with self.subTest(change=change), patch.dict(os.environ,
                    R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                    self.assertRaisesRegex(ValueError, 'resume_experiment_mismatch'):
                native.run(self.plan_path, resume=True)
            self.assertEqual(self.records(), before)
            self.assertEqual(len(self.children), 1)

    def test_seed1_variant_resume_preserves_binding_and_does_not_rebirth(self):
        self.select_experiment('no_distillation', seed=1)
        self.stop_at_committed_sleep()
        before = self.restore().checkpoint()
        native.run(self.plan_path, resume=True)
        stream = self.restore()
        binding = native.experiment_binding(self.plan)
        self.assertEqual(stream.experiment, binding)
        self.assertEqual(stream.rows[:2], before['state']['rows'])
        self.assertEqual(self.children[1].loaded_checkpoint['experiment'], binding)
        self.assertEqual([len(new) for new, old in self.children[1].sleeps], [2])
        for path in (Path(self.plan['root'])/'checkpoints').glob('*/COMMIT.json'):
            self.assertEqual(native.read(path)['experiment'], binding)

    def test_resume_rejects_model_binding_drift_before_loading(self):
        self.stop_at_committed_sleep()
        before = self.records()
        checkpoint_path = Path(self.plan['root'])/'checkpoints/sleep_000001/COMMIT.json'
        checkpoint = native.read(checkpoint_path)
        checkpoint['experiment']['seed'] = 1
        checkpoint_path.write_text(json.dumps(checkpoint))
        with self.assertRaisesRegex(ValueError, 'stream_model_experiment_binding'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_legacy_run_resumes_without_relabelling_or_changing_saved_artifacts(self):
        with patch.object(native, 'experiment_binding', return_value=None):
            self.stop_at_committed_sleep()
        before = self.restore().checkpoint()
        records = self.records()
        self.assertNotIn('experiment', before['state'])
        files = {path: path.read_bytes() for path in (Path(self.plan['root'])/'checkpoints').rglob('*') if path.is_file()}
        self.plan_path.write_text(json.dumps(dict(self.plan, seed=1)))
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                self.assertRaisesRegex(ValueError, 'legacy_experiment_configuration_frozen'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), records)
        self.assertEqual(len(self.children), 1)
        self.plan_path.write_text(json.dumps(self.plan))
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)):
            native.run(self.plan_path, resume=True)
        self.assertEqual({path: path.read_bytes() for path in files}, files)
        self.assertIsNone(self.restore().experiment)
        self.assertNotIn('experiment', self.restore().checkpoint()['state'])
        self.assertEqual(self.restore().rows[:3], before['state']['rows'])
        self.assertNotIn('experiment', native.read(Path(self.plan['root'])/'checkpoints/sleep_000002/COMMIT.json'))

    def test_native_creates_missing_life_directory_before_journal(self):
        Path(self.plan['root']).rmdir()
        native.run(self.plan_path)
        self.assertEqual(len(self.restore().sleep_receipts), 2)

    def test_verified_preupdate_recovery_finishes_only_existing_pending_rows(self):
        original = SyntheticChild.sleep

        def fail_second(child, *args, **kwargs):
            if child.optimizer_steps == 48:
                raise RuntimeError('encoding failed before updates')
            return original(child, *args, **kwargs)

        with patch.object(SyntheticChild, 'sleep', fail_second):
            with self.assertRaisesRegex(RuntimeError, 'encoding failed before updates'):
                native.run(self.plan_path)
        before = self.restore()
        self.assertIsNotNone(before.pending)
        rows = deepcopy(before.rows)
        plan = dict(self.plan, preupdate_recovery={'explicit_test_recovery': True})
        self.plan_path.write_text(json.dumps(plan))
        self.stop_after_readout = 2

        def reconstructed(child, stream, journal, recovery):
            self.assertEqual(child.optimizer_steps, 48)
            self.assertEqual(stream.rows, rows)
            self.assertEqual(stream.pending, before.pending)
            self.assertEqual(self.records()[-1]['kind'], 'SLEEP_REQUEST')
            return dict(status='COMPLETE', rng_reconstruction_verified=True)

        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                patch('gpu.orch_r125_preupdate_recovery.recover_rng', side_effect=reconstructed) as recover:
            with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
                native.run(self.plan_path, resume=True)
        recover.assert_called_once()
        restored = self.restore()
        self.assertIsNone(restored.pending)
        self.assertEqual(restored.rows, rows)
        self.assertEqual(restored.sleep_frontier, 6)
        self.assertEqual(len(restored.sleep_receipts), 2)
        self.assertEqual(self.children[-1].optimizer_steps, 99)

    def test_pending_generation_resume_never_loads_or_redispatches(self):
        self.fail_generate = True
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        before = self.records()
        self.assertEqual(before[-1]['kind'], 'REQUEST')
        self.assertIsNotNone(self.restore().pending)
        with self.assertRaisesRegex(ValueError, 'unresolved_generation_or_sleep_requires_reconciliation'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_pending_sleep_resume_cannot_fall_back_to_initial_adapter(self):
        self.fail_sleep = True
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        before = self.records()
        self.assertEqual(before[-1]['kind'], 'SLEEP_REQUEST')
        self.assertTrue(self.restore().pending.startswith('sleep:'))
        with self.assertRaisesRegex(ValueError, 'unresolved_generation_or_sleep_requires_reconciliation'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def stop_at_committed_sleep(self):
        self.stop_after_readout = 1
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        self.assertIsNone(self.restore().pending)
        self.stop_after_readout = None

    def test_resume_after_sleep_loads_exact_checkpoint_without_replaying_birth(self):
        self.stop_at_committed_sleep()
        first_rows = deepcopy(self.restore().rows)
        native.run(self.plan_path, resume=True)
        stream = self.restore()
        self.assertEqual(stream.rows[:3], first_rows)
        self.assertEqual(self.readouts, [0, 1, 2])
        self.assertEqual(self.children[1].loaded_checkpoint['optimizer_steps'], 48)
        self.assertEqual(self.children[1].optimizer_steps, 99)
        self.assertEqual(len(self.children[1].sleeps), 1)
        self.assertEqual([receipt['cycle'] for receipt in stream.sleep_receipts], [1, 2])
        self.assertEqual(len(stream.rows), 7)

    def test_plain_presentation_resume_preserves_life_and_fixed_readouts(self):
        from organism_v6.orch_r125_plain_context import VERSION, has_scaffolding
        self.stop_at_committed_sleep()
        before = self.restore().checkpoint()['state']
        plan = dict(self.plan, presentation_version=VERSION, context_limit=16384)
        self.plan_path.write_text(json.dumps(plan))
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)):
            native.run(self.plan_path, resume=True)
        after = self.restore()
        transitions = [record['document']['state']['state'] for record in self.records()
                       if record['kind'] == 'PRESENTATION']
        self.assertEqual(len(transitions), 1)
        for field in ('history', 'rows', 'sleep_frontier', 'model_state_sha256', 'sleep_receipts'):
            self.assertEqual(transitions[0][field], before[field])
        self.assertEqual(after.context_limit, 16384)
        self.assertEqual(after.rows[:3], before['rows'])
        self.assertFalse(any(has_scaffolding(str(row['prefix'])) for row in after.rows[3:]))
        self.assertEqual(self.children[-1].loaded_checkpoint['optimizer_steps'], 48)
        self.assertEqual(self.readouts, [0, 1, 2])

    def test_resume_dispatches_missing_sleep_readout_before_new_generation(self):
        self.stop_before_readout = 1
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        self.assertEqual(self.readouts, [0])
        self.assertIsNone(self.restore().pending)
        self.assertEqual(self.restore().sleep_frontier, len(self.restore().rows))
        self.stop_before_readout = None
        native.run(self.plan_path, resume=True)
        self.assertEqual(self.readouts, [0, 1, 2])
        self.assertEqual(self.children[1].loaded_checkpoint['optimizer_steps'], 48)

    def test_committed_unslept_generation_cannot_resume_stale_rng(self):
        original_step = ContinualStream.step

        def stop_after_commit(stream, *args, **kwargs):
            original_step(stream, *args, **kwargs)
            self.interrupt()

        with patch.object(ContinualStream, 'step', stop_after_commit):
            with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
                native.run(self.plan_path)
        stream = self.restore()
        self.assertIsNone(stream.pending)
        self.assertEqual(len(stream.rows), 1)
        self.assertEqual(stream.sleep_frontier, 0)
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'resume_requires_saved_RNG_sleep_boundary'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_terminal_continuation_is_not_a_saved_rng_resume_boundary(self):
        native.run(self.plan_path)
        stream = self.restore()
        self.assertIsNone(stream.pending)
        self.assertEqual(len(stream.rows)-stream.sleep_frontier, 1)
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'resume_requires_saved_RNG_sleep_boundary'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_resume_rejects_missing_or_ambiguous_exact_model_checkpoint(self):
        self.stop_at_committed_sleep()
        checkpoint_path = Path(self.plan['root'])/'checkpoints'/'sleep_000001'/'COMMIT.json'
        checkpoint = native.read(checkpoint_path)
        checkpoint_path.write_text(json.dumps(dict(checkpoint,
            checkpoint_sha256=dict(adapter='0'*64, optimizer='1'*64, rng='1'*64))))
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'one_exact_model_checkpoint_for_stream'):
            native.run(self.plan_path, resume=True)
        checkpoint_path.write_text(json.dumps(checkpoint))
        native.write_once(Path(self.plan['root'])/'checkpoints'/'duplicate'/'COMMIT.json', checkpoint)
        with self.assertRaisesRegex(ValueError, 'one_exact_model_checkpoint_for_stream'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_resume_rejects_changed_wall_even_with_updated_admission_hash(self):
        self.stop_at_committed_sleep()
        self.plan_path.write_text(json.dumps(dict(self.plan,
            hard_end_unix=self.plan['hard_end_unix']-1)))
        before = self.records()
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)):
            with self.assertRaisesRegex(ValueError, 'same_resume_wall'):
                native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def wall_extension_plan(self, stream=None):
        from gpu.orch_r125_stream_journal import WALL_EXTENSION_SCHEMA
        stream = stream or self.restore()
        authorization = dict(schema=WALL_EXTENSION_SCHEMA, previous_deadline_unix=stream.deadline_unix,
            previous_stream_sha256=stream.checkpoint()['sha256'], new_deadline_unix=stream.deadline_unix + 120,
            lease_end_unix=self.plan['lease_end_unix'], safety_margin_seconds=120)
        return dict(self.plan, hard_end_unix=authorization['new_deadline_unix'],
                    authorized_wall_extension=authorization)

    def test_authorized_wall_resume_preserves_complete_saved_state_and_checkpoint_bytes(self):
        self.stop_at_committed_sleep()
        previous = self.restore().checkpoint()
        old_records = self.records()
        files = {str(path): native.sha(path) for path in (Path(self.plan['root']) / 'checkpoints').rglob('*') if path.is_file()}
        plan = self.wall_extension_plan()
        self.plan_path.write_text(json.dumps(plan))
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                patch('gpu.orch_r107_base_anchors_inventory.build_inventory', side_effect=self.interrupt):
            with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
                native.run(self.plan_path, resume=True)
        records = self.records()
        self.assertEqual(records[:-1], old_records)
        self.assertEqual(records[-1]['kind'], 'WALL_EXTENDED')
        self.assertEqual(records[-1]['document']['plan_sha256'], native.sha(self.plan_path))
        self.assertEqual(records[-1]['document']['authorization'], plan['authorized_wall_extension'])
        expected = deepcopy(previous)
        expected['state']['deadline_unix'] = plan['hard_end_unix']
        expected['sha256'] = digest(expected['state'])
        self.assertEqual(self.restore().checkpoint(), expected)
        self.assertEqual({path: native.sha(path) for path in files}, files)
        self.assertEqual(self.children[-1].optimizer_steps, 48)
        self.assertEqual(self.children[-1].loaded_checkpoint,
            native.read(Path(self.plan['root']) / 'checkpoints/sleep_000001/COMMIT.json'))
        self.assertEqual(self.children[-1].generations, 0)

    def test_wall_extension_journal_failure_does_not_mutate_restored_deadline(self):
        self.stop_at_committed_sleep()
        before = self.restore().checkpoint()
        records = self.records()
        plan = self.wall_extension_plan()
        self.plan_path.write_text(json.dumps(plan))
        captured = []
        prepare = native.prepare_wall_extension
        original_record = StreamJournal.record

        def remember(plan, stream, **kwargs):
            captured.append(stream)
            return prepare(plan, stream, **kwargs)

        def reject_wall(journal, kind, document):
            if kind == 'WALL_EXTENDED':
                raise OSError('synthetic wall publication failure')
            return original_record(journal, kind, document)

        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                patch.object(native, 'prepare_wall_extension', side_effect=remember), \
                patch.object(StreamJournal, 'record', new=reject_wall), \
                self.assertRaisesRegex(OSError, 'synthetic wall publication failure'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(captured[0].checkpoint(), before)
        self.assertEqual(self.restore().checkpoint(), before)
        self.assertEqual(self.records(), records)
        self.assertEqual(self.children[-1].generations, 0)

    def test_wall_extension_prepare_rejects_wrong_bindings_budgets_and_configuration(self):
        self.stop_at_committed_sleep()
        stream = self.restore()
        previous = stream.checkpoint()
        plan = self.wall_extension_plan(stream)
        authorization = plan['authorized_wall_extension']
        variants = []
        for changes in (dict(previous_stream_sha256='0' * 64),
                        dict(previous_deadline_unix=stream.deadline_unix - 1),
                        dict(new_deadline_unix=stream.deadline_unix),
                        dict(new_deadline_unix=stream.deadline_unix - 1),
                        dict(new_deadline_unix=plan['lease_end_unix'] - 119),
                        dict(safety_margin_seconds=119), dict(safety_margin_seconds=True),
                        dict(lease_end_unix=plan['lease_end_unix'] + 1),
                        dict(previous_deadline_unix=float('nan')), dict(extra='not authorized')):
            variant = dict(plan, authorized_wall_extension=dict(authorization, **changes))
            if 'new_deadline_unix' in changes:
                variant['hard_end_unix'] = changes['new_deadline_unix']
            variants.append(variant)
        variants += [dict(plan, segment_tokens=17), dict(plan, context_limit=4096),
                     dict(plan, preupdate_recovery={'cannot_combine': True})]
        for variant in variants:
            with self.subTest(plan=variant), self.assertRaises(ValueError):
                native.prepare_wall_extension(variant, stream, resume=True, plan_sha256='a' * 64)
            self.assertEqual(stream.checkpoint(), previous)
        with self.assertRaisesRegex(ValueError, 'wall_extension_resume_only'):
            native.prepare_wall_extension(plan, stream, resume=False, plan_sha256='a' * 64)

    def test_wall_extension_denies_pending_generation_sleep_and_unslept_rows(self):
        self.stop_at_committed_sleep()
        saved = self.restore()
        for pending, unslept in (('a' * 64, False), ('sleep:' + 'a' * 64, False), (None, True)):
            stream = ContinualStream.restore(saved.checkpoint(), expected_sha256=saved.checkpoint()['sha256'])
            stream.pending = pending
            if unslept:
                stream.sleep_frontier -= 1
            plan = self.wall_extension_plan(stream)
            before = stream.checkpoint()
            with self.subTest(pending=pending, unslept=unslept), \
                    self.assertRaisesRegex(ValueError, 'wall_extension_saved_sleep_boundary'):
                native.prepare_wall_extension(plan, stream, resume=True, plan_sha256='a' * 64)
            self.assertEqual(stream.checkpoint(), before)

    def test_wall_extension_requires_verified_checkpoint_before_audit_record(self):
        self.stop_at_committed_sleep()
        plan = self.wall_extension_plan()
        self.plan_path.write_text(json.dumps(plan))
        before = self.records()
        adapter = Path(self.plan['root']) / 'checkpoints/sleep_000001/adapter/weights'
        adapter.write_text('changed bytes')
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)

    def test_wall_extension_rejected_on_new_run_before_child_or_journal_creation(self):
        from gpu.orch_r125_stream_journal import WALL_EXTENSION_SCHEMA
        plan = dict(self.plan, authorized_wall_extension=dict(schema=WALL_EXTENSION_SCHEMA,
            previous_deadline_unix=self.plan['hard_end_unix'] - 120, previous_stream_sha256='a' * 64,
            new_deadline_unix=self.plan['hard_end_unix'], lease_end_unix=self.plan['lease_end_unix'],
            safety_margin_seconds=120))
        self.plan_path.write_text(json.dumps(plan))
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)), \
                self.assertRaisesRegex(ValueError, 'wall_extension_resume_only'):
            native.run(self.plan_path)
        self.assertEqual(self.children, [])
        self.assertFalse((Path(self.plan['root']) / 'stream').exists())

    def test_wall_extension_supports_pinned_pilot_startup_and_plain_presentation(self):
        from organism_v6.orch_r125_plain_context import VERSION
        source = Path(self.plan['source_root'])
        source.mkdir()
        startup = source / 'pilot-startup.md'
        startup.write_text('Exact pinned pilot startup.\n')
        self.plan.update(birth_prompt=startup.read_text(), presentation_version=VERSION, context_limit=16384,
            startup_context=dict(version='R127_STARTUP_V1', path=str(startup), sha256=native.sha(startup)))
        self.plan_path.write_text(json.dumps(self.plan))
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)):
            self.stop_at_committed_sleep()
        stream = self.restore()
        before = stream.checkpoint()
        document = native.prepare_wall_extension(self.wall_extension_plan(stream), stream,
                                                 resume=True, plan_sha256='a' * 64)
        self.assertEqual(document['state']['state']['history'], before['state']['history'])
        self.assertEqual(document['state']['state']['presentation'], before['state']['presentation'])
        self.assertEqual(stream.checkpoint(), before)

    def test_resume_rejects_corrupted_adapter_before_new_journal_records(self):
        self.stop_at_committed_sleep()
        adapter = Path(self.plan['root'])/'checkpoints'/'sleep_000001'/'adapter'/'weights'
        adapter.write_text('changed adapter bytes')
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_unadmitted_plan_fails_before_child_or_journal_creation(self):
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256='0'*64):
            with self.assertRaisesRegex(ValueError, 'admitted_plan_environment'):
                native.run(self.plan_path)
        self.assertFalse((Path(self.plan['root'])/'stream').exists())
        self.assertEqual(self.children, [])


class FreshReadoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.plan = make_plan(self.directory)
        self.plan_path = self.directory/'plan.json'
        native.write_once(self.plan_path, self.plan)
        self.child = SyntheticChild(self.plan)
        self.checkpoint = self.child.checkpoint(self.directory/'checkpoint')
        self.state = dict(optimizer_steps=0, python_rng='synthetic resident RNG')
        self.child.offload_for_readout = Mock(return_value=self.state)
        self.child.restore_after_readout = Mock()
        self.child.history = 'PRIVATE_RESIDENT_HISTORY_SENTINEL'
        self.output = Path(self.plan['root'])/'readouts'/'sleep_000001'
        self.process = Mock(pid=123456789)
        self.process.wait.return_value = 0
        self.process.poll.return_value = 0
        self.command = None

    def spawn(self, command, **kwargs):
        self.command = command
        self.assertEqual(kwargs['stdin'], native.subprocess.DEVNULL)
        self.assertEqual(kwargs['cwd'], self.plan['source_root'])
        self.assertTrue(kwargs['start_new_session'])
        self.child.offload_for_readout.assert_called_once_with()
        self.assertEqual(command, [native.sys.executable, '-B', '-m', 'gpu.orch_r125_continual_readout',
            '--plan', str(self.plan_path), '--checkpoint',
            str(Path(self.checkpoint['adapter_path']).parent/'COMMIT.json'), '--output', str(self.output)])
        self.assertNotIn(self.child.history, json.dumps(command))
        return self.process

    def dispatch(self, spawn=None):
        with patch.object(native.subprocess, 'Popen', side_effect=spawn or self.spawn) as launch, \
                patch.object(native.os, 'killpg', side_effect=AssertionError('unexpected process signal')):
            native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        self.assertEqual(launch.call_count, 1)
        self.child.restore_after_readout.assert_called_once_with(self.state)

    def test_fresh_process_gets_checkpoint_only_and_dispatch_is_byte_bound(self):
        def completed(command, **kwargs):
            process = self.spawn(command, **kwargs)
            native.write_once(self.output/'COMPLETE.json', {'synthetic': True})
            return process
        checkpoint_before = native.sha(Path(self.checkpoint['adapter_path']).parent/'COMMIT.json')
        self.dispatch(completed)
        dispatch = native.read(self.output.parent/'sleep_000001_DISPATCH.json')
        self.assertEqual(dispatch['command_sha256'], digest(self.command))
        self.assertEqual(dispatch['checkpoint_sha256'], checkpoint_before)
        self.assertFalse(dispatch['history_shared'])
        self.assertFalse(dispatch['parent_present'])
        self.assertNotIn(self.child.history, json.dumps(dispatch))
        self.assertFalse((self.output.parent/'sleep_000001_FAILED.json').exists())
        NativeChild.verify_checkpoint(self.checkpoint)

    def test_nonzero_exit_preserves_failure_and_restores_resident_state(self):
        self.process.wait.return_value = 7
        self.process.poll.return_value = 7
        self.dispatch()
        failure = native.read(self.output.parent/'sleep_000001_FAILED.json')
        self.assertEqual(failure['error'], 'fresh_readout_incomplete')
        self.assertFalse(failure['retry_allowed'])
        self.assertTrue(failure['continued_training_not_evidence_of_readout_success'])
        self.assertFalse((self.output/'COMPLETE.json').exists())
        NativeChild.verify_checkpoint(self.checkpoint)

    def test_zero_exit_without_completion_is_still_failure(self):
        self.dispatch()
        self.assertEqual(native.read(self.output.parent/'sleep_000001_FAILED.json')['error'],
                         'fresh_readout_incomplete')

    def test_completion_marker_cannot_override_nonzero_exit(self):
        def failed_after_marker(command, **kwargs):
            process = self.spawn(command, **kwargs)
            native.write_once(self.output/'COMPLETE.json', {'synthetic': True})
            process.wait.return_value = 7
            process.poll.return_value = 7
            return process
        self.dispatch(failed_after_marker)
        self.assertEqual(native.read(self.output.parent/'sleep_000001_FAILED.json')['error'],
                         'fresh_readout_incomplete')
        self.assertEqual(native.read(self.output/'COMPLETE.json'), {'synthetic': True})

    def test_spawn_failure_restores_resident_and_cannot_implicitly_retry(self):
        self.dispatch(Mock(side_effect=OSError('synthetic spawn failure')))
        failure_path = self.output.parent/'sleep_000001_FAILED.json'
        before = failure_path.read_bytes()
        with patch.object(native.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'readout_no_implicit_replay'):
                native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        launch.assert_not_called()
        self.child.offload_for_readout.assert_called_once_with()
        self.assertEqual(failure_path.read_bytes(), before)

    def test_existing_output_is_not_reused_or_overwritten(self):
        native.write_once(self.output/'COMPLETE.json', {'preserved': True})
        with patch.object(native.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'readout_no_implicit_replay'):
                native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        launch.assert_not_called()
        self.child.offload_for_readout.assert_not_called()
        self.assertEqual(native.read(self.output/'COMPLETE.json'), {'preserved': True})

    def test_timeout_reaps_owned_process_before_restoring_resident(self):
        events = []
        self.process.wait.side_effect = [native.subprocess.TimeoutExpired('synthetic', 1),
                                        native.subprocess.TimeoutExpired('synthetic', 5), -9]
        self.process.poll.return_value = None
        self.child.restore_after_readout.side_effect = lambda state: events.append(('restore', state))
        with patch.object(native.subprocess, 'Popen', side_effect=self.spawn), \
                patch.object(native.os, 'killpg', side_effect=lambda pid, signum: events.append((pid, signum))):
            native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        self.assertEqual(events, [(self.process.pid, native.signal.SIGTERM),
                                  (self.process.pid, native.signal.SIGKILL), ('restore', self.state)])
        self.assertEqual(self.process.wait.call_count, 3)
        self.assertEqual(native.read(self.output.parent/'sleep_000001_FAILED.json')['error_type'],
                         'TimeoutExpired')


class CheckpointBindingTests(unittest.TestCase):
    def test_checkpoint_rejects_file_and_receipt_mutations(self):
        for mutation, reason in (
                ('base', 'checkpoint_base'), ('optimizer_file', 'optimizer_RNG_file_binding'),
                ('rng_digest', 'optimizer_RNG_file_binding'), ('adapter_file', 'adapter_file_binding'),
                ('extra_adapter_file', 'adapter_file_binding'), ('missing_adapter_file', 'adapter_file_binding'),
                ('adapter_digest', 'adapter_file_binding')):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                checkpoint = SyntheticChild(make_plan(directory)).checkpoint(Path(directory)/'checkpoint')
                NativeChild.verify_checkpoint(checkpoint)
                adapter = Path(checkpoint['adapter_path'])
                if mutation == 'base':
                    checkpoint['base_sha256'] = '0'*64
                elif mutation == 'optimizer_file':
                    Path(checkpoint['optimizer_rng_path']).write_text('changed optimizer and RNG')
                elif mutation == 'rng_digest':
                    checkpoint['checkpoint_sha256']['rng'] = '0'*64
                elif mutation == 'adapter_file':
                    (adapter/'weights').write_text('changed adapter')
                elif mutation == 'extra_adapter_file':
                    (adapter/'extra').write_text('unexpected file')
                elif mutation == 'missing_adapter_file':
                    (adapter/'weights').unlink()
                else:
                    checkpoint['checkpoint_sha256']['adapter'] = '0'*64
                with self.assertRaisesRegex(ValueError, reason):
                    NativeChild.verify_checkpoint(checkpoint)


if __name__ == '__main__':
    unittest.main()
