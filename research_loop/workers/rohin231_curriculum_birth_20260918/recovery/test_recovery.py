from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from gpu import r232_recovery as recovery
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


def checkpoint():
    stream = ContinualStream(TrainHistory(system_prompt='System', birth_prompt='Exact birth'),
        context_limit=4096, segment_tokens=512, segments_per_sleep=3,
        deadline_unix=2000000000, model_state_sha256='a' * 64)
    result = stream.checkpoint()
    result['state']['sleep_receipts'] = [dict(status='COMPLETE')]
    result['sha256'] = digest(result['state'])
    return result


class RecoveryTests(unittest.TestCase):
    def test_observed_protected_contexts_fit_without_edits(self):
        for token_count in (3637, 3600):
            with self.subTest(tokens=token_count):
                previous = checkpoint()
                document = recovery.epoch_document(previous, 'b' * 64)
                stream = ContinualStream.restore(document['state'], expected_sha256=document['state']['sha256'])
                before = stream.checkpoint()
                records = []
                result = stream.compact_for_prompt(lambda messages: token_count,
                    lambda *args: records.append(args), threshold=6144 * 3 // 4, protected_from=0)
                self.assertEqual(result.token_count, token_count)
                self.assertEqual(stream.checkpoint(), before)
                self.assertEqual(records, [])
                self.assertGreater(token_count, 4096 * 3 // 4 - 1)

    def test_only_context_changes_and_cannot_apply_twice(self):
        previous = checkpoint()
        document = recovery.epoch_document(previous, 'b' * 64)
        current = deepcopy(document['state']['state'])
        current['context_limit'] = 4096
        self.assertEqual(current, previous['state'])
        with self.assertRaises(ValueError):
            recovery.epoch_document(document['state'], 'b' * 64)

    def test_pending_untrained_or_plain_state_rejected(self):
        for key, value in [('pending', 'request'), ('sleep_frontier', 1), ('presentation', {'version': 'other'})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                previous = checkpoint()
                previous['state'][key] = value
                recovery.epoch_document(previous, 'b' * 64)

    def test_journal_rejects_any_non_context_change(self):
        previous = checkpoint()
        document = recovery.epoch_document(previous, 'b' * 64)
        state = dict(latest=dict(document=previous), request=None, response=None, sleep_request=None)
        for key, value in [('deadline_unix', 2100000000), ('model_state_sha256', 'c' * 64), ('segment_tokens', 1024)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                forged = deepcopy(document)
                forged['state']['state'][key] = value
                forged['state']['sha256'] = digest(forged['state']['state'])
                recovery.EpochJournalMixin()._advance(deepcopy(state), 'R232_RECOVERY_CONTEXT', forged)


if __name__ == '__main__':
    unittest.main()
