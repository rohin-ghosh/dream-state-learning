# Construct attack: authentic PCFL vertical world before any fit

**Date:** 2026-09-13 UTC
**Role:** independent shortcut / leakage / construct-validity audit
**Evidence cut:** repository `34ff7b05`
**Scope:** analysis and CPU-test design only. I changed no generator, benchmark,
model, adapter, prompt, threshold, job, or GPU state.

## Ruling

`PCFL-VERTICAL-DEV-v1` is the right scientific direction, but its current
two-twin prose object is **not yet identifiable enough to fit**. There is no
dedicated vertical-world generator in the repository at this evidence cut.
The nearby executable generators provide good custody and paired-collision
patterns, but none implements this EVENT/LINK/reachout/OLD+NEW object.

Four issues are presently construct-fatal:

1. `EVENT` is an exact restatement of a public action/outcome receipt, and
   `LINK` is defined by endpoint equality over those EVENT rows. Thus EVENT
   adds no world information beyond the receipt and LINK adds no information
   beyond the events. A no-link API cut can make the API necessary without
   making a stored connection necessary.
2. A two-world outcome twin can prove that the useful outcome was unknown. It
   cannot also prove that a distractor had one independent bit of outcome
   entropy but zero goal-relevant information. That requires a Cartesian
   crossing of the useful and distractor bits.
3. Saying that flipping an OLD dependency or NEW binding flips the answer is
   functional sensitivity, not proof that either view alone is
   non-identifying. Exact collision classes must map identical OLD-only and
   NEW-only views to different correct commands.
4. A native mounted endpoint is scoreable without a candidate bank, but only
   through an open command grammar and deterministic environment execution.
   A goal-specific legal-route menu, generated route candidates, per-item
   allowed-action list, answer-aware tool schema, or interactive second chance
   would leak or reacquire the answer.

The smallest sound repair is a three-bit, eight-world collision cube per base
skeleton, an explicit atoms-only causal arm, and a candidate-free one-shot
native scorer. All proposed checks below are exhaustive CPU checks. No model
or GPU execution is needed.

## 1. EVENT and LINK are not presently information-necessary

The proposed rows are:

```text
EVENT <event_id> AT <source> DID <port> GOT <destination>
LINK <link_id> FROM <event_id_1> THEN <event_id_2>
```

The compiler accepts a link when
`destination(event_id_1) == source(event_id_2)`. Therefore, for a complete
EVENT set `E` and this public rule,

```text
H(LINK | E, endpoint-equality rule) = 0.
```

Likewise, because every EVENT argument is copied from an executed public
action/outcome receipt `P`,

```text
H(EVENT semantics | P, fixed EVENT schema) = 0.
```

Child authorship remains a genuine provenance fact. It is not an information
treatment. The child rows may be a useful *organization or carrier surface*,
but the world does not require them to solve the task. `RAW_EPISODIC` with a
faithful normalizer and `EXACT_WITNESSED_GRAPH` should solve from public
receipts without either child commitment. That result is a valid ceiling, not
a baseline defect.

There is also a trilemma in the proposed LINK controls:

- If every endpoint has one compatible successor, the true LINK is uniquely
  derivable from EVENT rows. A fixed-point-free valid LINK permutation cannot
  exist.
- If at least four successors share a compatible endpoint, all four links are
  valid under the stated public verifier. Selecting one as the uniquely
  “true” link needs another public relation, or it silently uses a future goal
  or hidden graph label.
- If the permuted link joins incompatible endpoints, it is an easy
  contradiction visible from the EVENT rows. Following it proves that the
  adapter can inject a false pointer; ignoring it is rational. Neither outcome
  shows added value from the authentic link.

The same problem appears at read time. `READ LINK <event_handle>` returns one
local row. If an event has one successor, the row is derivable. If it has
several successors, a goal-blind memory worker has no principled way to choose
one, while returning a future-goal-selected row is leakage. The frozen API
must specify exhaustive adjacency, pagination/cursors, and read charging
before a query-budget claim is meaningful.

### Necessary interpretation repair

Do not claim that child EVENT/LINK rows are globally necessary for the route.
The maximum defensible construct is:

> exact child-authored rows were sufficient life-specific targets, and their
> stored organization improved bounded candidate-free access or traversal
> relative to the same child EVENT atoms without stored LINK rows.

