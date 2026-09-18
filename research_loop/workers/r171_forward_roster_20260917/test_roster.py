import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location('r171_roster_tests', Path(__file__).with_name('ROSTER.py'))
roster = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(roster)


class RosterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_dedup_is_exact_node_and_root_not_label_or_parent_count(self):
        rows = {}
        reference = dict(path='/local/CONFIG.json', sha256='a' * 64)
        roster.add_seed(rows, 'ovx2', '/same/life', 'first', reference, parent={})
        roster.add_seed(rows, 'ovx2', '/same/life', 'second', reference, parent={})
        roster.add_seed(rows, 'ovx3', '/same/life', 'third', reference, parent={})
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows['ovx2', '/same/life']['parent_configs']), 2)

    def test_native_entry_excludes_timer_supervisor_readout_and_evaluator(self):
        self.assertEqual(roster.native_entry(['python3', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', '/guard']), 'gpu.orch_r125_continual_guard')
        for argv in (['timeout', 'python3', '-m', 'gpu.orch_r125_continual_guard', 'native'],
                     ['python3', '-m', 'gpu.orch_r125_continual_guard', 'supervise'],
                     ['python3', '-m', 'gpu.orch_r167_fleet_eval', 'native'],
                     ['python3', '-m', 'gpu.orch_r139_continual_controls', '--readout-manifest', '/manifest']):
            self.assertIsNone(roster.native_entry(argv))

    def test_exact_node1_control_native_entry_is_supported_but_supervisor_is_not(self):
        module = 'gpu.orch_r136_node1_launcher'
        self.assertEqual(roster.native_entry(['python3', '-m', module, 'control-native', '--config', '/guard']), module)
        self.assertIsNone(roster.native_entry(['python3', '-m', module, 'control-supervise', '--config', '/guard']))

    def test_training_control_is_explicit_not_inferred_from_name(self):
        self.assertIsNone(roster.training_mode({'root': '/frozen-control'})['training_enabled'])
        self.assertIs(roster.training_mode({'schema': 'R125_NATIVE_CONTINUITY_V1'})['training_enabled'], True)
        for mode in ('frozen_rank8_no_sleep', 'frozen_base_no_adapter'):
            plan = dict(control=dict(mode=mode, learning_steps=0, optimizer_steps=0, sleep_enabled=False))
            self.assertIs(roster.training_mode(plan)['training_enabled'], False)
            plan['control']['optimizer_steps'] = 1
            self.assertIsNone(roster.training_mode(plan)['training_enabled'])

    def test_projection_does_not_expose_prompts_targets_or_source_pin_manifest(self):
        source = dict(root='/life', source_root='/source', physical=1, birth_prompt='private train text',
                      source_pins={'file.py': 'pin'}, control=dict(mode='frozen_base_no_adapter', adapter=None))
        projected = roster.plan_projection(source)
        self.assertNotIn('birth_prompt', projected)
        self.assertNotIn('source_pins', projected)
        self.assertEqual(projected['control'], dict(mode='frozen_base_no_adapter', adapter_present=False))

    def test_reader_refuses_nonoperational_paths_before_open(self):
        reader = roster.Reader(1024)
        for name in ('SCORES.json', 'answers.json', 'condition-map.json', 'readout/REQUEST.json'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'forbidden_nonoperational_path'):
                reader.document(self.root / name)
        self.assertEqual(reader.used, 0)

    def test_reader_enforces_caps_and_caches_metadata(self):
        path = self.root / 'CONFIG.json'
        path.write_text('{"root":"/life"}')
        reader = roster.Reader(1024)
        first = reader.document(path)
        used = reader.used
        self.assertEqual(reader.document(path), first)
        self.assertEqual(reader.used, used)
        with self.assertRaisesRegex(ValueError, 'aggregate_read_cap'):
            roster.Reader(2).document(path)
        with self.assertRaisesRegex(ValueError, 'per_file_read_cap'):
            roster.Reader(1024).document(path, limit=2)

    def test_head_limit_refuses_before_filesystem_reads(self):
        for limit in (0, 33, True):
            with self.assertRaisesRegex(ValueError, 'max_32_head_records'):
                roster.head_metadata(roster.Reader(1024), '/localhome/local-rohing/orch_fixture/life', limit)

    def test_missing_identity_is_unknown_not_retired_and_multiple_not_live(self):
        seeds = [dict(node='ovx2', life_root='/life', labels=['example'], parent_configs=[],
                      discovery_refs=[], registrations=[])]
        document = dict(seed_rows=seeds, node_passes={}, ended_evidence=[])
        self.assertEqual(roster.assemble(document)['rows'][0]['status'], 'UNKNOWN')
        native = dict(plan=dict(root='/life', source_root='/source', physical=1), training=roster.training_mode({}))
        document['node_passes'] = {'ovx2': dict(observation=dict(native_processes=[native, native]))}
        self.assertEqual(roster.assemble(document)['rows'][0]['status'], 'UNKNOWN')

    def test_explicit_exit_is_excluded_without_inventing_new_admission(self):
        registration = dict(life_id='R158_parented_learning', status='SOURCE_CANDIDATE')
        seed = dict(node='a40r', life_root='/ended', labels=['R158'], parent_configs=[], discovery_refs=[], registrations=[registration])
        document = dict(seed_rows=[seed], node_passes={}, ended_evidence=[dict(life_id='R158_parented_learning')])
        result = roster.assemble(document)
        self.assertEqual(result['rows'][0]['status'], 'ENDED_EXCLUDED')
        self.assertEqual(result['summary']['live_native_lives'], 0)

    def test_duplicate_node_attempt_refused_without_calling_wrapper(self):
        with mock.patch.object(roster.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'at_most_one_wrapper_pass_per_node'):
                roster.observe_all(dict(node_passes={'a100': dict(attempted=True)}))
        run.assert_not_called()

    def test_readonly_remote_module_can_load_without_stdin_path_or_cli_side_effects(self):
        namespace = dict(__file__=str(Path(roster.__file__).resolve()), __name__='r171_remote_readonly')
        with mock.patch.object(roster.subprocess, 'run') as run:
            exec(compile(Path(roster.__file__).read_text(), '<stdin-roster>', 'exec'), namespace)
        run.assert_not_called()
        self.assertEqual(namespace['NODE_CAP'], 14 * 1024 * 1024)

    def test_explicit_registry_process_storage_alias_counts_one_live_learner_without_claiming_storage(self):
        registration = dict(life_id='repo_reader', process_plan_root='/original', storage_root='/recovery', status='MISSING_CUSTODY_NOT_NEGATIVE')
        seed = dict(node='ovx3', life_root='/recovery', labels=['repo_reader'], parent_configs=[], discovery_refs=[], registrations=[registration])
        native = dict(plan=dict(root='/original', source_root='/recovery-source', physical=7), training=roster.training_mode({}))
        document = dict(seed_rows=[seed], ended_evidence=[], node_passes={'ovx3': dict(observation=dict(native_processes=[native]))})
        result = roster.assemble(document)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['life_root'], '/original')
        self.assertEqual(result['rows'][0]['declared_storage_root'], '/recovery')
        self.assertIsNone(result['rows'][0]['current_storage_saved_cycle'])
        self.assertEqual(result['summary']['live_missing_from_R167'], [])
        self.assertEqual(result['summary']['live_declared_missing_source_custody'], ['repo_reader'])


if __name__ == '__main__':
    unittest.main()
