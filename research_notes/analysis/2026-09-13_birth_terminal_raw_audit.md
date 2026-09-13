# SEQ-120 terminal BIRTH raw audit

Independent audit at 2026-09-13T01:08Z. I read the committed terminal capsule,
not the stored score rows, and independently derived every expected response
from the public request text. I did not import the corpus scorer or use its
reducers. No builder source, adapter, job, or remote artifact was changed.

## Evidence closure

The committed capsule SHA256 is
`07816cb0649255ddaec5377e0b2ab4442919ea806d2eb60243b0155f1dc96a2a`;
the external validation SHA256 is
`4a47152320d9b78e16427c25858b9f8d37d2bb054d6db2fcda46128dd2a3a07b`.
All 814 regular capsule members have exactly the declared name and SHA256.
There are 128 paired request/response records in each of OFF, AUTH and
DERANGED (384 calls total), and the ordered case IDs and public requests match
across cells. The remote terminal copy has the same two hashes as the committed
files.

## Raw result

`Own` below means exact complete response under that cell's assigned map;
`opposite` means exact complete response under the other map. Anchor targets
are identical across maps.

| Cell | PROSPECT own / opposite / other | REVISE own / opposite / other | ADDITION exact | COPY exact | Conditional length finishes |
|---|---:|---:|---:|---:|---:|
| OFF | 0 / 0 / 32 | 0 / 0 / 64 | 8/16 | 8/16 | 96/96 |
| AUTH | 32 / 0 / 0 | 58 / 0 / 6 | 15/16 | 16/16 | 0/96 |
| DERANGED | 32 / 0 / 0 | 56 / 0 / 8 | 15/16 | 16/16 | 0/96 |

Thus the learned conditional contrast is real and not an AUTH-only evaluator
artifact. PROSPECT is exactly complementary on all 32 paired prompts. In
REVISE, AUTH and DERANGED emit opposite correct complete policies together on
50/64 prompts. Their raw outputs differ on 64/64, and their COMPARE and POLICY
fields are the assigned complementary values on 64/64 in both cells, but NEXT
is correct on only 58/64 AUTH and 56/64 DERANGED. It is therefore accurate to
say the branch policy is opposite throughout; it is not accurate to say the
complete REVISE policy is correct/opposite throughout.

The REVISE error is sharply localized. Both cells are 32/32 on held `view3`
and on assigned MISMATCH/SWITCH cases. On held `view2`, AUTH is 26/32 and
DERANGED 24/32; equivalently, assigned MATCH/KEEP is 26/32 and 24/32. AUTH's
six misses and DERANGED's eight misses are disjoint. Every miss is a wrong NEXT
under the otherwise correct MATCH/KEEP branch; two DERANGED misses output both
actions (`NEXT: dax, wug`).

Independent endpoint-pair counts also reproduce the registered twin result:

| Assigned cell | belief | goal | expected | observed | prior-action |
|---|---:|---:|---:|---:|---:|
| AUTH | 16/16 | 16/16 | 26/32 | 26/32 | 26/32 |
| DERANGED | 16/16 | 16/16 | 24/32 | 24/32 | 24/32 |

No trained conditional answer equals the opposite map. There is zero forbidden
anchor-tag spill in all three cells.

## OFF floor and locality

OFF is a floor cell, not evidence of absent base competence: every one of its
96 conditional generations reaches the 64-token cap, so strict exact count is
zero under this interface/budget. Its anchors are only 8/16 exact for addition
and 8/16 for copy. The registered anchor rule is
`max(ceil(.95 * 16), OFF - 1) = max(16, 7) = 16`; the absolute term, not OFF,
is binding. AUTH and DERANGED both improve materially over OFF, and COPY is
16/16, but each misses the same addition case ID (`birth-r0-dev-addition-001`):
AUTH says `ACT: 89`, DERANGED says `ACT: 80`, target `ACT: 79`. Therefore the
registered anchor-locality conjunction fails both arms at 15/16. “The earlier
catastrophic locality collapse is gone” is supported; “locality passes/holds”
is not supported under the frozen criterion.

## Why `automatic_L1_pass` is false

It was not computed and then failed. The runner writes
`automatic_L1_pass=False` unconditionally in the aggregate and validation, and
the corpus/scorer explicitly supplies no L1 verdict. Even a perfect component
would retain that sentinel because this is authored, not clean, not own-wake,
and not the full birth core.

The observed predeclared component conjunction also genuinely fails. AUTH
passes the operation totals but misses all three REVISE twin minima
(26 < 29) and addition locality (15 < 16). DERANGED additionally misses the
REVISE total (56 < 58), misses all three REVISE twin minima (24 < 29), and
misses addition locality (15 < 16). Belief/goal twins, PROSPECT, COPY, and
zero-spill conditions pass.

## Contradictions and audit verdict

The stored numerical reductions match this raw recount; I found no count
contradiction. Two prose labels need correction. The coordination claim that
“locality now holds” is stronger than the registered result: only relative
non-collapse holds, while the 16/16 locality gate fails. Its statement that
“revising when the observation contradicts the expectation succeeds ~80%” is
also not the AUTH raw pattern: AUTH contradiction/MISMATCH cases are 32/32;
AUTH failures occur only when EXPECTED equals OBSERVED. The roughly 80% result
belongs to assigned MATCH/KEEP on `view2` (and, for DERANGED, that inverted
branch happens on literal EXPECTED/OBSERVED disagreement).

Verdict: narrow, one-root authored conditional map carriage is demonstrated,
including truly complementary PROSPECT and REVISE branch selection. Complete
REVISE execution is imperfect and template/branch-localized; registered anchor
locality and revision twins fail. This terminal cannot supply an automatic L1,
clean-birth, own-learning, Q0, parenting, H1, or H2 verdict.
