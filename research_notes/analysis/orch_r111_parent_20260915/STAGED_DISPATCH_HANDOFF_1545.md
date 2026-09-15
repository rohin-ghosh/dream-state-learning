# Route staged dispatch handoff — 2026-09-15 15:45 UTC

Both route owners are actually staged under Main's 15:28–15:50 CPU scope.
All eight actual releases and preserved-file hashes were verified. No standalone
GPU launch or dispatcher retry was issued by this worker. Main owns disposition
of the dispatcher session reported as `e834ff`, including its preserved failure.

## Exact final owner documents

Native directory:
`/localhome/local-rohing/orch_r118_route_parallel_candidate_20260915_v4/stage_1528/owners`.

- F1: `F1/FRESH_OWNER.json`, SHA256 `5235fefe8ffe8435fd34bf21244f13df42073c525b463d6462cbdf17b990b1bd`.
- A1: `A1/FRESH_OWNER.json`, SHA256 `f32dadf9ef93b8299921598243d09c266fc323e3f08d960dab569c514cdcb453`.

Exact command, cwd, environment, source closure and original bounds are in those
documents. They match the campaign's prepared runtime fields. The campaign and
frozen c56 source were not changed. `DISPATCH_HANDOFF_1542.json` preserves the
earlier staging observation; its pending F1 status is superseded by the identity
repair below, not rewritten retroactively.

## Broker identity correction, not source repair

At 15:44:36 UTC, the frozen native `validate_broker_binding` passed after correcting
only F1 broker PID2594802's recorded `identity.ppid` from2594767 to1. All identity
keys matched; the process had been reparented. Its other identity fields were
checked twice and unchanged. No source, validator, provider, PLAN, timing, queue,
charge or allocation was modified. No signals were issued for this repair.

F1 root:
`/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1`.

- Original binding preserved as `R118_PARALLEL_BROKER_BINDING_PRE_REPARENT_1544.json`, SHA256 `e7f5d18affabd424f3f4eda029a222bc4f8213a04f66a741546c424210406376`.
- Current `R118_PARALLEL_BROKER_BINDING.json`, SHA256 `6cb229c8e2e4108a878d9070e4dce7a45583934152e714427428e1a542c394ca`.
- Immutable `R118_BROKER_IDENTITY_REPAIR_1544.json`, SHA256 `17cc6d0c5bd9c10e3a67bdef32d8880c2fe01698c65a5e1bb683d8d32e8d9747`; byte-identical local compact `BROKER_IDENTITY_REPAIR_1544.json`.

A1 binding also passed the frozen validator: native custodian2563918 monitors
VM HTTP provider worker2488913 using source/PLAN-bound heartbeats. This is
explicitly NODE_BROKER_CUSTODIAN custody, not a claim that HTTP runs on the node.
Its binding SHA256 remains `7bf40e1200d99674bd1c69d2faabdef7823eb131ac369cda89440b8d2cd443e1`.
Original36 responses remain23 COMPLETE/3 SILENT/10 MISSING with preserved hashes;
no old request was replayed. The disjoint custody wrapper passed12 local and12
native tests. The candidate closure previously passed215 tests/28 subtests.

## Lifecycle limits

Old route FINAL waiters1496784/1496788 were identity-checked and retired under
the scoped authorization. Cutoff1271059/1271060 were already absent. Selector
1519259 was neither inspected nor signaled. Original PLAN/raw/counters remain
preserved: F1 N425/P68 nextC8; A1 N202/P36 nextC5 at staging. Missing interrupted
DEV/OPEN are not successful and are not replayed.

Replacement cutoff and FINAL identity bindings require actual Main-dispatched
actor/guard receipts and actual all-eight successor-era peer bindings. They are
not claimed active at CPU staging. Main's reported failed dispatch must be
resolved before treating any new identities as valid. The common selector,
checkpoint, optimizer, CONFIG and original TRAIN16:55/hard17:02 bounds remain
unchanged. FINAL remains separate48 calls/branch,17:00–17:20, using the canonical
selection only. No fabricated identities or competing selection writer.

All raw remains node-local. Publication is limited to source/tests, these compact
hash receipts and the worker journal; Main owns Git.
