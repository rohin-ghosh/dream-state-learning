from contextlib import nullcontext
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r168_targeted_replay as replay
from gpu import orch_r168_targeted_replay_native as integration
from gpu.astra_pchain2_native import EncodedRow


FIXTURES = Path(__file__).resolve().parents[1] / 'research_loop/workers/r168_replay_candidates_20260917'


class Finite:
    def __init__(self, value):
        self.value = math.isfinite(value)

    def __bool__(self):
        return self.value

    def all(self):
        return self.value


class Parameter:
    def __init__(self, value):
        self.value = value
        self.grad = None
        self.requires_grad = False

    def requires_grad_(self, value):
        self.requires_grad = value


class Loss:
    def __init__(self, parameter, value, weight=1):
        self.parameter = parameter
        self.value = value
        self.weight = weight

    def __mul__(self, weight):
        return Loss(self.parameter, self.value, self.weight * weight)

    def backward(self):
        self.parameter.grad = (self.parameter.grad or 0) + self.value * self.weight

    def item(self):
        return self.value


class TorchStub:
    long = 'long'
    bfloat16 = 'bfloat16'

    def tensor(self, values, *, dtype, device):
        assert dtype == self.long and device == 'cuda:0'
        return tuple(tuple(row) for row in values)

    def ones_like(self, values):
        return tuple(tuple(1 for token in row) for row in values)

    def autocast(self, **kwargs):
        assert kwargs == dict(device_type='cuda', dtype=self.bfloat16)
        return nullcontext()

    def isfinite(self, value):
        return Finite(value.value if isinstance(value, Loss) else value)


class ModelStub:
    def __init__(self):
        self.adapter = Parameter(0.2)
        self.base = Parameter(3.0)
        self.calls = []
        self.training = False

    def named_parameters(self):
        return [('lora_adapter', self.adapter), ('frozen_base', self.base)]

    def train(self):
        self.training = True

    def eval(self):
        self.training = False

    def requires_grad_(self, value):
        for name, parameter in self.named_parameters():
            parameter.requires_grad_(value)

    def __call__(self, *, input_ids, labels, attention_mask, use_cache):
        assert self.training and not use_cache and self.adapter.requires_grad and not self.base.requires_grad
        assert attention_mask == tuple(tuple(1 for token in row) for row in input_ids)
        self.calls.append(dict(input_ids=input_ids, labels=labels, attention_mask=attention_mask,
                               use_cache=use_cache))
        target = [token for token in labels[0] if token != -100]
        return SimpleNamespace(loss=Loss(self.adapter, 1 + sum(target) / (len(target) * 1000000)))


class OptimizerStub:
    def __init__(self, model):
        self.model = model
        self.traces = []
        self.fail_at = None

    def zero_grad(self, *, set_to_none):
        assert set_to_none
        self.model.adapter.grad = None

    def step(self):
        if len(self.traces) == self.fail_at:
            raise RuntimeError('injected_optimizer_failure')
        self.model.adapter.value -= self.model.adapter.grad * 0.001
        self.traces.append((self.model.adapter.value, self.model.adapter.grad))


