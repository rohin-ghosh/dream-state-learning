from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import prepare_continuation as prepare
import run_continuation as runner
import retired_coalescer


class ContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts, cls.manifest, cls.batches, cls.proof = prepare.original_state()

    def test_completed_chains_and_batch9_admission_failure_bound(self):
        self.assertEqual([row['ordinal'] for row in self.proof['completed_batches']], list(range(1, 9)))
        self.assertTrue(self.proof['fresh_diagnostics_do_not_recover_original_failed_scan'])

    def test_exact_original_95_batches_exclude_every_completed_group(self):
        entries, selected = prepare.selected_remaining(self.manifest, self.batches)
        self.assertEqual([row['ordinal'] for row in entries], list(range(9, 104)))
        self.assertEqual([group['selection_index'] for batch in selected for group in batch['groups']], list(range(41, 515)))
        self.assertEqual(sum(row['paths'] for row in entries), 3792)
        self.assertEqual(sum(row['replacements'] for row in entries), 2844)
        self.assertEqual(sum(row['potential_allocated_bytes'] for row in entries), 1446039552)

    def test_reintroduced_completed_group_rejected(self):
        changed = deepcopy(self.batches)
        changed[8]['groups'][0] = deepcopy(changed[0]['groups'][0])
        with self.assertRaisesRegex(ValueError, 'permanent_exclusion'):
            prepare.selected_remaining(self.manifest, changed)

    def test_completed_batch_not_receivable_even_with_supplied_approval(self):
        with self.assertRaisesRegex(ValueError, 'no_completed_batch'):
            runner.remote_program(self.artifacts, self.batches[0], dict(batch_sha256='not_authorization'))

    def test_receiver_seam_only_replaces_original_call_and_adds_diagnostic_module(self):
        self.assertEqual(prepare.prior.REMOTE.count(runner.OLD_CALL), 1)
        body = prepare.prior.REMOTE.replace(runner.OLD_CALL, runner.NEW_CALL)
        self.assertEqual(body.replace(runner.NEW_CALL, runner.OLD_CALL), prepare.prior.REMOTE)
        for batch in [self.batches[8], self.batches[-1]]:
            program = runner.remote_program(self.artifacts, batch, dict(batch_sha256=retired_coalescer.digest(batch)))
            compile(program, 'CPU_ONLY_RECEIVER_COMPILE', 'exec')
            self.assertLess(len(prepare.frozen.encoded_command(program).encode()), 100000)

    def test_new_binding_and_all_fields_required(self):
        binding = dict(runner.binding_template('fixture'), status='MAIN_REVIEWED_EXECUTION')
        self.assertEqual(runner.validate_binding(json.dumps(binding), 'fixture'), binding)
        with self.assertRaisesRegex(ValueError, 'fresh_Main_exact_diagnostic'):
            runner.validate_binding(json.dumps(runner.binding_template('fixture')), 'fixture')
        for key in binding:
            changed = dict(binding)
            changed[key] = 'changed'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'fresh_Main_exact_diagnostic'):
                runner.validate_binding(json.dumps(changed), 'fixture')

    def test_old_main_binding_cannot_authorize_continuation(self):
        raw = (prepare.PRIOR / 'EXECUTION/MAIN_BINDING.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'fresh_Main_exact_diagnostic'):
            runner.validate_binding(raw, 'fixture')

    def test_first_failed_new_batch_halts_without_later_launch(self):
        entries, selected = prepare.selected_remaining(self.manifest, self.batches)
        manifest = dict(batches=entries[:2], provenance=self.proof)
        event = dict(sequence=0, previous_sha256='0' * 64, kind='CPU_RAW_SCAN_FAILURE', document={})
        event['sha256'] = retired_coalescer.digest(event)
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO(json.dumps(event) + '\n'))
        process.wait.return_value = 1
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            with patch.object(runner, 'OUTPUT', work / 'EXECUTION'), \
                    patch.object(runner, 'load_prepared', return_value=(self.artifacts, manifest, 'fixture', selected[:2])), \
                    patch.object(runner.subprocess, 'Popen', return_value=process) as start:
                binding = dict(runner.binding_template('fixture'), status='MAIN_REVIEWED_EXECUTION')
                path = work / 'binding.json'
                path.write_text(json.dumps(binding))
                with self.assertRaisesRegex(ValueError, 'first_error_halts'):
                    runner.run(path)
                self.assertEqual(start.call_count, 1)
                self.assertTrue((runner.OUTPUT / 'BATCH_0009/HALTED.json').is_file())
                self.assertFalse((runner.OUTPUT / 'BATCH_0010').exists())
                self.assertEqual(json.loads((runner.OUTPUT / 'BATCH_0009/LEDGER.jsonl').read_text()), event)

    def test_existing_new_execution_directory_cannot_be_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            with patch.object(runner, 'OUTPUT', work), \
                    patch.object(runner, 'load_prepared', return_value=({}, {}, 'fixture', [])), \
                    patch.object(runner.subprocess, 'Popen') as start:
                binding = dict(runner.binding_template('fixture'), status='MAIN_REVIEWED_EXECUTION')
                path = work / 'binding.json'
                path.write_text(json.dumps(binding))
                with self.assertRaises(FileExistsError):
                    runner.run(path)
                start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
