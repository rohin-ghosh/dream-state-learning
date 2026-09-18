"""Independent local CPU regressions; all custody/receipts below are synthetic.

No receiver attestation is manufactured by these tests. No main entrypoint,
model, provider, remote wrapper, real witness, or sealed result is invoked.
"""

from contextlib import ExitStack
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

import prep_common as common
import r172_runner as runner
import r172_scheduler as scheduler
import transfer
from gpu import orch_r130_checkpoint_benchmark as checkpoint_engine


class ForwardReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='r172-review-synthetic-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.now = common.END - 12000
        self.stack.enter_context(patch.object(common.time, 'time', return_value=self.now))

    def bind(self, name, document):
        return common.write(self.root / name, document)

    def ledger(self, limit=100):
        return common.Ledger(self.root / 'read-ledger', dict(metadata=limit,
            adapter=limit, per_life=limit, discovery=limit), ['life'])

    def cell_fixture(self):
        self.stack.enter_context(patch.object(runner, 'ROOT', self.root))
        life_root = self.root / 'lives/life'
        capture_root = life_root / 'captures/000011'
        birth_source = self.bind('original-birth.json', dict(system_prompt='synthetic system',
            birth_prompt='synthetic birth'))
        context = common.read(birth_source['path'])
        source = self.root / 'synthetic-original-source'
        plan = dict(life_id='life', source_root=str(source), sleep_count=3,
            first_sleep=11, frozen_unix=self.now - 100, birth_plan=birth_source,
            metadata_read_cap=1000000, adapter_read_cap=1000000,
            source_authority=self.bind('authority.json', dict(synthetic=True)))
        plan_ref = self.bind('life-plan.json', plan)
        registration = self.bind('lives/life/REGISTERED.json', dict(plan=plan_ref))
        self.stack.enter_context(patch.object(runner.prior.queue, 'initialized',
            return_value=(plan, life_root, source, {})))
        adapter_files = {}
        for name, raw in {'adapter_model.safetensors': b'synthetic adapter',
                'adapter_config.json': b'{}'}.items():
            reference = common.write(capture_root / 'adapter' / name, raw)
            adapter_files[name] = reference['sha256']
        commit = dict(schema=checkpoint_engine.NATIVE_SCHEMA, base_sha256=runner.prior.queue.BASE,
            adapter_state_sha256='a' * 64, adapter_files=adapter_files,
            checkpoint_sha256=dict(adapter=runner.prior.protocol.digest(adapter_files)),
            optimizer_steps=1, created_unix=self.now - 50)
        commit_ref = common.write(capture_root / 'COMMIT.original.json', commit)
        manifest = common.write(capture_root / 'MANIFEST.json', dict(schema='R130_CHECKPOINT_MANIFEST_V1',
            adapter_path='adapter', commit_path='COMMIT.original.json', commit_sha256=commit_ref['sha256']))
        boundary = common.write(capture_root / 'BOUNDARY.json', dict(life_id='life', sleep=11,
            source_root=str(source), birth_plan=birth_source, source_authority=plan['source_authority'],
            context_sha256=runner.prior.protocol.digest(context), commit=commit_ref))
        birth = common.write(capture_root / 'BIRTH.private.json', context)
        capture = common.write(capture_root / 'COMPLETE.json', dict(manifest=manifest,
            boundary=boundary, birth=birth, observed_unix=self.now - 10))
        transferred = self.bind('transfer.json', dict(status='EXACT_RECEIVING_COPY_VERIFIED',
            capture=capture, life_id='life', sleep=11, proposal_sha256=common.PROPOSAL_SHA))
        pipeline = self.bind('pipeline.json', dict(schema='R172_PREPARED_ROLLING_CAMPAIGN_V1',
            proposal_sha256=common.PROPOSAL_SHA, call_cap=576, token_cap=294912,
            absolute_end_unix=common.END, lives=[dict(life_id='life', proposed_storage_root=str(source)),
                *[dict(life_id=f'peer_{index}', proposed_storage_root=f'/synthetic/peer_{index}')
                    for index in range(23)]]))
        evidence = self.bind('synthetic-witness.json', dict(synthetic=True))
        witness = self.bind('witness-freeze.json', dict(status='PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE',
            model_calls=0, frozen_unix=self.now - 20, evidence=evidence))
        rubric = self.bind('rubric.json', dict(methods=runner.prior.METHODS,
            parent_access=False, provider_calls=0))
        source_freeze = self.bind('source-freeze.json', dict(files={
            'r172_runner.py': common.ref(HERE / 'r172_runner.py')['sha256']}))
        cpu = self.bind('synthetic-cpu-gate.json', dict(status='ACTUAL_RECEIVING_CPU_PASS',
            source_freeze=source_freeze, synthetic_not_a_real_attestation=True))
        lease = self.bind('lease.json', dict(uuid_by_index={'0': 'SYNTHETIC_GPU_UUID'},
            lease_end_unix=common.END + 21601))
        service = self.bind('synthetic-service.py', b'pass\n')
        config = dict(schema=runner.SCHEMA, root=str(self.root), pipeline=pipeline, life_id='life',
            physical=0, condition='LORA_ON', registration=registration, sleep=11,
            capture=capture, transfer=transferred, TRAIN_freeze=witness, rubric=rubric,
            source_root=str(HERE), source_freeze=source_freeze, cpu_gate=cpu, lease=lease,
            gpu_uuid='SYNTHETIC_GPU_UUID', python=sys.executable,
            python_sha256=hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
            service_path=service['path'], service_sha256=service['sha256'])
        config_ref = self.bind('config.json', config)
        return Path(config_ref['path']), capture_root, config

    def reservation(self, condition='LORA_ON', sleep=11, capture_hash='a' * 64):
        return dict(life_id='life', sleep=sleep, condition=condition,
            physical=0 if condition == 'LORA_ON' else 1,
            pipeline=dict(path='synthetic-pipeline', sha256='p' * 64),
            capture=dict(path='synthetic-capture', sha256=capture_hash),
            execution_ref=dict(path='synthetic-config', sha256='c' * 64))

    def ready_transfer(self, name, sleep, ready):
        self.bind(f'receiving_transfers/{name}_{sleep:06d}/COMPLETE.json',
            dict(life_id=name, sleep=sleep, observed_unix=ready,
                capture=dict(path='synthetic-capture', sha256='a' * 64)))

    def partial_archive(self, sleep=11):
        name = f'lives/life/captures/{sleep:06d}/COMPLETE.json'
        raw = common.canonical(dict(manifest=dict(path='absent-manifest.json', sha256='a' * 64)))
        header = dict(schema=transfer.SCHEMA, life_id='life', sleep=sleep,
            proposal_sha256=common.PROPOSAL_SHA, private_evaluator_only=True,
            files=[dict(name=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())],
            capture=dict(path=str(self.root / name), sha256=hashlib.sha256(raw).hexdigest()))
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as archive:
            for filename, payload in {'TRANSFER_HEADER.json': common.canonical(header), name: raw}.items():
                member = tarfile.TarInfo(filename)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        stream.seek(0)
        return stream

    def test_runner_checkpoint_has_frozen_generator_required_fields(self):
        config_path, capture_root, config = self.cell_fixture()
        validated = runner.validate_cell(config_path)[2]
        self.assertTrue({'adapter_files', 'adapter_state_sha256', 'base_sha256'} <= set(validated),
            'Frozen generator snapshot needs the full verified checkpoint, not just three paths/hashes')

    def test_changed_adapter_is_rejected_before_model_load(self):
        config_path, capture_root, config = self.cell_fixture()
        (capture_root / 'adapter/adapter_model.safetensors').write_bytes(b'changed after receiving copy')
        with self.assertRaises(ValueError):
            runner.validate_cell(config_path)

    def test_frozen_cpu_checkpoint_verifier_accepts_complete_synthetic_join(self):
        config_path, capture_root, config = self.cell_fixture()
        manifest = common.read(capture_root / 'MANIFEST.json')
        verified = checkpoint_engine.verify_checkpoint(manifest, capture_root)
        self.assertEqual(verified['adapter_state_sha256'], 'a' * 64)
        (capture_root / 'adapter/adapter_model.safetensors').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'native_adapter_file_binding'):
            checkpoint_engine.verify_checkpoint(manifest, capture_root)

    def test_missing_model_source_closure_is_rejected(self):
        config_path, capture_root, config = self.cell_fixture()
        self.assertNotIn('gpu/orch_r167_fleet_eval.py', common.bound(config['source_freeze'])['files'])
        with self.assertRaises(ValueError):
            runner.validate_cell(config_path)

    def test_actual_receiving_lease_array_schema_is_supported(self):
        config_path, capture_root, config = self.cell_fixture()
        lease = self.bind('receiving-format-lease.json', dict(node='ovx',
            uuid_by_index=['SYNTHETIC_GPU_UUID', 'SYNTHETIC_SECOND_UUID'],
            lease_end_unix=common.END + 21601, hard_deadline_unix=common.END + 1))
        replacement = self.bind('receiving-format-config.json', dict(config, lease=lease))
        runner.validate_cell(replacement['path'])

    def test_source_export_charges_every_metadata_reread(self):
        config_path, capture_root, config = self.cell_fixture()
        life_root = self.root / 'lives/life'
        self.stack.enter_context(patch.object(transfer, 'ROOT', self.root))
        self.bind('lives/life/TRAIN_FREEZE.json', dict(synthetic=True))
        self.bind('lives/life/TRAIN_WITNESSES.private.json', dict(synthetic=True))
        for name in ('QUEUE_PLAN.json', 'MAIN_SOURCE_READ_COPY_GO.json', 'FRESH_CUSTODY.json'):
            self.bind(f'source_controls/life/{name}', dict(synthetic=True))
        files = [path for path in capture_root.rglob('*') if path.is_file()]
        files.extend(life_root / name for name in
            ('REGISTERED.json', 'TRAIN_FREEZE.json', 'TRAIN_WITNESSES.private.json'))
        files.extend(self.root / 'source_controls/life' / name for name in
            ('QUEUE_PLAN.json', 'MAIN_SOURCE_READ_COPY_GO.json', 'FRESH_CUSTODY.json'))
        metadata_paths = {path for path in files if path.parent != capture_root / 'adapter'}
        original = Path.read_bytes
        metadata_reads = []

        def counted_read(path):
            raw = original(path)
            if path in metadata_paths:
                metadata_reads.append(len(raw))
            return raw

        with patch.object(Path, 'read_bytes', counted_read):
            transfer.export('life', 11, io.BytesIO())
        charged = runner.prior.queue.read_totals(life_root)['metadata']
        self.assertLessEqual(sum(metadata_reads), charged,
            'COMMIT pre-read and COMPLETE hash reread also require charges')

    def test_forward_queue_does_not_wait_for_baselines_or_peers(self):
        self.ready_transfer('life', 11, 10)
        result = scheduler.candidates(self.root, 'LORA_ON')
        self.assertEqual([(row['life_id'], row['sleep']) for row in result], [('life', 11)])
        self.assertFalse((self.root / 'baseline_authorities').exists())

    def test_oldest_ready_sleep_precedes_out_of_order_transfer_arrival(self):
        self.ready_transfer('life', 11, 20)
        self.ready_transfer('life', 12, 10)
        self.assertEqual(scheduler.candidates(self.root, 'LORA_ON')[0]['sleep'], 11)

    def test_consumed_condition_does_not_retry_or_block_companion(self):
        self.ready_transfer('life', 11, 10)
        key = runner.prior.queue.key('life', 11, 'LORA_ON')
        self.bind(f'scheduler_once/{key}.json', dict(status='SYNTHETIC_UNCERTAIN'))
        self.assertEqual(scheduler.candidates(self.root, 'LORA_ON'), [])
        self.assertEqual(len(scheduler.candidates(self.root, 'LORA_OFF')), 1)

    def test_reservation_rejects_changed_on_off_capture(self):
        runner.reserve(self.root, self.reservation(), common.END + 21601, self.now)
        with self.assertRaises(ValueError):
            runner.reserve(self.root, self.reservation('LORA_OFF', capture_hash='b' * 64),
                common.END + 21601, self.now + 1)

    def test_execution_reservation_is_nonrefundable_and_cannot_slide_wall(self):
        config = self.reservation()
        reference = runner.reserve(self.root, config, common.END + 21601, self.now)
        self.assertEqual(common.bound(reference)['calls_charged'], 3)
        self.assertEqual(common.bound(reference)['tokens_charged'], 1536)
        with self.assertRaisesRegex(ValueError, 'once_only'):
            runner.reserve(self.root, config, common.END + 21601, self.now + 1)
        with self.assertRaisesRegex(ValueError, 'non_sliding_window'):
            runner.reserve(self.root, self.reservation(sleep=12), common.END + 21601,
                common.END - 915)

    def test_charge_precedes_read_and_failed_parse_keeps_charge(self):
        source = self.root / 'malformed.json'
        source.write_bytes(b'not json')
        ledger = self.ledger()
        reader = common.Reader(ledger, 'life', 'read-once', [source])
        with self.assertRaises(ValueError):
            reader.document(source)
        self.assertEqual(ledger.totals()['metadata'], 8)
        with self.assertRaisesRegex(ValueError, 'consumed'):
            common.Reader(ledger, 'life', 'read-once', [source]).raw(source)

    def test_budget_refusal_prevents_data_read(self):
        source = self.root / 'too-large'
        source.write_bytes(b'12')
        reader = common.Reader(self.ledger(limit=1), 'life', 'refused', [source])
        with self.assertRaisesRegex(ValueError, 'aggregate_read_budget'):
            reader.raw(source)
        self.assertEqual(reader.bytes, 0)

    def test_growth_during_read_never_exceeds_precharged_bytes(self):
        source = self.root / 'growing'
        source.write_bytes(b'abc')
        ledger = self.ledger()
        reader = common.Reader(ledger, 'life', 'growing-once', [source])
        original = ledger.reserve

        def grow_after_reservation(*arguments, **keywords):
            reference = original(*arguments, **keywords)
            source.write_bytes(b'abcd')
            return reference

        with patch.object(ledger, 'reserve', side_effect=grow_after_reservation):
            with self.assertRaisesRegex(ValueError, 'source_changed_during_read'):
                reader.raw(source)
        self.assertLessEqual(reader.bytes, ledger.totals()['metadata'],
            'Failure detection must not leave bytes actually read uncharged')

    def test_incomplete_transfer_cannot_claim_verified_receiving_copy(self):
        self.bind('control/PROPOSAL.json', dict(lives=[dict(life_id='life')]))
        with self.assertRaises((ValueError, FileNotFoundError)):
            transfer.receive(self.partial_archive(), self.root)

    def test_source_reader_rejects_symlink_and_outside_allowlist(self):
        source = self.root / 'source'
        source.write_bytes(b'synthetic')
        link = self.root / 'link'
        link.symlink_to(source)
        reader = common.Reader(self.ledger(), 'life', 'unsafe', [link])
        with self.assertRaisesRegex(ValueError, 'non_symlink'):
            reader.raw(link)
        with self.assertRaisesRegex(ValueError, 'allowlist'):
            reader.raw(source)

    def test_preparation_scope_does_not_satisfy_execution_go(self):
        scope = common.read(HERE / 'PREPARATION_SCOPE.json')
        reference = self.bind('not-execution-go.json', scope)
        with self.assertRaisesRegex(ValueError, 'preparation_scope_is_not_execution_GO'):
            runner.validate_go(reference['path'], {}, {}, {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
