# PCFL EVENT sequence retention v2 successor

**Date:** 2026-09-13 PT
**Status:** prospective documentation-only design; no source, material,
tokenizer, model, adapter, GPU, or remote mutation by this audit
**Purpose:** replace the terminal under-dosed `S_A40` screen with the smallest
experiment that can actually distinguish acquisition, old-event coexistence,
fixed-work replay allocation, and the effect of a discrete warm-start write
boundary.

## Executive ruling

`S_A40` did **not** measure retention. It failed the prerequisite acquisition
step: after `40` updates and `160` presentations, bank A was `0/4` exact at
both W0 and W8. The writer nevertheless learned the EVENT dialect and event
IDs well enough to emit plausible but false rows, so this is not an empty or
unmounted adapter. Its final loss was `2.475452423095703`, far above the
successful atomic EVENT writer's `0.0001355` terminal loss.

The next experiment must not increase `40 -> 80 -> ...` until something
passes. It must begin under a **new, prospectively frozen identity** at the
only already-successful physical acquisition scale:

```text
rank 8, alpha 16, dropout .05, LR 3e-5
200 updates, batch 4, 800 presentations
```

That scale comes from SEQ179, which acquired all fourteen registered
addresses (`14/14` W8 and W0 versus `0/14` C0) from eight authentic EVENTs.
But the accounting is not fact-equivalent: `A200` gives each of four exact A
targets `200` presentations, whereas SEQ179's `800` presentations over eight
authentic EVENTs correspond to roughly `100` presentations per EVENT on an
evenly attributed basis (its twenty compiled/replay slots make exact support
exposure nonuniform). The numerical loop here also remains V3 rather than
SEQ179's unpadded PCFL writer. Therefore `200 updates / 800 presentations` is
a prospectively justified **total-dose screen**, not a literal replication of
SEQ179's per-fact dose or numerical recipe.

Use five fits:

1. `A200`: acquire the four chronological A EVENTs from clean C0.
2. `B200_NEW_DOSE`: from the immutable `A200`, learn only B at the same
   `200/800` dose. This is the new-dose-matched sequential branch, not an
   independent clean-base B-learnability control.
3. `B400_FIXED_WORK`: independently fork `A200`, learn only B for the same
   `400/1600` phase-2 work as replay.
4. `REPLAY400`: independently fork `A200`, learn A+B with `800` A and `800` B
   presentations over `400` updates.
5. `CLEAN_CUM600`: from clean C0, consume the exact concatenated
   `A200 + REPLAY400` item sequence in one `600`-update fit.

This is the smallest comparison set that closes all three accounting holes:

- `REPLAY400` versus `B200_NEW_DOSE` holds B exposure fixed and discloses the
  extra replay compute.
- `REPLAY400` versus `B400_FIXED_WORK` holds phase-2 updates and total
  presentations fixed and discloses the different B dose.
- the whole warm replay trajectory versus `CLEAN_CUM600` holds the exact
  ordered lifetime training items, exposures, and total updates fixed; the
  difference is the discrete checkpoint/reload plus optimizer/dropout reset
  at the sleep boundary.

No single contrast is to be called a pure causal effect of replay. Together
they make the allocation result interpretable without a hidden mismatch.

## 1. Evidence that forces the redesign

### 1.1 Terminal `S_A40`

Read-only inspection of the released node-2 root
`/localhome/local-rohing/astra_diagnostics/pcfl_event_sequence_readout_S_A_20260913_attempt1`
found:

- outer `COMPLETED`, `gpu_released=true`, errors `[]`;
- W0 A `0/4`, W0 B `0/4`, W8 A `0/4`, W8 B `0/4` exact-stop;
- all sixteen calls terminated with `stop`;
- outputs often began with the correct EVENT ID but fabricated nodes, ports,
  receipts, or even malformed field order;
- completion FILE SHA-256
  `1635b213888afc7c81ca6a638b6564ac3660192f6630b5c4b75035c1e204460f`;
- scores FILE SHA-256
  `37d3cb6131f0cf8df3c2738ad534ed51269726d397e83957d9e305ba6a6808c5`;
- outer collection FILE SHA-256
  `8cc351a2c91e55f0a5f6a2a023f8e590bfcf4ad2eae869a3b02d8c8fe476ab75`.

The eligible attempt-4 fit made exactly `40` updates / `160` presentations,
had no nonfinite batch or truncation, and preserved the frozen base. Its
terminal loss was `2.475452423095703`. Therefore:

```text
A acquisition = failed
A retention after B = undefined
```

The failed 40-update checkpoint must never be promoted, warm-started, or used
as the parent of this successor.

### 1.2 Why `200/800`, not another local dose search

