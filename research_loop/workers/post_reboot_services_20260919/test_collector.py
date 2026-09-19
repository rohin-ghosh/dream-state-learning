import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collector


class CollectorTests(unittest.TestCase):
    def test_remote_cut_changes_only_clock_selection(self):
        source = (collector.LEGACY / "judge_epoch_report.py").read_text()
        restored = collector.remote_reader().replace(
            "    cut = min(time.time(), float(specification['cut_unix']))\n",
            "    cut = time.time()\n")
        self.assertEqual(source, restored)

    def test_sources_keep_player_epochs_and_individual_leases(self):
        sources = collector.specifications(1789772400)
        self.assertEqual(len(sources), 4)
        self.assertEqual(sum(len(row["players"]) for row in sources), 8)
        self.assertTrue(all(row["cut_unix"] < 1789772400 for row in sources))
        self.assertTrue(all(row["cutoff_unix"] <= collector.MAX_UNTIL for row in sources))

    def test_expired_source_is_not_queried(self):
        with patch.object(collector.subprocess, "run") as run:
            result = collector.fetch(dict(role="BASE", cutoff_unix=0), "unused")
        run.assert_not_called()
        self.assertEqual(result["status"], "SOURCE_LEASE_BOUND_REACHED_NOT_QUERIED")

    def test_existing_receipt_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "cut.json"
            collector.save(receipt, {"original": True}, exclusive=True)
            with self.assertRaises(FileExistsError):
                collector.save(receipt, {"original": False}, exclusive=True)
            self.assertEqual(json.loads(receipt.read_text()), {"original": True})

    def test_legacy_lock_prevents_second_collector(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "collector.lock"
            with lock.open("a") as owner:
                fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with patch.object(collector, "LOCK", lock), patch("sys.argv", ["collector.py"]):
                    self.assertEqual(collector.main(), 75)

    def test_lease_extension_is_rejected(self):
        with patch("sys.argv", ["collector.py", "--until-unix", str(collector.MAX_UNTIL + 1)]):
            with self.assertRaises(ValueError):
                collector.main()

    def test_reboot_catches_later_missing_hours_without_recollecting_completed_cuts(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(collector, "HERE", Path(directory)):
            completed = Path(directory) / "cuts" / "20260918T230000Z.json"
            collector.save(completed, {"complete": True}, exclusive=True)
            self.assertEqual(collector.pending_backfill(1789783200), [1789776000, 1789779600, 1789783200])

    def test_failed_live_read_retries_without_waiting_for_next_hour(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(collector, "HERE", root), patch.object(collector, "LOCK", root / "lock"), patch.object(collector, "REPO", root), patch.object(collector, "pending_backfill", return_value=[]), patch.object(collector, "identity", return_value={}), patch.object(collector, "collect", return_value=False) as collect, patch.object(collector.time, "sleep", side_effect=InterruptedError), patch("sys.argv", ["collector.py"]):
                with self.assertRaises(InterruptedError):
                    collector.main()
                heartbeat = json.loads((root / "COLLECTOR_HEARTBEAT.json").read_text())
            collect.assert_called_once()
            self.assertLessEqual(heartbeat["next_run_unix"] - collector.time.time(), 60)


if __name__ == "__main__":
    unittest.main()
