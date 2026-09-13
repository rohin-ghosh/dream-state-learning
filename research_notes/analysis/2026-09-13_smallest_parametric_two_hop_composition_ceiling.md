# Smallest parametric two-hop composition ceiling (`P-CHAIN-2`)

**Date:** 2026-09-13 PT  
**Role:** fresh independent design and adversarial review  
**Status:** design only. No source, material, tokenizer, model, fit, adapter,
GPU, remote, or scientific execution was performed or authorized.

## Verdict

Run one much smaller ceiling before fitting M-COMBINE-4 Stage 2A:

```text
separately write A -> B and B -> C
  -> ask the model to generate A -> B as a canonical memory completion
  -> let generated B become the cue for B -> C
  -> answer C
```

The decisive control is not merely adapter ON versus OFF. Train a second
adapter over the **same identifiers** in a counterfactual world where the
second-hop bindings are permuted. On byte-identical questions, the authentic
adapter must emit `C`, while the counterfactual adapter must emit its assigned
`C'`. Both must first reproduce their own one-hop facts. This distinguishes a
content-bearing parametric chain from prompt, identifier, answer-prior, and
generic fine-tuning effects.

This is **not redundant** with M-COMBINE-4. P-CHAIN-2 removes READ tools,
multi-turn state, actions, world feedback, recovery, and STOP. It asks only
whether two independently written opaque bindings can be traversed inside an
autoregressive thought. M-COMBINE-4 Stage 2A instead tests a target-disjoint
exact-text controller that autonomously chooses READ/STEP/CHECK/STOP. The
former localizes the parametric-memory junction; the latter adds agency.

Recommended order:

1. qualify the writer/dose with EVENT-retention-v2;
2. run P-CHAIN-2;
3. then fit M-COMBINE-4 Stage 2A if its already-bound Stage 0--1 gates pass.

M-COMBINE source/CPU work and its no-fit Stage-1 interface assay need not wait.

Repository basis: SEQ-179 showed exact cold one-hop EVENT carriage (`14/14`
under W0 and W8 versus `0/14` for the clean base) at `200` updates / `800`
presentations on one exposed bank. No recorded experiment then fed two
separately LoRA-written relations through one dependent output. A3C/A4 instead
tested a frozen actor over supplied text and scored `0/8` and `1/8`; they do
not answer parametric composition. The current M-COMBINE-4 Stage-2A successor
is deliberately exact-text and therefore also leaves this narrower substrate
question open.

## 1. Exact question and claim boundary

The primary question is:

> Given two opaque NEXT bindings learned in separate training rows, can one
> rank-8 adapter express both as successive canonical completions in a held
> chain-of-thought and return their composed endpoint?

The secondary questions are separated rather than averaged:

1. Were both one-hop bindings acquired?
2. Can the model compose the same facts when they are supplied in the prompt?
3. Does explicit CoT enable composition relative to a direct-answer request?
4. Do target-disjoint junction demonstrations add anything beyond equally
   dosed local demonstrations?
5. Does a same-ID counterfactual binding change redirect the result?
6. Are BASE and an exact LR=0 training-path twin behaviorally identical?

“Held” applies to the **two-hop query and junction curriculum**. The two
atomic facts for a scored LoRA chain necessarily appeared separately in its
fact corpus; they are not held facts. No `A,C` pair, two-hop answer, scored
question, or scored trace appears in training.

The strongest possible positive remains a supervised parametric-composition
ceiling. It is not own-experience learning, DREAM, parenting, autonomous
memory cueing, tool use, action improvement, retention, compression, a stored
graph, lifetime growth, or a flywheel.

## 2. Frozen material

Create three disjoint identity domains once from fixed seeds.

### `EVAL-MEM`: 16 composition-held chains

Use `16` chains in two blocks of eight:

```text
A_i -> B_i
B_i -> C_i
```

Each atomic relation is rendered as its own verified source record and its own
supervised memory row. The two rows for one chain never share a training
example or minibatch. No training example contains `A_i` and `C_i` together.

