# Independent held-construction review

Completed 2026-09-13 22:00 UTC. Verdict: PASS for the requested synthetic,
source-only construction scope. No runtime/scoring/science qualification and
no additional human gate. No functional defect found in the reviewed output.

## Bound inputs

- organism_v6/composition_birth_stage2a_held.py SHA256:
  4a0ede31c7b7585f86338fbfa419ee2e87e104bd3a05cdf243edb0ee35fe651d
- tests/test_composition_birth_stage2a_held.py SHA256:
  47106304e860a61cb684afb8fb791bb33fe18c48ec0ed82bd95fdb8cfd20d8c0
- Stage2A v3 sections 4/5 SHA256:
  da833b9df37930d0b06f9206e5fa47d5b436b325e833e6f6b2f4221f4d8808d1
- Stage2A v4 corrections SHA256:
  ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1
- Builder source clarification v1 SHA256:
  5484567fdad924247c5371a7430a071c925c563b5375336e8bef86dc6a4a99f9

Read the relevant imported v2 sections 9/10 and checker caller-limit contract.
Reviewed source and test hashes were unchanged at the closing read. Other
concurrent workspace changes were not reviewed or modified.

## Checks and evidence

Eight selected existing unittest methods passed in 1.610 seconds: pinned
source hashes/closed gates; all public-prefix targets; PROSPECT non-FOR byte
preservation; CHECK effective receipts/base preservation; v4 chain slots and
directory positions; exact chain recovery owners; witness replay through the
existing scalar Session; explicit role-token input rejection. Python/pytest
were unavailable under those command names; used installed python3 and the
standard-library unittest runner, with bytecode writing disabled.

Independent checks used a different synthetic SHA256/base32 namespace, the
symbolic inventory only, and independently written scalar-leaf, byte, slot,
pin, registry, transition, and trace assertions. No scientific allocator was
used. Checked all 32 intervention pairs/64 members and 16 chain worlds/32 tasks.

- Exact leaf-difference equality, not subset: SEEK 5 leaves, PROSPECT 6,
  CHECK 6, CONTINUE 6. Semantic object leaf sets are equal between members;
  no task rendering is duplicated in transcript. Relation swaps preserve all
  non-FOR rendered bytes and the full base-world mapping.
- Every intervention directory follows the two bounded pins and ascending
  remainder fill. The clarification's modulo-24 correction applies, including
  wraparound. No rotate/search/retry choice was introduced.
- CHECK override applies only at the designated start/current and event port.
  All other valid edges return their fixed base destination without a receipt.
  Both members retain the same base-world bytes. Typed receipt construction
  precedes construction of the scalar WORLD payload.
- Chain start and all eight predicted-hub directories match the exact pins
  and ascending remainder fill. Only the two scored first-hop blocks use the
  v4 (world+member) slot; unscored and hub blocks use the generic formula.
- Exactly two scored first-hop contradictions and candidate-owned recovery
  registrations per mismatch world, none in expected worlds. Nested recovery
  remains MISS; surprise hubs have no INDEX. Counts reconcile to 144 INDEX,
  3456 useful RELATION plus 16 recovery registrations, and 13888 chain edges.
- Witnesses use exactly two legal STEPs, one nonterminal KEEP/REVISE, then
  direct terminal STOP; sufficient READ sets have cardinality 4 expected/3
  mismatch. Predicted h and surprise w destinations follow their separate
  formulas. Four strata each contain four worlds/eight tasks.
- Public prefixes have exactly 4/6/8/2 messages for SEEK/PROSPECT/CHECK/CONTINUE;
  chains start with only system and TASK. Service replies replay exactly from
  requested keys; WORLD is the public scalar outcome. No evaluator metadata,
  answer annotation, intervention object, receipt, witness, or sufficient-read
  set is appended to these actor-message prefixes. Legitimate QUERY/EVENT/GOT
  identifiers in public service responses are not themselves answer leakage.

Ten targeted in-memory source mutants were rejected: unwrapped route pin;
CHECK widened to every port at CURRENT; CHECK disabled; PROSPECT GOT change;
generic rule substituted for scored first-hop slot; unshifted hub pin; wrong
surprise-hub multiplier; removed mismatch destination; KEEP on mismatch;
answer appended to public prefix. Rejections came from construction guards or
independent assertions, not from a claimed integrated runtime checker.

Mutation-test correction: the surprise multiplier mutant initially survived
the h04-only probe because both scored goals (8,16) make 5*j and 7*j identical
modulo 8. Expanded to h04-h07; the h05 distinguishing fixture rejects it via
the exact role inventory. This was a test-fixture alias, not a source defect.

## Nonblocking wording issue and explicit limits

P3 documentation: organism_v6/composition_birth_stage2a_held.py:108 calls the
entire PublicView an "Actor/parent-safe projection." That is broader than the
actual boundary: registry is a directly enumerable, complete host service
mapping, not merely previously observed responses hidden behind read().
The source does not send that host object anywhere; this is NOT an observed
actor-prompt leak. Its prefix is the actor-message projection. There is no
actor_messages runtime routine in this held module yet.

Minimal fix: change that docstring to describe a host-side public-service
facade and specify that only prefix and requested READ responses are
actor-visible; the entire registry/object is not parent-safe to serialize.
No functional refactor or new approval gate is needed for this wording fix.

One-shot custody is still a runtime responsibility. execute_step at line 194
is pure/reusable: repeated designated calls return the override again.
Confirmed this deliberately; it is appropriate to a source-only evaluator
helper, not evidence of session-level exactly-once consumption. Future runtime
must bind/consume the designated execution and durably record receipt before
emitting WORLD, without exposing intervention metadata or forcing actor actions.

Semantic-truth caller limits remain: evaluator answer and target bytes come
from the constructor; leaf equality proves only those compared objects, not
authenticated provenance or runtime truth. The existing checker explicitly
limits hashes/world facts to caller assertions and cannot prove public
visibility, latest CURRENT, target truth, or scientific validity. These tests
do not close those limits or establish runtime scoring, null gates, token
budgets, train-held separation, or model/GPU performance.

No repository edits, network, model, GPU, SSH, commits, or whole redundant
test suite. This /tmp note is the only intentionally written review artifact.
