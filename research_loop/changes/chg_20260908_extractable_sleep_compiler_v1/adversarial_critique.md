# Adversarial cross-critique — extractable SLEEP compiler v1

Date: 2026-09-08

Verdict: **REVISE before implementation.** The interpretations correctly
separate storage, extraction, use, dose, and cadence, but their first-pass
designs still contain causal and optimization ambiguities.

## Critical defects and exact repairs

1. **Verified-use admission is circular.** Requiring a lesson to have already
   caused a later successful use before it can be written prevents the first
   write that could have enabled that use. Repair: define three support
   levels. A direct public action/outcome can enter episode-scoped memory; a
   failure -> child revision -> better public outcome can enter corrective
   memory; a cross-situation principle requires two independent supports or
   prospective confirmation. Later verified use raises salience/dose and
   permits broader scope; it is not the only admission route.

2. **Winner-only targets create hindsight and survivorship bias.** Training
   only successful `THINK_TO_ACT` suffixes can behavior-clone lucky actions,
   erase uncertainty, and omit how the child noticed and repaired mistakes.
   Repair: keep failed actions as masked evidence; supervise the child's
   grounded post-outcome diagnosis, revised prediction, and next dispatched
   action when a subsequent outcome validates the correction. Preserve both
   positive and negative public evidence. Never supervise an unsuccessful
   action as the desired next action merely because it is in the ledger.

3. **A good outcome does not validate every thought token.** The child may
   reach a useful action for a false reason. Repair: target minimal native
   continuations and separately label which clauses are public observation,
   prediction, uncertainty, action, or supported inference. Unsupported
   explanations remain masked or are removed; broader causal language needs
   multiple evidence IDs.

4. **Cue diversity and thought-path diversity are different interventions.**
   Rewording the input while fixing one target tests cue invariance. Rewriting
   the target tests which reasoning/action paths are learned and adds a new
   factuality problem. Repair: first freeze one grounded target and vary only
   exact versus reordered/rewritten/state-only cues at equal target-token
   exposure. Test multiple validated target paths only in a later, separately
   named factor.

5. **`STATE_ONLY` does not prove recollection.** It can directly teach a
   state-to-action mapping, and success may be ordinary task SFT rather than
   extraction of experience. Repair: call it deployment-surface training.
   Require novel identifiers/instances plus state-target derangement and
   wrong-life controls. Extraction itself is measured by held-out cue forms;
   behavioral use is a separate endpoint.

6. **“Matched tokens” alone does not match optimization.** Adam depends on
   update count, batch boundaries, order, warmup/schedule, gradient
   accumulation, and initialization. Variable target lengths make simultaneous
   matching nontrivial. Repair: bind the exact ordered training multiset,
   loss-bearing target-token count, number of optimizer steps, token-balanced
   batch construction, LR schedule, initialization seed, data-order seed, and
   clipping. Predeclare a small tolerance where exact equality is impossible
   and report the residual. Record supervised rather than attended tokens.

7. **H4 is historical-view composition, not pure frequency.** It preserves
   transient compiler outputs that H1 omits. That is a valid contrast, but it
   cannot be called write cadence. Repair: name `H4-H1R` the historical-view
   effect. Under clean-base cumulative training, identical terminal
   corpus/trainer/seed has one terminal adapter; pure discarded intermediate
   writes have no endpoint path. Only a live K4/K1 comparison identifies the
   total cadence effect, and only as a package unless briefs are factored.

8. **The cadence proposal still bundles DREAM/SLEEP side effects.** Current
   sleeps change weights, generated briefs, compiler outputs, and gates; even
   rejected sleeps can leak corpora/briefs forward. Repair: after the writer is
   chosen, either disable briefs in the cadence experiment or add a brief-only
   arm. Rejected candidates must not become canonical compiler or context
   ancestors. Use occurrence-unique episode IDs and seeded compiler calls.

9. **Rank is not plasticity.** With `lora_alpha=2*rank`, the nominal LoRA
   scale `alpha/r` remains constant. Higher rank increases representational
   degrees of freedom; LR, target-token exposure, optimizer steps, and replay
   determine update pressure. Repair: tune compiler first, then test rank
   `{8,16}` crossed with low/high supervised exposure. Measure held-out
   extraction/use, adapter delta norm, anchor-prompt KL or log-prob drift, and
   interface harm. Choose the smallest safe rank on a representative corpus.

10. **The proposed GPU surface is too wide before a valid writer exists.** A
    16-fit dose/frequency study plus a rank grid can consume the mechanism
    window without resolving extraction. Repair: sequential gates: CPU corpus
    fidelity/provenance -> one-root/two-seed compiler 2x2 -> second-root
    replication only for surviving cells -> rank/plasticity calibration ->
    prospective cadence. Do not spend on 12k or long lives first.

11. **Current artifacts cannot seed a confirmatory claim unchanged.** The R2
    path is the old compiler/trainer; the write swarm varied optimizer dose;
    standalone probes were unseeded; cumulative retention rehearsed its test
    rows. Repair: reuse ledgers only as raw development evidence after
    occurrence/provenance repair. Rebuild corpora under the frozen compiler,
    seed trainer and inference explicitly, and reserve unreplayed sentinel
    evidence for retention.

12. **Literal repetition can manufacture the metric.** Requiring the same
    first NOTE every episode and scoring shared words with the parent's brief
    rewards phrase echo and may create another ritualized thinker. Repair:
    repeat a computation across varied relevant cases; score unprompted,
    semantically equivalent behavior, action change, public outcome, relevance
    selectivity, and persistence after context reset. Fade the prompt once the
    behavior appears.

13. **A bootstrap can erase the claimed parenting effect.** If it teaches the
    task, final vocabulary, answers, or exact evaluation behavior, it is
    ordinary task post-training and later parenting gain is uninterpretable.
    Repair: use target-blind unrelated microdomains, a surface/token-matched
    neutral bootstrap, and a bootstrap x parenting 2x2 separating entry level
    from interaction and learning rate.

14. **Bootstrap persistence can cross the forbidden boundary.** Replaying
    current parent utterances in every personal sleep would train the
    teacher's words. Repair: create and freeze a separately labeled schooled
    birth checkpoint; later personal LoRAs train from that birth base. Live
    parent language remains context-only and loss-masked. A permanent replay
    packet, if used instead, must be static pre-child schooling data and a
    separately declared substrate, never longitudinal parent messages.

## Required adjudication

The consensus should prioritize one question before frequency: under matched
optimization, which grounded compiler mixture makes experience extractable and
usable without harming the native agent? Cadence, rank growth, and parenting
scale become meaningful only after that gate passes.