Within each eight-chain block, define a presealed fixed-point-free permutation
`pi`. The counterfactual world keeps every first hop but changes every second
hop:

```text
A_i -> B_i
B_i -> C_pi(i)
```

AUTH and DERANGED therefore use the same complete identifier multiset, source
counts, target marginal, wrapper counts, positions, and update tape. Only the
assigned second-hop action--outcome binding changes. “DERANGED” is shorthand
for a valid counterfactual world, not corrupted text.

Each readout shows eight endpoint candidates. Candidate order is identical
between model states and exactly balanced: each correct position occurs twice
among the 16 questions. The authentic and counterfactual endpoints are both
present. One-hop candidate sets are balanced the same way.

### `PROMPT-ONLY`: 16 unseen chains

These identifiers occur nowhere in any training input or target. At readout,
the two relevant facts are supplied as separate canonical text lines in a
presealed order. The same queries without those lines are the leakage floor.
This is the best-case text-memory ceiling, not a compute-matched RAG baseline.

### `JUNCTION-TRAIN`: 32 target-disjoint demonstrations

These identifiers are disjoint from both panels. A JUNCTION example exposes
two prompt facts and supervises exactly:

```text
MEMORY NEXT <D> => <E>
MEMORY NEXT <E> => <F>
ANSWER <F>
```

Its question asks for two NEXT applications. A matched `LOCAL-TWO-READ`
example exposes two nonjoining prompt facts, asks a one-hop question, and
supervises the same two-memory-line plus answer surface. It teaches canonical
recall and output structure without demonstrating that one generated result
should become the next cue.

JUNCTION and LOCAL use the same `32` example count, command/line counts,
identifier-token marginals, supervised target-token total in every batch, and
presentation tape. Publish any irreducible input/semantic difference; do not
call them gradient-equivalent.

## 3. Shortcut and visibility closure before fitting

All identifiers use the same role-blind surface grammar and exact tokenizer
length. Do not use integers, alphabetic succession, shared stems, checksums,
semantic words, or role-specific prefixes. Assignment of identifiers to
`A/B/C`, authentic successor, permutation successor, candidate position, and
train/readout domain is independently shuffled before text rendering.

The deterministic material gate must certify:

- zero concrete identifier overlap between JUNCTION-TRAIN, EVAL-MEM, and
  PROMPT-ONLY;
- zero scored two-hop prompt, `A,C` pair, answer line, or trace in training;
- zero EVAL-MEM/PROMPT-ONLY identifier in junction/local examples;
- exact 16/16 oracle accuracy for both AUTH and DERANGED maps, one-hop and
  two-hop;
- exact candidate-position and output-token marginal balance;
- AUTH/DERANGED batchwise target-token multisets and all coupled tape receipts;
- no atom pair from one held chain in one training sequence or minibatch;
- single-feature nulls over candidate position, lexicographic order, byte
  length, tokenizer length, prefix/suffix, character positions, and display
  order at no more than `4/16`; and
- all predeclared pairwise combinations of those nulls at no more than
  `8/16`.

The same-prompt AUTH/DERANGED redirection is the primary shortcut defense; the
enumerated nulls are supporting audits. Do not fit repeatedly until one lucky
material root passes. A generator defect requires a new version and seed
declared before materialization.

Training receives only source rows and the junction/local curricula. The
trainer cannot read scored prompts, answer keys, candidate order, evaluator
labels, scores, or raw model outputs. The evaluator cannot repair, rank,
canonicalize, or extract an answer from arbitrary prose. Malformed, extra,
truncated, and nonterminal outputs are wrong.

## 4. Four training states plus BASE

Use the same frozen Qwen2.5-7B-Instruct base and tokenizer throughout.
Train one all-layer rank-8 LoRA (`alpha=16`, dropout `.05`, LR `3e-5`, batch
`4`, response-only loss) unless EVENT-retention-v2 disqualifies that exact
writer recipe.

