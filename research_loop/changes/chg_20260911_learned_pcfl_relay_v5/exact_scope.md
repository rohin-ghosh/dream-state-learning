# Learned-organism PCFL relay V5 — scientific rework proposal

**Change ID:** `chg_20260911_learned_pcfl_relay_v5`
**State:** proposal only. No implementation, source/root/data generation,
model/tokenizer call, benchmark execution, training, LoRA/adapter/checkpoint
work, parenting, GPU use, resource acquisition, claim, release, submission, or
C11 authority.

## 1. Purpose and precedence

This proposal defines the separate learned-organism relay needed to test:

```text
own action/outcome -> supported atoms and necessary co-use links
fresh goal -> goal-conditioned traversal and action
old memory -> discriminating information-seeking action
public outcome -> one supported new write
fresh delayed goal -> necessary old-plus-new use
```

It is not C11. C11 remains a fixed-policy, fixed-topology, supplied-memory
ceiling and cannot establish learning, LoRA transport, retention, recurrence,
parenting, or lifetime improvement.

If later ratified, this V5 proposal supersedes the scientific architecture and
claim intent of these three unbound proposals:

- note 58, SHA-256
  `20cad18ac51f1ff81b44a491ceabf609b53eaff3bc5af70d486fd42429a281d9`;
- note 59, SHA-256
  `6fc2d3dd4e9b779e76e6168a57424cb5e1cdeb6cff347ebb411b23ea6e4d00a2`;
- note 60, SHA-256
  `38f1212c8a2fe9197b4fee69f564134fc571f4cf690e1deeee8ab279c6bb571f`.

Notes 58--60 are informative design history only. No phrase, value, schema, or
procedure in them is normative by implication. The only normative imports are
the following exact sections of note 59 at the digest above:

| imported section | status here | exhaustive V5 override |
|---|---|---|
| `2.1 Canonical bytes` | normative serialization law | replace `ATOM_PROPOSE` with `ATOM_QUERY_V5` and replace `COUSE_PROPOSE` with `COUSE_PROPOSE_V5` below; all other object/parser laws survive |
| `4.1 Common core and merge receipt` | normative | rename `A_CORE` to the development-only or future-confirmatory child named by the lineage manifest; no other change |
| `4.2 Text carrier` | normative | schema version becomes 5; carrier semantics unchanged |
| `4.3 LoRA carrier and exact writer transaction` | normative | schema/system delimiter names become V5; the rank-8 recipe and every optimizer, mask, exposure, transaction, and receipt value otherwise survive exactly |
| `5. B5 finite adaptive reader closure`, paragraphs 1--4 through the randomized-policy reduction | normative | four READ calls and 256 charged return tokens per call survive; delete its DEV policy-selection paragraphs and use the full exact closure plus the separately frozen controller baseline defined here |
| `8. B7 Phase-D writer, reset, and literal closure`, reset paragraph and `F_D` registry | normative | schema names become V5; all reset fields and the full closure registry survive |
| `11.1 Unit, values, and failure inclusion` | normative | applies to DEV root values as hygiene; it supplies no confirmation inference |

Every other section of note 59 is rejected as a normative source. In
particular its atom/link compilers, root theorem constants not repeated here,
phase interventions, endpoint algebra, controls, statistics, sample sizes,
power, and claim do not survive. Note 60 contributes only the rule to stop a
root at an irreversibly failed causal link; its `N=96`, five-build estimate,
omnibus chain, statistics, and claim are rejected. A fail-closed source test
must prove that implementation code cites this table and cannot read notes
58--60 at runtime.

The first permitted implementation is development-only CPU M0 plus an
explicit-text relay. LoRA relay execution remains downstream of a separately
passed writer qualification and later exact execution authority. This file is
still proposal-only and grants neither step.

## 2. Unit, child, chronology, and isolation

The scientific unit is one sealed PCFL root/twin pair conditional on one fixed
parent-deleted child. Arm forks are potential-outcome clones, not independent
children. Roots do not communicate or share learned state.

Development and confirmation use different children. `DEV_CHILD` is selected,
unblinded, and permanently labeled developmental before relay DEV. Nothing
learned from `DEV_CHILD` may choose or alter the later `CONFIRM_CHILD`.
Confirmatory use requires signed immutable receipts proving:

