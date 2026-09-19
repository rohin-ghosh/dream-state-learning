from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import prepare_remaining as prepare
import run_remaining as runner
from verify_completed_canary import FROZEN, frozen, local_proof
import node2_scope
import retired_coalescer


class RemainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = frozen.frozen_artifacts()
        cls.assessment = json.loads(cls.artifacts['GROUPS.json'])
        cls.canary = json.loads(cls.artifacts['CANARY.json'])
        cls.completion = json.loads((FROZEN / 'CANARY_EXECUTION/VERIFIED.json').read_bytes())

    def plan(self, **changes):
        values = dict(assessment=deepcopy(self.assessment), canary=deepcopy(self.canary), completion=deepcopy(self.completion))
        values.update(changes)
        return prepare.plan_batches(**values)

    def test_independent_canary_chain_and_exact_binding(self):
        self.assertEqual(local_proof()['ledger_records'], 24)

    def test_exact_514_groups_4112_paths_103_bounded_batches(self):
        batches = self.plan()
        self.assertEqual(len(batches), 103)
        groups = [group for batch in batches for group in batch['groups']]
        self.assertEqual([group['selection_index'] for group in groups], list(range(1, 515)))
        paths = [path for group in groups for path in prepare.group_paths(group)]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 4112)
        self.assertTrue(all(batch['max_paths'] <= 40 for batch in batches))
        self.assertEqual(sum(group['potential_allocated_bytes_freed'] for group in groups), 1831120896)

    def test_no_canary_path_in_any_batch(self):
        excluded = set(prepare.group_paths(self.canary['groups'][0]))
        for batch in self.plan():
            self.assertFalse(excluded.intersection(path for group in batch['groups'] for path in prepare.group_paths(group)))

    def test_all_proposals_pass_actual_frozen_batch_and_scope_validation(self):
        with patch.object(retired_coalescer, 'owned_retired_path', side_effect=lambda path, root: Path(path)):
            for batch in self.plan():
                checksum = retired_coalescer.digest(batch)
                paths = retired_coalescer.validate_batch(batch, checksum, node2_scope.ROOT,
                    dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256=checksum))
                self.assertEqual(len(paths), batch['max_paths'])

    def test_changed_group_rejected(self):
        changed = deepcopy(self.assessment)
        changed['groups'][1]['metadata']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_original_515'):
            self.plan(assessment=changed)

    def test_duplicate_group_rejected(self):
        changed = deepcopy(self.assessment)
        changed['groups'][1] = deepcopy(changed['groups'][2])
        with self.assertRaisesRegex(ValueError, 'exact_original_515'):
            self.plan(assessment=changed)

    def test_missing_canary_path_rejected(self):
        changed = deepcopy(self.completion)
        changed['completion']['document']['paths'].pop()
        with self.assertRaisesRegex(ValueError, 'all_canary_paths'):
            self.plan(completion=changed)

    def test_failed_canary_rejected(self):
        changed = deepcopy(self.completion)
        changed['ssh_exit'] = 1
        with self.assertRaisesRegex(ValueError, 'successful_canary'):
            self.plan(completion=changed)

    def test_actual_frozen_validator_rejects_mutated_batch_group(self):
        batch = self.plan()[0]
        batch['groups'][0]['metadata']['sha256'] = '0' * 64
        checksum = retired_coalescer.digest(batch)
        with self.assertRaisesRegex(ValueError, 'exact_selected_group_bytes'):
            retired_coalescer.validate_batch(batch, checksum, node2_scope.ROOT,
                dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256=checksum))

    def test_template_is_not_authorization(self):
        with self.assertRaisesRegex(ValueError, 'fresh_Main_exact_remaining'):
            runner.validate_binding(json.dumps(runner.binding_template('fixture')), 'fixture')

    def test_all_exact_binding_fields_are_required(self):
        binding = dict(runner.binding_template('fixture'), status='MAIN_REVIEWED_EXECUTION')
        self.assertEqual(runner.validate_binding(json.dumps(binding), 'fixture'), binding)
        for key in binding:
            changed = dict(binding)
            changed[key] = 'wrong'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'fresh_Main_exact_remaining'):
                runner.validate_binding(json.dumps(changed), 'fixture')

    def test_every_receiving_command_is_bounded_and_compiles_without_execution(self):
        for batch in self.plan():
            checksum = retired_coalescer.digest(batch)
            approval = dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256=checksum)
            program = runner.remote_program(self.artifacts, batch, approval)
            compile(program, 'CPU_RECEIVING_COMPILE_ONLY', 'exec')
            self.assertLess(len(frozen.encoded_command(program).encode()), 100000)

    def test_derived_batch_approval_keeps_manifest_and_prior_chain(self):
        binding = dict(runner.binding_template('manifest'), status='MAIN_REVIEWED_EXECUTION')
        entry = dict(sha256='batch', ordinal=3)
        approval = runner.batch_approval(binding, b'raw_binding', entry, 'prior_chain')
        self.assertEqual(approval['manifest_sha256'], 'manifest')
        self.assertEqual(approval['batch_sha256'], 'batch')
        self.assertEqual(approval['previous_batch_completion_sha256'], 'prior_chain')
        self.assertTrue(approval['ledger_path'].endswith('EXECUTION/BATCH_0003/LEDGER.jsonl'))

    def test_missing_binding_never_starts_process(self):
        with patch.object(runner, 'load_prepared', return_value=({}, {}, 'fixture', [])), \
                patch.object(runner.subprocess, 'Popen') as start:
            with self.assertRaises(FileNotFoundError):
                runner.run(prepare.HERE / 'NO_SUCH_MAIN_BINDING.json')
        start.assert_not_called()

    def test_nonzero_first_batch_halts_without_next_batch_or_retry(self):
        batches = self.plan()[:2]
        entries = [dict(ordinal=batch['ordinal'], sha256=retired_coalescer.digest(batch)) for batch in batches]
        manifest = dict(batches=entries, completed_canary=dict(final_chain='canary_fixture'))
        event = dict(sequence=0, previous_sha256='0' * 64, kind='CPU_FAILURE', document={})
        event['sha256'] = retired_coalescer.digest(event)
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO(json.dumps(event) + '\n'))
        process.wait.return_value = 1
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            with patch.object(runner, 'OUTPUT', work / 'EXECUTION'), \
                    patch.object(runner, 'load_prepared', return_value=(self.artifacts, manifest, 'fixture', batches)), \
                    patch.object(runner.subprocess, 'Popen', return_value=process) as start:
                binding = dict(runner.binding_template('fixture'), status='MAIN_REVIEWED_EXECUTION')
                binding_path = work / 'binding.json'
                binding_path.write_text(json.dumps(binding))
                with self.assertRaisesRegex(ValueError, 'no_further_batches'):
                    runner.run(binding_path)
                self.assertEqual(start.call_count, 1)
                self.assertTrue((runner.OUTPUT / 'BATCH_0001/HALTED.json').is_file())
                self.assertFalse((runner.OUTPUT / 'BATCH_0002').exists())
                saved = json.loads((runner.OUTPUT / 'BATCH_0001/LEDGER.jsonl').read_text())
                self.assertEqual(saved, event)

    def test_existing_execution_directory_rejects_before_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            with patch.object(runner, 'OUTPUT', work), \
                    patch.object(runner, 'load_prepared', return_value=({}, {}, 'fixture', [])), \
                    patch.object(runner.subprocess, 'Popen') as start:
                binding = dict(runner.binding_template('fixture'), status='MAIN_REVIEWED_EXECUTION')
                binding_path = work / 'binding.json'
                binding_path.write_text(json.dumps(binding))
                with self.assertRaises(FileExistsError):
                    runner.run(binding_path)
                start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
