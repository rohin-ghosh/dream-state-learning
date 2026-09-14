"""CPU replay of real-format reader traces and independent pointer admission."""

from copy import deepcopy
from hashlib import sha256
import subprocess
import sys
import unittest
from unittest.mock import MagicMock

from organism_v6 import experienced_event_actual_reader_audit as audit
from organism_v6 import experienced_event_corrective_replay as corrective
from organism_v6 import experienced_event_read_route as controller
from tests.test_experienced_event_corrective_replay import fixture


def actual_fixture(no_reads=False, nonterminal=False):
    collection, unused, bindings = fixture()
    by_address = {episode['fact']['event']: episode['event']['raw'] for episode in collection['episodes']}
    records = []
    for episode_index, fact in enumerate(collection['bank']):
        commands = [] if no_reads else ['READ EVENT ' + address for address in fact['public_events']]
        port = fact['port'] if episode_index % 2 == 0 else next(port for port in fact['public_ports'] if port != fact['port'])
        commands = iter(commands + ['ROUTE ' + port])

        def actor(messages):
            return dict(raw=next(commands), terminal=True, truncated=False, messages=deepcopy(messages))

        def reader(address):
            raw = by_address[address] if address == fact['public_events'][0] else 'MISSING\nraw reader fragment'
            return dict(raw=raw, terminal=not nonterminal, truncated=nonterminal,
                        private_score='HIDDEN_READER_METADATA')

        transitions = {other['port']: other['outcome'] for other in collection['bank'] if other['node'] == fact['node']}
        episode = controller.run_episode(controller.public_task(fact), actor, reader, transitions.__getitem__)
        records.append(dict(event=fact['event'], episode=episode))
    return collection, records


def generation(raw, **kwargs):
    result = dict(raw=raw, terminal=True, truncated=False)
    result.update(kwargs)
    return result