```text
learned-relay architecture/endpoints/statistics lock
  < confirmatory parenting unblind
  < CONFIRM_CHILD selection and seal
  < parent/nursery deletion
  < relay root generation
```

A missing or retroactively created ordering receipt makes all relay results
developmental forever. Existing CompilerGym-exposed children cannot be clean
relay children. Deployment/relay descendants never return data, weights,
notes, caches, or decisions to the childhood trunk.

The actor sees only public typed state, its own prior public interaction, and
the carrier rows returned through the common finite reader. Hidden truth,
future goals, arm labels, scores, compiler privilege, and report data remain
capability-inaccessible. Every stochastic actor, writer, and read operation is
addressed by a predeclared root/stage/object seed. The master DEV seed is the
unsigned 64-bit integer `20260911`. For UTF-8 domain string `d`, root ordinal
`r`, stage string `s`, object ordinal `o`, and technical replicate `q`, the
operation seed is the first eight bytes, interpreted big-endian, of
`SHA256("PCFL_V5\0" || u64be(master) || "\0" || d || "\0" || u32be(r) ||
"\0" || s || "\0" || u32be(o) || "\0" || u32be(q))`. Scientific arms within
one root use the same complete actor/writer/read exogenous tape; only the named
intervention differs. Independent technical replicates use distinct `q` and
are nested inside the root, never treated as roots. The future confirmatory
master seed is generated and sealed only after a confirmatory contract is
ratified and before confirmation roots exist.

## 3. Phase A — genuine action/outcome acquisition

Before an information action, the child may commit:

```text
ATOM_QUERY(schema, endpoints, value_domain,
           outcome_symbol_0 -> canonical_row_0,
           outcome_symbol_1 -> canonical_row_1,
           prior_public_citations)
ACT(experiment)
```

The canonical public object replacing note 59's `ATOM_PROPOSE` is:

```text
ATOM_QUERY_V5 := {
  "action_id":ID,"atom_slot_id":ID,"endpoint_1":ID,"endpoint_2":ID,
  "kind":"ATOM_QUERY_V5","ordinal":INTEGER,
  "outcome_map":[{"outcome_symbol":ID,"value":ID},
                 {"outcome_symbol":ID,"value":ID}],
  "prior_event_citations":[ID,...],"proposal_id":ID,"schema":ID,
  "schema_version":5,"value_domain":[ID,ID]
}
```

Both arrays are lexicographically sorted, have two distinct members, and must
equal the registered binary action schema exactly. `action_id` names the next
legal public action in the opportunity tape. There is no prediction field and
no future support-event citation. After the event, the compiler attaches only
that public event ID to the selected row's audit receipt.

The key, endpoints, two-value domain, legal experiment, and complete
outcome-to-row map must be committed before the public outcome. The total
target-blind compiler selects exactly the precommitted row named by the
observed public outcome and attaches the public event citation. It never
requires the child's pre-outcome value guess to be correct, repairs a row, or
uses hidden truth to construct model-visible content. An isolated offline
truth audit returns only a pass/fail bit to the scorer.

To claim `newly acquired`, the actor-public information set immediately before
the action must leave both values live under the exact registered prior. If
only support/transport is being tested, label the row `supported observation`
instead.

An authentic connection requires a pre-action child emission:

```text
COUSE_PROPOSE_V5 := {
  "atom_ids":[ID,ID],"citations":[ID,ID],"intended_operation":ID,
  "kind":"COUSE_PROPOSE_V5","link_slot_id":ID,"ordinal":INTEGER,
  "proposal_id":ID,"schema_version":5,"support_action_id":ID
}
```

The two atom IDs and their two distinct public support-event citations are
sorted. Both atoms must already be admitted; the proposal ordinal must precede
`support_action_id`; and that next public action must consume both exact atom
relations through the registered argument paths. The compiler canonicalizes
and admits but may not originate a link. Missing or late proposal is
`NO_CHILD_LINK_PROPOSAL`, scores the child-authorship mediator zero, and
creates no link. Report proposal rate and compiler-admission rate separately.

