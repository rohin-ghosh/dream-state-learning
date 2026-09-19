import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from retired_coalescer import DurableLedger, digest
import transport_canary as subject


class TransportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.ledger = DurableLedger(self.work / 'LEDGER.jsonl')
        self.addCleanup(self.ledger.close)

    def event(self):
        entry = dict(sequence=0, previous_sha256='0' * 64, kind='CPU_EVENT', document={})
        return dict(entry, sha256=digest(entry))

    def test_frozen_payload_imports_actual_four_modules_and_exact_bindings_in_memory(self):
        artifacts = subject.frozen_artifacts()
        program = subject.module_loader(artifacts) + '''
assert sys.modules['node2_scope'].BOUND_SCOPE is not None
assert sys.modules['retired_writer_guard'].BOUND_LOCKS is not None
assert callable(sys.modules['retired_coalescer'].execute_batch)
print('FOUR_FROZEN_MODULES_AND_BINDINGS_LOADED')
'''
        result = subprocess.run(subject.encoded_command(program), shell=True, check=True,
                                capture_output=True, text=True, timeout=10, cwd=self.work)
        self.assertEqual(result.stdout.strip(), 'FOUR_FROZEN_MODULES_AND_BINDINGS_LOADED')
        self.assertEqual(list(self.work.iterdir()), [self.ledger.path])

    def test_remote_program_compiles_without_execution(self):
        compile(subject.remote_program(subject.frozen_artifacts(), subject.binding_template()),
                'receiving_canary', 'exec')

    def test_complete_receiving_payload_fits_one_ssh_argument(self):
        binding = dict(subject.binding_template(), status='MAIN_REVIEWED_EXECUTION')
        command = subject.encoded_command(subject.remote_program(subject.frozen_artifacts(), binding))
        self.assertLess(len(command.encode()), 100000)

    def test_ack_only_after_actual_fsync_and_exact_ledger_record(self):
        ledger = self.ledger
        entry = self.event()
        real_fsync = subject.os.fsync
        with patch('os.fsync', wraps=real_fsync) as synced:
            class CheckedWriter(io.StringIO):
                def write(self, raw):
                    if not synced.call_count:
                        raise AssertionError('ACK before fsync')
                    if json.loads(ledger.path.read_text()) != entry:
                        raise AssertionError('ACK before exact record')
                    return super().write(raw)
            process = Mock(stdin=CheckedWriter(), stdout=io.StringIO(json.dumps(entry) + '\n'))
            process.wait.return_value = 0
            self.assertEqual(subject.relay_acknowledgements(process, ledger), (0, entry))

    def test_bad_sequence_gets_no_ack_and_closes_transport(self):
        entry = self.event()
        entry['sequence'] = 1
        entry['sha256'] = digest({key: value for key, value in entry.items() if key != 'sha256'})
        output = Mock()
        process = Mock(stdin=output, stdout=io.StringIO(json.dumps(entry) + '\n'))
        with self.assertRaisesRegex(ValueError, 'durable_ledger_exact_sequence'):
            subject.relay_acknowledgements(process, self.ledger)
        output.write.assert_not_called()
        output.close.assert_called_once()

    def test_failed_fsync_gets_no_ack_and_closes_transport(self):
        output = Mock()
        process = Mock(stdin=output, stdout=io.StringIO(json.dumps(self.event()) + '\n'))
        with patch('os.fsync', side_effect=OSError('CPU fsync fault')):
            with self.assertRaisesRegex(OSError, 'CPU fsync fault'):
                subject.relay_acknowledgements(process, self.ledger)
        output.write.assert_not_called()
        output.close.assert_called_once()

    def test_empty_output_is_not_success(self):
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO(''))
        process.wait.return_value = 1
        self.assertEqual(subject.relay_acknowledgements(process, self.ledger), (1, None))

    def test_actual_acknowledged_ledger_cpu_subprocess_roundtrip(self):
        program = subject.module_loader(subject.frozen_artifacts()) + '''
ledger=sys.modules['retired_coalescer'].AcknowledgedLedger(sys.stdin,sys.stdout)
ledger.record('CPU_INTENT',dict(synthetic_only=True))
ledger.record('CPU_COMPLETE',dict(synthetic_only=True))
'''
        with subprocess.Popen([sys.executable, '-u', '-B', '-c', program],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, bufsize=1, cwd=self.work) as process:
            status, last = subject.relay_acknowledgements(process, self.ledger)
            self.assertEqual(status, 0, process.stderr.read())
        self.assertEqual(last['kind'], 'CPU_COMPLETE')
        self.assertEqual(self.ledger.sequence, 2)

    def test_unapproved_template_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fresh_Main_exact'):
            subject.validate_binding(json.dumps(subject.binding_template()))

    def test_exact_binding_fields_and_typed_scope_required(self):
        binding = dict(subject.binding_template(), status='MAIN_REVIEWED_EXECUTION')
        self.assertEqual(subject.validate_binding(json.dumps(binding)), binding)
        for key in binding:
            with self.subTest(field=key):
                mutated = dict(binding)
                mutated[key] = 'mutated'
                with self.assertRaisesRegex(ValueError, 'fresh_Main_exact'):
                    subject.validate_binding(json.dumps(mutated))
        with self.assertRaisesRegex(ValueError, 'fresh_Main_exact'):
            subject.validate_binding(json.dumps(dict(binding, groups=True)))

    def test_missing_binding_never_starts_transport(self):
        with patch.object(subject.subprocess, 'Popen') as start:
            with self.assertRaises(FileNotFoundError):
                subject.run(self.work / 'missing.json')
        start.assert_not_called()

    def test_existing_output_prevents_any_retry(self):
        binding = dict(subject.binding_template(), status='MAIN_REVIEWED_EXECUTION')
        binding_path = self.work / 'binding.json'
        binding_path.write_text(json.dumps(binding))
        with patch.object(subject, 'OUTPUT', self.work), patch.object(subject.subprocess, 'Popen') as start:
            with self.assertRaises(FileExistsError):
                subject.run(binding_path)
        start.assert_not_called()

    def test_encoded_command_roundtrip_is_cpu_only(self):
        result = subprocess.run(subject.encoded_command("print('CPU_QUOTING_ONLY')"),
                                shell=True, capture_output=True, text=True, check=True, timeout=10)
        self.assertEqual(result.stdout.strip(), 'CPU_QUOTING_ONLY')


if __name__ == '__main__':
    unittest.main()
