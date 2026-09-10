# Independent Stage-A oracle for RML-D0 Candidate B

**Object under test:** `RML-D0-FT-B-V1` only.  
**Authority:** `chg_20260901_rml_d0_exact_v2`, limited to the deterministic
CPU package and staged preflight.  
**Oracle scope:** an independent, adversarial Stage-A review specification. It
does not implement the subject, edit `rml_d0/`, execute Stage B, or authorize a
model, network, GPU, learned-memory, locked, on-policy, publication, or
scientific-claim action.

## 1. Pass meaning and independence rule

A Stage-A pass means only that the finite microgeometry and canonical
interfaces conform to Candidate B. It does not release Stage B by itself; the
authorized supervisor must consume a complete passing Stage-A report through
the frozen fail-closed transition.

The oracle must not import target, twin, bridge, P, first-accept, or quotient
expected values from `rml_d0`. It may invoke the subject through its public
Stage-A entry point and parse its sealed outputs, but all expectations must be
literal values from this file or a separately reviewed independent reference.
Otherwise a mutation to the subject constant and its self-generated golden can
pass together.

Before any comparison, require these exact predecessor hashes:

| Artifact | SHA-256 |
|---|---|
| Candidate B | `bd2a3b2bc11dd0b7f9591266ca9b9094e89195a0af581e248bc09e41e481805b` |
| authorized change | `bd3fc32b004047d3a3a9e7700193e9feb8f5850541741a4037bf5a1b8d91e748` |
| consensus | `41cfd553e9a27f6ab3c5343c0c6ce32b76f4f0b6ef1838d06f2f9e3c3f7be72c` |
| human ratification | `99a51f736198e670c153c280d7d9658feebc56dfbfb1113204e9b3505ab6ed34` |
| scope proposal | `ae15bf148190b133c7f44252c1a2e5d5454f059b865fbd35f9f65bfbef7feb17` |

A mismatch is `NOT_RUN_WRONG_PREDECESSOR`, not a failed scientific cell and
not permission to update an expected hash.

## 2. Digest convention

Vector digests below are SHA-256 over the exact one-line UTF-8 JSON bytes shown
or described, with object keys already in lexical order and with **no trailing
LF**. This matches Candidate B's rule that durable JCS records end in one LF
but their content hash covers the bytes before the LF. These are oracle-vector
digests, not substitutes for the subject's content-addressed record hashes.

## 3. Minimum exact vector suite

### A. Twin target algebra

The conditioner table is:

| `u` | `r` | H useful pair | twin-useful public families, named by H code |
|---|---|---|---|
| `00` | `11` | `T01,T11` | `T00,T10` |
| `01` | `10` | `T01,T10` | `T00,T11` |
| `10` | `01` | `T00,T11` | `T01,T10` |
| `11` | `00` | `T00,T10` | `T01,T11` |

Its canonical oracle array is:

```json
[{"h_pair":["T01","T11"],"r":"11","twin_pair":["T00","T10"],"u":"00"},{"h_pair":["T01","T10"],"r":"10","twin_pair":["T00","T11"],"u":"01"},{"h_pair":["T00","T11"],"r":"01","twin_pair":["T01","T10"],"u":"10"},{"h_pair":["T00","T10"],"r":"00","twin_pair":["T01","T11"],"u":"11"}]
```

Expected digest:
`316aac145f65bd5d9362e03a6fca1338a662cc0843f43e8fb96badadffd4c944`.

The valve involution is:

```json
[{"h":"BYPASS","twin":"RECIRCULATE"},{"h":"RECIRCULATE","twin":"BYPASS"},{"h":"PULSE","twin":"DIRECT"},{"h":"DIRECT","twin":"PULSE"}]
```

Expected digest:
`4d836dd079900c096afdef06d32fc09711f494f5126f0407a5d021793e92d5ac`.

Take the Cartesian product: all 16 target twins must have minimum depth nine
on both sides, exactly one unordered useful conditioner pair per side, exactly
one correct valve mode, disjoint cross-side pairs, different cross-side modes,
and byte-identical target-visible records. There are 32 successful side cases;
partial enumeration is failure. `NW_TARGET_00` is:

```json
{"h_mode":"BYPASS","h_pair":["T01","T11"],"minimum_depth":9,"r":"11","twin_mode":"RECIRCULATE","twin_pair":["T00","T10"],"u":"00"}
```

Expected digest:
`e422c5cc4bdf893308b3e260553e5a665948ba5f34c4ac8294365f861d54ee9a`.

### B. Certified-bypass bridges

The eight bridge rows are:

| bit | `a` | `z` | reset | exchanger | A | B |
|---|---:|---:|---|---|---|---|
| `v` | 0 | 0 | `00` | `00` | `T00` | `T01` |
| `v` | 0 | 1 | `01` | `01` | `T00` | `T01` |
| `v` | 1 | 0 | `00` | `10` | `T01` | `T00` |
| `v` | 1 | 1 | `01` | `11` | `T01` | `T00` |
| `i` | 0 | 0 | `00` | `00` | `T10` | `T11` |
| `i` | 0 | 1 | `10` | `10` | `T10` | `T11` |
| `i` | 1 | 0 | `00` | `01` | `T11` | `T10` |
| `i` | 1 | 1 | `10` | `11` | `T11` | `T10` |

For the canonical oracle objects, table columns `A` and `B` map to
`a_code,b_code`, scalar `a` maps to `set_value`, and the remaining keys are
`bit,exchanger,reset,z`. The object-array digest is
`f096c7ca5d2f4b8cf614963ec7fe4a997c8d757057c89ca10bf494b6fa3d5b8a`.

Every row must produce exactly:

```json
{"h_results":["APPLIED","RUN_STABLE","APPLIED","RUN_TRIPPED"],"twin_results":["APPLIED","RUN_TRIPPED","APPLIED","RUN_STABLE"]}
```

Expected digest:
`c9c9d05dda01d0f8bdc7d09b73d4ea99020039d2a135b67c5fba0e4ab554ff64`.
Both resets must be certified-bypass exchanger-bench resets; a valve family or
mode may not explain the contrast.

### C. Four-mode balance and source counts

For each omitted mode `mu` in all four modes, Stage A must enumerate all four
translations, all six local permutations, and all four selected-handle
positions. After removing the common factor, the action-only integer posterior
is exactly `[6,6,6,6]`. The four balance actions must be all four canonical
modes in order, never a `mu`-dependent subset.

The exact cumulative count vector is:

```json
{"cumulative_events":[123,250,500,996],"cumulative_mappings":[36,71,142,285],"schema_status_cumulative":[0,5,16,39],"schema_status_new":[0,5,11,23]}
```

Expected digest:
`a5860239f79a5f97b84f82b758e5fa242c9932a0a22d69f441fce68407a6335c`.

Stage A need not build full production lives, but its row expander must prove
these totals symbolically from `41` dense events, `37` V-sparse events, four
balance events, and four bridge events. A count-only proof does not replace the
four `mu`-conditioned BE multiset comparisons.

### D. P atoms-only completion

`NW_P4` must use four target-visible-identical completions ordered
`BYPASS,RECIRCULATE,PULSE,DIRECT`, each with integer weight one. Exactly one
minimal plan succeeds per completion. WITNESS-GRAPH value is `1/4`; SCHEMA-GOLD
and PROGRAM-SEARCH value are `1`.

```json
{"completion_modes":["BYPASS","RECIRCULATE","PULSE","DIRECT"],"completion_weights":[1,1,1,1],"schema_value":[1,1],"witness_graph_value":[1,4]}
```

Expected digest:
`45e104c62cca1d3ec115ce3e2fc20465e03cca3e6016d7da92dd9d9a668fc917`.
The ablation must not rerun affine-law filtering or target acceptance.

### E. Connected J inventory

The eight inventory cases below name the useful old and recent H codes. The
four public inventory families must always comprise both setters for `old_bit`
from the old module and both setters for the other bit from the recent module.