class CaseTests(unittest.TestCase):
    def test_all_reads_successful_and_failing_routes_duplicates_retained(self):
        collection, records = actual_fixture()
        self.assertEqual(sum(record['episode']['reached_goal'] for record in records), 2)
        self.assertEqual(corrective.prepare_cases(collection, records)['expected_calls'], 2)
        original = deepcopy((collection, records))
        bundle = audit.build_cases(collection, records)
        self.assertEqual(bundle['expected_calls'], 8)
        self.assertEqual(bundle['task_denominator'], 4)
        self.assertEqual([case['episode_index'] for case in bundle['cases']], [0, 0, 1, 1, 2, 2, 3, 3])
        self.assertEqual([case['read_index'] for case in bundle['cases']], [0, 1] * 4)
        self.assertEqual(len({case['address'] for case in bundle['cases']}), 4)
        self.assertEqual(original, (collection, records))
        self.assertEqual(bundle, audit.build_cases(collection, records))

    def test_real_raw_and_status_preserved_not_donor_rebuilt_or_prompt_leaked(self):
        collection, records = actual_fixture()
        bundle = audit.build_cases(collection, records)
        for case in bundle['cases']:
            trace = records[case['episode_index']]['episode']['traces'][case['trace_index']]
            self.assertEqual(case['reader_raw'], trace['response']['raw'])
            self.assertEqual(case['reader_raw_sha256'], sha256(trace['response']['raw'].encode()).hexdigest())
            self.assertEqual(case['reader_terminal'], trace['response']['terminal'])
            self.assertEqual(case['reader_truncated'], trace['response']['truncated'])
            self.assertEqual(case['response_sha256'], audit.document_sha256(trace['response']))
            self.assertTrue(case['messages'][1]['content'].endswith('UNTRUSTED READER REPLY\n' + trace['response']['raw']))
            self.assertEqual(case['messages'][0]['content'], audit.lesson.SYSTEM)
            self.assertTrue(case['messages'][1]['content'].startswith(audit.lesson.HELD_SKINS[0]))
            for marker in ('private_score', 'HIDDEN_READER_METADATA', 'reached_goal', 'episode_index',
                           'trace_index', 'reader_terminal', 'expected', 'fault', 'PARENT', 'GOAL'):
                self.assertNotIn(marker, str(case['messages']))
            for fact in collection['bank']:
                self.assertNotIn(fact['world'], str(case['messages']))
        self.assertEqual([case['kind'] for case in bundle['cases']], ['true', 'fault'] * 4)

    def test_lesson_neutral_prefix_layout_is_identical_for_actual_true_reply(self):
        collection, records = actual_fixture()
        bundle = audit.build_cases(collection, records)
        events = [dict(event=episode['fact']['event'], raw=episode['event']['raw']) for episode in collection['episodes']]
        lesson_cases = audit.lesson.build_cases(events, 'HELD')['cases']
        for case in bundle['cases']:
            if case['kind'] == 'true':
                matching = next(prior for prior in lesson_cases if prior['event'] == case['address']
                                and prior['kind'] == 'true' and prior['skin_index'] == 0)
                self.assertEqual(case['messages'], matching['prefix'])

    def test_incomplete_or_drifted_routes_not_invented(self):
        collection, records = actual_fixture(nonterminal=True)
        with self.assertRaises(ValueError):
            audit.build_cases(collection, records)
        collection, records = actual_fixture()
        records[0]['episode']['traces'][1]['response']['raw'] = 'changed'
        with self.assertRaises(ValueError):
            audit.build_cases(collection, records)
        with self.assertRaises(ValueError):
            audit.build_cases(collection, records[:3])

    def test_zero_reads_still_retains_all_four_task_denominator(self):
        collection, records = actual_fixture(no_reads=True)
        bundle = audit.build_cases(collection, records)
        generate = MagicMock()
        result = audit.collect_cases(bundle, generate)
        generate.assert_not_called()
        self.assertEqual(result['task_denominator'], 4)
        self.assertEqual(result['summary'], {kind: dict(correct=0, denominator=0) for kind in ('overall', 'true', 'fault')})
        self.assertEqual(result['row_source_indexes'], [])


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.collection, self.records = actual_fixture()
        self.bundle = audit.build_cases(self.collection, self.records)

    def test_correct_classifier_NONE_or_requested_pointer_replays_exactly(self):
        answers = iter(case['expected'] + '\n' for case in self.bundle['cases'])
        generate = MagicMock(side_effect=lambda messages: generation(next(answers), messages=deepcopy(messages)))
        result = audit.collect_cases(self.bundle, generate)
        self.assertEqual(generate.call_count, 8)
        self.assertEqual(result['admitted_selections'], 4)
        self.assertEqual(result['chosen_source_indexes'][::2], [None] * 4)
        self.assertEqual(len(result['row_source_indexes']), 32)
        self.assertEqual(result['summary'], dict(overall=dict(correct=8, denominator=8),
            true=dict(correct=4, denominator=4), fault=dict(correct=4, denominator=4)))
        captured = iter(result['captures'])

        def replay(messages):
            call = next(captured)
            self.assertEqual(call['messages'], messages)
            return deepcopy(call['response'])

        self.assertEqual(result, audit.collect_cases(self.bundle, replay))
        self.assertEqual(result['fits'], 0)
        self.assertFalse(result['parent_present'])

    def test_wrong_but_sourced_choices_admitted_and_duplicates_mechanically_mapped(self):
        selected = []
        for case in self.bundle['cases']:
            entry = next(source for source in self.bundle['sources'] if source['event'] != case['address'])
            selected.append(entry)
        answers = iter(entry['event'] for entry in selected)
        result = audit.collect_cases(self.bundle, lambda messages: generation(next(answers)))
        self.assertEqual((result['correct'], result['admitted_selections']), (0, 8))
        self.assertEqual(result['chosen_source_indexes'], [entry['source_index'] for entry in selected])
        self.assertEqual(result['row_source_indexes'], [index for entry in selected for index in entry['row_source_indexes']])
        self.assertEqual(len(result['material_origins']), 64)
        for origin in result['material_origins']:
            self.assertEqual(origin['source_raw_sha256'], self.bundle['sources'][origin['source_index']]['source_raw_sha256'])
            self.assertEqual(origin['call_sha256'], result['captures'][origin['call_index']]['call_sha256'])

    def test_NONE_is_correct_only_for_true_and_never_material(self):
        result = audit.collect_cases(self.bundle, lambda messages: generation('NONE'))
        self.assertEqual(result['chosen_source_indexes'], [None] * 8)
        self.assertEqual(result['admitted_selections'], 0)
        self.assertEqual(result['correct'], 4)
        self.assertEqual(result['row_source_indexes'], [])

    def test_errors_and_invalid_pointer_contract_no_retries_or_substitutions(self):
        address = self.bundle['sources'][0]['event']
        variants = [None, address, {}, generation('ADDRESS ' + address), generation(address + '\n\n'),
                    generation(' ' + address), generation(address, terminal=False),
                    generation(address, truncated=True), generation(address, messages=[])]
        for response in variants:
            with self.subTest(response=response):
                generate = MagicMock(return_value=response)
                result = audit.collect_cases(self.bundle, generate)
                self.assertEqual(generate.call_count, 8)
                self.assertEqual(result['chosen_source_indexes'], [None] * 8)
                self.assertEqual(result['correct'], 0)
                self.assertTrue(all(capture['response'] == response for capture in result['captures']))
        generate = MagicMock(side_effect=RuntimeError('failed classifier'))
        result = audit.collect_cases(self.bundle, generate)
        self.assertEqual(generate.call_count, 8)
        self.assertTrue(all(capture['error'] == dict(type='RuntimeError', message='failed classifier')
                            for capture in result['captures']))

    def test_source_and_case_hashes_bound_before_any_calls(self):
        for field in ('cases_sha256', 'expected_calls', 'case', 'response'):
            bundle = deepcopy(self.bundle)
            if field == 'case':
                bundle['cases'][0]['reader_raw'] = 'substitution'
            elif field == 'response':
                bundle['route_records'][0]['episode']['traces'][1]['response']['raw'] = 'substitution'
            else:
                bundle[field] = 'wrong'
            generate = MagicMock()
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.collect_cases(bundle, generate)
            generate.assert_not_called()

    def test_import_does_not_load_native_libraries(self):
        script = '''
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'peft', 'transformers', 'tokenizers'}:
        raise AssertionError('native import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import organism_v6.experienced_event_actual_reader_audit
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