An authentic connection is admitted only when the two atoms are the unique
minimal semantic support for that later public action: exhaustive public-world
evaluation must give value `>=.75` with both, `<=.25` with either one removed,
and a distinct or failed unique best action after either removal. Alternative
single-atom substitutions are forbidden rather than optionally accepted.
Mere syntactic co-mention, shared chronology, or a success symbol is
insufficient. The carrier link contains only the two atom IDs and no goal,
target, path order, action, answer, or value.

Every required missing, malformed, unsupported, late, conflicting, or false
atom/link remains an adverse root value. No root, opportunity, or proposal is
replaced.

## 4. Root theorem and finite closure

Before any model call, exhaustive deterministic checks prove for every root:

- two same-start Phase-B goals require different unique multi-row paths and
  no single row, identifier, source-action string, passive signature, fixed
  routine, or proper visible-feature subset can solve them;
- both atoms in every scored authentic link are necessary;
- every truthful null uses atoms present in every compared arm and is matched
  on component size, anchor reachability, shortest-path profile, endpoint
  presence, candidate incidence, slot accessibility, hit/miss pattern, types,
  degrees, age bins, and serialized lengths;
- derangement, bridge cut, truthful twin, sham signal, Phase-C binding twin,
  no-write, sham-write, and D binding redirection preserve every property not
  named by their intervention;
- Phase C has exactly two live hypotheses and at least one legal separating
  experiment, with the authentic signal changing which experiment is
  relevant relative to matched sham;
- the Phase-D goal is hidden until after reset and has a unique minimal proof
  requiring exactly one old authentic row and the newly acquired row; and
- a leaked oracle and native symbolic graph controller score `1.0`, while the
  exact generator-prior Bayes/no-semantic shortcut ceiling is `<=.25`.

Every hidden binary relation and the two Phase-C hypotheses have the explicit
finite prior `P(value_0)=P(value_1)=1/2`, independently conditional on the
public generator constraints. The generator emits the complete finite support
and rational mass of the conditioned prior; the CPU reducer enumerates it
exactly with rational arithmetic. A rejected/implicit/Monte-Carlo prior is a
benchmark failure. `newly acquired` requires posterior `(1/2,1/2)` immediately
before the action; the public outcome must make one value posterior 1.

The finite reader permits one exact one-hop lookup per typed call and cannot
rank, shortlist, validate, infer, or follow internally. The closure theorem
enumerates the full adaptive history-dependent policy class under exactly four
READ calls, one selected candidate per call, and a fixed logical return charge
of 256 tokens per call. At each reachable history it includes HIT, MISS,
UNAVAILABLE, MALFORMED, stopping, repeated queries, one terminal action, and
the common RNG counter. It must pass four golden fixtures: optimal query two
depends on query one's returned row; HIT and MISS select different next
queries; the exact adaptive optimum strictly exceeds every fixed nonadaptive
schedule; and the enumerator returns that optimum with lexicographic policy
tie-breaking. A DEV-selected controller is reported only as a frozen baseline
and is never called an exhaustive distributional ceiling.

Any theorem counterexample invalidates that benchmark version before actor
execution.

## 5. Carrier and E2 interventions

Both carriers expose the same canonical rows through the same finite read
contract. LoRA is mounted only for READ; a common clean resolver/actor acts.
Every build starts from the same sealed effective child and has immutable
input, mask, seed, optimization, output, mount, and rollback receipts.

Required semantic assignments are:

- `LINK_AUTH`: authentic atoms plus necessary authentic links;
- `ATOMS_PAD`: the same authentic atoms plus resource-matched inert padding;
- `LINK_DERANGED_BUILD`: a separately built degree/path/resource-matched
  derangement;
- `LINK_NULL`: truthful irrelevant links over atoms present in every arm;
- `LINK_AUTH_READ_PERM`: the exact authentic carrier with a presealed
  same-build link permutation applied only at READ;
- `BRIDGE_CUT`: necessary authentic return replaced by a matched miss;
- `BRIDGE_TWIN`: necessary authentic return and world binding replaced by a
  truthful matched twin that requires the twin-valid action;
- adapter off and wrong-life carrier; and
- explicit exact-text versions of the same semantic assignments.

