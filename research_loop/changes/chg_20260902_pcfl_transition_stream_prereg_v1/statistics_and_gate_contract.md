# PCFL Transition-Path statistics and gate contract

Status: proposed P0/P1 preregistration only. P1 is a calibration/spending
decision with six fixed world-life/twin pairs. It supplies no population
estimate, confidence interval, paper result, benchmark confirmation, or claim
release.

## 1. Assigned units and denominators

The independent design unit is the whole `(pair_root, H, tau(H))` world-life
pair. P0 uses 32 fixture pair roots. P1 uses exactly six disjoint canary pair
roots and the six cross-era recent-depth patterns specified in
`world_contract.md`. Sides, two goal members, arms, cuts, reads, actions, and
provider responses are nested and never counted as independent `n`.

Every preassigned slot appears exactly once in the terminal ledger. Unsupported,
uncompiled, unreadable, duplicate, malformed, rejected, timed-out,
provider-failed, parse-failed, out-of-resource, and unexecuted-after-abort slots
remain in their original denominator. There is no per-item replacement,
resampling, favorable corpus admission, or complete-case analysis.

The coverage vector is reported per side and snapshot as
`(allocated, introduced, supported, compiled, readable, action_usable)`.
Compiler usefulness never controls inclusion.

## 2. Value functions

Per-target raw action value `V` is one only if all of the following hold:

1. the model output parses under the one registered schema;
2. no cap or visibility rule is violated;
3. the executor applies a legal sequence from the assigned start;
4. `COMMIT` occurs at the assigned goal within four moves and one commit.

Otherwise `V=0`; there is no partial credit for a correct plan string,
citation, prefix, first action, or reported goal. D1 and D4 target-only Bayes
references are exactly `p_1=1/2` and `p_4=1/16`. The descriptive normalized
value is `V_norm=(V-p_d)/(1-p_d)` with no clipping. Raw value is primary.

A goal-pair score is one only if both goal members have `V=1` and their first
executed actions differ. A crossed-twin directional score is one only if the
submitted path has `V=0` in the actual world and `V=1` when replayed without
modification in the memory-matched counterpart world. A cut effect is the
paired difference `V_sham - V_cut` on the same sealed target and pre-action
fork. Linked-versus-bag action differences and scan work are reported but are
not connected-memory evidence.

Pair summaries average all assigned nested slots with equal goal/side weight.
P1 reports the six pair summaries and exact integer counts; it computes no
standard error, p-value, confidence interval, posterior, or population claim.

## 3. P0 deterministic receipts

P0 is all-or-none and must emit these receipts from the future implementation:

| Receipt | Required exact property |
|---|---|
| `P0_R01_TOTAL_GENERATOR` | 32 fixture pairs, two sides, eight trees/side, 240 assigned source slots/side, all registered D1/D4-age templates, zero rejection/resampling/duplicate replacement |
| `P0_R02_TREE_AND_TWIN` | Full depth-four tree invariants; exhaustive 32,768-bit single-tree orbit; `tau(tau(H))=H`; same non-outcome public shapes and target bytes |
| `P0_R03_TARGET_PRIOR` | Holding target bytes fixed, all 2 D1 and 16 D4 decisive-bit action sequences occur exactly once; Bayes values `1/2` and `1/16`; six cross-era depth-position patterns balanced |
| `P0_R04_GOAL_PAIR` | Only goal ID differs; each pair has opposite correct first actions in H and in tau; exact fixed widths and byte lengths |
| `P0_R05_DEPTH_HEADROOM` | Unique shortest-path binding depth is exactly 1 or 4; no shorter alternate path; typed exact-public-graph controller value 1 itemwise under four reads/four moves/one commit |
| `P0_R06_RETRIEVAL_REACHABILITY` | Every supported atom is reachable by both `PREDECESSOR(child)` and `SUCCESSOR(parent,action)` with the same atom hash; each D4 reverse query after the first depends on the prior return |
| `P0_R07_BAG_AND_GRAPH_CONTROLS` | Exact graph and full-scan atom bag both give typed-controller value 1 on fully supported cells; bag stores no endpoint/adjacency index and reports every comparison |
| `P0_R08_CUTS` | Old, new, both, and age/depth/size-matched sham sets are presealed; complete decisive cuts break the exact controller; matching shams do not |
| `P0_R09_VISIBILITY_RESET` | Every forbidden-taint mutant is caught; all allowed-byte equality and sequential-order reset tests pass; zero undeclared live object remains |
| `P0_R10_RESOURCE_SCOPE` | P0 stays within every resource/path/capability cap; zero provider/network/GPU/training/LoRA call or object |
| `P0_R11_MINIMAL_REPRODUCIBLE_ARTIFACT` | Fresh checkout command regenerates generator vectors, public events, target/twin manifests, oracle certificates, reader results, cuts, scores, and a root-hash manifest byte-for-byte |

