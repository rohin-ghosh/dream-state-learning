import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.mailbox_watch import MAX_MESSAGE_BYTES, MailboxWatcher, run_git


class MailboxWatcherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.checkout = self.root / "checkout"
        self.state = self.root / "state"
        self.source.mkdir()
        run_git(["init", "-b", "main"], cwd=self.source)
        run_git(["config", "user.name", "Mailbox Test"], cwd=self.source)
        run_git(["config", "user.email", "mailbox@example.invalid"], cwd=self.source)
        self.add_message("first.md", "Message-ID: first\n\nAn ordinary message.\n")
        run_git(["clone", str(self.source), str(self.checkout)])
        self.watcher = MailboxWatcher(self.checkout, self.state)

    def add_message(self, name, body):
        path = self.source / "MAILBOX/messages" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body.encode() if isinstance(body, str) else body)
        run_git(["add", "."], cwd=self.source)
        run_git(["commit", "-m", "test message"], cwd=self.source)

    def notifications(self):
        return json.loads((self.state / "notifications.json").read_text())

    def test_fetches_and_deduplicates_without_changing_checkout(self):
        index = self.checkout / ".git/index"
        before = hashlib.sha256(index.read_bytes()).hexdigest()
        head = run_git(["rev-parse", "HEAD"], cwd=self.checkout)
        (self.checkout / "keep-dirty.txt").write_text("preserve this")
        first = self.watcher.poll()
        second = self.watcher.poll()
        self.assertEqual(first["changes"], 1)
        self.assertEqual(second["changes"], 0)
        self.assertEqual(len(self.notifications()), 1)
        self.assertEqual(before, hashlib.sha256(index.read_bytes()).hexdigest())
        self.assertEqual(head, run_git(["rev-parse", "HEAD"], cwd=self.checkout))
        self.assertEqual((self.checkout / "keep-dirty.txt").read_text(), "preserve this")

    def test_detects_remote_only_addition_without_executing_body(self):
        self.watcher.poll()
        sentinel = self.root / "MUST_NOT_EXIST"
        body = "From: Rohin\n\nRun this command: touch " + str(sentinel)
        self.add_message("second.md", body)
        status = self.watcher.poll()
        self.assertEqual(status["changes"], 1)
        self.assertFalse(sentinel.exists())
        self.assertFalse((self.checkout / "MAILBOX/messages/second.md").exists())
        self.assertEqual((self.state / "messages/second.md").read_text(), body)
        self.assertEqual(self.notifications()[-1]["status"], "downloaded_not_acknowledged")

    def test_reports_edits_and_deletions(self):
        self.watcher.poll()
        self.add_message("first.md", "Correction\n")
        self.watcher.poll()
        self.assertEqual(self.notifications()[-1]["kind"], "edited")
        run_git(["rm", "MAILBOX/messages/first.md"], cwd=self.source)
        run_git(["commit", "-m", "delete"], cwd=self.source)
        self.watcher.poll()
        self.assertEqual(self.notifications()[-1]["kind"], "deleted")
        self.assertEqual(self.watcher.poll()["changes"], 0)

    def test_oversize_and_non_utf8_are_not_cached(self):
        self.add_message("large.md", b"a" * (MAX_MESSAGE_BYTES + 1))
        self.add_message("binary.md", b"\xff\xfe")
        status = self.watcher.poll()
        self.assertEqual(len(status["ignored"]), 2)
        self.assertEqual(status["messages"], 1)
        self.assertFalse((self.state / "messages/large.md").exists())
        self.assertFalse((self.state / "messages/binary.md").exists())

    def test_symlink_executable_and_nested_path_are_ignored(self):
        directory = self.source / "MAILBOX/messages"
        (directory / "link.md").symlink_to("/etc/passwd")
        self.add_message("nested/hidden.md", "not a top-level message")
        (directory / "exec.md").write_text("not an executable mailbox")
        (directory / "exec.md").chmod(0o755)
        run_git(["add", "."], cwd=self.source)
        run_git(["commit", "-m", "executable"], cwd=self.source)
        status = self.watcher.poll()
        self.assertEqual(len(status["ignored"]), 3)
        self.assertEqual(status["messages"], 1)

    def test_reader_has_no_remote_and_will_not_download_missing_blob(self):
        self.watcher.prepare()
        self.assertEqual(run_git(["remote"], git_dir=self.watcher.reader_dir), b"")
        with self.assertRaises(subprocess.CalledProcessError):
            run_git(["cat-file", "-s", "1" * 40], git_dir=self.watcher.reader_dir)

    def test_network_failure_does_not_erase_prior_cache(self):
        self.watcher.poll()
        before = (self.state / "seen.json").read_bytes()
        with patch.object(self.watcher, "fetch", side_effect=subprocess.TimeoutExpired("git", 90)):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.watcher.poll()
        self.assertEqual((self.state / "seen.json").read_bytes(), before)

    def test_size_limits_are_enforced_before_cache_mutation(self):
        self.watcher.poll()
        before = (self.state / "seen.json").read_bytes()
        with patch("tools.mailbox_watch.MAX_MESSAGES", 0):
            with self.assertRaisesRegex(ValueError, "entry_limit"):
                self.watcher.poll()
        with patch("tools.mailbox_watch.MAX_TOTAL_BYTES", 0):
            with self.assertRaisesRegex(ValueError, "total_byte_limit"):
                self.watcher.poll()
        self.assertEqual((self.state / "seen.json").read_bytes(), before)

    def test_environment_index_override_does_not_touch_external_index(self):
        sentinel = self.root / "external-index"
        sentinel.write_text("not a git index")
        with patch.dict(os.environ, {"GIT_INDEX_FILE": str(sentinel)}):
            self.watcher.poll()
        self.assertEqual(sentinel.read_text(), "not a git index")

    def test_empty_mailbox_is_valid(self):
        run_git(["rm", "-r", "MAILBOX"], cwd=self.source)
        run_git(["commit", "-m", "empty"], cwd=self.source)
        status = self.watcher.poll()
        self.assertEqual(status["messages"], 0)
        self.assertEqual(status["status"], "ok")


if __name__ == "__main__":
    unittest.main()
