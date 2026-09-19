# Mailbox setup receipt — September 19, 2026

## Relay-path repair verified at 23:45:11 UTC / 16:45:11 PDT

Rohin's other-machine reply was committed at
`mailbox/to_vm/20260919T232722Z-codex-relay-astra.md`, whereas the original watcher
only checked `MAILBOX/messages/`. The successful polls therefore missed it.
This was a routing omission, not evidence that the reply had been read.

Non-material repair: watch the canonical directory **and** `mailbox/to_vm/`
and `mailbox/from_vm/`, retaining route-specific cache paths to avoid filename
collisions. **12 tests pass**, including both relay directions, duplicate
filenames, and inert `interrupt: true` frontmatter. No runtime, curriculum,
training eligibility, or benchmark changed.

Only the mailbox poller was restarted. New process `4157335` in tmux session
`astra-mailbox` downloaded the incoming relay on its first poll at
**23:45:11.046192 UTC**, remote commit
`b41c6c2c02050c31ef7cfbaf9bcacfa322d178a2`: **3 messages, 14,310 bytes**.
Incoming relay SHA-256:
`05b92addde673b42f1e2073b406ee525e4b6bea57abaf03802861cba1a2869e7`.

Astra also read the message and wrote a separate
[acknowledgment and substantive reply](../mailbox/from_vm/20260919T234512Z-astra-reply-persistence.md).
The old watcher PID and earlier counts below are historical receipts.
The watcher still cannot wake an inactive assistant or survive a reboot.

## Published-message delivery verified at 23:09:17 UTC / 16:09:17 PDT

The same tmux process (`4056363`) completed its next scheduled poll and detected
**both newly published messages**, totaling **10,495 bytes**, at remote commit
`e135b326d6ed8a14ebbada2810b7d4d911c0a89e`. Both have local notification entries
marked `downloaded_not_acknowledged`; there were no ignored messages.

- Previous-reply message SHA-256:
  `b708df924d728c993d136603d3ede9f676f658f82e3e37e1d4bc691372943c32`.
- Reading-room handoff SHA-256:
  `68f5aa26c2d235e641bb26fbcee9b703690b6556f14005d9b232f6a657043f08`.

Publication checked **35 relative document links**, verified the submitted
abstract blob was unchanged, and preserved the ordinary local HEAD and index.
The focused **10-test suite passed again** after publication. No scientific
outcome was inferred from these infrastructure tests.

## Verified at 23:07:19 UTC / 16:07:19 PDT

- `tools/mailbox_watch.py` is running in tmux session `astra-mailbox`, PID
  `4056363`; the process was verified in a separate command after launch.
- Poll interval: **120 seconds**, reading `origin/main` only.
- First successful poll from this process: **23:07:15.590160 UTC** against
  `053fdd728dc71efbbe34b4747cb55851cf45e96b`.
- At that poll, the new mailbox had not yet been pushed: **0 remote messages**.
  This is a successful connection receipt, not a receipt of the new messages.
- Local receipt: `MAILBOX/.local/status.json`. Local notification queue:
  `MAILBOX/.local/notifications.json`. Both are ignored by Git.
- **10 CPU tests passed** with
  `python3 -m unittest discover -s tests -p 'test_mailbox_watch.py' -v`.
  `pytest` was unavailable in the system interpreter; no dependency was installed.

## Scope and limitations

The tests cover additions, duplicate polling, revisions/deletions, preservation
of the ordinary checkout/index, ignored symlinks/executables/nested paths,
size limits, invalid UTF-8, retained cache after a network failure, environment
index isolation, an empty mailbox, and an offline reader with no remote.
Message text containing a command remains text and is never executed.

The poller uses a separate bare Git cache and an offline reader, borrowing
existing objects instead of copying the repository. New Git fetches filter
large blobs; cached message text is bounded separately. Initial local footprint
was approximately **227 KiB**, not another checkpoint or full checkout.

**User-service installation was blocked by host policy.** The provided
`astra-mailbox.service` is a template, not an installed/enabled service.
Two short-lived background launch attempts did not survive their tool sessions;
the tmux launch above is the verified running one. It is **not reboot-persistent**.

The watcher does not wake a stopped assistant, acknowledge on anyone's behalf,
run experiments, execute instructions, alter parent prompts, or grant authority
based on a `From:` label. A human/active assistant must read and reply.
No scientific run, live-life change, or training-row filtering occurred.

If the VM or tmux server restarts, this process needs restarting. Check the
timestamp and PID in the local status file before assuming it is still active.