Any mismatch is P0 `STOP_INVALID`; P1 is not run. Passing P0 is construct and
software evidence only.

## 4. P1 arms and exact allocation

All P1 targets are cross-era D4. Each of six pair roots has H and tau sides and
one two-member goal pair, giving 24 core target instances. The target-blind
`WCANON-T1` corpus is built separately for each side and snapshot before any
target is exposed.

| Arm | Assigned target instances | Memory |
|---|---:|---|
| `A0_TARGET_ONLY` | all 24 | no memory and no reader |
| `A1_LINKED_AUTH_M1` | all 24 | authentic linked `M1` |
| `A2_LINKED_CROSSED_M1` | primary goal on both sides, 12 | opposite-side linked `M1` |
| `A3_LINKED_LAGGED_M0` | primary goal on both sides, 12 | authentic linked `M0` |
| `A4_FLAT_BAG_AUTH_M1` | primary goal on H only, 6 | authentic flat atom bag with counted scan |
| `A5_OLD_CUT` / `A6_SHAM_OLD` | primary goal on H only, 6 each | authentic linked `M1`, decisive or matched sham old-node removal |
| `A7_NEW_CUT` / `A8_SHAM_NEW` | primary goal on H only, 6 each | authentic linked `M1`, decisive or matched sham recent-node removal |
| `A9_BOTH_CUT` / `A10_SHAM_BOTH` | primary goal on H only, 6 each | authentic linked `M1`, decisive or matched sham four-node removal |

This is 114 assigned target episodes. The 24 target-only episodes permit one
model response each. The other 90 episodes permit at most four dependent
reader turns plus one final action-list response each: an absolute cap of 474
provider responses, 360 reader operations, and 570 executed target commands.
There is one attempt and no retry, fallback, repair parse, or target replacement.

`A4` is decisive for interpretation: if it matches linked text, stored links
are unnecessary for action on this canary; if it loses, the result is only an
interface/organization difference because scan work and access differ. The
exact public graph remains the P0 ceiling. Neither branch supports a learned
connected-memory claim.

## 5. Deterministic P1 request/stop rule

Define `S` as the six H-side primary-goal targets on which
`A1_LINKED_AUTH_M1` has `V=1`. P1 may end in
`REQUEST_FRESH_PAPER_WORLD_DESIGN` if and only if every condition below holds:

1. all P0 receipts passed and the later fresh independent code review returned
   `PASS_FOR_P1` on the exact implementation/manifests;
2. no identity, visibility, reset, parser, cap, resource, provider, or ledger
   violation occurred;
3. `A1_LINKED_AUTH_M1` succeeds on at least 20 of 24 targets;
4. at least 10 of 12 authentic goal pairs have goal-pair score one;
5. `A0_TARGET_ONLY` succeeds on at most 4 of 24 targets;
6. `A2_LINKED_CROSSED_M1` has counterpart-directional score at least 10/12
   and actual-world success at most 2/12;
7. `A3_LINKED_LAGGED_M0` succeeds on at most 4/12;
8. `|S|` is at least 5; each sham arm succeeds on at least `|S|-1` targets in
   `S`; summed paired `V_sham-V_cut` over `S` is at least 3 for old, at least 3
   for new, and at least 4 for both;
9. all 114 assigned episodes and their failures appear in the ledger and all
   P1 resource counters are within cap.

This rule is a spending heuristic, not a hypothesis test. `A4` is reported but
does not alter request eligibility. A request asks for a new material design
whose final paper world and construct are reconsidered; it does not request or
authorize LoRA on this transition tree.

If the run is valid but any numbered condition fails, the only outcome is
`STOP_TEXT_CAUSAL_USE_NOT_ESTABLISHED`. No threshold may be relaxed and no
failed cell may be rerun. If P0 or fresh review fails, the outcome is
`STOP_INVALID` before P1. None of these outcomes dispatches work.

## 6. Zero, structural absence, and `NOT_RUN`

- An assigned target is zero for missing support, missing/contradicted atom,
  compiler/read failure, invalid query, timeout, provider failure after P1 has
  begun, malformed output, illegal/extra move, wrong goal, absent commit,
  resource abort, or unexecuted remainder after an abort.
