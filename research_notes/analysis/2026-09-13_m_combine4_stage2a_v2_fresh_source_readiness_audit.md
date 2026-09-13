# Fresh source-readiness audit: M-COMBINE-4 Stage 2A v2

**Date:** 2026-09-13 PT

**Role:** fresh adversarial source-readiness reviewer

**Object:** commit `46cb89da60f55ef55fa3d4081199319d30f78408`, file
`research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v2.md`,
verified SHA-256
`dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74`.

I read the binding predecessor v1, verified SHA-256
`ac0a61fbbf907cc8dd463e4138ba268c4a44daded01926f298d759c6e9bf064a`,
and the prior implementation-readiness delta plan, verified SHA-256
`9ab0932e8dc41a3bc9efa35966a3d7b58674c75457dd9d10b03fe5a0d73a23dc`.
The audited commit changes only the v2 memo. It contains no Stage-2A source or
tests. This audit did not invoke or assess a model, tokenizer, adapter, fit,
GPU, remote process, or scientific result.

## Verdict

**REWORK. `GO_SOURCE = FALSE`.**

V2 closes A, B, D, and F at the behavioral-contract level and gets the count,
dose, cost, and claim boundaries right. It does not close C, E, and G to the
standard asserted by its final ruling. In particular, recovery-query
cardinality conflicts with registration semantics; the CHECK intervention is
not compatible with the fixed deterministic world unless an unlisted
intervention override is introduced; held filler material and opaque role
keys remain author-selected; and the topology/signature hash does not yet have
one byte-level canonical representation. Two independent source authors can
therefore produce different registries, public bytes, graph hashes, and
intervention-validity results while each plausibly follows v2.

This is a source-contract ruling only. The narrow design, exact-text wire,
256-target comparison, fixed dose branch, and resource caps should be
preserved. Materialization and every later execution activity remain closed by
v2 itself.

## A--G closure result

| finding | requested closure | audit result |
|---|---|---|
| A | distinct, complete READ-CHECK and STEP-CHECK | **Closed.** MISS and irrelevant READ-CHECKs carry the issued query and exact return and revise the query; STEP-CHECK carries the selected EVENT/STEP, GOT, and WORLD CURRENT and revises the event. The ATOM role table is complete and does not leak the corrective query into READ-CHECK. |
| B | nine total nulls, all 36 unordered pairs, separate autonomous schedules | **Closed as a policy contract.** Each one-turn null ranks a finite public candidate list with one exact sentinel; the pair rule is order-independent and has a final digest tie-break. The six rollout schedules have explicit failure termination and separate denominators. Their prospective score caps still have to be executed on a repaired root. |
| C | exact topology families, held tuple/strata, recovery rotation and matching | **REWORK.** Factor formulas, recovery subtype table, A/B/C motifs, the absent tuple, and four eight-task strata are exact. The actual query/block inventory, held non-designated material, and mismatch-world completion are not. |
| D | honest target-only coupling and RNG/dropout/prefix treatment | **Closed.** Equality is target-side; prefix bytes/tokens/roles and padding are residuals. Equal RNG start states are not called equal masks, optimizer moments may diverge, and D2 restores adapter/optimizer/cursor/update/RNG custody. |
| E | feasible allowlist, disjoint concrete pools, sealed-domain proof | **REWORK.** The internal M2A pool construction and exact-line allowlist are feasible, but the required public certificate is absent and unbound, Stage-1 tiny DEV drops out of the comparison scope, and lexical-atom extraction is not defined. |
| F | exact prompt/parser/service bytes | **Closed for wire syntax.** System, task, host, actor envelope, identifier grammar, row skins, headers, MISS, LF/CR, and terminal-LF rules are literal. Service-map content cannot be frozen until C is repaired. |
| G | canaries, cores/signatures, scans, diffs, and source gates | **REWORK.** Canary action counts and scanner normalization are good, but canary ID roles inherit the open allocator, graph canonicalization lacks an exact serialization, semantic aliases are undeclared, and one intervention cannot satisfy both its diff allowlist and fixed-world validation. |

## Exact source blockers

### P0.1 -- RECOVER query roles and registries do not describe one finite object

Section 4.3 first creates exactly one recovery-query role and a public block
for every `(z, goal)`. It then says every candidate in every useful or
recovery block owns a RECOVER query. Four candidates therefore require four
RECOVER operands, including candidates whose AT is a wrong-AT node for which
the earlier role construction creates no recovery role. The same section then
says every non-implicated RECOVER query is unregistered and only the relevant
mistaken EVENT has a registered RECOVER block. Those instructions do not say:

- whether the one `recover/z/gjj` query is one of the four candidate-owned
  queries or an additional query;
- which candidate-owned query IDs merely appear in rows and which own a
  four-EVENT block;
- whether “their public blocks” registers the per-`(z,goal)` recovery block
  in ordinary cases, which would contradict the later unregistered rule;
- which registered useful query owns the bad-event block in a STEP-mismatch
  case; or
- the literal role keys for the distinct predicted and surprise nodes and the
  bad/corrective blocks.

This is not cosmetic. Different choices alter pool counts, exact public IDs,
service MISS behavior, the role graph, CLOSED transcripts, and scanner
ledgers. Repair with a finite per-domain inventory table giving every literal
role key, its kind, owner, row reference, registry key, response-block owner,
and registered/unregistered bit. State explicitly that the initial mistaken
block replaces (or does not replace) the selected `query/s/gjj` block.

### P0.2 -- The CHECK intervention conflicts with the deterministic world

The public contract says a legal `(AT, DID)` has one fixed world transition,
except that a pre-authored mistaken EVENT may have GOT different from that
fixed destination. The CHECK pair holds the task, EVENT, DID, GOT, pre-outcome
transcript, and all non-allowlisted object fields fixed, but changes WORLD
CURRENT from GOT to an alternate node. If one member's fixed transition ends
at GOT, the other member cannot legally end at the alternate node without
changing the world transition or declaring an exogenous override. Neither is
in the allowed-diff list. The independent checker is simultaneously required
to reconstruct legal world transitions, so it cannot both enforce the fixed
world and accept both members.

Repair by choosing one exact semantics: either make CHECK pairs explicit
counterfactual transcript fixtures exempt from world-transition validation,
or include a typed outcome intervention and the concrete world-transition
destination pointer in the allowed diff. Bind whether the intervention is
part of the public prompt, evaluator custody, or world object. Also replace
the non-JSON-pointer `/EVENTS/*/FOR` notation with the two concrete array-index
pointers for every PROSPECT pair.

### P0.3 -- Opaque allocation and held filler bytes remain author-selected

Section 3 specifies the seven role-key components but does not enumerate the
literal values for `pair/world ID`, `state role`, `block purpose`, or
inapplicable components across train, interventions, chains, and canaries.
Sections 9, 10, and 13 do not produce the promised canonical role-key lists or
per-kind counts. Examples such as `s`, `query/z/gjj`, `miss/pXX/mY`, `h00`,
and `c00` do not uniquely map to the prescribed seven-field path. `start`
versus `s`, `bad_event` versus `mistaken`, or placing `mY` in the world versus
block component all conform to the prose but permute every public token.

The only complete display-order seed payload is explicitly “for train
display only.” Held panels pin selected positions but merely ask the writer to
fill all other rows with “fixed opaque/display permutations”; no held payload,
remaining-role order, or collision rule is supplied. Family C likewise
defines expected/mismatch behavior for scored tasks but not whether all 24
structural goal blocks in a mismatch world are mistaken or only the two
scored goals are. Those choices change stores and topology signatures.

Repair with committed canonical role-list bytes and expected per-kind counts
for all four materialized domains, plus exact held display permutations and
one total construction for every unscored goal/block. The checker should
derive these lists from the spec, not accept generator-emitted names as the
definition.

### P0.4 -- Separation cannot pass its own fail-closed gate

The target requires a committed PCFL/GOAL-BRAID namespace/forbidden-core
certificate and says absence or ambiguity fails closed. No such certificate
exists in the audited commit, and v2 binds no path, schema, issuer, or expected
hash for one. A source author cannot implement an independent certificate
check from exact bytes. V1 also required comparison against the preserved
Stage-1 tiny DEV inventory; v2 replaces the separation clause with six M2A
domains and PCFL/GOAL-BRAID certificates but never disposes Stage-1 tiny DEV.

The exact-line allowlist is workable, but “lexical atom” has no extraction
algorithm, so a whitespace lexer, identifier-aware lexer, and regex-token
scanner can disagree. Repair by binding a certificate schema/path/hash and
the public forbidden-core language, explicitly including or excluding the
tiny fixture with a reason, and defining the exact byte-to-atom procedure.
This can remain a construction proof; sealed instances need not be opened.

