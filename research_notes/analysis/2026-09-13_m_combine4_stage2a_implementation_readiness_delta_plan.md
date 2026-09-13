# M-COMBINE-4 Stage 2A implementation-readiness and source/test delta plan

**Date:** 2026-09-13 PT  
**Scope:** fresh, read-only implementation audit and concrete CPU/source plan.
No builder-owned source, material root, model, tokenizer, adapter, process,
remote state, or GPU was changed or invoked.  
**Binding design:**
`2026-09-13_m_combine4_stage2a_binding_successor_v1.md`, SHA-256
`ac0a61fbbf907cc8dd463e4138ba268c4a44daded01926f298d759c6e9bf064a`.  
**Current source:** `organism_v6/composition_birth_stage0.py`, SHA-256
`f69c85ac4ca0b6c07c246de484da7262490d89ed8a612ec58476c6343aa29699`.  
**Current tests:** `tests/test_composition_birth_stage0.py`, SHA-256
`75d2ce9696ed34c4544ba559ce4944baf3526530beb319f34f306d59c06105d5`.

## Verdict

**REWORK before Stage 2A implementation.** The bound scientific comparison is
coherent, the count and cost arithmetic closes, and there is a direct
implementation path. The current source is nevertheless only the intentionally
quarantined tiny-interface fixture, and several exact contracts needed to
implement rather than reinterpret Stage 2A remain contradictory or
underspecified. The most important are the READ-failure form of ATOM-LOCAL
CHECK, executable singleton/pairwise null semantics, exact topology/strata,
whole-prefix versus target-only coupling, actor wire bytes, and the meaning of
an identical dropout tape when the treatment deliberately changes sequence
shape.

The existing 11-test module remains **GO as a negative regression fixture**:

```text
python3 -m unittest tests.test_composition_birth_stage0 -v
11/11 PASS in 0.026 s
```

It remains **NO-GO** as Stage-0 closure, Stage-2A material, an actor runner, or
an execution gate. This agrees with the prior source audit and the current
coordination ruling. The later critical-path ruling skips the tiny Stage-1
*model* run but retains its CPU service/parser/oracle checks; it does not turn
the partial fixture into Stage-2A evidence or open Stage-2A materialization,
model calls, fitting, or GPU work. A separate execution opening is still
required.

## Exact delta from the current source

| Area | Current bytes | Bound Stage 2A | Disposition |
|---|---|---|---|
| Domains | only `tiny_interface_dev`; all rich domains raise | 64-case train, held intervention panels, 32 autonomous tasks, canaries, reserved later domains | keep quarantine; add a separate Stage-2A module |
| Topology | fixed exhaustible two-corridor world, three READs expose it | two train families plus a held family/feature tuple; >12 reachable candidate addresses and <=4 sufficient READs | replace generator |
| IDs | hash of semantic `world_id/prefix/slot` | opaque independently permuted IDs/addresses with audited marginals | replace ID allocation |
| Curriculum | zero birth units | 256 shared target units rendered as CLOSED histories and ATOM-LOCAL vignettes | add paired renderer and tape builder |
| Oracle | enumerates the entire tiny graph | validates every unit/panel and acts on chains using public state and exact returns only | replace, retaining only the public-service principle |
| Nulls | seven assisted 16/32 diagnostics; fixed READ/STOP are oracle ceilings at 32/32; 36 pairs disabled | all declared singleton and pairwise nulls executable and <=1/2 | replace completely after exact null contract is bound |
| Parser | exactly one LF; unrestricted nonempty THINK body | one frozen model-output envelope and exact static grammar for all readouts | do not silently reuse; bind then implement |
| Service | deterministic exact EVENT/EVENTS_AT bytes or `MISS` | same passive, goal-blind property on rich registries | reuse semantics; generalize data and receipts |
| World | fail-closed irreversible STEP and exact STOP success | same, with full Stage-2A budgets and autonomous scoring | reuse semantics; replace implementation |
| Custody | only accepted turns are retained | every raw attempt retained before validation, separate accepted receipts | replace |
| Manifest | task summaries and hashes only | canonical complete material, trace, coupling, null, scan, lineage, and cost manifests | replace |
| Checker | tests import generator/oracle/scorer | second manifest-only implementation | add |

## What Astra should reuse