- `STRUCTURALLY_ABSENT` is permitted only for the preregistered D1 cross-era
  cell and is not included in a denominator that ever assigned it.
- Environment-wide `NOT_RUN` is permitted only when, before the first P1 model
  response, the pinned provider/model identity cannot be attested or a single
  global runner/environment fault makes every assigned P1 cell unavailable.
  The complete predispatch evidence is retained. There is no arm/item
  `NOT_RUN` after the first response.
- Exhausting a resource cap after any response is not `NOT_RUN`: completed
  items retain their values, every unexecuted assignment is zero, and the gate
  stops.

## 7. Exact claim ladder and review outcomes

These are evidence labels, not released claims:

- `C0_CONSTRUCT`: after P0 all-pass only, “One deterministic CPU
  implementation conformed to the finite registered transition, target-prior,
  twin, reader, typed-headroom, cut, visibility/reset, and resource contracts.”
- `C1_TEXT_CANARY`: after a valid P1 request outcome only, “On the six fixed
  calibration world-life/twin pairs, the pinned resolver used target-blind
  mechanically compiled transition text to execute the registered cross-era
  D4 action paths under the canary rule.”
- `C2_FIXED_SOURCE_ACQUISITION_RETENTION_ACTION_USE`: requires a future,
  powered, freshly designed and ratified study; P0/P1 do not establish it.
- `C3_PARAMETRIC_TRANSPORT_OR_LORA`: not run and forbidden in this change.
- `C4_PAPER_BENCHMARK_OR_SYSTEM`: not established; the transition world is a
  preflight, not the sole paper-defining self-learning or connected-memory
  benchmark.
- `C5_PLATEAU_EFFICIENCY_COMPRESSION_ON_POLICY_OR_SOTA`: explicitly forbidden.

Before any future claim release, a fresh reviewer must receive exact design,
code, raw failure-inclusive ledger, roots, resources, and reproduction steps
without author conclusions. The review must choose exactly one of
`APPROVE_NARROW`, `NULL`, `NOT_RUN`, or `REJECT`, map evidence to the prewritten
sentence, and preserve rejection authority. All four are valid review
outcomes. An advocate cannot override the verdict; repaired bytes require new
bound review. No review verdict itself grants implementation, successor,
promotion, or claim-release authority.

## 8. MAT01–MAT08 disposition

| Contract | Binding in this successor |
|---|---|
| `MAT01_FIXED_SOURCE_AND_PRESEALED_TARGETS` | Total pre-bit topology/age/target allocation; propensity-one source deck; immutable common side-life; distinct coverage denominators; assigned failures retained |
| `MAT02_DESCENDANT_VISIBILITY_TAINT_AND_RESET` | Full descendant table, metadata-taint closure, constant-shape rules, mutation suite, and object-by-object reset in `visibility_contract.md` |
| `MAT03_DEPTH_HEADROOM_AND_EDGE_NECESSITY` | Exact D1/D4 unique paths, exhaustive lower-depth check, typed controller value one, bidirectional atom reachability, bag/graph controls, and complete cuts |
| `MAT04_TEXT_GATE_AND_FRESH_CORPUS_INCLUSION` | One disjoint text-only P1 canary; all preassigned side corpora and failures enter their scheduled arms; no usefulness filter or automatic successor |
| `MAT05_SUBSTRATE_READER_AND_LORA_CAUSAL_PANEL` | LoRA/adapter/training is removed and forbidden. Linked-versus-bag reader attribution is measured; any future LoRA proposal must freshly register the full candidate-only, wrong/twin-adapter, unaided, authentic/twin, decisive/sham, paired-training panel before execution |
| `MAT06_PAIR_POWER_SPLIT_AND_GENERATOR_CONTRACT` | Six fixed disjoint pair roots; nested-unit semantics; exact raw/normalized values; no inferential/paper claim; conservative zero/NOT_RUN rules; no generator generalization |
| `MAT07_STAGED_PRIMARY_CELL_AND_RESOURCE_MANIFEST` | Exact P0 then fresh-review then P1 sequence, 114 arm assignments, absolute call/action/storage/time limits, terminal outcomes, and no full Cartesian or confirmation surface |
| `MAT08_REVIEW_OUTCOME_AND_CLAIM_SENTENCE_GATE` | Exact evidence sentences, raw reproduction, four valid review verdicts, non-overriding advocate, fresh review after repair, and no authority from technical outcomes |

The prior full-paper power, baseline-plateau, same-corpus LoRA, and confirmation
questions are resolved here by deletion from current execution scope, not by an
implied positive design. Reintroducing any of them is a new material change.
