"""Synthetic CPU fixtures only; no child targets, tasks or model execution."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from organism_v6 import orch_guided_bridge as bridge
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


def digest(text):
    return sha256(text.encode()).hexdigest()


class GuidedBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.initial = self.adapter(self.root / 'initial-37ec', 'synthetic-initial')
        self.contract = bridge.CallerContract(1452, 4, 'RESET_EACH_CYCLE', json.dumps(dict(
            optimizer='AdamW', optimizer_kwargs=dict(betas=[0.9, 0.999], eps=1e-8,
                weight_decay=0.01, amsgrad=False, foreach=False, fused=False),
            learning_rate=3e-5, seed=0, native_protocol_sha256=digest('synthetic-protocol'))))

    def adapter(self, path, name, base=None):
        path.mkdir(parents=True, exist_ok=True)
        (path / 'adapter_config.json').write_text('{"fixture":true}')
        (path / 'adapter.bin').write_bytes(name.encode())
        files = tuple((filename, bridge.file_sha256(path / filename))
                      for filename in ('adapter_config.json', 'adapter.bin'))
        return bridge.AdapterIdentity(str(path), digest(name), base or digest('frozen-base'), files)

    def lineage(self, arm=bridge.ARMS[0]):
        return bridge.ArmLineage('synthetic-run', arm, str(self.root / 'outputs'), self.initial)

    def output(self, plan):
        if plan.lineage.arm == bridge.ARMS[1]:
            return self.initial
        return self.adapter(Path(plan.output_path), plan.lineage.arm + '-' + str(plan.cycle))

    def receipt(self, plan, output=None, mutate=None):
        output = self.output(plan) if output is None else output
        document = dict(schema='ORCH_GUIDED_BRIDGE_COMPLETION_V1', status='COMPLETE',
            plan_sha256=bridge.document_sha256(plan.document()), run_id=plan.lineage.run_id,
            arm=plan.lineage.arm, cycle=plan.cycle, input_adapter=plan.input_adapter.document(),
            output_adapter=output.document(), contract=plan.contract.manifest(plan.lineage.arm))
        if mutate:
            mutate(document)
        path = Path(plan.lineage.output_root) / plan.lineage.run_id / plan.lineage.arm / ('cycle-' + str(plan.cycle)) / 'COMPLETE.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))
        return bridge.ReceiptRef(str(path), bridge.file_sha256(path))

    def capture(self, binding):
        return dict(run_id=binding.run_id, arm=binding.arm, cycle=binding.cycle,
            actor=binding.adapter.document(), origin='ACTUAL_CHILD_OUTPUT', complete=True,
            admitted=True, error=None, student_prefix=[dict(role='system', content='fixture system'),
                dict(role='user', content='fixture public input')], response=dict(raw='fixture child bytes\nλ'))

    def test_three_cycles_all_arms_bind_collection_training_and_fresh_readout(self):
        seen = set()
        for arm in bridge.ARMS:
            lineage, current = self.lineage(arm), self.initial
            before = bridge.initial_readout(lineage, self.contract)
            self.assertEqual(before.adapter, self.initial)
            self.assertEqual(before.cycle, 0)
            for cycle in range(1, 4):
                plan = bridge.plan_cycle(lineage, self.contract)
                self.assertEqual(plan.cycle, cycle)
                collection = plan.binding('collection')
                self.assertEqual(collection.adapter, current)
                self.assertEqual(collection.parent_present, arm != bridge.ARMS[2])
                collection.verify_loaded(adapter=current, base_sha256=self.initial.base_sha256,
                    parent_present=arm != bridge.ARMS[2], fresh_process=False, transient_context=(), sleep_prompt=None)
                if arm == bridge.ARMS[1]:
                    self.assertEqual(current, self.initial)
                    with self.assertRaisesRegex(ValueError, 'frozen_training'):
                        plan.binding('training')
                else:
                    training = plan.binding('training')
                    self.assertEqual(training.adapter, current)
                    self.assertFalse(training.parent_present)
                    training.verify_loaded(adapter=current, base_sha256=self.initial.base_sha256,
                        parent_present=False, fresh_process=False, transient_context=(), sleep_prompt=None)
                    self.assertEqual(plan.contract.manifest(arm)['optimizer_lifecycle'], 'RESET_EACH_CYCLE')
                lineage, readout = bridge.complete_cycle(plan, self.receipt(plan))
                current = readout.adapter
                readout.verify_loaded(adapter=current, base_sha256=self.initial.base_sha256,
                                      parent_present=False, fresh_process=True, transient_context=(), sleep_prompt=None)
                self.assertEqual(readout.phase, 'sealed_readout')
                if arm != bridge.ARMS[1]:
                    self.assertNotIn(current.path, seen)
                    seen.add(current.path)
            with self.assertRaisesRegex(ValueError, 'three_cycles'):
                bridge.plan_cycle(lineage, self.contract)
        self.assertEqual(len(seen), 6)

    def test_dose_uses_released_layout_and_declares_reset_not_restore(self):
        for presentations, updates in ((4, 2928), (16, 11712)):
            contract = replace(self.contract, trajectory_presentations=presentations)
            manifest = contract.manifest(bridge.ARMS[0])
            layout = GoalReplayLayout(1452, presentations)
            self.assertEqual(manifest['declared_layout'], layout.manifest('FULL_TARGET'))
            self.assertEqual(manifest['executed_updates'], updates)
            self.assertEqual(manifest['executed_new_presentations'], 1452 * presentations)
            self.assertIsNone(manifest['optimizer_checkpoint'])
            for update in range(1, updates + 1):
                self.assertEqual(len(layout.training_indexes(update)), 4)
            frozen = contract.manifest(bridge.ARMS[1])
            self.assertEqual(frozen['executed_updates'], 0)
            self.assertEqual(frozen['executed_new_presentations'], 0)
            self.assertEqual(frozen['optimizer_lifecycle'], 'NONE')
        with self.assertRaisesRegex(ValueError, 'restore_not_implemented'):
            replace(self.contract, optimizer_lifecycle='RESTORE_EACH_CYCLE').manifest(bridge.ARMS[0])

    def test_zero_yield_and_undeclared_recipe_fail(self):
        for changes in (dict(new_trajectory_rows=0), dict(trajectory_presentations=True),
                        dict(recipe_json='{}'), dict(family_status='APPROVED')):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bridge.plan_cycle(self.lineage(), replace(self.contract, **changes))

    def test_optimizer_defaults_cannot_be_silently_inherited(self):
        recipe = json.loads(self.contract.recipe_json)
        del recipe['optimizer_kwargs']['weight_decay']
        with self.assertRaisesRegex(ValueError, 'all_adamw_options'):
            replace(self.contract, recipe_json=json.dumps(recipe)).manifest(bridge.ARMS[0])
        recipe = json.loads(self.contract.recipe_json)
        recipe['optimizer_kwargs']['eps'] = float('inf')
        with self.assertRaisesRegex(ValueError, 'invalid_adamw'):
            replace(self.contract, recipe_json=json.dumps(recipe)).manifest(bridge.ARMS[0])

    def test_completion_receipt_rejects_foreign_stale_incomplete_and_recipe_drift(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        changes = dict(status='RUNNING', schema='FOREIGN', arm=bridge.ARMS[2],
                       run_id='other-run', cycle=0, plan_sha256=digest('foreign'),
                       input_adapter=self.adapter(self.root / 'foreign', 'foreign').document(), contract={})
        for field, value in changes.items():
            with self.subTest(field=field):
                reference = self.receipt(plan, mutate=lambda doc: doc.update({field: value}))
                with self.assertRaises(ValueError):
                    bridge.complete_cycle(plan, reference)
        with self.assertRaises(ValueError):
            bridge.complete_cycle(plan, self.receipt(plan, mutate=lambda doc: doc.update(cycle=True)))

    def test_receipt_hash_and_path_identity(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        reference = self.receipt(plan)
        copied = self.root / 'copied.json'
        copied.write_bytes(Path(reference.path).read_bytes())
        with self.assertRaisesRegex(ValueError, 'receipt_path'):
            bridge.complete_cycle(plan, replace(reference, path=str(copied)))
        Path(reference.path).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'receipt_hash_drift'):
            bridge.complete_cycle(plan, reference)

    def test_prior_receipt_and_adapter_mutation_prevent_next_cycle(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        reference = self.receipt(plan)
        lineage, readout = bridge.complete_cycle(plan, reference)
        next_plan = bridge.plan_cycle(lineage, self.contract)
        Path(reference.path).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'receipt_hash_drift'):
            next_plan.binding('collection')
        reference = self.receipt(plan)
        lineage, readout = bridge.complete_cycle(plan, reference)
        (Path(readout.adapter.path) / 'adapter.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'file_hash_drift'):
            bridge.plan_cycle(lineage, self.contract)

    def test_no_accidental_37ec_reset_or_relabelled_initial_files(self):
        first = bridge.plan_cycle(self.lineage(), self.contract)
        lineage, _ = bridge.complete_cycle(first, self.receipt(first))
        second = bridge.plan_cycle(lineage, self.contract)
        with self.assertRaisesRegex(ValueError, 'output_path'):
            bridge.complete_cycle(second, self.receipt(second, self.initial))
        copied_initial = self.adapter(Path(second.output_path), 'synthetic-initial')
        with self.assertRaisesRegex(ValueError, 'reset_or_stale'):
            bridge.complete_cycle(second, self.receipt(second, replace(copied_initial, state_sha256=digest('fake-new-state'))))
        with self.assertRaisesRegex(ValueError, 'stale_or_forged'):
            replace(second, input_adapter=self.initial).binding('training')

    def test_cross_arm_and_cross_cycle_receipts_rejected(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        reference = self.receipt(plan)
        lineage, _ = bridge.complete_cycle(plan, reference)
        with self.assertRaises(ValueError):
            bridge.plan_cycle(replace(lineage, arm=bridge.ARMS[2]), self.contract)
        with self.assertRaises(ValueError):
            bridge.plan_cycle(replace(lineage, receipts=(reference, reference)), self.contract)
        with self.assertRaises(ValueError):
            bridge.plan_cycle(lineage, replace(self.contract, trajectory_presentations=16))

    def test_base_drift_and_foreign_adapter_path_rejected(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        output = self.output(plan)
        with self.assertRaisesRegex(ValueError, 'base_identity'):
            bridge.complete_cycle(plan, self.receipt(plan, replace(output, base_sha256=digest('changed-base'))))
        foreign = self.adapter(self.root / 'foreign-output', 'foreign-weights')
        with self.assertRaisesRegex(ValueError, 'output_path'):
            bridge.complete_cycle(plan, self.receipt(plan, foreign))

    def test_frozen_cannot_change_state_or_weights(self):
        plan = bridge.plan_cycle(self.lineage(bridge.ARMS[1]), self.contract)
        with self.assertRaisesRegex(ValueError, 'frozen_weights'):
            bridge.complete_cycle(plan, self.receipt(plan, replace(self.initial, state_sha256=digest('changed'))))

    def test_file_manifest_traversal_alias_extra_missing_and_hash_drift(self):
        for files in ((('../outside', digest('outside')),), (('adapter.bin', digest('wrong')),),
                      self.initial.files + (self.initial.files[0],), self.initial.files[:1]):
            with self.subTest(files=files), self.assertRaises(ValueError):
                replace(self.initial, files=files).verify()
        alias = self.root / 'alias'
        alias.symlink_to(self.initial.path, target_is_directory=True)
        with self.assertRaises(ValueError):
            replace(self.initial, path=str(alias)).verify()
        (Path(self.initial.path) / 'extra.bin').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'exact_adapter_manifest'):
            self.initial.verify()

    def test_readout_rejects_parent_stale_state_base_and_nonfresh_process(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        _, readout = bridge.complete_cycle(plan, self.receipt(plan))
        arguments = dict(adapter=readout.adapter, base_sha256=self.initial.base_sha256,
                         parent_present=False, fresh_process=True, transient_context=(), sleep_prompt=None)
        for changes in (dict(adapter=self.initial), dict(base_sha256=digest('other-base')),
                        dict(parent_present=True), dict(fresh_process=False),
                        dict(transient_context=('old conversation',)), dict(sleep_prompt='old sleep instruction')):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                readout.verify_loaded(**dict(arguments, **changes))

    def test_readout_rechecks_completion_receipt_before_use(self):
        plan = bridge.plan_cycle(self.lineage(), self.contract)
        reference = self.receipt(plan)
        _, readout = bridge.complete_cycle(plan, reference)
        Path(reference.path).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'receipt_hash_drift'):
            readout.verify_loaded(adapter=readout.adapter, base_sha256=self.initial.base_sha256,
                                  parent_present=False, fresh_process=True, transient_context=(), sleep_prompt=None)

    def test_projection_preserves_exact_child_bytes_and_public_prefix(self):
        binding = bridge.plan_cycle(self.lineage(), self.contract).binding('collection')
        capture = self.capture(binding)
        before = deepcopy(capture)
        row = bridge.project_child_capture(capture, bridge.document_sha256(capture), binding,
                                          private_guidance=('private fixture instruction',))
        self.assertEqual(row['assistant'].encode(), capture['response']['raw'].encode())
        self.assertEqual(row['prefix'], capture['student_prefix'])
        row['prefix'][0]['content'] = 'edited'
        self.assertEqual(capture, before)

    def test_parent_text_is_rejected_not_removed_from_prefix_or_target(self):
        binding = bridge.plan_cycle(self.lineage(), self.contract).binding('collection')
        for location in ('prefix', 'target'):
            for forbidden in ('private fixture instruction', 'PARENT PROCEDURAL GUIDANCE'):
                capture = self.capture(binding)
                if location == 'prefix':
                    capture['student_prefix'][1]['content'] += forbidden
                else:
                    capture['response']['raw'] += forbidden
                before = deepcopy(capture)
                with self.assertRaisesRegex(ValueError, 'parent_text'):
                    bridge.project_child_capture(capture, bridge.document_sha256(capture), binding,
                                                 private_guidance=('private fixture instruction',))
                self.assertEqual(capture, before)

    def test_projection_rejects_foreign_or_unadmitted_capture(self):
        binding = bridge.plan_cycle(self.lineage(), self.contract).binding('collection')
        changes = dict(arm=bridge.ARMS[2], cycle=2, origin='HAND_AUTHORED', complete=False,
                       admitted=False, error='failed', actor={})
        for field, value in changes.items():
            capture = dict(self.capture(binding), **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                bridge.project_child_capture(capture, bridge.document_sha256(capture), binding,
                                             private_guidance=('private fixture instruction',))
        with self.assertRaisesRegex(ValueError, 'capture_hash'):
            bridge.project_child_capture(self.capture(binding), digest('wrong'), binding,
                                         private_guidance=('private fixture instruction',))

    def test_unparented_record_projection_requires_empty_guidance_inventory(self):
        binding = bridge.plan_cycle(self.lineage(bridge.ARMS[2]), self.contract).binding('collection')
        capture = dict(self.capture(binding), origin='CHILD_PRODUCED_RECORD')
        row = bridge.project_child_capture(capture, bridge.document_sha256(capture), binding, private_guidance=())
        self.assertEqual(row['assistant'], capture['response']['raw'])
        with self.assertRaisesRegex(ValueError, 'visibility'):
            bridge.project_child_capture(capture, bridge.document_sha256(capture), binding, private_guidance=('parent',))

    def test_existing_mask_validator_integration_at_explicit_boundary(self):
        from gpu.astra_reader_audit_lesson_train import validate_masks

        encoded = SimpleNamespace(input_ids=(9, 10, 42, 43, 151645, 11),
                                  labels=(-100, -100, 42, 43, 151645, -100), target_ids=(42, 43, 151645))
        arguments = dict(prefix_ids=(9, 10), target_ids=(42, 43), suffix_ids=(11,),
                         eos_token_id=151645, validate_masks=validate_masks)
        bridge.validate_encoding_boundary(encoded, **arguments)
        for changes in (dict(labels=(9, -100, 42, 43, 151645, -100)),
                        dict(labels=(-100, -100, 42, 43, -100, -100)),
                        dict(input_ids=(9, 10, 99, 43, 151645, 11)),
                        dict(target_ids=(42, 43)), dict(labels=(-100, -100, 42, 43, 151645, 11))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bridge.validate_encoding_boundary(SimpleNamespace(**dict(vars(encoded), **changes)), **arguments)

    def test_cpu_import_and_mask_import_never_load_model_libraries(self):
        script = '''
import sys
class NoModels:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('torch', 'transformers', 'peft', 'safetensors'):
            raise AssertionError('model import forbidden: ' + fullname)
sys.meta_path.insert(0, NoModels())
from organism_v6 import orch_guided_bridge
from gpu.astra_reader_audit_lesson_train import validate_masks
assert not hasattr(orch_guided_bridge, 'main')
'''
        result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
