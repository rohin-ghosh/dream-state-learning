# Astra memo q14 — the first level-3 (preschool) lives: a post-outcome record slot, the artifact lesson, the numbered baseline; 128 episodes × 4 sleeps; shadow gate; item format; the cheapest H1 probe

Asked by Fable 2026-09-12 00:03 UTC (single call, `tools/astra.py`, effort high, 83 s; prompt in `q14_run/prompt.md`, raw reply in `q14_run/reply_raw.md`). Adopted as the design for the level-3 preschool experiment (THESIS v2 §7), pending Rohin's ruling on the tick format (the loop's tokens are his) and on launching parented lives under the Codex STOP.

---

## Recommendation

**Run 128 training episodes with four sleeps, not 256. Start with the post-outcome slot alone.** The present failure is partly architectural: the child is asked to record an observation before that observation exists. More exhortation cannot repair that timing.

The existing evidence supports **“the current pipeline does not produce child-authored records,” not “the child cannot learn record-writing.”** The zero articulation rate across 28 lives and the prediction-only/no-result rejection families are consistent with the missing slot. The bridge experiment supports explicit artifact teaching, but demonstrates form-conditioned production and storage—not independent retention. [Evidence supplied in question.]

**Limits:** I cannot verify q13’s exact paragraph, examples, gate implementation, or articulation denominator. Below are proposed replacements and explicit operational measures, not purported reproductions. No external evidence is assumed.

## 1. Smallest intervention and three cells

### (a) Add one post-outcome turn

Keep the current PREDICT / NOTE / ACT sequence unchanged. After execution, show:

```text
Program: <id>    Tick: <t>    Execution: <unique id>
ACT executed: <actual pass sequence>
Instructions before: 857
Instructions after: 470
Measured reduction: 45.2%
Execution status: success

NOTE_AFTER:
```

The child gets one short generation, capped initially at approximately 100 tokens. **Do not supply a model-written summary or completed first-person sentence.** Show actual executed passes, not merely requested passes; distinguish execution success from optimisation success. On failure, show the error and unavailable measurements explicitly.

`NOTE_AFTER` must be associated with that execution ID. It is available after all 16 ticks, including the final tick. The lead owns the final token names and compilation boundaries; the essential requirement is **measurement first, child-authored record second**.

In the slot-only cell, explain only: “This field is available after the execution result.” No examples, mandatory schema, minimum count, or retry-on-invalid mechanism.

### (b) Teach a named artifact

Proposed parent paragraph:

> “A useful thing to leave yourself is a **measured action record**. It says what you actually tried and what you actually observed, in your own voice. An expectation is not yet a result. After a run, you can write: what I did, what happened, and—if useful—what this makes me want to test next. A poor result can still make a good record. Keep observations separate from guesses. Here are examples of the kind of memory I mean, not passes you must use.”

Provide three **explicitly synthetic** examples initially, using the gym’s actual pass vocabulary in place of A/B:

- “I ran A. Instructions went from 1,000 to 800, a 20% reduction.”
- “I tried B. The count stayed at 600; this attempt did not improve it.”
- “I ran A then B. Instructions increased from 400 to 420. I would test A alone next; that comparison is not yet measured.”

These vary improvement, no change, and regression—not just wording. Do not prescribe the bridge experiment’s canonical sentence: that would primarily test enforced formatting again.

Deliver the paragraph and examples before episode 1. Give one short refresher with one new synthetic example after sleeps 1–3, **after the post-sleep probe**. Parents receive no scores. Fix the teaching content across lives rather than permitting uncontrolled compensatory coaching.

### (c) Add the numbered baseline

Only in the third cell, append:

> “For a starting practice, aim to write **10 measured action records per episode**, after 10 of your actual runs. This is practice, not a requirement to invent something interesting or successful. Adjust as you learn what is useful.”

Ten is a deliberate teaching dose, not an evidence-derived optimum. There are 16 opportunities, so it leaves discretion. The harness neither enforces ten nor fabricates missing records.

### Experiment

| Cell | Post-outcome slot | Parent artifact lesson | Numbered baseline |
|---|---|---|---|
| A | Yes | No | No |
| B | Yes | Yes | No |
| C | Yes | Yes | Aim for 10 |

Use **two lives per cell**, with two seed/program-order blocks shared across cells. Hold the corpus policy, sleep training, and acceptance panel constant.

Start cell A’s first 32 episodes first. This establishes whether the affordance alone elicits records and catches plumbing errors. Then complete all six lives; do not select favourable seeds.

**Budget:** 128 × 4.2 + 4 × 10 = **577.6 GPU-minutes ≈ 9.63 GPU-hours** before extra generation/probes. Eight additional probe episodes bring this to **10.19 GPU-hours** at the supplied episode rate. The remaining approximately 1.8 hours is overhead headroom, not guaranteed capacity: benchmark the extra turn immediately. A 256-episode life costs approximately **19.25 GPU-hours** before overhead and misses the limit. Six proposed lives require roughly 61 GPU-hours plus overhead; GPU availability and concurrency remain unverified.

## 2. Measurement, duration, and success

