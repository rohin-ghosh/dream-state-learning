import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_pipeline_l2_native as native
from gpu import orch_math_pipeline_l2_parent as parent
from gpu import orch_math_pipeline_l2_run as runner
from gpu.orch_l2_rich_math_bootstrap import read, sha, write
from organism_v6 import orch_math_pipeline_l2 as policy


def episodes():
    return [dict(task=task, trace='Incorrect past calculation. FINAL: -999',
        outcome=dict(status='INCORRECT', correct=False)) for task in policy.cohort()['train'][0]]


def call(episode, purpose='experience', raw=None):
    text = episode['trace'] if raw is None else raw
    return dict(task_id=episode['task']['id'], purpose=purpose, response=dict(raw=text),
        target_sha256=policy.text_sha(text), relative_path='call.json')


class Tokenizer:
    eos_token = '<|im_end|>'
    eos_token_id = 1
    all_special_ids = [1]

    def encode(self, text, add_special_tokens=False, truncation=False):
        chunks = text.split(self.eos_token)
        tokens = []
        for index, chunk in enumerate(chunks):
            if index:
                tokens.append(1)
            tokens.extend(ord(char) + 10 for char in chunk)
        return tokens

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, return_dict=False):
        text = ''.join(message['role'] + ':' + message['content'] + self.eos_token + '\n' for message in messages)
        if add_generation_prompt:
            text += 'assistant:'
        return self.encode(text) if tokenize else text


