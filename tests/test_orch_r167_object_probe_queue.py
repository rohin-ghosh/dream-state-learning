import copy
import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu import orch_r167_object_probe_queue as queue


protocol = queue.protocol


class QueueTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source/life'
        self.source.mkdir(parents=True)
        self.records = self.source / 'stream/records'
        self.records.mkdir(parents=True)
        self.context = dict(system_prompt='Help.', birth_prompt='Begin.')
        self.birth = self.root / 'external_rollout/PLAN.json'
        self.birth.parent.mkdir()
        protocol.write(self.birth, self.context)
        self.manifest = dict(schema='TEST_JOURNAL', journal_id='life')
        self.journal = self.source / 'stream/JOURNAL.json'
        protocol.write(self.journal, self.manifest)
        self.identity = dict(pid=1, start_ticks='2', boot_id='boot')
        self.observation = self.root / 'observation.json'
        protocol.write(self.observation, dict(status='IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED',
            source_root=str(self.source), life_id='life', last_completed_sleep=0,
            observed_unix=time.time() - 20, native_identity=self.identity))
        self.plan = dict(schema=queue.SCHEMA, queue_root=str(self.root / 'custody'), life_id='life',
            source_root=str(self.source), birth_plan=protocol.ref(self.birth), journal=protocol.ref(self.journal),
            first_sleep=1, sleep_count=3, frozen_unix=time.time() - 10, probes=list(queue.PROBES),
            conditions=list(queue.CONDITIONS), base_sha256=queue.BASE, model_call_cap=24,
            generated_token_cap=12288, metadata_read_cap=10**7, adapter_read_cap=10**7)
        self.authority = self.root / 'authority.json'
        self.authority_doc = dict(schema=queue.SCHEMA, status='MAIN_SOURCE_READ_COPY_GO', life_id='life',
            source_root=str(self.source), birth_plan=self.plan['birth_plan'], journal=self.plan['journal'],
            milestones=[0, 1, 2, 3], metadata_read_cap=10**7, adapter_read_cap=10**7,
            registration_observation=protocol.ref(self.observation), frozen_unix=self.plan['frozen_unix'],
            permissions=['metadata_discovery', 'adapter_only_copy'], read_end_unix=time.time() + 300)
        protocol.write(self.authority, self.authority_doc)
        self.plan['source_authority'] = protocol.ref(self.authority)
        self.plan_path = self.root / 'plan.json'
        protocol.write(self.plan_path, self.plan)
        self.previous = protocol.digest(self.manifest)
        self.record_index = 0

    def rewrite_plan(self):
        self.plan_path.write_text(json.dumps(self.plan))

    def rewrite_authority(self):
        self.authority.write_text(json.dumps(self.authority_doc))
        self.plan['source_authority'] = protocol.ref(self.authority)
        self.rewrite_plan()

    def commit(self, sleep, publish=True):
        path = queue.checkpoint_path(self.source, sleep)
        (path.parent / 'adapter').mkdir(parents=True)
        files = {name: protocol.write(path.parent / 'adapter' / name, raw)['sha256'] for name, raw in
            [('adapter_model.safetensors', b'adapter'), ('adapter_config.json', b'{}')]}
        document = dict(schema='R125_NATIVE_CONTINUITY_V1', base_sha256=queue.BASE,
            adapter_path=str(path.parent / 'adapter'), adapter_files=files,
            checkpoint_sha256=dict(adapter=protocol.digest(files), model='unchanged'),
            created_unix=time.time() - 5, optimizer_steps=sleep)
        if publish:
            protocol.write(path, document)
        return document

    def record(self, sleep, commit):
        state = dict(history=dict(self.context, events=[]), rows=[] if sleep == 0 else [dict(split='TRAIN')],
            model_state_sha256=protocol.digest(commit['checkpoint_sha256']))
        if sleep == 0:
            body = dict(state=dict(state=state, sha256=protocol.digest(state)))
            kind = 'INITIAL'
        else:
            body = dict(cycle=sleep, checkpoint=commit, status='COMPLETE')
            state.update(sleep_receipts=[{}] * (sleep - 1) + [copy.deepcopy(body)], sleep_frontier=1)
            body['resume_state'] = dict(state=state, sha256=protocol.digest(state))
            kind = 'SLEEP_COMPLETE'
        record = dict(self.manifest, index=self.record_index, previous_sha256=self.previous, kind=kind, document=body)
        record['sha256'] = protocol.digest(record)
        intent = dict(self.manifest, index=self.record_index, previous_sha256=self.previous, record_sha256=record['sha256'])
        protocol.write(self.records / f'{self.record_index:020d}.json', record)
        protocol.write(self.records / f'{self.record_index:020d}.intent.json', intent)
        self.record_index += 1
        self.previous = record['sha256']

    def ready(self):
        self.record(0, self.commit(0))
        self.record(1, self.commit(1))
        queue.initialize(self.plan_path)
        queue.discover(self.plan_path)

    def batch(self, count=21):
        lives = [dict(life_id=f'life{index}', node='node', storage_root=str(self.root / f'sources/{index}/life'),
            process_plan_root=str(self.root / f'sources/{index}/life'), birth_plan=protocol.ref(self.birth),
            inventory_identity=self.identity, inventory_observed_unix=time.time() - 100,
            inventory_evidence=[], hold='FRESH_IDENTITY_CUSTODY_REQUIRED') for index in range(count)]
        document = dict(schema=queue.BATCH_SCHEMA, queue_root=str(self.root / 'batch'), frozen_unix=time.time() - 30,
            lives=lives, unverified_coverage=[dict(life_id='missing', status='UNKNOWN_NOT_NEGATIVE')],
            probes=list(queue.PROBES), conditions=list(queue.CONDITIONS), future_sleeps=3,
            model_call_cap=count * 24, generated_token_cap=count * 24 * 512, physical_slots=[0, 1],
            not_before_unix=time.time() + 100, hard_end_unix=time.time() + 20000,
            lease_deadline_unix=time.time() + 30000, adapter_copy_cap=16 * 1024**3,
            metadata_read_cap=8 * 1024**3, resource_evidence=[], visibility='PRIVATE_EVALUATOR_ONLY_METADATA_TO_PARENTS')
        path = self.root / 'batch.json'
        protocol.write(path, document)
        return path, document

    def test_external_birth_explicitly_bound_and_immutable_capture(self):
        self.ready()
        result = queue.capture(self.plan_path, 1)
        self.assertEqual(result['model_calls'], 0)
        root = Path(self.plan['queue_root'])
        self.assertEqual((root / 'captures/000001/adapter/adapter_model.safetensors').read_bytes(), b'adapter')
        self.assertEqual(queue.status(self.plan_path)['condition_proposals'], 2)
        self.assertFalse((self.source / 'queue.lock').exists())
        with self.assertRaises(ValueError):
            queue.capture(self.plan_path, 1)

    def test_incremental_discovery_dedupes_and_preserves_missing(self):
        self.ready()
        self.assertEqual(queue.discover(self.plan_path)['added'], 0)
        result = queue.status(self.plan_path)
        self.assertEqual(result['bound_checkpoints'], 2)
        self.assertEqual(result['missing_or_unobserved_checkpoints'], 4)

    def test_discovery_chunks_preserve_cursor_and_initial_capture(self):
        self.record(0, self.commit(0))
        self.record(1, self.commit(1))
        queue.initialize(self.plan_path)
        result = queue.discover(self.plan_path, max_records=1)
        self.assertEqual(result['verified_through_index'], 0)
        queue.capture(self.plan_path, 0)
        self.assertEqual(queue.status(self.plan_path)['captured_checkpoints'], 1)
        result = queue.discover(self.plan_path, max_records=1)
        self.assertEqual(result['verified_through_index'], 1)
        self.assertEqual(queue.status(self.plan_path)['bound_checkpoints'], 2)

    def test_discovery_rejects_unbounded_chunks(self):
        for amount in (0, 257, True, -1):
            with self.subTest(amount=amount), self.assertRaisesRegex(ValueError, 'bounded_discovery_chunk'):
                queue.discover(self.plan_path, max_records=amount)

    def test_orphan_commit_not_completed_boundary(self):
        self.record(0, self.commit(0))
        self.commit(1)
        queue.initialize(self.plan_path)
        self.assertEqual(queue.discover(self.plan_path)['added'], 1)
        with self.assertRaises(ValueError):
            queue.capture(self.plan_path, 1)

    def test_missing_commit_later_visible_retains_verified_witness(self):
        self.record(0, self.commit(0))
        pending = self.commit(1, publish=False)
        self.record(1, pending)
        queue.initialize(self.plan_path)
        self.assertEqual(queue.discover(self.plan_path)['added'], 1)
        protocol.write(queue.checkpoint_path(self.source, 1), pending)
        self.assertEqual(queue.discover(self.plan_path)['added'], 1)

    def test_changed_pending_witness_rejected(self):
        self.record(0, self.commit(0))
        self.record(1, self.commit(1, publish=False))
        queue.initialize(self.plan_path)
        queue.discover(self.plan_path)
        path = self.records / '00000000000000000001.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            queue.discover(self.plan_path)

    def test_changed_adapter_copy_preserved_no_ready_proposal(self):
        self.ready()
        (queue.checkpoint_path(self.source, 1).parent / 'adapter/adapter_model.safetensors').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            queue.capture(self.plan_path, 1)
        self.assertTrue((Path(self.plan['queue_root']) / 'captures/000001/FAILED.json').exists())
        self.assertEqual(queue.status(self.plan_path)['condition_proposals'], 0)

    def test_wrong_source_checkpoint_rejected(self):
        commit = self.commit(1)
        commit['adapter_path'] = str(self.root / 'wrong/adapter')
        with self.assertRaises(ValueError):
            queue.checkpoint(commit, self.source, 1)

    def test_old_sleep_cannot_be_relabelled_prospective(self):
        self.record(0, self.commit(0))
        commit = self.commit(1, publish=False)
        commit['created_unix'] = self.plan['frozen_unix']
        protocol.write(queue.checkpoint_path(self.source, 1), commit)
        self.record(1, commit)
        queue.initialize(self.plan_path)
        with self.assertRaises(ValueError):
            queue.discover(self.plan_path)

    def test_authority_expiry_and_changed_hash_reject(self):
        self.authority_doc['read_end_unix'] = time.time() - 1
        self.rewrite_authority()
        with self.assertRaises(ValueError):
            queue.load(self.plan_path, True)
        self.authority.write_bytes(b'{}')
        with self.assertRaises(ValueError):
            queue.load(self.plan_path)

    def test_reader_disallows_held_optimizer_and_external_unbound_file(self):
        queue.initialize(self.plan_path)
        for name in ('HELD.json', 'optimizer.pt', 'elsewhere/PLAN.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                queue.Reader(self.plan, Path(self.plan['queue_root']), self.source, [self.source / name], 'metadata')

    def test_read_cap_charged_before_failed_copy(self):
        self.ready()
        root = Path(self.plan['queue_root'])
        protocol.write(root / 'reads/full.json', dict(kind='adapter', reserved_bytes=self.plan['adapter_read_cap']))
        with self.assertRaises(ValueError):
            queue.capture(self.plan_path, 1)

    def test_symlink_and_prompt_change_rejected(self):
        link = self.root / 'linked'
        link.symlink_to(self.source)
        self.plan['source_root'] = str(link)
        self.rewrite_plan()
        with self.assertRaises(ValueError):
            queue.load(self.plan_path)
        self.plan['probes'][0] = 'new prompt'
        self.rewrite_plan()
        with self.assertRaises(ValueError):
            queue.load(self.plan_path)

    def test_fleet_registers_all_21_and_no_model_calls(self):
        path, _ = self.batch()
        result = queue.batch_initialize(path)
        self.assertEqual((result['lives'], result['registered_checkpoints'], result['condition_slots']), (21, 84, 168))
        self.assertEqual((result['model_call_cap'], result['generated_token_cap']), (504, 258048))
        self.assertEqual((result['captured_checkpoints'], result['model_calls']), (0, 0))
        self.assertEqual(result['unverified_coverage'][0]['status'], 'UNKNOWN_NOT_NEGATIVE')

    def test_fleet_no_cap_increase_or_duplicate_identity(self):
        path, document = self.batch()
        document['model_call_cap'] += 6
        path.write_text(json.dumps(document))
        with self.assertRaises(ValueError):
            queue.load_batch(path)
        document['model_call_cap'] -= 6
        document['lives'][1]['storage_root'] = document['lives'][0]['storage_root']
        path.write_text(json.dumps(document))
        with self.assertRaises(ValueError):
            queue.load_batch(path)

    def test_fleet_deadline_cannot_extend_lease(self):
        path, document = self.batch()
        document['hard_end_unix'] = document['lease_deadline_unix'] + 1
        path.write_text(json.dumps(document))
        with self.assertRaises(ValueError):
            queue.load_batch(path)

    def test_fleet_binds_exact_next_three_before_source_read(self):
        path, document = self.batch(1)
        document['lives'][0].update(life_id='life', storage_root=str(self.source), process_plan_root=str(self.source))
        path.write_text(json.dumps(document))
        self.plan['queue_root'] = str(Path(document['queue_root']) / 'lives/life')
        self.rewrite_plan()
        queue.batch_initialize(path)
        self.assertEqual(queue.batch_bind(path, self.plan_path)['model_calls'], 0)
        self.assertEqual(queue.read_totals(Path(self.plan['queue_root'])), dict(metadata=0, adapter=0))
        with self.assertRaises(ValueError):
            queue.batch_bind(path, self.plan_path)

    def test_C5_recovery_hold_requires_new_exact_release(self):
        path, document = self.batch(1)
        document['lives'][0].update(life_id='life', storage_root=str(self.source), process_plan_root=str(self.source),
                                  hold='RECOVERY_COMMIT_REQUIRED')
        path.write_text(json.dumps(document))
        self.plan['queue_root'] = str(Path(document['queue_root']) / 'lives/life')
        self.rewrite_plan()
        queue.batch_initialize(path)
        with self.assertRaises(KeyError):
            queue.batch_bind(path, self.plan_path)

    def test_batch_registry_cannot_be_edited_after_registration(self):
        path, document = self.batch()
        queue.batch_initialize(path)
        document['lives'][0]['hold'] = 'RECOVERY_COMMIT_REQUIRED'
        path.write_text(json.dumps(document))
        with self.assertRaises(ValueError):
            queue.batch_status(path)


if __name__ == '__main__':
    unittest.main()
