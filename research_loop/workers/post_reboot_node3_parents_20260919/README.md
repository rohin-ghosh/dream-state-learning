# Node3 caption parent recovery, September 19, 2026

Non-material operational repair under the explicit urgent restoration directive.
Only five existing R233 caption-provider mailboxes are serviced, including the
historically named `unparented_fork`. No learner launches, signals, row filtering,
lease changes, math-parent replacements, or sealed-evaluation access occur.

The existing node-local classroom publisher PID1973233 and fifth-caption publisher
PID1973234 survived the VM reboot. Their locks, exact process identities and all
five current native identities are checked before accepting provider results.
The existing provider wrapper is reused with fresh, authenticated child-visible
ACT/Tool observations. Every first restored message acknowledges the operator gap
at September18 22:50:45UTC and requests one concrete caption/judge-feedback task.

## Main boot supervisor

Run in the real host namespace, inheriting the existing `NVIDIA_API_KEY` securely:

```sh
bash /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919/restart.sh
```

This is a foreground command for the main supervisor, not a native launcher.
`locks/SUPERVISOR.lock` plus one `locks/<exact-life>.lock` per caption fork prevent
duplicate workers using this entrypoint. Never launch the old all-eight provider
alongside it. The existing node publisher locks remain held by their original
processes. Changed native/publisher incarnations require explicit inspection,
not automatic rebinding. The unchanged service ceiling is September24 18UTC.
Keys are environment-only, never written to receipts or forwarded to node3.
Private provider inputs/outputs and runtime lock files are excluded from Git;
all original evidence stays on disk. No commit or push is part of this repair.

`FIRST_TURNS.json` preserves the exact recovery turn per fork across restarts.
`FIRST_RECEIPTS.json` distinguishes accepted provider results, publication, exact
hashed INBOX, masked REQUEST, linked RESPONSE and actual ACT. A delivered/acted-on
parent is **not** evidence of task uptake, correct judging, training, or improvement.
Unknown provider dispatches are retained and not silently repeated. Explicit
HTTP429 rejections are retried after15–60seconds in separate immutable attempt
directories; no failed attempt is erased or relabeled as a successful call.

Refresh receipts independently of provider latency (read-only on node3):

```sh
python3 -B research_loop/workers/post_reboot_node3_parents_20260919/audit_receipts.py
```

Each audit preserves a dated snapshot in `receipt_history/` and the first fully
verified chain per fork in `first_verified/`; `AUDIT_LATEST.json` is the current
cut. `STATUS.json` may lag during an in-flight provider call; its timestamp and
PID must not be treated as an independent current-liveness proof.

```sh
python3 -B -m unittest discover -s research_loop/workers/post_reboot_node3_parents_20260919 -p 'test_*.py' -v
```
