# Paper-learning architecture advisory — minimal Dream–LoRA–Think

**Purpose.** Paper-focused architecture advice only; it does not authorize runtime changes, model calls, training, or a scientific claim. This distinguishes demonstrated components from a defensible minimal experiment.

## Recommendation

Use four separable objects and one resolver used in two modes:

~~~text
public action/outcome ledger
  -> explicit semantic snapshot (truth and provenance authority)
  -> deterministic sleep compiler (one-edge training views)
  -> isolated per-life LoRA (lossy recognition transport)
  -> bounded goal-conditioned THINK (atom reads -> scratch path -> action)
                                               |
                                missing/conflicting dependency
                                               v
                       non-evidentiary replay agenda -> DREAM
~~~

The paper should not call the LoRA the world model's source of truth. The explicit ledger and semantic snapshot are episodic/epistemic memory. The LoRA is a fallible per-life transport that reconstructs one local atom under a fixed reader. The clean base model composes those returns. THINK's path is temporary; a request for DREAM is selection, never evidence.

This is the smallest mechanism that separates bad proposed writes, bad support/admission, bad compilation/training, bad parametric reads, and bad multi-hop use. It follows the current measured result: at small memory, the resolution protocol, not substrate, supplied value; the weight hypothesis starts only once memory exceeds the usable context window. [S1]

| Object | Persisted contents | Authority/use | Must not contain |
|---|---|---|---|
| Episodic ledger | Immutable public actions, observations, outcomes, intervention classes | Source of witnessed evidence and chronological testing | Hidden state, target answer, scorer, model rationale |
| Semantic snapshot | Canonical one-edge witnessed/supported/provisional/contradicted atoms, provenance DAG, status events | Audit, text/graph baseline, compiler input, target-blind reader | Plans, target solutions, free thought, support from repeats/views |
| THINK scratch | Goal, typed reads/path, hypotheses, missing/conflict records | Temporary traversal and action; creates only a replay agenda | Durable facts inferred by the thinker |
| Per-life LoRA | Compiled supported local-atom views | Recognition-assisted reconstruction of one declared atom | Provenance/status authority, literal graph, plan, cross-life knowledge |
| Loop policy, later | Cross-life operational trajectories | What to query/replay/act/stop | This life's facts/mappings |

The explicit contract already separates semantic structure and provenance depth from realization/touch pressure and thinker hypotheses. [S2] It also separately names the frozen base theta_0, per-life memory psi_l, and eventual shared policy phi. [S3]

## Minimal operational mechanism

### Wake: preserve explicit experience

The environment alone appends public action/outcome events. A deterministic parser may create witnessed one-edge atoms. This mechanical episodic cell must be available to all arms and disclosed: Paper 1 tests abstraction/consolidation above a reliable episodic base, not raw extraction. [S4]

Wake may act and emit typed operations, but its free-form workspace cannot write semantic memory. It should produce only a bounded declassified traversal projection or a missing-dependency record. The developmental-kernel proposal already excludes wake workspace from sleep and makes the projection a deterministic function of public events/operations. [S5]

### Dream: propose, do not certify

DREAM is the same resolver state machine fed a replay bundle rather than a live goal/state. It sees bounded public episodes and accepted local items. It proposes one target-independent one-edge claim with cited roots/parents and a prediction testable against later ordinary public experience. It may name an abstraction to make a future relation one hop; it may not emit a full parent set, plan, held-out answer, or self-supported fact.

This retains the useful one-machine/two-mode hypothesis without a confound: THINK and DREAM share operations, retrieval, budget and provenance interfaces, differing in input, grounding, and write permission. [S1] The strongest depth evidence also favors local revisit plus one additional check over a long monolithic transcript. [S6]

Blind self-review may be an arm, not truth evidence. The project observed outcome-visible self-check back-fitting every hypothesis as supported. [S1] Current v1f deliberately permits false same-evidence self-approvals and forbids a precision/verifier conclusion. [S7] The headline mechanism should therefore use precommitted predictions and later public outcomes under frozen support rules; self-check measures a precision–coverage trade-off.

### Sleep: deterministic compiler rather than oracle

At sealed cuts SLEEP should:

1. Resolve status from declared public evidence and frozen support rules.
2. Retain all proposals/statuses for audit but admit only supported, target-independent atoms to positive data.
3. Deduplicate identities; mix old/new and atom types by a frozen schedule; render fixed one-edge cue/value views.
4. Rebuild the lifetime adapter from a pristine base and seal corpus, snapshot, and fit receipts.

