import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import node_bridge as bridge
import recover


class RecoveryTests(unittest.TestCase):
    def test_exact_five_including_historically_unparented(self):
        self.assertEqual(len(bridge.CAPTIONS), 5)
        self.assertIn('r213_r226_caption_unparented_fork', bridge.CAPTIONS)
        self.assertFalse(any('math' in name for name in bridge.CAPTIONS))

    def test_math_and_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            bridge.job_directory('r233_classroom_handoff_v1/live/r213_math_a/turn_0001', 'r213_math_a')
        with self.assertRaises(ValueError):
            bridge.job_directory('../outside/turn_0001', bridge.CAPTIONS[0])

    def test_gap_acknowledgment_first_turn_only(self):
        self.assertIn(recover.GAP, recover.instruction(True))
        self.assertNotIn(recover.GAP, recover.instruction(False))
        self.assertIn('one concrete caption', recover.instruction(True))
        self.assertIn('never access or request sealed', recover.instruction(True))

    def test_pid_reuse_rejected_by_native_command(self):
        fake = SimpleNamespace(identity=lambda pid: dict(state='S', args=['unrelated'], cwd='/tmp'))
        helper = SimpleNamespace(alive=lambda binding: False)
        with self.assertRaises(ValueError):
            bridge.exact_bindings(fake, helper, {bridge.CAPTIONS[0]:
                dict(native_pid=123, control='/tmp/old', source='/tmp')})

    def test_changed_start_ticks_reject_rebind_before_any_mailbox_action(self):
        old = {bridge.CAPTIONS[0]: dict(process=dict(pid=123, start_ticks='old'))}
        current = {bridge.CAPTIONS[0]: dict(process=dict(pid=123, start_ticks='new'))}
        with patch.object(bridge, 'load_helpers', return_value=(None, None, None, {})), \
                patch.object(bridge, 'exact_bindings', return_value=current), \
                patch.object(bridge, 'publishers', return_value={}):
            with self.assertRaisesRegex(ValueError, 'incarnation_changed'):
                bridge.main(dict(mode='accept', bindings=old))

    def test_existing_identical_result_is_idempotent_not_republished(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            expected = dict(request_sha256='request', response=dict(message='One caption.'))
            (directory / 'PROVIDER_RESULT.json').write_text(json.dumps(expected))
            retirement = SimpleNamespace(sha=lambda path: 'unchanged')
            with patch.object(bridge, 'load_helpers', return_value=(retirement, None, None, {})), \
                    patch.object(bridge, 'exact_bindings', return_value={}), \
                    patch.object(bridge, 'publishers', return_value={}), \
                    patch.object(bridge, 'job_directory', return_value=directory):
                receipt = bridge.main(dict(mode='accept', life=bridge.CAPTIONS[0],
                    relative='turn', result=expected))
                self.assertTrue(receipt['accepted']['replay'])
                with self.assertRaisesRegex(ValueError, 'different_provider_result'):
                    bridge.main(dict(mode='accept', life=bridge.CAPTIONS[0],
                        relative='turn', result=dict(response='different')))

    def test_delivery_without_ACT_is_not_uptake(self):
        helper = SimpleNamespace(records=lambda *args: [])
        self.assertIsNone(bridge.act_chain(None, helper, bridge.CAPTIONS[0],
            dict(text='One caption.'), dict(REQUEST=dict(index=10))))

    def test_missing_result_is_not_reported_as_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(bridge, 'job_directory', return_value=directory):
                result = bridge.receipt(None, None, None, bridge.CAPTIONS[0], 'turn', {})
                self.assertEqual(result['state'], 'PROVIDER_PENDING_NOT_PUBLISHED')
                (directory / 'PROVIDER_RESULT.json').write_text('{}')
                result = bridge.receipt(None, None, None, bridge.CAPTIONS[0], 'turn', {})
                self.assertEqual(result['state'], 'PROVIDER_ACCEPTED_PUBLISHER_PENDING')

    def test_ACT_chain_requires_exact_response_origin_and_masked_parent(self):
        request = dict(messages=[dict(role='user', content='Astra: One caption.')],
            render_receipt=dict(all_history_tokens_masked=True))
        response = dict(request_sha256=bridge.digest(request))
        act = dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=11, record_sha256='response'))
        values = [dict(index=10, sha256='request', document=request),
            dict(index=11, sha256='response', document=response),
            dict(index=12, sha256='act', document=act)]
        helper = SimpleNamespace(records=lambda *args: [(0, 'REQUEST'), (1, 'RESPONSE'), (2, 'R184_ACT')])
        retirement = SimpleNamespace(record=lambda path: values[path])
        proof = bridge.act_chain(retirement, helper, bridge.CAPTIONS[0],
            dict(text='One caption.'), dict(REQUEST=dict(index=10)))
        self.assertEqual(proof['ACT']['index'], 12)
        act['origin']['record_sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            bridge.act_chain(retirement, helper, bridge.CAPTIONS[0],
                dict(text='One caption.'), dict(REQUEST=dict(index=10)))
        request['render_receipt']['all_history_tokens_masked'] = False
        with self.assertRaises(ValueError):
            bridge.act_chain(retirement, helper, bridge.CAPTIONS[0],
                dict(text='One caption.'), dict(REQUEST=dict(index=10)))

    def test_unknown_provider_attempt_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'private/requests/test-request'
            directory.mkdir(parents=True)
            (directory / 'DISPATCH.json').write_text('{}')
            with patch.object(recover, 'HERE', Path(temporary)):
                result = recover.generate(dict(request=dict(life=bridge.CAPTIONS[0]),
                    request_sha256='test-request'), {}, True)
            self.assertEqual(result['status'], 'UNCERTAIN_OR_FAILED_PROVIDER_ATTEMPT_NO_RETRY')

    def test_confirmed_429_preserved_and_retried_after_backoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'DISPATCH.json').write_text('{}')
            (directory / 'http_error_response.txt').write_text(json.dumps(dict(error=dict(code='429'))))
            failure = directory / 'FAILED.json'
            failure.write_text(json.dumps(dict(error_type='HTTPError')))
            self.assertEqual(recover.attempt_directory(directory, failure.stat().st_mtime)[1],
                'CONFIRMED_429_BACKOFF')
            following, blocked = recover.attempt_directory(directory, failure.stat().st_mtime + 20)
            self.assertIsNone(blocked)
            self.assertEqual(following.name, 'retry_0001')
            self.assertTrue(failure.exists())

    def test_non_429_and_unknown_dispatch_never_retried(self):
        for code in ('500', '401', 'ambiguous'):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                (directory / 'DISPATCH.json').write_text('{}')
                (directory / 'http_error_response.txt').write_text(json.dumps(dict(error=dict(code=code))))
                failure = directory / 'FAILED.json'
                failure.write_text(json.dumps(dict(error_type='HTTPError')))
                self.assertEqual(recover.attempt_directory(directory, failure.stat().st_mtime + 120)[1],
                    'UNCERTAIN_OR_FAILED_PROVIDER_ATTEMPT_NO_RETRY')


if __name__ == '__main__':
    unittest.main()
