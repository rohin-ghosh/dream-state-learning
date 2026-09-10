# Cross-critique: RML next-experiment decision

**Status:** read-only design recommendation.  It authorizes neither a runtime
change nor a GPU dispatch.

## Decision

**Do not run the proposed all-in RML two-pair LoRA pilot yet.**  First finish
the D1 CPU instrument contract, then run a **one-cut, two-DEV-twin-pair,
text-first fixed-deck mechanism pilot** at `2 L_native`.  Its job is to decide
whether Dream--LoRA--Think has an identifiable *consolidation/use* branch worth
training weights for.  It is not a paper result, a scaling result, or a
flywheel result.

The current `rml_d0` is a good D0 base, not that instrument.  Its sealed report
passes `CPU_STAGE_A_INSTRUMENT_CONFORMANCE` with 0 model/GPU/network calls,
996 source events and 285 cumulative mappings at its largest cut.  It also
certifies deterministic twin/source/isolation mechanics.  It does **not** yet
provide the generic gold THINK factorial, source-to-semantic-snapshot/DREAM
comparison, reader/backend channel, text/graph/RAG arms, LoRA fit/read, native
window measurement, or on-policy assignment outcome required by the RML plan.
Treating the report as a pass for those omitted links would be category error.

The decisive near-term question is therefore:

> With a frozen resolver and an already-valid action world, can a
> target-blind, chronologically admitted compiled text snapshot cause cited
> post-window J/P/X actions that beat both raw episodes and an uncrippled
> explicit structural alternative?

Only a yes makes a LoRA transport experiment informative.  Even that yes
identifies **provenance-conditioned compilation plus bounded reconstruction**;
it does not identify DREAM unless the writer/admission contrast below succeeds.

## Why the claimed mechanism is presently underidentified

| Proposed phrase | What a fixed-deck success actually establishes | Missing identifying contrast | Required resolution |
|---|---|---|---|
| `DREAM` discovers useful structure | At most, a compiler used a corpus containing useful atoms | A deterministic witnessed-atom compiler, raw proposals, and chronological prediction-supported proposals are otherwise conflated | Pilot E1: same replay/call budget; compare witnessed-only, raw DREAM, and prediction-supported admission; preserve rejected rows and score prospective precision, coverage, and later action. |
| `LoRA memory` carries a world model | Candidate-constrained one-atom recognition can transport a frozen corpus | The explicit snapshot remains truth authority; reader/candidate construction may do the work | Call it recognition-assisted parametric transport.  Compare identical corpus text vs E-LoRA, D-LoRA, and a generative-read sentinel only after text clears. |
| `THINK` performs constructive reasoning | Correct action can be a prior, target, or host-reader shortcut | A generic recurrent resolver may not be able to use good local atoms | Run gold atoms/schema × nonadaptive/recurrent/open controller before learned memory.  Require recurrent J/P/X >= .85, valid trace >= .80, nonadaptive/open <= .35. |
| `RML learns across a lifetime` | One post-window cut can show retention/use | A single cut cannot show continued acquisition, retention, or comparator saturation | Reserve `2x, 4x, 8x L_native` and three packs for confirmation; no curve language in the pilot. |
| `memory improves its own experience` | Nothing in a common scripted life | Memory assignment must precede information-gathering action and later reconsolidation | Keep this as a separate randomized on-policy study; a one-block relay check is wiring only. |

The P stratum is especially valuable, but it is also dangerous: a generator-aware
program inducer is permitted to win it.  If it does, that is evidence that RML
is a useful benchmark and that the proposed parametric moat is absent, not a
reason to weaken the program baseline or re-label it an oracle.

## Recommended next experiment and decision matrix