That sentence requires restoring `S1_ATOMS`: exact authentic child EVENT rows,
no LINK targets, and matched nonsemantic target tokens/updates. The current
`S1_AUTH`, `S1_EVENT_TWIN`, and `S1_LINK_PERMUTE` arms do not contain this
contrast. A read-time `MISS` substitution is not a replacement: it changes
the interface after the authentic LINK was already trained and is especially
irrelevant to implicit native mounted use.

Thus the smallest S1 design has four fits, not three:

```text
S1_AUTH
S1_ATOMS
S1_EVENT_TWIN
S1_LINK_PERMUTE
```

If `AUTH ~= ATOMS > LINK_PERMUTE`, report event composition and traversal, not
stored-link added value. If exact atoms/full public receipts solve perfectly,
that does not invalidate DLT; it closes the stronger necessity wording.

## 2. Equal outcome entropy is not equal experimental value

The present design requires

```text
H(Y_relevant | T_pre)   = 1
H(Y_distractor | T_pre) = 1
I(Y_relevant; Z_G | T_pre,G)   = 1
I(Y_distractor; Z_G | T_pre,G) = 0.
```

Two counterfactual worlds that differ only in the relevant binding establish
the first relevant-outcome line. They do not establish a one-bit distractor:
if its result is unchanged across the two worlds, its conditional entropy is
zero. Balancing distractor outcomes over unrelated roots is also insufficient
because those roots have different `T_pre`; root text or old history may
identify the outcome.

For each fixed old world and goal, preallocate a four-cell outcome quartet:

```text
(R,D) in {(0,0), (0,1), (1,0), (1,1)}
```

where `R` fixes the relevant frontier result and missing goal fact `Z_G`, and
`D` independently fixes the distractor result. All four cells must have
byte-identical model-visible pre-outcome history, task prompt, tool grammar,
action order, identifiers, and ordinary affordances. In every quartet:

- each relevant outcome is present `2/4` times;
- each distractor outcome is present `2/4` times;
- every `(Y_relevant,Y_distractor)` joint cell is present `1/4` times;
- `Z_G = R` (up to a fixed bijection); and
- `D` is independent of `(R,G)`.

This proves equal one-bit raw uncertainty but unequal target relevance. Merely
matching label counts, token lengths, or global entropy does not.

The proposed `7/8` wording/order gate is a useful technical robustness check,
but it is eight repeated views of one latent decision, not eight acquired
bits. Report `7/8` trace choices as surface robustness. At the scientific root
level, one committed useful action earns exactly `1` registered bit and any
irrelevant, invalid, missing, or post-outcome action earns `0`.

## 3. OLD + NEW needs view collisions, not only edge cuts

Deleting an old edge or new edge and observing no graph path proves structural
dependence of the oracle. It does not prove that an actor cannot recover the
correct command from identifiers, route order, goal wording, a legal-action
menu, or cross-root regularities. Conversely, an output that changes when a
bit flips may still be perfectly predictable from OLD alone.

Add one independent OLD binding bit `O` to the `(R,D)` outcome quartet. The
minimal object is therefore the eight-world cube

```text
(O,R,D) in {0,1}^3.
```

`O` changes one required old route segment. `R` changes the required new
frontier segment. `D` changes only the irrelevant experiment. Public old
experience legitimately reveals `O`; the NEW row must not. Pre-outcome
quartet equality is required conditional on fixed `O`, not across `O`.

The delayed task should score one exact complete route command in one shot.
For each goal `G`, require:

1. FULL `(OLD, NEW, delayed prompt)` has exactly one legal successful route.
2. Removing the registered OLD dependency destroys every successful route.
3. Removing the registered NEW dependency destroys every successful route.
4. Every exact OLD-only serialized view occurs with both `R=0` and `R=1` and
   therefore at least two different correct commands.
5. Every exact NEW-only serialized view occurs with both `O=0` and `O=1` and
   therefore at least two different correct commands.
6. Within an exact native-prompt equivalence class, the four `(O,R)` states
   give four balanced correct commands; `D` merely duplicates each command.

Clauses 4--6 are the missing identifiability proof. They are the route-world
analogue of the repository's repaired v0.3 collision twins and its fail-closed
v0.2 ambiguity audit.

A generator certificate can establish that the *task information* requires
OLD and NEW without more fits. It cannot establish that a mounted model
causally used each trained source. The modular reader cuts cover only the
clean-actor relay. If the paper claims necessity inside the native mounted
organism, retain `S2_OLD_REPLAY` as OLD-only and add counterfactual
`S2_NEW_ONLY_t0/t1` fits; otherwise limit native language to successful
behavior on an OLD+NEW-identifiable task.