class TokenizerStub:
    pad_token_id = None

    def __init__(self, rows):
        self.eos_token_id = rows[0]['token_ids'][-1]
        self.all_special_ids = [151644, self.eos_token_id]
        self.texts = {tuple(row['token_ids'][:-1]): row['target'] for row in rows}
        self.prompts = []

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=True, add_generation_prompt=True, return_dict=False)
        self.prompts.append(deepcopy(messages))
        return [151644] + [100 + len(message['content']) % 1000 for message in messages]

    def decode(self, tokens, **kwargs):
        assert kwargs == dict(skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return self.texts[tuple(tokens)]


class NativeReplayIntegrationTests(unittest.TestCase):
    def setUp(self):
        specification = importlib.util.spec_from_file_location('r168_bound_native_fixture',
            FIXTURES / 'NATIVE_cdb542.py')
        self.native = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.native)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.selected = json.loads((FIXTURES / 'ROW118_TRAIN_FIXTURE.json').read_text())
        self.assertEqual(replay.digest(self.selected), integration.ROW_SHA256)
        self.assertEqual(len(self.selected['token_ids']), 199)
        self.new_row = dict(deepcopy(self.selected), segment=119, event_id='child:segment:119',
            source_sha256='b' * 64, token_ids=[777, self.selected['token_ids'][-1]], target='Fresh object.')
        self.plan = dict(root=str(self.root), presleep_variant='reread_select', context_limit=16384,
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
            presentation_version='R125_PLAIN_CONTEXT_V1',
            system_prompt=self.selected['prefix'][0]['content'], birth_prompt=self.selected['prefix'][1]['content'])
        self.plan_ref = self.write(self.root / 'PLAN.json', self.plan)
        self.runtime = dict(schema='R168_NATIVE_SLEEP_RUNTIME_V1', native_sha256=integration.NATIVE_SHA256,
            arm_sha256=self.file_hash(replay.__file__), integration_sha256=self.file_hash(integration.__file__),
            dependencies={name: self.file_hash(importlib.import_module(name).__file__)
                          for name in integration.DEPENDENCIES})
        self.runtime_ref = self.write(self.root / 'RUNTIME.json', self.runtime)
        checkpoint = self.root / 'checkpoints/sleep_000040'
        checkpoint.mkdir(parents=True)
        (self.root / 'stream/records').mkdir(parents=True)
        commit = dict(adapter_path=str(checkpoint / 'adapter'), optimizer_rng_path=str(checkpoint / 'optimizer_rng.pt'),
            optimizer_steps=4000, checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='b' * 64))
        event = dict(event_id=self.selected['event_id'], actor='child', split='TRAIN', origin='TRAIN_COLLECTION',
                     text=self.selected['target'], source_sha256=self.selected['source_sha256'])
        state = dict(rows=[{} for unused in range(118)] + [deepcopy(self.selected)], pending=None,
            sleep_frontier=119, model_state_sha256=replay.digest(commit['checkpoint_sha256']),
            history=dict(events=[event]))
        boundary = dict(kind='SLEEP_COMPLETE', index=5000, journal_id='a' * 32,
            previous_sha256='b' * 64, document=dict(status='COMPLETE', cycle=40, checkpoint=commit,
            resume_state=dict(state=state, sha256=replay.digest(state))))
        boundary['sha256'] = replay.digest(boundary)
        boundary_ref = self.write(self.root / 'stream/records/00000000000000005000.json', boundary)
        commit_ref = self.write(checkpoint / 'COMMIT.json', commit)
        selection = replay.freeze_selection(own_root=self.root, boundary_ref=boundary_ref, checkpoint_ref=commit_ref,
            row_objects=[dict(segment=118, object_id='chrysanthemum-petal', selection_kind='OBJECT_REPLAY',
                             support_event_ids=[self.selected['event_id']])], dose=4,
            plan_sha256=self.plan_ref['sha256'], runtime_sha256=self.runtime_ref['sha256'], frozen_unix=90)
        self.selection_ref = self.write(self.root / 'SELECTION.json', selection)
        go = dict(schema=replay.GO_SCHEMA, action='ONE_EXPERIMENTAL_TARGETED_REPLAY_SLEEP',
            selection=self.selection_ref, approved_intake_sha256='e' * 64, not_before=100, expires=200,
            **{key: selection[key] for key in ('life_root', 'life_role', 'target_cycle', 'plan_sha256', 'runtime_sha256')})
        self.go_ref = self.write(self.root / 'GO.json', go)
        self.anchors = {}
        for position, family in enumerate(('code', 'math', 'simulated_tools', 'concise_answer')):
            self.anchors[family] = []
            for length in (position + 2, position + 3):
                tokens = tuple(range(100, 100 + length))
                self.anchors[family].append(dict(family=family, source_condition='PURE_BASE', split='TRAIN',
                    verified_competent=True, source_call_sha256='a' * 64,
                    encoded=EncodedRow(tokens, tokens, tokens)))
        self.child = self.make_child()
        self.records = []
        self.bridge = self.make_bridge()

    def file_hash(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def write(self, path, value):
        path.write_bytes(replay.encoded(value))
        return dict(path=str(path), sha256=self.file_hash(path))

    def make_child(self):
        model = ModelStub()
        child = SimpleNamespace(plan=deepcopy(self.plan), parameters={'lora_adapter': model.adapter},
            engine=SimpleNamespace(model=model), optimizer=OptimizerStub(model), optimizer_steps=4000,
            torch=TorchStub(), tokenizer=TokenizerStub([self.selected, self.new_row]),
            native=SimpleNamespace(is_lora=lambda name: name.startswith('lora_')), checks=[])
        child.adapter_hash = lambda: replay.digest(model.adapter.value)
        child.check = child.checks.append
        child.sleep = lambda new, old, anchors, record: self.native.NativeChild.sleep(
            child, new, old, anchors, record)

        def verify_base():
            self.assertEqual(model.base.value, 3)
            self.assertFalse(model.base.requires_grad)

        child.engine.verify_base = verify_base
        return child

    def make_bridge(self):
        arm = replay.SingleSleepArm(self.selection_ref, self.go_ref, approved_intake_sha256='e' * 64,
                                    now=lambda: 110)
        return integration.NativeReplaySleep(self.native, self.child, arm=arm,
            plan_ref=self.plan_ref, runtime_ref=self.runtime_ref)

    def record(self, kind, document):
        self.records.append((kind, deepcopy(document)))

    def run_target(self, **changes):
        args = dict(new_rows=[self.new_row], old_rows=[self.selected], anchors=self.anchors,
                    record=self.record, cycle=41)
        return self.bridge.sleep(**dict(args, **changes))

    def baseline(self, child=None, new_rows=None):
        child = child or self.make_child()
        records = []
        receipt = self.native.NativeChild.sleep(child, [self.new_row] if new_rows is None else new_rows,
            [self.selected], self.anchors, lambda kind, document: records.append((kind, deepcopy(document))))
        return child, receipt, records

    def test_no_arm_is_identical_and_needs_no_cycle_or_authority(self):
        child, receipt, records = self.baseline()
        bridge = integration.NativeReplaySleep(self.native, self.child)
        actual = bridge.sleep([self.new_row], [self.selected], self.anchors, self.record)
        self.assertEqual(actual, receipt)
        self.assertEqual(self.child.engine.model.calls, child.engine.model.calls)
        self.assertEqual(self.child.optimizer.traces, child.optimizer.traces)
        for expected, observed in zip(records, self.records):
            expected[1].pop('finished_unix', None)
            observed[1].pop('finished_unix', None)
        self.assertEqual(self.records, records)
        self.assertFalse((self.root / 'r168_targeted_replay').exists())

    def test_real_pinned_loop_preserves_baseline_and_finishes_four_extra_updates(self):
        child, baseline, records = self.baseline()
        original_globals = dict(self.native.__dict__)
        before_row = deepcopy(self.selected)
        receipt = self.run_target()
        self.assertEqual(self.native.__dict__, original_globals)
        self.assertEqual(self.selected, before_row)
        self.assertEqual(self.child.optimizer.traces[:17], child.optimizer.traces)
        self.assertEqual(self.child.engine.model.calls[:85], child.engine.model.calls)
        self.assertEqual(len(self.child.optimizer.traces), 21)
        self.assertEqual(len(self.child.engine.model.calls), 105)
        self.assertEqual(receipt['optimizer_steps'], 21)
        self.assertEqual(receipt['child_token_exposures'] - baseline['child_token_exposures'], 796)
        extra = [document for kind, document in self.records if kind == 'UPDATE'
                 and document['losses'][0]['kind'] == replay.EXTRA]
        self.assertEqual(len(extra), 4)
        self.assertTrue(all([loss['objective_weight'] for loss in item['losses']] == [0.75] + [0.0625] * 4
                            for item in extra))
        self.assertEqual(receipt['presentations'][integration.SOURCE_SHA256], 5)
        self.assertEqual(self.child.checks.count('microbatch'), 105)
        self.assertFalse(self.child.engine.model.training)
        self.assertFalse(self.child.engine.model.adapter.requires_grad)
        marker = self.root / 'r168_targeted_replay/sleep_000041'
        finished = json.loads((marker / 'FINISHED_UPDATES.json').read_text())
        self.assertEqual(finished, receipt['r168_targeted_replay'])
        self.assertEqual(finished['status'], 'FINISHED_UPDATES_NOT_CHECKPOINT_COMMIT')
        self.assertEqual(finished['optimizer_steps_after'], 4021)
        self.assertEqual(finished['accounting']['experimental_extra_steps'], 4)
        self.assertFalse((self.root / 'checkpoints/sleep_000041').exists())

    def test_before_and_after_target_run_original_loop_and_auto_expire(self):
        before = self.run_target(cycle=40)
        self.assertEqual(before['optimizer_steps'], 17)
        self.assertNotIn('r168_targeted_replay', before)
        self.run_target()
        after = self.run_target(cycle=42)
        self.assertEqual(after['optimizer_steps'], 17)
        self.assertNotIn('r168_targeted_replay', after)
        self.assertEqual(self.bridge.arm.status, 'EXPIRED_SINGLE_SLEEP_ARM')
        count = len(self.child.optimizer.traces)
        with self.assertRaisesRegex(ValueError, 'expired_arm_never_reactivated'):
            self.run_target()
        self.assertEqual(len(self.child.optimizer.traces), count)

    def test_new_instance_cannot_replay_consumed_target(self):
        self.run_target()
        count = len(self.child.optimizer.traces)
        self.bridge = self.make_bridge()
        with self.assertRaises(FileExistsError):
            self.run_target()
        self.assertEqual(len(self.child.optimizer.traces), count)
        self.assertTrue(self.bridge.uncertain)

    def test_native_R144_exclusion_refuses_selected_row_before_updates(self):
        self.child.tokenizer.all_special_ids.append(self.selected['token_ids'][0])
        with self.assertRaisesRegex(ValueError, 'must_pass_native_eligibility'):
            self.run_target()
        self.assertEqual(self.child.optimizer.traces, [])
        self.assertFalse((self.root / 'r168_targeted_replay').exists())
        self.assertEqual(self.bridge.arm.status, 'INACTIVE_BEFORE_TARGET_SLEEP')

    def test_plain_context_machine_scaffolding_refuses_before_updates(self):
        row = dict(self.selected, target='TRAIN_COLLECTION machine metadata')
        with self.assertRaisesRegex(ValueError, 'must_pass_native_eligibility'):
            self.run_target(old_rows=[row])
        self.assertEqual(self.child.optimizer.traces, [])

    def test_missing_new_rows_cannot_bypass_hook_into_rehearsal(self):
        with self.assertRaisesRegex(ValueError, 'must_pass_native_eligibility'):
            self.run_target(new_rows=[])
        self.assertEqual(self.child.optimizer.traces, [])
        child, baseline, records = self.baseline(new_rows=[])
        self.assertEqual(baseline['optimizer_steps'], 1)

    def test_changed_own_prefix_is_not_reencoded_as_a_new_target(self):
        row = deepcopy(self.selected)
        row['prefix'].append(dict(role='user', content='Changed conditioning.'))
        with self.assertRaisesRegex(ValueError, 'selected_row_changed'):
            self.run_target(old_rows=[row])
        self.assertEqual(self.child.optimizer.traces, [])

    def test_full_label_anchors_required(self):
        sample = self.anchors['code'][0]['encoded']
        self.anchors['code'][0]['encoded'] = EncodedRow(sample.input_ids, (-100,) + sample.labels[1:], sample.target_ids)
        with self.assertRaisesRegex(ValueError, 'full_label_native_anchors'):
            self.run_target()
        self.assertEqual(self.child.optimizer.traces, [])

    def test_plan_runtime_and_cycle_binding_before_updates(self):
        for change in ('plan', 'runtime', 'cycle', 'dose'):
            with self.subTest(change=change):
                self.bridge = self.make_bridge()
                saved_plan = deepcopy(self.child.plan)
                saved_runtime = deepcopy(self.bridge.runtime_ref)
                if change == 'plan':
                    self.child.plan['root'] = '/tmp/foreign'
                elif change == 'runtime':
                    self.bridge.runtime_ref['sha256'] = '0' * 64
                elif change == 'dose':
                    self.bridge.arm.selection['selected'][0]['extra_presentations'] = 3
                with self.assertRaises(ValueError):
                    self.run_target(cycle=True if change == 'cycle' else 41)
                self.child.plan = saved_plan
                self.bridge.runtime_ref = saved_runtime
        self.assertEqual(self.child.optimizer.traces, [])

    def test_replaced_live_native_method_is_not_admitted(self):
        with patch.object(self.native.NativeChild, 'sleep', lambda *args: None):
            with self.assertRaisesRegex(ValueError, 'live_native_method_matches_pinned_bytes'):
                self.run_target()
        self.assertEqual(self.child.optimizer.traces, [])

    def test_optimizer_failure_latches_and_never_reports_finished(self):
        self.child.optimizer.fail_at = 2
        with self.assertRaisesRegex(RuntimeError, 'injected_optimizer_failure'):
            self.run_target()
        self.assertEqual(len(self.child.optimizer.traces), 2)
        marker = self.root / 'r168_targeted_replay/sleep_000041'
        self.assertTrue((marker / 'CONSUMED.json').exists())
        self.assertTrue((marker / 'FAILED_OR_UNCERTAIN.json').exists())
        self.assertFalse((marker / 'FINISHED_UPDATES.json').exists())
        for cycle in (41, 42):
            with self.assertRaisesRegex(ValueError, 'native_replay_uncertain_no_retry'):
                self.run_target(cycle=cycle)

    def test_recorder_failure_after_real_step_latches(self):
        def fail(kind, document):
            if kind == 'UPDATE':
                raise OSError('journal_failure')
        with self.assertRaisesRegex(OSError, 'journal_failure'):
            self.run_target(record=fail)
        self.assertEqual(len(self.child.optimizer.traces), 1)
        self.assertTrue(self.bridge.uncertain)

    def test_recorder_mutation_cannot_fabricate_accounting(self):
        def change(kind, document):
            if kind == 'UPDATE':
                document['losses'][0]['target_tokens'] += 1
        with self.assertRaisesRegex(ValueError, 'update_receipt_mutated'):
            self.run_target(record=change)
        self.assertTrue(self.bridge.uncertain)

    def test_finished_receipt_write_failure_keeps_operation_consumed(self):
        original = replay.write_once

        def fail(path, value):
            if path.name == 'FINISHED_UPDATES.json':
                raise OSError('finished_receipt_failure')
            return original(path, value)

        with patch.object(replay, 'write_once', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'finished_receipt_failure'):
                self.run_target()
        self.assertEqual(len(self.child.optimizer.traces), 21)
        self.assertTrue(self.bridge.uncertain)
        self.assertTrue((self.root / 'r168_targeted_replay/sleep_000041/CONSUMED.json').exists())

    def test_expired_GO_refuses_before_any_update(self):
        self.bridge.arm.now = lambda: 201
        with self.assertRaisesRegex(ValueError, 'current_replay_GO'):
            self.run_target()
        self.assertEqual(self.child.optimizer.traces, [])
        self.assertEqual(self.child.engine.model.calls, [])

    def test_existing_target_checkpoint_refuses_before_any_update(self):
        (self.root / 'checkpoints/sleep_000041').mkdir()
        with self.assertRaisesRegex(ValueError, 'existing_target_checkpoint_never_replayed'):
            self.run_target()
        self.assertEqual(self.child.optimizer.traces, [])

    def test_base_verification_failure_after_updates_is_not_finished(self):
        def fail():
            raise ValueError('base_verification_failed')
        self.child.engine.verify_base = fail
        with self.assertRaisesRegex(ValueError, 'base_verification_failed'):
            self.run_target()
        self.assertEqual(len(self.child.optimizer.traces), 21)
        self.assertTrue(self.bridge.uncertain)
        self.assertFalse((self.root / 'r168_targeted_replay/sleep_000041/FINISHED_UPDATES.json').exists())

    def test_no_arm_empty_sleep_keeps_original_no_update_receipt(self):
        bridge = integration.NativeReplaySleep(self.native, self.child)
        receipt = bridge.sleep([], [], self.anchors, self.record)
        self.assertEqual(receipt['optimizer_steps'], 0)
        self.assertEqual(receipt['no_update_reason'], 'no_eligible_child_rows')
        self.assertNotIn('r168_targeted_replay', receipt)
        self.assertEqual(self.child.optimizer.traces, [])

    def test_finished_receipt_binding_does_not_alias_mutable_configuration(self):
        receipt = self.run_target()
        before = deepcopy(receipt['r168_targeted_replay'])
        self.bridge.plan_ref['path'] = '/tmp/changed'
        self.bridge.arm.main_go_ref['path'] = '/tmp/changed-go'
        self.assertEqual(receipt['r168_targeted_replay'], before)

    def completion_stubs(self, fail_checkpoint=False, fail_journal=False):
        stream = SimpleNamespace(rows=[self.selected, self.new_row], sleep_frontier=1,
            pending='sleep:' + replay.digest([self.new_row['source_sha256']]), experiment='fixture', receipts=[])
        stream.pending_rows = lambda: [self.new_row]

        def checkpoint(path):
            if fail_checkpoint:
                raise OSError('checkpoint_failure')
            path.mkdir()
            result = dict(experiment='fixture', optimizer_steps=self.child.optimizer_steps,
                checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='b' * 64))
            self.write(path / 'COMMIT.json', result)
            return result

        def commit_sleep(receipt, record):
            if fail_journal:
                raise OSError('sleep_commit_failure')
            stream.receipts.append(deepcopy(receipt))
            stream.sleep_frontier = len(stream.rows)
            record('SLEEP_COMPLETE', deepcopy(receipt))

        self.child.checkpoint = checkpoint
        stream.commit_sleep = commit_sleep
        return stream, SimpleNamespace(record=self.record)

    def test_pinned_finish_sleep_preserves_checkpoint_then_completion_order(self):
        stream, journal = self.completion_stubs()
        checkpoint = self.bridge.finish_sleep(stream, journal, self.anchors, self.root, 41)
        self.assertEqual(checkpoint['optimizer_steps'], 4021)
        self.assertIsNone(stream.pending)
        self.assertEqual(self.records[-1][0], 'SLEEP_COMPLETE')
        self.assertEqual(stream.receipts[0]['r168_targeted_replay']['accounting']['experimental_extra_steps'], 4)
        self.assertTrue((self.root / 'checkpoints/sleep_000041/COMMIT.json').exists())

    def test_no_arm_finish_sleep_uses_original_baseline_without_binding_reads(self):
        stream, journal = self.completion_stubs()
        bridge = integration.NativeReplaySleep(self.native, self.child)
        with patch.object(bridge, '_bind', side_effect=AssertionError('disabled_arm_must_not_bind')):
            checkpoint = bridge.finish_sleep(stream, journal, self.anchors, self.root, 41)
        self.assertEqual(checkpoint['optimizer_steps'], 4017)
        self.assertEqual(stream.receipts[0]['optimizer_steps'], 17)
        self.assertNotIn('r168_targeted_replay', stream.receipts[0])
        self.assertFalse((self.root / 'r168_targeted_replay').exists())

    def test_missed_cycle_does_not_catch_up(self):
        receipt = self.run_target(cycle=42)
        self.assertEqual(receipt['optimizer_steps'], 17)
        self.assertEqual(self.bridge.arm.status, 'EXPIRED_SINGLE_SLEEP_ARM')
        self.assertFalse((self.root / 'r168_targeted_replay').exists())
        with self.assertRaisesRegex(ValueError, 'expired_arm_never_reactivated'):
            self.run_target()
        self.assertEqual(len(self.child.optimizer.traces), 17)

    def assert_completion_failure_latches(self, failure):
        stream, journal = self.completion_stubs(fail_checkpoint=failure == 'checkpoint',
                                                fail_journal=failure == 'journal')
        with self.assertRaises(OSError):
            self.bridge.finish_sleep(stream, journal, self.anchors, self.root, 41)
        self.assertEqual(len(self.child.optimizer.traces), 21)
        self.assertTrue(self.bridge.uncertain)
        self.assertTrue((self.root / 'r168_targeted_replay/sleep_000041/FAILED_OR_UNCERTAIN.json').exists())
        self.assertFalse(any(kind == 'SLEEP_COMPLETE' for kind, document in self.records))
        with self.assertRaisesRegex(ValueError, 'native_replay_uncertain_no_retry'):
            self.bridge.finish_sleep(stream, journal, self.anchors, self.root, 42)

    def test_checkpoint_failure_after_updates_latches(self):
        self.assert_completion_failure_latches('checkpoint')

    def test_sleep_journal_failure_after_updates_latches(self):
        self.assert_completion_failure_latches('journal')

    def test_finish_sleep_rejects_foreign_checkpoint_root(self):
        stream, journal = self.completion_stubs()
        with self.assertRaisesRegex(ValueError, 'exact_own_checkpoint_root'):
            self.bridge.finish_sleep(stream, journal, self.anchors, self.root / 'foreign', 41)
        self.assertEqual(self.child.optimizer.traces, [])

    def test_actual_suffix_helper_still_rejects_EXTRA_and_unknown_kinds(self):
        from gpu import orch_r145_suffix_boundary as boundary

        class Labels:
            def __getitem__(self, indices):
                self_rows, columns = indices
                return (tuple(sample.labels[columns]),)

        sample = self.native.encode_own(self.selected, self.child.tokenizer, 16384)
        labels = Labels()
        expected = boundary.loss_arguments('REHEARSAL', sample, labels)
        self.assertEqual(expected['logits_to_keep'], 200)
        self.assertEqual(expected['labels'], ((-100,) + tuple(self.selected['token_ids']),))
        self.assertEqual(boundary.loss_arguments('NEW', sample, labels), expected)
        self.assertIs(boundary.loss_arguments('ANCHOR:code', sample, labels)['labels'], labels)
        for kind in (replay.EXTRA, 'UNKNOWN', 'REHEARSAL_OTHER'):
            with self.assertRaisesRegex(ValueError, 'known_child_presentation_kind'):
                boundary.loss_arguments(kind, sample, labels)
        self.run_target()
        self.assertTrue(any(document['losses'][0]['kind'] == replay.EXTRA
                            for kind, document in self.records if kind == 'UPDATE'))
        with self.assertRaisesRegex(ValueError, 'known_child_presentation_kind'):
            boundary.loss_arguments(replay.EXTRA, sample, labels)

    def test_suffix_patched_source_is_refused_not_silently_run(self):
        from gpu import orch_r145_suffix_boundary as boundary
        path = self.root / 'unsupported_suffix_native.py'
        source = (FIXTURES / 'NATIVE_cdb542.py').read_text()
        self.assertNotIn('r145_loss_arguments', source)
        self.assertEqual(source.count(boundary.OLD_FORWARD), 1)
        source = source.replace(boundary.OLD_FORWARD, boundary.NEW_FORWARD)
        path.write_text(source)
        specification = importlib.util.spec_from_file_location('unsupported_suffix_native', path)
        prospective = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(prospective)
        self.bridge.native = prospective
        with self.assertRaisesRegex(ValueError, 'native_source_pin'):
            self.run_target()
        self.assertEqual(self.child.optimizer.traces, [])
        self.assertEqual(self.child.engine.model.calls, [])
        self.assertFalse((self.root / 'r168_targeted_replay').exists())


if __name__ == '__main__':
    unittest.main()
