import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r118_claude_terminal_rebind as rebind


class TerminalRebindTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.ledger = self.root / 'parent_claude'
        self.ledger.mkdir()

    def test_claims_require_published_and_preserve_bytes(self):
        claim = self.ledger / 'old.claim'
        claim.mkdir()
        (claim / 'CLAIM.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'unpublished_claim'):
            rebind.claim_inventory(self.root)
        (claim / 'PUBLISHED.json').write_text('{}')
        before = rebind.claim_inventory(self.root)
        self.assertEqual(len(before), 2)
        self.assertEqual(rebind.claim_inventory(self.root), before)

    def test_bound_hash_rejects_changed_metadata(self):
        path = self.root / 'RUNTIME.json'
        path.write_text('{}')
        reference = rebind.reference(path)
        self.assertEqual(rebind.bound(reference), {})
        path.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, 'exact_bound_file'):
            rebind.bound(reference)

    def test_ready_not_written_until_actual_lock_success(self):
        base = SimpleNamespace(NodeLocalStore=type('Store', (), {'shell':Mock(return_value=SimpleNamespace(returncode=1))}))
        binding = dict(root=str(self.root), prior_claim_files={}, ready_path=str(self.root / 'READY.json'), terminal_path=str(self.root / 'NEW.json'))
        config = {'unchanged':True}
        rebind.install(base, binding, config, {})
        base.NodeLocalStore().shell('mkdir '+str(self.ledger / 'RUNNER.lock'), check=False)
        self.assertFalse(Path(binding['ready_path']).exists())
        self.assertEqual(base.terminal_path(config), Path(binding['terminal_path']))
        with self.assertRaisesRegex(ValueError, 'config_unchanged'):
            base.terminal_path({'changed':True})

    def test_successful_lock_publishes_once_and_failure_releases_only_own_lock(self):
        shell = Mock(return_value=SimpleNamespace(returncode=0))
        base = SimpleNamespace(NodeLocalStore=type('Store', (), {'shell':shell}))
        binding = dict(root=str(self.root), prior_claim_files={}, ready_path=str(self.root / 'READY.json'), terminal_path=str(self.root / 'NEW.json'))
        rebind.install(base, binding, {}, {})
        with patch.object(rebind, 'ready_record', return_value={'actual_single_lane_lock_acquired':True}):
            store = base.NodeLocalStore()
            store.shell('mkdir '+str(self.ledger / 'RUNNER.lock'))
            self.assertTrue(json.loads(Path(binding['ready_path']).read_text())['actual_single_lane_lock_acquired'])
            with self.assertRaises(FileExistsError):
                store.shell('mkdir '+str(self.ledger / 'RUNNER.lock'))
        self.assertEqual(shell.call_args.args[0], 'rmdir '+str(self.ledger / 'RUNNER.lock'))

    def test_terminal_map_is_family_specific(self):
        self.assertEqual(rebind.TERMINALS['F1'], 'R118_PARALLEL_TERMINAL.json')
        self.assertEqual(rebind.TERMINALS['F2'], 'GUARD_TERMINAL.json')
        self.assertEqual(rebind.TERMINALS['F3'], 'GUARD_TERMINAL.json')
        self.assertEqual(rebind.TERMINALS['F4'], 'R118_GRID_PARALLEL_TERMINAL.json')


if __name__ == '__main__':
    unittest.main()
