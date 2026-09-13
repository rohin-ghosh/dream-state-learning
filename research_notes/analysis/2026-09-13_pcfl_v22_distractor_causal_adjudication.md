# PCFL v2.2 distractor: minimal causal construction and hostile adjudication

**Date:** 2026-09-13 UTC  
**Role:** independent causal-benchmark skeptic  
**Scope:** specification adjudication only; no implementation, fixture,
tokenizer/model call, fit, adapter, GPU work, or scientific result

## Verdict

The smallest defensible completion of the missing distractor is the frontier
already latent in the frozen OLD skeleton:

```text
relevant probe:    H -> S_R    outcome port q_R = q[R]
distractor probe:  X -> Z      outcome port q_D = q[D]
```

Here `q[0]` and `q[1]` are the **same two opaque public `P_` identifiers** for
both probes. `q_R` and `q_D` are private aliases, never literals. This is safe
because the two transitions have different sources, so even when `R=D`,
`(source,port)` remains deterministic. The distractor denotes a real latent
transition:

```text
S_L --a_(1-O)--> X --q_D--> Z --u--> Y
```

That transition is reachable and outcome-bearing but can never reach either
delayed target. It therefore supplies one genuine unknown route-system bit,
not a dummy random label. Toggling `D` changes the port on this isolated edge
and the selected distractor's public-after-commit result, while leaving every
correct delayed route, OLD/NEW authentic row, dependency cut, and fitted
lineage unchanged.

Use one result renderer for both probes, with **no probe-result receipt in
either condition**:

```text
PROBE RESULT
PROBE {PROBE_ID}
TESTED {SOURCE_ID} TO {DESTINATION_ID}
DISCOVERED PORT {PORT_ID}
```

The block has no terminal LF. Its four placeholders are respectively typed
`Q_`, `N_`, `N_`, and `P_`. No other field is public. The exact raw result
bytes are custody-hashed outside the model-visible text.

If the selected probe is relevant, the already-frozen continuation follows:
the child receives the result, executes `EXPLORE H q_R`, receives the ordinary
executed-event receipt, and may author `e8/l4/l5`. If the selected probe is the
distractor, the above result block is the final public response. The root is
then marked failed privately and stops: there is no extra terminal message,
no relevant result, no retry, no EVENT/LINK request, and no S2 lineage.

This completes the present **bounded** claim: memory can support selection of
the probe that is useful for this registered task while an equally uncertain
probe is not useful. It still cannot establish that experiment choice changes
with the goal, because both delayed goals use `H -> S_R`. No distractor-only
repair can supply that missing goal intervention.

## 1. Why this is the minimum coherent edge

The frozen OLD observations already create two unfinished chains:

```text
main cross-route prefix:  S_L -> A -> H
right target suffix:      S_R -> B -> G_R0/G_R1

alternate/dead prefix:    S_L -> X
isolated dead suffix:     Z -> Y
```

`H -> S_R` joins the two target-bearing halves. `X -> Z` performs the same
kind of operation on the explicitly supplied dead halves. It adds no new node,
changes no OLD observation, and uses the otherwise isolated `X,Z,Y` structure
for a real purpose. Enumerating paths after adding both latent frontier edges
still gives exactly one successful delayed route:

```text
S_L --a_O--> A --b--> H --q_R--> S_R --d--> B --f_G--> G_RG
```

Every path using `q_D` ends at `Y`. The construction therefore avoids both
bad alternatives: a causally nonexistent `D` bit and a distractor that opens
an alternate target route.

The distractor edge is a private world relation plus a public PROBE result
when selected. It receives no model-visible `E_` address and is never an
admitted EVENT row. Otherwise a failed, irrelevant action would silently add
training information or expand the authentic row roster.

## 2. Candidate attacks and dispositions

### 2.1 `X -> Z` versus other endpoints — accept, with a claim limit

`X -> Z` is the only zero-new-node choice directly implied by the two frozen
dead fragments. It cannot reach a target and preserves the intended
relevant/distractor topology.

