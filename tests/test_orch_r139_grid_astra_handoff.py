from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[1]


def module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


subject = module(REPOSITORY / 'gpu/orch_r139_grid_astra_handoff.py', 'handoff')
legacy_path = REPOSITORY / 'gpu/orch_r119_grid_final_lifecycle.py'
if not legacy_path.exists():
    legacy_path = subject.CUSTODY
legacy = module(legacy_path, 'legacy_custody')
mailbox_path = REPOSITORY / 'gpu/orch_r119_grid_async_parent.py'
if not mailbox_path.exists():
    mailbox_path = Path('/localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1/gpu/orch_r119_grid_async_parent.py')
mailbox = module(mailbox_path, 'original_mailbox')


def plan():
    return dict(schema='R139_F4_SAVED_STATE_HANDOFF_V1', root=str(subject.ROOT), output=str(subject.ROOT / subject.ERA),
        requested_model=subject.ASTRA, source_sha256=subject.sha(subject.__file__), custody_sha256=subject.CUSTODY_SHA,
        hard_end_unix=subject.HARD_END, train_end_unix=subject.TRAIN_END, morning_unix=subject.MORNING,
        approved_intake='R121_fixture', requested_scope='F4_fixture')


def publication():
    return dict(authorized=True, published_by='Main', plan_sha256='a' * 64, approved_intake='R121_fixture',
        requested_scope='F4_fixture', modes=['release', 'resume', 'broker'], not_before_unix=100,
        new_parent_model=subject.ASTRA, no_reset=True, no_historical_redispatch=True)


def request(position=320, phase='experience', cycle=106):
    return dict(id=f'P{position:04d}', lane_deadline_unix=500,
                payload=dict(life_id='F4_FABLE', game='grid', phase=phase, cycle=cycle,
                             task_provenance=dict(split='TRAIN')))