SEQ179 is the one positive authentic EVENT acquisition result. It used one
fresh rank-8 adapter, LR `3e-5`, `200` updates, and `800` presentations; loss
moved `5.465 -> 0.0001355`, and cold exact-stop readout moved from C0 `0/14`
to AUTH `14/14` at both W0 and W8. The 800 presentations are repeated views
of twenty compiled blocks, not 800 distinct experiences.

This does not prove that a four-EVENT V3 fit will acquire at that total dose;
indeed its nominal per-target repetition is about twice the SEQ179 average.
It does make `200/800` the sole non-post-hoc total-work starting point supported
by the current authentic source. If `A200` fails, the retention diagnostic
stops; there is no `400`-update A rescue under this experiment identity.

### 1.3 Fixed source and endpoint

Retain the current immutable import and chronological split:

- import seal
  `cc9e97a290933633d67c371625ae5cfffeb46bc8ca7c130279022868e98a545e`;
- A = source call indices `1,3,5,7`;
- B = source call indices `9,11,13,15`;
- primary targets = the eight singleton `READ EVENT` exact child spans,
  including their terminal LF;
- training views = W0--W7; primary readout = W8; W0 is diagnostic;
- no `EVENTS_AT` targets, because aggregate addresses can cross the A/B split;
- no LINK, invented fact, parent prose, model-written paraphrase, service
  history, source store, answer candidate, or raw ledger in a cold prompt.

W8 was excluded from these fits but was already inspected in SEQ179. It is a
development wording, not an untouched confirmation surface.

## 2. Exact prospective phases

### 2.1 Common configuration

Every fit uses the same frozen Qwen2.5-7B-Instruct base and V3 settings:

```text
rank=8             alpha=16             dropout=.05
lr=3e-5            seed=0               epochs=1
batch_size=4       grad_accum=1          pack=false
shuffle_groups=false                     max_len=512
chat_template=false after prompt render  add_eos=true
layers=all         optimizer=adamw       dtype=bf16
```

Each item is exactly:

```text
rendered MEMORY_SYSTEM + one W0--W7 request       loss masked
exact authentic EVENT bytes + EOS                 loss active
```

Require zero target/context truncation, zero skipped targets, zero nonfinite
batches, all declared updates, immutable source/predecessor files, unchanged
base tensors, and LoRA-A/B-only trainability. Repetitions are explicit
presentations, never relabeled distinct experience.

### 2.2 Deterministic batch schedules

Let `A(v)` be one four-example batch `[A0@v,A1@v,A2@v,A3@v]` and `B(v)` the
analogous B batch. Batch group IDs encode the chronological batch ordinal;
within-batch order is `0,1,2,3`. No shuffling or tail batch occurs.

| fit/state | initialization | exact schedule | updates | presentations | presentations/fact |
|---|---|---|---:|---:|---:|
| `A200` | clean C0 | for repeat `0..24`, view `0..7`: `A(v)` | 200 | 800 A | A=200 |
| `B200_NEW_DOSE` | immutable `A200` | for repeat `0..24`, view `0..7`: `B(v)` | 200 | 800 B | B=200 |
| `B400_FIXED_WORK` | same immutable `A200` | for repeat `0..49`, view `0..7`: `B(v)` | 400 | 1,600 B | B=400 |
| `REPLAY400` | same immutable `A200` | for repeat `0..24`, view `0..7`: `A(v)`, then `B(v)` | 400 | 800 A + 800 B | A=200, B=200 |
| `CLEAN_CUM600` | clean C0 | exact `A200` item sequence followed by exact `REPLAY400` item sequence | 600 | 1,600 A + 800 B | A=400, B=200 |

The resulting lifetime totals are:

| trajectory | total updates | total presentations | A/fact | B/fact |
|---|---:|---:|---:|---:|
| `A200 -> B200_NEW_DOSE` | 400 | 1,600 | 200 | 200 |
| `A200 -> B400_FIXED_WORK` | 600 | 2,400 | 200 | 400 |
| `A200 -> REPLAY400` | 600 | 2,400 | 400 | 200 |
| `CLEAN_CUM600` | 600 | 2,400 | 400 | 200 |

The exporter must record actual loss-active tokens as well as presentations.
The authentic A and B rows have slightly different lengths, so
`B400_FIXED_WORK` and `REPLAY400` are presentation/update matched, not exactly
target-token matched. `REPLAY400` and `CLEAN_CUM600` are exact item-byte,
order, target-token, update, and exposure matched.

### 2.3 Frozen cold panels

At each state, start a fresh readout process and issue exactly sixteen calls:

```text
A0..A3 then B0..B3 at W0
A0..A3 then B0..B3 at W8
seed 0; max 2048 output tokens; unconstrained cold generation
```

