# Composition-birth Stage-0 source audit at `e28df7f3`

**Date:** 2026-09-13 PT  
**Scope:** fresh source-only audit of
`organism_v6/composition_birth_stage0.py` and
`tests/test_composition_birth_stage0.py` at helper commit `e28df7f3`. I ran
only the in-memory CPU unit test; I did not generate a material root, call a
model/tokenizer, fit an adapter, use a GPU, or inspect a sealed downstream
instance.

## Decision

**GO only as a deliberately incomplete, fail-closed tiny-interface source
fixture. NO-GO as Stage-0 closure, as a Stage-1 model runner, as GOAL-BRAID
source, or as M-COMBINE-4 material.**

The module labels itself correctly: `NO_GO_PARTIAL_SOURCE_ONLY`, disables all
non-tiny domains, emits zero birth units, reports the missing audits, and exits
nonzero. Preserve that negative status. It is useful source groundwork, but it
does not satisfy the Stage-0 GO condition and authorizes no materialization or
scientific execution.

Targeted check:

```text
python3 -m unittest tests.test_composition_birth_stage0 -v
11 tests PASS in 0.026 s
```

Passing those tests means the partial fixture behaves as authored. It does not
mean the bound Stage-0 contract passes.

## What is already sound

1. **Tiny topology and causal twins.** The source deterministically constructs
   16 two-corridor worlds and 32 paired goals. Each corridor has two edges;
   the paired tasks share the same world and differ in the goal.
2. **Constructive oracle.** The oracle reaches all `32/32` tasks using only
   START, GOAL, and exact public `READ EVENTS_AT` returns. It is not passed a
   hidden route. Arrival without exact `STOP` is not scored as success.
3. **Passive memory surface.** `READ EVENT` and `READ EVENTS_AT` are exact and
   target-blind; absent registered requests return literal `MISS`.
   `READ LINKS_FROM` is syntactically available and correctly returns `MISS`
   because this tiny family has no LINK bank.
4. **Strict local controller.** Malformed actions, invalid STEPs, truncation,
   and budget excess terminate without repair. The accepted action and world
   response are retained for successful turns.
5. **Several singleton shortcuts are balanced.** Constant action is `0/32`;
   lexicographic action, first displayed row, direct goal, local outdegree,
   LINK presence, and action position are each `16/32` under the authored
   assisted suffix.
6. **Quarantine is real.** Birth train, dose-DEV, confirmation, and writer
   domains raise rather than silently emitting provisional material. The
   report expressly says cross-domain intersections and forbidden-motif
   overlap are unverified.

No actor exists in this source, so there is presently no model-facing oracle
leak. That positive finding is limited to the tiny in-memory fixture.

## Blocking findings

### 1. Stage 0 is almost entirely unimplemented

Only `tiny_interface_dev` can be generated. There are no birth-train,
dose-DEV, untouched confirmation, writer-DEV, or release banks; no 256-unit
M-COMBINE root; no CLOSED/ATOM-LOCAL target coupling; no held topology/feature
combination; and no concrete identifier/text/core intersection audit. The
reserved names are not evidence of domain disjointness.

This is correctly admitted at source lines 59--69 and 330--347. It alone makes
Stage-0 closure **NO-GO**.

### 2. The registered shortcut gate fails and the pairwise suite is absent

`fixed_read_schedule` and `fixed_stop_depth` each score `32/32`, because both
retain the oracle's relation-based branch choice. The other singleton
policies also use an exact-row-assisted suffix. All 36 pairwise combinations
are merely enumerated as names and disabled; no pairwise policy or tie rule is
defined or executed.

That is not the bound requirement that every registered null execute and
score at most one-half. A READ schedule or STOP depth is not itself an action
chooser. It must either be paired prospectively with a target-blind action
chooser under exact tie rules, or be reclassified as an interface ablation and
removed from the shortcut-null gate by a new bound contract. It cannot remain
a nominal null that uses the oracle and scores perfectly.

### 3. The tiny graph is intentionally exhaustible

Three reads reveal the start and both child suffixes. That is acceptable only
for the Stage-1 interface/headroom sentinel. It cannot test learned SEEK or
M-COMBINE-4: a fixed exhaustive READ schedule observes the entire relevant
graph.

Stage-2A must separately guarantee more than 12 reachable addresses, at most
four sufficient reads, and paired panels on which exhaustive, fixed,
lexicographic, position, and read-all schedules remain at most one-half.

### 4. Public identifiers are derived from semantic slots

`identifier()` hashes `world_id/prefix/slot`, and EVENT/receipt slots are the
semantic edge enumeration. The world identifier also contains the factorial
cell index. This is deterministic, but it is not the GOAL-BRAID rule that an
independent opaque pool be permuted onto semantic roles and public addresses.

