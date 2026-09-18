"""CPU-only public-transcript and bounded native callback regression tests."""

from contextlib import contextmanager, nullcontext
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_experienced_event_microloop as native
from gpu import astra_experienced_event_adult_cycle as runner
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_sleep_recollection as recollection


def collection_fixture(*, final_lfs=1, include_messages=True, fail=False):
    bank = adult.build_bank(2)

    def generate(messages):
        fact = next(fact for fact in bank if fact['port'] in messages[1]['content'])
        raw = ('EXPLORE ' + fact['node'] + ' ' + fact['port'] if len(messages) == 2
               else native.material._event(fact).rstrip('\n') + '\n' * final_lfs)
        response = dict(raw=raw, terminal=not fail, truncated=fail)
        if include_messages:
            response['messages'] = deepcopy(messages)
        return response

    return adult.collect(generate, cycle=2)


class PromptTests(unittest.TestCase):
    def test_exact_instruction_and_user_enclosure(self):
        design = (Path(__file__).resolve().parents[1] / 'research_notes/analysis/2026-09-14_sleep_recollection_probe_design.md').read_text()
        instruction = design.split('System message:\n\n> ', 1)[1].split('\n\n', 1)[0]
        messages = recollection.build_messages(collection_fixture())
        self.assertEqual(messages[0], dict(role='system', content=instruction))
        self.assertEqual([message['role'] for message in messages], ['system', 'user'])
        self.assertTrue(messages[1]['content'].startswith('WAKE TRANSCRIPT\nW1\n'))
        self.assertTrue(messages[1]['content'].endswith(
            '\nEND WAKE TRANSCRIPT\nWrite your sleep note (at most 250 words), or NONE.'))
        self.assertEqual(recollection.MAX_NEW_TOKENS, 768)

    def test_all_raw_public_roles_text_and_lfs_preserved_without_metadata(self):
        for final_lfs in (0, 1, 3):
            with self.subTest(final_lfs=final_lfs):
                collection = collection_fixture(final_lfs=final_lfs)
                original = deepcopy(collection)
                prompt = recollection.build_messages(collection)[1]['content']
                body = prompt.removeprefix(recollection.USER_PREFIX).removesuffix(recollection.USER_SUFFIX)
                lines = body.splitlines()
                self.assertEqual(len(lines), 8)
                for index, episode in enumerate(collection['episodes']):
                    self.assertEqual(lines[2 * index], 'W' + str(index + 1))
                    transcript = json.loads(lines[2 * index + 1])
                    self.assertEqual(transcript, episode['event']['messages'] +
                                     [dict(role='assistant', content=episode['event']['raw'])])
                    self.assertEqual([message['role'] for message in transcript],
                                     ['system', 'user', 'assistant', 'user', 'assistant'])
                    self.assertEqual(transcript[2]['content'], episode['exploration']['raw'])
                for key in ('bank', 'fact', 'rows', 'accepted', 'source_raw_sha256', 'loss_policy', 'score', 'token_ids'):
                    self.assertNotIn('"' + key + '":', body)
                for fact in collection['bank']:
                    self.assertNotIn(fact['world'], body)
                self.assertEqual(collection, original)

    def test_failed_partial_corrupt_or_missing_actual_messages_rejected(self):
        with self.assertRaisesRegex(ValueError, 'four_accepted'):
            recollection.build_messages(collection_fixture(fail=True))
        with self.assertRaisesRegex(ValueError, 'full_captured_public'):
            recollection.build_messages(collection_fixture(include_messages=False))
        mutations = [lambda record: record['episodes'].pop(),
                     lambda record: record['captures'].pop(),
                     lambda record: record.update(accepted_events=3),
                     lambda record: record['episodes'][0]['event'].update(raw='invented'),
                     lambda record: record['episodes'][0]['event']['messages'][0].update(content='hidden advice'),
                     lambda record: record['bank'][0].update(outcome='hidden replacement')]
        for mutate in mutations:
            record = collection_fixture()
            mutate(record)
            with self.assertRaises(ValueError):
                recollection.build_messages(record)


