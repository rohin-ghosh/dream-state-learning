# Fresh audit: Stage2A metadata complexity and the smallest valid leak boundary

**Date:** 2026-09-14 PT  
**Role:** fresh scientific-efficiency reviewer  
**Scope:** current CPU source/scanner path only; no source edit, materialization,
model/tokenizer call, fit, GPU use, or scientific result.

## Verdict

**REWORK the full-object semantic-alias scan before the reduced 560-call
controller screen.** The complete source must remain in custody, but repeatedly
turning that source into a multi-megabyte alias-generating tree is not
scientifically necessary for target blindness. It is a provenance object being
used as a lexical blacklist. Those are different jobs.

The current path is not merely expensive. It is not total over its own source
population: the adopted `birth_full_v1` profile permits 131,072 scalar leaves,
while fresh read-only measurements of p00 and p01 produce 198,119 and 199,393
leaves. Increasing the limit again would make the implementation run, but it
would not make the scan more causal.

The smallest valid replacement is a **three-object boundary**:

1. one complete, content-addressed source/custody object per case, retained for
   reconstruction and independent checking but not atomized into scan needles;
2. one small per-arm/per-decision boundary receipt binding the exact public
   projection, target, retained history, source identities, core, and future-ID
   set; and
3. one typed leak basis containing only exact target/future/private values and
   the finite route automaton, with occurrence-level public-field receipts.

This is a prospective contract change. V3 section 8 explicitly requires the
twelve-root exhaustive alias ledger, so the Builder must not silently call the
reduced basis equivalent under v5. The present `source_semantic_occurrences`
path may remain a diagnostic, but it should not be promoted into the native
admission gate.

## Evidence inspected

The binding authority is Stage2A v5, file SHA-256
`6ebefdba31de6f14416105c9509dbba06319f306bdd3472259a8d072ba9877e7`,
with fresh audit SHA-256
`34a29185d57c0b5aa78ca9ed990b5897e3b4e94a8e7dacff1731eedb2048287b`.
The selected critical-path memo has SHA-256
`bc17448f0106909970b4550e9b806b74854d781c4b97b189c536c768fa30b14d`.
The current core binding has SHA-256
`04b214f3ade98bc9f1464a869791def711beaf3b143af4ca51d70f43e82250ff`.

I inspected the committed Stage2A source through `50b2b60a` and the following
uncommitted Builder files on the Astra helper at checkout `f2d92389`:

| object | reviewed SHA-256 |
|---|---|
| `composition_birth_stage2a_metadata_inputs.py` | `27bb7ee16af4f36015360497b3476bea2f859913ad250b3a7e681dceaffc081c` |
| `composition_birth_stage2a_inventory.py` | `029dbb1358c072fa45463c35506401cb43c813533a21dc0a97c72c6bf844f422` |
| `composition_birth_stage2a_scan_inputs.py` | `ba32b0b554bbed317e920e4cb90584de3f74cdcf86a32a8c56b83e3af52fff28` |
| `composition_birth_stage2a_scanner.py` | `30006dab934ffa5afbf108b1749bbc10c71b254d078abac8d87f55ba0de2926d` |
| `composition_birth_stage2a_route_scan.py` | `cbaaa5de9bb5389b91ed8754330b951c40473c4cfc8c612909fa1d04f35582b1` |
| `test_composition_birth_stage2a_source_occurrences.py` | `7cf18bd1a2b6fe18fc16c5cc26bb1d62ef7379eb2b623160cc9ea08067ee7159` |
| complete metadata schema memo | `e540a4650c8619160c915d3fd70759c38f0e8abc35982dbc2c8be1043dbe08c6` |
| integration-progress memo | `83ccf36d64ad0e28dafa1da68184086bfdde31a569a9d1cfb0820dfcd16f18b6` |
| optional occurrence-repair memo | `570e9e98d43f1d47cc2a529238de9abd929139b37b3ab720ab7fb6ce8626540c` |

The Builder's reported 96 scanner/profile tests and four inventory tests pass.
That establishes internal behavior of the current implementation, not the
scientific necessity of its representation.

## What the measurements show

The reported p02/m0/CLOSED/SEEK object is 1,661,198 canonical bytes, 73,783
nodes, 56,639 leaves, and 119,580 aliases. Its 18 strict failures come from the
values `246`, `545`, `632`, `722`, `goal`, `service`, and `start`, not from a
scheduled action, undisclosed complete identifier, or hidden route. The numeric
values are array-index aliases found as substrings inside random opaque public
IDs. The words are structural/schema keys colliding with fixed public protocol
vocabulary.

Fresh read-only construction of four source envelopes gave:

| source | bytes | nodes | leaves | role bindings | future IDs | route transitions |
|---|---:|---:|---:|---:|---:|---:|
| p00 | 5,808,476 | 257,689 | 198,119 | 10,873 | 7,800 | 2,400 |
| p01 | 5,845,802 | 259,389 | 199,393 | 10,909 | 7,810 | 2,408 |
| p02 | 1,661,198 | 73,783 | 56,639 | 3,079 | 2,184 | 672 |
| p03 | 1,698,528 | 75,483 | 57,913 | 3,115 | 2,194 | 680 |

For p00, `future` is 2,727,688 bytes, `oracle` is 2,417,032 bytes, and
`role_keys` is 655,582 bytes. Together those three roots are 5,800,302 bytes,
or 99.86% of the object. For p02 the same roots are 1,653,029 bytes, or 99.51%.
They repeatedly encode the same services, IDs, origins, route transitions, and
role bindings in different custody views.

This redundancy is useful for a full audit manifest. It does not create new
ways for hidden information to enter actor bytes. Atomizing JSON pointer
components, array indices, key names, scalars, tagged scalars, and lexer atoms
from every repeated copy creates a large family of coincidental substrings.
The optional occurrence repair then proves that those coincidental substrings
sit inside authentic public IDs or syntax. That repair is locally defensible,
but it is machinery for undoing false positives introduced by the alias
definition itself.

## The scientific boundary that actually matters

The Stage2A question is whether a child can execute a target-disjoint controller
from supplied memory. A valid source gate must prove:

```text
candidate actor bytes
    = exact rendering of the allowed public state at this decision

and no unauthorized occurrence of
    next action / future ID / private semantic value / future route
appears in those bytes.
```

The first line is stronger than scanning every private integer and JSON key. If
the candidate prefix equals an independently reconstructed public projection,
metadata such as `physical_route_depth=2` cannot enter it at all. Searching for
the byte `2` inside opaque IDs does not improve that guarantee.

The current source path already contains most of the right primitives:

- exact constructor/case/record reconstruction and source digests;
- exact retained-message spans and causal field ownership;
- a complete future-ID set derived before the decision;
- a finite effective-transition basis and occurrence-aware route matcher;
- exact full-target and operand checks;
- core namespace/edge-label checks; and
- immutable runtime/custody/scoring components.

The missing object is an independently checked boundary manifest joining these
primitives. A universal semantic-tree blacklist is not that object.

## Smallest prospective representation

### A. Shared complete source custody — retained, not scanned

Store the complete canonical task, registry/services, effective world edges,
trace, facts, four targets, role bindings, paired mutation, allocation/master
receipt, and route basis **once per case/pair**. Do not replace these objects
with hashes; hashes index and bind the retained objects. Do not repeat them
inside every target/arm's semantic tree.

An independent checker must reconstruct the case/pair, verify all exact source
bytes and counts, and reproduce the case, role-map, master, construction,
mutation, route-basis, and target hashes. This preserves v2's rule that a
summary hash is not a substitute for complete objects.

### B. Per-decision boundary receipt

For each of 64 cases x four targets x two arms, retain only:

- case/pair source object ID and exact source hashes;
- unit ID, arm, phase, decision index, retained source-turn indices;
- exact public projection bytes and message/field spans with source evidence;
- exact target bytes/hash and parsed command/operand;
- task START/GOAL and latest public CURRENT;
- implicated event/query and contradiction status where applicable;
- disclosed-ID and future-ID set hashes plus references to their retained
  canonical lists;
- core hash, public-graph hash, and route-basis hash; and
- actor-prefix tokenization/template receipt at native preparation.

The checker must rebuild the projection independently from the shared source
object and require byte equality. Caller-supplied spans, exemptions, success
flags, or inventories remain forbidden.

### C. Typed leak basis

Scan the exact public projection against this finite, source-derived basis:

1. exact next full action;
2. exact target operand, with the existing phase-specific typed occurrence
   rules;
3. every exact undisclosed QUERY/EVENT/PORT and non-task destination ID;
4. exact full private categorical values and full private role/case/unit keys
   that could be rendered as text, with provenance and no atomization;
5. the six forbidden cross-system labels plus forbidden `LINK`, `OLD`, and
   `NEW` edge labels; and
6. the complete typed effective-transition basis through the existing finite
   route-language matcher.

Do **not** create independent needles from JSON pointers, structural key names,
array indices, booleans, nulls, standalone integers, tagged pointer/value
forms, or substrings/lexer atoms of opaque identifiers. These are protected by
exact projection equality and structural source checking. A full private role
key may be forbidden; the words `goal` or `246` extracted from its path may
not be treated as a hidden answer.

