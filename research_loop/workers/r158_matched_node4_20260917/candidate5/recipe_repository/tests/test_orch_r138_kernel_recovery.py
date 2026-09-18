"""Synthetic CPU-only kernel recovery evidence; never accesses the live node."""

import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import random
import tempfile
import textwrap
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r138_kernel_recovery as recovery
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6.orch_r125_plain_context import VERSION


class FakeTensor:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return [self.value]


class FakeAdamW:
    def __init__(self):
        self.state = dict(state={'weight': dict(step=99, momentum=1.25)}, param_groups=[dict(lr=3e-5)])

    def state_dict(self):
        return deepcopy(self.state)

    def load_state_dict(self, state):
        self.state = deepcopy(state)


class FakeTorch:
    Tensor = FakeTensor
    optim = SimpleNamespace(AdamW=FakeAdamW)

    def __init__(self):
        self.counter, self.cuda_counter = 0, 0
        self.cuda = self
        self.loads = 0

    def get_rng_state(self):
        return FakeTensor(self.counter)

    def get_rng_state_all(self):
        return [FakeTensor(self.cuda_counter)]

    def set_rng_state(self, state):
        self.counter = state.value

    def set_rng_state_all(self, states):
        self.cuda_counter = states[0].value

    def load(self, path, **kwargs):
        self.loads += 1
        return deepcopy(self.payload)


class FakeChild:
    def __init__(self, root, source):
        self.plan = dict(root=str(root), source_root=str(source), segment_tokens=4, context_limit=16384,
            hard_end_unix=time.time()+3600, decoder=deepcopy(recovery.DECODER),
            presentation_version=VERSION, system_prompt='System.', birth_prompt='Birth.')
        self.torch, self.optimizer = FakeTorch(), FakeAdamW()
        self.parameters = {'weight': object()}
        self.optimizer_steps = 99
        self.adapter = recovery.ADAPTER_STATE_SHA256
        self.engine = SimpleNamespace(verify_base=lambda: None)
        self.tokenizer = SimpleNamespace(all_special_ids=[151643, 151644, 151645],
            decode=lambda tokens, **kwargs: '<|im_start|>' if tokens == [151644] else '')
        self.calls, self.mismatch, self.mutate, self.fail = [], None, None, False

    def adapter_hash(self):
        return self.adapter

    def verify_checkpoint(self, checkpoint):
        assert checkpoint['base_sha256'] == recovery.BASE_SHA256
        assert hashlib.sha256(Path(checkpoint['optimizer_rng_path']).read_bytes()).hexdigest() == checkpoint['checkpoint_sha256']['optimizer']
        files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in Path(checkpoint['adapter_path']).iterdir()}
        assert files == checkpoint['adapter_files'] and digest(files) == checkpoint['checkpoint_sha256']['adapter']

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.calls.append((deepcopy(messages), max_new_tokens, deadline_unix))
        self.torch.counter += 1
        self.torch.cuda_counter += 2
        if self.fail:
            raise RuntimeError('synthetic generation failure')
        counter = self.torch.counter
        special = counter % 3 == 2
        response = dict(raw=f'Generated {counter}: {random.random()}' + (' <|im_start|> internal' if special else ''),
            token_ids=[counter, 151644, counter, counter] if special else [counter, 151645],
            terminal=not special, truncated=special, prompt_tokens=len(messages),
            prompt_token_ids_sha256=digest(messages), adapter_state_sha256=self.adapter_hash(),
            base_sha256=recovery.BASE_SHA256, decoder=deepcopy(self.plan['decoder']))
        if self.mismatch is not None and counter == self.mismatch[0]:
            response[self.mismatch[1]] = self.mismatch[2]
        if self.mutate == 'prefix':
            messages[0]['content'] += ' forbidden change'
        if self.mutate == 'optimizer':
            self.optimizer.state['state']['weight']['momentum'] += 1
        if self.mutate == 'adapter':
            self.adapter = '0' * 64
        return response


