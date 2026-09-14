"""CPU-only public-transcript and bounded native callback regression tests."""

from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from gpu import astra_experienced_event_microloop as native
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


if __name__ == '__main__':
    unittest.main()
