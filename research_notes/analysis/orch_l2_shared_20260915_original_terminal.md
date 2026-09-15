# Original L2 SHORT-owned three-cycle terminal report

Verified September15, 2026 at01:10:47UTC. Original SHORT guardian completed
01:09:18UTC; original FROZEN guardian completed01:05:39UTC. UNPARENTED had
already completed00:33:50UTC. No restart, new cohort/source, policy change,
extra cycle, old-case model replay, or deadline extension was performed.

## Final owned treatment counts

Each experience cycle contains16tasks/eight worlds; each lane totals48tasks.

| Lane | C1/C2/C3 experience successes | Admitted rows | Actual updates | Learner reservations |
|---|---|---|---|---:|
| SHORT + sleep | 1/16, 6/16, 2/16 | 0, 0, 0 | 0, 0, 0 | 666/1600 |
| SHORT-guided FROZEN control | 0/16, 4/16, 4/16 | 0, 0, 0 | 0, 0, 0 | 677/1600 |
| UNPARENTED + sleep | 5/16, 4/16, 3/16 | 1, 0, 0 | 26, 0, 0 | 686/1600 |

SHORT and FROZEN actual mounted state remains
`e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf`.
UNPARENTED changed only at sleep1 to
`f2013ae172f58d3f2aea843272eb7aea286d587a21d4cb96b905cb965ac99100`.
Every collector/readout input is checked against the previous actual child;
every null sleep preserves that state. Frozen base throughout:
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.

## Exact same-stage held, matched controls and deterministic reference

Cells report **correct goals/16 ; both-goal world pairs/8**. Pairs require both
opposite-goal tasks correct and distinct first routes. Compare columns within
one row; rows use different fresh cohorts.

| Held stage | SHORT | Guided FROZEN CONTROL | UNPARENTED | First-current-port REFERENCE |
|---|---|---|---|---|
| Initial | 11/16 ; 5/8 | 11/16 ; 5/8 | 11/16 ; 5/8 | 8/16 ; 0/8 |
| C1 | 11/16 ; 4/8 | 11/16 ; 4/8 | 8/16 ; 2/8 | 8/16 ; 0/8 |
| C2 | 11/16 ; 4/8 | 11/16 ; 4/8 | 11/16 ; 4/8 | 8/16 ; 0/8 |
| C3 | 15/16 ; 7/8 | 15/16 ; 7/8 | 11/16 ; 3/8 | 8/16 ; 0/8 |

Every one of these12 completed owned readouts retains W0 **16/16**, W8
**16/16**, audit **16/16** (true8/8, fault8/8). No coaching at readout.
The deterministic reference is routing-only; W0/W8/audit are not applicable
to that no-model policy. Its counts are actually derived from unchanged
saved COHORT/SOURCE and checked transition receipts, not assumed8/16.

SHORT/FROZEN raw traces match on16/16tasks at EACH held stage. Their11-to15
change has unchanged weights and a changed cohort: it is NOT learning.
Their advantage over first-port is retained initial capability. Guided FROZEN
is the matched response-aware/no-sleep control, never the first-port reference.

## LONG: separate ongoing ownership, actual treatment and new held evidence

Read-only peer snapshot at this publication now contains LONG C1 held **8/16**
with W0/W8/audit16/16 after2admitted rows/28actual updates. The C1 same-stage
guided-frozen control is11/16 and deterministic first-port is8/16. This is
a descriptive3-goal deficit versus the matched control, NOT causal proof,
policy equivalence to first-port, or a guided gain. LONG is the first GUIDED
actual consolidation treatment; UNPARENTED's earlier26updates were unparented.
LONG C2 experience2/16,0rows/0updates is complete in this snapshot; later
held/terminal status remains its owner's responsibility. No physical1 action
or LONG policy/hook modification by SHORT.

## Accounting, failures and release

