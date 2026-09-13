# Fresh readiness audit: paper-facing evolving textual memory

**Date:** 2026-09-13 PT  
**Role:** independent source/readiness and claim audit  
**Evidence cut:** repository through `1435d8f7d9c37a722e422c3dcd0e2c4e1a6a85ca`  
**Scope:** documentation only; no builder-owned source, materialization,
tokenizer/model call, fit, GPU work, benchmark root, or scientific claim

## Verdict

**GO for one bounded exact-contract pass and parallel CPU authoring; STOP for
model/GPU certification or paper-facing “strong baseline” language.**

The repository presently has a well-tested **supplied exact-address service**
under the code name `ACTIVE_LINKED_TEXT`. It does not have an implemented
evolving textual-memory agent. The historical `ACTIVE_TEXT_FIXED` is an
866-line proposal-only reflector/curator design, not source. The later
`ACTIVE_TEXT_NATIVE-v2` is a useful design memo, but its fresh audit correctly
returned **REWORK**. `ACTIVE_TEXT_NATIVE-v2.1-AUTO` exists only as that audit's
repair recommendation; its exact query, graph, common-raw, load, actor, and
resource bytes are not frozen and no implementation or certificate exists.

This work should not interrupt the current controller -> authentic two-SLEEP
junction path. Close and build the text system on CPU under a separate owner
now. Spend actor GPU only after the common one-turn actor interface is frozen
and an authentic TSJ pass makes a lifetime comparison scientifically live.

## 1. What exists, exactly

| name currently used | authoritative reality | disposition |
|---|---|---|
| code projection `ACTIVE_LINKED_TEXT` | `materialize_queries()` constructs an exact request-to-registered-row table; `read_query()` returns that row or `MISS`; it has no evolving updater, ranking, or corpus-scale access problem | retain and report as **`ACTIVE_LINKED_TEXT_SUPPLIED`**, a component/service ceiling only |
| `TEXT_SAME_SEMANTICS` / finite reader | design source exists for a fixed-row causal carrier diagnostic | keep separate from the strong on-policy opponent; it cannot earn a lifetime-baseline claim |
| `ACTIVE_TEXT_FIXED` | proposal-only LLM `REFLECT`/deterministic `CURATE`/typed-playbook system; no implementation was found under `organism_v6/`, `gpu/`, or `tests/` | archive the name; do not claim or build this larger obsolete system |
| `ACTIVE_TEXT_NATIVE-v2` | documentation design, independently audited REWORK | do not implement these bytes |
| `ACTIVE_TEXT_NATIVE-v2.1-AUTO` | smallest credible repair direction: frozen actor, automatic target-blind retrieval, raw public ledger plus public witnessed graph | **candidate to close**, not yet a frozen contract or baseline |
| access curve / plateau | no implementation, actor evidence, or certified response curve | unmeasured |

The current manuscript is stale on this point. It says a validated
`ACTIVE_TEXT_FIXED` exists and describes an adapter-free LLM reflector/curator
plus lexical+dense retrieval. Neither statement matches current evidence or
the smaller deterministic v2.1-AUTO recommendation. Do not patch prose until
one exact successor is frozen; afterward the manuscript must name that exact
configuration rather than “same validated evolving textual memory.”

## 2. Smallest system worth certifying

Freeze one name and one role:

```text
ACTIVE_TEXT_NATIVE-v2.1-AUTO(q16,B8192)
```

It is the sole claim-bearing evolving text opponent and contains:

1. the same frozen child actor and inherited entry checkpoint as the paired
   DLT branch;
2. one append-only, branch-local ledger containing every eligible public
   dispatched action/outcome once, plus exact actor-visible child
   interpretations once;
3. deterministic BM25 over raw/typed documents and deterministic PPR/MMR over
   an `AUTO_WITNESSED_GRAPH` made only from actually observed public event
   envelopes;
4. automatic retrieval before at most the first 16 ordinary actor
   continuations, using only current public task/state and accepted earlier
   task-local THINK bytes;
5. at most 512 complete-row tokens per retrieval and 8,192 returned-memory
   tokens per task, inside the same 16-nonterminal + 1-terminal and 2,048
   generated-child-token envelope used by the neural arms; and
6. immutable citations, deterministic rebuildable indexes, and read-only exam
   descendants.

The model never has to emit `RECALL`. The existing 0/64 READ result shows that
making tool-policy elicitation part of the baseline would knowingly weaken
it. Automatic retrieval adds input/retrieval work, but no actor-generation or
THINK opportunity. Report that cost; do not call the systems compute-matched.

The exact contract must settle these nine fields before source is claim-ready:

1. canonical event/document bytes, eligibility frontier, batch barrier,
   duplicate/supersession law, and public rejection-status rule;
