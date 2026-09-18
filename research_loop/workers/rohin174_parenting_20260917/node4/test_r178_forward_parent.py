"""Synthetic R178 release, no-republish, and exact outbound route regressions."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest
import urllib.request


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('raw_forward', HOME / 'r178_forward_parent.py')
forward = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(forward)


class ForwardTests(unittest.TestCase):
    def receipt(self):
        return forward.base.read(forward.MAIN_RECEIPT)

    def state(self):
        return dict(caught_up=True, delivered={}, events=[])

    def test_existing_Main_receipt_releases_only_new_B_entrypoint(self):
        decision = forward.release(self.receipt())
        self.assertEqual((decision['physical'], decision['arm']), (1, 'B'))
        self.assertTrue(decision['no_baseline_republish'])
        with self.assertRaisesRegex(ValueError, forward.base.admission.REFUSAL):
            forward.base.admission.target(1, forward.base.ROOTS[1])

    def test_missing_preservation_or_wrong_publication_fails(self):
        changes = dict(status='PENDING', checkpoint_cycle=41, archive='/another/archive',
            root=forward.base.ROOTS[3], inbox_id='another', publication_sha256='0' * 64,
            baseline_text_unchanged=False, child_restart=True, child_signals=1,
            adapter_optimizer_rng_source_untouched=False, journal_records=2)
        for field, value in changes.items():
            with self.subTest(field=field):
                receipt = self.receipt()
                receipt[field] = value
                with self.assertRaisesRegex(ValueError, 'preservation_and_publication'):
                    forward.release(receipt)

    def test_no_provider_turn_before_baseline_render(self):
        self.assertEqual(forward.ready(self.state()), 'AWAITING_MAIN_ORIGINAL_BASELINE_RENDER')

    def test_baseline_render_needs_following_committed_child(self):
        state = self.state()
        state['delivered'][forward.TURN] = dict(inbox_sha256=forward.TURN_SHA, record_index=10)
        state['events'] = [dict(actor='child', record_index=11)]
        self.assertEqual(forward.ready(state), 'AWAITING_CHILD_COMMITTED_RESPONSE_AFTER_BASELINE')
        state['events'][0]['commit_record_index'] = 12
        self.assertEqual(forward.ready(state), 'READY_FOR_EXISTING_B_RESPONSE_CLOCK')

    def test_wrong_hash_cannot_count_as_Main_baseline(self):
        state = self.state()
        state['delivered'][forward.TURN] = dict(inbox_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'exact_Main_baseline_render'):
            forward.ready(state)

    def test_unknown_snapshot_never_dispatches(self):
        state = self.state()
        state['caught_up'] = False
        self.assertEqual(forward.ready(state), 'CATCHING_UP')

    def request(self, url=None, **changes):
        body = dict(model=forward.MODEL, tools=[], tool_choice='none', store=False)
        body.update(changes)
        return urllib.request.Request(url or forward.URL, data=json.dumps(body).encode())

    def test_exact_known_working_route(self):
        receipt = forward.check_request(self.request())
        self.assertEqual(receipt['url'], 'https://[REDACTED_HOST]/v1/responses')
        self.assertFalse(receipt['credential_recorded'])

    def test_missing_v1_or_wrong_model_tools_refused(self):
        requests = [self.request('https://[REDACTED_HOST]/responses'),
            self.request('https://[REDACTED_HOST]/v1/v1/responses'),
            self.request(model='gpt-6-astra'), self.request(tools=[{'type': 'shell'}]), self.request(store=True)]
        for request in requests:
            with self.subTest(url=request.full_url), self.assertRaisesRegex(ValueError, 'known_working_Astra_route'):
                forward.check_request(request)


if __name__ == '__main__':
    unittest.main()