It is not perfectly graph-isomorphic to `H -> S_R`: `H` participates in more
OLD structure than `X`, and the `S_R` suffix branches to two registered goals
whereas `Z` has one dead successor. Consequently a fixed graph heuristic can
correlate with the relevant probe in this one task family. This is **not a
surface leak**—the topology is precisely the information the memory is meant
to carry—but it forbids stronger wording such as “the agent learned a general
value-of-information rule” or “the goal changed which experiment it chose.”

Trying `H -> Z` makes the local sources equal but does not solve the scientific
limitation: downstream topology still distinguishes the choices, and the same
source would require four separate `q` ports to keep deterministic transition
semantics when `R=D`. Trying `X -> S_R` creates an alternate successful route
and is fatal. Trying `A -> Z` is arbitrary and discards the explicit `X`
frontier without buying a goal intervention. None is a better minimum.

If the paper later needs goal-switched experiment selection, add a separately
specified counterfactual goal for which the `X -> Z` frontier is useful and
the `H -> S_R` frontier is not, with matched terminal topology. That is a new
world version, not a permissible v2.2 implementation detail.

### 2.2 An arbitrary result-only dummy — reject

An independent bit rendered as `YES/NO`, `0/1`, a random token, or an opaque
port without a world transition has entropy but is not a matched experiment.
It proves only that a coin is unpredictable. The accepted result-only design
is different: `PROBE X TO Z` queries the real private binding
`X --q[D]--> Z`, and the oracle can execute that binding. “Result-only” means
the child does not subsequently traverse the useless edge; it does not mean
the result lacks denotation.

The preparer must therefore fail if toggling `D` changes only metadata or a
rendered label while leaving the distractor transition oracle unchanged.

### 2.3 Shared `q0/q1` — accept; separate distractor alphabet — reject

Reusing the two public port identifiers is the strongest outcome matching:
both experiments return one member of the same two-token alphabet under the
same renderer. Since the sources are `H` and `X`, a shared label does not make
the graph nondeterministic. When `R=D`, the same port spelling is valid at two
different sources; source-qualified execution remains unique.

Separate `qR0/qR1` and `qD0/qD1` alphabets add unnecessary identifiers and
make experiment type decodable from the result port itself. That occurs after
the commitment, so it would not by itself bias initial choice, but it weakens
the matched-outcome construction and creates avoidable projection work.

The shared alphabet does mean that blindly copying a distractor result into
the relevant source succeeds in half the cube. That is expected under zero
mutual information: it remains a `.5` guess before and after seeing `q_D`.
The exact quartet audit, not success on a single cell, is what proves this.

### 2.4 Receipt asymmetry — reject; no receipt for either probe result

A receipt ID on only one PROBE result is an unnecessary type cue. A normal
executed-event receipt on the distractor but not the relevant probe is worse:
the two tools would perform different operations. Adding matched probe-receipt
IDs to both outcomes is possible but buys no scientific information and adds
two opaque slots plus another parser/schema.

The minimal symmetric rule is that PROBE returns the exact result block above
for either choice and neither block has a receipt ID. Custody hashes are
private. Only a later `EXPLORE` action produces the ordinary `R_` event receipt.
The relevant branch performs that action because it is useful; the failed
distractor branch ends at its already-observed result. Since this divergence
occurs after the one blind commitment, it cannot cue the choice.

### 2.5 Public `G_` goal token — reject

The route goal is a graph endpoint and must be typed `N_` everywhere:

```text
GOAL {N_TARGET}
ROUTE {N_START} {N_TARGET} : ...
```

`G in {0,1}` is a private task/cube index, not a model token. A separate
model-visible `G_` identifier would require an additional public mapping from
goal handle to node, duplicate information already carried by the target
node, and create a new route-label shortcut. Substituting `G_` where the
executor expects `N_` is a type error.