`ATOMS_PAD` is the absence-of-link-content intervention, not an identical-data
claim. Relative to `LINK_AUTH`, it is matched exactly on example count,
rendered input tokens, gradient-bearing target tokens, optimizer steps and
counters, build-slot order, model calls, candidate incidence, four READ calls,
and `4*256` logical return-token budget. Its targets contain no valid link
delimiter or relation content. `LINK_NULL` is the strongest equal-labeled-dose
semantic control: truthful irrelevant links are matched one-to-one with
authentic links on example count, input/target token class, exposures, build
position, optimizer counters, endpoint types, degrees, age, catalog slot,
candidate incidence, and read budget. No perfect deterministic match is an
adverse root failure. The separately built derangement uses the unique
lexicographically first fixed-point-free permutation preserving this same
vector plus component size and shortest-path profile.

PCFL spill is the union of: a returned wrong anchor, wrong selected candidate,
wrong canonical row, malformed/noncanonical row, or downstream action outside
the action set licensed by the exact returned path. Each category is printed;
any spill in a required positive cell fails that carrier's spill gate.

E2 requires atomic fidelity/retention, `LINK_AUTH - ATOMS_PAD`,
`LINK_AUTH - LINK_NULL`, and authentic advantages over both separately built
and same-build read-time derangements, with bridge/twin, adapter-off,
wrong-life, interface, spill, and shortcut gates. Define separate binary root
products `R_E2_TEXT` and `R_E2_LORA`; each contains only the named carrier's
predicates. Their joint product is diagnostic only. Passing `R_E2_TEXT`
permits an exact-text semantic-carrier statement. Only passing `R_E2_LORA`
permits:

> Canonical action-derived atom and child-proposed, compiler-admitted necessary
> co-use records were transported and behaviorally used through the fixed
> per-root relay LoRA under the registered PCFL reader.

It does not prove a latent graph geometry inside weights or compression.

## 6. Phase B and E4 — goal-conditioned traversal

Two fresh goals share byte-identical public start state and carrier. Before
the decisive action the actor must publicly emit a strict typed sequence of
goal anchor, READ selections, FOLLOW selections, and one ACT. No private
chain-of-thought is scored or required.

E4 requires both goals to select their distinct authentic paths and valid
actions. `GOAL_SWAP` holds actor, public state, carrier, catalog, action menu,
and complete exogenous tape fixed and changes only the public goal bytes; it
must change the first path-relevant query, exact followed path, and final
action to the second goal's registered values. `GOAL_ONLY_NO_MEMORY` shows the
goal and byte-identical public state with carrier semantics replaced by matched
MISS returns and must score `<=.25`. Bridge cut must remove value; truthful
bridge twin must redirect both path and action; authentic must beat atoms,
null, and deranged conditions; and every registered shortcut policy must fail.
The symbolic graph controller and leaked oracle are positive instrument
checks.

Define `R_E4_TEXT=R_E2_TEXT*E4_TEXT` and
`R_E4_LORA=R_E2_LORA*E4_LORA`. Passing permits only carrier-specific
functional goal-conditioned traversal through the public reader under this
world/interface.

## 7. Phases C/D and E5 — complete expansion relay

From one sealed pre-C state, `AUTH_SIGNAL` and a fully matched `SHAM_SIGNAL`
each continue through the child's first pre-outcome committed legal public
experiment (or adverse failure if none), outcome,
compiler result, carrier write/no-write intervention, sterile reset, and the
same sealed Phase-D goal. `REACHOUT_OFF` denies the already selected authentic
experiment after equal opportunity and cost.

Before the Phase-C outcome, the actor must publicly commit a supported gap,
two live hypotheses, one legal registered experiment, and its complete
outcome-to-row map. Measure authentic-minus-sham contrasts for gap
identification, experiment selection, and target-relevant expected information
gain. Target EIG is the exact rational entropy reduction of the registered
binary target under the finite uniform prior in Section 4; ties are broken by
the lexicographically smallest canonical action bytes. A separate Phase-C
action/outcome binding twin preserves action and outcome marginals but applies
the presealed involution that swaps the two public outcome symbols. Its
precommitted map must therefore select the twin row and its delayed D action
must redirect to the registered twin action; retaining the original row, path,
or action fails the binding-twin predicate. `NO_ADMISSION` is not success in
this twin.

