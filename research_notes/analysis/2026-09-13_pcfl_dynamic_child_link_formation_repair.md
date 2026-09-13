# PCFL dynamic child-LINK formation repair

**Date:** 2026-09-13 PT  
**Status:** prospective, documentation-only implementation contract  
**Scope:** smallest repair after SEQ-171/172/173; no runtime/model/GPU work  
**Supersedes only:** the hidden or disclosed preselected `link_choices` seam in
OLD/NEW formation. The PCFL v2.2 world, writer, endpoints, controls, thresholds,
stage order, and claim limits otherwise remain unchanged.

## 0. Ruling

SEQ-171 showed the decisive bug: the child emitted a syntactically exact,
world-valid LINK, but the harness rejected it because it did not match a hidden
preselected pair. Disclosing the pair in SEQ-172/173 changed the opposite side
of the problem: the harness then selected the connection and the child merely
filled a requested row. Neither can support child-authored connection formation.

Use a **dynamic relation-set binder**:

1. Admit the child's eight exact EVENT rows from its public action/outcome
   history as before.
2. Before the first LINK call, mechanically derive and privately seal the set
   of every directly chained ordered EVENT pair in that admitted bank.
3. Ask only for “one not-yet-recorded directly chained pair,” supplying the
   next empty LINK address but no pair, candidate, shared node, receipt, route,
   goal answer, or correctness feedback.
4. Accept any member of the sealed valid set, in any child-chosen order,
   without replacement.
5. After four accepted OLD links, seal the **actual bank the child produced**
   and build all SLEEP/query material from those exact spans.

For every currently valid OLD history the relation set has exactly four
members. Requiring all four makes the endpoint order-invariant without
selecting a favorable subset. It establishes child emission of the complete
direct-connection set, not autonomous discovery of which connections matter.

## 1. Pre-output contract

Replace `build_plan(cell, actions, link_choices)` with an open-link plan such
as `build_plan(cell, actions)`. Keeping the already frozen EXPLORE curriculum
is the smallest repair; this memo does not claim autonomous action selection.

The independently retained plan may contain:

- the root/cell, exact OLD EXPLORE curriculum, public affordance schedule, and
  fresh EVENT/LINK address sequences;
- the literal target-free EVENT and LINK prompts and format-only decoder rule;
- `valid_pair_predicate_version = DIRECT_CHAIN_V1`;
- expected counts `8 EVENT`, `4 LINK`, then `1 EVENT + 2 LINK` per NEW branch;
- the fixed query grouping, control-derivation, replay, and scoring algorithms;
- hashes of sources, prompts, model/tokenizer, random tape, and root skeleton.

It must not contain an exact LINK pair list, expected LINK row, link-ID-to-pair
map, shared node, pair-specific receipts, future route, or private answer. In
particular, remove `link_choices`, `expected_bank` LINK fields,
`requested_preselected_already_admitted_event_handles_v1`, and
`requested_link_prompt` from the scientific path.

The current target-free one-line decoder may remain for this DEV if its exact
policy is receipted and the result is labeled **external format assistance**.
It may constrain only “one non-CR/LF line followed by LF”; it may not constrain
any identifier or field value. This preserves the existing narrow claim that
the semantic tokens are child-generated while making no learned-serialization
claim.

## 2. Exact dynamic admission

After eight EVENT admissions, define over the exact admitted rows:

```python
def valid_pairs(event_rows):
    return {
        (u.fields["event"], v.fields["event"])
        for u in event_rows
        for v in event_rows
        if u is not v and u.fields["destination"] == v.fields["source"]
    }
```

Require exactly four OLD pairs. Serialize the lexically sorted set only into a
private `valid_relation_set.json`, hash it, and close that artifact before the
first LINK request. Its bytes never enter a model request or training target.
The count/predicate were fixed before EVENT generation; the realized opaque
pairs are allowed to depend only on the admitted public history.

For LINK opportunity `i`:

1. Issue the generic LINK prompt with only fresh address `l_i`.
2. Preserve the whole raw model response, token IDs, finish state, timestamps,
   request/history hash, model identity, format-decoder receipt, and UTF-8 hash.
3. Parse the raw response without repair or normalization.
4. Require its LINK address to equal the fresh address.
5. Use the **child-supplied** first/second EVENT IDs to look up two already
   admitted exact EVENT rows and their actual public receipts.