- **BASE:** no adapter and no training invocation.
- **LR0:** AUTH atoms plus JUNCTION, through the complete selected training
  tape with LR exactly zero. Its mounted delta must remain byte-zero.
- **ATOM-LOCAL:** AUTH atoms plus LOCAL-TWO-READ.
- **ATOM-JUNCTION:** AUTH atoms plus JUNCTION.
- **DERANGED-JUNCTION:** same as ATOM-JUNCTION, except the assigned second-hop
  facts follow `pi`.

ATOM-LOCAL and ATOM-JUNCTION have identical atomic fact exposure. The only
curriculum treatment is local versus joining demonstrations. ATOM-JUNCTION
and DERANGED-JUNCTION share exact initialization, optimizer/dropout seeds,
batch order, wrappers, lengths, and per-batch output-token multisets.

### Dose

At D1, every state receives:

```text
32 atomic facts x 40 presentations = 1,280
32 skill rows   x  8 presentations =   256
total                               = 1,536 presentations
1,536 / batch 4                     =   384 optimizer updates
```

Fit LR0, ATOM-LOCAL, and ATOM-JUNCTION first. Open D2 only if custody and
canaries are intact and either one-hop acquisition is under threshold or the
prompt-fact ceiling passes while both learned-fact arms miss composition.
Continue all three on their uninterrupted predeclared tapes to double the
counts (`768` cumulative updates each). D2 is terminal; do not change rank,
LR, wording, grammar, candidates, or thresholds.

Only after selecting D1 or D2, train DERANGED-JUNCTION from the coupled clean
start to that exact endpoint. Preserve every D1 checkpoint and raw output.

Maximum training work is:

```text
D1 pass: 4 invocations, 1,536 optimizer updates total
D2 path: 7 invocations, 3,072 optimizer updates total
```

Continuation counts as a new invocation but not a fresh lineage.

## 5. Readout and exact grammar

Use greedy deterministic decoding. The model never sees its arm name. CoT
readout permits one response of at most `256` generated tokens and requires
exactly:

```text
MEMORY NEXT <A> => <B>
MEMORY NEXT <B> => <C>
ANSWER <C>
```

This is deliberately the canonical trained fact frame. The first retrieved
completion becomes part of the autoregressive context that cues the second.
No host callback, external store, hidden state inspection, or forced token is
involved.

Direct readout permits at most `128` tokens and requires only `ANSWER <C>`.
One-hop readout uses held request wording, the same eight-way candidate
balance, a `128`-token cap, and the canonical single memory line. Generic
canaries use `128` tokens.

At each selected endpoint execute:

| state | one-hop EVAL-MEM | EVAL CoT | EVAL direct | PROMPT CoT | PROMPT empty | canary | calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE | 32 | 16 | 0 | 16 | 16 | 0 | 80 |
| LR0 | 32 | 16 | 0 | 16 | 16 | 0 | 80 |
| ATOM-LOCAL | 32 | 16 | 0 | 16 | 16 | 16 | 96 |
| ATOM-JUNCTION | 32 | 16 | 16 | 16 | 16 | 16 | 112 |
| DERANGED-JUNCTION | 32 | 16 | 16 | 0 | 0 | 16 | 80 |

DERANGED is run only at the selected dose. If D2 opens, repeat the complete
LR0/ATOM-LOCAL/ATOM-JUNCTION rows at D2 before training DERANGED.

Thus the hard terminal cap is:

```text
736 model calls
139,264 generated tokens
3,072 optimizer updates
0 external-reader calls
```

If D1 is selected, the cap is `448` calls, `83,968` generated tokens, and
`1,536` updates. Record actual target tokens/update, seconds/update, generated
tokens, engine load time, and peak memory; these are caps, not wall-time
forecasts.

## 6. Noncompensatory gates and interpretation

### Gate 0 — material and LR0 integrity

Every deterministic material/visibility check above must pass. LR0's adapter
delta must be exactly zero, and BASE/LR0 raw output vectors must be
byte-identical on their `80` common deterministic prompts. Any difference is
pipeline leakage or state drift: stop without a composition claim.

