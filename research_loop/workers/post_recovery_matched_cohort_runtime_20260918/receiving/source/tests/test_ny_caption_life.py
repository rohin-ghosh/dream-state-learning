import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import pytest
from unittest.mock import patch

from gpu.ny_caption_life import POLICY, activate, child_act, observed_counts, parse_batch
from gpu.ny_caption_life_service import LifeSession
from gpu.orch_r125_stream_journal import _digest


class CaptionLifeTests(unittest.TestCase):
    def test_protocol_numbers_normalized_but_caption_is_verbatim(self):
        action = parse_batch('Scene: １\nDirection: contrast\nCount: １\nCaption: Literal ９８，中文', ['opaque'])
        self.assertEqual(action['contest_id'], 'opaque')
        self.assertEqual(action['captions'], ['Literal ９８，中文'])

    def test_invalid_count_or_duplicate_is_not_repaired(self):
        for raw in ('Scene: 1\nDirection: test\nCount: 2\nCaption: one',
                    'Scene: 1\nScene: 2\nDirection: test\nCount: 1\nCaption: one',
                    'Scene: 9\nDirection: test\nCount: 1\nCaption: one',
                    'Scene: 1\nCount: 1\nCaption: one'):
            with self.assertRaises(ValueError):
                parse_batch(raw, ['opaque'])

    def test_scene_handle_cannot_be_child_path(self):
        with self.assertRaises(ValueError):
            parse_batch('Scene: ../../private\nDirection: test\nCount: 1\nCaption: one', ['opaque'])

    def test_only_new_pixels_count_as_success(self):
        report = dict(requested_count=4, feedback=[
            dict(result=dict(ok=True, accepted=True, status='new_pixel')),
            dict(result=dict(ok=True, accepted=True, status='repeat')),
            dict(result=dict(ok=True, accepted=False, status='rejected')),
            dict(result=dict(ok=True, accepted=True, status='new_pixel', replayed=True))])
        result = observed_counts(report)
        self.assertEqual((result['successes'], result['quality_accepted'], result['cached']), (1, 2, 1))

    def test_source_bound_committed_act_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            records = Path(temporary) / 'stream' / 'records'
            records.mkdir(parents=True)
            response = dict(response=dict(raw='Scene: 1'), finished_unix=1)
            previous = 'genesis'
            chain = []
            for index, (kind, document) in enumerate((
                ('RESPONSE', response), ('COMMITTED', dict(source_sha256=_digest(response))),
                ('R184_STAGE', dict(stage='ACT', source_sha256=_digest(response))))):
                record = dict(index=index, kind=kind, document=document, journal_id='synthetic', previous_sha256=previous)
                record['sha256'] = _digest(record)
                (records / f'{index:020d}.json').write_text(json.dumps(record))
                previous = record['sha256']
                chain.append(record)
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=0, record_sha256=chain[0]['sha256'])
            self.assertEqual(child_act(temporary, origin), 'Scene: 1')
            chain[2]['document']['stage'] = 'THINK'
            chain[2]['sha256'] = _digest({key: value for key, value in chain[2].items() if key != 'sha256'})
            (records / '00000000000000000002.json').write_text(json.dumps(chain[2]))
            with self.assertRaises(ValueError):
                child_act(temporary, origin)

    def test_service_keeps_literal_attempt_and_real_feedback(self):
        class Game:
            def __init__(self):
                self.received = []

            def snapshot(self):
                return dict(received=list(self.received))

            def submit_caption(self, contest, caption):
                self.received.append((contest, caption))
                return dict(ok=True, accepted=False, status='rejected', q=None,
                            raw_score=-6.0, rank=55, reference_count=64, top_k=8)

        with tempfile.TemporaryDirectory() as temporary:
            game = Game()
            session = LifeSession(game, temporary, temporary, ['opaque'])
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256='a' * 64)
            message = dict(origin=origin, metrics=dict(THINK=20, ACT=30, LEARN=0))
            raw = 'Scene: 1\nDirection: test\nCount: 1\nCaption: Literal caption'
            with patch('gpu.ny_caption_life_service.child_act', return_value=raw):
                result = session.process(message)
                with self.assertRaises(ValueError):
                    session.process(message)
            self.assertEqual(game.received, [('opaque', 'Literal caption')])
            self.assertEqual(result['report']['feedback'][0]['result']['rank'], 55)
            self.assertFalse(result['report']['feedback'][0]['result']['accepted'])
            saved = json.loads((Path(temporary) / 'attempts' / ('a' * 64) / 'RESULT.json').read_text())
            self.assertEqual(saved['raw_act'], raw)
            self.assertFalse(saved['child_training_target'])

    def test_invalid_batch_gets_feedback_without_execution(self):
        game = SimpleNamespace(snapshot=lambda: {}, submit_caption=lambda *args: self.fail('not dispatched'))
        with tempfile.TemporaryDirectory() as temporary:
            session = LifeSession(game, temporary, temporary, ['opaque'])
            message = dict(origin=dict(record_sha256='b' * 64), metrics=dict(THINK=1, ACT=1, LEARN=0))
            with patch('gpu.ny_caption_life_service.child_act', return_value='I claim acceptance'):
                result = session.process(message)
            self.assertFalse(result['report']['ok'])
            self.assertEqual(result['report']['feedback'], [])

    def test_runtime_receives_feedback_before_return_and_never_executes_code(self):
        from gpu import orch_r184_think_act_learn as stages
        for fail in (False, True):
            events, records = [], []
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256='c' * 64)
            driver = SimpleNamespace(config=dict(trial_id='synthetic'),
                stream=SimpleNamespace(rows=[dict(target='Caption: raw')], history=SimpleNamespace(append=events.append)),
                generate_stage=lambda stage: dict(source_sha256='source', segment=1),
                last_response=origin, cycle_metrics=dict(THINK=1, ACT=1, LEARN=0),
                journal=SimpleNamespace(record=lambda kind, document: records.append((kind, document))),
                allocation=None, dataset=None, record_corrections=lambda outcome, raw: None,
                executor=lambda *args: self.fail('CPU execution is disabled'))
            returned = dict(policy=POLICY, origin=origin, report=dict(ok=True, feedback=[]))
            with patch.object(stages.ThinkActLearn, 'act', stages.ThinkActLearn.act):
                activate('/tmp/synthetic-caption.sock')
                with patch('gpu.ny_caption_life.request', side_effect=TimeoutError() if fail else None,
                           return_value=returned) as transport:
                    result = stages.ThinkActLearn.act(driver)
            self.assertEqual(transport.call_count, 1)
            self.assertEqual(events[-1].actor, 'environment')
            self.assertEqual(driver.cycle_phase, 'FEEDBACK_COMPLETE_OR_EXPLICIT_UNKNOWN')
            self.assertEqual(records[0][0], 'R184_ACT')
            self.assertEqual(result['status'], 'ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY' if fail else 'PUBLISHED')


if __name__ == '__main__':
    unittest.main()
def test_r212_explicit_humour_and_parameterised_rank_bar():
    from gpu.ny_caption_life import HELP
    from gpu.ny_caption_life_service import DEFAULT_TOP_K, scoring_rule

    assert DEFAULT_TOP_K == 50
    assert 'humour contest' in HELP and '64 human captions' in HELP
    assert 'rank <= 50 of 65' in scoring_rule(DEFAULT_TOP_K)
    assert 'rank <= 8 of 65' in scoring_rule(8)
    for invalid in (0, 66, True, 50.0):
        with pytest.raises(ValueError, match='rank_bar_between_one_and_65'):
            scoring_rule(invalid)
