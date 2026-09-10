# One-parent/one-child strong-memory baseline gate v1

Date: 2026-09-06

Status: **fresh independent read-only design audit**. This advisory changes no
approved bytes and authorizes no implementation, model/tokenizer call, task
generation, LoRA fit, benchmark, external deliberation, or GPU use.

## Verdict

**BLOCKING for any claim that the proposed system beats a strong agent-memory
baseline, continues after such a baseline saturates, or is submission-ready
at that claim level. NONBLOCKING for proposal-only deliberation, writer
calibration, and the four-root parenting/teachability spending gate.**

The current candidate says that every deployment service retains an “active
textual/external memory interface,” and lists a terminal same-corpus text
carrier and a matched LEAFE-style batch writer. That is resource parity and a
diagnostic intention, not a reproducible baseline:

- no active-text record schema, update policy, update cadence, retrieval
  policy, returned-token budget, capacity policy, or development strength gate
  is bound;
- no inferential contrast against that memory system is registered;
- the root-count rule is powered only around the parenting-by-write
  interaction `D`, which does not imply `P1>P0` or `P1>R0`;
- a terminal same-corpus carrier is post hoc carrier localization, not an
  online agent-memory system or a lifetime curve; and
- a final “LEAFE-style” fit is not defined sufficiently to prove reflection,
  rollback, improved-branch collection, reflection removal, rehearsal, or
  matched training dose.

This gap is repairable without changing the public one-parent -> one-child ->
parent deletion -> deployed learner versus ordinary agent story and without
adding a sixth longitudinal service.

## Closest-work ruling

The broad territory is occupied. LEAFE internalizes feedback-grounded recovery
from reflected and rolled-back branches; Early Experience learns from own
alternative actions and resulting states; ACE evolves an external playbook by
generation, reflection, and incremental curation; Evo-Memory's ReMem performs
an action--think--memory-refine loop; MemoPilot trains an online textual-memory
updater for a frozen player. Therefore:

- do not call prompted raw RAG a strong memory baseline;
- do not call the proposed fixed updater a MemoPilot reproduction (MemoPilot's
  updater is separately RL-trained);
- do not call the bounded rank-8 batch control a LEAFE reproduction (published
  LEAFE uses its own branch-generation pipeline and full-policy SFT); and
- any favorable comparison is only under the registered CompilerGym model,
  context, update, read, and compute envelope.

The smallest credible pair is one **ACE/ReMem-style active text system** run at
all lifetime cuts plus one **bounded LEAFE-style terminal writer**. Early
Experience, MemoPilot, and Evo-Memory remain direct prior art and external
validity references; reproducing all of them before the headline would waste
GPU-hours and create several incomparable systems.

## Mandatory confirmatory baseline: common `ACTIVE_TEXT`

Turn the already-promised common memory layer into one frozen system and give
it unchanged to `R0`, `U0`, `U1`, `P0`, and `P1`. No classroom, peer, shared
memory, or cross-root data is introduced. Each service owns an isolated store.

### State and update contract

Each store contains:

1. an unbounded append-only raw public ledger; and
2. an incrementally edited playbook of typed records:

```text
memory_id
claim_or_observation
scope
action_guidance
support_event_ids[]
counterevidence_event_ids[]
linked_memory_ids[]
status = PROVISIONAL | SUPPORTED | CONTRADICTED | SUPERSEDED
supersedes_memory_id | NONE
```

After every one of the 48 deployment programs, a pinned **adapter-free child
base** performs two target-blind memory calls over only that service's public
trace and current store:

1. `REFLECT`, at most 512 generated tokens, identifies reusable successes,
   failures, contradictions, and scope changes with ledger citations.
2. `CURATE`, at most 384 generated tokens, emits only typed
   `ADD | REVISE | LINK | SUPERSEDE | NOOP` deltas.

The deterministic merger checks identifiers, source existence, chronology,
and schema only. It never uses hidden compiler state, probe results, future
outcomes, semantic correctness, or an LLM judge. Malformed deltas are retained
as failed events and yield no update; roots are never replaced. Exact prompts,
template, model revision, greedy decoding, store format, merger, and update
cadence are frozen before spending roots.

This is an ACE/ReMem-style functional comparator, not MemoPilot: it uses a
frozen prompted updater rather than a separately outcome-trained memory
policy.

### Read contract

Before each ordinary actor continuation, a deterministic hybrid lexical+dense
retriever searches both the playbook and raw ledger, expands at most one link
hop, and returns at most four complete records in at most 1,024 input tokens.
The actor may use the same typed raw-ledger search tool under its existing
12-call program budget. No structured-record-count, raw-ledger, or index-byte
cap may be chosen to make weights win; report all stored bytes, index work,
returned tokens, retrievals, and updater calls. The context and returned-token
limits are the named deployment envelope, not a universal memory limit.