class KernelRecoveryTests(unittest.TestCase):
    def setUp(self):
        saved_random = random.getstate()
        self.addCleanup(random.setstate, saved_random)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source_root = self.root / 'source1'
        self.child = FakeChild(self.root, self.source_root)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=16384, segment_tokens=4, segments_per_sleep=2,
            deadline_unix=self.child.plan['hard_end_unix'], model_state_sha256='0' * 64)
        stream.set_presentation(dict(version=VERSION, system_prompt='System.', birth_prompt='Birth.'), 16384)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        directory = self.root / 'checkpoints' / 'sleep_000002'
        adapter = directory / 'adapter'
        adapter.mkdir(parents=True)
        (adapter / 'adapter.bin').write_bytes(b'Synthetic adapter evidence')
        optimizer_path = directory / 'optimizer_rng.pt'
        optimizer_path.write_bytes(b'Synthetic checkpoint bytes; FakeTorch loads the matching fixture payload')
        files = {'adapter.bin': hashlib.sha256((adapter / 'adapter.bin').read_bytes()).hexdigest()}
        checkpoint_hashes = dict(adapter=digest(files), optimizer=hashlib.sha256(optimizer_path.read_bytes()).hexdigest(),
            rng=hashlib.sha256(optimizer_path.read_bytes()).hexdigest())
        self.checkpoint = dict(base_sha256=recovery.BASE_SHA256, adapter_state_sha256=self.child.adapter,
            optimizer_steps=99, checkpoint_sha256=checkpoint_hashes, adapter_path=str(adapter),
            adapter_files=files, optimizer_rng_path=str(optimizer_path))
        for cycle in (1, 2):
            for unused in range(3):
                stream.step(self.child.generate, len, self.journal.record)
            self.sleep_request(stream, cycle)
            self.journal.record('UPDATE', dict(optimizer_step=48 if cycle == 1 else 99))
            if cycle == 2:
                state = self.journal._scan()
                previous = state['previous']
                for index in range(state['index'], 127):
                    record = dict(schema=self.journal._manifest['schema'], journal_id=self.journal._manifest['journal_id'],
                        index=index, kind='CHECKPOINT_METADATA', previous_sha256=previous, document=dict(synthetic=True))
                    record['sha256'] = digest(record)
                    self.journal._publish(self.journal._records_fd, f'{index:020d}.intent.json', self.journal._intent(record))
                    self.journal._publish(self.journal._records_fd, f'{index:020d}.json', record)
                    previous = record['sha256']
            stream.commit_sleep(dict(status='COMPLETE', cycle=cycle, optimizer_steps=48 if cycle == 1 else 51,
                checkpoint=self.checkpoint, checkpoint_sha256=checkpoint_hashes,
                new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()]), self.journal.record)
        self.child.torch.payload = dict(optimizer=self.child.optimizer.state_dict(), parameter_names=['weight'],
            optimizer_steps=99, cpu_rng=self.child.torch.get_rng_state(), cuda_rng=self.child.torch.get_rng_state_all(),
            python_rng=random.getstate())
        publish_parent(self.root, 'Astra', 'A TRAIN-only kernel question.')
        for unused in range(3):
            stream.step(self.child.generate, len, self.journal.record, incoming=self.journal.read_inbox())
        summary = deepcopy(stream.history.events[-2])
        from dataclasses import replace
        summary = replace(summary, event_id='compaction:3', phase='compaction')
        stream.history.compact(summary, through=stream.history.frontier(len(stream.history.events)-1))
        self.journal.record('COMPACTION', dict(kind='CHILD_COMPACTION', state=stream.checkpoint()))
        tail = self.sleep_request(stream, 3)['sha256']
        self.journal.record('TARGET_ELIGIBILITY', dict(version=VERSION, excluded=[], raw_modified=False,
            new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()], rehearsal_row_sha256=[]))
        self.stream = ContinualStream.restore(**self.journal.latest_checkpoint())
        self.expected_rng = recovery.previous._rng(self.child)
        self.child.torch.counter, self.child.torch.cuda_counter = 700, 800
        self.child.calls = []
        (self.root / 'OWN_CARRY.txt').write_bytes(b'Preserved own carry, never rewritten')
        control = self.root / 'control'
        control.mkdir()
        self.native_source = self.source_root / 'gpu' / 'orch_r125_continual_native.py'
        self.native_source.parent.mkdir(parents=True)
        source = ('def encode_own(row, tokenizer, context_limit):\n'
            '    visible = row["token_ids"]\n'
            '    permitted = {151643}\n'
            '    require(not (set(tokenizer.all_special_ids)-permitted).intersection(visible),\n'
            '            "no_special_token_target_injection")\n\n'
            'class NativeChild:\n' + textwrap.indent(textwrap.dedent(inspect.getsource(FakeChild.generate)), '    ')
            + '\n    def sleep(self, new_rows, old_rows, anchors, record):\n'
            + textwrap.indent(textwrap.dedent(recovery._PRE_ENCODING).strip(), '        ')
            + '\n        self.optimizer.step()\n')
        self.native_source.write_text(source)
        tree = ast.parse(source)
        sleep = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'sleep')
        encoder = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'encode_own')
        encoded = sleep.body[-2]
        guard = next(node for node in ast.walk(encoder) if isinstance(node, ast.Call))
        self.log = control / 'NATIVE.log'
        self.log.write_text('Traceback (most recent call last):\n'
            f'  File "{self.native_source}", line {encoded.lineno}, in sleep\n'
            f'  File "{self.native_source}", line {guard.lineno}, in encode_own\n'
            'ValueError: no_special_token_target_injection\n')
        self.exited = control / 'EXIT.json'
        self.exited.write_text(json.dumps(dict(exit_code=1, no_retry=True)))
        self.original_plan = control / 'PLAN.json'
        self.original_plan.write_text(json.dumps(self.child.plan))
        self.plan = dict(schema=recovery.SCHEMA, recovery_root=str(self.root / 'recoveries' / ('preupdate-' + tail)),
            sleep_request_sha256=tail, checkpoint=deepcopy(self.checkpoint), original_plan=self.ref(self.original_plan),
            original_log=self.ref(self.log), original_exit=self.ref(self.exited), native_source=self.ref(self.native_source))
        for key, value in dict(SLEEP_REQUEST_SHA256=tail, CHECKPOINT_SHA256=checkpoint_hashes,
                SOURCE_ROOT=str(self.source_root), ORIGINAL_PLAN_SHA256=self.plan['original_plan']['sha256'],
                ORIGINAL_LOG_SHA256=self.plan['original_log']['sha256'], ORIGINAL_EXIT_SHA256=self.plan['original_exit']['sha256']).items():
            patched = patch.object(recovery, key, value)
            patched.start()
            self.addCleanup(patched.stop)

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

    def files(self):
        return {str(path): path.read_bytes() for path in self.root.rglob('*')
            if path.is_file() and 'recoveries' not in path.relative_to(self.root).parts}

    def test_exact_three_replays_restore_rng_preserve_every_original_file_and_pending(self):
        before, stream_before = self.files(), self.stream.checkpoint()
        receipt = self.recover()
        self.assertEqual(receipt['status'], 'COMPLETE')
        self.assertEqual(receipt['rng_after'], self.expected_rng)
        self.assertEqual(receipt['optimizer_steps'], 99)
        self.assertEqual(receipt['optimizer_updates'], 0)
        self.assertEqual(receipt['matched_generations'], 3)
        self.assertEqual(self.child.torch.loads, 1)
        self.assertEqual(before, self.files())
        self.assertEqual(stream_before, self.stream.checkpoint())
        self.assertEqual(len(self.child.calls), 3)
        for index, call in enumerate(self.child.calls):
            self.assertEqual(call, (self.stream.pending_rows()[index]['prefix'], 4, self.child.plan['hard_end_unix']))
            self.assertTrue(self.evidence(f'{index:02d}_MATCH.json').exists())
        with self.assertRaises(FileExistsError):
            self.recover()
        self.assertEqual(len(self.child.calls), 3)

    def test_raw_mismatch_fails_first_replay_and_preserves_evidence(self):
        self.child.mismatch = (7, 'raw', 'wrong')
        with self.assertRaisesRegex(ValueError, 'bit_identical_generation:0'):
            self.recover()
        self.assertEqual(len(self.child.calls), 1)
        self.assertTrue(self.evidence('00_RESPONSE.json').exists())
        self.assertTrue(self.evidence('FAILED.json').exists())
        with self.assertRaises(FileExistsError):
            self.recover()

    def test_second_token_mismatch_never_attempts_third(self):
        self.child.mismatch = (8, 'token_ids', [151644])
        with self.assertRaisesRegex(ValueError, 'bit_identical_generation:1'):
            self.recover()
        self.assertEqual(len(self.child.calls), 2)

    def test_decoder_mismatch_fails_closed(self):
        self.child.mismatch = (7, 'decoder', {})
        with self.assertRaisesRegex(ValueError, 'bit_identical_generation:0'):
            self.recover()

    def test_optimizer_mutation_without_step_counter_change_rejected(self):
        self.child.mutate = 'optimizer'
        with self.assertRaisesRegex(ValueError, 'replay_cannot_update_learning'):
            self.recover()

    def test_prefix_mutation_rejected(self):
        self.child.mutate = 'prefix'
        with self.assertRaisesRegex(ValueError, 'replay_cannot_mutate_prefix'):
            self.recover()

    def test_appended_update_rejected_before_replay(self):
        self.journal.record('UPDATE', dict(optimizer_step=100))
        with self.assertRaisesRegex(ValueError, 'exact_kernel_127_140_tail'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_wrong_step_count_rejected_before_rng_restore(self):
        self.child.optimizer_steps = 48
        with self.assertRaisesRegex(ValueError, 'restored_sleep2_adapter_99_steps_base'):
            self.recover()
        self.assertEqual(self.child.torch.loads, 0)

    def test_wrong_checkpoint_adapter_rejected(self):
        self.child.adapter = '0' * 64
        with self.assertRaisesRegex(ValueError, 'restored_sleep2_adapter_99_steps_base'):
            self.recover()

    def test_original_plan_presentation_changes_rejected(self):
        self.child.plan['presentation_version'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'original_plan_semantics_unchanged'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_source_closure_path_change_allowed_but_generate_ast_unchanged(self):
        self.child.plan['source_root'] = str(self.root / 'repaired_kernel_closure')
        self.child.plan['preupdate_recovery'] = deepcopy(self.plan)
        self.assertEqual(self.recover()['status'], 'COMPLETE')

    def test_recovery_accepts_only_bound_startup_relocation(self):
        original = self.source_root / 'startup' / 'birth.txt'
        original.parent.mkdir()
        original.write_bytes(self.child.plan['birth_prompt'].encode())
        self.child.plan['startup_context'] = dict(version='R127_STARTUP_V1', **self.ref(original))
        self.original_plan.write_text(json.dumps(self.child.plan))
        self.plan['original_plan'] = self.ref(self.original_plan)
        new_root = self.root / 'source_recovery1'
        relocated = new_root / 'startup' / 'birth.txt'
        relocated.parent.mkdir(parents=True)
        relocated.write_bytes(original.read_bytes())
        self.child.plan['source_root'] = str(new_root)
        self.child.plan['startup_context']['path'] = str(relocated)
        with patch.object(recovery, 'ORIGINAL_PLAN_SHA256', self.plan['original_plan']['sha256']):
            self.assertEqual(self.recover()['status'], 'COMPLETE')

    def test_changed_original_log_rejected(self):
        self.log.write_text(self.log.read_text() + '\nChanged evidence')
        with self.assertRaisesRegex(ValueError, 'pinned_file_hash'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_optimizer_parameter_order_mismatch_rejected(self):
        self.child.torch.payload['parameter_names'] = ['other']
        with self.assertRaisesRegex(ValueError, 'sleep2_optimizer_order_experiment'):
            self.recover()

    def test_saved_optimizer_reload_is_verified_not_just_step_counter(self):
        self.child.optimizer.state['state']['weight']['momentum'] = 999
        with patch.object(self.child.optimizer, 'load_state_dict', return_value=None):
            with self.assertRaisesRegex(ValueError, 'exact_saved_AdamW_restored'):
                self.recover()
        self.assertFalse(self.child.calls)

    def test_modified_checkpoint_bytes_rejected_before_deserialization(self):
        Path(self.checkpoint['optimizer_rng_path']).write_bytes(b'changed checkpoint')
        with self.assertRaisesRegex(ValueError, 'saved_optimizer_rng_hash'):
            self.recover()
        self.assertEqual(self.child.torch.loads, 0)

    def test_source_with_optimizer_work_before_encoding_rejected(self):
        source = self.native_source.read_text().replace('        exclusions = []',
            '        self.optimizer.step()\n        exclusions = []')
        self.native_source.write_text(source)
        self.plan['native_source'] = self.ref(self.native_source)
        with self.assertRaisesRegex(ValueError, 'encoding_before_optimizer_work'):
            self.recover()
        self.assertFalse(self.child.calls)

    def test_no_held_reads_no_stream_steps_or_journal_records_during_recovery(self):
        original = recovery._raw
        permitted = {self.plan[field]['path'] for field in ('original_plan', 'original_log', 'original_exit', 'native_source')}
        permitted.add(self.checkpoint['optimizer_rng_path'])
        def guarded(path, limit):
            self.assertIn(str(path), permitted)
            return original(path, limit)
        with patch.object(recovery, '_raw', side_effect=guarded), \
                patch.object(self.stream, 'step', side_effect=AssertionError('TRAIN replay forbidden')), \
                patch.object(self.journal, 'record', side_effect=AssertionError('journal append forbidden')):
            self.assertEqual(self.recover()['status'], 'COMPLETE')

    def test_generation_failure_is_terminal_and_does_not_write_train(self):
        self.child.fail = True
        before = self.files()
        with self.assertRaisesRegex(RuntimeError, 'synthetic generation failure'):
            self.recover()
        self.assertEqual(before, self.files())
        self.assertTrue(self.evidence('FAILED.json').exists())

    def test_wrong_sleep_request_pin_rejected_without_replay(self):
        self.plan['sleep_request_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'pinned_kernel_sleep_request'):
            self.recover()
        self.assertFalse(self.child.calls)


    def test_legacy_class_rejects_any_saved_experiment_field(self):
        self.assertFalse(hasattr(self.child, 'experiment'))
        for field in ('checkpoint', 'payload'):
            for value in (None, 'unexpected'):
                with self.subTest(field=field, value=value):
                    checkpoint = deepcopy(self.checkpoint)
                    target = checkpoint if field == 'checkpoint' else self.child.torch.payload
                    target['experiment'] = value
                    before = recovery.previous._rng(self.child)
                    with self.assertRaisesRegex(ValueError, 'legacy_checkpoint_payload_without_experiment'):
                        recovery._restore(self.child, checkpoint, self.root)
                    self.assertEqual(before, recovery.previous._rng(self.child))
                    del target['experiment']
        self.assertFalse(self.child.calls)

    def test_nonlegacy_experiment_mismatch_still_rejected(self):
        self.child.experiment = 'bound-experiment'
        with self.assertRaisesRegex(ValueError, 'sleep2_optimizer_order_experiment'):
            recovery._restore(self.child, self.checkpoint, self.root)
        self.assertFalse(self.child.calls)
        self.child.experiment = None
        recovery._restore(self.child, self.checkpoint, self.root)

    def test_explicit_attempt2_preserves_failed_attempt_and_replays_once(self):
        before = self.files()
        with patch.object(recovery, '_restore', side_effect=AttributeError(recovery.PRIOR_ERROR)), \
                self.assertRaisesRegex(AttributeError, 'experiment'):
            self.recover()
        first_root = Path(self.plan['recovery_root'])
        first_files = {path.name: path.read_bytes() for path in first_root.iterdir()}
        self.assertFalse(self.child.calls)
        self.assertNotIn('STARTED.json', first_files)
        self.assertEqual(before, self.files())
        failed = json.loads(first_files['FAILED.json'])
        log = self.root / 'control_recovery1' / 'NATIVE.log'
        log.parent.mkdir()
        log.write_text('Traceback (most recent call last):\n'
            '  File "/frozen/helper.py", line 242, in _restore\n'
            'AttributeError: ' + recovery.PRIOR_ERROR + '\n')
        before = self.files()
        self.plan['prior_failed_attempt'] = dict(recovery_root=str(first_root),
            plan=self.ref(first_root / 'PLAN.json'), failed=self.ref(first_root / 'FAILED.json'),
            journal_evidence=self.ref(first_root / 'JOURNAL_EVIDENCE.json'), native_log=self.ref(log))
        self.plan['recovery_root'] += '-attempt2'
        fresh = FakeChild(self.root, self.source_root)
        fresh.plan = deepcopy(self.child.plan)
        fresh.torch.payload = deepcopy(self.child.torch.payload)
        self.child = fresh
        self.child.plan['source_root'] = str(self.root / 'source_recovery2')
        self.child.plan['preupdate_recovery'] = deepcopy(self.plan)
        with patch.object(recovery, 'PRIOR_FAILED_SHA256', self.plan['prior_failed_attempt']['failed']['sha256']), \
                patch.object(recovery, 'PRIOR_LOG_SHA256', self.ref(log)['sha256']), \
                patch.object(recovery, 'PRIOR_FAILURE_TIME', failed['finished_unix']):
            receipt = self.recover()
            self.assertEqual(receipt['matched_generations'], 3)
            evidence = json.loads(self.evidence('PRIOR_FAILED_ATTEMPT.json').read_bytes())
            self.assertEqual(receipt['prior_failed_attempt_sha256'], digest(evidence))
            with self.assertRaises(FileExistsError):
                self.recover()
        self.assertEqual(first_files, {path.name: path.read_bytes() for path in first_root.iterdir()})
        self.assertEqual(before, self.files())
        self.assertEqual(len(self.child.calls), 3)

    def test_attempt2_requires_explicit_prior_and_no_attempt3(self):
        original = self.plan['recovery_root']
        for suffix, prior in (('-attempt2', False), ('-attempt3', True), ('', True)):
            with self.subTest(suffix=suffix, prior=prior):
                plan = deepcopy(self.plan)
                plan['recovery_root'] = original + suffix
                if prior:
                    plan['prior_failed_attempt'] = {}
                with self.assertRaisesRegex(ValueError, 'deterministic_recovery_root'):
                    recovery.recover_rng(self.child, self.stream, self.journal, plan)
        self.assertFalse(self.child.calls)
        self.assertEqual(self.child.torch.loads, 0)


class PriorAttemptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.first = self.root / 'recoveries' / ('preupdate-' + recovery.SLEEP_REQUEST_SHA256)
        self.first.mkdir(parents=True)
        self.suffix = [dict(index=140, sha256='a' * 64)]
        self.plan = dict(schema=recovery.SCHEMA, recovery_root=str(self.first),
            sleep_request_sha256=recovery.SLEEP_REQUEST_SHA256, checkpoint={})
        for field, name in (('original_plan', 'ORIGINAL_PLAN.json'), ('original_log', 'ORIGINAL_NATIVE.log'),
                ('original_exit', 'ORIGINAL_EXIT.json'), ('native_source', 'ORIGINAL_NATIVE.py')):
            path = self.first / name
            path.write_bytes(b'Original pinned fixture')
            self.plan[field] = KernelRecoveryTests.ref(path)
        recovery.previous._save(self.first / 'PLAN.json', self.plan)
        recovery.previous._save(self.first / 'JOURNAL_EVIDENCE.json', self.suffix)
        recovery.previous._save(self.first / 'FAILED.json', dict(schema=recovery.SCHEMA, status='FAILED',
            error_type='AttributeError', error=recovery.PRIOR_ERROR, no_retry=True,
            child_must_be_discarded=True, finished_unix=recovery.PRIOR_FAILURE_TIME))
        log = self.root / 'control_recovery1' / 'NATIVE.log'
        log.parent.mkdir()
        log.write_text('Traceback (most recent call last):\n'
            '  File "/frozen/helper.py", line 242, in _restore\n'
            'AttributeError: ' + recovery.PRIOR_ERROR + '\n')
        self.plan['recovery_root'] += '-attempt2'
        self.plan['prior_failed_attempt'] = dict(recovery_root=str(self.first),
            plan=KernelRecoveryTests.ref(self.first / 'PLAN.json'),
            failed=KernelRecoveryTests.ref(self.first / 'FAILED.json'),
            journal_evidence=KernelRecoveryTests.ref(self.first / 'JOURNAL_EVIDENCE.json'),
            native_log=KernelRecoveryTests.ref(log))
        self.prior = self.plan['prior_failed_attempt']
        for key, value in dict(SOURCE_ROOT=str(self.root / 'source1'),
                PRIOR_FAILED_SHA256=self.prior['failed']['sha256'], PRIOR_LOG_SHA256=self.prior['native_log']['sha256']).items():
            mock = patch.object(recovery, key, value)
            mock.start()
            self.addCleanup(mock.stop)

    def verify(self):
        return recovery._verify_prior_attempt(self.plan, self.root, self.suffix)

    def test_exact_prior_pre_replay_evidence(self):
        self.assertTrue(self.verify()['journal_records_unchanged'])

    def test_replay_or_unknown_artifact_rejected_without_reading_it(self):
        for name in ('STARTED.json', '00_REQUEST.json', '00_RESPONSE.json', '00_MATCH.json',
                'COMPLETE.json', 'held.json'):
            with self.subTest(name=name):
                path = self.first / name
                path.write_bytes(b'Must not read')
                with patch.object(recovery, '_read') as reader, \
                        self.assertRaisesRegex(ValueError, 'prior_exact_pre_replay_inventory'):
                    self.verify()
                reader.assert_not_called()
                path.unlink()

    def test_pins_paths_missing_fields_and_symlinks_rejected(self):
        original = deepcopy(self.prior)
        for field in ('plan', 'failed', 'journal_evidence', 'native_log'):
            for change in ('hash', 'path', 'missing'):
                with self.subTest(field=field, change=change):
                    altered = deepcopy(original)
                    if change == 'missing':
                        del altered[field]
                    else:
                        altered[field]['sha256' if change == 'hash' else 'path'] = '0' * 64
                    self.plan['prior_failed_attempt'] = altered
                    with self.assertRaises(ValueError):
                        self.verify()
        self.plan['prior_failed_attempt'] = original
        path = self.first / 'FAILED.json'
        saved = self.root / 'saved-failure.json'
        path.rename(saved)
        path.symlink_to(saved)
        with self.assertRaises(OSError):
            self.verify()

    def test_changed_journal_rejected(self):
        self.suffix[0]['sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'prior_journal_unchanged'):
            self.verify()

    def test_prior_plan_and_original_copies_remain_bound(self):
        self.plan['checkpoint'] = {'changed': True}
        with self.assertRaisesRegex(ValueError, 'prior_same_recovery_plan'):
            self.verify()
        self.plan['checkpoint'] = {}
        (self.first / 'ORIGINAL_NATIVE.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'prior_original_evidence_hash'):
            self.verify()

    def test_wrong_failure_rejected_even_with_caller_hash(self):
        path = self.first / 'FAILED.json'
        document = json.loads(path.read_bytes())
        document['error'] = 'different failure'
        path.write_text(json.dumps(document))
        self.prior['failed'] = KernelRecoveryTests.ref(path)
        with self.assertRaisesRegex(ValueError, 'fixed_prior_failure_hash'):
            self.verify()
        with patch.object(recovery, 'PRIOR_FAILED_SHA256', self.prior['failed']['sha256']), \
                self.assertRaisesRegex(ValueError, 'exact_prior_legacy_attribute_failure'):
            self.verify()

    def test_changed_failure_log_rejected(self):
        Path(self.prior['native_log']['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'fixed_prior_log_hash'):
            self.verify()


class StartupRelocationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.original_path = self.root / 'source1' / 'prompts' / 'birth.txt'
        self.new_path = self.root / 'source_recovery1' / 'prompts' / 'birth.txt'
        self.birth = 'Exact birth bytes.\nπ stays unchanged.\n'
        for path in (self.original_path, self.new_path):
            path.parent.mkdir(parents=True)
            path.write_bytes(self.birth.encode())
        self.original = dict(source_root=str(self.root / 'source1'), birth_prompt=self.birth,
            startup_context=dict(version='R127_STARTUP_V1', path=str(self.original_path),
                sha256=hashlib.sha256(self.birth.encode()).hexdigest()),
            decoder={'temperature': 0.7}, hard_end_unix=1000, presentation_version=VERSION)
        self.resume = deepcopy(self.original)
        self.resume['source_root'] = str(self.root / 'source_recovery1')
        self.resume['startup_context']['path'] = str(self.new_path)
        self.resume['preupdate_recovery'] = {'schema': recovery.SCHEMA}

    def test_exact_relative_relocation_preserves_both_plans(self):
        before = deepcopy((self.original, self.resume))
        recovery._verify_original_plan(self.original, self.resume)
        self.assertEqual(before, (self.original, self.resume))

    def test_unchanged_closure_and_startup_still_valid(self):
        recovery._verify_original_plan(self.original, deepcopy(self.original))

    def test_same_hash_at_different_relative_path_rejected_without_read(self):
        self.resume['startup_context']['path'] = str(self.new_path.parent / 'other.txt')
        with patch.object(recovery, '_raw') as reader, self.assertRaisesRegex(ValueError, 'startup_exact_relative_relocation'):
            recovery._verify_original_plan(self.original, self.resume)
        reader.assert_not_called()

    def test_original_path_left_outside_new_closure_rejected(self):
        self.resume['startup_context']['path'] = str(self.original_path)
        with self.assertRaisesRegex(ValueError, 'startup_exact_relative_relocation'):
            recovery._verify_original_plan(self.original, self.resume)

    def test_version_hash_and_extra_field_changes_rejected(self):
        for field, value in (('version', 'R127_STARTUP_V2'), ('sha256', '0' * 64), ('extra', 'not allowed')):
            with self.subTest(field=field):
                altered = deepcopy(self.resume)
                altered['startup_context'][field] = value
                with self.assertRaises(ValueError):
                    recovery._verify_original_plan(self.original, altered)

    def test_changed_birth_decoder_deadline_or_presentation_rejected(self):
        for field, value in (('birth_prompt', 'Different.'), ('decoder', {'temperature': 1}),
                ('hard_end_unix', 1001), ('presentation_version', 'changed')):
            with self.subTest(field=field):
                altered = deepcopy(self.resume)
                altered[field] = value
                with self.assertRaisesRegex(ValueError, 'original_plan_semantics_unchanged'):
                    recovery._verify_original_plan(self.original, altered)

    def test_changed_original_or_relocated_bytes_rejected(self):
        for path in (self.original_path, self.new_path):
            with self.subTest(path=path):
                path.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'startup_exact_birth_bytes'):
                    recovery._verify_original_plan(self.original, self.resume)
                path.write_bytes(self.birth.encode())

    def test_symlink_relocated_file_rejected_even_with_same_bytes(self):
        self.new_path.unlink()
        self.new_path.symlink_to(self.original_path)
        with self.assertRaises(OSError):
            recovery._verify_original_plan(self.original, self.resume)

    def test_parent_component_relocation_rejected(self):
        self.resume['startup_context']['path'] = str(self.new_path.parent / '..' / 'prompts' / 'birth.txt')
        with self.assertRaisesRegex(ValueError, 'absolute_startup_paths'):
            recovery._verify_original_plan(self.original, self.resume)


if __name__ == '__main__':
    unittest.main()
