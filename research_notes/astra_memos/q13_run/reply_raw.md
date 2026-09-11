## Recommendation

Teach an **episode record**, not an instruction to reflect. First measure whether the child writes that artifact unaided; then gate corpus admission on ledger-grounded content. Treat duplication as a separate collapse indicator. Do not assume that grammatical first person, factual provenance, or an outcome somewhere in the training item establishes articulation.

Evidence labels below refer to the supplied audit, not independently verified results:

- **E1:** 17 lives lose first person and repeat the “Initial passes…” recipe.
- **E2:** Eight lives develop first-person slogans, including nine notes with “zero episode-specific content.”
- **E3:** Neither ritual records this program’s action and measured result.
- **E4:** ≥98.5% factual-token provenance in 24 lives, but two catalogue writers name unrun passes frequently.
- **E5:** The harness already appends actual actions and outcomes.
- **E6:** Requiring the child’s canonical sentence increases prose restatement from 26% to 78%; LoRA completion reaches 0.82 versus 0.91 for handwritten templates.

## 1. Diagnosis

“Write down what you learn” names a **practice without specifying its deliverable**. Repeating that instruction is an easy, familiar linguistic performance of compliance. First-person language can become part of that performance without acquiring experiential content [E2–E3].

The recipe is another low-variance completion: name familiar passes, give an expectation, promise adjustment. It resembles a useful optimisation note but can be emitted before seeing any result [E1]. Repeated whole-text training on cumulative, successful-episode material plausibly reinforces whichever formula appears early. **That feedback mechanism is a hypothesis:** these observations do not isolate training effects from prompting, sampling, or success selection.

High provenance does not rescue either ritual. “Mentioned somewhere in my life” is weaker than “I ran this here and observed this result” [E4].

The bridge supports **eliciting the artifact in the child’s own output**, rather than supplying equivalent information afterward [E6]. It does not establish that first-person pronouns cause learning or that compiler records will reproduce the planted-fact result. Since whole-text loss also trains on harness text, authorship has no privileged channel; any advantage must come through changed text, placement, consistency, or behaviour [E5–E6].

Also, “every input turns into weight change” is presently an aspiration: successful-episode selection, gating, and adapter rejection each interrupt that path.

## 2. ARTICULATION GATE

### Unit and ledger

Evaluate the **child-authored note before harness augmentation**. Attach immutable episode ID, tick, program-state ID, and available ledger events. A qualifying event contains an executed pass sequence and measured before/after instruction counts. Use only observations available when the note was written—not a later episode outcome.

Start with these tests:

| Test | Operational definition | Initial treatment |
|---|---|---|
| **Episode grounding, \(G\)** | The note asserts execution of ≥1 pass in a ledger event from this episode, and reports that event’s measured outcome. Both belong to the same textual action–result assertion. “I expected 55%” and merely listing a pass fail. | Enforce |
| **Numerical agreement, \(N\)** | Counts equal ledger integers. A percentage equals \(100(b-a)/b\), rounded to the precision printed in the note. Accept an explicit unchanged count; handle \(b=0\) through counts, not percentages. Every asserted execution/result claim must agree with an available event. | Enforce |
| **First-person record, \(F\)** | “I” or “my” grammatically owns the completed action or observation: e.g., “I ran…” or “my measured count…”. “I will learn” does not qualify. | Measure first |
| **Recent duplication, \(D\)** | Compare with the previous **64 raw notes in that life**, including rejected notes. Canonicalise whitespace, case, and punctuation; remove harness metadata/episode IDs; retain passes and numbers. Exact canonical equality is a duplicate. | Enforce exact deduplication |
| **Template collapse, \(T\)** | Replace pass names and numbers with typed placeholders; report the largest resulting template’s share of new notes. Also report token five-gram Jaccard similarity ≥0.8 against the previous 64 notes. | Measure, not reject |
| **Practice-only, \(P\)** | No qualifying action–result assertion, plus a clause matching a versioned list of practice instructions—initially “form expectations,” “write down what I learn,” “learn from [the] outcome,” “be concrete,” and “adjust strategy.” | Report reason; already fails \(G\) |

Extract assertions with a versioned, ledger-constrained parser; validate matches mechanically. Mark unparseable notes **unknown**, not false. Human-audit all unknowns in the pilot and a stratified sample of passes and failures. Parsing arbitrary prose is a limitation I cannot verify away.

The initial admission rule is **\(G \land N \land \neg D\)**. Add \(F\) only after validating its parser and measuring retention. First person is a target register, not a substitute for evidence.

Do not reject grounded records merely because their scaffold repeats or they include a reflective sentence. Structured repetition may be useful. The near-duplicate and practice measures diagnose collapse without rewarding decorative paraphrase.

### Measure before enforcing

Run the tests retrospectively over all 25 lives and prospectively in shadow mode for one 32-episode block. Report raw articulation, unknowns, each rejection reason, accepted notes, tokens, unique episodes, and action–outcome diversity. Report both all notes and success-eligible notes: success selection may itself distort articulation.