Preserve `composition_birth_stage0.py` and its tests as a separately named,
fail-closed Stage-1 CPU sentinel. Do not promote it in place and do not weaken
its `NO_GO_PARTIAL_SOURCE_ONLY` status. Reuse these concepts, preferably by
small dependency-free copies or a new neutral protocol module whose exact
bytes are reviewed:

1. `Event.raw` and `parse_events()` provide a simple deterministic EVENT wire
   shape. Reuse only after the terminal-newline convention is explicitly
   frozen for Stage 2A.
2. `ExactMemory` has the correct passive contract: a request maps to registered
   exact bytes or literal `MISS`; the service receives no goal and performs no
   path search, ranking, fallback, or model call.
3. `Session` has the right state-machine principles: STEP is irreversible,
   malformed/unsupported/over-budget turns terminate without repair, and
   arrival is not success until an exact STOP.
4. The existing tests for exact service returns, MISS, premature STOP,
   malformed output, budget boundaries, and causal twins are useful test
   patterns. Their expected custody behavior must change because failed raw
   attempts may no longer disappear.

Do **not** reuse `generate()`, `identifier()`, `scripted_oracle()`,
`decision_core()`, `source_report()`, `NULL_INTERPRETATIONS`, or the current
accepted-only `receipts` list for Stage 2A. The current oracle-assisted nulls
must never be imported as scientific null policies.

## Concrete source layout

Keep the tiny file untouched and implement the rich screen separately:

```text
organism_v6/composition_birth_stage2a.py
    pure frozen spec, dataclasses, deterministic semantic generator,
    opaque allocator, CLOSED/ATOM renderers, exact service/world/parser,
    public-information oracle, scanners, score and cost/state machine

organism_v6/composition_birth_stage2a_checker.py
    independent canonical-JSON checker; must not import the generator,
    renderer, oracle, decision-core helper, or scorer above

tests/test_composition_birth_stage2a.py
tests/test_composition_birth_stage2a_checker.py
```

If exact system/task prompt bytes, topology schemas, null policies, and
canaries are stored as data rather than constants, place them in one versioned
spec file and hash it. The scientific material generator must accept only that
spec plus fixed domain seeds. It must not import any PCFL/GOAL-BRAID module or
read their roots.

### 1. Freeze the semantic case ledger before rendering text

Generate exactly 64 semantic train cases, once, without a retry or
accept-until-balanced loop. Freeze independent domain seeds and explicit
remainder rotations. The semantic ledger must prove:

```text
family A/B                         32/32
ordinary/recovery                  32/32
reached/unresolved                 32/32
left/right goal                    32/32
skin 0/1                           32/32
recovery: strict MISS/irrelevant/
          STEP mismatch             8/8/16
```

It must also contain exactly 32 bijective `causal_pair_id` pairs (16
goal-switch, 16 returned-relation/deep-swap), balanced by family and flow, and
a second independent bijection mapping all 32 recovery cases to 32 ordinary
cases by `recovery_match_id`. Assert that the two registries are not silently
the same matching.

Generate opaque ID, address, port, receipt, row-order, and display-order pools
independently of semantic roles. Then apply separately seeded permutations to
roles. Public strings must not hash a family, factorial cell, semantic slot,
goal side, route choice, or target index. Save both the sealed pre-permutation
pool hash and the role-to-public permutation hash in the manifest; never save
a hidden answer in an actor prompt.

The topology schemas, held tuple, and exact remainder table need binding before
this step; they cannot safely be invented inside generator code.

### 2. Construct one target ledger, then render both arms

Derive one immutable ordered `TargetUnit` ledger from the 64 cases. Each case
contributes exactly four one-continuation units:

```text
READ   96 = 64 SEEK + 32 unresolved CONTINUE
STEP   64
THINK  64 = 32 KEEP + 32 REVISE
STOP   32
TOTAL 256
```

Render the target continuation exactly once. CLOSED and ATOM-LOCAL records
must reference the same `unit_id`, target bytes, target SHA-256, case public
IDs, and decision label. CLOSED renders the authentic accumulated prefix up to
that decision. ATOM-LOCAL renders only the frozen locally sufficient facts for
that decision and resets every unit. Each record contains exactly one target;
all prefix tokens are masked, and no erroneous recovery action is a target.

Build the presentation/update tape over shared `unit_id`s, not over separately
generated arm examples. D1 is four predeclared presentations of each unit;
D2 appends presentations five through eight without resetting either lineage:

```text
D1 per arm: 1,024 presentations / batch 4 = 256 updates
D2 per arm: 2,048 cumulative presentations / batch 4 = 512 updates
```

For every batch, emit the ordered unit IDs, target hashes, command counts,
target byte lengths, later tokenizer-derived target lengths, batch slots,
presentation number, optimizer-step index, and RNG checkpoint. Compare the
two arms field by field. Prefix byte/token/role distributions must be reported
as treatment-induced residuals rather than padded away.

The actual model tokenizer is a later authorized gate. Source tests may use a
small deterministic fake tokenizer to exercise masks and batching, but must
label those counts synthetic and cannot certify tokenizer marginals or target
tokens for execution.

### 3. Make forward-answer exclusion structural and scanned

Every prefix field needs a provenance tag such as `public_task_fact`,
`executed_child_action`, `service_return`, or `world_outcome`. There must be no
field capable of carrying `scheduled_action`, `future_route`, or evaluator
text. For each unit, derive a forbidden set from the semantic ledger:

- the exact next action and normalized action;
- its concrete READ address or STEP port;
- registered future-route IDs/addresses/ports not yet returned;
- future destinations not yet returned;
- evaluator/answer labels and declared aliases; and
- for recovery, any equality between the bad prior action and the corrective
  target.

Run literal byte scans, parsed-field scans, and the separately bound normalized
scan on every CLOSED and ATOM prefix. Record derivation inputs and zero counts.
The scanner must operate before text is admitted, and a failure invalidates
the fixed root rather than selecting another seed.

### 4. Implement one exact service/parser/world contract

The service is a presealed map from legal READ request bytes to exact response
bytes, otherwise `MISS`. It receives neither GOAL nor the oracle route. Row
order is part of the response bytes. Repeated, irrelevant, MISS, and
unsupported requests remain distinguishable in scoring.

The actor parser accepts exactly one action envelope and no repair,
canonicalization, fence stripping, whitespace trimming, or second-line
selection. Freeze whether the wire includes a terminal LF before code. Freeze
the exact THINK grammar: at minimum, scored CHECK targets are exactly `THINK
KEEP <event-id>` or `THINK REVISE <event-or-query-id>`. READ, STEP, and STOP
remain the static union and never enumerate task-local legal operands.

The autonomous session uses the Stage-2A limits, not the tiny limits:

```text
8 THINK / 12 READ / 8 STEP / 1 STOP / 4,096 generated actor tokens
at most 29 actor calls
```

Log counters before returning from every attempted call. Invalid token
accounting, truncation, malformed bytes, unsupported requests/actions, and
budget violations terminate the task.

### 5. Split lossless attempt custody from accepted world receipts

Append an immutable `Attempt` before parsing or validation, containing at
least sequence number, exact raw bytes (or an explicit typed non-string
encoding), generated-token declaration, truncation flag, pre-state, parser
disposition, operation/operand if parsed, service/world response bytes,
post-state, accepted flag, and terminal reason. Keep a separate
`AcceptedReceipt` ledger for executed valid actions and public responses.

Use separate append-only records for material generation, training batches,
model loading/identity, decode requests/outputs, evaluator results, and cost.
The canonical root manifest must include full task structures, registries,
unit/pair IDs, target and prefix hashes, correct public-information oracle
traces, null traces, coupling receipts, scanner output, topology certificates,
source/spec/config hashes, and parent-child artifact lineage. A summary is not
the custody root.

### 6. Implement three oracle surfaces

1. A unit oracle maps a parsed public prefix to the unique exact target for all
   256 units, without reading a scheduled target field.
2. An intervention oracle independently validates all 64 one-turn members and
   both-correct scoring for each of 32 pairs.
3. A chain oracle is itself an actor: it receives only START, GOAL, CURRENT,
   static grammar, its prior public transcript, and exact service returns. It
   must choose its READs and STEPs from those returns and finish all 32 tasks
   with verified arrival plus exact STOP. It may not receive a hidden route,
   sufficient-set list, next-address hint, or host-scheduled request.

The independent checker must reconstruct expected targets/routes from the
canonical public task and registry objects with separate code and reproduce
perfect scores.

### 7. Materialize the held readouts as first-class paired objects

Create 8 pairs for each transition, exactly 64 one-turn members. Each pair
stores an explicit allowed-diff schema and a byte-level diff receipt:

- SEEK: only GOAL, plus entailed prompt bookkeeping, changes; correct READ
  changes.
- PROSPECT: only the valid returned relation and its logically entailed bytes
  change; state, goal, request, candidate IDs, and display order remain fixed;
  correct STEP changes.
- CHECK: prior action and expectation remain fixed; CURRENT changes match to
  mismatch; exact KEEP/REVISE target changes.
- CONTINUE/STOP: CURRENT and store remain fixed; GOAL changes satisfied to
  unsatisfied; STOP changes to one useful READ.

Each member records exact command, operand, typed validity, and correctness;
the primary pair score requires both members correct.

Create 16 held causal-twin worlds and two goals per world. The 32 tasks use a
reserved topology/feature tuple and fresh public identifiers. For every task,
the checker must prove more than 12 distinct registered reachable candidate
addresses, a minimal sufficient witness set of at most four READs, and that
each next useful address is exposed by initial public state/goal or an earlier
exact return. Store the sufficient set only in evaluator custody, never actor
input. Score first irreversible STEP, full route, CHECK behavior, READ classes,
typed validity, goal arrival, exact STOP, and whole-chain success. On a
successful rollout, reject more than one pre-STEP READ outside the sufficient
set.

### 8. Replace nominal null names with executable total policies

Every singleton null must be a deterministic total mapping from the same
public input/transcript available to the actor to an action, including exact
tie and malformed/no-candidate rules. No null may call the oracle or use its
selected branch. Every unordered pair needs one frozen composition rule whose
result does not depend on name order. Save every action trace, not just a
score.

Run the singleton and all 36 pairwise policies on the exact scored panel(s)
named in the repaired contract and require each score to be at most one-half.
Separately run fixed/lexicographic/position/read-all-within-budget autonomous
schedules on the 32 chain panel and require at most 16 successes. The current
`fixed_read_schedule` and `fixed_stop_depth` implementations are ceilings
because they inherit the oracle branch; they must not survive under those
names.

### 9. Encode gates and dose selection as a closed state machine

At D1, evaluate BASE, CLOSED, and ATOM-LOCAL on all 64 intervention members,
32 autonomous tasks, and 16 generic canaries. A fitted arm is acquired only
with all four intervention types at >=6/8 pair-both-correct, >=60/64 strict
typed outputs, >=15/16 canaries, fitted-arm canary gap <=1/16, and every
source/custody/coupling/forward-scan/loss/parser receipt green.

An acquired arm qualifies on autonomous chains only with all of:

```text
whole-chain success                         >=26/32
arm - BASE                                  >= 8/32
causal twin pairs both correct              >=12/16
useful READ before first STEP               >=28/32
strict typed validity                       >=30/32
every predeclared eight-task stratum        >= 6/8
every deterministic null                    <=16/32
off-witness pre-STEP READs on each success  <=1
verified arrival followed by exact STOP     required
```

Select D1 and do not run D2 if both fitted arms acquire and at least one
qualifies on chains. Otherwise D2 may open only if custody/coupling are valid,
losses are finite, neither fitted arm loses more than 2/16 canaries from BASE,
and either an arm missed acquisition or both acquired but neither qualified.
Continue both lineages on the uninterrupted tape; never continue only the
favored arm. D2 is terminal and reruns only CLOSED/ATOM readouts, preserving
BASE and every D1 artifact.

After D2, advancement requires both fitted arms to be acquired. If only CLOSED
qualifies while ATOM-LOCAL is unacquired, do not advance. If ATOM-LOCAL
qualifies, select it by the simpler-curriculum rule, whether or not CLOSED also
qualifies. Select CLOSED only when CLOSED qualifies and acquired ATOM-LOCAL
fails chains; describe coherent-history benefit only if the gap is at least
8/32. If neither qualifies, stop this version. No deranged Stage-2A fit or
post-hoc rescue is allowed.

## CPU test and gate matrix

No scientific root should be emitted while source work is still closed. Once
the unresolved contracts below are rebound and source authoring is opened,
the implementation should pass these in-memory gates first:

1. **Inventory:** deterministic regeneration; exact 64/256 counts, all factor
   marginals, recovery allocation, two bijections, target-command totals, and
   no acceptance resampling.
2. **Opaque allocation:** semantic-role permutations are bijective; public IDs
   have no family/cell/slot input; train/readout namespaces and content sets
   are disjoint under the bound definition.