2. exact automatic-query fields, order, escaping, caps, missing sentinels, and
   truncation side;
3. equality-only identifier mapping
   `OID = SHA256(root_salt || exact_public_id)[:128 bits]`, with a root salt
   sampled before world contents, online first-public-appearance creation,
   collision rejection, and no type/role/order/future-inventory encoding;
4. directed public event topology and the exact document/symbol graph used by
   PPR; child LINK/MODEL prose may be searchable but cannot silently create
   hidden or oracle graph edges;
5. float64 BM25/PPR/fusion/MMR/packing constants, ties, empty behavior, and
   complete-row overflow behavior;
6. one exact `RAW_PUBLIC` lane and lifecycle shared by DLT, SLEEP_FROZEN, and
   ATN, or an explicit versioned decision that DLT has no such lane;
7. exact common LF-framed THINK/final-action transport and prompt partition;
8. optional RS8 `MODEL_INTERPRETATION` as a lexical cited document only, with
   no affine solver feature or ATN-only generation calls; and
9. one root definition: independent world/writer roots conditional on one
   fixed child, or independently raised child lineages. Repeated tasks, cuts,
   twins, and decodes never increase `n`.

The current v2.1 notes are internally inconsistent about doubled access:
automatic q16 means one retrieval before each of 16 actor continuations, while
the older `q32/B16384` arithmetic implicitly adds 32 actor turns. That changes
reasoning opportunity, not just memory access. The clean upper sensitivity is
therefore **`q16/B16384`**, with 1,024 complete-row tokens per automatic
retrieval and the same 16+1 actor calls. Do not use q32 in an access-only
claim.

## 3. Minimal implementation and certification sequence

### P0 — exact contract, CPU only

Write one self-contained v2.1-AUTO contract resolving the nine fields above
and a machine-readable config/golden registry. Fresh review must find no
normative dependency on `ACTIVE_TEXT_FIXED`, hidden world solvers, certificate
answers, or the supplied exact-address table.

**GO:** all bytes, arithmetic, roots, conditions, thresholds, and stage costs
are unique.  
**STOP:** any “either/or,” library default, unbound query field, or mutable
certificate choice remains.

This can proceed immediately in parallel with Stage2A/TSJ source work.

### P1 — pure store/index implementation, CPU only

Build one canonical module, not the historical reflector/curator:

```text
event ledger -> eligible documents -> BM25 + witnessed graph/PPR -> MMR pack
```

The model-free suite must pass exactly:

- canonical round-trip/hash/citation and every eligible dispatch exactly once;
- next-continuation and sibling-batch visibility;
- future/hidden/answer/candidate/arm/cut/evaluator taint invariance;
- salted-ID equality and rename equivariance;
- insertion-order, cache warm/cold, process-placement, and restart identity;
- wrong-root/store-swap isolation;
- graph edge equality to witnessed public events only;
- complete-row packing, overflow, misses, and resource totals; and
- evaluation run/skip leaving the scientific store byte-identical.

**GO:** every deterministic assertion passes; independent checker reconstructs
the same store root and retrieval bytes without importing generator helpers.  
**STOP:** any mismatch. No actor call.

### P2 — common actor integration, CPU/injected only

Mount automatic retrieval in the same physical LF-framed 16+1 transport used
by DLT/TSJ. Prove that retrieval cannot consume a neural turn, see a private
field, write exam output back, or change the final-action parser/scorer.
Tokenizer tests must reserve output first and receipt every kept/dropped input
token; backend truncation is forbidden.

**GO:** injected exact-turn, malformed/mixed-line, max-budget, empty, full,
wrong-root, restart, and run-versus-skip tests all pass.  
**STOP:** any carrier-specific parser, retry, fallback, or actor opportunity.

P0--P2 are the only work that should run while controller -> TSJ remains the
critical path. They need zero GPU-hours and do not require TSJ outcomes.

### P3 — prompt-length/device profile, after the common actor freezes

Before scientific roots, profile exact empty-, 157-, and 571-block stores at
actor positions 1, 8, and 16, cold and warm. Use two endpoint shapes and three
technical repeats: **54 actor calls**, zero fits. Bind actual input/output
tokens, returned tokens, occupied-device seconds, CPU/RAM, and storage.

**GO:** q16/B8192 fits without truncation at 571 blocks and the complete
prospective certificate is affordable under a bound set from these profiles.  
**STOP:** no silent token shrink. If the projected certificate exceeds the
available reservation, defer the superiority claim rather than weaken ATN.

Planning only: the present short-prompt reference is 2.62 A40-seconds/call, so
the 54-call profile is far below one A40-hour; cap it at 2 A40-hours to expose
pathological long-context behavior. The short-prompt reference is not a valid
certificate/lifetime estimate.