At the first enforced cumulative rebuild, apply the gate retrospectively; filtering only new additions leaves the ritual-rich backlog training for three epochs. Also ensure rejected material cannot re-enter through an unfiltered “thoughts” field. Report thoughts separately from notes.

### Avoiding starvation

**The evidence gives no defensible minimum corpus size.** Rank 8 and three epochs are insufficient to infer one. Size includes unique experience, token count, and effective updates—not just note count.

Keep whole-text, three-epoch training fixed. On available grounded data, test nested pools of, for example, 32, 64, 128, and 256 distinct episodes, where feasible, with three training seeds. Log tokens and optimiser steps. Define \(N_{\min}\) as the smallest pool producing a predeclared record-writing improvement while meeting panel non-inferiority, replicated at the next larger pool. None may qualify.

Until then, accumulate accepted records and **skip a sleep update when data are insufficient**, retaining the current adapter. Do not pad with duplicate slogans or silently substitute harness prose. Label any synthetic bootstrap supplement and evaluate it separately.

## 3. Parent instruction: name the artifact

> Leave me a short record I could use to reconstruct one thing you actually tried on this program. A useful shape is: “I ran [the passes I executed]. I observed [the measured instruction count before and after, or measured change].” If you made a prediction, put it beside the observation so I can see whether they agreed. You can add one next experiment, keeping it distinct from what already happened. Use the numbers and actions in your current ledger; an unchanged or worse result is still a useful record. Choose your own wording—the deliverable is this program’s action and result.

Two **illustrative, invented examples—not audit observations**:

- “I ran `-mem2reg` and `-sroa`. The instruction count went from 857 to 470, a 45.2% reduction. I had expected 55%, so I overestimated the reduction.”
- “I tried `-gvn` after `-simplifycfg`. I measured 470 instructions before and 470 afterward. This attempt made no further reduction; I would test another pass next.”

The child copies examples [E2]. Therefore ground classroom examples in changing, supplied ledgers, including null and adverse outcomes. Vary the facts more than the style. Test later writing without the paragraph or examples present. These are offered recipes; only corpus admission is enforced.

## 4. Articulation rate and teaching decision

For sleep \(s\),

\[
A_s =
\frac{\#\{\text{new raw notes satisfying }F,G,N\}}
{\#\{\text{new raw notes}\}}.
\]

Compute before gating or harness augmentation. Duplication does not change this register rate; report it alongside \(A_s\). Report blank-note frequency separately to expose avoidance. Publish lower/upper bounds treating parser-unknown notes as failures/successes.

A concrete **provisional engineering criterion**, not an evidence-derived threshold:

- Run four parented lives.
- In at least three, \(A_s\ge0.60\) in each of the final four sleeps, with no artifact reminder during those blocks.
- Each qualifying life exceeds the retrospectively measured 90th percentile of baseline lives’ corresponding final-window rates by at least 20 percentage points.
- Improvement is visible in raw output, not merely the accepted corpus.

E1–E3 predict low baseline rates but do not supply these computed values. Rescore all 25 identically. Historical comparison establishes a departure from observed behaviour, not clean parental causality. For that claim, add seed-matched prospective runs with identical gate/training settings and current versus artifact-naming instruction.

## 5. Does the write carry the records’ content?

Separate two hypotheses:

- **Behaviour transfer:** adaptation makes the child produce more valid records on new episodes.
- **Memory transfer:** adaptation preserves particular experienced action–outcome associations.

From identical pre-sleep checkpoints, compare correct-record training, no write, and an offline diagnostic adapter trained on **within-program shuffled action–outcome associations**. Match text format, token budget, and training recipe. These corrupted records are experimental controls, not deployed corpus material.

Probe with source records absent from context:

1. Given an episode/program cue, retrieve the executed passes and measured result.
2. Distinguish executed passes from merely mentioned catalogue passes.
3. Make an optimisation decision where the remembered result is relevant.

Use held-out probe wording; keep success, null, and adverse outcomes represented. Memory evidence requires correct-record adaptation to outperform no-write and shuffled-content controls. Behaviour improvement alone supports register transfer, not H1 with memory content.

Compare against both the child’s ordinary written brief and a token-budget-matched brief containing the same records. The supplied **15-of-24 text-memory result** makes this essential. Matching text memory can demonstrate storage without demonstrating practical superiority; an adapter advantage requires a defined benefit such as reduced context use, persistence, or better decisions.

Finally, compare child-written records with semantically matched harness-written records. E5–E6 motivate this contrast but do not resolve it. Evaluate candidate adapters before panel selection as well as retained ones.

## 6. One thing we will get wrong

We will initially confuse **ledger-faithful transcription with learning**. A child can accurately write “I ran X; Y happened” while acquiring neither causal understanding nor a useful next move. Accept that artifact as the first milestone, but reserve the stronger claim for content-sensitive retrieval and changed decisions—not improved first-person style.

[astra openai/openai/gpt-6-astra effort=high 74s tokens in=1236 out=2865 reasoning=500]