## 4. Native mounted behavior is scoreable without candidates

Use a scorer that never asks the model to choose among answer-bearing strings:

```text
public request: ordinary goal + global command grammar + one-shot budget
model output:   ROUTE <start> <goal> : <port_1>,...,<port_k>
private scorer: strict parse -> deterministic graph execution -> exact success
```

The ordinary grammar may name the two command verbs and delimiters. It must
not contain a goal-specific route list, possible complete routes, expected
length if length identifies a route, correct first-port subset, registered
dependency handles, score, hidden bit, or answer-aware “legal actions.” If
current-state port affordances are normally public, their multiset and order
must be byte-identical over the collision class and cannot prune to the
correct path.

Evaluation is one-shot. The environment returns no intermediate node/outcome
until the complete route is committed and scored; there is no repair, retry,
interactive exploration, memory write, or second action. The parser accepts
the same global language in every world. The correct commands are generated
privately by the exact oracle, not inserted into the request as likelihood
candidates.

The mounted actor sees the ordinary request only. Adapter path, arm name,
world bit, scorer metadata, expected answer, memory query trace, and candidate
arrays are outside the model-visible serialization. A different fitted
adapter may of course encode its own life; identical prompt bytes with
different correct outputs is the intended memory test.

## 5. Smallest exact CPU gate

Use four excluded base skeletons before any DEV fit. Each skeleton expands to
all eight `(O,R,D)` worlds and both goal branches. This is only `32` generated
worlds and `64` delayed/native task cells. Do not sample this gate. When DEV
and confirmation roots are later sealed, rerun the same exhaustive audit over
100% of their cubes.

### A. Outcome-entropy and pre-outcome equality

There are

```text
4 roots x 2 O values x 2 goals = 16 quartets,
4 (R,D) cells per quartet = 64 reachout task cells.
```

Require `16/16` quartets to have one exact model-visible pre-outcome hash and
the exact outcome table `{00:1, 01:1, 10:1, 11:1}`. Report the computed
conditional entropies and mutual informations for every quartet; all `16/16`
must equal `(1,1,1,0)` bits for
`(H(Y_R), H(Y_D), I(Y_R;Z_G), I(Y_D;Z_G))`. No average passes.

### B. OLD/NEW identifiability and structural cuts

Across the `64` delayed task cells require:

- FULL exact oracle: unique successful route on `64/64`;
- OLD-dependency deletion: no successful route on `64/64`;
- NEW-dependency deletion: no successful route on `64/64`.

For OLD-only views, group over the missing `R` bit at fixed
`(root,O,D,G)`: `32/32` two-world groups must have identical projected bytes
and two different correct commands. For NEW-only views, group over missing
`O` at fixed `(root,R,D,G)`: the corresponding `32/32` groups must also have
identical projected bytes and two different correct commands. Singleton keys
fail; a key passes only with support `>=2` and labels `>=2`.

For native prompt-only views, group the eight worlds by `(root,G)`. All `8/8`
groups must contain eight identical prompt byte strings and exactly four
correct commands at count `2/8` each. Thus the best prompt/goal/identifier/
order-only deterministic decoder is exactly `16/64 = .25`, not merely “chance
+ .05.”

### C. Atom/link identifiability

S1 has only the two old goals and does not depend on `R` or `D`. Audit the
`4 roots x 2 O values x 2 goals = 16` unique old-task cells under three exact
CPU solvers:

```text
raw public receipts -> deterministic witnessed graph
exact child EVENT rows only -> endpoint-composition oracle
exact child EVENT + LINK rows -> link-following oracle
```

Before authentic formation exists, these are audit-only ideal projections of
the public receipts into the proposed child schema. They are never training
rows and do not authenticate child authorship. After formation, the same
checks rerun on the exact admitted child bytes.

Report `16` decisions per solver, `48` total. If EVENT-only or public receipts
solve `16/16`, LINK is not information-necessary. That is the expected result
under the present schema. The learned added-value question must then be
decided only by `S1_AUTH` versus `S1_ATOMS` under a frozen equal-resource
interface.

Separately, for the four registered old links per world, enumerate the full
matched target roster. The denominator is

```text
4 roots x 2 O values x 4 links = 32 source-link instances.
```

