"""R115 section9.5 tests exercise actual runtime paths without native inference."""

import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r115_native as native
from gpu import orch_r110_claude_broker as broker
from organism_v6 import orch_math_feedback_uptake_r115 as policy


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.task = dict(id='TRAIN_1', split='TRAIN', question='What is 31 times 21?', question_sha256='a'*64)

    def test_95_open_inspection_is_enacted_environment_response(self):
        experience = policy.Experience()
        response = dict(raw='CALCULATE: 31 * 21\nINSPECT')
        observations = native.environment(experience, self.task, response)
        self.assertEqual(observations[0]['status'], 'ENACTED')
        self.assertEqual(observations[0]['observation'], '651')
        self.assertEqual(observations[1]['observation'], self.task['question'])
        self.assertIn('651', experience.events[0]['text'])
        self.assertIn('651', policy.messages(experience, 'Continue')[-3]['content'])
        self.assertEqual(native.environment(experience, self.task, dict(raw='I could calculate something later.')), [])

    def test_arithmetic_is_bounded_not_code_execution(self):
        self.assertEqual(policy.calculate('(8 + 4) / 3'), '4')
        for expression in ('__import__("os").system("id")', '2 ** 1000', '1 / 0', 'x + 2'):
            with self.assertRaises((ValueError, ZeroDivisionError)):
                policy.calculate(expression)

    def test_95_dev_final_and_attached_opens_never_buffer_or_rows(self):
        experience = policy.Experience()
        for split in ('DEV', 'FINAL', 'PROBE'):
            task = dict(self.task, split=split)
            for purpose in ('held', 'open_turn'):
                messages = policy.readout_messages(task, purpose, dict(raw='FINAL: 651'))
                self.assertTrue(messages)
                with self.assertRaises(ValueError):
                    experience.append(policy.event('child', 'held taint', split, messages))
                with self.assertRaises(ValueError):
                    experience.payload(task, 'life', 1, 0, 'open_turn', 'b'*64)
        self.assertEqual(experience.events, [])
        self.assertNotIn('Experience(', Path(native.__file__).read_text().split('def readout(',1)[1].split('def dispatch_readout',1)[0])

    def reflection_fixture(self, cap):
        experience = policy.Experience()
        experience.append(policy.event('child', 'I want to reconsider the experience.', 'TRAIN', 'trace'))
        payload = experience.payload(self.task, 'F2_test', 1, 0, 'presleep_metacognition', 'b'*64)
        now = time.time()
        request = dict(id='C1_PRESLEEP', payload=payload, payload_sha256=broker.digest(payload), lane_deadline_unix=now+120)
        config = dict(life_id='F2_test', family='math', train_tasks={'TRAIN_1':'a'*64},
            excluded_task_ids=[], cohort_sha256='b'*64, branch='F2', principles_sha256=broker.PRINCIPLES_V2_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fields = dict(policy.previous.FIELDS, REFLECTION=dict(mode='short' if cap<8192 else 'long', max_new_tokens=cap))
            prompt = broker.render_parent_prompt(fields).encode()
            (root/'F2.md').write_bytes(prompt)
            broker.write(root/'F2.fields.json', dict(schema='ORCH_R114_HEAD_FIELDS_V1',
                prompt_sha256=hashlib.sha256(prompt).hexdigest(), fields=fields))
            principles = Path(__file__).resolve().parents[1]/policy.previous.original.AREA/'PRINCIPLES_V2.md'
            system, raw_prompt, binding = broker.build_system(payload, config, root, principles)
        binding_sha = hashlib.sha256((json.dumps(binding,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
        response = dict(id=request['id'], status='SILENT', request_sha256=broker.digest(request),
            payload_sha256=request['payload_sha256'], finished_unix=now, prompt_binding=binding,
            transcript_receipt=dict(node_only=True, all_verified=True, files={'PROMPT_BINDING.json':binding_sha}))
        return request, response, config, now

    def test_95_actual_reflection_cap_changes_through_broker_to_generate(self):
        observed = []
        for cap in (512, 1024, 8192):
            request, response, config, now = self.reflection_fixture(cap)
            engine = Mock()
            engine.generate.return_value = dict(raw='own reflection')
            result, settings = policy.reflection_generate(engine, [], response, request, config, now=now)
            engine.generate.assert_called_once_with([], max_new_tokens=cap)
            self.assertEqual(settings['status'], 'BOUND_FOR_LANE_DECODER')
            observed.append(settings['actual_decoder_cap'])
        self.assertEqual(observed, [512,1024,8192])

    def test_forged_or_late_reflection_binding_cannot_change_cap(self):
        request, response, config, now = self.reflection_fixture(512)
        engine = Mock()
        policy.reflection_generate(engine, [], dict(response, request_sha256='f'*64), request, config, now=now)
        engine.generate.assert_called_with([], max_new_tokens=8192)
        policy.reflection_generate(engine, [], response, request, config, now=now+121)
        engine.generate.assert_called_with([], max_new_tokens=8192)

    def test_visible_failed_check_is_preserved(self):
        experience = policy.Experience()
        experience.append(policy.event('child', 'FINAL: 684', 'TRAIN', 'attempt'))
        experience.append(policy.event('environment', 'Checker says INCORRECT', 'TRAIN', 'delivered checker'))
        payload = experience.payload(self.task, 'F2_test', 1, 0, 'open_turn', 'b'*64)
        config = dict(life_id='F2_test',family='math',train_tasks={'TRAIN_1':'a'*64},excluded_task_ids=[],cohort_sha256='b'*64)
        self.assertIn('INCORRECT', broker.public_transcript(payload, config)['events'][-1]['text'])

    def test_counters_include_all_attached_probes_and_no_retries(self):
        self.assertEqual(34+43*26+16, policy.NATIVE_CAP)
        with tempfile.TemporaryDirectory() as directory:
            lane = Path(directory)
            native.reserve(lane, 'native', policy.NATIVE_CAP, {})
            with self.assertRaises(ValueError):
                native.reserve(lane, 'native', 1, {})

    def test_guard_does_not_signal_reused_or_foreign_readout_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            lane = Path(directory)
            native.write(lane/'READOUT_cycle_001_PROCESS.json',dict(pid=123,uid=1000))
            with patch.object(native.scanner.pinned,'identity',return_value=dict(pid=123,uid=2000)), \
                    patch.object(native.os,'pidfd_open') as opened:
                native.stop_readouts(lane)
                opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