### P4 — one four-root, maximum-load actor certificate

Run four fresh, permanently excluded roots, 16 balanced tasks/root, at the
exact 571-block lifetime load. The tasks cross opaque/reusable information,
route/different-goal/delayed/expansion endpoint, and two surface/order twins.
No identical answer row may exist in the reusable half.

Use these conditions once:

1. `FULL_PUBLIC_HISTORY`;
2. `EXACT_WITNESSED_GRAPH`;
3. ATN q16/B8192;
4. common `RAW_PUBLIC`;
5. `NONE_SHAM`;
6. truthful binding twin;
7. registered necessary cut;
8. irrelevant same-root store;
9. wrong-root store; and
10. ATN q16/B16384 access sensitivity.

That is **640 tasks, at most 10,880 actor calls, 1,310,720 generated tokens,
and 4,194,304 returned-memory tokens**. At the short-prompt rate, 10,880 calls
would be 7.9 A40-hours; long prompts dominate, so reserve a pre-profile ceiling
of **24 A40-hours**, replacing it with the P3 measured bound before launch.

The primary q16/B8192 configuration is fixed before these roots and is never
selected from their results. `NONE_SHAM`, q16/B8192, and q16/B16384 form the
minimal access response; optional lower points are descriptive only and must
not tune the primary.

All following gates are noncompensatory:

- model-free P1/P2 certificates remain exact;
- FULL, EXACT_GRAPH, and primary ATN each score `>=60/64`, no root below
  `14/16`;
- legal finals are `>=61/64` in each useful condition;
- citations/source joins are `64/64` and the complete necessary bundle is
  returned by ATN in `>=60/64`, no root below `14/16`;
- among FULL-solved cases, ATN loses at most `3/64` pooled and at most `1/16`
  on any root;
- truthful twins redirect `>=12/16` on every root;
- each preassigned atom/LINK/OLD/NEW cut family loses at least `3/4` cases on
  every root;
- irrelevant and wrong-root stores each differ from NONE in utility and
  legality by at most `3/64`, with zero false-root citation;
- FULL/EXACT_GRAPH leave at least `.10` utility headroom over NONE; and
- if RS8 is in scope, reusable-structure ATN succeeds on `>=30/32`.

**GO_STRONG_NAMED_CONFIG:** primary ATN passes every gate.  
**BASELINE_INVALID:** any primary gate fails; never count this as a LoRA win.  
**NO_PLATEAU:** q16/B16384 improves primary utility by more than `.05`, does
not fit, or later fails equivalence. This does not invalidate an otherwise
passing, exactly named q16/B8192 comparison.

Launch P4 only after an authentic TSJ pass, in parallel with its causal
attribution/backfill or RS8 preparation. This avoids delaying TSJ and avoids
spending baseline GPU time if the autobiographical mechanism itself fails.

### P5 — lifetime, staged

At five cuts and `N=16`, the on-policy ATN branch costs
`16*5*40 = 3,200` tasks and at most **54,400 actor calls**. Run it with
DLT_PERIODIC and SLEEP_FROZEN from byte-identical pre-branch scientific state;
each branch keeps only its own later outcomes and store.

Only if DLT beats SLEEP_FROZEN and the certified on-policy ATN endpoint under
the registered root-level gates, build disposable ATN indexes from DLT's exact
eligible history and spend the second 3,200 tasks / 54,400 calls. This is a
**same-history conditional system/access contrast**, not a pure substrate
contrast, because DLT-authored interpretations and ATN's graph algorithm
remain treatment-dependent objects.

The short-prompt floors are 39.6 A40-hours per 54,400-call view. A conservative
pre-profile reservation is **80 A40-hours per view**; exact P3 profiles must
replace it. Thus same-history staging can save roughly 40--80 A40-hours after
a failed primary lifetime gate.

### P6 — plateau only after a positive five-cut result

“Saturated” is not part of baseline certification. It requires two more
novelty-growing cuts in independent lifetime roots, retained old competence,
oracle headroom `>=.10`, and simultaneous 90% root-level equivalence intervals
for the late slope and each last-two increment inside `[-.05,+.05]`.

Also rerun the terminal ATN endpoint at q16/B16384 under the same 16+1 actor
envelope. Its primary-minus-doubled-access difference must be equivalent
inside `[-.05,+.05]`; a negative decline is not a plateau. If context cannot
fit B16384, access saturation is unmeasured.

The two extra on-policy ATN cuts add at most **21,760 calls** (15.8 short-prompt
A40-hours; reserve 32 before profiling). The terminal doubled-access panel
adds at most **10,880 calls** (7.9 short-prompt A40-hours; reserve 16). A
seven-cut same-history curve is optional and would add another 21,760 calls;
it is not needed to establish the on-policy baseline's local plateau.