The `SHAM_SIGNAL` path is fixed prospectively: its selected public experiment
produces one truthful, supported, previously uncarried but D-irrelevant atom;
that atom is admitted and written in the reserved D slot. It is matched to the
authentic new row on schema, endpoint/value types, canonical byte and token
class, evidence count/age, build slot, exposures, optimizer steps, and logical
read budget. Missing that row is adverse failure; neither `NO_ADMISSION` nor a
post-outcome choice of another sham is allowed.

After the common authentic public outcome, fresh D processes compare:

- `EDGE_WRITE`: exact authentic new row;
- `NO_WRITE`: no new semantic row under matched build schedule;
- `SHAM_WRITE`: matched supported irrelevant row;
- `NEW_BIND_SWAP`: authentic build with fixed read-time endpoint redirection;
- old-row cut; and
- wrong-life/adapter-off controls.

The D goal is revealed only after sterile reset. It must require and publicly
traverse exactly one old authentic row plus the new row. Required E5 effects
are authentic-vs-no-write, authentic-vs-sham-write, new-binding redirection,
old-row cut, authentic-vs-reachout-off, and the total path:

`AUTH signal -> actual action/outcome/write -> delayed value`
minus
`SHAM signal -> actual action/outcome/write -> same delayed goal value`.

All public action, outcome, compiler, write, read, and later-action mediators
are reported. Define `R_E5_TEXT=R_E4_TEXT*E5_TEXT` and
`R_E5_LORA=R_E4_LORA*E5_LORA`. Missing any link blocks that carrier's E5.
The maximum claim is a one-cycle expansion relay, not recurrence or a
flywheel.

## 8. Strong text comparator

The exact semantic text carrier validates the relay and matches carrier
semantics, but is not by itself the strong memory-agent baseline. Every full
E5 DEV or future confirmation run includes a frozen candidate-blind active-text system
over eligible raw public records, with bound updater, retriever, query,
tie-break, rendering, truncation, miss behavior, evidence citations, token
budget, action opportunities, and write latency.

Before comparison it must pass record faithfulness, retrieval recall,
citation identity, store-swap sensitivity, row-use, end-to-end relay, and
headroom gates. A failed text integration is `baseline invalid`, never
evidence for parametric superiority. LoRA need not beat text for E2/E4/E5;
superiority language requires a separate prospectively powered comparison.
`BASELINE_INVALID` blocks full E5 release but does not turn any learner field
positive or erase already valid carrier-specific E2/E4 instrument results.
The exact active-text model/tokenizer/prompt/updater/retriever/parser/session/
retry manifest must be sealed before its first model call; until that manifest
exists, active-text execution is forbidden rather than left to an implementer.

## 9. Separate noncompensatory releases

There is no omnibus result that suppresses a valid lower rung. Define nested
failure-inclusive root indicators separately by carrier:

```text
R_E2_TEXT = ACQ * LINK_AUTHOR * TEXT_FIDELITY * TEXT_CONNECTED
            * TEXT_E2_CONTROLS * (1-TEXT_SPILL)
R_E2_LORA = ACQ * LINK_AUTHOR * LORA_FIDELITY * LORA_CONNECTED
            * LORA_E2_CONTROLS * (1-LORA_SPILL)
R_E4_k = R_E2_k * BOTH_GOALS_k * GOAL_SWAP_k * GOAL_ONLY_FAIL_k
         * BRIDGE_CUT_k * BRIDGE_TWIN_k * E4_CONTROLS_k
R_E5_k = R_E4_k * AUTH_SELECT_k * SHAM_SELECT_k * BIND_TWIN_k
         * AUTH_WRITE_k * SHAM_WRITE_k * NOWRITE_EFFECT_k
         * NEW_BIND_REDIRECT_k * OLD_CUT_k * REACHOUT_EFFECT_k
         * TOTAL_PATH_k * E5_CONTROLS_k
```

Here `k in {TEXT,LORA}`; every symbol is the strict conjunction of all fixed
cells named in Sections 3--8. A required positive missing, malformed, or
technical-failure value is `0`; a leakage/spill/control failure value is `1`;
a benchmark/hash/capability violation yields `BENCHMARK_INVALID` before any
learner product is evaluated. Each factor occurs exactly once. The optional
dual-carrier product `R_Ex_BOTH=R_Ex_TEXT*R_Ex_LORA` is diagnostic unless a
future contract powers it.