class RevisionTests(unittest.TestCase):
    def prior_fixture(self, root):
        directory = root / 'recollect_rehearsal'
        directory.mkdir()
        collection = collection_fixture()
        current = dict(initial_training_result_sha256='a' * 64,
            adult_source=dict(path='fixed/collect', collection_sha256='b' * 64),
            memory_source={'old': 'fixed'}, cue_source={'cue': 'fixed'},
            prior_adult_source={'prior': 'fixed'}, development_arm='CUE_REPLAY', cycle=2,
            master=adult.SECOND_MASTER,
            arguments=dict(expected_base_sha256='c' * 64, expected_initial_adapter_sha256='d' * 64))
        prompt = recollection.build_messages(collection, recipe='rehearsal_allowed_v2')
        note = dict(messages=deepcopy(prompt), raw='Uncited opening. Next, I moved to ... NONE\n',
                    terminal=True, truncated=False)
        native.write(directory / 'SLEEP_PROMPT.json', prompt)
        native.write(directory / 'SLEEP_NOTE.json', note)
        previous = dict(deepcopy(current), schema=runner.SCHEMA, phase='recollect', state='BEFORE',
            status='RECOLLECTION_CAPTURED_NO_FIT', recollection_schema=recollection.SCHEMA,
            sleep_recipe='rehearsal_allowed_v2', parent_present=False, fits=0, model_calls=1,
            terminal=True, truncated=False, frozen_base_unchanged=True, training_admission='UNREVIEWED_NO_FIT',
            note_sha256=native.file_hash(directory / 'SLEEP_NOTE.json'), loaded_adapter_state_sha256='e' * 64,
            runner_sha256='f' * 64, material_sha256='0' * 64)
        previous['arguments'].update(sleep_recipe='rehearsal_allowed_v2', phase='recollect', state='BEFORE')
        request = {key: deepcopy(previous[key]) for key in ('schema', 'phase', 'state', 'cycle', 'master',
                   'development_arm', 'runner_sha256', 'material_sha256', 'arguments')}
        request['claim'] = 'ORIGINAL_PHASE_CLAIM'
        previous['claim'] = 'TRACE_SUPPORTED_POSED_SLEEP_NOTE_NOT_LEARNED_SELECTION_OR_UTILITY'
        native.write(directory / 'RESULT.json', previous)
        native.write(directory / 'REQUEST.json', request)
        return directory, collection, current, prompt, note

    def load(self, directory, collection, current):
        return runner.load_recollection_revision(directory, collection, current,
                                                 expected_adapter_state_sha256='e' * 64)

    def test_revision_preserves_previous_messages_note_and_exact_feedback(self):
        expected = ('Your whole note was rejected: the opening lacks W citations; “Next, I moved to” '
                    'and “Then, I went to” imply unobserved interepisode travel; trailing NONE conflicts '
                    'with a note. Regenerate the whole note. Cite every factual clause, distinguish '
                    'transcript order from observed movement, and use either a supported note or NONE '
                    'alone. Add no facts. Repetition is allowed.')
        self.assertEqual(recollection.PARENT_FEEDBACK, expected)
        with TemporaryDirectory() as temporary:
            directory, collection, current, prompt, note = self.prior_fixture(Path(temporary))
            originals = {path.name: path.read_bytes() for path in directory.iterdir()}
            messages, provenance = self.load(directory, collection, current)
            self.assertEqual(messages, prompt + [dict(role='assistant', content=note['raw']),
                                                dict(role='user', content=expected)])
            self.assertEqual(provenance['prior_note_sha256'], native.file_hash(directory / 'SLEEP_NOTE.json'))
            self.assertEqual(provenance['feedback_sha256'], native.hashlib.sha256(expected.encode()).hexdigest())
            self.assertEqual(provenance['prior_whole_note_disposition'], 'REJECTED_NOT_TRAINING_MATERIAL')
            self.assertEqual(originals, {path.name: path.read_bytes() for path in directory.iterdir()})

    def test_previous_source_receipt_actor_status_and_hash_mismatches_rejected(self):
        faults = [('initial_training_result_sha256', 'other'), ('adult_source', {}), ('memory_source', {}),
                  ('cue_source', {}), ('prior_adult_source', {}), ('development_arm', 'CUE_LOSS_OFF'),
                  ('cycle', 1), ('master', adult.MASTER), ('loaded_adapter_state_sha256', 'other'),
                  ('sleep_recipe', 'parental_revision_v1'), ('parent_present', True), ('fits', 1),
                  ('fits', False), ('model_calls', 2), ('status', 'FAILED'), ('state', 'AFTER'),
                  ('phase', 'train'), ('terminal', False), ('truncated', True),
                  ('frozen_base_unchanged', False), ('training_admission', 'APPROVED'), ('note_sha256', 'wrong')]
        for key, value in faults:
            with self.subTest(key=key, value=value), TemporaryDirectory() as temporary:
                directory, collection, current, prompt, note = self.prior_fixture(Path(temporary))
                result = native.read(directory / 'RESULT.json')
                result[key] = value
                (directory / 'RESULT.json').write_bytes(native.native._json_bytes(result))
                with self.assertRaises(ValueError):
                    self.load(directory, collection, current)
        for key in ('expected_base_sha256', 'expected_initial_adapter_sha256'):
            with self.subTest(key=key), TemporaryDirectory() as temporary:
                directory, collection, current, prompt, note = self.prior_fixture(Path(temporary))
                current['arguments'][key] = 'different'
                with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
                    self.load(directory, collection, current)

    def test_prompt_request_note_and_failure_corruption_rejected(self):
        for fault in ('prompt', 'note_messages', 'note_raw', 'request', 'FAILED.json'):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                directory, collection, current, prompt, note = self.prior_fixture(Path(temporary))
                if fault == 'prompt':
                    prompt[0]['content'] += ' Extra instruction.'
                    (directory / 'SLEEP_PROMPT.json').write_bytes(native.native._json_bytes(prompt))
                elif fault in ('note_messages', 'note_raw'):
                    note['messages' if fault == 'note_messages' else 'raw'] = [] if fault == 'note_messages' else 'Edited target'
                    (directory / 'SLEEP_NOTE.json').write_bytes(native.native._json_bytes(note))
                    result = native.read(directory / 'RESULT.json')
                    if fault == 'note_messages':
                        result['note_sha256'] = native.file_hash(directory / 'SLEEP_NOTE.json')
                        (directory / 'RESULT.json').write_bytes(native.native._json_bytes(result))
                elif fault == 'request':
                    request = native.read(directory / 'REQUEST.json')
                    request['arguments']['expected_base_sha256'] = 'different'
                    (directory / 'REQUEST.json').write_bytes(native.native._json_bytes(request))
                else:
                    native.write(directory / fault, {})
                with self.assertRaises(ValueError):
                    self.load(directory, collection, current)

    def test_revision_one_call_parent_true_no_fit_and_no_overwrite(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, collection, current, prompt, note = self.prior_fixture(root)
            messages, provenance = self.load(directory, collection, current)
            output = root / 'recollect_revision'
            output.mkdir()
            engine = MagicMock()
            engine.generate.return_value = dict(messages=messages, raw='NONE', terminal=True, truncated=False)
            result = runner.recollect_revision(engine, messages, output, provenance)
            engine.generate.assert_called_once_with(messages, max_new_tokens=768)
            self.assertEqual((result['parent_present'], result['model_calls'], result['fits']), (True, 1, 0))
            self.assertEqual(result['training_admission'], 'UNREVIEWED_NO_FIT')
            self.assertEqual(result['revision_source'], provenance)
            self.assertEqual(result['claim'], 'PARENT_FEEDBACK_RESPONSIVENESS_ONLY_NOT_LEARNING_TRANSFER_OR_UTILITY')
            self.assertFalse((output / 'adapter').exists())
            with self.assertRaises(FileExistsError):
                runner.recollect_revision(engine, messages, output, provenance)
            engine.generate.assert_called_once()

    def test_truncated_revision_retained_but_rejected_without_retry(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, collection, current, prompt, note = self.prior_fixture(root)
            messages, provenance = self.load(directory, collection, current)
            output = root / 'recollect_revision'
            output.mkdir()
            engine = MagicMock()
            engine.generate.return_value = dict(messages=messages, raw='partial', terminal=False, truncated=True)
            with self.assertRaisesRegex(ValueError, 'terminal_untruncated_revision_required'):
                runner.recollect_revision(engine, messages, output, provenance)
            engine.generate.assert_called_once()
            self.assertEqual(native.read(output / 'SLEEP_NOTE.json')['raw'], 'partial')

    def test_old_recipe_defaults_unchanged_and_revision_not_a_fit_phase(self):
        collection = collection_fixture()
        original = recollection.build_messages(collection)
        rehearsal = recollection.build_messages(collection, recipe='rehearsal_allowed_v2')
        self.assertEqual(original, recollection.build_messages(collection, recipe='novelty_optional_v1'))
        self.assertEqual(len(original), 2)
        self.assertEqual(len(rehearsal), 2)
        self.assertEqual(rehearsal[0]['content'], recollection.REHEARSAL_SYSTEM)
        self.assertNotIn(recollection.PARENT_FEEDBACK, str(original) + str(rehearsal))
        arguments = ['--phase', 'train', '--sleep-recipe', 'parental_revision_v1', '--previous-recollection', 'previous',
                     '--development-arm', 'CUE_REPLAY']
        for name in ('model-dir', 'expected-base-sha256', 'initial-adapter-dir', 'expected-initial-adapter-sha256',
                     'collection', 'cue-collection', 'output', 'gpu-uuid'):
            arguments.extend(['--' + name, 'unused'])
        with self.assertRaisesRegex(ValueError, 'explicit_parental_revision_source_required'):
            runner.main(arguments)


class DiagnosticModel:
    def __init__(self, *, restore=True):
        self.training = False
        self.layer = SimpleNamespace(lora_A={}, lora_B={}, disable_adapters=False)
        self.state = 'e' * 64
        self.restore = restore
        self.context_entries = self.context_exits = 0

    def named_modules(self):
        return [('layer', self.layer)]

    def named_parameters(self):
        return [('layer.lora_A.default.weight', object())]

    @contextmanager
    def disable_adapter(self):
        self.context_entries += 1
        self.layer.disable_adapters = True
        try:
            yield
        finally:
            self.context_exits += 1
            if self.restore:
                self.layer.disable_adapters = False


class BaseDiagnosticTests(unittest.TestCase):
    def fixture(self, root):
        previous = RevisionTests()
        directory, collection, current, prompt, note = previous.prior_fixture(root)
        messages, provenance = previous.load(directory, collection, current)
        revision_directory = root / 'recollect_revision'
        revision_directory.mkdir()
        revision_note = dict(messages=deepcopy(messages), raw='Rejected revision NONE', terminal=True, truncated=False)
        native.write(revision_directory / 'SLEEP_NOTE.json', revision_note)
        native.write(revision_directory / 'SLEEP_PROMPT.json', messages)
        revision_result = dict(deepcopy(current), schema=runner.SCHEMA, phase='recollect_revision',
            status='RECOLLECTION_CAPTURED_NO_FIT', state='BEFORE', sleep_recipe='parental_revision_v1',
            parent_present=True, fits=0, model_calls=1, frozen_base_unchanged=True,
            training_admission='UNREVIEWED_NO_FIT', loaded_adapter_state_sha256='e' * 64,
            revision_source=provenance, note_sha256=native.file_hash(revision_directory / 'SLEEP_NOTE.json'),
            terminal=True, truncated=False)
        native.write(revision_directory / 'RESULT.json', revision_result)
        return directory, collection, current

    def load(self, directory, collection, current):
        return runner.load_base_diagnostic_sources(directory, collection, current,
                                                    expected_adapter_state_sha256='e' * 64)

    def engine(self, *, fail=False, truncated=False, restore=True, mutate=False):
        model = DiagnosticModel(restore=restore)

        def generate(messages, *, max_new_tokens):
            self.assertIs(model.layer.disable_adapters, True)
            self.assertEqual(max_new_tokens, 768)
            if fail:
                raise RuntimeError('synthetic generation failure')
            if mutate:
                model.state = 'changed'
            return dict(messages=deepcopy(messages), raw='base-only output', terminal=not truncated, truncated=truncated)

        return SimpleNamespace(model=model, generate=MagicMock(side_effect=generate))

    def test_fixed_two_prompts_calls_flags_restoration_and_archived_on_unchanged(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, collection, current = self.fixture(root)
            before = {str(path): path.read_bytes() for path in root.rglob('*.json')}
            prompts, provenance = self.load(directory, collection, current)
            self.assertEqual(prompts[0]['messages'], native.read(directory / 'SLEEP_PROMPT.json'))
            self.assertEqual(prompts[1]['messages'], native.read(root / 'recollect_revision/SLEEP_PROMPT.json'))
            self.assertEqual(prompts[1]['messages'][2]['content'], native.read(directory / 'SLEEP_NOTE.json')['raw'])
            engine = self.engine()
            output = root / 'recollect_base_diagnostic'
            output.mkdir()
            with patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=lambda parameters: engine.model.state):
                result = runner.recollect_base_diagnostic(engine, prompts, output, provenance)
            self.assertEqual(engine.generate.call_count, 2)
            self.assertEqual((engine.model.context_entries, engine.model.context_exits), (1, 1))
            self.assertFalse(engine.model.layer.disable_adapters)
            self.assertTrue(result['adapter_restored'])
            self.assertEqual((result['model_calls'], result['fits']), (2, 0))
            self.assertEqual(result['actor_mode'], 'INFERENCE_ADAPTER_OFF')
            self.assertFalse(result['own_experience_actor'])
            self.assertEqual(result['training_admission'], 'EXCLUDED_FROM_TRAINING')
            for item in prompts:
                record = result['diagnostic_panels'][item['name']]
                self.assertEqual(record['parent_present'], item['parent_present'])
                self.assertEqual(record['model_calls'], 1)
                self.assertFalse(record['own_experience_actor'])
                self.assertEqual(record['training_admission'], 'EXCLUDED_FROM_TRAINING')
                self.assertEqual(native.read(output / (item['name'] + '_PROMPT.json')), item['messages'])
                self.assertEqual(native.read(output / (item['name'] + '.json'))['raw'], 'base-only output')
            self.assertEqual(before, {path: Path(path).read_bytes() for path in before})
            self.assertFalse((output / 'adapter').exists())

    def test_failure_truncation_and_state_drift_restore_or_fail_closed(self):
        for options, error in ((dict(fail=True), 'synthetic generation failure'),
                               (dict(truncated=True), 'terminal_untruncated_base_diagnostic'),
                               (dict(restore=False), 'adapter_not_restored'),
                               (dict(mutate=True), 'adapter_not_restored')):
            with self.subTest(options=options), TemporaryDirectory() as temporary:
                root = Path(temporary)
                directory, collection, current = self.fixture(root)
                prompts, provenance = self.load(directory, collection, current)
                output = root / 'base'
                output.mkdir()
                engine = self.engine(**options)
                with patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=lambda parameters: engine.model.state):
                    with self.assertRaisesRegex((ValueError, RuntimeError), error):
                        runner.recollect_base_diagnostic(engine, prompts, output, provenance)
                self.assertEqual(engine.model.context_exits, 1)
                if options.get('restore', True):
                    self.assertFalse(engine.model.layer.disable_adapters)
                self.assertEqual(engine.generate.call_count, 1 if options.get('fail') else 2)
                if options.get('truncated'):
                    self.assertTrue(native.read(output / 'SLEEP_BASE_REHEARSAL.json')['truncated'])
                    self.assertTrue(native.read(output / 'SLEEP_BASE_REVISION.json')['truncated'])

    def test_both_archived_on_conditions_must_match_sources(self):
        faults = ('initial_training_result_sha256', 'adult_source', 'loaded_adapter_state_sha256',
                  'revision_source', 'note_sha256', 'terminal', 'parent_present')
        for key in faults:
            with self.subTest(key=key), TemporaryDirectory() as temporary:
                root = Path(temporary)
                directory, collection, current = self.fixture(root)
                path = root / 'recollect_revision/RESULT.json'
                result = native.read(path)
                result[key] = False if key in ('terminal', 'parent_present') else 'wrong'
                path.write_bytes(native.native._json_bytes(result))
                with self.assertRaises(ValueError):
                    self.load(directory, collection, current)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, collection, current = self.fixture(root)
            prompt = native.read(root / 'recollect_revision/SLEEP_PROMPT.json')
            prompt[-1]['content'] += ' altered'
            (root / 'recollect_revision/SLEEP_PROMPT.json').write_bytes(native.native._json_bytes(prompt))
            with self.assertRaisesRegex(ValueError, 'on_revision_prompt_mismatch'):
                self.load(directory, collection, current)
        with TemporaryDirectory() as temporary:
            directory, collection, current = self.fixture(Path(temporary))
            current['adult_source'] = {'wrong': 'collection'}
            with self.assertRaisesRegex(ValueError, 'previous_recollection_source_mismatch'):
                self.load(directory, collection, current)

    def test_cli_requires_previous_source_and_forbids_after_and_recipe_selection(self):
        common = ['--phase', 'recollect_base_diagnostic', '--development-arm', 'CUE_REPLAY']
        for name in ('model-dir', 'expected-base-sha256', 'initial-adapter-dir', 'expected-initial-adapter-sha256',
                     'collection', 'cue-collection', 'output', 'gpu-uuid'):
            common.extend(['--' + name, 'unused'])
        for extra in ([], ['--state', 'AFTER'], ['--previous-recollection', 'prior', '--sleep-recipe', 'parental_revision_v1'],
                      ['--previous-recollection', 'prior', '--sleep-recipe', 'rehearsal_allowed_v2']):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                runner.main(common + extra)


class GeneratedTokens:
    def __init__(self, tokens):
        self.tokens = tokens

    def __getitem__(self, indexes):
        batch, selection = indexes
        if batch != 0:
            raise AssertionError('single generation only')
        return SimpleNamespace(tolist=lambda: self.tokens[selection])


class GenerationTests(unittest.TestCase):
    def engine(self, tail):
        engine = native.Engine.__new__(native.Engine)
        engine.check = MagicMock()
        engine.torch = MagicMock()
        engine.torch.inference_mode.side_effect = lambda: nullcontext()
        engine.device = 'synthetic-cpu-no-model'
        engine.tokenizer = MagicMock(eos_token_id=99, pad_token_id=0)
        engine.tokenizer.apply_chat_template.return_value = [10, 11]
        engine.tokenizer.decode.return_value = 'captured text'
        engine.transformers = SimpleNamespace(GenerationConfig=lambda **kwargs: SimpleNamespace(**kwargs))
        engine.model = MagicMock()
        engine.model.generate.return_value = GeneratedTokens([10, 11] + tail)
        return engine

    def test_default160_matches_existing_generation_recipe_and_result(self):
        tail = [7] * 160
        engine = self.engine(tail)
        messages = [dict(role='user', content='public')]
        result = engine.generate(messages)
        self.assertEqual(result, dict(messages=messages, prompt_tokens=2, token_ids=tail,
                                     raw='captured text', terminal=False, truncated=True))
        config = engine.model.generate.call_args.kwargs['generation_config']
        self.assertEqual(vars(config), dict(do_sample=False, num_beams=1, use_cache=True, max_new_tokens=160,
            repetition_penalty=1.0, eos_token_id=99, pad_token_id=0))
        engine.model.generate.assert_called_once()

    def test_override_bound_controls_truncation_and_eot(self):
        for limit in (1, 160, 768):
            for terminal in (False, True):
                with self.subTest(limit=limit, terminal=terminal):
                    tail = [7] * limit
                    if terminal:
                        tail[-1] = 99
                    engine = self.engine(tail)
                    result = engine.generate([], max_new_tokens=limit)
                    self.assertEqual((result['terminal'], result['truncated']), (terminal, not terminal))
                    self.assertEqual(engine.model.generate.call_args.kwargs['generation_config'].max_new_tokens, limit)
                    self.assertEqual(engine.tokenizer.decode.call_args.args[0], tail[:-1] if terminal else tail)
        self.assertFalse(self.engine([7] * 160).generate([], max_new_tokens=768)['truncated'])

    def test_bad_bounds_rejected_before_generation(self):
        for limit in (0, -1, 769, True, 768.0, '768', None):
            with self.subTest(limit=limit):
                engine = self.engine([])
                with self.assertRaisesRegex(ValueError, 'bounded_generation_tokens_required'):
                    engine.generate([], max_new_tokens=limit)
                engine.model.generate.assert_not_called()
                engine.tokenizer.apply_chat_template.assert_not_called()

    def test_prompt_limit_remains2048_with_revision_output_budget(self):
        engine = self.engine([])
        engine.tokenizer.apply_chat_template.return_value = [7] * 2049
        with self.assertRaisesRegex(ValueError, 'context_bound_exceeded_no_truncation'):
            engine.generate([], max_new_tokens=768)
        engine.model.generate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