| Stage | Minimum cells and controls | Stop / go gate | Estimated model work and GPU-hours |
|---|---|---|---|
| **D1, CPU only** | Extend D0 to the full RML V0/V1 contract over the frozen 64-pair CPU panel: actual `L_native`; N/O/J/P/X targets; no-life/shortcut probes; target-byte twins; J/P/X necessity; gold semantic snapshot; generic recurrent vs nonadaptive/open controller; no direct closure; causal mask/twin substitution; run/skip isolation. | **Stop:** any V0/V1 failure.  **Go:** exact/legal >= .85, no-life/shortcut and nonadaptive/open <= .35, recurrent gold >= .85 and valid trace >= .80. | 0 model calls; 0 GPU-h.  This is a precondition, not a billable experiment. |
| **G1, text-first fixed deck (next GPU experiment)** | Two DEV twin pairs (four world-lives), one pack, one `2 L_native` cut.  `N`, native truncated context, raw RAG, an explicit witnessed graph **and** generator-aware program learner, matched reflected-text (`X-text`), E1 writer/admission variants, and `E-text`.  All use the frozen resolver; keep all failures in denominator.  Include whole-memory twin swap and `S-bind` on at least one J and one P target per side. | **Stop:** text fails either pair to beat raw RAG and the stronger graph/program result, or E1 shows no precision--coverage/downstream advantage over witnessed/raw proposal, or causal masking/twin substitution does not redirect action.  **Go:** both pairs are directionally positive, valid cited traces are present, and `E-text` is within .10 of gold-memory gain / recovers >=70% of it. | Hard-cap 4 target-blind writer/replay batches (one/life), <=64 gold-controller episodes, <=160 fixed-deck arm×target episodes, and <=2,700 bounded resolver operations (12/episode cap).  Use the existing one-cut planning anchor: **about 4--12 GPU-h**, to be replaced by sealed first-call timings. |
| **G2, transport micro** | Same frozen four snapshots; no new DREAM or target selection.  `E-text`, `D-LoRA`, `E-LoRA` recognition, candidate-only clean base, `S-bind-LoRA`, authentic/twin adapter swap, plus one generative-read sentinel.  One adapter seed/pair is enough to reject a branch, not to estimate an effect. | **Stop:** fixed-query E-LoRA fidelity < .90, E-LoRA < E-text -.10, E-LoRA fails to beat D-LoRA directionally, or binding/twin effects are not in the authentic direction.  **Go:** only to a separately ratified calibration protocol. | 8 bounded adapter fits at most (E and D for four snapshots), plus fixed evaluation calls.  At the recorded rank-64 anchor this is roughly **0.8--7.1 adapter GPU-h**; total G1+G2 should be budgeted as **5--20 GPU-h**, not silently merged with confirmation. |
| **F0, on-policy relay sentinel** | One authentic/null-or-twin assigned-memory collection block per side after G1, equal action/query caps, one deterministic reconsolidation, and one target sealed before collection.  Cross the collected trace through compiled text, raw RAG, graph, and D-LoRA offline. | **Stop / defer flywheel:** assignment produces no different information action or no target-relevant coverage change.  **Go:** only to designing the randomized study; no effect size or flywheel conclusion. | <=4 collection episodes and <=48 resolver operations; include within G1 only if it does not displace a fixed-deck cell (roughly <=1 additional GPU-h). |

The G1 row is intentionally smaller than the architecture advisory's combined
two-pair LoRA roster.  It is not weaker scientifically: it removes the largest
avoidable ambiguity before spending on adapters.  The first positive branch
change is text/compiler/use versus strong explicit memory; LoRA can neither
repair a failed compiler nor establish DREAM necessity.

## Baselines: pilot versus confirmation

### Mandatory in G1

- No-lifetime prompted controller plus the exact no-life Bayes ceiling.
- Honest native chronology/truncation and raw episodic RAG.
- An uncrippled explicit witnessed graph and a generator-aware program learner.
  They answer different objections: storage/traversal versus prospective law
  induction.
- Matched reflected/lesson text (`X-text`) and `E-text`, with identical writer
  model, replay windows, and write-call budget where applicable.
- Witnessed-only, raw-DREAM, and chronological prediction-supported writer
  variants; `S-bind`, authentic/twin swap, and minimal cited-cut masking.

An A-MEM native arm is desirable in G1 only if a pinned, native implementation
is ready before the freeze.  A rushed imitation is less adversarial than the
graph/program pair and should not delay the branch test.

### Mandatory before any confirmation claim