3. **Arm coupling:** every unit target byte/hash and every D1/D2 batch slot is
   identical across arms; all prefixes are masked; CLOSED histories are
   coherent; ATOM units reset; prefix residuals are reported.
4. **Recovery schemas:** MISS, irrelevant return, match, and mismatch each
   expose only their locally sufficient CHECK facts and select the correct
   implicated query/event operand.
5. **Forward scan:** literal, parsed, and normalized scans are zero; injected
   next address, port, route, destination, alias, evaluator label, or loss on
   a bad action is rejected.
6. **Parser/service/world:** golden bytes plus fuzzed CR/LF, whitespace,
   fences, multi-action, unknown-ID, repeated READ, MISS, invalid STEP,
   premature STOP, truncation, token/accounting, and all budget boundaries.
7. **Custody:** every invalid and valid attempt remains in the raw ledger;
   accepted receipts contain only executed turns; pre/post state and terminal
   reasons reconcile.
8. **Panels:** exactly 8 pairs per transition; only allowed fields differ;
   exact target flips; pair-both scoring; fresh IDs and held feature tuple.
9. **Chains:** exactly 16 worlds/32 tasks; >12 reachable candidates, <=4
   sufficient witnesses, no actor-visible witness/route; oracle 32/32; exact
   STOP; READ-class reconciliation.
10. **Nulls:** all singleton and 36 pairwise policies actually execute, use no
    oracle-selected fields, save traces, and score <=1/2 on the declared
    denominator; autonomous schedule nulls are <=16/32.
11. **Topology/separation:** independent role-core/rooted-signature
    reconstruction, zero forbidden equalities, one exact held combination,
    target/action contingency tables, and every declared pairwise surface
    table.
12. **Independent checker:** consume canonical JSON only; reproduce inventory,
    legal transitions, oracle scores, scans, nulls, topology certificates,
    hashes, and costs; mutation tests must reject one-byte target, route,
    registry, mask, pair, and receipt corruptions.
13. **Dose state machine:** exercise every D1/D2 acquisition/canary/chain
    branch, preserve D1 artifacts, never rerun BASE at D2, and make D2
    terminal.
14. **Cost:** programmatically recompute all caps below from task and token
    limits.

After those pass, require a fresh independent source review. Only a separately
authorized materialization may write a canonical root and invoke the exact
tokenizer to certify chat-template bytes, response-only masks, target token
counts, identifier tokenization, padding, and per-update sequence tokens. Only
after that evidence and an explicit execution opening may model/fit/GPU work
begin.

## Constraints that must be repaired or made exact before implementation

### A. ATOM-LOCAL CHECK is internally incomplete

The target inventory makes 16 recovery CHECKs follow failed READs (8 `MISS`,
8 irrelevant returns) and 16 follow STEP/outcome mismatches. Section 4,
however, defines ATOM-LOCAL CHECK only as prior STEP + EVENT-implied
consequence + CURRENT. That schema cannot render a locally sufficient
query-revision vignette for a failed READ. Bind two CHECK schemas:

```text
READ-CHECK: issued query + exact MISS/irrelevant return + facts needed to
            establish irrelevance -> THINK REVISE <query-id>
STEP-CHECK: selected STEP + implicated EVENT expectation + CURRENT
            -> THINK KEEP/REVISE <event-id>
```

Also bind what proves an irrelevant return irrelevant without leaking the
future corrective READ.

### B. Null semantics are not implementable as written

The nine inherited names are not nine total action policies over SEEK,
PROSPECT, CHECK, CONTINUE/STOP, and autonomous rollouts. READ schedule and STOP
depth are schedules, not branch choosers; pairwise composition and tie rules
are absent; and the scoring denominator called “actual Stage-2A material” is
not named. The current source demonstrates the failure by giving the two
schedules an oracle suffix and scoring 32/32. Bind separate one-turn
classifier nulls and autonomous rollout policies, the exact panel for each,
and one order-independent pair composition rule.

### C. The topology and strata are names, not frozen material definitions

“Two unrelated train families,” the held family/feature combination, topology
motif, depth, goal switch, match/mismatch tuple, sufficient witness, reachable
candidate address, and every eight-task stratum need exact definitions. So do
the recovery remainder rotation and how causal-pair mutations preserve other
factors. Without them, two compliant-looking generators can test materially
different hypotheses.

