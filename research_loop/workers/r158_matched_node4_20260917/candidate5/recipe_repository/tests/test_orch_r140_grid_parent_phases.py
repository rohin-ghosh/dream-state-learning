import copy
import importlib.util
import inspect
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('phase_subject',
    Path(__file__).resolve().parents[1] / 'gpu/orch_r140_grid_parent_phases.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class PhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.head, cls.scratch, cls.handoff, cls.http = subject.dependencies()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir='/data/home/rohing/courier/runtime')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.boundary = dict(after_parent=322, next_cycle=111)
        self.plan = dict(cumulative_caps=dict(PARENT=404430))
        self.request = dict(id='P0325', lane_deadline_unix=1000,
            payload=dict(cycle=112, phase='open_turn', life_id='F4_FABLE', game='grid',
                         task_provenance=dict(split='TRAIN')))
        self.predicate = subject.phase_predicate(self.handoff)

    def production(self):
        builder = subject.broker_builder(self.head, self.scratch, self.handoff, self.http)
        serving = builder(self.http, self.boundary, self.plan, {}, 'CPU_ONLY')
        head_processor = serving.__globals__['process_request']
        processor = inspect.getclosurevars(head_processor).nonlocals['original']
        original = inspect.getclosurevars(processor).nonlocals['original_process']
        return head_processor, processor, original

    def store(self, disposed=None):
        encoded = json.dumps(self.request).encode()
        packet = self.handoff.ROOT / 'parent_queue/P0325.request.json'
        def exists(path):
            return path == packet or path == disposed
        store = SimpleNamespace(exists=Mock(side_effect=exists),
            shell=Mock(return_value=SimpleNamespace(stdout=str(len(encoded)))),
            copy=Mock(side_effect=lambda source, target: Path(target).write_bytes(encoded)),
            hash=Mock(return_value=__import__('hashlib').sha256(encoded).hexdigest()))
        return store

    def test_three_current_TRAIN_phases_no_mutation(self):
        for phase in subject.PHASES:
            self.request['payload']['phase'] = phase
            before = copy.deepcopy(self.request)
            self.assertTrue(self.predicate(self.request, self.boundary, now=100))
            self.assertEqual(before, self.request)

    def test_unknown_DEV_FINAL_rejected(self):
        for phase in ('unknown', 'reflection', 'EXPERIENCE', '', None):
            self.request['payload']['phase'] = phase
            self.assertFalse(self.predicate(self.request, self.boundary, now=100))
        for split in ('DEV', 'FINAL'):
            self.request['payload'].update(phase='experience', task_provenance=dict(split=split))
            self.assertFalse(self.predicate(self.request, self.boundary, now=100))

    def test_history_floor_and_pre_boundary_cycle_rejected(self):
        for number in (1, 298, 322, 323, 324):
            self.request['id'] = f'P{number:04d}'
            self.assertFalse(self.predicate(self.request, self.boundary, now=100))
        self.request['id'] = 'P0325'
        self.request['payload']['cycle'] = 110
        self.assertFalse(self.predicate(self.request, self.boundary, now=100))

    def test_expired_cutoff_disposed_and_wrong_identity_rejected(self):
        self.assertFalse(self.predicate(self.request, self.boundary, now=970))
        self.assertFalse(self.predicate(self.request, self.boundary, now=100, disposed=True))
        self.assertTrue(self.predicate(self.request, self.boundary, now=969))
        for key, value in [('life_id', 'A4_ASTRA'), ('game', 'math')]:
            request = copy.deepcopy(self.request)
            request['payload'][key] = value
            self.assertFalse(self.predicate(request, self.boundary, now=100))

    def test_experience_predicate_matches_frozen_except_required_floor(self):
        self.request['payload']['phase'] = 'experience'
        for now in (100, 969, 970, 1000, self.handoff.TRAIN_END):
            self.assertEqual(self.predicate(self.request, self.boundary, now=now),
                             self.handoff.prospective(self.request, self.boundary, now=now))

    def test_production_factory_binds_both_preclaim_and_evaluate_guards(self):
        head_processor, processor, original = self.production()
        evaluate = original.__globals__['evaluate']
        self.assertIs(processor.__globals__['prospective'], evaluate.__globals__['prospective'])
        for phase in subject.PHASES:
            self.request['payload']['phase'] = phase
            self.assertTrue(evaluate.__globals__['prospective'](self.request, self.boundary, now=100))
        self.assertFalse(self.handoff.prospective(self.request, self.boundary, now=100))

    def test_production_preclaim_forwards_all_three_unchanged(self):
        for phase in subject.PHASES:
            self.request['payload']['phase'] = phase
            head_processor, processor, original = self.production()
            forwarded = Mock(return_value='CPU_FORWARD_ONLY')
            cells = dict(zip(processor.__code__.co_freevars, processor.__closure__))
            cells['original_process'].cell_contents = forwarded
            store = self.store()
            before = copy.deepcopy(self.request)
            with patch.object(self.handoff.time, 'time', return_value=100):
                self.assertEqual(head_processor(store, {}, {}, 'P0325.request.json', self.root, None, None), 'CPU_FORWARD_ONLY')
            forwarded.assert_called_once_with(store, {}, {}, 'P0325.request.json', self.root, None, None)
            self.assertEqual(before, self.request)
            self.assertFalse((self.root / 'eligibility.json').exists())

    def test_production_old_slots_rejected_before_IO(self):
        head_processor, processor, original = self.production()
        store = SimpleNamespace(exists=Mock(side_effect=AssertionError('no historical IO')))
        for number in (298, 323, 324):
            self.assertEqual(head_processor(store, {}, {}, f'P{number:04d}.request.json', self.root, None, None),
                             'PRE_REPAIR_HISTORICAL_NO_REDISPATCH')
        self.assertEqual(head_processor(store, {}, {}, 'P404431.request.json', self.root, None, None),
                         'CUMULATIVE_CAP_EXHAUSTED')

    def test_production_any_claim_response_or_disposition_never_replayed(self):
        head_processor, processor, original = self.production()
        for folder, suffix in [('parent_claude', '.claim'), ('parent_astra_r139', '.claim'),
                               ('parent_received', '.json'), ('parent_queue', '.response.json')]:
            store = self.store(self.handoff.ROOT / folder / ('P0325' + suffix))
            self.assertEqual(head_processor(store, {}, {}, 'P0325.request.json', self.root, None, None),
                             'DISPOSED_OR_MISSING_NO_REDISPATCH')
            store.copy.assert_not_called()

    def test_production_expired_unknown_and_FINAL_never_forward(self):
        for phase, split, now in [('open_turn', 'TRAIN', 970), ('unknown', 'TRAIN', 100),
                                  ('experience', 'FINAL', 100), ('open_turn', 'DEV', 100)]:
            self.request['payload'].update(phase=phase, task_provenance=dict(split=split))
            head_processor, processor, original = self.production()
            cells = dict(zip(processor.__code__.co_freevars, processor.__closure__))
            cells['original_process'].cell_contents = Mock(side_effect=AssertionError('no dispatch'))
            with patch.object(self.handoff.time, 'time', return_value=now):
                self.assertEqual(head_processor(self.store(), {}, {}, 'P0325.request.json', self.root, None, None),
                                 'EXPIRED_OR_NON_EPISODE_NO_REDISPATCH')

    def test_production_prompt_assembly_identical_to_existing_head_wrapper(self):
        head_processor, processor, original = self.production()
        evaluator = inspect.getclosurevars(original.__globals__['evaluate']).nonlocals['evaluator']
        actual = evaluator.__globals__['transport']
        old = self.head.prompt_view(self.scratch, self.http.astra.transport)
        fields = dict(GAME='grid', STYLE='unchanged', NUDGING='unchanged', FOCUS='unchanged',
                      REFLECTION=dict(mode='short', max_new_tokens=128))
        prompt = self.root / 'F4.md'
        prompt.write_text(old.render_parent_prompt(fields))
        fields['NEXT_GUIDANCE'] = 'Synthetic exact optional text.'
        prompt.with_suffix('.fields.json').write_text(json.dumps(dict(schema='ORCH_R114_HEAD_FIELDS_V1',
            prompt_sha256=subject.sha(prompt), fields=fields)))
        principles = self.root / 'principles.txt'
        principles.write_text('Synthetic exact policy.')
        config = dict(branch='F4', family='grid', principles_sha256=subject.sha(principles))
        for phase in subject.PHASES:
            transcript = dict(game='grid', cycle=112, episode=1, phase=phase)
            self.assertEqual(actual.build_system(transcript, config, self.root, principles),
                             old.build_system(transcript, config, self.root, principles))

    def test_authorization_requires_exact_wrapper_floor_and_immutable_archive(self):
        archive = self.root / 'old.json'
        archive.write_text('{}')
        publication = dict(phase_wrapper=subject.source_ref(), allowed_TRAIN_phases=list(subject.PHASES),
            P0324_preserved_no_retry=True, prompt_text_unchanged=True,
            previous_publication=dict(path=str(archive), sha256=subject.sha(archive)))
        head = SimpleNamespace(authorize=Mock())
        subject.authorize(head, self.scratch, None, {}, publication, 'hash', 'broker', 100, 324)
        for change in [dict(phase_wrapper={}), dict(allowed_TRAIN_phases=['experience']),
                       dict(P0324_preserved_no_retry=False), dict(prompt_text_unchanged=False)]:
            with self.assertRaises(ValueError):
                subject.authorize(head, self.scratch, None, {}, dict(publication, **change), 'hash', 'broker', 100, 324)
        with self.assertRaises(ValueError):
            subject.authorize(head, self.scratch, None, {}, publication, 'hash', 'broker', 100, 325)
        archive.write_text('{"authorized":false}')
        with self.assertRaisesRegex(ValueError, 'pre_revocation'):
            subject.authorize(head, self.scratch, None, {}, publication, 'hash', 'broker', 100, 324)

    def test_cli_no_publication_no_runtime(self):
        with (patch.object(subject.sys, 'dont_write_bytecode', True),
              patch.object(subject.sys, 'argv', ['phases', 'broker', '--expected-self-sha256', subject.sha(subject.__file__)]),
              patch.object(subject, 'dependencies', side_effect=AssertionError('no runtime')),
              patch.dict(os.environ, CUDA_VISIBLE_DEVICES='')):
            with self.assertRaisesRegex(ValueError, 'explicit_Main_publication'):
                subject.main()


if __name__ == '__main__':
    unittest.main()
