from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r125_continual_native as native
from gpu import orch_r168_targeted_replay as replay
from gpu.astra_pchain2_native import EncodedRow
from gpu.orch_r144_sleep_targets import encode_sleep_targets


class Tokenizer:
    eos_token_id = 2
    pad_token_id = None
    all_special_ids = [1, 2]

    def apply_chat_template(self, messages, **kwargs):
        return [1] + [ord(character) + 100 for message in messages for character in message['content']]

    def decode(self, tokens, **kwargs):
        return ''.join(chr(token - 100) for token in tokens)


def child_row(segment, target='A'):
    return dict(segment=segment, split='TRAIN', actor='child', event_id=f'child:{segment}',
        prefix=[dict(role='system', content='s'), dict(role='user', content='parent context')],
        target=target, token_ids=[ord(character) + 100 for character in target] + [2],
        append_eos=False, prefix_loss=False, target_loss=True, source_sha256=replay.digest(['row', segment]),
        model_state_sha256='a' * 64, terminal=True, truncated=False)


class TargetedReplayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'stream/records').mkdir(parents=True)
        checkpoint = self.root / 'checkpoints/sleep_000001'
        checkpoint.mkdir(parents=True)
        self.old = [child_row(0), child_row(1, 'B')]
        self.new = [child_row(2, 'C')]
        events = [dict(event_id=row['event_id'], actor='child', split='TRAIN', origin='TRAIN_COLLECTION',
            text=row['target'], source_sha256=row['source_sha256']) for row in self.old]
        events.append(dict(event_id='feedback:0', actor='environment', split='TRAIN',
            origin='TRAIN_COLLECTION', source_sha256='f' * 64, text='Observed result differs from prediction.'))
        self.commit = dict(adapter_path=str(checkpoint / 'adapter'),
            optimizer_rng_path=str(checkpoint / 'optimizer_rng.pt'), optimizer_steps=32,
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='b' * 64))
        self.state = dict(rows=deepcopy(self.old), pending=None, sleep_frontier=2,
            history=dict(events=events), model_state_sha256=replay.digest(self.commit['checkpoint_sha256']))
        self.record = dict(kind='SLEEP_COMPLETE', index=4, journal_id='a' * 32,
            previous_sha256='b' * 64, document=dict(status='COMPLETE', cycle=1,
            checkpoint=self.commit, resume_state=dict(state=self.state, sha256=replay.digest(self.state))))
        self.record['sha256'] = replay.digest(self.record)
        self.boundary_path = self.root / 'stream/records/00000000000000000004.json'
        self.commit_path = checkpoint / 'COMMIT.json'
        self.boundary_ref = self.write(self.boundary_path, self.record)
        self.commit_ref = self.write(self.commit_path, self.commit)
        self.objects = [dict(segment=0, object_id='object-a', selection_kind='OBJECT_REPLAY',
                             support_event_ids=['child:0'])]
        self.tokenizer = Tokenizer()
        self.clock = 110

    def write(self, path, value):
        path.write_bytes(replay.encoded(value))
        return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def freeze(self, **changes):
        values = dict(own_root=self.root, boundary_ref=self.boundary_ref, checkpoint_ref=self.commit_ref,
            row_objects=self.objects, dose=4, plan_sha256='c' * 64, runtime_sha256='d' * 64, frozen_unix=90)
        return replay.freeze_selection(**dict(values, **changes))

    def arguments(self):
        new, old, encoded, excluded = encode_sleep_targets(self.new, self.old, self.tokenizer, 1024, native.encode_own)
        self.assertEqual(excluded, [])
        return dict(new_rows=new, old_rows=old, baseline_schedule=native.presentation_schedule(new, old),
            encoded_rows=encoded, encoder=lambda row: native.encode_own(row, self.tokenizer, 1024),
            plan_sha256='c' * 64, runtime_sha256='d' * 64, target_cycle=2,
            anchor_token_counts=[[7, 11], [3], [13], [5]])

    def prepare_go(self, selection=None):
        selection = self.freeze() if selection is None else selection
        selection_ref = self.write(self.root / 'SELECTION.json', selection)
        go = dict(schema=replay.GO_SCHEMA, action='ONE_EXPERIMENTAL_TARGETED_REPLAY_SLEEP',
            selection=selection_ref, approved_intake_sha256='e' * 64, not_before=100, expires=200,
            **{key: selection[key] for key in ('life_root', 'life_role', 'target_cycle',
                                              'plan_sha256', 'runtime_sha256')})
        return selection_ref, self.write(self.root / 'GO.json', go), go

    def admit(self, **changes):
        selection_ref, go_ref, unused = self.prepare_go()
        return replay.admit_schedule(selection_ref, go_ref, approved_intake_sha256='e' * 64,
            now=lambda: self.clock, **dict(self.arguments(), **changes))

    def repin_boundary(self):
        self.record['document']['resume_state']['sha256'] = replay.digest(self.state)
        self.record['sha256'] = replay.digest({key: value for key, value in self.record.items() if key != 'sha256'})
        self.boundary_ref = self.write(self.boundary_path, self.record)

    def test_manifest_contains_selectors_not_reconstructed_targets(self):
        selection = self.freeze()
        self.assertEqual(selection['target_cycle'], 2)
        self.assertEqual(selection['baseline'], replay.BASELINE)
        self.assertNotIn('prefix', selection['selected'][0])
        self.assertNotIn('target', selection['selected'][0])
        self.assertNotIn('token_ids', selection['selected'][0])
        self.assertEqual(selection['selected'][0]['row_sha256'], replay.digest(self.old[0]))
        self.assertEqual(replay.validate_selection(selection), selection)

    def test_native_schedule_and_full_anchor_indices_preserved(self):
        args = self.arguments()
        before = deepcopy((self.old, self.new, args['encoded_rows']))
        steps, receipt = replay.preview_schedule(self.freeze(), **args)
        self.assertEqual(steps[:18], args['baseline_schedule'])
        self.assertEqual(steps[18:], [(replay.EXTRA, self.old[0])] * 4)
        self.assertTrue(all(steps[index][1] is row for index, (kind, row) in enumerate(args['baseline_schedule'])))
        self.assertEqual(Counter(kind for kind, row in steps), dict(NEW=16, REHEARSAL=2,
            R168_EXPERIMENTAL_EXTRA_OWN=4))
        self.assertEqual(receipt['extra_steps'], 4)
        self.assertEqual(receipt['extra_anchor_samples'], 16)
        self.assertEqual(receipt['extra_anchor_index_start'], 18)
        self.assertEqual(receipt['extra_anchor_token_exposures'], 120)
        self.assertEqual(receipt['selected'][0]['extra_child_token_exposures'], 8)
        self.assertEqual((self.old, self.new, args['encoded_rows']), before)
        self.assertEqual(receipt['status'], 'PLANNED_NOT_EXECUTED')

    def test_parent_conditioning_remains_masked_and_native_targets_exact(self):
        args = self.arguments()
        steps, unused = replay.preview_schedule(self.freeze(), **args)
        row = steps[-1][1]
        sample = args['encoded_rows'][row['source_sha256']]
        self.assertEqual(sample.target_ids, tuple(row['token_ids']))
        self.assertEqual(sample.labels[:-2], (-100,) * (len(sample.labels) - 2))
        self.assertEqual(row['prefix'][1]['content'], 'parent context')

    def test_dose_and_selection_caps_reject_bool_zero_excess_duplicates(self):
        for dose in (True, 0, -1, 5, 1.5):
            with self.subTest(dose=dose), self.assertRaises(ValueError):
                self.freeze(dose=dose)
        for items in ([], self.objects * 2, self.objects * 3):
            with self.subTest(items=items), self.assertRaises(ValueError):
                self.freeze(row_objects=items)

    def test_two_rows_four_each_is_bounded_eight_extra(self):
        items = self.objects + [dict(segment=1, object_id='object-b', selection_kind='OBJECT_REPLAY',
                                    support_event_ids=['child:1'])]
        unused, receipt = replay.preview_schedule(self.freeze(row_objects=items), **self.arguments())
        self.assertEqual(receipt['extra_steps'], 8)

    def test_parent_eval_and_invented_rows_rejected_even_if_rehashed(self):
        for changes in (dict(actor='parent'), dict(split='FINAL'), dict(prefix_loss=True),
                        dict(target_loss=False), dict(append_eos=True)):
            with self.subTest(changes=changes):
                self.state['rows'][0] = dict(self.old[0], **changes)
                self.repin_boundary()
                with self.assertRaises(ValueError):
                    self.freeze()

    def test_selected_row_must_match_actual_child_event(self):
        self.state['rows'][0]['target'] = 'invented corrected retelling'
        self.repin_boundary()
        with self.assertRaisesRegex(ValueError, 'original_child_event_binding'):
            self.freeze()

    def test_foreign_boundary_or_checkpoint_rejected_before_payload_reads(self):
        foreign = dict(path=str(self.root.parent / 'foreign/COMMIT.json'), sha256='a' * 64)
        for changes in (dict(boundary_ref=foreign), dict(checkpoint_ref=foreign)):
            with patch.object(replay, 'read_bound', side_effect=AssertionError('must not read')):
                with self.assertRaises(ValueError):
                    self.freeze(**changes)

    def test_pending_nonboundary_and_zero_step_controls_rejected(self):
        self.state['pending'] = 'sleep:uncertain'
        self.repin_boundary()
        with self.assertRaisesRegex(ValueError, 'clean_exact_saved_boundary'):
            self.freeze()
        self.state['pending'] = None
        self.state['matched'] = dict(arm='parented_learning')
        self.repin_boundary()
        with self.assertRaisesRegex(ValueError, 'matched_or_control'):
            self.freeze()
        del self.state['matched']
        self.commit['optimizer_steps'] = 0
        self.commit_ref = self.write(self.commit_path, self.commit)
        self.repin_boundary()
        with self.assertRaisesRegex(ValueError, 'nonfrozen'):
            self.freeze()

    def test_clean_state_and_record_hashes_cannot_be_spoofed(self):
        self.record['document']['cycle'] = 2
        self.boundary_ref = self.write(self.boundary_path, self.record)
        with self.assertRaisesRegex(ValueError, 'bound_completed_journal_record'):
            self.freeze()

    def test_manifest_tampering_and_wrong_target_cycle_rejected(self):
        for key, value in (('life_role', 'FROZEN'), ('selection_split', 'DEV'), ('target_cycle', 3),
                           ('baseline', dict(replay.BASELINE, new_presentations=1))):
            selection = self.freeze()
            selection[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                replay.preview_schedule(selection, **self.arguments())
        for key, value in (('target_cycle', 3), ('runtime_sha256', 'f' * 64), ('plan_sha256', 'f' * 64)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                replay.preview_schedule(self.freeze(), **dict(self.arguments(), **{key: value}))

    def test_baseline_cannot_be_reordered_repeated_or_silently_reweighted(self):
        args = self.arguments()
        for schedule in (args['baseline_schedule'][1:], list(reversed(args['baseline_schedule'])),
                         args['baseline_schedule'] + [('NEW', self.new[0])]):
            with self.assertRaisesRegex(ValueError, 'unchanged_NATIVE'):
                replay.preview_schedule(self.freeze(), **dict(args, baseline_schedule=schedule))

    def test_excluded_selected_row_is_fatal_not_silently_replaced(self):
        args = self.arguments()
        old = [self.old[1]]
        with self.assertRaisesRegex(ValueError, 'selected_row_excluded'):
            replay.preview_schedule(self.freeze(), **dict(args, old_rows=old,
                baseline_schedule=native.presentation_schedule(self.new, old)))

    def test_selected_prefix_tokens_or_masks_cannot_change(self):
        selection = self.freeze()
        for key, value in (('target', 'different'), ('token_ids', [999, 2]),
                           ('prefix', [dict(role='user', content='replacement')])):
            args = self.arguments()
            row = deepcopy(self.old[0])
            row[key] = value
            old = [row, self.old[1]]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'selected_row_changed'):
                replay.preview_schedule(selection, **dict(args, old_rows=old,
                    baseline_schedule=native.presentation_schedule(self.new, old)))
        args = self.arguments()
        source = self.old[0]['source_sha256']
        sample = args['encoded_rows'][source]
        args['encoded_rows'][source] = EncodedRow(sample.input_ids, sample.input_ids, sample.target_ids)
        with self.assertRaisesRegex(ValueError, 'exact_native_prefix'):
            replay.preview_schedule(selection, **args)

    def test_special_token_exclusion_is_never_bypassed(self):
        selection = self.freeze()
        args = self.arguments()
        def reject(row):
            raise ValueError('no_special_token_target_injection')
        with self.assertRaisesRegex(ValueError, 'no_special_token_target_injection'):
            replay.preview_schedule(selection, **dict(args, encoder=reject))

    def test_object_not_correctness_and_strategy_requires_discriminating_support(self):
        item = dict(self.objects[0], selection_kind='CORRECT_CODE')
        with self.assertRaisesRegex(ValueError, 'not_correctness_claim'):
            self.freeze(row_objects=[item])
        item['selection_kind'] = 'ATTENTION_STRATEGY_REPLAY'
        with self.assertRaisesRegex(ValueError, 'beyond_self_report'):
            self.freeze(row_objects=[item])
        item['support_event_ids'] = ['feedback:0']
        selection = self.freeze(row_objects=[item])
        self.assertEqual(selection['selected'][0]['support'][0]['event_id'], 'feedback:0')
        item['support_event_ids'] = ['invented:feedback']
        with self.assertRaisesRegex(ValueError, 'existing_TRAIN_support_only'):
            self.freeze(row_objects=[item])

    def test_admission_needs_exact_GO_intake_and_current_time(self):
        selection_ref, go_ref, go = self.prepare_go()
        for changes in (dict(action='RUN_ANYTHING'), dict(life_role='UNPARENTED'), dict(expires=100),
                        dict(approved_intake_sha256='f' * 64), dict(extra='not allowed')):
            changed_ref = self.write(self.root / 'GO.json', dict(go, **changes))
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replay.admit_schedule(selection_ref, changed_ref, approved_intake_sha256='e' * 64,
                                      now=lambda: 110, **self.arguments())
        self.assertFalse((self.root / 'r168_targeted_replay').exists())

    def test_consumed_sleep_cannot_retry_with_new_GO_or_filename(self):
        schedule = self.admit()
        self.assertTrue((schedule.marker / 'CONSUMED.json').is_file())
        selection_ref, go_ref, go = self.prepare_go()
        new_go_ref = self.write(self.root / 'NEW_GO.json', dict(go, not_before=101))
        with self.assertRaises(FileExistsError):
            replay.admit_schedule(selection_ref, new_go_ref, approved_intake_sha256='e' * 64,
                                  now=lambda: 110, **self.arguments())
        self.assertEqual(len(list(schedule)), 22)
        self.assertEqual(schedule.status, 'EXHAUSTED_NOT_EXECUTION_PROOF')
        with self.assertRaisesRegex(ValueError, 'never_replayed'):
            iter(schedule)

    def test_crash_before_consumed_json_still_latches_sleep(self):
        selection_ref, go_ref, unused = self.prepare_go()
        with patch.object(replay, 'write_once', side_effect=OSError('disk failed')):
            with self.assertRaises(OSError):
                replay.admit_schedule(selection_ref, go_ref, approved_intake_sha256='e' * 64,
                                      now=lambda: 110, **self.arguments())
        with self.assertRaises(FileExistsError):
            replay.admit_schedule(selection_ref, go_ref, approved_intake_sha256='e' * 64,
                                  now=lambda: 110, **self.arguments())

    def test_expiry_after_preparation_does_not_admit(self):
        selection_ref, go_ref, unused = self.prepare_go()
        with self.assertRaisesRegex(ValueError, 'current_replay_GO'):
            replay.admit_schedule(selection_ref, go_ref, approved_intake_sha256='e' * 64,
                                  now=iter([110, 201]).__next__, **self.arguments())
        self.assertFalse((self.root / 'r168_targeted_replay').exists())

    def test_existing_orphan_target_checkpoint_refuses_replay(self):
        (self.root / 'checkpoints/sleep_000002').mkdir()
        with self.assertRaisesRegex(ValueError, 'existing_target_checkpoint_never_replayed'):
            self.admit()
        self.assertFalse((self.root / 'r168_targeted_replay').exists())

    def test_full_anchor_families_required_not_own_only_extra(self):
        for counts in ([], [[7]], [[7], [3], [13], []], [[7], [3], [13], [True]]):
            with self.subTest(counts=counts), self.assertRaisesRegex(ValueError, 'four_full_label_anchor'):
                replay.preview_schedule(self.freeze(), **dict(self.arguments(), anchor_token_counts=counts))

    def test_actual_receipt_reconciles_baseline_and_experimental_exposures(self):
        schedule = self.admit()
        counts = Counter(row['source_sha256'] for kind, row in schedule)
        planned = schedule.planned
        receipt = dict(optimizer_steps=22, presentations=dict(counts), child_token_exposures=44,
            anchor_token_exposures=planned['baseline_anchor_token_exposures'] + 120,
            anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION', frozen_base_verified=True)
        evidence = replay.verify_sleep_receipt(schedule, receipt)
        self.assertEqual(evidence['experimental_extra_steps'], 4)
        self.assertEqual(evidence['experimental_extra_child_token_exposures'], 8)
        for change in (dict(optimizer_steps=18), dict(child_token_exposures=36),
                       dict(anchor_token_exposures=0), dict(presentations={}), dict(anchor_lambda=0)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replay.verify_sleep_receipt(schedule, dict(receipt, **change))

    def test_mutation_during_iteration_fails_without_retry(self):
        schedule = self.admit()
        self.old[0]['target'] = 'changed after admission'
        with self.assertRaisesRegex(ValueError, 'row_mutated_after_admission'):
            list(schedule)
        self.assertEqual(schedule.status, 'FAILED_OR_UNCERTAIN_NO_RETRY')
        with self.assertRaises(ValueError):
            iter(schedule)

    def test_encoded_mapping_mutation_before_extra_fails(self):
        args = self.arguments()
        schedule = self.admit(**args)
        source = self.old[0]['source_sha256']
        sample = args['encoded_rows'][source]
        args['encoded_rows'][source] = EncodedRow(sample.input_ids, sample.input_ids, sample.target_ids)
        with self.assertRaisesRegex(ValueError, 'encoded_row_mutated_after_admission'):
            list(schedule)

    def test_nonfinite_duplicate_symlink_and_foreign_metadata_fail_closed(self):
        path = self.root / 'bad.json'
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            path.write_bytes(raw)
            ref = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())
            with self.assertRaises(ValueError):
                replay.read_bound(ref)
        link = self.root / 'linked.json'
        link.symlink_to(path)
        with self.assertRaises(ValueError):
            replay.read_bound(dict(path=str(link), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

    def test_replacement_after_hash_does_not_change_decoded_bytes(self):
        path = self.root / 'read.json'
        ref = self.write(path, dict(original=True))
        original = replay.json.loads
        def replace(raw, **kwargs):
            path.write_text('{"replacement":true}')
            return original(raw, **kwargs)
        with patch.object(replay.json, 'loads', side_effect=replace):
            self.assertEqual(replay.read_bound(ref), dict(original=True))
        with self.assertRaisesRegex(ValueError, 'metadata_hash_mismatch'):
            replay.read_bound(ref)

    def test_single_sleep_arm_automatically_expires_without_restart(self):
        selection_ref, go_ref, unused = self.prepare_go()
        arm = replay.SingleSleepArm(selection_ref, go_ref, approved_intake_sha256='e' * 64,
                                    now=lambda: self.clock)
        args = self.arguments()
        before, disposition = arm.schedule(**dict(args, target_cycle=1))
        self.assertIs(before, args['baseline_schedule'])
        self.assertEqual(disposition['experimental_extra_steps'], 0)
        target, planned = arm.schedule(**args)
        self.assertEqual(len(list(target)), 22)
        self.assertEqual(planned['extra_steps'], 4)
        for cycle in (1, 2):
            with self.assertRaisesRegex(ValueError, 'consumed_arm_never_reactivated'):
                arm.schedule(**dict(args, target_cycle=cycle))
        for cycle in (3, 4, 10):
            later, disposition = arm.schedule(**dict(args, target_cycle=cycle))
            self.assertIs(later, args['baseline_schedule'])
            self.assertEqual(disposition['status'], 'EXPIRED_SINGLE_SLEEP_ARM')
            self.assertEqual(disposition['experimental_extra_steps'], 0)
        with self.assertRaisesRegex(ValueError, 'expired_arm_never_reactivated'):
            arm.schedule(**args)

    def test_missed_target_expires_and_never_catches_up(self):
        selection_ref, go_ref, unused = self.prepare_go()
        arm = replay.SingleSleepArm(selection_ref, go_ref, approved_intake_sha256='e' * 64)
        args = self.arguments()
        later, disposition = arm.schedule(**dict(args, target_cycle=3))
        self.assertIs(later, args['baseline_schedule'])
        self.assertFalse((self.root / 'r168_targeted_replay').exists())
        with self.assertRaises(ValueError):
            arm.schedule(**args)

    def test_expiry_cannot_reset_via_earlier_cycle(self):
        selection_ref, go_ref, unused = self.prepare_go()
        arm = replay.SingleSleepArm(selection_ref, go_ref, approved_intake_sha256='e' * 64)
        args = self.arguments()
        arm.schedule(**dict(args, target_cycle=3))
        for cycle in (1, 2):
            with self.assertRaisesRegex(ValueError, 'expired_arm_never_reactivated'):
                arm.schedule(**dict(args, target_cycle=cycle))
            self.assertEqual(arm.status, 'EXPIRED_SINGLE_SLEEP_ARM')

    def test_failed_admission_cannot_reset_or_continue_baseline(self):
        selection_ref, go_ref, unused = self.prepare_go()
        arm = replay.SingleSleepArm(selection_ref, go_ref, approved_intake_sha256='e' * 64,
                                    now=lambda: self.clock)
        args = self.arguments()
        with patch.object(replay, 'admit_schedule', side_effect=ValueError('injected')):
            with self.assertRaisesRegex(ValueError, 'injected'):
                arm.schedule(**args)
        for cycle in (1, 2, 3):
            with self.assertRaisesRegex(ValueError, 'uncertain_arm_never_resumed'):
                arm.schedule(**dict(args, target_cycle=cycle))

    def test_unfinished_or_failed_iteration_cannot_expire_into_baseline(self):
        selection_ref, go_ref, unused = self.prepare_go()
        arm = replay.SingleSleepArm(selection_ref, go_ref, approved_intake_sha256='e' * 64,
                                    now=lambda: self.clock)
        args = self.arguments()
        schedule, unused = arm.schedule(**args)
        with self.assertRaisesRegex(ValueError, 'unfinished_or_uncertain_schedule'):
            arm.schedule(**dict(args, target_cycle=3))
        self.old[0]['target'] = 'mutated'
        with self.assertRaisesRegex(ValueError, 'row_mutated_after_admission'):
            list(schedule)
        with self.assertRaisesRegex(ValueError, 'unfinished_or_uncertain_schedule'):
            arm.schedule(**dict(args, target_cycle=3))

    def test_actual_torch_CPU_applies_exact_baseline_then_four_extra_updates(self):
        try:
            import torch
        except ImportError:
            self.skipTest('actual Torch CPU dependency unavailable')
        self.assertFalse(torch.cuda.is_initialized())
        schedule = self.admit()
        steps = list(schedule)
        initial = torch.tensor([0.2, -0.1], dtype=torch.float64)

        def run(entries):
            adapter = torch.nn.Parameter(initial.clone())
            optimizer = torch.optim.AdamW([adapter], lr=0.001, weight_decay=0.01)
            traces = []
            for kind, row in entries:
                optimizer.zero_grad(set_to_none=True)
                target = torch.tensor([row['segment'] * 0.1, 0.3], dtype=torch.float64)
                loss = 0.75 * ((adapter - target) ** 2).mean()
                for anchor in (0.1, 0.2, 0.3, 0.4):
                    loss = loss + 0.0625 * ((adapter - anchor) ** 2).mean()
                loss.backward()
                optimizer.step()
                traces.append(adapter.detach().clone())
            return adapter.detach(), optimizer.state[adapter], traces

        actual, state, traces = run(steps)
        baseline = native.presentation_schedule(self.new, self.old)
        reference, reference_state, reference_traces = run(baseline + [(replay.EXTRA, self.old[0])] * 4)
        baseline_value, baseline_state, baseline_traces = run(baseline)
        self.assertTrue(torch.equal(actual, reference))
        self.assertTrue(all(torch.equal(before, after) for before, after in zip(traces[:18], baseline_traces)))
        self.assertTrue(torch.equal(traces[17], baseline_value))
        self.assertEqual(state['step'].item(), 22)
        self.assertEqual(baseline_state['step'].item(), 18)
        self.assertTrue(torch.equal(state['exp_avg'], reference_state['exp_avg']))
        self.assertTrue(torch.equal(state['exp_avg_sq'], reference_state['exp_avg_sq']))
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__':
    unittest.main()
