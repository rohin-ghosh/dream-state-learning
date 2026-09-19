import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from retired_coalescer import DurableLedger, digest
from run_approved_canary import relay_acknowledgements


class CanaryTransportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(directory.cleanup)
        self.ledger = DurableLedger(Path(directory.name) / 'ledger.jsonl')
        self.addCleanup(self.ledger.close)

    def test_ack_is_sent_only_after_exact_durable_record(self):
        entry = dict(sequence=0, previous_sha256='0' * 64, kind='CPU_EVENT', document={})
        entry['sha256'] = digest(entry)
        ledger = self.ledger

        class CheckedWriter(io.StringIO):
            def write(self, text):
                saved = json.loads(ledger.path.read_text())
                self.assertion = json.loads(text) == dict(durable=True, sha256=saved['sha256'])
                if not self.assertion:
                    raise AssertionError('acknowledgement before exact durable record')
                return super().write(text)

        process = Mock(stdin=CheckedWriter(), stdout=io.StringIO(json.dumps(entry) + '\n'))
        process.wait.return_value = 0
        status, last = relay_acknowledgements(process, self.ledger)
        self.assertEqual((status, last), (0, entry))
        self.assertTrue(process.stdin.assertion)

    def test_invalid_sequence_gets_no_ack_and_closes_transport(self):
        entry = dict(sequence=1, previous_sha256='0' * 64, kind='CPU_EVENT', document={})
        entry['sha256'] = digest(entry)
        output = Mock()
        process = Mock(stdin=output, stdout=io.StringIO(json.dumps(entry) + '\n'))
        with self.assertRaisesRegex(ValueError, 'durable_ledger_exact_sequence'):
            relay_acknowledgements(process, self.ledger)
        output.write.assert_not_called()
        output.close.assert_called_once()

    def test_empty_worker_output_never_means_success(self):
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO(''))
        process.wait.return_value = 1
        self.assertEqual(relay_acknowledgements(process, self.ledger), (1, None))
        self.assertEqual(self.ledger.sequence, 0)


if __name__ == '__main__':
    unittest.main()
