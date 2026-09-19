"""Synthetic journal/state-machine tests, never actual model recovery evidence."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu import orch_r145_node3_pending_recovery as recovery
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


CAPTURES = Path(__file__).resolve().parents[1] / 'research_loop/workers/r144_node3_targets_20260916t1515z_operator2'


class Tensor:
    def __init__(self, value):
        self.value = value

    def clone(self):
        return Tensor(self.value)

    def tolist(self):
        return [self.value]


class AdamW:
    def __init__(self):
        self.state = {'state': {'weight': {'step': 0, 'momentum': 1.25}}}

    def state_dict(self):
        return deepcopy(self.state)

    def load_state_dict(self, state):
        self.state = deepcopy(state)


class Torch:
    Tensor = Tensor
    optim = SimpleNamespace(AdamW=AdamW)

    def __init__(self):
        self.counter = 0
        self.cuda = self

    def get_rng_state(self):
        return Tensor(self.counter)

    def get_rng_state_all(self):
        return [Tensor(self.counter)]

    def set_rng_state(self, value):
        self.counter = value.value

    def set_rng_state_all(self, values):
        self.counter = values[0].value

    def load(self, source, **kwargs):
        return deepcopy(self.payload)


class Child:
    def __init__(self, plan, steps):
        self.plan, self.optimizer_steps = plan, steps
        self.optimizer, self.torch = AdamW(), Torch()
        self.parameters = {'weight': object()}
        self.engine = SimpleNamespace(verify_base=lambda: None)
        self.adapter, self.calls = 'a' * 64, 0
        self.experiment = None
        self.mismatch_at = None
        self.fail_after = None
        self.reverse_rehearsal = False
        self.change_eligibility = False

    def check(self, label):
        recovery.require(time.time() < self.plan['hard_end_unix'], 'original_wall')

    def adapter_hash(self):
        return self.adapter

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.calls += 1
        self.torch.counter += 1
        raw = str(random.random()) + ('mismatch' if self.calls == self.mismatch_at else '')
        return dict(raw=raw, token_ids=[self.torch.counter, 151645], terminal=True, truncated=False,
                    prompt_tokens=len(messages), prompt_token_ids_sha256=recovery.digest(messages),
                    adapter_state_sha256=self.adapter, base_sha256=recovery.BASE_SHA, decoder=self.plan['decoder'])

    def sleep(self, new_rows, old_rows, anchors, record):
        record('TARGET_ELIGIBILITY', dict(version=self.plan['presentation_version'], excluded=[],
            new_row_sha256=[row['source_sha256'] for row in new_rows],
            rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=self.change_eligibility))
        schedule = new_rows * 16 + (list(reversed(old_rows)) if self.reverse_rehearsal else old_rows)
        for index, row in enumerate(schedule):
            self.optimizer_steps += 1
            record('UPDATE', dict(optimizer_step=self.optimizer_steps, source_sha256=row['source_sha256']))
            if self.fail_after is not None and index + 1 == self.fail_after:
                raise RuntimeError('synthetic_capacity_OOM')
        self.adapter = 'c' * 64
        return dict(optimizer_steps=len(schedule), total_optimizer_steps=self.optimizer_steps)

    def checkpoint(self, destination):
        destination.mkdir(parents=True)
        return dict(optimizer_steps=self.optimizer_steps, experiment=None,
                    checkpoint_sha256=dict(adapter='c' * 64, optimizer='d' * 64, rng='d' * 64))


class SyntheticJournalWriter:
    """Linear fixture publication; real full-chain scans still validate every boundary.

