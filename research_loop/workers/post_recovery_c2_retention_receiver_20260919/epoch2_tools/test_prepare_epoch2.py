"""Focused local preparer/standalone-helper tests; no native process operations."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from research_loop.workers.post_recovery_c2_retention_receiver_20260919 import test_receiver as fixture
from research_loop.workers.post_recovery_retention_boundary_20260918 import boundary


TOOLS = Path(__file__).resolve().parent


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


prepare = load('c2_local_epoch2_preparation', TOOLS / 'prepare_epoch2.py')
cpu = load('c2_local_standalone_CPU', TOOLS / 'cpu_check.py')


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.stage = prepare.read(prepare.ROLLOUT / 'C2_STAGED.json')
        self.observation = next(row for row in prepare.read(prepare.ROLLOUT / 'node5_INVENTORY2.json')['results']
            if row['life'] == 'C2')

    def test_exact_actual_inventory_and_three_epoch1_changes(self):
        prepare.check_inputs(self.stage, self.observation)
        self.assertEqual(len(self.stage['new_source_pins']), 183)

    def test_full_local_epoch1_resolution(self):
        resolved = prepare.locate(self.stage['new_source_pins'], [prepare.RETENTION / 'fork', prepare.PREIMAGE])
        self.assertEqual(len(resolved), 183)
        self.assertEqual({name: prepare.checksum(entry['content']) for name, entry in resolved.items()},
            self.stage['new_source_pins'])

    def test_changed_guard_journal_or_native_refuses(self):
        for key, value in (('old_guard_sha256', '0' * 64), ('journal_id', 'a' * 32),
                ('native', dict(self.stage['native'], pid=1))):
            changed = deepcopy(self.stage)
            changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'same_C2_inventory'):
                prepare.check_inputs(changed, self.observation)

    def test_extra_epoch1_delta_is_not_silently_approved(self):
        self.stage['new_source_pins']['gpu/r184_cpu_bridge.py'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_three_retention_changes'):
            prepare.check_inputs(self.stage, self.observation)

    def test_wrong_life_or_frozen_physical_identity_refuses(self):
        self.observation['plan']['think_act_learn']['trial_id'] = 'curriculum_frozen_sibling'
        with self.assertRaisesRegex(ValueError, 'same_learned_C2'):
            prepare.check_inputs(self.stage, self.observation)

    def test_missing_or_wrong_hash_preimage_refuses(self):
        with self.assertRaisesRegex(ValueError, 'missing_exact_C2_preimage'):
            prepare.locate({'gpu/orch_r125_continual_native.py': '0' * 64}, [prepare.PREIMAGE])

    def test_source_paths_reject_traversal_absolute_and_empty(self):
        for name in ('../outside.py', '/tmp/outside.py', 'gpu/../../x.py', '', 'gpu//x.py'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                prepare.relative_name(name)

    def test_symlink_preimage_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'target.py').write_bytes(b'unchanged')
            (root / 'alias.py').symlink_to(root / 'target.py')
            with self.assertRaisesRegex(ValueError, 'missing_exact_C2_preimage'):
                prepare.locate({'alias.py': prepare.checksum(b'unchanged')}, [root])

    def test_existing_output_is_never_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'new_unused_worker_local_output_only'):
            prepare.prepare(TOOLS)

    def test_output_outside_worker_refuses_before_reads_or_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'not-created'
            with self.assertRaisesRegex(ValueError, 'new_unused_worker_local_output_only'):
                prepare.prepare(target)
            self.assertFalse(target.exists())

    def test_plan_template_preserves_old_root_bridge_wall_and_selection(self):
        old = deepcopy(self.observation['plan'])
        remote = Path(self.stage['new_source']).parent.parent / 'epoch2/source'
        plan = prepare.plan_template(old, remote)
        self.assertEqual(old, self.observation['plan'])
        self.assertNotIn('authorized_wall_extension', plan)
        for key in ('root', 'hard_end_unix', 'lease_end_unix', 'think_act_learn', 'checkpoint_tail_recovery',
                'learn_row_policy', 'decoder', 'system_prompt', 'birth_prompt'):
            self.assertEqual(plan[key], old[key])
        self.assertEqual(plan['hard_end_unix'], 1789927200)

    def test_standalone_guard_checker_allows_only_anchor_rebinding(self):
        source = Path(self.stage['new_source']).parent.parent / 'epoch2/source'
        template = prepare.plan_template(self.observation['plan'], source)
        effective = deepcopy(template)
        effective['checkpoint_tail_recovery'].update(complete_index=12000, complete_sha256='a' * 64)
        cpu.verify_guard_template(effective, template, source)
        for key, value in (('hard_end_unix', 1789927201), ('root', '/other'), ('system_prompt', 'changed'),
                ('learn_row_policy', 'changed'), ('think_act_learn', {})):
            changed = deepcopy(effective)
            changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'no_recipe_wall_or_bridge_change'):
                cpu.verify_guard_template(changed, template, source)

    def test_standalone_helper_never_imports_repository_worker(self):
        source = (TOOLS / 'cpu_check.py').read_text() + (TOOLS / 'source_checks.py').read_text()
        for text in ('from research_loop.workers', 'import research_loop.workers', 'ssh ', 'systemd-run', 'Popen('):
            self.assertNotIn(text, source)

    def test_seal_modes_and_publish_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source'
            source.mkdir()
            path = source / 'exact.py'
            prepare.publish(path, b'original\n')
            with self.assertRaises(FileExistsError):
                prepare.publish(path, b'overwrite')
            prepare.seal(source)
            self.assertEqual(path.stat().st_mode & 0o777, 0o444)
            self.assertEqual(source.stat().st_mode & 0o777, 0o555)
            self.assertEqual(path.read_bytes(), b'original\n')
            source.chmod(0o700)
            path.chmod(0o600)


class CheckpointSelectionTests(fixture.ReceiverFixture):
    def test_exact_point_pair_without_prefix_decode(self):
        candidate, pins = cpu.read_checkpoint_pair(boundary, self.binding,
            self.candidate['complete_index'], self.candidate['complete_sha256'])
        self.assertEqual(candidate['checkpoint'], self.candidate['checkpoint'])
        self.assertEqual(len(pins), 4)
        self.assertTrue(all(Path(path).name.startswith(('00000000000000000002', '00000000000000000003')) for path in pins))

    def test_historical_checkpoint_read_is_not_current_handoff_claim(self):
        self.append('REQUEST', dict(pending=True))
        candidate, _ = cpu.read_checkpoint_pair(boundary, self.binding,
            self.candidate['complete_index'], self.candidate['complete_sha256'])
        self.assertEqual(candidate['complete_sha256'], self.candidate['complete_sha256'])
        self.assertIsNone(boundary.read_boundary(self.binding))

    def test_invented_index_or_wrong_pin_refuses(self):
        with self.assertRaisesRegex(ValueError, 'exact_historically_selected_COMPLETE'):
            cpu.read_checkpoint_pair(boundary, self.binding, self.candidate['complete_index'], '0' * 64)
        with self.assertRaises(FileNotFoundError):
            cpu.read_checkpoint_pair(boundary, self.binding, 10000, '0' * 64)

    def test_corrupt_intent_refuses(self):
        path = Path(self.binding['journal_root']) / 'records/00000000000000000003.intent.json'
        document = json.loads(path.read_bytes())
        document['record_sha256'] = '0' * 64
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(boundary.Refusal, 'durable_record_intent_pair'):
            cpu.read_checkpoint_pair(boundary, self.binding, self.candidate['complete_index'], self.candidate['complete_sha256'])


if __name__ == '__main__':
    unittest.main()