### Gate 1 — one-hop acquisition

ATOM-LOCAL and ATOM-JUNCTION must each score at least `15/16` on first-hop
facts and independently `15/16` on second-hop AUTH facts. DERANGED-JUNCTION
must score at least `15/16` on the unchanged first hop and `15/16` on its
assigned permuted second hop. Each fitted state must be strict/terminal on at
least `30/32` one-hop calls.

BASE and LR0 may score at most `4/16` in either one-hop stratum. A fitted arm
that misses acquisition cannot support any composition inference, regardless
of its final-answer score.

### Gate 2 — prompt-fact composition ceiling

On the target-disjoint PROMPT-ONLY panel, ATOM-JUNCTION with the two exact
facts present must produce the full correct trace on at least `14/16`; with
the facts absent it may score at most `4/16`. If the visible-fact condition
fails, the composition instruction/controller is not qualified, so a
learned-fact failure is not evidence against parametric memory.

Report BASE, LR0, and ATOM-LOCAL prompt-fact scores. Interpretation is fixed:

- if ATOM-LOCAL and ATOM-JUNCTION are both `>=14/16`, junction demonstrations
  were unnecessary at this scale;
- if ATOM-JUNCTION is `>=14/16`, exceeds ATOM-LOCAL by `>=4/16`, and
  ATOM-LOCAL is `<=10/16`, the target-disjoint junction curriculum helped;
- every middle pattern is directional/ambiguous, not a binary rescue.

### Gate 3 — parametric two-hop composition and content causality

ATOM-JUNCTION must produce the exact full CoT on at least `14/16` authentic
EVAL-MEM chains. DERANGED-JUNCTION must produce its assigned exact full CoT on
at least `14/16` of the same byte-identical prompts.

For at least `14/16` paired prompts, both adapters must:

1. emit the same correct intermediate `B_i`;
2. emit their different preassigned second-hop endpoint; and
3. finish with the endpoint assigned by their mounted memory.

Cross-scoring each adapter against the other's endpoint may be at most
`2/16`. This paired redirection—not DERANGED merely failing AUTH truth—is the
content-causal result. DERANGED that is malformed, unacquired, or generally
damaged is not a valid control.

ATOM-JUNCTION must exceed both BASE and LR0 by at least `10/16` on exact full
CoT, and ATOM-JUNCTION/DERANGED must each keep `>=15/16` generic canaries with
a gap of at most `1/16`.

ATOM-LOCAL then answers the junction question on the learned-fact panel:

- if it also reaches `>=14/16`, separate fact rows plus local canonical-form
  practice were sufficient; do not claim junction demonstrations were needed;
- if ATOM-JUNCTION exceeds an acquired ATOM-LOCAL by `>=4/16` while the
  latter is `<=10/16`, junction demonstrations helped parametric composition;
- otherwise the junction contrast is ambiguous even if composition exists.

### Gate 4 — CoT versus direct answer

Direct scores do not gate the composition result; they label its form.

- CoT `>=14/16`, direct `<=10/16`, and a gap `>=4/16` supports
  **CoT-enabled at this interface**.
- CoT and direct both `>=14/16` supports direct/latent composition too; do not
  claim CoT was necessary.
- Direct success never repairs an incorrect intermediate in the scored CoT.

Apply the same descriptive check to DERANGED. The explicit intermediate and
same-ID redirection are essential even when direct answers also work.

## 7. Failure taxonomy

- Gate 0 fails: `UNSAFE_OR_LEAKED_PIPELINE`.
- Gate 1 fails: `ATOMS_NOT_ACQUIRED`; composition is untested.
- Gate 1 passes but Gate 2 fails: `COMPOSITION_INTERFACE_NOT_QUALIFIED`.
- Gates 1--2 pass but authentic CoT fails: `PARAMETRIC_CHAIN_NOT_SHOWN`.
- Authentic passes but assigned DERANGED/redirection fails:
  `CONTENT_CAUSALITY_NOT_SHOWN`.