Test and release in fixed order `E2 -> E4 -> E5`, separately for TEXT and
LoRA. Missing or post-exposure
failed cells are adverse-filled. E5 failure cannot erase a passed E2 or E4
claim. Component vectors and continuous scores remain visible for diagnosis.

This proposal fixes no confirmatory `N`, SESOI, interval, or power law. DEV is
performed only with `DEV_CHILD`. After DEV, endpoints and a statistics/power
law may be proposed and independently ratified. Only then may the separate
`CONFIRM_CHILD` parenting result be unblinded or selected. Post-unblind design
work permanently labels that child developmental and requires a later child
for confirmation. DEV may select no endpoint or threshold; it may only yield a
separately ratified fixed design or STOP.

## 10. E0 and development sequence

No LoRA PCFL result is interpretable until one writer representation passes:

```text
conditional multi-key mapping carriage
AND wrong-life/adapter-off specificity and bounded spill
AND native-interface preservation and generic non-harm
AND survival through one identity-disjoint cumulative write
AND exact PCFL-row read fidelity
```

This is `PCFL_E0_V1`, not an automatic promotion of the unimplemented
multi-key writer V6 proposal. Its fixed DEV task has two identity-disjoint
roots in ordinal order. Per root, build from clean child: `AUTH8` carrying
eight canonical PCFL rows over four anchors; `DERANGED8` carrying the same
row marginals under the registered fixed-point-free anchor permutation; and
`CUMULATIVE12` carrying `AUTH8` plus four new rows with disjoint endpoints.
Each has two technical fits (`q=0,1`), reduced inside root by conjunction.
E0 passes only if, on both roots: all eight AUTH rows and all twelve cumulative
rows are returned byte-exactly on the first charged READ; adapter-off and
wrong-life return no correct target row; deranged queries follow the deranged
binding rather than the original; total wrong-anchor/candidate/row/malformed
spill is zero; all 32 seeded native-interface prompts emit one legal typed
action; and the mean generic-task score is no more than `.05` below the paired
adapter-off score. Any failed fit, mount, receipt, or cell is adverse. This is
a development writer qualification only; a later confirmation may require a
new writer gate.

The information-efficient sequence is:

1. implement CPU M0, lineage isolation, compilers, theorem, reader/controller
   closure, interventions, reducer, resources, and receipts;
2. require a fully scripted positive relay and mutation suite;
3. run one exact-text parser/session canary, then roots `dev_0000` through
   `dev_0003`, and extend to `dev_0004` through `dev_0007` only if at least two
   of the first four have `R_E2_TEXT=1` and `R_E4_TEXT=1`; no failed root is
   replaced;
4. qualify E0 independently;
5. on the first root in that sealed order with `R_E4_TEXT=1`, begin with
   `AUTH_OLD`, `DERANGED_OLD`, and `EDGE_NEW` LoRA builds; stop on an
   irreversible core failure; if no root qualifies, stop;
6. only after the core survives, execute every remaining null, sham, cut,
   wrong-life, off, binding, interface, and active-text control required for a
   complete one-root result; and
7. run at most eight LoRA DEV roots for feasibility/covariance/cost before any
   separate confirmation proposal.

No source implementation or execution is authorized by this proposal.

The complete distinct LoRA build roster per attempted relay root is exactly
`AUTH_OLD`, `ATOMS_PAD`, `DERANGED_OLD`, `LINK_NULL`, `EDGE_NEW`, and
`SHAM_NEW`: six clean-base fits. Cuts, goal swap, read permutation, binding
twins, adapter-off, and reachout-off are read/world interventions and create no
additional fit. Thus the maximum eight-root relay DEV is 48 fits. E0 is 12
fits (2 roots * 3 builds * 2 technical fits), for an all-in maximum of 60
fits before any future confirmation. Exact actor/read call and rendered-token
maxima must be mechanically derived from the frozen root/arm matrix before a
run grant; a mismatch between projected and materialized counts is `NO_GO`.

## 11. E6 and compression are separate