SLEEP makes no model call and cannot make a claim, add evidence, or rewrite an earlier snapshot. This is specified in the PCFL bundle and cyclic contract. [S2][S8]

Compile named concepts and directed relations, not chains or plans. Use predetermined forward, reverse, partial/incident, and declarative/QA views. G2f found that two-hop adapter reads collapse, while coined names plus one-hop facts, sufficient exposure, resolved reads, and clean-base composition reached 0.949 in the oracle-statement condition. [S9] That is a format/reader result, not proof of unbounded fixed-rank graph storage.

### LoRA: lossy recognition transport

Fit one psi_l from one sealed life. Never stack across lives or use it as the shared controller. For each read, host code first resolves zero/one/conflicting manifest values target-blind. Only a unique case scores a frozen candidate roster for a single missing field. THINK receives only ROW, NOT_FOUND, or CONFLICT and one atom; then the adapter is unmounted before clean-base continuation.

Call it recognition-assisted parametric memory, not retrieval-free recall. v1f's current fidelity condition is immediate selected-cue, candidate-constrained training-set resubstitution (48 cases per life with host cardinality resolution), not unseen access, whole-corpus storage, or generalization. [S7][S10]

What LoRA learns here:

- Local factual/relational associations in the chosen cue geometry; not epistemic truth.
- No traversal/action policy in Paper 1; otherwise world memory and controller competence are confounded.
- Potentially format/cue shortcuts. Probe reverse, paraphrase, partial cue, binding/twin swap, root masking, held-out atoms, and clean-base composition. Relation/answer-form failures are already diagnosed in G/C work. [S9][S11]

### Think: bounded decompression and action

Start every evaluation with fresh scratch and an immutable checkpoint. The resolver selects one declared atomic query, receives one local result, updates typed workspace/path, and updates/backtracks/acts/defers/releases. Every post-first query must be anchored by public state or a previous read. A multi-hop result is thus a trace property, not merely answer accuracy.

The current thinker contract is goal -> subgoal -> query/follow -> scratch hypothesis -> release/backtrack/request-dream/defer, and REQUEST_DREAM ends the attempt so the next checkpoint starts a fresh replan. [S12] A2/A3 credit requires a dependency DAG and minimal causal memory cut; lucky action is not constructive-memory credit. [S13]

Clean-base composition is required by data, not style. Direct context/LoRA methods were near floor whereas context/LoRA plus recognition and clean composition matched at a 1,086-token corpus; a mounted adapter degraded D0 relative to read-then-unmount. [S1][S11]

## Competing architectures

| Architecture | What it tests | Why not enough as headline | Paper role |
|---|---|---|---|
| Raw RAG / long context | Exact episodic access | Can win with no abstraction/compression | Strong baseline while life fits |
| Explicit graph/A-MEM | Auditable multi-hop memory | May be the better engineering answer; no parametric transport | Strong baseline/reference ceiling |
| Direct trajectory-to-QA LoRA | Raw parametric fact storage | Confounds extraction, format, training and read | Required control |
| Dreamed full summaries/plans -> LoRA | Short demos | Encodes target shortcut; write quality unidentifiable | Exclude |
| Monolithic recurrent dream transcript | Cheap recurrence | 7B and 32B generation/depth failure | Negative ablation |
| Separate bespoke dreamer/thinker | Flexibility | Mode-specific programs confound operation skill | Later ablation |
| Shared lifelong adapter | Transfer possibility | Leaks life facts and mixes memory/policy | Defer |

The paper should accept the possibility that explicit graph or RAG wins. Same-corpus text/LoRA at small scale cannot prove LoRA superiority; PCFL-Stream rightly requires active bytes and reader-work reporting. [S13][S14]

## Five identifying experiments

All use paired counterfactual twins, sealed splits/goals/budgets, a frozen controller, byte-identical common source lives where attribution requires it, and offline scoring only after all traces seal. Private truth, solver outputs, target answer, target-derived candidates, and scores must be absent from DREAM, SLEEP, reader, THINK, and training data.

### E1 — Write quality

**Unit:** one prospective, target-independent causal atom.

Hold replay blocks constant. Compare witnessed-only, raw proposal, blind self-check, chronological prediction-supported admission, chronological admission plus targeted re-dreaming from typed missing/conflict records, and an offline-only oracle ceiling. Measure syntax/newness, independent-root diversity, prospective prediction precision/recall, reusable-mapping coverage, false-row rate, relation-type breakdown, and later target-cut relevance. Retain rejected/false rows.

