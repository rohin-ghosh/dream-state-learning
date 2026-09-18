"""CPU contract tests reject initial, live, or misrouted rehome packets."""

from copy import deepcopy
import unittest

import r188_stage_final_packets as stage


class FinalPacketTests(unittest.TestCase):
    def fixture(self):
        return dict(physical=0, status='PERSISTENT_LOCAL_PACKET_VERIFIED', archive_paths_verified=True,
            gzip_crc_verified=True, archive=str(stage.PACKETS / 'physical0.tar.gz'), packet=dict(
                final_full_stream_included=True, current_learner_continues=False, later_live_updates_not_in_this_packet=False))

    def test_final_packet_accepted_and_targets_exact(self):
        stage.validate(0, self.fixture())
        self.assertEqual(stage.TARGETS, {0: 7, 2: 5, 3: 6})

    def test_initial_live_or_other_life_rejected(self):
        original = self.fixture()
        cases = [dict(original, archive='/initial/physical0.tar.gz'), dict(original, physical=1)]
        for field, value in (('final_full_stream_included', False), ('current_learner_continues', True),
                             ('later_live_updates_not_in_this_packet', True)):
            candidate = deepcopy(original)
            candidate['packet'][field] = value
            cases.append(candidate)
        for candidate in cases:
            with self.assertRaises(ValueError):
                stage.validate(0, candidate)


if __name__ == '__main__':
    unittest.main()