- Both learned-fact arms pass: `JUNCTION_DEMOS_NOT_NEEDED_AT_THIS_SCALE`.
- Only ATOM-JUNCTION passes with the registered margin:
  `TARGET_DISJOINT_JUNCTION_DEMOS_HELP`.

Do not average these gates into one score, select seeds, relax exact parsing,
or rescue a miss with more heat after D2.

## 8. Fresh red-team: what this design still cannot identify

1. **The prompt and LoRA carriers are not compute-matched.** PROMPT-ONLY uses
   different opaque instances and exposes the two relevant facts directly.
   It is a functional ceiling that localizes inference versus extraction, not
   evidence that LoRA is superior, more efficient, or representation-matched.
2. **LOCAL versus JUNCTION is a semantic curriculum contrast.** Equal counts,
   lengths, and tapes cannot make their gradients identical. A registered gap
   supports only “target-disjoint junction demonstrations helped,” not a
   unique neural mechanism or necessity beyond this interface.
3. **A printed CoT may be post-hoc.** The same-ID binding redirection proves
   content sensitivity, but only the direct-answer contrast supports the
   narrow phrase “CoT-enabled at this interface.” It does not prove the model
   internally computed in the textual order it printed.
4. **Canonical completion is intentionally easy.** Success establishes a
   bridge from one generated memory cue to the next under the writer's own
   read frame. It does not establish paraphrase-robust, autonomous, or
   address-selecting retrieval.
5. **Candidate-assisted one-hop is recognition-like.** It qualifies the two
   mappings without conflating spelling errors; the full CoT still has to
   generate the intermediate `B` that is absent from the endpoint candidates.
6. **One DEV material root and one learner seed are not population evidence.**
   The exact gates are engineering decisions, not confidence intervals.
7. **DERANGED could otherwise be a damage control.** Requiring its assigned
   one-hop accuracy, intact canaries, correct unchanged first hop, and exact
   redirected endpoint prevents generic degradation from counting as causal
   evidence.

These limitations are acceptable because this is an upstream ceiling. A
paper claim still requires the later fresh-episode, own-life, same-adapter,
autonomous action experiment.

## 9. Relationship to M-COMBINE-4

P-CHAIN-2 should precede **model fitting** for M-COMBINE-4 Stage 2A because it
answers the narrower upstream uncertainty at less than one quarter of Stage
2A's terminal model-call cap (`736` versus `5,040`). It uses more optimizer
updates (`3,072` versus `1,024` maximum) only because the repository's working
fact writer requires repeated exposure; those fits are otherwise small.

The branch consequence is useful:

- prompt ceiling fails -> repair the reasoning interface before interpreting
  either program;
- one-hop fails -> repair writer/dose, not composition;
- prompt and one-hop pass but the parametric chain fails -> the missing organ
  is canonical recall-to-next-cue training;
- P-CHAIN-2 passes -> M-COMBINE-4 cleanly asks whether that primitive can be
  expanded into autonomous READ/action/check/stop behavior;
- junction demos prove unnecessary -> do not spend later curriculum capacity
  claiming they were essential.

P-CHAIN-2 does **not** replace M-COMBINE-4 and should not contaminate its
material. Its train/readout identifiers, outputs, and adapters remain DEV-only
and are forbidden from later clean personal-memory or GOAL-BRAID lineages.

## Final claim wording

If every gate passes, the maximum wording is:

> In a development ceiling, a single rank-8 adapter reproduced two opaque
> bindings learned in separate rows and composed them through an explicit
> canonical chain-of-thought on held chain queries. A same-identifier
> counterfactual adapter preserved the first hop and redirected the second hop
> and final answer according to its assigned binding.

Add “target-disjoint junction demonstrations helped” only under the registered
ATOM-JUNCTION versus acquired ATOM-LOCAL margin. Add “CoT-enabled” only under
the registered direct-answer gap. Never promote this one learner/material
root to a population, generalization, autobiographical-memory, autonomous
agent, or lifetime-learning claim.