The successor binding must explicitly supersede the prospective register's
ambiguous inclusion of `G_` in the model-visible namespace. The safest v2.2
rule is: allocate no visible `G_` IDs. If implementation compatibility retains
one in the private manifest, assert zero occurrences across every
model-visible prompt, result, memory row, query, and command. It cannot be
used as a tokenizer-equality filler.

## 3. Exact state transition

For a prepared cell `(root,O,R,D,G)`, define privately:

```text
frontier[Q_relevant]   = (H, q[R], S_R)
frontier[Q_distractor] = (X, q[D], Z)
```

Before commitment the public state contains only RA or RB, which lists both
probe IDs and their endpoints. It contains neither port. The only legal model
action is one exact `PROBE <Q_...>`.

After the action:

1. Reject a missing, malformed, unknown, repeated, or post-outcome action.
2. Look up only the selected probe in `frontier`.
3. Render the one exact PROBE RESULT block from that tuple.
4. If relevant, expose only `q[R]` to the existing singleton EXPLORE step.
5. If distractor, seal the diagnostic transcript and stop the root privately.

No model-visible field may say `R`, `D`, `relevant`, `distractor`, `useful`,
`correct`, `failed`, `dead`, `target route`, or `continue`. The private action
record may carry the structural probe role and failure label, but the public
renderer must be a closed projection that cannot serialize them.

The unselected outcome is never public. A relevant selection cannot expose
`q[D]`; a distractor selection cannot expose `q[R]`. A distractor primary can
never be resumed into S2 even if its `q_D` happens to equal `q_R`.

## 4. Must-pass falsifiers before any model call

All checks are exact and noncompensatory.

### 4.1 Real-edge and determinism certificate

Across all 32 excluded-root worlds:

- both registered probe bindings exist (`64/64`);
- executing the returned `(source,port)` reaches the registered destination
  (`64/64`);
- substituting the other `q` port at that source does not realize that same
  registered frontier (`64/64`);
- no source has two destinations for one port (`32/32` worlds); and
- toggling `D` changes the distractor port/after-commit bytes but not the
  relevant port/bytes, while toggling `R` has the exact converse.

A distractor label with no executable private relation is an immediate
`VS_ASSAY_INVALID`.

### 4.2 Route and alternate-path certificate

For all 64 delayed tasks, with both latent frontier relations available to the
private oracle:

- exactly one simple successful target route exists (`64/64`);
- the successful route contains `e0` and relevant `e8`, never the distractor
  edge (`64/64`);
- deleting `e0` destroys success (`64/64`);
- deleting `e8` destroys success (`64/64`);
- deleting or toggling only the distractor edge leaves the exact correct route
  byte-identical (`64/64`); and
- every syntactically legal route containing the distractor transition fails
  to reach the requested target (`64/64` cell-level exhaustive verdicts).

Checking only the registered answer is insufficient; enumerate every simple
path under the bounded acyclic graph so an unregistered alternate cannot hide.

### 4.3 Entropy and outcome identity certificate

Retain the sixteen fixed `(root,O,G)` quartets. Each must have:

- one exact RA/RB-specific pre-outcome byte hash across all four R/D cells;
- the joint outcome table `00,01,10,11` exactly once;
- exact `(H(Y_R),H(Y_D),I(Y_R;Z_G),I(Y_D;Z_G))=(1,1,1,0)`;
- identical result template, field count, placement, whitespace, terminal-LF
  policy, and tokenizer substitution-class length for relevant and distractor;
  and
- only `PORT_ID` changing across the 0/1 outcome twin for a fixed selected
  probe. Any content hash remains private and cannot introduce extra bytes.

Global balance cannot rescue one failed quartet.

### 4.4 Visibility and transcript certificate

Across the 32 reachout cells and every RA/RB render:

- zero outcome-port occurrences exist before commitment;
- structural roles and hidden bits have zero decoded occurrences;
- each branch has exactly one commitment and exactly one public result block;
- no PROBE result contains an `R_` receipt, event/link address, score, route,
  future action, or continuation marker;
- a distractor branch contains no relevant result and no post-result public
  message, retry, formation request, or S2 descendant;