**Falsifier:** chronological admission does not improve the precision–coverage/downstream-availability frontier versus raw or self-check; or gains survive twin/binding shuffle. Then dreaming has not improved writing.

### E2 — Compression/generalization

First use independent PCFL-Stream cohorts for acquisition/retention. Then PCFL-Schema: source cohorts support a target-independent schema proposal; it must predict a later cohort before outcome; a fresh sparse cohort contains a decisive unknown mapping that local atoms cannot resolve.

Compare same atoms versus atoms+schema, explicit schema versus text/LoRA transport, and equal byte/rank/token budgets. Require descriptor/mapping twins, schema-binding shuffle, a post-evaluation schema leakage ceiling, and mask/twin swap of the cited schema. Report prospective prediction, retained bytes, fresh-cohort action, and paired gist/verbatim retention.

**Falsifier:** atoms match schema, schema is post-hoc, binding shuffle preserves gain, or needed capacity grows linearly. That is storage, not compression/generalization. [S14]

### E3 — Decompression/traversal

Freeze a trusted semantic snapshot, then cross:

~~~text
backend: text/graph | LoRA recognition | LoRA generation
controller: scripted read-plan ceiling | prompted bounded resolver
memory: full | mask a required root | twin substitute | path exclude
~~~

Equal semantic outcomes must produce byte-identical closed reader returns. Score atomic forward/reverse/paraphrase/partial fidelity, query selection, NOT_FOUND/conflict calibration, valid dependency DAG, minimal cut, clean-base composition, and action.

**Falsifier:** action survives root mask/twin swap; the thinker fails with oracle-good local atoms; or LoRA loses to text under identical reader semantics. Do not blame DREAM for a downstream defect or call a lucky answer multi-hop. The 32B gold-control is only an existence proof that a generic sequential protocol can execute a complete D3 blend from faithful memory, not broad autonomy/transport. [S11]

### E4 — Action improvement

Use PCFL A2/A3, then A4, with fresh handles and novel combinations. Replay a common life across no-memory, raw RAG, A-MEM/graph, direct-QA LoRA, compiled text, and compiled LoRA; match action, write, retrieval, resolver, and token budgets. Score normalized return/regret, plan success, recovery, cost, valid constructive trace, and twin-valid action. Include action/outcome binding shuffle and semantic path masking.

**Falsifier:** no-memory or target/state/identifier/passive-signature probes match memory; direct-copy closure exists; binding shuffle leaves gain; or correct action lacks its dependency cut. These are required PCFL gates. [S5][S13]

### E5 — Lifetime scaling

Use PCFL-Stream rather than repeating PCFL-13. At one pre-native and at least three strictly post-native checkpoints (provisionally 2L_native, 4L_native, 8L_native), add genuinely new independent cohorts. Plot separately:

- New-cohort acquisition, old-cohort retention, and cross-era composition.
- Unique supported mappings/minimal sufficient-statistic bytes.
- Explicit-memory bytes, adapter rank/bytes, reader work/latency, and dream/compiler/train/think compute.
- Atomic fidelity and valid constructive trace rate.

Sweep a preregistered small capacity/rank grid. Require constant-degree goal-anchor retrieval; a hidden O(total-life) scan is external search, not scalable parametric recall.

**Falsifier:** mappings plateau with raw tokens; fewer than three post-native points; acquisition stalls; retention collapses; cross-era gain vanishes after cuts; reader work is linear; or rank grows linearly. Report retention/storage, not a continuing learner/fixed-capacity law. [S14]

## Timescales

| Rate | State/learner | Legitimate content | Paper-1 status |
|---|---|---|---|
| Tokens/seconds | Scratch and operation history | Current dependency/plan; no gradient | Required |
| Episodes/sleep | Snapshot plus per-life psi_l | This life's supported local regularities | Required; reset every life |
| Many lives | Shared phi loop policy | Retrieval/replay/action/stopping skill | Deferred or prompted ceiling |
| Very many lives | Base/critic | Broad representations/acting | Outside Paper 1 |

A rank cascade/pyramid is interesting Paper-3 work, not minimal. First prove that per-life world memory and cross-life loop skill are distinct objects; the repository itself postpones cascade, learned exploration, and base promotion. [S1]

## Existing evidence: what is and is not shown

### Supported, with bounded wording