class AuthorizationTests(unittest.TestCase):
    def test_Main_exact_scope_and_model_required(self):
        subject.authorize(plan(), publication(), 'a' * 64, 'resume', 101)
        for key, value in [('authorized', False), ('published_by', 'sidecar'), ('plan_sha256', 'b' * 64),
                           ('new_parent_model', 'claude-fable-5-1'), ('no_reset', False),
                           ('not_before_unix', 102), ('no_historical_redispatch', False),
                           ('approved_intake', 'different'), ('modes', [])]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                subject.authorize(plan(), dict(publication(), **{key: value}), 'a' * 64, 'resume', 101)

    def test_wall_and_source_cannot_expand(self):
        for key, value in [('hard_end_unix', subject.HARD_END + 1), ('source_sha256', 'b' * 64),
                           ('train_end_unix', subject.TRAIN_END + 1), ('morning_unix', subject.MORNING + 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                subject.authorize(dict(plan(), **{key: value}), publication(), 'a' * 64, 'release', 101)

    def test_no_gpu_or_signal_before_publication(self):
        with (patch.object(subject, 'release', side_effect=AssertionError('no_signals')),
              patch.object(subject, 'resume', side_effect=AssertionError('no_GPU'))):
            with patch.object(subject.sys, 'argv', ['handoff', 'resume', '--expected-self-sha256', subject.sha(subject.__file__)]):
                with self.assertRaisesRegex(ValueError, 'explicit_plan'):
                    subject.main()

    def test_jsonl_hash_reference_is_not_parsed_as_one_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'LEDGER.jsonl'
            path.write_text('{"number":1}\n{"number":2}\n')
            reference = subject.reference(path)
            self.assertEqual(subject.check_hash(reference), path)
            path.write_text('{"number":0}\n')
            with self.assertRaises(ValueError):
                subject.check_hash(reference)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.carry = [dict(split='TRAIN', trace='synthetic_fixture')]
        self.rows = [dict(kind='PARENT', number=number, cycle=7, reserved_unix=50) for number in range(1, 299)]
        self.rows += [dict(kind='NATIVE', number=number, cycle=7, split='TRAIN', attached_readout=False) for number in (1, 2)]
        self.write('CARRY.json', self.carry)
        self.write('cycles/0007/TRAIN_COMPLETE.json', dict(outcomes=[{}, {}], carry=self.carry, optimizer_steps=0))
        for number in (1, 2):
            self.write(f'calls/N{number:05d}.json', dict(status='COMPLETE'))
        for number in range(1, 299):
            (self.root / 'parent_claude' / f'P{number:04d}.claim').mkdir(parents=True)
        (self.root / 'parent_queue').mkdir()
        self.ledger()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def ledger(self):
        (self.root / 'LEDGER.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in self.rows))

    def test_exact_boundary_preserves_all_bytes_and_counters(self):
        before = {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        result = subject.boundary_snapshot(self.root, legacy)
        self.assertEqual(result['next_cycle'], 8)
        self.assertEqual(result['after_parent'], 298)
        self.assertEqual(result['first_new_parent'], 299)
        self.assertEqual(result['counts'], dict(NATIVE=2, PARENT=298))
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    def test_inflight_model_input_cannot_be_abandoned(self):
        self.write('calls/N00002.json', dict(status='STARTED'))
        with self.assertRaisesRegex(ValueError, 'unfinished_model'):
            subject.boundary_snapshot(self.root, legacy)

    def test_incomplete_episode_or_carry_mismatch_cannot_release(self):
        self.write('cycles/0007/TRAIN_COMPLETE.json', dict(outcomes=[{}], carry=self.carry, optimizer_steps=0))
        with self.assertRaisesRegex(ValueError, 'durable_carry'):
            subject.boundary_snapshot(self.root, legacy)

    def test_old_claims_cannot_be_erased(self):
        (self.root / 'parent_claude/P0298.claim').rmdir()
        with self.assertRaisesRegex(ValueError, '298_Claude'):
            subject.boundary_snapshot(self.root, legacy)

    def test_no_future_queue_outside_cumulative_ledger(self):
        self.write('parent_queue/P0299.request.json', request(299))
        with self.assertRaisesRegex(ValueError, 'queue_ledger'):
            subject.boundary_snapshot(self.root, legacy)


class ConsumerTests(unittest.TestCase):
    def test_truthful_Astra_accepted_without_changing_lineage(self):
        from organism_v6 import orch_r111_grid as policy
        config = dict(life_id='F4_FABLE', parent_model='claude-fable-5-1', checkpoint='unchanged')
        boundary = dict(cycle=105, next_cycle=106, after_parent=319, first_new_parent=320)
        before = deepcopy(config)
        new = subject.consumer_config(config, boundary)
        self.assertEqual(config, before)
        self.assertEqual(new, dict(config, parent_model=subject.ASTRA))
        queued = request()
        queued['payload_sha256'] = policy.digest(queued['payload'])
        response = dict(status='COMPLETE', actual_model=subject.ASTRA, finished_unix=101,
            request_sha256=policy.digest(queued), payload_sha256=queued['payload_sha256'],
            plan=dict(speak=True, message='synthetic guidance'), usage={})
        self.assertEqual(policy.parent_disposition(queued, response, 102, new['parent_model'])['status'], 'COMPLETE')
        self.assertEqual(policy.parent_disposition(queued, response, 102, config['parent_model'])['status'], 'MISSING')
        self.assertNotIn('canonicalModel', json.dumps(response))

    def test_historical_missing_expired_and_non_TRAIN_skipped(self):
        boundary = dict(after_parent=319, next_cycle=106)
        self.assertTrue(subject.prospective(request(), boundary, now=101))
        candidates = [None, request(319), request(cycle=105), request(phase='open_turn'),
                      dict(request(), lane_deadline_unix=131)]
        held = request()
        held['payload']['task_provenance']['split'] = 'FINAL'
        candidates.append(held)
        for item in candidates:
            with self.subTest(item=item):
                self.assertFalse(subject.prospective(item, boundary, now=101))
        self.assertFalse(subject.prospective(request(), boundary, now=101, disposed=True))

    def test_broker_segment_uses_remaining_existing_cap_only(self):
        old = dict(branch='F4', family='grid', life_id='F4_FABLE', max_parent_calls=298,
            deadline_unix=1, train_tasks={'id': 'hash'}, excluded_task_ids=['held'],
            max_budget_usd=1, max_output_tokens=8192, queue_transport='node_local')
        before = deepcopy(old)
        config = subject.broker_config(old, dict(after_parent=319), dict(PARENT=404430), {'source': 'hash'})
        self.assertEqual(config['max_parent_calls'], 404111)
        self.assertEqual(config['deadline_unix'], subject.HARD_END)
        for key in ('train_tasks', 'excluded_task_ids', 'max_budget_usd', 'max_output_tokens'):
            self.assertEqual(config[key], old[key])
        self.assertEqual(old, before)

    def test_original_mailbox_ignores_prior_pending_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'parent_queue').mkdir()
            (root / 'parent_queue/P0319.request.json').write_text(json.dumps(request(319)))
            (root / 'LEDGER.jsonl').write_text(json.dumps(dict(kind='PARENT', number=319, reserved_unix=50)) + '\n')
            class BaseLife:
                def __init__(self, root, config):
                    self.root, self.config = root, config
            grid = SimpleNamespace(Life=BaseLife, read=lambda path: json.loads(path.read_text()))
            life = mailbox.life_class(grid, subject.OLD_ERA, first_parent=320)(root, {})
            self.assertEqual(life.poll(), ([], []))
            self.assertFalse((root / 'parent_received').exists())
            self.assertTrue((root / 'parent_queue/P0319.request.json').exists())

    def test_resume_never_replays_models_or_loads_optimizer(self):
        text = inspect_source(subject.resume)
        self.assertIn("boundary['next_cycle']", text)
        self.assertIn("first_parent=boundary['first_new_parent']", text)
        self.assertIn('is_trainable=False', text)
        self.assertNotIn('AdamW(', text)
        self.assertNotIn('ReplayLife', text)
        self.assertNotIn('FINAL.json', text)


def inspect_source(function):
    import inspect
    return inspect.getsource(function)


class BrokerBuildTests(unittest.TestCase):
    @unittest.skipUnless(subject.BROKER_RUNTIME.exists(), 'VM-only pinned A4 runtime')
    def test_existing_A4_adapter_builds_without_provider_or_queue_calls(self):
        http = subject.load_broker_runtime()
        bound = subject.broker_functions(http, dict(after_parent=319, next_cycle=106),
            dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        processor = bound.__globals__['process_request']
        store = SimpleNamespace(exists=lambda path: (_ for _ in ()).throw(AssertionError('no_old_queue_reads')))
        self.assertEqual(processor(store, {}, {}, 'P0319.request.json', None, None, None), 'HISTORICAL_NO_REDISPATCH')
        self.assertEqual(processor(store, {}, {}, 'P404431.request.json', None, None, None), 'CUMULATIVE_CAP_EXHAUSTED')


if __name__ == '__main__':
    unittest.main()
