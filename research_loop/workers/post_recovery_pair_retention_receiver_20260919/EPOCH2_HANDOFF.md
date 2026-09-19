# Pair epoch2: local source preparation complete, live admission pending

Selected output: `prepared_epoch2_v2/SUMMARY.json`, September 19, 2026,
01:32:48.453315 UTC. Earlier `prepared_epoch2_v1` is retained evidence only.

## Prepared bytes and unchanged scope

Each arm contains 209 pinned Python files plus exact `context/BIRTH_R231.txt`:
2,833,098 source bytes. All 207 epoch1 Python preimages were located locally and
matched to main's staged SHA256s; filenames alone were never trusted. No live
transport or remote reads/writes were used. The source trees are fsynced and
sealed with file mode 0444 and directory mode 0555. The runner refuses an existing
output path, a path outside this worker, symlink preimages, missing hashes, or
inventory/receipt drift. It never modifies the observed original or epoch1.

For both arms, the exact epoch1-to-epoch2 additions/change are:

| File | Before | After |
| --- | --- | --- |
| `gpu/checkpoint_tail_runtime.py` | absent | `972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e` |
| `gpu/pair_retention_runtime.py` | absent | `bc632040bfaf43968feb82a08c599b2828de9ae8cf8b082d9da407e3a283cd29` |
| `gpu/r232_recovery.py` | `278b1c566a8685a160f4ae2b1e26316d93be9f3721ca5c0eef56ca8a944b5e4a` | `6fe61718ef2ceede3301e558ddc8fddf426ea4974fbf19840b0a09bb0375cc48` |

Each `EPOCH2_SOURCE.json` includes the complete six-entry original-to-epoch2
delta, including the already staged three retention files, full old/epoch1/new
pin sets, per-file local preimage origins, startup proof, and reader/parent
provenance. The reader bytes exactly match the existing C2 reader manifest;
`TO_PASTEUR.md` is the explicit owner-review handoff, not an acknowledgment.

The wrapper additionally preserves original root/manifest/partial-publication
checks and explicit full journal `audit()` semantics. Receiving open uses the
existing hash-prefix scanner. Explicit audit remains a full verification request;
it is never an automatic slow-replay fallback during receiving.

Both plan templates preserve deadline `1790791200` (**September 30, 2026,
18:00 UTC**) and lease end `1790812800`. There is no wall extension. The only
template edits are source/startup path relocation and removal of consumed wall
authorization. That removal still needs the exact original WALL_EXTENDED/intent
proof joined to the selected future COMPLETE; templates are not deployable plans.

## Artifacts main can consume

Under `prepared_epoch2_v2/<life>/epoch2/`, for `curriculum_learner` and
`curriculum_frozen_sibling`:

- `source/`: sealed exact source for main's transport to the corresponding
  `/localhome/local-rohing/orch_retention_20260919/<life>/epoch2/source`.
- `EPOCH2_SOURCE.json`: source allowlist and provenance, not a reservation or
  remote staging-success receipt.
- `cpu/LOCAL_SOURCE_CPU.json`, `SOURCE_TESTS.stdout`, `SOURCE_TESTS.stderr`:
  actual-source synthetic CPU evidence. `live_handoff_authorization=false` is
  deliberately rejected by receiving preflight as operational proof.
- `control/PLAN.template.json`: semantic-preserving template, not a bound PLAN.
- `control/ORIGINAL_GUARD_METADATA.json`: retained observation, not a new guard.
- `control/REQUIRED_LIVE_EVIDENCE.json`: explicit remaining host/candidate gates.
- `control/PARENT_DEPENDENCY_PENDING.json`: exact Kuhn contract snapshot and
  hash, with dependency and rebind receipts absent and rebind disabled.

Top-level `INPUTS.json` pins the helper code, tests, inventories, staged receipts,
reader manifest/log, and Kuhn's contract. `BUILDER_PROVENANCE.md` is the dated
worker-local Builder entry; no global coordination or deployment record changed.

The selected source-receipt file hashes are:

- learner: `20d1c9d393a7d67b8ce1a91c33dd7bffea5e159c80eecd4bcbeab9a2c6e03a92`
- frozen: `2bbec3d96b04122ae8d903915384c8b2b67c335c2fabb8843e6eac4fa1e984dc`

## Exact local commands and results

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_pair_retention_receiver_20260919 -p 'test_*.py' -q
```

25 tests passed in 0.479s (preparer plus receiver, including local-proof rejection).

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s research_loop/workers/post_recovery_retention_boundary_20260918 -p 'test_*.py' -q
```

83 tests passed in 0.252s. No boundary code was changed.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  research_loop/workers/post_recovery_pair_retention_receiver_20260919/prepare_epoch2.py \
  --output research_loop/workers/post_recovery_pair_retention_receiver_20260919/prepared_epoch2_v2
```

Completed successfully. Re-running this exact output path safely refuses; select
a new unused worker-local output directory for any fresh preparation. The runner
executes `source_checks.py --source <local-source>` on each exact closure, with
CUDA hidden and scratch restricted to the worker output. Each closure passes
14 source integration tests: real learner/frozen tail/full-replay parity, frozen
zero-update control, source epoch, pending/raced work rejection, writer locking,
prefix corruption, partial publication, tail bounds, no cold start, unchanged
deadline, missing/mismatched LEARN rejection, retained/arriving INBOX files, and
full explicit audit. No actual GPU/model, checkpoint payload, or live journal is
opened. No signals, reservations, service management, admission or dispatch occur.

## Cost and remaining dependencies

Eight successful synthetic receiving opens hashed 26,247–27,607 raw record bytes
each, with eight prefix records and one/two tail records. Open times (including
synthetic adoption publication) were 0.00829–0.01782 seconds. These are tiny test
measurements, not host throughput predictions. The algorithm hashes the whole
retained prefix and only decodes relevant anchor/INBOX/tail bodies; normal cached
appends do not force a whole replay. Existing correct hash-prefix restore is
accepted here; O(tail) optimization is **not** a prerequisite.

Main owns transport, real bounded read-only checkpoint/tail CPU probes, exact
candidate/consumed-wall receipts, guard/allocation/lease verification, and the
unchanged privileged confinement/admission path. None is fabricated. Kuhn's
contract remains future-only: exact owner delivery fence/zero-inflight/ledger
proof precedes handoff; actual canonical LOADED and source-adoption evidence
precede explicit single-use parent rebind. Current parent runtime must continue
rejecting changed natives. Main must not treat a local test, dispatch PID, or
this preparation receipt as permission to bypass those dependencies.