The full factorial protects several tiny-fixture marginals, so this is not an
observed tiny-panel shortcut. It is nevertheless unsafe to reuse in
GOAL-BRAID or richer birth material. Replace it before promotion with
independently presealed role-to-ID, role-to-address, row-order, formation-order,
and training-view permutations. No semantic slot or crossing-coded cell index
may be the public-ID input.

### 5. The topology certificate is too weak

`decision_core()` canonicalizes only the fixed two-corridor graph and reports
two depth-one signatures. It does not enumerate radius-0 through radius-3
rooted projections, target/action contingency tables, Bayes-best collision
groups, route labels, or the surface pairs required by GOAL-BRAID. It also
cannot establish train/dose-DEV/confirmation non-isomorphism because those
domains do not exist.

For M-COMBINE, add target-action tables against identifier tokenization,
bytes/tokens, character and display position, goal side, depth, family, skin,
flow class, and every predeclared pair. The decisive protection must remain
the held single-variable SEEK/PROSPECT/CHECK/CONTINUE-STOP pairs.

### 6. Custody drops failed attempts

`Session.receipts` is appended only after a valid completed turn. Malformed,
invalid, truncated, and over-budget raw attempts disappear; the tests
currently assert that disappearance. Fail-closed scoring is correct, but
lossless audit custody is not.

Add an immutable attempt ledger written before validation containing exact raw
bytes (or typed non-string representation), generated-token declaration,
truncation flag, parser disposition, pre/post state, response bytes, and
terminal reason. Keep accepted world receipts as a distinct field. Invalid
attempts must remain failures while still being auditable.

### 7. Manifests are summaries, not custody manifests

The report hashes prompt and concatenated row bytes, but omits the complete
task structures, correct routes/actions, exact query registry and response
map, null traces, collision groups, raw oracle trace, source/code hash,
generator/config hash, namespace inventories, and parent-child artifact
lineage. There is no exact-byte root manifest because no root is emitted.

Before Stage-0 GO, emit a canonical manifest covering every generated object
and its hash, plus a separate immutable custody receipt. Recomputing the same
summary from the same implementation is not independent verification.

### 8. Tests are good regressions for the partial code, not an independent checker

The tests import the generator, oracle, service, and `decision_core()` they
are supposed to validate. They do not implement an independent topology or
scorer, execute any pairwise null, attack joint surface cues, validate richer
domains, test cross-domain intersections/motifs, or verify exact cut/mount
collisions. The test that checks the null report explicitly expects the two
perfect-score nulls and 36 disabled pairs, so it certifies fail-closure rather
than scientific validity.

Build a second checker that consumes only the canonical material manifest and
does not import generator helpers. Both implementations must agree on every
task, legal path, score, projection, null, cut, mount, registry return, and
hash before material can be called closed.

### 9. No Stage-1 actor runner or real token accounting exists

The source accepts direct strings and synthetic `generated_tokens`; it has no
frozen model wrapper, seeded decode tape, raw output envelope, tokenizer count,
or actor-call custody. The report correctly says token totals are synthetic.
Thus it is not yet the authorized 32-rollout Stage-1 base assay.

When that runner is authored, bind one wire convention. This tiny parser
requires exactly one terminal LF, whereas the GOAL-BRAID active-reader
amendment specifies one-line actor output with no CR/LF. The tiny sentinel may
keep LF if its own contract says so, but shared parser code must not silently
serve both conflicting conventions.

## Exact repair sequence

1. Keep this module quarantined as the tiny Stage-1 **source fixture** and
   retain its current nonzero/NO-GO report.
2. Define executable target-blind singleton and pairwise null policies with
   complete tie rules. Resolve fixed-READ/fixed-STOP classification rather
   than letting them call the oracle.
3. Add the independent manifest-only checker and lossless raw-attempt custody
   before any model runner.
4. Add the Stage-1 base runner with exact output envelope, decode seeds,
   tokenizer accounting, returned-byte/token accounting, and immutable raw
   traces. This remains a sentinel, not M-COMBINE evidence.
5. In a separate richer Stage-0 generator, implement the bound M-COMBINE-4
   `CLOSED` versus `ATOM-LOCAL` material: 64 cases x 4 targets, exact target
   coupling, non-exhaustible service, four held causal intervention panels,
   held topology combination, and full domain/motif separation. Do not revive
   the superseded LINKED/UNLINKED claim.
6. If GOAL-BRAID is later authored, use its independent opaque role/address
   permutations, authentic OLD/NEW chronology, grouped cuts, coherent mounts,
   common active READ interface, radius-0--3 projection certificate, and exact
   child-custody rules. This tiny graph is not that source.

## Final gate

Accept `e28df7f3` as honest, useful partial groundwork. Do not relabel its
passing unit tests as Stage-0 certification, do not materialize downstream
birth roots from it, and do not launch Stage 1 or Stage 2 on its authority.
The next source review can become GO only after the null suite, independent
checker, custody, and relevant domain generator exist and the report itself
changes from fail-closed for evidence-backed reasons.