- a relevant branch's only later receipt is causally downstream of its
  separately committed `EXPLORE H q_R`; and
- the failed distractor transcript/result is retained but tainted and has zero
  path into any authentic corpus, replay registry, adapter, or lineage.

### 4.5 Namespace and goal-typing certificate

- every visible `START`, `GOAL`, ROUTE start/goal, probe source/destination,
  EVENT source/destination, and LINK shared node parses only as `N_`;
- every returned/command port parses only as `P_`;
- probe identities parse only as `Q_`;
- the two accepted result substitution families have equal tokenizer counts;
- `G_` occurs zero times in all model-visible bytes; and
- wrong-prefix mutations fail rather than normalize.

### 4.6 Shortcut boundary

The existing nuisance audit must still show no decoding from probe order,
RA/RB wording, opaque ID spelling or order, tokenizer length, root index,
hidden-bit metadata, result position, or any pairwise combination. A policy
that never reads life memory—OFF, wrong-root, fixed first/second, or
ID/order-only—must remain within its registered `<=18/32` ceiling.

Do not require goal-blind graph heuristics to be at chance and then call the
exact-graph ceiling a pass: graph structure is the intended evidence. Instead,
report the strongest simple graph-only probe heuristic (source degree,
destination degree, reachability from START, reachability to GOAL, shortest
prefix/suffix lengths) alongside the model result. If a non-goal heuristic
selects `H -> S_R` perfectly, the current bounded relevance result may still
run, but no value-of-information or goal-conditioned-choice language is
allowed. Only a goal intervention can close that explanatory gap.

## 5. Unsafe designs that must be rejected

Reject preparation if any of the following appears:

1. `D` changes only a private integer or rendered coin label and no real
   `X --q[D]--> Z` relation.
2. `D` changes an authentic EVENT/LINK row, delayed answer, route, cut, corpus,
   replay choice, or fitted adapter input.
3. The distractor reaches `S_R`, `B`, either delayed goal, or any node with a
   path to a delayed goal.
4. Relevant and distractor results use different prose, field counts, receipt
   policy, terminal bytes, or token substitution class.
5. A probe result is visible before the one commitment, both results become
   public, or a wrong choice later receives the relevant result.
6. The public result includes relevance, utility, correctness, score,
   continuation, or private bit labels.
7. Separate q alphabets or a public G token are silently added as an
   implementation convenience.
8. An executed-event receipt is manufactured from a PROBE result, or a
   distractor row enters authentic SLEEP.
9. Any D branch is resumed, retried, replaced, or used to select a favorable
   root.
10. A two-root/global entropy average substitutes for all sixteen exact
    quartets or an answer-only oracle substitutes for exhaustive path search.

## 6. What this construction proves—and does not

If the CPU gates and later registered reachout contrast pass, the defensible
sentence remains:

> In the registered development worlds, the child selected the frontier probe
> whose one-bit result could complete the stated delayed route rather than an
> equally uncertain isolated frontier, under surface-balanced and
> memory-dependence controls.

This is stronger than “the child chose the high-entropy experiment”: both
choices have exactly one bit. It is weaker than general learned curiosity,
value-of-information estimation, or goal-conditioned experiment switching.
Those require goals that reverse probe utility.

This memo resolves one missing construction choice for a successor execution
binding. It does not itself authorize source authoring or a model call, and it
cannot turn the existing no-op `D` fixture into scientific evidence.

## Authoritative inputs inspected

- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md`
  (`222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456`)
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md`
  (`5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd`)
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md`
  (`f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679`)
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
  (`683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca`)
- `research_notes/analysis/2026-09-13_pcfl_v22_minimum_execution_closure_contract.md`
  (`f9b9891761c47e6d8047e7a9161a827d00fae464df91940c523b40f85af535d0`)
- `research_notes/analysis/2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md`
  (`bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`)
- `research_notes/analysis/2026-09-13_pcfl_vertical_world_construct_identifiability_attack.md`