6. Call the unchanged world admission predicate: first destination equals
   second source equals `VIA`; evidence IDs equal those events' receipts in
   first/second order; the pair has not appeared before.
7. Require the pair to belong to the privately sealed valid set. Record the
   accepted raw child span unchanged.

The compiler's lookup in step 5 is verification, not authorship: the child
chooses both IDs; the compiler neither proposes nor repairs them. Any malformed,
disconnected, reversed, duplicated, unsupported, or wrong-field line fails the
opportunity and the root. There is no corrective prompt, retry, alternate
decode, replacement root, or partial-bank fit.

At OLD completion require:

```text
accepted EVENTs = 8/8
accepted LINKs  = 4/4
set((first, second) of accepted LINKs) = sealed valid relation set
fresh LINK addresses = l0,l1,l2,l3 exactly once each
```

Then create `actual_formation_bank.json` from the eight exact EVENT spans and
four exact LINK spans in child order, seal it, and materialize the fixed memory
API from that bank. `formation_complete` means structural completion plus this
dynamic set equality; it no longer means equality to a preauthored LINK bank.

## 3. NEW formation after SLEEP 1

Use the same rule, not a special answer-aware path. After the child commits the
relevant experiment, receives its public result, executes the revealed port,
and authors the new EVENT, compute privately:

```text
valid NEW pairs = all direct chains in OLD + NEW admitted EVENTs
                  that include the new EVENT
```

Require exactly two such pairs. Privately seal their set before the first NEW
LINK call. Ask two ordinary generic LINK requests with fresh addresses `l4`
and `l5`; accept the two valid pairs in either order. The validator may access
the sealed OLD bank, but no OLD receipt, EVENT/LINK row, roster, memory-service
return, compiler state, candidate pair, or valid-set hash may enter the native
child context. Therefore every OLD identifier in a NEW LINK must come from the
mounted child's own parametric state.

Each of the four counterfactual continuations (two roots x two public R
outcomes) requires `1/1 EVENT`, `2/2 LINK`, exact set completion, and a sterile
context certificate. A failure is `VS_CHILD_NEW_FORMATION_FAIL`; no S2 fit is
created for that branch.

## 4. Binding SLEEP and controls to the actual bank

The post-formation binding is deterministic but necessarily occurs after the
child has authored the bank. This is not post-hoc selection because every
valid relation is required and every exact span is retained.

- `READ EVENT` and `READ EVENTS_AT` use the actual admitted EVENT spans.
- `READ LINKS_FROM` groups the actual admitted LINK spans by their child-chosen
  first EVENT and sorts them by their assigned LINK address.
- S1 must still materialize exactly 17 first response blocks; S2 exactly 19.
  Any different count is `VS_ASSAY_INVALID`, not a writer result.
- Build a hidden bookkeeping map from each actual LINK to one of the four
  predeclared structural relation roles. Use that map—not an assumption that
  `l0` means the left entrance, etc.—for EVENT_TWIN counterparts,
  `LINK_PERMUTE`, causal LINK cuts, cross-root joins, and report strata.
- In NEW branches, similarly map `l4/l5` by their actual relation role before
  constructing FULL_R0/FULL_R1 or cuts.
- The v2.2 output-blind replay algorithm remains rooted in the pre-output
  skeleton hash. Actual child text, opaque lexical order, link emission order,
  score, loss, or future outcome may not choose replay positions.

Every authentic training target remains an exact accepted child span or an
exact grouped/replayed occurrence of such spans. Parsing produces metadata;
it never produces target bytes. Synthetic TWIN/PERMUTE material remains
explicitly tainted, sealed, and barred from authentic lineage.

## 5. CPU/preflight gates before any model call

The implementation is not ready until all of these pass:

1. **Exhaustive order invariance.** Exercise both O values, both possible
   first-choice orders at the repeated `S_L` and `B` affordances, every `4!`
   OLD LINK order, both R values, and both NEW LINK orders: 768 complete
   synthetic formation sequences. Every valid sequence binds, yields the same
   structural relation set, and materializes 17 S1 / 19 S2 requests.