Independent one-cycle relay roots are not a lifetime. E6 requires a later
sequential same-life protocol with multiple expansion cycles, future-goal
blindness at every write, at least three fixed checkpoints after a prospective
active-text local plateau, unrelated-write retention, recurrence-off,
write-off, and bridge-removal ablations, evolving LoRA and evolving active
text under equal public outcomes/affordances, and multiple independent
child/life roots. The relay may qualify the mechanism; it supplies no E6
evidence.

Compression requires a separate registered total-state rate--distortion
accounting boundary and feasible physical crossover. Neither fixed rank,
small files, semantic distillation, nor a relay pass establishes compression.

## 12. Acceptance-test families before any later actor execution

A later scoped implementation must pass deterministic tests for:

- canonical bytes, schemas, IDs, strict parsing, and malformed mutations;
- chronological support, complete pre-outcome maps, conflict/revocation, and
  hidden-truth noninterference;
- two-atom necessity, root/twin theorems, truthful nulls, derangements,
  bridge/twin redirection, C equipoise, D old/new uniqueness, and every
  shortcut controller;
- adaptive reader closure and charged calls/tokens;
- exact-text carrier fidelity and scripted/leaked-oracle completion;
- all A/B/C/D phase transitions, intervention timing, fresh-process sterile
  resets, and cross-branch contamination attacks;
- clean lineage, no-return descendants, source mutation, unknown ancestry,
  symlink/path aliases, transaction crash/rollback, and stale markers;
- response-only masks, writer optimization, mount/off, wrong-life, retention,
  interface, and row-read tests before LoRA release; and
- reducer nesting, adverse missing values, separate E2/E4/E5 releases,
  resource accounting, and confirmation-feedback attacks.

## 13. Closed authoring boundary and executable test registry

A later source-authoring grant may create or edit only:

```text
organism_v6/pcfl_relay_v5/{schema,ids,serialize,generator,prior,compiler,
theorem,reader,controller,interventions,phases,reducer,resources,lineage,
text_carrier,active_text,e0,writer,transactions,runner}.py
tests/pcfl_relay_v5/test_*.py
tests/pcfl_relay_v5/fixtures/{golden,mutation}/**
research_loop/changes/chg_20260911_learned_pcfl_relay_v5/{manifests,receipts}/**
```

Development outputs may be written only beneath
`v6_out/pcfl_relay_v5_dev/`. Source processes must fail closed on network,
CUDA, model/tokenizer import or load, benchmark/root-data generation outside
the deterministic fixture command, childhood/parenting path access, child
weight access, and any C11 path or artifact. C11 code may not be imported.
Text/model/E0/LoRA execution each requires a later, separate grant naming
exact manifests and commands.

The deterministic registry below is normative. Every test writes one canonical
JSON receipt with `{test_id,setup_sha256,observed,expected,status,
falsifies,artifact_sha256,code_sha256}`. `required_before=CPU` gates any actor
call; `TEXT` gates the text canary; `E0` gates writer qualification; `LORA`
gates relay fits. The future implementation packet must bind exact fixture
hashes and commands; absent hashes make the relevant stage unauthorized.

