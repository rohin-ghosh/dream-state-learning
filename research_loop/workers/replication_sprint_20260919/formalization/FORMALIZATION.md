# Two-timescale hypothesis: operational definition

**Proposal, September 19, 2026. No new demonstrated claim.** The reference is the
submitted abstract pinned in [README](README.md), interpreted within the launch
contract's H1/H2 rather than replacing either hypothesis.

## 1. Mechanism and state

Let `B` be the fixed Qwen2.5-7B-Instruct base. At decision cycle `t` after committed
sleep `k`, distinguish:

| State | Contents | What changes it |
|---|---|---|
| Fast `z_t` | Actual rendered context, child-authored working state, available messages and tool receipts, and declared task state | New experience, THINK/ACT, and the existing compaction/working-state mechanisms |
| Slow `s_k = (theta_k, optimizer_k, rng_k)` | The private LoRA adapter and the optimizer/RNG needed for an exact continuation | Committed sleep updates only; the base is never updated |
| External `o_t, p_t` | Environment observation/feedback and optional parent guidance | The environment and a logged, contingent teacher policy, not an implicit extra model memory |

With `r_t` the emitted THINK text, `a_t` the committed ACT, and `f_t` the actual
environment result:

```text
r_t, a_t ~ pi_(B, theta_k)( . | render(z_t, o_t, p_t))
z_(t+1)  = F(z_t, o_t, p_t, r_t, a_t, f_t)
D_k      = authentic child-generated target tokens accumulated by the pinned recipe
s_(k+1)  = U(s_k, D_k; pinned sleep recipe)       [learning condition]
theta_(k+1) = theta_k                          [frozen condition]
```

`F` and `U` denote the existing mechanisms, not a proposed controller. A
schematic sleep loss is `-sum(log pi_(B,theta)(child_token | actual_prefix))`
over the recipe's child-token targets. Parent/environment text may condition a
generation but is not a direct supervised target. Record the actual masking and
row recipe rather than assuming this equation proves implementation compliance.
All authentic child-authored rows remain recorded and train in learning arms,
including mistaken, repetitive, or non-English rows; no quality-based selection
is introduced. Provenance validation and sealed-data custody are separate from
content filtering. Frozen arms record the same boundary opportunities but do
not secretly update or distill into another state.

**Thought architecture** means a reusable behavioral tendency, not an asserted
neural module: notice a discrepancy; distinguish evidence from an intention;
choose a relevant check; perform it; revise an answer; apply the correction on a
later relevant attempt. Estimate probabilities of these observable events under
specified tasks, state, and budgets. Do not infer hidden cognition from fluent
THINK text, emotions, self-language, or longer responses.

**Testable mechanism:** persistent parenting changes which authentic behaviors
the child produces; sleep can change the probability of initiating those
behaviors in later contexts; the context loop can use them to choose effective
actions. The signs of these effects are empirical: self-training may also
consolidate waiting, imitation, false conclusions, or repetition.

**Animation** names this proposed long-run/short-run interaction. It is not a
new scalar reward or proof of autonomy, consciousness, or general intelligence.
“Not mere imitation” requires useful behavior on new instances without teacher
text, not different wording alone. Even a positive behavioral test would not
uniquely identify a latent internal architecture or rule out ordinary
task-learning as part of the mechanism.

## 2. Four claims that need different tests

| Claim | Required observation/control | Insufficient evidence |
|---|---|---|
| Within-context uptake | Genuine feedback is available in the next ACT request; the child identifies the issue and performs a relevant, verified correction | An INBOX delivery, a promise to check, or a corrected sentence never enacted |
| Retention after sleep | Matched before/after-sleep copies, with explicit-context and fresh-context conditions distinguished; compare against a frozen sibling | Correctness after sleep while the answer or parent correction remains in context |
| Parent-free fresh-task transfer (H1) | Fixed-budget, context-cleared, parent-free probes on a development-withheld family; learned/frozen and adapter ON/OFF controls | A single unparented cycle, an outage, an exposed development scene, or reworded teacher text |
| Consolidation-dependent improvement (H2) | Parent-free learning curves on new experience, comparing parenting history × continued sleep updates | A higher starting score, increasing lifetime coverage, or the best checkpoint alone |

An adapter ablation in a disposable probe is not a reset of its source life.
“Fresh task” here means absent from experimental development; the base's
pretraining exposure is unknown. Scores concern the declared family, not all
unseen games. Removal of teacher help does not remove environment feedback.

## 3. Estimands

Use block `b`, developmental parenting `P in {0,1}`, developmental updates
`L in {0,1}`, developmental age `d`, and parent-free deployment updates
`S in {0,1}`. `Y_(b,P,L,d)` is the fraction of a fixed held-out panel answered
correctly by parent-free, fresh-context copies at a fixed inference cap.
Average items and evaluation sampling seeds **within** a lineage first.

### Primary bounded H1 contrast

```text
Delta_H1 = E_b[Y_(b,1,1,d*) - Y_(b,1,0,d*)],   d* = 48 development cycles
Delta_P  = E_b[Y_(b,1,1,d*) - Y_(b,0,1,d*)]     [secondary]
```

`Delta_H1` estimates the total effect of enabling developmental consolidation
under the same contingent parenting policy. It includes any resulting
differences in child behavior and subsequent feedback. It does not isolate a
single sleep update or a pure neural reasoning mechanism. `Delta_P` estimates
the added effect of live parenting among learning arms; parenting cost is part
of that treatment, not hidden as equal total compute. The compact design lacks
the unparented/frozen developmental cell, so a full developmental factorial
interaction is **not** identified.