## 4. Leakage and provenance risks that must remain visible

1. **Supplied-service relabeling:** the existing exact address table must
   never be imported into ATN ranking or called an evolving baseline.
2. **Private query taint:** automatic queries cannot include answer, candidate,
   useful-address, future, cut, branch, adapter, evaluator, or report fields.
3. **Identifier side channels:** registered slot/type/order tokens are not
   equality-only. Use salted opaque hashes and reject collisions.
4. **Graph oracle leakage:** graph edges come only from public actions the
   branch actually witnessed. No hidden topology, necessary-route registry,
   child-evaluation label, or raw co-occurrence edge is allowed.
5. **Validator feedback leakage:** rejected prose is searchable only if the
   exact status/reason bytes were shown to the ordinary actor; private reason
   codes remain audit-only.
6. **Information multiplication:** each public event and exact child
   interpretation appears once. LoRA paraphrases, replay presentations,
   wrappers, optimizer epochs, and evaluator products are not new text
   experiences.
7. **Root contamination:** tuning/profile/certificate roots never enter DEV,
   confirmation, same-history, or lifetime `n`; certificate outputs never
   write back into a store.
8. **Same-history overclaim:** rebuilding from DLT history controls unique
   experience, not the formation policy or access algorithm.
9. **Scale extrapolation:** a small store cannot qualify a 571-block life; an
   847-block seven-cut extension needs its own maximum-load preflight.
10. **Resource masking:** equal generated/action opportunities are not equal
    input tokens, compute, storage, latency, or energy. Report every lane.

## 5. Claims this sequence can and cannot support

After P4 alone:

> The frozen q16/B8192 BM25-plus-public-witnessed-graph text agent was a
> source-faithful, restartable, maximum-load-usable opponent on four excluded
> PCFL roots.

After positive P5 on-policy only:

> Under the registered finite PCFL lives, DLT exceeded that exact evolving
> text-memory system as a total on-policy system.

After the same-history view also agrees:

> The corresponding same-DLT-history conditional system/access contrast also
> favored DLT.

Only after P6 may the paper say:

> The named ATN configuration reached a practical local plateau under the
> registered novelty-growing PCFL regime, while DLT continued to improve.

None of this establishes superiority to external memory generally, a pure
text-versus-parameter carrier effect, DREAM compiler value, recurrence,
parenting, autonomous retrieval-policy learning, physical compression,
general continual learning, or an internal graph representation. Those need,
respectively, broader baselines, `TEXT_SAME_SEMANTICS`, matched
`RAW_CHRONOLOGY_LORA`, `FINAL_BATCH`, parenting factorials, a separate learned
retrieval study, byte accounting, external tasks, and representational tests.

## Final ruling

The baseline is scientifically necessary for the full paper but is not the
next scientific run. The highest-information ordering is:

```text
now, separate CPU owner: v2.1-AUTO exact contract -> store/index -> injected integration
critical path unchanged: reduced controller birth -> authentic TSJ
after first authentic TSJ pass: profile -> shared max-load ATN certificate
after connected confirmation: five-cut on-policy lifetime
only on positive gates: same-history read + seven-cut/doubled-access plateau
```

This makes the text baseline ready before the lifetime opens without spending
one controller/TSJ GPU-hour or letting a weak/unimplemented baseline create a
paper claim.

## Evidence inspected

- `AGENTS.md`
- `paper/iclr2027_experience_models/main.tex`
- `paper/iclr2027_experience_models/PCFL_MANUSCRIPT_MIGRATION.md`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md`
- `research_notes/analysis/2026-09-13_paper_claim_state_refresh.md`
- `research_notes/analysis/2026-09-13_full_objective_paper_claim_coverage_audit.md`
- `research_notes/analysis/2026-09-13_full_objective_evidence_and_pcfl_redteam.md`
- `research_notes/analysis/2026-09-13_post_relay_minimum_decisive_benchmark_ladder.md`
- `research_notes/analysis/2026-09-13_post_event_only_decisive_critical_path.md`
- `research_notes/analysis/2026-09-13_post_seq195_critical_path_efficiency_reaudit.md`
- `research_notes/analysis/2026-09-13_pcfl_recurrent_reader_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_strong_external_memory_fairness_audit.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_executable_design.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_adversarial_audit.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/2026-09-11_active_text_role_closure_amendment_v1.md`
- `research_notes/2026-09-11_active_text_compression_design_adjudication.md`
- `research_loop/plans/active_text_fixed_contract_v1.md`
- `organism_v6/pcfl_vertical_dev.py`
- `organism_v6/pcfl_vertical_prepare.py`
- `organism_v6/composition_birth_stage0.py`
- current PCFL/Stage2A/TSJ source and test inventory
