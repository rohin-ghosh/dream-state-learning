"""Synthetic saved-document tests; no native/model/helper replay dependencies."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_goal_pair_comparison_summary as summary


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def panel(master, condition, correct, paired):
    return dict(master=master, condition=condition, collection_sha256='collection-' + master,
        shared_text_sha256='text-' + master,
        summary=dict(individual=dict(correct=correct, denominator=4), paired=dict(correct=paired, denominator=2)),
        episodes=['not included in compact summary'])


def capsule(root):
    material = {group: [dict(row_index=index, actual_target=f'{group}-{index}') for index in range(size)]
                for group, size in zip(summary.GROUPS, summary.GROUP_SIZES)}
    reference = [dict(input_ids=[10, 20, 30], labels=[-100, 20, -100], target_ids=[20]) for unused in range(270)]
    binding = dict(initial_state=summary.PARENT_STATE, teaching_result_sha256='actual-teaching-source',
                   baseline_result_sha256='reused-baseline-source', protocol_sha256='design-sha')
    recipes = {}
    for arm in summary.ARMS:
        recipes[arm] = dict(arm=arm, initial_state=summary.PARENT_STATE, updates=400, batch_size=4,
            learning_rate=3e-5, seed=0, rank=8, optimizer='FRESH_ADAMW', optimizer_kwargs={'eps': 1e-8},
            loss='MEAN_CAUSAL_CE_TIMES_ACTIVE_OVER_FULL_REFERENCE_LABELS',
            schedule=[[offset % 128, 128 + offset % 94, 222 + (2 * offset) % 48, 222 + (2 * offset + 1) % 48]
                      for offset in range(400)],
            masked_row_indexes=list(range(222, 270)) if arm == summary.ARMS[1] else [])
    write(root / 'prepare/RESULT.json', dict(schema=summary.DRIVER_SCHEMA, phase='prepare',
        status='PREPARED_NO_MODEL', entry_sha256='recorded-driver-sha', binding=binding))
    write(root / 'prepare/INPUTS.json', binding)
    write(root / 'prepare/TRAINING_ROWS.json', material)
    write(root / 'prepare/RECIPES.json', recipes)
    (root / 'source_commit.txt').write_text('synthetic-commit\n')
    for index, arm in enumerate(summary.ARMS):
        train, after = root / arm / 'train', root / arm / 'after'
        state = ('a' if index == 0 else 'b') * 64
        controlled = deepcopy(reference)
        if index:
            for row in controlled[222:]:
                row['labels'] = [-100] * len(row['labels'])
        for name, value in (('TRAINING_ROWS.json', material), ('REFERENCE_MASKS.json', reference),
                            ('MASKS.json', controlled), ('RECIPE.json', recipes[arm])):
            write(train / name, value)
        (train / 'LOSSES.jsonl').write_text('{}\n' * 400)
        write(train / 'STATES.json', dict(before=summary.PARENT_STATE, after=state))
        trained = dict(schema=summary.DRIVER_SCHEMA, phase='train', arm=arm, status='COMPLETE',
            binding=binding, loaded_adapter_state_sha256=summary.PARENT_STATE, adapter_state_after=state,
            fits=1, updates=400, frozen_base_unchanged=True, model_calls=0, max_native_calls=0,
            started_unix=100 + index, finished_unix=130 + index,
            actual_supervised_tokens=1000 - index * 250, reference_supervised_tokens=1000)
        write(train / 'RESULT.json', trained)
        measurements = dict(panels=dict(TRAIN=[panel('TRAIN-A', 'OWN_TEXT', 4, 2), panel('TRAIN-B', 'OWN_TEXT', 3, 1)],
            PROBE=[panel('PROBE-A', 'OWN_TEXT', 3 - index, 1 - index), panel('PROBE-A', 'UNAVAILABLE', 1, 0),
                   panel('PROBE-B', 'OWN_TEXT', 3, 1), panel('PROBE-B', 'UNAVAILABLE', 0, 0)]),
            primary=dict(correct=2-index, denominator=4, individual=dict(correct=6-index, denominator=8)),
            deterministic_first_port=[dict(master='PROBE-A', native_calls=0, policy='FIRST_CURRENT_DISPLAYED_PORT_NO_READS',
                summary=dict(individual=dict(correct=2, denominator=4), paired=dict(correct=0, denominator=2)), episodes=['omit'])],
            baseline=[panel('PROBE-A', 'OWN_TEXT', 1, 0), panel('PROBE-B', 'OWN_TEXT', 2, 0)],
            old_recall={'0': dict(correct=15, denominator=16), '8': dict(correct=16, denominator=16)},
            held_audit=dict(overall=dict(correct=14 + index, denominator=16)),
            taught_graph=dict(OWN_TEXT=dict(correct=3, denominator=4)),
            previous_fresh_graph=dict(OWN_TEXT=dict(correct=2 + index, denominator=4)),
            engineering_checks={key: False for key in summary.ENGINEERING_TARGETS}, engineering_target_met=False)
        write(after / 'SUMMARY.json', measurements)
        write(after / 'STATES.json', dict(before=state, after=state))
        write(after / 'CALL_000.json', dict(response='not audited'))
        write(after / 'RESULT.json', dict(schema=summary.DRIVER_SCHEMA, phase='after', arm=arm, status='COMPLETE',
            binding=binding, loaded_adapter_state_sha256=state, adapter_state_after=state,
            training_result_sha256=hashlib.sha256((train / 'RESULT.json').read_bytes()).hexdigest(),
            model_calls=218-index, max_native_calls=240, role_calls=dict(actor=170-index), fits=0, updates=0,
            started_unix=200 + index, finished_unix=220 + index, **measurements))


class SummaryTests(unittest.TestCase):
    def test_complete_counts_matches_labels_states_and_source_references(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsule(root)
            result = summary.summarize(root)
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertTrue(all(result['cross_arm_saved_matches'].values()))
            self.assertEqual(result['prepared_row_counts'], dict(zip(summary.GROUPS, summary.GROUP_SIZES)))
            self.assertEqual(result['source']['recorded_commit'], 'synthetic-commit')
            for index, arm in enumerate(summary.ARMS):
                output = result['arms'][arm]
                self.assertTrue(all(output['matches'].values()))
                self.assertEqual(output['train']['wall_seconds'], 30)
                self.assertEqual(output['train']['observed_loss_lines'], 400)
                self.assertEqual(output['after']['calls']['reported'], 218-index)
                self.assertEqual(output['after']['calls']['saved_call_files'], 1)
                measured = output['measurements']
                self.assertEqual(measured['primary']['correct'], 2-index)
                self.assertEqual(measured['panels']['PROBE'][0]['paired']['correct'], 1-index)
                self.assertEqual(measured['retention']['held_audit']['overall']['correct'], 14+index)
                self.assertEqual(measured['retention']['previous_fresh_text']['OWN_TEXT']['correct'], 2+index)
                self.assertFalse(measured['engineering']['reported_target_met'])
                self.assertIn('NOT_CHILD_NATIVE', measured['deterministic_first_port']['label'])
                self.assertIn('NOT_INDEPENDENT', measured['reused_37ec_probe_baseline']['label'])
                self.assertNotIn('episodes', measured['reused_37ec_probe_baseline']['panels'][0])
                self.assertNotIn('schedule', output['saved_material']['recipe'])
                self.assertEqual(output['saved_material']['recipe']['schedule_length'], 400)
            path = 'FULL_TARGET/train/TRAINING_ROWS.json'
            self.assertEqual(result['input_references'][path]['sha256'], hashlib.sha256((root / path).read_bytes()).hexdigest())
            self.assertIn('no independent tensor/custody', result['limitation'])

    def test_mismatches_are_reported_without_authentication_or_discarding_scores(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsule(root)
            directory = root / summary.ARMS[1] / 'train'
            for filename, mutate in (
                ('TRAINING_ROWS.json', lambda document: document['new_trajectory_rows'][0].update(actual_target='drift')),
                ('REFERENCE_MASKS.json', lambda document: document[0]['input_ids'].append(99)),
                ('RECIPE.json', lambda document: document['schedule'][0].reverse()),
                ('MASKS.json', lambda document: document[222]['labels'].__setitem__(1, 20)),
            ):
                value = json.loads((directory / filename).read_text())
                mutate(value)
                write(directory / filename, value)
            receipt = json.loads((directory / 'RESULT.json').read_text())
            receipt['loaded_adapter_state_sha256'] = '9d-not-37ec'
            write(directory / 'RESULT.json', receipt)
            result = summary.summarize(root)
            for name in ('training_rows', 'reference_masks', 'schedule', 'initial_37ec'):
                self.assertFalse(result['cross_arm_saved_matches'][name])
            matched = result['arms'][summary.ARMS[1]]['matches']
            for name in ('rows_to_prepared', 'recipe_to_prepared', 'controlled_masks', 'initial_37ec', 'after_training_result_sha'):
                self.assertFalse(matched[name])
            self.assertEqual(result['arms'][summary.ARMS[1]]['measurements']['primary']['correct'], 1)

    def test_failed_stage_wins_over_result_and_missing_stages_remain_unknown(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsule(root)
            path = root / summary.ARMS[0] / 'after'
            write(path / 'FAILED.json', dict(schema=summary.DRIVER_SCHEMA, phase='after', arm=summary.ARMS[0],
                status='FAILED', error='readonly state changed', model_calls=218, started_unix=200, finished_unix=221))
            result = summary.summarize(root)
            self.assertEqual(result['status'], 'FAILED')
            self.assertEqual(result['failed_stages'], ['FULL_TARGET/after'])
            stage = result['arms'][summary.ARMS[0]]['after']
            self.assertTrue(stage['result_and_failure_present'])
            self.assertEqual(stage['error'], 'readonly state changed')
            self.assertEqual(result['arms'][summary.ARMS[0]]['measurements']['primary']['correct'], 2)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root / summary.ARMS[0] / 'train/REQUEST.json', dict(schema=summary.DRIVER_SCHEMA, phase='train',
                arm=summary.ARMS[0], started_unix=100))
            (root / summary.ARMS[0] / 'train/LOSSES.jsonl').write_text('{}\n{}\n')
            result = summary.summarize(root)
            self.assertEqual(result['status'], 'NOT_YET_TERMINAL')
            self.assertEqual(result['arms'][summary.ARMS[0]]['train']['status'], 'NOT_YET_TERMINAL')
            self.assertEqual(result['arms'][summary.ARMS[0]]['train']['observed_loss_lines'], 2)
            self.assertIsNone(result['arms'][summary.ARMS[0]]['train']['wall_seconds'])
            self.assertEqual(result['arms'][summary.ARMS[1]]['train']['status'], 'NOT_STARTED')
            self.assertIsNone(result['cross_arm_saved_matches']['training_rows'])

    def test_partial_after_retains_completed_world_and_observed_retention_counts(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            after = root / summary.ARMS[0] / 'after'
            write(after / 'PROBE_0_OWN_TEXT_SUMMARY.json', panel('PROBE-A', 'OWN_TEXT', 1, 0))
            write(after / 'OLD_RECALL_W0_00.json', dict(correct=True))
            write(after / 'OLD_RECALL_W0_01.json', dict(correct=False))
            write(after / 'TAUGHT_OWN_TEXT_EPISODE_00.json', dict(score=dict(correct=False)))
            write(after / 'HELD_AUDIT.json', dict(summary=dict(overall=dict(correct=2, denominator=3))))
            result = summary.summarize(root)
            measured = result['arms'][summary.ARMS[0]]['measurements']
            self.assertEqual(measured['panels']['PROBE'][0]['individual'], dict(correct=1, denominator=4))
            self.assertEqual(measured['retention']['old_recall']['0']['observed_denominator'], 2)
            self.assertEqual(measured['retention']['old_recall']['0']['correct'], 1)
            self.assertIsNone(measured['retention']['old_recall']['8'])
            self.assertEqual(measured['retention']['original_taught_text']['OWN_TEXT']['observed_denominator'], 1)
            self.assertIsNone(measured['engineering']['reported_target_met'])

    def test_malformed_files_and_wrong_identity_are_visible_not_success_defaults(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsule(root)
            (root / 'FULL_TARGET/train/REFERENCE_MASKS.json').write_text('{broken')
            (root / 'NEW_TRAJECTORY_LOSS_OFF/after/FAILED.json').write_text('{broken')
            value = json.loads((root / 'FULL_TARGET/after/RESULT.json').read_text())
            value['arm'] = 'OTHER'
            write(root / 'FULL_TARGET/after/RESULT.json', value)
            result = summary.summarize(root)
            self.assertEqual(result['status'], 'FAILED')
            self.assertFalse(result['arms']['FULL_TARGET']['after']['identity_matches']['arm'])
            self.assertIsNone(result['cross_arm_saved_matches']['reference_masks'])
            self.assertEqual(len(result['read_issues']), 2)
            self.assertEqual(result['input_references']['FULL_TARGET/train/REFERENCE_MASKS.json']['status'], 'MALFORMED')

    def test_deterministic_readonly_and_cli_no_model_imports(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            capsule(root)
            before = {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            self.assertEqual(summary.summarize(root), summary.summarize(root))
            script = '''
import builtins, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'tokenizers', 'peft', 'organism_v6'):
        raise AssertionError(name)
    if name.startswith('gpu.') and name != 'gpu.astra_goal_pair_comparison_summary':
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from gpu.astra_goal_pair_comparison_summary import main
main(['--root', sys.argv[1]])
'''
            completed = subprocess.run([sys.executable, '-B', '-c', script, str(root)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)['schema'], summary.SCHEMA)
            self.assertEqual(before, {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()})


if __name__ == '__main__':
    unittest.main()
