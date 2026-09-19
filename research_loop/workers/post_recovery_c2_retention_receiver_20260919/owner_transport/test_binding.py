"""Synthetic exact post-LOADED journal/intent/source checks, never /proc of a life."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import common as core
import c2_owner_binding as binding_api
from common import DEADLINE, digest, read, reference, sha, write_once


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / 'life'
        (self.root / 'stream/records').mkdir(parents=True)
        self.source = self.directory / 'source'
        (self.source / 'gpu').mkdir(parents=True)
        original = core.HERE.parent / 'prepared_epoch4_v5/C2/epoch4/source/gpu/r188_node5_confinement.py'
        (self.source / 'gpu/r188_node5_confinement.py').write_bytes(original.read_bytes())
        self.pins = {'gpu/r188_node5_confinement.py': sha(self.source / 'gpu/r188_node5_confinement.py')}
        self.guard_path = self.directory / 'GUARD.json'
        self.actor = dict(pid=999, uid=2524, start_ticks='20', boot_id='boot', state='R', ppid=998,
            argv=['python', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(self.guard_path)], cwd=str(self.source))
        self.addCleanup(patch.stopall)
        patch.object(binding_api, 'ROOT', str(self.root)).start()
        patch.object(binding_api, 'process_identity', side_effect=lambda process: deepcopy(self.actor)).start()
        patch.object(binding_api.time, 'time', return_value=DEADLINE - 1000).start()
        checkpoint = dict(optimizer_steps=8588)
        state = dict(deadline_unix=DEADLINE)
        self.saved = dict(state=state, sha256=digest(state))
        self.previous = '0' * 64
        complete = self.record(3, 'SLEEP_COMPLETE', dict(resume_state=self.saved, checkpoint=checkpoint))
        learned = self.record(4, 'R184_LEARN_COMPLETE', dict(checkpoint=checkpoint))
        plan = dict(source_root=str(self.source), root=str(self.root), hard_end_unix=DEADLINE,
            physical=1, gpu_uuid='GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c',
            think_act_learn=dict(trial_id='C2_R216_current_conversation_maintenance'))
        write_once(self.directory / 'PLAN.json', plan)
        guard = dict(plan_path=str(self.directory / 'PLAN.json'), plan_sha256=sha(self.directory / 'PLAN.json'),
            copy_raw=str(self.root), source_pins=self.pins, resume=True)
        write_once(self.guard_path, guard)
        candidate = dict(complete_index=3, complete_sha256=complete['sha256'], resume_state=self.saved,
            records=[complete, learned], checkpoint=checkpoint)
        self.token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', old_native_exited=True, old_pid=777,
            deadline_unix=DEADLINE, epoch_id='C2-epoch4', life_binding_sha256='b' * 64, new_source_pins=self.pins,
            exact_complete=candidate, receiver=dict(dispatcher_module='gpu.r188_node5_confinement',
                same_journal_root=str(self.root / 'stream'), guard_path=str(self.guard_path), plan=plan, plan_sha256=digest(plan),
                artifact_pins={str(self.guard_path): sha(self.guard_path), str(self.directory / 'PLAN.json'): sha(self.directory / 'PLAN.json')}))
        self.token['sha256'] = digest(self.token)
        handoff = write_once(self.directory / 'HANDOFF.json', self.token)
        self.adopted = self.record(5, 'RETENTION_SOURCE_ADOPTED', dict(handoff_sha256=self.token['sha256'],
            source_pins_sha256=digest(self.pins), epoch_id='C2-epoch4', deadline_unix=DEADLINE, wall_extended=False))
        self.loaded = self.record(6, 'LOADED', dict(pid=999, resume=True, optimizer_steps=8588))
        self.binding = dict(schema='C2_POST_LOADED_OWNER_BINDING_V1', deadline_unix=DEADLINE, handoff=handoff,
            source_epoch='C2-epoch4', life_binding_sha256='b' * 64, native=deepcopy(self.actor),
            loaded=dict(index=6, sha256=self.loaded['sha256']))
        self.reference = write_once(self.directory / 'BINDING.json', self.binding)

    def record(self, index, kind, document):
        value = dict(schema='R125_STREAM_JOURNAL_V1', journal_id=core.JOURNAL, index=index, kind=kind,
            document=document, previous_sha256=self.previous)
        value['sha256'] = digest(value)
        self.previous = value['sha256']
        write_once(self.root / 'stream/records' / f'{index:020d}.json', value)
        write_once(self.root / 'stream/records' / f'{index:020d}.intent.json', dict(schema=value['schema'], journal_id=core.JOURNAL,
            index=index, previous_sha256=value['previous_sha256'], record_sha256=value['sha256']))
        return value

    def verify(self):
        return binding_api.verify(self.reference['path'], self.reference['sha256'])

    def test_authentic_LOADED_and_adoption_verified_readonly(self):
        before = {str(path): sha(path) for path in self.directory.rglob('*') if path.is_file()}
        result = self.verify()
        self.assertEqual(result['schema'], 'C2_ACTUAL_POST_LOADED_REBIND_VERIFIED_V1')
        self.assertEqual(result['native_signals'], 0)
        self.assertEqual(before, {str(path): sha(path) for path in self.directory.rglob('*') if path.is_file()})

    def test_pid_reuse_refused(self):
        self.actor['start_ticks'] = '21'
        with self.assertRaises(ValueError):
            self.verify()

    def test_stopped_native_refused(self):
        self.actor['state'] = 'T'
        with self.assertRaises(ValueError):
            self.verify()

    def test_scheduler_state_change_does_not_change_incarnation(self):
        first = deepcopy(self.actor)
        second = dict(first, state='S')
        with patch.object(binding_api, 'process_identity', side_effect=[first, second]):
            self.verify()

    def test_intent_tamper_refused(self):
        (self.root / 'stream/records/00000000000000000005.intent.json').write_text('{}')
        with self.assertRaises(ValueError):
            self.verify()

    def test_missing_adoption_refused(self):
        (self.root / 'stream/records/00000000000000000005.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify()

    def test_source_tamper_refused(self):
        (self.source / 'gpu/r188_node5_confinement.py').write_text('changed')
        with self.assertRaises(ValueError):
            self.verify()

    def test_guard_copy_root_edit_refused(self):
        guard = read(self.guard_path)
        guard['copy_raw'] += '-clone'
        self.guard_path.write_text(json.dumps(guard))
        with self.assertRaises(ValueError):
            self.verify()

    def drain_fixture(self):
        write_once(self.root / 'stream/JOURNAL.json', dict(journal_id=core.JOURNAL))
        inbox = self.root / 'stream/inbox'
        inbox.mkdir()
        message = dict(id='synthetic-parent', actor='parent', text='synthetic CPU test only')
        source = inbox / 'message.json'
        write_once(source, message)
        consumed = self.record(7, 'INBOX', dict(message=message, source_id=str(source), source_sha256=sha(source)))
        life = dict(pid=self.actor['pid'], uid=self.actor['uid'], start_ticks=self.actor['start_ticks'],
            boot_id=self.actor['boot_id'], command=self.actor['argv'], guard_path=str(self.guard_path),
            guard_sha256=sha(self.guard_path), journal_root=str(self.root / 'stream'),
            journal_id=core.JOURNAL, hard_end_unix=DEADLINE)
        inventory = dict(publications=[dict(publication=dict(id=message['id']),
            consumption=dict(record_index=7, record_sha256=consumed['sha256']))])
        return dict(old_life=life), inventory, source

    def test_drain_verifies_actual_INBOX_record_intent_and_mailbox(self):
        plan, inventory, source = self.drain_fixture()
        result = binding_api.drain(plan, inventory)
        self.assertEqual(result['inventory_sha256'], digest(inventory))
        self.assertEqual(result['native_signals'], 0)
        self.assertEqual(result['journal_writes'], 0)

    def test_drain_rejects_changed_mailbox_bytes(self):
        plan, inventory, source = self.drain_fixture()
        source.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'mailbox_bytes'):
            binding_api.drain(plan, inventory)

    def test_drain_rejects_delivery_receipt_for_non_INBOX_record(self):
        plan, inventory, source = self.drain_fixture()
        inventory['publications'][0]['consumption'] = dict(record_index=6, record_sha256=self.loaded['sha256'])
        with self.assertRaisesRegex(ValueError, 'consumed_publication'):
            binding_api.drain(plan, inventory)


if __name__ == '__main__':
    unittest.main(verbosity=2)