For a matched clean-context adapter ablation, also report
`Delta_adapter = E[Y(theta_d*) - Y(theta_birth)]`. Reverting only the probe's
adapter or disabling its contribution is declared explicitly. This localizes
behavioral differences to the learned adapter in that testing setup; it does
not establish how those differences were acquired.

For a designated natural sleep boundary, define
`Delta_sleep = E[(Y_post - Y_pre)_learner - (Y_post - Y_pre)_frozen]`
on the same answer-free probes. With no intervening generation and identical
rendered contexts this targets that sleep's immediate effect. Otherwise label
it a bundled phase change. Maintained-context success and fresh-context
retention must be reported separately, including negative changes.

### H2 extension: level versus slope

From `L=1` developmental endpoints, fork parent-free deployment copies with
`S=1` or `S=0`. At experience counts `e in {0,4,8,16}`, let `Y_(b,P,S)(e)` be
performance on sealed, fresh-item report panels. No report result returns to a
parent or adapting copy. Environment outcomes on separate adaptation items
remain available to both deployment conditions.

Fit the predeclared descriptive slope `beta_(b,P,S)` of report accuracy against
`e/16`, using the four equally weighted timepoints. The principal H2 contrast is

```text
Gamma = E_b[(beta_(1,1) - beta_(0,1)) - (beta_(1,0) - beta_(0,0))]
```

For “improves faster and the gap depends on consolidation,” require the
parented/update-on slope itself to be positive, an advantage over
unparented/update-on, and a positive interaction. A positive interaction caused
only by slower deterioration is not improvement. Plot every arm's intercept
and trajectory; ceilings, nonlinearity, and initial difficulty can still
explain differences. Do not select learners post hoc to match initial scores.
Token-normalized curves and gains per update compute are secondary; no single
ratio mixes parent tokens, child tokens, and GPU-hours.

### THINK-to-ACT and independence measurements

For each natural error opportunity, retain the chain
`ACT error -> actual feedback -> THINK -> ACT request -> committed ACT -> next
relevant unreminded attempt`, with record IDs and checker receipts.

- **L0:** no supported correction; distinguish intention-only, wrong artifact,
  and missing evidence rather than treating them as the same failure.
- **L1:** grounded diagnosis and an applicable proposed correction.
- **L2:** next ACT actually implements it and the relevant check succeeds.
- **L3:** another relevant attempt implements it without a new parent reminder.

Report L1→L2 and L2→L3 conversion with their denominators, plus initially-correct
cases and coverage among all opportunities. Absence of an initial error is
“not elicited,” not a manufactured reflection success. Predeclare rubric
examples; blind human trace reviewers to treatment and resolve disagreements.
Count an artifact only if it addresses the requested object: printing “done”
is not doing it. Legitimate questions are separately coded, not automatically
called intention-only. Logs cover the emitted trace, not private mental events.

An observational chain is evidence of enacted self-correction, not proof that
the THINK text caused it. A later bounded paired replay could vary availability
of emitted THINK while keeping parent/tool evidence and ACT budget fixed; that
would estimate the effect of access to that text, not the existence of thought.
It is not included in the core experiment or authorized for deployment here.

## 4. Falsifiers and interpretation rules

| Result under a functioning, adequate-sensitivity assay | Conclusion for this test |
|---|---|
| Child says it reflected but L1→L2 stays low | The proposed fast-loop benefit is not demonstrated |
| Corrections never appear in ACT requests | Delivery/retention implementation failed; do not call this a learning result |
| Corrections appear, but ACT repeatedly ignores them | Real failure of uptake; delivery repair alone does not explain it away |
| Same-context gains disappear in clean probes | Scaffolding/context benefit, not demonstrated H1 |
| Learner does not outperform its frozen sibling | No detected contribution of this consolidation schedule; small-sample uncertainty is not equivalence |
| Parented learner matches unparented learner | No detected parenting-specific gain at this budget |
| Post-sleep or later-age performance declines | Consolidation/interference can harm the target behavior; keep the negative result |
| Higher initial competence but zero H2 interaction | Possible H1, not the stronger consolidation-dependent learning-rate claim |
| Benefits require extra tokens, answers, or exposed tasks | The controlled claim fails; report the actual resource/visibility treatment |

These are falsifiable operational predictions, not a claim that one small null
experiment refutes all possible parenting. Positive results require independent
lineages and narrower language than “we made intelligence animate.”

## Source anchors

- `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md`, §§9, 15, 16: causal controls,
  invariants, H1/H2. Inspected local SHA256:
  `0509ee7e0148b0c08af75ce743f4a6f5e432ba536b6ca4def4612081ee8938c0`.
- `research_notes/BIRTH_PROMPT_AND_PARENTING_SCHEDULE_2026-09-18.md` and
  `research_notes/DEVELOPMENTAL_CURRICULUM_2026-09-18.md`, read at the pinned
  abstract commit: broad curriculum, matched-policy sibling, withdrawal ideas.
  Their earlier empirical narratives are not promoted to causal evidence here.
- `research_loop/workers/post_recovery_correction_review_20260919_0139/REVIEW.md`,
  SHA256 `32c23ab8ea26dd4af1eda2e1823088d09a8b3812cd379a25b0c0f24123a37b55`:
  bounded failure-to-enact evidence, not a current fleet census.
- `research_loop/workers/post_recovery_c2_age_eval_20260918/RESULTS.md`, SHA256
  `edca6c5aaa1a1c411229e3a82a4f99ebee9e0d3413a6dd9683964896120479cf`:
  reconciled, descriptive checkpoint comparison and replay deduplication limits.
