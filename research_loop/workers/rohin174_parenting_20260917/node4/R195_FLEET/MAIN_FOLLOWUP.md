# Node4 receiving follow-up — 2026-09-18 02:15 UTC

Operator preparation proceeds without deployment; Main has not frozen READY.

## Remaining R188 alias integration finding

The new explicit CPU-root policy is present, but the three relocated lives
still pass logical symlink roots: `StreamJournal.__init__` uses `.absolute()`,
and R184 `_cpu` passes `str(self.journal.root.parent)` unchanged. The new
`cpu_once` branch requires `root.resolve() == root`. Therefore these three
same-life calls reject with `canonical_existing_TRAIN_life_root` before a CPU
attempt. This follows directly from the current source and the inspected
logical/backing root bindings; no child tool was executed.

Please have Main bind the existing logical alias to its actual canonical
backing root at the CPU transport call while retaining journal-id/source/gate
checks. Do not rewrite the life's logical plan, checkpoint paths, journal,
history, or inboxes. This operator will not patch shared runtime itself.

Other reported changes (remote explicit policy fields, host policy opt-in,
NFKC kernel bridge) are being included in closure preparation, not assumed live.