### D. Several literal coupling requirements conflict with the treatment

If “identifier-token marginals” means the entire prefix, CLOSED necessarily
contains earlier-history identifiers that minimal ATOM-LOCAL omits. Those
whole-prefix marginals cannot be identical without adding nonminimal padding.
Bind target-only identifier equality plus separately reported prefix
residuals, or define an allowed prefix-marginal comparison.

Likewise, identical dropout *masks* are not naturally defined when coherent
and local prefixes have different sequence shapes. A common global seed does
not produce positionwise identical masks after different numbers of random
draws. Bind whether “dropout tape” means identical per-update RNG checkpoints,
a counter-based target-position coupling implemented by a reviewed trainer,
or merely identical seed/schedule receipts. Do not claim exact mask coupling
from equal seeds alone. “Optimizer tape” also needs a list of the state and
hyperparameter fields required to match while gradients properly differ.

### E. Literal zero text overlap conflicts with the shared interface

The arms and downstream domains deliberately share generic grammar words and
wire semantics, while the contract also says zero text intersection and
forbids reading/hash-comparing sealed PCFL/GOAL-BRAID instances. Define the
comparison unit as concrete content strings/IDs with an explicit allowlist for
protocol literals. Supply a public forbidden-spec/namespace certificate that
can be checked without opening sealed roots. Zero overlap with unknown sealed
instance bytes cannot otherwise be empirically certified.

### F. Parser and prompt bytes are not frozen

The tiny source requires one terminal LF; other project contracts use a
no-CR/LF one-line envelope. The Stage-2A successor does not choose. It also
does not freeze exact system/task instructions, whether generic THINK text is
legal beyond KEEP/REVISE, response ordering, or query-ID spelling. These are
scientific inputs and typed-validity determinants, so bind their exact bytes
before sharing parser code.

### G. Canaries, topology cores, scanners, and diff entailments are incomplete

The 16 generic actor canaries per state and their scorer are absent. The exact
role-labelled decision core, rooted signature radius/fields, forbidden motif
specification, normalized-alias function, and logically entailed diff
allowlists for interventions are also absent. All affect gates. Freeze them in
the spec rather than filling them in after seeing source output.

### H. Execution pins remain later gates

Before fitting, bind the exact base/tokenizer/chat-template bytes, decode tape,
one-turn token cap, initialization derivation, optimizer serialization,
padding/collation, and actual target-token receipts. These do not block pure
source planning, but source-only fake-tokenizer tests cannot satisfy them.

## Cost closure

The successor's arithmetic is internally consistent and should be encoded as
assertions:

| Stage-2A work | D1 | D2 addition | terminal cap |
|---|---:|---:|---:|
| fit invocations | 2 | 2 continuations | 4 |
| optimizer updates, both arms | 512 | 512 | 1,024 |
| autonomous rollouts | 96 | 64 | 160 |
| max autonomous actor calls | 2,784 | 1,856 | 4,640 |
| intervention calls | 192 | 128 | 320 |
| canary calls | 48 | 32 | 80 |
| total model calls | 3,024 | 2,016 | 5,040 |
| generated-token cap | 454,656 | 303,104 | 757,760 |
| reader-model calls | 0 | 0 | 0 |

The token totals are `rollouts * 4,096 + one_turn_calls * 256`. Training
tokens, wall time, and GPU-hours are intentionally not inferable until actual
prefix/tokenizer receipts exist; record sequence tokens/update,
seconds/update, actual actor tokens, engine-load time, and peak memory.

## Handoff ruling

1. Preserve the current tiny fixture and its passing negative tests.
2. Rebind A--G above as exact spec bytes; this is the minimum REWORK needed
   before Stage-2A source can be judged faithful rather than designer-chosen.
3. After an explicit source-authoring opening, implement the separate pure
   generator/runtime plus independent manifest-only checker in the order
   above, with no scientific root or tokenizer/model access.
4. Require every CPU gate and a fresh independent source audit.
5. Only then request the separate materialization/tokenizer and execution
   openings. Do not run the skipped tiny Stage-1 model assay unless the latest
   root ruling is itself changed.

**Final ruling: REWORK.** The scientific Stage-2A question and resource cap
are usable, but exact source authoring should wait for the listed contracts;
current passing tests certify only the quarantined tiny CPU fixture.