Record production can change in episode 1; **sleep-mediated retention requires crossing sleep boundaries**. Use 32 episodes as the mechanical pilot, 64 as an early diagnosis, and 128/four sleeps as the primary endpoint. This is a practical design choice, not a power calculation.

Preserve the retrospective q13 metric if its implementation is available. Additionally pre-register:

\[
A_s^{raw} =
\frac{\text{executions with a qualifying child-authored post-outcome record}}
{\text{executions returning a numerical result in block }s}.
\]

A qualifying record contains:

1. A first-person account of the executed action.
2. An observed numerical outcome attributable to that execution.
3. No contradiction with the execution trace.

Harness text never counts as child articulation. Score all measured attempts, not only successful episodes. Separately report articulation in the assembled training corpus, using its own explicit denominator.

**Preschool acquisition threshold:** in each of the final two 32-episode blocks:

- \(A_s^{raw} \ge 0.20\);
- at least 24/32 episodes contain a qualifying record;
- manual factual audit finds at least 98% precision in claimed action/result facts.

Require this in **both lives of a cell** to call that configuration reproducibly successful at this scale. With 512 measured executions, 20% is about 103 records per block. These are proposed operational thresholds—not thresholds estimated from the supplied data.

This establishes record-writing **under the teaching configuration**. It does not establish H1.

**Sleep-destruction signature:** raw articulation rises before sleep, then the same neutral probe shows a ≥50% relative and ≥10-percentage-point absolute fall immediately after an **accepted** adapter update, repeated across two boundaries. Replay those probes with the saved pre-sleep adapter: recovery would implicate the sleep write rather than program mix or context. A rejected adapter cannot explain degradation through changed weights.

## 3. Shadow gate: log and promotion rule

Per sleep, save:

- Model/adapter identifiers, exact corpus manifest, gate/scorer versions.
- Executions, numerical-result opportunities, NOTE_AFTER completions.
- \(A_s^{raw}\), episode coverage, and counts stratified by optimisation success/failure.
- G, N, D separately, their intersections, admission rate, and all rejection-family counts; distinguish overlapping flags from any exclusive summary.
- Exact links between child spans and execution IDs; matched and unmatched numbers.
- **New-item admission and whole-corpus survival separately**, by item source and age.
- Corpus articulation before/after proposed filtering; duplicate rate and token counts.
- Pre/post-sleep probe results, checkpoint acceptance, panel score and training loss. Parents still see no scores.
- A small random audit plus all unmatched-number cases.

**Promotion proposal:** enforce only after two consecutive blocks with \(A_s^{raw}\ge0.20\), broad episode coverage, and **at least 64 distinct new items passing the actual gate per block** from training-eligible episodes. Articulation alone is insufficient: the success-only harvesting policy may still leave almost no admissible corpus.

For the initial three-cell experiment, keep the gate shadowed throughout. Apply this promotion rule to the next phase, or a separately declared extension. Switching individual cells at different times would confound teaching with corpus filtering.

Today’s 0–2.5% admission and near-empty surviving corpora make immediate enforcement an inadequate test of sleep learning. [Supplied retrospective gate results.]

## 4. Training-item format

**For an admitted record, let the child’s record replace the appended harness action/outcome line.** Keep the authoritative trace in audit metadata, outside the training target.

```text
Program <id>.
My measured action record: <verbatim child NOTE_AFTER>
```

Do not rewrite a deficient note into a good record. Do not attach unrelated pre-action thinking as though it were retrospective observation.

Rationale: whole-text loss should reward the child-authored procedural record, not repeatedly reward a harness-authored completion that supplies the facts the child omitted. Putting both beside each other duplicates the outcome and allows the current division of labour to persist: child writes slogan; harness writes evidence.

During shadow mode, leave non-admitted legacy items unchanged and log their contribution. This deliberately preserves the possibility that legacy training overwhelms the new behaviour; the pre/post probes detect it. Once enforced, train only admitted items, including previously admitted records—not the rejected legacy corpus.

## 5. Cheapest H1 probe

Reserve **one probe episode immediately before and after each sleep**, excluded from corpus harvesting and parent feedback: eight extra episodes total.

Use paired held-out programs with:

- fresh context, no classroom history, examples, reminders, or “ten”;
- ordinary compiler task instructions;
- measurements still visible;
- a neutral optional post-result field, such as `Scratchpad`, rather than the taught artifact name.

Removing all opportunity to write would not test expression fairly.

Count preliminary H1 evidence only if both lives retain measurable articulation in the final post-sleep neutral probes—for example **≥20% of measured executions**—and exceed their pre-training neutral baseline. Save a base-checkpoint replay for comparison. These small probes are noisy; report counts, not just percentages.

Parent-specific H1 evidence additionally requires B or C to outperform A on those probes. If all three transfer equally, the useful finding is that repairing the interaction enabled the skill—not that parenting taught it.

## 6. One thing we will get wrong

**We will be tempted to mistake an excellent ledger for reflection.** First-person restatement of supplied measurements is a worthwhile preschool behaviour, but it need not change the next experiment or prediction.

Do not broaden this six-day test into a reasoning benchmark. Establish the ledger first. Then test whether a stored record changes a later decision when the relevant program returns.

[astra openai/openai/gpt-6-astra effort=high 83s tokens in=1365 out=3322 reasoning=1034]
