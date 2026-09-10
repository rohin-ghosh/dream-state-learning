# Exact visible-policy capacity certifier design

Date: 2026-09-04  
Status: read-only scientific/design audit; not implementation, consensus,
ratification, or GPU authorization

## Result

For the current selected manifest and current `rml_d0`/`rml_stage_b`
semantics, the exact registered-side capacities are:

| arm | registered sides | exact capacity | lower-bound witness |
|---|---|---:|---|
| `NONE_REC` | `J_H`, `J_TWIN`, `P_H`, `P_TWIN` | **1/4** | the `J_H` nine-ENV plan |
| P `ATOMS_REC` | `P_H`, `P_TWIN` | **1/2** | the `P_H` nine-ENV plan |

These are integer maxima for one shared deterministic visible-history policy.
They are not probabilities, model outcomes, population estimates, or empirical
gates. In particular, the unchanged empirical `P ATOMS_REC = 0/2` predicate is
not a structural zero ceiling.

The current `build_slice_certificate` happens to return the two correct
integers, but it does not certify them for the required policy class.
`_best_fixed_capacity` intersects hashes of fixed shortest action sequences;
that is open-loop enumeration. It neither permits authorized branching after
visible histories diverge nor proves that no such adaptive policy can solve
more sides. Its witness is only a digest, not a replayable policy table, and
`planner_enumerator_agree` checks depths/tie counts rather than an upper bound.
Also, taking the maximum over multiple visible `ATOMS` classes would be wrong:
a single policy may select different actions on different visible histories,
so values of initially distinct classes add. The current P slice has only one
class, which hides that defect.

## Authority and exact domain

The certifier must hash-bind and then use without substitution:

- the already committed selected-side manifest and arm mounts;
- `rml_d0.world` transition, public-action, public-target, and terminal
  semantics;
- the Stage-B operation parser, exact four-READ then nine-ENV phase machine,
  public-state renderer, memory service, and mounted snapshot bytes;
- the authorized model-visible observation function and exact success
  predicate.

For this audit, the important current hashes were:

```text
rml_d0/world.py      7b3911dac851c9c1614287e2af7f46c6a656ae26c4e24a9c172b70f2fb91eb52
rml_d0/planner.py    6cf63009ba50c4f29d50f9e47d83d52395c184a8e24b48be4671d491443fe812
rml_stage_b/contract.py c6f3546419269b687e145fe72d75dc4afbcf8026ad8b0160f68b88a6c71bfd63
rml_stage_b/fixtures.py 9d4fc24fbb59db336119aa349509a9c2a074af737c6d826f730e98f1a07ccc19
rml_stage_b/machine.py  36d364f9ffc9efc8e7312d5b0a48a8f852f9504c80cd4ba37cb8f33a7493b804
rml_stage_b/memory.py   95582319f53c4b03932da2d3c9ce4c1fe3596095ef2048291cccca8ee76d876c
rml_stage_b/reducer.py  7c4c4250cafa28dc127ff04e4e55543d7990c1f376abfff4eb12f1c7f2d5a657
```

The hash list is an audit observation, not a ratification. A future executable
certificate must bind the complete dependency closure, not just this summary.

For arm `A`, let `S_A` be its fixed registered side set. Define

```text
K_A = max over one deterministic policy pi of
      |{s in S_A : exact frozen replay of pi on s is
                    SCIENTIFIC_VALID_SUCCESS}|.
```

`pi` maps each complete byte-canonical authorized visible history to one next
phase-valid output. The history includes the public target and initial state,
slot and phase, emitted READ keys and ENV actions, exact returned
row/status/handle, ordinary result codes/text/state, and controller-authored
scratch/citations. It excludes side identity, hidden transforms, valve truth,
score, candidate work, reducer state, capacity results, and witnesses. One
mapping is replayed unchanged on all sides. Equal history bytes must receive
equal output bytes; different outputs are permitted only after authorized
history bytes differ.

