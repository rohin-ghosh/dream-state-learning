import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from retired_coalescer import DurableLedger,digest
import run_approved_remaining as subject


class RemainingTransportTests(unittest.TestCase):
    def test_exact_published_index_and_evidence_load(self):
        payload = subject.load_payload()
        self.assertEqual(digest(payload['index']), subject.INDEX_SHA256)
        self.assertEqual(len(payload['batches']), 125)
        self.assertEqual(payload['index']['replacements'], 3189)

    def test_per_batch_receipt_is_durable_before_ack(self):
        temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        ledger = DurableLedger(directory / 'ledger.jsonl')
        self.addCleanup(ledger.close)
        entry = dict(sequence=0,previous_sha256='0'*64,kind='REMAINING_BATCH_POSTCHECK',document=dict(ordinal=1))
        entry['sha256'] = digest(entry)

        class CheckedWriter(io.StringIO):
            def write(self,text):
                receipt = json.loads((directory / 'BATCH_0001_VERIFIED.json').read_bytes())
                if json.loads(text) != dict(durable=True,sha256=receipt['sha256']):
                    raise AssertionError('receipt missing before acknowledgement')
                return super().write(text)

        process = Mock(stdin=CheckedWriter(),stdout=io.StringIO(json.dumps(entry)+'\n'))
        process.wait.return_value = 0
        self.assertEqual(subject.relay(process,ledger,directory),(0,entry))

    def test_remote_worker_syntax_valid_without_execution(self):
        compile(subject.REMOTE,'remaining_worker_cpu_syntax','exec')


if __name__ == '__main__':
    unittest.main()