Add native A-MEM/linked memory, hierarchical reflection, procedural skill
memory where the pack affords real reusable procedures, raw-event LoRA,
direct-QA LoRA, end-of-prefix batch SFT, E-LoRA, unaided generative LoRA, and
the full `S-life`, `S-bind`, and `T-swap` factorial.  Use three non-isomorphic
packs, three post-native cuts (`2x/4x/8x`), six locked calibration pairs, then
16 confirmation pairs (or the RML plan's stricter per-pack replication if that
is retained).  Do not describe an approximate TMEM/PEAM/Auto-Dreamer
reimplementation as a reproduction; their functional objections are covered
by direct-QA LoRA, procedural memory, and reflected text respectively.

## Exact promotion gates

1. **No GPU dispatch** until D1 freezes a protocol/model/tokenizer/context
   manifest and passes V0/V1.  D0's `passed: true` applies only to its stated
   Stage-A micro-preflight.
2. **No LoRA fitting** until G1 passes both DEV pairs, the writer/admission
   contrast is positive, and E-text beats raw RAG plus the stronger explicit
   baseline directionally without a failed mask/swap audit.  If graph/program
   wins, report the negative phase branch and stop weights work.
3. **No fixed-deck positive claim** until six locked calibration pairs pass:
   mean pipeline gain >= .10 in at least four of six pairs, E-LoRA read
   fidelity >= .90 per seed, RMS seed spread <= .10, E-LoRA >= E-text -.10,
   and the half-gain `S-bind` rule plus same-direction `S-life/T-swap` pass.
4. **No development/saturation wording** until three strictly post-window
   points show >= .10 `2x -> 8x` gain, no interval drop below -.05, preserved
   old relation value, growing causal coverage, and prespecified simultaneous
   plateau equivalence for every named baseline.
5. **No flywheel claim** until randomized memory assignment has positive
   intention-to-treat lower bounds for both information gain/action and sealed
   later action, after one reconsolidation.  A G1 relay sentinel cannot satisfy
   this gate.

## Should on-policy be included now?

**In the protocol now: yes.  In the primary next GPU pilot: no.**  Its cloned
memory-assignment design, action/query budget, presealed later target, and
intention-to-treat estimand must be frozen now so it cannot be retrofitted after
an attractive fixed-deck result.  But including it as a powered primary arm now
would multiply a still-unvalidated writer/reader/controller interaction and
would not identify whether a failure came from compilation, transport, or
exploration.  Run at most the F0 relay sentinel once G1 is viable.  The powered
on-policy study follows fixed-deck calibration, as the RML plan itself says.

## Decisions that genuinely require Rohin

1. **Paper objective:** Is a high-quality fixed-deck consolidation/transport
   paper acceptable if F1 later fails, or is the desired Paper-1 claim
   intrinsically the flywheel?  The latter choice should defer GPU spending
   until the full randomized on-policy study is ratified.
2. **Adversarial result policy:** Is an explicit graph or program learner being
   treated as a legitimate winner (recommended), with a negative/benchmark
   paper as an acceptable outcome?  No implementer should be allowed to reduce
   that baseline after it wins G1.
3. **Scope decision for D0:** Authorize a D1 extension of this fluid/thermal
   micro-world as the one-pack DEV instrument, or instead require a fresh RML
   implementation before any model work.  D0's current authority is CPU-only
   and its report cannot be silently promoted.
4. **GPU ceiling and model commitment:** Approve the staged 5--20 GPU-h maximum
   (G1+conditional G2), exact resolver/memory model revisions, and the rule
   that first-call timings may reduce but never expand the sealed cap.
5. **Prospective-law claim:** Decide whether P/schema is a co-primary
   near-term claim.  If yes, retain the program learner as a co-primary
   competitor and require the writer E1 prediction contrast; if no, remove P
   from the early decision rather than retaining a weak pseudo-schema test.

All remaining choices—reader return schema, exact call ledger, corpus views,
hashes, native-baseline vendor pinning, and split mechanics—are implementation
and review work constrained by the already stated contracts, not a reason to
ask Rohin to choose ad hoc details.