There is a renderer detail that an implementation must close explicitly:
current `RmlActionMachine.model_visible_value()` preserves an ENV
`action_record` but, for a READ, preserves only `operation_kind`, not the
emitted key. The architecture critique requires emitted keys in the complete
history. The certifier should therefore maintain an explicit append-only
controller history `H` containing every emitted normalized operation and every
authorized response, and check that the eventual runtime renderer provides the
same perfect-recall distinction. It must not silently equate “current rendered
input” with the architectural history if their bytes differ. This omission
does not alter the numerical result below because READ never splits a current
arm and the compatibility computation fixes the same READ prefix on every
side, but it must be resolved before a production certificate claims exact
policy-class equivalence.

Success is the Stage-B/D0-owned terminal condition, not mere reachability of a
convenient `GameState`: four valid READ returns occur first; exactly nine ENV
slots are available; the ninth ENV action is applied; and success requires its
legal `COMMIT`, `COMMITTED`, D0 `state.success`, and Stage-B
`SCIENTIFIC_VALID_SUCCESS`. Early `STOP`, trip, bad/early commit, malformed or
wrong-phase output, illegal action, fifth READ, or other terminal invalidity is
not success. READs do not consume an ENV action.

### Scratch and citations

The literal scratch alphabet is large but adds no exogenous information.
Scratch and citation strings are selected by the same deterministic policy,
are echoed into later visible history, and are ignored by the memory return,
D0 transition, action legality, and the structural terminal predicate. Thus
every successful policy has a capacity-equivalent normal form with canonical
JSON encoding, `scratch=""`, and `citations=[]`: reconstruct the original
self-authored fields internally from its deterministic prior history and emit
the same READ keys and ENV actions. This changes no external observation or
world transition. The certifier may therefore enumerate only this normal form.

This normalization is valid only for this structural capacity. Citation
minimality and return-before-use are separate post-freeze intervention-reducer
properties and must not be smuggled into, or used as an oracle by, the capacity
calculation. Conversely, a certifier must reject any implementation that lets
scratch/citations depend on hidden side at a byte-identical visible history.
Malformed and noncanonical variants are represented by one absorbing
nonsuccess output because none can improve capacity.

## Reference exact joint-history dynamic program

The most direct exact algorithm reuses the production transition semantics but
keeps all hidden state strictly inside the offline evaluator.

Represent a replay as `(side_id, exact_machine_state, H)`, where `H` is the
append-only canonical controller history described above. After each advance,
append the emitted normalized operation, exact authorized return or environment
feedback, and next public rendering. Compare `H` as bytes, not by hash alone.
Initially partition the registered sides by exact initial `H`. This is
important: an initially visible distinction permits different policy actions,
while a hidden distinction does not.

At a node `N=(H, R)`, all replays in `R` must be nonterminal and have the same
complete observation/history bytes `H`. Enumerate the closed output alphabet:

- in each of slots 0--3, every exact `READ(key)` whose key is in the current
  authorized `allowed_keys`; the checker verifies that the allowed-key set is
  equal across the byte-equal group;
- in each of slots 4--12, every one of the 23 exact public action records from
  the closed D0 action universe, even if an action sacrifices some sides;
- one canonical absorbing invalid output covering all malformed, oversized,
  wrong-phase, or otherwise non-success-improving outputs.

For each output `o`, apply the exact Stage-B machine separately to every side
in `R` with that arm's sealed memory service, append the authorized transcript
bytes to `H`, count terminal successes, and partition nonterminal successors by
their new exact `H`. Then compute

```text
V(H,R) = max_o [ terminal_successes(o)
                 + sum_{B in exact_visible_partitions(o)} V(H_B, R_B) ].
```

Terminal leaves return their success count. The arm value is the sum of `V`
over distinct initial visible-history groups. The maximizing output plus the
maximizing child choices form one shared lower-bound policy table. Branch
tables are unioned only after checking that no exact history byte string is
assigned two outputs.

Pseudocode:

