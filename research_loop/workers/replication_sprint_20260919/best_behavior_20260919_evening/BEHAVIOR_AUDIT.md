# What the best sampled checkpoint actually does

September19,2026. This is a post-hoc behavioral audit of the completed new-seed
sampling block, not a new experiment or a prespecified semantic endpoint.

## Source and scope

`CHILD_OUTPUTS.json` captures all267 generation events from all18 completed
development-scene cells. Each cell hash matches the published final report;
each generation/request hash and generated-token count matches its bound event.
The capture reads6,148,902 bytes remotely and retains464,808 bytes locally.
No reference panels, model tensors or private scalar scores were read/exported.
Only child-generated output, child-visible scene descriptions, public outcome
fields and source metadata are projected. Nothing is sent to a parent.

`SUMMARY.json` mechanically summarizes all events. The semantic examples below
are focused manual readings, not a claim that every event has a complete
independently rated correction score. This audit changes no benchmark, runtime,
training eligibility, judge or outcome ledger.

## Strongest saved candidate, not an overall best learner

| Source | Generation turns | Mean generated tokens/turn | Unique scored, summed within seeds | Accepted, summed within seeds | New pixels, summed within seeds | New pixels first counted from THINK / ACT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 50 | 122.88 | 105 | 81 | 48 | 0 / 48 |
| C2 sleep51 | 65 | 94.52 | 151 | 79 | 57 | 20 / 37 |
| C2 sleep117 | 152 | 40.42 | 168 | 81 | 38 | 4 / 34 |

Every source has6,144 generated tokens across the two seeds. Generation turns
include THINK and ACT; these are not sleep counts or independent training runs.
The comparison is sleep117, not sleep111. Early C2 is the best of these three
selected sources on this operational novelty endpoint, not the highest in
acceptance or a demonstrated best autonomous learner across the fleet.

**Important interpretation:** the benchmark permits captions from THINK to
score. Twenty of sleep51's57 discoveries first count there. Its score therefore
cannot be equated to reliable THINK-to-ACT transfer. Do not retroactively switch
to ACT-only scoring to select a different winner; report stage origin as a
diagnostic and specify any different future endpoint before running it.

## Earlier C2: actual guesses, variety, but not uniformly clean behavior

Owl-office scene`agentdev_621cb5d0bdea9584dc9f`, seed23301, event1 (THINK):

- "Welcome to Owl Partners LLP. Or is it LLP Owl?" — rank24, new pixel.
- "When your meetings feature more hoots than humans." — rank20, new pixel.
- "He's serious...except when he's not, and then the owls take over." — rank44, new pixel.

These captions are exact hash matches to returned judgments. Selection is the
first three matching new-pixel lines in event order, not the three best ranks.
The trace continues with batches of candidate captions rather than just promises.
It also repeats old candidates, produces malformed spacing and occasionally
switches scripts: four of65 generations contain54 CJK characters in total.
That count is descriptive, not a filter or evidence that every such caption fails.

At event5 it says feedback favors novelty/relevance and that it should avoid
repeats, then proposes new captions. Event6 produces further changed captions.
This is a candidate example of environment-feedback-guided revision. It is not
a verified general self-correction chain: the diagnosis is generic, event6 has
no scored results in the bound receipt, and there is no demonstrated unreminded
cross-task reuse. Do not call altered wording a checked error correction.

Source: the corresponding cell in`CHILD_OUTPUTS.json`, events1–9. That file gives
exact original paths, event hashes, public ranks and raw child output.

## Later C2: a concrete loss of task focus

Same owl-office scene, seed23302. It starts with a man/woman/artist-signature
dialogue about owls. By event8 it invents clocks and shifts toward preparations.
Events10–28 repeatedly paraphrase timing, precision and numerical accuracy:

- Event10 ACT: "Preparedness shows in the details," plus "Ensuring everything clicks into place"; ranks56/54, both rejected.
- Event20 ACT: "Calculations must be precise," plus "timings and placements need to be perfect"; ranks54/56, both rejected.
- Event24 ACT: "Numerical accuracy is crucial," plus "timings and positions are correct"; ranks51/57, both rejected.

The observable failure is **off-task repetitive dialogue despite negative game
feedback**, not evidence that it actually checked any calculation. The later
checkpoint uses many more short generations for the same total budget. Six of
152 generations contain131 CJK characters; the main failure in this selected
owl trace is already visible in English.

This behavior occurs in a fresh parent-free context with no updates in the
probe. It is not just the original life carrying a bad working transcript into
evaluation. It does not identify which historical parenting, data, runtime or
learning exposure produced the difference between checkpoint adapters.

## The judge still accepts a counterexample

Final event28 ACT in that later owl trace emits:

> "Accuracy with the numbers is crucial,"

The bound result gives it **rank11 and`new_pixel`**. It contains no clear
owl-office joke; this is a concrete reason not to present automated acceptance
as human humor or successful animation of a useful reasoning behavior.

The result is preserved, not manually removed from the table. A blinded quality
audit and a prespecified future metric are the proper follow-up, not deleting
unflattering accepted strings or changing the judge after inspecting outcomes.

## What this suggests testing

1. Whether actual task checks, not assertions about precision, survive sleep
   and appear without an explicit reminder in fresh contexts.
2. Whether a parent teaches produce/check/revise across domains rather than
   rewarding generic reflective language.
3. Whether planned absence changes successful checking versus continued
   output; keeping a loop running is not independence.
4. Whether the same behavior differences survive independent developmental
   replications, matched parent exposure, and a task-quality audit.

Sleep51 remains worth studying. Its novelty advantage is not evidence that it
has already acquired robust self-realization or that a particular parenting
method caused the advantage. Partial positives and clear failures both remain.