For all `32/32`, report the number `K` of targets supported using only public
pre-goal evidence. If `K=1`, report LINK as derivable. If `K>1`, every one of
those `K` targets is supported unless a prospectively declared public
relation distinguishes it; future route utility and hidden graph labels may
not select the authentic target. Never call a syntactically well-formed but
endpoint-incompatible permutation “valid under its own map.”

### D. Candidate-free native serialization and scorer

For all `64/64` native task cells, require:

- exact equality of the model-visible request inside each of the `8` collision
  groups above;
- an empty candidate array and no goal-specific action/route enumeration;
- exact field allowlists for public request versus private scorer objects;
- the private oracle command parses and succeeds (`64/64`);
- each registered OLD cut command fails (`64/64`); and
- each registered NEW cut command fails (`64/64`).

This is `192` deterministic parse/execute decisions. Also require `0/64`
intermediate outcome returns before commitment and `0/64` retries. Recursive
substring scans are only a backstop; schema separation and collision equality
are the primary leakage proof.

### E. Projection-based shortcut audit

For each registered shortcut projection—goal text, start/target IDs, event and
link handles, row/order positions, port frequency, outcome frequency, command
length, legal-affordance order, and every pairwise combination—the audit key
is composed only from model-visible fields and the label is the private exact
command. Every key must have support at least `2` and at least `2` labels.
Report, for each projection, all of:

```text
number of keys
number of 64 task occurrences covered
minimum support per key
minimum labels per key
deterministic keys
deterministically decoded occurrences
Bayes-best exact-command accuracy
```

Pass requires `64/64` occurrence coverage, zero deterministic keys, zero
deterministically decoded occurrences, and prospectively frozen Bayes ceilings.
Do not infer safety from balanced marginals. The executable Q0 generator only
checks a hand-written family of nuisance projections; the v0.2 failure shows
why collision support for exact public projections is the stronger standard.

## 6. Generator acceptance and claim disposition

Before the first fit, require one immutable audit receipt containing the
generator/source hashes, all `32` world hashes, all `64` task hashes, the 16
entropy tables, 64 full routes, 128 dependency-cut results, 64 OLD-only
collision memberships, 64 NEW-only collision memberships, 64 native prompt
memberships, shortcut reports, and public/private schema inventories. A second
independent CPU oracle must reproduce all labels and cuts from public atoms
only. Equality must be over actual rendered bytes passed to the component,
not normalized semantic objects.

The go/no-go consequences are:

- If the eight-world cube cannot be constructed, label `VS_ASSAY_INVALID` and
  do not fit.
- If atoms solve, retain the assay but narrow the link claim; do not hide the
  result by forcing the reader to request LINK.
- If useful/distractor information differs only by entropy or surface cues,
  the reachout construct is invalid.
- If either OLD-only or NEW-only projection has a deterministic correct
  command, the delayed reuse construct is invalid.
- If native scoring needs answer candidates or interactive feedback, report a
  modular memory-service result only.
- If native causal necessity is claimed, add the NEW-only fitted controls;
  generator impossibility alone supports task structure, not internal use.

With these repairs the vertical slice remains small and much more decisive
than the diagnostic ladder. Without them, a successful run could be explained
by receipt normalization, endpoint composition, a goal-visible gap, a
two-world entropy illusion, route-surface priors, or a candidate-bearing
native scorer.

## Repository evidence inspected

- `research_notes/analysis/2026-09-13_claim_ladder_area_chair_audit.md`
- `research_notes/analysis/2026-09-13_minimum_authentic_child_authored_m_bridge.md`
- `research_notes/analysis/2026-09-12_smallest_post_h1_connected_traversal_expansion_module.md`
- `research_notes/analysis/2026-09-12_h1_path_connected_claim_fresh_redteam.md`
- `organism_v6/endogenous_action_relay.py` and its CPU fixtures
- `organism_v6/semantic_writer_diagnostic.py`
- `organism_v6/multikey_writer_gateway_simple.py`
- `research_loop/microdream_world.py`
- `lands/v03.py`, `lands/v03r.py`, and their paired-world tests
- `lands/audit_v02_shortcuts.py` and `lands/test_v02_shortcut_audit.py`

The strongest reusable patterns are v0.3's paired public-byte collision and
bridge-removal oracle, v0.2's fail-closed repeated-key ambiguity rule, the
endogenous relay's exact raw-span/provenance checks, and Q0's explicit
shortcut-count receipts. None currently composes them into the proposed
vertical object.