```python
def value(group):
    assert group and all(not r.machine.terminal for r in group)
    h = group[0].controller_history_bytes
    assert all(r.controller_history_bytes == h for r in group)
    best = (-1, None, None)
    for output in exhaustive_normal_form_outputs(group):
        done = 0
        buckets = {}
        for replay in group:
            nxt = exact_advance(replay, output)
            if nxt.machine.terminal:
                done += int(exact_structural_success(nxt.machine))
            else:
                h2 = nxt.controller_history_bytes
                buckets.setdefault(h2, []).append(nxt)
        children = [value(bucket) for bucket in buckets.values()]
        candidate = done + sum(child.value for child in children)
        best = max_by_frozen_tie_rule(best,
                                      (candidate, output, children))
    emit_node(h, group, all_candidate_values, best)
    return best

capacity = sum(value(g).value for g in partition_by_initial_visible_bytes(sides))
```

Do not memoize by current D0 state or current observation alone. Two nodes with
equal current public state but different earlier visible bytes are distinct to
a history-dependent controller. Safe options are (1) no cross-history merge,
or (2) memoization keyed by the complete canonical history bytes plus the exact
ordered evaluator replay states. Any stronger quotient needs its own
machine-checked bisimulation proof.

### Why this proves both bounds

The selected argmax actions and recursively selected children give a concrete
policy. Replaying that one table on every registered side proves the lower
bound and records the complete visible histories, operations, public
transitions, terminal dispositions, and success vector.

For the upper bound, use induction on remaining slots. At a leaf the recorded
success count is exact. At an internal shared-history node, every admissible
deterministic policy must choose exactly one member of the exhaustively checked
normal-form output alphabet. The exact simulator determines its successor
visible partition. Once histories differ, policy choices on the child
histories are independent, so child maxima add; while histories remain equal,
they remain one node and are forced to share an output. Taking the maximum over
all current outputs therefore bounds every policy and is attained by the
stored argmax. Induction yields exact `K_A`.

An independent checker must reconstruct every node from the bound inputs and
reject a certificate with a missing/extra action, hidden-dependent split,
incorrect exact-byte partition, duplicate history with conflicting actions,
wrong transition, wrong terminal disposition, wrong candidate total, or wrong
maximum. Hashes commit artifacts, but equality/partition checks operate on
canonical bytes so a hash collision cannot authorize branching.

## Smaller exhaustive certificate for the current slice

The generic DP is conceptually simple but has a loose exponential bound. The
current fixture admits a much smaller certificate that is still exact for the
full history-dependent policy class.

1. **Prove READ non-splitting.** Exhaustively unfold all four READ slots for
   each arm. There are eight initial authorized public query anchors and no
   returned `next_key` in these mounted rows. At every reachable shared READ
   history and every legal key, replay on every registered side produces
   identical next visible bytes and identical next allowed-key sets. `NONE_REC`
   mounts the same empty service on all four sides; P `ATOMS_REC` mounts the
   same presealed `H:ATOMS` snapshot on both P sides. Thus no READ policy can
   learn side identity. Any one canonical four-READ prefix can be used for the
   witness without restricting the upper bound.
2. **Enumerate every single-side successful ENV trace.** Define an exact
   finite-horizon `Good(machine, remaining_slots)` recurrence over all 23
   public action records and exact Stage-B advance/terminal semantics. Enumerate
   only edges whose successor remains `Good`; this is exact pruning, not use of
   hidden information by the policy. Independently verify D0 minimum depth is
   nine. Therefore every successful nine-slot trace is a shortest path and no
   diagnostic `OBSERVE`/`MEASURE`, redundant move/configure, illegal action, or
   premature terminal can occur in one.
3. **Record exact predecision histories.** For every successful trace `t` on
   side `s`, record the nine pairs `(H_{s,t,j}, O_{s,t,j})`, where `H` is the
   exact append-only authorized controller-history bytes immediately before ENV
   decision `j` and `O` is the canonical normalized ENV output.