| `u` | old bit | H old | H recent | twin old, named by H code | twin recent, named by H code |
|---|---|---|---|---|---|
| `00` | `v` | `T01` | `T11` | `T00` | `T10` |
| `00` | `i` | `T11` | `T01` | `T10` | `T00` |
| `01` | `v` | `T01` | `T10` | `T00` | `T11` |
| `01` | `i` | `T10` | `T01` | `T11` | `T00` |
| `10` | `v` | `T00` | `T11` | `T01` | `T10` |
| `10` | `i` | `T11` | `T00` | `T10` | `T01` |
| `11` | `v` | `T00` | `T10` | `T01` | `T11` |
| `11` | `i` | `T10` | `T00` | `T11` | `T01` |

The canonical object-array digest, with keys
`h_old,h_recent,old_bit,twin_old,twin_recent,u`, is
`8593c0f7b57d01c59f30eb074353f6f988b23594bf6e25618ef0363b20edbb4b`.

For both sides of all eight cases, base value is one and all four
`J_REGISTERED_OLD_TRANSFORM_CUT` variants have value zero. It is insufficient
to test only removal of an arbitrarily labelled “old” item; module provenance
and bit role must match this table.

### F. First-accept recurrence

For the production `a=1/4` case, survival after caps 1--4 is
`3/4,9/16,27/64,81/256`. Conditional on acceptance by the cap, the unnormalized
first-accepted-at-attempt vectors are:

| cap | integer vector |
|---:|---|
| 1 | `[1]` |
| 2 | `[4,3]` |
| 3 | `[16,12,9]` |
| 4 | `[64,48,36,27]` |

The recurrence implementation must also pass a deliberately heterogeneous
two-class toy so it cannot apply Candidate B's production-only cap cancellation
as a general rule. With equal prior, `a(h0)=1/4`, and `a(h1)=1/2`, the posterior
integer weights `(h0,h1)` after observing acceptance by the cap are:

| cap | posterior weights |
|---:|---|
| 1 | `(1,2)` |
| 2 | `(7,12)` |
| 3 | `(37,56)` |
| 4 | `(35,48)` |

The combined vector is:

```json
{"attempt_weights_by_cap":[[1],[4,3],[16,12,9],[64,48,36,27]],"heterogeneous_posterior_h0_h1":[[1,2],[7,12],[37,56],[35,48]],"survival":[[3,4],[9,16],[27,64],[81,256]]}
```

Expected digest:
`8ba883f19c7c6fee04e42c9bc64488ef9359a65e684c53799a74253fab08d704`.
Every rational must be reduced, and recurrence, closed form, and brute-force
enumeration must agree exactly—never within a tolerance.

### G. State quotient and literal histories

The exact fixed-truth quotient key fields, in order, are:

```json
["position","remaining_actions","coolant_bits","item_status[4]","valve_mode","run_stable","terminal","failure_kind","necessity_mask"]
```

Expected digest:
`927ae08326f7341dc37db6a5798b7d8d8224beda8f6ce6b92e571f65457b1aca`.

An independent literal-history enumerator must agree with the quotient through
depth six for all 16 target/twin goldens, including reached-state sets, legal
actions, rendered successors, minimum values, and canonical tie breaks. Then
check the one-step closure argument for every action and every pair of states
sharing the complete key. For Bayes states, equality also requires the complete
reduced integer mass object, not only a possibly colliding or stale hash.

### H. Canonical record smoke vectors

At minimum, validate these independent `RecallGoal` bytes. The serialized file
adds exactly one LF; the digest is over the shown bytes before that LF.

```json
{"desired_coolant":{"inhibitor":"LEAN","viscosity":"HIGH"},"goal_handle":"GO000000000000","goal_kind":"ONE_APPLY_COOLANT"}
```

Expected digest:
`61ce382efad86108f7708d506d6ef7d447b26ffb713e64e46b22b9cb0504ec8b`.