class PipelineTest(unittest.TestCase):
    def test_retention_seams_resolve_at_cpu_import(self):
        self.assertTrue(callable(native.recall_retention))
        self.assertTrue(callable(native.collect_retention_audit))

    def test_cohort_is_frozen_unique_disjoint(self):
        document = policy.cohort()
        self.assertEqual(document, policy.cohort())
        tasks = [task for group in document['train'] + document['held'] for task in group]
        self.assertEqual(len(tasks), 56)
        self.assertEqual(len({task['question_sha256'] for task in tasks}), 56)
        for field, argument in [('id', 'excluded_ids'), ('question_sha256', 'excluded_questions')]:
            with self.assertRaises(AssertionError):
                policy.cohort(**{argument: [tasks[0][field]]})

    def test_exact_oracle_separate_truncation(self):
        task = policy.cohort()['train'][0][0]
        response = dict(raw='FINAL: ' + task['gold'], terminal=False, truncated=True)
        result = policy.judge(task, response)
        self.assertTrue(result['correct'])
        self.assertTrue(result['truncated'])
        self.assertFalse(policy.judge(task, dict(response, raw='No answer'))['correct'])

    def test_failed_trace_preserved_nonendorsed(self):
        episode = episodes()[0]
        row = policy.recorded_row(episode, 'past_attempt', episode['trace'], call(episode), 'a' * 64)
        self.assertEqual(row['outcome'], 'INCORRECT')
        self.assertFalse(row['observed_fact_endorsement'])
        self.assertIn('NOT as an endorsed solution', row['student_prefix'][0]['content'])
        self.assertEqual(row['target'], episode['trace'])

    def test_exact_child_source_required(self):
        episode = episodes()[0]
        with self.assertRaises(AssertionError):
            policy.recorded_row(episode, 'past_attempt', 'invented', call(episode), 'a' * 64)

    def test_teacher_private_and_not_compiled(self):
        episode = episodes()[0]
        teacher = 'Distinct private teacher lesson: inspect your assumptions.'
        actual, public = policy.reflection_messages(episode, teacher)
        self.assertIn(teacher, actual[0]['content'])
        self.assertNotIn(teacher, json.dumps(public))
        response = call(episode, 'reflection', 'I should check the equation before trusting my result.')
        row = policy.recorded_row(episode, 'past_reflection', response['response']['raw'], response, 'b' * 64, teacher)
        self.assertNotIn(teacher, json.dumps(row))
        with self.assertRaises(AssertionError):
            response = call(episode, 'reflection', teacher)
            policy.recorded_row(episode, 'past_reflection', teacher, response, 'b' * 64, teacher)

    def test_parent_visibility_closed_schema(self):
        payload = policy.parent_payload(episodes(), 1)
        for key in ('held', 'retention_score', 'gold'):
            changed = copy.deepcopy(payload)
            changed[key] = 'secret'
            with self.assertRaises(AssertionError):
                policy.validate_parent_payload(changed)
        payload['episodes'][0]['task_id'] = 'secret_HELD_task'
        with self.assertRaises(AssertionError):
            policy.validate_parent_payload(payload)

    def test_parent_cannot_omit_failed_episode(self):
        source = episodes()
        ids = [episode['task']['id'] for episode in source]
        plan = dict(order=ids, guidance='Replay all.', rationale='All experience.', episode_guidance={value: 'Check.' for value in ids})
        policy.validate_parent_plan(plan, source)
        plan['order'] = ids[:-1]
        with self.assertRaises(AssertionError):
            policy.validate_parent_plan(plan, source)

    def test_every_episode_reflection_required_even_no_response(self):
        source = episodes()
        source[0]['trace'] = ''
        rows = []
        for episode in source:
            if episode['trace']:
                rows.append(policy.recorded_row(episode, 'past_attempt', episode['trace'], call(episode), 'a' * 64))
            response = call(episode, 'reflection', 'I will check the actual computation.')
            rows.append(policy.recorded_row(episode, 'past_reflection', response['response']['raw'], response, 'b' * 64))
        self.assertEqual(policy.validate_coverage(source, rows)['failures'], 8)
        self.assertEqual({row['dose_rule'] for row in rows}, {'paired_original_reflection_wallclock_window'})
        with self.assertRaises(AssertionError):
            policy.validate_coverage(source, rows[:-1])

    def test_full_masks_and_no_teacher_targets(self):
        episode = episodes()[0]
        row = policy.recorded_row(episode, 'past_attempt', episode['trace'], call(episode), 'a' * 64)
        encoded = native.encode_row(row, Tokenizer())
        self.assertEqual(tuple(value for value in encoded.labels if value != -100), encoded.target_ids)
        self.assertTrue(all(value == -100 for value in encoded.labels[:20]))
        self.assertEqual(encoded.labels[-1], -100)
        row['target'] = 'a' * policy.CONTEXT
        with self.assertRaises(AssertionError):
            native.encode_row(row, Tokenizer())

    def test_long_budget_and_full_history(self):
        self.assertEqual(native.generation_budget(100, 8192), 8192)
        self.assertEqual(native.generation_budget(10000, 8192), 6384)
        with self.assertRaises(AssertionError):
            native.generation_budget(16384, 8192)

    def test_source_path_tamper_and_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            episode = episodes()[0]
            response = call(episode)
            write(root / 'call.json', response)
            row = policy.recorded_row(episode, 'past_attempt', episode['trace'], response, sha(root / 'call.json'))
            native.source_row(root, row)
            for path in ('../call.json', '/tmp/call.json'):
                with self.assertRaises(AssertionError):
                    native.source_row(root, dict(row, source_call_path=path))
            write(root / 'call.json', dict(response, task_id='different'))
            with self.assertRaises(AssertionError):
                native.source_row(root, row)

    def test_single_lifetime_no_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root / 'READY.json', {})
            first = runner.new_lifetime(root)
            self.assertEqual(first['max_calls'], 1632)
            with self.assertRaises(FileExistsError):
                runner.new_lifetime(root)
            self.assertEqual(first, read(root / 'LIFETIME.json'))

    def test_parent_tools_disabled(self):
        command = parent.command(Path('/tmp/public_fixture'), dict(model='verified_fixture', mcp_servers={'fixture': {}}))
        self.assertIn('mcp_servers.fixture.enabled=false', command)
        self.assertIn('shell_tool', command)
        self.assertIn('web_search="disabled"', command)

    def test_handoff_has_no_quality_gate(self):
        with self.assertRaises(AssertionError):
            runner.check_handoff(dict(schema='bad', quality_score=1), policy.cohort())

    def test_no_reset_predecessor_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, marker in [('INITIAL.json', 'initial'),
                ('GUIDED_SLEEP/cycle1/experience/COMPLETE.json', 'cycle1'),
                ('GUIDED_SLEEP/cycle2/experience/COMPLETE.json', 'cycle2')]:
                write(root / name, dict(output_adapter=marker))
            with patch.object(native.bridge.AdapterIdentity, 'from_document', side_effect=lambda document: document):
                self.assertEqual(native.input_state(root, 'GUIDED_SLEEP', 0, 'readout')[0], 'initial')
                self.assertEqual(native.input_state(root, 'GUIDED_SLEEP', 2, 'experience')[0], 'cycle1')
                self.assertEqual(native.input_state(root, 'GUIDED_SLEEP', 2, 'readout')[0], 'cycle2')

    def test_current_allocation_and_minor_binding(self):
        from gpu import orch_math_pipeline_l2_scan as scanner
        scanner.bind()
        self.assertEqual(set(scanner.minor.pinned.policy.DEVICES), {4, 5, 7})
        with self.assertRaises(ValueError):
            scanner.minor.pinned.policy.allocation(2)
        self.assertEqual(scanner.minor.minor_from_documents(['GPU UUID: GPU-test\nDevice Minor: 3'], 'GPU-test'), 3)

    def test_handoff_complete_counts_and_source_disjoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            write(root / 'manifest.json', dict(source='source_only'))
            receipt = dict(status='COMPLETE', output_adapter=dict(state_sha256='a' * 64), process=['boot', 100, 10],
                updates=8, layout=dict(new_supervised_presentations=32, new_target_presentations=32))
            write(root / 'complete.json', receipt)
            document = dict(schema='ORCH_MATH_PIPELINE_L1_FULL_HANDOFF_V1',
                complete_receipt=dict(path=str(root / 'complete.json'), sha256=sha(root / 'complete.json')),
                source_snapshot=dict(path=str(root / 'manifest.json'), sha256=sha(root / 'manifest.json')),
                output_adapter=receipt['output_adapter'], source_task_ids=['previous_source'],
                source_question_hashes=['b' * 64], updates=8, rows=2, presentations=16)
            self.assertEqual(runner.check_handoff(document, policy.cohort()), receipt)
            document['source_task_ids'] = [policy.cohort()['train'][0][0]['id']]
            with self.assertRaises(AssertionError):
                runner.check_handoff(document, policy.cohort())

    def test_release_cannot_target_other_devices(self):
        with self.assertRaises(AssertionError):
            runner.verify_release(dict(releases={}))


if __name__ == '__main__':
    unittest.main()
