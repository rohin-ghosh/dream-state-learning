import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from gpu import orch_r139_route_astra_handoff as original
from gpu.orch_r139_route_delayed_exit import settle


class DelayedExitTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.stage = Path(self.directory.name)
        self.proc = self.stage / 'proc'
        self.proc.mkdir()
        self.state = self.stage / 'state.json'
        self.state.write_text('{}')
        self.boundary = dict(root=str(self.stage), logical_life_reset=False,
            preserved={str(self.state): original.sha(self.state)}, checkpoint=original.ref(self.state),
            optimizer_rng=original.ref(self.state), next_cycle=56, sleeps=55)
        (self.stage / 'BOUNDARY.json').write_text(json.dumps(self.boundary))
        self.handoff = SimpleNamespace(**{name: getattr(original, name)
            for name in ('require', 'read', 'sha', 'bound', 'write', 'ref')})
        self.handoff.ROOT = self.stage
        self.handoff.authorize = Mock(return_value=(dict(actor=dict(pid=123)), {}))

    def test_dead_actor_preserved_state_is_released_without_signals(self):
        result = settle(self.handoff, self.stage, self.proc)
        self.assertEqual(result['next_cycle'], 56)
        self.assertEqual(original.read(self.stage / 'RELEASED.json')['new_signals'], 0)

    def test_live_or_reused_pid_rejected(self):
        (self.proc / '123').mkdir()
        with self.assertRaisesRegex(ValueError, 'still_present'):
            settle(self.handoff, self.stage, self.proc)

    def test_changed_state_rejected(self):
        self.state.write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, 'boundary_data_changed'):
            settle(self.handoff, self.stage, self.proc)

    def test_existing_launch_rejected(self):
        (self.stage / 'LAUNCH.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'already_launched'):
            settle(self.handoff, self.stage, self.proc)

    def test_existing_release_not_overwritten(self):
        (self.stage / 'RELEASED.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'already_recorded'):
            settle(self.handoff, self.stage, self.proc)


if __name__ == '__main__':
    unittest.main()