- G2f showed small-corpus parametric transport with one-hop name-mediated facts and recognition; G4h matched its 0.949 oracle-statement ceiling with a real L0 dreamer and no write-path oracle. G4k's best-rep three-world results were 0.949/0.882/0.923. [S9]
- Relation write cost differs from entity write cost; storage is relatively prior-indifferent while proposal/composition are prior-scaffolded. [S1][S9]
- C2r reports 228/228 finite-grammar recognition fidelity; recognition plus clean-base composition is materially stronger than generative adapter reading in these tests. [S9]
- At 1,086 memory tokens, context+recognition and LoRA+recognition both achieved D2=0.50; direct methods were near floor. Existing small-scale evidence does not establish LoRA advantage. [S1][S11]
- v0.2 exhaustive public branch/revisit reached 23/24 exact parents on untouched seeds 1–2. This is a scaffold/compute ceiling, not learned dreaming. [S6][S9]
- V5 is a valid negative: 0/12 true retained parents, so its corpus is barred from transport. [S1][S9]
- PCFL/PCFL-Stream and v1f are proposals/contracts, not positive experiments. v1f is an aligned engineering ceiling whose permitted LoRA result is selected-cue resubstitution recognition. [S7][S10]

### Unproven

- A generic verifier-free dream policy autonomously creates useful connected structure.
- Chronological public-outcome support beats blind model self-check at controlled compute.
- Autonomously grown connections transport through LoRA and are reconstructed by an adaptive thinker.
- Parametric transport outperforms strong text/graph/RAG after actual context saturation.
- A learned shared policy schedules dream/think/action usefully; current prompted/exhaustive traces are teachers.
- Action-selected evidence causes a later memory/action flywheel.
- Schema compression is prospective and sublinear rather than accumulation.
- Any v03r v1f canary establishes open recall, durability, generalization, whole-corpus storage, generic construction, or action gain.

## Paper claim and stop rules

The strongest credible sentence after E1–E4 is:

> In a sealed counterfactually paired causal-world assay, target-blind provenance-conditioned local consolidation from a frozen resolver improves held-out multi-step decisions over registered memory controls, while writer quality, compilation, parametric recognition transport, and bounded reconstruction are separately measured.

Add beyond context, continual growth, or LoRA necessity only after E5 observes baseline saturation at multiple post-native points. Add compression/generalization only after E2's prospective schema test. Add self-learning flywheel only after on-policy evidence acquisition changes later experience and action. This is narrower than the long-horizon thesis and consistent with the frozen goalposts: scale is where the weights claim begins. [S4]

## Source-path citations

- [S1] research_notes/IDEAS.md — Laws, ACTIVE, and ALIVE sections.
- [S2] research_loop/cyclic_organism_contract.py — module contract and record definitions.
- [S3] research_notes/42_system_thesis_and_experiment_map.md — Three nested learning timescales and rung/claim map.
- [S4] research_notes/35_goalposts_paper1.md — frozen claim, cheating boundary, memory epistemics, architecture.
- [S5] research_notes/45_developmental_kernel_pilot_v1.md — §§3–7, wake projection, writer authority, sleep/compiler, reader.
- [S6] REVIEW_PACK.md — §4f and autonomy spectrum.
- [S7] research_loop/changes/chg_20260903_paper1_v03r_end_to_end_canary_v1f/experiment_spec.md — Question, held-out organism, conditional LoRA transport and claim boundary.
- [S8] research_notes/47_pcfl_execution_bundle_v1.md — §§1 and 6–9.
- [S9] alchemy/v2_out/mini_ledger.md — G2f–G5 and C0–C3/C3s/C3stream; corroborated by REVIEW_PACK.md §§4d–4e.
- [S10] research_loop/changes/chg_20260903_paper1_v03r_end_to_end_canary_v1f/memory_transport_contract.json — candidate mapping, isolation, claim boundary.
- [S11] alchemy/v2_out/mini_ledger.md — substrate trio/2x2, gold-control, dream-ladder entries.
- [S12] research_loop/goal_conditioned_thinker.py — module contract, ExactCheckpointReader, ThinkerMachine.
- [S13] research_notes/46_pcfl_constructive_assay_v1.md — §§4–7; research_loop/recurrent_text_organism.py — snapshot/recurrent-cycle implementation.
- [S14] research_notes/48_pcfl_stream_and_schema_design_v0.md — cohorts, post-native scaling, capacity surface, schema and falsifiers.