```json
{"desired_coolant":{"inhibitor":"RICH","viscosity":"LOW"},"goal_handle":"GO000000000001","goal_kind":"ONE_APPLY_COOLANT"}
```

Expected digest:
`ed4e557cac54ab2cd1a2d08aebb9b95b0dbffbc98f58a3d5e966d2cf66f30f8d`.

Also reject unknown keys, duplicate keys, floats, nulls, non-NFC strings,
lowercase/short handles, a missing LF, or two LFs. The oracle must parse raw
input bytes before a generic JSON library erases duplicate keys.

## 4. Required mutation kills

The implementation review is not green until each mutation below causes the
named oracle failure. Mutations run only in an isolated disposable copy of the
subject and may never rewrite frozen evidence.

| ID | Mutation | Expected failure; a pass is evidence of a weak oracle |
|---|---|---|
| M1 | regress `tau_X` from identity to `r xor 10` | all 16 twin targets lose the registered two-bit/disjoint-pair/depth-nine property; target table or Cartesian-product assertion must fail |
| M2 | replace four balance rows by only the `mu,tau_V(mu)` modes | BE can still look balanced, so require the event totals to become the forbidden `[123,248,496,990]` and the action-only posterior to have support on only the revealed two-mode orbit (for `BYPASS/RECIRCULATE`, `[6,6,0,0]` rather than `[6,6,6,6]`) |
| M3a | derive a target handle from side metadata | H/twin target-visible byte collision must fail |
| M3b | derive a side-common handle from slot/cut/stratum/ordinal/proposal metadata | with a fixed injected target-handle tape, permuting all such metadata must leave the accepted handle sequence unchanged; identifier-only conditioning must not recover registry role |
| M4 | construct J from four current-module families, or place both useful setters in one era | the explicit eight-case inventory table must fail; at least recent-only or old-only succeeds, or old-transform variants 1--2 leave base success unchanged |
| M5a | ignore preceding rejection mass or treat first-accept position as uniform | the cap-2--4 attempt vectors must fail |
| M5b | cancel the proposal cap for every hidden class | the heterogeneous `(1,2),(7,12),(37,56),(35,48)` toy must fail |
| M5c | infer hidden registry role from target handles instead of summing `rho` | the M3b metadata permutation and handle-tape substitution tests must change the erroneous posterior |
| M6 | delete each quotient field in turn, or retain only a belief hash | literal histories must expose a collision with different legality, successor bytes, score, or necessity result; no deleted field may survive all witnesses |
| M7 | retain the affine grammar or rerun target selection inside `ATOMS_ONLY_COMPLETION` | WITNESS-GRAPH becomes greater than `1/4`, completion weights cease to be `[1,1,1,1]`, or target-visible hashes diverge |
| M8 | use a valve-sensitive bridge, a shared reset/object handle, or fewer than all eight bridge rows | the exact bridge result vector, certified-bypass assertion, reset independence, or enumeration count must fail |
| M9 | generate oracle goldens through the same subject functions being checked | change one subject constant and its generated fixture together; the literal vector digest in this file must still reject it |

For M3b, the complementary metamorphic test is also required: hold all metadata
fixed, alter one valid target-handle tape value, and require the corresponding
handle bytes to change. This distinguishes true tape consumption from a
hard-coded metadata handle.

For M6, require explicit collision witnesses for at least:

| Removed field | States that the incomplete key merges | Distinguishing check |
|---|---|---|
| `position` | LOCKER versus PLANT | ACQUIRE/APPLY legality |
| `remaining_actions` | one versus two actions left before RUN+COMMIT | attainable terminal value |
| `coolant_bits` | target coolant versus one-bit mismatch | RUN stable versus terminal trip |
| `item_status[4]` | cartridge in inventory versus consumed/locker | APPLY legality and successor |
| `valve_mode` | correct versus wrong mode | RUN stable versus terminal trip |
| `run_stable` | stable-run state versus otherwise identical pre-run state | COMMIT success versus failure |
| `terminal` | active versus terminal | every subsequent action's legality |
| `failure_kind` | `LOOP_TRIPPED` versus `ILLEGAL` terminal states | distinct public bytes and certificate replay |
| `necessity_mask` | base versus registered-cut state | J certificate disposition |