### P0.5 -- Core and rooted-signature hashes are not reproducible bytes

The graph edge vocabulary is useful, but the decisive zero-equality gate does
not define:

- the canonical JSON standard, exact keys/value encodings, or typed-role
  naming;
- how tuple-source edges `(STATE,GOAL)` and `(STATE,PORT)` enter an adjacency
  serialization;
- which vertices constitute the “public-input induced subgraph” at each
  phase and whether typed counts cover that subgraph or the full object;
- how the EVENT/PORT root pair is distinguished and serialized; or
- delimiters, vertex numbering, multiedge ordering, and the exact byte string
  hashed after the lexicographic minimization.

Thus independent implementations can agree on graph isomorphism while emitting
different decision-core and four-radius hashes. The scanner has a similar
smaller hole: its normalization is exact, but the “declared semantic aliases”
added to each forbidden ledger are never declared.

Repair with one canonical test-vector appendix: complete canonical JSON bytes,
graph/hyperedge encoding, radius-0..3 preimages and hashes for at least one
train and one held decision, plus the exhaustive alias-derivation rule.
Mutation tests then have a stable independent target.

### P0.6 -- Later decode seeds are not exact execution pins yet

The repository revision, recipe, optimizer, continuation custody, context
cap, greedy decode settings, and call/token maxima are substantially pinned
and correctly remain later gates. The seed preimage nevertheless contains an
ASCII `panel` value that is never enumerated, and `call_index` has no declared
scope (per task, per condition, or global panel order). Unlike the dropout
seed, the adapter-init and decode `low64` clauses also omit an explicit byte
slice/integer interpretation. These choices yield different seed receipts.

Repair by enumerating exact panel labels, assigning a global immutable call
ordinal from the already-declared task/canary order, and defining `low64` once
for every seed use. The authenticated model/tokenizer file receipt can remain
a later fail-closed artifact; none was inspected in this audit.

## Counts, pair structure, and resource arithmetic

An independent enumeration of the section-4 formulas confirms:

```text
cases                                      64
family A/B                                 32/32
ordinary/recovery                          32/32
reached/unresolved                         32/32
goal side left/right                       32/32
skin 0/1                                   32/32
causal pair type goal/relation             32/32 cases
recovery MISS/irrelevant/mismatch           8/8/16 cases
each recovery subtype balanced on family,
terminal, goal side, skin, and pair type    yes
```

The `recovery_match_id=(p-1,m)` map is a 32-to-32 bijection distinct from the
within-`p` causal pairing. The command arithmetic also closes:

```text
READ 96 + STEP 64 + THINK 64 + STOP 32 = 256 targets
D1 updates across arms                  = 2 * 256 = 512
D2 additional updates across arms       = 2 * 256 = 512
D1 calls                                = 96*29 + 192 + 48 = 3,024
D2 calls                                = 64*29 + 128 + 32 = 2,016
D1 generated-token cap                  = 96*4096 + 240*256 = 454,656
D2 generated-token cap                  = 64*4096 + 160*256 = 303,104
terminal calls/tokens                    = 5,040 / 757,760
```

Training-token work, elapsed time, memory, and GPU-hours are honestly left
unbound pending later receipts. No padding record is counted as a target.

## Claim and authority boundary

The allowed result remains narrowly a lab-taught exact-text controller, with
a coherent-history statement allowed only under the predeclared CLOSED minus
ATOM condition. V2 explicitly excludes parenting, own-life learning,
parametric memory, general reasoning, recurrence, and the larger flywheel.
Nothing in this audit expands those claims or authorizes materialization.

## Disposition

```text
REWORK_MCOMBINE_STAGE2A_V2 = TRUE
GO_SOURCE                  = FALSE
GO_MATERIALIZE             = FALSE
GO_MODEL_TOKENIZER         = FALSE
GO_FIT_OR_GPU              = FALSE
GO_CLAIM                   = FALSE
```

The minimum successor is not a new experiment. It is a byte-exact completion
of the existing one: finite recovery registries; legal CHECK intervention
semantics; complete literal role lists and held filler ordering; an available
certificate; canonical graph/signature/alias test vectors; and exact decode
seed ordinals. After those repairs, a fresh reviewer should be able to derive
the same public stores, targets, null traces, signature hashes, and costs
without borrowing generator choices.
