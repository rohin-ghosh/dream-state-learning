import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('head_subject',
    Path(__file__).resolve().parents[1] / 'gpu/orch_r139_grid_head_fields.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class HeadFieldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch, cls.handoff, cls.http = subject.dependencies()
        cls.transport = cls.http.astra.transport

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.prompt = self.root / 'F4.md'
        self.settings = self.root / 'F4.fields.json'
        self.principles = self.root / 'principles.txt'
        self.principles.write_text('Synthetic fixed policy; do not rephrase.')
        self.config = dict(branch='F4', family='grid', principles_sha256=subject.sha(self.principles))
        self.transcript = dict(game='grid', cycle=111, episode=0, phase='experience')
        self.fields = dict(GAME='grid', STYLE='unchanged', NUDGING='unchanged', FOCUS='unchanged',
                           REFLECTION=dict(mode='short', max_new_tokens=128))
        self.view = subject.prompt_view(self.scratch, self.transport)
        self.write_fields(self.fields)

    def write_fields(self, fields, match=True):
        prompt = self.transport.render_parent_prompt({key: value for key, value in self.fields.items()})
        self.prompt.write_text(prompt)
        self.settings.write_text(json.dumps(dict(schema='ORCH_R114_HEAD_FIELDS_V1',
            prompt_sha256=subject.sha(self.prompt) if match else '0' * 64, fields=fields)))

    def build(self, view=None):
        return (view or self.view).build_system(self.transcript, self.config, self.root, self.principles)

    def test_reproduces_exact_optional_key_failure_and_repairs_it(self):
        self.write_fields(dict(self.fields, NEXT_GUIDANCE='Synthetic optional guidance.'))
        with self.assertRaisesRegex(ValueError, '^head_fields_keys$'):
            self.transport.head_binding(self.prompt, self.prompt.read_bytes())
        with self.assertRaisesRegex(ValueError, '^head_fields_keys$'):
            self.build(self.transport)
        system, prompt, binding = self.build()
        self.assertEqual(binding['head_settings']['status'], 'BOUND_REQUESTED_SETTINGS')
        self.assertIn('Synthetic optional guidance.', system)
        self.assertEqual(prompt, self.prompt.read_bytes())

    def test_optional_text_is_exactly_appended_without_policy_rephrasing(self):
        original_system, original_prompt, original_binding = self.build(self.transport)
        guidance = 'Keep [FOCUS] literal.\nDo not alter this optional text.'
        self.write_fields(dict(self.fields, NEXT_GUIDANCE=guidance))
        before = {path: path.read_bytes() for path in (self.prompt, self.settings, self.principles)}
        system, prompt, binding = self.build()
        old_part = '\n\n' + self.transport.SYSTEM_CONTRACT + '\n\nTRAIN TRANSCRIPT:\n'
        new_part = '\n\nASYNCHRONOUS HEAD NEXT_GUIDANCE:\n' + guidance + old_part
        self.assertEqual(system, original_system.replace(old_part, new_part, 1))
        self.assertEqual(prompt, original_prompt)
        self.assertEqual(binding['transport_contract_sha256'], original_binding['transport_contract_sha256'])
        self.assertEqual(binding['next_guidance_sha256'], hashlib.sha256(guidance.encode()).hexdigest())
        self.assertFalse(binding['head_waited'])
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_absent_and_empty_optional_text_preserve_system_bytes(self):
        original = self.build(self.transport)[0]
        self.assertEqual(self.build()[0], original)
        self.write_fields(dict(self.fields, NEXT_GUIDANCE=''))
        self.assertEqual(self.build()[0], original)

    def test_optional_unicode_uses_byte_limit_not_character_limit(self):
        self.view.render_parent_prompt(dict(self.fields, NEXT_GUIDANCE='🙂' * 256))
        for value in (None, 3, [], '🙂' * 257, 'a' * 1025):
            with self.subTest(kind=type(value).__name__), self.assertRaisesRegex(ValueError, 'bounded_next_guidance'):
                self.view.render_parent_prompt(dict(self.fields, NEXT_GUIDANCE=value))

    def test_unknown_or_missing_keys_remain_rejected(self):
        for fields in (dict(self.fields, SECRET='not_allowed'), {key: value for key, value in self.fields.items() if key != 'FOCUS'}):
            with self.assertRaisesRegex(ValueError, 'head_fields_keys'):
                self.view.render_parent_prompt(fields)

    def test_original_reflection_bounds_remain_rejected(self):
        for reflection in (dict(mode='invalid', max_new_tokens=128), dict(mode='short', max_new_tokens=8193)):
            with self.assertRaisesRegex(ValueError, 'reflection_request_bounds'):
                self.view.render_parent_prompt(dict(self.fields, REFLECTION=reflection, NEXT_GUIDANCE='bound'))

    def test_unbound_settings_never_supply_guidance(self):
        self.write_fields(dict(self.fields, NEXT_GUIDANCE='UNBOUND_DO_NOT_USE'), match=False)
        system, prompt, binding = self.build()
        self.assertEqual(binding['head_settings']['status'], 'SETTINGS_MISMATCH_REPORT_ONLY')
        self.assertNotIn('UNBOUND_DO_NOT_USE', system)
        self.assertEqual(binding['next_guidance_sha256'], hashlib.sha256(b'').hexdigest())

    def test_drifted_prompt_and_wrong_principles_still_fail(self):
        self.prompt.write_text('not the fixed prompt')
        with self.assertRaisesRegex(ValueError, 'fixed_v4_parent_prompt_drift'):
            self.build()
        self.write_fields(self.fields)
        self.principles.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'principles_hash_changed'):
            self.build()

    def test_other_branch_is_not_enabled(self):
        self.config['branch'] = 'A2'
        with self.assertRaisesRegex(ValueError, 'F4_grid_only'):
            self.build()

    def test_frozen_source_and_functions_are_unchanged(self):
        before = {relative: subject.sha(self.handoff.BROKER_RUNTIME / relative) for relative in self.handoff.BROKER_PINS}
        original = self.transport.render_parent_prompt
        self.view.render_parent_prompt(dict(self.fields, NEXT_GUIDANCE='new'))
        self.assertIs(self.transport.render_parent_prompt, original)
        with self.assertRaisesRegex(ValueError, 'head_fields_keys'):
            original(dict(self.fields, NEXT_GUIDANCE='new'))
        self.assertEqual(before, {relative: subject.sha(self.handoff.BROKER_RUNTIME / relative) for relative in before})

    def test_repair_floor_skips_P0323_and_all_prior_without_IO(self):
        builder = subject.broker_builder(self.scratch, self.handoff, self.http, 325)
        serving = builder(self.http, dict(after_parent=320, next_cycle=111),
            dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        processor = serving.__globals__['process_request']
        store = SimpleNamespace(exists=Mock(side_effect=AssertionError('no_historical_IO')))
        for number in (320, 323, 325):
            self.assertEqual(processor(store, {}, {}, f'P{number:04d}.request.json', None, None, None),
                             'PRE_REPAIR_HISTORICAL_NO_REDISPATCH')
        store.exists.assert_not_called()
        self.assertEqual(processor(store, {}, {}, 'P404431.request.json', None, None, None), 'CUMULATIVE_CAP_EXHAUSTED')

    def test_builder_actually_wires_repaired_prompt_into_evaluator(self):
        self.write_fields(dict(self.fields, NEXT_GUIDANCE='wired-guidance'))
        builder = subject.broker_builder(self.scratch, self.handoff, self.http, 325)
        serving = builder(self.http, dict(after_parent=320, next_cycle=111),
            dict(cumulative_caps=dict(PARENT=404430)), {}, 'CPU_ONLY')
        processor = serving.__globals__['process_request']
        original = inspect.getclosurevars(processor).nonlocals['original']
        original_process = inspect.getclosurevars(original).nonlocals['original_process']
        outer_evaluate = original_process.__globals__['evaluate']
        evaluator = inspect.getclosurevars(outer_evaluate).nonlocals['evaluator']
        transport = evaluator.__globals__['transport']
        self.assertIn('wired-guidance', self.build(transport)[0])
        self.assertEqual(str(self.http.slots.ROOT), '/tmp/orch_astra_http_slots')
        self.assertEqual(self.http.slots.LIMIT, 4)

    def test_publication_cannot_lower_frozen_repair_floor(self):
        scratch = SimpleNamespace(authorize=Mock())
        publication = dict(head_fields_wrapper=subject.source_ref(), repair_after_parent=325, P0323_preserved_no_retry=True)
        plan = dict(cumulative_caps=dict(PARENT=404430))
        subject.authorize(scratch, None, plan, publication, 'hash', 'broker', 1, 325)
        for patch_values in ({'repair_after_parent': 324}, {'head_fields_wrapper': {}}, {'P0323_preserved_no_retry': False}):
            with self.assertRaises(ValueError):
                subject.authorize(scratch, None, plan, dict(publication, **patch_values), 'hash', 'broker', 1, 325)
        with self.assertRaises(ValueError):
            subject.authorize(scratch, None, plan, dict(publication, repair_after_parent=322), 'hash', 'broker', 1, 322)

    def test_cli_missing_publication_cannot_load_or_dispatch(self):
        with (patch.object(subject.sys, 'argv', ['head', 'broker', '--expected-self-sha256', subject.sha(subject.__file__)]),
              patch.object(subject, 'dependencies', side_effect=AssertionError('no_live_action')),
              patch.dict(os.environ, CUDA_VISIBLE_DEVICES='')):
            with self.assertRaisesRegex(ValueError, 'explicit_Main_publication'):
                subject.main()


if __name__ == '__main__':
    unittest.main()