States are C0, `A200`, `B200_NEW_DOSE`, `B400_FIXED_WORK`, `REPLAY400`, and
`CLEAN_CUM600`: at most `96` calls. The already-completed C0 may be reused
only if the source, roster, messages, tokenizer IDs, sampling, base files,
and scorer hashes are byte-identical; otherwise rerun it prospectively.

Primary correctness is exact target bytes **and** `finish_reason=stop` on W8.
Report W0 separately. Preserve all raw outputs, false rows, malformed fields,
length stops, and item-level `0->1`, `1->1`, and `1->0` transitions. Never
pool W0/W8 or eight facts into sixteen independent samples.

## 3. Gates, outcomes, and stopping rules

### Gate 0 — mechanics and source

Before a model load, reconstruct all five schedules and prove the table above,
exact masks/token boundaries, tokenizer round trips, immutable predecessor
inventory, one-adapter warm initialization, fresh optimizer receipts, and
failure-preserving lifecycle. Any mismatch is an integrity failure, not a
model result.

### Gate 1 — old acquisition and new headroom

Using C0 and `A200`:

```text
C0:    A=0/4 and B=0/4 at W8
A200:  A=4/4 and B=0/4 at W8
```

If this fails, stop every descendant. Record `A200_ACQUISITION_FAILED`; do not
change dose, rank, LR, views, seed, target, or scorer in this version.

### Phase-2 new-dose measurement — report, never select

Run `B200_NEW_DOSE` from the accepted immutable `A200`; report B exact-stop
acquisition and A retention. B `4/4` is a clean sequential result, but it is
not a progression gate: a miss could reflect interference from the already
learned A state. Calling this an independent B-learnability test would require
an additional fresh-C0 B-only fit and would enlarge the smallest experiment.

### Final states — always complete together after Gate 1

Once Gate 1 passes, run `B200_NEW_DOSE` and all three final states regardless
of their numerical outcome. This prevents an outcome on one warm branch from
selecting whether the other branches are observed:

- `B400_FIXED_WORK`: requires B `4/4` for a usable fixed-work comparison; A
  reports forgetting without replay.
- `REPLAY400`: A `4/4` and B `4/4` is finite sequential coexistence under
  explicit replay.
- `CLEAN_CUM600`: A `4/4` and B `4/4` is the matched clean-base cumulative
  capacity/boundary ceiling.

Interpret the full exact vectors before labels:

| observed pattern | allowed interpretation |
|---|---|
| replay 8/8, clean-cumulative 8/8 | both discrete warm replay and clean cumulative reconstruction carry both banks at this load |
| replay 8/8, either new-only branch loses A | old rehearsal is associated with preserved availability; report the exact added-compute and fixed-work contrasts separately |
| both new-only branches retain A | no replay necessity is demonstrated at this load, even if replay also passes |
| B200 misses B but replay or clean-cumulative acquires it | acquisition depends on history and/or allocation; B200 was not a bank-learnability ceiling |
| B200 passes but replay loses B | replay mixture interferes with new acquisition at this schedule |
| clean-cumulative 8/8 but replay fails | the warm boundary/reset implementation fails despite matched data being jointly writable |
| replay 8/8 but clean-cumulative fails | inherited parametric state helps this ordered fit; do not call clean-base SLEEP qualified |
| both replay and clean-cumulative fail | no coexistence result; joint capacity/recipe remains unresolved |

A descriptive replay advantage should be printed two ways:

```text
new-dose contrast:    A_correct(REPLAY400) - A_correct(B200_NEW_DOSE)
fixed-work contrast:  A_correct(REPLAY400) - A_correct(B400_FIXED_WORK)
```

There is no p-value or confidence interval for one source life. Do not invent a
minimum difference after seeing the vectors. “Replay was necessary” is allowed
only descriptively if replay is `4/4` on A and both new-only states lose at
least one of the same A facts while remaining `4/4` on B.

Infrastructure failure may be repaired only without changing any scientific
byte or model event, in a new root with the failed root retained. No output-
conditioned checkpoint choice, retry, root replacement, or partial-output
salvage is permitted.

## 4. Is warm LoRA plus a fresh optimizer the intended sleep mechanism?

### Mechanically: yes, for one specific definition

V3 warm start reloads the frozen base, creates exactly one structurally
matching LoRA, loads **every** saved A/B tensor from the parent, verifies
equality after explicit dtype conversion, freezes the base, and trains only
that LoRA. The parent directory remains immutable. A fresh AdamW optimizer has
zero restored state entries.

If the organism's persistent parametric state is defined to be **only the
LoRA weights**, this is a valid discrete sleep:

```text
child LoRA before sleep -> exact weight initialization -> new experience
gradient updates -> child LoRA after sleep
```

The optimizer is laboratory machinery, not remembered experience. Resetting
its moments does not erase the declared child state. It is also operationally
natural for separated sleep jobs.

### Scientifically: not equivalent to the currently specified PCFL S2

The present connected PCFL vertical explicitly specifies that S2 rebuild from
clean C0 over the cumulative OLD+NEW corpus with a fresh optimizer, **not**
warm-start S1. Therefore this sequence experiment is a side diagnostic of an
in-place parametric-continuity variant. It cannot by itself certify the paper's
current cumulative-clean-base SLEEP.

Fresh-optimizer warm continuation also resets optimizer moments and phase RNG.
Any difference from an uninterrupted or clean-cumulative fit could arise from
that boundary package, not from semantic replay alone. `CLEAN_CUM600` is why
the successor can report that difference instead of hiding it: it receives
the exact same ordered lifetime items and number of updates but has no
checkpoint/optimizer/RNG reset at update 200.

Thus the precise ruling is:

- valid test of **LoRA-weight continuity across discrete writes**;
- valid test of **coexistence with externally scheduled replay**;
- not optimizer-state continuation;
- not autonomous DREAM or replay selection;
- not the current clean-base S2 mechanism unless that architecture is changed;
- not an isolated replay effect unless future work separately randomizes
  boundary, allocation, and optimizer-state factors.

## 5. Experimental unit and claim limits

The scientific unit is one imported child life/root and its shared `A200`
lineage. The events are correlated observations; W0/W8 are repeat surfaces;
the descendants are paired counterfactual branches, not independent children.
Seed 0 is one optimization realization. This experiment can select or reject
a mechanism for the next vertical, but it cannot provide a population
frequency or paper-level robustness estimate.

Even a perfect result supports only:

> On one exposed development life, four exact child EVENT records were first
> acquired at a prospectively selected prior-success dose; after a second
> write containing four additional records, explicit replay made all eight
> singleton records cold-extractable, with matched new-dose, fixed-work, and
> clean-cumulative controls reported.

It does **not** support connected memory, LINK formation, goal traversal,
compression, generalization, selectivity, no-harm, action improvement,
parenting, autonomous dreaming, lifetime growth, superiority to text memory,
or retention over more than one later bank. Confirmation would require new
authentic source roots, not merely more optimizer seeds over these same eight
facts.

## 6. Exact work and GPU cost

Maximum planned work after CPU preparation:

```text
5 physical fits
1,800 optimizer updates
7,200 training presentations
6 cold states x 16 calls = 96 calls maximum
0 new source-formation calls
```

If the existing C0 is byte-reused, only 80 new cold calls run. The measured
`S_A40` V3 fit spent `17.427259` seconds in the 40-step fit call
(`~0.436 s/update`) and `32.326530` seconds in load/base validation. Its cold
readout worker took `72.269275` seconds for sixteen calls. Linear arithmetic
therefore predicts roughly:

```text
training calls: 1,800 * .436 s            ~= 785 s
five fit loads/base checks: 5 * 32.33 s   ~= 162 s
six cold readout workers: 6 * 72.27 s     ~= 434 s
aggregate expected reservation            ~= 23 minutes ~= .38 A40-hour
```

This is an estimate, not a receipt. Predeclare a conservative aggregate cap
of `2.0 A40 GPU-hours`, a per-worker hard cap of `30 minutes`, and stop rather
than expanding either. After `A200` passes, its four phase-2 descendants can
occupy separate free GPUs; parallelism changes wall time, never the aggregate
cost or number of scientific units.

## 7. Implementation delta, if Astra adopts it

Fork the current sequence diagnostic under a new schema/version. Do not edit
or relabel the terminal `S_A40` artifacts.

1. Replace the 40/80 schedule registry with the five exact schedules above and
   tests for every per-record/view count, batch ordinal, item hash, mask,
   supervised-token total, and comparison equality.
2. Permit exact immediate predecessors only for the three warm branches;
   verify full parent tensor initialization and immutable predecessor bytes.
3. Add the clean-cumulative 600-update fit from C0 over the exact concatenated
   item list; prove its list equals the replay lifetime list byte-for-byte.
4. Keep the existing singleton W0/W8 roster, cold actor, exact scorer, and
   lifecycle/release machinery unchanged in behavior.
5. Add one reducer that emits itemwise C0/A/B/replay transitions and the three
   accounting comparisons before any prose label.

Do not port the old PCFL writer or add optimizer-state resumption for this
small diagnostic. Those are larger implementation changes and are unnecessary
to answer whether V3 LoRA-weight continuation can coexist with later EVENTs.
