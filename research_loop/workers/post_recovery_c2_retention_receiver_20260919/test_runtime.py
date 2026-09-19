"""New-source adoption seam on the exact old C2 reader, with synthetic records."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research_loop.workers.post_recovery_c2_retention_receiver_20260919 import test_cpu_probe as cpu_fixture
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.c2_retention_runtime import bind_journal, digest
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.ports import (
    proposed_ports, changes_for, NATIVE, RUNTIME, NATIVE_BEFORE)
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.receiver import (
    DEADLINE, GPU_UUID, CONFINEMENT, TRIAL, write_once)


SOURCE = cpu_fixture.SOURCE
StreamJournal = cpu_fixture.StreamJournal


class RuntimeTests(unittest.TestCase):
    step = cpu_fixture.TailTests.step
    receipt = cpu_fixture.TailTests.receipt
    parent = cpu_fixture.TailTests.parent
    pins = cpu_fixture.TailTests.pins

    def setUp(self):
        cpu_fixture.TailTests.setUp(self)
        self.source = self.root.parent.parent / 'epoch2/source'
        outputs = proposed_ports(SOURCE)
        for name, content in outputs.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.plan = dict(root=str(self.root.parent), source_root=str(self.source), hard_end_unix=DEADLINE,
            physical=1, gpu_uuid=GPU_UUID, think_act_learn=dict(trial_id=TRIAL),
            checkpoint_tail_recovery=self.selection)
        complete = self.selection['complete_index']
        records = [json.loads((self.root / 'records' / f'{index:020d}.json').read_bytes())
            for index in range(complete, self.candidate['head_index'] + 1)]
        self.candidate.update(journal_id=self.selection['journal_id'], complete_index=complete,
            complete_sha256=self.selection['complete_sha256'], learn_index=records[-1]['index'],
            learn_sha256=records[-1]['sha256'], records=records,
            mailbox={str(path): dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                for path in (self.root / 'inbox').iterdir()})
        receiver = dict(plan=self.plan, plan_sha256=digest(self.plan), source_epoch='synthetic-epoch2',
            dispatcher_module=CONFINEMENT, same_journal_root=str(self.root))
        self.token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', old_native_exited=True,
            deadline_unix=DEADLINE, no_cold_start=True, no_unresolved_work_replayed=True,
            epoch_record_required_before_first_THINK=True, epoch_id='synthetic-epoch2',
            exact_complete=self.candidate, receiver=receiver,
            new_source_pins={name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()})
        self.token_path = self.source.parent / 'control/RETENTION_HANDOFF.json'
        self.save_token()

    def save_token(self):
        self.token['sha256'] = digest({key: value for key, value in self.token.items() if key != 'sha256'})
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(self.token))

    def reopen(self, *, close=True):
        if close:
            self.journal.close()
        wrapper = bind_journal(StreamJournal, self.plan)
        journal = wrapper(self.root, checkpoint_tail=self.selection)
        self.addCleanup(journal.close)
        return journal

    def test_exact_adoption_under_writer_lock_before_model_or_THINK(self):
        before = self.pins()
        journal = self.reopen()
        index = journal._state['index'] - 1
        record = json.loads((self.root / 'records' / f'{index:020d}.json').read_bytes())
        self.assertEqual(record['kind'], 'RETENTION_SOURCE_ADOPTED')
        self.assertEqual(record['document']['handoff_sha256'], self.token['sha256'])
        self.assertEqual(record['document']['deadline_unix'], DEADLINE)
        self.assertFalse(record['document']['wall_extended'])
        self.assertFalse(record['document']['historical_rows_changed'])
        self.assertEqual(journal.latest_checkpoint()['expected_sha256'], self.candidate['resume_state']['sha256'])
        self.assertTrue((self.root / 'records' / f'{index:020d}.intent.json').is_file())
        after = self.pins()
        self.assertTrue(all(after[name] == value for name, value in before.items()))
        self.assertEqual(len(after), len(before) + 2)

    def test_old_writer_still_holds_lock_refuses_no_record(self):
        before = self.pins()
        with self.assertRaises((BlockingIOError, ValueError)):
            self.reopen(close=False)
        self.assertEqual(before, self.pins())

    def test_duplicate_adoption_refuses_without_second_epoch_record(self):
        journal = self.reopen()
        journal.close()
        before = self.pins()
        with self.assertRaisesRegex(ValueError, 'no_work_before_C2_source_adoption'):
            self.reopen()
        self.assertEqual(before, self.pins())

    def test_wrong_saved_state_refuses(self):
        self.token['exact_complete']['resume_state']['sha256'] = '0' * 64
        self.save_token()
        before = self.pins()
        with self.assertRaisesRegex(ValueError, 'exact_resolved_C2_saved_state'):
            self.reopen()
        self.assertEqual(before, self.pins())

    def test_pending_tail_refuses_before_model(self):
        def fail(*arguments, **keywords):
            raise RuntimeError('synthetic-incomplete-generation')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=fail)
        before = self.pins()
        with self.assertRaisesRegex(ValueError, 'exact_resolved_C2_saved_state'):
            self.reopen()
        self.assertEqual(before, self.pins())

    def test_wrong_LEARN_or_selected_tail_refuses(self):
        self.token['exact_complete']['learn_sha256'] = '0' * 64
        self.save_token()
        with self.assertRaisesRegex(ValueError, 'same_C2_driver_LEARN_completion'):
            self.reopen()

    def test_new_INBOX_is_preserved_and_accepted(self):
        path = self.parent(name='new-parent.json', identifier='new-parent', text='New queued message.')
        self.journal.record('INBOX', dict(message=json.loads(path.read_bytes()), source_id=str(path),
            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        before = path.read_bytes()
        journal = self.reopen()
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(journal.read_inbox()), 2)

    def test_old_mailbox_rewrite_refuses(self):
        path = next(iter(self.candidate['mailbox']))
        Path(path).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'preserve_C2_original_parent_mailbox_bytes'):
            self.reopen()

    def test_alive_native_wrong_wall_or_corrupt_token_refuses(self):
        original = deepcopy(self.token)
        for key, value in (('old_native_exited', False), ('deadline_unix', DEADLINE + 1), ('sha256', '0' * 64)):
            self.token = deepcopy(original)
            self.token[key] = value
            if key == 'sha256':
                self.token_path.write_text(json.dumps(self.token))
            else:
                self.save_token()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'exact_exited_C2_handoff_token'):
                bind_journal(StreamJournal, self.plan)

    def test_no_cold_creation_or_changed_selection(self):
        wrapper = bind_journal(StreamJournal, self.plan)
        with self.assertRaisesRegex(ValueError, 'same_original_C2_journal_resume_only'):
            wrapper(self.root, create=True, checkpoint_tail=self.selection)
        with self.assertRaisesRegex(ValueError, 'same_original_C2_journal_resume_only'):
            wrapper(self.root, checkpoint_tail=dict(self.selection, persist_complete_anchors=False))

    def test_runtime_source_tamper_refuses(self):
        (self.source / RUNTIME).write_text('changed')
        with self.assertRaisesRegex(ValueError, 'exact_adopted_receiving_source_closure'):
            self.reopen()

    def test_port_changes_only_two_entry_lines_and_keeps_old_reader(self):
        original = (SOURCE / NATIVE).read_bytes()
        outputs = proposed_ports(SOURCE)
        added = b'    from gpu.c2_retention_runtime import bind_journal\n    StreamJournal = bind_journal(StreamJournal, plan)\n'
        self.assertEqual(outputs[NATIVE].count(added), 1)
        self.assertEqual(outputs[NATIVE].replace(added, b''), original)
        self.assertEqual(hashlib.sha256(original).hexdigest(), NATIVE_BEFORE)
        self.assertEqual(changes_for(SOURCE)[RUNTIME]['before'], None)
        for content in outputs.values():
            ast.parse(content)
        self.assertNotIn(b'r232_recovery', outputs[RUNTIME])
        self.assertNotIn(b'FrozenJournal', outputs[RUNTIME])
        self.assertNotIn(b'checkpoint_tail_runtime.py', outputs[RUNTIME])


if __name__ == '__main__':
    unittest.main()
