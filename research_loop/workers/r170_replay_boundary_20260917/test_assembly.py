"""Fixture-local staging tests: no remote, live process, GPU, or model operations."""

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location('r170_test_assembly', Path(__file__).with_name('ASSEMBLY.py'))
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)
replay = assembly.replay
integration = assembly.integration


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.life = self.root / 'creative_reread/run1'
        self.old_source = self.root / 'old_source'
        self.output = self.root / 'stage/physical1'
        self.source = self.output / 'source'
        self.patch_life = mock.patch.object(assembly.driver, 'LIFE_ROOT', str(self.life))
        self.patch_life.start()
        self.addCleanup(self.patch_life.stop)
        self.intake = 'e' * 64
        evidence = json.loads((assembly.EVIDENCE_ROOT / 'NATIVE_CPU_FINAL.json').read_bytes())
        self.originals = {}
        for name, checksum in evidence['source_sha256'].items():
            if name.startswith(('gpu/', 'organism_v6/')) and name not in assembly.HELPER_PINS:
                raw = (assembly.REPO_ROOT / name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), checksum)
                self.originals[name] = raw
        self.originals[assembly.NATIVE_PATH] = (assembly.EVIDENCE_ROOT / 'NATIVE_cdb542.py').read_bytes()
        self.originals[assembly.GUARD_PATH] = (assembly.REPO_ROOT / assembly.GUARD_PATH).read_bytes()
        self.originals['gpu/__init__.py'] = b''
        self.originals['organism_v6/__init__.py'] = b''
        self.originals['gpu/pinned_but_not_imported.py'] = b'raise RuntimeError("must not execute source")\n'
        for name, raw in self.originals.items():
            destination = self.old_source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        (self.old_source / 'STARTUP.md').write_bytes(b'Existing child-facing startup.\n')
        (self.old_source / 'PROGRAMME.md').write_text('unvetted: must not copy')
        (self.old_source / 'unvetted.py').write_text('raise RuntimeError("never copy")')
        self.plan = dict(schema='R125_CONTINUAL_NATIVE_V1', root=str(self.life),
            source_root=str(self.old_source), physical=1, gpu_uuid=assembly.GPU_UUID,
            presleep_variant='reread_select', new_presentations=16, rehearsal_presentations=1,
            anchor_lambda=0.25, hard_end_unix=1000, lease_end_unix=1100,
            startup_context=dict(version='R127_STARTUP_V1', **assembly.file_ref(self.old_source / 'STARTUP.md')),
            max_sleeps=800, base_sha256='b' * 64, opaque_preserved_settings={'unchanged': [1, 2]})
        self.plan_ref = self.write(self.root / 'OLD_PLAN.json', self.plan)
        self.allocation = dict(plan_sha256=self.plan_ref['sha256'], physical=1, gpu_uuid=assembly.GPU_UUID,
            cpu_tests_passed=True, builder_entry_pushed=True, declared_unix=12, original_note='preserve exactly')
        self.allocation_ref = self.write(self.root / 'OLD_ALLOCATION.json', self.allocation)
        self.guard = dict(schema='R125_CONTINUAL_GUARD_V1', plan_path=self.plan_ref['path'],
            plan_sha256=self.plan_ref['sha256'], source_pins={name: hashlib.sha256(raw).hexdigest()
                for name, raw in self.originals.items()}, allocation_path=self.allocation_ref['path'],
            allocation_sha256=self.allocation_ref['sha256'], hard_end_unix=1000,
            attempt_dir=str(self.root / 'old_attempt'), resume=False, lease_path='/unchanged/LEASE.json',
            lease_sha256='f' * 64, host_sha256='a' * 64, next_reserved_unix=1200,
            device_containment={'unit': 'existing-unit', 'minor': 1})
        self.guard_ref = self.write(self.root / 'OLD_GUARD.json', self.guard)
        self.row = json.loads((assembly.EVIDENCE_ROOT / 'ROW118_TRAIN_FIXTURE.json').read_bytes())
        self.assertEqual(replay.digest(self.row), integration.ROW_SHA256)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(replay.encoded(value) + b'\n')
        return assembly.file_ref(path)

    def restage_guard(self):
        self.guard_ref = self.write(self.root / 'OLD_GUARD.json', self.guard)

    def restage_plan(self):
        self.plan_ref = self.write(self.root / 'OLD_PLAN.json', self.plan)
        self.allocation['plan_sha256'] = self.plan_ref['sha256']
        self.allocation_ref = self.write(self.root / 'OLD_ALLOCATION.json', self.allocation)
        self.guard.update(plan_path=self.plan_ref['path'], plan_sha256=self.plan_ref['sha256'],
                          allocation_sha256=self.allocation_ref['sha256'])
        self.restage_guard()

    def scaffold(self, **changes):
        arguments = dict(old_guard_ref=self.guard_ref, old_plan_ref=self.plan_ref,
            new_source_root=self.source, output_root=self.output, approved_intake_sha256=self.intake, now=90)
        arguments.update(changes)
        return assembly.scaffold_immutable_files(**arguments)

    def boundary(self, cycle=40, row=None, pending=None, origin='TRAIN_COLLECTION', complete=True):
        selected = deepcopy(self.row if row is None else row)
        checkpoint = self.life / f'checkpoints/sleep_{cycle:06d}'
        commit = dict(adapter_path=str(checkpoint / 'adapter'), optimizer_rng_path=str(checkpoint / 'optimizer_rng.pt'),
            optimizer_steps=4000, checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        event = dict(event_id=selected['event_id'], actor='child', split='TRAIN', origin=origin,
                     text=selected['target'], source_sha256=selected['source_sha256'])
        state = dict(rows=[{} for unused in range(118)] + [selected], pending=pending, sleep_frontier=119,
            model_state_sha256=replay.digest(commit['checkpoint_sha256']), history=dict(events=[event]))
        record = dict(kind='SLEEP_COMPLETE' if complete else 'SLEEP_BEGIN', index=5000,
            journal_id='d' * 32, previous_sha256='b' * 64,
            document=dict(status='COMPLETE', cycle=cycle, checkpoint=commit,
                          resume_state=dict(state=state, sha256=replay.digest(state))))
        record['sha256'] = replay.digest(record)
        return (self.write(self.life / 'stream/records/00000000000000005000.json', record),
                self.write(checkpoint / 'COMMIT.json', commit))

    def finalize(self, scaffold, boundary=None, **changes):
        boundary_ref, checkpoint_ref = boundary or self.boundary()
        arguments = dict(scaffold_ref=scaffold['scaffold_ref'], boundary_ref=boundary_ref,
            checkpoint_ref=checkpoint_ref, approved_intake_sha256=self.intake, now=100)
        arguments.update(changes)
        return assembly.finalize_selection_bundle(**arguments)

    def test_scaffold_whitelists_old_pins_STARTUP_and_exact_three_helpers(self):
        staged = self.scaffold()
        self.assertEqual(set(staged['source_pins']), set(self.originals) | set(assembly.HELPER_PINS))
        for name, original in self.originals.items():
            self.assertEqual((self.source / name).read_bytes(), original)
            self.assertEqual((self.old_source / name).read_bytes(), original)
        self.assertEqual((self.source / 'STARTUP.md').read_bytes(), (self.old_source / 'STARTUP.md').read_bytes())
        self.assertEqual({str(path.relative_to(self.source)) for path in self.source.rglob('*') if path.is_file()},
                         set(staged['source_pins']) | {'STARTUP.md'})
        self.assertFalse(self.life.exists())
        self.assertFalse((self.output / 'MAIN_GO.json').exists())
        self.assertFalse((self.output / 'DRIVER_BINDING.json').exists())
        self.assertFalse((self.output / 'PROPOSED_GUARD.json').exists())
        for name in assembly.DISCLAIMERS:
            self.assertIs(staged[name], False)

    def test_plan_only_two_paths_allocation_only_plan_hash_and_runtime_actual_bytes(self):
        staged = self.scaffold()
        expected = deepcopy(self.plan)
        expected['source_root'] = str(self.source)
        expected['startup_context']['path'] = str(self.source / 'STARTUP.md')
        self.assertEqual(replay.read_bound(staged['plan_ref']), expected)
        self.assertEqual(replay.read_bound(staged['allocation_ref']),
                         dict(self.allocation, plan_sha256=staged['plan_ref']['sha256']))
        runtime = replay.read_bound(staged['runtime_ref'])
        for name in integration.DEPENDENCIES:
            self.assertEqual(runtime['dependencies'][name],
                             assembly.file_ref(self.source / (name.replace('.', '/') + '.py'))['sha256'])
        self.assertEqual(runtime['native_sha256'], integration.NATIVE_SHA256)

    def test_scaffold_then_actual_boundary_selects_its_next_cycle_without_GO(self):
        scaffold = self.scaffold()
        bundle = self.finalize(scaffold, self.boundary(cycle=47))
        selection = replay.read_bound(bundle['selection_ref'])
        self.assertEqual((bundle['source_cycle'], bundle['target_cycle']), (47, 48))
        self.assertEqual(replay.validate_selection(selection), selection)
        self.assertEqual(selection['selected'][0]['row_sha256'], integration.ROW_SHA256)
        self.assertEqual(selection['selected'][0]['selection_kind'], 'OBJECT_REPLAY')
        self.assertEqual(selection['selected'][0]['extra_presentations'], 4)
        self.assertEqual(selection['selected'][0]['support_event_ids'], ['child:segment:118'])
        self.assertFalse((self.output / 'MAIN_GO.json').exists())
        self.assertFalse((self.life / 'r168_targeted_replay').exists())
        self.assertFalse((self.life / 'checkpoints/sleep_000047/adapter').exists())
        self.assertIs(bundle['saved_state_ownership_verified'], False)
        self.assertIs(bundle['boundary_admitted'], False)

    def test_convenience_interface_builds_selection_without_live_actions(self):
        boundary_ref, checkpoint_ref = self.boundary(53)
        result = assembly.build_selection_bundle(old_guard_ref=self.guard_ref, old_plan_ref=self.plan_ref,
            new_source_root=self.source, output_root=self.output, boundary_ref=boundary_ref,
            checkpoint_ref=checkpoint_ref, approved_intake_sha256=self.intake, now=100)
        self.assertEqual(result['target_cycle'], 54)
        self.assertIs(result['main_go_created'], False)

    def test_explicit_Main_scope_patches_exact_guard_and_builds_final_source_pins(self):
        scaffold = self.scaffold()
        bundle = self.finalize(scaffold)
        original = (self.source / assembly.GUARD_PATH).read_bytes()
        explicit_scope = dict(life_root=str(self.life), life_role=replay.ROLE, target_cycle=41,
            plan_sha256=scaffold['plan_ref']['sha256'], runtime_sha256=scaffold['runtime_ref']['sha256'],
            approved_intake_sha256=self.intake, not_before=100, expires=1000)
        result = assembly.bind_main_go(selection_bundle_ref=bundle['selection_bundle_ref'],
                                       main_go_scope=explicit_scope, now=101)
        expected = assembly.driver.patch_guard(original, result['driver_binding_ref'])
        self.assertEqual((self.source / assembly.GUARD_PATH).read_bytes(), expected)
        self.assertEqual((self.old_source / assembly.GUARD_PATH).read_bytes(), original)
        changed = {name for name in result['source_pins']
                   if result['source_pins'][name] != scaffold['source_pins'][name]}
        self.assertEqual(changed, {assembly.GUARD_PATH})
        binding = replay.read_bound(result['driver_binding_ref'])
        self.assertEqual(binding['driver_sha256'], assembly.DRIVER_SHA256)
        for field in ('plan_ref', 'runtime_ref', 'selection_ref', 'main_go_ref'):
            self.assertFalse(Path(binding[field]['path']).is_relative_to(self.source))
        self.assertFalse(Path(result['driver_binding_ref']['path']).is_relative_to(self.source))
        selection = replay.read_bound(result['selection_ref'])
        go = replay.read_bound(result['main_go_ref'])
        replay.validate_go(go, result['selection_ref'], selection, self.intake, 101)
        self.assertEqual(go['expires'], self.plan['hard_end_unix'])
        new_guard = replay.read_bound(result['guard_ref'])
        self.assertEqual(new_guard, dict(self.guard, plan_path=scaffold['plan_ref']['path'],
            plan_sha256=scaffold['plan_ref']['sha256'], allocation_path=scaffold['allocation_ref']['path'],
            allocation_sha256=scaffold['allocation_ref']['sha256'], attempt_dir=str(self.output),
            resume=True, source_pins=result['source_pins']))
        stage = replay.read_bound(result['staged_source_ref'])
        self.assertEqual(Path(result['plan_ref']['path']).name, 'PROPOSED_PLAN.json')
        self.assertEqual(Path(result['config_ref']['path']).name, 'PROPOSED_GUARD.json')
        self.assertEqual(stage['guard_sha256'], result['guard_ref']['sha256'])
        self.assertEqual(stage['driver_binding'], result['driver_binding_ref'])
        for name in assembly.DISCLAIMERS:
            self.assertIs(result[name], False)
        self.assertFalse((self.root / 'stage/INVENTORY.json').exists())

    def test_bound_reference_supports_large_history_metadata_not_FIFOs_or_symlinks(self):
        document = {'large_history_fixture': 'x' * (1024 * 1024 + 1)}
        reference = self.write(self.root / 'LARGE.json', document)
        self.assertEqual(replay.read_bound(reference), document)
        link = self.root / 'link.json'
        link.symlink_to(reference['path'])
        with self.assertRaisesRegex(ValueError, 'canonical_absolute_path'):
            assembly.file_ref(link)
        fifo = self.root / 'fifo'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'bounded_regular_reference'):
            assembly.file_ref(fifo)

    def test_unknown_CPU_evidence_refuses_before_writing_source(self):
        reference = self.write(self.root / 'UNKNOWN_CPU.json', {'failures': 0, 'errors': 0})
        with self.assertRaisesRegex(ValueError, 'approved_local_CPU_evidence_hash'):
            self.scaffold(cpu_evidence_ref=reference)
        self.assertFalse(self.output.exists())

    def test_unknown_dependency_hash_cannot_be_laundered_through_old_pins(self):
        name = 'gpu/orch_r144_sleep_targets.py'
        (self.old_source / name).write_bytes(b'not the approved dependency\n')
        self.guard['source_pins'][name] = assembly.file_ref(self.old_source / name)['sha256']
        self.restage_guard()
        with self.assertRaisesRegex(ValueError, 'source_candidate_matches_native_CPU_evidence'):
            self.scaffold()
        self.assertFalse(self.output.exists())

    def test_old_source_or_STARTUP_hash_mismatch_refuses_before_writes(self):
        for relative in ('STARTUP.md', 'gpu/pinned_but_not_imported.py'):
            with self.subTest(relative=relative):
                path = self.old_source / relative
                original = path.read_bytes()
                path.write_bytes(original + b'changed\n')
                with self.assertRaisesRegex(ValueError, 'native_source_pin'):
                    self.scaffold()
                path.write_bytes(original)
                self.assertFalse(self.output.exists())

    def test_source_pins_reject_traversal_and_non_python(self):
        for name in ('../outside.py', '/tmp/outside.py', 'gpu/../outside.py', 'PROGRAMME.md'):
            with self.subTest(name=name):
                self.guard['source_pins'][name] = 'a' * 64
                self.restage_guard()
                with self.assertRaisesRegex(ValueError, 'relative_python_pin'):
                    self.scaffold()
                del self.guard['source_pins'][name]
        self.assertFalse(self.output.exists())

    def test_modified_or_missing_helper_hash_rejected(self):
        helpers = self.root / 'helper_candidate'
        for name in assembly.HELPER_PINS:
            destination = helpers / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((assembly.REPO_ROOT / name).read_bytes())
        path = helpers / 'gpu/orch_r168_targeted_replay_driver.py'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'native_source_pin'):
            self.scaffold(helper_source_root=helpers)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.scaffold(helper_source_root=helpers)
        self.assertFalse(self.output.exists())

    def test_scaffold_rejects_preexisting_destination_or_source_nested_metadata(self):
        self.source.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'fresh_staging_destination'):
            self.scaffold()
        with self.assertRaisesRegex(ValueError, 'external_binding_metadata_outside_source'):
            self.scaffold(new_source_root=self.root / 'fresh', output_root=self.root / 'fresh/metadata')

    def test_unvetted_added_files_and_symlinks_refuse_finalization(self):
        scaffold = self.scaffold()
        for name in ('UNVETTED.md', 'gpu/extra.py', 'unexpected.pth'):
            with self.subTest(name=name):
                path = self.source / name
                path.write_text('unvetted')
                with self.assertRaisesRegex(ValueError, 'source_whitelist_only'):
                    self.finalize(scaffold)
                path.unlink()
        link = self.source / 'gpu/link.py'
        link.symlink_to(self.old_source / 'gpu/__init__.py')
        with self.assertRaisesRegex(ValueError, 'no_source_symlinks'):
            self.finalize(scaffold)
        self.assertFalse((self.output / 'SELECTION.json').exists())

    def test_mutated_staged_source_hash_refuses_finalization(self):
        scaffold = self.scaffold()
        path = self.source / 'gpu/orch_r144_sleep_targets.py'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'source_pin_delta_or_unknown_hash'):
            self.finalize(scaffold)
        self.assertFalse((self.output / 'MAIN_GO.json').exists())

    def test_rebound_plan_allocation_and_runtime_still_reject_nonallowed_deltas(self):
        scaffold = self.scaffold()
        original_scaffold = replay.read_bound(scaffold['scaffold_ref'])
        for field, change, reason in (
                ('plan_ref', {'max_sleeps': 801}, 'plan_paths_only_delta'),
                ('allocation_ref', {'declared_unix': 100}, 'allocation_plan_hash_only'),
                ('runtime_ref', {'native_sha256': 'c' * 64}, 'actual_source_runtime_binding')):
            with self.subTest(field=field):
                original = replay.read_bound(original_scaffold[field])
                path = Path(original_scaffold[field]['path'])
                changed_ref = self.write(path, dict(original, **change))
                modified = dict(original_scaffold, **{field: changed_ref})
                modified_ref = self.write(Path(scaffold['scaffold_ref']['path']), modified)
                with self.assertRaisesRegex(ValueError, reason):
                    self.finalize({'scaffold_ref': modified_ref})
                self.write(path, original)
        self.assertFalse((self.output / 'SELECTION.json').exists())

    def test_wrong_life_physical_baseline_or_wall_extension_refused(self):
        for field, value in (('root', '/tmp/other-life'), ('physical', 2), ('gpu_uuid', 'other-device'),
                             ('new_presentations', 17), ('authorized_wall_extension', {'added': 1})):
            with self.subTest(field=field):
                original = deepcopy(self.plan)
                self.plan[field] = value
                self.restage_plan()
                with self.assertRaisesRegex(ValueError, 'exact_creative_reread_physical1_baseline'):
                    self.scaffold()
                self.plan = original
        self.assertFalse(self.output.exists())

    def test_uncompleted_pending_untrusted_or_rewritten_row_boundary_rejected(self):
        scaffold = self.scaffold()
        rewritten = dict(self.row, target=self.row['target'] + ' polished')
        bad_split = dict(self.row, split='VALIDATION')
        for arguments in ({'complete': False}, {'pending': {'update': True}},
                          {'origin': 'SEALED'}, {'row': rewritten}, {'row': bad_split}):
            with self.subTest(arguments=list(arguments)):
                with self.assertRaises(ValueError):
                    self.finalize(scaffold, self.boundary(**arguments))
                self.assertFalse((self.output / 'SELECTION.json').exists())

    def test_COMMIT_mismatch_or_foreign_path_refused(self):
        scaffold = self.scaffold()
        boundary_ref, commit_ref = self.boundary()
        foreign_ref = self.write(self.root / 'COMMIT.json', replay.read_bound(commit_ref))
        with self.assertRaisesRegex(ValueError, 'own_completed_checkpoint_only'):
            self.finalize(scaffold, (boundary_ref, foreign_ref))
        commit = replay.read_bound(commit_ref)
        commit['optimizer_steps'] += 1
        commit_ref = self.write(Path(commit_ref['path']), commit)
        with self.assertRaisesRegex(ValueError, 'nonfrozen_completed_checkpoint'):
            self.finalize(scaffold, (boundary_ref, commit_ref))

    def test_exact_predeclared_intake_and_valid_time_required(self):
        scaffold = self.scaffold()
        with self.assertRaisesRegex(ValueError, 'exact_predeclared_scaffold_intake'):
            self.finalize(scaffold, approved_intake_sha256='d' * 64)
        for now in (True, float('nan'), 89, 1000, 1001):
            with self.subTest(now=now), self.assertRaises(ValueError):
                self.finalize(scaffold, now=now)
        self.assertFalse((self.output / 'SELECTION.json').exists())

    def test_GO_requires_explicit_exact_scope_and_fixed_unexpired_hardwall(self):
        bundle = self.finalize(self.scaffold())
        expected = bundle['expected_main_go_scope']
        scopes = [None, {}, dict(expected, target_cycle=42), dict(expected, target_cycle=41.0),
                  dict(expected, expires=1001),
                  dict(expected, expires=999), dict(expected, approved_intake_sha256='d' * 64),
                  dict(expected, human_ratified=True)]
        for scope in scopes:
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'explicit_Main_exact_scope_required'):
                assembly.bind_main_go(selection_bundle_ref=bundle['selection_bundle_ref'],
                                      main_go_scope=scope, now=101)
        for now in (99, 1000, float('inf')):
            with self.subTest(now=now), self.assertRaises(ValueError):
                assembly.bind_main_go(selection_bundle_ref=bundle['selection_bundle_ref'],
                                      main_go_scope=deepcopy(expected), now=now)
        self.assertFalse((self.output / 'MAIN_GO.json').exists())
        self.assertEqual((self.source / assembly.GUARD_PATH).read_bytes(), self.originals[assembly.GUARD_PATH])

    def test_boundary_or_source_changed_after_selection_cannot_get_GO(self):
        bundle = self.finalize(self.scaffold())
        self.boundary(cycle=41)
        with self.assertRaisesRegex(ValueError, 'metadata_hash_mismatch'):
            assembly.bind_main_go(selection_bundle_ref=bundle['selection_bundle_ref'],
                main_go_scope=deepcopy(bundle['expected_main_go_scope']), now=101)
        self.assertFalse((self.output / 'MAIN_GO.json').exists())

    def test_staging_and_selection_outputs_are_create_only(self):
        scaffold = self.scaffold()
        with self.assertRaisesRegex(ValueError, 'fresh_staging_destination'):
            self.scaffold()
        self.finalize(scaffold)
        with self.assertRaises(FileExistsError):
            self.finalize(scaffold)


if __name__ == '__main__':
    unittest.main()