| test IDs | setup and exact expected result | falsifies | required before |
|---|---|---|---|
| `AUTH-001..004` | import graph contains only the allowlist; simulated network/CUDA/model/child/C11 opens each fail | source/capability closure | CPU |
| `GRAM-001..008` | golden objects round-trip byte-exactly; duplicate keys, unknown fields, invalid UTF-8/NFKC, aliases, booleans-as-int, trailing bytes each reject | canonical identity | CPU |
| `SEED-001..004` | fixed seed vectors equal registered hex; arm order/restart leaves tapes byte-identical; `q` alone changes technical tape | causal coupling | CPU |
| `GEN-001..006` | eight DEV IDs materialize once with exact count; rerun is byte-identical; collision, redraw, root replacement, or confirmation ID access fails | prospective roots | CPU |
| `PRIOR-001..004` | finite support masses sum exactly to one; C and A pre-action posterior is `1/2,1/2`; public outcome makes one value 1; hidden truth mutation cannot change visible bytes | genuine acquisition | CPU |
| `ATOM-001..008` | complete early map admits selected truthful row; missing/late/map-conflict/false/malformed/revoked/duplicate cases yield their fixed adverse status | atom compiler | CPU |
| `LINK-001..010` | early child proposal plus unique two-atom necessity admits; missing/late/compiler-created/one-atom-sufficient/duplicate-support/paraphrased-same-evidence/conflict/revocation cases do not | child-authored connection | CPU |
| `MATCH-001..006` | null/pad/deranged match vectors equal on every registered field; single-field mutations fail; derangement is fixed-point-free and lexicographically unique | causal controls | CPU |
| `THEOREM-001..010` | oracle positives meet `.75/.90`, all proper supports/shortcuts `<=.25`; leaked oracle is 1; cut/twin/sham/D uniqueness and all feature masks behave exactly | benchmark validity | CPU |
| `CTRL-001..006` | exact DP includes HIT/MISS/error/repeat/stop; adaptive fixture beats every nonadaptive schedule and is found; tie policy is lexicographic | controller closure | CPU |
| `PHASE-001..010` | A/B/C/D transitions match the state table; premature goal/write, cross-fork state, stale cache, nonsterile reset, and post-outcome intervention each fail | temporal causality | CPU |
| `REDUCE-001..010` | exhaustive Boolean truth tables match carrier-specific E2/E4/E5 products; missing values adverse-fill; benchmark invalidity has precedence; lower rung survives higher-rung failure | claim algebra | CPU |
| `LINEAGE-001..010` | realpath/symlink/hardlink/unknown-ancestry/source-mutation/no-return/crash/rollback/stale-marker/cross-root attacks all fail | clean child/root isolation | CPU |
| `RESOURCE-001..004` | sealed matrix reports exactly 12 E0 and at most 48 relay fits; materialized calls/tokens/builds equal projection; any excess fails | workload lock | CPU |
| `TEXT-001..008` | model-visible bytes, parser, fresh session, timeout/retry, exact HIT/MISS, store swap, citations, and same-semantics carrier match golden results | text instrument | TEXT |
| `ACTIVE-001..007` | updater faithfulness, candidate blindness, retrieval recall, citation, store-swap, row-use, relay, and headroom all pass or output `BASELINE_INVALID` | strong text baseline | TEXT |
| `E0-001..010` | masks/EOS, AUTH8, DERANGED8, CUMULATIVE12, off, wrong-life, spill, native interface, non-harm, clean mounts, and two technical-fit conjunction match Section 10 | writer qualification | E0 |
| `LORA-001..010` | exact imported recipe, response mask, zero-state builds, transaction receipt, crash rollback, mount/off, first-positive-root selection, read bytes, wrong-life, and six-build roster pass | parametric relay | LORA |

## 14. Fixed development materialization contract

The CPU generator must emit, for each of exactly eight DEV roots, one closed
manifest containing: root/twin public and hidden bytes; exactly two Phase-B
goals; all Phase-A atom/link opportunities; exactly two Phase-C hypotheses;
the complete legal action/outcome table; authentic, sham, twin, null,
derangement, bridge, and D intervention tables; catalog slots; canonical row
decks; complete finite prior; common exogenous tape addresses; exact theorem
proof; and the full phase-by-arm-by-carrier matrix. IDs are derived only from
the Section-2 seed law and semantic objects. There is no hand-authored DEV
root, behavior-conditioned retry, or alternate generator.

The matrix must enumerate every positive and adverse arm before root bytes are
shown to an actor. `GOAL_SWAP` is the only goal-byte intervention. Phase-C
binding twin always redirects. SHAM always writes the truthful irrelevant row.
Same-build read permutation never trains a new adapter. All actor episodes have
four READ opportunities and one terminal action; unused opportunities are
charged. These choices are closed and cannot be selected from observed data.

The model/tokenizer/chat-template identity is not a free scientific choice: it
is exactly the selected child's sealed lineage manifest. The clean resolver is
that same child with the relay adapter absent; the relay adapter is mounted
only for the canonical READ response, then removed before the resolver acts.
All generation settings and retry/timeout behavior must be copied byte-for-
byte from that lineage's presealed deployment policy into the later execution
manifest. If no such complete policy exists, execution stops rather than
choosing one here.