Every allowed target/identifier occurrence still requires an exact typed
public-field receipt at the correct chronology. Authentic earlier history can
be admitted only at its original source offsets. Copied, moved, appended,
foreign-arm, foreign-child, or endpoint-only matches remain failures. Unknown
route prose remains uncertified; it cannot become an exemption.

## Preserved invariants

| invariant | prospective proof |
|---|---|
| target blindness | exact public-projection reconstruction plus full-target, operand, future-ID, private-value, and route checks |
| public/hidden separation | physically separate shared hidden source and public boundary objects; independent byte-equality projection check |
| route authenticity | unchanged complete effective-transition basis, recovery ownership, finite grammar, and causal-prefix-through-second-endpoint receipt |
| causal prefix identity | exact message bytes, source-turn indices, chronology, arm, and prefix hash; no copied occurrence inherits a receipt |
| custody | complete objects retained once, content addressed, and referenced from every boundary; no hash-only substitution |
| paired intervention design | unchanged 32 pairs, v5 route placement, allowed diffs, same target tape and seeds |
| scoring | unchanged strict parser, intervention/chain/canary scoring and BASE/D1 paired logical seeds |
| training | unchanged `ATOM_LOCAL` single fit, rank/heat/mask/template, 256 updates and four presentations at D1 |
| controller thresholds | unchanged 3/4 per skill, 30/32 typed interventions, 6/8 chains, 7/8 READs, 7/8 STEPs, 15/16 canaries, and +2/8 over BASE |
| cost | unchanged 280 BASE + 280 D1 reserved slots; zero reader calls; no new fit, model call, or GPU cell |
| claims | unchanged target-disjoint supplied-memory controller screen; no learning, recurrence, parenting, or whole-organism claim |

## Required stop/go tests before the 560-call screen

Run these on the full 64-case/256-unit/512-arm source, not just p02:

1. **Source totality:** independent reconstruction matches every complete
   retained case/pair object, all role/master/allocation pins, v5 placements,
   256 targets with READ/STEP/THINK/STOP `96/64/64/32`, and both arms.
2. **Boundary equality:** all 512 candidate public projections equal the
   independently rendered allowed bytes exactly. Any extra, deleted, moved,
   reordered, or changed byte fails before lexical scanning.
3. **Inventory equality:** per boundary, independently reproduce complete
   disclosed/future ID sets and the complete effective transition basis;
   verify hashes, counts, source paths, and recovery ownership.
4. **Clean-source pass:** every authentic CLOSED and ATOM boundary passes with
   receipts for all legitimate causal occurrences. ATOM never inherits CLOSED
   history.
5. **Leak mutation matrix:** for every phase and both arms, inject at a fresh
   unauthorized span (a) the full target, (b) target operand, (c) one future ID
   of every available type, (d) a full private categorical value and role key,
   (e) each forbidden core label, and (f) every supported two-transition route
   rendering family. Every injection must fail.
6. **Receipt adversaries:** copied source text, moved/truncated prefixes,
   altered intervening WORLD/service bytes, same endpoints with a changed
   middle, foreign arm/case/master/role map, boundary-crossing matches, and
   caller-created spans/inventories must fail.
7. **Pair and scoring integrity:** intervention twins retain only their
   predeclared differences; target tape, decode seeds, BASE/D1 identity,
   strict scoring, canaries, and cost arithmetic reproduce exactly.
8. **Resource receipt:** report canonical bytes, item counts, peak RSS, and
   wall time for all 512 checks. No truncation or sample-based clearance is
   allowed. The algorithm must be bounded by the public projection, exact
   inventories, and finite transition basis—not by traversal of a repeated
   full semantic tree per arm.

**STOP** if any clean boundary lacks source ownership, any required inventory
cannot be independently derived, any injected leak passes, any copied/foreign
occurrence inherits a receipt, any complete source object is omitted from
custody, or any scoring/training/cost invariant changes.

**GO_NATIVE_PREPARATION** only after all eight rows pass and a fresh reviewer
checks the exact source/test/receipt bytes. This still does not by itself open
model/GPU execution; the existing native tokenizer/runtime/initialization and
device/deadline gates remain.

## Minimal next action

Write a short versioned Stage2A successor that separates **complete custody**
from the **typed boundary leak basis** exactly as above. Then replace the
current full-object promotion path—not the source objects, future-ID producer,
route matcher, scoring, or reducer—and run the eight CPU gates across all 512
records. Do not spend another cycle raising `birth_full_v1` limits or expanding
source-occurrence exemptions.

The reduced 560-call screen remains the correct next model experiment. This
audit removes a non-scientific metadata bottleneck; it does not weaken the
experiment and does not authorize its execution.
