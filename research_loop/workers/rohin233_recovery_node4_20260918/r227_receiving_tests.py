"""Synthetic CPU tests against a copied, source-pinned receiving closure."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import Mock, patch


parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--original', type=Path, required=True)
parser.add_argument('--plan', type=Path, required=True)
parser.add_argument('--support', type=Path, required=True)
parser.add_argument('--life', choices=('P7', 'C2', 'P3'), required=True)
arguments = parser.parse_args()
sys.path[:0] = [str(arguments.source), str(arguments.source / 'tests'), str(arguments.support)]
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
import r227_sleep_fixture as fixture
import test_orch_r184_think_act_learn as stage_fixture
from gpu import orch_r125_continual_native as native
from gpu import orch_r184_think_act_learn as driver_module
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6.orch_r125_plain_context import VERSION
from organism_v6.orch_r227_learning_policy import POLICY


class ExactChild(stage_fixture.Child):
    def generate(self, messages, **limits):
        self.calls.append(messages)
        text = next(self.outputs)
        return dict(raw=text, token_ids=[ord(character) + 100 for character in text] + [2],
            terminal=True, truncated=False)


class ReceivingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.stage = stage_fixture.ThinkActLearnTests()
        self.stage.setUp()
        self.addCleanup(self.stage.doCleanups)
        self.plan = json.loads(arguments.plan.read_bytes())

    def driver(self, texts, console=False):
        config = dict(self.stage.config, learn_row_policy=POLICY,
            learn_review_filter='R195_CHILD_ROW_REVIEW_V1',
            content_target_filter='R213_CONTENT_BEARING_TARGETS_V1')
        if console:
            config.update(console_reply_policy='R205_CONSOLE_REPLY_ACT_V1',
                pinned_messages_policy='R206_VERBATIM_ROHIN_MESSAGES_V1',
                stage_boundary_policy='R203_STAGE_BOUNDARIES_V1')
        return driver_module.ThinkActLearn(ExactChild(texts), self.stage.stream, self.stage.journal, config)

    def test_actual_receiving_plan_and_driver_validate_consistently(self):
        before = deepcopy(self.plan)
        self.assertIs(native.validate_plan(self.plan), self.plan)
        config = driver_module.validate_config(self.plan['think_act_learn'])
        self.assertEqual(config['learn_row_policy'], POLICY)
        self.assertEqual(self.plan, before)
        self.assertNotIn('language_target_policy', config)
        self.assertEqual(config['code_policy'], 'R194_FIRST_CODE_BLOCK_NFKC_V1')
        if arguments.life == 'C2':
            self.assertEqual(config['deep_work_policy'], 'R222_DEEP_WORK_DISCUSSION_V1')
        broken = deepcopy(self.plan)
        broken['think_act_learn'].pop('learn_row_policy')
        with self.assertRaisesRegex(ValueError, 'same_learn_row_policy'):
            native.validate_plan(broken)

    def test_no_semantic_rejection_of_authentic_rows_or_historical_annotations(self):
        child, anchors = fixture.child_fixture()
        child.plan.update(learn_row_policy=POLICY, learn_review_filter='R195_CHILD_ROW_REVIEW_V1',
            presentation_version=VERSION, system_prompt=native.SYSTEM, birth_prompt=native.BIRTH)
        texts = ['中文也是自己的话。这个叶子让我想到隔离。', '我会继续思考然后完成。',
            '```python\nprint(１ + ２)\n```', 'Ｆｕｌｌｗｉｄｔｈ own prose！',
            'word word word word word word', 'one two three one two three one two three one two three',
            'Rohin: Imagined speech by the child.', 'source_sha256: ordinary own words',
            'Do not train: self - requested by child', '```story\nThe leaf stayed beside the door.\n```']
        rows = [fixture.row(str(index), text, content_target_filter='R213_CONTENT_BEARING_TARGETS_V1',
            learn_review=dict(eligible=False, reason='historical_annotation')) for index, text in enumerate(texts)]
        before = deepcopy(rows)
        with patch('organism_v6.orch_r194_code_target_filter.filter_learn_review_targets',
                side_effect=AssertionError('semantic review ran')), patch(
                'organism_v6.orch_r194_code_target_filter.filter_sleep_targets',
                side_effect=AssertionError('glyph filter ran')):
            receipt, records = fixture.run_sleep(child, anchors, rows)
        self.assertEqual(rows, before)
        self.assertEqual(receipt['excluded_rows'], [])
        self.assertEqual(receipt['optimizer_steps'], 16 * len(rows))
        self.assertEqual(receipt['presentations'], {row['source_sha256']:16 for row in rows})
        for kind, document in records:
            if kind in ('SLEEP_RECIPE', 'TARGET_ELIGIBILITY'):
                self.assertEqual(document['active_semantic_filters'], [])
                self.assertFalse(document['semantic_row_exclusion'])
        self.assertEqual(receipt['historical_row_annotations'], 'PRESERVED_NOT_APPLIED')

    def test_actual_stage_rows_reach_optimizer_without_LEARN_veto(self):
        driver = self.driver(['中文含有正常标点。', 'A repeated word word word word word.',
            'Do not train: self - I would exclude my own row.'])
        for stage in ('THINK','ACT','LEARN'):
            driver.generate_stage(stage)
        self.assertFalse(self.stage.records('R195_LEARN_REVIEW'))
        rows = self.stage.stream.pending_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['prefix_loss'] is False and row['actor']=='child' for row in rows))
        child, anchors = fixture.child_fixture()
        child.plan['learn_row_policy'] = POLICY
        receipt, records = fixture.run_sleep(child, anchors, rows)
        self.assertEqual(receipt['optimizer_steps'], 48)
        self.assertEqual(receipt['excluded_rows'], [])

    def test_console_pinning_and_own_reply_training_are_preserved(self):
        publication = publish_parent(self.stage.root, 'Rohin', 'Tell me your actual answer.')
        path = self.stage.root / 'stream/inbox' / (publication['id'] + '.json')
        before = path.read_bytes()
        driver = self.driver(['我自己的回答。', 'I will think more.'], console=True)
        driver.generate_stage('THINK')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(self.stage.records('R205_CONSOLE_REPLY')), 1)
        self.assertTrue(all(row['actor']=='child' and row['prefix_loss'] is False for row in self.stage.stream.rows))
        child, anchors = fixture.child_fixture()
        child.plan['learn_row_policy'] = POLICY
        receipt, records = fixture.run_sleep(child, anchors, self.stage.stream.rows)
        self.assertEqual(receipt['optimizer_steps'], 32)
        self.assertEqual(receipt['excluded_rows'], [])

    def test_provenance_and_special_token_protection_remain(self):
        for changes, reason in ((dict(actor='parent'), 'child_targets_only'),
                (dict(prefix_loss=True), 'child_targets_only'),
                (dict(target='Changed text.'), 'native_target_roundtrip')):
            with self.subTest(changes=changes):
                child, anchors = fixture.child_fixture()
                child.plan['learn_row_policy'] = POLICY
                row = fixture.row('bad', 'Original text.')
                row.update(changes)
                with self.assertRaisesRegex(ValueError, reason):
                    fixture.run_sleep(child, anchors, [row])
                child.optimizer.step.assert_not_called()
        child, anchors = fixture.child_fixture()
        child.plan['learn_row_policy'] = POLICY
        receipt, records = fixture.run_sleep(child, anchors,
            [fixture.row('safe', 'Own words.'), fixture.row('invalid', token_ids=[1,2])])
        self.assertEqual(receipt['optimizer_steps'], 16)
        self.assertEqual(receipt['excluded_rows'][0]['reason'], 'no_special_token_target_injection')

    def test_actual_CPU_bridge_and_generic_root_policy_forward_unchanged(self):
        driver = object.__new__(driver_module.ThinkActLearn)
        driver.config = driver_module.validate_config(self.plan['think_act_learn'])
        driver.journal = self.stage.journal
        origin = dict(kind='TRAIN_CHILD_RESPONSE', source_sha256='a'*64)
        with patch('gpu.r184_cpu_bridge.call', return_value=dict(receipt='mocked_not_executed')) as call:
            result = driver._cpu(origin)
            call.assert_called_once_with(driver.config, origin)
        self.assertEqual(result['receipt'], 'mocked_not_executed')
        driver.config = dict(driver.config, trial_id='synthetic_generic_life')
        from gpu.orch_r153_community_transport import EXISTING_LIFE_CPU_POLICY
        with patch('gpu.orch_r153_community_transport.cpu_once', return_value={}) as call:
            driver._cpu(origin)
            self.assertEqual(call.call_args.kwargs['root_policy'], EXISTING_LIFE_CPU_POLICY)
            self.assertEqual(call.call_args.kwargs['code_policy'], 'R194_FIRST_CODE_BLOCK_NFKC_V1')

    def test_AdamW_checkpoint_history_rng_and_next_new_only_sleep(self):
        original = fixture.JournalTests()
        original.setUp()
        self.addCleanup(original.doCleanups)
        child = original.child
        child.plan['learn_row_policy'] = POLICY
        child.optimizer = torch.optim.AdamW(child.parameters.values(), lr=3e-5)
        original.step('中文第一行。')
        original.step('Do not train: self - a literal own request.')
        before = deepcopy(original.stream.rows)
        history = original.stream.history.checkpoint()
        cpu_rng, python_rng = torch.get_rng_state().clone(), random.getstate()
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            checkpoint = native.finish_sleep(child, original.stream, original.journal, original.anchors, original.root, 1)
        native.NativeChild.verify_checkpoint(checkpoint)
        self.assertEqual(original.stream.rows, before)
        self.assertEqual(original.stream.history.checkpoint(), history)
        self.assertEqual(original.stream.sleep_receipts[-1]['optimizer_steps'], 32)
        payload = torch.load(checkpoint['optimizer_rng_path'], weights_only=False, map_location='cpu')
        self.assertTrue(torch.equal(payload['cpu_rng'], cpu_rng))
        self.assertEqual(payload['python_rng'], python_rng)
        self.assertEqual(payload['optimizer_steps'], child.optimizer_steps)
        original.journal.audit()
        original.journal.close()
        original.journal = StreamJournal(original.root / 'stream')
        original.stream = ContinualStream.restore(**original.journal.latest_checkpoint())
        original.child, original.anchors = fixture.child_fixture()
        original.child.plan['learn_row_policy'] = POLICY
        original.child.engine.model.load_state_dict(torch.load(Path(checkpoint['adapter_path']) /
            'synthetic_adapter.pt', weights_only=True, map_location='cpu'))
        original.child.optimizer = torch.optim.AdamW(original.child.parameters.values(), lr=3e-5)
        original.child.optimizer.load_state_dict(payload['optimizer'])
        original.child.optimizer_steps = payload['optimizer_steps']
        self.assertEqual(original.child.adapter_hash(), checkpoint['adapter_state_sha256'])
        original.step('Only this new own row.')
        original.step('And this new row.')
        with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
            following = native.finish_sleep(original.child, original.stream, original.journal,
                original.anchors, original.root, 2)
        self.assertEqual(following['optimizer_steps'], checkpoint['optimizer_steps']+32)
        self.assertEqual(original.stream.rows[:2], before)
        original.journal.audit()

    def test_only_declared_source_functions_changed(self):
        allowed = {'gpu/orch_r125_continual_native.py': {'validate_plan','NativeChild.sleep','candidate_row_filter_policies'},
            'gpu/orch_r184_think_act_learn.py': {'validate_config','run_loop'},
            'organism_v6/orch_r125_plain_context.py': {'eligible_rows'}}
        manifest = json.loads((arguments.original/'PINNED_SOURCE_MANIFEST.json').read_bytes())
        for relative, expected in manifest['source_pins'].items():
            original = arguments.original/relative
            actual = arguments.source/relative
            if relative not in allowed:
                self.assertEqual(hashlib.sha256(actual.read_bytes()).hexdigest(), expected, relative)
                continue
            def functions(path):
                found = {}
                for node in ast.parse(path.read_text()).body:
                    if isinstance(node, (ast.FunctionDef,ast.AsyncFunctionDef)):
                        found[node.name] = ast.dump(node)
                    elif isinstance(node, ast.ClassDef):
                        for method in node.body:
                            if isinstance(method, (ast.FunctionDef,ast.AsyncFunctionDef)):
                                found[node.name+'.'+method.name] = ast.dump(method)
                return {name:body for name,body in found.items() if name not in allowed[relative]}
            self.assertEqual(functions(original), functions(actual), relative)


if __name__ == '__main__':
    for module in (native, driver_module):
        if not Path(module.__file__).resolve().is_relative_to(arguments.source.resolve()):
            raise RuntimeError('tests_must_import_exact_receiving_source')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReceivingPolicyTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(dict(life=arguments.life, source=str(arguments.source), ran=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), GPU_science_run=False,
        actual_live_adoption=False)), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
