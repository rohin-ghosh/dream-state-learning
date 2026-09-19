# Epoch3 locally sealed; no deployment or native handoff

September 19, 2026 UTC. Selected local artifact: `prepared_epoch3_v1/SUMMARY.json`.
Per-arm receipts: `prepared_epoch3_v1/<life>/epoch3/EPOCH3_SOURCE.json`.
Local source directories: `prepared_epoch3_v1/<life>/epoch3/source`.
Destination declarations, not delivery claims:

```text
/localhome/local-rohing/orch_retention_20260919/curriculum_learner/epoch3/source
/localhome/local-rohing/orch_retention_20260919/curriculum_frozen_sibling/epoch3/source
```

Both closures retain **209 Python files plus the unchanged startup asset**.
Files are 0444, directories 0555. Epoch2/epoch1 are preserved. Exactly one
existing file changes from epoch2; no additional source file is enrolled:

```text
organism_v6/orch_r124_train_history.py
before: ec7ecd7ebf395885606e7b500a47baedd11172a4c46e23b8d05d569dc8fac1d3
after:  8d44b45941228b229340a1546d3bf984965b0f9d2acfab12967c829d48f16315
```

The original full old-native-to-epoch3 per-file delta is in each receipt's
`changed`. Source, retained C2 identity/copy_raw mapping, prompt/row/control
settings, lease and deadline are inherited exactly. The unchanged deadline is
1790791200 (September 30, 2026 18:00 UTC). No active old plan or guard is edited.

`prepare_epoch3.py` verifies both local epoch2 closures against main's actual
staged receipts, applies `frontier_port.port` to those exact bytes, requires the
user-approved final hash, compares it to the real historical byte-equivalence
benchmark receipts, tests and seals a new directory. It does no remote work.

CPU results for EACH actual epoch3 closure: **14 source integration tests PASS**,
plus old/new every-prefix frontier/canonical checkpoint bytes, Unicode/surrogate
escaping, duplicate event, pinned-parent compaction, restore, deepcopy and tamper
parity checks. These are synthetic CPU checks and intentionally carry
`live_handoff_authorization=false`. Actual historical benchmark receipts remain
historical, not live-head/sidecar/current-checkpoint authority.

Provenance nuance: main's `TEST_RECEIPT_1789783461.json` pins the earlier port
helper SHA `551aaf3e…ea79`; the current helper is `a40e2394…a1fb5`.
`INPUTS.json` records the mismatch explicitly rather than claiming the earlier
9+124 tests tested the newer helper. This preparation independently verifies the
resulting full history bytes equal the authorized/real-benchmarked `8d44b459…16315`
hash, then runs the new closure's tests and byte-parity checks. No historical
test receipt is rewritten. Each local CPU result and artifact hash is retained.

Safe local rerun (choose a NEW output directory; never overwrite sealed epochs):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  research_loop/workers/post_recovery_pair_retention_receiver_20260919/prepare_epoch3.py \
  --output research_loop/workers/post_recovery_pair_retention_receiver_20260919/prepared_epoch3_review
```

The node-safe standalone source test remains unchanged:

```text
source_checks.py: 13252 bytes
SHA256: 1f1c96fa6fcdd25ce99e96bc0737440f2b4ff929de49fdef214debf5bea105a9
python3 -I -B /reviewed/operator/source_checks.py --source /declared/epoch3/source
```

It requires only that file, stdlib, a writable temporary directory and the exact
receiving source closure; it does not need a candidate or production checkpoint.
Do not substitute this synthetic test for the actual candidate proof.

Main still owns transport, exact epoch authority, actual-source/guard/admission
receipts, consumed-wall proof and activation. The optional bounded reserved path
is in `RESERVED_PREFLIGHT_HANDOFF.md`; it needs the total cost of ALL reserved
checks, not just the 19s/8s historical reader. Kuhn's actual fence and post-LOADED
rebind remain pending. No source template or local CPU receipt grants admission.