Not a durability/atomic-publication test or a production journal replacement.
Retain original per-entry state validation, record hashes and intent bindings.
"""

    def __init__(self, journal):
        self.journal = journal
        self.state = journal._scan()

    def __call__(self, kind, document):
        journal = self.journal
        with journal._mutex:
            journal._validate_entry(kind, document)
            document = json.loads(json.dumps(document))
            index, previous = self.state['index'], self.state['previous']
            journal._advance(self.state, kind, document)
            item = dict(schema=journal._manifest['schema'], journal_id=journal._manifest['journal_id'],
                        index=index, kind=kind, previous_sha256=previous, document=document)
            item['sha256'] = recovery.digest(item)
            for ending, content in (('.intent.json', journal._intent(item)), ('.json', item)):
                path = journal.root / 'records' / f'{index:020d}{ending}'
                with path.open('x') as handle:
                    json.dump(content, handle)
            self.state['index'], self.state['previous'] = index + 1, item['sha256']
            return dict(index=index, path=str(journal.root / 'records' / f'{index:020d}.json'), sha256=item['sha256'])


class CapturedMetadataTests(unittest.TestCase):
    def test_actual_capture_metadata_agree_for_both_renewed_lanes(self):
        for physical, count, total in ((5, 64, 816), (6, 58, 630)):
            lane = recovery.load_lane(physical, CAPTURES / 'EXITED_5_6_SUMMARY.json', CAPTURES / 'INVENTORY.json')
            report = recovery.validate_capture(lane)
            self.assertEqual(report['replacement_updates'], count)
            self.assertEqual(report['prospective_total'], total)
            self.assertFalse(report['raw_chain_verified'])
            self.assertFalse(report['checkpoint_payloads_verified'])
            self.assertFalse(report['launch_performed'])
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(ValueError, 'missing_raw_capture'):
                    recovery.verify_saved_files(lane, recovery.LocalCaptureStore(directory))

    def test_capture_tampering_rejected_even_when_structurally_plausible(self):
        lane = recovery.load_lane(5, CAPTURES / 'EXITED_5_6_SUMMARY.json', CAPTURES / 'INVENTORY.json')
        document = lane.inventory
        document['exit_receipt']['finished_unix'] += 1
        with self.assertRaisesRegex(ValueError, 'exact_lane_capture_binding'):
            recovery.validate_capture(replace(lane, inventory_json=json.dumps(document)))

    def test_only_5_6_not_bool_or_other_node(self):
        for physical in (True, '5', 0, 1, 2, 3, 4, 7):
            with self.subTest(physical=physical), self.assertRaises(ValueError):
                recovery.load_lane(physical, CAPTURES / 'EXITED_5_6_SUMMARY.json', CAPTURES / 'INVENTORY.json')

    def test_store_never_falls_back_to_live_absolute_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            store = recovery.LocalCaptureStore(directory)
            for path in ('relative', '/etc/passwd', '/localhome/local-rohing/../other'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    store.raw(path)
            (Path(directory) / 'link').symlink_to('/tmp')
            with self.assertRaisesRegex(ValueError, 'no_capture_symlink'):
                store.path('/localhome/local-rohing/link/file')


class PendingStateMachineTests(unittest.TestCase):
    def patched(self, owner, name, value):
        patcher = patch.object(owner, name, value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fixture(self, physical, *, full_size=False):
        saved_random = random.getstate()
        self.addCleanup(random.setstate, saved_random)
        random.seed(145 + physical)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        store = recovery.LocalCaptureStore(temporary.name)
        spec = deepcopy(capacity.LANES[physical])
        if not full_size:
            offset = 32 - spec['start']
            spec.update(saved_cycle=2, start=32, end=spec['end'] + offset,
                        requests=tuple(index + offset for index in spec['requests']),
                        eligibility=spec['eligibility'] + offset, abandoned=spec['abandoned'] + offset)
        self.patched(recovery, 'EXPECTED_REPLACEMENT_UPDATES', dict(recovery.EXPECTED_REPLACEMENT_UPDATES)
                     | {physical: 32 + 2 * spec['saved_cycle']})
        base = recovery.ORIGIN / ('orch_r133_node3_' + spec['name'] + '_20260916_attempt1')
        root, old_source, new_source = base / 'run1', base / 'source1', base / 'source_r145_synthetic'
        plan_path, guard_path = base / 'control_fixture/PLAN.json', base / 'control_fixture/GUARD.json'
        original_plan = dict(root=str(root), source_root=str(old_source), physical=physical,
            gpu_uuid=capacity.DEVICES[physical], segment_tokens=4, context_limit=16384,
            hard_end_unix=time.time() + 3600, decoder={'temperature': 0.7},
            presentation_version='R125_PLAIN_CONTEXT_V1', system_prompt='Synthetic system.', birth_prompt='Synthetic birth.')
        child = Child(dict(original_plan, source_root=str(new_source)), spec['saved_steps'])
        store.path(root).mkdir(parents=True)
        journal = StreamJournal(store.path(root / 'stream'), create=True)
        self.addCleanup(journal.close)
        writer = SyntheticJournalWriter(journal)
        journal.record = writer
        stream = ContinualStream(TrainHistory(system_prompt=original_plan['system_prompt'], birth_prompt=original_plan['birth_prompt']),
            context_limit=16384, segment_tokens=4, segments_per_sleep=2, deadline_unix=original_plan['hard_end_unix'],
            model_state_sha256='0' * 64)
        stream.set_presentation(dict(version=original_plan['presentation_version'],
            system_prompt=original_plan['system_prompt'], birth_prompt=original_plan['birth_prompt']), 16384)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))

        def write(origin, value):
            path = store.path(origin)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
            return capacity.file_sha(path)

        directory = root / 'checkpoints' / f"sleep_{spec['saved_cycle']:06d}"
        files = {'adapter.bin': write(directory / 'adapter/adapter.bin', b'SYNTHETIC_ADAPTER_NOT_WEIGHTS')}
        optimizer_pin = write(directory / 'optimizer_rng.pt', b'SYNTHETIC_OPTIMIZER_NOT_TORCH_PAYLOAD')
        checkpoint = dict(optimizer_steps=spec['saved_steps'], adapter_files=files,
            checkpoint_sha256=dict(adapter=recovery.digest(files), optimizer=optimizer_pin, rng=optimizer_pin),
            adapter_path=str(directory / 'adapter'), optimizer_rng_path=str(directory / 'optimizer_rng.pt'),
            adapter_state_sha256=child.adapter, base_sha256=recovery.BASE_SHA, experiment=None)
        spec['commit_sha256'] = write(directory / 'COMMIT.json', checkpoint)
        self.patched(capacity, 'LANES', dict(capacity.LANES) | {physical: spec})

        def sleep_request(cycle):
            stream.pending = 'sleep:' + recovery.digest([row['source_sha256'] for row in stream.pending_rows()])
            journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=stream.checkpoint()))

        for cycle in range(1, spec['saved_cycle'] + 1):
            for unused in range(2):
                stream.step(child.generate, len, journal.record)
            sleep_request(cycle)
            if cycle == spec['saved_cycle']:
                while writer.state['index'] < spec['start']:
                    writer('CHECKPOINT_METADATA', {'synthetic_fixture_padding': True})
            stream.pending = None
            stream.commit_sleep(dict(status='COMPLETE', cycle=cycle, optimizer_steps=32,
                checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'],
                new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()]), journal.record)
        child.torch.payload = dict(optimizer=child.optimizer.state_dict(), parameter_names=['weight'],
            optimizer_steps=spec['saved_steps'], python_rng=random.getstate(), cpu_rng=child.torch.get_rng_state(),
            cuda_rng=child.torch.get_rng_state_all(), experiment=None)
        if physical == 5:
            journal.record('LOADED', dict(optimizer_steps=spec['saved_steps'], synthetic_fixture=True))
        publish_parent(store.path(root), 'Astra', 'Synthetic TRAIN parent context retained, not called again.')
        for unused in range(2):
            stream.step(child.generate, len, journal.record, incoming=journal.read_inbox())
        sleep_request(spec['saved_cycle'] + 1)
        journal.record('TARGET_ELIGIBILITY', dict(version=original_plan['presentation_version'], excluded=[], raw_modified=False,
            new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()],
            rehearsal_row_sha256=[row['source_sha256'] for row in stream.rows[:stream.sleep_frontier]]))
        journal.record('UPDATE', dict(optimizer_step=spec['saved_steps'] + 1,
            source_sha256=stream.pending_rows()[0]['source_sha256']))
        records = recovery.scan_records(journal)[1]
        self.assertEqual(len(records), spec['end'])
        suffix = [dict(path=str(root / 'stream/records' / f"{item['index']:020d}.json"),
            sha256=capacity.file_sha(journal.root / 'records' / f"{item['index']:020d}.json"), kind=item['kind'],
            metadata={key: value for key, value in item['document'].items() if key != 'resume_state'})
            for item in records[spec['start']:]]
        summary = dict(physical=physical, commit_path=str(directory / 'COMMIT.json'), commit_sha256=spec['commit_sha256'],
            saved_cycle=spec['saved_cycle'], saved_steps=spec['saved_steps'], suffix=suffix)
        original_native = ('class NativeChild:\n    def generate(self, messages):\n        return messages\n'
            '    def sleep(self, new_rows, old_rows, anchors, record):\n' + capacity.OLD_ENCODING
            + '        for label, sample, weight in batch:\n            if True:\n                if True:\n                    if True:\n'
            + capacity.OLD_FORWARD + '    def checkpoint(self, path):\n        return path\n')
        launcher = b'synthetic_launcher_never_executed = True\n'
        self.patched(capacity, 'NATIVE_SHA', hashlib.sha256(original_native.encode()).hexdigest())
        self.patched(capacity, 'LAUNCHER_SHA', hashlib.sha256(launcher).hexdigest())
        pins = {'gpu/orch_r125_continual_native.py': write(old_source / 'gpu/orch_r125_continual_native.py', original_native.encode()),
                'gpu/orch_r133_node3_programmes.py': write(old_source / 'gpu/orch_r133_node3_programmes.py', launcher)}
        runtime_pin = write(new_source / 'gpu' / capacity.RUNTIME_FILENAME, {'synthetic_fixture': True, 'actual_runtime': False})
        child.synthetic_runtime_pin = runtime_pin
        write(new_source / 'gpu/orch_r125_continual_native.py', capacity.patch_source(original_native, runtime_pin).encode())
        for module in (capacity, recovery):
            write(new_source / 'gpu' / Path(module.__file__).name, Path(module.__file__).read_bytes())
        plan_pin = write(plan_path, original_plan)
        guard_pin = write(guard_path, dict(plan_sha256=plan_pin, source_pins=pins))
        inventory = dict(physical=physical, root=str(root), gpu_uuid=capacity.DEVICES[physical], minor=physical, live=False,
            exit_receipt={'exit_code': 1}, source_root=str(old_source), source_pins=pins,
            plan_path=str(plan_path), plan_sha256=plan_pin, guard_path=str(guard_path), guard_sha256=guard_pin,
            old_native_sha256=capacity.NATIVE_SHA, exited_suffix_from_last_sleep=deepcopy(suffix),
            journal_head={key: suffix[-1][key] for key in ('path', 'kind', 'sha256')})
        lane = recovery.CapturedLane(physical, json.dumps(summary), json.dumps(inventory))
        self.patched(recovery, 'CAPTURE_BINDINGS', dict(recovery.CAPTURE_BINDINGS) | {physical: lane.binding})
        method_gate = patch.object(recovery, 'verify_child_methods', return_value=None)
        method_gate.start()
        self.addCleanup(method_gate.stop)
        output = store.path(root / 'recoveries/r145-synthetic-local-only')
        session = recovery.PendingRecovery(lane, store, child, stream, journal, output)
        child.calls = 0
        return SimpleNamespace(session=session, lane=lane, store=store, child=child, journal=journal,
                               stream=stream, output=output, spec=spec, original=records, write=write)

    @staticmethod
    def probe(child, stream, anchors):
        return dict(status='PASS', state_restored=True, optimizer_updates=0,
                    synthetic_fixture=True, actual_GPU_probe=False, schema=capacity.SCHEMA,
                    train_only=True, exact_learning_trajectory_claim=False,
                    adapter_sha256=child.adapter_hash(), optimizer_sha256=recovery.optimizer_sha(child),
                    rng_sha256=capacity.rng_fingerprint(capacity.rng_state(child.torch)),
                    runtime_pin_sha256=child.synthetic_runtime_pin)

    def ready(self, physical=5, *, full_size=False):
        fixture = self.fixture(physical, full_size=full_size)
        fixture.session.prepare_and_probe({}, self.probe)
        return fixture

    def test_both_exact_renewed_suffixes_replay_then_recompute(self):
        for physical, total in ((5, 816), (6, 630)):
            with self.subTest(physical=physical):
                fixture = self.ready(physical, full_size=True)
                state = deepcopy(fixture.stream.checkpoint())
                fixture.session.replay()
                self.assertEqual(fixture.child.calls, 2)
                self.assertEqual(fixture.stream.checkpoint(), state)
                self.assertEqual(recovery.scan_records(fixture.journal)[1], fixture.original)
                saved = fixture.session.recompute({})
                self.assertEqual(saved['optimizer_steps'], total)
                self.assertEqual(fixture.session.phase, 'SAVED')
                self.assertIsNone(fixture.stream.pending)
                self.assertEqual(fixture.stream.sleep_frontier, len(fixture.stream.rows))
                self.assertEqual(fixture.session._files(), fixture.session.original_files)
                updated = recovery.scan_records(fixture.journal)[1]
                original_update = updated[fixture.spec['abandoned']]
                replacements = [item['document'] for item in updated[fixture.spec['end']:] if item['kind'] == 'UPDATE']
                self.assertEqual([item['source_sha256'] for item in replacements], fixture.lane.expected_sources)
                self.assertEqual(replacements[0]['optimizer_step'], original_update['document']['optimizer_step'])
                self.assertEqual(replacements[0]['r145_recovery']['historical_abandoned_updates'], 1)
                self.assertFalse(replacements[0]['r145_recovery']['bitwise_learning_trajectory_claim'])
                for item in fixture.lane.summary['suffix']:
                    self.assertEqual(capacity.file_sha(fixture.output / Path(item['path']).name), item['sha256'])
                with self.assertRaises(ValueError):
                    fixture.session.recompute({})

    def test_raw_file_hash_is_not_internal_record_hash(self):
        fixture = self.fixture(5)
        item = fixture.lane.summary['suffix'][-1]
        self.assertNotEqual(item['sha256'], fixture.original[-1]['sha256'])
        recovery.bind_pending(fixture.lane, fixture.store, fixture.child, fixture.stream, fixture.journal)
        path = fixture.store.path(item['path'])
        path.write_bytes(path.read_bytes() + b'\n')
        recovery.scan_records(fixture.journal)
        with self.assertRaisesRegex(ValueError, 'captured_raw_file_hash'):
            recovery.bind_pending(fixture.lane, fixture.store, fixture.child, fixture.stream, fixture.journal)

    def test_incomplete_intent_or_prefix_corruption_rejected(self):
        fixture = self.fixture(6)
        path = fixture.journal.root / 'records/00000000000000000002.intent.json'
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'journal_intent_binding'):
            recovery.bind_pending(fixture.lane, fixture.store, fixture.child, fixture.stream, fixture.journal)

    def test_one_matching_generation_is_not_enough(self):
        fixture = self.ready()
        fixture.child.mismatch_at = 2
        with self.assertRaisesRegex(ValueError, 'exact_generation_response:1'):
            fixture.session.replay()
        self.assertEqual(fixture.child.calls, 2)
        self.assertEqual(fixture.session.phase, 'FAILED')
        self.assertEqual(fixture.session._files(), fixture.session.original_files)
        with self.assertRaises(ValueError):
            fixture.session.recompute({})
        with self.assertRaises(ValueError):
            fixture.session.replay()

    def test_probe_mutating_rng_is_rejected_before_replay(self):
        fixture = self.fixture(6)
        def bad_probe(child, stream, anchors):
            child.torch.counter += 1
            return self.probe(child, stream, anchors)
        with self.assertRaisesRegex(ValueError, 'successful_state_restoring_TRAIN_probe_required'):
            fixture.session.prepare_and_probe({}, bad_probe)
        self.assertEqual(fixture.child.calls, 0)
        self.assertEqual(fixture.session.phase, 'FAILED')

    def test_probe_cannot_mutate_anchors_even_with_matching_rng(self):
        fixture = self.fixture(6)
        anchors = {'synthetic': ['unchanged']}
        def bad_probe(child, stream, inventory):
            inventory['synthetic'].append('mutation')
            return self.probe(child, stream, inventory)
        with self.assertRaisesRegex(ValueError, 'probe_did_not_mutate_saved_state'):
            fixture.session.prepare_and_probe(anchors, bad_probe)
        self.assertEqual(fixture.child.calls, 0)

    def test_changed_source_after_probe_rejected_before_generation(self):
        fixture = self.ready()
        path = fixture.store.path(Path(fixture.child.plan['source_root']) / 'gpu/orch_r125_continual_native.py')
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'exact_prospective_child_only_patch'):
            fixture.session.replay()
        self.assertEqual(fixture.child.calls, 0)

    def test_missing_exact_probe_runtime_binding_rejected(self):
        fixture = self.fixture(5)
        def bad_probe(child, stream, anchors):
            return dict(self.probe(child, stream, anchors), runtime_pin_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'successful_state_restoring_TRAIN_probe_required'):
            fixture.session.prepare_and_probe({}, bad_probe)
        self.assertEqual(fixture.child.calls, 0)

    def test_attempt_path_cannot_escape_owned_local_recovery_root(self):
        fixture = self.fixture(5)
        escape = fixture.output.parent / '..' / '..' / 'r145-outside'
        with self.assertRaisesRegex(ValueError, 'new_owned_recovery_namespace'):
            recovery.PendingRecovery(fixture.lane, fixture.store, fixture.child, fixture.stream, fixture.journal, escape)

    def test_unsaved_weights_or_wrong_optimizer_parameter_order_rejected(self):
        fixture = self.fixture(5)
        fixture.child.adapter = 'unsaved'
        with self.assertRaisesRegex(ValueError, 'loaded_saved_not_unsaved_adapter'):
            recovery.bind_pending(fixture.lane, fixture.store, fixture.child, fixture.stream, fixture.journal)
        fixture.child.adapter = fixture.lane.checkpoint['adapter_state_sha256']
        fixture.child.torch.payload['parameter_names'] = ['other_weight']
        with self.assertRaisesRegex(ValueError, 'saved_parameter_order_steps_experiment'):
            recovery.restore_saved(fixture.child, fixture.lane, fixture.store)

    def test_source_and_recipe_changes_rejected(self):
        fixture = self.fixture(6)
        altered = dict(fixture.child.plan, context_limit=8192)
        with self.assertRaisesRegex(ValueError, 'no_recipe_generation_deadline_parent_changes'):
            recovery.verify_source_and_plan(fixture.lane, fixture.store, altered)
        path = fixture.store.path(Path(fixture.child.plan['source_root']) / 'gpu/orch_r125_continual_native.py')
        path.write_text(path.read_text().replace("label.startswith('ANCHOR:')", 'False'))
        with self.assertRaisesRegex(ValueError, 'exact_prospective_child_only_patch'):
            recovery.verify_source_and_plan(fixture.lane, fixture.store, fixture.child.plan)

    def test_post_replay_rng_change_cannot_start_sleep(self):
        fixture = self.ready()
        fixture.session.replay()
        fixture.child.torch.counter += 1
        with self.assertRaisesRegex(ValueError, 'no_interposed_RNG_or_optimizer_changes'):
            fixture.session.recompute({})
        self.assertEqual(fixture.session._files(), fixture.session.original_files)

    def test_unchanged_eligibility_and_rehearsal_order_required(self):
        for mutation in ('change_eligibility', 'reverse_rehearsal'):
            with self.subTest(mutation=mutation):
                fixture = self.ready(6)
                fixture.session.replay()
                setattr(fixture.child, mutation, True)
                with self.assertRaises(ValueError):
                    fixture.session.recompute({})
                self.assertEqual(fixture.session.phase, 'FAILED')
                self.assertEqual(fixture.session._files(), fixture.session.original_files)

    def test_second_OOM_is_preserved_and_never_automatically_retried(self):
        fixture = self.ready(5)
        fixture.session.replay()
        fixture.child.fail_after = 2
        with self.assertRaisesRegex(RuntimeError, 'synthetic_capacity_OOM'):
            fixture.session.recompute({})
        self.assertEqual(fixture.session._files(), fixture.session.original_files)
        self.assertEqual(fixture.child.optimizer_steps, 754)
        self.assertFalse((fixture.output / 'SLEEP_RECOMPUTED.json').exists())
        with self.assertRaises(ValueError):
            fixture.session.recompute({})
        failure = json.loads((fixture.output / 'FAILED.json').read_text())
        self.assertFalse(failure['retry_allowed'])
        self.assertTrue(failure['child_must_be_discarded'])


if __name__ == '__main__':
    unittest.main()