2. **Fail-closed mutations.** Reject a duplicate, reverse/disconnected pair,
   wrong VIA, reversed evidence receipts, unadmitted/cross-root EVENT, wrong
   fresh LINK address, missing/extra text, repair, and partial set.
3. **No hidden target surface.** Assert that actor requests contain no
   preselected pair list, expected LINK row, shared-node answer, pair-specific
   receipts, route answer, private role label, or post-output binding artifact.
4. **Chronology/custody.** Prove the valid-set file was closed after the eighth
   EVENT admission and before the first LINK request; prove each target hash
   joins one native child response and its cited public receipts; preserve all
   rejected/uncalled slots.
5. **Downstream order invariance.** For all 24 OLD orders and both NEW orders,
   independently replay query grouping, counterpart construction, LINK
   derangement, critical cuts, and v2.2 replay selection; semantic roles and
   denominators must be invariant even when LINK IDs attach to different
   pairs.
6. **No obsolete seam.** The production manifest, runtime, preparer, reducer,
   and tests must reject `link_choices`, public pair prompts, and equality to a
   preauthored LINK bank.

These are CPU/provenance tests. They neither authorize a run nor count as model
evidence.

## 6. Scientific progression and stopping

The order is unchanged, with this repair inserted at formation:

```text
CPU/collision/preflight gates
-> corrected supplied-memory THINK/READ C0 ceiling
-> one disposable dynamic OLD formation (20 calls, zero fits)
-> two untouched DEV dynamic OLD formations (20 calls/root)
-> S1 fits/evaluation
-> native reachout
-> four dynamic NEW continuations (4 calls/continuation)
-> S2 fits/evaluation
-> immutable one-shot reduction
```

The disposable root must achieve 8/8 EVENT and 4/4 dynamic LINK admission with
no retry before DEV roots are opened. Its output cannot be fitted into a DEV
lineage. On DEV, a root stops at the first failed formation or later existing
progression gate; a safe sibling may finish, but no replacement root is made.
Prompt, parser, decoder, dynamic predicate, or threshold changes after the
disposable result require a new protocol version and fresh untouched DEV roots.

The event-only SEQ-171 prefix diagnostic may remain a bounded storage
localizer. It cannot substitute for this dynamic full-bank formation, LINK
carriage, or the two-root vertical.

## 7. Exact resource arithmetic

Dynamic binding adds **zero model calls, fits, or optimizer updates**.

```text
OLD: 3 formations x (8 EXPLORE + 8 EVENT + 4 LINK) = 60 calls
NEW: 4 continuations x (1 EXPLORE + 1 EVENT + 2 LINK) = 16 calls
TOTAL FORMATION = 28 EXPLORE + 28 EVENT + 20 LINK = 76 calls

output maxima:
28 x 128 + 28 x 192 + 20 x 256 = 14,080 tokens
```

These 76 calls remain inside the registered 8,950 maximum actor-generation
transactions and 10 aggregate A40-hour DEV inference cap. The v2.2 writer
maximum remains 14 scientific DEV fits plus one mandatory LOW calibration fit
and at most one conditionally licensed HIGH fit: **15--16 fits, 3,000--3,200
updates, at most 8 A40-hours training, and 19--20 aggregate A40-hours for the
complete qualified vertical**. Failure removes unlaunched descendants and
never enlarges those maxima.

## 8. Permitted interpretation

Passing formation permits:

> Under a disclosed target-free one-line format scaffold, the child emitted
> every directly supported OLD connection from its own admitted public EVENT
> records, in its own order, and those exact spans—not compiler-rendered
> relations—became the sealed SLEEP bank.

It does not establish autonomous exploration, useful-subset discovery, learned
serialization, storage, traversal, or action improvement. Storage requires the
writer/readout gate. Connected utility requires AUTH over ATOMS plus the
endpoint-specific LINK cut or permutation on both DEV roots. The later S2
claim additionally requires sterile NEW formation, OLD retention, and
candidate-free OLD+NEW use. Lifetime improvement, strong-memory superiority,
generalization, recurrence, parenting, and compression remain downstream.

## 9. Implementation delta in one sentence

Delete the requested/expected pair map; parse the child's pair, validate it
against the complete direct-chain set derived from its admitted EVENTs, bind
all downstream state to the exact bank it actually authored, and keep every
existing no-retry, provenance, writer, endpoint, and resource gate.