Source448calls remains shared once. SHORT provider bucket (including
UNPARENTED semantic review) reserved184/600 slots; FROZEN184/600. These are
actual pre-provider reservations, distinct from92logical requests per bucket;
do not double-count logical parent requests as extra provider calls. All
learner ledgers are contiguous, failed attempts remain charged, and original
deadline1789472611.845884 is unchanged. This is not a terminal claim for LONG.

All3 SHORT parent distillations and FROZEN C2 distillation are retained.
FROZEN C1 and C3 distillation failures remain failures with original raw
provider outputs/errors; no salvage, retry or synthesized replacement.
1451 original owned provider files, including exact messages and accounting,
are archived separately. Earlier UNPARENTED pregradient failure and unresolved
reviews remain preserved. Null cycles include zero rehearsal updates and
their real readouts; no padding, retroactive admission or prefix repair.

After final receipt/count/chain verification, both actual guardian/native
PIDs had exited and UUID-checked inventory showed0MiB:

- A100physical0 `GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6`.
- A100physical2 `GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296`.

These two lanes are released upward to Main for allocation; no new task is
launched. Physical3 was released earlier and belongs to Erdos's separate
original37ec-seeded pilot. Physical1 remains LONG-owned. The serial parent
broker stays available for LONG; it is not killed on SHORT completion.

## Durable exact evidence

Under `research_notes/analysis/orch_l2_shared_20260914_attempt1/`:

- `ORIGINAL_OWNED_TERMINAL_20260915.tar.gz`, SHA256
  `e18ee9d5102d8950921151ed546eac4ea583730b0385989223c4cc23c47a6278`.
  Three owned lanes, original failed/completed guardians, captures, masks,
  losses, source/cohort/legacy bytes and ledgers; adapter tensors excluded
  from archive but original remote tensors preserved. Remote/local hashes match.
- `ORIGINAL_OWNED_TERMINAL_20260915_SUMMARY.json`, SHA256
  `6120ee1f4810385cbd29eddbf445dba0212590a3a668fd9accd8e0c635b945e1`.
  Exact native receipt paths/hashes, transitions, mounted chain, task/pair
  reductions, guardian endpoints, absent PIDs, idle UUIDs and budget assertions.
- `FIRSTPORT_FIXED_REFERENCE_20260915.json`, SHA256
  `5bbbbeeb19ea98046caf415268e5f6a642fe534417f50e832689aebfefc1685a`.
  Existing fixed worlds only; zero model/provider calls/fits; every route bound.
- `LONG_READONLY_STATUS_AT_OWNED_TERMINAL.json`: exact peer receipt pointers
  and hashes, not ownership, terminality or independent replication.

Under `research_notes/analysis/orch_l2_guided_20260914_attempt1/`:

- `OWNED_TERMINAL_PROVIDER_RECEIPTS_20260915.tar.gz`, SHA256
  `8589ab50b04877ba2d6d4caf322d83067c19e3280856ebb02e7d94bcfea3f146`.
  Companion JSON hashes all1451files and binds both184-slot provider ledgers.

All artifacts here are operator-only, never parent input. Interface/source
unchanged. Four report-parser CPU regressions and terminal count/mounted-chain/
retention/ledger/trace assertions pass; no live-runtime repair was deployed.

## Scientific close and next compute

This completed SHORT recipe realized no qualified guided consolidation in
three cycles. That is a genuine bounded null, not a missing launch or evidence
against the developmental thesis. Retained action capability exceeds the
deterministic reference but provides no gain claim. LONG's first actual guided
treatment currently does not beat its same-stage control; wait for its owned
full trajectory before a broader conclusion. No H2/promotion/replication claim.
Main's separately controlled original37ec rich-bootstrap pilot is the next
allocated test; do not extend this run, change its source, or borrow its caps.
Peer lesson: distinguish controls, deterministic references, treatment actually
received, and cross-cohort variation before interpreting an improving score.
