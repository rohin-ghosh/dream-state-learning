# September 19, 2026 — reserved-preflight and epoch3 handoff

[Builder] 2026-09-19 02:10 UTC. Non-material worker-local continuity repair.
Review-ready executable artifacts, not live admission or deployment readiness.
No native/parent signals, reservations, handoffs, remote actions, GPU dispatch,
privileged/service management, commits or pushes. Root history and staged
epoch1/epoch2 remain untouched. Main alone owns live route review/activation.

## Selected artifacts

- `operator_bundle_v2/MANIFEST.json`: exact standalone operator import closure;
  SHA256 `27046ff9e52afe2cd588e1c8698da009fed704e03a5edb4dfd38b67c940435dc`.
  Isolated `python3 -I -B` hash/import smoke PASS, without constructing or
  invoking a coordinator. Keep this operator tree outside immutable GPU source.
- `RESERVED_PREFLIGHT_HANDOFF.md`: concrete policy, approval digest, required
  static receipt fields, owner contract, CPU commands and outstanding live gates.
- `RESERVED_CPU_RECEIPT_v1.json`: exact tested operator/test hashes and logs;
  SHA256 `0cfb504a75ff9297bbf5d78cf273f7fde42a7e802c6f51d4f75527348e896bce`.
- `prepared_epoch3_v1/SUMMARY.json`: separately sealed 209-file closures;
  SHA256 `a87ed9e60bb88d7b18156453a5f907de34af351eb8399222eb94e6d67c5f0b2f`.
  See `EPOCH3_HANDOFF.md` for exact destination declarations, one-file history
  delta, unchanged deadline, test provenance and the earlier port-receipt nuance.

## Exact passing CPU results

- Pair worker suite: 63 tests, 1.296 seconds, exit 0.
- Unmodified boundary suite: 83 tests, 0.213 seconds, exit 0.
- Prepared epoch3 source suites: 14 tests per arm, both exit 0, plus old/new
  Unicode/all-prefix/retention/compaction/checkpoint/restore/deepcopy/tamper parity.
- Operator bundle: all 13 file hashes matched; isolated imports PASS.

Safe repeatable suite command (no activation):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_pair_retention_receiver_20260919 \
  -p 'test_*.py' -q
```

## Changed files in this resumed implementation

Added operator/preparer/test code:

- `reserved_preflight.py`
- `test_reserved_preflight.py`
- `prepare_epoch3.py`
- `test_prepare_epoch3.py`
- `validate_local.py`

Modified existing worker code:

- `integration.py`: optional strategy, distinct execution approval; old default.
- `receiver.py`: cheap candidate-family check, shared helper budget, timeout
  evidence, closed inherited descriptors; same seven-hook interface.
- `parent_dependency_bridge.py`: shared-budget timeout clipping, closed inherited
  descriptors; same nonce/original-ledger/fence verifier and post-LOADED join.
- `package_operator.py`: include optional strategy and bind exact passing test
  receipt/source bytes before packaging.

Added documentation: `RESERVED_PREFLIGHT_HANDOFF.md`, `EPOCH3_HANDOFF.md`, this file.
Updated documentation: `README.md`, `DEPENDENCY_DISPATCH_INTEGRATION.md`, `TO_KUHN.md`.
Generated artifacts: `operator_bundle_v2/`, `prepared_epoch3_v1/`,
`RESERVED_CPU_RECEIPT_v1.json`. Older bundle/prepared directories are preserved.
No shared boundary or native/reader/history implementation outside this worker
is modified. The new epoch3 history bytes come only from main's approved port.

## What main still must establish

The opt-in path now captures before expensive candidate proof, making the
simulated moving-native case reachable. It retains the existing <=30-second
guardian, all saved-state/durable/identity/owner checks and original dispatch.
Expiry/failure is terminal with a persistent review gate; an early boundary race
resumes the same handle and retries only a new COMPLETE. CPU tests do not prove
the actual live window or total latency.

Still required: selected/delivered epoch3 and actual-source receipts; real total
reserved timing including all owner/source/guard/fsync/audit work; original
confinement/management admission availability; actual Kuhn fence with authenticated
original-host owner RPC; fresh exact native binding and consumed-wall record/intent;
explicit new strategy approval. No positive static readiness receipt was invented.
After real LOADED/source adoption, Kuhn must separately bind the exact new native
without resetting ledgers or duplicating messages. No automatic PID adoption.