4. **Solve compatibility, not signature intersection.** A set of successful
   traces, at most one per side, is jointly implementable by one deterministic
   history policy iff the union of all recorded pairs is a function:

   ```text
   H_a == H_b  implies  O_a == O_b.
   ```

   Different action sequences are allowed when their prior authorized
   histories differ. Search side subsets from largest to smallest and choose
   one successful trace per side with backtracking/SAT. A compatible tuple is
   a lower-bound policy; exhaustive failure of every tuple for every larger
   subset is an upper-bound certificate.

Completeness is immediate: the replay of any policy that succeeds on side `s`
must induce one member of the exhaustively enumerated successful trace set for
`s`, and determinism makes the induced tuple compatible. Conversely, a
compatible tuple's union is a policy on all reached histories and may be
completed arbitrarily elsewhere.

This is strictly more general than open-loop enumeration. Open-loop signature
intersection requires the same nine actions across sides even after their
visible feedback differs. Compatibility requires the same action only while
the complete visible histories are equal. A two-side toy mutation with a
shared first action, distinct authorized feedback, and side-specific successful
second actions must score 2 under this checker but at most 1 under an open-loop
enumerator.

## Independent CPU scratch result

A provider-free CPU script, kept out of production files, used the current
builders and exact machine to inspect the selected cases and then performed an
independent successful-trace/visible-history compatibility search. It found:

```text
closed ENV public-action alphabet: 23
initial authorized public query anchors: 8
all four public target byte strings: identical

side       hidden transforms  useful pair  valve truth  min depth  success traces
J_H        (0,1,2,3)          (1,3)        BYPASS       9          12
J_TWIN     (1,0,3,2)          (0,2)        RECIRCULATE  9          12
P_H        (0,1,2,3)          (1,3)        RECIRCULATE  9          12
P_TWIN     (1,0,3,2)          (0,2)        BYPASS       9          12

NONE: 0 compatible successful trace-pairs out of 6 * 12 * 12 = 864
P:    0 compatible successful trace-pairs out of 1 * 12 * 12 = 144
```

The 12 traces per side are the two orders of acquiring its unique useful pair
times the six orders of its two APPLY operations and required CONFIGURE.
Exact minimum depth 9 excludes every other successful shape.

The `J_H` plan, with any canonical four-READ prefix and empty
scratch/citations, replays under `NONE_REC` as:

```text
J_H       SCIENTIFIC_VALID_SUCCESS     (ninth ENV is COMMITTED)
J_TWIN    SCIENTIFIC_VALID_NONSUCCESS  (RUN_TRIPPED at ENV 8)
P_H       SCIENTIFIC_VALID_NONSUCCESS  (RUN_TRIPPED at ENV 8)
P_TWIN    SCIENTIFIC_VALID_NONSUCCESS  (RUN_TRIPPED at ENV 8)
```

This proves `K_NONE >= 1`. Since no successful trace pair is compatible, no
policy can solve any two sides, proving `K_NONE <= 1`. Hence `K_NONE = 1/4`.

The `P_H` plan analogously succeeds on `P_H` and trips on `P_TWIN`, proving
`K_P >= 1`; the 0/144 compatible-pair result proves `K_P <= 1`. Hence
`K_P = 1/2`.

The upper bound is not being inferred from useful-pair inequality alone. It is
the exact compatibility result over every successful trace and the exact
authorized history bytes. The useful-pair/valve table is explanatory context.

## Complexity

For the generic DP, with `n` registered sides, per-slot normalized output
bound `A`, and `T=13`, a conservative no-quotient bound is exponential,
`O(n * sum(A^t, t=0..T))` transition replays, with exact histories retained.
Separating phases gives
`O(n * (sum(R^t, t=1..4) + R^4 * sum(E^t, t=1..9)))`, where currently
`R=8` and `E=23`. Terminal and exact-reachability pruning reduce this greatly,
but must never alter the proved output closure.