The same external-memory mechanism is present in all cells. Thus:

- `R0` is the public ordinary agent: raw frozen actor + `ACTIVE_TEXT`;
- `P0` is the strongest internally controlled text baseline: the exact
  parented entry checkpoint + `ACTIVE_TEXT`, deployment LoRA writes off; and
- `P1-P0` isolates the value of deployed Think--Dream--Sleep writes **on top
  of** the same parenting and active text memory.

### Strength gate

Before any spending root, require on disjoint development fixtures:

- `>=.95` target-record recall@4 on 100 sealed exact/link/contradiction
  queries, with 100% returned-event citation validity;
- active retrieval within `.05` task value of directly injecting the same
  relevant records on 24 target-blind development programs; and
- at least `.05` task-value gain from the oracle-inserted supported playbook
  over an empty store, with no routing/non-erasure failure.

Failure means the external baseline is crippled: repair on development or
report `NOT_RUN`; never retain the phrase “strong memory baseline.” Scientific
results may not tune the updater, schema, retrieval weights, or read budget.

## Confirmatory endpoints and power

Keep the registered parenting interaction `D` primary. Add a hierarchical
strong-baseline gate, evaluated on the same independently raised roots:

```text
C_text   = gAUC(P1) - gAUC(P0)
C_public = gAUC(P1) - gAUC(R0)
```

Only after `D` passes, test `C_text`; only after `C_text` passes, test
`C_public`. Each requires a positive two-sided 95% root-level interval, a
point estimate at least the registered `.05` SESOI, and the existing routing
and proposal-quality non-erasure gates. Fixed-sequence gatekeeping preserves
the headline family without a post hoc maximum over baselines.

This matters because positive `D` can occur when deployment writes harm `U1`
more than `U0`; it does not mathematically entail that `P1` beats its parented
active-text twin. Likewise `P1>R0` alone can be inherited parenting competence.

At the blinded `n=12` variance release, disclose no arm means but compute the
upper uncertainty bound for the SD of `D`, `C_text`, and `C_public`. The
existing `n=20` stop is legal only if **all mandatory contrasts** satisfy the
registered `.075` SD rule; continue to `n=32` if all satisfy `.10`. Otherwise
omit a powered joint-superiority claim. Powering `D` alone is insufficient.

## Exact bounded LEAFE-style terminal comparator

This is mandatory if the manuscript says periodic within-life writes beat a
strong batch-internalization alternative; it is not the external-memory
saturation baseline.

Reuse each root's authentic `P0` deployment history—no additional 48-program
life. For each program, mechanically select the earliest registered failure or
expectation-violation point. From that historical state:

1. one frozen adapter-free reflector call (maximum 256 tokens) emits a
   feedback-grounded diagnosis;
2. one frozen adapter-free recovery call (maximum 512 tokens) sees the
   original history plus diagnosis, then emits one revised native action;
3. the environment rolls back, dispatches that action, and admits it only when
   its registered public result improves over the original branch; and
4. the diagnosis is removed from the SFT input. The original failure history
   maps directly to the improved native response target.

Use the same parented childhood rows, rank-8 all-layer placement, response-only
mask, selected heat, four target exposures, exact 320-position terminal
geometry, and 20% successful-behavior rehearsal as `P1`; deterministic
rehearsal fills failed branch slots. Rebuild once from clean base, mount the
terminal `P0` active-text snapshot, and run the same eight-probe panel.

Call this `LEAFE_STYLE_FINAL`: one branch per program and rank-8 LoRA are
explicit deviations from published LEAFE. The only allowed claim is relative
to this bounded matched implementation. Register

```text
C_batch = V_P1(48) - V_LEAFE_STYLE_FINAL(48).
```

If batch superiority is claimed, gate it after `C_public` with the same
positive 95% interval and `.05` point-estimate rule, and include its contrast
SD in the blinded root-count decision. Otherwise report it descriptively and
do not say periodic consolidation beat LEAFE.

## Conditional, exact saturation sentence

Do not use “saturates” merely because a slope is nonsignificant. The only
permitted sentence names `P0+ACTIVE_TEXT` and its exact envelope:

> Under the registered 48-program, 1,024-return-token-per-actor-continuation,
> two-update-call-per-program envelope, the parent-matched active-text baseline showed no
> practically meaningful improvement over its last two eras while P1
> continued improving.

It requires all of:

1. simultaneous TOST/max-t 90% root-level intervals for
   `V_P0(32)-V_P0(16)` and `V_P0(48)-V_P0(32)` wholly inside
   `[-.05,+.05]`, where `.05` is the registered SESOI;
2. a presealed, cognition-hidden 10,000-sequence fixed-seed compiler search
   reference at least `.10` above `V_P0(48)`, ruling out task ceiling;
3. the 95% lower bound for `V_P1(48)-V_P1(32)` above zero; and
4. the 95% lower bound for the last-era difference-in-differences
   `[V_P1(48)-V_P1(32)]-[V_P0(48)-V_P0(32)]` above zero, with point estimate
   at least `.05`.

If any condition fails or `n<=32` cannot make the equivalence intervals
precise, omit saturation language and report curves, last-interval changes,
and the resource frontier. This is a conditional extension, not a reason to
delay the parenting interaction.

## Resource delta

`ACTIVE_TEXT` adds no service, actor life, probe panel, or fit. Its two calls
per program add exactly, per root:

```text
5 services * 48 programs * 2 calls = 480 logical calls
5 * 48 * (512 + 384) = 215,040 generated-token ceiling
0 fits
```

`LEAFE_STYLE_FINAL` reuses `P0` history and adds per root:

```text
48 * 2 branch calls + 8 probes * 8 calls = 160 logical calls
48 * (256 + 512) + 8 * 1,024 = 45,056 generated-token ceiling
1 terminal fit
```

Combined with the current 4,811-call/757,504-token/12-fit per-root envelope,
the full strong-baseline ceiling is **5,451 calls, 1,017,600 generated tokens,
and 13 fits per root**.

Including 2 development + 4 pilot + confirmation roots, plus the existing
18-fit writer canary:

| route | calls before separate writer canary | generated tokens | total fits including writer canary |
|---|---:|---:|---:|
| `N=20` (26 roots) | 141,726 | 26,457,600 | 356 |
| `N=32` (38 roots) | 207,138 | 38,668,800 | 512 |

The strong-text calls batch across services and roots. Stage
`LEAFE_STYLE_FINAL` only after the interaction and text-baseline contrasts are
immutable; a failed headline saves its fits and branch generation. Actual
input/output tokens, store/index bytes, wall time, and occupied GPU time remain
mandatory receipts.

## Mandatory versus optional

**Mandatory before a strong-memory paper claim**

- frozen longitudinal `ACTIVE_TEXT` in all five services;
- its development strength gate;
- registered `C_text` and `C_public` with variance-aware root selection; and
- `LEAFE_STYLE_FINAL` only if claiming superiority to batch reflective
  internalization.

**Optional mechanism studies after the headline is immutable**

- same-corpus active-text carrier made from P1's admitted rows (carrier
  localization, not a baseline);
- raw-periodic LoRA, binding/state-target derangement, adapter-off, rank-16,
  linked/atoms carrier panels, and exact-memory swaps;
- full MemoPilot training, exact Evo-Memory benchmark reproduction, or a
  second external environment.

Adapter-off remains a mandatory causal diagnostic for a parametric-attribution
sentence, but it is not a strong agent-memory competitor.

## Sources inspected

- `research_loop/plans/one_parent_child_headline_v1.md`
- `research_notes/ICLR_2027_READINESS_20260906.md`
- `paper/iclr2027_experience_models/main.tex`
- `research_notes/related_work/20260906_experience_learning_neighbors.md`
- `research_notes/{03_agent_memory_benchmarks,11_baselines_benchmarks,12_atlas_baselines_learned_write,43_developmental_experiential_learning_v1}.md`
- `research_loop/advisory/20260903_paper_prior_baseline_audit.md`
- `research_loop/advisory/20260903_rml_paper_crossadjudication_v1.md`
- `research_loop/advisory/20260906_iclr_c2_c6_counterfactual_lifetime_headline_v0.md`
- `research_loop/advisory/20260906_iclr_headline_{adjudication,science_attack,resource_attack}_v1.md`
- Primary pages: <https://arxiv.org/abs/2603.16843>,
  <https://arxiv.org/abs/2606.08656>,
  <https://arxiv.org/abs/2511.20857>,
  <https://arxiv.org/abs/2510.04618>, and
  <https://github.com/ace-agent/ace>.

## Exact disposition

**The current candidate is underdefined and unpowered for the strong-baseline
claim. Repair the common active-memory layer and add its contrasts before
exact architecture ratification.** This is a material proposal change and must
enter the repository's deliberation/ratification path. It does not authorize
editing the current bound plan or running a baseline.
