"""CPU regression tests for the bounded, non-material pre-update repair."""

import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import textwrap
import time
import unittest
from unittest.mock import patch

from gpu import orch_r125_preupdate_recovery as recovery
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


class FakeTensor:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return [self.value]


class FakeTorch:
    def __init__(self):
        self.counter = 0
        self.cuda = self

    def get_rng_state(self):
        return FakeTensor(self.counter)

    def get_rng_state_all(self):
        return [FakeTensor(self.counter * 2)]


class FakeChild:
    def __init__(self, root, deadline):
        self.plan = dict(root=str(root), segment_tokens=512, context_limit=8192,
            hard_end_unix=deadline, decoder=dict(temperature=0.7, top_p=0.95,
                repetition_penalty=1.05, no_repeat_ngram_size=16))
        self.torch = FakeTorch()
        self.optimizer_steps = 48
        self.calls = []
        self.mismatch = None
        self.fail = False
        self.mutate_prefix = False

    def adapter_hash(self):
        return 'a' * 64

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.calls.append((deepcopy(messages), max_new_tokens, deadline_unix))
        self.torch.counter += 1
        if self.fail:
            raise RuntimeError('generation interrupted')
        response = self.output(messages)
        if self.mismatch is not None and self.torch.counter == self.mismatch[0]:
            response[self.mismatch[1]] = self.mismatch[2]
        if self.mutate_prefix:
            messages[0]['content'] = 'mutated'
        return response

    def output(self, messages):
        counter = self.torch.counter
        padded = counter % 3 == 2
        tokens = [counter] * 512 if padded else [counter, 2]
        if padded:
            tokens[20] = 151643
        return dict(raw=f'Generated {counter}' + (' <|endoftext|> internal' if padded else ''),
            token_ids=tokens, terminal=not padded, truncated=padded,
            prompt_tokens=len(messages), prompt_token_ids_sha256=digest(messages),
            adapter_state_sha256=self.adapter_hash(), base_sha256='b' * 64,
            decoder=deepcopy(self.plan['decoder']))


class PreupdateRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.prepare()

    def prepare(self, mode=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.child = FakeChild(self.root, time.time() + 3600)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=8192, segment_tokens=512, segments_per_sleep=2,
            deadline_unix=self.child.plan['hard_end_unix'], model_state_sha256='0' * 64)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        self.checkpoint = dict(base_sha256='b' * 64, adapter_state_sha256='a' * 64,
            optimizer_steps=48, checkpoint_sha256=dict(adapter='c' * 64, optimizer='d' * 64, rng='d' * 64))
        for unused in range(3):
            stream.step(self.child.generate, len, self.journal.record)
        self.sleep_request(stream, 1)
        self.journal.record('UPDATE', dict(optimizer_step=48))
        stream.commit_sleep(dict(status='COMPLETE', cycle=1, optimizer_steps=48,
            checkpoint=self.checkpoint, checkpoint_sha256=self.checkpoint['checkpoint_sha256'],
            new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()]), self.journal.record)
        for unused in range(2 if mode in ('request', 'response') else 3):
            stream.step(self.child.generate, len, self.journal.record)
        if mode in ('request', 'response'):
            def interrupted(kind, document):
                if kind == ('RESPONSE' if mode == 'request' else 'COMMITTED'):
                    raise RuntimeError('interrupted')
                return self.journal.record(kind, document)
            with self.assertRaises(RuntimeError):
                stream.step(self.child.generate, len, interrupted)
            tail = self.journal._scan()['previous']
        else:
            if mode == 'update_before_request':
                self.journal.record('UPDATE', dict(optimizer_step=49))
            tail = self.sleep_request(stream, 2)['sha256']
        self.stream = ContinualStream.restore(**self.journal.latest_checkpoint())
        self.expected_rng = recovery._rng(self.child)
        self.child.torch.counter = 3
        self.child.calls.clear()
        control = self.root / 'control2'
        control.mkdir()
        self.source_path = self.root / 'source_v2' / 'gpu' / 'orch_r125_continual_native.py'
        self.source_path.parent.mkdir(parents=True)
        self.log_path = control / 'NATIVE.log'
        self.exit_path = control / 'EXIT.json'
        self.exit_path.write_text(json.dumps(dict(exit_code=1, no_retry=True)))
        self.source = ('def encode_own(row, tokenizer, context_limit):\n'
            '    visible = row["token_ids"]\n'
            '    require(not set(tokenizer.all_special_ids).intersection(visible),\n'
            '            "no_special_token_target_injection")\n\n'
            'class NativeChild:\n' + textwrap.indent(textwrap.dedent(inspect.getsource(FakeChild.generate)), '    ')
            + '\n    def sleep(self, new_rows, old_rows, anchors, record):\n'
            + textwrap.indent(textwrap.dedent(recovery._PRE_ENCODING).strip(), '        ')
            + '\n        self.optimizer.zero_grad()\n        self.optimizer.step()\n')
        self.write_source(self.source)
        self.plan = dict(schema=recovery.SCHEMA,
            recovery_root=str(self.root / 'recoveries' / ('preupdate-' + tail)),
            sleep_request_sha256=tail, original_log=self.ref(self.log_path),
            original_exit=self.ref(self.exit_path), native_source=self.ref(self.source_path),
            checkpoint=deepcopy(self.checkpoint))

    def write_source(self, source):
        self.source_path.write_text(source)
        tree = ast.parse(source)
        guard = next(node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == 'require'
            and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == 'no_special_token_target_injection')
        encoded = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'encoded')
        self.log_path.write_text('Traceback (most recent call last):\n'
            f'  File "{self.source_path}", line {encoded.lineno}, in sleep\n'
            '    encoded = {row["source_sha256"]: encode_own(row, tokenizer, context_limit)}\n'
            f'  File "{self.source_path}", line {guard.lineno}, in encode_own\n'
            '    require(not set(tokenizer.all_special_ids).intersection(visible),\n'
            'ValueError: no_special_token_target_injection\n')

    @staticmethod
    def ref(path):
        return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def sleep_request(self, stream, cycle):
        pending = stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in stream.pending_rows()])
        pending['sha256'] = digest(pending['state'])
        return self.journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))

    def recover(self):
        return recovery.recover_rng(self.child, self.stream, self.journal, self.plan)

    def evidence(self, name):
        return Path(self.plan['recovery_root']) / name

    def snapshot(self):
        return {str(path): path.read_bytes() for path in self.root.rglob('*')
                if path.is_file() and 'recoveries' not in path.parts}

    def test_all_three_match_actual_rng_reconstructed_without_mutation_or_retry(self):
        before = self.snapshot()
        stream_before = self.stream.checkpoint()
        plan_before = deepcopy(self.plan)
        receipt = self.recover()
        self.assertEqual(receipt['status'], 'COMPLETE')
        self.assertTrue(receipt['rng_reconstruction_verified'])
        self.assertEqual(receipt['rng_after'], self.expected_rng)
        self.assertNotEqual(receipt['rng_before'], receipt['rng_after'])
        self.assertEqual(receipt['matched_generations'], 3)
        self.assertEqual(receipt['optimizer_updates'], 0)
        self.assertFalse(receipt['original_final_rng_snapshot_available'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(stream_before, self.stream.checkpoint())
        self.assertEqual(plan_before, self.plan)
        self.assertEqual(self.child.optimizer_steps, 48)
        for index, call in enumerate(self.child.calls):
            self.assertEqual(call, (self.stream.pending_rows()[index]['prefix'], 512,
                                   self.child.plan['hard_end_unix']))
            self.assertTrue(self.evidence(f'{index:02d}_MATCH.json').exists())
        self.assertEqual(json.loads(self.evidence('COMPLETE.json').read_text()), receipt)
        with self.assertRaises(FileExistsError):
            self.recover()
        self.assertEqual(len(self.child.calls), 3)

    def test_every_output_mismatch_stops_at_first_bad_generation(self):
        for field, wrong in [('raw', 'different'), ('token_ids', [7]), ('terminal', False),
                             ('truncated', True), ('prompt_token_ids_sha256', 'f' * 64),
                             ('decoder', {})]:
            with self.subTest(field=field):
                self.prepare()
                self.child.mismatch = (4, field, wrong)
                with self.assertRaisesRegex(ValueError, 'bit_identical_generation:0'):
                    self.recover()
                self.assertEqual(len(self.child.calls), 1)
                self.assertTrue(self.evidence('00_RESPONSE.json').exists())
                self.assertTrue(self.evidence('FAILED.json').exists())
                self.assertFalse(self.evidence('COMPLETE.json').exists())
                with self.assertRaises(FileExistsError):
                    self.recover()
                self.assertEqual(len(self.child.calls), 1)

    def test_second_and_third_mismatch_do_not_continue(self):
        for counter in (5, 6):
            with self.subTest(counter=counter):
                self.prepare()
                self.child.mismatch = (counter, 'raw', 'different')
                with self.assertRaisesRegex(ValueError, 'bit_identical_generation'):
                    self.recover()
                self.assertEqual(len(self.child.calls), counter - 3)

    def test_wrong_file_hashes_fail_before_replay_and_preserve_bytes(self):
        for key in ('original_log', 'original_exit', 'native_source'):
            with self.subTest(key=key):
                self.prepare()
                self.plan[key]['sha256'] = 'f' * 64
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, 'pinned_file_hash'):
                    self.recover()
                self.assertEqual(before, self.snapshot())
                self.assertFalse(self.child.calls)
                self.assertTrue(self.evidence('FAILED.json').exists())

    def test_exit_zero_and_wrong_traceback_rejected(self):
        self.exit_path.write_text(json.dumps(dict(exit_code=0, no_retry=True)))
        self.plan['original_exit'] = self.ref(self.exit_path)
        with self.assertRaisesRegex(ValueError, 'original_exit1'):
            self.recover()
        self.prepare()
        self.log_path.write_text('ValueError: no_special_token_target_injection\n')
        self.plan['original_log'] = self.ref(self.log_path)
        with self.assertRaisesRegex(ValueError, 'specific_encode_own_traceback'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_late_update_and_update_before_request_rejected(self):
        self.journal.record('UPDATE', dict(optimizer_step=49))
        with self.assertRaisesRegex(ValueError, 'latest_exact_SLEEP_REQUEST'):
            self.recover()
        self.assertFalse(self.child.calls)
        self.prepare('update_before_request')
        with self.assertRaisesRegex(ValueError, 'no_postcheckpoint_UPDATE'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_request_pending_and_response_without_commit_rejected(self):
        for mode in ('request', 'response'):
            with self.subTest(mode=mode):
                self.prepare(mode)
                with self.assertRaisesRegex(ValueError, 'no_pending_generation'):
                    self.recover()
                self.assertFalse(self.child.calls)

    def test_wrong_checkpoint_receipt_and_restored_learning_state_rejected(self):
        self.plan['checkpoint']['optimizer_steps'] = 49
        with self.assertRaisesRegex(ValueError, 'matching_last_committed_checkpoint'):
            self.recover()
        self.prepare()
        self.child.optimizer_steps = 49
        with self.assertRaisesRegex(ValueError, 'restored_adapter_optimizer'):
            self.recover()
        self.prepare()
        with patch.object(self.child, 'adapter_hash', return_value='f' * 64):
            with self.assertRaisesRegex(ValueError, 'restored_adapter_optimizer'):
                self.recover()
        self.assertFalse(self.child.calls)

    def test_changed_prefix_pending_and_flags_rejected(self):
        for field, value in [('prefix', []), ('terminal', False), ('truncated', True)]:
            with self.subTest(field=field):
                self.prepare()
                self.stream.rows[-1][field] = value
                with self.assertRaisesRegex(ValueError, 'restored_stream_matches_journal'):
                    self.recover()
                self.assertFalse(self.child.calls)
        self.prepare()
        self.stream.pending = None
        with self.assertRaisesRegex(ValueError, 'restored_stream_matches_journal'):
            self.recover()

    def test_optimizer_before_encoding_source_rejected(self):
        source = self.source.replace('        encoded =', '        self.optimizer.zero_grad()\n        encoded =')
        self.write_source(source)
        self.plan['native_source'] = self.ref(self.source_path)
        self.plan['original_log'] = self.ref(self.log_path)
        with self.assertRaisesRegex(ValueError, 'encoding_before_sleep_optimizer_initialization'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_changed_generate_AST_rejected_but_formatting_is_ignored(self):
        source = self.source.replace('self.torch.counter += 1', 'self.torch.counter += 2')
        self.write_source(source)
        self.plan['native_source'] = self.ref(self.source_path)
        self.plan['original_log'] = self.ref(self.log_path)
        with self.assertRaisesRegex(ValueError, 'unchanged_generate_AST'):
            self.recover()
        self.prepare()
        self.write_source('\n\n' + self.source)
        self.plan['native_source'] = self.ref(self.source_path)
        self.plan['original_log'] = self.ref(self.log_path)
        self.assertEqual(self.recover()['status'], 'COMPLETE')

    def test_generation_exception_retains_started_evidence_and_no_retry(self):
        self.child.fail = True
        with self.assertRaisesRegex(RuntimeError, 'generation interrupted'):
            self.recover()
        self.assertTrue(self.evidence('STARTED.json').exists())
        self.assertTrue(self.evidence('00_REQUEST.json').exists())
        self.assertFalse(self.evidence('00_RESPONSE.json').exists())
        self.assertTrue(self.evidence('FAILED.json').exists())
        with self.assertRaises(FileExistsError):
            self.recover()
        self.assertEqual(len(self.child.calls), 1)

    def test_prefix_copy_protects_rows_even_from_mutating_generator(self):
        before = self.stream.checkpoint()
        self.child.mutate_prefix = True
        with self.assertRaisesRegex(ValueError, 'replay_cannot_mutate_prefix'):
            self.recover()
        self.assertEqual(before, self.stream.checkpoint())

    def test_deadline_decoder_and_alternate_recovery_directory_rejected(self):
        self.child.plan['hard_end_unix'] += 1
        with self.assertRaisesRegex(ValueError, 'replay_budget_deadline'):
            self.recover()
        self.prepare()
        self.child.plan['decoder']['temperature'] = 0.8
        with self.assertRaisesRegex(ValueError, 'exact_native_decoder'):
            self.recover()
        self.prepare()
        self.plan['recovery_root'] += '-retry'
        with self.assertRaisesRegex(ValueError, 'deterministic_local_recovery_root'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_wrong_sleep_hash_and_metadata_after_sleep_rejected(self):
        self.plan['sleep_request_sha256'] = 'f' * 64
        self.plan['recovery_root'] = str(self.root / 'recoveries' / ('preupdate-' + 'f' * 64))
        with self.assertRaisesRegex(ValueError, 'latest_exact_SLEEP_REQUEST'):
            self.recover()
        self.assertFalse(self.child.calls)
        self.prepare()
        self.journal.record('LOADED', dict(optimizer_steps=48))
        with self.assertRaisesRegex(ValueError, 'latest_exact_SLEEP_REQUEST'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_expired_deadline_and_changed_run_root_cannot_replay(self):
        with patch.object(recovery.time, 'time', return_value=self.child.plan['hard_end_unix'] + 1):
            with self.assertRaisesRegex(ValueError, 'replay_deadline'):
                self.recover()
        self.assertFalse(self.child.calls)
        self.prepare()
        self.child.plan['root'] = str(self.root / 'other')
        self.plan['recovery_root'] = str(Path(self.child.plan['root']) / 'recoveries'
            / ('preupdate-' + self.plan['sleep_request_sha256']))
        with self.assertRaisesRegex(ValueError, 'journal_run_root_binding'):
            self.recover()
        self.assertFalse(self.child.calls)


if __name__ == '__main__':
    unittest.main()