For the current specialized certificate, READ non-splitting costs
`O(n * sum(R^t, t=1..4))` exact replays (28,080 side-key replays across the
four-side and two-side arms at `R=8`). Let `N_s` be the number of successful
ENV traces for side `s`; here every `N_s=12`. General compatibility
backtracking is `O(sum_{U subseteq S} product_{s in U} N_s * 9)` in the worst
case. Once a one-side witness exists, proving the upper bound 1 needs only all
pair tests: 1,008 trace-pair comparisons, each of at most 18 history/action
pairs. The input size is tiny and CPU-only.

## Required certificate contents

The emitted evaluator-only artifact should contain:

- complete input/dependency hashes and selected-manifest commitment;
- exact arm, side denominator, observation schema, normal-form proof version,
  READ/ENV alphabets, and success predicate identifier;
- READ non-splitting forest or full DP nodes;
- per-side complete successful-trace lists with exact visible transcripts and
  terminal replay records;
- compatibility search order, every rejected larger-subset tuple or a compact
  independently checkable SAT/branch proof, and exact upper value;
- one serialized shared policy table, frozen tie rule, full replay on every
  side, and lower-bound success vector;
- separately named structural capacity and empirical gate fields;
- checker version/hash and mutation-test results.

The certificate, policy, hidden states, scores, and capacity are evaluator-only
after store and manifest commitment. They must be unreachable from builder,
selector, prompt, resolver, online service, cache/KV state, query returns,
execution order, or timing. Capacity must not cause candidate reselection.

## Mutation suite

At minimum, the certifier and independent checker must reject or correctly
recompute all of the following:

1. **Side reorder/swap:** capacity is invariant and the witness success vector
   follows side identity, proving no list-position oracle.
2. **Forbidden hidden bit:** append side/truth/capacity to visible history. The
   authorized-observation hash/schema check must reject it; it may not silently
   raise capacity.
3. **False merge:** delete an earlier visible byte or merge on current D0 state
   only. Exact-history partition checking must reject the quotient.
4. **False split:** assign different actions to byte-identical histories or
   inject side-dependent scratch/citations. The shared-policy checker rejects
   the conflicting table.
5. **Authorized adaptive branch:** in a tiny synthetic machine, make a common
   action produce two different public observations followed by distinct
   successful actions. Full policy capacity must be 2 while open-loop capacity
   is 1.
6. **READ return change:** alter one side's returned row/status/handle or add a
   `next_key`. The dependency hash must fail; under an explicitly mutated test
   authority the exact READ forest must split only on the changed visible
   bytes and recompute capacity.
7. **Feedback change:** mutate result text/code/public state before a decision.
   Hash binding and exact transcript replay must detect it; a sanctioned
   mutation may change compatibility only through that visible byte change.
8. **Extra diagnostic action or tenth ENV:** action-budget/phase binding must
   reject it. Removing a required action must continue to be justified by the
   exact `Good` recurrence, never a heuristic dominance list.
9. **Fourth-return/ninth-action semantics:** hide the fourth READ return, allow
   a fifth READ, fail to apply ENV 9, or credit early D0 state reachability.
   Exact machine replay must reject each mutation.
10. **Scratch/citation oracle:** make transition, return, or success depend on
    a self-authored field or reducer-only citation result. Normal-form
    preconditions fail and capacity certification stops.
11. **Corrupt witness:** alter one action, returned row, history byte, terminal
    disposition, or claimed success vector. Replay fails the lower bound.
12. **Corrupt upper certificate:** omit an action/trace/tuple, change a child
    partition/value, duplicate a history with another output, or change the
    reported max. Independent exhaustive checking fails.

## Audit disposition

The amendment's expected numerical repair is mathematically supported:
`NONE_REC` is exactly 1/4 and the selected P `ATOMS_REC` slice is exactly 1/2
for the current bytes. Production should not claim those exact bounds from the
existing fixed-signature fields. It needs the full history-policy DP or the
equivalent complete successful-trace compatibility certificate above, plus an
independent checker. This design note does not modify intake state, adjudicate
the amendment, ratify bytes, authorize implementation, or authorize any model
or GPU call.