## 5. Stage-A implementation review checklist

### Frozen scope and entry

- [ ] The predecessor hashes above are verified before subject import or
  dispatch.
- [ ] Exactly one Stage-A public entry exists; it cannot name or dispatch Stage
  B, the 64-pair gate, network, model, GPU, trainer, adapter, or external code.
- [ ] The run uses one worker and records zero network/model/GPU calls.
- [ ] Failure is terminal and cannot change a filter, expected vector, cap, or
  threshold.

### Canonical bytes and schemas

- [ ] Raw duplicate-key and UTF-8/NFC checks occur before semantic JSON parsing.
- [ ] Every durable record is JCS UTF-8 plus exactly one LF; every content hash
  is over bytes before LF.
- [ ] Record key sets match Candidate B exactly; no implementation-only field
  enters a public or target-visible object.
- [ ] The two independent RecallGoal hashes and every vector digest in this
  oracle match.

### World algebra

- [ ] All 16 target cross-products, 32 sides, eight bridges, four omitted valve
  modes, four P completions, and eight J inventories are enumerated—not sampled.
- [ ] `tau_C` and `tau_V` are fixed-point-free involutions and `tau_X` is exact
  identity.
- [ ] Target pairs are unique within side, disjoint across twins, depth nine,
  and use distinct correct modes.
- [ ] Bridge resets are fresh, public, certified-bypass exchanger-bench states.
- [ ] Four-mode balance passes both complete BE equality and action-only
  `[6,6,6,6]`; neither check substitutes for the other.

### Target construction and handles

- [ ] J inventories contain exactly two old-bit setters from the old module and
  two other-bit setters from the recent module in all eight cases.
- [ ] All four J cuts are evaluated on both sides and return zero.
- [ ] P deletes only the schema/grammar and omitted edge; it does not rerun
  selection or use the realized law.
- [ ] Target handles consume an independent injected tape after acceptance,
  are copied across twins, and pass both metadata-permutation metamorphics.
- [ ] No handle is derived from protocol hash, pair, slot, cut, stratum,
  ordinal, side, proposal counter, or hidden truth.

### Exact probability and planning

- [ ] First-accept recurrence, closed form, and brute force agree as reduced
  rationals for caps 1--4.
- [ ] The heterogeneous-acceptance toy passes, proving cap cancellation is not
  applied outside its premise.
- [ ] No float, tolerance, pruned positive mass, approximate posterior, or
  sampled Bellman action is present.
- [ ] Literal-history and quotient results agree through depth six on every
  target/twin; one-step closure covers every legal action.
- [ ] Each quotient-field deletion mutation is killed with a preserved witness.
- [ ] Compact certificates replay from target bytes and truth/ablation hash;
  they are not accepted merely because a stored root hash matches.

### Evidence and resources

- [ ] The report lists every fixture count, expected/actual digest, mutation
  disposition, state/transition count, and first failure without omission.
- [ ] Stage A stays within 60 seconds, 512 MiB RSS, 50 MiB temporary bytes,
  25 MiB sealed bytes, one worker, and two million transitions.
- [ ] Counters are checked before dispatch; a limit hit is a nonpassing receipt,
  never a partial pass.
- [ ] Final labels say only `CPU_STAGE_A_INSTRUMENT_CONFORMANCE`; forbidden
  learning, benchmark, paper, native-context, developmental, LoRA, and
  promotion language is absent.
- [ ] No Stage-B artifact, input release, model artifact, or GPU artifact is
  created by this oracle review.

## 6. Decision rule

Stage A is review-green only when every literal vector, full enumeration,
metamorphic independence check, quotient comparison, mutation kill, canonical
byte check, and resource/scope gate passes in one sealed run. Missing evidence
is failure, not “not applicable.” A green result may be handed to the authorized
supervisor as Stage-A conformance evidence; this oracle itself does not release
or execute Stage B.
