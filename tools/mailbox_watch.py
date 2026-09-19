"""Fetch bounded repository messages without executing them or touching a checkout."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


MAX_MESSAGE_BYTES = 128 * 1024
MAX_MESSAGES = 500
MAX_TOTAL_BYTES = 4 * 1024 * 1024
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\.md\Z")
MESSAGE_PREFIXES = ("MAILBOX/messages/", "mailbox/to_vm/", "mailbox/from_vm/")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def write_json(path, data):
    atomic_write(path, (json.dumps(data, indent=2, sort_keys=True) + "\n").encode())


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def run_git(arguments, cwd=None, git_dir=None):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update(GIT_TERMINAL_PROMPT="0", GIT_SSH_COMMAND="ssh -oBatchMode=yes")
    command = ["git", "-c", "core.hooksPath=/dev/null"]
    if git_dir is not None:
        command.append("--git-dir=" + str(git_dir))
    result = subprocess.run(command + list(arguments), cwd=cwd, env=environment,
                            capture_output=True, timeout=90, check=True)
    return result.stdout


class MailboxWatcher:
    def __init__(self, repo, state):
        self.repo = Path(repo).resolve()
        self.state = Path(state).resolve()
        self.remote_dir = self.state / "remote.git"
        self.reader_dir = self.state / "reader.git"

    def prepare(self):
        objects = run_git(["rev-parse", "--git-path", "objects"], cwd=self.repo)
        source_objects = (self.repo / objects.decode().strip()).resolve()
        remote = run_git(["remote", "get-url", "origin"], cwd=self.repo).decode().strip()
        self.state.mkdir(parents=True, exist_ok=True)
        for directory, alternate in ((self.remote_dir, source_objects),
                                     (self.reader_dir, self.remote_dir / "objects")):
            if not directory.exists():
                run_git(["init", "--bare", str(directory)])
            atomic_write(directory / "objects/info/alternates", (str(alternate) + "\n").encode())
        run_git(["config", "remote.origin.url", remote], git_dir=self.remote_dir)
        run_git(["config", "remote.origin.promisor", "true"], git_dir=self.remote_dir)
        run_git(["config", "remote.origin.partialclonefilter",
                 "blob:limit=" + str(MAX_MESSAGE_BYTES + 1)], git_dir=self.remote_dir)
        if run_git(["remote"], git_dir=self.reader_dir).strip():
            raise ValueError("offline_reader_must_have_no_remotes")

    def fetch(self):
        run_git(["fetch", "--no-tags", "--depth=1", "--no-write-fetch-head",
                 "--filter=blob:limit=" + str(MAX_MESSAGE_BYTES + 1), "origin",
                 "+refs/heads/main:refs/heads/observed"], git_dir=self.remote_dir)
        return run_git(["rev-parse", "refs/heads/observed"], git_dir=self.remote_dir).decode().strip()

    def read_messages(self, commit):
        listing = run_git(["ls-tree", "-r", "-z", commit, "--", *MESSAGE_PREFIXES],
                          git_dir=self.reader_dir)
        entries = [entry for entry in listing.split(b"\0") if entry]
        if len(entries) > MAX_MESSAGES:
            raise ValueError("mailbox_entry_limit_exceeded")
        messages = {}
        ignored = []
        total_bytes = 0
        for entry in entries:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, blob = metadata.decode().split()
            path = raw_path.decode("utf-8", errors="replace")
            prefix = next((item for item in MESSAGE_PREFIXES if path.startswith(item)), None)
            name = path.removeprefix(prefix) if prefix is not None else ""
            if mode != "100644" or kind != "blob" or not NAME_PATTERN.fullmatch(name):
                ignored.append({"path": path, "reason": "not_a_plain_message_file"})
                continue
            try:
                size = int(run_git(["cat-file", "-s", blob], git_dir=self.reader_dir))
            except subprocess.CalledProcessError:
                ignored.append({"path": path, "reason": "not_in_bounded_offline_cache"})
                continue
            if size > MAX_MESSAGE_BYTES:
                ignored.append({"path": path, "reason": "message_too_large"})
                continue
            total_bytes += size
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError("mailbox_total_byte_limit_exceeded")
            body = run_git(["cat-file", "blob", blob], git_dir=self.reader_dir)
            try:
                body.decode("utf-8")
            except UnicodeDecodeError:
                ignored.append({"path": path, "reason": "not_utf8"})
                continue
            messages[path] = {"blob": blob, "sha256": hashlib.sha256(body).hexdigest(),
                              "body": body, "bytes": len(body)}
        return messages, ignored

    def poll(self):
        self.prepare()
        commit = self.fetch()
        messages, ignored = self.read_messages(commit)
        previous = load_json(self.state / "seen.json", {})
        notifications = load_json(self.state / "notifications.json", [])
        checked_at = utc_now()
        changes = []
        current = {}
        for path, message in messages.items():
            current[path] = message["blob"]
            cache_name = path.removeprefix("MAILBOX/messages/")
            cache_path = self.state / "messages" / cache_name
            atomic_write(cache_path, message["body"])
            if previous.get(path) != message["blob"]:
                changes.append({"kind": "added" if path not in previous else "edited",
                                "path": path, "commit": commit, "checked_at": checked_at,
                                "blob": message["blob"], "sha256": message["sha256"],
                                "cached_path": str(cache_path.relative_to(self.state)),
                                "status": "downloaded_not_acknowledged"})
        ignored_paths = {entry["path"] for entry in ignored}
        for path, blob in previous.items():
            if path in ignored_paths:
                current[path] = blob
            elif path not in current:
                changes.append({"kind": "deleted", "path": path, "commit": commit,
                                "checked_at": checked_at, "previous_blob": blob})
        write_json(self.state / "notifications.json", (notifications + changes)[-200:])
        write_json(self.state / "seen.json", current)
        status = {"status": "ok", "checked_at": checked_at, "pid": os.getpid(),
                  "remote_commit": commit, "messages": len(messages), "changes": len(changes),
                  "ignored": ignored, "message_bytes": sum(item["bytes"] for item in messages.values()),
                  "executes_messages": False, "wakes_assistant": False,
                  "touches_worktree_or_index": False}
        write_json(self.state / "status.json", status)
        return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--interval", type=int, default=120)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.interval < 10:
        parser.error("interval must be at least 10 seconds")
    state = args.state_dir or args.repo / "MAILBOX/.local"
    state.mkdir(parents=True, exist_ok=True)
    watcher = MailboxWatcher(args.repo, state)
    with (state / "watch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "mailbox watcher already running for this state directory\n")
        while True:
            try:
                status = watcher.poll()
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                status = {"status": "error", "checked_at": utc_now(), "pid": os.getpid(),
                          "error_type": type(error).__name__,
                          "detail": "Poll failed; previous cache retained. Check Git access and limits."}
                write_json(state / "status.json", status)
            print(json.dumps(status), flush=True)
            if args.once:
                return 0 if status["status"] == "ok" else 1
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
