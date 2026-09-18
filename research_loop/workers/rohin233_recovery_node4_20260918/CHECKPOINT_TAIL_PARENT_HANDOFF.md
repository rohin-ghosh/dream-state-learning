# Prepared C2 CPU rebind — not activated

Owner split: Main owns native receiving preflight, switch and dispatch. These
helpers only prepare/observe the new incarnation and reuse the original CPU
parent after an explicit handoff. Existing waiter3590563/start186658124 and
parent471781/start183179491 have not been signaled or replaced.

New control: `/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/control`.
Same C2 root/journal, exact COMPLETE11502 plus original11503 retained. Bound:
September20,2026 18:00UTC (`1789927200`). New source identity is separate from
the unchanged original parent-view source and its original guard/source pins.

## After Main confirms dispatch

1. Main supplies the actual native PID/start ticks and admitted new guard hash.
   Copy these read-only helper dependencies outside the native source closure:
   `checkpoint_tail_parent_binding.py`, `deadline_resume.py`, `receipt_window.py`.
2. On node5, observe once; retry only this read if pending:

```sh
python3 -B OPERATOR/checkpoint_tail_parent_binding.py \
  --pid ACTUAL_PID --start-ticks ACTUAL_START --guard-sha256 ADMITTED_GUARD_SHA
```

   Output is `PENDING_ACTUAL_LOAD` until both actual matching WALL and LOADED
   exist. It verifies same optimizer7756, saved state, process/source/control
   and original view-source pins. It writes no journal/cache and signals nothing.
   Preserve a `LOADED` result verbatim as a new immutable receipt on the node and
   locally; do not substitute a dispatch record. Hash the exact receipt bytes.
3. After dispatch is confirmed, the owner must retire only the exact old CPU
   waiter and drain the exact original CPU parent using the existing pidfd/idle
   handoff. No helper here performs termination. If either remains, new parent
   activation fails closed on the existing controller/parent locks. Do not start
   another observer-controller or new parent alongside them.
4. Prepare local receipt files after actual LOAD and after the old parent ledger
   is settled (use fresh receipt and output directories):

```sh
python3 -B checkpoint_tail_parent_prepare.py \
  --binding LOCAL_ACTUAL_BINDING.json --remote-binding-path REMOTE_ACTUAL_BINDING.json \
  --remote-operator OPERATOR --receipt-directory NEW_RECEIPTS --parent-output NEW_OUTPUT
```

   This changes only deadline, predecessor/cursor and explicit native-binding
   references in the original parent config. It preserves all old ledger files,
   reserves every previous SOURCE cursor, and pins local/remote helper hashes.
   It does not start a process. It prints the immutable manifest path/hash.
5. Only after the authorized CPU handoff, activate explicitly:

```sh
python3 -B checkpoint_tail_parent_continue.py \
  --manifest NEW_RECEIPTS/CHECKPOINT_TAIL_PARENT_MANIFEST.json \
  --manifest-sha256 PRINTED_MANIFEST_SHA
```

   Keep the existing provider environment; do not expose credentials. The same
   parent writer lock and census apply. Every remote read/publication verifies
   the new actual native binding first; only snapshot reads retry. Publication
   failures are not blindly retried. No native signals are implemented.

## Evidence still required

Prepared scripts/tests are not live parenting. After activation, preserve the
actual STARTED identity, parent publication ID/text hash, native INBOX receipt,
exact REQUEST masked rendering, and linked child ACT. Do not equate INBOX
registration or process liveness with rendered exposure. No new behavioral
instruction, policy or exclusion is introduced by this handoff.
