"""Synthetic P3 identity, uncertainty, accounting and read-only projections."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

import p3_audit
import p3_collect
import p3_read
from source_adapter import PREVIOUS
from test_decision_audit import FIXTURE, cycle


def receipt(response, accepted=1, pixels=1, scene='one'):
    return dict(origin=dict(record_index=response['record_index'], record_sha256=response['record_sha256']),
                receipt_sha256=hashlib.sha256(str(response['record_index']).encode()).hexdigest(),
                session_sha256='b' * 64, raw_act_sha256=hashlib.sha256(
                    response['document']['response']['raw'].encode()).hexdigest(),
                saved_unix=2000, feedback_present=True,
                counts=dict(parsed=1, scored=1, accepted=accepted, new_pixels=pixels,
                            judge_rejected=1-accepted, cached=0),
                selections=[dict(kind='scene', identifier_sha256=hashlib.sha256(scene.encode()).hexdigest())])


class P3Tests(unittest.TestCase):
    def fixture(self, think='I will continue.', act='An actual caption.'):
        journal = FIXTURE.Journal()
        response = cycle(journal, 1, think, act)
        return journal, response

    def test_exact_origin_and_ACT_bytes_bind_counts_not_consumption(self):
        journal, response = self.fixture()
        report = p3_audit.project(journal.evidence(), [receipt(response)])
        self.assertEqual(report['label'], 'P3')
        game = report['cycles'][0]['game']
        self.assertEqual(game['counts']['accepted'], 1)
        self.assertEqual(game['counts']['new_pixels'], 1)
        self.assertEqual(game['outcomes'][0]['feedback_delivered_or_consumed'], 'NOT_MEASURED')

    def test_record_hash_mismatch_is_unknown_not_zero(self):
        journal, response = self.fixture()
        source = receipt(response)
        source['origin']['record_sha256'] = 'c' * 64
        game = p3_audit.project(journal.evidence(), [source])['cycles'][0]['game']
        self.assertIsNone(game['counts'])
        self.assertEqual(game['unknown_ACTs'], 1)

    def test_matching_origin_wrong_ACT_text_is_unknown(self):
        journal, response = self.fixture()
        source = receipt(response)
        source['raw_act_sha256'] = 'c' * 64
        game = p3_audit.project(journal.evidence(), [source])['cycles'][0]['game']
        self.assertEqual(game['outcomes'][0]['status'], 'UNKNOWN_ACT_BYTES_MISMATCH')

    def test_duplicate_migrated_receipts_are_not_summed(self):
        journal, response = self.fixture()
        first = receipt(response)
        second = copy.deepcopy(first)
        second['session_sha256'] = 'd' * 64
        report = p3_audit.project(journal.evidence(), [first, second])
        self.assertIsNone(report['cycles'][0]['game']['counts'])
        self.assertEqual(report['game_coverage']['totals_known_only']['accepted'], 0)

    def test_accepted_repeat_is_not_new_pixel(self):
        journal, response = self.fixture()
        report = p3_audit.project(journal.evidence(), [receipt(response, pixels=0)])
        self.assertEqual(report['cycles'][0]['game']['counts']['accepted'], 1)
        self.assertEqual(report['cycles'][0]['game']['counts']['new_pixels'], 0)

    def test_missing_feedback_is_not_a_zero_result(self):
        journal, response = self.fixture()
        source = receipt(response)
        source['feedback_present'] = False
        self.assertIsNone(p3_audit.project(journal.evidence(), [source])['cycles'][0]['game']['counts'])

    def test_invalid_accounting_is_unknown(self):
        journal, response = self.fixture()
        source = receipt(response)
        source['counts']['new_pixels'] = 2
        self.assertIsNone(p3_audit.project(journal.evidence(), [source])['cycles'][0]['game']['counts'])

    def test_actual_selection_change_is_inferred_not_self_declaration(self):
        journal, first = self.fixture(think='What next?', act='First caption.')
        second = cycle(journal, 2, 'Could this work?', 'Second caption.')
        report = p3_audit.project(journal.evidence(), [receipt(first), receipt(second, scene='two')])
        current = report['cycles'][1]
        self.assertEqual(current['self_declared_decision'], 'UNKNOWN')
        self.assertEqual(current['game']['scene_direction_transition']['inferred_decision'], 'BRANCH')
        self.assertFalse(report['questions_are_failures'])

    def test_stops_changes_requires_declared_stop_and_actual_selection(self):
        journal, first = self.fixture(think='I will stop.')
        second = cycle(journal, 2, 'Another observation.', 'Second caption.')
        report = p3_audit.project(journal.evidence(), [receipt(first), receipt(second, scene='two')])
        self.assertEqual(report['cycles'][1]['game']['behavior_observations'][0]['label'], 'STOPS_CHANGES')

    def test_successive_pixels_qualified_not_semantic_discovery(self):
        journal, first = self.fixture()
        second = cycle(journal, 2, 'Another observation.', 'Second caption.')
        report = p3_audit.project(journal.evidence(), [receipt(first), receipt(second)])
        observed = report['cycles'][1]['game']['behavior_observations'][0]
        self.assertEqual(observed['label'], 'KEEPS_DISCOVERING')
        self.assertIn('NOT_SEMANTIC_NOVELTY', observed['basis'])

    def test_partial_response_cannot_acquire_score(self):
        journal = FIXTURE.Journal()
        journal.stage('THINK', 0, 'Which scene?')
        response = journal.stage('ACT', 1, 'Uncommitted.', committed=False)
        journal.sleep(1)
        report = p3_audit.project(journal.evidence(), [receipt(response)])
        self.assertEqual(report['game_coverage']['bound_ACTs'], 0)
        self.assertIsNone(report['cycles'][0]['game']['counts'])

    def test_public_report_never_contains_caption(self):
        journal, response = self.fixture(act='PRIVATE_CHILD_CAPTION_NOT_FOR_PUBLIC')
        report = p3_audit.project(journal.evidence(), [receipt(response)])
        self.assertNotIn('PRIVATE_CHILD_CAPTION_NOT_FOR_PUBLIC', json.dumps(report))

    def test_invalid_observer_bounds_before_IO(self):
        with self.assertRaisesRegex(ValueError, 'bounded_P3_observer_required'):
            p3_collect.run(interval=0)

    def test_observer_writes_local_receipt_then_expires_without_signals(self):
        journal, response = self.fixture()
        clock = [1000.0]
        document = dict(journal=journal.evidence(), receipts=[receipt(response)])
        def source(after, start_cycle):
            self.assertIsNone(after)
            clock[0] += 1
            return document, dict(input_file_sha256='a' * 64)
        with tempfile.TemporaryDirectory() as directory:
            own = Path(directory)
            for filename in ('p3_collect.py', 'p3_read.py', 'p3_audit.py', 'decision_audit.py', 'source_adapter.py'):
                (own / filename).write_text('synthetic')
            with mock.patch.object(p3_collect, 'OWN', own), \
                    mock.patch.object(p3_collect, 'collect', side_effect=source), \
                    mock.patch.object(p3_collect, 'identity', return_value=dict(pid=123, start_ticks=456, uid=1)), \
                    mock.patch.object(p3_collect.time, 'time', side_effect=lambda: clock[0]), \
                    mock.patch.object(p3_collect.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0]+seconds)):
                p3_collect.run(interval=30, maximum_seconds=30)
            process = json.loads((own / 'operator/P3_PROCESS.json').read_bytes())
            self.assertEqual(process['status'], 'EXPIRED_NORMALLY')
            self.assertEqual(process['successful_projections'], 1)
            self.assertEqual(process['learner_signals'], 0)
            self.assertEqual(process['inbox_writes'], 0)
            self.assertEqual(process['GPU_calls'], 0)
            self.assertEqual(process['parent_messages'], 0)
            self.assertNotIn('An actual caption', (own / 'operator/P3_LATEST.json').read_text())

    def test_existing_accounting_excludes_cached_without_losing_accept_repeat(self):
        modules = []
        for name, path in [('reader', PREVIOUS / 'journal_reader.py'), ('counts', p3_collect.ACCOUNTING)]:
            specification = importlib.util.spec_from_file_location('p3_test_' + name, path)
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            modules.append(module)
        document = dict(unix=2000, origin=dict(record_index=1, record_sha256='a' * 64),
                        raw_act='PRIVATE_CAPTION', action=dict(contest_id='PRIVATE_SCENE'),
                        report=dict(requested_count=3, feedback=[
                            dict(result=dict(ok=True, accepted=True, status='new_pixel')),
                            dict(result=dict(ok=True, accepted=True, status='repeat')),
                            dict(result=dict(ok=True, accepted=True, status='new_pixel', replayed=True))]))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'attempts/example/RESULT.json'
            destination.parent.mkdir(parents=True)
            destination.write_text(json.dumps(document))
            bindings = dict(Path=Path, json=json, hashlib=hashlib, time=time,
                            read_bytes=modules[0].read_bytes, native_outcome_row=modules[1].native_outcome_row)
            with mock.patch.dict(p3_read.__dict__, bindings):
                result = p3_read.scorer_receipts([directory])
        self.assertEqual(result[0]['counts']['scored'], 2)
        self.assertEqual(result[0]['counts']['accepted'], 2)
        self.assertEqual(result[0]['counts']['new_pixels'], 1)
        self.assertEqual(result[0]['counts']['cached'], 1)
        self.assertNotIn('PRIVATE_CAPTION', json.dumps(result))
        self.assertNotIn('PRIVATE_SCENE', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
