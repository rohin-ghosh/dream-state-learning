from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import r232_runtime as frozen
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import digest


def previous():
    return dict(optimizer_steps=0, adapter_state_sha256='a' * 64)


def receipt():
    return dict(control_policy=frozen.POLICY, optimizer_steps=0, total_optimizer_steps=0,
        cumulative_optimizer_steps=0, weight_updates_enabled=False,
        no_update_reason='R232_frozen_sibling_updates_disabled', presentations=[],
        child_token_exposures=0, anchor_token_exposures=0, frozen_base_verified=True,
        before_adapter_sha256='a' * 64, after_adapter_sha256='a' * 64,
        before_optimizer_state_sha256='b' * 64, after_optimizer_state_sha256='b' * 64)


class FrozenTests(unittest.TestCase):
    def test_zero_receipt_accepts_initial_zero(self):
        frozen.validate_frozen(receipt(), previous())

    def test_forged_updates_adapter_or_exposures_rejected(self):
        for key, value in dict(optimizer_steps=1, total_optimizer_steps=1,
                after_adapter_sha256='c' * 64, after_optimizer_state_sha256='c' * 64,
                child_token_exposures=1, weight_updates_enabled=True, control_policy='other').items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                frozen.validate_frozen(dict(receipt(), **{key: value}), previous())

    def test_optimizer_step_is_disabled(self):
        with self.assertRaisesRegex(ValueError, 'optimizer_step_forbidden'):
            frozen.forbid_step()

    def test_first_and_second_sleep_roundtrip_real_journal(self):
        frozen.INITIAL = previous()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stream'
            stream = frozen.FrozenStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
                context_limit=4096, segment_tokens=128, segments_per_sleep=2,
                deadline_unix=1000, model_state_sha256='f' * 64)
            with frozen.FrozenJournal(path, create=True) as journal:
                journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
                for cycle in (1, 2):
                    for unused in range(2):
                        stream.step(lambda *args, **kwargs: dict(raw='Actual synthetic calculation: 2 + 2 = 4.',
                            token_ids=[10, 2], terminal=True, truncated=False),
                            lambda messages: sum(len(item['content'].split()) + 4 for item in messages),
                            journal.record, now=lambda: 100)
                    pending = stream.checkpoint()
                    pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in stream.pending_rows()])
                    pending['sha256'] = digest(pending['state'])
                    journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
                    complete = dict(receipt(), status='COMPLETE', cycle=cycle,
                        new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()],
                        checkpoint_sha256=dict(adapter='d' * 64, optimizer='e' * 64, rng='e' * 64))
                    complete['checkpoint'] = dict(previous(), checkpoint_sha256=complete['checkpoint_sha256'])
                    stream.commit_sleep(complete, journal.record)
                    self.assertEqual(stream.sleep_frontier, len(stream.rows))
                    self.assertEqual(len(stream.sleep_receipts), cycle)
                expected = deepcopy(journal.latest_checkpoint())
            with frozen.FrozenJournal(path) as journal:
                self.assertEqual(journal.latest_checkpoint(), expected)


if __name__ == '__main__':
    unittest.main()
